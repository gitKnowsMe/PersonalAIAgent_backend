"""
Dynamic Fallback Message Service - Generate contextual messages when no chunks are found
"""

import logging
import os
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.services.document_content_service import document_service

logger = logging.getLogger("personal_ai_agent")

class FallbackMessageService:
    """Generate dynamic, contextual fallback messages based on query type and user documents"""
    
    def __init__(self):
        self.message_templates = {
            'expense': {
                'with_years': "I couldn't find expense information for {years}. {suggestion}",
                'without_years': "I couldn't find expense information in your documents. {suggestion}",
                'missing_docs': "To answer expense questions, please upload financial records, budget documents, or monthly expense reports."
            },
            'skills': {
                'general': "I couldn't find technical skills information in your documents. {suggestion}",
                'missing_docs': "To answer skills questions, please upload your resume, CV, or professional profile."
            },
            'vacation': {
                'with_years': "I couldn't find vacation information for {years}. {suggestion}",
                'without_years': "I couldn't find vacation information in your documents. {suggestion}",
                'missing_docs': "To answer travel questions, please upload travel documents, itineraries, or trip reports."
            },
            'prompt_engineering': {
                'general': "I couldn't find information about prompt engineering in your documents. {suggestion}",
                'missing_docs': "To answer AI/prompt engineering questions, please upload relevant documents about AI, machine learning, or prompt engineering."
            },
            'combined': {
                'multiple': "I couldn't find information about {topics} in your documents. {suggestion}",
                'missing_docs': "Please upload relevant documents for the topics you're asking about."
            },
            'default': {
                'general': "I don't have enough information to answer that question. {suggestion}",
                'missing_docs': "Please upload relevant documents or try a more specific question."
            }
        }
        
        self.document_type_names = {
            'expense': 'financial records',
            'resume': 'resume/CV',
            'travel': 'travel documents',
            'prompt': 'AI/ML documents'
        }
    
    def generate_no_chunks_message(
        self, 
        query_types: Dict[str, bool], 
        years: List[str], 
        user_id: int, 
        db: Session
    ) -> str:
        """Generate contextual fallback message when no chunks are found"""
        try:
            # Get user's document types
            user_doc_types = self._get_user_document_types(user_id, db)
            
            # Determine primary query type
            active_types = [qtype for qtype, is_active in query_types.items() if is_active]
            
            # Generate appropriate message
            if len(active_types) > 1:
                return self._generate_combined_message(active_types, years, user_doc_types)
            elif 'is_expense_query' in active_types:
                return self._generate_expense_message(years, user_doc_types)
            elif 'is_skills_query' in active_types:
                return self._generate_skills_message(user_doc_types)
            elif 'is_vacation_query' in active_types:
                return self._generate_vacation_message(years, user_doc_types)
            elif 'is_prompt_engineering_query' in active_types:
                return self._generate_prompt_message(user_doc_types)
            else:
                return self._generate_default_message(user_doc_types)
                
        except Exception as e:
            logger.error(f"Error generating fallback message: {e}")
            return "I don't have enough information to answer that question. Please upload relevant documents or try a different question."
    
    def _get_user_document_types(self, user_id: int, db: Session) -> List[str]:
        """Get list of document types the user has uploaded"""
        try:
            documents = document_service.get_user_documents(user_id, db)
            doc_types = []
            
            for doc in documents:
                # Extract filename from file_path and use title as fallback
                filename = ""
                if doc.file_path:
                    filename = os.path.basename(doc.file_path)
                elif doc.title:
                    filename = doc.title
                
                filename_lower = filename.lower()
                
                # Check for document type indicators
                if any(keyword in filename_lower for keyword in ['expense', 'budget', 'financial']):
                    if 'expense' not in doc_types:
                        doc_types.append('expense')
                elif any(keyword in filename_lower for keyword in ['resume', 'cv']):
                    if 'resume' not in doc_types:
                        doc_types.append('resume')
                elif any(keyword in filename_lower for keyword in ['travel', 'vacation', 'trip']):
                    if 'travel' not in doc_types:
                        doc_types.append('travel')
                elif any(keyword in filename_lower for keyword in ['prompt', 'ai', 'ml']):
                    if 'prompt' not in doc_types:
                        doc_types.append('prompt')
            
            return doc_types
            
        except Exception as e:
            logger.error(f"Error getting user document types: {e}")
            return []
    
    def _generate_expense_message(self, years: List[str], user_doc_types: List[str]) -> str:
        """Generate expense-specific fallback message"""
        templates = self.message_templates['expense']
        suggestion = self._generate_suggestion('expense', user_doc_types)
        
        if years:
            return templates['with_years'].format(
                years=', '.join(years), 
                suggestion=suggestion
            )
        else:
            return templates['without_years'].format(suggestion=suggestion)
    
    def _generate_skills_message(self, user_doc_types: List[str]) -> str:
        """Generate skills-specific fallback message"""
        templates = self.message_templates['skills']
        suggestion = self._generate_suggestion('skills', user_doc_types)
        
        return templates['general'].format(suggestion=suggestion)
    
    def _generate_vacation_message(self, years: List[str], user_doc_types: List[str]) -> str:
        """Generate vacation-specific fallback message"""
        templates = self.message_templates['vacation']
        suggestion = self._generate_suggestion('vacation', user_doc_types)
        
        if years:
            return templates['with_years'].format(
                years=', '.join(years), 
                suggestion=suggestion
            )
        else:
            return templates['without_years'].format(suggestion=suggestion)
    
    def _generate_prompt_message(self, user_doc_types: List[str]) -> str:
        """Generate prompt engineering-specific fallback message"""
        templates = self.message_templates['prompt_engineering']
        suggestion = self._generate_suggestion('prompt_engineering', user_doc_types)
        
        return templates['general'].format(suggestion=suggestion)
    
    def _generate_combined_message(self, active_types: List[str], years: List[str], user_doc_types: List[str]) -> str:
        """Generate message for multiple query types"""
        templates = self.message_templates['combined']
        
        # Clean up type names for display
        display_types = []
        for qtype in active_types:
            if 'expense' in qtype:
                display_types.append('expenses')
            elif 'skills' in qtype:
                display_types.append('skills')
            elif 'vacation' in qtype:
                display_types.append('vacation')
            elif 'prompt' in qtype:
                display_types.append('prompt engineering')
        
        topics = ', '.join(display_types[:-1]) + f" or {display_types[-1]}" if len(display_types) > 1 else display_types[0]
        suggestion = self._generate_suggestion('combined', user_doc_types)
        
        return templates['multiple'].format(topics=topics, suggestion=suggestion)
    
    def _generate_default_message(self, user_doc_types: List[str]) -> str:
        """Generate default fallback message"""
        templates = self.message_templates['default']
        suggestion = self._generate_suggestion('default', user_doc_types)
        
        return templates['general'].format(suggestion=suggestion)
    
    def _generate_suggestion(self, query_category: str, user_doc_types: List[str]) -> str:
        """Generate contextual suggestion based on what documents user has/needs"""
        try:
            # What user has
            has_docs = []
            if user_doc_types:
                has_docs = [self.document_type_names.get(doc_type, doc_type) for doc_type in user_doc_types]
            
            # What user needs for this query type
            needed_doc = None
            if query_category in ['expense', 'combined']:
                needed_doc = 'financial records'
            elif query_category == 'skills':
                needed_doc = 'resume/CV'
            elif query_category in ['vacation', 'travel']:
                needed_doc = 'travel documents'
            elif query_category == 'prompt_engineering':
                needed_doc = 'AI/ML documents'
            
            # Generate personalized suggestion
            if has_docs and needed_doc:
                if needed_doc.lower() in [doc.lower() for doc in has_docs]:
                    return "Try rephrasing your question or check if the information is in your uploaded documents."
                else:
                    has_text = f"You have uploaded: {', '.join(has_docs)}. "
                    need_text = f"To answer this question, please upload {needed_doc}."
                    return has_text + need_text
            elif has_docs:
                return f"You have uploaded: {', '.join(has_docs)}. Please upload additional relevant documents or try a different question."
            else:
                # Use template default
                template_key = query_category if query_category in self.message_templates else 'default'
                return self.message_templates[template_key]['missing_docs']
                
        except Exception as e:
            logger.error(f"Error generating suggestion: {e}")
            return "Please upload relevant documents or try a different question."
    
    def generate_no_documents_message(self) -> str:
        """Generate message when user has no documents at all"""
        return "You haven't uploaded any documents yet. Please upload some documents before asking questions."


# Global service instance
fallback_message_service = FallbackMessageService()