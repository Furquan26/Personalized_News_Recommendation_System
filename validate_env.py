"""
Environment validation for production readiness
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from utils import log_error, log_info

# Load environment
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

REQUIRED_VARS = [
    'SECRET_KEY',
    'DATABASE_URL',
]

OPTIONAL_VARS = [
    'DEBUG',
    'APP_NAME',
    'JWT_ALGORITHM',
    'JWT_EXPIRATION_HOURS',
    'RSS_TIMEOUT',
    'RSS_CACHE_DURATION',
    'MAX_ARTICLES_PER_FEED',
]

def validate_environment():
    """Validate required environment variables"""
    missing = []
    warnings = []

    for var in REQUIRED_VARS:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        log_error(f"Missing required environment variables: {', '.join(missing)}")
        return False

    # Check SECRET_KEY strength
    secret_key = os.getenv('SECRET_KEY')
    if secret_key and len(secret_key) < 32:
        warnings.append("SECRET_KEY should be at least 32 characters for security")

    # Check DATABASE_URL format
    db_url = os.getenv('DATABASE_URL')
    if db_url and not db_url.startswith(('postgresql://', 'postgres://')):
        warnings.append("DATABASE_URL should be a valid PostgreSQL connection string")

    if warnings:
        for warning in warnings:
            log_info(f"Warning: {warning}")

    log_info("Environment validation completed successfully")
    return True

if __name__ == "__main__":
    if validate_environment():
        print("✅ Environment validation passed")
        sys.exit(0)
    else:
        print("❌ Environment validation failed")
        sys.exit(1)