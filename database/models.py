"""
PostgreSQL Database Models
Complete schema for news aggregator
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from database.connection import db_manager
from loguru import logger


class UserModel:
    """User management model"""

    @staticmethod
    def create_user(email: str, password_hash: str, username: str) -> Optional[Dict]:
        """Create new user"""
        try:
            query = """
                INSERT INTO users (user_id, email, password_hash, username, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING user_id, email, username, created_at
            """
            user_id = uuid.uuid4()
            now = datetime.now()

            result = db_manager.execute_query(
                query,
                (user_id, email, password_hash, username, now),
                fetch_one=True
            )
            return result
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            query = "SELECT * FROM users WHERE email = %s AND is_active = TRUE"
            return db_manager.execute_query(query, (email,), fetch_one=True)
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE user_id = %s AND is_active = TRUE"
        return db_manager.execute_query(query, (user_id,), fetch_one=True)

    @staticmethod
    def update_last_login(user_id: str):
        """Update user's last login time"""
        query = "UPDATE users SET last_login = %s WHERE user_id = %s"
        db_manager.execute_query(query, (datetime.now(), user_id))

    @staticmethod
    def update_preferences(user_id: str, preferences: Dict):
        """Update user preferences"""
        try:
            query = "UPDATE users SET preferences = %s WHERE user_id = %s"
            db_manager.execute_query(query, (preferences, user_id))
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            raise

    @staticmethod
    def get_preferences(user_id: str) -> Dict:
        """Get user preferences"""
        query = "SELECT preferences FROM users WHERE user_id = %s"
        result = db_manager.execute_query(query, (user_id,), fetch_one=True)
        return result.get('preferences', {}) if result else {}

    @staticmethod
    def deactivate_user(user_id: str):
        """Soft delete user"""
        query = "UPDATE users SET is_active = FALSE WHERE user_id = %s"
        db_manager.execute_query(query, (user_id,))


class BookmarkModel:
    """Bookmark management model"""

    @staticmethod
    def add_bookmark(user_id: str, article_url: str, article_title: str, category: str = None):
        """Add article to bookmarks"""
        try:
            query = """
                INSERT INTO bookmarks (bookmark_id, user_id, article_url, article_title, category, saved_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING bookmark_id
            """
            bookmark_id = uuid.uuid4()
            now = datetime.now()

            result = db_manager.execute_query(
                query,
                (bookmark_id, user_id, article_url, article_title, category, now),
                fetch_one=True
            )
            return result
        except Exception as e:
            logger.error(f"Error adding bookmark for user {user_id}: {e}")
            return None

    @staticmethod
    def get_user_bookmarks(user_id: str, limit: int = 50) -> list:
        """Get all bookmarks for a user"""
        query = """
            SELECT bookmark_id, article_url, article_title, category, saved_at
            FROM bookmarks
            WHERE user_id = %s
            ORDER BY saved_at DESC
            LIMIT %s
        """
        return db_manager.execute_query(query, (user_id, limit), fetch_all=True) or []

    @staticmethod
    def remove_bookmark(bookmark_id: str, user_id: str):
        """Remove bookmark"""
        query = "DELETE FROM bookmarks WHERE bookmark_id = %s AND user_id = %s"
        db_manager.execute_query(query, (bookmark_id, user_id))

    @staticmethod
    def is_bookmarked(user_id: str, article_url: str) -> bool:
        """Check if article is bookmarked"""
        query = "SELECT 1 FROM bookmarks WHERE user_id = %s AND article_url = %s"
        result = db_manager.execute_query(
            query, (user_id, article_url), fetch_one=True)
        return result is not None


class ActivityModel:
    """User activity tracking model"""

    @staticmethod
    def log_activity(user_id: str, activity_type: str, metadata: Dict = None):
        """Log user activity"""
        query = """
            INSERT INTO user_activity (activity_id, user_id, activity_type, timestamp, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """
        activity_id = uuid.uuid4()
        now = datetime.now()

        db_manager.execute_query(
            query,
            (activity_id, user_id, activity_type, now, metadata or {})
        )

    @staticmethod
    def get_user_activity(user_id: str, days: int = 7) -> list:
        """Get recent user activity"""
        query = """
            SELECT activity_type, timestamp, metadata
            FROM user_activity
            WHERE user_id = %s AND timestamp >= NOW() - INTERVAL '%s days'
            ORDER BY timestamp DESC
        """
        return db_manager.execute_query(query, (user_id, days), fetch_all=True) or []


class NewsModel:
    """News article management with full-text search"""

    @staticmethod
    def create_tables():
        """Create all tables (run once at startup)"""
        queries = [
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                username VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                preferences JSONB DEFAULT '{}'::jsonb
            )
            """,

            # Bookmarks table
            """
            CREATE TABLE IF NOT EXISTS bookmarks (
                bookmark_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                article_url TEXT NOT NULL,
                article_title TEXT,
                category VARCHAR(50),
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,

            # User activity table
            """
            CREATE TABLE IF NOT EXISTS user_activity (
                activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                activity_type VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            )
            """,

            # News articles cache table
            """
            CREATE TABLE IF NOT EXISTS news_articles (
                article_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source VARCHAR(100),
                category VARCHAR(50),
                published_at TIMESTAMP,
                description TEXT,
                content TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,

            # Create indexes for performance
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON user_activity(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_news_url ON news_articles(url)",
            "CREATE INDEX IF NOT EXISTS idx_news_category ON news_articles(category)",
            "CREATE INDEX IF NOT EXISTS idx_news_published ON news_articles(published_at)",

            # Full-text search index for news
            """
            CREATE INDEX IF NOT EXISTS idx_news_search 
            ON news_articles USING GIN(to_tsvector('english', title || ' ' || COALESCE(description, '')))
            """
        ]

        for query in queries:
            try:
                db_manager.execute_query(query)
            except Exception as e:
                logger.error(f"Failed to create table: {e}")

        logger.info("✅ Database tables created successfully")

    @staticmethod
    def search_articles(search_query: str, category: str = None, limit: int = 20) -> list:
        """Full-text search in news articles"""
        if not search_query:
            return []

        query = """
            SELECT article_id, title, url, source, category, 
                   published_at, description,
                   ts_rank(to_tsvector('english', title || ' ' || COALESCE(description, '')),
                          plainto_tsquery('english', %s)) as relevance
            FROM news_articles
            WHERE to_tsvector('english', title || ' ' || COALESCE(description, ''))
                  @@ plainto_tsquery('english', %s)
        """
        params = [search_query, search_query]

        if category:
            query += " AND category = %s"
            params.append(category)

        query += " ORDER BY relevance DESC LIMIT %s"
        params.append(limit)

        return db_manager.execute_query(query, tuple(params), fetch_all=True) or []

    @staticmethod
    def save_article(article_data: Dict):
        """Save or update article in cache"""
        query = """
            INSERT INTO news_articles (title, url, source, category, published_at, description, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                fetched_at = CURRENT_TIMESTAMP
            RETURNING article_id
        """
        result = db_manager.execute_query(
            query,
            (
                article_data.get('title'),
                article_data.get('url'),
                article_data.get('source'),
                article_data.get('category'),
                article_data.get('published_at'),
                article_data.get('description'),
                article_data.get('content')
            ),
            fetch_one=True
        )
        return result


# Initialize tables when module loads
NewsModel.create_tables()
