"""
Utilities module for News Aggregator
Contains helper functions, caching, rate limiting, and logging
"""

from utils.cache import CacheManager, cached, st_cached_fetch
from utils.rate_limiter import RateLimiter, check_rate_limit, get_rate_limit_status, rate_limited
from utils.logger import (
    setup_logger,
    log_error,
    log_info,
    log_warning,
    log_debug,
    log_user_action,
    log_performance
)
from utils.helpers import (
    validate_url,
    clean_html,
    truncate_text,
    format_date,
    extract_domain,
    generate_id,
    safe_get,
    chunk_list,
    is_valid_email,
    slugify,
    get_time_ago
)

__all__ = [
    # Cache
    'CacheManager',
    'cached',
    'st_cached_fetch',

    # Rate Limiter
    'RateLimiter',
    'check_rate_limit',
    'get_rate_limit_status',
    'rate_limited',

    # Logger
    'setup_logger',
    'log_error',
    'log_info',
    'log_warning',
    'log_debug',
    'log_user_action',
    'log_performance',

    # Helpers
    'validate_url',
    'clean_html',
    'truncate_text',
    'format_date',
    'extract_domain',
    'generate_id',
    'safe_get',
    'chunk_list',
    'is_valid_email',
    'slugify',
    'get_time_ago'
]
