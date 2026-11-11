# Google Local Development Setup

## Overview

This guide explains how to set up Google OAuth and Gmail API integration for local development of Pew Mail.

## Prerequisites

Before setting up Google integration, ensure you have:

1. A Google account (personal or Google Workspace)
2. Access to Google Cloud Console
3. Python 3.8+ installed
4. Pew Mail backend and frontend running locally

## Google Cloud Project Setup

### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" then "New Project"
3. Enter project name: `pew-mail-development`
4. Click "Create"

### Step 2: Enable Required APIs

1. In the Google Cloud Console, navigate to "APIs & Services" > "Library"
2. Search for and enable the following APIs:
   - Gmail API
   - Google People API (for user info)
   - Google+ API (deprecated but sometimes required)

### Step 3: Create OAuth Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted to configure the OAuth consent screen:
   - Click "Configure Consent Screen"
   - Select "External" (for development)
   - Fill in required fields:
     - App name: `Pew Mail Development`
     - User support email: Your email
     - Developer contact information: Your email
   - Click "Save and Continue"
   - Skip scopes and test users for now
   - Click "Save and Continue" then "Back to Dashboard"
4. Back in the credentials creation:
   - Select "Web application" as the application type
   - Name: `Pew Mail Local Development`
   - Authorized redirect URIs:
     ```
     http://localhost:5173/google/callback
     http://127.0.0.1:5173/google/callback
     ```
   - Click "Create"
5. Save the Client ID and Client Secret - you'll need these for configuration

## Environment Configuration

### Step 1: Update .env File

Add the following to your backend `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### Step 2: Verify Frontend Configuration

Ensure your frontend is configured to work with the backend:

1. Check that `FRONTEND_URL` in backend config matches your frontend URL
2. Default is `http://localhost:5173`

## Running the Application

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd /Users/im45145v/Projects/Pew-Mail/backend
   ```

2. Install/update dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run database migrations (if needed):
   ```bash
   alembic upgrade head
   ```

4. Start the backend server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd /Users/im45145v/Projects/Pew-Mail/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the frontend development server:
   ```bash
   npm run dev
   ```

## Testing the Integration

### Step 1: Access the Application

1. Open your browser to `http://localhost:5173`
2. Navigate to Settings → Connected Accounts
3. Click "Connect Google Account"

### Step 2: OAuth Flow

1. You'll be redirected to Google's OAuth consent screen
2. Sign in with your Google account
3. Review the permissions being requested:
   - View your email address
   - View your basic profile info
   - Manage drafts and send emails
4. Click "Continue" or "Allow"

### Step 3: Verify Connection

1. After authorization, you should be redirected back to Pew Mail
2. Your Google account should appear in the Connected Accounts list
3. The account status should show as "Connected"

## Troubleshooting

### Common Issues

#### OAuth Redirect URI Mismatch

**Problem**: Error message about redirect URI mismatch

**Solution**:
1. Go to Google Cloud Console > APIs & Services > Credentials
2. Edit your OAuth client ID
3. Ensure the redirect URIs exactly match:
   ```
   http://localhost:5173/google/callback
   http://127.0.0.1:5173/google/callback
   ```
4. Save the changes

#### Invalid Client

**Problem**: "Invalid client" error during OAuth

**Solution**:
1. Verify your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
2. Ensure there are no extra spaces or quotes
3. Restart the backend server after changes

#### Missing Scopes

**Problem**: Insufficient permissions for Gmail operations

**Solution**:
1. Go to Google Cloud Console > APIs & Services > OAuth consent screen
2. Add the required scopes:
   - `https://www.googleapis.com/auth/gmail.compose`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`

#### Database Issues

**Problem**: Database errors related to Google account tables

**Solution**:
1. Run database migrations:
   ```bash
   alembic revision --autogenerate -m "Add Google integration models"
   alembic upgrade head
   ```

### Debugging Tips

#### Check Backend Logs

Monitor backend logs for OAuth-related errors:
```bash
# Look for Google integration logs
tail -f backend/logs/app.log | grep -i google
```

#### Test API Endpoints

Use curl to test API endpoints:
```bash
# Test Google auth URL generation
curl "http://localhost:8000/emails/google/auth-url?redirect_uri=http://localhost:5173/google/callback"

# List connected accounts
curl "http://localhost:8000/emails/google/accounts"
```

#### Verify Environment Variables

Check that environment variables are loaded correctly:
```bash
# In backend directory
python -c "from app.core.config import settings; print(f'Client ID: {settings.GOOGLE_CLIENT_ID[:10]}...')"
```

## Testing Email Operations

### Create a Test Email

1. Create a new email in Pew Mail
2. Add some content and save a version
3. Stage the email version

### Create a Gmail Draft

1. Navigate to the staged email
2. Click "Create Gmail Draft"
3. Select your connected Google account
4. Add test recipients
5. Verify the draft appears in your Gmail drafts folder

### Send a Test Email

1. With a staged email, click "Send Test Email"
2. Select your connected Google account
3. Add test recipients
4. Verify the email arrives in the test inboxes

## Development Best Practices

### Security Considerations

1. **Never commit secrets**: Keep client IDs/secrets in `.env` only
2. **Use separate projects**: Create different projects for development/staging/production
3. **Limit scopes**: Only request necessary permissions
4. **Regular cleanup**: Remove test accounts periodically

### Testing Strategies

1. **Mock services**: Use mocks for automated tests
2. **Test accounts**: Use dedicated Google accounts for testing
3. **Edge cases**: Test token expiration, revocation scenarios
4. **Error handling**: Verify graceful error handling

### Code Quality

1. **Follow existing patterns**: Match the existing code style
2. **Comprehensive logging**: Log important operations
3. **Error boundaries**: Handle errors gracefully
4. **Documentation**: Keep documentation updated

## Advanced Configuration

### Multiple Google Accounts

For testing multi-account scenarios:

1. Create additional OAuth credentials in Google Cloud Console
2. Add them as test users in the OAuth consent screen
3. Test switching between different connected accounts

### Google Workspace Integration

Testing with Google Workspace:

1. Ensure your Google Workspace admin has enabled API access
2. Use a Google Workspace account for testing
3. Verify domain restrictions are properly handled

### Rate Limit Testing

To test Gmail API rate limits:

1. Set up a test script that creates many drafts
2. Monitor for rate limit errors
3. Implement appropriate backoff strategies

## Production Preparation

Before moving to production:

1. **Create production OAuth credentials**: New project/client for production
2. **Domain verification**: Verify your production domain
3. **OAuth verification**: Submit for Google verification if needed
4. **Privacy policy**: Ensure you have a privacy policy
5. **Production scopes**: Review and finalize required scopes

### Production Environment Variables

For production deployment:

```bash
# Production Google OAuth
GOOGLE_CLIENT_ID=production_client_id_here
GOOGLE_CLIENT_SECRET=production_client_secret_here
SECRET_KEY=production_secret_key_here  # Critical for token encryption
```

## Useful Resources

### Google Documentation

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Google Cloud Console](https://console.cloud.google.com/)

### Development Tools

- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground)
- [Google API Explorer](https://developers.google.com/apis-explorer)
- [Postman](https://www.postman.com/) for API testing

### Pew Mail Documentation

- [Google OAuth Integration](../integrations/google-oauth.md)
- [Gmail Delivery](../integrations/gmail-delivery.md)
- [Token Management Security](../security/token-management.md)

## Support

For issues with Google integration:

1. Check the Google Cloud Console for API errors
2. Review backend logs for detailed error messages
3. Ensure all prerequisites are met
4. Consult the troubleshooting section above
5. Contact the development team for persistent issues

Remember to regularly update your dependencies and review Google's API documentation for any changes that might affect your integration.