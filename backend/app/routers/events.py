from fastapi import APIRouter, Depends, Query, status
from pymongo.database import Database
from typing import Optional, List
from app.database import get_db
from app.schemas.base import SuccessResponse
from app.schemas.entities import EventResponse
from app.schemas.events import EventCreate, EventUpdate
from app.security.auth import require_admin, require_staff
from app.utils.objectid import str_to_object_id
from app.services.events import (
    create_event,
    list_events,
    get_event_by_id,
    update_event,
    cancel_event,
)
from pydantic import BaseModel

router = APIRouter(prefix="/api/events", tags=["Event Management"])

class EventSingleResponse(BaseModel):
    success: bool = True
    data: EventResponse

class EventListResponse(BaseModel):
    success: bool = True
    data: List[EventResponse]
    page: int
    page_size: int
    total: int

@router.post("", response_model=EventSingleResponse, status_code=status.HTTP_201_CREATED)
def post_event(
    payload: EventCreate,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Creates a new event with status set initially to draft (Admin only).
    """
    event = create_event(
        db=db,
        current_admin=current_admin,
        name=payload.name,
        description=payload.description,
        venue=payload.venue,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        capacity=payload.capacity,
        timezone_name=payload.timezone
    )
    return {
        "success": True,
        "data": event
    }

@router.get("", response_model=EventListResponse)
def get_events(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    date: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    current_user: dict = Depends(require_staff),
    db: Database = Depends(get_db)
):
    """
    Retrieves all events matching query params (Admin/Staff).
    """
    result = list_events(db, page, page_size, status, date, search)
    return {
        "success": True,
        "data": result["items"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total": result["total"]
    }

@router.get("/{id}", response_model=EventSingleResponse)
def get_event_detail(
    id: str,
    current_user: dict = Depends(require_staff),
    db: Database = Depends(get_db)
):
    """
    Retrieves full details of a specific event (Admin/Staff).
    """
    obj_id = str_to_object_id(id)
    event = get_event_by_id(db, obj_id)
    return {
        "success": True,
        "data": event
    }

@router.put("/{id}", response_model=EventSingleResponse)
def put_event(
    id: str,
    payload: EventUpdate,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Updates event details including lifecycle status (Admin only).
    """
    obj_id = str_to_object_id(id)
    event = update_event(db, current_admin, obj_id, payload.model_dump(exclude_unset=True))
    return {
        "success": True,
        "data": event
    }

@router.delete("/{id}", response_model=SuccessResponse)
def delete_event(
    id: str,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Cancels an event without executing physical database deletions (Admin only).
    """
    obj_id = str_to_object_id(id)
    result = cancel_event(db, current_admin, obj_id)
    return {
        "success": True,
        "data": result
    }
