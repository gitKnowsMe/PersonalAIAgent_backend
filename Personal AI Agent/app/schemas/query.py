from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator

class QueryBase(BaseModel):
    """Base query schema"""
    question: str = Field(..., min_length=1, max_length=5000, description="User question")
    document_id: Optional[int] = None
    
    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()

class QueryCreate(QueryBase):
    """Schema for creating a query"""
    pass

class Query(QueryBase):
    """Schema for a query"""
    id: int
    answer: str
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class QueryResponse(BaseModel):
    """Response schema for a query"""
    id: int
    question: str
    answer: str
    created_at: datetime 