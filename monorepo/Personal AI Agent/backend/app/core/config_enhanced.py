"""
Enhanced configuration management system.

Provides environment-specific configuration loading, validation,
and management utilities to replace hardcoded values and improve
configuration flexibility.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Type
from contextlib import contextmanager

from pydantic import ValidationError
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

from app.core.config_schema import (
    EnvironmentType,
    ServerSettings,
    SecuritySettings,
    DatabaseSettings,
    FileUploadSettings,
    LLMSettings,
    EmbeddingSettings,
    VectorStoreSettings,
    GmailSettings,
    EmailProcessingSettings,
    LoggingSettings,
    CORSSettings,
    MonitoringSettings
)

logger = logging.getLogger("personal_ai_agent")


class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass


class ConfigurationManager:
    """Manages application configuration with environment-specific loading."""
    
    def __init__(self, environment: Optional[EnvironmentType] = None):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self._config_cache = {}
        self.environment = environment or self._detect_environment()
        self._load_environment_files()
    
    def _detect_environment(self) -> EnvironmentType:
        """Auto-detect environment based on various indicators."""
        # Check explicit environment variable
        env_var = os.getenv("ENVIRONMENT", "").lower()
        if env_var in [e.value for e in EnvironmentType]:
            return EnvironmentType(env_var)
        
        # Check for testing
        if "pytest" in sys.modules or "unittest" in sys.modules:
            return EnvironmentType.TESTING
        
        # Check for development indicators
        if (
            os.getenv("DEBUG", "").lower() == "true" or
            os.getenv("DEV", "").lower() == "true" or
            os.path.exists(self.base_dir / ".git")
        ):
            return EnvironmentType.DEVELOPMENT
        
        # Check for production indicators
        if (
            os.getenv("PRODUCTION", "").lower() == "true" or
            os.getenv("PROD", "").lower() == "true" or
            not os.getenv("DEBUG")
        ):
            return EnvironmentType.PRODUCTION
        
        # Default to development
        return EnvironmentType.DEVELOPMENT
    
    def _load_environment_files(self):
        """Load environment files in priority order."""
        env_files = [
            self.base_dir / f".env.{self.environment.value}",  # Environment-specific
            self.base_dir / ".env.local",                      # Local overrides
            self.base_dir / ".env",                            # Default
        ]
        
        loaded_files = []
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file, override=False)  # Don't override previously loaded values
                loaded_files.append(str(env_file))
        
        if loaded_files:
            logger.info(f"Loaded environment files: {', '.join(loaded_files)}")
        else:
            logger.warning("No environment files found")
        
        # Set environment in env vars for other components
        os.environ.setdefault("ENVIRONMENT", self.environment.value)
    
    def get_settings(self, settings_class: Type[BaseSettings]) -> BaseSettings:
        """Get and cache settings for a specific settings class."""
        class_name = settings_class.__name__
        
        if class_name not in self._config_cache:
            try:
                self._config_cache[class_name] = settings_class()
                logger.debug(f"Loaded {class_name} configuration")
            except ValidationError as e:
                error_msg = f"Configuration validation failed for {class_name}: {e}"
                logger.error(error_msg)
                raise ConfigurationError(error_msg) from e
        
        return self._config_cache[class_name]
    
    def reload_settings(self, settings_class: Type[BaseSettings]) -> BaseSettings:
        """Reload settings for a specific class (clears cache)."""
        class_name = settings_class.__name__
        if class_name in self._config_cache:
            del self._config_cache[class_name]
        return self.get_settings(settings_class)
    
    def validate_all_settings(self) -> Dict[str, Any]:
        """Validate all settings and return validation results."""
        settings_classes = [
            ServerSettings,
            SecuritySettings,
            DatabaseSettings,
            FileUploadSettings,
            LLMSettings,
            EmbeddingSettings,
            VectorStoreSettings,
            GmailSettings,
            EmailProcessingSettings,
            LoggingSettings,
            CORSSettings,
            MonitoringSettings
        ]
        
        results = {
            "environment": self.environment.value,
            "valid": True,
            "errors": {},
            "warnings": {},
            "summary": {}
        }
        
        for settings_class in settings_classes:
            class_name = settings_class.__name__
            try:
                settings = self.get_settings(settings_class)
                results["summary"][class_name] = "✅ Valid"
                
                # Check for warnings (e.g., default values in production)
                warnings = self._check_settings_warnings(settings, class_name)
                if warnings:
                    results["warnings"][class_name] = warnings
                
            except ConfigurationError as e:
                results["valid"] = False
                results["errors"][class_name] = str(e)
                results["summary"][class_name] = "❌ Invalid"
        
        return results
    
    def _check_settings_warnings(self, settings: BaseSettings, class_name: str) -> list:
        """Check for configuration warnings."""
        warnings = []
        
        # Production-specific warnings
        if self.environment == EnvironmentType.PRODUCTION:
            if class_name == "SecuritySettings":
                # Check for default or weak secret keys
                if hasattr(settings, 'secret_key'):
                    if len(settings.secret_key) < 64:
                        warnings.append("Consider using a longer secret key in production (64+ chars)")
            
            elif class_name == "ServerSettings":
                if hasattr(settings, 'debug') and settings.debug:
                    warnings.append("Debug mode should be disabled in production")
            
            elif class_name == "DatabaseSettings":
                if hasattr(settings, 'url') and "sqlite" in settings.url:
                    warnings.append("Consider using PostgreSQL or MySQL in production")
            
            elif class_name == "CORSSettings":
                if hasattr(settings, 'allowed_origins') and "*" in settings.allowed_origins:
                    warnings.append("Wildcard CORS origins should be avoided in production")
        
        return warnings
    
    def generate_env_template(self, include_comments: bool = True) -> str:
        """Generate .env template with all available settings."""
        template_lines = []
        
        if include_comments:
            template_lines.extend([
                "# Personal AI Agent Configuration",
                f"# Environment: {self.environment.value}",
                "# Generated template with all available settings",
                "",
                "# Environment Type (development, staging, production, testing)",
                f"ENVIRONMENT={self.environment.value}",
                ""
            ])
        
        settings_classes = [
            ("Server Settings", ServerSettings),
            ("Security Settings", SecuritySettings),
            ("Database Settings", DatabaseSettings),
            ("File Upload Settings", FileUploadSettings),
            ("LLM Settings", LLMSettings),
            ("Embedding Settings", EmbeddingSettings),
            ("Vector Store Settings", VectorStoreSettings),
            ("Gmail Settings", GmailSettings),
            ("Email Processing Settings", EmailProcessingSettings),
            ("Logging Settings", LoggingSettings),
            ("CORS Settings", CORSSettings),
            ("Monitoring Settings", MonitoringSettings),
        ]
        
        for section_name, settings_class in settings_classes:
            if include_comments:
                template_lines.extend([
                    f"# {section_name}",
                    *self._generate_settings_template(settings_class),
                    ""
                ])
            else:
                template_lines.extend(self._generate_settings_template(settings_class))
        
        return "\n".join(template_lines)
    
    def _generate_settings_template(self, settings_class: Type[BaseSettings]) -> list:
        """Generate template lines for a specific settings class."""
        lines = []
        
        # Get settings instance with defaults
        try:
            settings = settings_class()
            model_config = getattr(settings_class, 'model_config', {})
            env_prefix = model_config.get('env_prefix', '')
            
            # Get field information from the model (Pydantic v2)
            if hasattr(settings_class, 'model_fields'):
                fields = settings_class.model_fields
            else:
                fields = getattr(settings_class, '__fields__', {})
            
            for field_name, field_info in fields.items():
                env_var_name = f"{env_prefix}{field_name.upper()}"
                
                # Get default value
                default_value = getattr(settings, field_name, None)
                if default_value is not None:
                    # Format different types appropriately
                    if isinstance(default_value, bool):
                        default_value = str(default_value).lower()
                    elif isinstance(default_value, Path):
                        default_value = str(default_value)
                    elif isinstance(default_value, list):
                        default_value = ",".join(map(str, default_value))
                
                # Add description as comment if available
                description = getattr(field_info, 'description', None)
                if description:
                    lines.append(f"# {description}")
                
                # Add the environment variable
                if default_value is not None:
                    lines.append(f"{env_var_name}={default_value}")
                else:
                    lines.append(f"# {env_var_name}=")
                
                lines.append("")  # Empty line after each setting
        
        except Exception as e:
            logger.warning(f"Could not generate template for {settings_class.__name__}: {e}")
        
        return lines


class ApplicationSettings:
    """Unified application settings using the enhanced configuration system."""
    
    def __init__(self, environment: Optional[EnvironmentType] = None):
        self._config_manager = ConfigurationManager(environment)
        self._settings_cache = {}
    
    @property
    def environment(self) -> EnvironmentType:
        """Get current environment."""
        return self._config_manager.environment
    
    @property
    def server(self) -> ServerSettings:
        """Get server settings."""
        return self._config_manager.get_settings(ServerSettings)
    
    @property
    def security(self) -> SecuritySettings:
        """Get security settings."""
        return self._config_manager.get_settings(SecuritySettings)
    
    @property
    def database(self) -> DatabaseSettings:
        """Get database settings."""
        return self._config_manager.get_settings(DatabaseSettings)
    
    @property
    def upload(self) -> FileUploadSettings:
        """Get file upload settings."""
        return self._config_manager.get_settings(FileUploadSettings)
    
    @property
    def llm(self) -> LLMSettings:
        """Get LLM settings."""
        return self._config_manager.get_settings(LLMSettings)
    
    @property
    def embedding(self) -> EmbeddingSettings:
        """Get embedding settings."""
        return self._config_manager.get_settings(EmbeddingSettings)
    
    @property
    def vector_store(self) -> VectorStoreSettings:
        """Get vector store settings."""
        return self._config_manager.get_settings(VectorStoreSettings)
    
    @property
    def gmail(self) -> GmailSettings:
        """Get Gmail settings."""
        return self._config_manager.get_settings(GmailSettings)
    
    @property
    def email_processing(self) -> EmailProcessingSettings:
        """Get email processing settings."""
        return self._config_manager.get_settings(EmailProcessingSettings)
    
    @property
    def logging(self) -> LoggingSettings:
        """Get logging settings."""
        return self._config_manager.get_settings(LoggingSettings)
    
    @property
    def cors(self) -> CORSSettings:
        """Get CORS settings."""
        return self._config_manager.get_settings(CORSSettings)
    
    @property
    def monitoring(self) -> MonitoringSettings:
        """Get monitoring settings."""
        return self._config_manager.get_settings(MonitoringSettings)
    
    def validate_all(self) -> Dict[str, Any]:
        """Validate all configuration settings."""
        return self._config_manager.validate_all_settings()
    
    def reload_all(self):
        """Reload all configuration settings."""
        self._config_manager._config_cache.clear()
    
    @contextmanager
    def override_settings(self, **overrides):
        """Temporarily override settings for testing."""
        original_env = os.environ.copy()
        try:
            # Apply overrides to environment
            for key, value in overrides.items():
                os.environ[key] = str(value)
            
            # Clear cache to force reload
            self._config_manager._config_cache.clear()
            yield self
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
            self._config_manager._config_cache.clear()


# Global settings instance
settings = ApplicationSettings()


def get_settings() -> ApplicationSettings:
    """Get the global settings instance."""
    return settings


def validate_configuration() -> bool:
    """Validate configuration and log results."""
    try:
        results = settings.validate_all()
        
        logger.info(f"Configuration validation for environment: {results['environment']}")
        
        # Log summary
        for class_name, status in results['summary'].items():
            logger.info(f"  {class_name}: {status}")
        
        # Log warnings
        if results['warnings']:
            logger.warning("Configuration warnings:")
            for class_name, warnings in results['warnings'].items():
                for warning in warnings:
                    logger.warning(f"  {class_name}: {warning}")
        
        # Log errors
        if results['errors']:
            logger.error("Configuration errors:")
            for class_name, error in results['errors'].items():
                logger.error(f"  {class_name}: {error}")
        
        if results['valid']:
            logger.info("✅ All configuration validation passed")
        else:
            logger.error("❌ Configuration validation failed")
        
        return results['valid']
    
    except Exception as e:
        logger.error(f"Configuration validation failed with exception: {e}")
        return False