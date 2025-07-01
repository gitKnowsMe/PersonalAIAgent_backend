"""
AI Configuration service for managing AI behavior and responses
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum

from app.core.exceptions import ConfigurationError


class AIBehaviorMode(str, Enum):
    """AI behavior modes"""
    STRICT_CONTEXT_ONLY = "strict_context_only"
    BALANCED = "balanced"
    CREATIVE = "creative"


class ResponseValidationLevel(str, Enum):
    """Response validation levels"""
    STRICT = "strict"
    MODERATE = "moderate"
    MINIMAL = "minimal"


@dataclass
class AIConfig:
    """AI Configuration settings"""
    # Behavior Settings
    behavior_mode: AIBehaviorMode = AIBehaviorMode.BALANCED
    validation_level: ResponseValidationLevel = ResponseValidationLevel.MINIMAL
    enable_hallucination_detection: bool = False
    enable_response_caching: bool = False
    
    # Response Quality Settings
    min_response_length: int = 10
    max_response_length: int = 2048
    require_context_reference: bool = False
    allow_general_knowledge_fallback: bool = True
    
    # LLM Parameters
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 1024
    repeat_penalty: float = 1.1
    
    # Search Parameters
    search_top_k: int = 20
    search_similarity_threshold: float = 0.2
    search_max_chunks: int = 10
    search_chunk_overlap: float = 0.2
    
    # Hallucination Detection
    hallucination_threshold: float = 0.9
    hallucination_keywords: List[str] = field(default_factory=lambda: [
        "I don't know", "I don't have", "I cannot", "I can't", 
        "no information", "not provided", "not mentioned", "not specified", "not given"
    ])
    
    # Validation Keywords
    hallucination_indicators: List[str] = field(default_factory=lambda: [
        "i am an ai language model",
        "i am an artificial intelligence",
        "i am a computer program",
        "i am not able to",
        "i cannot access",
        "i do not have access"
    ])
    
    error_indicators: List[str] = field(default_factory=lambda: [
        "error generating",
        "sorry, i encountered an error",
        "please try again",
        "i apologize, but",
        "i'm having trouble",
        "unable to generate"
    ])
    
    context_required_phrases: List[str] = field(default_factory=lambda: [
        "i don't have that specific information",
        "not mentioned in the provided context",
        "that information is not available in your documents",
        "please upload relevant documents",
        "try a different question"
    ])


@dataclass
class QueryClassificationConfig:
    """Query classification keywords configuration"""
    general_ai_keywords: List[str] = field(default_factory=lambda: [
        "prompt engineering", "few-shot", "one-shot", "chain-of-thought",
        "temperature", "top-k", "top-p", "what is ai", "machine learning",
        "artificial intelligence", "large language model", "llm", "gpt",
        "transformer", "neural network", "deep learning", "model training",
        "natural language processing", "nlp", "computer vision", "algorithm"
    ])
    
    personal_data_keywords: List[str] = field(default_factory=lambda: [
        "my", "i ", "expense", "skill", "vacation", "travel", "resume",
        "experience", "job", "work", "spent", "cost", "trip", "qualification",
        "education", "degree", "certification", "achievement", "project"
    ])
    
    expense_keywords: List[str] = field(default_factory=lambda: [
        "money", "spend", "spent", "expense", "expenses", "cost", "budget",
        "dollar", "$", "purchase", "transaction", "bill", "total", "payment",
        "finance", "financial", "receipt", "invoice", "charge"
    ])
    
    skills_keywords: List[str] = field(default_factory=lambda: [
        "technical", "skill", "skills", "resume", "cv", "qualification",
        "experience", "expertise", "proficiency", "ability", "programming",
        "developer", "software", "engineer", "coding", "framework",
        "language", "technology", "automation", "testing", "competency"
    ])
    
    vacation_keywords: List[str] = field(default_factory=lambda: [
        "vacation", "travel", "trip", "holiday", "went", "go", "visit",
        "traveled", "journey", "tour", "flight", "hotel", "resort",
        "beach", "destination", "tourism", "sightseeing", "adventure"
    ])


@dataclass
class ResponseTemplatesConfig:
    """Response templates configuration"""
    no_context_found: Dict[str, str] = field(default_factory=lambda: {
        "general": "I don't have that specific information in your uploaded documents. Please upload relevant documents or try a different question.",
        "expense": "I couldn't find any expense information for that period. Please upload relevant financial documents and try again.",
        "skills": "I couldn't find any information about your technical skills. Please upload your resume or CV and try again.",
        "vacation": "I couldn't find any information about your travels. Please upload relevant travel documents or try a different question."
    })
    
    insufficient_context: Dict[str, str] = field(default_factory=lambda: {
        "general": "The available information is limited. Could you provide more specific details or upload additional documents?",
        "financial": "I found some financial information but need more details to provide an accurate answer.",
        "personal": "I found some personal information but need more context to answer completely."
    })
    
    hallucination_detected: Dict[str, str] = field(default_factory=lambda: {
        "personal_query": "I don't have that specific information in your uploaded documents. Please upload relevant documents or try a different question.",
        "general_query": "That information is not available in your uploaded documents.",
        "ai_knowledge": "I can only answer based on information in your uploaded documents. For general knowledge questions, please specify if you want me to search your documents for related information."
    })
    
    error_fallback: Dict[str, str] = field(default_factory=lambda: {
        "processing": "I apologize, but I encountered an issue while processing your request. Please try rephrasing your question.",
        "generation": "I'm having trouble generating a complete response. Please try rephrasing your question or asking about a specific aspect of the topic.",
        "search": "I couldn't search your documents properly. Please try again with a different question."
    })


@dataclass
class SystemPromptsConfig:
    """System prompts configuration"""
    base: str = """You are a helpful assistant that STRICTLY answers based ONLY on the provided context.

CRITICAL RULES:
1. NEVER make up information that is not explicitly stated in the context
2. Use EXACT numbers, dates, and amounts from the context
3. If information is missing or unclear, say "I don't have that specific information in the provided context"
4. When providing financial amounts, use the EXACT dollar figures from the context
5. For dates and timeframes, use only what is explicitly mentioned"""
    
    personal_data: str = """
IMPORTANT: This is a personal information question. Focus ONLY on the user's specific data from the context. DO NOT provide general knowledge or generic answers."""
    
    general_knowledge: str = """
IMPORTANT: This appears to be a general knowledge question. You should ONLY answer if the specific information is explicitly mentioned in the provided context. DO NOT use your general training knowledge. If the context doesn't contain the answer, clearly state that the information is not available in the user's documents."""
    
    expense_query: str = """
EXPENSE INFORMATION RULES - CRITICAL FOR ACCURACY:
- Find the EXACT month and year mentioned in the query (e.g., "March 2023")
- Look for that EXACT combination in the context
- Use the EXACT "Total Spent:" amount shown for that specific month/year
- DO NOT use amounts from other months or years
- If context shows "March 2023... Total Spent: $2650" then answer is $2650
- DO NOT round, estimate, or modify the amounts
- If the exact month/year combination is not found, say so clearly"""
    
    skills_query: str = """
TECHNICAL SKILLS RULES:
- List ONLY skills explicitly mentioned in the context
- Include specific programming languages, tools, frameworks as written
- Do NOT infer skills that aren't directly stated
- Focus ONLY on professional and technical information
- If context mentions "8 years experience" use that exact phrase
- Separate clearly between technical skills and work experience"""
    
    vacation_query: str = """
VACATION INFORMATION RULES:
- Look ONLY for exact vacation details in the context
- Use EXACT destination names, years, and costs as written
- If a specific year is mentioned in the question (like 2023), ONLY provide information about vacations from that EXACT year
- If you find "Thailand 2023" with "$5000", use those exact details
- DO NOT combine information from different trips or years"""


@dataclass
class DocumentTypeKeywordsConfig:
    """Document type classification keywords"""
    vacation: List[str] = field(default_factory=lambda: [
        'vacation', 'travel', 'trip', 'holiday', 'airline', 'flight', 'hotel', 
        'rental car', 'thailand', 'phuket', 'bangkok', 'resort', 'tour', 'beach', 
        'island', 'visit', 'journey', 'tourism', 'sightseeing', 'adventure'
    ])
    
    resume: List[str] = field(default_factory=lambda: [
        'resume', 'cv', 'work history', 'experience', 'education', 'skill', 
        'professional', 'job', 'technical', 'programming', 'framework', 'language', 
        'certification', 'qualification', 'expertise', 'proficiency', 'accomplishment',
        'career', 'developer', 'software', 'engineer', 'coding', 'technology', 
        'automation', 'testing', 'competency'
    ])
    
    expense: List[str] = field(default_factory=lambda: [
        'expense', 'budget', 'cost', 'spent', '$', 'dollar', 'payment', 'finance', 
        'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 
        'september', 'october', 'november', 'december', 'money', 'price', 'pay', 
        'paid', 'bill', 'invoice', 'receipt', 'purchase', 'transaction', 'charge'
    ])
    
    prompt_engineering: List[str] = field(default_factory=lambda: [
        'prompt', 'engineering', 'llm', 'ai', 'language model', 'gpt', 'instruction',
        'artificial intelligence', 'chatgpt', 'chat', 'completion', 'token',
        'parameter', 'temperature', 'top-p', 'top-k', 'context window', 'few-shot',
        'zero-shot', 'one-shot', 'chain of thought', 'cot', 'role prompting', 
        'system prompt', 'machine learning', 'transformer', 'neural network', 
        'deep learning', 'model training', 'natural language processing', 'nlp'
    ])


class AIConfigService:
    """Service for managing AI configuration"""
    
    def __init__(self):
        self._ai_config = AIConfig()
        self._query_classification = QueryClassificationConfig()
        self._response_templates = ResponseTemplatesConfig()
        self._system_prompts = SystemPromptsConfig()
        self._document_type_keywords = DocumentTypeKeywordsConfig()
    
    def get_ai_config(self) -> AIConfig:
        """Get the current AI configuration"""
        return self._ai_config
    
    def get_query_classification_keywords(self) -> QueryClassificationConfig:
        """Get query classification keywords"""
        return self._query_classification
    
    def get_response_template(self, category: str, subcategory: str = "general") -> str:
        """Get a response template"""
        templates = getattr(self._response_templates, category, None)
        if templates and isinstance(templates, dict):
            return templates.get(subcategory, self._response_templates.error_fallback["generation"])
        return self._response_templates.error_fallback["generation"]
    
    def get_system_prompt(self, query_type: str, additional_rules: List[str] = None) -> str:
        """Get system prompt for a specific query type"""
        base_prompt = self._system_prompts.base
        
        type_prompt = getattr(self._system_prompts, query_type, "")
        if type_prompt:
            base_prompt += type_prompt
        
        if additional_rules:
            base_prompt += "\n\nADDITIONAL RULES:\n" + "\n".join(f"- {rule}" for rule in additional_rules)
        
        return base_prompt
    
    def get_document_type_keywords(self) -> DocumentTypeKeywordsConfig:
        """Get document type keywords"""
        return self._document_type_keywords
    
    def update_ai_config(self, **kwargs) -> bool:
        """Update AI configuration settings"""
        try:
            for key, value in kwargs.items():
                if hasattr(self._ai_config, key):
                    setattr(self._ai_config, key, value)
                else:
                    raise ConfigurationError(f"Unknown configuration key: {key}")
            return True
        except Exception as e:
            raise ConfigurationError(f"Failed to update AI configuration: {e}")
    
    def reset_ai_config(self):
        """Reset AI configuration to defaults"""
        self._ai_config = AIConfig()


# Global instance for backward compatibility
_default_ai_config_service: AIConfigService = None


def get_ai_config_service() -> AIConfigService:
    """Get the default AI config service instance"""
    global _default_ai_config_service
    
    if _default_ai_config_service is None:
        _default_ai_config_service = AIConfigService()
    
    return _default_ai_config_service