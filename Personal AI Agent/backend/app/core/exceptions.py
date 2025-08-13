"""
Custom exceptions for the Personal AI Agent application
"""

class PersonalAIException(Exception):
    """Base exception for Personal AI Agent"""
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ConfigurationError(PersonalAIException):
    """Raised when there's a configuration issue"""
    pass


class DocumentProcessingError(PersonalAIException):
    """Raised when document processing fails"""
    pass


class EmbeddingGenerationError(PersonalAIException):
    """Raised when embedding generation fails"""
    pass


class VectorStoreError(PersonalAIException):
    """Raised when vector store operations fail"""
    pass


class ModelLoadError(PersonalAIException):
    """Raised when model loading fails"""
    pass


class ValidationError(PersonalAIException):
    """Raised when data validation fails"""
    pass


class AuthenticationError(PersonalAIException):
    """Raised when authentication fails"""
    pass


class FileUploadError(PersonalAIException):
    """Raised when file upload fails"""
    pass