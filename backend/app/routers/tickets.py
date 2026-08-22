from fastapi import APIRouter, Depends, Query, status
from pymongo.database import Database
from app.database import get_db
from app.schemas.base import SuccessResponse
from app.schemas.tickets import (
    TicketGenerateResponse,
    TicketListResponse,
    PublicTicketDetailResponse,
)
from app.security.auth import require_admin
from app.utils.objectid import str_to_object_id
from app.services.tickets import (
    generate_tickets_for_event,
    list_tickets_for_event,
    revoke_ticket,
    get_public_ticket_by_token,
)

router = APIRouter(tags=["Ticket Management"])

@router.post("/api/events/{event_id}/tickets/generate", response_model=TicketGenerateResponse, status_code=status.HTTP_201_CREATED)
def post_generate_tickets(
    event_id: str,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Generates tickets for all registered active participants who do not have tickets (Admin only).
    """
    event_obj_id = str_to_object_id(event_id)
    generated = generate_tickets_for_event(db, current_admin, event_obj_id)
    return {
        "success": True,
        "data": {
            "generated": generated
        }
    }

@router.get("/api/events/{event_id}/tickets", response_model=TicketListResponse)
def get_event_tickets(
    event_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str = Query(default=None),
    search: str = Query(default=None),
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Retrieves safe administrative list of tickets for an event. Excludes secret tokens (Admin only).
    """
    event_obj_id = str_to_object_id(event_id)
    result = list_tickets_for_event(db, event_obj_id, page, page_size, status, search)
    return {
        "success": True,
        "data": result["items"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total": result["total"]
    }

@router.post("/api/tickets/{id}/revoke", response_model=SuccessResponse)
def post_revoke_ticket(
    id: str,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Revokes an active ticket, preventing future check-in verification (Admin only).
    """
    ticket_obj_id = str_to_object_id(id)
    result = revoke_ticket(db, current_admin, ticket_obj_id)
    return {
        "success": True,
        "data": result
    }

@router.get("/api/tickets/{token}", response_model=PublicTicketDetailResponse)
def get_public_ticket(
    token: str,
    db: Database = Depends(get_db)
):
    """
    Retrieves public-safe ticket info by token (Public endpoint).
    """
    result = get_public_ticket_by_token(db, token)
    return {
        "success": True,
        "data": result
    }
