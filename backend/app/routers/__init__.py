from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.events import router as events_router
from app.routers.participants import router as participants_router
from app.routers.tickets import router as tickets_router
from app.routers.attendance import router as attendance_router
from app.routers.reports import router as reports_router
from app.routers.audit_logs import router as audit_logs_router
from app.routers.portal import router as portal_router

__all__ = [
    "health_router",
    "auth_router",
    "users_router",
    "events_router",
    "participants_router",
    "tickets_router",
    "attendance_router",
    "reports_router",
    "audit_logs_router",
    "portal_router",
]
