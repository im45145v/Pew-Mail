# Gmail Delivery Integration

## Overview

This document describes the Gmail delivery integration for Pew Mail, which enables users to send emails through their connected Gmail or Google Workspace accounts.

## Architecture

The Gmail delivery system implements a provider abstraction that allows multiple email delivery providers:

```
EmailDeliveryProvider (Abstract)
├── create_draft()
├── send_test()
├── send_production()
├── get_status()
└── validate_account()

GmailProvider (Implementation)
MockProvider (Implementation)
LocalDevelopmentProvider (Implementation)
```

## Core Components

### GoogleAccount Model

Represents a connected Google account with encrypted tokens and status tracking.

### GoogleDraft Model

Tracks Gmail drafts created from Pew Mail staging snapshots.

### GoogleSendHistory Model

Records all delivery operations for auditing and tracking.

## Gmail API Integration

### Draft Creation

The draft creation process:

1. Retrieve staging snapshot HTML content
2. Build MIME message with proper headers
3. Encode message for Gmail API
4. Create draft using Gmail API
5. Store draft reference in database

### Test Email Sending

Sending test emails through Gmail:

1. Validate connected account status
2. Retrieve staging snapshot content
3. Build and encode email message
4. Send via Gmail API
5. Record delivery in send history

### Production Email Sending

Production email sending with safeguards:

1. Require explicit user confirmation
2. Verify approval status of staging snapshot
3. Validate connected account
4. Send with proper tracking
5. Record delivery results

## MIME Message Construction

### Content Formatting

Emails are constructed with:

1. **HTML Content**: Full HTML email body from staging snapshot
2. **Subject**: Email subject line
3. **Recipients**: To, CC, and BCC addresses
4. **Encoding**: UTF-8 encoding for international characters
5. **Headers**: Proper MIME headers for deliverability

### Address Handling

Support for multiple recipient types:

1. **Primary Recipients**: To addresses
2. **Carbon Copy**: CC addresses
3. **Blind Carbon Copy**: BCC addresses
4. **Sender Identity**: From address from connected account

## Security Measures

### Content Protection

1. **Exact Content Delivery**: Uses exact staging snapshot HTML
2. **No Modification**: Content is not altered during delivery
3. **Sanitization**: Basic HTML sanitization for security
4. **Validation**: Recipient address validation

### Account Security

1. **Token Encryption**: Encrypted storage of OAuth tokens
2. **Access Control**: User-specific account access
3. **Revocation Handling**: Proper token revocation on disconnect
4. **Status Monitoring**: Account status validation

## Error Handling

### Common Error Types

1. **Authentication Errors**: Expired or revoked tokens
2. **Quota Errors**: Gmail API rate limiting
3. **Permission Errors**: Insufficient scopes
4. **Network Errors**: Connectivity issues
5. **Content Errors**: Invalid email content

### Retry Logic

The system implements appropriate retry strategies:

1. **Token Refresh**: Automatic refresh of expired access tokens
2. **Transient Errors**: Retry for temporary network issues
3. **Quota Management**: Backoff for rate limited requests
4. **Fatal Errors**: Immediate failure for permanent issues

## Delivery Guarantees

### Idempotency

1. **Duplicate Prevention**: Unique identifiers for send operations
2. **Transaction Safety**: Database transactions for consistency
3. **State Tracking**: Clear status for all operations

### Delivery Confirmation

Delivery status tracking:

1. **Requested**: Send operation initiated
2. **Accepted**: Accepted by Gmail API
3. **Delivered**: Delivered to recipient server
4. **Failed**: Delivery failed with error details
5. **Unknown**: Uncertain delivery state

## Integration Patterns

### Test Delivery Workflow

1. User stages email revision
2. Validation runs automatically
3. User selects connected Gmail account
4. User specifies test recipients
5. Pew Mail sends exact staged HTML
6. Delivery result is recorded
7. User inspects message in inbox

### Production Delivery Workflow

1. Valid staged snapshot required
2. Successful mandatory validation
3. Approval of exact snapshot
4. Connected sending account
5. Valid sender identity
6. Confirmed recipients
7. Valid subject line
8. Explicit user confirmation
9. Actual email sending
10. Delivery tracking

## API Endpoints

### Draft Operations

```
POST /emails/google/drafts/create
{
  "google_account_id": "uuid",
  "staging_snapshot_id": "uuid",
  "to_addresses": ["email@example.com"],
  "subject": "Email Subject",
  "cc_addresses": ["cc@example.com"],
  "bcc_addresses": ["bcc@example.com"]
}
```

### Test Sending

```
POST /emails/google/send/test
{
  "google_account_id": "uuid",
  "staging_snapshot_id": "uuid",
  "recipients": ["test@example.com"],
  "subject": "Test Email"
}
```

### Production Sending

```
POST /emails/google/send/production
{
  "google_account_id": "uuid",
  "staging_snapshot_id": "uuid",
  "recipients": ["recipient@example.com"],
  "subject": "Production Email",
  "confirmation_token": "user_confirmation_token"
}
```

## Database Schema

### Google Accounts Table

```sql
CREATE TABLE google_accounts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    encrypted_refresh_token TEXT NOT NULL,
    encrypted_access_token TEXT,
    access_token_expires_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'connected',
    last_checked_at TIMESTAMP,
    organization_id UUID,
    is_shared BOOLEAN DEFAULT FALSE,
    google_user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Google Drafts Table

```sql
CREATE TABLE google_drafts (
    id UUID PRIMARY KEY,
    staging_snapshot_id UUID NOT NULL,
    google_account_id UUID NOT NULL,
    google_draft_id VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    to_addresses TEXT NOT NULL,
    cc_addresses TEXT,
    bcc_addresses TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Send History Table

```sql
CREATE TABLE google_send_history (
    id UUID PRIMARY KEY,
    email_id UUID NOT NULL,
    email_version_id UUID NOT NULL,
    staging_snapshot_id UUID NOT NULL,
    google_account_id UUID NOT NULL,
    recipient_metadata TEXT NOT NULL,
    subject VARCHAR(255) NOT NULL,
    google_message_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'requested',
    error_message TEXT,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Performance Considerations

### Caching Strategy

1. **Token Caching**: Cache access tokens to reduce API calls
2. **Account Validation**: Cache account status for reasonable periods
3. **API Response Caching**: Cache non-sensitive API responses

### Batch Operations

1. **Bulk Draft Creation**: Support for creating multiple drafts
2. **Batch Sending**: Efficient sending of multiple emails
3. **Parallel Processing**: Concurrent operations where appropriate

## Monitoring and Logging

### Audit Trail

All operations are logged for compliance:

1. **Account Connections**: Track when accounts are connected/disconnected
2. **Draft Creation**: Log draft creation attempts
3. **Email Sending**: Record all send operations
4. **Error Conditions**: Log all error scenarios

### Metrics Collection

Key metrics for monitoring:

1. **Success Rates**: Delivery success percentages
2. **Error Rates**: Failure statistics by type
3. **Latency**: API response times
4. **Usage**: Account connection and usage statistics

## Testing Strategy

### Unit Tests

1. Token encryption/decryption
2. MIME message construction
3. Error handling scenarios
4. Account validation logic

### Integration Tests

1. OAuth flow simulation
2. Gmail API interaction mocking
3. Database operation validation
4. End-to-end workflow testing

### Manual Testing

1. Real OAuth flow verification
2. Actual Gmail draft creation
3. Test email delivery
4. Production send confirmation flow

## Compliance and Privacy

### Data Handling

1. **Minimal Data Storage**: Only essential information stored
2. **Encrypted Tokens**: Secure storage of authentication tokens
3. **No Content Logging**: Email content not logged
4. **Access Controls**: Role-based access to account information

### Privacy Considerations

1. **User Consent**: Explicit consent for account connection
2. **Data Portability**: Ability to disconnect accounts
3. **Deletion Support**: Complete removal of account data
4. **Transparency**: Clear documentation of data usage