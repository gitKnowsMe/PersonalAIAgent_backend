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


# Response Templates (backward compatibility)
def _get_response_templates_dict():
    service = get_ai_config_service()
    config = service._response_templates
    return {
        "no_context_found": config.no_context_found,
        "insufficient_context": config.insufficient_context,
        "hallucination_detected": config.hallucination_detected,
        "error_fallback": config.error_fallback,
    }


RESPONSE_TEMPLATES = _get_response_templates_dict()


# System Prompts (backward compatibility)
def _get_system_prompts_dict():
    service = get_ai_config_service()
    config = service._system_prompts
    return {
        "base": config.base,
        "personal_data": config.personal_data,
        "general_knowledge": config.general_knowledge,
        "expense_query": config.expense_query,
        "skills_query": config.skills_query,
        "vacation_query": config.vacation_query,
    }


SYSTEM_PROMPTS = _get_system_prompts_dict()


# Document Type Keywords (backward compatibility)
def _get_document_type_keywords_dict():
    service = get_ai_config_service()
    config = service.get_document_type_keywords()
    return {
        'vacation': config.vacation,
        'resume': config.resume,
        'expense': config.expense,
        'prompt_engineering': config.prompt_engineering,
    }


DOCUMENT_TYPE_KEYWORDS = _get_document_type_keywords_dict()


# Backward compatibility functions
def get_ai_config() -> Dict[str, Any]:
    """Get the current AI configuration"""
    return _get_ai_config_dict()


def get_query_classification_keywords() -> Dict[str, List[str]]:
    """Get query classification keywords"""
    return _get_query_classification_dict()


def get_response_template(category: str, subcategory: str = "general") -> str:
    """Get a response template"""
    service = get_ai_config_service()
    return service.get_response_template(category, subcategory)


def get_system_prompt(query_type: str, additional_rules: List[str] = None) -> str:
    """Get system prompt for a specific query type"""
    service = get_ai_config_service()
    return service.get_system_prompt(query_type, additional_rules)


def update_ai_config(key: str, value: Any) -> bool:
    """Update a specific AI configuration setting"""
    service = get_ai_config_service()
    return service.update_ai_config(**{key: value})


def reset_ai_config():
    """Reset AI configuration to defaults"""
    service = get_ai_config_service()
    service.reset_ai_config()


def get_default_config() -> Dict[str, Any]:
    """Get default AI configuration"""
    return _get_ai_config_dict()