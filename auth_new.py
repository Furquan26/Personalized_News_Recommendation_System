# auth.py
import streamlit as st
import sqlite3
import hashlib
import re
import os
import uuid
import time
from config import config
from utils import (
    log_error,
    log_info,
    cached,
    check_rate_limit,
    is_valid_email,
    format_date
)

# Database setup


def create_connection():
    """Create database connection with error handling"""
    try:
        log_info("Creating database connection")
        os.makedirs(os.path.dirname(config.DATABASE_PATH)
                    or '.', exist_ok=True)
        conn = sqlite3.connect(config.DATABASE_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL,
                      email TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS preferences
                     (email TEXT PRIMARY KEY, sources TEXT, category TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS sessions
                     (token TEXT PRIMARY KEY, email TEXT NOT NULL, expires_at INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS bookmarks
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      email TEXT NOT NULL,
                      title TEXT NOT NULL,
                      link TEXT NOT NULL,
                      source TEXT,
                      saved_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS reading_activity
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      email TEXT NOT NULL,
                      article_title TEXT NOT NULL,
                      article_link TEXT NOT NULL,
                      source TEXT,
                      category TEXT,
                      read_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      reading_time_seconds INTEGER DEFAULT 0)''')
        conn.commit()
        log_info("Database connection created successfully")
        return conn
    except Exception as e:
        log_error(f"Failed to create database connection: {str(e)}")
        raise

# Password hashing


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Note: is_valid_email is imported from utils module

# Save user preferences


def save_preferences(email, sources, category):
    """Save user news preferences with error handling"""
    try:
        log_info(f"Saving preferences for user: {email}")
        conn = create_connection()
        c = conn.cursor()
        sources_str = ",".join(sources) if sources else ""
        c.execute("INSERT OR REPLACE INTO preferences VALUES (?, ?, ?)",
                  (email, sources_str, category))
        conn.commit()
        conn.close()
        log_info(f"Preferences saved successfully for: {email}")
        return True
    except Exception as e:
        log_error(f"Failed to save preferences for {email}: {str(e)}")
        return False

# Load user preferences


def load_preferences(email):
    """Load user news preferences with error handling"""
    try:
        log_info(f"Loading preferences for user: {email}")
        conn = create_connection()
        c = conn.cursor()
        c.execute(
            "SELECT sources, category FROM preferences WHERE email=?", (email,))
        result = c.fetchone()
        conn.close()

        if result:
            sources = result[0].split(",") if result[0] else []
            category = result[1]
            log_info(f"Preferences loaded for: {email}")
            return sources, category
        log_info(f"No preferences found for: {email}, using defaults")
        return [], "General"
    except Exception as e:
        log_error(f"Failed to load preferences for {email}: {str(e)}")
        return [], "General"

# Session token helpers


def create_session_token(email):
    """Create a new session token for authenticated user"""
    try:
        log_info(f"Creating session token for: {email}")
        conn = create_connection()
        c = conn.cursor()
        token = uuid.uuid4().hex
        expires_at = int(time.time()) + 86400 * 7  # 7 days
        c.execute("INSERT OR REPLACE INTO sessions VALUES (?, ?, ?)",
                  (token, email, expires_at))
        conn.commit()
        conn.close()
        log_info(f"Session token created for: {email}")
        return token
    except Exception as e:
        log_error(f"Failed to create session token for {email}: {str(e)}")
        return None


def validate_session_token(email, token):
    """Validate if session token is still active"""
    try:
        if not email or not token:
            return False
        conn = create_connection()
        c = conn.cursor()
        c.execute(
            "SELECT expires_at FROM sessions WHERE email=? AND token=?", (email, token))
        result = c.fetchone()
        conn.close()
        if result and result[0] >= int(time.time()):
            log_info(f"Session token validated for: {email}")
            return True
        log_info(f"Session token expired or invalid for: {email}")
        return False
    except Exception as e:
        log_error(f"Failed to validate session token: {str(e)}")
        return False


def clear_session_token(token):
    """Clear session token on logout"""
    try:
        if not token:
            return
        log_info("Clearing session token")
        conn = create_connection()
        c = conn.cursor()
        c.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()
        conn.close()
        log_info("Session token cleared")
    except Exception as e:
        log_error(f"Failed to clear session token: {str(e)}")


def restore_session_from_query():
    params = st.query_params
    token = params.get("auth_token", None)
    email = params.get("email", None)
    if token and email and validate_session_token(email, token):
        conn = create_connection()
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        if user:
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.user_name = user[0]
            sources, category = load_preferences(email)
            st.session_state.selected_sources = sources
            st.session_state.selected_category = category
            return True
    return False

# Sign up function


def sign_up():
    with st.form("signup_form"):
        st.subheader("Create New Account")
        name = st.text_input("Full Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input(
            "Password", type='password', key="signup_password")
        confirm_password = st.text_input(
            "Confirm Password", type='password', key="signup_confirm_password")

        submitted = st.form_submit_button("Sign Up")

        if submitted:
            if not name or not email or not password:
                st.error("All fields are required!")
                return False
            if not is_valid_email(email):
                st.error("Please enter a valid email address")
                return False
            if password != confirm_password:
                st.error("Passwords do not match!")
                return False
            if len(password) < 6:
                st.error("Password must be at least 6 characters")
                return False

            conn = create_connection()
            c = conn.cursor()

            try:
                c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                          (name, email, hash_password(password)))
                conn.commit()
                st.success("Account created successfully! Please login.")
                return True
            except sqlite3.IntegrityError:
                st.error("Email already exists. Please login instead.")
                return False
            finally:
                conn.close()
    return False

# Login function


def login():
    with st.form("login_form"):
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input(
            "Password", type='password', key="login_password")

        submitted = st.form_submit_button("Login")

        if submitted:
            if not email or not password:
                st.error("Both email and password are required!")
                return False

            conn = create_connection()
            c = conn.cursor()
            c.execute("SELECT username FROM users WHERE email=? AND password=?",
                      (email, hash_password(password)))
            user = c.fetchone()
            conn.close()

            if user:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_name = user[0]

                # Persist login across refresh/reload
                token = create_session_token(email)
                st.query_params.update({"auth_token": token, "email": email})

                # Load saved preferences
                sources, category = load_preferences(email)
                st.session_state.selected_sources = sources
                st.session_state.selected_category = category

                st.success(f"Welcome back, {user[0]}!")
                return True
            else:
                st.error("Invalid email or password")
                return False
    return False

# Logout function


def logout():
    if st.sidebar.button("Logout"):
        params = st.query_params
        token = params.get("auth_token", None)
        if token:
            clear_session_token(token)
        st.query_params.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Bookmarks functions


def add_bookmark(email, title, link, source):
    """Add a bookmark for the user"""
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute("INSERT INTO bookmarks (email, title, link, source) VALUES (?, ?, ?, ?)",
                  (email, title, link, source))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Error adding bookmark: {str(e)}")
        return False


def get_bookmarks(email):
    """Get all bookmarks for a user"""
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute("SELECT title, link, source, saved_date FROM bookmarks WHERE email=? ORDER BY saved_date DESC",
                  (email,))
        bookmarks = c.fetchall()
        conn.close()
        return bookmarks
    except Exception as e:
        log_error(f"Error fetching bookmarks: {str(e)}")
        return []


def delete_bookmark(email, title, link):
    """Delete a bookmark"""
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute("DELETE FROM bookmarks WHERE email=? AND title=? AND link=?",
                  (email, title, link))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Error deleting bookmark: {str(e)}")
        return False

# Reading Activity Tracking Functions


def log_article_read(email, article_title, article_link, source, category, reading_time_seconds=0):
    """Log when a user reads an article"""
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute("""INSERT INTO reading_activity 
                     (email, article_title, article_link, source, category, reading_time_seconds) 
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (email, article_title, article_link, source, category, reading_time_seconds))
        conn.commit()
        conn.close()
        log_info(f"Logged article read for {email}: {article_title}")
        return True
    except Exception as e:
        log_error(f"Error logging article read: {str(e)}")
        return False


def get_articles_read_count(email, days=None):
    """Get total articles read by user (within optional time period)"""
    try:
        conn = create_connection()
        c = conn.cursor()

        if days:
            c.execute("""SELECT COUNT(*) FROM reading_activity 
                         WHERE email=? AND read_date >= datetime('now', '-' || ? || ' days')""",
                      (email, days))
        else:
            c.execute(
                "SELECT COUNT(*) FROM reading_activity WHERE email=?", (email,))

        result = c.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        log_error(f"Error getting articles read count: {str(e)}")
        return 0


def get_total_reading_time(email, days=None):
    """Get total reading time in seconds (within optional time period)"""
    try:
        conn = create_connection()
        c = conn.cursor()

        if days:
            c.execute("""SELECT SUM(reading_time_seconds) FROM reading_activity 
                         WHERE email=? AND read_date >= datetime('now', '-' || ? || ' days')""",
                      (email, days))
        else:
            c.execute(
                "SELECT SUM(reading_time_seconds) FROM reading_activity WHERE email=?", (email,))

        result = c.fetchone()
        conn.close()
        return result[0] if result and result[0] else 0
    except Exception as e:
        log_error(f"Error getting total reading time: {str(e)}")
        return 0


def get_articles_by_category(email, days=None):
    """Get article count by category (within optional time period)"""
    try:
        conn = create_connection()
        c = conn.cursor()

        if days:
            c.execute("""SELECT category, COUNT(*) as count FROM reading_activity 
                         WHERE email=? AND read_date >= datetime('now', '-' || ? || ' days')
                         GROUP BY category ORDER BY count DESC""",
                      (email, days))
        else:
            c.execute("""SELECT category, COUNT(*) as count FROM reading_activity 
                         WHERE email=? GROUP BY category ORDER BY count DESC""",
                      (email,))

        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        log_error(f"Error getting articles by category: {str(e)}")
        return []


def get_articles_by_source(email, days=None):
    """Get article count by source (within optional time period)"""
    try:
        conn = create_connection()
        c = conn.cursor()

        if days:
            c.execute("""SELECT source, COUNT(*) as count FROM reading_activity 
                         WHERE email=? AND read_date >= datetime('now', '-' || ? || ' days')
                         GROUP BY source ORDER BY count DESC""",
                      (email, days))
        else:
            c.execute("""SELECT source, COUNT(*) as count FROM reading_activity 
                         WHERE email=? GROUP BY source ORDER BY count DESC""",
                      (email,))

        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        log_error(f"Error getting articles by source: {str(e)}")
        return []


def get_daily_reading_stats(email, days=30):
    """Get daily reading statistics for the last N days"""
    try:
        conn = create_connection()
        c = conn.cursor()

        c.execute("""SELECT DATE(read_date) as date, COUNT(*) as count, SUM(reading_time_seconds) as total_time
                     FROM reading_activity 
                     WHERE email=? AND read_date >= datetime('now', '-' || ? || ' days')
                     GROUP BY DATE(read_date)
                     ORDER BY date DESC""",
                  (email, days))

        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        log_error(f"Error getting daily reading stats: {str(e)}")
        return []


def get_hourly_pattern(email, days=30):
    """Get reading activity by hour of day"""
    try:
        conn = create_connection()
        c = conn.cursor()

        c.execute("""SELECT CAST(STRFTIME('%H', read_date) AS INTEGER) as hour, COUNT(*) as count
                     FROM reading_activity 
                     WHERE email=? AND read_date >= datetime('now', '-' || ? || ' days')
                     GROUP BY hour
                     ORDER BY hour""",
                  (email, days))

        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        log_error(f"Error getting hourly pattern: {str(e)}")
        return []


def get_favorite_topic(email, days=None):
    """Get the most read category/topic"""
    try:
        results = get_articles_by_category(email, days)
        if results:
            return results[0][0], results[0][1]
        return "General", 0
    except Exception as e:
        log_error(f"Error getting favorite topic: {str(e)}")
        return "General", 0


def get_reading_streak(email):
    """Calculate current reading streak (consecutive days of reading)"""
    try:
        conn = create_connection()
        c = conn.cursor()

        # Get all unique reading dates in descending order
        c.execute("""SELECT DISTINCT DATE(read_date) as date FROM reading_activity 
                     WHERE email=? ORDER BY date DESC LIMIT 365""",
                  (email,))

        dates = [row[0] for row in c.fetchall()]
        conn.close()

        if not dates:
            return 0

        from datetime import datetime, timedelta
        streak = 0
        current_date = datetime.now().date()

        for date_str in dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            if date_obj == current_date or date_obj == current_date - timedelta(days=1):
                streak += 1
                current_date = date_obj
            else:
                break

        return streak
    except Exception as e:
        log_error(f"Error calculating reading streak: {str(e)}")
        return 0


def get_reading_activity(email, limit=10):
    """Get recent reading activity"""
    try:
        conn = create_connection()
        c = conn.cursor()

        c.execute("""SELECT article_title, source, category, read_date FROM reading_activity 
                     WHERE email=? ORDER BY read_date DESC LIMIT ?""",
                  (email, limit))

        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        log_error(f"Error getting reading activity: {str(e)}")
        return []

# Main auth function


def show_auth_page():
    # Page configuration is handled by the main app script to avoid duplicate calls.
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("📰 News Aggregator")
        st.markdown("### Your Personalized News Hub")

        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            if login():
                st.rerun()

        with tab2:
            if sign_up():
                st.success("Now please login with your new account")
