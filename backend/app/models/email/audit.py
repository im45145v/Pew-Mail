from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class EmailAuditEvent(BaseModel):
    __tablename__ = "email_audit_events"
    
    # Entity association
    entity_type = Column(String, nullable=False)  # e.g., "staging_snapshot", "validation_run", "test_send"
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Action details
    action = Column(String, nullable=False)  # e.g., "created", "validated", "approved", "sent_test"
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Additional context
    description = Column(Text, nullable=True)
    event_metadata = Column(JSON, nullable=True)  # Additional structured data (renamed from metadata to avoid conflict)
    
    def __repr__(self):
        return f"<EmailAuditEvent(id={self.id}, action='{self.action}', entity_type='{self.entity_type}')>"