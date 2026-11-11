from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class BrandProfile(BaseModel):
    __tablename__ = "brand_profiles"
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    
    # Colors
    colors = Column(JSON, nullable=True)  # {primary, secondary, accent, background, text}
    
    # Typography
    typography = Column(JSON, nullable=True)  # {font_family, heading_style, body_style}
    
    # Communication preferences
    communication = Column(JSON, nullable=True)  # {tone, greeting, signoff, language}
    
    # Email defaults
    email_defaults = Column(JSON, nullable=True)  # {footer, social_links, button_style}
    
    # Guidelines
    guidelines = Column(JSON, nullable=True)  # {instructions, design_preferences, avoid}
    
    def __repr__(self):
        return f"<BrandProfile(id={self.id}, name='{self.name}', organization_id={self.organization_id})>"