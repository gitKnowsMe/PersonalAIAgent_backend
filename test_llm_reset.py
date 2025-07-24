#!/usr/bin/env python3
"""
Test script to reset LLM and see debug output
"""
import sys
from pathlib import Path

# Add the app to Python path
sys.path.append(str(Path(__file__).parent))

print("=== TESTING LLM RESET ===")

try:
    from app.utils.llm import reset_llm, get_llm
    
    print("1. Resetting any existing LLM...")
    reset_llm()
    
    print("2. Attempting to get LLM (this should trigger initialization)...")
    llm = get_llm()
    
    print("3. LLM initialized successfully!")
    print(f"   LLM object: {type(llm)}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()