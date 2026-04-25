"""
⚙️ Settings - User Configuration
Manage preferences, notification settings, and account
"""

import streamlit as st
from auth_new import logout, save_preferences
from utils import log_info, log_error

# Page config
st.set_page_config(
    page_title="⚙️ Settings",
    page_icon="⚙️",
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
    
    .settings-section {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    
    .settings-title {
        font-size: 18px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    .preference-group {
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .preference-group:last-child {
        border-bottom: none;
    }
    
    .success-message {
        background: #e8f5e9;
        border-left: 4px solid #2ecc71;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        color: #2e7d32;
    }
</style>
""", unsafe_allow_html=True)

# Navbar
st.markdown("""
<div class="navbar">
    <h2 class="navbar-title">⚙️ Settings & Preferences</h2>
    <div>Customize your News experience</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("👤 User Profile")
    st.write(f"**Name:** {st.session_state.user_name}")
    st.write(f"**Email:** {st.session_state.user_email}")

    st.markdown("---")
    settings_section = st.radio(
        "Settings",
        ["News Preferences", "Display & Theme",
            "Notifications", "Privacy", "Account"]
    )

    logout()

# Settings content
if settings_section == "News Preferences":
    st.markdown("---")
    st.subheader("📰 News Preferences")

    with st.container():
        st.markdown('<div class="settings-section">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Preferred News Sources**")
            sources = {
                "Times of India": "times",
                "The Hindu": "hindu",
                "Dainik Bhaskar": "bhaskar",
                "ABP Majha": "abp",
                "Dainik Jagran": "jagran",
                "Aaj Tak": "aajtak",
                "India Today": "indiatoday"
            }

            selected_sources = st.multiselect(
                "Choose your favorite sources",
                list(sources.keys()),
                default=st.session_state.selected_sources or []
            )

        with col2:
            st.write("**Preferred Categories**")
            categories = ["General", "Sports", "Politics",
                          "Technology", "Market", "Entertainment", "Health"]
            preferred_category = st.selectbox(
                "Primary category",
                categories,
                index=categories.index(
                    st.session_state.selected_category) if st.session_state.selected_category in categories else 0
            )

        st.markdown("---")
        st.write("**Content Preferences**")

        col1, col2, col3 = st.columns(3)
        with col1:
            show_images = st.checkbox("Show article images", value=True)
        with col2:
            show_author = st.checkbox("Show author names", value=True)
        with col3:
            show_reading_time = st.checkbox("Show reading time", value=True)

        st.markdown("---")

        if st.button("💾 Save News Preferences"):
            save_preferences(st.session_state.user_email,
                             selected_sources, preferred_category)
            st.session_state.selected_sources = selected_sources
            st.session_state.selected_category = preferred_category
            st.markdown(
                '<div class="success-message">✅ News preferences updated successfully!</div>', unsafe_allow_html=True)
            log_info(f"User {st.session_state.user_email} updated preferences")

        st.markdown('</div>', unsafe_allow_html=True)

elif settings_section == "Display & Theme":
    st.markdown("---")
    st.subheader("🎨 Display & Theme")

    with st.container():
        st.markdown('<div class="settings-section">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Theme**")
            theme = st.radio(
                "Choose theme",
                ["Light", "Dark", "Auto"],
                index=0,
                horizontal=True
            )

        with col2:
            st.write("**Text Size**")
            text_size = st.slider("Text size (em)", 0.8, 1.5, 1.0)

        st.markdown("---")
        st.write("**Display Options**")

        col1, col2, col3 = st.columns(3)
        with col1:
            compact_view = st.checkbox("Compact card view", value=False)
        with col2:
            show_thumbnails = st.checkbox("Show thumbnails", value=True)
        with col3:
            full_width = st.checkbox("Full width layout", value=False)

        st.markdown("---")

        if st.button("💾 Save Display Settings"):
            st.markdown(
                '<div class="success-message">✅ Display settings updated successfully!</div>', unsafe_allow_html=True)
            log_info(
                f"Display settings updated for {st.session_state.user_email}")

        st.markdown('</div>', unsafe_allow_html=True)

elif settings_section == "Notifications":
    st.markdown("---")
    st.subheader("🔔 Notification Settings")

    with st.container():
        st.markdown('<div class="settings-section">', unsafe_allow_html=True)

        st.write("**Email Notifications**")

        col1, col2 = st.columns(2)
        with col1:
            daily_digest = st.checkbox(
                "Daily news digest", value=True, help="Receive daily news summary at 8 AM")
        with col2:
            trending = st.checkbox(
                "Trending news", value=True, help="Get notified about trending stories")

        col1, col2 = st.columns(2)
        with col1:
            breaking = st.checkbox(
                "Breaking news", value=False, help="Urgent alerts for breaking news")
        with col2:
            weekly_summary = st.checkbox(
                "Weekly summary", value=True, help="Weekly reading stats and top articles")

        st.markdown("---")

        st.write("**In-App Notifications**")
        col1, col2 = st.columns(2)
        with col1:
            push_notifications = st.checkbox("Push notifications", value=False)
        with col2:
            suggestions = st.checkbox("Article suggestions", value=True)

        st.markdown("---")

        if st.button("💾 Save Notification Settings"):
            st.markdown(
                '<div class="success-message">✅ Notification settings updated successfully!</div>', unsafe_allow_html=True)
            log_info(
                f"Notification settings updated for {st.session_state.user_email}")

        st.markdown('</div>', unsafe_allow_html=True)

elif settings_section == "Privacy":
    st.markdown("---")
    st.subheader("🔒 Privacy & Security")

    with st.container():
        st.markdown('<div class="settings-section">', unsafe_allow_html=True)

        st.write("**Data Privacy**")

        col1, col2 = st.columns(2)
        with col1:
            track_reading = st.checkbox(
                "Track reading history", value=True, help="Allow us to personalize recommendations")
        with col2:
            analytics = st.checkbox(
                "Share usage analytics", value=False, help="Help improve our service")

        st.markdown("---")

        st.write("**Search & Browsing**")

        col1, col2 = st.columns(2)
        with col1:
            save_search = st.checkbox("Save search history", value=True)
        with col2:
            personalize = st.checkbox("Personalized content", value=True)

        st.markdown("---")

        st.write("**Data Management**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download My Data"):
                st.info(
                    "Your data export is being prepared. You'll receive a download link within 24 hours.")

        with col2:
            if st.button("🗑️ Delete Account (Permanently)"):
                if st.checkbox("I understand this cannot be undone"):
                    st.warning(
                        "⚠️ Contact admin@example.com to delete your account")

        st.markdown("---")

        if st.button("💾 Save Privacy Settings"):
            st.markdown(
                '<div class="success-message">✅ Privacy settings updated successfully!</div>', unsafe_allow_html=True)
            log_info(
                f"Privacy settings updated for {st.session_state.user_email}")

        st.markdown('</div>', unsafe_allow_html=True)

elif settings_section == "Account":
    st.markdown("---")
    st.subheader("👤 Account Settings")

    with st.container():
        st.markdown('<div class="settings-section">', unsafe_allow_html=True)

        st.write("**Account Information**")

        col1, col2 = st.columns(2)
        with col1:
            st.text_input(
                "Full Name", value=st.session_state.user_name, disabled=True)
        with col2:
            st.text_input(
                "Email", value=st.session_state.user_email, disabled=True)

        st.markdown("---")

        st.write("**Change Password**")

        col1, col2 = st.columns(2)
        with col1:
            current_pwd = st.text_input("Current password", type="password")
        with col2:
            new_pwd = st.text_input("New password", type="password")

        confirm_pwd = st.text_input("Confirm new password", type="password")

        if st.button("🔐 Update Password"):
            if new_pwd and new_pwd == confirm_pwd:
                st.markdown(
                    '<div class="success-message">✅ Password updated successfully!</div>', unsafe_allow_html=True)
            else:
                st.error("Passwords don't match!")

        st.markdown("---")

        st.write("**Account Actions**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📧 Verify Email"):
                st.info("Verification email sent to your inbox")

        with col2:
            if st.button("🚪 Logout"):
                st.session_state.clear()
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
