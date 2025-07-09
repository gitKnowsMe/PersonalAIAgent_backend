"""
AI Configuration service for managing AI behavior and responses
Follows best practices: environment-based configuration, no hardcoded values, validation
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from app.core.exceptions import ConfigurationError
from app.core.config import settings


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
    """AI Configuration settings loaded from environment variables and config files"""
    # Behavior Settings
    behavior_mode: AIBehaviorMode = field(default_factory=lambda: AIBehaviorMode(
        os.getenv("AI_BEHAVIOR_MODE", AIBehaviorMode.BALANCED.value)
    ))
    validation_level: ResponseValidationLevel = field(default_factory=lambda: ResponseValidationLevel(
        os.getenv("AI_VALIDATION_LEVEL", ResponseValidationLevel.MODERATE.value)
    ))
    
    # Response Quality Settings
    min_response_length: int = field(default_factory=lambda: int(
        os.getenv("AI_MIN_RESPONSE_LENGTH", "10")
    ))
    max_response_length: int = field(default_factory=lambda: int(
        os.getenv("AI_MAX_RESPONSE_LENGTH", "2048")
    ))
    require_context_reference: bool = field(default_factory=lambda: 
        os.getenv("AI_REQUIRE_CONTEXT_REFERENCE", "false").lower() == "true"
    )
    allow_general_knowledge_fallback: bool = field(default_factory=lambda: 
        os.getenv("AI_ALLOW_GENERAL_KNOWLEDGE_FALLBACK", "true").lower() == "true"
    )
    
    # LLM Parameters (from core settings with environment overrides)
    temperature: float = field(default_factory=lambda: float(
        os.getenv("AI_TEMPERATURE", str(settings.LLM_TEMPERATURE))
    ))
    top_p: float = field(default_factory=lambda: float(
        os.getenv("AI_TOP_P", str(settings.LLM_TOP_P))
    ))
    top_k: int = field(default_factory=lambda: int(
        os.getenv("AI_TOP_K", str(settings.LLM_TOP_K))
    ))
    max_tokens: int = field(default_factory=lambda: int(
        os.getenv("AI_MAX_TOKENS", str(settings.LLM_MAX_TOKENS))
    ))
    repeat_penalty: float = field(default_factory=lambda: float(
        os.getenv("AI_REPEAT_PENALTY", "1.05")
    ))
    
    # Search Parameters (from core settings with environment overrides)
    search_top_k: int = field(default_factory=lambda: int(
        os.getenv("AI_SEARCH_TOP_K", str(settings.VECTOR_SEARCH_TOP_K))
    ))
    search_similarity_threshold: float = field(default_factory=lambda: float(
        os.getenv("AI_SEARCH_SIMILARITY_THRESHOLD", str(settings.VECTOR_SIMILARITY_THRESHOLD))
    ))
    search_max_chunks: int = field(default_factory=lambda: int(
        os.getenv("AI_SEARCH_MAX_CHUNKS", "7")
    ))
    search_chunk_overlap: float = field(default_factory=lambda: float(
        os.getenv("AI_SEARCH_CHUNK_OVERLAP", "0.1")
    ))


@dataclass
class SystemPromptsConfig:
    """System prompts configuration loaded from files or environment"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(settings.BASE_DIR) / "config"
        self._load_prompts()
    
    def _load_prompts(self):
        """Load system prompts from configuration files or environment variables"""
        self.base = self._load_prompt("base", self._get_default_base_prompt())
        self.personal_data = self._load_prompt("personal_data", self._get_default_personal_data_prompt())
        self.general_knowledge = self._load_prompt("general_knowledge", self._get_default_general_knowledge_prompt())
    
    def _load_prompt(self, prompt_name: str, default_value: str) -> str:
        """Load a prompt from file or environment variable"""
        # Try environment variable first
        env_var = f"AI_PROMPT_{prompt_name.upper()}"
        if env_value := os.getenv(env_var):
            return env_value
        
        # Try configuration file
        config_file = self.config_dir / f"{prompt_name}_prompt.txt"
        if config_file.exists():
            return config_file.read_text().strip()
        
        # Use default
        return default_value
    
    def _get_default_base_prompt(self) -> str:
        """Get default base system prompt"""
        return """You are a helpful assistant that answers based on the provided context.

CRITICAL RULES:
1. Use information from the provided context when available
2. If information is missing, clearly state that it's not available in the provided context
3. Be concise and direct - focus on the exact question asked
4. Use exact numbers, dates, and amounts when provided in context
5. For location-specific queries (e.g., "Rome", "Istanbul"), ONLY use information that explicitly mentions that exact location
6. Do NOT mix information from different locations - each location should be treated separately"""
    
    def _get_default_personal_data_prompt(self) -> str:
        """Get default personal data prompt"""
        return """

IMPORTANT: This is a personal information question. Focus on the user's specific data from the context."""
    
    def _get_default_general_knowledge_prompt(self) -> str:
        """Get default general knowledge prompt"""
        return """

IMPORTANT: Answer based on the provided context. If the context doesn't contain the answer, clearly state that the information is not available in the user's documents."""


@dataclass
class ResponseTemplatesConfig:
    """Response templates configuration loaded from files or environment"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(settings.BASE_DIR) / "config"
        self._load_templates()
    
    def _load_templates(self):
        """Load response templates from configuration files"""
        self.no_context_found = self._load_template_dict("no_context_found", {
            "general": "I don't have that specific information in your uploaded documents. Please upload relevant documents or try a different question.",
            "financial": "I couldn't find any financial information for that request. Please upload relevant documents.",
            "personal": "I couldn't find any personal information for that request. Please upload relevant documents."
        })
        
        self.error_fallback = self._load_template_dict("error_fallback", {
            "processing": "I apologize, but I encountered an issue while processing your request. Please try rephrasing your question.",
            "generation": "I'm having trouble generating a complete response. Please try rephrasing your question.",
            "search": "I couldn't search your documents properly. Please try again with a different question."
        })
    
    def _load_template_dict(self, template_name: str, default_dict: Dict[str, str]) -> Dict[str, str]:
        """Load a template dictionary from file or use default"""
        config_file = self.config_dir / f"{template_name}_templates.json"
        if config_file.exists():
            try:
                return json.loads(config_file.read_text())
            except json.JSONDecodeError:
                pass
        return default_dict


class AIConfigService:
    """Service for managing AI configuration with environment-based settings"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(settings.BASE_DIR) / "config"
        self._ai_config = AIConfig()
        self._system_prompts = SystemPromptsConfig(config_dir)
        self._response_templates = ResponseTemplatesConfig(config_dir)
    
    def get_ai_config(self) -> AIConfig:
        """Get the current AI configuration"""
        return self._ai_config
    
    def get_system_prompt(self, query_type: str = "base", additional_rules: Optional[List[str]] = None) -> str:
        """Get system prompt for a specific query type"""
        base_prompt = self._system_prompts.base
        
        # Add type-specific prompt
        if query_type == "personal_data":
            base_prompt += self._system_prompts.personal_data
        elif query_type == "general_knowledge":
            base_prompt += self._system_prompts.general_knowledge
        
        # Add additional rules if provided
        if additional_rules:
            base_prompt += "\n\nADDITIONAL RULES:\n" + "\n".join(f"- {rule}" for rule in additional_rules)
        
        return base_prompt
    
    def get_response_template(self, category: str, subcategory: str = "general") -> str:
        """Get a response template"""
        templates = getattr(self._response_templates, category, None)
        if templates and isinstance(templates, dict):
            return templates.get(subcategory, self._response_templates.error_fallback["generation"])
        return self._response_templates.error_fallback["generation"]
    
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
    
    def validate_config(self) -> bool:
        """Validate the current configuration"""
        try:
            # Validate temperature range
            if not 0.0 <= self._ai_config.temperature <= 2.0:
                raise ConfigurationError("Temperature must be between 0.0 and 2.0")
            
            # Validate top_p range
            if not 0.0 <= self._ai_config.top_p <= 1.0:
                raise ConfigurationError("Top_p must be between 0.0 and 1.0")
            
            # Validate top_k
            if self._ai_config.top_k < 1:
                raise ConfigurationError("Top_k must be at least 1")
            
            # Validate max_tokens
            if self._ai_config.max_tokens < 1:
                raise ConfigurationError("Max_tokens must be at least 1")
            
            # Validate search parameters
            if self._ai_config.search_top_k < 1:
                raise ConfigurationError("Search_top_k must be at least 1")
            
            if not 0.0 <= self._ai_config.search_similarity_threshold <= 1.0:
                raise ConfigurationError("Search_similarity_threshold must be between 0.0 and 1.0")
            
            return True
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")


# Global instance for backward compatibility
_default_ai_config_service: Optional[AIConfigService] = None


def get_ai_config_service() -> AIConfigService:
    """Get the default AI config service instance"""
    global _default_ai_config_service
    
    if _default_ai_config_service is None:
        _default_ai_config_service = AIConfigService()
        _default_ai_config_service.validate_config()
    
    return _default_ai_config_service