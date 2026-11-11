import enum
from sqlalchemy import Column, String, Text, ForeignKey, Boolean, JSON, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class TemplateCategory(str, enum.Enum):
    EVENT_INVITATION = "event_invitation"
    EVENT_ANNOUNCEMENT = "event_announcement"
    NEWSLETTER = "newsletter"
    HACKATHON_ANNOUNCEMENT = "hackathon_announcement"
    SPONSORSHIP_OUTREACH = "sponsorship_outreach"
    PARTNERSHIP_OUTREACH = "partnership_outreach"
    PRODUCT_ANNOUNCEMENT = "product_announcement"
    WELCOME_EMAIL = "welcome_email"
    THANK_YOU_EMAIL = "thank_you_email"
    FOLLOW_UP_EMAIL = "follow_up_email"
    PROFESSIONAL_COMMUNICATION = "professional_communication"
    CUSTOM = "custom"

class TemplateScope(str, enum.Enum):
    SYSTEM = "system"
    ORGANIZATION = "organization"
    PROJECT = "project"
    PERSONAL = "personal"

class EmailTemplate(BaseModel):
    __tablename__ = "email_templates"
    
    # Organization association
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Template metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(TemplateCategory), nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tag strings
    thumbnail_url = Column(String, nullable=True)
    
    # Email metadata
    subject = Column(String, nullable=True)
    preheader = Column(String, nullable=True)
    
    # Source email (if created from an existing email)
    source_email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=True)
    
    # Structured document
    document = Column(JSON, nullable=False)  # Full structured email template document
    
    # Compiled outputs
    mjml_content = Column(Text, nullable=True)  # Generated MJML
    html_content = Column(Text, nullable=True)  # Compiled HTML
    
    # Template scope and ownership
    scope = Column(Enum(TemplateScope), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Design tokens
    design_tokens = Column(JSON, nullable=True)
    
    # Archiving
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Versioning
    current_version_id = Column(UUID(as_uuid=True), ForeignKey("email_template_versions.id"), nullable=True)
    
    # Starter templates flag
    is_starter = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<EmailTemplate(id={self.id}, name='{self.name}', organization_id={self.organization_id})>"