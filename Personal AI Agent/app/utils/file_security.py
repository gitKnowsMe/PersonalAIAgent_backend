"""
Secure file handling utilities for preventing path traversal and other file-based attacks.
"""

import os
import re
import uuid
import mimetypes
from pathlib import Path
from typing import Tuple, Optional, List

from app.core.constants import SUPPORTED_FILE_EXTENSIONS

# Try to import python-magic, fall back to mimetypes if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to prevent path traversal and other attacks.
    
    Args:
        filename: The original filename
        max_length: Maximum allowed filename length
        
    Returns:
        A sanitized filename safe for filesystem use
    """
    if not filename:
        return "unnamed_file"
    
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    # Keep only alphanumeric, dots, hyphens, underscores, and spaces
    filename = re.sub(r'[^\w\s\-_\.]', '', filename)
    
    # Replace multiple spaces/dots with single ones
    filename = re.sub(r'\.{2,}', '.', filename)  # Remove .. attacks
    filename = re.sub(r'\s+', '_', filename)      # Replace spaces with underscores
    
    # Remove leading/trailing dots and spaces (Windows issues)
    filename = filename.strip('. ')
    
    # Ensure filename is not empty after sanitization
    if not filename:
        filename = "sanitized_file"
    
    # Truncate if too long
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext) - 1
        filename = name[:max_name_length] + ext
    
    # Ensure it doesn't start with dot (hidden files)
    if filename.startswith('.'):
        filename = 'file_' + filename[1:]
    
    return filename


def generate_secure_filename(original_filename: str, user_id: int) -> str:
    """
    Generate a cryptographically secure filename that prevents all path traversal attacks.
    
    Args:
        original_filename: The original filename (used for extension)
        user_id: User ID for namespace isolation
        
    Returns:
        A secure UUID-based filename
    """
    # Extract file extension safely
    _, ext = os.path.splitext(original_filename)
    ext = ext.lower()
    
    # Validate extension is allowed
    if ext not in SUPPORTED_FILE_EXTENSIONS:
        ext = '.txt'  # Default to safe extension
    
    # Generate UUID-based filename
    secure_name = str(uuid.uuid4())
    
    # Add user prefix for additional isolation
    return f"user_{user_id}_{secure_name}{ext}"


def validate_file_type(file_content: bytes, filename: str, allowed_types: List[str] = None) -> Tuple[bool, str]:
    """
    Validate file type by content (magic bytes) not just extension.
    
    Args:
        file_content: The file content bytes
        filename: The filename (for extension check)
        allowed_types: List of allowed MIME types
        
    Returns:
        Tuple of (is_valid, detected_mime_type)
    """
    if allowed_types is None:
        allowed_types = [
            'text/plain',
            'text/csv', 
            'text/markdown',
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
    
    try:
        detected_mime = None
        
        # Use python-magic if available for better detection
        if MAGIC_AVAILABLE:
            try:
                detected_mime = magic.from_buffer(file_content, mime=True)
            except Exception:
                pass  # Fall back to mimetypes
        
        # Also check by filename extension as fallback
        guessed_mime, _ = mimetypes.guess_type(filename)
        
        # If we have magic detection, prefer it
        if detected_mime:
            # For text files, magic might return different subtypes
            if detected_mime.startswith('text/') and any(t.startswith('text/') for t in allowed_types):
                return True, detected_mime
                
            # Check if detected type is in allowed list
            if detected_mime in allowed_types:
                return True, detected_mime
        
        # Check guessed type as fallback
        if guessed_mime in allowed_types:
            return True, guessed_mime
            
        return False, detected_mime or guessed_mime or 'unknown'
        
    except Exception as e:
        # If all detection fails, fall back to extension check only
        guessed_mime, _ = mimetypes.guess_type(filename)
        is_valid = guessed_mime in allowed_types if guessed_mime else False
        return is_valid, guessed_mime or 'unknown'


def validate_file_extension(filename: str) -> bool:
    """
    Validate that file extension is in the allowed list.
    
    Args:
        filename: The filename to check
        
    Returns:
        True if extension is allowed, False otherwise
    """
    _, ext = os.path.splitext(filename.lower())
    return ext in SUPPORTED_FILE_EXTENSIONS


def create_secure_path(base_dir: str, user_id: int, filename: str) -> Tuple[str, str]:
    """
    Create a secure file path that prevents directory traversal.
    
    Args:
        base_dir: Base upload directory
        user_id: User ID for isolation
        filename: Original filename
        
    Returns:
        Tuple of (full_secure_path, relative_path)
    """
    # Sanitize the base directory path
    base_path = Path(base_dir).resolve()
    
    # Create user-specific subdirectory
    user_dir = base_path / str(user_id)
    
    # Generate secure filename
    secure_filename = generate_secure_filename(filename, user_id)
    
    # Create full secure path
    secure_path = user_dir / secure_filename
    
    # Ensure the final path is still within the base directory (security check)
    try:
        secure_path.resolve().relative_to(base_path.resolve())
    except ValueError:
        # If path escapes base directory, create a safe alternative
        safe_filename = f"safe_{uuid.uuid4()}.txt"
        secure_path = user_dir / safe_filename
    
    return str(secure_path), str(secure_path.relative_to(base_path))


def validate_upload_directory(directory: str) -> bool:
    """
    Validate that upload directory is safe and accessible.
    
    Args:
        directory: Directory path to validate
        
    Returns:
        True if directory is safe to use
    """
    try:
        dir_path = Path(directory).resolve()
        
        # Check if directory exists or can be created
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Check if directory is writable
        if not os.access(dir_path, os.W_OK):
            return False
            
        # Check if it's actually a directory
        if not dir_path.is_dir():
            return False
            
        return True
        
    except (OSError, PermissionError):
        return False


def scan_file_for_threats(file_content: bytes, filename: str) -> Tuple[bool, List[str]]:
    """
    Basic threat scanning for uploaded files.
    
    Args:
        file_content: File content to scan
        filename: Filename to check
        
    Returns:
        Tuple of (is_safe, list_of_issues)
    """
    issues = []
    
    # Check for suspicious file extensions
    suspicious_extensions = ['.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs', '.js', '.jar']
    _, ext = os.path.splitext(filename.lower())
    
    if ext in suspicious_extensions:
        issues.append(f"Suspicious file extension: {ext}")
    
    # Check file size (bomb detection)
    if len(file_content) > 100 * 1024 * 1024:  # 100MB
        issues.append("File size suspiciously large")
    
    # Check for embedded executables in text files
    if filename.lower().endswith(('.txt', '.csv', '.md')):
        # Look for executable signatures
        executable_signatures = [b'MZ', b'\x7fELF', b'\xcf\xfa\xed\xfe']
        for sig in executable_signatures:
            if sig in file_content[:1024]:  # Check first 1KB
                issues.append("Suspicious executable content in text file")
                break
    
    # Check for script injection attempts
    script_patterns = [
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'data:text/html',
        b'<?php'
    ]
    
    content_lower = file_content[:4096].lower()  # Check first 4KB
    for pattern in script_patterns:
        if pattern in content_lower:
            issues.append(f"Potential script injection detected")
            break
    
    return len(issues) == 0, issues