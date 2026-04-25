# File: config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from current directory
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration"""

    # App Config
    APP_NAME = os.getenv('APP_NAME', 'Personalized News Recommendation System')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-key')

    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/users.db')

    # RSS Settings
    RSS_TIMEOUT = int(os.getenv('RSS_TIMEOUT', 10))
    RSS_CACHE_DURATION = int(os.getenv('RSS_CACHE_DURATION', 1800))
    MAX_ARTICLES_PER_FEED = int(os.getenv('MAX_ARTICLES_PER_FEED', 10))

    # API Keys (for future)
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
    NEWSAPI_ORG_KEY = os.getenv('NEWSAPI_ORG_KEY', '')
    GNEWS_API_KEY = os.getenv('GNEWS_API_KEY', '')

    # Email (for future)
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')

    # Admin
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')

    # Streamlit
    STREAMLIT_THEME = os.getenv('STREAMLIT_THEME', 'light')
    STREAMLIT_PORT = int(os.getenv('STREAMLIT_PORT', 8501))


# Create config instance
config = Config()
