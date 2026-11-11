from sqlalchemy import Column, String, Text
from app.models.base import BaseModel

class Organization(BaseModel):
    __tablename__ = "organizations"
    
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"