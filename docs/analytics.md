# Pew Mail Analytics Documentation

## Overview
Pew Mail analytics provide insight into email delivery performance using actual provider data. The system distinguishes between different stages of the delivery pipeline and supports extensible provider event ingestion.

## Email Delivery Pipeline

### Stages
1. **Requested** - Email send request submitted
2. **Provider Accepted** - Email provider accepted the request
3. **Delivered** - Confirmed delivery to recipient's mail server
4. **Bounced** - Rejected by recipient's mail server
5. **Failed** - Technical failure during delivery
6. **Opened** - Recipient opened the email (when tracking enabled)
7. **Clicked** - Recipient clicked links in the email (when tracking enabled)
8. **Complained** - Recipient marked as spam

### Important Distinctions
- **Accepted ≠ Delivered**: Provider acceptance does not guarantee inbox delivery
- **Tracking is Optional**: Open and click tracking must be explicitly enabled
- **Privacy Respected**: Tracking respects user privacy and consent

## Data Models

### Provider Events
Individual events from email providers are stored in `ProviderEvent` records:
- `provider_reference` - Unique identifier from the provider
- `source` - Email provider (Gmail, SES, SendGrid, etc.)
- `event_type` - Type of event (delivered, bounced, opened, etc.)
- `timestamp` - When the event occurred
- `recipient` - Email address of recipient
- `metadata` - Additional provider-specific data

Events are processed exactly once to prevent duplication.

### Analytics Aggregates
Aggregated statistics are stored in `EmailAnalyticsAggregate` records:
- Counts for each delivery stage
- Updated as new provider events are processed
- Associated with individual email records

## Provider Integration

### Supported Providers
Current provider integrations:
- **Google Gmail** - Native integration through existing Gmail API

### Extensible Architecture
The analytics system supports adding new providers through:
- Standardized event model
- Provider-specific webhook handlers
- Signature verification for security
- Idempotent event processing

### Webhook Security
Provider webhooks implement:
- Signature verification
- Timestamp validation
- Idempotent processing
- Request size limits

## Metrics and Reporting

### Email-Level Analytics
Each email displays available metrics:
- Number of recipients
- Send attempts
- Provider-accepted messages
- Confirmed deliveries
- Bounces
- Failures
- Opens (if tracking enabled)
- Clicks (if tracking enabled)

### Campaign Analytics
Campaign dashboards show:
- Total emails in campaign
- Combined recipient counts
- Aggregate delivery statistics
- Historical activity trends

### Filtering Options
Analytics can be filtered by:
- Date range
- Project
- Campaign
- Email
- Sending account
- Provider
- Status

## Privacy Considerations

### Tracking Opt-In
Open and click tracking:
- Requires explicit organization-level enablement
- Includes clear privacy disclosures
- Provides opt-out mechanisms
- Documents tracking limitations

### Limitation Acknowledgment
Tracking has inherent limitations:
- Image blocking prevents open tracking
- Privacy proxies mask user activity
- Automated scanners generate false events
- Delivery confirmation doesn't guarantee inbox placement

## Implementation Architecture

### Event Processing Flow
1. Provider sends webhook event
2. System validates webhook authenticity
3. Event is stored in `ProviderEvent` table
4. Event processor updates `EmailAnalyticsAggregate`
5. Dashboards reflect updated metrics

### Data Integrity
- Events processed exactly once
- Aggregates updated atomically
- Historical data preserved
- Audit trail maintained

## Dashboard Features

### Overview Metrics
High-level statistics show:
- Total emails sent
- Delivery success rates
- Recent activity trends

### Detailed Views
Specific pages for:
- Individual email performance
- Campaign performance
- Provider comparison

### Visualization
Charts and graphs display:
- Delivery funnel
- Time series data
- Comparative metrics

Empty states provide helpful guidance for new organizations.