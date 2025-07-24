#!/usr/bin/env python3
"""
Script to download the Phi-2 model from Hugging Face.
This will download the quantized GGUF version of the model.
"""

import os
import sys
import requests
from tqdm import tqdm

MODEL_URL = "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2-q4_k_m.gguf"
MODEL_PATH = "models/phi-2-instruct-Q4_K_M.gguf"

def download_file(url, filename):
    """
    Download a file with progress bar
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Check if file already exists
    if os.path.exists(filename):
        print(f"File {filename} already exists. Skipping download.")
        return
    
    # Download the file
    print(f"Downloading {url} to {filename}")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    # Show a progress bar during download
    with open(filename, 'wb') as f, tqdm(
        desc=filename,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            bar.update(size)

def main():
    """
    Main function
    """
    print("Downloading Phi-2 model...")
    download_file(MODEL_URL, MODEL_PATH)
    print(f"Model downloaded to {MODEL_PATH}")
    print("You can now run the application with: python main.py")

if __name__ == "__main__":
    main() 