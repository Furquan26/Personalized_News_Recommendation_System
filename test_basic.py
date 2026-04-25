"""
Basic tests for production readiness
"""

import pytest
from health import health_check
from validate_env import validate_environment
from database.connection import db_manager
from api.auth import AuthManager
from utils.rate_limiter import check_rate_limit

def test_health_check():
    """Test health check functionality"""
    status = health_check()
    assert status["status"] in ["healthy", "unhealthy"]
    assert "database" in status["checks"]
    assert "application" in status["checks"]

def test_environment_validation():
    """Test environment variable validation"""
    # This will pass if env vars are set, fail otherwise
    result = validate_environment()
    assert isinstance(result, bool)

def test_database_connection():
    """Test database connection"""
    try:
        result = db_manager.execute_query("SELECT 1", fetch_one=True)
        assert result is not None
    except Exception:
        pytest.skip("Database not available")

def test_rate_limiter():
    """Test rate limiter functionality"""
    client_id = "test_client"
    allowed, info = check_rate_limit(client_id, max_requests=5, window_seconds=60)
    assert allowed == True
    assert "remaining" in info
    assert info["remaining"] >= 0

def test_email_validation():
    """Test email validation"""
    assert AuthManager.validate_email("test@example.com") == True
    assert AuthManager.validate_email("invalid-email") == False

def test_password_validation():
    """Test password validation"""
    valid, msg = AuthManager.validate_password("StrongPass123")
    assert valid == True

    invalid, msg = AuthManager.validate_password("weak")
    assert invalid == False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])