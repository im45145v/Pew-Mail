from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid
import json

from app.database.session import get_db
from app.services.contacts.contact_service import ContactService, ContactServiceError
from app.services.contacts.personalization_service import PersonalizationService, PersonalizationServiceError
from app.models.contact import Contact, ContactGroup, ContactImport
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/contacts", tags=["contacts"])

# Pydantic models for request/response
class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    organization: Optional[str] = None
    job_title: Optional[str] = None
    phone_number: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    consent_status: Optional[str] = None
    consent_source: Optional[str] = None

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    organization: Optional[str] = None
    job_title: Optional[str] = None
    phone_number: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    is_archived: Optional[bool] = None
    consent_status: Optional[str] = None
    consent_source: Optional[str] = None
    is_suppressed: Optional[bool] = None

class ContactResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    organization: Optional[str] = None
    job_title: Optional[str] = None
    phone_number: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    is_archived: bool
    consent_status: Optional[str] = None
    consent_timestamp: Optional[str] = None
    consent_source: Optional[str] = None
    unsubscribe_timestamp: Optional[str] = None
    is_suppressed: bool
    source: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        orm_mode = True

class ContactGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ContactGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ContactGroupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        orm_mode = True

class ContactImportResponse(BaseModel):
    id: str
    file_name: str
    total_records: int
    successful_records: int
    updated_records: int
    skipped_records: int
    failed_records: int
    column_mapping: Optional[Dict[str, str]] = None
    created_at: str
    updated_at: str
    
    class Config:
        orm_mode = True

class CSVImportRequest(BaseModel):
    column_mapping: Dict[str, str]
    skip_duplicates: bool = True
    update_existing: bool = False

class SearchContactsRequest(BaseModel):
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    group_id: Optional[str] = None
    include_archived: bool = False

class PersonalizationPreviewRequest(BaseModel):
    html_content: str
    contact_id: str

class PersonalizationPreviewResponse(BaseModel):
    personalized_html: str
    missing_variables: List[str]

class RecipientSelectionRequest(BaseModel):
    recipient_ids: List[str]
    group_ids: List[str]
    manual_emails: List[str]

class RecipientSummaryResponse(BaseModel):
    total_recipients: int
    duplicate_count: int
    invalid_recipients: List[str]
    missing_personalization_fields: Dict[str, List[str]]
    recipient_sources: Dict[str, int]

def get_current_user():  # Placeholder for actual auth
    return User(id=uuid.uuid4(), email="test@example.com", first_name="Test", last_name="User")

@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    contact: ContactCreate,
    organization_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new contact"""
    try:
        service = ContactService(db)
        created_contact = service.create_contact(
            organization_id=organization_id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            email=contact.email,
            organization=contact.organization,
            job_title=contact.job_title,
            phone_number=contact.phone_number,
            custom_fields=contact.custom_fields,
            tags=contact.tags,
            notes=contact.notes,
            consent_status=contact.consent_status,
            consent_source=contact.consent_source
        )
        return created_contact
    except ContactServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a contact by ID"""
    service = ContactService(db)
    contact = service.get_contact_by_id(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: str,
    contact_update: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a contact"""
    try:
        service = ContactService(db)
        updated_contact = service.update_contact(
            contact_id=contact_id,
            first_name=contact_update.first_name,
            last_name=contact_update.last_name,
            email=contact_update.email,
            organization=contact_update.organization,
            job_title=contact_update.job_title,
            phone_number=contact_update.phone_number,
            custom_fields=contact_update.custom_fields,
            tags=contact_update.tags,
            notes=contact_update.notes,
            is_archived=contact_update.is_archived,
            consent_status=contact_update.consent_status,
            consent_source=contact_update.consent_source,
            is_suppressed=contact_update.is_suppressed
        )
        return updated_contact
    except ContactServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{contact_id}")
def delete_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a contact"""
    service = ContactService(db)
    deleted = service.delete_contact(contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}

@router.post("/{contact_id}/archive", response_model=ContactResponse)
def archive_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive a contact"""
    try:
        service = ContactService(db)
        archived_contact = service.archive_contact(contact_id)
        return archived_contact
    except ContactServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/search", response_model=List[ContactResponse])
def search_contacts(
    search_request: SearchContactsRequest,
    organization_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search contacts with filters"""
    service = ContactService(db)
    contacts = service.search_contacts(
        organization_id=organization_id,
        query=search_request.query,
        tags=search_request.tags,
        group_id=search_request.group_id,
        include_archived=search_request.include_archived
    )
    return contacts

# Group management endpoints
@router.post("/groups", response_model=ContactGroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    group: ContactGroupCreate,
    organization_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new contact group"""
    try:
        service = ContactService(db)
        created_group = service.create_contact_group(
            organization_id=organization_id,
            name=group.name,
            description=group.description
        )
        return created_group
    except ContactServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/groups", response_model=List[ContactGroupResponse])
def list_groups(
    organization_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all contact groups for an organization"""
    service = ContactService(db)
    groups = service.get_contact_groups(organization_id)
    return groups

@router.put("/groups/{group_id}", response_model=ContactGroupResponse)
def update_group(
    group_id: str,
    group_update: ContactGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a contact group"""
    try:
        service = ContactService(db)
        updated_group = service.update_contact_group(
            group_id=group_id,
            name=group_update.name,
            description=group_update.description
        )
        return updated_group
    except ContactServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/groups/{group_id}")
def delete_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a contact group"""
    service = ContactService(db)
    deleted = service.delete_contact_group(group_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group deleted successfully"}

@router.post("/groups/{group_id}/members/{contact_id}")
def add_contact_to_group(
    group_id: str,
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a contact to a group"""
    try:
        service = ContactService(db)
        success = service.add_contact_to_group(contact_id, group_id)
        if success:
            return {"message": "Contact added to group successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add contact to group")
    except ContactServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/groups/{group_id}/members/{contact_id}")
def remove_contact_from_group(
    group_id: str,
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a contact from a group"""
    service = ContactService(db)
    removed = service.remove_contact_from_group(contact_id, group_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Membership not found")
    return {"message": "Contact removed from group successfully"}

@router.get("/groups/{group_id}/members", response_model=List[ContactResponse])
def get_group_members(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all contacts in a group"""
    service = ContactService(db)
    members = service.get_group_members(group_id)
    return members

# CSV Import endpoints
@router.post("/import/csv", response_model=ContactImportResponse)
async def import_contacts_csv(
    file: UploadFile = File(...),
    organization_id: str = "",
    column_mapping_json: str = "",  # JSON string of column mapping
    skip_duplicates: bool = True,
    update_existing: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import contacts from a CSV file"""
    try:
        # Parse column mapping
        column_mapping = json.loads(column_mapping_json) if column_mapping_json else {}
        
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Import contacts
        service = ContactService(db)
        import_record = service.import_contacts_from_csv(
            organization_id=organization_id,
            user_id=str(current_user.id),
            file_name=file.filename,
            csv_content=csv_content,
            column_mapping=column_mapping,
            skip_duplicates=skip_duplicates,
            update_existing=update_existing
        )
        
        return import_record
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid column mapping JSON")
    except ContactServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV file: {str(e)}")

@router.get("/import/history", response_model=List[ContactImportResponse])
def get_import_history(
    organization_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contact import history"""
    imports = db.query(ContactImport).filter(
        ContactImport.organization_id == organization_id
    ).order_by(ContactImport.created_at.desc()).all()
    return imports

# Personalization endpoints
@router.post("/personalization/preview", response_model=PersonalizationPreviewResponse)
def preview_personalization(
    preview_request: PersonalizationPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview personalization for a contact"""
    try:
        # Get contact
        service = ContactService(db)
        contact = service.get_contact_by_id(preview_request.contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Create personalization service
        personalization_service = PersonalizationService(db)
        
        # Extract template variables
        template_variables = personalization_service.extract_template_variables(
            preview_request.html_content
        )
        
        # Resolve personalization variables
        personalization_vars = personalization_service.resolve_personalization_variables(
            contact, template_variables
        )
        
        # Personalize content
        personalized_html = personalization_service.personalize_html_content(
            preview_request.html_content, personalization_vars
        )
        
        # Get missing variables (for display purposes)
        missing_variables_dict = personalization_service.get_missing_variables(
            preview_request.html_content, [contact]
        )
        missing_variables = [f"{var} (missing for {', '.join(names)})" 
                           for var, names in missing_variables_dict.items()]
        
        return PersonalizationPreviewResponse(
            personalized_html=personalized_html,
            missing_variables=missing_variables
        )
    except PersonalizationServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/personalization/recipient-summary", response_model=RecipientSummaryResponse)
def get_recipient_summary(
    selection_request: RecipientSelectionRequest,
    organization_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a summary of selected recipients for sending"""
    try:
        service = ContactService(db)
        personalization_service = PersonalizationService(db)
        
        # Collect all recipients
        all_recipients = []
        recipient_sources = {"individual": 0, "group": 0, "manual": 0}
        processed_emails = set()
        invalid_recipients = []
        
        # Process individual contacts
        for contact_id in selection_request.recipient_ids:
            contact = service.get_contact_by_id(contact_id)
            if contact and not contact.is_suppressed:
                if contact.email not in processed_emails:
                    all_recipients.append(contact)
                    processed_emails.add(contact.email)
                    recipient_sources["individual"] += 1
            else:
                invalid_recipients.append(f"Contact {contact_id}")
        
        # Process group members
        for group_id in selection_request.group_ids:
            contacts = service.get_group_members(group_id)
            for contact in contacts:
                if contact.email not in processed_emails and not contact.is_suppressed:
                    all_recipients.append(contact)
                    processed_emails.add(contact.email)
                    recipient_sources["group"] += 1
        
        # Process manual emails
        for email in selection_request.manual_emails:
            normalized_email = service.normalize_email(email)
            if normalized_email:
                # Check if contact exists
                existing_contact = db.query(Contact).filter(
                    and_(
                        Contact.email == normalized_email,
                        Contact.organization_id == organization_id
                    )
                ).first()
                
                if existing_contact and not existing_contact.is_suppressed:
                    if existing_contact.email not in processed_emails:
                        all_recipients.append(existing_contact)
                        processed_emails.add(existing_contact.email)
                        recipient_sources["manual"] += 1
                elif not existing_contact:
                    # Would create temporary contact in real implementation
                    recipient_sources["manual"] += 1
            else:
                invalid_recipients.append(f"Invalid email: {email}")
        
        # For this example, we'll assume we have some HTML content to check
        # In a real implementation, this would come from the email being sent
        sample_html_content = "<p>Hello {{first_name}},</p><p>Welcome to {{event_name | default: 'our event'}}!</p>"
        
        # Check for missing personalization fields
        missing_fields = personalization_service.get_missing_variables(
            sample_html_content, all_recipients
        ) if all_recipients else {}
        
        return RecipientSummaryResponse(
            total_recipients=len(all_recipients),
            duplicate_count=len(selection_request.recipient_ids) + 
                          sum(len(service.get_group_members(gid)) for gid in selection_request.group_ids) + 
                          len(selection_request.manual_emails) - len(all_recipients),
            invalid_recipients=invalid_recipients,
            missing_personalization_fields=missing_fields,
            recipient_sources=recipient_sources
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))