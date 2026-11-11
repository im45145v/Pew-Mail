from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class PersonalizationSchema(BaseModel):
    __tablename__ = "personalization_schemas"
    
    # Organization association
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Schema definition
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Available variables for this organization
    variables = Column(JSON, nullable=False)  # List of variable definitions
    
    def __repr__(self):
        return f"<PersonalizationSchema(id={self.id}, name='{self.name}', organization_id={self.organization_id})>"

class RecipientSnapshot(BaseModel):
    __tablename__ = "recipient_snapshots"
    
    # Association with staging snapshot for traceability
    staging_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("staging_snapshots.id"), nullable=False)
    
    # Recipient data at time of send preparation
    recipient_data = Column(JSON, nullable=False)  # Serialized contact data for this recipient
    
    # Personalization variables resolved for this recipient
    personalization_variables = Column(JSON, nullable=False)
    
    # Generated personalized content
    personalized_html = Column(Text, nullable=True)
    personalized_plain_text = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<RecipientSnapshot(id={self.id}, staging_snapshot_id={self.staging_snapshot_id})>"

class PersonalizedEmail(BaseModel):
    __tablename__ = "personalized_emails"
    
    # Associations
    recipient_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("recipient_snapshots.id"), nullable=False)
    staging_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("staging_snapshots.id"), nullable=False)
    google_send_history_id = Column(UUID(as_uuid=True), ForeignKey("google_send_history.id"), nullable=True)
    
    # Recipient information
    recipient_email = Column(String, nullable=False)
    recipient_name = Column(String, nullable=True)
    
    # Content
    subject = Column(String, nullable=False)
    html_content = Column(Text, nullable=False)
    plain_text_content = Column(Text, nullable=True)
    
    # Delivery tracking
    delivery_status = Column(String, default="pending", nullable=False)  # pending, sent, failed
    delivery_error = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<PersonalizedEmail(id={self.id}, recipient_email='{self.recipient_email}', delivery_status='{self.delivery_status}')>"