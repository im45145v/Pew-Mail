from sqlalchemy import Column, String, Text, ForeignKey, Enum, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
import enum

class EmailStatus(str, enum.Enum):
    DRAFT = "draft"
    EDITING = "editing"
    VALIDATION = "validation"
    STAGING = "staging"
    TESTING = "testing"
    REVIEW = "review"
    APPROVED = "approved"
    READY_FOR_PRODUCTION = "ready_for_production"
    PRODUCTION_DELIVERY = "production_delivery"
    ARCHIVED = "archived"

class Email(BaseModel):
    __tablename__ = "emails"
    
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    preheader = Column(String, nullable=True)
    
    # Project association
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # Structured document storage
    document = Column(JSON, nullable=False)  # Full structured email document
    
    # Compiled outputs
    mjml_content = Column(Text, nullable=True)  # Generated MJML
    html_content = Column(Text, nullable=True)  # Compiled HTML
    
    # Status
    status = Column(Enum(EmailStatus), default=EmailStatus.DRAFT, nullable=False)
    
    # Version tracking
    version_count = Column(Integer, default=0, nullable=False)
    
    # Collaboration fields
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_edited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<Email(id={self.id}, name='{self.name}', project_id={self.project_id})>"