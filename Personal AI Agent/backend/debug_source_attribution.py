#!/usr/bin/env python3
"""
Debug script to analyze source attribution issue for Apple invoice query
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_store_service import search_similar_chunks
from app.services.email.email_store import EmailStore
from app.services.embedding_service import SentenceTransformerEmbeddingService

async def debug_apple_source_attribution():
    """Debug the Apple invoice source attribution issue"""
    
    # Test query
    query = "check emails how much was the Apple invoice?"
    user_id = 1  # Assuming user ID 1
    
    print(f"🔍 Debugging query: '{query}' for user {user_id}")
    print("=" * 60)
    
    # 1. Check email search results
    print("\n📧 EMAIL SEARCH RESULTS:")
    print("-" * 40)
    
    email_store = EmailStore()
    embedding_service = SentenceTransformerEmbeddingService()
    
    try:
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(query)
        
        # Search emails
        email_results = await email_store.search_emails(
            query_embedding=query_embedding,
            user_id=user_id,
            k=10
        )
        
        print(f"Found {len(email_results)} email results:")
        for i, result in enumerate(email_results):
            metadata = result.get('metadata', {})
            text = result.get('text', '')[:200] + "..." if len(result.get('text', '')) > 200 else result.get('text', '')
            print(f"\n  Email {i+1}:")
            print(f"    Subject: {metadata.get('subject', 'No Subject')}")
            print(f"    Sender: {metadata.get('sender', 'Unknown')}")
            print(f"    Score: {result.get('score', 0.0):.3f}")
            print(f"    Email ID: {metadata.get('email_id', 'N/A')}")
            print(f"    Text: {text}")
            
            # Check for Apple amounts
            apple_amounts = ["$8001.00", "$15,180.80", "$180.80", "8001", "15180", "180.80"]
            found_amounts = [amount for amount in apple_amounts if amount in text]
            if found_amounts:
                print(f"    🔍 CONTAINS AMOUNTS: {found_amounts}")
            else:
                print(f"    ❌ No target amounts found")
    
    except Exception as e:
        print(f"Error searching emails: {e}")
    
    # 2. Check document search results
    print("\n📄 DOCUMENT SEARCH RESULTS:")
    print("-" * 40)
    
    try:
        # Search documents
        document_results = await search_similar_chunks(
            query=query,
            user_id=user_id,
            top_k=10
        )
        
        print(f"Found {len(document_results)} document results:")
        for i, result in enumerate(document_results):
            metadata = result.get('metadata', {})
            text = result.get('content', '')[:200] + "..." if len(result.get('content', '')) > 200 else result.get('content', '')
            print(f"\n  Document {i+1}:")
            print(f"    Title: {metadata.get('title', metadata.get('filename', 'Unknown'))}")
            print(f"    Namespace: {result.get('namespace', 'N/A')}")
            print(f"    Score: {result.get('score', 0.0):.3f}")
            print(f"    Text: {text}")
            
            # Check for Apple amounts
            apple_amounts = ["$8001.00", "$15,180.80", "$180.80", "8001", "15180", "180.80"]
            found_amounts = [amount for amount in apple_amounts if amount in text]
            if found_amounts:
                print(f"    🔍 CONTAINS AMOUNTS: {found_amounts}")
            else:
                print(f"    ❌ No target amounts found")
    
    except Exception as e:
        print(f"Error searching documents: {e}")
    
    # 3. Simulate the combined search logic from queries.py
    print("\n🔀 COMBINED SEARCH SIMULATION:")
    print("-" * 40)
    
    # Check if query starts with "check emails" for email prioritization
    query_lower = query.lower().strip()
    prioritize_emails = query_lower.startswith("check emails")
    print(f"Prioritize emails: {prioritize_emails}")
    
    # Simulate email search for formatting
    email_chunks = []
    try:
        for result in email_results:
            metadata = result.get('metadata', {})
            subject = metadata.get('subject', 'No Subject')
            sender = metadata.get('sender', 'Unknown Sender')
            email_content = f"[EMAIL from {sender}] Subject: {subject}\nContent: {result.get('text', '')}"
            
            # Create chunk dictionary with proper format for LLM
            email_chunk = {
                'text': email_content,
                'score': result.get('score', 0.0),
                'metadata': {
                    'content_type': 'email',
                    'email_id': metadata.get('email_id', ''),
                    'subject': subject,
                    'sender': sender,
                    'sender_email': metadata.get('sender', ''),
                    'date': metadata.get('date', ''),
                    'classification_tags': metadata.get('classification_tags', [])
                },
                'namespace': f"user_{user_id}_email_{metadata.get('email_id', '')}"
            }
            email_chunks.append(email_chunk)
    except Exception as e:
        print(f"Error formatting email chunks: {e}")
    
    # Convert document results to chunks format
    document_chunks = []
    for result in document_results:
        document_chunk = {
            'text': result.get('content', ''),
            'score': result.get('score', 0.0),
            'metadata': result.get('metadata', {}),
            'namespace': result.get('namespace', '')
        }
        document_chunks.append(document_chunk)
    
    # Combine chunks with prioritization
    if prioritize_emails:
        # When prioritizing emails, put email chunks first and limit documents
        chunks = email_chunks + document_chunks[:5]  # Limit documents when emails are prioritized
        print(f"Email-prioritized search: {len(email_chunks)} email chunks + {len(document_chunks[:5])} document chunks = {len(chunks)} total")
    else:
        # Normal combination
        chunks = document_chunks + email_chunks
        print(f"Combined search: {len(document_chunks)} document chunks + {len(email_chunks)} email chunks = {len(chunks)} total")
    
    # 4. Analyze source attribution logic
    print("\n🏷️ SOURCE ATTRIBUTION ANALYSIS:")
    print("-" * 40)
    
    sources = []
    seen_sources = set()
    # Use the actual chunks that will be sent to LLM for attribution
    # This ensures source attribution matches the content that generated the answer
    chunks_for_attribution = chunks[:5]
    
    print(f"Analyzing first 5 chunks for source attribution:")
    
    for i, chunk in enumerate(chunks_for_attribution):
        print(f"\n  Chunk {i+1}:")
        if isinstance(chunk, dict):
            meta = chunk.get('metadata', {})
            ns = chunk.get('namespace', '')
            text = chunk.get('text', '')[:100] + "..." if len(chunk.get('text', '')) > 100 else chunk.get('text', '')
            
            print(f"    Content: {text}")
            print(f"    Namespace: {ns}")
            print(f"    Content Type: {meta.get('content_type', 'unknown')}")
            
            # Check for Apple amounts
            apple_amounts = ["$8001.00", "$15,180.80", "$180.80", "8001", "15180", "180.80"]
            found_amounts = [amount for amount in apple_amounts if amount in text]
            if found_amounts:
                print(f"    🔍 CONTAINS AMOUNTS: {found_amounts}")
            else:
                print(f"    ❌ No target amounts found")
            
            # Email source
            if meta.get('content_type') == 'email':
                src_id = meta.get('email_id')
                label = meta.get('subject') or meta.get('sender_email') or f"Email {src_id}"
                key = f"email:{src_id}"
                if key not in seen_sources:
                    sources.append({
                        'type': 'email',
                        'id': src_id,
                        'label': label
                    })
                    seen_sources.add(key)
                    print(f"    📧 EMAIL SOURCE: {label}")
            # Document source
            else:
                src_id = meta.get('document_id') or meta.get('doc_id') or ns
                label = meta.get('title') or meta.get('filename') or ns or f"Document {src_id}"
                key = f"document:{src_id}"
                if key not in seen_sources:
                    sources.append({
                        'type': 'document',
                        'id': src_id,
                        'label': label
                    })
                    seen_sources.add(key)
                    print(f"    📄 DOCUMENT SOURCE: {label}")
    
    print(f"\n📋 FINAL SOURCE ATTRIBUTION:")
    for i, source in enumerate(sources):
        print(f"  {i+1}. {source['type'].upper()}: {source['label']} (ID: {source['id']})")
    
    # 5. Find chunks that actually contain the amounts
    print("\n🎯 CHUNKS CONTAINING TARGET AMOUNTS:")
    print("-" * 40)
    
    apple_amounts = ["$8001.00", "$15,180.80", "$180.80", "8001", "15180", "180.80"]
    
    chunks_with_amounts = []
    for i, chunk in enumerate(chunks):
        text = chunk.get('text', '')
        found_amounts = [amount for amount in apple_amounts if amount in text]
        if found_amounts:
            chunks_with_amounts.append((i, chunk, found_amounts))
    
    if chunks_with_amounts:
        print(f"Found {len(chunks_with_amounts)} chunks with target amounts:")
        for i, (chunk_idx, chunk, amounts) in enumerate(chunks_with_amounts):
            meta = chunk.get('metadata', {})
            ns = chunk.get('namespace', '')
            print(f"\n  Chunk {chunk_idx+1} (position {chunk_idx+1} in final list):")
            print(f"    Amounts found: {amounts}")
            print(f"    Content type: {meta.get('content_type', 'unknown')}")
            print(f"    Namespace: {ns}")
            
            if meta.get('content_type') == 'email':
                print(f"    📧 EMAIL: {meta.get('subject', 'No Subject')}")
            else:
                print(f"    📄 DOCUMENT: {meta.get('title', meta.get('filename', 'Unknown'))}")
    else:
        print("❌ No chunks contain the target amounts!")
    
    # 6. Summary and recommendations
    print("\n📝 SUMMARY & RECOMMENDATIONS:")
    print("-" * 40)
    
    if chunks_with_amounts:
        amount_chunk_positions = [pos for pos, _, _ in chunks_with_amounts]
        attribution_positions = list(range(5))  # First 5 chunks used for attribution
        
        print(f"Chunks with amounts at positions: {amount_chunk_positions}")
        print(f"Chunks used for attribution: {attribution_positions}")
        
        # Check if amounts are in attribution chunks
        amounts_in_attribution = any(pos in attribution_positions for pos in amount_chunk_positions)
        
        if amounts_in_attribution:
            print("✅ Amounts are found in attribution chunks")
            
            # Check if email sources are being attributed incorrectly
            email_sources_in_attribution = []
            document_sources_in_attribution = []
            
            for i in range(min(5, len(chunks))):
                chunk = chunks[i]
                meta = chunk.get('metadata', {})
                if meta.get('content_type') == 'email':
                    email_sources_in_attribution.append(i)
                else:
                    document_sources_in_attribution.append(i)
            
            amount_sources = []
            for pos, chunk, amounts in chunks_with_amounts:
                if pos < 5:  # Only check attribution chunks
                    meta = chunk.get('metadata', {})
                    if meta.get('content_type') == 'email':
                        amount_sources.append('email')
                    else:
                        amount_sources.append('document')
            
            print(f"Email sources in attribution: positions {email_sources_in_attribution}")
            print(f"Document sources in attribution: positions {document_sources_in_attribution}")
            print(f"Amount sources: {amount_sources}")
            
            if 'document' in amount_sources and email_sources_in_attribution:
                print("⚠️  ISSUE IDENTIFIED: Email sources are being attributed even though amounts come from documents")
                print("    This is due to email prioritization putting email chunks first in the list")
                print("    even when they don't contain the relevant information.")
        else:
            print("❌ Amounts are NOT found in attribution chunks (positions 0-4)")
            print("    This means source attribution will be incorrect regardless")
    else:
        print("❌ No chunks contain the target amounts - this is a search quality issue")

if __name__ == "__main__":
    asyncio.run(debug_apple_source_attribution())