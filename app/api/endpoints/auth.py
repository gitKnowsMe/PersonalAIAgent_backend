from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.db.database import get_db
from app.db.models import User
from app.schemas.user import UserCreate, UserResponse, Token

# Get the logger
logger = logging.getLogger("personal_ai_agent")

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        is_admin=user_data.is_admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    
    Expected format: application/x-www-form-urlencoded
    Body: username=<username>&password=<password>
    """
    logger.info(f"Login attempt for username: {form_data.username}")
    
    # Validate input
    if not form_data.username or not form_data.username.strip():
        logger.warning("Login failed: Empty username provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not form_data.password or not form_data.password.strip():
        logger.warning(f"Login failed: Empty password for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user exists
    user = db.query(User).filter(User.username == form_data.username.strip()).first()
    if not user:
        logger.warning(f"Login failed: User '{form_data.username}' not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password. Please check your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login failed: User '{form_data.username}' is inactive")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled. Please contact support.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if password is correct
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed: Incorrect password for user '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password. Please check your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        logger.info(f"Login successful for username: '{form_data.username}' (User ID: {user.id})")
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
        }
    except Exception as e:
        logger.error(f"Token generation failed for user '{form_data.username}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable. Please try again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout():
    """
    Logout endpoint for JWT tokens.
    Since JWT tokens are stateless, logout is handled on the frontend by removing the token.
    This endpoint mainly serves as a confirmation and for logging purposes.
    """
    logger.info("User logged out successfully")
<<<<<<< HEAD
    return {"message": "Logged out successfully"} 
=======
    return {"message": "Logged out successfully"}


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile information
    
    Returns the authenticated user's profile data including:
    - username
    - email 
    - is_active status
    - is_admin status
    - created_at timestamp
    """
    logger.info(f"Profile requested for user: {current_user.username} (ID: {current_user.id})")
    
    return current_user 
>>>>>>> origin/fix/rate-limiting-and-search-improvements
