from sqlalchemy import Column, String, Text, ForeignKey, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class EmailAsset(BaseModel):
    __tablename__ = "email_assets"
    
    # Organization association
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Asset metadata
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String, nullable=False)
    
    # Storage information
    storage_key = Column(String, nullable=False)  # Key/path in storage system
    public_url = Column(String, nullable=True)    # Publicly accessible URL
    
    # Usage tracking
    is_used = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<EmailAsset(id={self.id}, filename='{self.filename}', organization_id={self.organization_id})>"