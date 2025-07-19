"""
Dynamic Error Message Service - Generate contextual technical error messages
"""

import logging
import random
from typing import Optional

logger = logging.getLogger("personal_ai_agent")

class ErrorMessageService:
    """Generate dynamic, contextual technical error messages"""
    
    def __init__(self):
        # Technical difficulty messages with variations
        self.technical_difficulty_messages = [
            "I'm experiencing technical difficulties right now. Please try your question again in a moment.",
            "There's a temporary issue with my processing system. Please retry your question shortly.",
            "I'm having trouble connecting to my language model. Please try again in a few moments.",
            "My AI processing is temporarily unavailable. Please wait a moment and try again.",
            "I encountered a technical problem while processing your request. Please try again."
        ]
        
        # Broken pipe specific messages
        self.connection_error_messages = [
            "I lost connection to my processing system. Please try your question again.",
            "There was a connection interruption. Please retry your question.",
            "I'm having connectivity issues. Please try again in a moment.",
            "My connection to the language model was interrupted. Please retry shortly."
        ]
        
        # Search error messages
        self.search_error_messages = [
            "I'm having trouble searching your documents right now. Please try again.",
            "There's an issue with document search. Please retry your question.",
            "I encountered a problem while looking through your documents. Please try again.",
            "Document search is temporarily unavailable. Please try again shortly."
        ]
        
        # Generation error messages
        self.generation_error_messages = [
            "I'm having trouble generating a response right now. Please try again.",
            "There's an issue with my response generation. Please retry your question.",
            "I encountered a problem while creating your answer. Please try again.",
            "Response generation is temporarily unavailable. Please try again shortly."
        ]
    
    def get_technical_difficulty_message(self, error_context: Optional[str] = None) -> str:
        """Get a technical difficulty message with optional context"""
        try:
            if error_context:
                if "broken pipe" in error_context.lower() or "errno 32" in error_context.lower():
                    return random.choice(self.connection_error_messages)
                elif "search" in error_context.lower():
                    return random.choice(self.search_error_messages)
                elif "generat" in error_context.lower():
                    return random.choice(self.generation_error_messages)
            
            # Default technical difficulty message
            return random.choice(self.technical_difficulty_messages)
            
        except Exception as e:
            logger.error(f"Error generating technical difficulty message: {e}")
            # Fallback to a safe default
            return "I'm experiencing technical difficulties right now. Please try your question again in a moment."
    
    def get_connection_error_message(self) -> str:
        """Get a connection-specific error message"""
        try:
            return random.choice(self.connection_error_messages)
        except Exception as e:
            logger.error(f"Error generating connection error message: {e}")
            return "I lost connection to my processing system. Please try your question again."
    
    def get_search_error_message(self) -> str:
        """Get a search-specific error message"""
        try:
            return random.choice(self.search_error_messages)
        except Exception as e:
            logger.error(f"Error generating search error message: {e}")
            return "I'm having trouble searching your documents right now. Please try again."
    
    def get_generation_error_message(self) -> str:
        """Get a generation-specific error message"""
        try:
            return random.choice(self.generation_error_messages)
        except Exception as e:
            logger.error(f"Error generating generation error message: {e}")
            return "I'm having trouble generating a response right now. Please try again."
    
    def get_http_error_detail(self, error_type: str, context: Optional[str] = None) -> str:
        """Get HTTP error detail messages"""
        error_details = {
            'document_not_found': "The requested document could not be found or you don't have access to it.",
            'search_error': "Unable to search documents at this time. Please try again.",
            'generation_error': "Unable to generate response. Please try again.",
            'processing_error': "Unable to process your request. Please try again.",
            'routing_error': "Unable to route your query. Please try again."
        }
        
        try:
            return error_details.get(error_type, "An error occurred while processing your request. Please try again.")
        except Exception as e:
            logger.error(f"Error generating HTTP error detail: {e}")
            return "An error occurred. Please try again."


# Global service instance
error_message_service = ErrorMessageService()