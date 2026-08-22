from fastapi import APIRouter, Depends, Query, status
from pymongo.database import Database
from app.database import get_db
from app.security.auth import require_admin
from app.schemas.entities import AuditLogResponse
from app.services.audit import list_audit_logs
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logging"])

class AuditLogListResponse(BaseModel):
    success: bool = True
    data: List[AuditLogResponse]
    page: int
    page_size: int
    total: int

@router.get("", response_model=AuditLogListResponse, status_code=status.HTTP_200_OK)
def get_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    action: Optional[str] = Query(default=None),
    status_str: Optional[str] = Query(default=None, alias="status"),
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Returns a paginated list of security audit logs (Admin only).
    """
    result = list_audit_logs(db, page, page_size, action, status_str)
    return {
        "success": True,
        "data": result["items"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total": result["total"]
    }
