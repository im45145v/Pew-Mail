import enum
from sqlalchemy import Column, String, Text, ForeignKey, Integer, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.models.email.template import TemplateCategory

class EmailTemplateVersion(BaseModel):
    __tablename__ = "email_template_versions"
    
    # Template association
    template_id = Column(UUID(as_uuid=True), ForeignKey("email_templates.id"), nullable=False, index=True)
    
    # Version metadata
    version_number = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(TemplateCategory), nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tag strings
    thumbnail_url = Column(String, nullable=True)
    
    # Email metadata
    subject = Column(String, nullable=True)
    preheader = Column(String, nullable=True)
    
    # Document snapshots
    document = Column(JSON, nullable=False)  # Full structured email template document at this version
    mjml_content = Column(Text, nullable=True)  # MJML at this version
    html_content = Column(Text, nullable=True)  # HTML at this version
    
    # Design tokens at the time of this version
    design_tokens = Column(JSON, nullable=True)
    
    # Author
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Change description
    change_description = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<EmailTemplateVersion(id={self.id}, template_id={self.template_id}, version_number={self.version_number})>"