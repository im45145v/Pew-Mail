from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
import uuid
import re

class DocumentOperation(BaseModel):
    """Represents a structured operation on an email document"""
    operation_type: str = Field(..., description="Type of operation (add_section, update_section, etc.)")
    section_id: Optional[str] = Field(None, description="ID of the section being operated on")
    parent_section_id: Optional[str] = Field(None, description="ID of parent section for hierarchical operations")
    data: Dict[str, Any] = Field(..., description="Operation-specific data")
    description: str = Field(..., description="Human-readable description of the operation")

class DocumentOperationValidator:
    """Validates document operations against the email schema"""
    
    @staticmethod
    def validate_operation(operation: DocumentOperation) -> bool:
        """Validate a document operation"""
        if not operation.operation_type:
            raise ValueError("Operation type is required")
        
        # Validate operation type
        valid_operations = [
            "add_section", "update_section", "remove_section", 
            "reorder_sections", "update_global_style", "update_metadata",
            "duplicate_section"
        ]
        
        if operation.operation_type not in valid_operations:
            raise ValueError(f"Invalid operation type: {operation.operation_type}")
        
        # Validate section ID for operations that require it
        if operation.operation_type in ["update_section", "remove_section", "duplicate_section"]:
            if not operation.section_id:
                raise ValueError(f"Section ID is required for {operation.operation_type}")
        
        # Validate data
        if not isinstance(operation.data, dict):
            raise ValueError("Operation data must be a dictionary")
        
        # Specific validations based on operation type
        if operation.operation_type == "add_section":
            return DocumentOperationValidator._validate_add_section(operation.data)
        elif operation.operation_type == "update_section":
            return DocumentOperationValidator._validate_update_section(operation.data)
        elif operation.operation_type == "update_metadata":
            return DocumentOperationValidator._validate_update_metadata(operation.data)
        elif operation.operation_type == "update_global_style":
            return DocumentOperationValidator._validate_update_global_style(operation.data)
        
        return True
    
    @staticmethod
    def _validate_add_section(data: Dict[str, Any]) -> bool:
        """Validate add_section operation data"""
        if "type" not in data:
            raise ValueError("Section type is required")
        
        if "props" not in data:
            raise ValueError("Section props are required")
        
        if not isinstance(data["props"], dict):
            raise ValueError("Section props must be a dictionary")
        
        # Validate common props
        DocumentOperationValidator._validate_section_props(data["props"])
        
        return True
    
    @staticmethod
    def _validate_update_section(data: Dict[str, Any]) -> bool:
        """Validate update_section operation data"""
        if not isinstance(data, dict):
            raise ValueError("Section update data must be a dictionary")
        
        # Validate props if present
        if "props" in data:
            DocumentOperationValidator._validate_section_props(data["props"])
        
        return True
    
    @staticmethod
    def _validate_update_metadata(data: Dict[str, Any]) -> bool:
        """Validate update_metadata operation data"""
        if not isinstance(data, dict):
            raise ValueError("Metadata must be a dictionary")
        
        # Validate specific metadata fields
        if "subject" in data and not isinstance(data["subject"], str):
            raise ValueError("Subject must be a string")
        
        if "preheader" in data and data["preheader"] is not None and not isinstance(data["preheader"], str):
            raise ValueError("Preheader must be a string or null")
        
        if "name" in data and not isinstance(data["name"], str):
            raise ValueError("Name must be a string")
        
        return True
    
    @staticmethod
    def _validate_update_global_style(data: Dict[str, Any]) -> bool:
        """Validate update_global_style operation data"""
        if not isinstance(data, dict):
            raise ValueError("Style data must be a dictionary")
        
        # Validate color formats if present
        for key, value in data.items():
            if "color" in key.lower() and value is not None:
                if not DocumentOperationValidator._is_valid_color(value):
                    raise ValueError(f"Invalid color format for {key}: {value}")
        
        return True
    
    @staticmethod
    def _validate_section_props(props: Dict[str, Any]) -> bool:
        """Validate common section properties"""
        # Validate URLs if present
        for key, value in props.items():
            if "url" in key.lower() and value is not None:
                if not isinstance(value, str) or not DocumentOperationValidator._is_valid_url(value):
                    raise ValueError(f"Invalid URL format for {key}: {value}")
            
            # Validate color formats
            if "color" in key.lower() and value is not None:
                if not DocumentOperationValidator._is_valid_color(value):
                    raise ValueError(f"Invalid color format for {key}: {value}")
        
        return True
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if a string is a valid URL"""
        # Simple URL validation - in a real app, you might want to use a more robust solution
        return isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))
    
    @staticmethod
    def _is_valid_color(color: str) -> bool:
        """Check if a string is a valid color format"""
        if not isinstance(color, str):
            return False
        
        # Hex color (#RRGGBB or #RGB)
        if re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color):
            return True
        
        # RGB color
        if re.match(r'^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$', color):
            return True
        
        # RGBA color
        if re.match(r'^rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[0-1]?\.?\d*\s*\)$', color):
            return True
        
        # Named colors (common ones)
        named_colors = [
            'black', 'silver', 'gray', 'white', 'maroon', 'red', 'purple', 'fuchsia',
            'green', 'lime', 'olive', 'yellow', 'navy', 'blue', 'teal', 'aqua',
            'orange', 'pink', 'brown', 'violet', 'indigo', 'turquoise'
        ]
        
        return color.lower() in named_colors

def apply_operations_to_document(document: Dict[str, Any], operations: List[DocumentOperation]) -> Dict[str, Any]:
    """Apply a list of operations to an email document"""
    # Create a deep copy of the document
    import copy
    result_document = copy.deepcopy(document)
    
    for operation in operations:
        # Validate operation before applying
        DocumentOperationValidator.validate_operation(operation)
        
        if operation.operation_type == "add_section":
            result_document = _apply_add_section(result_document, operation)
        elif operation.operation_type == "update_section":
            result_document = _apply_update_section(result_document, operation)
        elif operation.operation_type == "remove_section":
            result_document = _apply_remove_section(result_document, operation)
        elif operation.operation_type == "reorder_sections":
            result_document = _apply_reorder_sections(result_document, operation)
        elif operation.operation_type == "update_global_style":
            result_document = _apply_update_global_style(result_document, operation)
        elif operation.operation_type == "update_metadata":
            result_document = _apply_update_metadata(result_document, operation)
        elif operation.operation_type == "duplicate_section":
            result_document = _apply_duplicate_section(result_document, operation)
    
    return result_document

def _apply_add_section(document: Dict[str, Any], operation: DocumentOperation) -> Dict[str, Any]:
    """Apply add_section operation to document"""
    new_section = {
        "id": str(uuid.uuid4()),
        "type": operation.data["type"],
        "props": operation.data["props"]
    }
    
    document["sections"].append(new_section)
    return document

def _apply_update_section(document: Dict[str, Any], operation: DocumentOperation) -> Dict[str, Any]:
    """Apply update_section operation to document"""
    for i, section in enumerate(document["sections"]):
        if section["id"] == operation.section_id:
            # Update props
            if "props" in operation.data:
                section["props"].update(operation.data["props"])
            # Update type if specified
            if "type" in operation.data:
                section["type"] = operation.data["type"]
            break
    
    return document

def _apply_remove_section(document: Dict[str, Any], operation: DocumentOperation) -> Dict[str, Any]:
    """Apply remove_section operation to document"""
    document["sections"] = [
        section for section in document["sections"] 
        if section["id"] != operation.section_id
    ]
    return document

def _apply_reorder_sections(document: Dict[str, Any], operation: DocumentOperation) -> Dict[str, Any]:
    """Apply reorder_sections operation to document"""
    # This is a simplified implementation
    # In a real app, you'd want more sophisticated reordering logic
    if "new_order" in operation.data:
        section_map = {section["id"]: section for section in document["sections"]}
        document["sections"] = [
            section_map[section_id] for section_id in operation.data["new_order"]
            if section_id in section_map
        ]
    
    return document

def _apply_update_global_style(document: Dict[str, Any], operation: DocumentOperation) -> Dict[str, Any]:
    """Apply update_global_style operation to document"""
    document["settings"].update(operation.data)
    return document

def _apply_update_metadata(document: Dict[str, Any], operation: DocumentOperation) -> Dict[str, Any]:
    """Apply update_metadata operation to document"""
    document["metadata"].update(operation.data)
    return document

def _apply_duplicate_section(document: Dict[str, Any], operation: DocumentOperation) -> Dict[str, Any]:
    """Apply duplicate_section operation to document"""
    for section in document["sections"]:
        if section["id"] == operation.section_id:
            # Create a copy with new ID
            duplicated_section = {
                "id": str(uuid.uuid4()),
                "type": section["type"],
                "props": section["props"].copy()
            }
            document["sections"].append(duplicated_section)
            break
    
    return document