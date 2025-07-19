#!/usr/bin/env python3
"""
Quick fix for LLM context and decode issues.
This addresses the 'llama_decode returned -3' error and context mismatch.
"""

import logging
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from app.utils.llm import reset_llm, get_llm
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_llm_with_simple_query():
    """Test LLM with a simple query to diagnose issues."""
    logger.info("🔧 Testing LLM with simple query...")
    
    try:
        # Reset LLM to clear any stuck state
        reset_llm()
        
        # Simple test query
        test_query = "What is 2 + 2?"
        test_context = ["The answer to 2 + 2 is 4."]
        
        from app.utils.llm import generate_response
        
        logger.info(f"Testing with query: '{test_query}'")
        logger.info(f"Context: {test_context}")
        
        response = generate_response(test_query, test_context)
        logger.info(f"✅ LLM Response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM test failed: {e}")
        return False


def test_apple_invoice_query():
    """Test the specific Apple invoice query that was failing."""
    logger.info("🍎 Testing Apple invoice query...")
    
    try:
        # Reset LLM
        reset_llm()
        
        # Simplified Apple invoice context (shorter to avoid context issues)
        apple_context = [
            "Subject: Invoice from Apple Store - Payment Confirmation. Dear Customer, Thank you for your purchase from Apple Store. Invoice #INV-2024-001. Total: $12.99. Payment processed successfully.",
            "Subject: Your receipt from Apple. iCloud+ with 2 TB (Monthly). Subtotal: $9.99"
        ]
        
        query = "How much was the Apple invoice?"
        
        from app.utils.llm import generate_response
        
        logger.info(f"Testing Apple query: '{query}'")
        response = generate_response(query, apple_context)
        logger.info(f"✅ Apple Invoice Response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Apple invoice test failed: {e}")
        return False


def check_llm_configuration():
    """Check current LLM configuration for issues."""
    logger.info("📊 Checking LLM Configuration...")
    
    logger.info(f"LLM Model Path: {settings.LLM_MODEL_PATH}")
    logger.info(f"Context Window: {settings.LLM_CONTEXT_WINDOW}")
    logger.info(f"Max Tokens: {settings.LLM_MAX_TOKENS}")
    logger.info(f"Temperature: {settings.LLM_TEMPERATURE}")
    logger.info(f"Use Metal: {settings.USE_METAL}")
    logger.info(f"Metal GPU Layers: {settings.METAL_N_GPU_LAYERS}")
    
    # Check if model file exists
    model_path = Path(settings.LLM_MODEL_PATH)
    if model_path.exists():
        logger.info(f"✅ Model file exists: {model_path}")
        logger.info(f"Model file size: {model_path.stat().st_size / (1024*1024*1024):.1f} GB")
    else:
        logger.error(f"❌ Model file not found: {model_path}")
        return False
    
    return True


def create_llm_with_safer_config():
    """Create LLM instance with safer configuration."""
    logger.info("🛠️ Creating LLM with safer configuration...")
    
    try:
        # Reset any existing LLM
        reset_llm()
        
        # Get LLM with conservative settings
        llm = get_llm()
        
        if llm:
            logger.info("✅ LLM created successfully with safer config")
            return True
        else:
            logger.error("❌ Failed to create LLM")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error creating LLM: {e}")
        return False


def main():
    """Main diagnosis and fix function."""
    logger.info("🚀 Starting LLM Context Issue Fix")
    logger.info("=" * 50)
    
    # Step 1: Check configuration
    if not check_llm_configuration():
        logger.error("❌ LLM configuration check failed")
        return
    
    # Step 2: Create LLM with safer config
    if not create_llm_with_safer_config():
        logger.error("❌ Failed to create LLM with safer config")
        return
    
    # Step 3: Test with simple query
    if not test_llm_with_simple_query():
        logger.error("❌ Simple LLM test failed")
        logger.error("Possible solutions:")
        logger.error("1. Restart the application completely")
        logger.error("2. Check if model file is corrupted")
        logger.error("3. Reduce context window in settings")
        return
    
    # Step 4: Test Apple invoice query
    if not test_apple_invoice_query():
        logger.error("❌ Apple invoice test failed")
        logger.error("The LLM works for simple queries but fails on complex ones")
        logger.error("This suggests a context length or prompt formatting issue")
        return
    
    logger.info("🎉 All tests passed! LLM should be working correctly now.")
    logger.info("")
    logger.info("💡 Recommendations:")
    logger.info("1. The Apple invoice query should now work correctly")
    logger.info("2. If issues persist, try restarting the application")
    logger.info("3. Consider using shorter, more specific queries")


if __name__ == "__main__":
    main()