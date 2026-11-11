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