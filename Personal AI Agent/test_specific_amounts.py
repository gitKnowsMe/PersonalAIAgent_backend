#!/usr/bin/env python3
"""
Test script to demonstrate the specific source attribution issue
with numerical amounts vs email search
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_store_service import search_similar_chunks
from app.services.email.email_store import EmailStore
from app.services.embedding_service import SentenceTransformerEmbeddingService

async def test_specific_amounts_attribution():
    """Test the specific case where emails are prioritized but amounts come from documents"""
    
    test_user_id = 10
    
    # Test query specifically asking for amounts that are only in documents
    query = "check emails how much was $8001.00 and $15,180.80?"
    print(f"🔍 Testing problematic query: '{query}' for user {test_user_id}")
    print("=" * 70)
    print("This query should demonstrate the issue:")
    print("- 'check emails' triggers email prioritization")
    print("- But the specific amounts ($8001.00, $15,180.80) are only in bank documents")
    print("- Source attribution will incorrectly show email sources")
    print("=" * 70)
    
    email_store = EmailStore()
    embedding_service = SentenceTransformerEmbeddingService()
    
    # 1. Search emails first
    print("\n📧 EMAIL SEARCH RESULTS:")
    print("-" * 40)
    
    try:
        query_embedding = await embedding_service.generate_embedding(query)
        email_results = await email_store.search_emails(
            query_embedding=query_embedding,
            user_id=test_user_id,
            k=10
        )
        
        print(f"Found {len(email_results)} email results:")
        email_has_amounts = False
        
        for i, result in enumerate(email_results):
            metadata = result.get('metadata', {})
            text = result.get('text', '')
            print(f"\n  Email {i+1}: {metadata.get('subject', 'No Subject')}")
            
            # Check specifically for the target amounts
            target_amounts = ["$8001.00", "$15,180.80", "8001.00", "15,180.80", "15180.80"]
            found_amounts = [amount for amount in target_amounts if amount in text]
            if found_amounts:
                print(f"    🎯 CONTAINS TARGET AMOUNTS: {found_amounts}")
                email_has_amounts = True
            else:
                print(f"    ❌ No target amounts ($8001.00, $15,180.80)")
        
        if not email_has_amounts:
            print(f"\n💡 KEY FINDING: No emails contain the specific amounts!")
    
    except Exception as e:
        print(f"Error searching emails: {e}")
    
    # 2. Search documents
    print("\n📄 DOCUMENT SEARCH RESULTS:")
    print("-" * 40)
    
    try:
        document_results = await search_similar_chunks(
            query=query,
            user_id=test_user_id,
            top_k=10
        )
        
        print(f"Found {len(document_results)} document results:")
        document_has_amounts = False
        
        for i, result in enumerate(document_results):
            text = result.get('content', '')
            metadata = result.get('metadata', {})
            namespace = result.get('namespace', '')
            
            # Check specifically for the target amounts
            target_amounts = ["$8001.00", "$15,180.80", "8001.00", "15,180.80", "15180.80"]
            found_amounts = [amount for amount in target_amounts if amount in text]
            if found_amounts:
                print(f"\n  Document {i+1}: {namespace}")
                print(f"    🎯 CONTAINS TARGET AMOUNTS: {found_amounts}")
                print(f"    Text: {text[:150]}...")
                document_has_amounts = True
        
        if document_has_amounts:
            print(f"\n💡 KEY FINDING: Documents DO contain the specific amounts!")
    
    except Exception as e:
        print(f"Error searching documents: {e}")
    
    # 3. Simulate the problematic prioritization
    print("\n🔀 PROBLEMATIC PRIORITIZATION SIMULATION:")
    print("-" * 40)
    
    # Email prioritization puts emails first
    print("With 'check emails' prioritization:")
    
    # Format email chunks
    email_chunks = []
    for result in email_results:
        metadata = result.get('metadata', {})
        subject = metadata.get('subject', 'No Subject')
        sender = metadata.get('sender', 'Unknown Sender')
        email_content = f"[EMAIL from {sender}] Subject: {subject}\nContent: {result.get('text', '')}"
        
        email_chunk = {
            'text': email_content,
            'score': result.get('score', 0.0),
            'metadata': {
                'content_type': 'email',
                'email_id': metadata.get('email_id', ''),
                'subject': subject,
                'sender': sender,
            },
            'namespace': f"user_{test_user_id}_email_{metadata.get('email_id', '')}"
        }
        email_chunks.append(email_chunk)
    
    # Format document chunks
    document_chunks = []
    for result in document_results:
        document_chunk = {
            'text': result.get('content', ''),
            'score': result.get('score', 0.0),
            'metadata': result.get('metadata', {}),
            'namespace': result.get('namespace', '')
        }
        document_chunks.append(document_chunk)
    
    # Email prioritization: emails first, then limited documents
    chunks = email_chunks + document_chunks[:5]
    print(f"Combined: {len(email_chunks)} email chunks + {len(document_chunks[:5])} document chunks = {len(chunks)} total")
    
    # 4. Source Attribution Analysis
    print("\n🏷️ SOURCE ATTRIBUTION (First 5 chunks only):")
    print("-" * 40)
    
    sources = []
    seen_sources = set()
    chunks_for_attribution = chunks[:5]  # Only first 5 chunks used for attribution
    
    chunks_with_target_amounts = []
    
    for i, chunk in enumerate(chunks_for_attribution):
        meta = chunk.get('metadata', {})
        ns = chunk.get('namespace', '')
        text = chunk.get('text', '')
        
        # Check for target amounts
        target_amounts = ["$8001.00", "$15,180.80", "8001.00", "15,180.80", "15180.80"]
        found_amounts = [amount for amount in target_amounts if amount in text]
        
        print(f"\n  Chunk {i+1} ({meta.get('content_type', 'document')}):")
        if found_amounts:
            print(f"    🎯 HAS TARGET AMOUNTS: {found_amounts}")
            chunks_with_target_amounts.append(i)
        else:
            print(f"    ❌ No target amounts")
        
        # Add to sources
        if meta.get('content_type') == 'email':
            src_id = meta.get('email_id')
            label = meta.get('subject') or f"Email {src_id}"
            key = f"email:{src_id}"
            if key not in seen_sources:
                sources.append({
                    'type': 'email',
                    'id': src_id,
                    'label': label
                })
                seen_sources.add(key)
        else:
            src_id = meta.get('document_id') or ns
            label = meta.get('title') or meta.get('filename') or ns or f"Document {src_id}"
            key = f"document:{src_id}"
            if key not in seen_sources:
                sources.append({
                    'type': 'document',
                    'id': src_id,
                    'label': label
                })
                seen_sources.add(key)
    
    print(f"\n📋 FINAL SOURCE ATTRIBUTION:")
    for i, source in enumerate(sources):
        print(f"  {i+1}. {source['type'].upper()}: {source['label']}")
    
    # 5. Check chunks beyond first 5
    print(f"\n🔍 CHUNKS BEYOND FIRST 5 (not used for attribution):")
    print("-" * 40)
    
    chunks_beyond_5_with_amounts = []
    for i in range(5, min(15, len(chunks))):
        chunk = chunks[i]
        text = chunk.get('text', '')
        meta = chunk.get('metadata', {})
        
        target_amounts = ["$8001.00", "$15,180.80", "8001.00", "15,180.80", "15180.80"]
        found_amounts = [amount for amount in target_amounts if amount in text]
        
        if found_amounts:
            chunks_beyond_5_with_amounts.append((i, chunk, found_amounts))
            print(f"  Chunk {i+1}: {meta.get('content_type', 'document')} - HAS TARGET AMOUNTS: {found_amounts}")
    
    # 6. Final diagnosis
    print(f"\n🚨 ISSUE DIAGNOSIS:")
    print("-" * 40)
    
    attribution_has_amounts = len(chunks_with_target_amounts) > 0
    later_chunks_have_amounts = len(chunks_beyond_5_with_amounts) > 0
    
    if not attribution_has_amounts and later_chunks_have_amounts:
        print("🔴 ISSUE CONFIRMED!")
        print("  ❌ First 5 chunks (used for attribution) don't contain target amounts")
        print("  ✅ Later chunks (not used for attribution) DO contain target amounts")
        print("  📧 Source attribution will show email sources")
        print("  📄 But actual answer comes from document sources")
        print("\n💡 SOLUTION NEEDED:")
        print("  - Source attribution should be based on chunks that actually contain the answer")
        print("  - Not just the first 5 chunks after prioritization")
    elif attribution_has_amounts:
        print("✅ NO ISSUE in this case")
        print("  ✅ First 5 chunks DO contain the target amounts")
        print("  📧 Email source attribution is correct")
    else:
        print("⚠️  NO AMOUNTS FOUND")
        print("  ❌ No chunks contain the target amounts")
        print("  🔍 This indicates a search quality issue")

if __name__ == "__main__":
    asyncio.run(test_specific_amounts_attribution())