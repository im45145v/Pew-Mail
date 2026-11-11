# Pew Mail - Billing and Subscription Management

This document outlines the billing and subscription management system for Pew Mail SaaS offering.

## Overview

Pew Mail implements a flexible subscription model with support for multiple pricing tiers and pay-as-you-go usage billing. The system is designed to be provider-agnostic, supporting multiple payment processors including Stripe and Razorpay.

## Subscription Architecture

### Plan Types

1. **Free Plan**
   - Limited features
   - Basic usage quotas
   - Community support

2. **Pro Plan**
   - Enhanced features
   - Higher usage quotas
   - Priority support

3. **Team Plan**
   - Collaborative features
   - Organization-level quotas
   - Dedicated support

4. **Enterprise Plan**
   - Custom features and quotas
   - SLA guarantees
   - Account management

### Entitlement System

The entitlement system manages feature access based on subscription status:

```python
class EntitlementService:
    def __init__(self, db_session):
        self.db = db_session
    
    def check_entitlement(self, organization_id, feature):
        """Check if an organization has access to a feature"""
        subscription = self.get_subscription(organization_id)
        plan = subscription.plan
        
        # Check plan entitlements
        if feature in plan.entitlements:
            limit = plan.entitlements[feature]
            usage = self.get_usage(organization_id, feature)
            return usage < limit if limit else True
        
        return False
    
    def get_quota_limit(self, organization_id, quota):
        """Get the quota limit for an organization"""
        subscription = self.get_subscription(organization_id)
        plan = subscription.plan
        return plan.quotas.get(quota, 0)
```

## Billing Provider Integration

### Provider Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BillingProvider(ABC):
    @abstractmethod
    def create_checkout_session(self, organization_id: str, plan_id: str, success_url: str, cancel_url: str) -> str:
        """Create a checkout session and return the session URL"""
        pass
    
    @abstractmethod
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details"""
        pass
    
    @abstractmethod
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        pass
    
    @abstractmethod
    def update_subscription_plan(self, subscription_id: str, new_plan_id: str) -> bool:
        """Update subscription plan"""
        pass
    
    @abstractmethod
    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle webhook events"""
        pass
    
    @abstractmethod
    def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Get invoice details"""
        pass
```

### Stripe Integration

```python
import stripe
from typing import Dict, Any

class StripeBillingProvider(BillingProvider):
    def __init__(self, api_key: str, webhook_secret: str):
        stripe.api_key = api_key
        self.webhook_secret = webhook_secret
    
    def create_checkout_session(self, organization_id: str, plan_id: str, success_url: str, cancel_url: str) -> str:
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': plan_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=organization_id,
                automatic_tax={'enabled': True},
            )
            return checkout_session.url
        except Exception as e:
            raise BillingError(f"Failed to create checkout session: {str(e)}")
    
    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return self.process_event(event)
        except ValueError:
            # Invalid payload
            raise BillingError("Invalid webhook payload")
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            raise BillingError("Invalid webhook signature")
    
    def process_event(self, event) -> Dict[str, Any]:
        """Process Stripe webhook events"""
        event_type = event['type']
        data = event['data']['object']
        
        if event_type == 'customer.subscription.created':
            return self.handle_subscription_created(data)
        elif event_type == 'customer.subscription.updated':
            return self.handle_subscription_updated(data)
        elif event_type == 'customer.subscription.deleted':
            return self.handle_subscription_cancelled(data)
        elif event_type == 'invoice.payment_succeeded':
            return self.handle_payment_succeeded(data)
        elif event_type == 'invoice.payment_failed':
            return self.handle_payment_failed(data)
        
        return {'status': 'ignored', 'event_type': event_type}
```

### Razorpay Integration

```python
import razorpay
from typing import Dict, Any

class RazorpayBillingProvider(BillingProvider):
    def __init__(self, key_id: str, key_secret: str):
        self.client = razorpay.Client(auth=(key_id, key_secret))
    
    def create_checkout_session(self, organization_id: str, plan_id: str, success_url: str, cancel_url: str) -> str:
        try:
            # Create subscription
            subscription = self.client.subscription.create({
                'plan_id': plan_id,
                'customer_notify': 1,
                'notes': {
                    'organization_id': organization_id
                }
            })
            
            # Create receipt for subscription
            receipt_data = {
                'subscription_id': subscription['id'],
                'organization_id': organization_id,
                'success_url': success_url,
                'cancel_url': cancel_url
            }
            
            # In a real implementation, you would store this receipt
            # and return a URL that can process the subscription
            return f"/billing/razorpay/checkout/{subscription['id']}"
        except Exception as e:
            raise BillingError(f"Failed to create checkout session: {str(e)}")
```

### Mock Provider (for development/testing)

```python
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

class MockBillingProvider(BillingProvider):
    def __init__(self):
        self.subscriptions = {}
        self.invoices = {}
    
    def create_checkout_session(self, organization_id: str, plan_id: str, success_url: str, cancel_url: str) -> str:
        # Simulate successful checkout
        subscription_id = f"sub_{uuid.uuid4().hex[:12]}"
        self.subscriptions[subscription_id] = {
            'id': subscription_id,
            'organization_id': organization_id,
            'plan_id': plan_id,
            'status': 'active',
            'created_at': datetime.utcnow(),
            'current_period_start': datetime.utcnow(),
            'current_period_end': datetime.utcnow() + timedelta(days=30),
        }
        return success_url + f"?session_id={subscription_id}"
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        return self.subscriptions.get(subscription_id, {})
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]['status'] = 'cancelled'
            return True
        return False
    
    def update_subscription_plan(self, subscription_id: str, new_plan_id: str) -> bool:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]['plan_id'] = new_plan_id
            return True
        return False
    
    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        # Mock webhook handling
        return {'status': 'processed'}
    
    def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        return self.invoices.get(invoice_id, {})
```

## Usage Metering

### Usage Tracking

```python
from sqlalchemy import Column, String, Integer, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from datetime import datetime

class UsageRecord(BaseModel):
    __tablename__ = "usage_records"
    
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    usage_type = Column(String, nullable=False, index=True)  # ai_tokens, email_sends, storage, etc.
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=True)  # Optional, if cost is known
    currency = Column(String(3), nullable=True)  # USD, EUR, etc.
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)  # Related resource if applicable
    provider = Column(String, nullable=True)  # AI provider, email service, etc.
    metadata = Column(String, nullable=True)  # Additional JSON metadata

class UsageService:
    def __init__(self, db_session):
        self.db = db_session
    
    def record_usage(self, organization_id: str, usage_type: str, quantity: int, 
                     user_id: str = None, resource_id: str = None, provider: str = None):
        """Record usage for an organization"""
        usage_record = UsageRecord(
            organization_id=organization_id,
            user_id=user_id,
            usage_type=usage_type,
            quantity=quantity,
            resource_id=resource_id,
            provider=provider
        )
        self.db.add(usage_record)
        self.db.commit()
        
        # Check if usage exceeds quota
        self.check_quota_thresholds(organization_id, usage_type, quantity)
    
    def get_usage_report(self, organization_id: str, start_date: datetime, end_date: datetime):
        """Generate usage report for an organization"""
        from sqlalchemy import func, and_
        
        result = self.db.query(
            UsageRecord.usage_type,
            func.sum(UsageRecord.quantity).label('total_quantity'),
            func.avg(UsageRecord.unit_cost).label('avg_unit_cost'),
            func.sum(UsageRecord.quantity * UsageRecord.unit_cost).label('total_cost')
        ).filter(
            and_(
                UsageRecord.organization_id == organization_id,
                UsageRecord.timestamp >= start_date,
                UsageRecord.timestamp <= end_date
            )
        ).group_by(UsageRecord.usage_type).all()
        
        return result
    
    def check_quota_thresholds(self, organization_id: str, usage_type: str, quantity: int):
        """Check if usage is approaching quota thresholds"""
        entitlement_service = EntitlementService(self.db)
        quota_limit = entitlement_service.get_quota_limit(organization_id, usage_type)
        
        if quota_limit > 0:
            current_usage = self.get_current_usage(organization_id, usage_type)
            percentage_used = (current_usage / quota_limit) * 100
            
            # Send warning notifications at thresholds
            if percentage_used >= 90 and percentage_used < 95:
                self.send_quota_warning(organization_id, usage_type, percentage_used)
            elif percentage_used >= 95:
                self.send_quota_exceeded(organization_id, usage_type, percentage_used)
```

### Quota Management

```python
class QuotaService:
    def __init__(self, db_session):
        self.db = db_session
        self.usage_service = UsageService(db_session)
        self.entitlement_service = EntitlementService(db_session)
    
    def check_quota(self, organization_id: str, quota_type: str, requested_amount: int = 1) -> bool:
        """Check if an organization has sufficient quota for a request"""
        # Get quota limit for the organization
        quota_limit = self.entitlement_service.get_quota_limit(organization_id, quota_type)
        
        # If no limit is set, allow unlimited usage
        if quota_limit is None or quota_limit == 0:
            return True
        
        # Get current usage
        current_usage = self.usage_service.get_current_usage(organization_id, quota_type)
        
        # Check if requested amount would exceed quota
        return (current_usage + requested_amount) <= quota_limit
    
    def reserve_quota(self, organization_id: str, quota_type: str, amount: int) -> bool:
        """Reserve quota for a pending operation"""
        # This is a simplified reservation system
        # A more complex system might use database locks or distributed locks
        return self.check_quota(organization_id, quota_type, amount)
    
    def release_quota(self, organization_id: str, quota_type: str, amount: int):
        """Release reserved quota (in case of operation failure)"""
        # In this simple implementation, we don't actually reserve quota
        # A more complex system would track reservations
        pass
```

## Plan Configuration

### Plan Definitions

```python
class Plan:
    def __init__(self, id, name, price, interval, currency, entitlements, quotas):
        self.id = id
        self.name = name
        self.price = price
        self.interval = interval  # monthly, annual
        self.currency = currency
        self.entitlements = entitlements
        self.quotas = quotas

# Default plans configuration
PLANS = {
    'free': Plan(
        id='free',
        name='Free',
        price=0,
        interval='monthly',
        currency='USD',
        entitlements={
            'email_editor': True,
            'basic_ai': True,
            'test_sending': True,
            'google_integration': True,
        },
        quotas={
            'projects': 3,
            'templates': 10,
            'contacts': 1000,
            'test_sends_per_day': 10,
            'ai_tokens_per_month': 5000,
            'storage_mb': 100,
        }
    ),
    'pro': Plan(
        id='pro_monthly',
        name='Pro',
        price=29,
        interval='monthly',
        currency='USD',
        entitlements={
            'email_editor': True,
            'advanced_ai': True,
            'test_sending': True,
            'google_integration': True,
            'custom_domains': True,
            'priority_support': True,
        },
        quotas={
            'projects': 20,
            'templates': 100,
            'contacts': 10000,
            'test_sends_per_day': 100,
            'ai_tokens_per_month': 50000,
            'storage_mb': 1000,
        }
    ),
    'team': Plan(
        id='team_monthly',
        name='Team',
        price=99,
        interval='monthly',
        currency='USD',
        entitlements={
            'email_editor': True,
            'advanced_ai': True,
            'test_sending': True,
            'google_integration': True,
            'custom_domains': True,
            'priority_support': True,
            'team_collaboration': True,
            'campaign_analytics': True,
            'shared_templates': True,
        },
        quotas={
            'projects': 100,
            'templates': 500,
            'contacts': 100000,
            'test_sends_per_day': 1000,
            'ai_tokens_per_month': 250000,
            'storage_mb': 10000,
            'team_members': 25,
        }
    )
}
```

## Webhook Handling

### Idempotent Webhook Processing

```python
import hashlib
import hmac
from typing import Dict, Any

class WebhookProcessor:
    def __init__(self, db_session):
        self.db = db_session
        self.processed_events = set()  # In production, use Redis or database
    
    def process_webhook(self, payload: bytes, signature: str, provider: str) -> Dict[str, Any]:
        """Process webhook with idempotency protection"""
        # Generate event ID from payload to detect duplicates
        event_id = hashlib.sha256(payload).hexdigest()
        
        # Check if event was already processed
        if event_id in self.processed_events:
            return {'status': 'duplicate', 'event_id': event_id}
        
        # Verify webhook signature
        if not self.verify_signature(payload, signature, provider):
            raise SecurityError("Invalid webhook signature")
        
        # Parse payload
        event_data = self.parse_payload(payload, provider)
        
        # Process event
        result = self.handle_event(event_data, provider)
        
        # Mark event as processed
        self.processed_events.add(event_id)
        
        return {'status': 'processed', 'event_id': event_id, 'result': result}
    
    def verify_signature(self, payload: bytes, signature: str, provider: str) -> bool:
        """Verify webhook signature"""
        if provider == 'stripe':
            return self.verify_stripe_signature(payload, signature)
        elif provider == 'razorpay':
            return self.verify_razorpay_signature(payload, signature)
        return True  # Mock provider
    
    def verify_stripe_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        # Implementation would use stripe.Webhook.construct_event
        # This is simplified for illustration
        expected_signature = hmac.new(
            STRIPE_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
```

## Error Handling and Retry Logic

### Payment Failure Handling

```python
import time
from datetime import datetime, timedelta

class PaymentErrorHandler:
    def __init__(self, db_session, billing_provider):
        self.db = db_session
        self.billing_provider = billing_provider
    
    def handle_payment_failure(self, subscription_id: str, failure_reason: str):
        """Handle payment failure for a subscription"""
        subscription = self.billing_provider.get_subscription(subscription_id)
        
        # Record the failure
        failure_record = PaymentFailure(
            subscription_id=subscription_id,
            failure_reason=failure_reason,
            timestamp=datetime.utcnow()
        )
        self.db.add(failure_record)
        self.db.commit()
        
        # Check failure count
        failure_count = self.get_recent_failure_count(subscription_id)
        
        # Take appropriate action based on failure count
        if failure_count == 1:
            # First failure - send notification
            self.send_first_failure_notification(subscription['organization_id'])
        elif failure_count == 2:
            # Second failure - send urgent notification
            self.send_second_failure_notification(subscription['organization_id'])
        elif failure_count >= 3:
            # Third failure - suspend service
            self.suspend_service(subscription['organization_id'])
            
            # Cancel subscription if grace period expired
            if self.grace_period_expired(subscription_id):
                self.cancel_subscription(subscription_id)
    
    def retry_payment(self, subscription_id: str):
        """Attempt to retry payment for a failed subscription"""
        try:
            # In a real implementation, this would trigger a new payment attempt
            # For now, we'll just log the retry attempt
            retry_record = PaymentRetry(
                subscription_id=subscription_id,
                timestamp=datetime.utcnow()
            )
            self.db.add(retry_record)
            self.db.commit()
            
            return True
        except Exception as e:
            # Log the retry failure
            error_record = PaymentRetryError(
                subscription_id=subscription_id,
                error_message=str(e),
                timestamp=datetime.utcnow()
            )
            self.db.add(error_record)
            self.db.commit()
            
            return False
```

## Configuration

### Environment Variables

```bash
# Billing Provider Configuration
BILLING_PROVIDER=mock  # mock, stripe, razorpay
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXXXXXXXXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### Configuration Service

```python
from app.core.config import settings

class BillingConfig:
    @staticmethod
    def get_provider():
        """Get the configured billing provider"""
        provider_map = {
            'stripe': StripeBillingProvider,
            'razorpay': RazorpayBillingProvider,
            'mock': MockBillingProvider
        }
        
        provider_class = provider_map.get(settings.BILLING_PROVIDER)
        if not provider_class:
            raise ConfigurationError(f"Unsupported billing provider: {settings.BILLING_PROVIDER}")
        
        if settings.BILLING_PROVIDER == 'stripe':
            return StripeBillingProvider(
                api_key=settings.STRIPE_SECRET_KEY,
                webhook_secret=settings.STRIPE_WEBHOOK_SECRET
            )
        elif settings.BILLING_PROVIDER == 'razorpay':
            return RazorpayBillingProvider(
                key_id=settings.RAZORPAY_KEY_ID,
                key_secret=settings.RAZORPAY_KEY_SECRET
            )
        else:
            return MockBillingProvider()
    
    @staticmethod
    def get_plans():
        """Get available plans"""
        return PLANS
```

## Security Considerations

### Webhook Security

1. **Signature Verification**:
   - Always verify webhook signatures
   - Use provider-specific verification methods
   - Reject unverifiable webhooks

2. **Idempotency**:
   - Process each event only once
   - Use event IDs to detect duplicates
   - Handle concurrent processing

3. **Data Validation**:
   - Validate all webhook data
   - Sanitize incoming data
   - Use type-safe parsing

### PCI Compliance

1. **Tokenization**:
   - Never store raw credit card data
   - Use provider tokenization services
   - Implement proper encryption for sensitive data

2. **Data Minimization**:
   - Collect only necessary payment data
   - Retain data only as long as required
   - Implement proper data deletion

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from app.billing.service import BillingService
from app.billing.providers.mock import MockBillingProvider

class TestBillingService:
    def setup_method(self):
        self.billing_provider = MockBillingProvider()
        self.billing_service = BillingService(self.billing_provider)
    
    def test_create_checkout_session(self):
        organization_id = "org_123"
        plan_id = "pro_monthly"
        success_url = "https://example.com/success"
        cancel_url = "https://example.com/cancel"
        
        session_url = self.billing_service.create_checkout_session(
            organization_id, plan_id, success_url, cancel_url
        )
        
        assert success_url in session_url
        assert "?session_id=" in session_url
    
    def test_handle_webhook_success(self):
        payload = b'{"type": "test.event", "data": {}}'
        signature = "test_signature"
        
        result = self.billing_service.handle_webhook(payload, signature)
        
        assert result['status'] == 'processed'
```

## Monitoring and Metrics

### Key Metrics to Track

1. **Subscription Metrics**:
   - New subscriptions
   - Churn rate
   - Upgrade/downgrade rates
   - Revenue recognition

2. **Payment Metrics**:
   - Payment success rate
   - Payment failure reasons
   - Retry success rates
   - Chargeback rates

3. **Usage Metrics**:
   - Feature adoption
   - Quota utilization
   - Usage patterns
   - Resource consumption

## Conclusion

The billing system in Pew Mail is designed to be flexible, secure, and scalable. It supports multiple billing providers, provides comprehensive usage tracking, and implements robust error handling. The system enforces entitlements at the API level to ensure secure access control.

Key features:
1. Provider-agnostic billing interface
2. Flexible subscription plans
3. Granular entitlement management
4. Comprehensive usage tracking
5. Robust error handling and retry logic
6. Secure webhook processing
7. Extensive monitoring and metrics

Implementation considerations:
1. Thorough testing of payment flows
2. Regular security audits
3. Monitoring of payment success rates
4. Customer support for billing inquiries
5. Compliance with financial regulations