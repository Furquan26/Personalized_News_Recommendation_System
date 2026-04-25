"""
Cache management with TTL (Time To Live)
Uses dictionary-based caching with expiration
"""

import time
from functools import wraps
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import streamlit as st
from loguru import logger


class CacheManager:
    """Simple in-memory cache with TTL support"""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # key: (value, expiry_time)

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Store value in cache with expiration"""
        expiry = time.time() + ttl_seconds
        self._cache[key] = (value, expiry)
        logger.debug(f"Cached: {key} (expires in {ttl_seconds}s)")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                logger.debug(f"Cache hit: {key}")
                return value
            else:
                # Remove expired entry
                del self._cache[key]
                logger.debug(f"Cache expired: {key}")
        return None

    def delete(self, key: str) -> None:
        """Remove specific key from cache"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")

    def clear(self) -> None:
        """Clear entire cache"""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "total_entries": len(self._cache),
            "active_entries": sum(1 for _, (_, exp) in self._cache.items() if time.time() < exp),
            "expired_entries": sum(1 for _, (_, exp) in self._cache.items() if time.time() >= exp)
        }


# Singleton cache instance
_cache_manager = CacheManager()


def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results

    Usage:
        @cached(ttl_seconds=600)
        def fetch_news(url):
            return expensive_operation(url)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{key_prefix or func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_result = _cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache_manager.set(cache_key, result, ttl_seconds)
            return result
        return wrapper
    return decorator


# Streamlit-specific cache helper
@st.cache_data(ttl=300, show_spinner=False)
def st_cached_fetch(func, *args, **kwargs):
    """Streamlit-compatible cache wrapper"""
    return func(*args, **kwargs)
