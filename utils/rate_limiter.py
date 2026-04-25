"""
Rate limiting to prevent API abuse
Tracks requests per user/IP and blocks if limit exceeded
"""

import time
from collections import defaultdict
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps
from loguru import logger


class RateLimiter:
    """
    Rate limiter with sliding window algorithm

    Features:
    - Per-user rate limiting
    - Per-IP rate limiting
    - Configurable limits per endpoint
    - Automatic cleanup of old entries
    """

    def __init__(self):
        # Store request timestamps for each client
        self._requests: Dict[str, list] = defaultdict(list)
        self._cleanup_counter = 0
        self._cleanup_threshold = 100  # Clean up after 100 clients

    def _cleanup_old_requests(self, client_id: str, window_seconds: int) -> None:
        """Remove requests older than window"""
        now = time.time()
        if client_id in self._requests:
            self._requests[client_id] = [
                req_time for req_time in self._requests[client_id]
                if now - req_time < window_seconds
            ]

    def _periodic_cleanup(self) -> None:
        """Periodically clean up old client entries"""
        self._cleanup_counter += 1
        if self._cleanup_counter >= self._cleanup_threshold:
            now = time.time()
            # Remove clients with no recent requests
            to_delete = []
            for client_id, timestamps in self._requests.items():
                if not timestamps or now - max(timestamps) > 3600:  # 1 hour
                    to_delete.append(client_id)

            for client_id in to_delete:
                del self._requests[client_id]

            self._cleanup_counter = 0
            logger.debug(
                f"Cleaned up {len(to_delete)} inactive rate limit entries")

    def is_allowed(self, client_id: str, max_requests: int = 60, window_seconds: int = 60) -> Tuple[bool, Dict]:
        """
        Check if request is allowed

        Args:
            client_id: User ID or IP address
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            (is_allowed, info_dict) where info contains remaining requests and reset time
        """
        now = time.time()

        # Clean up old requests for this client
        self._cleanup_old_requests(client_id, window_seconds)

        # Check if limit exceeded
        current_requests = len(self._requests[client_id])
        is_allowed = current_requests < max_requests

        # Add current request if allowed (or track anyway for metrics)
        self._requests[client_id].append(now)

        # Calculate remaining requests and reset time
        remaining = max(0, max_requests - current_requests -
                        (1 if is_allowed else 0))

        # Find oldest request to calculate reset time
        if self._requests[client_id]:
            oldest = min(self._requests[client_id])
            reset_time = oldest + window_seconds
        else:
            reset_time = now + window_seconds

        info = {
            "allowed": is_allowed,
            "remaining": remaining,
            "reset_at": reset_time,
            "reset_in_seconds": max(0, reset_time - now),
            "total_requests": current_requests + 1,
            "max_requests": max_requests,
            "window_seconds": window_seconds
        }

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id}: {current_requests}/{max_requests}")

        return is_allowed, info

    def get_status(self, client_id: str, max_requests: int = 60, window_seconds: int = 60) -> Dict:
        """Get current rate limit status without consuming a request"""
        now = time.time()
        self._cleanup_old_requests(client_id, window_seconds)

        current_requests = len(self._requests[client_id])
        remaining = max(0, max_requests - current_requests)

        if self._requests[client_id]:
            oldest = min(self._requests[client_id])
            reset_time = oldest + window_seconds
        else:
            reset_time = now + window_seconds

        return {
            "remaining": remaining,
            "reset_at": reset_time,
            "reset_in_seconds": max(0, reset_time - now),
            "total_requests": current_requests,
            "max_requests": max_requests
        }

    def reset_client(self, client_id: str) -> None:
        """Reset rate limit for a specific client"""
        if client_id in self._requests:
            del self._requests[client_id]
            logger.info(f"Rate limit reset for {client_id}")

    def reset_all(self) -> None:
        """Reset all rate limits"""
        self._requests.clear()
        self._cleanup_counter = 0
        logger.info("All rate limits reset")


# Singleton rate limiter instance
_rate_limiter = RateLimiter()


def check_rate_limit(client_id: str, max_requests: int = 60, window_seconds: int = 60) -> Tuple[bool, Dict]:
    """Convenience function to check rate limit"""
    return _rate_limiter.is_allowed(client_id, max_requests, window_seconds)


def get_rate_limit_status(client_id: str, max_requests: int = 60, window_seconds: int = 60) -> Dict:
    """Convenience function to get rate limit status"""
    return _rate_limiter.get_status(client_id, max_requests, window_seconds)


# Decorator for rate limiting functions
def rate_limited(max_requests: int = 60, window_seconds: int = 60):
    """
    Decorator to rate limit a function

    Usage:
        @rate_limited(max_requests=10, window_seconds=60)
        def api_call(user_id):
            return expensive_operation()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get client_id from first argument or kwargs
            client_id = kwargs.get('client_id', str(
                args[0]) if args else 'default')

            is_allowed, info = check_rate_limit(
                client_id, max_requests, window_seconds)

            if not is_allowed:
                logger.warning(f"Rate limit blocked for {client_id}")
                raise Exception(
                    f"Rate limit exceeded. Try again in {int(info['reset_in_seconds'])} seconds")

            return func(*args, **kwargs)
        return wrapper
    return decorator
