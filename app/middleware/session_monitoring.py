"""
Session monitoring middleware for Personal AI Agent.

Tracks user sessions, login attempts, and provides security monitoring.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from collections import defaultdict, deque
from fastapi import Request, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.config import settings

logger = logging.getLogger("personal_ai_agent")


class SessionMonitor:
    """
    Monitors user sessions and login attempts for security purposes.
    
    Features:
    - Track active sessions per user
    - Monitor failed login attempts
    - Detect suspicious activity patterns
    - Provide session analytics
    """
    
    def __init__(self):
        # In-memory storage for session data
        # In production, this could be moved to Redis or database
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.failed_attempts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10))
        self.login_history: deque = deque(maxlen=1000)
        self.session_analytics: Dict[str, Any] = {
            "total_logins": 0,
            "failed_logins": 0,
            "unique_users": set(),
            "active_sessions_count": 0
        }
    
    def track_login_attempt(self, username: str, ip_address: str, success: bool, user_agent: str = None):
        """Track a login attempt"""
        attempt_data = {
            "username": username,
            "ip_address": ip_address,
            "success": success,
            "timestamp": datetime.now(),
            "user_agent": user_agent
        }
        
        self.login_history.append(attempt_data)
        
        if success:
            self.session_analytics["total_logins"] += 1
            self.session_analytics["unique_users"].add(username)
        else:
            self.session_analytics["failed_logins"] += 1
            self.failed_attempts[ip_address].append(attempt_data)
        
        # Log security events
        if success:
            logger.info(f"Successful login: {username} from {ip_address}")
        else:
            logger.warning(f"Failed login attempt: {username} from {ip_address}")
            
            # Check for brute force patterns
            if self.is_brute_force_attempt(ip_address):
                logger.error(f"Potential brute force attack from {ip_address}")
    
    def create_session(self, user_id: str, username: str, ip_address: str, user_agent: str = None) -> str:
        """Create a new user session"""
        session_id = f"{user_id}_{datetime.now().timestamp()}"
        
        session_data = {
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "request_count": 0
        }
        
        self.active_sessions[session_id] = session_data
        self.session_analytics["active_sessions_count"] = len(self.active_sessions)
        
        logger.info(f"Session created: {session_id} for user {username}")
        return session_id
    
    def update_session_activity(self, session_id: str, endpoint: str = None):
        """Update session activity"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session["last_activity"] = datetime.now()
            session["request_count"] += 1
            
            if endpoint:
                if "endpoints" not in session:
                    session["endpoints"] = defaultdict(int)
                session["endpoints"][endpoint] += 1
    
    def end_session(self, session_id: str):
        """End a user session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            duration = datetime.now() - session["created_at"]
            
            logger.info(f"Session ended: {session_id}, duration: {duration}")
            del self.active_sessions[session_id]
            self.session_analytics["active_sessions_count"] = len(self.active_sessions)
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Remove expired sessions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        expired_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            if session_data["last_activity"] < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.end_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def is_brute_force_attempt(self, ip_address: str, threshold: int = 5, time_window_minutes: int = 15) -> bool:
        """Check if IP address is performing brute force attacks"""
        if ip_address not in self.failed_attempts:
            return False
        
        recent_failures = []
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        for attempt in self.failed_attempts[ip_address]:
            if attempt["timestamp"] > cutoff_time:
                recent_failures.append(attempt)
        
        return len(recent_failures) >= threshold
    
    def get_user_sessions(self, user_id: str) -> list:
        """Get all active sessions for a user"""
        user_sessions = []
        for session_id, session_data in self.active_sessions.items():
            if session_data["user_id"] == user_id:
                user_sessions.append({
                    "session_id": session_id,
                    "ip_address": session_data["ip_address"],
                    "user_agent": session_data.get("user_agent"),
                    "created_at": session_data["created_at"],
                    "last_activity": session_data["last_activity"],
                    "request_count": session_data["request_count"]
                })
        return user_sessions
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get session analytics"""
        return {
            "total_logins": self.session_analytics["total_logins"],
            "failed_logins": self.session_analytics["failed_logins"],
            "unique_users_count": len(self.session_analytics["unique_users"]),
            "active_sessions_count": self.session_analytics["active_sessions_count"],
            "recent_failed_attempts": len([
                attempt for attempts in self.failed_attempts.values() 
                for attempt in attempts 
                if attempt["timestamp"] > datetime.now() - timedelta(hours=1)
            ])
        }


# Global session monitor instance
session_monitor = SessionMonitor()


async def session_monitoring_middleware(request: Request, call_next):
    """
    Middleware to monitor user sessions and activity.
    """
    start_time = datetime.now()
    
    # Extract request info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    endpoint = request.url.path
    
    # Process request
    response = await call_next(request)
    
    # Track session activity if user is authenticated
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # In a real implementation, you'd decode the JWT to get user info
        # For now, we'll create a simple session tracking
        session_id = f"session_{hash(auth_header)}_{ip_address}"
        session_monitor.update_session_activity(session_id, endpoint)
    
    # Log slow requests
    request_duration = (datetime.now() - start_time).total_seconds()
    if request_duration > 2.0:  # Log requests taking more than 2 seconds
        logger.warning(
            f"Slow request: {request.method} {endpoint} took {request_duration:.2f}s "
            f"from {ip_address}"
        )
    
    # Periodic cleanup
    if endpoint == "/api/health-check":  # Piggyback on health checks
        session_monitor.cleanup_expired_sessions()
    
    return response


def get_session_monitor() -> SessionMonitor:
    """Get the global session monitor instance"""
    return session_monitor