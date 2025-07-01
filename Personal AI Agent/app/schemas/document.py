from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator

from app.core.constants import TITLE_MAX_LENGTH, DESCRIPTION_MAX_LENGTH

class DocumentBase(BaseModel):
    """Base document schema"""
    title: str = Field(..., min_length=1, max_length=TITLE_MAX_LENGTH, description="Document title")
    description: Optional[str] = Field(None, max_length=DESCRIPTION_MAX_LENGTH, description="Document description")
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    pass

class Document(DocumentBase):
    """Schema for a document"""
    id: int
    file_name: str
    file_path: str
    vector_namespace: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    chunks_count: Optional[int] = None
    
    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: int
    file_path: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    vector_namespace: str
    owner_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True 