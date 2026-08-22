from fastapi import APIRouter, Depends, Query, status
from pymongo.database import Database
from app.database import get_db
from app.schemas.attendance import (
    VerifyTicketRequest,
    VerifyTicketResponse,
    StaffScanHistoryResponse,
)
from app.security.auth import require_staff
from app.utils.objectid import str_to_object_id
from app.services.attendance import (
    verify_and_check_in_ticket,
    list_staff_scans,
)

router = APIRouter(tags=["Attendance & Scanning"])

@router.post("/api/attendance/verify", response_model=VerifyTicketResponse, status_code=status.HTTP_200_OK)
def post_verify_ticket(
    payload: VerifyTicketRequest,
    current_user: dict = Depends(require_staff),
    db: Database = Depends(get_db)
):
    """
    Verifies a ticket QR token and checks in the participant (Staff/Admin only).
    """
    event_obj_id = str_to_object_id(payload.event_id)
    result = verify_and_check_in_ticket(
        db=db,
        current_user=current_user,
        token=payload.token,
        event_id=event_obj_id
    )
    return {
        "success": True,
        "data": result
    }

@router.get("/api/attendance/my-scans", response_model=StaffScanHistoryResponse)
def get_my_scans(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(require_staff),
    db: Database = Depends(get_db)
):
    """
    Retrieves recent check-ins executed by the currently logged-in user (Staff/Admin only).
    """
    result = list_staff_scans(
        db=db,
        user_id=current_user["_id"],
        page=page,
        page_size=page_size
    )
    return {
        "success": True,
        "data": result["items"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total": result["total"]
    }
