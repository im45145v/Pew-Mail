"""
Delivery models for email sending and tracking.
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class Delivery(BaseModel):
    __tablename__ = "delivery"

    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=False)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)  # e.g., "scheduled", "sent", "failed"
    delivery_method = Column(String, nullable=False)  # e.g., "smtp", "gmail_api", "ses"
    provider_response = Column(JSON, nullable=True)  # Response from delivery provider
    metadata = Column(JSON, nullable=True)  # Additional delivery details


class DeliveryRecipient(BaseModel):
    __tablename__ = "delivery_recipients"

    delivery_id = Column(UUID(as_uuid=True), ForeignKey("delivery.id"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    email_address = Column(String, nullable=False)
    status = Column(String, nullable=False)  # e.g., "sent", "delivered", "bounced", "opened"
    provider_response = Column(JSON, nullable=True)  # Response from delivery provider
    bounced_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)