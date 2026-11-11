# Pew Mail Provider Events Documentation

## Overview
Provider events represent individual delivery events reported by email providers. This system enables Pew Mail to track email performance across different delivery channels.

## Event Model

### Core Fields
- `provider_reference` - Unique identifier from the provider
- `source` - Email provider that generated the event
- `event_type` - Type of delivery event
- `timestamp` - When the event occurred
- `recipient` - Email address of the recipient
- `metadata` - Additional provider-specific data
- `processed_at` - When Pew Mail processed the event
- `is_processed` - Processing status flag

### Event Types
1. **Delivery Requested** - Send request submitted to provider
2. **Provider Accepted** - Provider accepted the send request
3. **Delivered** - Confirmed delivery to recipient's mail server
4. **Bounced** - Rejected by recipient's mail server
5. **Opened** - Recipient opened the email (tracking required)
6. **Clicked** - Recipient clicked links (tracking required)
7. **Failed** - Technical failure during delivery
8. **Complained** - Recipient marked as spam

### Provider Sources
1. **Google Gmail** - Native integration
2. **Amazon SES** - Planned integration
3. **SendGrid** - Planned integration
4. **Mailgun** - Planned integration
5. **Postmark** - Planned integration

## Webhook Integration

### Security Measures
- HMAC signature verification
- Timestamp validation (5-minute window)
- Replay attack prevention
- Provider IP whitelisting (where available)

### Endpoint Structure
Webhooks are received at provider-specific endpoints:
- `/api/v1/webhooks/google-gmail`
- `/api/v1/webhooks/amazon-ses`
- `/api/v1/webhooks/sendgrid`
- `/api/v1/webhooks/mailgun`
- `/api/v1/webhooks/postmark`

### Request Processing
1. Validate webhook signature
2. Parse event data
3. Store in `ProviderEvent` table
4. Queue for processing
5. Return HTTP 200 OK

## Event Processing

### Idempotency
- Events identified by `provider_reference` + `source`
- Duplicate events ignored
- Processing state tracked in `is_processed` flag

### Data Transformation
- Provider event formats normalized
- Timestamps standardized
- Recipient addresses validated
- Metadata preserved for debugging

### Aggregate Updates
Processed events update `EmailAnalyticsAggregate`:
- Increment appropriate counter
- Maintain data consistency
- Handle failed updates gracefully

## Supported Providers

### Google Gmail
**Current Status**: Implemented
**Event Types Supported**:
- Delivery Requested
- Provider Accepted
- Failed

**Limitations**:
- No delivery confirmation (Gmail API limitation)
- No open/click tracking (privacy considerations)

### Amazon SES
**Current Status**: Planned
**Expected Event Types**:
- Delivery Requested
- Provider Accepted
- Delivered
- Bounced
- Opened
- Clicked
- Failed
- Complained

### SendGrid
**Current Status**: Planned
**Expected Event Types**:
- Delivery Requested
- Provider Accepted
- Delivered
- Bounced
- Opened
- Clicked
- Failed
- Complained

### Mailgun
**Current Status**: Planned
**Expected Event Types**:
- Delivery Requested
- Provider Accepted
- Delivered
- Bounced
- Opened
- Clicked
- Failed
- Complained

### Postmark
**Current Status**: Planned
**Expected Event Types**:
- Delivery Requested
- Provider Accepted
- Delivered
- Bounced
- Opened
- Clicked
- Failed
- Complained

## Implementation Considerations

### Scalability
- Asynchronous event processing
- Batch updates for aggregates
- Database indexing for performance
- Queue-based processing system

### Reliability
- Dead letter queues for failed events
- Retry mechanisms for transient failures
- Monitoring and alerting
- Manual reconciliation tools

### Debugging
- Full event storage for audit
- Processing logs
- Error classification
- Manual reprocessing capabilities

## API Endpoints

### Event Ingestion
- `POST /api/v1/webhooks/{provider}` - Receive provider events

### Event Querying
- `GET /api/v1/provider-events` - List events
- `GET /api/v1/provider-events/{id}` - Get specific event

### Analytics Querying
- `GET /api/v1/analytics/emails/{email_id}` - Get email analytics
- `GET /api/v1/analytics/campaigns/{campaign_id}` - Get campaign analytics

All APIs require appropriate authentication and authorization.