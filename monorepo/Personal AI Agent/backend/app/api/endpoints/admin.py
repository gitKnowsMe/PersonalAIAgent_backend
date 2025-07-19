"""
Admin user management endpoints.

Provides administrative functionality for user management, system monitoring,
and security oversight. Requires admin privileges.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.db.database import get_db
from app.db.models import User
from app.core.security import get_current_user, require_admin, get_password_hash, verify_password
from app.utils.audit_logger import audit_admin_action, AuditEventType
from app.middleware.session_monitoring import get_session_monitor

logger = logging.getLogger("personal_ai_agent")
router = APIRouter()


# Pydantic models for admin endpoints
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False
    is_active: bool = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True


class SessionInfo(BaseModel):
    session_id: str
    ip_address: str
    user_agent: Optional[str]
    created_at: str
    last_activity: str
    request_count: int


class SystemStats(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    total_logins: int
    failed_logins: int
    active_sessions: int


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    return request.client.host if request.client else "unknown"


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all users in the system.
    
    Requires admin privileges. Supports pagination and search.
    """
    query = db.query(User)
    
    # Apply search filter if provided
    if search:
        query = query.filter(
            User.username.contains(search) | 
            User.email.contains(search)
        )
    
    users = query.offset(skip).limit(limit).all()
    
    # Audit the action
    audit_admin_action(
        admin_user_id=str(current_user.id),
        admin_username=current_user.username,
        action="list_users",
        details={"search": search, "count": len(users)},
        ip_address=get_client_ip(request)
    )
    
    logger.info(f"Admin {current_user.username} listed {len(users)} users")
    
    return [UserResponse.model_validate(user) for user in users]


@router.post("/users", response_model=UserResponse)
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new user.
    
    Requires admin privileges. Validates uniqueness and creates user with hashed password.
    """
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        audit_admin_action(
            admin_user_id=str(current_user.id),
            admin_username=current_user.username,
            action="create_user_failed",
            details={"reason": "user_exists", "attempted_username": user_data.username},
            ip_address=get_client_ip(request)
        )
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_admin=user_data.is_admin,
        is_active=user_data.is_active
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Audit the action
    audit_admin_action(
        admin_user_id=str(current_user.id),
        admin_username=current_user.username,
        action="create_user",
        target_user=new_user.username,
        details={"is_admin": user_data.is_admin, "is_active": user_data.is_active},
        ip_address=get_client_ip(request)
    )
    
    logger.info(f"Admin {current_user.username} created user {new_user.username}")
    
    return UserResponse.model_validate(new_user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get details for a specific user.
    
    Requires admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Audit the action
    audit_admin_action(
        admin_user_id=str(current_user.id),
        admin_username=current_user.username,
        action="get_user",
        target_user=user.username,
        ip_address=get_client_ip(request)
    )
    
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update a user's information.
    
    Requires admin privileges. Cannot modify the last admin user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent removing admin status from the last admin
    if user_update.is_admin is False and user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove admin status from the last admin user"
            )
    
    # Track changes for audit
    changes = {}
    if user_update.username is not None and user_update.username != user.username:
        changes["username"] = {"old": user.username, "new": user_update.username}
        user.username = user_update.username
    
    if user_update.email is not None and user_update.email != user.email:
        changes["email"] = {"old": user.email, "new": user_update.email}
        user.email = user_update.email
    
    if user_update.is_admin is not None and user_update.is_admin != user.is_admin:
        changes["is_admin"] = {"old": user.is_admin, "new": user_update.is_admin}
        user.is_admin = user_update.is_admin
    
    if user_update.is_active is not None and user_update.is_active != user.is_active:
        changes["is_active"] = {"old": user.is_active, "new": user_update.is_active}
        user.is_active = user_update.is_active
    
    if changes:
        db.commit()
        db.refresh(user)
        
        # Audit the action
        audit_admin_action(
            admin_user_id=str(current_user.id),
            admin_username=current_user.username,
            action="update_user",
            target_user=user.username,
            details={"changes": changes},
            ip_address=get_client_ip(request)
        )
        
        logger.info(f"Admin {current_user.username} updated user {user.username}")
    
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a user.
    
    Requires admin privileges. Cannot delete the last admin user or self.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting self
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Prevent deleting the last admin
    if user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last admin user"
            )
    
    username = user.username  # Store for audit log
    db.delete(user)
    db.commit()
    
    # Audit the action
    audit_admin_action(
        admin_user_id=str(current_user.id),
        admin_username=current_user.username,
        action="delete_user",
        target_user=username,
        ip_address=get_client_ip(request)
    )
    
    logger.info(f"Admin {current_user.username} deleted user {username}")
    
    return {"message": f"User {username} deleted successfully"}


@router.get("/sessions", response_model=List[SessionInfo])
async def list_active_sessions(
    request: Request,
    current_user: User = Depends(require_admin)
):
    """
    List all active sessions.
    
    Requires admin privileges. Shows current user sessions for monitoring.
    """
    session_monitor = get_session_monitor()
    sessions = []
    
    for session_id, session_data in session_monitor.active_sessions.items():
        sessions.append(SessionInfo(
            session_id=session_id,
            ip_address=session_data["ip_address"],
            user_agent=session_data.get("user_agent"),
            created_at=session_data["created_at"].isoformat(),
            last_activity=session_data["last_activity"].isoformat(),
            request_count=session_data["request_count"]
        ))
    
    # Audit the action
    audit_admin_action(
        admin_user_id=str(current_user.id),
        admin_username=current_user.username,
        action="list_sessions",
        details={"session_count": len(sessions)},
        ip_address=get_client_ip(request)
    )
    
    return sessions


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get system statistics.
    
    Requires admin privileges. Provides overview of system usage and security metrics.
    """
    # Database statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    
    # Session statistics
    session_monitor = get_session_monitor()
    analytics = session_monitor.get_analytics()
    
    stats = SystemStats(
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        total_logins=analytics["total_logins"],
        failed_logins=analytics["failed_logins"],
        active_sessions=analytics["active_sessions_count"]
    )
    
    # Audit the action
    audit_admin_action(
        admin_user_id=str(current_user.id),
        admin_username=current_user.username,
        action="get_stats",
        ip_address=get_client_ip(request)
    )
    
    return stats