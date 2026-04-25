"""
JWT Authentication for Streamlit
Handles user login, signup, and session management
"""

import hashlib
import re
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from database.models import UserModel, ActivityModel
from loguru import logger
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-me')
ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))


class AuthManager:
    """Manages authentication and user sessions"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_password(password: str) -> tuple:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        return True, "Valid password"

    @staticmethod
    def create_access_token(data: Dict, expires_delta: timedelta = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """Decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"Token decode error: {e}")
            return None

    @staticmethod
    def sign_up(email: str, password: str, username: str) -> tuple:
        """Register new user"""
        try:
            # Validate inputs
            if not email or not password or not username:
                return False, "All fields are required"

            if not AuthManager.validate_email(email):
                return False, "Invalid email format"

            is_valid, msg = AuthManager.validate_password(password)
            if not is_valid:
                return False, msg

            if not username or len(username) < 3:
                return False, "Username must be at least 3 characters"

            # Check if user exists
            existing_user = UserModel.get_user_by_email(email)
            if existing_user:
                return False, "Email already registered"

            # Create user
            password_hash = AuthManager.hash_password(password)
            user = UserModel.create_user(email, password_hash, username)

            if user:
                # Log activity
                ActivityModel.log_activity(user['user_id'], 'signup')
                logger.info(f"New user registered: {email}")
                return True, "Registration successful! Please login."

            return False, "Registration failed"
        except Exception as e:
            logger.error(f"Signup error for {email}: {e}")
            return False, "An error occurred during registration. Please try again."

    @staticmethod
    def login(email: str, password: str) -> tuple:
        """Authenticate user and create session"""
        try:
            # Validate inputs
            if not email or not password:
                return False, "Email and password are required", None

            # Get user
            user = UserModel.get_user_by_email(email)
            if not user:
                return False, "Invalid email or password", None

            # Verify password
            if not AuthManager.verify_password(password, user['password_hash']):
                return False, "Invalid email or password", None

            # Update last login
            UserModel.update_last_login(user['user_id'])

            # Log activity
            ActivityModel.log_activity(user['user_id'], 'login')

            # Create token
            token = AuthManager.create_access_token({
                "sub": str(user['user_id']),
                "email": user['email'],
                "username": user['username']
            })

            # Store in session state
            st.session_state.authenticated = True
            st.session_state.user_id = str(user['user_id'])
            st.session_state.user_email = user['email']
            st.session_state.user_name = user['username']
            st.session_state.token = token
            st.session_state.preferences = user.get('preferences', {})

            logger.info(f"User logged in: {email}")
            return True, "Login successful", token
        except Exception as e:
            logger.error(f"Login error for {email}: {e}")
            return False, "An error occurred during login. Please try again.", None

    @staticmethod
    def logout():
        """Logout user"""
        if 'user_id' in st.session_state:
            ActivityModel.log_activity(st.session_state.user_id, 'logout')

        # Clear session
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        logger.info("User logged out")
        st.rerun()

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)

    @staticmethod
    def get_current_user() -> Optional[Dict]:
        """Get current user data"""
        if not AuthManager.is_authenticated():
            return None

        return UserModel.get_user_by_id(st.session_state.user_id)
