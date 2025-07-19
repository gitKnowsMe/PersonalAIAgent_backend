#!/usr/bin/env python3
"""
Manual cleanup of frontend files for hybrid deployment
"""

import os
import shutil
from pathlib import Path

def cleanup():
    """Remove frontend files"""
    
    # Files to remove
    files_to_remove = [
        'static/css',
        'static/js',
        'static/index.html',
        'static/error.html', 
        'static/favicon.ico',
        'test_login_debug.html'
    ]
    
    for file_path in files_to_remove:
        path = Path(file_path)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {path}")
            else:
                path.unlink()
                print(f"Removed file: {path}")
        else:
            print(f"File not found: {path}")
    
    # Keep only uploads and emails in static temporarily
    # (They'll be moved to data/ by the config changes)
    
    print("Frontend files cleanup completed!")

if __name__ == "__main__":
    cleanup()