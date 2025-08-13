#!/usr/bin/env python3
"""
Debug script to analyze source attribution issue for Apple invoice query with real data
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.vector_store_service import search_similar_chunks
from app.services.email.email_store import EmailStore
from app.services.embedding_service import SentenceTransformerEmbeddingService
from app.db.models import User, Document, Email

async def debug_apple_source_attribution():
    """Debug the Apple invoice source attribution issue with real data"""
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Check what users have documents and emails
        print("📊 USER DATA ANALYSIS:")
        print("-" * 40)
        
        users = db.query(User).all()
        for user in users:
            doc_count = db.query(Document).filter(Document.owner_id == user.id).count()
            email_count = db.query(Email).filter(Email.user_id == user.id).count()
            print(f"User {user.id} ({user.username}): {doc_count} documents, {email_count} emails")
        
        # Find a user with documents for testing
        user_with_docs = db.query(User).join(Document).first()
        if not user_with_docs:
            print("❌ No users with documents found")
            return
        
        test_user_id = user_with_docs.id
        print(f"\n🧪 Testing with user {test_user_id} ({user_with_docs.username})")
        
        # Check their documents
        documents = db.query(Document).filter(Document.owner_id == test_user_id).all()
        print(f"\nDocuments for user {test_user_id}:")
        for doc in documents:
            print(f"  - {doc.title} (ID: {doc.id}, Namespace: {doc.vector_namespace})")
        
        # Test query
        query = "check emails how much was the Apple invoice?"
        print(f"\n🔍 Debugging query: '{query}' for user {test_user_id}")
        print("=" * 60)
        
        # 2. Check email search results
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
                user_id=test_user_id,
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
                apple_amounts = ["$8001.00", "$15,180.80", "$180.80", "8001", "15180", "180.80", "apple", "Apple"]
                found_amounts = [amount for amount in apple_amounts if amount.lower() in text.lower()]
                if found_amounts:
                    print(f"    🔍 CONTAINS APPLE/AMOUNTS: {found_amounts}")
                else:
                    print(f"    ❌ No Apple/target amounts found")
        
        except Exception as e:
            print(f"Error searching emails: {e}")
        
        # 3. Check document search results
        print("\n📄 DOCUMENT SEARCH RESULTS:")
        print("-" * 40)
        
        try:
            # Search documents
            document_results = await search_similar_chunks(
                query=query,
                user_id=test_user_id,
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
                apple_amounts = ["$8001.00", "$15,180.80", "$180.80", "8001", "15180", "180.80", "apple", "Apple"]
                found_amounts = [amount for amount in apple_amounts if amount.lower() in text.lower()]
                if found_amounts:
                    print(f"    🔍 CONTAINS APPLE/AMOUNTS: {found_amounts}")
                else:
                    print(f"    ❌ No Apple/target amounts found")
        
        except Exception as e:
            print(f"Error searching documents: {e}")
        
        # 4. Test different queries to find Apple-related content
        print("\n🔍 TESTING DIFFERENT QUERIES:")
        print("-" * 40)
        
        test_queries = [
            "Apple",
            "invoice",
            "receipt",
            "8001",
            "15180",
            "180.80",
            "payment",
            "transaction"
        ]
        
        for test_query in test_queries:
            print(f"\n  Testing query: '{test_query}'")
            try:
                doc_results = await search_similar_chunks(
                    query=test_query,
                    user_id=test_user_id,
                    top_k=3
                )
                
                if doc_results:
                    for i, result in enumerate(doc_results):
                        text = result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
                        print(f"    Doc {i+1}: {text} (Score: {result.get('score', 0.0):.3f})")
                else:
                    print(f"    No results for '{test_query}'")
            except Exception as e:
                print(f"    Error searching '{test_query}': {e}")
        
        # 5. Check if we can find bank statement data
        print("\n🏦 BANK STATEMENT ANALYSIS:")
        print("-" * 40)
        
        bank_queries = [
            "bank statement",
            "transaction",
            "debit",
            "credit",
            "balance"
        ]
        
        for bank_query in bank_queries:
            print(f"\n  Bank query: '{bank_query}'")
            try:
                doc_results = await search_similar_chunks(
                    query=bank_query,
                    user_id=test_user_id,
                    top_k=3
                )
                
                if doc_results:
                    for i, result in enumerate(doc_results):
                        text = result.get('content', '')[:150] + "..." if len(result.get('content', '')) > 150 else result.get('content', '')
                        print(f"    Doc {i+1}: {text} (Score: {result.get('score', 0.0):.3f})")
                        
                        # Check for Apple or specific amounts
                        apple_amounts = ["apple", "Apple", "8001", "15180", "180.80"]
                        found_amounts = [amount for amount in apple_amounts if amount.lower() in text.lower()]
                        if found_amounts:
                            print(f"    🔍 CONTAINS: {found_amounts}")
                else:
                    print(f"    No results for '{bank_query}'")
            except Exception as e:
                print(f"    Error searching '{bank_query}': {e}")
        
        # 6. Check vector store directories
        print("\n📁 VECTOR STORE DIRECTORY ANALYSIS:")
        print("-" * 40)
        
        vector_db_path = settings.VECTOR_DB_PATH
        print(f"Vector DB path: {vector_db_path}")
        
        if os.path.exists(vector_db_path):
            print("Root directory files:")
            for file in os.listdir(vector_db_path):
                if file.endswith('.index') or file.endswith('.pkl'):
                    print(f"  - {file}")
            
            # Check category subdirectories
            categories = ['financial', 'long_form', 'generic']
            for category in categories:
                category_path = os.path.join(vector_db_path, category)
                if os.path.exists(category_path):
                    print(f"\n{category}/ directory files:")
                    for file in os.listdir(category_path):
                        if file.endswith('.index') or file.endswith('.pkl'):
                            print(f"  - {file}")
        else:
            print("Vector DB directory doesn't exist")
        
        # 7. Check email vector store
        print("\n📧 EMAIL VECTOR STORE ANALYSIS:")
        print("-" * 40)
        
        email_path = os.path.join(vector_db_path, "emails")
        if os.path.exists(email_path):
            print(f"Email vector store path: {email_path}")
            email_files = os.listdir(email_path)
            print(f"Email vector files: {len(email_files)}")
            for file in email_files[:10]:  # Show first 10 files
                print(f"  - {file}")
        else:
            print("No email vector store found")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_apple_source_attribution())