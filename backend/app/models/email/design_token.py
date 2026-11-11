from sqlalchemy import Column, String, Text, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class DesignTokenSet(BaseModel):
    __tablename__ = "design_token_sets"
    
    # Token set metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Design tokens
    tokens = Column(JSON, nullable=False)  # Key-value pairs of design tokens
    
    # Ownership
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # System defaults
    is_system_default = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<DesignTokenSet(id={self.id}, name='{self.name}', organization_id={self.organization_id})>"