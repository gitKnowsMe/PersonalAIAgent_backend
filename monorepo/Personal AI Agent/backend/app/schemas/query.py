from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator

class QueryBase(BaseModel):
    """Base query schema"""
    question: str = Field(..., min_length=1, max_length=5000, description="User question")
    
    # Legacy support - will be deprecated in favor of source_type/source_id
    document_id: Optional[int] = None
    
    # New unified source selection
    source_type: Optional[str] = Field(None, description="Type of source: 'all', 'document', or 'email_type'")
    source_id: Optional[str] = Field(None, description="ID of the source (document_id, email_type, or None for 'all')")
    
    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()
    
    @validator('source_type')
    def validate_source_type(cls, v):
        if v is not None and v not in ['all', 'document', 'email_type']:
            raise ValueError('source_type must be one of: all, document, email_type')
        return v

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
    from_cache: Optional[bool] = False
    response_time_ms: Optional[float] = None 