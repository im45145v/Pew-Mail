# Pew Mail - AI Usage and Cost Control

This document outlines the AI usage management and cost control mechanisms implemented in Pew Mail to ensure responsible and predictable AI spending.

## Overview

Pew Mail implements comprehensive AI usage controls to prevent unexpected costs while providing flexibility for different subscription tiers. The system tracks usage, enforces quotas, and provides cost estimation capabilities.

## AI Provider Abstraction

### Provider Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class AIModelConfig:
    provider: str
    model: str
    base_url: str
    api_key_ref: str
    enabled: bool
    organization_allowed: Optional[List[str]] = None
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None

class AIProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using the AI model"""
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """Count tokens in text"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information including pricing"""
        pass

class OpenAIProvider(AIProvider):
    def __init__(self, config: AIModelConfig):
        self.config = config
        self.client = openai.OpenAI(
            api_key=config.api_key_ref,
            base_url=config.base_url
        )
    
    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            return {
                'text': response.choices[0].message.content,
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'model': self.config.model,
                'provider': self.config.provider
            }
        except Exception as e:
            raise AIError(f"Failed to generate text: {str(e)}")
    
    def get_token_count(self, text: str) -> int:
        # Simplified token counting
        # In practice, you might use tiktoken or similar
        return len(text.split()) * 1.3  # Rough approximation
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            'provider': self.config.provider,
            'model': self.config.model,
            'cost_per_1k_input_tokens': self.config.cost_per_1k_input_tokens,
            'cost_per_1k_output_tokens': self.config.cost_per_1k_output_tokens
        }
```

### Provider Configuration

```python
# ai/providers.py
from typing import Dict, List
import os

class AIProviderManager:
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self.models: Dict[str, AIModelConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """Load AI provider configuration from environment"""
        # OpenAI Configuration
        if os.getenv('OPENAI_API_KEY'):
            openai_config = AIModelConfig(
                provider='openai',
                model=os.getenv('AI_MODEL', 'gpt-4'),
                base_url=os.getenv('AI_PROVIDER_URL', 'https://api.openai.com/v1'),
                api_key_ref=os.getenv('OPENAI_API_KEY'),
                enabled=os.getenv('OPENAI_ENABLED', 'true').lower() == 'true',
                cost_per_1k_input_tokens=0.03,  # GPT-4 pricing
                cost_per_1k_output_tokens=0.06
            )
            self.models['openai'] = openai_config
            self.providers['openai'] = OpenAIProvider(openai_config)
        
        # Anthropic Configuration
        if os.getenv('ANTHROPIC_API_KEY'):
            anthropic_config = AIModelConfig(
                provider='anthropic',
                model=os.getenv('ANTHROPIC_MODEL', 'claude-3-opus'),
                base_url=os.getenv('ANTHROPIC_PROVIDER_URL', 'https://api.anthropic.com'),
                api_key_ref=os.getenv('ANTHROPIC_API_KEY'),
                enabled=os.getenv('ANTHROPIC_ENABLED', 'true').lower() == 'true',
                cost_per_1k_input_tokens=0.015,  # Claude-3 Opus pricing
                cost_per_1k_output_tokens=0.075
            )
            self.models['anthropic'] = anthropic_config
            self.providers['anthropic'] = AnthropicProvider(anthropic_config)
    
    def get_provider(self, provider_name: str) -> AIProvider:
        """Get AI provider by name"""
        if provider_name not in self.providers:
            raise ConfigurationError(f"AI provider '{provider_name}' not configured")
        return self.providers[provider_name]
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return list(self.models.keys())
    
    def is_model_enabled(self, model_name: str) -> bool:
        """Check if model is enabled"""
        return self.models.get(model_name, {}).get('enabled', False)
```

## Usage Quotas and Limits

### Quota System

```python
from sqlalchemy import Column, String, Integer, DateTime, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from datetime import datetime

class AIQuota(BaseModel):
    __tablename__ = "ai_quotas"
    
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    plan_id = Column(String, nullable=False)
    monthly_token_limit = Column(Integer, nullable=False)  # Total tokens per month
    daily_request_limit = Column(Integer, nullable=False)  # Requests per day
    max_input_tokens = Column(Integer, nullable=False)  # Max tokens per input
    max_output_tokens = Column(Integer, nullable=False)  # Max tokens per output
    allowed_models = Column(String, nullable=False)  # Comma-separated list
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class AIUsage(BaseModel):
    __tablename__ = "ai_usage"
    
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    model = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    requests = Column(Integer, nullable=False, default=1)
    estimated_cost = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)  # Related resource
```

### Quota Enforcement Service

```python
from datetime import datetime, timedelta
from sqlalchemy import and_, func

class AIQuotaService:
    def __init__(self, db_session):
        self.db = db_session
    
    def check_quota(self, organization_id: str, model: str, input_tokens: int, 
                   output_tokens: int = 0) -> bool:
        """Check if an organization has sufficient AI quota"""
        # Get organization quota
        quota = self.db.query(AIQuota).filter(
            and_(
                AIQuota.organization_id == organization_id,
                AIQuota.is_active == True
            )
        ).first()
        
        if not quota:
            return False  # No quota configured
        
        # Check if model is allowed
        allowed_models = quota.allowed_models.split(',')
        if model not in allowed_models:
            return False
        
        # Check input token limit
        if input_tokens > quota.max_input_tokens:
            raise QuotaError(f"Input tokens ({input_tokens}) exceed limit ({quota.max_input_tokens})")
        
        # Check output token limit
        if output_tokens > quota.max_output_tokens:
            raise QuotaError(f"Output tokens ({output_tokens}) exceed limit ({quota.max_output_tokens})")
        
        # Check daily request limit
        today = datetime.utcnow().date()
        start_of_day = datetime(today.year, today.month, today.day)
        daily_requests = self.db.query(func.sum(AIUsage.requests)).filter(
            and_(
                AIUsage.organization_id == organization_id,
                AIUsage.timestamp >= start_of_day
            )
        ).scalar() or 0
        
        if daily_requests >= quota.daily_request_limit:
            raise QuotaError(f"Daily request limit ({quota.daily_request_limit}) exceeded")
        
        # Check monthly token limit
        start_of_month = datetime(today.year, today.month, 1)
        monthly_tokens = self.db.query(
            func.sum(AIUsage.input_tokens + AIUsage.output_tokens)
        ).filter(
            and_(
                AIUsage.organization_id == organization_id,
                AIUsage.timestamp >= start_of_month
            )
        ).scalar() or 0
        
        requested_tokens = input_tokens + output_tokens
        if (monthly_tokens + requested_tokens) > quota.monthly_token_limit:
            raise QuotaError(f"Monthly token limit ({quota.monthly_token_limit}) would be exceeded")
        
        return True
    
    def record_usage(self, organization_id: str, user_id: str, model: str, provider: str,
                    input_tokens: int, output_tokens: int, resource_id: str = None):
        """Record AI usage"""
        # Calculate estimated cost
        estimated_cost = self.calculate_cost(provider, model, input_tokens, output_tokens)
        
        usage_record = AIUsage(
            organization_id=organization_id,
            user_id=user_id,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
            resource_id=resource_id
        )
        
        self.db.add(usage_record)
        self.db.commit()
        
        # Check if approaching quota limits
        self.check_quota_thresholds(organization_id)
    
    def calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost for AI usage"""
        # In a real implementation, you would get pricing from the provider config
        provider_manager = AIProviderManager()
        model_config = provider_manager.models.get(provider)
        
        if not model_config or not model_config.cost_per_1k_input_tokens:
            return 0.0  # No pricing information available
        
        input_cost = (input_tokens / 1000) * model_config.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000) * model_config.cost_per_1k_output_tokens
        
        return input_cost + output_cost
    
    def check_quota_thresholds(self, organization_id: str):
        """Check if organization is approaching quota thresholds"""
        quota = self.db.query(AIQuota).filter(
            and_(
                AIQuota.organization_id == organization_id,
                AIQuota.is_active == True
            )
        ).first()
        
        if not quota:
            return
        
        # Check monthly usage
        today = datetime.utcnow().date()
        start_of_month = datetime(today.year, today.month, 1)
        monthly_tokens = self.db.query(
            func.sum(AIUsage.input_tokens + AIUsage.output_tokens)
        ).filter(
            and_(
                AIUsage.organization_id == organization_id,
                AIUsage.timestamp >= start_of_month
            )
        ).scalar() or 0
        
        percentage_used = (monthly_tokens / quota.monthly_token_limit) * 100
        
        # Send warnings at threshold levels
        if percentage_used >= 80 and percentage_used < 90:
            self.send_quota_warning(organization_id, 'monthly_tokens', percentage_used)
        elif percentage_used >= 90 and percentage_used < 95:
            self.send_quota_warning(organization_id, 'monthly_tokens', percentage_used)
        elif percentage_used >= 95:
            self.send_quota_exceeded(organization_id, 'monthly_tokens', percentage_used)
```

## Rate Limiting

### API Rate Limiting

```python
import time
import redis
from functools import wraps
from typing import Callable

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed under rate limit"""
        current_time = int(time.time())
        pipeline = self.redis.pipeline()
        
        # Remove old entries
        pipeline.zremrangebyscore(key, 0, current_time - window)
        
        # Count current requests
        pipeline.zcard(key)
        
        # Add current request
        pipeline.zadd(key, {str(current_time): current_time})
        
        # Set expiration
        pipeline.expire(key, window)
        
        results = pipeline.execute()
        request_count = results[1]
        
        return request_count < limit
    
    def rate_limit(self, limit: int, window: int, key_prefix: str = "rate_limit"):
        """Decorator for rate limiting"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate key based on function and arguments
                key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                if not self.is_allowed(key, limit, window):
                    raise RateLimitError(f"Rate limit exceeded: {limit} requests per {window} seconds")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator

# Usage example
rate_limiter = RateLimiter(redis_client)

@rate_limiter.rate_limit(limit=100, window=3600, key_prefix="ai_generate")
def generate_email_content(prompt: str, organization_id: str):
    """Generate email content with rate limiting"""
    # AI generation logic here
    pass
```

## Cost Estimation and Reporting

### Cost Tracking Service

```python
from datetime import datetime, timedelta
from sqlalchemy import and_, func

class AICostTrackingService:
    def __init__(self, db_session):
        self.db = db_session
        self.quota_service = AIQuotaService(db_session)
    
    def get_cost_breakdown(self, organization_id: str, start_date: datetime, end_date: datetime):
        """Get detailed cost breakdown for an organization"""
        results = self.db.query(
            AIUsage.provider,
            AIUsage.model,
            func.sum(AIUsage.input_tokens).label('total_input_tokens'),
            func.sum(AIUsage.output_tokens).label('total_output_tokens'),
            func.sum(AIUsage.estimated_cost).label('total_cost'),
            func.count(AIUsage.id).label('request_count')
        ).filter(
            and_(
                AIUsage.organization_id == organization_id,
                AIUsage.timestamp >= start_date,
                AIUsage.timestamp <= end_date
            )
        ).group_by(AIUsage.provider, AIUsage.model).all()
        
        return results
    
    def get_daily_costs(self, organization_id: str, days: int = 30):
        """Get daily cost trends"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        results = self.db.query(
            func.date(AIUsage.timestamp).label('date'),
            func.sum(AIUsage.estimated_cost).label('daily_cost'),
            func.sum(AIUsage.input_tokens + AIUsage.output_tokens).label('daily_tokens')
        ).filter(
            and_(
                AIUsage.organization_id == organization_id,
                AIUsage.timestamp >= start_date,
                AIUsage.timestamp <= end_date
            )
        ).group_by(func.date(AIUsage.timestamp)).order_by(func.date(AIUsage.timestamp)).all()
        
        return results
    
    def get_top_users(self, organization_id: str, limit: int = 10):
        """Get top users by AI usage"""
        results = self.db.query(
            AIUsage.user_id,
            func.sum(AIUsage.estimated_cost).label('total_cost'),
            func.sum(AIUsage.input_tokens + AIUsage.output_tokens).label('total_tokens'),
            func.count(AIUsage.id).label('request_count')
        ).filter(
            AIUsage.organization_id == organization_id
        ).group_by(AIUsage.user_id).order_by(func.sum(AIUsage.estimated_cost).desc()).limit(limit).all()
        
        return results
```

## Abuse Prevention

### Usage Anomaly Detection

```python
import numpy as np
from datetime import datetime, timedelta

class AIAbuseDetection:
    def __init__(self, db_session):
        self.db = db_session
    
    def detect_anomalies(self, organization_id: str):
        """Detect anomalous AI usage patterns"""
        # Get recent usage data
        recent_period = datetime.utcnow() - timedelta(hours=24)
        usage_data = self.db.query(AIUsage).filter(
            and_(
                AIUsage.organization_id == organization_id,
                AIUsage.timestamp >= recent_period
            )
        ).order_by(AIUsage.timestamp).all()
        
        if len(usage_data) < 10:  # Need minimum data points
            return []
        
        # Analyze patterns
        anomalies = []
        
        # Check for sudden spikes in usage
        token_counts = [u.input_tokens + u.output_tokens for u in usage_data]
        mean_tokens = np.mean(token_counts)
        std_tokens = np.std(token_counts)
        
        for i, usage in enumerate(usage_data):
            total_tokens = usage.input_tokens + usage.output_tokens
            if total_tokens > (mean_tokens + 3 * std_tokens):  # 3-sigma rule
                anomalies.append({
                    'type': 'usage_spike',
                    'usage_id': usage.id,
                    'timestamp': usage.timestamp,
                    'tokens': total_tokens,
                    'threshold': mean_tokens + 3 * std_tokens
                })
        
        # Check for repeated identical requests (copy-paste abuse)
        request_texts = {}
        for usage in usage_data:
            # This would require storing request content
            # Simplified for illustration
            pass
        
        return anomalies
    
    def handle_anomaly(self, organization_id: str, anomaly: dict):
        """Handle detected anomaly"""
        if anomaly['type'] == 'usage_spike':
            # Temporarily reduce quotas
            self.temp_reduce_quota(organization_id, duration_minutes=60)
            
            # Send alert to admins
            self.send_abuse_alert(organization_id, anomaly)
            
            # Log the event
            self.log_abuse_event(organization_id, anomaly)
```

## Configuration

### Environment Variables

```bash
# AI Provider Configuration
AI_PROVIDER=openai
AI_MODEL=gpt-4
AI_PROVIDER_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
ANTHROPIC_API_KEY=sk-ant-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# AI Usage Limits (per organization per month)
AI_QUOTA_LIMIT=100000  # tokens
AI_DAILY_RATE_LIMIT=1000  # requests per day
AI_MAX_INPUT_TOKENS=4000
AI_MAX_OUTPUT_TOKENS=1000

# Rate Limiting Configuration
AI_RATE_LIMIT_WINDOW=3600  # 1 hour
AI_RATE_LIMIT_REQUESTS=100  # per window

# Cost Tracking
AI_COST_TRACKING_ENABLED=true
AI_COST_ALERT_THRESHOLD=50.00  # USD
```

### Plan-Based Quotas

```python
# Default quota configurations by plan
DEFAULT_QUOTAS = {
    'free': {
        'monthly_token_limit': 50000,
        'daily_request_limit': 50,
        'max_input_tokens': 2000,
        'max_output_tokens': 500,
        'allowed_models': 'openai:gpt-3.5-turbo'
    },
    'pro': {
        'monthly_token_limit': 500000,
        'daily_request_limit': 500,
        'max_input_tokens': 8000,
        'max_output_tokens': 2000,
        'allowed_models': 'openai:gpt-4,openai:gpt-3.5-turbo,anthropic:claude-3-haiku'
    },
    'team': {
        'monthly_token_limit': 2000000,
        'daily_request_limit': 2000,
        'max_input_tokens': 16000,
        'max_output_tokens': 4000,
        'allowed_models': 'openai:gpt-4,openai:gpt-4-turbo,anthropic:claude-3-opus,anthropic:claude-3-sonnet'
    }
}
```

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Usage Metrics**:
   - Daily/Monthly token consumption
   - Request volume by model
   - Average tokens per request
   - Usage by organization/user

2. **Cost Metrics**:
   - Daily/Monthly AI spending
   - Cost per model
   - ROI by feature/application

3. **Performance Metrics**:
   - Response times
   - Error rates
   - Retry rates

4. **Abuse Detection**:
   - Anomalous usage patterns
   - Spike detection
   - Repeat request detection

### Alerting System

```python
class AIAlertingService:
    def __init__(self, db_session):
        self.db = db_session
    
    def check_thresholds(self):
        """Check all AI usage thresholds"""
        organizations = self.db.query(Organization).all()
        
        for org in organizations:
            self.check_organization_thresholds(org.id)
    
    def check_organization_thresholds(self, organization_id: str):
        """Check thresholds for a specific organization"""
        # Check 80%, 90%, 95% usage thresholds
        quota_service = AIQuotaService(self.db)
        cost_service = AICostTrackingService(self.db)
        
        # Monthly usage check
        today = datetime.utcnow().date()
        start_of_month = datetime(today.year, today.month, 1)
        monthly_tokens = cost_service.get_monthly_tokens(organization_id)
        quota = quota_service.get_quota(organization_id)
        
        if quota:
            percentage = (monthly_tokens / quota.monthly_token_limit) * 100
            
            if percentage >= 95:
                self.send_alert(organization_id, 'quota_critical', percentage)
            elif percentage >= 90:
                self.send_alert(organization_id, 'quota_high', percentage)
            elif percentage >= 80:
                self.send_alert(organization_id, 'quota_warning', percentage)
```

## Security Considerations

### Input Validation

```python
import re

class AIInputValidator:
    def __init__(self):
        self.max_length = 50000  # 50KB limit
        self.dangerous_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
        ]
    
    def validate_input(self, text: str) -> bool:
        """Validate AI input for security"""
        # Length check
        if len(text) > self.max_length:
            raise ValidationError(f"Input too long: {len(text)} characters")
        
        # Content checks
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValidationError(f"Dangerous content detected: {pattern}")
        
        return True
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize input for AI processing"""
        # Remove or escape dangerous content
        sanitized = text
        for pattern in self.dangerous_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized
```

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from app.ai.quota_service import AIQuotaService
from app.ai.cost_tracking import AICostTrackingService

class TestAIQuotaService:
    def setup_method(self):
        self.db_session = Mock()
        self.quota_service = AIQuotaService(self.db_session)
    
    def test_check_quota_within_limits(self):
        # Mock quota configuration
        mock_quota = Mock()
        mock_quota.monthly_token_limit = 100000
        mock_quota.daily_request_limit = 1000
        mock_quota.max_input_tokens = 8000
        mock_quota.max_output_tokens = 2000
        mock_quota.allowed_models = "openai:gpt-4"
        
        self.db_session.query().filter().first.return_value = mock_quota
        self.db_session.query().filter().scalar.return_value = 50000  # Current usage
        
        # Should allow usage within limits
        result = self.quota_service.check_quota("org_123", "openai:gpt-4", 1000, 500)
        assert result == True
    
    def test_check_quota_exceeds_limit(self):
        # Mock quota configuration
        mock_quota = Mock()
        mock_quota.monthly_token_limit = 100000
        mock_quota.daily_request_limit = 1000
        mock_quota.max_input_tokens = 8000
        mock_quota.max_output_tokens = 2000
        mock_quota.allowed_models = "openai:gpt-4"
        
        self.db_session.query().filter().first.return_value = mock_quota
        self.db_session.query().filter().scalar.return_value = 99000  # Near limit
        
        # Should reject usage that exceeds limit
        with pytest.raises(QuotaError):
            self.quota_service.check_quota("org_123", "openai:gpt-4", 2000, 1000)
```

## Conclusion

The AI usage and cost control system in Pew Mail provides comprehensive management of AI resources with multiple layers of protection against unexpected costs. The system combines quota enforcement, rate limiting, cost tracking, and abuse detection to ensure responsible AI usage.

Key features:
1. Provider-agnostic AI interface
2. Flexible quota system by subscription plan
3. Real-time usage tracking and cost estimation
4. Rate limiting to prevent abuse
5. Anomaly detection for unusual usage patterns
6. Comprehensive monitoring and alerting
7. Security-focused input validation

Implementation considerations:
1. Regular monitoring of AI spending
2. Adjustment of quotas based on usage patterns
3. Clear communication of limits to users
4. Graceful degradation when quotas are exceeded
5. Integration with billing system for overage charges