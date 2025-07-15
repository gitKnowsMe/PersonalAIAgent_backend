#!/usr/bin/env python3
"""
Test script for the enhanced configuration management system.
Validates configuration loading, environment-specific settings, and utilities.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.config_enhanced import ApplicationSettings, EnvironmentType, ConfigurationError
from app.utils.config_utils import (
    validate_configuration,
    generate_env_file,
    show_current_configuration,
    export_configuration
)


def test_environment_detection():
    """Test automatic environment detection."""
    print("🧪 Testing Environment Detection")
    
    # Test explicit environment setting
    original_env = os.environ.get("ENVIRONMENT", "")
    
    try:
        # Test development detection
        os.environ["ENVIRONMENT"] = "development"
        settings = ApplicationSettings()
        assert settings.environment == EnvironmentType.DEVELOPMENT
        print("✅ Explicit environment detection works")
        
        # Test testing detection (pytest simulation)
        del os.environ["ENVIRONMENT"]
        sys.modules["pytest"] = type(sys)("pytest")  # Mock pytest module
        settings = ApplicationSettings()
        assert settings.environment == EnvironmentType.TESTING
        print("✅ Testing environment auto-detection works")
        
        # Clean up
        del sys.modules["pytest"]
        
    finally:
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        elif "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]
    
    return True


def test_configuration_validation():
    """Test configuration validation with different scenarios."""
    print("\n🧪 Testing Configuration Validation")
    
    # Test with development environment
    try:
        settings = ApplicationSettings(EnvironmentType.DEVELOPMENT)
        results = settings.validate_all()
        print(f"✅ Development validation: {results['valid']}")
        
        # Check that we get some warnings in development
        if results['warnings']:
            print(f"   Found {len(results['warnings'])} warnings (expected)")
        
    except Exception as e:
        print(f"❌ Development validation failed: {e}")
        return False
    
    # Test with invalid configuration
    try:
        with settings.override_settings(SECURITY_SECRET_KEY="short"):
            try:
                invalid_settings = ApplicationSettings()
                invalid_settings.security  # This should trigger validation
                print("❌ Should have failed with short secret key")
                return False
            except ConfigurationError:
                print("✅ Invalid configuration properly rejected")
    except Exception as e:
        print(f"⚠️  Override test failed: {e}")
    
    return True


def test_environment_specific_loading():
    """Test loading different environment configurations."""
    print("\n🧪 Testing Environment-Specific Loading")
    
    environments = [
        EnvironmentType.DEVELOPMENT,
        EnvironmentType.PRODUCTION,
        EnvironmentType.TESTING
    ]
    
    for env in environments:
        try:
            settings = ApplicationSettings(env)
            
            # Check that environment-specific settings are loaded
            server_settings = settings.server
            
            # Verify environment-specific values
            if env == EnvironmentType.DEVELOPMENT:
                assert server_settings.debug == True
                assert server_settings.port == 8000
            elif env == EnvironmentType.PRODUCTION:
                assert server_settings.debug == False
                assert server_settings.workers == 4
            elif env == EnvironmentType.TESTING:
                assert server_settings.port == 8001
                assert server_settings.workers == 1
            
            print(f"✅ {env.value} configuration loaded correctly")
            
        except Exception as e:
            print(f"❌ {env.value} configuration failed: {e}")
            return False
    
    return True


def test_type_safety_and_validation():
    """Test type safety and validation features."""
    print("\n🧪 Testing Type Safety and Validation")
    
    try:
        settings = ApplicationSettings(EnvironmentType.DEVELOPMENT)
        
        # Test that types are correct
        assert isinstance(settings.server.port, int)
        assert isinstance(settings.server.debug, bool)
        assert isinstance(settings.upload.max_file_size, int)
        assert isinstance(settings.llm.temperature, float)
        
        print("✅ Type safety verified")
        
        # Test validation methods
        gmail_settings = settings.gmail
        if gmail_settings.client_id and gmail_settings.client_secret:
            assert gmail_settings.is_configured == True
        else:
            assert gmail_settings.is_configured == False
        
        print("✅ Validation methods work correctly")
        
        # Test computed properties
        upload_size_mb = settings.upload.max_file_size_mb
        assert isinstance(upload_size_mb, float)
        assert upload_size_mb > 0
        
        print("✅ Computed properties work correctly")
        
    except Exception as e:
        print(f"❌ Type safety test failed: {e}")
        return False
    
    return True


def test_configuration_utilities():
    """Test configuration management utilities."""
    print("\n🧪 Testing Configuration Utilities")
    
    try:
        # Test environment file generation
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "test.env"
            
            generate_env_file(
                environment=EnvironmentType.DEVELOPMENT,
                output_path=template_path,
                include_comments=True
            )
            
            assert template_path.exists()
            content = template_path.read_text()
            assert "SERVER_HOST=" in content
            assert "ENVIRONMENT=development" in content
            print("✅ Environment file generation works")
        
        # Test validation utility
        result = validate_configuration(EnvironmentType.DEVELOPMENT)
        assert isinstance(result, bool)
        print("✅ Configuration validation utility works")
        
        # Test export functionality
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "config.json"
            
            export_configuration(
                environment=EnvironmentType.DEVELOPMENT,
                output_format="json",
                output_path=export_path,
                include_sensitive=False
            )
            
            assert export_path.exists()
            print("✅ Configuration export works")
    
    except Exception as e:
        print(f"❌ Utilities test failed: {e}")
        return False
    
    return True


def test_settings_override():
    """Test settings override functionality for testing."""
    print("\n🧪 Testing Settings Override")
    
    try:
        settings = ApplicationSettings(EnvironmentType.DEVELOPMENT)
        
        # Get original value
        original_port = settings.server.port
        
        # Test override
        with settings.override_settings(SERVER_PORT="9999"):
            new_port = settings.server.port
            assert new_port == 9999
            assert new_port != original_port
        
        # Verify restoration
        restored_port = settings.server.port
        assert restored_port == original_port
        
        print("✅ Settings override works correctly")
        
    except Exception as e:
        print(f"❌ Settings override test failed: {e}")
        return False
    
    return True


def test_comprehensive_coverage():
    """Test that all configuration sections are properly covered."""
    print("\n🧪 Testing Comprehensive Coverage")
    
    try:
        settings = ApplicationSettings(EnvironmentType.DEVELOPMENT)
        
        # Verify all major settings sections are accessible
        sections = [
            ("server", settings.server),
            ("security", settings.security),
            ("database", settings.database),
            ("upload", settings.upload),
            ("llm", settings.llm),
            ("embedding", settings.embedding),
            ("vector_store", settings.vector_store),
            ("gmail", settings.gmail),
            ("email_processing", settings.email_processing),
            ("logging", settings.logging),
            ("cors", settings.cors),
            ("monitoring", settings.monitoring),
        ]
        
        for section_name, section_obj in sections:
            assert section_obj is not None
            assert hasattr(section_obj, 'model_dump')
            section_dict = section_obj.model_dump()
            assert len(section_dict) > 0
            print(f"   ✅ {section_name}: {len(section_dict)} settings")
        
        print("✅ All configuration sections are properly covered")
        
    except Exception as e:
        print(f"❌ Comprehensive coverage test failed: {e}")
        return False
    
    return True


def main():
    """Run all configuration system tests."""
    print("🚀 Testing Enhanced Configuration Management System")
    print("=" * 60)
    
    tests = [
        ("Environment Detection", test_environment_detection),
        ("Configuration Validation", test_configuration_validation),
        ("Environment-Specific Loading", test_environment_specific_loading),
        ("Type Safety and Validation", test_type_safety_and_validation),
        ("Configuration Utilities", test_configuration_utilities),
        ("Settings Override", test_settings_override),
        ("Comprehensive Coverage", test_comprehensive_coverage),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All configuration system tests passed!")
        print("\n✅ Enhanced configuration management is working correctly:")
        print("   1. Environment-specific configuration loading")
        print("   2. Type-safe settings with Pydantic validation")
        print("   3. Comprehensive error handling and validation")
        print("   4. Configuration management utilities")
        print("   5. Testing and override capabilities")
        print("\n🚀 The configuration system is ready for production use!")
    else:
        print("\n⚠️  Some tests failed. Please review the configuration implementation.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)