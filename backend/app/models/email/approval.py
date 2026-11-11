from sqlalchemy import Column, String, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
import enum

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"

class Approval(BaseModel):
    __tablename__ = "approvals"
    
    # Staging snapshot association
    staging_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("staging_snapshots.id"), nullable=False)
    
    # Approver details
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Approval status
    status = Column(Enum(ApprovalStatus), nullable=False)
    
    # Comments
    comments = Column(Text, nullable=True)
    
    # If changes requested, track the new staging snapshot
    revision_staging_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("staging_snapshots.id"), nullable=True)
    
    def __repr__(self):
        return f"<Approval(id={self.id}, staging_snapshot_id={self.staging_snapshot_id}, status={self.status})>"

class ReviewComment(BaseModel):
    __tablename__ = "review_comments"
    
    # Staging snapshot association
    staging_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("staging_snapshots.id"), nullable=False)
    
    # Commenter
    commenter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # If this comment relates to a specific section
    section_id = Column(String, nullable=True)
    
    # Thread support
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("review_comments.id"), nullable=True)
    
    def __repr__(self):
        return f"<ReviewComment(id={self.id}, staging_snapshot_id={self.staging_snapshot_id})>"