from pydantic import BaseModel, EmailStr, ConfigDict, Field, validator
from typing import Optional
from datetime import datetime

from app.core.constants import (
    USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH,
    PASSWORD_MIN_LENGTH, EMAIL_MAX_LENGTH
)

class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=EMAIL_MAX_LENGTH, description="User email address")
    username: str = Field(..., min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH, description="Username")

class UserCreate(UserBase):
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, description="User password")
    is_admin: bool = False
    
    @validator('username')
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {PASSWORD_MIN_LENGTH} characters long')
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int] = None  # Token expiration time in seconds 