from sqlalchemy import Column, String, Text, ForeignKey, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.models.organization import Organization
import enum
from datetime import datetime

class GoogleAccountStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"

class GoogleAccount(BaseModel):
    __tablename__ = "google_accounts"
    
    # User who connected the account
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Google account details
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    
    # Google OAuth tokens (encrypted)
    encrypted_refresh_token = Column(Text, nullable=False)
    encrypted_access_token = Column(Text, nullable=True)
    
    # Token metadata
    access_token_expires_at = Column(DateTime, nullable=True)
    
    # Account status
    status = Column(String, default=GoogleAccountStatus.CONNECTED, nullable=False)
    
    # Last successful connection check
    last_checked_at = Column(DateTime, nullable=True)
    
    # Organization association (optional)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    # Sharing within organization
    is_shared = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    google_user_id = Column(String, nullable=True)  # Google's unique user ID
    
    def __repr__(self):
        return f"<GoogleAccount(id={self.id}, email='{self.email}', status={self.status})>"

class GoogleDraft(BaseModel):
    __tablename__ = "google_drafts"
    
    # Staging snapshot association
    staging_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("staging_snapshots.id"), nullable=False)
    
    # Google account association
    google_account_id = Column(UUID(as_uuid=True), ForeignKey("google_accounts.id"), nullable=False)
    
    # Google draft ID
    google_draft_id = Column(String, nullable=False)
    
    # Draft metadata
    subject = Column(String, nullable=False)
    to_addresses = Column(Text, nullable=False)  # JSON serialized list
    cc_addresses = Column(Text, nullable=True)   # JSON serialized list
    bcc_addresses = Column(Text, nullable=True)  # JSON serialized list
    
    def __repr__(self):
        return f"<GoogleDraft(id={self.id}, google_draft_id='{self.google_draft_id}')>"

class GoogleSendHistory(BaseModel):
    __tablename__ = "google_send_history"
    
    # Email associations
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=False)
    email_version_id = Column(UUID(as_uuid=True), ForeignKey("email_versions.id"), nullable=False)
    staging_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("staging_snapshots.id"), nullable=False)
    
    # Google account association
    google_account_id = Column(UUID(as_uuid=True), ForeignKey("google_accounts.id"), nullable=False)
    
    # Recipient metadata (store as JSON for simplicity in PoC)
    recipient_metadata = Column(Text, nullable=False)  # JSON serialized recipient data
    
    # Email metadata
    subject = Column(String, nullable=False)
    
    # Provider message ID from Gmail
    google_message_id = Column(String, nullable=True)
    
    # Status tracking
    status = Column(String, default="requested", nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<GoogleSendHistory(id={self.id}, status={self.status})>"