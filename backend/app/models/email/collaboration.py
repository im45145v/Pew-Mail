import enum
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class CommentStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    DELETED = "deleted"

class EmailComment(BaseModel):
    __tablename__ = "email_comments"
    
    # Email association
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=False, index=True)
    
    # Section association (optional)
    section_id = Column(String, nullable=True)  # Stable section identifier
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Author
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Status
    status = Column(String, nullable=False)  # Using string instead of enum for flexibility
    
    # Resolution tracking
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<EmailComment(id={self.id}, email_id={self.email_id}, author_id={self.author_id})>"

class EmailCommentReply(BaseModel):
    __tablename__ = "email_comment_replies"
    
    # Parent comment
    comment_id = Column(UUID(as_uuid=True), ForeignKey("email_comments.id"), nullable=False, index=True)
    
    # Reply content
    content = Column(Text, nullable=False)
    
    # Author
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Status
    status = Column(String, nullable=False)  # Using string instead of enum for flexibility
    
    def __repr__(self):
        return f"<EmailCommentReply(id={self.id}, comment_id={self.comment_id}, author_id={self.author_id})>"

class ActivityEvent(BaseModel):
    __tablename__ = "activity_events"
    
    # Entity association
    entity_type = Column(String, nullable=False, index=True)  # e.g., "email", "template", "campaign"
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Action details
    action = Column(String, nullable=False)  # e.g., "created", "edited", "commented", "approved"
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Additional context
    description = Column(Text, nullable=True)
    metadata = Column(String, nullable=True)  # Additional structured data (using String instead of JSON to avoid naming conflict)
    
    def __repr__(self):
        return f"<ActivityEvent(id={self.id}, action='{self.action}', entity_type='{self.entity_type}')>"