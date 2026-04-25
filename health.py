"""
Health check endpoint for monitoring application status
"""

import json
from datetime import datetime
from database.connection import db_manager
from utils import log_info


def health_check():
    """Perform health checks and return status"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    # Database check
    try:
        db_manager.execute_query("SELECT 1", fetch_one=True)
        status["checks"]["database"] = "healthy"
    except Exception as e:
        status["checks"]["database"] = f"unhealthy: {str(e)}"
        status["status"] = "unhealthy"
        log_info(f"Health check failed - database: {e}")

    # Application check
    status["checks"]["application"] = "healthy"

    return status


if __name__ == "__main__":
    print(json.dumps(health_check(), indent=2))
