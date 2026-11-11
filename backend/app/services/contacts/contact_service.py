from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
import csv
import io
import json
import uuid
from datetime import datetime
import logging

from app.models.contact import Contact, ContactGroup, ContactGroupMembership, ContactImport
from app.models.organization import Organization
from app.services.email.rendering import email_rendering_service

logger = logging.getLogger(__name__)

class ContactServiceError(Exception):
    """Custom exception for contact service errors"""
    pass

class ContactService:
    """Service for managing contacts, groups, and personalization"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def normalize_email(self, email: str) -> str:
        """Normalize email address for comparison"""
        if not email:
            return ""
        return email.strip().lower()
    
    def check_duplicate_email(self, email: str, organization_id: str) -> Optional[Contact]:
        """Check if a contact with the same email already exists in the organization"""
        normalized_email = self.normalize_email(email)
        return self.db.query(Contact).filter(
            and_(
                Contact.email == normalized_email,
                Contact.organization_id == organization_id
            )
        ).first()
    
    def create_contact(
        self,
        organization_id: str,
        first_name: str,
        last_name: str,
        email: str,
        organization: Optional[str] = None,
        job_title: Optional[str] = None,
        phone_number: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        source: Optional[str] = "manual",
        consent_status: Optional[str] = None,
        consent_source: Optional[str] = None
    ) -> Contact:
        """
        Create a new contact
        
        Args:
            organization_id: ID of the organization
            first_name: First name of the contact
            last_name: Last name of the contact
            email: Email address (will be normalized)
            organization: Organization/company of the contact
            job_title: Job title of the contact
            phone_number: Phone number of the contact
            custom_fields: Dictionary of custom fields
            tags: List of tags
            notes: Notes about the contact
            source: Source of the contact (manual, csv_import, api)
            consent_status: Consent status
            consent_source: How consent was obtained
            
        Returns:
            The created contact
            
        Raises:
            ContactServiceError: If a contact with the same email already exists
        """
        # Normalize email
        normalized_email = self.normalize_email(email)
        
        # Check for duplicates
        existing_contact = self.check_duplicate_email(normalized_email, organization_id)
        if existing_contact:
            raise ContactServiceError(f"A contact with email '{email}' already exists in this organization")
        
        # Create the contact
        contact = Contact(
            first_name=first_name,
            last_name=last_name,
            email=normalized_email,
            organization=organization,
            job_title=job_title,
            phone_number=phone_number,
            organization_id=organization_id,
            custom_fields=custom_fields or {},
            tags=tags or [],
            notes=notes,
            source=source,
            consent_status=consent_status,
            consent_source=consent_source,
            consent_timestamp=datetime.utcnow() if consent_status else None
        )
        
        try:
            self.db.add(contact)
            self.db.commit()
            self.db.refresh(contact)
            return contact
        except IntegrityError as e:
            self.db.rollback()
            raise ContactServiceError(f"Failed to create contact: {str(e)}")
    
    def update_contact(
        self,
        contact_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        organization: Optional[str] = None,
        job_title: Optional[str] = None,
        phone_number: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        is_archived: Optional[bool] = None,
        consent_status: Optional[str] = None,
        consent_source: Optional[str] = None,
        is_suppressed: Optional[bool] = None
    ) -> Contact:
        """
        Update an existing contact
        
        Args:
            contact_id: ID of the contact to update
            Various optional fields to update
            
        Returns:
            The updated contact
            
        Raises:
            ContactServiceError: If contact not found or email conflict
        """
        contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise ContactServiceError(f"Contact with ID {contact_id} not found")
        
        # Check for email change and duplicates
        if email and email != contact.email:
            normalized_email = self.normalize_email(email)
            existing_contact = self.check_duplicate_email(normalized_email, contact.organization_id)
            if existing_contact and existing_contact.id != contact_id:
                raise ContactServiceError(f"A contact with email '{email}' already exists in this organization")
            contact.email = normalized_email
        
        # Update fields if provided
        if first_name is not None:
            contact.first_name = first_name
        if last_name is not None:
            contact.last_name = last_name
        if organization is not None:
            contact.organization = organization
        if job_title is not None:
            contact.job_title = job_title
        if phone_number is not None:
            contact.phone_number = phone_number
        if custom_fields is not None:
            contact.custom_fields = custom_fields
        if tags is not None:
            contact.tags = tags
        if notes is not None:
            contact.notes = notes
        if is_archived is not None:
            contact.is_archived = is_archived
        if is_suppressed is not None:
            contact.is_suppressed = is_suppressed
            
        # Handle consent updates
        if consent_status is not None:
            contact.consent_status = consent_status
            if consent_status and not contact.consent_timestamp:
                contact.consent_timestamp = datetime.utcnow()
        if consent_source is not None:
            contact.consent_source = consent_source
            
        try:
            self.db.commit()
            self.db.refresh(contact)
            return contact
        except IntegrityError as e:
            self.db.rollback()
            raise ContactServiceError(f"Failed to update contact: {str(e)}")
    
    def delete_contact(self, contact_id: str) -> bool:
        """
        Delete a contact
        
        Args:
            contact_id: ID of the contact to delete
            
        Returns:
            True if deleted, False if not found
        """
        contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return False
            
        # Delete group memberships first
        self.db.query(ContactGroupMembership).filter(
            ContactGroupMembership.contact_id == contact_id
        ).delete()
        
        # Delete the contact
        self.db.delete(contact)
        self.db.commit()
        return True
    
    def archive_contact(self, contact_id: str) -> Contact:
        """
        Archive a contact
        
        Args:
            contact_id: ID of the contact to archive
            
        Returns:
            The archived contact
        """
        return self.update_contact(contact_id, is_archived=True)
    
    def search_contacts(
        self,
        organization_id: str,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        group_id: Optional[str] = None,
        include_archived: bool = False
    ) -> List[Contact]:
        """
        Search contacts with various filters
        
        Args:
            organization_id: ID of the organization
            query: Search term (first name, last name, email, organization)
            tags: List of tags to filter by
            group_id: ID of group to filter by
            include_archived: Whether to include archived contacts
            
        Returns:
            List of matching contacts
        """
        query_builder = self.db.query(Contact).filter(
            Contact.organization_id == organization_id
        )
        
        # Filter out archived contacts unless requested
        if not include_archived:
            query_builder = query_builder.filter(Contact.is_archived == False)
            
        # Filter out suppressed contacts
        query_builder = query_builder.filter(Contact.is_suppressed == False)
        
        # Apply text search
        if query:
            search_term = f"%{query.lower()}%"
            query_builder = query_builder.filter(
                or_(
                    func.lower(Contact.first_name).like(search_term),
                    func.lower(Contact.last_name).like(search_term),
                    func.lower(Contact.email).like(search_term),
                    func.lower(Contact.organization).like(search_term)
                )
            )
        
        # Apply tag filter
        if tags:
            # This is a simplified approach. For complex tag queries, 
            # we'd need to use JSON operators
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(Contact.tags.contains([tag]))
            if tag_conditions:
                query_builder = query_builder.filter(or_(*tag_conditions))
        
        # Apply group filter
        if group_id:
            query_builder = query_builder.join(ContactGroupMembership).filter(
                ContactGroupMembership.group_id == group_id
            )
        
        return query_builder.all()
    
    def get_contact_by_id(self, contact_id: str) -> Optional[Contact]:
        """Get a contact by ID"""
        return self.db.query(Contact).filter(Contact.id == contact_id).first()
    
    def get_contact_groups(self, organization_id: str) -> List[ContactGroup]:
        """Get all contact groups for an organization"""
        return self.db.query(ContactGroup).filter(
            ContactGroup.organization_id == organization_id
        ).all()
    
    def create_contact_group(
        self,
        organization_id: str,
        name: str,
        description: Optional[str] = None
    ) -> ContactGroup:
        """Create a new contact group"""
        group = ContactGroup(
            name=name,
            description=description,
            organization_id=organization_id
        )
        
        try:
            self.db.add(group)
            self.db.commit()
            self.db.refresh(group)
            return group
        except IntegrityError as e:
            self.db.rollback()
            raise ContactServiceError(f"Failed to create group: {str(e)}")
    
    def update_contact_group(
        self,
        group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> ContactGroup:
        """Update a contact group"""
        group = self.db.query(ContactGroup).filter(ContactGroup.id == group_id).first()
        if not group:
            raise ContactServiceError(f"Group with ID {group_id} not found")
        
        if name is not None:
            group.name = name
        if description is not None:
            group.description = description
            
        try:
            self.db.commit()
            self.db.refresh(group)
            return group
        except IntegrityError as e:
            self.db.rollback()
            raise ContactServiceError(f"Failed to update group: {str(e)}")
    
    def delete_contact_group(self, group_id: str) -> bool:
        """Delete a contact group"""
        group = self.db.query(ContactGroup).filter(ContactGroup.id == group_id).first()
        if not group:
            return False
        
        # Delete group memberships first
        self.db.query(ContactGroupMembership).filter(
            ContactGroupMembership.group_id == group_id
        ).delete()
        
        # Delete the group
        self.db.delete(group)
        self.db.commit()
        return True
    
    def add_contact_to_group(self, contact_id: str, group_id: str) -> bool:
        """Add a contact to a group"""
        # Check if membership already exists
        existing = self.db.query(ContactGroupMembership).filter(
            and_(
                ContactGroupMembership.contact_id == contact_id,
                ContactGroupMembership.group_id == group_id
            )
        ).first()
        
        if existing:
            return True  # Already a member
            
        # Create new membership
        membership = ContactGroupMembership(
            contact_id=contact_id,
            group_id=group_id
        )
        
        try:
            self.db.add(membership)
            self.db.commit()
            return True
        except IntegrityError as e:
            self.db.rollback()
            raise ContactServiceError(f"Failed to add contact to group: {str(e)}")
    
    def remove_contact_from_group(self, contact_id: str, group_id: str) -> bool:
        """Remove a contact from a group"""
        membership = self.db.query(ContactGroupMembership).filter(
            and_(
                ContactGroupMembership.contact_id == contact_id,
                ContactGroupMembership.group_id == group_id
            )
        ).first()
        
        if not membership:
            return False  # Not a member
            
        self.db.delete(membership)
        self.db.commit()
        return True
    
    def get_group_members(self, group_id: str) -> List[Contact]:
        """Get all contacts in a group"""
        return self.db.query(Contact).join(ContactGroupMembership).filter(
            ContactGroupMembership.group_id == group_id
        ).all()
    
    def parse_csv_data(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse CSV content into a list of dictionaries"""
        # Using StringIO to treat string as file-like object
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        return list(reader)
    
    def validate_contact_data(
        self,
        data: Dict[str, Any],
        column_mapping: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate contact data based on column mapping
        
        Args:
            data: Row data from CSV
            column_mapping: Mapping of CSV columns to contact fields
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            csv_column = next((k for k, v in column_mapping.items() if v == field), None)
            if not csv_column or not data.get(csv_column, '').strip():
                errors.append(f"Missing required field: {field}")
        
        # Validate email format (basic check)
        email_field = next((k for k, v in column_mapping.items() if v == 'email'), None)
        if email_field and data.get(email_field):
            email = data[email_field].strip()
            if '@' not in email or '.' not in email.split('@')[-1]:
                errors.append(f"Invalid email format: {email}")
                
        return len(errors) == 0, errors
    
    def import_contacts_from_csv(
        self,
        organization_id: str,
        user_id: str,
        file_name: str,
        csv_content: str,
        column_mapping: Dict[str, str],
        skip_duplicates: bool = True,
        update_existing: bool = False
    ) -> ContactImport:
        """
        Import contacts from CSV data
        
        Args:
            organization_id: Organization ID
            user_id: User performing the import
            file_name: Name of the uploaded file
            csv_content: CSV content as string
            column_mapping: Mapping of CSV columns to contact fields
            skip_duplicates: Whether to skip duplicate contacts
            update_existing: Whether to update existing contacts
            
        Returns:
            ContactImport record with import results
        """
        # Parse CSV data
        rows = self.parse_csv_data(csv_content)
        
        # Create import record
        contact_import = ContactImport(
            organization_id=organization_id,
            user_id=user_id,
            file_name=file_name,
            total_records=len(rows),
            column_mapping=column_mapping
        )
        
        self.db.add(contact_import)
        self.db.flush()  # Get the ID
        
        # Initialize counters
        successful_records = 0
        updated_records = 0
        skipped_records = 0
        failed_records = 0
        error_details = []
        
        # Process each row
        for i, row in enumerate(rows):
            try:
                # Validate data
                is_valid, errors = self.validate_contact_data(row, column_mapping)
                if not is_valid:
                    failed_records += 1
                    error_details.append(f"Row {i+1}: {', '.join(errors)}")
                    continue
                
                # Map fields
                contact_data = {}
                custom_fields = {}
                
                for csv_column, contact_field in column_mapping.items():
                    value = row.get(csv_column, '').strip()
                    if not value:
                        continue
                        
                    if contact_field in ['first_name', 'last_name', 'email', 'organization', 
                                       'job_title', 'phone_number']:
                        contact_data[contact_field] = value
                    else:
                        # Treat as custom field
                        custom_fields[contact_field] = value
                        
                # Check for duplicates
                email = contact_data.get('email', '')
                existing_contact = self.check_duplicate_email(email, organization_id)
                
                if existing_contact:
                    if skip_duplicates:
                        skipped_records += 1
                        continue
                    elif update_existing:
                        # Update existing contact
                        self.update_contact(
                            existing_contact.id,
                            first_name=contact_data.get('first_name'),
                            last_name=contact_data.get('last_name'),
                            organization=contact_data.get('organization'),
                            job_title=contact_data.get('job_title'),
                            phone_number=contact_data.get('phone_number'),
                            custom_fields=custom_fields
                        )
                        updated_records += 1
                        continue
                
                # Create new contact
                self.create_contact(
                    organization_id=organization_id,
                    first_name=contact_data.get('first_name', ''),
                    last_name=contact_data.get('last_name', ''),
                    email=contact_data.get('email', ''),
                    organization=contact_data.get('organization'),
                    job_title=contact_data.get('job_title'),
                    phone_number=contact_data.get('phone_number'),
                    custom_fields=custom_fields,
                    source="csv_import"
                )
                successful_records += 1
                
            except Exception as e:
                failed_records += 1
                error_details.append(f"Row {i+1}: {str(e)}")
        
        # Update import record with results
        contact_import.successful_records = successful_records
        contact_import.updated_records = updated_records
        contact_import.skipped_records = skipped_records
        contact_import.failed_records = failed_records
        
        # If there are errors, create error report
        if error_details:
            # In a real implementation, we'd save this to a file
            # For now, we'll just store the count
            pass
            
        self.db.commit()
        self.db.refresh(contact_import)
        
        return contact_import