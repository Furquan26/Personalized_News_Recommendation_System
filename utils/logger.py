"""
Logging configuration for the application
Logs to both file and console with rotation
"""

import os
import sys
from pathlib import Path
from loguru import logger
from datetime import datetime


def setup_logger(log_level: str = "INFO", log_to_file: bool = True):
    """
    Setup logger configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to write logs to file
    """
    # Remove default handler
    logger.remove()

    # Determine log level
    level = getattr(logger.level, log_level.upper(), logger.level.INFO)

    # Console logging with structured format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
        enqueue=True  # Thread-safe
    )

    # File logging (with rotation)
    if log_to_file:
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Main application log file
        logger.add(
            log_dir / "app.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            enqueue=True
        )

        # Error-only log file
        logger.add(
            log_dir / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="5 MB",
            retention="60 days",
            compression="zip",
            encoding="utf-8",
            enqueue=True
        )

        # Security log file
        logger.add(
            log_dir / "security.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level="WARNING",
            rotation="5 MB",
            retention="90 days",
            compression="zip",
            encoding="utf-8",
            enqueue=True,
            filter=lambda record: "auth" in record["name"].lower() or "security" in record["message"].lower()
        )

    logger.info(f"Logger initialized with level: {log_level}")
    return logger


def log_error(message: str, exception: Exception = None):
    """Log error message with optional exception details"""
    if exception:
        logger.error(f"{message} - {str(exception)}", exc_info=True)
    else:
        logger.error(message)


def log_info(message: str):
    """Log info message"""
    logger.info(message)


def log_warning(message: str):
    """Log warning message"""
    logger.warning(message)


def log_debug(message: str):
    """Log debug message"""
    logger.debug(message)


# Session-based logging for Streamlit
def log_user_action(user_id: str, action: str, details: dict = None):
    """Log user-specific actions"""
    log_info(f"User: {user_id} | Action: {action} | Details: {details}")


# Performance logging decorator
def log_performance(func):
    """Decorator to log function execution time"""
    from functools import wraps
    import time

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.debug(f"{func.__name__} took {execution_time:.3f} seconds")
        return result
    return wrapper
