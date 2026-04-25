"""
📈 Analytics - Reading Statistics & Insights
Track your reading habits and preferences
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from utils import log_info
from auth_new import (
    get_articles_read_count,
    get_total_reading_time,
    get_articles_by_category,
    get_articles_by_source,
    get_daily_reading_stats,
    get_hourly_pattern,

    get_favorite_topic,
    get_reading_streak,
    get_reading_activity,
    get_bookmarks
)

# Page config
st.set_page_config(
    page_title="📈 Analytics",
    page_icon="📊",
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
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-top: 4px solid #667eea;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #667eea;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 14px;
        color: #7f8c8d;
        text-transform: uppercase;
        font-weight: 600;
    }
    
    .metric-change {
        font-size: 12px;
        color: #2ecc71;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Navbar
st.markdown("""
<div class="navbar">
    <h2 class="navbar-title">📈 Your Analytics</h2>
    <div>Track your reading habits and preferences</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("👤 User Profile")
    st.write(f"**Name:** {st.session_state.user_name}")

    st.markdown("---")
    time_period = st.selectbox(
        "Time Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
    )

    st.markdown("---")
    if st.button("🏠 Back to Dashboard"):
        st.switch_page("pages/01_📊_Dashboard.py")

    from auth_new import logout
    logout()

# Convert time period to days
time_periods = {
    "Last 7 Days": 7,
    "Last 30 Days": 30,
    "Last 90 Days": 90,
    "All Time": None
}
days_filter = time_periods[time_period]

# Fetch real data
try:
    email = st.session_state.user_email
    articles_read = get_articles_read_count(email, days_filter)
    total_time_seconds = get_total_reading_time(email, days_filter)
    total_bookmarks = len(get_bookmarks(email))
    favorite_topic, topic_count = get_favorite_topic(email, days_filter)
except Exception as e:
    log_info(f"Error fetching analytics data: {e}")
    st.error("Failed to load analytics data. Please try again.")
    articles_read = 0
    total_time_seconds = 0
    total_bookmarks = 0
    favorite_topic = "N/A"
    topic_count = 0

# Convert seconds to hours and minutes
hours = total_time_seconds // 3600
minutes = (total_time_seconds % 3600) // 60
reading_time_str = f"{int(hours)}h {int(minutes)}m"

# Calculate percentage
topic_percentage = int((topic_count / max(articles_read, 1)) * 100)

# Main metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">📖 Articles Read</div>
        <div class="metric-value">{articles_read}</div>
        <div class="metric-change">📊 {time_period}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">⏱️ Reading Time</div>
        <div class="metric-value">{reading_time_str}</div>
        <div class="metric-change">⏰ {time_period}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🔖 Bookmarks</div>
        <div class="metric-value">{total_bookmarks}</div>
        <div class="metric-change">📌 Total</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">⭐ Favorite Topic</div>
        <div class="metric-value">{favorite_topic}</div>
        <div class="metric-change">{topic_percentage}% of reads</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Get visualization data
try:
    daily_stats = get_daily_reading_stats(
        email, 30 if not days_filter else min(days_filter, 30))
    category_stats = get_articles_by_category(email, days_filter)
    hourly_stats = get_hourly_pattern(email, days_filter)
    reading_activity = get_reading_activity(email, 10)
except Exception as e:
    log_info(f"Error fetching visualization data: {e}")
    daily_stats = []
    category_stats = []
    hourly_stats = []
    reading_activity = []

# Sample data for visualizations
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Overview", "📚 Reading Patterns", "🏆 Top Topics", "📅 Timeline"])

with tab1:
    st.subheader("Reading Activity Overview")

    # Convert daily stats to DataFrame
    if daily_stats:
        df_daily = pd.DataFrame(daily_stats, columns=[
                                'Date', 'Articles', 'Total Time'])
        df_daily['Date'] = pd.to_datetime(df_daily['Date'])
        df_daily = df_daily.sort_values('Date')
        df_daily['Reading Time (mins)'] = df_daily['Total Time'].fillna(
            0) // 60

        col1, col2 = st.columns(2)

        with col1:
            if not df_daily.empty:
                fig_articles = px.bar(
                    df_daily,
                    x='Date',
                    y='Articles',
                    title='Articles Read Per Day',
                    color_discrete_sequence=['#667eea']
                )
                fig_articles.update_layout(height=400)
                st.plotly_chart(fig_articles, use_container_width=True)
            else:
                st.info("No reading activity yet. Start reading to see stats!")

        with col2:
            if not df_daily.empty:
                fig_time = px.line(
                    df_daily,
                    x='Date',
                    y='Reading Time (mins)',
                    title='Daily Reading Time',
                    color_discrete_sequence=['#764ba2'],
                    markers=True
                )
                fig_time.update_layout(height=400)
                st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("No reading activity yet. Start reading to see stats!")

with tab2:
    st.subheader("Reading Patterns & Insights")

    col1, col2 = st.columns(2)

    with col1:
        if hourly_stats:
            df_hourly = pd.DataFrame(
                hourly_stats, columns=['Hour', 'Articles'])
            all_hours = list(range(24))
            df_hourly_full = pd.DataFrame({'Hour': all_hours})
            df_hourly_full = df_hourly_full.merge(
                df_hourly, on='Hour', how='left')
            df_hourly_full['Articles'] = df_hourly_full['Articles'].fillna(0)
            df_hourly_full['Time'] = df_hourly_full['Hour'].apply(
                lambda h: f'{h:02d}:00')

            fig_time_dist = px.pie(
                df_hourly_full[df_hourly_full['Articles'] > 0],
                values='Articles',
                names='Time',
                title='Reading Time Distribution',
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig_time_dist.update_layout(height=400)
            st.plotly_chart(fig_time_dist, use_container_width=True)
        else:
            st.info("No reading activity data available yet.")

    with col2:
        st.markdown("""
        <div style="background: #f0f2f6; padding: 1.5rem; border-radius: 10px;">
            <h5>📊 Device Usage</h5>
            <p><strong>Primary Device:</strong> Desktop</p>
            <p><strong>Mobile:</strong> 40% of reads</p>
            <p><strong>Tablet:</strong> 5% of reads</p>
            <p style="color: #667eea; margin-top: 1rem;"><em>Device tracking coming soon!</em></p>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.subheader("Top Categories")

    col1, col2 = st.columns([2, 1])

    with col1:
        if category_stats:
            df_category = pd.DataFrame(category_stats, columns=[
                                       'Category', 'Articles'])
            df_category = df_category.sort_values('Articles', ascending=True)

            fig_category = px.bar(
                df_category,
                x='Articles',
                y='Category',
                title='Top Reading Categories',
                color='Articles',
                color_continuous_scale='Blues',
                orientation='h'
            )
            fig_category.update_layout(height=400)
            st.plotly_chart(fig_category, use_container_width=True)
        else:
            st.info("No category data available. Start reading to see stats!")

    with col2:
        st.write("**Category Breakdown**")
        if category_stats:
            for category, count in category_stats[:5]:
                percentage = int(
                    (count / sum([c[1] for c in category_stats])) * 100)
                st.metric(category, f"{count} articles", f"{percentage}%")
        else:
            st.info("No data yet")

with tab4:
    st.subheader("Reading Timeline")

    if daily_stats and len(daily_stats) > 0:
        df_timeline = pd.DataFrame(daily_stats, columns=[
                                   'Date', 'Count', 'Time'])
        df_timeline['Date'] = pd.to_datetime(df_timeline['Date'])
        df_timeline = df_timeline.sort_values('Date')
        df_timeline['Cumulative'] = df_timeline['Count'].cumsum()

        fig_timeline = go.Figure()

        fig_timeline.add_trace(go.Scatter(
            x=df_timeline['Date'],
            y=df_timeline['Cumulative'],
            mode='lines+markers',
            name='Articles Read',
            line=dict(color='#667eea', width=3),
            fill='tozeroy'
        ))

        fig_timeline.update_layout(
            title='Cumulative Reading Progress',
            xaxis_title='Date',
            yaxis_title='Articles',
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info(
            "No reading activity data available yet. Start reading to see your timeline!")

st.markdown("---")

# Recommendations
st.subheader("💡 Recommendations")

col1, col2, col3 = st.columns(3)

try:
    streak = get_reading_streak(email)
except Exception as e:
    log_info(f"Error fetching reading streak: {e}")
    streak = 0
with col1:
    if articles_read > 0:
        st.success(f"🔥 Current Streak: {streak} day(s)! Keep it up!")
    else:
        st.info("📖 Start reading to build your streak!")

with col2:
    if articles_read >= 30:
        st.success("⭐ Great job! You're hitting your reading goals!")
    else:
        st.info(f"📚 You've read {articles_read} articles. Keep reading!")

with col3:
    if not category_stats:
        st.warning("🔔 Start reading to unlock personalized recommendations!")
    elif len(category_stats) < 5:
        st.warning(
            f"🌍 Explore more categories! You've read from {len(category_stats)} so far.")
    else:
        st.success("✨ You're exploring diverse topics!")
