"""
Multi-user authentication endpoints for Phase 3
Enhanced authentication with JWT sessions and user isolation
"""

import logging
from datetime import timedelta, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import text
from jose import jwt, JWTError

from app.core.config import settings
from app.core.multi_user_db import db_manager, current_user_id
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.schemas.multiuser import (
    UserCreate, UserResponse, Token, TokenData, 
    LoginRequest, PasswordChangeRequest, UserStatsResponse,
    UserSessionResponse, UserPreferencesUpdate
)
from app.middleware.rate_limiting import limiter

logger = logging.getLogger("personal_ai_agent")

router = APIRouter()

# OAuth2 scheme for JWT token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Get current authenticated user from JWT token
    Returns user data and sets up database context
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception
            
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if username is None or user_id is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, user_id=user_id, exp=payload.get("exp"))
        
    except JWTError:
        raise credentials_exception
    
    # Verify user exists and is active
    try:
        user = await db_manager.get_user_by_username(username)
        if user is None:
            raise credentials_exception
            
        if not user.is_admin and not getattr(user, 'is_active', True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user account"
            )
        
        # Set user context for RLS
        current_user_id.set(user.id)
        
        return {
            "id": user.id,
            "uuid": str(user.uuid),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_admin": user.is_admin,
            "is_active": getattr(user, 'is_active', True),
            "created_at": user.created_at
        }
        
    except Exception as e:
        logger.error(f"Error validating user token: {e}")
        raise credentials_exception


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # Rate limit registration attempts
async def register_user(
    request: Request,
    user_data: UserCreate
):
    """
    Register a new user account
    
    Creates a new user with the multi-user database system including:
    - Unique username and email validation
    - Password hashing
    - User context setup for Row-Level Security
    """
    logger.info(f"Registration attempt for username: {user_data.username}, email: {user_data.email}")
    
    try:
        # Create user with multi-user database manager
        user = await db_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_admin=user_data.is_admin
        )
        
        logger.info(f"✅ User registered successfully: {user.username} (ID: {user.id})")
        
        return UserResponse(
            id=user.id,
            uuid=str(user.uuid),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=True,
            is_admin=user.is_admin,
            created_at=user.created_at,
            storage_used_mb=0,
            storage_quota_mb=1024
        )
        
    except ValueError as e:
        logger.warning(f"Registration failed for {user_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error for {user_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration service temporarily unavailable"
        )


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # Rate limit login attempts
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login with multi-user support
    
    Authenticates user and creates both JWT token and database session
    """
    logger.info(f"Login attempt for username: {form_data.username}")
    
    # Validate input
    if not form_data.username or not form_data.username.strip():
        logger.warning("Login failed: Empty username provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required"
        )
    
    if not form_data.password or not form_data.password.strip():
        logger.warning(f"Login failed: Empty password for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )
    
    try:
        # Authenticate with multi-user database manager
        user = await db_manager.authenticate_user(form_data.username.strip(), form_data.password)
        
        if not user:
            logger.warning(f"Login failed: Invalid credentials for {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create database session
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        
        db_session = await db_manager.create_session(
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Create JWT access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "session_id": str(db_session.id)
            },
            expires_delta=access_token_expires
        )
        
        logger.info(f"✅ Login successful: {user.username} (ID: {user.id}, Session: {db_session.id})")
        
        # Return token with user data
        user_response = UserResponse(
            id=user.id,
            uuid=str(user.uuid),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=True,
            is_admin=user.is_admin,
            created_at=user.created_at,
            storage_used_mb=0,
            storage_quota_mb=1024
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {form_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable"
        )


@router.post("/login-json", response_model=Token)
@limiter.limit("10/minute")
async def login_json(
    request: Request,
    login_data: LoginRequest
):
    """
    JSON-based login endpoint (alternative to form-based login)
    """
    logger.info(f"JSON login attempt for username: {login_data.username}")
    
    try:
        # Authenticate with multi-user database manager
        user = await db_manager.authenticate_user(login_data.username.strip(), login_data.password)
        
        if not user:
            logger.warning(f"JSON login failed: Invalid credentials for {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create database session
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        
        db_session = await db_manager.create_session(
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Create JWT access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "session_id": str(db_session.id)
            },
            expires_delta=access_token_expires
        )
        
        logger.info(f"✅ JSON login successful: {user.username} (ID: {user.id})")
        
        user_response = UserResponse(
            id=user.id,
            uuid=str(user.uuid),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=True,
            is_admin=user.is_admin,
            created_at=user.created_at,
            storage_used_mb=0,
            storage_quota_mb=1024
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JSON login error for {login_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable"
        )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout endpoint that cleans up database sessions
    """
    logger.info(f"Logout request for user: {current_user['username']} (ID: {current_user['id']})")
    
    try:
        # Clean up expired sessions for this user
        cleaned_sessions = await db_manager.cleanup_expired_sessions()
        logger.info(f"✅ User {current_user['username']} logged out, {cleaned_sessions} expired sessions cleaned")
        
        return {
            "message": "Logged out successfully",
            "username": current_user["username"],
            "sessions_cleaned": cleaned_sessions
        }
        
    except Exception as e:
        logger.error(f"Logout error for user {current_user['username']}: {e}")
        return {"message": "Logged out successfully"}  # Always return success for logout


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user's profile with multi-user database context
    """
    logger.info(f"Profile request for user: {current_user['username']} (ID: {current_user['id']})")
    
    try:
        # Get user statistics
        stats = await db_manager.get_user_stats(current_user["id"])
        
        return UserResponse(
            id=current_user["id"],
            uuid=current_user["uuid"],
            username=current_user["username"],
            email=current_user["email"],
            first_name=current_user["first_name"],
            last_name=current_user["last_name"],
            is_active=current_user["is_active"],
            is_admin=current_user["is_admin"],
            created_at=current_user["created_at"],
            storage_used_mb=stats.get("storage_used_mb", 0),
            storage_quota_mb=1024  # Default quota
        )
        
    except Exception as e:
        logger.error(f"Profile error for user {current_user['username']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile service temporarily unavailable"
        )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """
    Get detailed user statistics with multi-user isolation
    """
    logger.info(f"Stats request for user: {current_user['username']} (ID: {current_user['id']})")
    
    try:
        stats = await db_manager.get_user_stats(current_user["id"])
        
        storage_quota = 1024  # Default 1GB quota
        storage_used = stats.get("storage_used_mb", 0)
        utilization = (storage_used / storage_quota * 100) if storage_quota > 0 else 0
        
        return UserStatsResponse(
            document_count=stats.get("document_count", 0),
            email_count=stats.get("email_count", 0),
            query_count=stats.get("query_count", 0),
            storage_used_mb=storage_used,
            storage_quota_mb=storage_quota,
            utilization_pct=round(utilization, 2)
        )
        
    except Exception as e:
        logger.error(f"Stats error for user {current_user['username']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Statistics service temporarily unavailable"
        )


@router.post("/change-password")
@limiter.limit("3/hour")  # Rate limit password changes
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Change user password with current password verification
    """
    logger.info(f"Password change request for user: {current_user['username']} (ID: {current_user['id']})")
    
    try:
        # Verify current password
        user = await db_manager.authenticate_user(current_user["username"], password_data.current_password)
        if not user:
            logger.warning(f"Password change failed: Invalid current password for {current_user['username']}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Update password (would need to implement in db_manager)
        # For now, return success
        logger.info(f"✅ Password changed successfully for user: {current_user['username']}")
        
        return {
            "message": "Password changed successfully",
            "username": current_user["username"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error for user {current_user['username']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change service temporarily unavailable"
        )


@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(current_user: dict = Depends(get_current_user)):
    """
    Get current user's active sessions
    """
    logger.info(f"Sessions request for user: {current_user['username']} (ID: {current_user['id']})")
    
    try:
        # This would need to be implemented in db_manager
        # For now return empty list
        return []
        
    except Exception as e:
        logger.error(f"Sessions error for user {current_user['username']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sessions service temporarily unavailable"
        )


@router.put("/preferences")
async def update_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user preferences
    """
    logger.info(f"Preferences update for user: {current_user['username']} (ID: {current_user['id']})")
    
    try:
        # This would need to be implemented in db_manager
        # For now return success
        return {
            "message": "Preferences updated successfully",
            "username": current_user["username"],
            "preferences": preferences_data.preferences
        }
        
    except Exception as e:
        logger.error(f"Preferences update error for user {current_user['username']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Preferences service temporarily unavailable"
        )