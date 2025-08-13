#!/usr/bin/env python3
"""
Direct test of the source attribution fix without API calls
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_store_service import search_similar_chunks
from app.services.email.email_store import EmailStore
from app.services.embedding_service import SentenceTransformerEmbeddingService

async def test_source_attribution_directly():
    """Test the fixed source attribution logic directly"""
    
    print("🧪 Testing Source Attribution Fix Directly")
    print("=" * 50)
    
    # Use user 10 who has both emails and documents
    test_user_id = 10
    
    # Test the problematic query
    query = "check emails how much was $8001.00 and $15,180.80?"
    print(f"🔍 Testing query: '{query}' for user {test_user_id}")
    print("=" * 50)
    
    email_store = EmailStore()
    embedding_service = SentenceTransformerEmbeddingService()
    
    # Simulate the exact logic from queries.py
    print("\n1️⃣ SEARCHING EMAILS (prioritized):")
    print("-" * 40)
    
    try:
        query_embedding = await embedding_service.generate_embedding(query)
        email_results = await email_store.search_emails(
            query_embedding=query_embedding,
            user_id=test_user_id,
            k=10
        )
        
        print(f"Found {len(email_results)} email results")
        
        # Format email chunks (exactly as in queries.py)
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
                    'sender_email': metadata.get('sender', ''),
                    'date': metadata.get('date', ''),
                    'classification_tags': metadata.get('classification_tags', [])
                },
                'namespace': f"user_{test_user_id}_email_{metadata.get('email_id', '')}"
            }
            email_chunks.append(email_chunk)
    
    except Exception as e:
        print(f"Error searching emails: {e}")
        email_chunks = []
    
    print("\n2️⃣ SEARCHING DOCUMENTS:")
    print("-" * 40)
    
    try:
        document_results = await search_similar_chunks(
            query=query,
            user_id=test_user_id,
            top_k=10
        )
        
        print(f"Found {len(document_results)} document results")
        
        # Convert to chunks format
        document_chunks = []
        for result in document_results:
            document_chunk = {
                'text': result.get('content', ''),
                'score': result.get('score', 0.0),
                'metadata': result.get('metadata', {}),
                'namespace': result.get('namespace', '')
            }
            document_chunks.append(document_chunk)
    
    except Exception as e:
        print(f"Error searching documents: {e}")
        document_chunks = []
    
    print("\n3️⃣ COMBINING WITH EMAIL PRIORITIZATION:")
    print("-" * 40)
    
    # Email prioritization: emails first, then limited documents
    chunks = email_chunks + document_chunks[:5]
    print(f"Combined: {len(email_chunks)} email chunks + {len(document_chunks[:5])} document chunks = {len(chunks)} total")
    
    print("\n4️⃣ TESTING NEW SOURCE ATTRIBUTION LOGIC:")
    print("-" * 40)
    
    # Simulate the new source attribution logic from the fix
    import re
    
    def extract_key_terms_from_query(query_text):
        """Extract important terms from the query for relevance matching"""
        # Extract monetary amounts, numbers, and important keywords
        monetary_amounts = re.findall(r'\$[\d,]+\.?\d*', query_text.lower())
        numbers = re.findall(r'\b\d{3,}\b', query_text.lower())  # 3+ digit numbers
        # Extract merchant names and important terms (basic)
        important_words = []
        words = query_text.lower().split()
        for word in words:
            if len(word) > 3 and word not in ['check', 'emails', 'much', 'what', 'how', 'was', 'the', 'and']:
                important_words.append(word)
        return monetary_amounts + numbers + important_words
    
    def chunk_relevance_score(chunk, key_terms):
        """Calculate how relevant a chunk is based on key terms"""
        text = chunk.get('text', '').lower()
        score = 0
        for term in key_terms:
            if term in text:
                score += 1
        return score
    
    # Extract key terms from the query
    key_terms = extract_key_terms_from_query(query)
    print(f"Extracted key terms: {key_terms}")
    
    # Calculate relevance for all chunks
    chunk_relevance = []
    for i, chunk in enumerate(chunks):
        if isinstance(chunk, dict):
            relevance = chunk_relevance_score(chunk, key_terms)
            chunk_relevance.append((i, chunk, relevance))
            
            # Show chunk details
            meta = chunk.get('metadata', {})
            content_type = meta.get('content_type', 'document')
            text_preview = chunk.get('text', '')[:100] + "..." if len(chunk.get('text', '')) > 100 else chunk.get('text', '')
            print(f"  Chunk {i+1} ({content_type}): relevance={relevance}")
            print(f"    Preview: {text_preview}")
    
    # Sort by relevance (descending) but preserve original order for ties
    chunk_relevance.sort(key=lambda x: (-x[2], x[0]))
    
    print(f"\n📊 RELEVANCE RANKING:")
    for i, (original_idx, chunk, relevance) in enumerate(chunk_relevance[:5]):
        meta = chunk.get('metadata', {})
        content_type = meta.get('content_type', 'document')
        print(f"  Rank {i+1}: Chunk {original_idx+1} ({content_type}) - relevance={relevance}")
    
    # Apply the new logic
    relevant_chunks = [item for item in chunk_relevance if item[2] > 0][:3]
    top_chunks = chunks[:2] if len(chunks) >= 2 else chunks[:1]
    
    # Combine relevant chunks and top chunks for attribution
    attribution_chunk_indices = set()
    for _, chunk, _ in relevant_chunks:
        attribution_chunk_indices.add(chunks.index(chunk))
    for i, chunk in enumerate(top_chunks):
        attribution_chunk_indices.add(i)
    
    chunks_for_attribution = [chunks[i] for i in sorted(attribution_chunk_indices)]
    
    print(f"\n🏷️ SOURCE ATTRIBUTION DECISION:")
    print(f"Relevant chunks with score > 0: {len(relevant_chunks)}")
    print(f"Top chunks for context: {len(top_chunks)}")
    print(f"Attribution chunk indices: {sorted(attribution_chunk_indices)}")
    print(f"Total chunks for attribution: {len(chunks_for_attribution)}")
    
    # Generate sources
    sources = []
    seen_sources = set()
    
    print(f"\n📋 FINAL SOURCES:")
    for i, chunk in enumerate(chunks_for_attribution):
        if isinstance(chunk, dict):
            meta = chunk.get('metadata', {})
            ns = chunk.get('namespace', '')
            
            # Check what this chunk contains
            text = chunk.get('text', '').lower()
            target_amounts = ["$8001.00", "$15,180.80", "8001.00", "15,180.80", "15180.80"]
            found_amounts = [amount for amount in target_amounts if amount in text]
            
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
                    print(f"  📧 EMAIL: {label}")
                    if found_amounts:
                        print(f"     🎯 Contains amounts: {found_amounts}")
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
                    print(f"  📄 DOCUMENT: {label}")
                    if found_amounts:
                        print(f"     🎯 Contains amounts: {found_amounts}")
    
    print(f"\n🏁 SUMMARY:")
    print(f"Query: {query}")
    print(f"Sources attributed: {len(sources)}")
    
    # Check if fix is working
    has_email_sources = any(s['type'] == 'email' for s in sources)
    has_document_sources = any(s['type'] == 'document' for s in sources)
    
    # Find chunks with target amounts
    amount_chunks = []
    for i, chunk in enumerate(chunks):
        text = chunk.get('text', '').lower()
        target_amounts = ["$8001.00", "$15,180.80", "8001.00", "15,180.80", "15180.80"]
        found_amounts = [amount for amount in target_amounts if amount in text]
        if found_amounts:
            meta = chunk.get('metadata', {})
            content_type = meta.get('content_type', 'document')
            amount_chunks.append((i, content_type, found_amounts))
    
    if amount_chunks:
        print(f"\nChunks containing target amounts:")
        for i, content_type, amounts in amount_chunks:
            print(f"  Chunk {i+1} ({content_type}): {amounts}")
        
        # Check if source attribution includes sources that actually have the amounts
        amount_source_types = set()
        for i, content_type, amounts in amount_chunks:
            if i in attribution_chunk_indices:
                amount_source_types.add(content_type)
        
        if amount_source_types:
            print(f"\n✅ Fix is working! Source attribution includes: {amount_source_types}")
        else:
            print(f"\n❌ Issue persists: Amount chunks not in attribution set")
    else:
        print(f"\n⚠️  No chunks contain the target amounts")

if __name__ == "__main__":
    asyncio.run(test_source_attribution_directly())