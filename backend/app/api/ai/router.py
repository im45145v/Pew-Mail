from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database.session import get_db
from app.ai.service import get_ai_service
from app.ai.document_operations import DocumentOperation
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/ai", tags=["ai"])

# Pydantic models for request/response
class GenerateEmailRequest(BaseModel):
    user_request: str
    organization_id: uuid.UUID
    project_id: uuid.UUID
    model: str = "gpt-4"
    temperature: float = 0.7

class ModifyEmailRequest(BaseModel):
    user_request: str
    email_id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    model: str = "gpt-4"
    temperature: float = 0.7

class ApplyOperationsRequest(BaseModel):
    operations: List[Dict[str, Any]]
    change_description: str
    author_id: uuid.UUID

class AIResponse(BaseModel):
    operations: List[Dict[str, Any]]
    explanation: str

class EmailResponse(BaseModel):
    email: Dict[str, Any]

class StreamRequest(BaseModel):
    conversation_history: List[Dict[str, str]]
    model: str = "gpt-4"
    temperature: float = 0.7

class StreamResponse(BaseModel):
    response: str

class GenerateAndModifyEmailRequest(BaseModel):
    user_request: str
    email_document: Optional[Dict[str, Any]] = None
    email_id: Optional[uuid.UUID] = None
    organization_id: uuid.UUID
    project_id: uuid.UUID
    model: str = "gpt-4"
    temperature: float = 0.7

@router.post("/generate-email", response_model=AIResponse)
async def generate_email(request: GenerateEmailRequest, db: Session = Depends(get_db)):
    """Generate a new email document from a natural language brief"""
    try:
        ai_service = get_ai_service(db)
        result = await ai_service.generate_email_from_brief(
            user_request=request.user_request,
            organization_id=str(request.organization_id),
            project_id=str(request.project_id),
            model=request.model,
            temperature=request.temperature
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating email: {str(e)}"
        )

@router.post("/modify-email", response_model=AIResponse)
async def modify_email(request: ModifyEmailRequest, db: Session = Depends(get_db)):
    """Modify an existing email document based on user request"""
    try:
        ai_service = get_ai_service(db)
        result = await ai_service.modify_existing_email(
            user_request=request.user_request,
            email_id=str(request.email_id),
            organization_id=str(request.organization_id),
            project_id=str(request.project_id),
            model=request.model,
            temperature=request.temperature
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error modifying email: {str(e)}"
        )

@router.post("/apply-operations", response_model=EmailResponse)
def apply_operations(
    email_id: uuid.UUID,
    request: ApplyOperationsRequest, 
    db: Session = Depends(get_db)
):
    """Apply proposed operations to an email document"""
    try:
        ai_service = get_ai_service(db)
        result = ai_service.apply_operations(
            email_id=str(email_id),
            operations=request.operations,
            change_description=request.change_description,
            author_id=str(request.author_id)
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying operations: {str(e)}"
        )

@router.post("/stream", response_model=StreamResponse)
async def stream_response(request: StreamRequest, db: Session = Depends(get_db)):
    """Stream a response from the AI model"""
    try:
        ai_service = get_ai_service(db)
        response_text = ""
        async for token in ai_service.stream_response(
            conversation_history=request.conversation_history,
            model=request.model,
            temperature=request.temperature
        ):
            response_text += token
        
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error streaming response: {str(e)}"
        )

@router.get("/skills")
def list_skills():
    """List all available AI skills"""
    from app.ai.skills import get_all_skills
    skills = get_all_skills()
    return {
        skill_id: skill.to_dict() 
        for skill_id, skill in skills.items()
    }

@router.get("/providers")
def list_providers():
    """List available AI providers"""
    return {
        "providers": [
            {
                "id": "openai",
                "name": "OpenAI Compatible",
                "description": "Any OpenAI-compatible API provider"
            }
        ]
    }

@router.post("/generate", response_model=AIResponse)
async def generate_email_operations(
    request: GenerateAndModifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Generate operations to create or modify an email document based on a user request.
    
    Args:
        request: {
            "user_request": "Create an email for a hackathon invitation",
            "email_document": {existing email document},  # Optional: existing email
            "email_id": "uuid",  # Optional: existing email ID
            "organization_id": "uuid",
            "project_id": "uuid",
            "model": "gpt-4",
            "temperature": 0.7
        }
        
    Returns:
        AIResponse: {
            "operations": [{"operation_type": "add_section", "data": {...}, "description": "Added hero section"}],
            "explanation": "I've created a compelling hero section and added a registration button."
        }
    """
    ai_service = get_ai_service(db)
    
    try:
        # Select relevant skills based on the request
        context = ai_service.context_assembler.assemble_context(
            str(request.organization_id),
            str(request.project_id)
        )
        
        skills = select_relevant_skills(request.user_request, context)
        
        # If email_document is provided, modify; otherwise, create new
        if request.email_document:
            operations = await ai_service.modify_email(
                request.user_request,
                request.email_document,
                skills,
                request.model,
                request.temperature
            )
        else:
            operations = await ai_service.generate_email_from_brief(
                request.user_request,
                str(request.organization_id),
                str(request.project_id),
                request.model,
                request.temperature
            )
        
        # Apply operations to the email document
        explanation = "I've processed your request and prepared the following changes:"
        
        return {
            "operations": operations,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate email operations: {str(e)}"
        )