"""
Configuration management utilities.

Provides CLI commands and utilities for configuration validation,
template generation, and environment management.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from app.core.config_enhanced import ApplicationSettings, EnvironmentType
from app.core.config_schema import *


def generate_env_file(
    environment: EnvironmentType = EnvironmentType.DEVELOPMENT,
    output_path: Optional[Path] = None,
    include_comments: bool = True
) -> Path:
    """Generate environment file template."""
    settings = ApplicationSettings(environment)
    template_content = settings._config_manager.generate_env_template(include_comments)
    
    if output_path is None:
        output_path = Path(f".env.{environment.value}.template")
    
    output_path.write_text(template_content)
    print(f"Generated environment template: {output_path}")
    return output_path


def validate_configuration(environment: Optional[EnvironmentType] = None) -> bool:
    """Validate configuration and print results."""
    settings = ApplicationSettings(environment)
    results = settings.validate_all()
    
    print(f"\n🔍 Configuration Validation for {results['environment'].upper()}")
    print("=" * 60)
    
    # Print summary
    print("\n📋 Configuration Summary:")
    for class_name, status in results['summary'].items():
        print(f"  {status} {class_name}")
    
    # Print warnings
    if results['warnings']:
        print("\n⚠️  Configuration Warnings:")
        for class_name, warnings in results['warnings'].items():
            print(f"\n  {class_name}:")
            for warning in warnings:
                print(f"    • {warning}")
    
    # Print errors
    if results['errors']:
        print("\n❌ Configuration Errors:")
        for class_name, error in results['errors'].items():
            print(f"\n  {class_name}:")
            print(f"    • {error}")
    
    # Print final result
    print("\n" + "=" * 60)
    if results['valid']:
        print("✅ Configuration validation PASSED")
    else:
        print("❌ Configuration validation FAILED")
        print("\nTo fix errors:")
        print("1. Check your .env file or environment variables")
        print("2. Run 'python -m app.utils.config_utils generate-template' for examples")
        print("3. See documentation for required settings")
    
    print()
    return results['valid']


def show_current_configuration(environment: Optional[EnvironmentType] = None):
    """Display current configuration (without sensitive values)."""
    settings = ApplicationSettings(environment)
    
    print(f"\n📖 Current Configuration for {settings.environment.value.upper()}")
    print("=" * 60)
    
    # Define sensitive fields to hide
    sensitive_fields = {
        'secret_key', 'password', 'token', 'key', 'secret', 
        'client_secret', 'client_id'
    }
    
    config_sections = [
        ("Server", settings.server),
        ("Security", settings.security),
        ("Database", settings.database),
        ("File Upload", settings.upload),
        ("LLM", settings.llm),
        ("Embedding", settings.embedding),
        ("Vector Store", settings.vector_store),
        ("Gmail", settings.gmail),
        ("Email Processing", settings.email_processing),
        ("Logging", settings.logging),
        ("CORS", settings.cors),
        ("Monitoring", settings.monitoring),
    ]
    
    for section_name, section_settings in config_sections:
        print(f"\n📁 {section_name}:")
        
        # Convert to dict and filter sensitive values
        settings_dict = section_settings.dict()
        for key, value in settings_dict.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                if value:
                    print(f"  {key}: ***HIDDEN***")
                else:
                    print(f"  {key}: <not set>")
            else:
                print(f"  {key}: {value}")


def export_configuration(
    environment: Optional[EnvironmentType] = None,
    output_format: str = "json",
    output_path: Optional[Path] = None,
    include_sensitive: bool = False
) -> Path:
    """Export current configuration to file."""
    settings = ApplicationSettings(environment)
    
    # Collect all settings
    config_data = {
        "environment": settings.environment.value,
        "server": settings.server.dict(),
        "security": settings.security.dict(),
        "database": settings.database.dict(),
        "upload": settings.upload.dict(),
        "llm": settings.llm.dict(),
        "embedding": settings.embedding.dict(),
        "vector_store": settings.vector_store.dict(),
        "gmail": settings.gmail.dict(),
        "email_processing": settings.email_processing.dict(),
        "logging": settings.logging.dict(),
        "cors": settings.cors.dict(),
        "monitoring": settings.monitoring.dict(),
    }
    
    # Filter sensitive data if requested
    if not include_sensitive:
        sensitive_fields = {
            'secret_key', 'password', 'token', 'key', 'secret',
            'client_secret', 'client_id'
        }
        
        def filter_sensitive(obj):
            if isinstance(obj, dict):
                return {
                    k: "***HIDDEN***" if any(s in k.lower() for s in sensitive_fields) and v
                    else filter_sensitive(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return [filter_sensitive(item) for item in obj]
            else:
                return obj
        
        config_data = filter_sensitive(config_data)
    
    # Generate output path
    if output_path is None:
        env_suffix = f".{settings.environment.value}" if settings.environment != EnvironmentType.DEVELOPMENT else ""
        output_path = Path(f"config_export{env_suffix}.{output_format}")
    
    # Export based on format
    if output_format.lower() == "json":
        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
    elif output_format.lower() == "yaml":
        try:
            import yaml
            with open(output_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, default=str)
        except ImportError:
            print("PyYAML not installed. Using JSON format instead.")
            output_path = output_path.with_suffix('.json')
            with open(output_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
    else:
        raise ValueError(f"Unsupported format: {output_format}")
    
    print(f"Configuration exported to: {output_path}")
    return output_path


def check_environment_differences():
    """Compare configuration across different environments."""
    environments = [EnvironmentType.DEVELOPMENT, EnvironmentType.STAGING, EnvironmentType.PRODUCTION]
    
    print("\n🔄 Environment Configuration Comparison")
    print("=" * 60)
    
    configs = {}
    for env in environments:
        try:
            settings = ApplicationSettings(env)
            configs[env.value] = {
                "server": settings.server.dict(),
                "security": settings.security.dict(),
                "database": settings.database.dict(),
            }
            print(f"✅ {env.value}: Configuration loaded")
        except Exception as e:
            print(f"❌ {env.value}: {e}")
            configs[env.value] = None
    
    # Compare configurations
    if len([c for c in configs.values() if c is not None]) < 2:
        print("\nNeed at least 2 valid environments to compare")
        return
    
    print(f"\n📊 Key Differences:")
    
    # Compare specific important settings
    important_settings = [
        ("server.debug", "Debug mode"),
        ("server.port", "Server port"),
        ("security.access_token_expire_minutes", "Token expiration"),
        ("database.url", "Database URL"),
    ]
    
    for setting_path, description in important_settings:
        print(f"\n  {description} ({setting_path}):")
        
        values = {}
        for env_name, config in configs.items():
            if config is not None:
                # Navigate nested dict
                parts = setting_path.split('.')
                value = config
                try:
                    for part in parts:
                        value = value[part]
                    values[env_name] = value
                except KeyError:
                    values[env_name] = "<not set>"
        
        for env_name, value in values.items():
            print(f"    {env_name}: {value}")


def main():
    """CLI interface for configuration utilities."""
    parser = argparse.ArgumentParser(description="Configuration management utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument(
        "--environment", "-e",
        type=str,
        choices=[e.value for e in EnvironmentType],
        help="Environment to validate"
    )
    
    # Generate template command
    template_parser = subparsers.add_parser("generate-template", help="Generate .env template")
    template_parser.add_argument(
        "--environment", "-e",
        type=str,
        choices=[e.value for e in EnvironmentType],
        default="development",
        help="Environment type for template"
    )
    template_parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path"
    )
    template_parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Generate template without comments"
    )
    
    # Show config command
    show_parser = subparsers.add_parser("show", help="Show current configuration")
    show_parser.add_argument(
        "--environment", "-e",
        type=str,
        choices=[e.value for e in EnvironmentType],
        help="Environment to show"
    )
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export configuration")
    export_parser.add_argument(
        "--environment", "-e",
        type=str,
        choices=[e.value for e in EnvironmentType],
        help="Environment to export"
    )
    export_parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["json", "yaml"],
        default="json",
        help="Output format"
    )
    export_parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path"
    )
    export_parser.add_argument(
        "--include-sensitive",
        action="store_true",
        help="Include sensitive values in export"
    )
    
    # Compare command
    subparsers.add_parser("compare", help="Compare configurations across environments")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "validate":
            env = EnvironmentType(args.environment) if args.environment else None
            success = validate_configuration(env)
            sys.exit(0 if success else 1)
        
        elif args.command == "generate-template":
            env = EnvironmentType(args.environment)
            output = Path(args.output) if args.output else None
            generate_env_file(env, output, not args.no_comments)
        
        elif args.command == "show":
            env = EnvironmentType(args.environment) if args.environment else None
            show_current_configuration(env)
        
        elif args.command == "export":
            env = EnvironmentType(args.environment) if args.environment else None
            output = Path(args.output) if args.output else None
            export_configuration(env, args.format, output, args.include_sensitive)
        
        elif args.command == "compare":
            check_environment_differences()
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()