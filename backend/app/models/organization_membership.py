from sqlalchemy import Column, ForeignKey, String, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.models.base import BaseModel

class OrganizationRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"

class OrganizationMembership(BaseModel):
    __tablename__ = "organization_memberships"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    role = Column(Enum(OrganizationRole), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'organization_id', name='unique_user_organization'),
    )
    
    def __repr__(self):
        return f"<OrganizationMembership(user_id={self.user_id}, organization_id={self.organization_id}, role='{self.role}')>"