# News.py
import streamlit as st
import requests
import xmltodict
import time
from datetime import datetime
from auth_new import show_auth_page, logout

# Check authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    show_auth_page()
    st.stop()

# Page configuration
st.set_page_config(page_title="🗞️ News Results", layout="wide")

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
    "General": [{"name": "Times of India", "url": sources["Times of India"]}],
    "Sports": [{"name": "TOI Sports", "url": "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms"}],
    "Politics": [{"name": "The Hindu Politics", "url": sources["The Hindu"]}],
    "Technology": [{"name": "India Today Tech", "url": "https://www.indiatoday.in/technology/rss"}],
    "Market": [{"name": "Economic Times Market", "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"}],
    "Entertainment": [{"name": "TOI Entertainment", "url": "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms"}], 
    "Health": [{"name": "India Today Health", "url": "https://www.indiatoday.in/health/rss"}]
}

# Initialize session state for news filters if not present
if "news_filters" not in st.session_state:
    st.session_state.news_filters = {
        "search_term": "",
        "sort_by": "relevance",
        "max_items": 20
    }

# Sidebar with user info and filters
with st.sidebar:
    st.markdown(f"### Welcome, {st.session_state.user_name}!")
    st.divider()
    
    st.header("🔍 News Filters")
    
    # Search filter
    st.session_state.news_filters["search_term"] = st.text_input(
        "Search in headlines", 
        value=st.session_state.news_filters.get("search_term", "")
    )
    
    # Sort options
    st.session_state.news_filters["sort_by"] = st.radio(
        "Sort by",
        ["relevance", "newest"],
        index=0 if st.session_state.news_filters.get("sort_by") == "relevance" else 1
    )
    
    # Number of results
    st.session_state.news_filters["max_items"] = st.slider(
        "Max results", 
        min_value=5, 
        max_value=50, 
        value=st.session_state.news_filters.get("max_items", 20)
    )
    
    st.divider()
    logout()

# Main content
st.title("🗞️ News Results")

# Function to fetch and process RSS feeds
def fetch_news(feed_list):
    news_items = []
    progress_text = "Fetching news from selected sources..."
    progress_bar = st.progress(0)
    
    for i, feed in enumerate(feed_list):
        try:
            resp = requests.get(feed["url"], timeout=10)
            if resp.status_code == 200:
                data = xmltodict.parse(resp.content)
                
                if "rss" in data and "channel" in data["rss"] and "item" in data["rss"]["channel"]:
                    items = data["rss"]["channel"]["item"]
                    
                    # Ensure items is a list
                    if isinstance(items, dict):
                        items = [items]
                    
                    for item in items:
                        # Get basic info
                        title = item.get("title", "No Title")
                        link = item.get("link", "#")
                        
                        # Skip if doesn't match search term
                        search_term = st.session_state.news_filters["search_term"].lower()
                        if search_term and search_term not in title.lower():
                            continue
                        
                        # Get additional details
                        pubDate = item.get("pubDate", "")
                        description = item.get("description", "No description available")
                        
                        # Clean description (remove HTML)
                        if description and isinstance(description, str):
                            description = description.split('<')[0]
                        
                        # Parse date for sorting
                        try:
                            date_obj = datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %z")
                            timestamp = date_obj.timestamp()
                        except:
                            timestamp = 0
                        
                        news_items.append({
                            "title": title,
                            "link": link,
                            "pubDate": pubDate,
                            "description": description,
                            "source": feed["name"],
                            "timestamp": timestamp
                        })
            
            # Update progress bar
            progress_bar.progress((i + 1) / len(feed_list))
            time.sleep(0.1)  # Small delay for visual feedback
            
        except Exception as e:
            st.warning(f"Failed to load from {feed['name']}: {str(e)}")
    
    progress_bar.empty()
    
    # Apply sorting
    if st.session_state.news_filters["sort_by"] == "newest":
        news_items.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return news_items[:st.session_state.news_filters["max_items"]]

# Check if we have sources selected
if "selected_sources" not in st.session_state or not st.session_state.selected_sources:
    st.warning("Please go to the Home page and select news sources.")
    
    if st.button("Go to Home"):
        st.switch_page("Home.py")
    st.stop()

# Create list of feeds to fetch
feeds_to_fetch = []

# Add selected sources
for src in st.session_state.selected_sources:
    feeds_to_fetch.append({"name": src, "url": sources[src]})

# Add selected category
if "selected_category" in st.session_state and st.session_state.selected_category in categories:
    feeds_to_fetch.extend(categories[st.session_state.selected_category])

# Fetch button
if st.button("🔄 Refresh News"):
    with st.spinner("Fetching latest news..."):
        news = fetch_news(feeds_to_fetch)
        st.session_state.current_news = news

# Display results
if "current_news" in st.session_state and st.session_state.current_news:
    news = st.session_state.current_news
    
    # Display in a grid layout
    st.markdown(f"### Found {len(news)} news items")
    
    # Create columns for the grid
    col1, col2 = st.columns(2)
    
    for i, item in enumerate(news):
        col = col1 if i % 2 == 0 else col2
        
        with col:
            with st.container():
                st.markdown(f"### [{item['title']}]({item['link']})")
                st.caption(f"Source: {item['source']} | {item['pubDate']}")
                
                # Show description if available (safely check if None)
                description = item.get('description')
                if description:
                    st.markdown(description[:150] + "..." if len(description) > 150 else description)
                
                st.divider()
else:
    st.info("Click 'Refresh News' to fetch the latest headlines.")
