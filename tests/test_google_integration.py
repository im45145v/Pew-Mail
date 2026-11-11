import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.models.email.google_account import GoogleAccount, GoogleAccountStatus, GoogleDraft, GoogleSendHistory
from app.models.email.staging import StagingSnapshot
from app.models.user import User
from app.services.email.google_integration import GoogleAuthService, GoogleEmailProvider, GoogleIntegrationError
from app.core.security import TokenEncryption

class TestGoogleIntegration:
    """Test suite for Google integration components"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Mock user"""
        return User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            is_active=True,
            is_superuser=False
        )
    
    @pytest.fixture
    def mock_google_account(self, mock_user):
        """Mock Google account"""
        return GoogleAccount(
            id=str(uuid.uuid4()),
            user_id=mock_user.id,
            email="test@gmail.com",
            name="Test User",
            encrypted_refresh_token="encrypted_refresh_token",
            encrypted_access_token="encrypted_access_token",
            access_token_expires_at=datetime.utcnow() + timedelta(hours=1),
            status=GoogleAccountStatus.CONNECTED,
            last_checked_at=datetime.utcnow(),
            google_user_id="google_user_id"
        )
    
    @pytest.fixture
    def mock_staging_snapshot(self):
        """Mock staging snapshot"""
        return StagingSnapshot(
            id=str(uuid.uuid4()),
            email_id=str(uuid.uuid4()),
            email_version_id=str(uuid.uuid4()),
            subject="Test Email",
            html_snapshot="<html><body><h1>Test Email</h1></body></html>",
            document_snapshot={},
            author_id=str(uuid.uuid4())
        )
    
    def test_token_encryption(self):
        """Test token encryption and decryption"""
        encryption = TokenEncryption()
        original_token = "test_refresh_token_12345"
        
        # Encrypt the token
        encrypted = encryption.encrypt(original_token)
        assert encrypted is not None
        assert encrypted != original_token
        
        # Decrypt the token
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original_token
        
        # Test None handling
        assert encryption.encrypt(None) is None
        assert encryption.decrypt(None) is None
    
    @patch('app.services.email.google_integration.Flow')
    def test_create_authorization_url(self, mock_flow_class, mock_db, mock_user):
        """Test creating Google OAuth authorization URL"""
        # Setup mock flow
        mock_flow = Mock()
        mock_flow.authorization_url.return_value = ("https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=test", "test_state")
        mock_flow_class.from_client_config.return_value = mock_flow
        
        # Create service and test
        auth_service = GoogleAuthService(mock_db)
        redirect_uri = "http://localhost:5173/google/callback"
        
        auth_url = auth_service.create_authorization_url(mock_user.id, redirect_uri)
        
        # Verify the result
        assert auth_url is not None
        assert "accounts.google.com" in auth_url
        mock_flow.authorization_url.assert_called_once_with(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
    
    @patch('app.services.email.google_integration.build')
    @patch('app.services.email.google_integration.Flow')
    def test_handle_oauth_callback(self, mock_flow_class, mock_build, mock_db, mock_user):
        """Test handling Google OAuth callback"""
        # Setup mock flow
        mock_flow = Mock()
        mock_credentials = Mock()
        mock_credentials.refresh_token = "test_refresh_token"
        mock_credentials.token = "test_access_token"
        mock_credentials.expiry = datetime.utcnow() + timedelta(hours=1)
        mock_flow.credentials = mock_credentials
        mock_flow.fetch_token.return_value = None
        mock_flow_class.from_client_config.return_value = mock_flow
        
        # Setup mock user info service
        mock_user_info_service = Mock()
        mock_user_info = {
            'email': 'test@gmail.com',
            'name': 'Test User',
            'id': 'google_user_id'
        }
        mock_user_info_service.userinfo().get().execute.return_value = mock_user_info
        mock_build.return_value = mock_user_info_service
        
        # Setup mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Create service and test
        auth_service = GoogleAuthService(mock_db)
        code = "test_auth_code"
        state = "test_state"
        redirect_uri = "http://localhost:5173/google/callback"
        
        google_account = auth_service.handle_callback(code, state, redirect_uri)
        
        # Verify the result
        assert google_account is not None
        assert google_account.email == "test@gmail.com"
        assert google_account.name == "Test User"
        assert google_account.status == GoogleAccountStatus.CONNECTED
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @patch('app.services.email.google_integration.build')
    def test_validate_account_success(self, mock_build, mock_db, mock_google_account):
        """Test validating a Google account successfully"""
        # Setup mock service
        mock_service = Mock()
        mock_profile = {'emailAddress': 'test@gmail.com', 'messagesTotal': 100}
        mock_service.users().getProfile().execute.return_value = mock_profile
        mock_build.return_value = mock_service
        
        # Setup mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_google_account
        
        # Create provider and test
        provider = GoogleEmailProvider(mock_db)
        is_valid = provider.validate_account(mock_google_account.id)
        
        # Verify the result
        assert is_valid is True
        assert mock_google_account.status == GoogleAccountStatus.CONNECTED
        mock_service.users().getProfile().execute.assert_called_once()
    
    @patch('app.services.email.google_integration.build')
    def test_validate_account_failure(self, mock_build, mock_db, mock_google_account):
        """Test validating a Google account with failure"""
        # Setup mock service to raise an exception
        mock_service = Mock()
        mock_service.users().getProfile().execute.side_effect = Exception("API Error")
        mock_build.return_value = mock_service
        
        # Setup mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_google_account
        
        # Create provider and test
        provider = GoogleEmailProvider(mock_db)
        is_valid = provider.validate_account(mock_google_account.id)
        
        # Verify the result
        assert is_valid is False
        assert mock_google_account.status == GoogleAccountStatus.ERROR
    
    @patch('app.services.email.google_integration.build')
    def test_create_draft_success(self, mock_build, mock_db, mock_google_account, mock_staging_snapshot):
        """Test creating a Gmail draft successfully"""
        # Setup mock service
        mock_service = Mock()
        mock_draft_response = {'id': 'gmail_draft_id_123'}
        mock_service.users().drafts().create().execute.return_value = mock_draft_response
        mock_build.return_value = mock_service
        
        # Setup mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_google_account,  # First call for GoogleAccount
            mock_staging_snapshot  # Second call for StagingSnapshot
        ]
        
        # Create provider and test
        provider = GoogleEmailProvider(mock_db)
        to_addresses = ["recipient@example.com"]
        subject = "Test Draft"
        
        google_draft = provider.create_draft(
            mock_google_account.id,
            mock_staging_snapshot,
            to_addresses,
            subject
        )
        
        # Verify the result
        assert google_draft is not None
        assert google_draft.google_draft_id == "gmail_draft_id_123"
        assert google_draft.subject == subject
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_disconnect_account_success(self, mock_db, mock_user, mock_google_account):
        """Test disconnecting a Google account successfully"""
        # Setup mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_google_account
        
        # Create service and test
        auth_service = GoogleAuthService(mock_db)
        success = auth_service.disconnect_account(mock_google_account.id, mock_user.id)
        
        # Verify the result
        assert success is True
        assert mock_google_account.status == GoogleAccountStatus.DISCONNECTED
        assert mock_google_account.encrypted_refresh_token is None
        assert mock_google_account.encrypted_access_token is None
        assert mock_google_account.access_token_expires_at is None
        
        # Verify database operations
        mock_db.commit.assert_called_once()
    
    def test_disconnect_account_not_found(self, mock_db, mock_user):
        """Test disconnecting a non-existent Google account"""
        # Setup mock database query to return None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Create service and test
        auth_service = GoogleAuthService(mock_db)
        success = auth_service.disconnect_account("nonexistent_id", mock_user.id)
        
        # Verify the result
        assert success is False

if __name__ == "__main__":
    pytest.main([__file__])