"""
AI Configuration Module - backward compatibility layer
This module now delegates to the new AIConfigService for better architecture
"""

from typing import Dict, List, Any

from app.services.ai_config_service import (
    get_ai_config_service,
    AIBehaviorMode,
    ResponseValidationLevel
)


def _get_ai_config_dict() -> Dict[str, Any]:
    """Convert AIConfig dataclass to dictionary for backward compatibility"""
    service = get_ai_config_service()
    config = service.get_ai_config()
    
    return {
        "behavior_mode": config.behavior_mode,
        "validation_level": config.validation_level,
        "enable_hallucination_detection": config.enable_hallucination_detection,
        "enable_response_caching": config.enable_response_caching,
        "min_response_length": config.min_response_length,
        "max_response_length": config.max_response_length,
        "require_context_reference": config.require_context_reference,
        "allow_general_knowledge_fallback": config.allow_general_knowledge_fallback,
        "temperature": config.temperature,
        "top_p": config.top_p,
        "top_k": config.top_k,
        "max_tokens": config.max_tokens,
        "repeat_penalty": config.repeat_penalty,
        "search_top_k": config.search_top_k,
        "search_similarity_threshold": config.search_similarity_threshold,
        "search_max_chunks": config.search_max_chunks,
        "search_chunk_overlap": config.search_chunk_overlap,
        "hallucination_threshold": config.hallucination_threshold,
        "hallucination_keywords": config.hallucination_keywords,
        "hallucination_indicators": config.hallucination_indicators,
        "error_indicators": config.error_indicators,
        "context_required_phrases": config.context_required_phrases,
    }


# Backward compatibility - dynamic property that always reflects current config
class _AIConfigProxy:
    def __getitem__(self, key):
        return _get_ai_config_dict()[key]
    
    def __setitem__(self, key, value):
        service = get_ai_config_service()
        service.update_ai_config(**{key: value})
    
    def get(self, key, default=None):
        return _get_ai_config_dict().get(key, default)
    
    def copy(self):
        return _get_ai_config_dict()


AI_CONFIG = _AIConfigProxy()

# Query Classification Keywords (backward compatibility)
def _get_query_classification_dict():
    service = get_ai_config_service()
    config = service.get_query_classification_keywords()
    return {
        "general_ai_keywords": config.general_ai_keywords,
        "personal_data_keywords": config.personal_data_keywords,
        "expense_keywords": config.expense_keywords,
        "skills_keywords": config.skills_keywords,
        "vacation_keywords": config.vacation_keywords,
    }

QUERY_CLASSIFICATION = _get_query_classification_dict()

# Response Templates (non-hard-coded, context-aware)
RESPONSE_TEMPLATES = {
    "no_context_found": {
        "general": "I don't have that specific information in your uploaded documents. Please upload relevant documents or try a different question.",
        "expense": "I couldn't find any expense information for that period. Please upload relevant financial documents and try again.",
        "skills": "I couldn't find any information about your technical skills. Please upload your resume or CV and try again.",
        "vacation": "I couldn't find any information about your travels. Please upload relevant travel documents or try a different question."
    },
    
    "insufficient_context": {
        "general": "The available information is limited. Could you provide more specific details or upload additional documents?",
        "financial": "I found some financial information but need more details to provide an accurate answer.",
        "personal": "I found some personal information but need more context to answer completely."
    },
    
    "hallucination_detected": {
        "personal_query": "I don't have that specific information in your uploaded documents. Please upload relevant documents or try a different question.",
        "general_query": "That information is not available in your uploaded documents.",
        "ai_knowledge": "I can only answer based on information in your uploaded documents. For general knowledge questions, please specify if you want me to search your documents for related information."
    },
    
    "error_fallback": {
        "processing": "I apologize, but I encountered an issue while processing your request. Please try rephrasing your question.",
        "generation": "I'm having trouble generating a complete response. Please try rephrasing your question or asking about a specific aspect of the topic.",
        "search": "I couldn't search your documents properly. Please try again with a different question."
    }
}

# System Prompts for Different Query Types
SYSTEM_PROMPTS = {
    "base": """You are a helpful assistant that STRICTLY answers based ONLY on the provided context.

CRITICAL RULES:
1. NEVER make up information that is not explicitly stated in the context
2. Use EXACT numbers, dates, and amounts from the context
3. If information is missing or unclear, say "I don't have that specific information in the provided context"
4. When providing financial amounts, use the EXACT dollar figures from the context
5. For dates and timeframes, use only what is explicitly mentioned""",
    
    "personal_data": """
IMPORTANT: This is a personal information question. Focus ONLY on the user's specific data from the context. DO NOT provide general knowledge or generic answers.""",
    
    "general_knowledge": """
IMPORTANT: This appears to be a general knowledge question. You should ONLY answer if the specific information is explicitly mentioned in the provided context. DO NOT use your general training knowledge. If the context doesn't contain the answer, clearly state that the information is not available in the user's documents.""",
    
    "expense_query": """
EXPENSE INFORMATION RULES - CRITICAL FOR ACCURACY:
- Find the EXACT month and year mentioned in the query (e.g., "March 2023")
- Look for that EXACT combination in the context
- Use the EXACT "Total Spent:" amount shown for that specific month/year
- DO NOT use amounts from other months or years
- If context shows "March 2023... Total Spent: $2650" then answer is $2650
- DO NOT round, estimate, or modify the amounts
- If the exact month/year combination is not found, say so clearly""",
    
    "skills_query": """
TECHNICAL SKILLS RULES:
- List ONLY skills explicitly mentioned in the context
- Include specific programming languages, tools, frameworks as written
- Do NOT infer skills that aren't directly stated
- Focus ONLY on professional and technical information
- If context mentions "8 years experience" use that exact phrase
- Separate clearly between technical skills and work experience""",
    
    "vacation_query": """
VACATION INFORMATION RULES:
- Look ONLY for exact vacation details in the context
- Use EXACT destination names, years, and costs as written
- If a specific year is mentioned in the question (like 2023), ONLY provide information about vacations from that EXACT year
- If you find "Thailand 2023" with "$5000", use those exact details
- DO NOT combine information from different trips or years"""
}

# Document Type Classification Keywords
DOCUMENT_TYPE_KEYWORDS = {
    'vacation': [
        'vacation', 'travel', 'trip', 'holiday', 'airline', 'flight', 'hotel', 
        'rental car', 'thailand', 'phuket', 'bangkok', 'resort', 'tour', 'beach', 
        'island', 'visit', 'journey', 'tourism', 'sightseeing', 'adventure'
    ],
    'resume': [
        'resume', 'cv', 'work history', 'experience', 'education', 'skill', 
        'professional', 'job', 'technical', 'programming', 'framework', 'language', 
        'certification', 'qualification', 'expertise', 'proficiency', 'accomplishment',
        'career', 'developer', 'software', 'engineer', 'coding', 'technology', 
        'automation', 'testing', 'competency'
    ],
    'expense': [
        'expense', 'budget', 'cost', 'spent', '$', 'dollar', 'payment', 'finance', 
        'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 
        'september', 'october', 'november', 'december', 'money', 'price', 'pay', 
        'paid', 'bill', 'invoice', 'receipt', 'purchase', 'transaction', 'charge'
    ],
    'prompt_engineering': [
        'prompt', 'engineering', 'llm', 'ai', 'language model', 'gpt', 'instruction',
        'artificial intelligence', 'chatgpt', 'chat', 'completion', 'token',
        'parameter', 'temperature', 'top-p', 'top-k', 'context window', 'few-shot',
        'zero-shot', 'one-shot', 'chain of thought', 'cot', 'role prompting', 
        'system prompt', 'machine learning', 'transformer', 'neural network', 
        'deep learning', 'model training', 'natural language processing', 'nlp'
    ]
}

def get_ai_config() -> Dict[str, Any]:
    """Get the current AI configuration"""
    return AI_CONFIG.copy()

def get_query_classification_keywords() -> Dict[str, List[str]]:
    """Get query classification keywords"""
    return QUERY_CLASSIFICATION.copy()

def get_response_template(category: str, subcategory: str = "general") -> str:
    """Get a response template"""
    return RESPONSE_TEMPLATES.get(category, {}).get(subcategory, 
        RESPONSE_TEMPLATES["error_fallback"]["generation"])

def get_system_prompt(query_type: str, additional_rules: List[str] = None) -> str:
    """Get system prompt for a specific query type"""
    base_prompt = SYSTEM_PROMPTS["base"]
    
    if query_type in SYSTEM_PROMPTS:
        base_prompt += SYSTEM_PROMPTS[query_type]
    
    if additional_rules:
        base_prompt += "\n\nADDITIONAL RULES:\n" + "\n".join(f"- {rule}" for rule in additional_rules)
    
    return base_prompt

def update_ai_config(key: str, value: Any) -> bool:
    """Update a specific AI configuration setting"""
    if key in AI_CONFIG:
        AI_CONFIG[key] = value
        return True
    return False

def reset_ai_config():
    """Reset AI configuration to defaults"""
    global AI_CONFIG
    AI_CONFIG = get_default_config()

def get_default_config() -> Dict[str, Any]:
    """Get default AI configuration"""
    return {
        "behavior_mode": AIBehaviorMode.BALANCED,
        "validation_level": ResponseValidationLevel.MINIMAL,
        "enable_hallucination_detection": False,
        "enable_response_caching": False,
        "min_response_length": 10,
        "max_response_length": 2048,
        "require_context_reference": False,
        "allow_general_knowledge_fallback": True,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "max_tokens": 1024,
        "repeat_penalty": 1.1,
        "search_top_k": 20,
        "search_similarity_threshold": 0.2,
        "search_max_chunks": 10,
        "search_chunk_overlap": 0.2,
        "hallucination_threshold": 0.9,
        "hallucination_keywords": ["I don't know", "I don't have", "I cannot", "I can't", "no information", "not provided", "not mentioned", "not specified", "not given"],
        "hallucination_indicators": [
            "i am an ai language model",
            "i am an artificial intelligence",
            "i am a computer program",
            "i am not able to",
            "i cannot access",
            "i do not have access"
        ],
        "error_indicators": [
            "error generating",
            "sorry, i encountered an error",
            "please try again",
            "i apologize, but"
        ],
        "context_required_phrases": [
            "i don't have that specific information",
            "not mentioned in the provided context",
            "that information is not available in your documents"
        ]
    } 