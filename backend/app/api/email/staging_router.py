from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.database.session import get_db
from app.services.email.staging import StagingService
from app.services.email.approval import ApprovalService
from app.services.email.test_delivery import TestDeliveryService
from app.models.email.staging import StagingSnapshot, StagingSnapshotStatus
from app.models.email.validation import ValidationRun, ValidationResult
from app.models.email.approval import Approval, ApprovalStatus, ReviewComment
from app.models.email.test import TestSend, TestRecipient

router = APIRouter(prefix="/email/staging", tags=["email-staging"])

# Pydantic models for request/response
class StagingSnapshotCreate(BaseModel):
    email_id: str
    email_version_id: str

class StagingSnapshotResponse(BaseModel):
    id: str
    email_id: str
    email_version_id: str
    subject: str
    preheader: Optional[str]
    staging_status: StagingSnapshotStatus
    has_passed_validation: bool
    author_id: str
    created_at: str
    updated_at: str

class ValidationRunResponse(BaseModel):
    id: str
    staging_snapshot_id: str
    score: Optional[int]
    error_count: int
    warning_count: int
    info_count: int
    created_at: str

class ValidationResultResponse(BaseModel):
    id: str
    validation_run_id: str
    check_id: str
    category: str
    severity: str
    status: str
    description: str
    affected_section_id: Optional[str]
    suggested_resolution: Optional[str]
    created_at: str

class ApprovalCreate(BaseModel):
    status: ApprovalStatus
    comments: Optional[str] = None

class ApprovalResponse(BaseModel):
    id: str
    staging_snapshot_id: str
    approver_id: str
    status: ApprovalStatus
    comments: Optional[str]
    created_at: str
    updated_at: str

class ReviewCommentCreate(BaseModel):
    content: str
    section_id: Optional[str] = None
    parent_comment_id: Optional[str] = None

class ReviewCommentResponse(BaseModel):
    id: str
    staging_snapshot_id: str
    commenter_id: str
    content: str
    section_id: Optional[str]
    parent_comment_id: Optional[str]
    created_at: str

class TestSendCreate(BaseModel):
    recipient_emails: List[str]

class TestSendResponse(BaseModel):
    id: str
    staging_snapshot_id: str
    recipients: List[str]
    sender_id: str
    sender_email: str
    subject: str
    delivery_status: str
    provider_response: Optional[str]
    error_message: Optional[str]
    message_id: Optional[str]
    created_at: str

class TestRecipientCreate(BaseModel):
    email: str
    name: Optional[str] = None

class TestRecipientResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    name: Optional[str]
    is_active: bool
    created_at: str

# Dependency functions
def get_staging_service(db: Session = Depends(get_db)) -> StagingService:
    return StagingService(db)

def get_approval_service(db: Session = Depends(get_db)) -> ApprovalService:
    return ApprovalService(db)

def get_test_delivery_service(db: Session = Depends(get_db)) -> TestDeliveryService:
    return TestDeliveryService(db)

# Staging snapshot endpoints
@router.post("/", response_model=StagingSnapshotResponse)
def create_staging_snapshot(
    payload: StagingSnapshotCreate,
    staging_service: StagingService = Depends(get_staging_service),
    current_user_id: str = Depends(lambda: "mock-user-id")  # In a real app, get from auth
):
    """Create a staging snapshot from an email version"""
    try:
        staging_snapshot = staging_service.create_staging_snapshot(
            payload.email_id,
            payload.email_version_id,
            current_user_id
        )
        
        return StagingSnapshotResponse(
            id=str(staging_snapshot.id),
            email_id=str(staging_snapshot.email_id),
            email_version_id=str(staging_snapshot.email_version_id),
            subject=staging_snapshot.subject,
            preheader=staging_snapshot.preheader,
            staging_status=staging_snapshot.staging_status,
            has_passed_validation=staging_snapshot.has_passed_validation,
            author_id=str(staging_snapshot.author_id),
            created_at=staging_snapshot.created_at.isoformat(),
            updated_at=staging_snapshot.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{staging_snapshot_id}", response_model=StagingSnapshotResponse)
def get_staging_snapshot(
    staging_snapshot_id: str,
    staging_service: StagingService = Depends(get_staging_service)
):
    """Get a staging snapshot by ID"""
    try:
        uuid.UUID(staging_snapshot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staging snapshot ID")
    
    staging_snapshot = staging_service.get_staging_snapshot(staging_snapshot_id)
    if not staging_snapshot:
        raise HTTPException(status_code=404, detail="Staging snapshot not found")
    
    return StagingSnapshotResponse(
        id=str(staging_snapshot.id),
        email_id=str(staging_snapshot.email_id),
        email_version_id=str(staging_snapshot.email_version_id),
        subject=staging_snapshot.subject,
        preheader=staging_snapshot.preheader,
        staging_status=staging_snapshot.staging_status,
        has_passed_validation=staging_snapshot.has_passed_validation,
        author_id=str(staging_snapshot.author_id),
        created_at=staging_snapshot.created_at.isoformat(),
        updated_at=staging_snapshot.updated_at.isoformat()
    )

@router.get("/{email_id}/history", response_model=List[StagingSnapshotResponse])
def get_staging_history(
    email_id: str,
    staging_service: StagingService = Depends(get_staging_service)
):
    """Get staging history for an email"""
    try:
        uuid.UUID(email_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid email ID")
    
    staging_snapshots = staging_service.get_staging_history(email_id)
    
    return [
        StagingSnapshotResponse(
            id=str(snapshot.id),
            email_id=str(snapshot.email_id),
            email_version_id=str(snapshot.email_version_id),
            subject=snapshot.subject,
            preheader=snapshot.preheader,
            staging_status=snapshot.staging_status,
            has_passed_validation=snapshot.has_passed_validation,
            author_id=str(snapshot.author_id),
            created_at=snapshot.created_at.isoformat(),
            updated_at=snapshot.updated_at.isoformat()
        )
        for snapshot in staging_snapshots
    ]

@router.put("/{staging_snapshot_id}/status")
def update_staging_status(
    staging_snapshot_id: str,
    new_status: StagingSnapshotStatus,
    staging_service: StagingService = Depends(get_staging_service),
    current_user_id: str = Depends(lambda: "mock-user-id")  # In a real app, get from auth
):
    """Update the status of a staging snapshot"""
    try:
        uuid.UUID(staging_snapshot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staging snapshot ID")
    
    try:
        staging_snapshot = staging_service.update_staging_status(
            staging_snapshot_id,
            new_status,
            current_user_id
        )
        
        return {
            "message": "Status updated successfully",
            "staging_snapshot_id": str(staging_snapshot.id),
            "new_status": staging_snapshot.staging_status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Validation endpoints
@router.get("/{staging_snapshot_id}/validation", response_model=dict)
def get_validation_results(
    staging_snapshot_id: str,
    staging_service: StagingService = Depends(get_staging_service)
):
    """Get validation results for a staging snapshot"""
    try:
        uuid.UUID(staging_snapshot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staging snapshot ID")
    
    validation_run, validation_results = staging_service.get_validation_results(staging_snapshot_id)
    
    if not validation_run:
        raise HTTPException(status_code=404, detail="No validation results found")
    
    run_response = ValidationRunResponse(
        id=str(validation_run.id),
        staging_snapshot_id=str(validation_run.staging_snapshot_id),
        score=validation_run.score,
        error_count=validation_run.error_count,
        warning_count=validation_run.warning_count,
        info_count=validation_run.info_count,
        created_at=validation_run.created_at.isoformat()
    )
    
    results_response = [
        ValidationResultResponse(
            id=str(result.id),
            validation_run_id=str(result.validation_run_id),
            check_id=result.check_id,
            category=result.category,
            severity=result.severity,
            status=result.status,
            description=result.description,
            affected_section_id=result.affected_section_id,
            suggested_resolution=result.suggested_resolution,
            created_at=result.created_at.isoformat()
        )
        for result in validation_results
    ]
    
    return {
        "validation_run": run_response,
        "validation_results": results_response
    }

# Approval endpoints
@router.post("/{staging_snapshot_id}/approval", response_model=ApprovalResponse)
def create_approval(
    staging_snapshot_id: str,
    payload: ApprovalCreate,
    approval_service: ApprovalService = Depends(get_approval_service),
    current_user_id: str = Depends(lambda: "mock-user-id")  # In a real app, get from auth
):
    """Create or update an approval for a staging snapshot"""
    try:
        uuid.UUID(staging_snapshot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staging snapshot ID")
    
    try:
        approval = approval_service.create_approval(
            staging_snapshot_id,
            current_user_id,
            payload.status,
            payload.comments
        )
        
        return ApprovalResponse(
            id=str(approval.id),
            staging_snapshot_id=str(approval.staging_snapshot_id),
            approver_id=str(approval.approver_id),
            status=approval.status,
            comments=approval.comments,
            created_at=approval.created_at.isoformat(),
            updated_at=approval.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{staging_snapshot_id}/approvals", response_model=List[ApprovalResponse])
def get_approvals(
    staging_snapshot_id: str,
    approval_service: ApprovalService = Depends(get_approval_service)
):
    """Get all approvals for a staging snapshot"""
    try:
        uuid.UUID(staging_snapshot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staging snapshot ID")
    
    approvals = approval_service.get_approvals(staging_snapshot_id)
    
    return [
        ApprovalResponse(
            id=str(approval.id),
            staging_snapshot_id=str(approval.staging_snapshot_id),
            approver_id=str(approval.approver_id),
            status=approval.status,
            comments=approval.comments,
            created_at=approval.created_at.isoformat(),
            updated_at=approval.updated_at.isoformat()
        )
        for approval in approvals
    ]

# Review comment endpoints
@router.post("/{staging_snapshot_id}/comments", response_model=ReviewCommentResponse)
def add_review_comment(
    staging_snapshot_id: str,
    payload: ReviewCommentCreate,
    approval_service: ApprovalService = Depends(get_approval_service),
    current_user_id: str = Depends(lambda: "mock-user-id")  # In a real app, get from auth
):
    """Add a review comment to a staging snapshot"""
    try:
        uuid.UUID(staging_snapshot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staging snapshot ID")
    
    try:
        comment = approval_service.add_review_comment(
            staging_snapshot_id,
            current_user_id,
            payload.content,
            payload.section_id,
            payload.parent_comment_id
        )
        
        return ReviewCommentResponse(
            id=str(comment.id),
            staging_snapshot_id=str(comment.staging_snapshot_id),
            commenter_id=str(comment.commenter_id),
            content=comment.content,
            section_id=comment.section_id,
            parent_comment_id=comment.parent_comment_id,
            created_at=comment.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{staging_snapshot_id}/comments", response_model=List[ReviewCommentResponse])
def get_review_comments(
    staging_snapshot_id: str,
    approval_service: ApprovalService = Depends(get_approval_service)
):
    """Get all review comments for a staging snapshot"""
    try:
        uuid.UUID(staging_snapshot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staging snapshot ID")
    
    comments = approval_service.get_review_comments(staging_snapshot_id)
    
    return [
        ReviewCommentResponse(
            id=str(comment.id),
            staging_snapshot_id=str(comment.staging_snapshot_id),
            commenter_id=str(comment.commenter_id),
            content=comment.content,
            section_id=comment.section_id,
            parent_comment_id=comment.parent_comment_id,
            created_at=comment.created_at.isoformat()
        )
        for comment in comments
    ]

# Test delivery endpoints
@router.post("/{staging_snapshot_id}/test-send", response_model=TestSendResponse)
def send_test_email(
    staging_snapshot_id: str,
    payload: TestSendCreate,
    test_delivery_service: TestDeliveryService = Depends(get_test_delivery_service),
    current_user_id: str = Depends(lambda: "mock-user-id")  # In a real app, get from auth
):
    """Send a test email for a staging snapshot"""
    try:
        uuid.UUID(staging_snapshot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staging snapshot ID")
    
    try:
        test_send = test_delivery_service.send_test_email(
            staging_snapshot_id,
            payload.recipient_emails,
            current_user_id
        )
        
        return TestSendResponse(
            id=str(test_send.id),
            staging_snapshot_id=str(test_send.staging_snapshot_id),
            recipients=test_send.recipients,
            sender_id=str(test_send.sender_id),
            sender_email=test_send.sender_email,
            subject=test_send.subject,
            delivery_status=test_send.delivery_status,
            provider_response=test_send.provider_response,
            error_message=test_send.error_message,
            message_id=test_send.message_id,
            created_at=test_send.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{staging_snapshot_id}/test-sends", response_model=List[TestSendResponse])
def get_test_sends(
    staging_snapshot_id: str,
    test_delivery_service: TestDeliveryService = Depends(get_test_delivery_service)
):
    """Get all test sends for a staging snapshot"""
    try:
        uuid.UUID(staging_snapshot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staging snapshot ID")
    
    test_sends = test_delivery_service.get_test_sends(staging_snapshot_id)
    
    return [
        TestSendResponse(
            id=str(test_send.id),
            staging_snapshot_id=str(test_send.staging_snapshot_id),
            recipients=test_send.recipients,
            sender_id=str(test_send.sender_id),
            sender_email=test_send.sender_email,
            subject=test_send.subject,
            delivery_status=test_send.delivery_status,
            provider_response=test_send.provider_response,
            error_message=test_send.error_message,
            message_id=test_send.message_id,
            created_at=test_send.created_at.isoformat()
        )
        for test_send in test_sends
    ]

@router.get("/organization/{organization_id}/test-recipients", response_model=List[TestRecipientResponse])
def get_test_recipients(
    organization_id: str,
    test_delivery_service: TestDeliveryService = Depends(get_test_delivery_service)
):
    """Get all test recipients for an organization"""
    try:
        uuid.UUID(organization_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid organization ID")
    
    test_recipients = test_delivery_service.get_test_recipients(organization_id)
    
    return [
        TestRecipientResponse(
            id=str(recipient.id),
            organization_id=str(recipient.organization_id),
            email=recipient.email,
            name=recipient.name,
            is_active=recipient.is_active,
            created_at=recipient.created_at.isoformat()
        )
        for recipient in test_recipients
    ]

@router.post("/organization/{organization_id}/test-recipients", response_model=TestRecipientResponse)
def add_test_recipient(
    organization_id: str,
    payload: TestRecipientCreate,
    test_delivery_service: TestDeliveryService = Depends(get_test_delivery_service)
):
    """Add a test recipient"""
    try:
        uuid.UUID(organization_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid organization ID")
    
    try:
        test_recipient = test_delivery_service.add_test_recipient(
            organization_id,
            payload.email,
            payload.name
        )
        
        return TestRecipientResponse(
            id=str(test_recipient.id),
            organization_id=str(test_recipient.organization_id),
            email=test_recipient.email,
            name=test_recipient.name,
            is_active=test_recipient.is_active,
            created_at=test_recipient.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/test-recipients/{recipient_id}")
def remove_test_recipient(
    recipient_id: str,
    test_delivery_service: TestDeliveryService = Depends(get_test_delivery_service)
):
    """Remove a test recipient"""
    try:
        uuid.UUID(recipient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid recipient ID")
    
    test_delivery_service.remove_test_recipient(recipient_id)
    
    return {"message": "Test recipient removed successfully"}