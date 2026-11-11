from sqlalchemy import Column, String, Text, ForeignKey, Boolean, JSON, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
import enum

class StagingSnapshotStatus(str, enum.Enum):
    VALIDATION_PENDING = "validation_pending"
    VALIDATION_IN_PROGRESS = "validation_in_progress"
    VALIDATION_COMPLETED = "validation_completed"
    STAGING = "staging"
    TESTING = "testing"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    READY_FOR_PRODUCTION = "ready_for_production"
    DISCARDED = "discarded"

class StagingSnapshot(BaseModel):
    __tablename__ = "staging_snapshots"
    
    # Email association
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=False)
    email_version_id = Column(UUID(as_uuid=True), ForeignKey("email_versions.id"), nullable=False)
    
    # Snapshot data
    subject = Column(String, nullable=False)
    preheader = Column(String, nullable=True)
    mjml_snapshot = Column(Text, nullable=False)  # Exact MJML snapshot at staging time
    html_snapshot = Column(Text, nullable=False)  # Exact HTML snapshot at staging time
    document_snapshot = Column(JSON, nullable=False)  # Full structured document at staging time
    assets = Column(JSON, nullable=True)  # Asset references at staging time
    
    # Metadata
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    staging_status = Column(Enum(StagingSnapshotStatus), default=StagingSnapshotStatus.VALIDATION_PENDING, nullable=False)
    
    # Validation flag
    has_passed_validation = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<StagingSnapshot(id={self.id}, email_id={self.email_id}, staging_status={self.staging_status})>"