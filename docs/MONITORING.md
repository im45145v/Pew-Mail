# Pew Mail - Monitoring and Observability

This document outlines the monitoring and observability strategy for Pew Mail to ensure application performance, reliability, and quick incident response.

## Overview

Pew Mail implements a comprehensive monitoring system covering application logs, health checks, error tracking, and operational metrics. The system follows modern observability practices with structured logging, metrics collection, and distributed tracing.

## Logging Strategy

### Structured Logging

```python
import logging
import json
from datetime import datetime
from typing import Dict, Any

class StructuredLogger:
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Configure structured logging handler
        handler = logging.StreamHandler()
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        self.logger.info(message, extra={'structured_data': kwargs})
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        self.logger.error(message, extra={'structured_data': kwargs})
    
    def warn(self, message: str, **kwargs):
        """Log warning message with structured data"""
        self.logger.warning(message, extra={'structured_data': kwargs})

class JsonFormatter(logging.Formatter):
    def format(self, record):
        """Format log record as JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': getattr(record, 'service', 'unknown'),
            'request_id': getattr(record, 'request_id', None),
            'organization_id': getattr(record, 'organization_id', None),
            'user_id': getattr(record, 'user_id', None),
            'resource_id': getattr(record, 'resource_id', None)
        }
        
        # Add structured data if present
        if hasattr(record, 'structured_data'):
            log_entry.update(record.structured_data)
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)
```

### Log Levels and Content

#### Security-Sensitive Information Handling

```python
import logging

# Never log these types of information
SENSITIVE_FIELDS = {
    'password',
    'token',
    'secret',
    'key',
    'credential',
    'authorization',
    'cookie',
    'access_token',
    'refresh_token',
    'api_key',
    'private_key',
    'credit_card',
    'ssn',
    'phone_number',
    'email_address'
}

class SecureLogger(StructuredLogger):
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from log data"""
        sanitized = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_FIELDS:
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, str) and len(value) > 1000:
                # Truncate very long strings
                sanitized[key] = value[:1000] + '...[TRUNCATED]'
            else:
                sanitized[key] = value
        return sanitized
    
    def info(self, message: str, **kwargs):
        """Log info message with sanitized data"""
        sanitized_kwargs = self._sanitize_data(kwargs)
        super().info(message, **sanitized_kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with sanitized data"""
        sanitized_kwargs = self._sanitize_data(kwargs)
        super().error(message, **sanitized_kwargs)
```

### Log Configuration

```python
# logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'app.logging.JsonFormatter',
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/pewmail/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'uvicorn': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

def setup_logging():
    """Setup logging configuration"""
    logging.config.dictConfig(LOGGING_CONFIG)
```

## Health Checks

### Application Health Endpoint

```python
from fastapi import APIRouter, Depends
from typing import Dict, Any
from sqlalchemy import text
import redis
import logging

router = APIRouter(prefix="/health", tags=["health"])

logger = logging.getLogger(__name__)

@router.get("/live")
async def liveness_check():
    """Liveness probe - is the application running?"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

@router.get("/ready")
async def readiness_check(db_session=Depends(get_db)):
    """Readiness probe - is the application ready to serve requests?"""
    checks = {}
    
    # Database check
    try:
        db_result = db_session.execute(text("SELECT 1")).fetchone()
        checks['database'] = 'ok' if db_result else 'error'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
        logger.error("Database health check failed", error=str(e))
    
    # Redis check (if used for caching/background jobs)
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        checks['redis'] = 'ok'
    except Exception as e:
        checks['redis'] = f'error: {str(e)}'
        logger.error("Redis health check failed", error=str(e))
    
    # Storage check
    try:
        storage_service = get_storage_service()
        storage_service.check_health()
        checks['storage'] = 'ok'
    except Exception as e:
        checks['storage'] = f'error: {str(e)}'
        logger.error("Storage health check failed", error=str(e))
    
    # Overall status
    overall_status = 'ok' if all(check == 'ok' for check in checks.values()) else 'degraded'
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/deep")
async def deep_health_check(db_session=Depends(get_db)):
    """Deep health check - comprehensive system verification"""
    results = {}
    
    # Database connection pool status
    try:
        from app.database.session import engine
        pool_status = {
            'size': engine.pool.size(),
            'checked_out': engine.pool.checkedout(),
            'overflow': engine.pool.overflow(),
            'checked_in': engine.pool.checkedin()
        }
        results['database_pool'] = pool_status
    except Exception as e:
        results['database_pool'] = f'error: {str(e)}'
    
    # Cache hit ratio (if using Redis)
    try:
        redis_client = get_redis_client()
        info = redis_client.info()
        if info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0) > 0:
            hit_ratio = info.get('keyspace_hits', 0) / (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0))
            results['cache_hit_ratio'] = hit_ratio
        else:
            results['cache_hit_ratio'] = 0
    except Exception as e:
        results['cache_hit_ratio'] = f'error: {str(e)}'
    
    return {
        "status": "ok",
        "details": results,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Error Monitoring

### Error Tracking Integration

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.core.config import settings

def init_error_monitoring():
    """Initialize error monitoring service"""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            environment=settings.ENVIRONMENT,
        )

# FastAPI exception handlers
from fastapi import Request
from fastapi.responses import JSONResponse

async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with error tracking"""
    # Capture exception in monitoring service
    sentry_sdk.capture_exception(exc)
    
    # Log the exception
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        request_url=str(request.url),
        request_method=request.method,
        user_agent=request.headers.get('user-agent'),
        client_ip=request.client.host if request.client else None
    )
    
    # Return generic error response
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"}
    )
```

### Custom Error Classes

```python
class PewMailError(Exception):
    """Base exception class for Pew Mail"""
    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code

class ValidationError(PewMailError):
    """Validation error"""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 400)

class QuotaError(PewMailError):
    """Quota limit exceeded"""
    def __init__(self, message: str):
        super().__init__(message, "QUOTA_EXCEEDED", 429)

class AuthenticationError(PewMailError):
    """Authentication failed"""
    def __init__(self, message: str):
        super().__init__(message, "AUTHENTICATION_FAILED", 401)

class AuthorizationError(PewMailError):
    """Authorization failed"""
    def __init__(self, message: str):
        super().__init__(message, "AUTHORIZATION_FAILED", 403)
```

## Operational Metrics

### Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge, Summary
import time

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_CONNECTIONS = Gauge(
    'database_active_connections',
    'Number of active database connections'
)

# Business metrics
AI_REQUEST_COUNT = Counter(
    'ai_requests_total',
    'Total AI requests',
    ['model', 'provider', 'organization_id']
)

EMAIL_SEND_COUNT = Counter(
    'email_sends_total',
    'Total email sends',
    ['status', 'provider', 'organization_id']
)

USER_COUNT = Gauge(
    'active_users',
    'Number of active users'
)

ORGANIZATION_COUNT = Gauge(
    'active_organizations',
    'Number of active organizations'
)
```

### Metrics Middleware

```python
from fastapi import Request
import time

async def metrics_middleware(request: Request, call_next):
    """Middleware to collect request metrics"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)
    
    return response

# FastAPI startup event to initialize metrics
@app.on_event("startup")
async def startup_event():
    # Initialize database connection gauge
    from app.database.session import engine
    def update_db_connections():
        ACTIVE_CONNECTIONS.set(engine.pool.checkedout())
    
    # Schedule periodic updates (in a real implementation, use a background task)
    import asyncio
    async def update_loop():
        while True:
            update_db_connections()
            await asyncio.sleep(30)  # Update every 30 seconds
    
    asyncio.create_task(update_loop())
```

### Custom Metrics Collectors

```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter

metrics_router = APIRouter(prefix="/metrics", tags=["metrics"])

@metrics_router.get("")
async def metrics_endpoint():
    """Expose Prometheus metrics"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Business metrics collectors
class BusinessMetricsCollector:
    def __init__(self, db_session):
        self.db = db_session
    
    def collect_ai_usage_metrics(self):
        """Collect AI usage metrics"""
        from app.models.ai.usage import AIUsage
        from sqlalchemy import func
        
        # Get recent AI usage grouped by model
        usage_stats = self.db.query(
            AIUsage.model,
            AIUsage.provider,
            func.count(AIUsage.id).label('request_count'),
            func.sum(AIUsage.input_tokens + AIUsage.output_tokens).label('total_tokens')
        ).group_by(AIUsage.model, AIUsage.provider).all()
        
        for stat in usage_stats:
            AI_REQUEST_COUNT.labels(
                model=stat.model,
                provider=stat.provider,
                organization_id='all'  # Aggregate
            ).inc(stat.request_count)
    
    def collect_email_metrics(self):
        """Collect email sending metrics"""
        from app.models.email.staging import StagingSnapshot
        from app.models.email.test import TestSend
        from sqlalchemy import func
        
        # Production sends (from staging snapshots marked as production)
        prod_sends = self.db.query(func.count(StagingSnapshot.id)).filter(
            StagingSnapshot.is_production == True
        ).scalar()
        
        EMAIL_SEND_COUNT.labels(
            status='production',
            provider='all',
            organization_id='all'
        ).inc(prod_sends)
        
        # Test sends
        test_sends = self.db.query(func.count(TestSend.id)).scalar()
        
        EMAIL_SEND_COUNT.labels(
            status='test',
            provider='all',
            organization_id='all'
        ).inc(test_sends)
```

## Distributed Tracing

### OpenTelemetry Integration

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

def setup_tracing(service_name: str):
    """Setup distributed tracing"""
    # Create tracer provider
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    
    # Configure OTLP exporter (for Tempo, Jaeger, etc.)
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://tempo:4317",
        insecure=True
    )
    
    # Add span processor
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Instrument FastAPI
    FastAPIInstrumentor().instrument_app(app)
    
    # Instrument SQLAlchemy
    from app.database.session import engine
    SQLAlchemyInstrumentor().instrument(engine=engine)

# Tracing utility functions
def trace_ai_request(model: str, provider: str, input_tokens: int, output_tokens: int):
    """Trace an AI request"""
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("ai_request") as span:
        span.set_attribute("ai.model", model)
        span.set_attribute("ai.provider", provider)
        span.set_attribute("ai.input_tokens", input_tokens)
        span.set_attribute("ai.output_tokens", output_tokens)
        span.set_attribute("ai.total_tokens", input_tokens + output_tokens)
        
        # Add any additional attributes or events
        if output_tokens > 1000:
            span.add_event("large_output", {"tokens": output_tokens})

def trace_email_send(staging_id: str, recipient_count: int, provider: str):
    """Trace an email send operation"""
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("email_send") as span:
        span.set_attribute("email.staging_id", staging_id)
        span.set_attribute("email.recipient_count", recipient_count)
        span.set_attribute("email.provider", provider)
```

## Dashboard Configuration

### Grafana Dashboard Example

```json
{
  "dashboard": {
    "title": "Pew Mail Operations Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}} {{status_code}}"
          }
        ]
      },
      {
        "title": "Request Duration",
        "type": "heatmap",
        "targets": [
          {
            "expr": "http_request_duration_seconds_bucket",
            "format": "heatmap"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "database_active_connections",
            "legendFormat": "Active Connections"
          }
        ]
      },
      {
        "title": "AI Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_requests_total[5m])",
            "legendFormat": "{{model}} ({{provider}})"
          }
        ]
      },
      {
        "title": "Email Sends",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(email_sends_total[5m])",
            "legendFormat": "{{status}}"
          }
        ]
      }
    ]
  }
}
```

## Alerting Configuration

### Alert Rules

```yaml
# Prometheus alert rules
groups:
- name: pewmail.alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate ({{ $value }}%)"
      description: "Error rate has been above 5% for more than 5 minutes"

  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High latency ({{ $value }}s)"
      description: "95th percentile request latency has been above 2 seconds"

  - alert: DatabaseDown
    expr: up{job="database"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database is down"
      description: "Database is not responding to health checks"

  - alert: LowDiskSpace
    expr: node_filesystem_free_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Low disk space"
      description: "Less than 10% disk space remaining"

  - alert: HighAIUsage
    expr: rate(ai_requests_total[1h]) > 1000
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High AI usage"
      description: "AI request rate has exceeded 1000 requests per hour"
```

### Alertmanager Configuration

```yaml
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'slack-notifications'

receivers:
- name: 'slack-notifications'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#alerts'
    send_resolved: true
    title: '{{ template "slack.title" . }}'
    text: '{{ template "slack.text" . }}'
```

## Environment-Specific Configuration

### Development Environment

```python
# Development logging configuration
DEVELOPMENT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}
```

### Production Environment

```python
# Production logging configuration
PRODUCTION_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'app.logging.JsonFormatter',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/pewmail/app.log',
            'maxBytes': 104857600,  # 100MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'syslog': {
            'level': 'WARNING',
            'class': 'logging.handlers.SysLogHandler',
            'address': '/dev/log',
            'formatter': 'json',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'syslog'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}
```

## Third-Party Integrations

### ELK Stack (Elasticsearch, Logstash, Kibana)

```python
# logstash configuration example
"""
input {
  file {
    path => "/var/log/pewmail/app.log"
    codec => "json"
  }
}

filter {
  json {
    source => "message"
  }
  
  date {
    match => [ "timestamp", "ISO8601" ]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "pewmail-%{+YYYY.MM.dd}"
  }
}
"""
```

### Datadog Integration

```python
import datadog

def setup_datadog():
    """Setup Datadog integration"""
    datadog.initialize(
        api_key='YOUR_API_KEY',
        app_key='YOUR_APP_KEY'
    )

def send_custom_metric(metric_name: str, value: float, tags: list = None):
    """Send custom metric to Datadog"""
    datadog.api.Metric.send(
        metric=metric_name,
        points=value,
        tags=tags or [],
        host='pewmail-backend'
    )
```

## Performance Optimization

### Profiling

```python
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    """Decorator to profile function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profiler.disable()
            
            # Save profiling results
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            stats.dump_stats(f'/tmp/profile_{func.__name__}.prof')
            
            # Log top functions
            stats.print_stats(10)  # Print top 10 functions
    
    return wrapper

# Usage
@profile_function
def complex_operation():
    # Your complex operation here
    pass
```

### Memory Monitoring

```python
import psutil
import gc

class MemoryMonitor:
    def __init__(self):
        self.process = psutil.Process()
    
    def get_memory_usage(self):
        """Get current memory usage"""
        return {
            'rss': self.process.memory_info().rss,
            'vms': self.process.memory_info().vms,
            'percent': self.process.memory_percent(),
            'garbage_collected': gc.get_stats()
        }
    
    def log_memory_usage(self, context: str = ""):
        """Log current memory usage"""
        usage = self.get_memory_usage()
        logger.info(
            f"Memory usage {context}",
            memory_rss_mb=usage['rss'] / 1024 / 1024,
            memory_vms_mb=usage['vms'] / 1024 / 1024,
            memory_percent=usage['percent']
        )
```

## Conclusion

The monitoring and observability system in Pew Mail provides comprehensive visibility into application performance, reliability, and business metrics. The system enables proactive issue detection, rapid incident response, and data-driven optimization decisions.

Key components:
1. Structured logging with security safeguards
2. Multi-level health checks
3. Error tracking and monitoring
4. Operational metrics collection
5. Distributed tracing
6. Alerting and notification systems

Implementation best practices:
1. Regular review of monitoring coverage
2. Tuning of alert thresholds
3. Performance optimization based on metrics
4. Security audit of logged data
5. Capacity planning based on usage trends
6. Integration with incident response procedures

The system is designed to be scalable and adaptable to different deployment environments while maintaining consistent observability standards.