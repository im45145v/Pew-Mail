import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.models.organization_membership import OrganizationRole
from datetime import datetime, timedelta

class OrganizationInvitationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"

class OrganizationInvitation(BaseModel):
    __tablename__ = "organization_invitations"
    
    # Organization association
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Inviter
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Invitee
    email = Column(String, nullable=False, index=True)
    
    # Role to assign
    role = Column(Enum(OrganizationRole), nullable=False)
    
    # Security
    token = Column(String, nullable=False, unique=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=False)
    
    # Status
    status = Column(String, nullable=False)  # Using string instead of enum for flexibility
    
    def is_expired(self) -> bool:
        """Check if the invitation has expired"""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<OrganizationInvitation(id={self.id}, email='{self.email}', organization_id={self.organization_id})>"