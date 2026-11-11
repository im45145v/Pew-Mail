# Google OAuth Integration

## Overview

This document describes the Google OAuth integration for Pew Mail, which allows users to connect their Gmail or Google Workspace accounts for email delivery.

## Architecture

The Google OAuth integration follows these principles:

1. **Secure Token Management**: Refresh tokens are encrypted at rest using the application's secret key
2. **Stateless OAuth Flow**: Uses PKCE (Proof Key for Code Exchange) for secure authorization
3. **User-Controlled Connections**: Users can connect, disconnect, and manage their Google accounts
4. **Organization-Level Permissions**: Connected accounts can be shared within organizations

## Required Scopes

The integration requests the following minimal scopes:

### Required Scopes

1. `https://www.googleapis.com/auth/gmail.compose` - Allows creating drafts and sending emails
2. `https://www.googleapis.com/auth/userinfo.email` - Retrieves the user's email address
3. `https://www.googleapis.com/auth/userinfo.profile` - Retrieves the user's profile information

### Scope Justification

| Scope | Purpose | Sensitivity |
|-------|---------|-------------|
| gmail.compose | Create drafts and send emails | Medium - Allows email composition |
| userinfo.email | Identify connected account | Low - Public information |
| userinfo.profile | Display user's name | Low - Public information |

## Security Implementation

### Token Encryption

Refresh tokens are encrypted using the Fernet symmetric encryption scheme:

1. The application's `SECRET_KEY` is used to derive a 32-byte encryption key
2. Refresh tokens are encrypted before storage in the database
3. Access tokens are not stored persistently
4. Tokens are never exposed to the frontend

### OAuth State Validation

The implementation uses OAuth state parameters to prevent CSRF attacks:

1. Random state tokens are generated for each authorization request
2. State tokens are verified during the callback process
3. Authorization codes are exchanged only when state validation passes

## Google Cloud Configuration

### Setting Up Your Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click on "Gmail API" and then "Enable"

### Creating OAuth Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application" as the application type
4. Configure authorized redirect URIs:
   ```
   http://localhost:5173/google/callback
   https://yourdomain.com/google/callback
   ```
5. Save the client ID and client secret

### OAuth Consent Screen

1. Navigate to "APIs & Services" > "OAuth consent screen"
2. Select "External" for testing or "Internal" for domain-restricted apps
3. Fill in the required application information:
   - App name: "Pew Mail"
   - User support email: Your support email
   - Developer contact information: Your email

### Publishing Status

For production use, the OAuth consent screen must be published:

1. **Testing**: During testing, only whitelisted users can authorize the app
2. **Verification**: Certain scopes require Google verification
3. **Publishing**: Publish the app to make it available to all users

## Environment Variables

### Required Configuration

Add these variables to your `.env` file:

```bash
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

### Example .env Configuration

```bash
# Google OAuth
GOOGLE_CLIENT_ID=1234567890-example.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-example-secret
```

## Local Development Setup

### Initial Setup

1. Follow the Google Cloud Configuration steps above
2. Add your credentials to `.env`
3. Ensure your development redirect URI is configured in Google Cloud Console:
   `http://localhost:5173/google/callback`

### Testing the Integration

1. Start the backend server: `uvicorn app.main:app --reload`
2. Start the frontend: `npm run dev`
3. Navigate to Settings → Connected Accounts
4. Click "Connect Google Account"
5. Authorize the application in the Google OAuth screen
6. Verify the account appears in the connected accounts list

## Production Considerations

### Verified Status

For production deployment, consider these requirements:

1. **Domain Verification**: Verify your domain in Google Search Console
2. **App Verification**: Submit your app for verification if using sensitive scopes
3. **Privacy Policy**: Provide a privacy policy URL in the OAuth consent screen
4. **Terms of Service**: Include terms of service for your application

### Scopes and Limitations

The current implementation uses the minimum required scopes. Additional scopes may be needed for:

- Reading existing emails
- Managing labels
- Accessing email metadata
- Using advanced Gmail features

### Rate Limits

The Gmail API has the following quotas:

- **Daily Usage**: 1,000,000,000 quota units per day
- **Per User Rate**: 250 quota units per user per second
- **Draft Creation**: 500 draft creations per day per user
- **Message Sending**: 500 message sends per day per user

## Troubleshooting

### Common Issues

1. **Invalid Client**: Check that your client ID and secret are correct
2. **Redirect URI Mismatch**: Verify that the redirect URI is configured in Google Cloud Console
3. **Unauthorized Scopes**: Ensure all requested scopes are added to the OAuth consent screen
4. **Token Expiration**: Implement proper token refresh handling

### Error Codes

| Error | Description | Solution |
|-------|-------------|----------|
| invalid_client | Invalid client ID or secret | Verify credentials |
| redirect_uri_mismatch | Redirect URI not configured | Add URI to Google Cloud Console |
| access_denied | User denied permission | Check requested scopes |
| invalid_scope | Unauthorized scope requested | Verify scope configuration |

## Testing

### Automated Testing

Use mocked Google API responses for standard automated tests:

1. Mock OAuth flow responses
2. Mock Gmail API calls
3. Test token encryption/decryption
4. Test error handling scenarios

### Integration Testing

1. Connect a test Google account
2. Create email drafts
3. Send test emails
4. Verify account disconnection
5. Test token refresh scenarios

## Future Enhancements

Potential improvements to the Google OAuth integration:

1. **Enhanced Scopes**: Add support for reading emails, managing labels
2. **Batch Operations**: Support bulk draft creation and sending
3. **Advanced Features**: Integrate with Gmail's advanced features
4. **Analytics**: Collect delivery analytics from Gmail