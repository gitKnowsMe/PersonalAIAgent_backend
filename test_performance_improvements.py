#!/usr/bin/env python3
"""
Test script to verify performance improvements
"""

import sys
sys.path.append('.')
from app.utils.llm import generate_answer, reset_llm, get_llm
from app.core.config import settings
import time
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("performance_test")

async def test_performance_improvements():
    print("🚀 Testing Performance Improvements")
    print("=" * 60)
    
    # Show current configuration
    print("📋 Current Configuration:")
    print(f"   Context Window: {settings.LLM_CONTEXT_WINDOW}")
    print(f"   Metal Enabled: {settings.USE_METAL}")
    print(f"   Metal GPU Layers: {settings.METAL_N_GPU_LAYERS}")
    print(f"   LLM Threads: {settings.LLM_THREADS}")
    print()
    
    # Reset LLM to ensure clean state
    reset_llm()
    
    # Test queries
    test_queries = [
        "What is artificial intelligence?",
        "How does machine learning work?", 
        "What is prompt engineering?"
    ]
    
    dummy_context = [
        {
            'content': 'Artificial intelligence (AI) is a branch of computer science that aims to create intelligent machines.',
            'score': 0.95,
            'metadata': {'source': 'ai_basics.pdf'}
        },
        {
            'content': 'Machine learning is a subset of AI that enables computers to learn and improve from experience.',
            'score': 0.90,
            'metadata': {'source': 'ml_guide.pdf'}
        },
        {
            'content': 'Prompt engineering is the practice of designing effective prompts for AI models.',
            'score': 0.88,
            'metadata': {'source': 'prompt_guide.pdf'}
        }
    ]
    
    total_times = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"🧪 Test {i}: '{query}'")
        
        start_time = time.time()
        try:
            response, from_cache = await generate_answer(query, dummy_context)
            end_time = time.time()
            
            query_time = end_time - start_time
            total_times.append(query_time)
            
            print(f"   ⏱️  Time: {query_time:.2f}s (cached: {from_cache})")
            print(f"   📝 Response length: {len(response)} chars")
            print(f"   🎯 First 100 chars: {response[:100]}...")
            
            # Check for duplicate token warnings
            if "duplicate leading" in str(response):
                print("   ❌ Duplicate token warning detected")
            else:
                print("   ✅ No duplicate token warnings")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
        
        print()
    
    # Calculate performance statistics
    if total_times:
        avg_time = sum(total_times) / len(total_times)
        min_time = min(total_times)
        max_time = max(total_times)
        
        print("📊 Performance Summary:")
        print(f"   Average query time: {avg_time:.2f}s")
        print(f"   Fastest query: {min_time:.2f}s")
        print(f"   Slowest query: {max_time:.2f}s")
        
        # Performance assessment
        if avg_time < 5:
            print("   🎉 EXCELLENT: Average response time under 5 seconds!")
        elif avg_time < 10:
            print("   ✅ GOOD: Average response time under 10 seconds")
        elif avg_time < 15:
            print("   ⚠️  OK: Average response time under 15 seconds")
        else:
            print("   ❌ POOR: Average response time over 15 seconds")
    
    # Test model caching
    print("\n🔄 Testing Model Caching:")
    print("   Running same query twice to test caching...")
    
    test_query = "Test caching query"
    
    # First query (should load model)
    start1 = time.time()
    try:
        response1, _ = await generate_answer(test_query, dummy_context[:1])
        time1 = time.time() - start1
        print(f"   First query: {time1:.2f}s")
    except Exception as e:
        print(f"   First query failed: {e}")
        return
    
    # Second query (should use cached model)
    start2 = time.time()
    try:
        response2, _ = await generate_answer(test_query, dummy_context[:1])
        time2 = time.time() - start2
        print(f"   Second query: {time2:.2f}s")
        
        # Check caching effectiveness
        if time2 < time1 * 0.5:  # Second query should be much faster
            print("   🎉 Model caching is working effectively!")
        elif time2 < time1:
            print("   ✅ Model caching shows some improvement")
        else:
            print("   ⚠️  Model caching may not be working properly")
            
    except Exception as e:
        print(f"   Second query failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_performance_improvements())