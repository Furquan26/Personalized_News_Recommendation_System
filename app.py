"""
Personalized News Aggregator - Main Application
PostgreSQL backend with Streamlit frontend
"""

import streamlit as st
from datetime import datetime
from api.auth import AuthManager
from api.news_fetcher import NewsFetcher, NEWS_SOURCES
from database.models import BookmarkModel, ActivityModel, UserModel
from utils import (
    setup_logger,
    log_info,
    log_error,
    cached,
    check_rate_limit,
    clean_html,
    truncate_text,
    format_date,
    is_valid_email,
    get_time_ago
)

# Page config MUST be first Streamlit command
st.set_page_config(
    page_title="📰 Personalized News Aggregator",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logger at app startup
logger = setup_logger(log_level="INFO")
log_info("Main application started")

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .news-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .bookmark-btn {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 1.2rem;
    }
    </style>
""", unsafe_allow_html=True)


def show_landing_page():
    """Show login/signup page"""
    st.markdown('<div class="main-header"><h1>📰 Personalized News Aggregator</h1><p>Your AI-powered news companion</p></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "Login", use_container_width=True)

                if submitted:
                    if not email or not password:
                        st.error("Please fill all fields")
                    else:
                        try:
                            success, message, token = AuthManager.login(
                                email, password)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                        except Exception as e:
                            log_error(f"Login error: {e}")
                            st.error(
                                "An error occurred during login. Please try again.")

        with tab2:
            with st.form("signup_form"):
                username = st.text_input("Username")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input(
                    "Confirm Password", type="password")
                submitted = st.form_submit_button(
                    "Sign Up", use_container_width=True)

                if submitted:
                    if password != confirm_password:
                        st.error("Passwords don't match")
                    else:
                        try:
                            success, message = AuthManager.sign_up(
                                email, password, username)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                        except Exception as e:
                            log_error(f"Signup error: {e}")
                            st.error(
                                "An error occurred during signup. Please try again.")


def show_dashboard():
    """Main dashboard after login"""

    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.user_name}!")
        st.markdown(f"📧 {st.session_state.user_email}")
        st.divider()

        # News Preferences
        st.header("📰 Preferences")

        # Source selection
        available_sources = list(NEWS_SOURCES.keys())
        selected_sources = st.multiselect(
            "Select News Sources",
            available_sources,
            default=st.session_state.preferences.get('sources', [])
        )

        # Category selection
        categories = list(set(source['category']
                          for source in NEWS_SOURCES.values()))
        selected_category = st.selectbox(
            "Preferred Category",
            ["All"] + categories,
            index=0
        )

        # Save preferences
        if st.button("💾 Save Preferences", use_container_width=True):
            try:
                UserModel.update_preferences(st.session_state.user_id, {
                    'sources': selected_sources,
                    'category': selected_category
                })
                st.session_state.preferences = {
                    'sources': selected_sources, 'category': selected_category}
                st.success("Preferences saved!")
            except Exception as e:
                log_error(f"Error saving preferences: {e}")
                st.error("Failed to save preferences. Please try again.")

        st.divider()

        # Navigation
        st.header("🔗 Navigation")
        page = st.radio(
            "Go to", ["📊 News Feed", "🔖 Bookmarks", "📈 Activity", "👤 Profile"])

        st.divider()

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            AuthManager.logout()

    # Main content
    if page == "📊 News Feed":
        show_news_feed(selected_sources, selected_category)
    elif page == "🔖 Bookmarks":
        show_bookmarks()
    elif page == "📈 Activity":
        show_activity()
    elif page == "👤 Profile":
        show_profile()


def show_news_feed(selected_sources, selected_category):
    """Display news feed"""
    st.header("📊 News Feed")

    # Search bar
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "🔍 Search news", placeholder="Enter keywords...")
    with col2:
        st.markdown("")
        st.markdown("")
        refresh = st.button("🔄 Refresh", use_container_width=True)

    # Fetch news
    if refresh or 'news_items' not in st.session_state:
        with st.spinner("Fetching latest news..."):
            try:
                category_to_fetch = None if selected_category == "All" else selected_category
                st.session_state.news_items = NewsFetcher.get_news_for_user(
                    st.session_state.user_id,
                    selected_sources,
                    category_to_fetch
                )
            except Exception as e:
                log_error(f"Error fetching news: {e}")
                st.error("Failed to fetch news. Please try again later.")
                st.session_state.news_items = []

    # Search filter
    if search_query:
        filtered_news = [n for n in st.session_state.get('news_items', [])
                         if search_query.lower() in n['title'].lower()]
        st.info(
            f"Found {len(filtered_news)} articles matching '{search_query}'")
    else:
        filtered_news = st.session_state.get('news_items', [])

    # Display news
    if filtered_news:
        for idx, article in enumerate(filtered_news):
            with st.container():
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.markdown(f"### [{article['title']}]({article['url']})")
                    st.caption(
                        f"📰 {article['source']} | 📅 {article['published_at'].strftime('%Y-%m-%d %H:%M')}")
                    if article.get('description'):
                        st.write(article['description'][:200] + "...")

                with col2:
                    # Bookmark button
                    try:
                        is_bookmarked = BookmarkModel.is_bookmarked(
                            st.session_state.user_id, article['url'])
                        bookmark_label = "🔖" if is_bookmarked else "📑"
                        if st.button(bookmark_label, key=f"bookmark_{idx}", help="Save for later"):
                            if is_bookmarked:
                                # Would need bookmark_id - simplified for demo
                                st.warning(
                                    "Remove bookmark feature - implement with bookmark_id")
                            else:
                                try:
                                    BookmarkModel.add_bookmark(
                                        st.session_state.user_id,
                                        article['url'],
                                        article['title'],
                                        article.get('category', 'General')
                                    )
                                    st.success("Bookmarked!")
                                    st.rerun()
                                except Exception as e:
                                    log_error(f"Error adding bookmark: {e}")
                                    st.error("Failed to bookmark article.")
                    except Exception as e:
                        log_error(f"Error checking bookmark status: {e}")
                        st.error("Error loading bookmark status.")

                st.divider()
    else:
        st.info("No news found. Select sources and click Refresh to get started!")


def show_bookmarks():
    """Display user bookmarks"""
    st.header("🔖 Your Bookmarks")

    try:
        bookmarks = BookmarkModel.get_user_bookmarks(st.session_state.user_id)

        if bookmarks:
            for bookmark in bookmarks:
                with st.container():
                    st.markdown(
                        f"### [{bookmark['article_title']}]({bookmark['article_url']})")
                    st.caption(
                        f"📌 Saved on: {bookmark['saved_at'].strftime('%Y-%m-%d %H:%M')}")
                    if st.button("🗑️ Remove", key=f"remove_{bookmark['bookmark_id']}"):
                        try:
                            BookmarkModel.remove_bookmark(
                                bookmark['bookmark_id'], st.session_state.user_id)
                            st.rerun()
                        except Exception as e:
                            log_error(f"Error removing bookmark: {e}")
                            st.error("Failed to remove bookmark.")
                    st.divider()
        else:
            st.info("No bookmarks yet. Start saving articles you like!")
    except Exception as e:
        log_error(f"Error loading bookmarks: {e}")
        st.error("Failed to load bookmarks. Please try again.")


def show_activity():
    """Display user activity"""
    st.header("📈 Your Activity")

    try:
        activities = ActivityModel.get_user_activity(
            st.session_state.user_id, days=30)

        if activities:
            for activity in activities:
                icon = "🔐" if activity['activity_type'] == 'login' else "📰" if activity['activity_type'] == 'news_fetched' else "⭐"
                st.markdown(
                    f"{icon} **{activity['activity_type'].upper()}** - {activity['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                if activity.get('metadata'):
                    st.caption(f"Details: {activity['metadata']}")
        else:
            st.info("No activity recorded yet")
    except Exception as e:
        log_error(f"Error loading activity: {e}")
        st.error("Failed to load activity data.")


def show_profile():
    """Display user profile"""
    st.header("👤 Your Profile")

    try:
        user = AuthManager.get_current_user()
        if user:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Username", user['username'])
                st.metric("Email", user['email'])
                st.metric("Member Since",
                          user['created_at'].strftime('%Y-%m-%d'))
            with col2:
                if user.get('last_login'):
                    st.metric("Last Login", user['last_login'].strftime(
                        '%Y-%m-%d %H:%M'))
                st.metric("Account Status",
                          "✅ Active" if user['is_active'] else "❌ Inactive")

            st.divider()

            if st.button("🗑️ Delete Account", use_container_width=True, type="secondary"):
                if st.checkbox("I understand this is permanent"):
                    try:
                        UserModel.deactivate_user(st.session_state.user_id)
                        AuthManager.logout()
                    except Exception as e:
                        log_error(f"Error deleting account: {e}")
                        st.error(
                            "Failed to delete account. Please contact support.")
        else:
            st.error("Unable to load user profile.")
    except Exception as e:
        log_error(f"Error loading profile: {e}")
        st.error("Failed to load profile. Please try again.")


def main():
    """Main application entry point"""
    try:
        # Check authentication
        if not AuthManager.is_authenticated():
            show_landing_page()
        else:
            show_dashboard()
    except Exception as e:
        log_error(f"Application error: {e}")
        st.error("An unexpected error occurred. Please refresh the page.")
        if st.button("🔄 Refresh"):
            st.rerun()


if __name__ == "__main__":
    main()
