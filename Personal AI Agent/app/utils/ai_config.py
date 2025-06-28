"""
AI Configuration Module

This module centralizes all AI behavior configuration to ensure consistent,
maintainable, and non-hard-coded responses across the Personal AI Agent system.
"""

from typing import Dict, List, Any
from enum import Enum

class AIBehaviorMode(Enum):
    """AI behavior modes"""
    STRICT_CONTEXT_ONLY = "strict_context_only"  # Only use provided context
    ENHANCED_CONTEXT = "enhanced_context"        # Context + limited general knowledge
    GENERAL_KNOWLEDGE = "general_knowledge"      # Allow general knowledge when appropriate

class ResponseValidationLevel(Enum):
    """Response validation levels"""
    STRICT = "strict"      # Strict validation, reject suspicious responses
    MODERATE = "moderate"  # Moderate validation, warn but allow
    PERMISSIVE = "permissive"  # Minimal validation

# Current AI Configuration
AI_CONFIG = {
    # Behavior Settings
    "behavior_mode": AIBehaviorMode.STRICT_CONTEXT_ONLY,
    "validation_level": ResponseValidationLevel.STRICT,
    "enable_hallucination_detection": True,
    "enable_response_caching": False,  # Disabled to ensure fresh responses
    
    # Response Quality Settings
    "min_response_length": 10,
    "max_response_length": 2048,
    "require_context_reference": True,
    "allow_general_knowledge_fallback": False,
    
    # LLM Parameters
    "temperature": 0.05,  # Very low for deterministic responses
    "top_p": 0.9,
    "top_k": 40,
    "max_tokens": 512,
    "repeat_penalty": 1.1,
    
    # Search Parameters
    "max_chunks_per_query": 5,
    "max_chunks_per_document_type": 3,
    "similarity_threshold": 0.6,
    "search_top_k": 20,
    
    # Validation Keywords
    "hallucination_indicators": [
        "prompt engineering is the process",
        "few-shot prompting",
        "chain-of-thought",
        "temperature adjustment",
        "role-based prompting",
        "context enrichment",
        "large language model",
        "artificial intelligence",
        "machine learning",
        "neural network",
        "transformer",
        "deep learning"
    ],
    
    "error_indicators": [
        "error generating",
        "sorry, i encountered an error",
        "please try again",
        "i apologize, but",
        "i'm having trouble",
        "unable to generate"
    ],
    
    "context_required_phrases": [
        "i don't have that specific information",
        "not mentioned in the provided context",
        "that information is not available in your documents",
        "please upload relevant documents",
        "try a different question"
    ]
}

# Query Classification Keywords
QUERY_CLASSIFICATION = {
    "general_ai_keywords": [
        "prompt engineering", "few-shot", "one-shot", "chain-of-thought",
        "temperature", "top-k", "top-p", "what is ai", "machine learning",
        "artificial intelligence", "large language model", "llm", "gpt",
        "transformer", "neural network", "deep learning", "model training",
        "natural language processing", "nlp", "computer vision", "algorithm"
    ],
    
    "personal_data_keywords": [
        "my", "i ", "expense", "skill", "vacation", "travel", "resume",
        "experience", "job", "work", "spent", "cost", "trip", "qualification",
        "education", "degree", "certification", "achievement", "project"
    ],
    
    "expense_keywords": [
        "money", "spend", "spent", "expense", "expenses", "cost", "budget",
        "dollar", "$", "purchase", "transaction", "bill", "total", "payment",
        "finance", "financial", "receipt", "invoice", "charge"
    ],
    
    "skills_keywords": [
        "technical", "skill", "skills", "resume", "cv", "qualification",
        "experience", "expertise", "proficiency", "ability", "programming",
        "developer", "software", "engineer", "coding", "framework",
        "language", "technology", "automation", "testing", "competency"
    ],
    
    "vacation_keywords": [
        "vacation", "travel", "trip", "holiday", "went", "go", "visit",
        "traveled", "journey", "tour", "flight", "hotel", "resort",
        "beach", "destination", "tourism", "sightseeing", "adventure"
    ]
}

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
        "behavior_mode": AIBehaviorMode.STRICT_CONTEXT_ONLY,
        "validation_level": ResponseValidationLevel.STRICT,
        "enable_hallucination_detection": True,
        "enable_response_caching": False,
        "min_response_length": 10,
        "max_response_length": 2048,
        "require_context_reference": True,
        "allow_general_knowledge_fallback": False,
        "temperature": 0.05,
        "top_p": 0.9,
        "top_k": 40,
        "max_tokens": 512,
        "repeat_penalty": 1.1,
        "max_chunks_per_query": 5,
        "max_chunks_per_document_type": 3,
        "similarity_threshold": 0.6,
        "search_top_k": 20,
        "hallucination_indicators": [
            "prompt engineering is the process",
            "few-shot prompting",
            "chain-of-thought",
            "temperature adjustment",
            "role-based prompting",
            "context enrichment"
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