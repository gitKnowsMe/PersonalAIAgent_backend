from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.core.constants import (
    USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH,
    PASSWORD_MIN_LENGTH, EMAIL_MAX_LENGTH,
    TITLE_MAX_LENGTH, DESCRIPTION_MAX_LENGTH
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(EMAIL_MAX_LENGTH), unique=True, index=True, nullable=False)
    username = Column(String(USERNAME_MAX_LENGTH), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)  # bcrypt hashes are ~60 chars, but allow more
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    documents = relationship("Document", back_populates="owner")
    queries = relationship("Query", back_populates="user")
    
    __table_args__ = (
        CheckConstraint(f'LENGTH(username) >= {USERNAME_MIN_LENGTH}', name='username_min_length'),
        CheckConstraint(f'LENGTH(username) <= {USERNAME_MAX_LENGTH}', name='username_max_length'),
        CheckConstraint(f'LENGTH(email) <= {EMAIL_MAX_LENGTH}', name='email_max_length'),
        CheckConstraint("email LIKE '%@%'", name='email_format'),
        CheckConstraint("LENGTH(hashed_password) >= 8", name='password_hash_min_length'),
    )

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(TITLE_MAX_LENGTH), index=True, nullable=False)
    description = Column(Text, nullable=True)  # Optional field, can be NULL
    file_path = Column(String(500), nullable=False)  # File paths can be long
    file_type = Column(String(10), nullable=False)  # e.g., 'pdf', 'txt', 'docx'
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    vector_namespace = Column(String(200), unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    owner = relationship("User", back_populates="documents")
    queries = relationship("Query", back_populates="document")
    
    __table_args__ = (
        CheckConstraint(f'LENGTH(title) >= 1', name='title_not_empty'),
        CheckConstraint(f'LENGTH(title) <= {TITLE_MAX_LENGTH}', name='title_max_length'),
        CheckConstraint('file_size > 0', name='file_size_positive'),
        CheckConstraint('LENGTH(file_type) >= 2', name='file_type_min_length'),
        CheckConstraint('LENGTH(vector_namespace) >= 5', name='namespace_min_length'),
    )

class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)  # Can be NULL if query failed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)  # Optional: query might be across all docs
    
    user = relationship("User", back_populates="queries")
    document = relationship("Document", back_populates="queries")
    
    __table_args__ = (
        CheckConstraint('LENGTH(question) >= 1', name='question_not_empty'),
        CheckConstraint('LENGTH(question) <= 5000', name='question_max_length'),  # Reasonable question length limit
    ) 