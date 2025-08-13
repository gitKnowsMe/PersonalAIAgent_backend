"""
Portable Database Models

This module provides database models that are compatible with both PostgreSQL 
and SQLite for the single executable deployment.

The models are identical to the original models but with SQLite-compatible 
configurations and constraints.
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import os

from app.db.database_portable import Base
from app.core.constants import (
    USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH,
    PASSWORD_MIN_LENGTH, EMAIL_MAX_LENGTH,
    TITLE_MAX_LENGTH, DESCRIPTION_MAX_LENGTH
)

# Check if we're using SQLite for portable deployment
IS_SQLITE = os.getenv("PORTABLE_MODE", "false").lower() == "true" or "sqlite" in os.getenv("DATABASE_URL", "").lower()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(EMAIL_MAX_LENGTH), unique=True, index=True, nullable=False)
    username = Column(String(USERNAME_MAX_LENGTH), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    documents = relationship("Document", back_populates="owner")
    queries = relationship("Query", back_populates="user")
    email_accounts = relationship("EmailAccount", back_populates="user")
    emails = relationship("Email", back_populates="user")
    email_attachments = relationship("EmailAttachment", back_populates="user")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(TITLE_MAX_LENGTH), index=True, nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)
    document_type = Column(String(20), nullable=False, default="generic")
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    vector_namespace = Column(String(200), unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    owner = relationship("User", back_populates="documents")
    queries = relationship("Query", back_populates="document")
    
    __table_args__ = (
        # Basic indexes for all database types
        Index('idx_documents_owner_id', 'owner_id'),
        Index('idx_documents_document_type', 'document_type'),
        Index('idx_documents_created_at', 'created_at'),
    )

class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    user = relationship("User", back_populates="queries")
    document = relationship("Document", back_populates="queries")
    
    __table_args__ = (
        Index('idx_queries_user_id', 'user_id'),
        Index('idx_queries_document_id', 'document_id'),
        Index('idx_queries_created_at', 'created_at'),
    )

class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email_address = Column(String(EMAIL_MAX_LENGTH), nullable=False, index=True)
    provider = Column(String(50), nullable=False, default="gmail")
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sync_enabled = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    user = relationship("User", back_populates="email_accounts")
    emails = relationship("Email", back_populates="email_account")
    
    __table_args__ = (
        Index('idx_email_accounts_user_id', 'user_id'),
        Index('idx_email_accounts_is_active', 'is_active'),
        Index('idx_email_accounts_sync_enabled', 'sync_enabled'),
        Index('idx_email_accounts_last_sync_at', 'last_sync_at'),
    )

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    email_account_id = Column(Integer, ForeignKey("email_accounts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(String(255), nullable=False, unique=True, index=True)
    thread_id = Column(String(255), nullable=True, index=True)
    subject = Column(String(500), nullable=True)
    sender_email = Column(String(EMAIL_MAX_LENGTH), nullable=False, index=True)
    sender_name = Column(String(200), nullable=True)
    recipient_emails = Column(Text, nullable=True)
    cc_emails = Column(Text, nullable=True)
    bcc_emails = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    email_type = Column(String(20), nullable=False, default="generic")
    is_read = Column(Boolean, default=False, nullable=False)
    is_important = Column(Boolean, default=False, nullable=False)
    has_attachments = Column(Boolean, default=False, nullable=False)
    gmail_labels = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    vector_namespace = Column(String(200), nullable=True)
    
    email_account = relationship("EmailAccount", back_populates="emails")
    user = relationship("User", back_populates="emails")
    attachments = relationship("EmailAttachment", back_populates="email")
    
    __table_args__ = (
        # Essential indexes for performance
        Index('idx_emails_user_id', 'user_id'),
        Index('idx_emails_email_account_id', 'email_account_id'),
        Index('idx_emails_email_type', 'email_type'),
        Index('idx_emails_is_read', 'is_read'),
        Index('idx_emails_has_attachments', 'has_attachments'),
        Index('idx_emails_is_important', 'is_important'),
        # Composite indexes for common query patterns
        Index('idx_emails_user_account_composite', 'user_id', 'email_account_id'),
        Index('idx_emails_user_type_composite', 'user_id', 'email_type'),
        Index('idx_emails_user_sent_at_composite', 'user_id', 'sent_at'),
        Index('idx_emails_user_read_composite', 'user_id', 'is_read'),
    )

class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    attachment_id = Column(String(255), nullable=False)
    is_downloaded = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    email = relationship("Email", back_populates="attachments")
    user = relationship("User", back_populates="email_attachments")
    
    __table_args__ = (
        Index('idx_email_attachments_email_id', 'email_id'),
        Index('idx_email_attachments_user_id', 'user_id'),
        Index('idx_email_attachments_is_downloaded', 'is_downloaded'),
        Index('idx_email_attachments_mime_type', 'mime_type'),
    )

class OAuthSession(Base):
    __tablename__ = "oauth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    oauth_state = Column(String(255), nullable=False)
    redirect_uri = Column(String(500), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_oauth_sessions_user_id', 'user_id'),
        Index('idx_oauth_sessions_expires_at', 'expires_at'),
        Index('idx_oauth_sessions_provider', 'provider'),
    )