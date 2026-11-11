from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.email.email import Email, EmailStatus
from app.models.email.version import EmailVersion
from app.models.email.asset import EmailAsset
from app.models.email.template import EmailTemplate
from app.models.project import Project
from app.models.user import User
from app.services.email.rendering import email_rendering_service
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid

router = APIRouter(prefix="/emails", tags=["emails"])

# Import staging router
from app.api.email.staging_router import router as staging_router
router.include_router(staging_router)

# Import Google router
from app.api.email.google_router import router as google_router
router.include_router(google_router)

# Import Contacts router
from app.api.contacts.router import router as contacts_router
router.include_router(contacts_router)

# Pydantic models for request/response
class EmailCreate(BaseModel):
    name: str
    subject: str
    preheader: Optional[str] = None
    project_id: uuid.UUID
    document: Dict[str, Any]

class EmailUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    preheader: Optional[str] = None
    document: Optional[Dict[str, Any]] = None
    status: Optional[EmailStatus] = None

class EmailResponse(BaseModel):
    id: uuid.UUID
    name: str
    subject: str
    preheader: Optional[str] = None
    project_id: uuid.UUID
    document: Dict[str, Any]
    mjml_content: Optional[str] = None
    html_content: Optional[str] = None
    status: EmailStatus
    version_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class EmailVersionCreate(BaseModel):
    change_description: Optional[str] = None

class EmailVersionResponse(BaseModel):
    id: uuid.UUID
    email_id: uuid.UUID
    version_number: int
    parent_version_id: Optional[uuid.UUID] = None
    change_description: Optional[str] = None
    document_snapshot: Dict[str, Any]
    mjml_snapshot: Optional[str] = None
    html_snapshot: Optional[str] = None
    author_id: uuid.UUID
    created_at: str

    class Config:
        from_attributes = True

class EmailAssetCreate(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    storage_key: str
    public_url: Optional[str] = None

class EmailAssetResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    storage_key: str
    public_url: Optional[str] = None
    is_used: bool
    created_at: str

    class Config:
        from_attributes = True

class EmailTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    organization_id: uuid.UUID
    source_email_id: Optional[uuid.UUID] = None
    document: Dict[str, Any]

class EmailTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    organization_id: uuid.UUID
    source_email_id: Optional[uuid.UUID] = None
    document: Dict[str, Any]
    mjml_content: Optional[str] = None
    html_content: Optional[str] = None
    is_starter: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[EmailResponse])
def list_emails(project_id: Optional[uuid.UUID] = None, db: Session = Depends(get_db)):
    """List all emails, optionally filtered by project"""
    query = db.query(Email)
    if project_id:
        query = query.filter(Email.project_id == project_id)
    return query.all()

@router.post("/", response_model=EmailResponse)
def create_email(email: EmailCreate, db: Session = Depends(get_db)):
    """Create a new email"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == email.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_email = Email(
        name=email.name,
        subject=email.subject,
        preheader=email.preheader,
        project_id=email.project_id,
        document=email.document,
        status=EmailStatus.DRAFT,
        version_count=0
    )
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email

@router.get("/{email_id}", response_model=EmailResponse)
def get_email(email_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific email by ID"""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email

@router.put("/{email_id}", response_model=EmailResponse)
def update_email(email_id: uuid.UUID, email_update: EmailUpdate, db: Session = Depends(get_db)):
    """Update an email"""
    db_email = db.query(Email).filter(Email.id == email_id).first()
    if not db_email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Update fields if provided
    if email_update.name is not None:
        db_email.name = email_update.name
    if email_update.subject is not None:
        db_email.subject = email_update.subject
    if email_update.preheader is not None:
        db_email.preheader = email_update.preheader
    if email_update.document is not None:
        db_email.document = email_update.document
    if email_update.status is not None:
        db_email.status = email_update.status
    
    db.commit()
    db.refresh(db_email)
    return db_email

@router.delete("/{email_id}")
def delete_email(email_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete an email"""
    db_email = db.query(Email).filter(Email.id == email_id).first()
    if not db_email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    db.delete(db_email)
    db.commit()
    return {"message": "Email deleted successfully"}

# Email Versions endpoints
@router.post("/{email_id}/versions", response_model=EmailVersionResponse)
def create_email_version(email_id: uuid.UUID, version: EmailVersionCreate, db: Session = Depends(get_db)):
    """Create a new version of an email"""
    # Get the email
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Increment version count
    email.version_count += 1
    db.commit()
    
    # Create version
    db_version = EmailVersion(
        email_id=email_id,
        version_number=email.version_count,
        change_description=version.change_description,
        document_snapshot=email.document,
        mjml_snapshot=email.mjml_content,
        html_snapshot=email.html_content,
        author_id=uuid.uuid4()  # In a real implementation, this would come from auth
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version

@router.get("/{email_id}/versions", response_model=List[EmailVersionResponse])
def list_email_versions(email_id: uuid.UUID, db: Session = Depends(get_db)):
    """List all versions of an email"""
    versions = db.query(EmailVersion).filter(EmailVersion.email_id == email_id).all()
    return versions

@router.get("/versions/{version_id}", response_model=EmailVersionResponse)
def get_email_version(version_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific email version"""
    version = db.query(EmailVersion).filter(EmailVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Email version not found")
    return version

@router.post("/versions/{version_id}/restore")
def restore_email_version(version_id: uuid.UUID, db: Session = Depends(get_db)):
    """Restore an email to a previous version"""
    # Get the version
    version = db.query(EmailVersion).filter(EmailVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Email version not found")
    
    # Get the email
    email = db.query(Email).filter(Email.id == version.email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Create a new version before restoring
    email.version_count += 1
    db_version = EmailVersion(
        email_id=email.id,
        version_number=email.version_count,
        parent_version_id=version.id,
        change_description=f"Restored to version {version.version_number}",
        document_snapshot=email.document,
        mjml_snapshot=email.mjml_content,
        html_snapshot=email.html_content,
        author_id=uuid.uuid4()  # In a real implementation, this would come from auth
    )
    db.add(db_version)
    
    # Restore the document
    email.document = version.document_snapshot
    email.mjml_content = version.mjml_snapshot
    email.html_content = version.html_snapshot
    
    db.commit()
    db.refresh(email)
    return {"message": f"Email restored to version {version.version_number}"}

# Email Assets endpoints
@router.post("/assets", response_model=EmailAssetResponse)
def create_email_asset(asset: EmailAssetCreate, db: Session = Depends(get_db)):
    """Upload a new email asset"""
    # In a real implementation, organization_id would come from auth
    db_asset = EmailAsset(
        organization_id=uuid.uuid4(),
        filename=asset.filename,
        original_filename=asset.original_filename,
        file_size=asset.file_size,
        mime_type=asset.mime_type,
        storage_key=asset.storage_key,
        public_url=asset.public_url,
        is_used=False
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.get("/assets", response_model=List[EmailAssetResponse])
def list_email_assets(organization_id: Optional[uuid.UUID] = None, db: Session = Depends(get_db)):
    """List all email assets, optionally filtered by organization"""
    query = db.query(EmailAsset)
    if organization_id:
        query = query.filter(EmailAsset.organization_id == organization_id)
    return query.all()

@router.delete("/assets/{asset_id}")
def delete_email_asset(asset_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete an email asset"""
    asset = db.query(EmailAsset).filter(EmailAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Email asset not found")
    
    # Check if asset is used
    if asset.is_used:
        raise HTTPException(status_code=400, detail="Cannot delete used asset")
    
    db.delete(asset)
    db.commit()
    return {"message": "Email asset deleted successfully"}

# Email Templates endpoints
@router.post("/templates", response_model=EmailTemplateResponse)
def create_email_template(template: EmailTemplateCreate, db: Session = Depends(get_db)):
    """Create a new email template"""
    db_template = EmailTemplate(
        name=template.name,
        description=template.description,
        organization_id=template.organization_id,
        source_email_id=template.source_email_id,
        document=template.document,
        is_starter=False
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/templates", response_model=List[EmailTemplateResponse])
def list_email_templates(organization_id: Optional[uuid.UUID] = None, db: Session = Depends(get_db)):
    """List all email templates, optionally filtered by organization"""
    query = db.query(EmailTemplate)
    if organization_id:
        query = query.filter(EmailTemplate.organization_id == organization_id)
    return query.all()

@router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
def get_email_template(template_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific email template"""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Email template not found")
    return template

@router.post("/{email_id}/from-template/{template_id}")
def create_email_from_template(email_id: uuid.UUID, template_id: uuid.UUID, db: Session = Depends(get_db)):
    """Create a new email based on a template"""
    # Get the template
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get the email
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Update email with template document
    email.document = template.document
    db.commit()
    db.refresh(email)
    return {"message": "Email updated with template"}