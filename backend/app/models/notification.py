import enum
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class NotificationStatus(str, enum.Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"

class Notification(BaseModel):
    __tablename__ = "notifications"
    
    # Recipient
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Notification content
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    
    # Type and entity reference
    notification_type = Column(String, nullable=False)  # e.g., "invitation", "comment", "approval"
    entity_type = Column(String, nullable=True)  # e.g., "organization_invitation", "email_comment"
    entity_id = Column(UUID(as_uuid=True), nullable=True)  # ID of the referenced entity
    
    # Status
    status = Column(String, nullable=False)  # Using string instead of enum for flexibility
    
    # Read tracking
    read_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Notification(id={self.id}, recipient_id={self.recipient_id}, type='{self.notification_type}')>"