"""
AI Usage model for tracking PewPew interactions.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.models.base import BaseModel


class AIUsage(BaseModel):
    __tablename__ = "ai_usage"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=True)
    skill_name = Column(String, nullable=False)  # e.g., "email_architect", "visual_hierarchy_expert"
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    model = Column(String, nullable=False)  # e.g., "gpt-4", "claude-3-opus"
    timestamp = Column(DateTime, nullable=False)
    metadata = Column(JSON, nullable=True)