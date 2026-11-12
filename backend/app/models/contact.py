from sqlalchemy import Column, String, Text, ForeignKey, Boolean, DateTime, JSON, UniqueConstraint, Index, Integer
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from app.models.base import BaseModel
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from cryptography.fernet import Fernet
from app.core.config import settings
import base64
import hashlib

class TokenEncryption:
    """Handles encryption and decryption of PII fields"""
    
    def __init__(self):
        # Use the SECRET_KEY from settings, but ensure it's 32 url-safe base64-encoded bytes
        key = settings.SECRET_KEY.encode()
        # Ensure the key is exactly 32 bytes by hashing it
        self.key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
        self.cipher_suite = Fernet(self.key)
    
    def encrypt(self, value: str) -> str:
        """Encrypt a value"""
        if not value:
            return None
        encrypted_value = self.cipher_suite.encrypt(value.encode())
        return encrypted_value.decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt a value"""
        if not encrypted_value:
            return None
        decrypted_value = self.cipher_suite.decrypt(encrypted_value.encode())
        return decrypted_value.decode()

class Contact(BaseModel):
    __tablename__ = "contacts"
    
    # Basic contact information
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    _email = Column('email', String, nullable=False, index=True)
    organization = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    _phone_number = Column('phone_number', String, nullable=True)
    
    # Organization association (scoping)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Custom fields and metadata
    custom_fields = Column(JSON, nullable=True)  # Flexible storage for additional fields
    tags = Column(JSON, nullable=True)           # Array of tag strings
    notes = Column(Text, nullable=True)
    
    # Full-text search vector
    search_vector = Column(TSVECTOR, nullable=True)
    
    # Status fields
    is_archived = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete timestamp
    
    # Consent and unsubscribe tracking
    consent_status = Column(String, nullable=True)         # e.g., "consented", "unsubscribed"
    consent_timestamp = Column(DateTime, nullable=True)
    consent_source = Column(String, nullable=True)         # How consent was obtained
    unsubscribe_timestamp = Column(DateTime, nullable=True)
    is_suppressed = Column(Boolean, default=False, nullable=False)
    
    # Source tracking
    source = Column(String, nullable=True)                 # e.g., "csv_import", "manual", "api"
    import_id = Column(UUID(as_uuid=True), ForeignKey("contact_imports.id"), nullable=True)
    
    # Ensure unique email per organization
    __table_args__ = (
        UniqueConstraint('email', 'organization_id', name='unique_email_per_organization'),
        Index('ix_contacts_tags', 'tags', postgresql_using='gin'),
        Index('ix_contacts_search_vector', 'search_vector', postgresql_using='gin'),
    )
    
    @hybrid_property
    def email(self):
        """Get encrypted email"""
        if not self._email:
            return None
        return TokenEncryption().decrypt(self._email)
    
    @email.setter
    def email(self, value):
        """Set encrypted email"""
        if not value:
            self._email = None
            return
        self._email = TokenEncryption().encrypt(value)
    
    @hybrid_property
    def phone_number(self):
        """Get encrypted phone number"""
        if not self._phone_number:
            return None
        return TokenEncryption().decrypt(self._phone_number)
    
    @phone_number.setter
    def phone_number(self, value):
        """Set encrypted phone number"""
        if not value:
            self._phone_number = None
            return
        self._phone_number = TokenEncryption().encrypt(value)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def __repr__(self):
        return f"<Contact(id={self.id}, email='[ENCRYPTED]', first_name='{self.first_name}', last_name='{self.last_name}', organization_id={self.organization_id})>"

class ContactGroup(BaseModel):
    __tablename__ = "contact_groups"
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Ensure unique group names per organization
    __table_args__ = (
        UniqueConstraint('name', 'organization_id', name='unique_group_name_per_organization'),
    )
    
    def __repr__(self):
        return f"<ContactGroup(id={self.id}, name='{self.name}', organization_id={self.organization_id})>"

class ContactGroupMembership(BaseModel):
    __tablename__ = "contact_group_memberships"
    
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("contact_groups.id"), nullable=False)
    
    # Ensure unique membership
    __table_args__ = (
        UniqueConstraint('contact_id', 'group_id', name='unique_contact_group_membership'),
    )
    
    def __repr__(self):
        return f"<ContactGroupMembership(contact_id={self.contact_id}, group_id={self.group_id})>"

class ContactImport(BaseModel):
    __tablename__ = "contact_imports"
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    
    # Import statistics
    total_records = Column(Integer, default=0, nullable=False)
    successful_records = Column(Integer, default=0, nullable=False)
    updated_records = Column(Integer, default=0, nullable=False)
    skipped_records = Column(Integer, default=0, nullable=False)
    failed_records = Column(Integer, default=0, nullable=False)
    
    # Configuration
    column_mapping = Column(JSON, nullable=True)  # Map CSV columns to contact fields
    
    # Import results
    error_report_path = Column(String, nullable=True)  # Path to error report file
    
    def __repr__(self):
        return f"<ContactImport(id={self.id}, file_name='{self.file_name}', organization_id={self.organization_id})>"