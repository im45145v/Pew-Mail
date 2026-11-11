# Pew Mail - Performance Optimization Guide

This document outlines performance optimization strategies and implementation patterns for Pew Mail to ensure optimal application responsiveness, scalability, and resource utilization.

## Overview

Pew Mail implements various performance optimization techniques across the application stack to deliver fast response times and efficient resource usage. This guide documents the approaches used and provides implementation patterns for maintaining high performance.

## Database Optimization

### Indexing Strategy

```python
# Proper indexing for common query patterns
from sqlalchemy import Index, Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class Email(BaseModel):
    __tablename__ = "emails"
    
    # Primary key is automatically indexed
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    subject = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)  # For filtering
    
    scheduled_at = Column(DateTime, nullable=True, index=True)  # For scheduling
    sent_at = Column(DateTime, nullable=True, index=True)       # For analytics
    
    is_published = Column(Boolean, default=False, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    
    # Composite indexes for common query combinations
    __table_args__ = (
        Index('idx_emails_org_status', 'organization_id', 'status'),
        Index('idx_emails_user_created', 'user_id', 'created_at'),
        Index('idx_emails_scheduled', 'scheduled_at', 'status'),
    )

class Contact(BaseModel):
    __tablename__ = "contacts"
    
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)  # For lookups
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    is_subscribed = Column(Boolean, default=True, index=True)
    tags = Column(String, nullable=True)  # JSON array of tags
    
    last_emailed_at = Column(DateTime, nullable=True, index=True)
    
    __table_args__ = (
        Index('idx_contacts_org_email', 'organization_id', 'email', unique=True),
        Index('idx_contacts_tags', 'organization_id', 'tags'),
        Index('idx_contacts_subscription', 'organization_id', 'is_subscribed'),
    )
```

### Query Optimization

```python
# Efficient query patterns
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func, or_, and_

class EmailService:
    def get_emails_with_metadata(self, organization_id: str, limit: int = 50, offset: int = 0):
        """Efficient email retrieval with related data"""
        # Use selectinload for collections to avoid N+1 queries
        emails = self.db.query(Email)\
            .options(
                selectinload(Email.template),  # For collections
                joinedload(Email.user)          # For single objects
            )\
            .filter(Email.organization_id == organization_id)\
            .filter(Email.is_deleted == False)\
            .order_by(Email.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return emails
    
    def get_email_statistics(self, organization_id: str):
        """Aggregate query for email statistics"""
        stats = self.db.query(
            func.count(Email.id).label('total_emails'),
            func.count(Email.sent_at).label('sent_emails'),
            func.avg(Email.delivery_time).label('avg_delivery_time'),
            func.sum(Email.open_count).label('total_opens')
        ).filter(
            Email.organization_id == organization_id,
            Email.created_at >= func.current_date() - func.interval('30 days')
        ).first()
        
        return stats
    
    def search_emails(self, organization_id: str, search_term: str, limit: int = 20):
        """Optimized search with full-text search capabilities"""
        # Use database-specific full-text search when available
        emails = self.db.query(Email)\
            .filter(Email.organization_id == organization_id)\
            .filter(or_(
                Email.subject.ilike(f'%{search_term}%'),
                Email.body.ilike(f'%{search_term}%')
            ))\
            .order_by(Email.created_at.desc())\
            .limit(limit)\
            .all()
        
        return emails

# Query optimization with raw SQL for complex operations
from sqlalchemy import text

class AnalyticsService:
    def get_complex_analytics(self, organization_id: str):
        """Complex analytics with optimized raw SQL"""
        sql = text("""
            WITH email_stats AS (
                SELECT 
                    DATE_TRUNC('day', created_at) as day,
                    COUNT(*) as email_count,
                    AVG(delivery_time) as avg_delivery,
                    SUM(open_count) as total_opens
                FROM emails 
                WHERE organization_id = :org_id 
                    AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE_TRUNC('day', created_at)
            )
            SELECT 
                day,
                email_count,
                COALESCE(avg_delivery, 0) as avg_delivery,
                COALESCE(total_opens, 0) as total_opens,
                CASE 
                    WHEN LAG(email_count) OVER (ORDER BY day) > 0 THEN
                        ROUND(((email_count - LAG(email_count) OVER (ORDER BY day)) * 100.0 / 
                              LAG(email_count) OVER (ORDER BY day)), 2)
                    ELSE 0
                END as growth_rate
            FROM email_stats
            ORDER BY day DESC
        """)
        
        result = self.db.execute(sql, {'org_id': organization_id}).fetchall()
        return [dict(row) for row in result]
```

### Connection Pooling

```python
# Database connection pooling configuration
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from app.core.config import settings

# Production database configuration
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # Number of connections to maintain
    max_overflow=30,        # Additional connections beyond pool_size
    pool_pre_ping=True,     # Validate connections before use
    pool_recycle=3600,      # Recycle connections after 1 hour
    echo=settings.DEBUG
)

# Session factory with proper connection handling
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Don't expire objects after commit
)
```

## Caching Strategies

### Redis-Based Caching

```python
import redis
import json
import pickle
from typing import Any, Optional
from app.core.config import settings

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=False,  # We'll handle serialization manually
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value is not None:
                return pickle.loads(value)
        except Exception as e:
            # Log error but don't fail the request
            logger.warning(f"Cache get failed for key {key}: {str(e)}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        try:
            serialized_value = pickle.dumps(value)
            self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {str(e)}")
    
    def delete(self, key: str):
        """Delete value from cache"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {str(e)}")
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching a pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache pattern invalidation failed for {pattern}: {str(e)}")

# Application-level caching with decorators
from functools import wraps
import hashlib

def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function signature
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = f"{key_prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

# Usage example
class EmailTemplateService:
    @cache_result(ttl=1800, key_prefix="template")
    def get_template_with_components(self, template_id: str):
        """Get template with all components (cached for 30 minutes)"""
        template = self.db.query(EmailTemplate)\
            .options(selectinload(EmailTemplate.components))\
            .filter(EmailTemplate.id == template_id)\
            .first()
        
        return template
    
    def update_template(self, template_id: str, update_data: dict):
        """Update template and invalidate cache"""
        # Perform update
        template = self.db.query(EmailTemplate)\
            .filter(EmailTemplate.id == template_id)\
            .first()
        
        for field, value in update_data.items():
            setattr(template, field, value)
        
        self.db.commit()
        
        # Invalidate cache for this template
        cache.invalidate_pattern(f"template:*{template_id}*")
        
        return template
```

### CDN and Static Asset Optimization

```python
# Frontend asset optimization
# vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { compression } from 'vite-plugin-compression'

export default defineConfig({
  plugins: [
    react(),
    compression({
      algorithm: 'gzip',
      ext: '.gz',
    }),
    compression({
      algorithm: 'brotliCompress',
      ext: '.br',
    })
  ],
  build: {
    rollupOptions: {
      output: {
        // Separate vendor and app code for better caching
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          utils: ['lodash', 'moment'],
        }
      }
    },
    // Enable minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      }
    }
  },
  // Asset optimization
  assetsInclude: ['**/*.svg', '**/*.png', '**/*.jpg', '**/*.jpeg', '**/*.gif'],
})
```

## API Performance Optimization

### Response Compression

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()

# Add gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

# Optimized response models with selective field inclusion
from pydantic import BaseModel
from typing import Optional, List

class EmailSummaryResponse(BaseModel):
    """Lightweight email summary for listing"""
    id: str
    subject: str
    status: str
    created_at: str
    # Only essential fields

class EmailDetailResponse(EmailSummaryResponse):
    """Detailed email information"""
    body: str
    template_id: Optional[str]
    scheduled_at: Optional[str]
    sent_at: Optional[str]
    # Additional fields as needed

# Pagination with cursor-based approach
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    data: List[Any]
    next_cursor: Optional[str]
    has_more: bool

class EmailService:
    def get_paginated_emails(self, organization_id: str, cursor: str = None, limit: int = 50):
        """Cursor-based pagination for better performance"""
        query = self.db.query(Email)\
            .filter(Email.organization_id == organization_id)
        
        if cursor:
            # Use cursor for efficient pagination
            query = query.filter(Email.id > cursor)
        
        emails = query.order_by(Email.id)\
            .limit(limit + 1)\
            .all()
        
        has_more = len(emails) > limit
        if has_more:
            emails = emails[:-1]  # Remove extra item
        
        next_cursor = emails[-1].id if emails else None
        
        return PaginatedResponse(
            data=emails,
            next_cursor=next_cursor,
            has_more=has_more
        )
```

### Background Processing

```python
# Asynchronous task processing with Celery
from celery import Celery
from app.core.config import settings

celery_app = Celery("pewmail")
celery_app.conf.broker_url = settings.CELERY_BROKER_URL
celery_app.conf.result_backend = settings.CELERY_RESULT_BACKEND

# Background tasks for heavy operations
@celery_app.task
def process_email_batch(organization_id: str, email_ids: List[str]):
    """Process email batch in background"""
    # Heavy processing moved out of request/response cycle
    pass

@celery_app.task
def generate_analytics_report(organization_id: str, date_range: dict):
    """Generate analytics report in background"""
    # Long-running analytics computation
    pass

# API endpoint that delegates to background task
from fastapi import BackgroundTasks

@router.post("/emails/batch-process")
async def batch_process_emails(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Schedule batch email processing"""
    # Validate request synchronously
    validate_batch_request(request)
    
    # Delegate heavy work to background
    background_tasks.add_task(
        process_email_batch,
        organization_id=request.organization_id,
        email_ids=request.email_ids
    )
    
    return {"message": "Batch processing scheduled"}
```

## Memory Optimization

### Efficient Data Structures

```python
# Use generators instead of loading all data into memory
class EmailService:
    def stream_email_attachments(self, email_id: str):
        """Stream email attachments efficiently"""
        attachments = self.db.query(Attachment)\
            .filter(Attachment.email_id == email_id)\
            .yield_per(100)  # Limit memory usage
        
        for attachment in attachments:
            yield attachment.content

# Object pooling for frequently created objects
from typing import List
import threading

class ObjectPool:
    def __init__(self, create_func, max_size=100):
        self.create_func = create_func
        self.pool = []
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def get(self):
        with self.lock:
            if self.pool:
                return self.pool.pop()
            return self.create_func()
    
    def put(self, obj):
        with self.lock:
            if len(self.pool) < self.max_size:
                # Reset object state
                self._reset_object(obj)
                self.pool.append(obj)
    
    def _reset_object(self, obj):
        # Reset object to reusable state
        pass

# Pool for frequently used objects
email_parser_pool = ObjectPool(lambda: EmailParser(), max_size=50)
```

### Memory Monitoring

```python
import psutil
import gc
from functools import wraps

class MemoryMonitor:
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss
    
    def get_memory_usage(self):
        current_memory = self.process.memory_info().rss
        return {
            'current': current_memory,
            'increase': current_memory - self.initial_memory,
            'percentage': self.process.memory_percent()
        }
    
    def log_memory_usage(self, context: str = ""):
        usage = self.get_memory_usage()
        logger.info(
            f"Memory usage {context}",
            memory_mb=usage['current'] / 1024 / 1024,
            increase_mb=usage['increase'] / 1024 / 1024,
            percentage=usage['percentage']
        )

def monitor_memory(func):
    """Decorator to monitor memory usage of functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        monitor = MemoryMonitor()
        monitor.log_memory_usage(f"before {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            monitor.log_memory_usage(f"after {func.__name__}")
            # Force garbage collection if memory increased significantly
            if monitor.get_memory_usage()['increase'] > 50 * 1024 * 1024:  # 50MB
                gc.collect()
    
    return wrapper
```

## Load Testing

### Performance Testing Scripts

```python
# locustfile.py - Load testing with Locust
from locust import HttpUser, task, between, events
import random
import uuid

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """Login before starting tests"""
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def get_emails(self):
        """Test email listing endpoint"""
        self.client.get("/emails", headers=self.headers)
    
    @task(2)
    def create_email(self):
        """Test email creation endpoint"""
        response = self.client.post("/emails", json={
            "subject": f"Test Email {random.randint(1, 1000)}",
            "body": "<p>This is a test email body</p>",
            "organization_id": str(uuid.uuid4())
        }, headers=self.headers)
        
        if response.status_code == 200:
            email_id = response.json()["id"]
            # Test related endpoints
            self.client.get(f"/emails/{email_id}", headers=self.headers)
    
    @task(1)
    def get_analytics(self):
        """Test analytics endpoint"""
        self.client.get("/analytics/dashboard", headers=self.headers)

# Custom metrics for load testing
@events.request_success.add_listener
def on_request_success(request_type, name, response_time, response_length, **kwargs):
    if response_time > 1000:  # Log slow requests
        print(f"SLOW REQUEST: {name} took {response_time}ms")

@events.request_failure.add_listener
def on_request_failure(request_type, name, response_time, response_length, exception, **kwargs):
    print(f"FAILED REQUEST: {name} failed with {exception}")
```

## Frontend Performance

### React Component Optimization

```tsx
// Efficient React components with memoization
import React, { memo, useMemo, useCallback } from 'react';

// Memoized component to prevent unnecessary re-renders
interface EmailListItemProps {
  email: Email;
  onToggleSelect: (id: string) => void;
  isSelected: boolean;
}

const EmailListItem = memo(({ email, onToggleSelect, isSelected }: EmailListItemProps) => {
  // Memoize expensive computations
  const preview = useMemo(() => {
    return email.body.replace(/<[^>]*>/g, '').substring(0, 100) + '...';
  }, [email.body]);

  // Memoize event handlers
  const handleToggle = useCallback(() => {
    onToggleSelect(email.id);
  }, [onToggleSelect, email.id]);

  return (
    <div className={`email-item ${isSelected ? 'selected' : ''}`}>
      <input 
        type="checkbox" 
        checked={isSelected}
        onChange={handleToggle}
      />
      <div className="email-content">
        <h4>{email.subject}</h4>
        <p>{preview}</p>
        <span className="date">{email.created_at}</span>
      </div>
    </div>
  );
});

// Virtual scrolling for large lists
import { FixedSizeList as List } from 'react-window';

interface EmailListProps {
  emails: Email[];
  onSelectEmail: (email: Email) => void;
}

const EmailList: React.FC<EmailListProps> = ({ emails, onSelectEmail }) => {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      <EmailListItem
        email={emails[index]}
        isSelected={false}
        onToggleSelect={() => {}}
      />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={emails.length}
      itemSize={100}
      width="100%"
    >
      {Row}
    </List>
  );
};

// Lazy loading components
import { lazy, Suspense } from 'react';

const RichTextEditor = lazy(() => import('./RichTextEditor'));

const EmailEditor: React.FC = () => {
  return (
    <Suspense fallback={<div>Loading editor...</div>}>
      <RichTextEditor />
    </Suspense>
  );
};
```

### Bundle Optimization

```json
// tsconfig.json with optimization settings
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "node",
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": false,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    
    // Performance optimizations
    "removeComments": true,
    "importsNotUsedAsValues": "remove",
    "preserveConstEnums": false
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

## Monitoring Performance

### Performance Metrics Collection

```python
from prometheus_client import Histogram, Gauge, Counter
import time

# Performance metrics
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_USERS = Gauge(
    'active_users',
    'Number of currently active users'
)

DATABASE_QUERY_TIME = Histogram(
    'database_query_duration_seconds',
    'Database query execution time',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# Performance monitoring middleware
from fastapi import Request
import asyncio

async def performance_middleware(request: Request, call_next):
    """Middleware to collect performance metrics"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Record latency
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)
    
    return response

# Database query timing
from contextlib import contextmanager

@contextmanager
def timed_database_query(query_type: str):
    """Context manager to time database queries"""
    start_time = time.time()
    try:
        yield
    finally:
        DATABASE_QUERY_TIME.labels(query_type=query_type).observe(
            time.time() - start_time
        )

# Usage example
class EmailService:
    def get_emails(self, organization_id: str):
        with timed_database_query("email_list"):
            return self.db.query(Email)\
                .filter(Email.organization_id == organization_id)\
                .all()
```

## Conclusion

This performance optimization guide provides a comprehensive framework for maintaining high-performance standards in Pew Mail. The implementation encompasses database optimization, caching strategies, API performance enhancements, memory management, and frontend optimization techniques.

Key optimization areas:
1. Database indexing and query optimization
2. Intelligent caching with Redis
3. API response optimization with compression and pagination
4. Background processing for heavy operations
5. Memory-efficient data structures and monitoring
6. Frontend performance optimization with React best practices
7. Comprehensive performance monitoring and metrics

Implementation best practices:
1. Regular performance testing and profiling
2. Monitoring of key performance indicators
3. Continuous optimization based on real usage patterns
4. Scalability planning for future growth
5. Resource utilization tracking and optimization
6. User experience monitoring with real-user metrics
7. Automated performance regression detection

The system is designed to scale efficiently while maintaining responsive user experiences across all application features.