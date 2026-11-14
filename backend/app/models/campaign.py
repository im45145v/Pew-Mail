"""
Campaign model for email campaigns.
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class Campaign(BaseModel):
    __tablename__ = "campaigns"

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    status = Column(String, nullable=False)  # e.g., "draft", "active", "completed"
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    schedule = Column(JSON, nullable=True)  # {type: "once|recurring", recurrence: "daily|weekly|monthly"}
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_edited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)