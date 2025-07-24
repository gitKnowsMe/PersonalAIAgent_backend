#!/usr/bin/env python3
"""
Script to download the sentence-transformers embedding model.
This will download the all-MiniLM-L6-v2 model for text embeddings.
"""

import os
import sys
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_PATH = "models/all-MiniLM-L6-v2"

def download_embedding_model():
    """
    Download the sentence-transformers embedding model
    """
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    # Check if model already exists
    if os.path.exists(MODEL_PATH):
        print(f"Model {MODEL_PATH} already exists. Skipping download.")
        return
    
    print(f"Downloading embedding model: {MODEL_NAME}")
    print("This may take a few minutes...")
    
    try:
        # Download the model
        model = SentenceTransformer(MODEL_NAME)
        
        # Save the model locally
        model.save(MODEL_PATH)
        
        print(f"Embedding model downloaded successfully to {MODEL_PATH}")
        
        # Test the model
        print("Testing the model...")
        test_texts = ["Hello world", "This is a test"]
        embeddings = model.encode(test_texts)
        print(f"Model test successful! Generated embeddings of shape: {embeddings.shape}")
        
    except Exception as e:
        print(f"Error downloading embedding model: {e}")
        sys.exit(1)

def main():
    """
    Main function
    """
    print("Downloading sentence-transformers embedding model...")
    download_embedding_model()
    print("You can now run the application with: python main.py")

if __name__ == "__main__":
    main() 