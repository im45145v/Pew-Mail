from sqlalchemy import Column, String, Text, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class EmailVersion(BaseModel):
    __tablename__ = "email_versions"
    
    # Email association
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=False)
    
    # Version metadata
    version_number = Column(Integer, nullable=False)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("email_versions.id"), nullable=True)
    change_description = Column(Text, nullable=True)
    
    # Document snapshots
    document_snapshot = Column(JSON, nullable=False)  # Full structured email document at this version
    mjml_snapshot = Column(Text, nullable=True)       # MJML at this version
    html_snapshot = Column(Text, nullable=True)       # HTML at this version
    
    # Author
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    def __repr__(self):
        return f"<EmailVersion(id={self.id}, email_id={self.email_id}, version_number={self.version_number})>"