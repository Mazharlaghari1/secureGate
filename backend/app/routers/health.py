from fastapi import APIRouter, Response, status
from app.database import db_manager

router = APIRouter(prefix="/api/health", tags=["Health Check"])

@router.get("", response_model=None)
def check_health(response: Response):
    """
    Health check endpoint to verify API and Database connectivity.
    """
    try:
        # Check connectivity by pinging the database
        db = db_manager.get_db()
        db.client.admin.command('ping')
        return {
            "success": True,
            "data": {
                "status": "ok",
                "database": "connected"
            }
        }
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "success": False,
            "error": {
                "code": "DATABASE_DISCONNECTED",
                "message": "Database connectivity check failed.",
                "details": {}
            }
        }
