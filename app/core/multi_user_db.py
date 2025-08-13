"""
Phase 2: Multi-User Database Session Management
Personal AI Agent - SQLAlchemy implementation with Row-Level Security
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, AsyncGenerator, List, Callable

from sqlalchemy import text, func, and_, or_, event
from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    async_sessionmaker, 
    AsyncSession,
    AsyncEngine
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, Pool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, TimeoutError as SQLTimeoutError

from app.core.config import settings
from app.core.security import verify_password, get_password_hash

# Simple data classes for multi-user schema (until models are created)
class User:
    def __init__(self, id, uuid, username, email, first_name=None, last_name=None, is_admin=False, created_at=None, **kwargs):
        self.id = id
        self.uuid = uuid
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.is_admin = is_admin
        self.created_at = created_at

class UserSession:
    def __init__(self, id, user_id, session_token, expires_at, created_at=None, **kwargs):
        self.id = id
        self.user_id = user_id
        self.session_token = session_token
        self.expires_at = expires_at
        self.created_at = created_at

logger = logging.getLogger(__name__)

# Context variable for current user ID (used by RLS)
current_user_id: ContextVar[Optional[int]] = ContextVar('current_user_id', default=None)

class MultiUserDatabaseManager:
    """
    Multi-user database manager with Row-Level Security (RLS) support
    Handles user sessions, connection pooling, and data isolation
    """
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._pool_stats = {
            'connection_attempts': 0,
            'connection_failures': 0,
            'session_created': 0,
            'session_closed': 0,
            'health_check_failures': 0,
            'last_health_check': None,
            'total_query_time': 0.0,
            'query_count': 0
        }
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self) -> None:
        """Initialize database engine and connection pool with advanced features"""
        try:
            logger.info("🔧 Initializing enhanced multi-user database manager...")
            
            # Ensure we use asyncpg driver
            database_url = settings.DATABASE_URL
            if not database_url.startswith("postgresql+asyncpg://"):
                # Replace any postgresql:// or postgresql+psycopg2:// with asyncpg
                if "postgresql://" in database_url:
                    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
                elif "postgresql+psycopg2://" in database_url:
                    database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
            
            logger.info(f"🔧 Using database URL: {database_url.replace('://', '://***@')}")
            
            # Create async engine with advanced connection pooling
            self.engine = create_async_engine(
                database_url,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=settings.DATABASE_POOL_SIZE,  # Base pool size
                max_overflow=settings.DATABASE_MAX_OVERFLOW,  # Additional connections
                pool_timeout=settings.DATABASE_POOL_TIMEOUT,  # Timeout for getting connection
                pool_recycle=settings.DATABASE_POOL_RECYCLE,  # Recycle connections
                pool_pre_ping=True,  # Validate connections before use
                pool_reset_on_return='commit',  # Reset connections on return
                echo=settings.DEBUG,  # Log SQL queries in debug mode
                future=True,  # Use SQLAlchemy 2.0 style
                connect_args={
                    "server_settings": {
                        "application_name": "PersonalAIAgent_Multi",
                        "jit": "off",  # Disable JIT for better connection speed
                    }
                }
            )
            
            # Set up connection pool event listeners for monitoring
            self._setup_pool_events()
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # Test database connection
            await self._test_connection()
            
            # Initialize schema if needed
            await self._ensure_schema_ready()
            
            # Start background health monitoring
            self._health_check_task = asyncio.create_task(self._health_monitor_loop())
            
            logger.info(f"✅ Enhanced database manager initialized")
            logger.info(f"📊 Pool config: size={settings.DATABASE_POOL_SIZE}, overflow={settings.DATABASE_MAX_OVERFLOW}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database manager: {e}")
            raise
    
    async def _test_connection(self) -> None:
        """Test database connection and basic functionality"""
        async with self.engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            db_version = result.scalar()
            logger.info(f"📊 Database connection successful: {db_version}")
            
            # Test RLS functionality
            result = await conn.execute(text("SELECT current_user"))
            db_user = result.scalar()
            logger.info(f"🔒 Database user: {db_user}")
    
    def _setup_pool_events(self) -> None:
        """Set up SQLAlchemy pool event listeners for monitoring"""
        
        @event.listens_for(self.engine.sync_engine.pool, "connect")
        def on_connect(dbapi_conn, connection_record):
            """Handle new database connections"""
            self._pool_stats['connection_attempts'] += 1
            logger.debug("🔌 New database connection established")
            
        @event.listens_for(self.engine.sync_engine.pool, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            """Handle connection checkout from pool"""
            connection_record.info['checkout_time'] = time.time()
            logger.debug("📤 Connection checked out from pool")
            
        @event.listens_for(self.engine.sync_engine.pool, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            """Handle connection checkin to pool"""
            if 'checkout_time' in connection_record.info:
                checkout_time = connection_record.info.pop('checkout_time')
                usage_time = time.time() - checkout_time
                self._pool_stats['total_query_time'] += usage_time
                self._pool_stats['query_count'] += 1
            logger.debug("📥 Connection returned to pool")
            
        @event.listens_for(self.engine.sync_engine.pool, "reset")
        def on_reset(dbapi_conn, connection_record):
            """Handle connection reset"""
            logger.debug("🔄 Database connection reset")
            
        @event.listens_for(self.engine.sync_engine.pool, "invalidate")
        def on_invalidate(dbapi_conn, connection_record, exception):
            """Handle connection invalidation"""
            self._pool_stats['connection_failures'] += 1
            logger.warning(f"❌ Database connection invalidated: {exception}")
    
    async def _health_monitor_loop(self) -> None:
        """Background task to monitor database health"""
        logger.info("🏥 Starting database health monitor")
        
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(settings.DATABASE_HEALTH_CHECK_INTERVAL)
                await self._perform_health_check()
                
            except asyncio.CancelledError:
                logger.info("🏥 Health monitor cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")
                self._pool_stats['health_check_failures'] += 1
    
    async def _perform_health_check(self) -> bool:
        """Perform database health check"""
        try:
            start_time = time.time()
            
            # Simple connectivity test
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                
            # Pool status check
            pool_status = await self.get_connection_stats()
            
            # Log health metrics
            health_time = time.time() - start_time
            self._pool_stats['last_health_check'] = datetime.utcnow()
            
            logger.debug(f"💚 Health check passed ({health_time:.3f}s) - Pool: {pool_status['total_connections']}/{pool_status['pool_size']}")
            
            # Warning if pool usage is high
            if pool_status['total_connections'] > pool_status['pool_size'] * 0.8:
                logger.warning(f"⚠️ High pool usage: {pool_status['total_connections']}/{pool_status['pool_size']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            self._pool_stats['health_check_failures'] += 1
            return False

    async def _ensure_schema_ready(self) -> None:
        """Ensure database schema is ready for multi-user operations"""
        async with self.engine.begin() as conn:
            # Check if schema_versions table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'schema_versions'
                )
            """))
            
            schema_exists = result.scalar()
            if not schema_exists:
                logger.warning("⚠️ Multi-user schema not found - may need to run setup_multiuser_schema.sql")
            else:
                # Get current schema version
                result = await conn.execute(text("""
                    SELECT version FROM schema_versions 
                    ORDER BY applied_at DESC LIMIT 1
                """))
                current_version = result.scalar()
                logger.info(f"📋 Current schema version: {current_version}")
    
    @asynccontextmanager
    async def get_user_session(self, user_id: int) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with user context set for Row-Level Security
        
        Args:
            user_id: ID of the user for RLS context
            
        Yields:
            AsyncSession: Database session with user context
        """
        if not self.session_factory:
            raise RuntimeError("Database manager not initialized")
        
        session_start_time = time.time()
        session = None
        
        try:
            # Create new session
            session = self.session_factory()
            self._pool_stats['session_created'] += 1
            
            # Set user context for Row-Level Security
            await session.execute(
                text("SELECT set_config('app.current_user_id', :user_id, true)"),
                {"user_id": str(user_id)}
            )
            
            # Set context variable for application use
            current_user_id.set(user_id)
            
            logger.debug(f"🔒 Database session created for user {user_id}")
            
            yield session
            
        except (SQLAlchemyError, DisconnectionError, SQLTimeoutError) as e:
            logger.error(f"❌ Database session error for user {user_id}: {e}")
            self._pool_stats['connection_failures'] += 1
            if session:
                try:
                    await session.rollback()
                except Exception:
                    pass  # Ignore rollback errors during cleanup
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected session error for user {user_id}: {e}")
            if session:
                try:
                    await session.rollback()
                except Exception:
                    pass
            raise
        finally:
            if session:
                try:
                    await session.close()
                    self._pool_stats['session_closed'] += 1
                    session_duration = time.time() - session_start_time
                    logger.debug(f"🔒 Session closed for user {user_id} ({session_duration:.3f}s)")
                except Exception as e:
                    logger.warning(f"⚠️ Error closing session for user {user_id}: {e}")
            
            current_user_id.set(None)
    
    @asynccontextmanager
    async def get_admin_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session without RLS restrictions (admin access)
        
        Yields:
            AsyncSession: Database session with admin privileges
        """
        if not self.session_factory:
            raise RuntimeError("Database manager not initialized")
        
        session = self.session_factory()
        
        try:
            # Disable RLS for this session (admin access)
            await session.execute(text("SET row_security = off"))
            
            logger.debug("🛡️ Admin database session created")
            
            yield session
            
        finally:
            await session.close()
            logger.debug("🛡️ Admin database session closed")
    
    async def create_user(
        self, 
        username: str, 
        email: str, 
        password: str, 
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_admin: bool = False
    ) -> User:
        """
        Create new user account
        
        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
            first_name: Optional first name
            last_name: Optional last name
            is_admin: Whether user has admin privileges
            
        Returns:
            User: Created user object
        """
        async with self.get_admin_session() as session:
            try:
                # Check if username or email already exists
                existing_user = await session.execute(
                    text("SELECT id FROM users WHERE username = :username OR email = :email"),
                    {"username": username, "email": email}
                )
                
                if existing_user.first():
                    raise ValueError("Username or email already exists")
                
                # Create new user
                user_data = {
                    'uuid': str(uuid.uuid4()),
                    'username': username,
                    'email': email,
                    'password_hash': get_password_hash(password),
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_admin': is_admin,
                    'created_at': datetime.utcnow()
                }
                
                result = await session.execute(
                    text("""
                        INSERT INTO users (uuid, username, email, password_hash, first_name, last_name, is_admin, created_at)
                        VALUES (:uuid, :username, :email, :password_hash, :first_name, :last_name, :is_admin, :created_at)
                        RETURNING id, uuid, username, email, first_name, last_name, is_admin, created_at
                    """),
                    user_data
                )
                
                user_row = result.first()
                await session.commit()
                
                logger.info(f"👤 Created new user: {username} (ID: {user_row.id})")
                
                # Convert to User object (simplified)
                return User(
                    id=user_row.id,
                    uuid=user_row.uuid,
                    username=user_row.username,
                    email=user_row.email,
                    first_name=user_row.first_name,
                    last_name=user_row.last_name,
                    is_admin=user_row.is_admin,
                    created_at=user_row.created_at
                )
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Failed to create user {username}: {e}")
                raise
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username or email (without password verification)
        
        Args:
            username: Username or email
            
        Returns:
            User: User object if found, None otherwise
        """
        async with self.get_admin_session() as session:
            try:
                result = await session.execute(
                    text("""
                        SELECT id, uuid, username, email, first_name, last_name, is_admin, is_active, created_at
                        FROM users 
                        WHERE (username = :username OR email = :username) AND is_active = true
                    """),
                    {"username": username}
                )
                
                user_row = result.first()
                if not user_row:
                    return None
                
                return User(
                    id=user_row.id,
                    uuid=user_row.uuid,
                    username=user_row.username,
                    email=user_row.email,
                    first_name=user_row.first_name,
                    last_name=user_row.last_name,
                    is_admin=user_row.is_admin,
                    created_at=user_row.created_at
                )
                
            except Exception as e:
                logger.error(f"❌ Error getting user by username {username}: {e}")
                return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user credentials
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User: User object if authentication successful, None otherwise
        """
        async with self.get_admin_session() as session:
            try:
                # Find user by username or email
                result = await session.execute(
                    text("""
                        SELECT id, uuid, username, email, password_hash, first_name, last_name, is_admin, is_active, created_at
                        FROM users 
                        WHERE (username = :username OR email = :username) AND is_active = true
                    """),
                    {"username": username}
                )
                
                user_row = result.first()
                if not user_row:
                    logger.warning(f"🚫 Authentication failed: User not found: {username}")
                    return None
                
                # Verify password
                if not verify_password(password, user_row.password_hash):
                    logger.warning(f"🚫 Authentication failed: Invalid password for user: {username}")
                    return None
                
                # Update last login
                await session.execute(
                    text("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = :user_id"),
                    {"user_id": user_row.id}
                )
                await session.commit()
                
                logger.info(f"✅ User authenticated successfully: {username} (ID: {user_row.id})")
                
                return User(
                    id=user_row.id,
                    uuid=user_row.uuid,
                    username=user_row.username,
                    email=user_row.email,
                    first_name=user_row.first_name,
                    last_name=user_row.last_name,
                    is_admin=user_row.is_admin,
                    created_at=user_row.created_at
                )
                
            except Exception as e:
                logger.error(f"❌ Authentication error for user {username}: {e}")
                return None
    
    async def create_session(
        self, 
        user_id: int, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """
        Create new user session
        
        Args:
            user_id: User ID
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            
        Returns:
            UserSession: Created session object
        """
        async with self.get_admin_session() as session:
            try:
                session_data = {
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'session_token': str(uuid.uuid4()),
                    'expires_at': datetime.utcnow() + timedelta(hours=24),  # 24-hour sessions
                    'ip_address': ip_address,
                    'user_agent': user_agent
                }
                
                result = await session.execute(
                    text("""
                        INSERT INTO user_sessions (id, user_id, session_token, expires_at, ip_address, user_agent)
                        VALUES (:id, :user_id, :session_token, :expires_at, :ip_address, :user_agent)
                        RETURNING id, user_id, session_token, expires_at, created_at
                    """),
                    session_data
                )
                
                session_row = result.first()
                await session.commit()
                
                logger.info(f"🎫 Created session for user {user_id}: {session_row.session_token}")
                
                return UserSession(
                    id=session_row.id,
                    user_id=session_row.user_id,
                    session_token=session_row.session_token,
                    expires_at=session_row.expires_at,
                    created_at=session_row.created_at
                )
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Failed to create session for user {user_id}: {e}")
                raise
    
    async def get_user_by_session_token(self, session_token: str) -> Optional[User]:
        """
        Get user by session token
        
        Args:
            session_token: Session token
            
        Returns:
            User: User object if session valid, None otherwise
        """
        async with self.get_admin_session() as session:
            try:
                result = await session.execute(
                    text("""
                        SELECT u.id, u.uuid, u.username, u.email, u.first_name, u.last_name, u.is_admin, u.created_at
                        FROM users u
                        JOIN user_sessions s ON u.id = s.user_id
                        WHERE s.session_token = :token 
                          AND s.expires_at > CURRENT_TIMESTAMP 
                          AND s.is_active = true
                          AND u.is_active = true
                    """),
                    {"token": session_token}
                )
                
                user_row = result.first()
                if not user_row:
                    return None
                
                # Update last accessed
                await session.execute(
                    text("UPDATE user_sessions SET last_accessed = CURRENT_TIMESTAMP WHERE session_token = :token"),
                    {"token": session_token}
                )
                await session.commit()
                
                return User(
                    id=user_row.id,
                    uuid=user_row.uuid,
                    username=user_row.username,
                    email=user_row.email,
                    first_name=user_row.first_name,
                    last_name=user_row.last_name,
                    is_admin=user_row.is_admin,
                    created_at=user_row.created_at
                )
                
            except Exception as e:
                logger.error(f"❌ Error getting user by session token: {e}")
                return None
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            int: Number of sessions cleaned up
        """
        async with self.get_admin_session() as session:
            try:
                result = await session.execute(
                    text("DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP")
                )
                
                deleted_count = result.rowcount
                await session.commit()
                
                if deleted_count > 0:
                    logger.info(f"🧹 Cleaned up {deleted_count} expired sessions")
                
                return deleted_count
                
            except Exception as e:
                logger.error(f"❌ Error cleaning up expired sessions: {e}")
                return 0
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database connection pool statistics
        
        Returns:
            Dict: Detailed connection pool statistics
        """
        if not self.engine:
            return {"status": "not_initialized"}
        
        pool = self.engine.pool
        
        # Calculate averages
        avg_query_time = 0.0
        if self._pool_stats['query_count'] > 0:
            avg_query_time = self._pool_stats['total_query_time'] / self._pool_stats['query_count']
        
        return {
            # Basic pool metrics
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.checkedin() + pool.checkedout(),
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            
            # Pool utilization
            "utilization_pct": (pool.checkedout() / pool.size() * 100) if pool.size() > 0 else 0,
            "overflow_pct": (pool.overflow() / settings.DATABASE_MAX_OVERFLOW * 100) if settings.DATABASE_MAX_OVERFLOW > 0 else 0,
            
            # Performance metrics
            "connection_attempts": self._pool_stats['connection_attempts'],
            "connection_failures": self._pool_stats['connection_failures'],
            "session_created": self._pool_stats['session_created'],
            "session_closed": self._pool_stats['session_closed'],
            "avg_query_time_sec": round(avg_query_time, 3),
            "total_queries": self._pool_stats['query_count'],
            
            # Health metrics
            "health_check_failures": self._pool_stats['health_check_failures'],
            "last_health_check": self._pool_stats['last_health_check'],
            
            # Status
            "status": "healthy" if self._pool_stats['health_check_failures'] < 5 else "degraded"
        }
    
    async def get_detailed_pool_metrics(self) -> Dict[str, Any]:
        """
        Get detailed pool metrics including connection lifecycle information
        
        Returns:
            Dict: Detailed metrics for monitoring and debugging
        """
        stats = await self.get_connection_stats()
        
        # Additional calculated metrics
        failure_rate = 0.0
        if self._pool_stats['connection_attempts'] > 0:
            failure_rate = self._pool_stats['connection_failures'] / self._pool_stats['connection_attempts'] * 100
        
        session_balance = self._pool_stats['session_created'] - self._pool_stats['session_closed']
        
        return {
            **stats,
            "failure_rate_pct": round(failure_rate, 2),
            "session_balance": session_balance,  # Should be close to 0 for healthy pools
            "total_query_time_sec": round(self._pool_stats['total_query_time'], 3),
            "pool_config": {
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
                "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
                "pool_recycle": settings.DATABASE_POOL_RECYCLE,
                "health_check_interval": settings.DATABASE_HEALTH_CHECK_INTERVAL
            },
            "recommendations": self._get_pool_recommendations(stats)
        }
    
    def _get_pool_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate pool optimization recommendations"""
        recommendations = []
        
        # High utilization warning
        if stats.get('utilization_pct', 0) > 80:
            recommendations.append("Consider increasing DATABASE_POOL_SIZE - high pool utilization detected")
        
        # High overflow usage
        if stats.get('overflow_pct', 0) > 50:
            recommendations.append("Consider increasing DATABASE_POOL_SIZE - frequent overflow connections")
        
        # High failure rate
        if stats.get('connection_failures', 0) > stats.get('connection_attempts', 1) * 0.05:
            recommendations.append("High connection failure rate - check database connectivity")
        
        # Session leaks
        session_balance = stats.get('session_created', 0) - stats.get('session_closed', 0)
        if session_balance > 10:
            recommendations.append(f"Possible session leak detected - {session_balance} unclosed sessions")
        
        # Slow queries
        if stats.get('avg_query_time_sec', 0) > 1.0:
            recommendations.append("High average query time - consider query optimization")
        
        if not recommendations:
            recommendations.append("Pool performance is optimal")
        
        return recommendations
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get user statistics (document count, email count, etc.)
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: User statistics
        """
        async with self.get_user_session(user_id) as session:
            try:
                # Get document count (using correct table name and column)
                doc_result = await session.execute(
                    text("SELECT COUNT(*) FROM documents WHERE owner_id = :user_id"),
                    {"user_id": user_id}
                )
                document_count = doc_result.scalar() or 0
                
                # Get email count (using correct table name and column)
                email_result = await session.execute(
                    text("SELECT COUNT(*) FROM emails WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                email_count = email_result.scalar() or 0
                
                # Get query count (using correct table name and column)
                query_result = await session.execute(
                    text("SELECT COUNT(*) FROM queries WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                query_count = query_result.scalar() or 0
                
                # Calculate storage usage from document file sizes
                storage_result = await session.execute(
                    text("SELECT COALESCE(SUM(file_size), 0) FROM documents WHERE owner_id = :user_id"),
                    {"user_id": user_id}
                )
                storage_bytes = storage_result.scalar() or 0
                storage_used_mb = round(storage_bytes / (1024 * 1024), 2)
                
                return {
                    "document_count": document_count,
                    "email_count": email_count,
                    "query_count": query_count,
                    "storage_used_mb": storage_used_mb
                }
                
            except Exception as e:
                logger.error(f"❌ Error getting user stats for user {user_id}: {e}")
                return {
                    "document_count": 0,
                    "email_count": 0,
                    "query_count": 0,
                    "storage_used_mb": 0
                }
    
    async def close(self) -> None:
        """Close database connections and clean up resources"""
        logger.info("🔄 Shutting down database manager...")
        
        # Signal shutdown to health monitor
        self._shutdown_event.set()
        
        # Cancel health check task
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            logger.info("🏥 Health monitor stopped")
        
        # Close database engine
        if self.engine:
            # Log final stats
            final_stats = await self.get_connection_stats()
            logger.info(f"📊 Final pool stats: {final_stats['session_created']} created, {final_stats['session_closed']} closed")
            
            await self.engine.dispose()
            logger.info("📊 Database connections closed")
        
        logger.info("✅ Database manager shutdown complete")

# Global database manager instance
db_manager = MultiUserDatabaseManager()

# Dependency injection functions for FastAPI
async def get_current_user_db(user_id: int) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get user database session"""
    async with db_manager.get_user_session(user_id) as session:
        yield session

async def get_admin_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get admin database session"""
    async with db_manager.get_admin_session() as session:
        yield session