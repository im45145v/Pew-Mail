from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
import json
import logging
from datetime import datetime, timedelta
import uuid

from app.models.email.google_account import GoogleAccount, GoogleAccountStatus, GoogleDraft, GoogleSendHistory
from app.models.email.staging import StagingSnapshot
from app.models.user import User
from app.core.security import TokenEncryption
from app.core.config import settings

logger = logging.getLogger(__name__)

class GoogleIntegrationError(Exception):
    """Custom exception for Google integration errors"""
    pass

class GoogleEmailProvider:
    """Provider for Gmail integration"""
    
    def __init__(self, db: Session):
        self.db = db
        self.token_encryption = TokenEncryption()
        
    def _get_credentials(self, google_account: GoogleAccount) -> Credentials:
        """
        Get valid Google credentials for an account
        
        Args:
            google_account: GoogleAccount object
            
        Returns:
            Valid Credentials object
        """
        # Decrypt tokens
        refresh_token = self.token_encryption.decrypt(google_account.encrypted_refresh_token)
        
        # Create credentials
        creds = Credentials(
            token=None,  # We'll refresh to get a new access token
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
        
        # Refresh the token if needed
        try:
            creds.refresh(Request())
            
            # Update the access token in the database
            google_account.encrypted_access_token = self.token_encryption.encrypt(creds.token)
            google_account.access_token_expires_at = datetime.utcnow() + timedelta(seconds=creds.expiry.timestamp() - datetime.utcnow().timestamp()) if creds.expiry else None
            google_account.status = GoogleAccountStatus.CONNECTED
            google_account.last_checked_at = datetime.utcnow()
            self.db.commit()
            
        except RefreshError as e:
            # Token refresh failed, mark account as expired
            google_account.status = GoogleAccountStatus.EXPIRED if "expired" in str(e).lower() else GoogleAccountStatus.REVOKED
            self.db.commit()
            raise GoogleIntegrationError(f"Failed to refresh Google credentials: {str(e)}")
            
        return creds
    
    def _build_gmail_service(self, google_account: GoogleAccount):
        """
        Build Gmail service for a Google account
        
        Args:
            google_account: GoogleAccount object
            
        Returns:
            Gmail service object
        """
        creds = self._get_credentials(google_account)
        return build('gmail', 'v1', credentials=creds, cache_discovery=False)
    
    def create_draft(
        self,
        google_account_id: str,
        staging_snapshot: StagingSnapshot,
        to_addresses: List[str],
        subject: str,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None
    ) -> GoogleDraft:
        """
        Create a Gmail draft from a staging snapshot
        
        Args:
            google_account_id: ID of the Google account to use
            staging_snapshot: StagingSnapshot to create draft from
            to_addresses: List of recipient email addresses
            subject: Email subject
            cc_addresses: Optional list of CC addresses
            bcc_addresses: Optional list of BCC addresses
            
        Returns:
            GoogleDraft object
        """
        # Get the Google account
        google_account = self.db.query(GoogleAccount).filter(GoogleAccount.id == google_account_id).first()
        if not google_account:
            raise GoogleIntegrationError(f"Google account with ID {google_account_id} not found")
        
        if google_account.status != GoogleAccountStatus.CONNECTED:
            raise GoogleIntegrationError(f"Google account is not connected (status: {google_account.status})")
        
        try:
            # Build the Gmail service
            service = self._build_gmail_service(google_account)
            
            # Create the email message
            message = self._create_email_message(
                staging_snapshot.html_snapshot,
                to_addresses,
                subject,
                cc_addresses,
                bcc_addresses,
                staging_snapshot.sender_email if hasattr(staging_snapshot, 'sender_email') else google_account.email
            )
            
            # Create the draft
            draft_body = {
                'message': {
                    'raw': message
                }
            }
            
            draft = service.users().drafts().create(userId='me', body=draft_body).execute()
            
            # Save the draft reference
            google_draft = GoogleDraft(
                staging_snapshot_id=staging_snapshot.id,
                google_account_id=google_account.id,
                google_draft_id=draft['id'],
                subject=subject,
                to_addresses=json.dumps(to_addresses),
                cc_addresses=json.dumps(cc_addresses) if cc_addresses else None,
                bcc_addresses=json.dumps(bcc_addresses) if bcc_addresses else None
            )
            
            self.db.add(google_draft)
            self.db.commit()
            self.db.refresh(google_draft)
            
            return google_draft
            
        except Exception as e:
            logger.error(f"Failed to create Gmail draft: {str(e)}")
            raise GoogleIntegrationError(f"Failed to create Gmail draft: {str(e)}")
    
    def send_test_email(
        self,
        google_account_id: str,
        staging_snapshot: StagingSnapshot,
        recipients: List[str],
        subject: str
    ) -> Dict[str, any]:
        """
        Send a test email through Gmail
        
        Args:
            google_account_id: ID of the Google account to use
            staging_snapshot: StagingSnapshot to send
            recipients: List of recipient email addresses
            subject: Email subject
            
        Returns:
            Dictionary with delivery results
        """
        # Get the Google account
        google_account = self.db.query(GoogleAccount).filter(GoogleAccount.id == google_account_id).first()
        if not google_account:
            raise GoogleIntegrationError(f"Google account with ID {google_account_id} not found")
        
        if google_account.status != GoogleAccountStatus.CONNECTED:
            raise GoogleIntegrationError(f"Google account is not connected (status: {google_account.status})")
        
        try:
            # Build the Gmail service
            service = self._build_gmail_service(google_account)
            
            # Create the email message
            message = self._create_email_message(
                staging_snapshot.html_snapshot,
                recipients,
                subject,
                sender_email=google_account.email
            )
            
            # Send the email
            send_result = service.users().messages().send(userId='me', body={'raw': message}).execute()
            
            # Record in send history
            send_history = GoogleSendHistory(
                email_id=staging_snapshot.email_id,
                email_version_id=staging_snapshot.email_version_id,
                staging_snapshot_id=staging_snapshot.id,
                google_account_id=google_account.id,
                recipient_metadata=json.dumps(recipients),
                subject=subject,
                google_message_id=send_result['id'],
                status="sent",
                sent_at=datetime.utcnow()
            )
            
            self.db.add(send_history)
            self.db.commit()
            
            return {
                'success': True,
                'message_id': send_result['id'],
                'history_id': send_history.id
            }
            
        except Exception as e:
            logger.error(f"Failed to send test email through Gmail: {str(e)}")
            
            # Record failure in send history
            send_history = GoogleSendHistory(
                email_id=staging_snapshot.email_id,
                email_version_id=staging_snapshot.email_version_id,
                staging_snapshot_id=staging_snapshot.id,
                google_account_id=google_account.id,
                recipient_metadata=json.dumps(recipients),
                subject=subject,
                status="failed",
                error_message=str(e),
                sent_at=datetime.utcnow()
            )
            
            self.db.add(send_history)
            self.db.commit()
            
            raise GoogleIntegrationError(f"Failed to send test email through Gmail: {str(e)}")
    
    def _create_email_message(
        self,
        html_content: str,
        to_addresses: List[str],
        subject: str,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        sender_email: Optional[str] = None
    ) -> str:
        """
        Create a raw email message for Gmail API
        
        Args:
            html_content: HTML content of the email
            to_addresses: List of recipient email addresses
            subject: Email subject
            cc_addresses: Optional list of CC addresses
            bcc_addresses: Optional list of BCC addresses
            sender_email: Optional sender email address
            
        Returns:
            Base64 encoded raw message
        """
        import base64
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        # Create message container
        message = MIMEMultipart('alternative')
        message['to'] = ', '.join(to_addresses)
        message['subject'] = subject
        
        if sender_email:
            message['from'] = sender_email
            
        if cc_addresses:
            message['cc'] = ', '.join(cc_addresses)
            
        # Create the HTML part
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(html_part)
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return raw_message
    
    def validate_account(self, google_account_id: str) -> bool:
        """
        Validate a Google account by checking if we can access the Gmail API
        
        Args:
            google_account_id: ID of the Google account to validate
            
        Returns:
            True if account is valid, False otherwise
        """
        google_account = self.db.query(GoogleAccount).filter(GoogleAccount.id == google_account_id).first()
        if not google_account:
            return False
        
        try:
            service = self._build_gmail_service(google_account)
            # Try to get the user's profile
            profile = service.users().getProfile(userId='me').execute()
            google_account.status = GoogleAccountStatus.CONNECTED
            google_account.last_checked_at = datetime.utcnow()
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to validate Google account {google_account_id}: {str(e)}")
            google_account.status = GoogleAccountStatus.ERROR
            self.db.commit()
            return False

class GoogleAuthService:
    """Service for handling Google OAuth authentication"""
    
    def __init__(self, db: Session):
        self.db = db
        self.token_encryption = TokenEncryption()
    
    def create_authorization_url(self, user_id: str, redirect_uri: str) -> str:
        """
        Create Google OAuth authorization URL
        
        Args:
            user_id: ID of the user requesting authorization
            redirect_uri: Redirect URI for OAuth callback
            
        Returns:
            Authorization URL
        """
        # Create the OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=[
                'https://www.googleapis.com/auth/gmail.compose',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile'
            ]
        )
        
        flow.redirect_uri = redirect_uri
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to get refresh token
        )
        
        return authorization_url
    
    def handle_callback(self, code: str, state: str, redirect_uri: str) -> GoogleAccount:
        """
        Handle Google OAuth callback
        
        Args:
            code: Authorization code from Google
            state: OAuth state parameter
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            GoogleAccount object
        """
        try:
            # Create the OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=[
                    'https://www.googleapis.com/auth/gmail.compose',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile'
                ],
                state=state
            )
            
            flow.redirect_uri = redirect_uri
            
            # Exchange authorization code for credentials
            flow.fetch_token(code=code)
            creds = flow.credentials
            
            # Get user info
            user_info_service = build('oauth2', 'v2', credentials=creds, cache_discovery=False)
            user_info = user_info_service.userinfo().get().execute()
            
            # Check if account already exists
            google_account = self.db.query(GoogleAccount).filter(
                GoogleAccount.email == user_info['email']
            ).first()
            
            if not google_account:
                # Create new Google account
                google_account = GoogleAccount(
                    user_id=user_info.get('id'),  # This should be linked to our user ID
                    email=user_info['email'],
                    name=user_info.get('name'),
                    encrypted_refresh_token=self.token_encryption.encrypt(creds.refresh_token),
                    encrypted_access_token=self.token_encryption.encrypt(creds.token),
                    access_token_expires_at=datetime.utcnow() + timedelta(seconds=creds.expiry.timestamp() - datetime.utcnow().timestamp()) if creds.expiry else None,
                    status=GoogleAccountStatus.CONNECTED,
                    last_checked_at=datetime.utcnow(),
                    google_user_id=user_info.get('id')
                )
                
                self.db.add(google_account)
            else:
                # Update existing account
                google_account.encrypted_refresh_token = self.token_encryption.encrypt(creds.refresh_token)
                google_account.encrypted_access_token = self.token_encryption.encrypt(creds.token)
                google_account.access_token_expires_at = datetime.utcnow() + timedelta(seconds=creds.expiry.timestamp() - datetime.utcnow().timestamp()) if creds.expiry else None
                google_account.status = GoogleAccountStatus.CONNECTED
                google_account.last_checked_at = datetime.utcnow()
                google_account.name = user_info.get('name')
                google_account.google_user_id = user_info.get('id')
            
            self.db.commit()
            self.db.refresh(google_account)
            
            return google_account
            
        except Exception as e:
            logger.error(f"Failed to handle Google OAuth callback: {str(e)}")
            raise GoogleIntegrationError(f"Failed to handle Google OAuth callback: {str(e)}")
    
    def disconnect_account(self, google_account_id: str, user_id: str) -> bool:
        """
        Disconnect a Google account
        
        Args:
            google_account_id: ID of the Google account to disconnect
            user_id: ID of the user requesting disconnection
            
        Returns:
            True if successful, False otherwise
        """
        google_account = self.db.query(GoogleAccount).filter(
            and_(
                GoogleAccount.id == google_account_id,
                GoogleAccount.user_id == user_id
            )
        ).first()
        
        if not google_account:
            return False
        
        # Revoke the token with Google
        try:
            refresh_token = self.token_encryption.decrypt(google_account.encrypted_refresh_token)
            if refresh_token:
                import requests
                requests.post(
                    'https://oauth2.googleapis.com/revoke',
                    params={'token': refresh_token},
                    headers={'content-type': 'application/x-www-form-urlencoded'}
                )
        except Exception as e:
            logger.warning(f"Failed to revoke Google token: {str(e)}")
        
        # Update account status
        google_account.status = GoogleAccountStatus.DISCONNECTED
        google_account.encrypted_refresh_token = None
        google_account.encrypted_access_token = None
        google_account.access_token_expires_at = None
        
        self.db.commit()
        return True