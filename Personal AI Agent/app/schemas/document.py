from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class DocumentBase(BaseModel):
    """Base document schema"""
    title: str
    description: Optional[str] = None

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