# Home.py
import streamlit as st
import requests
import xmltodict
import json
import csv
from datetime import datetime
from config import config
from auth_new import show_auth_page, logout, save_preferences, restore_session_from_query, add_bookmark, get_bookmarks, delete_bookmark
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

# Page configuration - MUST BE FIRST Streamlit command
st.set_page_config(page_title="📰 Personalized News", layout="wide")

# Initialize logger at app startup
logger = setup_logger(log_level="INFO")
log_info("News Recommendation System started")

# Restore authentication from query parameters if available
restore_session_from_query()

# Check authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    show_auth_page()
    st.stop()

# Source and category mappings
sources = {
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Dainik Bhaskar": "https://www.bhaskar.com/rss-v1--category-1061.xml",
    "ABP Majha": "https://marathi.abplive.com/rss/featured-articles.xml",
    "Dainik Jagran": "https://www.jagran.com/rss/news/national.xml",
    "Aaj Tak": "https://www.aajtak.in/rss",
    "India Today": "https://www.indiatoday.in/rss/home"
}

categories = {
    "General": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "Sports": "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms",
    "Politics": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Technology": "https://www.indiatoday.in/technology/rss",
    "Market": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Entertainment": "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms",
    "Health": "https://www.indiatoday.in/health/rss"
}

# Initialize session state variables if not present
if "selected_sources" not in st.session_state:
    st.session_state.selected_sources = []
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "General"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "news_cache" not in st.session_state:
    st.session_state.news_cache = {}
# View and mode control
if "main_view" not in st.session_state:
    st.session_state.main_view = "📊 News Dashboard"
if "show_only_category" not in st.session_state:
    st.session_state.show_only_category = False

# Sidebar with user info and preferences
with st.sidebar:
    st.markdown(f"### Welcome, {st.session_state.user_name}!")
    st.divider()

    st.header("📰 News Preferences")

    # Source selection
    selected_sources = st.multiselect(
        "Select News Sources",
        list(sources.keys()),
        default=st.session_state.selected_sources
    )

    # Category selection
    selected_category = st.selectbox(
        "Select News Category",
        list(categories.keys()),
        index=list(categories.keys()).index(st.session_state.selected_category)
        if st.session_state.selected_category in categories else 0
    )

    # Save preferences button
    if st.button("💾 Save Preferences"):
        save_preferences(st.session_state.user_email,
                         selected_sources, selected_category)
        st.session_state.selected_sources = selected_sources
        st.session_state.selected_category = selected_category
        st.success("Preferences saved!")

    st.divider()

    # Search functionality
    st.header("🔍 Search News")
    search_query = st.text_input(
        "Search headlines", placeholder="Enter keyword...")
    if search_query:
        if "news_items" in st.session_state and st.session_state.news_items:
            filtered_news = [
                news for news in st.session_state.news_items
                if search_query.lower() in news['title'].lower() or
                search_query.lower() in news.get('description', '').lower()
            ]
            if filtered_news:
                st.success(f"Found {len(filtered_news)} articles")
                if "filtered_news" not in st.session_state:
                    st.session_state.filtered_news = []
                st.session_state.filtered_news = filtered_news
            else:
                st.warning("No matching articles found")

    st.divider()

    # Bookmarks section
    st.header("🔖 My Bookmarks")
    bookmarks = get_bookmarks(st.session_state.user_email)
    if bookmarks:
        st.write(f"Total bookmarks: {len(bookmarks)}")
        for i, (title, link, source, saved_date) in enumerate(bookmarks[:5]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.caption(f"📌 [{title[:30]}...](../{link})")
            with col2:
                if st.button("❌", key=f"del_bookmark_{i}"):
                    if delete_bookmark(st.session_state.user_email, title, link):
                        st.success("Bookmark removed!")
                        st.rerun()
    else:
        st.info("No bookmarks yet")

    st.divider()

    # Export functionality
    st.header("📤 Export News")
    if "news_items" in st.session_state and st.session_state.news_items:
        export_format = st.radio("Choose format", ["JSON", "CSV"])
        if export_format == "JSON":
            json_data = json.dumps(st.session_state.news_items, indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"news_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            csv_rows = [["Title", "Link", "Source", "Date", "Description"]]
            for news in st.session_state.news_items:
                csv_rows.append([
                    news['title'], news['link'], news['source'],
                    news['pubDate'], news.get('description', '')
                ])
            csv_string = "\n".join([",".join(row) for row in csv_rows])
            st.download_button(
                label="📥 Download as CSV",
                data=csv_string,
                file_name=f"news_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    st.divider()
    logout()

# Main area
st.title("📰 Personalized News Hub")

# Fetch news function with caching - using @cached decorator for performance
@cached(ttl_seconds=config.RSS_CACHE_DURATION)
def fetch_rss(url):
    """Fetch RSS feed with caching and error handling"""
    try:
        log_info(f"Fetching RSS from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(
            url, timeout=config.RSS_TIMEOUT, headers=headers)
        if response.status_code != 200:
            log_error(f"Failed to fetch {url}: HTTP {response.status_code}")
            return []

        data = xmltodict.parse(response.content)
        if "rss" not in data or "channel" not in data["rss"] or "item" not in data["rss"]["channel"]:
            return []

        items = data["rss"]["channel"]["item"]
        # Ensure items is a list (some feeds return a single item as dict)
        if isinstance(items, dict):
            items = [items]

        log_info(f"Successfully fetched {len(items)} items from {url}")
        return items
    except Exception as e:
        log_error(f"Error fetching RSS from {url}: {str(e)}")
        st.error(f"Error fetching news: {str(e)}")
        return []

# Function to get news
def get_news():
    st.session_state.news_items = []

    # If we're in category-only mode (triggered by Quick Categories), fetch only that category
    if st.session_state.get("show_only_category", False):
        items = fetch_rss(categories[st.session_state.selected_category])
        for item in (items or [])[:10]:
            try:
                title = item.get("title", "No Title")
                link = item.get("link", "#")
                pubDate = item.get("pubDate", "Unknown Date")
                description = item.get(
                    "description", "No description available")

                # Clean and truncate description using utility functions
                if description and isinstance(description, str):
                    description = clean_html(description)
                    description = truncate_text(description, max_length=200)

                st.session_state.news_items.append({
                    "title": title,
                    "link": link,
                    "pubDate": format_date(pubDate),
                    "description": description,
                    "source": st.session_state.selected_category
                })
            except Exception as e:
                log_error(f"Error processing news item: {str(e)}")
                continue
        return

    # Default: combine selected sources and the chosen category
    for src in st.session_state.selected_sources:
        items = fetch_rss(sources[src])
        for item in (items or [])[:5]:
            try:
                title = item.get("title", "No Title")
                link = item.get("link", "#")
                pubDate = item.get("pubDate", "Unknown Date")
                description = item.get(
                    "description", "No description available")

                # Clean and truncate description
                if description and isinstance(description, str):
                    description = clean_html(description)
                    description = truncate_text(description, max_length=200)

                st.session_state.news_items.append({
                    "title": title,
                    "link": link,
                    "pubDate": format_date(pubDate),
                    "description": description,
                    "source": src
                })
            except Exception as e:
                log_error(f"Error processing news item: {str(e)}")
                continue

    # From category
    items = fetch_rss(categories[st.session_state.selected_category])
    for item in (items or [])[:5]:
        try:
            title = item.get("title", "No Title")
            link = item.get("link", "#")
            pubDate = item.get("pubDate", "Unknown Date")
            description = item.get("description", "No description available")

            # Clean and truncate description
            if description and isinstance(description, str):
                description = clean_html(description)
                description = truncate_text(description, max_length=200)

            st.session_state.news_items.append({
                "title": title,
                "link": link,
                "pubDate": format_date(pubDate),
                "description": description,
                "source": st.session_state.selected_category
            })
        except Exception as e:
            log_error(f"Error processing news item: {str(e)}")
            continue


# Bot response logic
def handle_bot_query(query):
    query = query.lower()

    # Check for greetings
    greetings = ["hi", "hello", "hey", "greetings"]
    if any(g in query for g in greetings):
        log_info(f"User greeting: {query}")
        return "Hello! I'm your news assistant. You can ask me for news about specific categories like sports, politics, technology, or market updates."

    # Check for category matches
    matched_category = None
    for cat in categories:
        if cat.lower() in query:
            matched_category = cat
            break

    if matched_category:
        log_info(f"Fetching news for category: {matched_category}")
        with st.spinner(f"Fetching {matched_category} news..."):
            items = fetch_rss(categories[matched_category])
            if items:
                response = f"Here are the latest {matched_category} news headlines:\n\n"
                for i, item in enumerate(items[:5]):
                    if i > 0:
                        response += "\n\n"
                    title = item.get('title', 'No Title')
                    link = item.get('link', '#')
                    response += f"🔗 **[{truncate_text(title, max_length=100)}]({link})**"
                    description = item.get("description", "")
                    if description and isinstance(description, str):
                        description = clean_html(description)
                        description = truncate_text(description, max_length=150)
                        response += f"\n{description}"
                return response
            else:
                log_error(f"No news found for category: {matched_category}")
                return f"Sorry, I couldn't find any {matched_category} news right now. Please try again later."

    # Check for commands
    if "help" in query:
        log_info("User requested help")
        return "I can help you get news from different categories. Try asking for:\n\n" + \
               "- Sports news\n" + \
               "- Politics updates\n" + \
               "- Technology news\n" + \
               "- Market information\n" + \
               "- Entertainment news\n" + \
               "- Health updates"

    if "clear" in query and "chat" in query:
        st.session_state.chat_history = []
        log_info("Chat history cleared")
        return "Chat history cleared!"

    # Generic response
    log_info(f"Generic query: {query}")
    return "I can provide news about specific categories like Sports, Politics, Technology, Market, Entertainment, or Health. What type of news are you interested in?"


# View selector for different views (allows programmatic switching)
st.session_state.main_view = st.radio(
    "",
    ["📊 News Dashboard", "💬 News Assistant"],
    index=0 if st.session_state.get(
        "main_view", "📊 News Dashboard") == "📊 News Dashboard" else 1,
    horizontal=True,
    key="main_view_radio",
)

if st.session_state.get("main_view", "📊 News Dashboard") == "📊 News Dashboard":
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Today's Headlines")

        # Get news from selected sources and category
        if st.button("🔄 Refresh News"):
            # when user manually refreshes, show combined view
            st.session_state.show_only_category = False
            with st.spinner("Fetching latest news..."):
                get_news()

        # Display news items
        if "news_items" in st.session_state and st.session_state.news_items:
            for i, news in enumerate(st.session_state.news_items):
                with st.container():
                    st.markdown(f"### [{news['title']}]({news['link']})")
                    st.caption(f"Source: {news['source']} | {news['pubDate']}")

                    # Safely handle description - check if it exists and is not None
                    description = news.get('description')
                    if description:
                        st.markdown(f"{description[:200]}..." if len(
                            description) > 200 else description)
                    st.divider()
        else:
            st.info("Click 'Refresh News' to fetch the latest headlines")

    with col2:
        st.header("Quick Categories")

        # Create a button for each category
        for cat in categories:
            if st.button(f"📌 {cat}"):
                # Set selected category, switch to dashboard and show only that category
                st.session_state.selected_category = cat
                st.session_state.show_only_category = True
                st.session_state.main_view = "📊 News Dashboard"
                with st.spinner(f"Fetching {cat} news..."):
                    get_news()

else:
    st.header("🤖 News Assistant")
    st.markdown(
        "Ask questions about news topics or request specific news categories.")

    # Display chat history
    for i, (role, message) in enumerate(st.session_state.chat_history):
        with st.chat_message(role):
            st.markdown(message)

# Chat input outside of tabs to avoid StreamlitAPIException
user_input = st.chat_input("Ask me about news topics or categories...")

# Handle chat input
if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    reply = handle_bot_query(user_input)
    st.session_state.chat_history.append(("assistant", reply))
    with st.chat_message("assistant"):
        st.markdown(reply)

    # Keep history limited to last 10 exchanges
    if len(st.session_state.chat_history) > 20:
        st.session_state.chat_history = st.session_state.chat_history[-20:]

    st.rerun()
