from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.brand_profile import BrandProfile
from app.models.project import Project
from app.models.email.email import Email
from app.models.email.template import EmailTemplate
from app.models.organization import Organization
import json

class ContextAssembler:
    """Service for assembling relevant context for AI generation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_brand_context(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve brand guidelines for an organization"""
        brand_profile = self.db.query(BrandProfile).filter(
            BrandProfile.organization_id == organization_id
        ).first()
        
        if not brand_profile:
            return None
        
        return {
            "name": brand_profile.name,
            "colors": brand_profile.colors or {},
            "typography": brand_profile.typography or {},
            "communication": brand_profile.communication or {},
            "email_defaults": brand_profile.email_defaults or {},
            "guidelines": brand_profile.guidelines or {}
        }
    
    def get_project_context(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve project-specific context"""
        project = self.db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if not project:
            return None
        
        return {
            "name": project.name,
            "description": project.description,
            "instructions": project.instructions
        }
    
    def get_email_context(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve current email document context"""
        email = self.db.query(Email).filter(
            Email.id == email_id
        ).first()
        
        if not email:
            return None
        
        return {
            "name": email.name,
            "subject": email.subject,
            "preheader": email.preheader,
            "document": email.document,
            "status": email.status.value
        }
    
    def get_organization_context(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve organization context"""
        organization = self.db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not organization:
            return None
        
        return {
            "name": organization.name,
            "description": organization.description
        }
    
    def assemble_context(
        self, 
        organization_id: str,
        project_id: str, 
        email_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assemble all relevant context for AI generation
        
        Args:
            organization_id: Organization ID
            project_id: Project ID
            email_id: Optional email ID for existing email context
            
        Returns:
            Dictionary containing all relevant context
        """
        context = {
            "organization": self.get_organization_context(organization_id),
            "brand": self.get_brand_context(organization_id),
            "project": self.get_project_context(project_id)
        }
        
        if email_id:
            context["email"] = self.get_email_context(email_id)
        
        # Remove None values
        context = {k: v for k, v in context.items() if v is not None}
        
        return context

def format_context_for_prompt(context: Dict[str, Any]) -> str:
    """Format context for inclusion in AI prompts"""
    context_lines = []
    
    if "organization" in context:
        org = context["organization"]
        context_lines.append(f"Organization: {org.get('name', 'Unknown')}")
        if org.get("description"):
            context_lines.append(f"Organization Description: {org['description']}")
    
    if "brand" in context:
        brand = context["brand"]
        context_lines.append(f"Brand Name: {brand.get('name', 'Unknown')}")
        
        if brand.get("colors"):
            context_lines.append("Brand Colors:")
            for color_name, color_value in brand["colors"].items():
                context_lines.append(f"  {color_name}: {color_value}")
        
        if brand.get("typography"):
            context_lines.append("Typography:")
            for font_name, font_value in brand["typography"].items():
                context_lines.append(f"  {font_name}: {font_value}")
        
        if brand.get("communication"):
            context_lines.append("Communication Style:")
            for comm_key, comm_value in brand["communication"].items():
                context_lines.append(f"  {comm_key}: {comm_value}")
        
        if brand.get("guidelines"):
            context_lines.append("Brand Guidelines:")
            for guideline_key, guideline_value in brand["guidelines"].items():
                context_lines.append(f"  {guideline_key}: {guideline_value}")
    
    if "project" in context:
        project = context["project"]
        context_lines.append(f"Project: {project.get('name', 'Unnamed Project')}")
        if project.get("description"):
            context_lines.append(f"Project Description: {project['description']}")
        if project.get("instructions"):
            context_lines.append(f"Project Instructions: {project['instructions']}")
    
    if "email" in context:
        email = context["email"]
        context_lines.append(f"Current Email: {email.get('name', 'Untitled Email')}")
        context_lines.append(f"Subject: {email.get('subject', '')}")
        if email.get("preheader"):
            context_lines.append(f"Preheader: {email['preheader']}")
    
    if not context_lines:
        return "No specific brand or project context available."
    
    return "\n".join(context_lines)