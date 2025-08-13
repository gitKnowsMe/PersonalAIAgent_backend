"""
Multi-user schema definitions for Phase 3 API integration
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=255, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, max_length=255, description="First name")
    last_name: Optional[str] = Field(None, max_length=255, description="Last name")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    is_admin: bool = Field(False, description="Admin privileges flag")


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user data in responses"""
    id: int
    uuid: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    storage_used_mb: int
    storage_quota_mb: int
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class TokenData(BaseModel):
    """Token payload data"""
    username: str
    user_id: int
    exp: int


class UserSessionCreate(BaseModel):
    """Schema for creating user sessions"""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class UserSessionResponse(BaseModel):
    """Schema for user session data"""
    id: str
    user_id: int
    expires_at: datetime
    created_at: datetime
    last_accessed: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Schema for user statistics"""
    document_count: int
    email_count: int
    query_count: int
    storage_used_mb: int
    storage_quota_mb: int
    utilization_pct: float


class LoginRequest(BaseModel):
    """Schema for login requests (alternative to form data)"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class PasswordChangeRequest(BaseModel):
    """Schema for password change requests"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences"""
    preferences: dict = Field({}, description="User preferences as key-value pairs")