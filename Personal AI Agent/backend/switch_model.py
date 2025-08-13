#!/usr/bin/env python3
"""
Script to switch the default LLM model for the Personal AI Agent
"""

import os
import sys
from pathlib import Path

# Available models
MODELS = {
    "mistral-7b": "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
    "phi-2": "phi-2-instruct-Q4_K_M.gguf"
}

def update_env_file(model_name: str):
    """Update the .env file with the new model"""
    base_dir = Path(__file__).parent
    env_file = base_dir / ".env"
    model_path = base_dir / "models" / MODELS[model_name]
    
    # Read existing .env file
    env_lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_lines = f.readlines()
    
    # Update or add LLM_MODEL_PATH
    updated = False
    for i, line in enumerate(env_lines):
        if line.startswith('LLM_MODEL_PATH='):
            env_lines[i] = f'LLM_MODEL_PATH={model_path}\n'
            updated = True
            break
    
    if not updated:
        env_lines.append(f'LLM_MODEL_PATH={model_path}\n')
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.writelines(env_lines)
    
    print(f"✅ Updated .env file to use {model_name}")
    print(f"Model path: {model_path}")

def show_current_config():
    """Show current model configuration"""
    try:
        sys.path.append('app')
        from app.core.config import settings
        from app.utils.llm import get_current_model_info
        
        print("Current Configuration:")
        print(f"  Model Path: {settings.LLM_MODEL_PATH}")
        
        # Try to determine which model is configured
        model_name = "unknown"
        for name, filename in MODELS.items():
            if filename in settings.LLM_MODEL_PATH:
                model_name = name
                break
        
        print(f"  Model: {model_name}")
        
        # Show runtime info if model is loaded
        model_info = get_current_model_info()
        if model_info['loaded']:
            print(f"  Currently Loaded: {model_info['model_name']}")
        else:
            print(f"  Currently Loaded: None")
            
    except Exception as e:
        print(f"Could not read current config: {e}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("LLM Model Switcher for Personal AI Agent")
        print("="*50)
        
        show_current_config()
        
        print("\\nAvailable Models:")
        for name, filename in MODELS.items():
            size = "Unknown size"
            model_path = Path(__file__).parent / "models" / filename
            if model_path.exists() or model_path.is_symlink():
                try:
                    if model_path.is_symlink():
                        actual_path = model_path.resolve()
                        size_bytes = actual_path.stat().st_size
                    else:
                        size_bytes = model_path.stat().st_size
                    size = f"{size_bytes / (1024**3):.1f}GB"
                except:
                    size = "Unknown size"
            else:
                size = "NOT FOUND"
            
            print(f"  {name}: {filename} ({size})")
        
        print("\\nUsage:")
        print(f"  python {sys.argv[0]} <model_name>")
        print(f"  python {sys.argv[0]} phi-2      # Switch to Phi-2 (faster)")
        print(f"  python {sys.argv[0]} mistral-7b # Switch to Mistral-7B (higher quality)")
        print("\\nNote: Restart the server after switching models")
        return
    
    model_name = sys.argv[1].lower()
    
    if model_name not in MODELS:
        print(f"❌ Unknown model: {model_name}")
        print(f"Available models: {list(MODELS.keys())}")
        sys.exit(1)
    
    # Check if model file exists
    model_path = Path(__file__).parent / "models" / MODELS[model_name]
    if not (model_path.exists() or model_path.is_symlink()):
        print(f"❌ Model file not found: {model_path}")
        print("Make sure the model file exists in the models/ directory")
        sys.exit(1)
    
    # Update configuration
    update_env_file(model_name)
    
    print("\\n📋 Next Steps:")
    print("1. Restart the Personal AI Agent server")
    print("2. The new model will be loaded on the first query")
    print("\\n🚀 Performance Expectations:")
    if model_name == "phi-2":
        print("  • ~55% faster response times")
        print("  • ~2x better throughput")  
        print("  • Slightly more concise responses")
    else:
        print("  • More detailed, comprehensive responses")
        print("  • Better handling of complex queries")
        print("  • Slower but higher quality output")

if __name__ == "__main__":
    main()