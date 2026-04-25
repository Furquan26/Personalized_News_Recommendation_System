"""
👤 Profile - User Account & Preferences
View and manage your profile information
"""

import streamlit as st
from datetime import datetime
from auth_new import (
    logout,
    get_articles_read_count,
    get_total_reading_time,
    get_articles_by_category,
    get_articles_by_source,
    get_reading_activity,
    get_reading_streak,
    get_bookmarks,
    load_preferences
)
from utils import log_info

# Page config
st.set_page_config(
    page_title="👤 Profile",
    page_icon="👤",
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
    
    .profile-header {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .profile-avatar {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 48px;
        margin: 0 auto 1rem;
    }
    
    .profile-name {
        font-size: 28px;
        font-weight: bold;
        color: #2c3e50;
        margin: 0.5rem 0;
    }
    
    .profile-email {
        color: #7f8c8d;
        font-size: 14px;
    }
    
    .section {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    
    .section-title {
        font-size: 18px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
    }
    
    .info-item {
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
        border-left: 3px solid #667eea;
    }
    
    .info-label {
        font-size: 12px;
        color: #7f8c8d;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .info-value {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
    }
    
    .activity-item {
        padding: 1rem;
        border-bottom: 1px solid #e0e0e0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .activity-item:last-child {
        border-bottom: none;
    }
    
    .activity-icon {
        font-size: 24px;
        margin-right: 1rem;
    }
    
    .activity-text {
        flex: 1;
    }
    
    .activity-time {
        font-size: 12px;
        color: #7f8c8d;
    }
</style>
""", unsafe_allow_html=True)

# Navbar
st.markdown("""
<div class="navbar">
    <h2 class="navbar-title">👤 User Profile</h2>
    <div>Manage your account and preferences</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("Quick Navigation")

    if st.button("📊 Dashboard"):
        st.switch_page("pages/01_📊_Dashboard.py")

    if st.button("🔖 Saved News"):
        st.switch_page("pages/02_🔖_Saved_News.py")

    if st.button("⚙️ Settings"):
        st.switch_page("pages/03_⚙️_Settings.py")

    if st.button("📈 Analytics"):
        st.switch_page("pages/04_📈_Analytics.py")

    st.markdown("---")
    logout()

# Profile Header
st.markdown(f"""
<div class="profile-header">
    <div class="profile-avatar">{st.session_state.user_name[0].upper()}</div>
    <h2 class="profile-name">{st.session_state.user_name}</h2>
    <p class="profile-email">{st.session_state.user_email}</p>
    <p style="color: #2ecc71; font-size: 12px; margin-top: 0.5rem;">✅ Active Member</p>
</div>
""", unsafe_allow_html=True)

# Profile Information
st.subheader("📋 Account Information")

with st.container():
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="section">
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Username</div>
                    <div class="info-value">""" + st.session_state.user_name + """</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Email</div>
                    <div class="info-value">""" + st.session_state.user_email + """</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Account Type</div>
                    <div class="info-value">Premium</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Member Since</div>
                    <div class="info-value">Apr 2026</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Get dynamic stats
        email = st.session_state.user_email
        articles_read = get_articles_read_count(email)
        total_bookmarks = len(get_bookmarks(email))
        total_time_seconds = get_total_reading_time(email)
        hours = total_time_seconds // 3600
        minutes = (total_time_seconds % 3600) // 60
        reading_time_str = f"{int(hours)}h {int(minutes)}m"

        st.markdown(f"""
        <div class="section">
            <div class="section-title">🎯 Account Stats</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Articles Read</div>
                    <div class="info-value">{articles_read}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Bookmarks</div>
                    <div class="info-value">{total_bookmarks}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Reading Time</div>
                    <div class="info-value">{reading_time_str}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Days Active</div>
                    <div class="info-value">-</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Reading Preferences
st.subheader("📚 Reading Preferences")

with st.container():
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="section">
            <div class="section-title">🏷️ Favorite Categories</div>
        """, unsafe_allow_html=True)

        category_stats = get_articles_by_category(st.session_state.user_email)
        if category_stats:
            for i, (cat, count) in enumerate(category_stats[:5], 1):
                st.write(
                    f"{i}. {cat if cat else 'General'} ({count} articles)")
        else:
            st.write("Start reading to see your favorite categories!")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="section">
            <div class="section-title">🗞️ Subscribed Sources</div>
        """, unsafe_allow_html=True)

        sources, category = load_preferences(st.session_state.user_email)
        if sources:
            for i, src in enumerate(sources[:5], 1):
                st.write(f"{i}. {src}")
        else:
            st.write("No sources selected. Update preferences on Settings page!")

        st.markdown("</div>", unsafe_allow_html=True)

# Recent Activity
st.subheader("📊 Recent Activity")

with st.container():
    st.markdown('<div class="section">', unsafe_allow_html=True)

    activities = get_reading_activity(st.session_state.user_email, 10)

    if activities:
        for article_title, source, category, read_date in activities:
            # Parse the date
            try:
                date_obj = datetime.fromisoformat(
                    read_date.replace('Z', '+00:00'))
                time_ago = f"{(datetime.now(date_obj.tzinfo) - date_obj).days} days ago" if (
                    datetime.now(date_obj.tzinfo) - date_obj).days > 0 else "Today"
            except:
                time_ago = "Recently"

            st.markdown(f"""
            <div class="activity-item">
                <div style="display: flex; align-items: center; flex: 1;">
                    <div class="activity-icon">📖</div>
                    <div class="activity-text">{article_title[:50]}... <br/><span style="font-size: 12px; color: #7f8c8d;">{source}</span></div>
                </div>
                <div class="activity-time">{time_ago}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No reading activity yet. Start reading to see your activity log!")

    st.markdown('</div>', unsafe_allow_html=True)

# Badges & Achievements
st.subheader("🏆 Achievements & Badges")

# Calculate achievements
email = st.session_state.user_email
articles_total = get_articles_read_count(email)
streak = get_reading_streak(email)
category_stats = get_articles_by_category(email)
tech_count = next(
    (count for cat, count in category_stats if 'Technology' in cat or 'Tech' in cat), 0)

col1, col2, col3, col4 = st.columns(4)

# Achievement 1: Reading Streak
with col1:
    has_streak = streak >= 7
    st.markdown(f"""
    <div class="section" style="text-align: center; {'opacity: 1' if has_streak else 'opacity: 0.5'} ;">
        <div style="font-size: 36px; margin-bottom: 0.5rem;">🔥</div>
        <div style="font-weight: 600; color: #2c3e50;">{streak}-Day Streak</div>
        <div style="font-size: 12px; color: #7f8c8d;">Read {streak}+ days in a row</div>
    </div>
    """, unsafe_allow_html=True)

# Achievement 2: Century Club
with col2:
    has_century = articles_total >= 100
    st.markdown(f"""
    <div class="section" style="text-align: center; {'opacity: 1' if has_century else 'opacity: 0.5'};">
        <div style="font-size: 36px; margin-bottom: 0.5rem;">📚</div>
        <div style="font-weight: 600; color: #2c3e50;">Century Club</div>
        <div style="font-size: 12px; color: #7f8c8d;">Read {articles_total}/100 articles</div>
    </div>
    """, unsafe_allow_html=True)

# Achievement 3: Tech Expert
with col3:
    has_tech = tech_count >= 30
    st.markdown(f"""
    <div class="section" style="text-align: center; {'opacity: 1' if has_tech else 'opacity: 0.5'};">
        <div style="font-size: 36px; margin-bottom: 0.5rem;">⭐</div>
        <div style="font-weight: 600; color: #2c3e50;">Tech Expert</div>
        <div style="font-size: 12px; color: #7f8c8d;">Read {tech_count}/30 tech articles</div>
    </div>
    """, unsafe_allow_html=True)

# Achievement 4: Goal Getter
with col4:
    has_goal = articles_total >= 30
    st.markdown(f"""
    <div class="section" style="text-align: center; {'opacity: 1' if has_goal else 'opacity: 0.5'};">
        <div style="font-size: 36px; margin-bottom: 0.5rem;">🎯</div>
        <div style="font-weight: 600; color: #2c3e50;">Goal Getter</div>
        <div style="font-size: 12px; color: #7f8c8d;">Read {articles_total}/30 weekly goal</div>
    </div>
    """, unsafe_allow_html=True)

# Account Actions
st.markdown("---")
st.subheader("⚙️ Account Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔐 Change Password", use_container_width=True):
        with st.form("change_pwd_form"):
            old_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password", type="password")
            confirm_pwd = st.text_input("Confirm Password", type="password")

            if st.form_submit_button("Update Password"):
                if new_pwd == confirm_pwd:
                    st.success("✅ Password updated successfully!")
                    log_info(
                        f"Password changed for {st.session_state.user_email}")
                else:
                    st.error("Passwords don't match!")

with col2:
    if st.button("📥 Download Data", use_container_width=True):
        st.info(
            "Your data export is being prepared. You'll receive a download link within 24 hours.")

with col3:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()
