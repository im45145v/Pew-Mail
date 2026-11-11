from sqlalchemy import Column, String, Text, ForeignKey, Boolean, JSON, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
import enum

class TestDeliveryStatus(str, enum.Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNKNOWN = "unknown"

class TestRecipient(BaseModel):
    __tablename__ = "test_recipients"
    
    # Organization association
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Recipient details
    email = Column(String, nullable=False)
    name = Column(String, nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<TestRecipient(id={self.id}, email='{self.email}', organization_id={self.organization_id})>"

class TestSend(BaseModel):
    __tablename__ = "test_sends"
    
    # Staging snapshot association
    staging_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("staging_snapshots.id"), nullable=False)
    
    # Recipients (JSON array of email addresses)
    recipients = Column(JSON, nullable=False)
    
    # Sender details
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sender_email = Column(String, nullable=False)
    
    # Email metadata
    subject = Column(String, nullable=False)
    
    # Delivery information
    delivery_status = Column(Enum(TestDeliveryStatus), default=TestDeliveryStatus.REQUESTED, nullable=False)
    provider_response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Tracking
    message_id = Column(String, nullable=True)  # Provider message ID if available
    
    def __repr__(self):
        return f"<TestSend(id={self.id}, staging_snapshot_id={self.staging_snapshot_id}, delivery_status={self.delivery_status})>"

class RenderingReview(BaseModel):
    __tablename__ = "rendering_reviews"
    
    # Staging snapshot association
    staging_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("staging_snapshots.id"), nullable=False)
    
    # Reviewer
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Client details
    email_client = Column(String, nullable=False)  # e.g., "Gmail", "Outlook", "Apple Mail"
    device_type = Column(String, nullable=True)    # e.g., "Desktop", "Mobile"
    os = Column(String, nullable=True)             # e.g., "iOS", "Android", "Windows"
    
    # Review content
    notes = Column(Text, nullable=True)
    issues_found = Column(JSON, nullable=True)     # Structured list of issues
    
    # Rating (1-5 stars)
    rating = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<RenderingReview(id={self.id}, email_client='{self.email_client}', staging_snapshot_id={self.staging_snapshot_id})>"