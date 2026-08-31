from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import db_manager
from app.utils.logging_config import setup_logging
from app.routers import (
    health_router,
    auth_router,
    users_router,
    events_router,
    participants_router,
    tickets_router,
    attendance_router,
    reports_router,
    audit_logs_router,
    portal_router,
)
from app.middleware import (
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)

import logging

setup_logging()
logger = logging.getLogger("event_access")

def init_default_admin():
    try:
        db = db_manager.get_db()
        admin_email = getattr(settings, "INITIAL_ADMIN_EMAIL", "admin@securegate.com").strip().lower()
        existing = db.users.find_one({"email": admin_email})
        if not existing:
            from datetime import datetime, timezone
            from app.security.auth import hash_password
            now = datetime.now(timezone.utc)
            admin_doc = {
                "name": "System Administrator",
                "email": admin_email,
                "password_hash": hash_password(getattr(settings, "INITIAL_ADMIN_PASSWORD", "Admin12345!")),
                "role": "admin",
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
            db.users.insert_one(admin_doc)
            logger.info(f"Bootstrap: Initial administrator account verified/created ({admin_email})")
    except Exception as e:
        logger.warning(f"Bootstrap administrator initialization skipped: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing application resources during lifespan startup...")
    try:
        # Load configuration (done automatically by import of settings)
        # Initialize connection and verify connectivity
        db_manager.connect()
        # Initialize indexes
        db_manager.init_indexes()
        # Ensure default administrator exists
        init_default_admin()
        logger.info("Lifespan startup verification complete.")
    except Exception as e:
        logger.critical(f"Failed to complete startup checks: {str(e)}")
        raise e
    yield
    logger.info("Tearing down application resources during lifespan shutdown...")
    db_manager.close()
    logger.info("Lifespan shutdown complete.")

app = FastAPI(
    title="Smart Web-Based Event Access and QR Ticket Verification System",
    description="Backend API services for event, participant, ticket management, and QR scanning check-ins.",
    version="1.0.1",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration
origins = settings.ALLOWED_ORIGINS
if isinstance(origins, str):
    origins = [origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://([a-zA-Z0-9-]+\.)*(repl\.co|replit\.dev|replit\.app|onrender\.com|localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(events_router)
app.include_router(participants_router)
app.include_router(tickets_router)
app.include_router(attendance_router)
app.include_router(reports_router)
app.include_router(audit_logs_router)
app.include_router(portal_router)

# Register global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
