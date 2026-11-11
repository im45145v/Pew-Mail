from sqlalchemy import Column, String, Text, ForeignKey, Integer, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
import enum

class ValidationSeverity(str, enum.Enum):
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"

class ValidationCategory(str, enum.Enum):
    HTML = "html"
    LINK = "link"
    IMAGE = "image"
    CONTENT = "content"
    ACCESSIBILITY = "accessibility"
    RESPONSIVE = "responsive"

class ValidationResultStatus(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"

class ValidationRun(BaseModel):
    __tablename__ = "validation_runs"
    
    # Staging snapshot association
    staging_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("staging_snapshots.id"), nullable=False)
    
    # Overall score (0-100)
    score = Column(Integer, nullable=True)
    
    # Summary statistics
    error_count = Column(Integer, default=0, nullable=False)
    warning_count = Column(Integer, default=0, nullable=False)
    info_count = Column(Integer, default=0, nullable=False)
    
    def __repr__(self):
        return f"<ValidationRun(id={self.id}, staging_snapshot_id={self.staging_snapshot_id}, score={self.score})>"

class ValidationResult(BaseModel):
    __tablename__ = "validation_results"
    
    # Validation run association
    validation_run_id = Column(UUID(as_uuid=True), ForeignKey("validation_runs.id"), nullable=False)
    
    # Check identification
    check_id = Column(String, nullable=False)  # Unique identifier for the validation check
    category = Column(Enum(ValidationCategory), nullable=False)
    severity = Column(Enum(ValidationSeverity), nullable=False)
    status = Column(Enum(ValidationResultStatus), nullable=False)
    
    # Details
    description = Column(Text, nullable=False)
    affected_section_id = Column(String, nullable=True)  # Identifier of the section this affects
    suggested_resolution = Column(Text, nullable=True)
    
    # Raw data for debugging
    raw_data = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<ValidationResult(id={self.id}, check_id='{self.check_id}', severity={self.severity}, status={self.status})>"