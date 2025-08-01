# Home.py
import streamlit as st
import requests
import xmltodict
import json
from datetime import datetime
from auth_new import show_auth_page, logout, save_preferences

# Check authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    show_auth_page()
    st.stop()

# Page configuration
st.set_page_config(page_title="📰 Personalized News", layout="wide")

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
if "refresh_news" not in st.session_state:
    st.session_state.refresh_news = False

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
        save_preferences(st.session_state.user_email, selected_sources, selected_category)
        st.session_state.selected_sources = selected_sources
        st.session_state.selected_category = selected_category
        st.success("Preferences saved!")
    
    st.divider()
    logout()

# Main area
st.title("📰 Personalized News Hub")

# Fetch news function with caching
def fetch_rss(url):
    # Check cache first (with 30-minute expiry)
    current_time = datetime.now().timestamp()
    if url in st.session_state.news_cache:
        cached_time, data = st.session_state.news_cache[url]
        if current_time - cached_time < 1800:  # 30 minutes
            return data
    
    # If not in cache or expired, fetch new data
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []
            
        data = xmltodict.parse(response.content)
        if "rss" not in data or "channel" not in data["rss"] or "item" not in data["rss"]["channel"]:
            return []
            
        items = data["rss"]["channel"]["item"]
        # Ensure items is a list (some feeds return a single item as dict)
        if isinstance(items, dict):
            items = [items]
            
        # Cache the result
        st.session_state.news_cache[url] = (current_time, items)
        return items
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        return []

# Function to get news
def get_news():
    st.session_state.news_items = []
    
    # From selected sources
    for src in st.session_state.selected_sources:
        items = fetch_rss(sources[src])
        for item in items[:5]:
            try:
                title = item.get("title", "No Title")
                link = item.get("link", "#")
                pubDate = item.get("pubDate", "Unknown Date")
                description = item.get("description", "No description available")
                
                # Clean description (remove HTML)
                if description and isinstance(description, str):
                    description = description.split('<')[0]
                
                st.session_state.news_items.append({
                    "title": title,
                    "link": link,
                    "pubDate": pubDate,
                    "description": description,
                    "source": src
                })
            except Exception as e:
                continue
    
    # From category
    items = fetch_rss(categories[st.session_state.selected_category])
    for item in items[:5]:
        try:
            title = item.get("title", "No Title")
            link = item.get("link", "#")
            pubDate = item.get("pubDate", "Unknown Date")
            description = item.get("description", "No description available")
            
            # Clean description (remove HTML)
            if description and isinstance(description, str):
                description = description.split('<')[0]
            
            st.session_state.news_items.append({
                "title": title,
                "link": link,
                "pubDate": pubDate,
                "description": description,
                "source": st.session_state.selected_category
            })
        except Exception as e:
            continue

# Check if we need to refresh news (from category click)
if st.session_state.refresh_news:
    get_news()
    st.session_state.refresh_news = False

# Bot response logic
def handle_bot_query(query):
    query = query.lower()
    
    # Check for greetings
    greetings = ["hi", "hello", "hey", "greetings"]
    if any(g in query for g in greetings):
        return "Hello! I'm your news assistant. You can ask me for news about specific categories like sports, politics, technology, or market updates."
    
    # Check for category matches
    matched_category = None
    for cat in categories:
        if cat.lower() in query:
            matched_category = cat
            break
    
    if matched_category:
        with st.spinner(f"Fetching {matched_category} news..."):
            items = fetch_rss(categories[matched_category])
            if items:
                response = f"Here are the latest {matched_category} news headlines:\n\n"
                for i, item in enumerate(items[:5]):
                    if i > 0:
                        response += "\n\n"
                    response += f"🔗 **[{item.get('title', 'No Title')}]({item.get('link', '#')})**"
                    description = item.get("description", "")
                    if description and isinstance(description, str):
                        description = description.split('<')[0]
                        if len(description) > 100:
                            description = description[:100] + "..."
                        response += f"\n{description}"
                return response
            else:
                return f"Sorry, I couldn't find any {matched_category} news right now. Please try again later."
    
    # Check for commands
    if "help" in query:
        return "I can help you get news from different categories. Try asking for:\n\n" + \
               "- Sports news\n" + \
               "- Politics updates\n" + \
               "- Technology news\n" + \
               "- Market information\n" + \
               "- Entertainment news\n" + \
               "- Health updates"
    
    if "clear" in query and "chat" in query:
        st.session_state.chat_history = []
        return "Chat history cleared!"
        
    # Generic response
    return "I can provide news about specific categories like Sports, Politics, Technology, Market, Entertainment, or Health. What type of news are you interested in?"

# Tabs for different views
tab1, tab2 = st.tabs(["📊 News Dashboard", "💬 News Assistant"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Today's Headlines")
        
        # Get news from selected sources and category
        if st.button("🔄 Refresh News"):
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
                        st.markdown(f"{description[:200]}..." if len(description) > 200 else description)
                    st.divider()
        else:
            st.info("Click 'Refresh News' to fetch the latest headlines")
    
    with col2:
        st.header("Quick Categories")
        
        # Create a button for each category
        for cat in categories:
            if st.button(f"📌 {cat}"):
                st.session_state.selected_category = cat
                st.session_state.refresh_news = True
                st.rerun()

with tab2:
    st.header("🤖 News Assistant")
    st.markdown("Ask questions about news topics or request specific news categories.")
    
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
