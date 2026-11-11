import enum
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"

class Campaign(BaseModel):
    __tablename__ = "campaigns"
    
    # Campaign metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Project association
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    
    # Status
    status = Column(String, nullable=False)  # Using string instead of enum for flexibility
    
    # Timeline
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # Creator
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', project_id={self.project_id})>"

class CampaignEmail(BaseModel):
    __tablename__ = "campaign_emails"
    
    # Associations
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=False, index=True)
    
    __table_args__ = (
        # Ensure an email can only be associated with a campaign once
        {'sqlite_autoincrement': True},  # Only for SQLite
    )
    
    def __repr__(self):
        return f"<CampaignEmail(campaign_id={self.campaign_id}, email_id={self.email_id})>"