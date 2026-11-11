from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.models.base import BaseModel

class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"

class Project(BaseModel):
    __tablename__ = "projects"
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    instructions = Column(Text, nullable=True)
    brand_profile_id = Column(UUID(as_uuid=True), ForeignKey("brand_profiles.id"), nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', organization_id={self.organization_id})>"