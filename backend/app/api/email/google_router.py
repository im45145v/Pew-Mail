from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from app.database.session import get_db
from app.models.user import User
from app.models.email.google_account import GoogleAccount, GoogleAccountStatus
from app.services.email.google_integration import GoogleAuthService, GoogleEmailProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/google", tags=["google"])

# In a real implementation, you would have proper authentication
# For now, we'll simulate user authentication
def get_current_user():
    # This is a placeholder - in reality, you'd extract user from auth token
    return User(id="mock-user-id", email="test@example.com")

@router.get("/auth-url")
async def get_google_auth_url(
    redirect_uri: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Google OAuth authorization URL
    
    Args:
        redirect_uri: The redirect URI for OAuth callback
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Authorization URL
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    try:
        auth_service = GoogleAuthService(db)
        auth_url = auth_service.create_authorization_url(current_user.id, redirect_uri)
        return {"authorization_url": auth_url}
    except Exception as e:
        logger.error(f"Failed to create Google auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create Google auth URL: {str(e)}")

@router.get("/callback")
async def google_oauth_callback(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Handle Google OAuth callback
    
    Args:
        request: HTTP request containing OAuth parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success response with account information
    """
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    redirect_uri = f"{settings.FRONTEND_URL}/google/callback"
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth parameters")
    
    try:
        auth_service = GoogleAuthService(db)
        google_account = auth_service.handle_callback(code, state, redirect_uri)
        
        return {
            "success": True,
            "account": {
                "id": google_account.id,
                "email": google_account.email,
                "name": google_account.name,
                "status": google_account.status,
                "last_checked_at": google_account.last_checked_at
            }
        }
    except Exception as e:
        logger.error(f"Failed to handle Google OAuth callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to handle Google OAuth callback: {str(e)}")

@router.get("/accounts")
async def list_connected_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all connected Google accounts for the current user
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of connected Google accounts
    """
    try:
        accounts = db.query(GoogleAccount).filter(
            GoogleAccount.user_id == current_user.id
        ).all()
        
        return {
            "accounts": [
                {
                    "id": account.id,
                    "email": account.email,
                    "name": account.name,
                    "status": account.status,
                    "last_checked_at": account.last_checked_at,
                    "organization_id": account.organization_id,
                    "is_shared": account.is_shared
                }
                for account in accounts
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list Google accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list Google accounts: {str(e)}")

@router.post("/accounts/{account_id}/disconnect")
async def disconnect_google_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disconnect a Google account
    
    Args:
        account_id: ID of the Google account to disconnect
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success response
    """
    try:
        auth_service = GoogleAuthService(db)
        success = auth_service.disconnect_account(account_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Google account not found")
        
        return {"success": True, "message": "Account disconnected successfully"}
    except Exception as e:
        logger.error(f"Failed to disconnect Google account: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect Google account: {str(e)}")

@router.post("/accounts/{account_id}/validate")
async def validate_google_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate a Google account connection
    
    Args:
        account_id: ID of the Google account to validate
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Validation result
    """
    try:
        provider = GoogleEmailProvider(db)
        is_valid = provider.validate_account(account_id)
        
        return {
            "account_id": account_id,
            "is_valid": is_valid,
            "message": "Account is valid" if is_valid else "Account validation failed"
        }
    except Exception as e:
        logger.error(f"Failed to validate Google account: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate Google account: {str(e)}")

@router.post("/drafts/create")
async def create_gmail_draft(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a Gmail draft from a staging snapshot
    
    Args:
        request: Request containing draft creation parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created draft information
    """
    try:
        google_account_id = request.get("google_account_id")
        staging_snapshot_id = request.get("staging_snapshot_id")
        to_addresses = request.get("to_addresses", [])
        subject = request.get("subject")
        cc_addresses = request.get("cc_addresses")
        bcc_addresses = request.get("bcc_addresses")
        
        if not all([google_account_id, staging_snapshot_id, to_addresses, subject]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # In a real implementation, you would fetch the staging snapshot
        # For now, we'll simulate this
        provider = GoogleEmailProvider(db)
        
        # This is a simplified implementation - in reality, you'd fetch the actual staging snapshot
        # and validate permissions, etc.
        from app.models.email.staging import StagingSnapshot
        staging_snapshot = db.query(StagingSnapshot).filter(
            StagingSnapshot.id == staging_snapshot_id
        ).first()
        
        if not staging_snapshot:
            raise HTTPException(status_code=404, detail="Staging snapshot not found")
        
        google_draft = provider.create_draft(
            google_account_id,
            staging_snapshot,
            to_addresses,
            subject,
            cc_addresses,
            bcc_addresses
        )
        
        return {
            "success": True,
            "draft": {
                "id": google_draft.id,
                "google_draft_id": google_draft.google_draft_id,
                "staging_snapshot_id": google_draft.staging_snapshot_id,
                "subject": google_draft.subject
            }
        }
    except Exception as e:
        logger.error(f"Failed to create Gmail draft: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create Gmail draft: {str(e)}")