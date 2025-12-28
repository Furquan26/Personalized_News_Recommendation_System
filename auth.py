# auth.py
import streamlit as st
import sqlite3
import hashlib
import re
import os

# Database setup
def create_connection():
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect('data/users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS preferences
                 (email TEXT PRIMARY KEY, sources TEXT, category TEXT)''')
    conn.commit()
    return conn

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Email validation
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

# Save user preferences
def save_preferences(email, sources, category):
    conn = create_connection()
    c = conn.cursor()
    sources_str = ",".join(sources) if sources else ""
    c.execute("INSERT OR REPLACE INTO preferences VALUES (?, ?, ?)", 
              (email, sources_str, category))
    conn.commit()
    conn.close()

# Load user preferences
def load_preferences(email):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT sources, category FROM preferences WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    
    if result:
        sources = result[0].split(",") if result[0] else []
        category = result[1]
        return sources, category
    return [], "General"

# Sign up function
def sign_up():
    with st.form("signup_form"):
        st.subheader("Create New Account")
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type='password')
        confirm_password = st.text_input("Confirm Password", type='password')
        
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
                c.execute("INSERT INTO users VALUES (?, ?, ?)", 
                        (email, hash_password(password), name))
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
        email = st.text_input("Email")
        password = st.text_input("Password", type='password')
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if not email or not password:
                st.error("Both email and password are required!")
                return False
            
            conn = create_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=? AND password=?", 
                    (email, hash_password(password)))
            user = c.fetchone()
            conn.close()
            
            if user:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_name = user[2]
                
                # Load saved preferences
                sources, category = load_preferences(email)
                st.session_state.selected_sources = sources
                st.session_state.selected_category = category
                
                st.success(f"Welcome back, {user[2]}!")
                return True
            else:
                st.error("Invalid email or password")
                return False
    return False

# Logout function
def logout():
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Main auth function
def show_auth_page():
    st.set_page_config(page_title="News Aggregator - Authentication", layout="centered")
    
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
