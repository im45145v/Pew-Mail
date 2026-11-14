"""
Billing and subscription models.
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.models.base import BaseModel


class Billing(BaseModel):
    __tablename__ = "billing"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, unique=True)
    plan = Column(String, nullable=False)  # e.g., "free", "pro", "enterprise"
    status = Column(String, nullable=False)  # e.g., "active", "cancelled", "trialing"
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)  # Additional billing details


class BillingInvoice(BaseModel):
    __tablename__ = "billing_invoices"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    billing_id = Column(UUID(as_uuid=True), ForeignKey("billing.id"), nullable=False)
    invoice_id = Column(String, nullable=False)  # e.g., "in_1Pq5rE2eZvKYlo2C4f1aR5zS"
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)  # e.g., "usd", "eur"
    status = Column(String, nullable=False)  # e.g., "paid", "open", "void"
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=True)
    url = Column(String, nullable=True)  # Hosted invoice URL
    pdf_url = Column(String, nullable=True)  # PDF download URL
    metadata = Column(JSON, nullable=True)  # Additional invoice details