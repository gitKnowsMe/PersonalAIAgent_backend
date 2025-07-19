"""
Caching utilities for Personal AI Agent.

Provides in-memory caching for frequently accessed data to improve performance.
Uses TTL-based caching with automatic cleanup.
"""

import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from functools import wraps
from collections import defaultdict

logger = logging.getLogger("personal_ai_agent")


class TTLCache:
    """
    Time-To-Live cache with automatic expiration.
    
    Features:
    - TTL-based expiration
    - Automatic cleanup of expired entries
    - Memory usage tracking
    - Hit/miss statistics
    """
    
    def __init__(self, default_ttl_seconds: int = 300, max_size: int = 1000):
        self.default_ttl = default_ttl_seconds
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if a cache entry is expired"""
        return datetime.now() > entry["expires_at"]
    
    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        expired_keys = []
        for key, entry in self.cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            self.stats["evictions"] += 1
        
        self.stats["size"] = len(self.cache)
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _enforce_size_limit(self):
        """Enforce maximum cache size by removing oldest entries"""
        if len(self.cache) <= self.max_size:
            return
        
        # Sort by creation time and remove oldest entries
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1]["created_at"]
        )
        
        to_remove = len(self.cache) - self.max_size
        for i in range(to_remove):
            key = sorted_entries[i][0]
            del self.cache[key]
            self.stats["evictions"] += 1
        
        self.stats["size"] = len(self.cache)
        logger.debug(f"Evicted {to_remove} entries to enforce size limit")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Cleanup expired entries periodically
        if len(self.cache) % 100 == 0:
            self._cleanup_expired()
        
        if key not in self.cache:
            self.stats["misses"] += 1
            return None
        
        entry = self.cache[key]
        if self._is_expired(entry):
            del self.cache[key]
            self.stats["misses"] += 1
            self.stats["evictions"] += 1
            self.stats["size"] = len(self.cache)
            return None
        
        self.stats["hits"] += 1
        entry["accessed_at"] = datetime.now()
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set value in cache with TTL"""
        ttl = ttl_seconds or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self.cache[key] = {
            "value": value,
            "created_at": datetime.now(),
            "accessed_at": datetime.now(),
            "expires_at": expires_at
        }
        
        self.stats["size"] = len(self.cache)
        self._enforce_size_limit()
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        if key in self.cache:
            del self.cache[key]
            self.stats["size"] = len(self.cache)
            return True
        return False
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.stats["size"] = 0
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "size": self.stats["size"],
            "max_size": self.max_size,
            "evictions": self.stats["evictions"]
        }


# Global cache instances for different data types
user_cache = TTLCache(default_ttl_seconds=300, max_size=500)  # 5 minutes
document_cache = TTLCache(default_ttl_seconds=600, max_size=200)  # 10 minutes
query_cache = TTLCache(default_ttl_seconds=180, max_size=100)  # 3 minutes
gmail_cache = TTLCache(default_ttl_seconds=120, max_size=50)  # 2 minutes


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments"""
    # Create a deterministic key from arguments
    key_data = {
        "args": str(args),
        "kwargs": sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(cache_instance: TTLCache, ttl_seconds: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Args:
        cache_instance: The cache instance to use
        ttl_seconds: TTL for this specific cache entry
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache_instance.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_instance.set(key, result, ttl_seconds)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        return wrapper
    return decorator


# Convenience decorators for specific cache types
def cache_user_data(ttl_seconds: Optional[int] = None):
    """Cache user-related data"""
    return cached(user_cache, ttl_seconds)


def cache_document_data(ttl_seconds: Optional[int] = None):
    """Cache document-related data"""
    return cached(document_cache, ttl_seconds)


def cache_query_result(ttl_seconds: Optional[int] = None):
    """Cache query results"""
    return cached(query_cache, ttl_seconds)


def cache_gmail_data(ttl_seconds: Optional[int] = None):
    """Cache Gmail-related data"""
    return cached(gmail_cache, ttl_seconds)


def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a specific user"""
    keys_to_delete = []
    for key in user_cache.cache.keys():
        if f"user_{user_id}" in key or f'"user_id": "{user_id}"' in key:
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        user_cache.delete(key)
    
    if keys_to_delete:
        logger.info(f"Invalidated {len(keys_to_delete)} cache entries for user {user_id}")


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all cache instances"""
    return {
        "user_cache": user_cache.get_stats(),
        "document_cache": document_cache.get_stats(),
        "query_cache": query_cache.get_stats(),
        "gmail_cache": gmail_cache.get_stats()
    }


def clear_all_caches():
    """Clear all cache instances"""
    user_cache.clear()
    document_cache.clear()
    query_cache.clear()
    gmail_cache.clear()
    logger.info("All caches cleared")


# Cache warming functions
def warm_user_cache():
    """Pre-load frequently accessed user data"""
    # This could be implemented to pre-load common user queries
    pass


def warm_document_cache():
    """Pre-load document metadata"""
    # This could be implemented to pre-load document classifications
    pass