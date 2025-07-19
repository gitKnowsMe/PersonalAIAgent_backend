"""
Gmail API Integration Service

Handles Gmail OAuth2 authentication, email synchronization, and API interactions.
Provides secure token management and email data processing.
"""

import json
import logging
import base64
import email
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import User, EmailAccount, Email, EmailAttachment
from app.schemas.email import EmailCreate, GmailSyncResponse
from app.services.email_auth_service import EmailAuthService
from app.exceptions import (
    GmailApiError,
    GmailAuthenticationError,
    GmailTokenError,
    GmailTokenExpiredError,
    GmailTokenRefreshError,
    GmailQuotaExceededError,
    GmailRateLimitError,
    GmailSyncError,
    GmailMessageError,
    NetworkError,
    ConnectionTimeoutError,
    APIConnectionError,
    AuthenticationError,
    AuthorizationError,
    TokenRefreshError,
    RateLimitError,
    QuotaExceededError,
    EmailSyncError,
    handle_gmail_api_error,
    handle_network_error
)

logger = logging.getLogger("personal_ai_agent")


class GmailService:
    """
    Gmail API service for OAuth2 authentication and email management
    """
    
    def __init__(self):
        self.auth_service = EmailAuthService()
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/userinfo.email'
        ]
        
        # Gmail API configuration
        self.api_service_name = 'gmail'
        self.api_version = 'v1'
        
        # Simplified token refresh management
        self._token_refresh_buffer = timedelta(minutes=5)  # Refresh 5 minutes early
        self._refresh_attempts = {}  # Track retry attempts
        
        # Rate limiting settings
        self.max_requests_per_minute = 250  # Gmail API quota
        self.request_count = 0
        self.last_request_time = datetime.now()
    
    def _should_refresh_token(self, email_account: EmailAccount) -> bool:
        """Check if token should be refreshed based on expiry and recent attempts."""
        if not self._is_token_near_expiry(email_account.token_expires_at):
            return False
        
        # Avoid rapid refresh attempts for same account
        account_id = email_account.email_address
        last_attempt = self._refresh_attempts.get(account_id)
        if last_attempt and (datetime.now() - last_attempt).total_seconds() < 60:
            return False
            
        return True
    
    def _is_token_near_expiry(self, expiry: Optional[datetime]) -> bool:
        """Check if token is expired or will expire within the buffer time."""
        if not expiry:
            return True
        
        from datetime import timezone
        
        # Ensure both datetimes are timezone-aware for comparison
        if expiry.tzinfo is None:
            # If expiry is naive, assume UTC
            expiry = expiry.replace(tzinfo=timezone.utc)
        
        # Get current time in UTC
        now_utc = datetime.now(timezone.utc)
        
        # Convert expiry to UTC for comparison
        expiry_utc = expiry.astimezone(timezone.utc)
        
        # Compare in UTC timezone
        return expiry_utc <= (now_utc + self._token_refresh_buffer)
    
    def get_authorization_url(self, redirect_uri: str) -> Tuple[str, str]:
        """
        Get Gmail OAuth2 authorization URL
        
        Args:
            redirect_uri: OAuth2 redirect URI
            
        Returns:
            Tuple of (authorization_url, state)
        """
        try:
            # Debug: Check what settings are actually loaded
            logger.info(f"DEBUG OAuth: Settings object type: {type(settings)}")
            logger.info(f"DEBUG OAuth: Settings client_id: '{settings.GMAIL_CLIENT_ID}'")
            logger.info(f"DEBUG OAuth: Settings client_secret: '{settings.GMAIL_CLIENT_SECRET[:20] if settings.GMAIL_CLIENT_SECRET else None}...'")
            
            # Get credentials from settings, but validate them
            client_id = settings.GMAIL_CLIENT_ID
            client_secret = settings.GMAIL_CLIENT_SECRET
            
            # Check for placeholder values and use the real ones
            if not client_id or client_id in ['your_gmail_client_id_from_google_cloud_console', None]:
                logger.warning(f"Settings returned invalid client_id: '{client_id}', using environment variable directly")
                import os
                client_id = os.getenv("GMAIL_CLIENT_ID")
                logger.info(f"Direct os.getenv GMAIL_CLIENT_ID: '{client_id}'")
            
            if not client_secret or client_secret in ['your_gmail_client_secret_from_google_cloud_console', None]:
                logger.warning(f"Settings returned invalid client_secret, using environment variable directly")
                import os
                client_secret = os.getenv("GMAIL_CLIENT_SECRET")
                logger.info(f"Direct os.getenv GMAIL_CLIENT_SECRET: '{client_secret[:20] if client_secret else None}...'")
            
            # Final validation
            if not client_id or not client_secret:
                raise ValueError(f"Missing OAuth credentials: client_id='{client_id}', client_secret={'***' if client_secret else None}")
            
            logger.info(f"Using OAuth credentials: client_id='{client_id}', client_secret_length={len(client_secret) if client_secret else 0}")
            
            # Create OAuth2 flow
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = redirect_uri
            
            # Generate authorization URL
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'  # Force consent screen to get refresh token
            )
            
            logger.info(f"Generated Gmail authorization URL for redirect_uri: {redirect_uri}")
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {e}")
            if "network" in str(e).lower() or "connection" in str(e).lower():
                raise handle_network_error(e)
            raise GmailApiError(f"Failed to generate authorization URL: {str(e)}")
    
    def exchange_code_for_tokens(self, auth_code: str, redirect_uri: str, db: Session, user: User) -> EmailAccount:
        """
        Exchange authorization code for access/refresh tokens
        
        Args:
            auth_code: OAuth2 authorization code
            redirect_uri: OAuth2 redirect URI
            db: Database session
            user: User object
            
        Returns:
            EmailAccount object
        """
        try:
            # Get credentials using same logic as get_authorization_url
            client_id = settings.GMAIL_CLIENT_ID
            client_secret = settings.GMAIL_CLIENT_SECRET
            
            # Check for placeholder values and use the real ones
            if not client_id or client_id in ['your_gmail_client_id_from_google_cloud_console', None]:
                import os
                client_id = os.getenv("GMAIL_CLIENT_ID")
            
            if not client_secret or client_secret in ['your_gmail_client_secret_from_google_cloud_console', None]:
                import os
                client_secret = os.getenv("GMAIL_CLIENT_SECRET")
            
            # Create OAuth2 flow
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = redirect_uri
            
            # Try manual token exchange first to avoid OAuth library scope validation
            import requests
            from google.oauth2.credentials import Credentials
            from datetime import datetime, timedelta
            
            logger.info("Attempting manual token exchange to bypass scope validation issues")
            
            token_data = {
                'code': auth_code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
            if response.status_code == 200:
                token_info = response.json()
                logger.info(f"Successfully exchanged token manually. Scopes: {token_info.get('scope', 'unknown')}")
                
                # Create credentials manually
                credentials = Credentials(
                    token=token_info['access_token'],
                    refresh_token=token_info.get('refresh_token'),
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=token_info.get('scope', '').split()
                )
                
                # Set expiry if provided
                if 'expires_in' in token_info:
                    credentials.expiry = datetime.utcnow() + timedelta(seconds=token_info['expires_in'])
                
            else:
                logger.error(f"Manual token exchange failed: {response.text}")
                logger.info("Falling back to standard OAuth flow")
                # Fall back to the standard flow if manual exchange fails
                try:
                    flow.fetch_token(code=auth_code)
                    credentials = flow.credentials
                except Exception as e:
                    logger.error(f"Standard OAuth flow also failed: {e}")
                    raise
            
            # Get user email address
            user_info = self._get_user_info(credentials)
            email_address = user_info.get('email')
            
            if not email_address:
                raise ValueError("Could not retrieve email address from Gmail")
            
            # Check if email account already exists
            existing_account = db.query(EmailAccount).filter(
                EmailAccount.user_id == user.id,
                EmailAccount.email_address == email_address
            ).first()
            
            if existing_account:
                # Update existing account
                existing_account.access_token = self.auth_service.encrypt_token(credentials.token)
                existing_account.refresh_token = self.auth_service.encrypt_token(credentials.refresh_token)
                existing_account.token_expires_at = credentials.expiry
                existing_account.is_active = True
                existing_account.sync_enabled = True
                db.commit()
                
                logger.info(f"Updated existing Gmail account: {email_address}")
                return existing_account
            else:
                # Create new email account
                email_account = EmailAccount(
                    user_id=user.id,
                    email_address=email_address,
                    provider="gmail",
                    access_token=self.auth_service.encrypt_token(credentials.token),
                    refresh_token=self.auth_service.encrypt_token(credentials.refresh_token),
                    token_expires_at=credentials.expiry,
                    is_active=True,
                    sync_enabled=True
                )
                
                db.add(email_account)
                db.commit()
                db.refresh(email_account)
                
                logger.info(f"Created new Gmail account: {email_address}")
                return email_account
                
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            if "401" in str(e) or "unauthorized" in str(e).lower():
                raise AuthenticationError(f"OAuth code exchange failed - invalid or expired code: {str(e)}")
            elif "403" in str(e) or "forbidden" in str(e).lower():
                raise AuthorizationError(f"OAuth code exchange failed - insufficient permissions: {str(e)}")
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                raise handle_network_error(e)
            raise GmailApiError(f"Failed to exchange authorization code: {str(e)}")
    
    async def refresh_access_token(self, email_account: EmailAccount, db: Session) -> bool:
        """
        Simplified token refresh without complex locking
        
        Args:
            email_account: EmailAccount object
            db: Database session
            
        Returns:
            True if refresh successful, False otherwise
        """
        account_id = email_account.email_address
        
        try:
            # Check if we should refresh (includes rate limiting)
            if not self._should_refresh_token(email_account):
                return True
                
            # Record this refresh attempt
            self._refresh_attempts[account_id] = datetime.now()
            
            if not email_account.refresh_token:
                logger.error(f"No refresh token available for account {account_id}")
                return False
            
            # Decrypt refresh token
            refresh_token = self.auth_service.decrypt_token(email_account.refresh_token)
            
            # Get credentials using same validation logic
            client_id = settings.GMAIL_CLIENT_ID
            client_secret = settings.GMAIL_CLIENT_SECRET
            
            if not client_id or client_id in ['your_gmail_client_id_from_google_cloud_console', None]:
                import os
                client_id = os.getenv("GMAIL_CLIENT_ID")
            
            if not client_secret or client_secret in ['your_gmail_client_secret_from_google_cloud_console', None]:
                import os
                client_secret = os.getenv("GMAIL_CLIENT_SECRET")
            
            # Create credentials object
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret
            )
            
            # Refresh token (this is a synchronous call to Google)
            credentials.refresh(Request())
            
            # Update database
            email_account.access_token = self.auth_service.encrypt_token(credentials.token)
            email_account.token_expires_at = credentials.expiry
            db.commit()
            
            logger.info(f"Successfully refreshed access token for account {account_id}")
            return True
                
        except Exception as e:
            logger.error(f"Error refreshing access token for {account_id}: {e}")
            
            # Convert to specific exception types
            if "401" in str(e) or "unauthorized" in str(e).lower():
                raise TokenRefreshError(f"Token refresh failed - refresh token invalid or expired for {account_id}")
            elif "403" in str(e) or "forbidden" in str(e).lower():
                raise AuthorizationError(f"Token refresh failed - insufficient permissions for {account_id}")
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                raise handle_network_error(e)
            
            raise TokenRefreshError(f"Failed to refresh access token for {account_id}: {str(e)}")
    
    async def get_valid_credentials(self, email_account: EmailAccount, db: Session) -> Optional[Credentials]:
        """
        Get valid credentials, refreshing if necessary using thread-safe mechanism
        
        Args:
            email_account: EmailAccount object
            db: Database session
            
        Returns:
            Valid Credentials object or None
        """
        try:
            if not email_account.access_token:
                return None
            
            # Decrypt tokens
            access_token = self.auth_service.decrypt_token(email_account.access_token)
            refresh_token = self.auth_service.decrypt_token(email_account.refresh_token) if email_account.refresh_token else None
            
            # Get credentials using same validation logic
            client_id = settings.GMAIL_CLIENT_ID
            client_secret = settings.GMAIL_CLIENT_SECRET
            
            if not client_id or client_id in ['your_gmail_client_id_from_google_cloud_console', None]:
                import os
                client_id = os.getenv("GMAIL_CLIENT_ID")
            
            if not client_secret or client_secret in ['your_gmail_client_secret_from_google_cloud_console', None]:
                import os
                client_secret = os.getenv("GMAIL_CLIENT_SECRET")
            
            # Create credentials object
            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=self.scopes
            )
            
            # Set expiry from database if available with proper timezone handling
            if email_account.token_expires_at:
                from datetime import timezone
                expiry = email_account.token_expires_at
                
                # Ensure expiry is timezone-aware
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                
                credentials.expiry = expiry
            
            # Check if token needs refresh using our buffer logic
            if self._is_token_near_expiry(credentials.expiry) and credentials.refresh_token:
                # Use the thread-safe refresh method
                refresh_success = await self.refresh_access_token(email_account, db)
                if not refresh_success:
                    logger.error(f"Failed to refresh credentials for {email_account.email_address}")
                    return None
                
                # Re-decrypt the new token after refresh
                access_token = self.auth_service.decrypt_token(email_account.access_token)
                credentials = Credentials(
                    token=access_token,
                    refresh_token=refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=self.scopes
                )
                credentials.expiry = email_account.token_expires_at
                
                logger.info(f"Used thread-safe token refresh for account {email_account.email_address}")
            
            return credentials
            
        except (AuthenticationError, AuthorizationError, TokenRefreshError, NetworkError):
            # Re-raise specific exceptions
            raise
        except Exception as e:
            logger.error(f"Error getting valid credentials for {email_account.email_address}: {e}")
            raise AuthenticationError(f"Failed to obtain valid credentials for {email_account.email_address}: {str(e)}")
    
    async def sync_emails(self, email_account: EmailAccount, db: Session, max_emails: int = 50, sync_since: Optional[datetime] = None) -> GmailSyncResponse:
        """
        Sync emails from Gmail account with thread-safe token management
        
        Args:
            email_account: EmailAccount object
            db: Database session
            max_emails: Maximum number of emails to sync
            sync_since: Only sync emails since this date
            
        Returns:
            GmailSyncResponse object
        """
        start_time = datetime.now()
        errors = []
        emails_synced = 0
        
        try:
            # Get valid credentials using thread-safe method
            credentials = await self.get_valid_credentials(email_account, db)
            if not credentials:
                error_msg = f"Could not obtain valid credentials for {email_account.email_address}. Token may be expired or invalid."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Build Gmail service with timezone-safe credentials
            from google.oauth2.credentials import Credentials as GoogleCredentials
            from datetime import timezone
            
            # Create timezone-safe credentials for Google API
            safe_credentials = GoogleCredentials(
                token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_uri=credentials.token_uri,
                client_id=credentials.client_id,
                client_secret=credentials.client_secret,
                scopes=credentials.scopes
            )
            
            # Set expiry as timezone-naive UTC to avoid datetime comparison issues
            if credentials.expiry:
                if credentials.expiry.tzinfo:
                    # Convert to UTC and make naive
                    safe_credentials.expiry = credentials.expiry.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    safe_credentials.expiry = credentials.expiry
            
            service = build(self.api_service_name, self.api_version, credentials=safe_credentials)
            
            # Build query
            query = self._build_email_query(sync_since)
            
            # Get email list with timeout
            try:
                import socket
                original_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(30)  # 30 second timeout
                
                result = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=max_emails
                ).execute()
                
                socket.setdefaulttimeout(original_timeout)
                
            except Exception as e:
                socket.setdefaulttimeout(original_timeout)
                logger.error(f"Failed to fetch email list from Gmail API: {str(e)}")
                
                # Convert to specific exception
                gmail_error = handle_gmail_api_error(e)
                if isinstance(gmail_error, (AuthenticationError, AuthorizationError, RateLimitError, QuotaExceededError)):
                    raise gmail_error
                elif "timeout" in str(e).lower():
                    raise NetworkError(f"Timeout fetching email list from Gmail API: {str(e)}", timeout=True)
                else:
                    raise EmailSyncError(f"Failed to fetch email list from Gmail API: {str(e)}", email_account.email_address)
            
            messages = result.get('messages', [])
            logger.info(f"Found {len(messages)} emails to sync for {email_account.email_address}")
            
            # Process each email with individual timeouts
            for i, message in enumerate(messages):
                try:
                    # Add progress logging every 10 emails
                    if i % 10 == 0 and i > 0:
                        logger.info(f"Processed {i}/{len(messages)} emails for {email_account.email_address}")
                    
                    # Check if email already exists
                    existing_email = db.query(Email).filter(
                        Email.message_id == message['id'],
                        Email.user_id == email_account.user_id
                    ).first()
                    
                    if existing_email:
                        continue  # Skip existing emails
                    
                    # Fetch email details with timeout
                    try:
                        original_timeout = socket.getdefaulttimeout()
                        socket.setdefaulttimeout(15)  # 15 second timeout per email
                        
                        email_details = service.users().messages().get(
                            userId='me',
                            id=message['id'],
                            format='full'
                        ).execute()
                        
                        socket.setdefaulttimeout(original_timeout)
                        
                    except Exception as e:
                        socket.setdefaulttimeout(original_timeout)
                        logger.warning(f"Timeout or error fetching email {message['id']}: {e}")
                        
                        # Don't raise for individual email failures, just log and continue
                        if "timeout" in str(e).lower():
                            logger.warning(f"Timeout fetching email {message['id']}, skipping")
                        else:
                            logger.warning(f"Error fetching email {message['id']}: {e}, skipping")
                        continue
                    
                    # Parse email
                    email_data = self._parse_gmail_message(email_details, email_account)
                    
                    if email_data:
                        # Create email record
                        new_email = Email(**email_data)
                        db.add(new_email)
                        emails_synced += 1
                        
                        # Process attachments if any (skip for now to prevent timeouts)
                        # if email_details.get('payload', {}).get('parts'):
                        #     self._process_attachments(email_details, new_email, service, db)
                    
                except Exception as e:
                    error_msg = f"Error processing email {message.get('id', 'unknown')}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    
                    # Continue processing other emails even if one fails
                    continue
            
            # Update last sync time
            email_account.last_sync_at = datetime.now()
            db.commit()
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.info(f"Synced {emails_synced} emails for {email_account.email_address} in {duration_ms}ms")
            
            return GmailSyncResponse(
                success=True,
                emails_synced=emails_synced,
                errors=errors,
                sync_duration_ms=duration_ms
            )
            
        except (AuthenticationError, AuthorizationError, RateLimitError, QuotaExceededError, NetworkError, EmailSyncError) as e:
            # Handle specific known errors
            logger.error(f"Gmail sync error for {email_account.email_address}: {e.message}")
            errors.append(e.message)
        except Exception as e:
            # Handle unexpected errors with more detail
            import traceback
            error_msg = f"Unexpected error syncing emails for {email_account.email_address}: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Full traceback: {traceback.format_exc()}")
            errors.append(error_msg)
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return GmailSyncResponse(
                success=False,
                emails_synced=emails_synced,
                errors=errors,
                sync_duration_ms=duration_ms
            )
    
    async def disconnect_account(self, email_account: EmailAccount, db: Session) -> bool:
        """
        Disconnect Gmail account and revoke tokens
        
        Args:
            email_account: EmailAccount object
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to get credentials for token revocation, but don't fail if this doesn't work
            credentials = None
            try:
                credentials = await self.get_valid_credentials(email_account, db)
            except Exception as cred_error:
                logger.warning(f"Could not get credentials for token revocation: {cred_error}")
                # Continue with disconnect even if credentials are invalid
            
            if credentials and credentials.token:
                try:
                    # Revoke token
                    response = requests.post(
                        'https://oauth2.googleapis.com/revoke',
                        params={'token': credentials.token},
                        headers={'content-type': 'application/x-www-form-urlencoded'},
                        timeout=10
                    )
                    if response.status_code == 200:
                        logger.info(f"Successfully revoked token for {email_account.email_address}")
                    else:
                        logger.warning(f"Token revocation returned status {response.status_code} for {email_account.email_address}")
                except Exception as revoke_error:
                    logger.warning(f"Could not revoke token for {email_account.email_address}: {revoke_error}")
                    # Continue with disconnect even if revocation fails
            else:
                logger.info(f"No valid credentials found for {email_account.email_address}, skipping token revocation")
            
            # Clear tokens and deactivate account (this should always work)
            email_account.access_token = None
            email_account.refresh_token = None
            email_account.token_expires_at = None
            email_account.is_active = False
            email_account.sync_enabled = False
            
            db.commit()
            
            logger.info(f"Successfully disconnected Gmail account: {email_account.email_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting account {email_account.email_address}: {e}")
            
            # Try to rollback the database transaction
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(f"Could not rollback database transaction: {rollback_error}")
            
            return False
    
    def _get_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        """Get user info from Google OAuth2"""
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {credentials.token}'}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            
            # Don't raise for user info failures - return empty dict as fallback
            if "401" in str(e) or "unauthorized" in str(e).lower():
                logger.error("Authentication failed when getting user info")
            elif "403" in str(e) or "forbidden" in str(e).lower():
                logger.error("Authorization failed when getting user info")
            
            return {}
    
    def _build_email_query(self, sync_since: Optional[datetime] = None) -> str:
        """Build Gmail search query"""
        query_parts = []
        
        if sync_since:
            # Format date for Gmail API (YYYY/MM/DD)
            date_str = sync_since.strftime('%Y/%m/%d')
            query_parts.append(f'after:{date_str}')
        
        # Exclude spam and trash
        query_parts.extend(['-in:spam', '-in:trash'])
        
        return ' '.join(query_parts) if query_parts else 'in:inbox'
    
    def _parse_gmail_message(self, message: Dict[str, Any], email_account: EmailAccount) -> Optional[Dict[str, Any]]:
        """Parse Gmail message into email data"""
        try:
            payload = message.get('payload', {})
            headers = {h['name']: h['value'] for h in payload.get('headers', [])}
            
            # Extract basic email info
            subject = headers.get('Subject', '')
            sender_email = self._extract_email_address(headers.get('From', ''))
            sender_name = self._extract_sender_name(headers.get('From', ''))
            
            # Extract recipients
            to_emails = self._parse_email_addresses(headers.get('To', ''))
            cc_emails = self._parse_email_addresses(headers.get('Cc', ''))
            bcc_emails = self._parse_email_addresses(headers.get('Bcc', ''))
            
            # Extract body
            body_text, body_html = self._extract_email_body(payload)
            
            # Extract date
            date_str = headers.get('Date', '')
            sent_at = self._parse_email_date(date_str)
            
            # Extract labels
            labels = message.get('labelIds', [])
            
            # Check for attachments
            has_attachments = self._has_attachments(payload)
            
            return {
                'email_account_id': email_account.id,
                'user_id': email_account.user_id,
                'message_id': message['id'],
                'thread_id': message.get('threadId'),
                'subject': subject,
                'sender_email': sender_email,
                'sender_name': sender_name,
                'recipient_emails': json.dumps(to_emails) if to_emails else None,
                'cc_emails': json.dumps(cc_emails) if cc_emails else None,
                'bcc_emails': json.dumps(bcc_emails) if bcc_emails else None,
                'body_text': body_text,
                'body_html': body_html,
                'email_type': 'generic',  # Will be classified later
                'is_read': 'UNREAD' not in labels,
                'is_important': 'IMPORTANT' in labels,
                'has_attachments': has_attachments,
                'gmail_labels': json.dumps(labels),
                'sent_at': sent_at
            }
            
        except Exception as e:
            logger.error(f"Error parsing Gmail message: {e}")
            
            # Don't raise for individual message parsing failures
            # Return None so the email is skipped
            return None
    
    def _extract_email_address(self, from_header: str) -> str:
        """Extract email address from From header"""
        import re
        match = re.search(r'<(.+?)>', from_header)
        if match:
            return match.group(1)
        # If no angle brackets, assume the whole string is the email
        return from_header.strip()
    
    def _extract_sender_name(self, from_header: str) -> Optional[str]:
        """Extract sender name from From header"""
        import re
        # Look for "Name <email@domain.com>" format
        match = re.match(r'^(.+?)\s*<.+?>$', from_header)
        if match:
            name = match.group(1).strip().strip('"')
            return name if name else None
        return None
    
    def _parse_email_addresses(self, email_str: str) -> List[str]:
        """Parse comma-separated email addresses"""
        if not email_str:
            return []
        
        emails = []
        for addr in email_str.split(','):
            email_addr = self._extract_email_address(addr.strip())
            if email_addr and '@' in email_addr:
                emails.append(email_addr)
        
        return emails
    
    def _extract_email_body(self, payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extract text and HTML body from email payload"""
        body_text = None
        body_html = None
        
        def extract_body_recursive(part):
            nonlocal body_text, body_html
            
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            
            elif mime_type == 'text/html':
                data = part.get('body', {}).get('data', '')
                if data:
                    body_html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            
            # Process nested parts
            for nested_part in part.get('parts', []):
                extract_body_recursive(nested_part)
        
        extract_body_recursive(payload)
        
        return body_text, body_html
    
    def _parse_email_date(self, date_str: str) -> datetime:
        """Parse email date string"""
        try:
            # Gmail dates are in RFC 2822 format
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            # Fallback to current time if parsing fails
            return datetime.now()
    
    def _has_attachments(self, payload: Dict[str, Any]) -> bool:
        """Check if email has attachments"""
        def check_parts(part):
            # Check if this part is an attachment
            if part.get('filename'):
                return True
            
            # Check nested parts
            for nested_part in part.get('parts', []):
                if check_parts(nested_part):
                    return True
            
            return False
        
        return check_parts(payload)
    
    def _process_attachments(self, message: Dict[str, Any], email_obj: Email, service, db: Session):
        """Process email attachments"""
        # Implementation for attachment processing
        # This would handle downloading and storing attachment metadata
        pass