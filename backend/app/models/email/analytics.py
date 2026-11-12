import enum
from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class AnalyticsSource(str, enum.Enum):
    GOOGLE_GMAIL = "google_gmail"
    AMAZON_SES = "amazon_ses"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    POSTMARK = "postmark"

class AnalyticsEventType(str, enum.Enum):
    DELIVERY_REQUESTED = "delivery_requested"
    PROVIDER_ACCEPTED = "provider_accepted"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"
    COMPLAINED = "complained"

class ProviderEvent(BaseModel):
    __tablename__ = "provider_events"
    
    # Email associations
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=True, index=True)
    staging_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("staging_snapshots.id"), nullable=True, index=True)
    
    # Provider identification
    provider_reference = Column(String, nullable=False, index=True)  # Unique identifier from the provider
    source = Column(String, nullable=False, index=True)  # Using string instead of enum for flexibility
    
    # Event details
    event_type = Column(String, nullable=False)  # Using string instead of enum for flexibility
    timestamp = Column(DateTime, nullable=False)
    recipient = Column(String, nullable=True)  # Email address of recipient
    
    # Additional data
    event_metadata = Column(String, nullable=True)  # Additional event data (renamed from metadata to avoid conflict)
    
    # Processing status
    processed_at = Column(DateTime, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False, index=True)
    
    __table_args__ = (
        # Ensure we don't process the same event twice
        {'sqlite_autoincrement': True},  # Only for SQLite
    )
    
    def __repr__(self):
        return f"<ProviderEvent(id={self.id}, source='{self.source}', event_type='{self.event_type}')>"

class EmailAnalyticsAggregate(BaseModel):
    __tablename__ = "email_analytics_aggregates"
    
    # Email association
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=False, unique=True, index=True)
    
    # Event counts
    requested_count = Column(Integer, default=0, nullable=False)
    provider_accepted_count = Column(Integer, default=0, nullable=False)
    delivered_count = Column(Integer, default=0, nullable=False)
    bounced_count = Column(Integer, default=0, nullable=False)
    opened_count = Column(Integer, default=0, nullable=False)
    clicked_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    complained_count = Column(Integer, default=0, nullable=False)
    
    def __repr__(self):
        return f"<EmailAnalyticsAggregate(email_id={self.email_id})>"