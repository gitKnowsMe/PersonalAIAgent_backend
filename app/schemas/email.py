"""
Email schemas for API request/response validation
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator


class EmailAccountBase(BaseModel):
    email_address: EmailStr
    provider: str = "gmail"
    sync_enabled: bool = True


class EmailAccountCreate(EmailAccountBase):
    pass


class EmailAccountUpdate(BaseModel):
    sync_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class EmailAccountResponse(EmailAccountBase):
    id: int
    user_id: int
    is_active: bool
    last_sync_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmailAttachmentBase(BaseModel):
    filename: str
    file_size: int
    mime_type: str


class EmailAttachmentResponse(EmailAttachmentBase):
    id: int
    email_id: int
    attachment_id: str
    is_downloaded: bool
    file_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmailBase(BaseModel):
    subject: Optional[str] = None
    sender_email: EmailStr
    sender_name: Optional[str] = None
    body_text: Optional[str] = None
    email_type: str = "generic"
    is_read: bool = False
    is_important: bool = False
    has_attachments: bool = False
    sent_at: datetime


class EmailCreate(EmailBase):
    message_id: str
    thread_id: Optional[str] = None
    recipient_emails: Optional[List[str]] = None
    cc_emails: Optional[List[str]] = None
    bcc_emails: Optional[List[str]] = None
    body_html: Optional[str] = None
    gmail_labels: Optional[List[str]] = None


class EmailUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_important: Optional[bool] = None
    email_type: Optional[str] = None


class EmailResponse(EmailBase):
    id: int
    email_account_id: int
    user_id: int
    message_id: str
    thread_id: Optional[str]
    recipient_emails: Optional[List[str]]
    cc_emails: Optional[List[str]]
    bcc_emails: Optional[List[str]]
    body_html: Optional[str]
    gmail_labels: Optional[List[str]]
    vector_namespace: Optional[str]
    created_at: datetime
    attachments: List[EmailAttachmentResponse] = []
    
    class Config:
        from_attributes = True


class EmailSearchRequest(BaseModel):
    query: str
    email_type: Optional[str] = None
    sender_email: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_attachments: bool = False
    limit: int = Field(default=10, le=100)


class EmailSearchResponse(BaseModel):
    emails: List[EmailResponse]
    total_count: int
    query: str
    processing_time_ms: int


class GmailAuthRequest(BaseModel):
    auth_code: str
    redirect_uri: str


class GmailAuthResponse(BaseModel):
    success: bool
    email_address: str
    message: str


class GmailSyncRequest(BaseModel):
    account_id: int
    max_emails: int = Field(default=100, le=1000)
    sync_since: Optional[datetime] = None


class GmailSyncResponse(BaseModel):
    success: bool
    emails_synced: int
    errors: List[str] = []
    sync_duration_ms: int


class GmailStatusResponse(BaseModel):
    account_id: int
    email_address: str
    is_connected: bool
    sync_enabled: bool
    last_sync_at: Optional[datetime]
    total_emails: int
    unread_emails: int
    sync_errors: List[str] = []


class EmailLegacyQueryRequest(BaseModel):
    question: str
    email_account_id: Optional[int] = None
    email_type_filter: Optional[str] = None
    include_pdfs: bool = True  # Include PDF documents in search
    max_results: int = Field(default=5, le=20)


class EmailLegacyQueryResponse(BaseModel):
    answer: str
    query_type: str
    email_matches: int
    document_matches: int
    sources: List[Dict[str, Any]] = []
    from_cache: bool = False
    processing_time_ms: int


# Email classification schemas
class EmailClassificationRequest(BaseModel):
    subject: Optional[str]
    body_text: str
    sender_email: str
    recipient_emails: List[str] = []


class EmailClassificationResponse(BaseModel):
    email_type: str
    confidence: float
    reasoning: str
    suggested_chunking: Dict[str, Any]


# OAuth2 and security schemas
class OAuth2TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "Bearer"


# Additional schemas for email endpoints
class EmailUploadResponse(BaseModel):
    success: bool
    message: str
    filename: str


class EmailQueryRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10


class EmailQueryResponse(BaseModel):
    answer: str
    results: List[Dict[str, Any]]
    query_analysis: Dict[str, Any]
    result_count: int


class EmailSearchRequest(BaseModel):
    query: str
    categories: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sender: Optional[str] = None
    max_results: Optional[int] = 20


class EmailStatsResponse(BaseModel):
    total_emails: int
    total_accounts: int
    total_attachments: int
    recent_emails: int
    vector_stats: Dict[str, Any]