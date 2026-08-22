import io
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from pymongo.database import Database
from app.database import get_db
from app.security.auth import require_admin
from app.utils.objectid import str_to_object_id
from app.schemas.reports import DashboardStatsResponse, EventStatsResponse
from app.services.reports import (
    get_dashboard_stats,
    get_event_stats,
    generate_event_csv_report,
)

router = APIRouter(prefix="/api/reports", tags=["Reporting & Dashboard"])

@router.get("/dashboard", response_model=DashboardStatsResponse, status_code=status.HTTP_200_OK)
def get_dashboard(
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Returns administrative high-level overview metrics (Admin only).
    """
    stats = get_dashboard_stats(db)
    return {
        "success": True,
        "data": stats
    }

@router.get("/event/{event_id}", response_model=EventStatsResponse, status_code=status.HTTP_200_OK)
def get_event_report(
    event_id: str,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Returns statistics and check-in timeline metrics for a specific event (Admin only).
    """
    event_obj_id = str_to_object_id(event_id)
    stats = get_event_stats(db, event_obj_id)
    return {
        "success": True,
        "data": stats
    }

@router.get("/event/{event_id}/export")
def get_event_export(
    event_id: str,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Streams a CSV file containing check-in records for an event (Admin only).
    """
    event_obj_id = str_to_object_id(event_id)
    csv_bytes = generate_event_csv_report(db, event_obj_id)
    
    # Return streaming download response
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=event_checkins_{event_id}.csv"
        }
    )
