#!/usr/bin/env python3
"""
Test script to check model loading and response generation
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.llm import get_llm, get_current_model_info, generate_response
from app.core.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_model_loading():
    """Test model loading and basic response generation"""
    
    print("=== MODEL LOADING TEST ===")
    
    # Check current config
    print(f"LLM_MODEL_PATH from config: {settings.LLM_MODEL_PATH}")
    
    # Test model loading
    try:
        llm = get_llm()
        print("Model loaded successfully")
        
        model_info = get_current_model_info()
        print(f"Current model info: {model_info}")
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    # Test simple response generation
    print("\n=== SIMPLE RESPONSE TEST ===")
    
    simple_context = [
        "Transaction: 05/17 Foreign Exch Rt ADJ Fee 05/16 Unifree Ist 8107 / M Istanbul Card 6822 6.35"
    ]
    
    query = "How much did I spend on Istanbul Card?"
    
    try:
        response = generate_response(query, simple_context)
        print(f"Query: {query}")
        print(f"Response: {response}")
        print(f"Response length: {len(response)}")
    except Exception as e:
        print(f"Error generating response: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_loading()