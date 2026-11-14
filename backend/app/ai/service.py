from typing import Dict, Any, List, Optional, AsyncGenerator
from sqlalchemy.orm import Session
import json
import logging
from app.ai.provider import get_ai_provider, AIProvider
from app.ai.skills import select_relevant_skills, get_all_skills
from app.ai.context import ContextAssembler, format_context_for_prompt
from app.ai.document_operations import DocumentOperation, apply_operations_to_document
from app.models.email.email import Email
from app.models.email.version import EmailVersion
from app.services.email.rendering import email_rendering_service
import uuid

logger = logging.getLogger(__name__)

class AIService:
    """Main AI service for PewPew email assistant"""
    
    def __init__(self, db: Session):
        self.db = db
        self.provider: AIProvider = get_ai_provider()
        self.context_assembler = ContextAssembler(db)
    
    async def generate_email_from_brief(
        self,
        user_request: str,
        organization_id: str,
        project_id: str,
        model: str = "gpt-4",
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate a new email document from a natural language brief
        
        Args:
            user_request: Natural language description of the email
            organization_id: Organization ID for brand context
            project_id: Project ID for project context
            model: AI model to use
            temperature: Temperature for generation creativity
            
        Returns:
            Dictionary containing the generated email document and operations
        """
        # Assemble context
        context = self.context_assembler.assemble_context(organization_id, project_id)
        context_text = format_context_for_prompt(context)
        
        # Select relevant skills
        skills = select_relevant_skills(user_request, context)
        skills_text = self._format_skills_for_prompt(skills)
        
        # Prepare the prompt
        prompt = self._create_generation_prompt(user_request, context_text, skills_text)
        
        # Generate response
        messages = [
            {"role": "system", "content": "You are PewPew, an AI email design assistant. Respond with structured JSON operations."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.provider.generate_response(
                messages=messages,
                model=model,
                temperature=temperature
            )
            
            # Parse the response
            return self._parse_ai_response(response)
        except Exception as e:
            logger.error(f"Error generating email from brief: {str(e)}")
            raise
    
    async def modify_existing_email(
        self,
        user_request: str,
        email_id: str,
        organization_id: str,
        project_id: str,
        model: str = "gpt-4",
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Modify an existing email document based on user request
        
        Args:
            user_request: Natural language description of the changes
            email_id: ID of the email to modify
            organization_id: Organization ID for brand context
            project_id: Project ID for project context
            model: AI model to use
            temperature: Temperature for generation creativity
            
        Returns:
            Dictionary containing the proposed operations
        """
        # Assemble context
        context = self.context_assembler.assemble_context(organization_id, project_id, email_id)
        context_text = format_context_for_prompt(context)
        
        # Get current email document
        email = self.db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise ValueError(f"Email with ID {email_id} not found")
        
        # Select relevant skills
        skills = select_relevant_skills(user_request, context)
        skills_text = self._format_skills_for_prompt(skills)
        
        # Prepare the prompt
        prompt = self._create_modification_prompt(
            user_request, 
            context_text, 
            skills_text, 
            email.document
        )
        
        # Generate response
        messages = [
            {"role": "system", "content": "You are PewPew, an AI email design assistant. Respond with structured JSON operations."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.provider.generate_response(
                messages=messages,
                model=model,
                temperature=temperature
            )
            
            # Parse the response
            return self._parse_ai_response(response)
        except Exception as e:
            logger.error(f"Error modifying existing email: {str(e)}")
            raise
    
    async def stream_response(
        self,
        conversation_history: List[Dict[str, str]],
        model: str = "gpt-4",
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from the AI model
        
        Args:
            conversation_history: List of messages in the conversation
            model: AI model to use
            temperature: Temperature for generation creativity
            
        Returns:
            Async generator yielding response tokens
        """
        system_message = {
            "role": "system", 
            "content": "You are PewPew, an AI email design assistant. Help users create and modify professional emails."
        }
        
        messages = [system_message] + conversation_history
        
        try:
            async for token in self.provider.stream_response(
                messages=messages,
                model=model,
                temperature=temperature
            ):
                yield token
        except Exception as e:
            logger.error(f"Error streaming AI response: {str(e)}")
            raise
    
    def apply_operations(
        self,
        email_id: str,
        operations: List[Dict[str, Any]],
        change_description: str,
        author_id: str
    ) -> Dict[str, Any]:
        """
        Apply proposed operations to an email document
        
        Args:
            email_id: ID of the email to modify
            operations: List of operations to apply
            change_description: Description of the changes
            author_id: ID of the author making the changes
            
        Returns:
            Updated email document
        """
        # Get the email
        email = self.db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise ValueError(f"Email with ID {email_id} not found")
        
        # Convert operations to DocumentOperation objects
        doc_operations = [
            DocumentOperation(**op) for op in operations
        ]
        
        # Apply operations to document
        updated_document = apply_operations_to_document(
            email.document, 
            doc_operations
        )
        
        # Render the updated document
        try:
            mjml_content, html_content, error = email_rendering_service.render_document_to_html(
                updated_document
            )
            
            if error:
                logger.warning(f"Error rendering email: {error}")
        except Exception as e:
            logger.error(f"Error rendering email: {str(e)}")
            mjml_content, html_content = None, None
        
        # Update the email
        email.document = updated_document
        email.mjml_content = mjml_content
        email.html_content = html_content
        
        # Create a new version
        email.version_count += 1
        self.db.commit()  # Commit to get the updated version_count
        
        db_version = EmailVersion(
            email_id=email.id,
            version_number=email.version_count,
            change_description=change_description,
            document_snapshot=updated_document,
            mjml_snapshot=mjml_content,
            html_snapshot=html_content,
            author_id=uuid.UUID(author_id)
        )
        self.db.add(db_version)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(email)
        
        return {
            "email": {
                "id": str(email.id),
                "name": email.name,
                "subject": email.subject,
                "preheader": email.preheader,
                "document": email.document,
                "mjml_content": email.mjml_content,
                "html_content": email.html_content,
                "status": email.status.value,
                "version_count": email.version_count
            }
        }
    
    async def modify_email(
        self,
        user_request: str,
        email_document: Dict[str, Any],
        skills: List[AISkill],
        model: str = "gpt-4",
        temperature: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Modify an existing email document based on a user request.
        
        Args:
            user_request: Natural language description of desired changes
            email_document: Current email document
            skills: List of relevant skills
            model: AI model to use
            temperature: Temperature for generation creativity
            
        Returns:
            List of operations to apply to the email document
        """
        # Assemble instructions for the AI
        skill_instructions = "\n".join([
            f"### {skill.name}:\n{skill.instructions}\n\n"
            for skill in skills
        ])
        
        # Format the prompt
        prompt = f"""
You are PewPew, an AI email design assistant for Pew Mail.

Here is the user's request:
"""
{user_request}
"""

Current email document:
{json.dumps(email_document, indent=2)}

Relevant skills:
{skill_instructions}

Based on the user's request, suggest specific operations to improve or modify the email.
Each operation should be a dict with:
- operation_type: the type of change (e.g., "add_section", "update_section", "delete_section", "update_settings")
- data: the data required for the operation
- description: a concise explanation of the change

Respond ONLY with a JSON array of operations. Do not include additional text.
"""
        
        # Call the AI provider
        response = await self.provider.generate_response(
            prompt=prompt,
            max_tokens=2000,
            temperature=temperature,
            model=model
        )
        
        # Parse the response
        try:
            operations = json.loads(response.strip())
            if not isinstance(operations, list):
                raise ValueError("Response is not a list of operations")
            return operations
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return []
            
    def _create_generation_prompt(
        self, 
        user_request: str, 
        context_text: str, 
        skills_text: str
    ) -> str:
        """Create a prompt for generating a new email"""
        return f"""
You are PewPew, an AI email design assistant. Your task is to create a professional email based on the user's request.

User Request:
{user_request}

Context:
{context_text}

Relevant Design Skills:
{skills_text}

Please create a structured email document that:
1. Addresses the user's request
2. Follows brand guidelines if provided
3. Applies appropriate design principles
4. Uses suitable email sections/components
5. Includes compelling content

Respond with a JSON object containing:
1. "operations": An array of structured operations to build the email
2. "explanation": A brief explanation of your design choices

Each operation should have:
- "operation_type": The type of operation (e.g., "add_section")
- "data": Operation-specific data
- "description": Human-readable description of what this operation does

Example section types: header, hero, heading, paragraph, image, button, divider, spacer, columns, social, footer, html

Important:
- Use appropriate placeholders for content that isn't specified
- Follow brand colors if provided
- Ensure the email is responsive and accessible
- Make the design visually appealing and professional
"""

    def _create_modification_prompt(
        self, 
        user_request: str, 
        context_text: str, 
        skills_text: str,
        current_document: Dict[str, Any]
    ) -> str:
        """Create a prompt for modifying an existing email"""
        return f"""
You are PewPew, an AI email design assistant. Your task is to modify an existing email based on the user's request.

User Request:
{user_request}

Context:
{context_text}

Relevant Design Skills:
{skills_text}

Current Email Document:
{json.dumps(current_document, indent=2)}

Please analyze the request and propose structured operations to modify the email.

Respond with a JSON object containing:
1. "operations": An array of structured operations to modify the email
2. "explanation": A brief explanation of your changes

Each operation should have:
- "operation_type": The type of operation (e.g., "update_section", "add_section", "remove_section")
- "section_id": ID of the section being modified (when applicable)
- "data": Operation-specific data
- "description": Human-readable description of what this operation does

Operation Types:
- "add_section": Add a new section to the email
- "update_section": Update properties of an existing section
- "remove_section": Remove a section from the email
- "reorder_sections": Change the order of sections
- "update_global_style": Update global styling settings
- "update_metadata": Update email metadata (subject, preheader, etc.)
- "duplicate_section": Duplicate an existing section

Important:
- Be specific about which sections you're modifying
- Only make changes that align with the user's request
- Preserve existing content unless explicitly asked to change it
- Follow brand guidelines if provided
- Ensure the email remains responsive and accessible
"""

    def _format_skills_for_prompt(self, skills: List[Any]) -> str:
        """Format skills for inclusion in AI prompts"""
        if not skills:
            return "No specific design skills applied."
        
        skill_lines = []
        for skill in skills:
            skill_lines.append(f"- {skill.name}: {skill.description}")
        
        return "\n".join(skill_lines)
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response and extract operations"""
        # Try to parse as JSON
        try:
            # Handle potential markdown code blocks
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            import json
            parsed_response = json.loads(response)
            
            # Validate required fields
            if "operations" not in parsed_response:
                raise ValueError("AI response missing 'operations' field")
            
            if not isinstance(parsed_response["operations"], list):
                raise ValueError("'operations' field must be an array")
            
            return parsed_response
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing AI response as JSON: {str(e)}")
            logger.error(f"Raw response: {response}")
            raise ValueError(f"AI response is not valid JSON: {response}")
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            raise

# Convenience function to get AI service
def get_ai_service(db: Session) -> AIService:
    """Get an instance of the AI service"""
    return AIService(db)