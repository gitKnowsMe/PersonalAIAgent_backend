"""
Email processing module for RAG workflow.

This module provides comprehensive email integration for local RAG queries,
including ingestion, classification, processing, and search capabilities.
"""

from .email_ingestion import EmailIngestionService
from .email_classifier import EmailClassifier
from .email_processor import EmailProcessor
from .email_store import EmailStore
from .email_query import EmailQueryService

__all__ = [
    "EmailIngestionService",
    "EmailClassifier", 
    "EmailProcessor",
    "EmailStore",
    "EmailQueryService"
]