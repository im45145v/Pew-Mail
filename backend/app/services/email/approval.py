from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.email.approval import Approval, ApprovalStatus, ReviewComment
from app.models.email.staging import StagingSnapshot, StagingSnapshotStatus
from app.models.email.audit import EmailAuditEvent
import logging

logger = logging.getLogger(__name__)

class ApprovalService:
    """Service for managing email approvals"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_approval(
        self,
        staging_snapshot_id: str,
        approver_id: str,
        status: ApprovalStatus,
        comments: Optional[str] = None
    ) -> Approval:
        """
        Create an approval for a staging snapshot
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            approver_id: ID of the user approving
            status: Approval status
            comments: Optional comments
            
        Returns:
            Created approval
        """
        # Verify the staging snapshot exists
        staging_snapshot = self.db.query(StagingSnapshot).filter(
            StagingSnapshot.id == staging_snapshot_id
        ).first()
        
        if not staging_snapshot:
            raise ValueError(f"Staging snapshot with ID {staging_snapshot_id} not found")
        
        # Check if user has already approved this snapshot
        existing_approval = self.db.query(Approval).filter(
            and_(
                Approval.staging_snapshot_id == staging_snapshot_id,
                Approval.approver_id == approver_id
            )
        ).first()
        
        if existing_approval:
            # Update existing approval
            existing_approval.status = status
            existing_approval.comments = comments
            self.db.add(existing_approval)
        else:
            # Create new approval
            approval = Approval(
                staging_snapshot_id=staging_snapshot_id,
                approver_id=approver_id,
                status=status,
                comments=comments
            )
            self.db.add(approval)
        
        # Record audit event
        audit_event = EmailAuditEvent(
            entity_type="approval",
            entity_id=staging_snapshot_id,  # Using staging snapshot ID for consistency
            action="created",
            actor_id=approver_id,
            description=f"Approval {status} created for staging snapshot",
            metadata={"comments": comments} if comments else None
        )
        self.db.add(audit_event)
        
        # If this is an approval, update staging snapshot status
        if status == ApprovalStatus.APPROVED:
            staging_snapshot.staging_status = StagingSnapshotStatus.APPROVED
            self.db.add(staging_snapshot)
            
            # Record status change audit event
            status_audit_event = EmailAuditEvent(
                entity_type="staging_snapshot",
                entity_id=staging_snapshot_id,
                action="status_changed",
                actor_id=approver_id,
                description="Status changed to APPROVED due to approval"
            )
            self.db.add(status_audit_event)
        
        # Commit changes
        self.db.commit()
        
        # Refresh and return the approval
        if existing_approval:
            self.db.refresh(existing_approval)
            return existing_approval
        else:
            self.db.refresh(approval)
            return approval
    
    def get_approvals(self, staging_snapshot_id: str) -> List[Approval]:
        """
        Get all approvals for a staging snapshot
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            
        Returns:
            List of approvals
        """
        return self.db.query(Approval).filter(
            Approval.staging_snapshot_id == staging_snapshot_id
        ).all()
    
    def get_latest_approval(self, staging_snapshot_id: str) -> Optional[Approval]:
        """
        Get the latest approval for a staging snapshot
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            
        Returns:
            Latest approval or None if none exists
        """
        return self.db.query(Approval).filter(
            Approval.staging_snapshot_id == staging_snapshot_id
        ).order_by(Approval.created_at.desc()).first()
    
    def add_review_comment(
        self,
        staging_snapshot_id: str,
        commenter_id: str,
        content: str,
        section_id: Optional[str] = None,
        parent_comment_id: Optional[str] = None
    ) -> ReviewComment:
        """
        Add a review comment to a staging snapshot
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            commenter_id: ID of the user commenting
            content: Comment content
            section_id: Optional section ID the comment relates to
            parent_comment_id: Optional parent comment ID for threading
            
        Returns:
            Created review comment
        """
        # Verify the staging snapshot exists
        staging_snapshot = self.db.query(StagingSnapshot).filter(
            StagingSnapshot.id == staging_snapshot_id
        ).first()
        
        if not staging_snapshot:
            raise ValueError(f"Staging snapshot with ID {staging_snapshot_id} not found")
        
        # Verify parent comment exists and is for the same staging snapshot
        if parent_comment_id:
            parent_comment = self.db.query(ReviewComment).filter(
                and_(
                    ReviewComment.id == parent_comment_id,
                    ReviewComment.staging_snapshot_id == staging_snapshot_id
                )
            ).first()
            
            if not parent_comment:
                raise ValueError(f"Parent comment with ID {parent_comment_id} not found for staging snapshot {staging_snapshot_id}")
        
        # Create review comment
        comment = ReviewComment(
            staging_snapshot_id=staging_snapshot_id,
            commenter_id=commenter_id,
            content=content,
            section_id=section_id,
            parent_comment_id=parent_comment_id
        )
        self.db.add(comment)
        self.db.flush()  # Flush to get the ID
        
        # Record audit event
        audit_event = EmailAuditEvent(
            entity_type="review_comment",
            entity_id=comment.id,
            action="created",
            actor_id=commenter_id,
            description="Review comment created",
            metadata={
                "staging_snapshot_id": staging_snapshot_id,
                "section_id": section_id
            }
        )
        self.db.add(audit_event)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(comment)
        
        return comment
    
    def get_review_comments(self, staging_snapshot_id: str) -> List[ReviewComment]:
        """
        Get all review comments for a staging snapshot
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            
        Returns:
            List of review comments
        """
        return self.db.query(ReviewComment).filter(
            ReviewComment.staging_snapshot_id == staging_snapshot_id
        ).order_by(ReviewComment.created_at.asc()).all()
    
    def get_comment_thread(self, comment_id: str) -> List[ReviewComment]:
        """
        Get a comment thread (comment and all its replies)
        
        Args:
            comment_id: ID of the root comment
            
        Returns:
            List of comments in the thread
        """
        # Get the root comment
        root_comment = self.db.query(ReviewComment).filter(ReviewComment.id == comment_id).first()
        if not root_comment:
            raise ValueError(f"Comment with ID {comment_id} not found")
        
        # Get all comments in the thread
        thread_comments = self.db.query(ReviewComment).filter(
            and_(
                ReviewComment.staging_snapshot_id == root_comment.staging_snapshot_id,
                ReviewComment.id == comment_id or ReviewComment.parent_comment_id == comment_id
            )
        ).order_by(ReviewComment.created_at.asc()).all()
        
        return thread_comments
    
    def update_staging_snapshot_status_after_approval(
        self,
        staging_snapshot_id: str,
        actor_id: str
    ) -> None:
        """
        Update staging snapshot status based on approvals
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            actor_id: ID of the user triggering the update
        """
        # Get the staging snapshot
        staging_snapshot = self.db.query(StagingSnapshot).filter(
            StagingSnapshot.id == staging_snapshot_id
        ).first()
        
        if not staging_snapshot:
            raise ValueError(f"Staging snapshot with ID {staging_snapshot_id} not found")
        
        # Check if there's an approved approval
        approved_approval = self.db.query(Approval).filter(
            and_(
                Approval.staging_snapshot_id == staging_snapshot_id,
                Approval.status == ApprovalStatus.APPROVED
            )
        ).first()
        
        if approved_approval:
            # Update status to approved
            staging_snapshot.staging_status = StagingSnapshotStatus.APPROVED
            self.db.add(staging_snapshot)
            
            # Record audit event
            audit_event = EmailAuditEvent(
                entity_type="staging_snapshot",
                entity_id=staging_snapshot_id,
                action="status_changed",
                actor_id=actor_id,
                description="Status changed to APPROVED due to approval"
            )
            self.db.add(audit_event)
            
            # Commit changes
            self.db.commit()
            self.db.refresh(staging_snapshot)