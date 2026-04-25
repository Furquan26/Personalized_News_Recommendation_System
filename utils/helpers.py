"""
Helper utility functions for common operations
"""

import re
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
import html


def validate_url(url: str) -> bool:
    """
    Validate if string is a valid URL

    Args:
        url: URL string to validate

    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text

    Args:
        text: HTML text to clean

    Returns:
        Plain text without HTML tags
    """
    if not text:
        return ""

    # Remove HTML tags
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)

    # Unescape HTML entities
    text = html.unescape(text)

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text.strip()


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length allowed
        suffix: String to append at the end

    Returns:
        Truncated text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    # Try to truncate at last space within limit
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')

    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + suffix


def format_date(date_input, format_string: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format date to string

    Args:
        date_input: datetime object or date string
        format_string: Desired output format

    Returns:
        Formatted date string
    """
    if not date_input:
        return "Unknown date"

    try:
        if isinstance(date_input, str):
            # Try to parse common date formats
            for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"]:
                try:
                    date_input = datetime.strptime(date_input, fmt)
                    break
                except ValueError:
                    continue
            else:
                return date_input[:16]  # Fallback

        return date_input.strftime(format_string)
    except Exception:
        return str(date_input)[:16]


def extract_domain(url: str) -> str:
    """
    Extract domain name from URL

    Args:
        url: Full URL

    Returns:
        Domain name (e.g., "timesofindia.indiatimes.com")
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return "unknown"


def generate_id() -> str:
    """
    Generate unique ID (UUID)

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def safe_get(data: dict, key: str, default=None):
    """
    Safely get value from dictionary with dot notation support

    Args:
        data: Dictionary to search
        key: Key path (supports dot notation like 'user.profile.name')
        default: Default value if key not found

    Returns:
        Value from dictionary or default
    """
    keys = key.split('.')
    current = data

    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default

    return current


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split list into chunks

    Args:
        lst: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def is_valid_email(email: str) -> bool:
    """
    Validate email format

    Args:
        email: Email string to validate

    Returns:
        True if valid email format
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug

    Args:
        text: Text to slugify

    Returns:
        Slugified string
    """
    # Convert to lowercase and remove special characters
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')


def get_time_ago(timestamp) -> str:
    """
    Get human-readable time difference

    Args:
        timestamp: datetime object

    Returns:
        String like "5 minutes ago", "2 hours ago", etc.
    """
    if not timestamp:
        return "Unknown"

    now = datetime.now()
    diff = now - timestamp

    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        return timestamp.strftime("%Y-%m-%d")
