"""
🔖 Saved News - Bookmark Management
View, organize, and manage your saved articles
"""

import streamlit as st
from datetime import datetime
from auth_new import logout, get_bookmarks, delete_bookmark, add_bookmark
from utils import log_info, truncate_text

# Page config
st.set_page_config(
    page_title="🔖 Saved News",
    page_icon="📚",
    layout="wide"
)

# Check authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first!")
    st.stop()

# Custom CSS
st.markdown("""
<style>
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
    
    .collection-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .collection-card:hover {
        transform: translateX(4px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
    }
    
    .bookmark-item {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #2ecc71;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .bookmark-title {
        font-weight: 600;
        color: #2c3e50;
        flex: 1;
    }
    
    .bookmark-meta {
        font-size: 12px;
        color: #7f8c8d;
        margin-top: 0.25rem;
    }
    
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #7f8c8d;
    }
    
    .empty-state-icon {
        font-size: 48px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Navbar
st.markdown("""
<div class="navbar">
    <h2 class="navbar-title">🔖 Saved News</h2>
    <div>Your personal news library</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("👤 User Profile")
    st.write(f"**Name:** {st.session_state.user_name}")

    st.markdown("---")
    view_type = st.radio(
        "View Type", ["All Bookmarks", "By Source", "By Date"])

    if st.button("🏠 Back to Dashboard"):
        st.switch_page("pages/01_📊_Dashboard.py")

    logout()

# Get bookmarks
bookmarks = get_bookmarks(st.session_state.user_email)

# Main content
st.subheader(f"📚 Your Bookmarks ({len(bookmarks)} articles)")

if not bookmarks:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">📭</div>
        <h3>No bookmarks yet</h3>
        <p>Start saving articles from the Dashboard to build your personal news library!</p>
    </div>
    """, unsafe_allow_html=True)
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Search bookmarks...",
                               placeholder="Search by title or source...")
    with col2:
        sort_by = st.selectbox("Sort by", ["Newest", "Oldest", "A-Z"])

    st.markdown("---")

    # Filter and display bookmarks
    filtered_bookmarks = bookmarks
    if search:
        filtered_bookmarks = [b for b in bookmarks if search.lower(
        ) in b[0].lower() or search.lower() in b[2].lower()]

    # Sort
    if sort_by == "A-Z":
        filtered_bookmarks = sorted(filtered_bookmarks, key=lambda x: x[0])
    elif sort_by == "Oldest":
        filtered_bookmarks = sorted(filtered_bookmarks, key=lambda x: x[3])

    for i, (title, link, source, date) in enumerate(filtered_bookmarks):
        col1, col2, col3 = st.columns([1, 0.15, 0.1])

        with col1:
            st.markdown(f"""
            <div class="bookmark-item">
                <div>
                    <div class="bookmark-title">{truncate_text(title, max_length=100)}</div>
                    <div class="bookmark-meta">🏢 {source} • 📅 {date}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("📖", key=f"read_{i}", help="Read article"):
                st.markdown(
                    f'<a href="{link}" target="_blank">Read</a>', unsafe_allow_html=True)

        with col3:
            if st.button("❌", key=f"del_{i}", help="Delete bookmark"):
                delete_bookmark(st.session_state.user_email, title, link)
                st.success("Removed from bookmarks!")
                st.rerun()

    st.markdown("---")

    # Additional options
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Export Bookmarks as CSV"):
            import csv
            csv_data = "Title,Source,Link,Date\n"
            for title, link, source, date in bookmarks:
                csv_data += f'"{title}","{source}","{link}","{date}"\n'
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="bookmarks.csv",
                mime="text/csv"
            )

    with col2:
        if st.button("🗑️ Clear All Bookmarks"):
            if st.checkbox("Are you sure?"):
                for title, link, _, _ in bookmarks:
                    delete_bookmark(st.session_state.user_email, title, link)
                st.success("All bookmarks cleared!")
                st.rerun()
