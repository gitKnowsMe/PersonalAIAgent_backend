#!/usr/bin/env python3
"""
Enable hallucination prevention features in AI configuration
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai_config_service import get_ai_config_service, ResponseValidationLevel, AIBehaviorMode


def enable_hallucination_prevention():
    """Enable hallucination prevention features"""
    
    print("=== Enabling Hallucination Prevention Features ===\n")
    
    service = get_ai_config_service()
    
    # Get current configuration
    current_config = service.get_ai_config()
    print("Current Configuration:")
    print(f"  Behavior Mode: {current_config.behavior_mode}")
    print(f"  Validation Level: {current_config.validation_level}")
    print(f"  Hallucination Detection: {current_config.enable_hallucination_detection}")
    print(f"  Hallucination Threshold: {current_config.hallucination_threshold}")
    
    print("\n" + "="*50)
    
    # Update configuration for better hallucination prevention
    updates = {
        'enable_hallucination_detection': True,
        'validation_level': ResponseValidationLevel.MODERATE,
        'behavior_mode': AIBehaviorMode.STRICT_CONTEXT_ONLY,
        'hallucination_threshold': 0.8,  # More strict threshold
        'require_context_reference': True,
        'allow_general_knowledge_fallback': False,
        'temperature': 0.2,  # Lower temperature for more consistent responses
        'max_tokens': 300,   # Shorter responses to reduce hallucination risk
    }
    
    print("Applying Updates:")
    for key, value in updates.items():
        print(f"  {key}: {value}")
    
    # Apply updates
    success = service.update_ai_config(**updates)
    
    if success:
        print("\n✅ Configuration updated successfully!")
        
        # Show updated configuration
        updated_config = service.get_ai_config()
        print("\nUpdated Configuration:")
        print(f"  Behavior Mode: {updated_config.behavior_mode}")
        print(f"  Validation Level: {updated_config.validation_level}")
        print(f"  Hallucination Detection: {updated_config.enable_hallucination_detection}")
        print(f"  Hallucination Threshold: {updated_config.hallucination_threshold}")
        print(f"  Temperature: {updated_config.temperature}")
        print(f"  Max Tokens: {updated_config.max_tokens}")
        
        print("\n" + "="*50)
        print("Hallucination prevention features are now enabled!")
        print("\nKey improvements:")
        print("  ✅ Strict context-only mode enabled")
        print("  ✅ Moderate validation level")
        print("  ✅ Lower temperature for consistency")
        print("  ✅ Shorter response length")
        print("  ✅ Context reference required")
        print("  ✅ General knowledge fallback disabled")
        
    else:
        print("\n❌ Failed to update configuration")
    
    return success


if __name__ == "__main__":
    enable_hallucination_prevention() 