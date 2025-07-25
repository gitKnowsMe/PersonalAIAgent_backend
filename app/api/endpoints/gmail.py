"""
Gmail API endpoints for OAuth2 authentication and email management
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.db.models import User, EmailAccount, Email
from app.schemas.email import (
    GmailAuthRequest,
    GmailAuthResponse,
    GmailSyncRequest,
    GmailSyncResponse,
    GmailStatusResponse,
    EmailAccountResponse,
    EmailResponse,
    EmailSearchRequest,
    EmailSearchResponse
)
from app.services.gmail_service import GmailService
from app.services.email.email_processor import EmailProcessor as NewEmailProcessor
from app.services.email.email_store import EmailStore
from app.services.email.email_classifier import EmailClassifier
from app.services.vector_store_service import get_vector_store_manager
from app.exceptions.email_exceptions import (
    EmailServiceError,
    AuthenticationError,
    AuthorizationError,
    TokenRefreshError,
    GmailApiError,
    RateLimitError,
    QuotaExceededError,
    NetworkError,
    EmailSyncError
)

logger = logging.getLogger("personal_ai_agent")

router = APIRouter(prefix="/gmail", tags=["gmail"])

# Initialize services
gmail_service = GmailService()
email_processor = NewEmailProcessor()
email_classifier = EmailClassifier()
email_store = EmailStore()
vector_store_manager = get_vector_store_manager()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login")


@router.get("/auth")
async def initiate_gmail_auth(
    token: Optional[str] = Query(None, description="Bearer token for authentication"),
    db: Session = Depends(get_db)
):
    """
    Initiate Gmail OAuth2 authentication by redirecting to Google
    """
    try:
        from fastapi.responses import RedirectResponse
        from fastapi import Request
        import uuid
        from jose import JWTError, jwt
        
        # Authenticate user from token parameter or header
        auth_token = token
        if not auth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token required. Please login first.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate token and get user
        try:
            payload = jwt.decode(
                auth_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        current_user = db.query(User).filter(User.username == username).first()
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        auth_url, state = gmail_service.get_authorization_url(settings.GMAIL_REDIRECT_URI)
        
        # Store user ID and state in database for callback retrieval
        # We'll use a simple approach: store in the database with expiration
        from app.db.models import OAuthSession
        
        # Clean up old sessions for this user
        db.query(OAuthSession).filter(
            OAuthSession.user_id == current_user.id,
            OAuthSession.provider == "gmail"
        ).delete()
        
        # Create new session with longer expiration to prevent timeouts
        oauth_session = OAuthSession(
            session_id=session_id,
            user_id=current_user.id,
            provider="gmail",
            oauth_state=state,
            redirect_uri=settings.GMAIL_REDIRECT_URI,
            expires_at=datetime.utcnow() + timedelta(minutes=60)  # 60 minute expiration
        )
        
        db.add(oauth_session)
        db.commit()
        
        logger.info(f"User {current_user.id} initiating Gmail OAuth with session: {session_id}")
        
        # Redirect to Google's OAuth page
        return RedirectResponse(url=auth_url, status_code=302)
        
    except NetworkError as e:
        logger.error(f"Network error initiating Gmail auth for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Network error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Error initiating Gmail auth for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Gmail authentication"
        )


@router.get("/auth-url")
async def get_gmail_auth_url(
    redirect_uri: str = Query(..., description="OAuth2 redirect URI"),
    current_user: User = Depends(get_current_user)
):
    """
    Get Gmail OAuth2 authorization URL
    """
    try:
        auth_url, state = gmail_service.get_authorization_url(redirect_uri)
        
        return {
            "authorization_url": auth_url,
            "state": state,
            "redirect_uri": redirect_uri
        }
        
    except NetworkError as e:
        logger.error(f"Network error getting Gmail auth URL for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Network error: {e.message}"
        )
    except GmailApiError as e:
        logger.error(f"Gmail API error getting auth URL for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gmail API error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Error getting Gmail auth URL for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )


@router.get("/callback")
async def gmail_oauth_callback(
    code: str = Query(..., description="OAuth2 authorization code"),
    state: str = Query(None, description="OAuth2 state parameter"),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth2 callback from Google
    """
    try:
        from fastapi.responses import HTMLResponse
        from app.db.models import OAuthSession
        
        # Find the OAuth session using the state parameter
        logger.info(f"OAuth callback: Looking for state parameter: {state}")
        
        # First, check if any sessions exist at all
        all_sessions = db.query(OAuthSession).filter(
            OAuthSession.provider == "gmail"
        ).all()
        logger.info(f"OAuth callback: Found {len(all_sessions)} total Gmail sessions in database")
        
        for session in all_sessions:
            logger.info(f"OAuth session: ID={session.id}, State={session.oauth_state}, UserID={session.user_id}, Expires={session.expires_at}")
        
        oauth_session = db.query(OAuthSession).filter(
            OAuthSession.oauth_state == state,
            OAuthSession.provider == "gmail",
            OAuthSession.expires_at > datetime.utcnow()
        ).first()
        
        if not oauth_session:
            logger.error(f"OAuth callback: Invalid or expired state parameter: {state}")
            # Also check if the session exists but is expired
            expired_session = db.query(OAuthSession).filter(
                OAuthSession.oauth_state == state,
                OAuthSession.provider == "gmail"
            ).first()
            if expired_session:
                logger.error(f"OAuth callback: Session found but expired. Expires at: {expired_session.expires_at}, Current time: {datetime.utcnow()}")
                error_msg = "oauth_session_expired"
            else:
                logger.error(f"OAuth callback: No session found with state: {state}")
                error_msg = "oauth_session_not_found"
            from fastapi.responses import RedirectResponse
            frontend_error_url = f"{settings.FRONTEND_URL}/gmail-callback?error={error_msg}&details=Gmail+OAuth+callback+failed"
            return RedirectResponse(url=frontend_error_url, status_code=302)
        
        # Get the user from the session
        user = db.query(User).filter(User.id == oauth_session.user_id).first()
        if not user:
            logger.error(f"OAuth callback: User not found for session: {oauth_session.session_id}")
            from fastapi.responses import RedirectResponse
            frontend_error_url = f"{settings.FRONTEND_URL}/gmail-callback?error=user_not_found"
            return RedirectResponse(url=frontend_error_url, status_code=302)
        
        # Exchange code for tokens and create/update email account
        email_account = gmail_service.exchange_code_for_tokens(
            auth_code=code,
            redirect_uri=settings.GMAIL_REDIRECT_URI,
            db=db,
            user=user
        )
        
        # Clean up the OAuth session
        db.delete(oauth_session)
        db.commit()
        
        logger.info(f"User {user.id} successfully authenticated Gmail account: {email_account.email_address}")
        
        # Redirect back to frontend Gmail callback page with success message
        from fastapi.responses import RedirectResponse
        frontend_url = f"{settings.FRONTEND_URL}/gmail-callback?gmail_connected={email_account.email_address}"
        logger.info(f"Redirecting to frontend Gmail callback: {frontend_url}")
        return RedirectResponse(url=frontend_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        from fastapi.responses import RedirectResponse
        frontend_error_url = f"{settings.FRONTEND_URL}/gmail-callback?error=oauth_failed&message={str(e)}"
        return RedirectResponse(url=frontend_error_url, status_code=302)


@router.post("/auth", response_model=GmailAuthResponse)
async def authenticate_gmail(
    request: GmailAuthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exchange OAuth2 authorization code for access tokens
    """
    try:
        # Exchange code for tokens and create/update email account
        email_account = gmail_service.exchange_code_for_tokens(
            auth_code=request.auth_code,
            redirect_uri=request.redirect_uri,
            db=db,
            user=current_user
        )
        
        logger.info(f"User {current_user.id} successfully authenticated Gmail account: {email_account.email_address}")
        
        return GmailAuthResponse(
            success=True,
            email_address=email_account.email_address,
            message="Gmail account connected successfully"
        )
        
    except AuthenticationError as e:
        logger.error(f"Gmail authentication error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e.message}"
        )
    except AuthorizationError as e:
        logger.error(f"Gmail authorization error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authorization failed: {e.message}"
        )
    except NetworkError as e:
        logger.error(f"Network error authenticating Gmail for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Network error: {e.message}"
        )
    except GmailApiError as e:
        logger.error(f"Gmail API error authenticating for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gmail API error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Error authenticating Gmail for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate Gmail account: {str(e)}"
        )


@router.post("/sync", response_model=GmailSyncResponse)
async def sync_gmail_emails(
    request: GmailSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync emails from Gmail account
    """
    try:
        # Get email account
        email_account = db.query(EmailAccount).filter(
            EmailAccount.id == request.account_id,
            EmailAccount.user_id == current_user.id,
            EmailAccount.is_active == True
        ).first()
        
        if not email_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email account not found or inactive"
            )
        
        # Sync emails
        sync_response = await gmail_service.sync_emails(
            email_account=email_account,
            db=db,
            max_emails=request.max_emails,
            sync_since=request.sync_since
        )
        
        # Check if sync was successful
        if not sync_response.success:
            error_details = "; ".join(sync_response.errors) if sync_response.errors else "Unknown sync error"
            logger.error(f"Gmail sync failed for user {current_user.id}: {error_details}")
            logger.error(f"Sync response details: success={sync_response.success}, emails_synced={sync_response.emails_synced}, errors={sync_response.errors}")
            
            # Provide more specific error messages based on common issues
            if "credentials" in error_details.lower() or "authentication" in error_details.lower():
                detail_message = f"Gmail authentication failed: {error_details}. Please try disconnecting and reconnecting your Gmail account."
                status_code = status.HTTP_401_UNAUTHORIZED
            elif "quota" in error_details.lower() or "rate limit" in error_details.lower():
                detail_message = f"Gmail API rate limit exceeded: {error_details}. Please try again in a few minutes."
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
            elif "permission" in error_details.lower() or "scope" in error_details.lower():
                detail_message = f"Gmail permission error: {error_details}. Please reconnect your Gmail account with proper permissions."
                status_code = status.HTTP_403_FORBIDDEN
            else:
                detail_message = f"Gmail sync failed: {error_details}"
                status_code = status.HTTP_400_BAD_REQUEST
            
            raise HTTPException(
                status_code=status_code,
                detail=detail_message
            )
        
        # Process and classify synced emails in background (don't wait)
        if sync_response.emails_synced > 0:
            # Start background task for email processing - don't await
            try:
                import asyncio
                task = asyncio.create_task(_process_synced_emails(email_account.id, current_user.id))
                # Add done callback to log any background task failures
                task.add_done_callback(lambda t: logger.error(f"Background email processing task failed: {t.exception()}") if t.exception() else None)
                logger.info(f"Started background processing task for {sync_response.emails_synced} emails")
            except Exception as background_error:
                # Background task creation failure should not affect sync response
                logger.error(f"Failed to start background email processing: {background_error}")
                logger.warning("Email sync completed, but background processing could not be started")
        
        logger.info(f"Synced {sync_response.emails_synced} emails for user {current_user.id}")
        
        return sync_response
        
    except HTTPException:
        raise
    except AuthenticationError as e:
        logger.error(f"Gmail authentication error during sync for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e.message}. Please reconnect your Gmail account."
        )
    except AuthorizationError as e:
        logger.error(f"Gmail authorization error during sync for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authorization failed: {e.message}. Please reconnect your Gmail account with proper permissions."
        )
    except RateLimitError as e:
        logger.error(f"Gmail rate limit during sync for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {e.message}. Please try again in a few minutes."
        )
    except QuotaExceededError as e:
        logger.error(f"Gmail quota exceeded during sync for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quota exceeded: {e.message}. Please try again later."
        )
    except NetworkError as e:
        logger.error(f"Network error during Gmail sync for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Network error: {e.message}. Please check your connection and try again."
        )
    except EmailSyncError as e:
        logger.error(f"Email sync error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sync error: {e.message}"
        )
    except Exception as e:
        # Import traceback for better error logging
        import traceback
        
        # Log full traceback for debugging
        logger.error(f"Unexpected error syncing Gmail emails for user {current_user.id}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Ensure we always return a structured error response
        error_detail = {
            "error": "internal_server_error",
            "message": "An unexpected error occurred during Gmail sync",
            "details": str(e) if str(e) else "Unknown error",
            "user_message": "Gmail sync failed due to an internal error. Please try again in a few moments."
        }
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get("/accounts", response_model=List[EmailAccountResponse])
async def get_email_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's Gmail accounts
    """
    try:
        accounts = db.query(EmailAccount).filter(
            EmailAccount.user_id == current_user.id
        ).all()
        
        return accounts
        
    except Exception as e:
        logger.error(f"Error getting email accounts for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve email accounts"
        )


@router.get("/status/{account_id}", response_model=GmailStatusResponse)
async def get_gmail_status(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Gmail account sync status
    """
    try:
        # Get email account
        email_account = db.query(EmailAccount).filter(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id
        ).first()
        
        if not email_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email account not found"
            )
        
        # Get email counts
        total_emails = db.query(Email).filter(
            Email.email_account_id == account_id,
            Email.user_id == current_user.id
        ).count()
        
        unread_emails = db.query(Email).filter(
            Email.email_account_id == account_id,
            Email.user_id == current_user.id,
            Email.is_read == False
        ).count()
        
        return GmailStatusResponse(
            account_id=email_account.id,
            email_address=email_account.email_address,
            is_connected=email_account.is_active,
            sync_enabled=email_account.sync_enabled,
            last_sync_at=email_account.last_sync_at,
            total_emails=total_emails,
            unread_emails=unread_emails,
            sync_errors=[]  # TODO: Implement error tracking
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Gmail status for user {current_user.id}, account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Gmail status"
        )


@router.delete("/disconnect/{account_id}")
async def disconnect_gmail_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect Gmail account and revoke tokens
    """
    try:
        # Get email account
        email_account = db.query(EmailAccount).filter(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id
        ).first()
        
        if not email_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email account not found"
            )
        
        # Disconnect account
        success = await gmail_service.disconnect_account(email_account, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to disconnect Gmail account"
            )
        
        logger.info(f"User {current_user.id} disconnected Gmail account: {email_account.email_address}")
        
        return {"message": "Gmail account disconnected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting Gmail account for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Gmail account"
        )


@router.get("/emails", response_model=List[EmailResponse])
async def get_emails(
    account_id: Optional[int] = Query(None, description="Filter by email account ID"),
    email_type: Optional[str] = Query(None, description="Filter by email type"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's emails with filtering
    """
    try:
        query = db.query(Email).filter(Email.user_id == current_user.id)
        
        if account_id:
            query = query.filter(Email.email_account_id == account_id)
        
        if email_type:
            query = query.filter(Email.email_type == email_type)
        
        emails = query.order_by(Email.sent_at.desc()).offset(offset).limit(limit).all()
        
        return emails
        
    except Exception as e:
        logger.error(f"Error getting emails for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve emails"
        )


@router.post("/chunking-preferences")
async def set_chunking_preferences(
    preferences: Dict,
    current_user: User = Depends(get_current_user)
):
    """
    Set user-specific email chunking preferences
    
    Example preferences:
    {
        "strategy": "preserve_payments",  # or "minimal", "comprehensive", "adaptive"
        "chunk_size": 400,
        "min_chunk_size": 20,
        "overlap": 50
    }
    """
    try:
        # Update processor preferences
        email_processor.set_user_chunking_preferences(current_user.id, preferences)
        
        logger.info(f"Updated chunking preferences for user {current_user.id}: {preferences}")
        
        return {
            "success": True,
            "message": "Chunking preferences updated successfully",
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Error updating chunking preferences for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chunking preferences"
        )


@router.get("/chunking-preferences")
async def get_chunking_preferences(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's current email chunking preferences
    """
    try:
        preferences = email_processor.get_user_chunking_config(current_user.id)
        
        return {
            "success": True,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Error getting chunking preferences for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chunking preferences"
        )


@router.post("/reprocess-emails")
async def reprocess_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reprocess all emails with updated chunking preferences
    """
    try:
        # Get all emails for user
        emails = db.query(Email).filter(
            Email.user_id == current_user.id
        ).all()
        
        # Reset vector namespaces to trigger reprocessing
        for email in emails:
            email.vector_namespace = None
        
        db.commit()
        
        # Trigger background reprocessing
        import asyncio
        task = asyncio.create_task(_process_synced_emails(1, current_user.id))  # Use first email account
        task.add_done_callback(lambda t: logger.error(f"Reprocessing task failed: {t.exception()}") if t.exception() else None)
        
        logger.info(f"Started reprocessing {len(emails)} emails for user {current_user.id}")
        
        return {
            "success": True,
            "message": f"Started reprocessing {len(emails)} emails with new preferences",
            "email_count": len(emails)
        }
        
    except Exception as e:
        logger.error(f"Error reprocessing emails for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start email reprocessing"
        )


@router.post("/search", response_model=EmailSearchResponse)
async def search_emails(
    request: EmailSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search emails using vector similarity
    """
    start_time = datetime.now()
    
    try:
        # Use vector store to search emails
        results = vector_store_manager.search_emails(
            user_id=current_user.id,
            query=request.query,
            email_type=request.email_type,
            sender_email=request.sender_email,
            date_from=request.date_from,
            date_to=request.date_to,
            limit=request.limit
        )
        
        # Get email objects from database
        email_ids = [result['email_id'] for result in results]
        emails = db.query(Email).filter(
            Email.id.in_(email_ids),
            Email.user_id == current_user.id
        ).all()
        
        # Sort emails by relevance score
        email_dict = {email.id: email for email in emails}
        sorted_emails = [email_dict[result['email_id']] for result in results if result['email_id'] in email_dict]
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return EmailSearchResponse(
            emails=sorted_emails,
            total_count=len(sorted_emails),
            query=request.query,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Error searching emails for user {current_user.id}: {e}")
        logger.error(f"Email search traceback: {traceback.format_exc()}")
        
        error_detail = {
            "error": "email_search_failed",
            "message": "Failed to search emails",
            "details": str(e) if str(e) else "Unknown error",
            "user_message": "Email search failed. Please try again."
        }
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


async def _process_synced_emails(email_account_id: int, user_id: int):
    """
    Process and classify newly synced emails using our email processing pipeline
    """
    from app.db.session_manager import background_session
    
    try:
        logger.info(f"Starting background email processing for account {email_account_id}, user {user_id}")
        
        with background_session() as db:
            # Get email account information
            email_account = db.query(EmailAccount).filter(EmailAccount.id == email_account_id).first()
            if not email_account:
                logger.error(f"Email account {email_account_id} not found for background processing")
                return
            
            # Get unprocessed emails (those without vector_namespace)
            unprocessed_emails = db.query(Email).filter(
                Email.email_account_id == email_account_id,
                Email.vector_namespace.is_(None)  # Not yet processed
            ).limit(50).all()  # Process in batches
            
            logger.info(f"Found {len(unprocessed_emails)} unprocessed emails for account {email_account.email_address}")
            
            # Process each email within the same session
            for email in unprocessed_emails:
                try:
                    # Convert database email to our email processing format
                    email_data = {
                        'message_id': email.message_id,
                        'subject': email.subject or '',
                        'sender': email.sender_email,
                        'recipient': email.recipient_emails,
                        'body_text': email.body_text or '',
                        'body_html': email.body_html or '',
                        'date': email.sent_at,
                        'attachments': []  # We'll handle attachments later
                    }
                    
                    # Simplified email type detection (no classification needed)
                    email.email_type = 'email'  # Simplified - all emails are just 'email'
                    
                    # Process email content for vector storage with user-aware chunking
                    processed_chunks = await email_processor.process_email(email_data, email.user_id)
                    
                    if processed_chunks:
                        # Generate unique email ID for storage
                        email_id = f"gmail_{email.id}"
                        
                        # Store in vector database
                        success = email_store.store_email_chunks(processed_chunks, email.user_id, email_id)
                        
                        if success:
                            # Update vector namespace
                            email.vector_namespace = f"user_{email.user_id}_email_{email_id}"
                            logger.info(f"Successfully processed email {email.id}: '{email.subject[:50]}...'")
                        else:
                            logger.error(f"Failed to store vector chunks for email {email.id}")
                    else:
                        logger.warning(f"No chunks generated for email {email.id}")
                    
                except Exception as e:
                    logger.error(f"Error processing email {email.id}: {e}")
                    continue
            
            # Session is automatically committed by the context manager
            logger.info(f"Processed {len(unprocessed_emails)} emails for account {email_account.email_address}")
        
    except Exception as e:
        import traceback
        logger.error(f"Error processing synced emails for account {email_account_id}, user {user_id}: {e}")
        logger.error(f"Background processing traceback: {traceback.format_exc()}")
        # Session rollback is handled automatically by the context manager
        # Background task failures should not affect the main sync response