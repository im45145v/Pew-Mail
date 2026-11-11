from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import html
import re
from datetime import datetime
import logging

from app.models.contact import Contact
from app.models.personalization import PersonalizationSchema, RecipientSnapshot, PersonalizedEmail
from app.models.email.staging import StagingSnapshot
from app.models.email.google_account import GoogleSendHistory
from app.services.contacts.contact_service import ContactService
from app.services.email.rendering import email_rendering_service

logger = logging.getLogger(__name__)

class PersonalizationServiceError(Exception):
    """Custom exception for personalization service errors"""
    pass

class PersonalizationService:
    """Service for handling email personalization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.contact_service = ContactService(db)
    
    def escape_html(self, text: str) -> str:
        """Escape HTML characters to prevent XSS"""
        return html.escape(text) if text else ""
    
    def parse_template_variable(self, variable: str) -> tuple:
        """
        Parse a template variable like {{first_name | default: "there"}}
        
        Returns:
            Tuple of (variable_name, default_value)
        """
        # Remove {{ and }}
        var_content = variable.strip(" {}")
        
        # Split by |
        parts = var_content.split("|")
        variable_name = parts[0].strip()
        
        # Check for default value
        default_value = ""
        if len(parts) > 1:
            for part in parts[1:]:
                part = part.strip()
                if part.startswith("default:"):
                    # Extract default value, removing quotes if present
                    default_value = part[8:].strip().strip('"\'')
                    break
                    
        return variable_name, default_value
    
    def extract_template_variables(self, template_content: str) -> List[str]:
        """
        Extract all template variables from content
        
        Args:
            template_content: HTML content with template variables
            
        Returns:
            List of unique template variables
        """
        # Find all {{variable}} patterns
        pattern = r'\{\{[^}]+\}\}'
        variables = re.findall(pattern, template_content)
        # Return unique variables
        return list(set(variables))
    
    def resolve_personalization_variables(
        self,
        contact: Contact,
        template_variables: List[str]
    ) -> Dict[str, str]:
        """
        Resolve template variables for a specific contact
        
        Args:
            contact: Contact object
            template_variables: List of template variables to resolve
            
        Returns:
            Dictionary of variable names to resolved values
        """
        resolved = {}
        
        # Standard contact fields
        contact_fields = {
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'full_name': contact.full_name,
            'email': contact.email,
            'organization': contact.organization or "",
            'job_title': contact.job_title or "",
            'phone_number': contact.phone_number or ""
        }
        
        # Resolve each variable
        for variable in template_variables:
            var_name, default_value = self.parse_template_variable(variable)
            
            # Check standard fields first
            if var_name in contact_fields:
                value = contact_fields[var_name]
                resolved[var_name] = self.escape_html(value) if value else default_value
            # Check custom fields
            elif contact.custom_fields and var_name in contact.custom_fields:
                value = contact.custom_fields[var_name]
                resolved[var_name] = self.escape_html(str(value)) if value else default_value
            # Use default value
            else:
                resolved[var_name] = default_value
                
        return resolved
    
    def personalize_html_content(
        self,
        html_content: str,
        personalization_variables: Dict[str, str]
    ) -> str:
        """
        Substitute template variables in HTML content
        
        Args:
            html_content: HTML content with template variables
            personalization_variables: Dictionary of variables to substitute
            
        Returns:
            Personalized HTML content
        """
        personalized_content = html_content
        
        # Replace each variable
        for variable_pattern, value in personalization_variables.items():
            # Create the full pattern to match
            pattern = r'\{\{' + re.escape(variable_pattern) + r'(?:\s*\|\s*default\s*:\s*"[^"]*")?\s*\}\}'
            personalized_content = re.sub(pattern, value, personalized_content)
            
        return personalized_content
    
    def create_recipient_snapshot(
        self,
        staging_snapshot_id: str,
        contact: Contact
    ) -> RecipientSnapshot:
        """
        Create a recipient snapshot for personalization
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            contact: Contact object
            
        Returns:
            Created recipient snapshot
        """
        # Extract template variables from the staging snapshot HTML
        staging_snapshot = self.db.query(StagingSnapshot).filter(
            StagingSnapshot.id == staging_snapshot_id
        ).first()
        
        if not staging_snapshot:
            raise PersonalizationServiceError(f"Staging snapshot {staging_snapshot_id} not found")
        
        # Extract variables from HTML content
        template_variables = self.extract_template_variables(staging_snapshot.html_snapshot)
        
        # Resolve personalization variables
        personalization_vars = self.resolve_personalization_variables(contact, template_variables)
        
        # Create recipient data snapshot
        recipient_data = {
            'id': str(contact.id),
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'full_name': contact.full_name,
            'email': contact.email,
            'organization': contact.organization,
            'job_title': contact.job_title,
            'phone_number': contact.phone_number,
            'custom_fields': contact.custom_fields,
            'tags': contact.tags
        }
        
        # Create recipient snapshot
        recipient_snapshot = RecipientSnapshot(
            staging_snapshot_id=staging_snapshot_id,
            recipient_data=recipient_data,
            personalization_variables=personalization_vars
        )
        
        self.db.add(recipient_snapshot)
        self.db.commit()
        self.db.refresh(recipient_snapshot)
        
        return recipient_snapshot
    
    def generate_personalized_content(
        self,
        recipient_snapshot: RecipientSnapshot
    ) -> RecipientSnapshot:
        """
        Generate personalized HTML content for a recipient snapshot
        
        Args:
            recipient_snapshot: Recipient snapshot object
            
        Returns:
            Updated recipient snapshot with personalized content
        """
        # Get the staging snapshot
        staging_snapshot = self.db.query(StagingSnapshot).filter(
            StagingSnapshot.id == recipient_snapshot.staging_snapshot_id
        ).first()
        
        if not staging_snapshot:
            raise PersonalizationServiceError(f"Staging snapshot {recipient_snapshot.staging_snapshot_id} not found")
        
        # Personalize the HTML content
        personalized_html = self.personalize_html_content(
            staging_snapshot.html_snapshot,
            recipient_snapshot.personalization_variables
        )
        
        # Store the personalized content
        recipient_snapshot.personalized_html = personalized_html
        
        # Generate plain text version (simplified)
        # In a real implementation, we'd use a proper HTML to text converter
        plain_text = re.sub(r'<[^>]+>', '', personalized_html)
        plain_text = re.sub(r'\s+', ' ', plain_text).strip()
        recipient_snapshot.personalized_plain_text = plain_text
        
        self.db.commit()
        self.db.refresh(recipient_snapshot)
        
        return recipient_snapshot
    
    def prepare_recipients_for_send(
        self,
        staging_snapshot_id: str,
        recipient_ids: List[str],
        group_ids: List[str],
        manual_emails: List[str]
    ) -> List[RecipientSnapshot]:
        """
        Prepare recipients for email send by creating snapshots
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            recipient_ids: List of contact IDs
            group_ids: List of group IDs
            manual_emails: List of manually entered email addresses
            
        Returns:
            List of recipient snapshots
        """
        recipient_snapshots = []
        
        # Process individual contacts
        for contact_id in recipient_ids:
            contact = self.contact_service.get_contact_by_id(contact_id)
            if contact and not contact.is_suppressed:
                snapshot = self.create_recipient_snapshot(staging_snapshot_id, contact)
                recipient_snapshots.append(snapshot)
        
        # Process group members
        processed_contact_ids = set(recipient_ids)  # Avoid duplicates
        for group_id in group_ids:
            contacts = self.contact_service.get_group_members(group_id)
            for contact in contacts:
                if contact.id not in processed_contact_ids and not contact.is_suppressed:
                    snapshot = self.create_recipient_snapshot(staging_snapshot_id, contact)
                    recipient_snapshots.append(snapshot)
                    processed_contact_ids.add(contact.id)
        
        # Process manual emails (create temporary contacts)
        for email in manual_emails:
            # Check if this email already exists as a contact
            normalized_email = self.contact_service.normalize_email(email)
            existing_contact = self.db.query(Contact).filter(
                Contact.email == normalized_email
            ).first()
            
            if existing_contact and not existing_contact.is_suppressed:
                # Use existing contact if not suppressed
                if existing_contact.id not in processed_contact_ids:
                    snapshot = self.create_recipient_snapshot(staging_snapshot_id, existing_contact)
                    recipient_snapshots.append(snapshot)
                    processed_contact_ids.add(existing_contact.id)
            elif not existing_contact:
                # Create temporary contact for this send
                temp_contact = Contact(
                    first_name="",
                    last_name="",
                    email=normalized_email,
                    organization_id="",  # Will be set when we know the organization
                    custom_fields={},
                    tags=[],
                    source="manual_entry"
                )
                # For now, we'll skip manual emails that don't correspond to existing contacts
                # In a real implementation, we'd handle this differently
                pass
                
        return recipient_snapshots
    
    def create_personalized_emails(
        self,
        recipient_snapshots: List[RecipientSnapshot],
        staging_snapshot: StagingSnapshot,
        google_send_history: Optional[GoogleSendHistory] = None
    ) -> List[PersonalizedEmail]:
        """
        Create personalized email records for delivery
        
        Args:
            recipient_snapshots: List of recipient snapshots
            staging_snapshot: Staging snapshot
            google_send_history: Optional Google send history record
            
        Returns:
            List of personalized email records
        """
        personalized_emails = []
        
        for snapshot in recipient_snapshots:
            # Generate personalized content if not already done
            if not snapshot.personalized_html:
                self.generate_personalized_content(snapshot)
            
            # Get recipient email and name
            recipient_data = snapshot.recipient_data
            recipient_email = recipient_data.get('email', '')
            recipient_name = recipient_data.get('full_name', '')
            
            # Create personalized email record
            personalized_email = PersonalizedEmail(
                recipient_snapshot_id=snapshot.id,
                staging_snapshot_id=staging_snapshot.id,
                google_send_history_id=google_send_history.id if google_send_history else None,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                subject=staging_snapshot.subject,
                html_content=snapshot.personalized_html,
                plain_text_content=snapshot.personalized_plain_text,
                delivery_status="pending"
            )
            
            self.db.add(personalized_email)
            personalized_emails.append(personalized_email)
            
        self.db.commit()
        
        # Refresh all personalized emails
        for email in personalized_emails:
            self.db.refresh(email)
            
        return personalized_emails
    
    def get_missing_variables(
        self,
        html_content: str,
        sample_contacts: List[Contact]
    ) -> Dict[str, List[str]]:
        """
        Identify which variables are missing for sample contacts
        
        Args:
            html_content: HTML content with template variables
            sample_contacts: List of sample contacts to check
            
        Returns:
            Dictionary mapping variable names to list of contacts missing that variable
        """
        # Extract all template variables
        template_variables = self.extract_template_variables(html_content)
        
        # Parse variable names (without defaults)
        variable_names = []
        for var in template_variables:
            var_name, _ = self.parse_template_variable(var)
            variable_names.append(var_name)
        
        # Check which contacts are missing which variables
        missing_variables = {var: [] for var in variable_names}
        
        for contact in sample_contacts:
            resolved_vars = self.resolve_personalization_variables(contact, template_variables)
            for var_name, value in resolved_vars.items():
                # If value is empty and there's no default, consider it missing
                original_var = next((v for v in template_variables 
                                   if v.startswith('{{' + var_name)), None)
                _, default_value = self.parse_template_variable(original_var) if original_var else ('', '')
                
                if not value and not default_value:
                    # Find the original variable pattern in template to check for default
                    has_default = '|' in original_var if original_var else False
                    if not has_default:
                        missing_variables[var_name].append(contact.full_name)
        
        # Filter out variables that no one is missing
        return {k: v for k, v in missing_variables.items() if v}