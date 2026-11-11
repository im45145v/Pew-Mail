import enum
from sqlalchemy import Column, String, Text, ForeignKey, Integer, JSON, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.models.email.template import TemplateScope

class ReusableComponent(BaseModel):
    __tablename__ = "reusable_components"
    
    # Component metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # e.g., "header", "footer", "cta", etc.
    thumbnail_url = Column(String, nullable=True)
    
    # Component definition
    component_definition = Column(JSON, nullable=False)  # Structured component definition
    default_styles = Column(JSON, nullable=True)  # Default CSS styles
    configuration_options = Column(JSON, nullable=True)  # Supported configuration options
    
    # Version tracking
    version = Column(Integer, nullable=False)
    
    # Ownership and visibility
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    scope = Column(Enum(TemplateScope), nullable=False)
    
    # Archiving
    is_archived = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<ReusableComponent(id={self.id}, name='{self.name}', organization_id={self.organization_id})>"

class ReusableComponentVersion(BaseModel):
    __tablename__ = "reusable_component_versions"
    
    # Component association
    component_id = Column(UUID(as_uuid=True), ForeignKey("reusable_components.id"), nullable=False, index=True)
    
    # Version metadata
    version_number = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Component definition snapshot
    component_definition = Column(JSON, nullable=False)
    default_styles = Column(JSON, nullable=True)
    configuration_options = Column(JSON, nullable=True)
    
    # Author
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Change description
    change_description = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<ReusableComponentVersion(id={self.id}, component_id={self.component_id}, version_number={self.version_number})>"