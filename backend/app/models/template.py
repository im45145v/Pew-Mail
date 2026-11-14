"""
Template model for reusable email templates.
"""
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class Template(BaseModel):
    __tablename__ = "templates"

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    document = Column(JSON, nullable=False)  # Structured template document
    mjml_content = Column(Text, nullable=True)  # Compiled MJML
    html_content = Column(Text, nullable=True)  # Compiled HTML
    thumbnail_url = Column(String, nullable=True)
    category = Column(String, nullable=True)  # e.g., "newsletter", "event"
    version = Column(String, nullable=False, default="1.0")
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_edited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)