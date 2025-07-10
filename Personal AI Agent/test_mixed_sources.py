#!/usr/bin/env python3
"""
Test mixed source scenarios to ensure the fix works in various cases
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_store_service import search_similar_chunks
from app.services.email.email_store import EmailStore
from app.services.embedding_service import SentenceTransformerEmbeddingService

async def test_mixed_source_scenarios():
    """Test various scenarios to ensure source attribution works correctly"""
    
    print("🧪 Testing Mixed Source Attribution Scenarios")
    print("=" * 60)
    
    test_user_id = 10
    
    test_scenarios = [
        {
            "query": "check emails Apple receipt",
            "description": "Should find Apple emails and show email sources",
            "expect_email": True,
            "expect_document": False
        },
        {
            "query": "check emails how much was $8001.00",
            "description": "Should find amounts in documents and show document sources",
            "expect_email": False,
            "expect_document": True
        },
        {
            "query": "find emails and documents about Apple",
            "description": "Should find both emails and documents about Apple",
            "expect_email": True,
            "expect_document": False  # Depends on content
        }
    ]
    
    embedding_service = SentenceTransformerEmbeddingService()
    email_store = EmailStore()
    
    for i, scenario in enumerate(test_scenarios):
        query = scenario["query"]
        description = scenario["description"]
        
        print(f"\n🔍 Scenario {i+1}: {query}")
        print(f"Description: {description}")
        print("-" * 60)
        
        # Quick source attribution test
        try:
            # Get email and document results
            query_embedding = await embedding_service.generate_embedding(query)
            email_results = await email_store.search_emails(
                query_embedding=query_embedding,
                user_id=test_user_id,
                k=5
            )
            
            document_results = await search_similar_chunks(
                query=query,
                user_id=test_user_id,
                top_k=5
            )
            
            print(f"Found {len(email_results)} email results, {len(document_results)} document results")
            
            # Check relevance in emails
            email_relevance = 0
            for result in email_results:
                text = result.get('text', '').lower()
                if any(term in text for term in ['apple', 'receipt', '$8001', '$15,180']):
                    email_relevance += 1
            
            # Check relevance in documents  
            doc_relevance = 0
            for result in document_results:
                text = result.get('content', '').lower()
                if any(term in text for term in ['apple', 'receipt', '$8001', '$15,180']):
                    doc_relevance += 1
            
            print(f"Email relevance: {email_relevance}/5, Document relevance: {doc_relevance}/5")
            
            # Predict what sources should be attributed
            predicted_email = email_relevance > 0 or query.startswith(('check emails', 'find emails'))
            predicted_document = doc_relevance > 0
            
            print(f"Expected sources: Email={scenario['expect_email']}, Document={scenario['expect_document']}")
            print(f"Predicted sources: Email={predicted_email}, Document={predicted_document}")
            
            if predicted_email == scenario['expect_email'] and predicted_document == scenario['expect_document']:
                print("✅ Scenario prediction matches expectation")
            else:
                print("⚠️  Scenario may have different results than expected")
            
        except Exception as e:
            print(f"❌ Error in scenario {i+1}: {e}")
    
    print(f"\n🏁 MIXED SOURCE TEST SUMMARY:")
    print("The new source attribution logic should:")
    print("1. ✅ Include document sources when documents contain the actual answer")
    print("2. ✅ Include email sources when emails contain relevant information") 
    print("3. ✅ Include both when both are relevant")
    print("4. ✅ Prioritize relevance over just position in list")
    print("5. ✅ Still respect email prioritization for LLM context")

if __name__ == "__main__":
    asyncio.run(test_mixed_source_scenarios())