"""
📊 Dashboard - Personalized News Feed
Main news feed with advanced filtering and search
"""

import streamlit as st
import requests
import xmltodict
from datetime import datetime
from config import config
from auth_new import (
    logout,
    save_preferences,
    get_bookmarks,
    add_bookmark,
    log_article_read,
    get_articles_read_count,
    get_favorite_topic
)
from utils import (
    log_info,
    log_error,
    cached,
    clean_html,
    truncate_text,
    format_date,
    get_time_ago
)

# Page config
st.set_page_config(
    page_title="📊 Dashboard - News Feed",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first!")
    st.stop()

# Custom CSS
st.markdown("""
<style>
    :root {
        --primary: #667eea;
        --secondary: #764ba2;
        --success: #2ecc71;
        --warning: #f39c12;
        --danger: #e74c3c;
        --light: #ecf0f1;
        --dark: #2c3e50;
    }
    
    .navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .navbar-title {
        font-size: 24px;
        font-weight: bold;
        margin: 0;
    }
    
    .news-card {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        border: 1px solid #e0e0e0;
    }
    
    .news-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        border-color: #667eea;
    }
    
    .news-card-header {
        padding: 1.5rem;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .news-card-title {
        font-size: 18px;
        font-weight: 600;
        color: #2c3e50;
        margin: 0 0 0.5rem 0;
        line-height: 1.4;
    }
    
    .news-card-meta {
        display: flex;
        gap: 1rem;
        font-size: 12px;
        color: #7f8c8d;
        margin-top: 0.5rem;
    }
    
    .news-card-meta-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    .news-card-content {
        padding: 1.5rem;
        background: #fafafa;
    }
    
    .news-card-description {
        color: #555;
        line-height: 1.6;
        font-size: 14px;
    }
    
    .news-card-footer {
        display: flex;
        gap: 0.5rem;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.5rem;
        background: white;
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .badge-primary {
        background: #e3f2fd;
        color: #1976d2;
    }
    
    .badge-success {
        background: #e8f5e9;
        color: #388e3c;
    }
    
    .filter-panel {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        border: 1px solid #e0e0e0;
    }
    
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        border-left: 4px solid #667eea;
    }
    
    .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: #667eea;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 12px;
        color: #7f8c8d;
        text-transform: uppercase;
        font-weight: 600;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .reading-time {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        color: #e67e22;
        font-weight: 500;
    }
    
    .source-badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Data structures
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

# Initialize session state
if "dashboard_filters" not in st.session_state:
    st.session_state.dashboard_filters = {
        "sources": st.session_state.selected_sources or [],
        "category": st.session_state.selected_category or "General",
        "search": "",
        "sort_by": "recent",
        "items_per_page": 10
    }

# Navbar
st.markdown("""
<div class="navbar">
    <h2 class="navbar-title">📊 News Dashboard</h2>
    <div>Your personalized news feed, updated in real-time</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("👤 User Profile")
    st.write(f"**Name:** {st.session_state.user_name}")
    st.write(f"**Email:** {st.session_state.user_email}")

    st.markdown("---")
    st.subheader("🎯 Filter News")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.dashboard_filters["sort_by"] = st.selectbox(
            "Sort by",
            ["recent", "trending", "oldest"],
            index=["recent", "trending", "oldest"].index(
                st.session_state.dashboard_filters.get("sort_by", "recent"))
        )

    with col2:
        st.session_state.dashboard_filters["items_per_page"] = st.selectbox(
            "Items per page",
            [5, 10, 20, 50],
            index=[5, 10, 20, 50].index(
                st.session_state.dashboard_filters.get("items_per_page", 10))
        )

    st.session_state.dashboard_filters["search"] = st.text_input(
        "🔍 Search news",
        placeholder="Enter keywords..."
    )

    st.markdown("---")
    st.subheader("📂 Categories")

    selected_category = st.selectbox(
        "Choose category",
        list(categories.keys()),
        index=list(categories.keys()).index(
            st.session_state.dashboard_filters["category"])
    )
    st.session_state.dashboard_filters["category"] = selected_category

    st.markdown("---")
    st.subheader("📢 News Sources")

    selected_sources = st.multiselect(
        "Choose sources",
        list(sources.keys()),
        default=st.session_state.dashboard_filters["sources"]
    )
    st.session_state.dashboard_filters["sources"] = selected_sources

    if st.button("💾 Save Preferences", use_container_width=True):
        save_preferences(st.session_state.user_email,
                         selected_sources, selected_category)
        st.session_state.selected_sources = selected_sources
        st.session_state.selected_category = selected_category
        st.success("✅ Preferences saved!")

    st.markdown("---")
    logout()

# Stats row
email = st.session_state.user_email
articles_read = get_articles_read_count(email)
bookmarks = len(get_bookmarks(email))
favorite_topic, _ = get_favorite_topic(email)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-label">📰 Total Articles</div>
        <div class="stat-value">2,847+</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">🔖 Bookmarks</div>
        <div class="stat-value">{bookmarks}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">👁️ Articles Read</div>
        <div class="stat-value">{articles_read}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">⭐ Top Category</div>
        <div class="stat-value">{favorite_topic if favorite_topic else 'N/A'}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Main content
# Fetch news function with caching


@cached(ttl_seconds=config.RSS_CACHE_DURATION)
def fetch_rss(url):
    """Fetch RSS feed with caching"""
    try:
        log_info(f"Fetching RSS from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(
            url, timeout=config.RSS_TIMEOUT, headers=headers)
        if response.status_code != 200:
            return []

        data = xmltodict.parse(response.content)
        if "rss" not in data or "channel" not in data["rss"] or "item" not in data["rss"]["channel"]:
            return []

        items = data["rss"]["channel"]["item"]
        if isinstance(items, dict):
            items = [items]

        log_info(f"Fetched {len(items)} items")
        return items
    except Exception as e:
        log_error(f"Error fetching RSS: {str(e)}")
        return []

# Get news based on filters


def get_filtered_news():
    news_items = []
    filters = st.session_state.dashboard_filters

    # Fetch from selected sources or category
    fetch_urls = []
    if filters["sources"]:
        for src in filters["sources"]:
            fetch_urls.append((src, sources.get(src)))
    else:
        fetch_urls.append(
            (filters["category"], categories.get(filters["category"])))

    for source_name, url in fetch_urls:
        if not url:
            continue
        items = fetch_rss(url)
        for item in (items or [])[:filters["items_per_page"]]:
            try:
                title = item.get("title", "No Title")
                link = item.get("link", "#")
                pubDate = item.get("pubDate", "Unknown Date")
                description = item.get("description", "")

                # Filter by search query
                if filters["search"] and filters["search"].lower() not in title.lower():
                    continue

                if description and isinstance(description, str):
                    description = clean_html(description)
                    description = truncate_text(description, max_length=250)

                news_items.append({
                    "title": title,
                    "link": link,
                    "pubDate": format_date(pubDate),
                    "description": description,
                    "source": source_name,
                    "time_ago": get_time_ago(datetime.now())
                })
            except Exception as e:
                log_error(f"Error processing item: {str(e)}")
                continue

    return sorted(news_items, key=lambda x: x["pubDate"], reverse=True)[:filters["items_per_page"]]


# Display news
st.subheader(f"📚 Latest {st.session_state.dashboard_filters['category']} News")

with st.spinner("Loading news..."):
    news_items = get_filtered_news()

if news_items:
    for idx, news in enumerate(news_items):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"""
            <div class="news-card">
                <div class="news-card-header">
                    <h3 class="news-card-title">{news['title']}</h3>
                    <div class="news-card-meta">
                        <div class="news-card-meta-item">
                            <span class="source-badge">{news['source']}</span>
                        </div>
                        <div class="news-card-meta-item">
                            📅 {news['pubDate']}
                        </div>
                        <div class="news-card-meta-item">
                            ⏱️ {news['time_ago']}
                        </div>
                    </div>
                </div>
                <div class="news-card-content">
                    <p class="news-card-description">{news['description']}</p>
                </div>
                <div class="news-card-footer">
                    <a href="{news['link']}" target="_blank" class="btn-primary">Read Full Article →</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Mark as Read and Bookmark buttons
            col_read, col_save = st.columns(2)
            with col_read:
                if st.button(f"✅ Read", key=f"read_{idx}", help="Mark as read"):
                    log_article_read(
                        email=st.session_state.user_email,
                        article_title=news['title'],
                        article_link=news['link'],
                        source=news['source'],
                        category=st.session_state.dashboard_filters['category'],
                        reading_time_seconds=300  # Default 5 minutes
                    )
                    st.success("Marked as read!")

            with col_save:
                if st.button(f"🔖", key=f"save_{idx}", help="Save bookmark"):
                    add_bookmark(
                        email=st.session_state.user_email,
                        title=news['title'],
                        link=news['link'],
                        source=news['source']
                    )
                    st.success("Bookmarked!")
else:
    st.info("📭 No articles found. Try adjusting your filters!")
