from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class QueryBase(BaseModel):
    """Base query schema"""
    question: str
    document_id: Optional[int] = None

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