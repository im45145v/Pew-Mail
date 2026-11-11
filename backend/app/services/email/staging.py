from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.email.staging import StagingSnapshot, StagingSnapshotStatus
from app.models.email.validation import ValidationRun, ValidationResult
from app.models.email.email import Email
from app.models.email.version import EmailVersion
from app.models.email.audit import EmailAuditEvent
from app.services.email.validation import ValidationEngine
from app.services.email.rendering import email_rendering_service
import uuid
import logging

logger = logging.getLogger(__name__)

class StagingService:
    """Service for managing email staging and snapshots"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validation_engine = ValidationEngine()
    
    def create_staging_snapshot(
        self,
        email_id: str,
        email_version_id: str,
        author_id: str
    ) -> StagingSnapshot:
        """
        Create a staging snapshot from an email version
        
        Args:
            email_id: ID of the email
            email_version_id: ID of the specific version to stage
            author_id: ID of the user creating the staging snapshot
            
        Returns:
            The created staging snapshot
        """
        # Get the email and version
        email = self.db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise ValueError(f"Email with ID {email_id} not found")
        
        email_version = self.db.query(EmailVersion).filter(
            EmailVersion.id == email_version_id,
            EmailVersion.email_id == email_id
        ).first()
        if not email_version:
            raise ValueError(f"Email version with ID {email_version_id} not found for email {email_id}")
        
        # Render the document to get MJML and HTML
        try:
            mjml_content, html_content, error = email_rendering_service.render_document_to_html(
                email_version.document_snapshot
            )
            
            if error:
                logger.warning(f"Error rendering document to HTML: {error}")
        except Exception as e:
            logger.error(f"Failed to render document to HTML: {str(e)}")
            raise ValueError(f"Failed to render email: {str(e)}")
        
        # Create the staging snapshot
        staging_snapshot = StagingSnapshot(
            email_id=email_id,
            email_version_id=email_version_id,
            subject=email.subject,
            preheader=email.preheader,
            mjml_snapshot=mjml_content,
            html_snapshot=html_content,
            document_snapshot=email_version.document_snapshot,
            assets={},  # In a full implementation, this would extract asset references
            author_id=author_id,
            staging_status=StagingSnapshotStatus.VALIDATION_PENDING
        )
        
        # Save to database
        self.db.add(staging_snapshot)
        self.db.flush()  # Flush to get the ID
        
        # Record audit event
        audit_event = EmailAuditEvent(
            entity_type="staging_snapshot",
            entity_id=staging_snapshot.id,
            action="created",
            actor_id=author_id,
            description=f"Created staging snapshot for email {email.name}"
        )
        self.db.add(audit_event)
        
        # Run validation
        self._run_validation(staging_snapshot, author_id)
        
        # Commit all changes
        self.db.commit()
        self.db.refresh(staging_snapshot)
        
        return staging_snapshot
    
    def _run_validation(self, staging_snapshot: StagingSnapshot, actor_id: str):
        """
        Run validation on a staging snapshot
        
        Args:
            staging_snapshot: The staging snapshot to validate
            actor_id: ID of the user triggering the validation
        """
        # Update status to in progress
        staging_snapshot.staging_status = StagingSnapshotStatus.VALIDATION_IN_PROGRESS
        self.db.add(staging_snapshot)
        
        # Record audit event
        audit_event = EmailAuditEvent(
            entity_type="staging_snapshot",
            entity_id=staging_snapshot.id,
            action="validation_started",
            actor_id=actor_id,
            description="Started validation process"
        )
        self.db.add(audit_event)
        
        # Commit status update
        self.db.commit()
        
        try:
            # Run validation
            validation_results, score = self.validation_engine.validate_staging_snapshot(staging_snapshot)
            
            # Create validation run record
            validation_run = ValidationRun(
                staging_snapshot_id=staging_snapshot.id,
                score=score,
                error_count=sum(1 for r in validation_results if r.severity == "error" and r.status == "fail"),
                warning_count=sum(1 for r in validation_results if r.severity == "warning" and r.status == "fail"),
                info_count=sum(1 for r in validation_results if r.severity == "information" and r.status == "fail")
            )
            self.db.add(validation_run)
            self.db.flush()  # Flush to get the ID
            
            # Create validation result records
            for result in validation_results:
                validation_result = ValidationResult(
                    validation_run_id=validation_run.id,
                    check_id=result.check_id,
                    category=result.category,
                    severity=result.severity,
                    status=result.status,
                    description=result.description,
                    affected_section_id=result.affected_section_id,
                    suggested_resolution=result.suggested_resolution,
                    raw_data=result.raw_data
                )
                self.db.add(validation_result)
            
            # Update staging snapshot with validation results
            has_errors = any(result.severity == "error" and result.status == "fail" for result in validation_results)
            staging_snapshot.has_passed_validation = not has_errors
            staging_snapshot.staging_status = StagingSnapshotStatus.VALIDATION_COMPLETED
            
            # Record audit event
            audit_event = EmailAuditEvent(
                entity_type="staging_snapshot",
                entity_id=staging_snapshot.id,
                action="validation_completed",
                actor_id=actor_id,
                description=f"Validation completed with score {score}. Errors: {validation_run.error_count}, Warnings: {validation_run.warning_count}"
            )
            self.db.add(audit_event)
            
        except Exception as e:
            logger.error(f"Error during validation: {str(e)}")
            staging_snapshot.staging_status = StagingSnapshotStatus.VALIDATION_COMPLETED  # Still mark as completed
            
            # Record error audit event
            audit_event = EmailAuditEvent(
                entity_type="staging_snapshot",
                entity_id=staging_snapshot.id,
                action="validation_failed",
                actor_id=actor_id,
                description=f"Validation failed with error: {str(e)}"
            )
            self.db.add(audit_event)
        
        # Commit all validation changes
        self.db.commit()
    
    def get_staging_snapshot(self, staging_snapshot_id: str) -> Optional[StagingSnapshot]:
        """
        Get a staging snapshot by ID
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            
        Returns:
            The staging snapshot or None if not found
        """
        return self.db.query(StagingSnapshot).filter(StagingSnapshot.id == staging_snapshot_id).first()
    
    def get_staging_history(self, email_id: str) -> List[StagingSnapshot]:
        """
        Get staging history for an email
        
        Args:
            email_id: ID of the email
            
        Returns:
            List of staging snapshots for the email
        """
        return self.db.query(StagingSnapshot).filter(
            StagingSnapshot.email_id == email_id
        ).order_by(StagingSnapshot.created_at.desc()).all()
    
    def update_staging_status(
        self,
        staging_snapshot_id: str,
        new_status: StagingSnapshotStatus,
        actor_id: str,
        notes: Optional[str] = None
    ) -> StagingSnapshot:
        """
        Update the status of a staging snapshot
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            new_status: New status to set
            actor_id: ID of the user making the change
            notes: Optional notes about the status change
            
        Returns:
            Updated staging snapshot
        """
        staging_snapshot = self.get_staging_snapshot(staging_snapshot_id)
        if not staging_snapshot:
            raise ValueError(f"Staging snapshot with ID {staging_snapshot_id} not found")
        
        # Validate status transition
        if not self._is_valid_status_transition(staging_snapshot.staging_status, new_status):
            raise ValueError(
                f"Invalid status transition from {staging_snapshot.staging_status} to {new_status}"
            )
        
        # Update status
        old_status = staging_snapshot.staging_status
        staging_snapshot.staging_status = new_status
        self.db.add(staging_snapshot)
        
        # Record audit event
        audit_event = EmailAuditEvent(
            entity_type="staging_snapshot",
            entity_id=staging_snapshot.id,
            action="status_changed",
            actor_id=actor_id,
            description=f"Status changed from {old_status} to {new_status}",
            metadata={"notes": notes} if notes else None
        )
        self.db.add(audit_event)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(staging_snapshot)
        
        return staging_snapshot
    
    def _is_valid_status_transition(
        self,
        current_status: StagingSnapshotStatus,
        new_status: StagingSnapshotStatus
    ) -> bool:
        """
        Check if a status transition is valid
        
        Args:
            current_status: Current status
            new_status: Proposed new status
            
        Returns:
            True if the transition is valid, False otherwise
        """
        # Define valid transitions
        valid_transitions = {
            StagingSnapshotStatus.VALIDATION_PENDING: [
                StagingSnapshotStatus.VALIDATION_IN_PROGRESS
            ],
            StagingSnapshotStatus.VALIDATION_IN_PROGRESS: [
                StagingSnapshotStatus.VALIDATION_COMPLETED
            ],
            StagingSnapshotStatus.VALIDATION_COMPLETED: [
                StagingSnapshotStatus.STAGING,
                StagingSnapshotStatus.DISCARDED
            ],
            StagingSnapshotStatus.STAGING: [
                StagingSnapshotStatus.TESTING,
                StagingSnapshotStatus.DISCARDED
            ],
            StagingSnapshotStatus.TESTING: [
                StagingSnapshotStatus.REVIEW,
                StagingSnapshotStatus.DISCARDED
            ],
            StagingSnapshotStatus.REVIEW: [
                StagingSnapshotStatus.APPROVED,
                StagingSnapshotStatus.REJECTED,
                StagingSnapshotStatus.CHANGES_REQUESTED,
                StagingSnapshotStatus.DISCARDED
            ],
            StagingSnapshotStatus.APPROVED: [
                StagingSnapshotStatus.READY_FOR_PRODUCTION,
                StagingSnapshotStatus.DISCARDED
            ],
            StagingSnapshotStatus.REJECTED: [
                StagingSnapshotStatus.DISCARDED
            ],
            StagingSnapshotStatus.CHANGES_REQUESTED: [
                StagingSnapshotStatus.DISCARDED
            ],
            StagingSnapshotStatus.READY_FOR_PRODUCTION: [
                StagingSnapshotStatus.PRODUCTION_DELIVERY,
                StagingSnapshotStatus.DISCARDED
            ],
            StagingSnapshotStatus.PRODUCTION_DELIVERY: [
                StagingSnapshotStatus.ARCHIVED
            ],
            StagingSnapshotStatus.DISCARDED: []  # Terminal state
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    def discard_staging_snapshot(self, staging_snapshot_id: str, actor_id: str) -> StagingSnapshot:
        """
        Discard a staging snapshot
        
        Args:
            staging_snapshot_id: ID of the staging snapshot to discard
            actor_id: ID of the user discarding the snapshot
            
        Returns:
            Updated staging snapshot
        """
        return self.update_staging_status(
            staging_snapshot_id,
            StagingSnapshotStatus.DISCARDED,
            actor_id,
            "Discarded by user"
        )
    
    def get_validation_results(self, staging_snapshot_id: str) -> Tuple[Optional[ValidationRun], List[ValidationResult]]:
        """
        Get validation results for a staging snapshot
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            
        Returns:
            Tuple of (validation run, list of validation results)
        """
        # Get the latest validation run
        validation_run = self.db.query(ValidationRun).filter(
            ValidationRun.staging_snapshot_id == staging_snapshot_id
        ).order_by(ValidationRun.created_at.desc()).first()
        
        if not validation_run:
            return None, []
        
        # Get all validation results for this run
        validation_results = self.db.query(ValidationResult).filter(
            ValidationResult.validation_run_id == validation_run.id
        ).all()
        
        return validation_run, validation_results