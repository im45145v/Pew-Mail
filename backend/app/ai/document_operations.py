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

def apply_operations_to_document(
    email_document: Dict[str, Any],
    operations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Apply a list of operations to an email document.
    
    Args:
        email_document: The current email document
        operations: List of operations to apply
        
    Returns:
        The updated email document
        
    Raises:
        ValueError: If an operation is invalid
    """
    # Make a deep copy of the document to avoid modifying the original
    updated_document = {
        **email_document,
        "sections": email_document["sections"].copy()
    }
    
    for operation_dict in operations:
        # Create a DocumentOperation instance
        try:
            operation = DocumentOperation(**operation_dict)
            DocumentOperationValidator.validate_operation(operation)
        except Exception as e:
            raise ValueError(f"Invalid operation: {str(e)}")
        
        # Apply the operation
        if operation.operation_type == "add_section":
            updated_document = _apply_add_section(updated_document, operation)
        elif operation.operation_type == "update_section":
            updated_document = _apply_update_section(updated_document, operation)
        elif operation.operation_type == "remove_section":
            updated_document = _apply_remove_section(updated_document, operation)
        elif operation.operation_type == "reorder_sections":
            updated_document = _apply_reorder_sections(updated_document, operation)
        elif operation.operation_type == "update_metadata":
            updated_document = _apply_update_metadata(updated_document, operation)
        elif operation.operation_type == "update_global_style":
            updated_document = _apply_update_global_style(updated_document, operation)
        elif operation.operation_type == "duplicate_section":
            updated_document = _apply_duplicate_section(updated_document, operation)
        else:
            raise ValueError(f"Unsupported operation type: {operation.operation_type}")
    
    return updated_document


def _apply_add_section(
    document: Dict[str, Any],
    operation: DocumentOperation
) -> Dict[str, Any]:
    """Apply an add_section operation to the document"""
    new_section = {
        "id": f"section-{uuid.uuid4()}",
        "type": operation.data["type"],
        "props": operation.data["props"]
    }
    
    # Create a copy of the document with updated sections
    updated_document = {
        **document,
        "sections": [
            *document["sections"],
            new_section
        ]
    }
    
    return updated_document


def _apply_update_section(
    document: Dict[str, Any],
    operation: DocumentOperation
) -> Dict[str, Any]:
    """Apply an update_section operation to the document"""
    updated_sections = []
    for section in document["sections"]:
        if section["id"] == operation.section_id:
            # Create an updated section
            updated_section = {
                **section,
                "props": {
                    **section["props"],
                    **operation.data["props"]
                }
            }
            updated_sections.append(updated_section)
        else:
            updated_sections.append(section)
    
    # Create a copy of the document with updated sections
    updated_document = {
        **document,
        "sections": updated_sections
    }
    
    return updated_document


def _apply_remove_section(
    document: Dict[str, Any],
    operation: DocumentOperation
) -> Dict[str, Any]:
    """Apply a remove_section operation to the document"""
    # Filter out the section to remove
    updated_sections = [
        section for section in document["sections"]
        if section["id"] != operation.section_id
    ]
    
    # Create a copy of the document with updated sections
    updated_document = {
        **document,
        "sections": updated_sections
    }
    
    return updated_document


def _apply_reorder_sections(
    document: Dict[str, Any],
    operation: DocumentOperation
) -> Dict[str, Any]:
    """Apply a reorder_sections operation to the document"""
    section_order = operation.data.get("order", [])
    
    if not section_order:
        raise ValueError("Section order is required for reorder_sections operation")
    
    # Create a mapping of section_id to section
    section_map = {section["id"]: section for section in document["sections"]}
    
    # Reorder sections according to the specified order
    updated_sections = []
    for section_id in section_order:
        if section_id in section_map:
            updated_sections.append(section_map[section_id])
    
    # Add any sections not in the order list at the end
    missing_sections = [
        section for section_id, section in section_map.items()
        if section_id not in section_order
    ]
    
    updated_sections.extend(missing_sections)
    
    # Create a copy of the document with updated sections
    updated_document = {
        **document,
        "sections": updated_sections
    }
    
    return updated_document


def _apply_update_metadata(
    document: Dict[str, Any],
    operation: DocumentOperation
) -> Dict[str, Any]:
    """Apply an update_metadata operation to the document"""
    updated_metadata = {
        **document["metadata"],
        **operation.data
    }
    
    # Create a copy of the document with updated metadata
    updated_document = {
        **document,
        "metadata": updated_metadata
    }
    
    return updated_document


def _apply_update_global_style(
    document: Dict[str, Any],
    operation: DocumentOperation
) -> Dict[str, Any]:
    """Apply an update_global_style operation to the document"""
    updated_settings = {
        **document["settings"],
        **operation.data
    }
    
    # Create a copy of the document with updated settings
    updated_document = {
        **document,
        "settings": updated_settings
    }
    
    return updated_document


def _apply_duplicate_section(
    document: Dict[str, Any],
    operation: DocumentOperation
) -> Dict[str, Any]:
    """Apply a duplicate_section operation to the document"""
    # Find the section to duplicate
    section_to_duplicate = next(
        (section for section in document["sections"] if section["id"] == operation.section_id),
        None
    )
    
    if not section_to_duplicate:
        raise ValueError(f"Section not found: {operation.section_id}")
    
    # Create a new section with a new ID
    duplicated_section = {
        **section_to_duplicate,
        "id": f"section-{uuid.uuid4()}"
    }
    
    # Insert the duplicated section after the original
    updated_sections = []
    for section in document["sections"]:
        updated_sections.append(section)
        if section["id"] == operation.section_id:
            updated_sections.append(duplicated_section)
    
    # Create a copy of the document with updated sections
    updated_document = {
        **document,
        "sections": updated_sections
    }
    
    return updated_document