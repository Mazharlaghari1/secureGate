from datetime import datetime, timezone, timedelta
import secrets
import jwt
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.database import get_db
from app.security.auth import require_attendee, hash_password
from app.schemas.entities import EventResponse, UserResponse
from app.utils.objectid import str_to_object_id
from app.config import settings
from app.models.constants import UserRole, EventStatus, TicketStatus, AuditStatus
from app.services.audit import log_audit
from app.utils.timezone import local_to_utc

router = APIRouter(prefix="/api/portal", tags=["Attendee Portal"])

# --- SCHEMAS ---

class PortalEventResponseData(BaseModel):
    id: str
    name: str
    date: str
    venue: str
    start_time: str
    end_time: str
    timezone: str
    status: str
    ticket_code: Optional[str] = None
    ticket_status: Optional[str] = None
    checked_in: bool = False

class PortalEventListResponse(BaseModel):
    success: bool = True
    data: List[PortalEventResponseData]

class PortalEventDetailResponseData(BaseModel):
    event: EventResponse
    ticket_id: Optional[str] = None
    ticket_code: Optional[str] = None
    ticket_status: Optional[str] = None
    checked_in: bool = False
    scanned_at: Optional[datetime] = None

class PortalEventDetailResponse(BaseModel):
    success: bool = True
    data: PortalEventDetailResponseData

class PortalTicketResponseData(BaseModel):
    id: str
    ticket_code: str
    status: str
    expires_at: datetime
    event_name: str
    venue: str
    date: str
    time: str

class PortalTicketListResponse(BaseModel):
    success: bool = True
    data: List[PortalTicketResponseData]

class PortalTicketDetailResponseData(BaseModel):
    id: str
    ticket_code: str
    status: str
    expires_at: datetime
    event_name: str
    venue: str
    date: str
    time: str
    timezone: str
    participant_name: str
    qr_payload: str
    checked_in: bool
    scanned_at: Optional[datetime] = None

class PortalTicketDetailResponse(BaseModel):
    success: bool = True
    data: PortalTicketDetailResponseData

class PortalProfileUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)

class PortalProfileResponse(BaseModel):
    success: bool = True
    data: UserResponse

class PortalTicketQrResponseData(BaseModel):
    qr_token: str
    expires_at: datetime
    server_time: datetime

class PortalTicketQrResponse(BaseModel):
    success: bool = True
    data: PortalTicketQrResponseData

# --- ADDITIONAL PORTAL SCHEMAS ---

class AvailableEventResponseData(BaseModel):
    id: str
    name: str
    venue: str
    date: str
    start_time: str
    end_time: str
    timezone: str
    description: Optional[str] = None
    capacity: int
    registered_count: int
    remaining_capacity: int
    booking_open: bool
    already_booked: bool = False
    ticket_id: Optional[str] = None

class AvailableEventListResponse(BaseModel):
    success: bool = True
    data: List[AvailableEventResponseData]

class AvailableEventDetailResponse(BaseModel):
    success: bool = True
    data: AvailableEventResponseData

class BookingTicketData(BaseModel):
    id: str
    ticket_code: str
    status: str
    event_id: str
    event_name: str
    qr_payload: str

class BookingResponseData(BaseModel):
    ticket: BookingTicketData

class BookingResponse(BaseModel):
    success: bool = True
    data: BookingResponseData

# --- ROUTES ---

@router.get("/me", response_model=PortalProfileResponse)
def get_portal_me(
    current_user: dict = Depends(require_attendee)
):
    """
    Retrieves profile details of the logged in attendee.
    """
    return {
        "success": True,
        "data": current_user
    }

@router.put("/profile", response_model=PortalProfileResponse)
def put_portal_profile(
    payload: PortalProfileUpdate,
    current_user: dict = Depends(require_attendee),
    db: Database = Depends(get_db)
):
    """
    Safely updates name of the logged in attendee.
    """
    db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"name": payload.name.strip(), "updated_at": datetime.utcnow()}}
    )
    updated_user = db.users.find_one({"_id": current_user["_id"]})
    return {
        "success": True,
        "data": updated_user
    }

@router.get("/events/available", response_model=AvailableEventListResponse)
def get_portal_available_events(
    current_user: dict = Depends(require_attendee),
    db: Database = Depends(get_db)
):
    """
    Lists all available (active) events for registration.
    """
    events = list(db.events.find({"status": EventStatus.ACTIVE.value}))
    
    email_normalized = current_user["email"].strip().lower()
    participants = list(db.participants.find({"email": email_normalized, "is_active": True}))
    registered_event_ids = {str(p["event_id"]) for p in participants}

    response_data = []
    for event in events:
        registered_count = db.participants.count_documents({"event_id": event["_id"], "is_active": True})
        remaining_capacity = max(0, event["capacity"] - registered_count)
        
        today_str = datetime.now(timezone.utc).date().isoformat()
        booking_open = remaining_capacity > 0 and event["date"] >= today_str
        
        already_booked = str(event["_id"]) in registered_event_ids
        
        response_data.append({
            "id": str(event["_id"]),
            "name": event["name"],
            "venue": event["venue"],
            "date": event["date"],
            "start_time": event["start_time"],
            "end_time": event["end_time"],
            "timezone": event["timezone"],
            "description": event.get("description"),
            "capacity": event["capacity"],
            "registered_count": registered_count,
            "remaining_capacity": remaining_capacity,
            "booking_open": booking_open,
            "already_booked": already_booked
        })
        
    return {
        "success": True,
        "data": response_data
    }

@router.get("/events/available/{event_id}", response_model=AvailableEventDetailResponse)
def get_portal_available_event_detail(
    event_id: str,
    current_user: dict = Depends(require_attendee),
    db: Database = Depends(get_db)
):
    """
    Retrieves available event details with registered stats and user status.
    """
    event_obj_id = str_to_object_id(event_id)
    event = db.events.find_one({"_id": event_obj_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "EVENT_NOT_FOUND",
                "message": "The requested event does not exist."
            }
        )
        
    if event["status"] != EventStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EVENT_NOT_BOOKABLE",
                "message": "This event is not open for registrations."
            }
        )
        
    email_normalized = current_user["email"].strip().lower()
    part = db.participants.find_one({"event_id": event_obj_id, "email": email_normalized, "is_active": True})
    already_booked = part is not None
    
    ticket_id = None
    if already_booked:
        ticket = db.tickets.find_one({"event_id": event_obj_id, "participant_id": part["_id"]})
        if ticket:
            ticket_id = str(ticket["_id"])
    
    registered_count = db.participants.count_documents({"event_id": event_obj_id, "is_active": True})
    remaining_capacity = max(0, event["capacity"] - registered_count)
    
    today_str = datetime.now(timezone.utc).date().isoformat()
    booking_open = remaining_capacity > 0 and event["date"] >= today_str
    
    return {
        "success": True,
        "data": {
            "id": str(event["_id"]),
            "name": event["name"],
            "venue": event["venue"],
            "date": event["date"],
            "start_time": event["start_time"],
            "end_time": event["end_time"],
            "timezone": event["timezone"],
            "description": event.get("description"),
            "capacity": event["capacity"],
            "registered_count": registered_count,
            "remaining_capacity": remaining_capacity,
            "booking_open": booking_open,
            "already_booked": already_booked,
            "ticket_id": ticket_id
        }
    }

@router.post("/events/{event_id}/book", response_model=BookingResponse)
def post_portal_book_event(
    event_id: str,
    current_user: dict = Depends(require_attendee),
    db: Database = Depends(get_db)
):
    """
    Registers the authenticated attendee to the specified event and generates a ticket.
    Includes duplicate checks, capacity validation, manual rollback, and audit logging.
    """
    event_obj_id = str_to_object_id(event_id)
    event = db.events.find_one({"_id": event_obj_id})
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "EVENT_NOT_FOUND",
                "message": "Event not found."
            }
        )
        
    if event["status"] != EventStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EVENT_NOT_BOOKABLE",
                "message": f"This event cannot be booked. Status is {event['status']}."
            }
        )
        
    today_str = datetime.now(timezone.utc).date().isoformat()
    if event["date"] < today_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EVENT_EXPIRED",
                "message": "Cannot book a past event."
            }
        )

    # 1. Capacity Validation
    registered_count = db.participants.count_documents({"event_id": event_obj_id, "is_active": True})
    if registered_count >= event["capacity"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EVENT_FULL",
                "message": "This event is currently full."
            }
        )

    email_normalized = current_user["email"].strip().lower()

    # 2. Check duplicate bookings
    existing_part = db.participants.find_one({
        "event_id": event_obj_id,
        "email": email_normalized,
        "is_active": True
    })
    if existing_part:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ALREADY_REGISTERED",
                "message": "You are already registered for this event."
            }
        )

    # Calculate expiration time: local event end time + 2 hours
    try:
        local_end_utc = local_to_utc(event["date"], event["end_time"], event["timezone"])
        expires_at = local_end_utc + timedelta(hours=2)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "TICKET_CREATION_FAILED",
                "message": f"Could not calculate ticket expiration: {str(e)}"
            }
        )

    now_utc = datetime.now(timezone.utc)
    
    # 3. Create Participant Document
    part_doc = {
        "event_id": event_obj_id,
        "name": current_user["name"].strip(),
        "email": email_normalized,
        "phone": None,
        "is_active": True,
        "created_at": now_utc,
        "updated_at": now_utc
    }
    
    try:
        res_part = db.participants.insert_one(part_doc)
        part_id = res_part.inserted_id
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ALREADY_REGISTERED",
                "message": "You are already registered for this event."
            }
        )

    # 4. Generate Ticket
    token = secrets.token_urlsafe(32)
    ticket_code = f"EVT-{secrets.token_hex(4).upper()}"
    ticket_doc = {
        "event_id": event_obj_id,
        "participant_id": part_id,
        "ticket_code": ticket_code,
        "token": token,
        "status": "active",
        "expires_at": expires_at,
        "created_at": now_utc,
        "updated_at": now_utc
    }

    try:
        res_ticket = db.tickets.insert_one(ticket_doc)
        ticket_id = res_ticket.inserted_id
    except Exception as e:
        # Revert/Rollback participant creation
        db.participants.delete_one({"_id": part_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "TICKET_CREATION_FAILED",
                "message": f"Could not generate ticket for booking: {str(e)}"
            }
        )

    # 5. Log Audit Log
    log_audit(
        db=db,
        action="ATTENDEE_BOOKED_EVENT",
        actor_id=current_user["_id"],
        actor_email=email_normalized,
        target_type="event",
        target_id=event_obj_id,
        status=AuditStatus.SUCCESS,
        metadata={
            "event_id": str(event_obj_id),
            "participant_id": str(part_id),
            "ticket_id": str(ticket_id)
        }
    )

    return {
        "success": True,
        "data": {
            "ticket": {
                "id": str(ticket_id),
                "ticket_code": ticket_code,
                "status": "active",
                "event_id": str(event_obj_id),
                "event_name": event["name"],
                "qr_payload": f"{settings.FRONTEND_URL}/tickets/{token}"
            }
        }
    }

@router.get("/events", response_model=PortalEventListResponse)
def get_portal_events(
    current_user: dict = Depends(require_attendee),
    db: Database = Depends(get_db)
):
    """
    Lists all events the authenticated attendee is registered for.
    """
    email_normalized = current_user["email"].strip().lower()
    
    participants = list(db.participants.find({"email": email_normalized, "is_active": True}))
    if not participants:
        return {"success": True, "data": []}
        
    event_ids = [p["event_id"] for p in participants]
    events = list(db.events.find({"_id": {"$in": event_ids}}))
    
    participant_ids = [p["_id"] for p in participants]
    tickets = list(db.tickets.find({"participant_id": {"$in": participant_ids}}))
    
    response_data = []
    for event in events:
        part = next((p for p in participants if p["event_id"] == event["_id"]), None)
        ticket = None
        if part:
            ticket = next((t for t in tickets if t["participant_id"] == part["_id"]), None)
            
        ticket_status = None
        if ticket:
            ticket_status = ticket.get("status")
            expires_at = ticket["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if ticket_status == "active" and datetime.now(timezone.utc) >= expires_at:
                ticket_status = "expired"

        checked_in = ticket_status == "used" if ticket else False
        
        response_data.append({
            "id": str(event["_id"]),
            "name": event["name"],
            "date": event["date"],
            "venue": event["venue"],
            "start_time": event["start_time"],
            "end_time": event["end_time"],
            "timezone": event["timezone"],
            "status": event["status"],
            "ticket_code": ticket["ticket_code"] if ticket else None,
            "ticket_status": ticket_status,
            "checked_in": checked_in
        })
        
    return {
        "success": True,
        "data": response_data
    }

@router.get("/events/{event_id}", response_model=PortalEventDetailResponse)
def get_portal_event_detail(
    event_id: str,
    current_user: dict = Depends(require_attendee),
    db: Database = Depends(get_db)
):
    """
    Retrieves single event details for authenticated attendee, with IDOR protection.
    """
    event_obj_id = str_to_object_id(event_id)
    email_normalized = current_user["email"].strip().lower()
    
    part = db.participants.find_one({
        "event_id": event_obj_id, 
        "email": email_normalized, 
        "is_active": True
    })
    if not part:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCESS_DENIED",
                "message": "You are not registered for this event."
            }
        )
        
    event = db.events.find_one({"_id": event_obj_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Event not found."
            }
        )
        
    ticket = db.tickets.find_one({
        "event_id": event_obj_id, 
        "participant_id": part["_id"]
    })
    
    ticket_status = None
    checked_in = False
    scanned_at = None
    
    if ticket:
        ticket_status = ticket.get("status")
        expires_at = ticket["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if ticket_status == "active" and datetime.now(timezone.utc) >= expires_at:
            ticket_status = "expired"

        checked_in = ticket_status == "used"
        if checked_in:
            attendance = db.attendance.find_one({"ticket_id": ticket["_id"]})
            if attendance:
                scanned_at = attendance["scanned_at"]
                
    return {
        "success": True,
        "data": {
            "event": event,
            "ticket_id": str(ticket["_id"]) if ticket else None,
            "ticket_code": ticket["ticket_code"] if ticket else None,
            "ticket_status": ticket_status,
            "checked_in": checked_in,
            "scanned_at": scanned_at
        }
    }

@router.get("/tickets", response_model=PortalTicketListResponse)
def get_portal_tickets(
    current_user: dict = Depends(require_attendee),
    db: Database = Depends(get_db)
):
    """
    Lists all tickets belonging to the authenticated attendee.
    """
    email_normalized = current_user["email"].strip().lower()
    
    participants = list(db.participants.find({"email": email_normalized, "is_active": True}))
    if not participants:
        return {"success": True, "data": []}
        
    participant_ids = [p["_id"] for p in participants]
    tickets = list(db.tickets.find({"participant_id": {"$in": participant_ids}}))
    if not tickets:
        return {"success": True, "data": []}
        
    response_data = []
    for ticket in tickets:
        event = db.events.find_one({"_id": ticket["event_id"]})
        if not event:
            continue
            
        ticket_status = ticket.get("status")
        expires_at = ticket["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if ticket_status == "active" and datetime.now(timezone.utc) >= expires_at:
            ticket_status = "expired"
            
        response_data.append({
            "id": str(ticket["_id"]),
            "ticket_code": ticket["ticket_code"],
            "status": ticket_status,
            "expires_at": ticket["expires_at"],
            "event_name": event["name"],
            "venue": event["venue"],
            "date": event["date"],
            "time": f"{event['start_time']} - {event['end_time']}"
        })
        
    return {
        "success": True,
        "data": response_data
    }

@router.get("/tickets/{ticket_id}", response_model=PortalTicketDetailResponse)
def get_portal_ticket_detail(
    ticket_id: str,
    current_user: dict = Depends(require_attendee),
    db: Database = Depends(get_db)
):
    """
    Retrieves full details of a specific ticket, protected against IDOR.
    """
    ticket_obj_id = str_to_object_id(ticket_id)
    email_normalized = current_user["email"].strip().lower()
    
    ticket = db.tickets.find_one({"_id": ticket_obj_id})
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Ticket not found."
            }
        )
        
    part = db.participants.find_one({
        "_id": ticket["participant_id"], 
        "email": email_normalized, 
        "is_active": True
    })
    if not part:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCESS_DENIED",
                "message": "Access to this ticket is forbidden."
            }
        )
        
    event = db.events.find_one({"_id": ticket["event_id"]})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Associated event not found."
            }
        )
        
    ticket_status = ticket.get("status")
    expires_at = ticket["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if ticket_status == "active" and datetime.now(timezone.utc) >= expires_at:
        ticket_status = "expired"

    checked_in = ticket_status == "used"
    scanned_at = None
    if checked_in:
        attendance = db.attendance.find_one({"ticket_id": ticket["_id"]})
        if attendance:
            scanned_at = attendance["scanned_at"]
            
    return {
        "success": True,
        "data": {
            "id": str(ticket["_id"]),
            "ticket_code": ticket["ticket_code"],
            "status": ticket_status,
            "expires_at": ticket["expires_at"],
            "event_name": event["name"],
            "venue": event["venue"],
            "date": event["date"],
            "time": f"{event['start_time']} - {event['end_time']}",
            "timezone": event["timezone"],
            "participant_name": part["name"],
            "qr_payload": f"{settings.FRONTEND_URL}/tickets/{ticket['token']}",
            "checked_in": checked_in,
            "scanned_at": scanned_at
        }
    }

@router.get("/tickets/{ticket_id}/qr", response_model=PortalTicketQrResponse)
def get_portal_ticket_qr(
    ticket_id: str,
    current_user: dict = Depends(require_attendee),
    db: Database = Depends(get_db)
):
    """
    Generates a cryptographically secure 60-second rotating QR challenge token for the attendee's ticket.
    Verifies ownership, active ticket state, and inserts challenge to database.
    """
    ticket_obj_id = str_to_object_id(ticket_id)
    email_normalized = current_user["email"].strip().lower()
    
    # 1. Fetch ticket and verify existence
    ticket = db.tickets.find_one({"_id": ticket_obj_id})
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Ticket not found."
            }
        )
        
    # 2. IDOR Protection: Verify participant registration matches email
    part = db.participants.find_one({
        "_id": ticket["participant_id"], 
        "email": email_normalized, 
        "is_active": True
    })
    if not part:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCESS_DENIED",
                "message": "Access to this ticket is forbidden."
            }
        )
        
    # 3. Check ticket state: must be active
    if ticket["status"] == "used":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "TICKET_ALREADY_USED",
                "message": "Ticket has already been checked in. QR cannot be generated."
            }
        )
    if ticket["status"] == "revoked":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "TICKET_REVOKED",
                "message": "This ticket has been revoked."
            }
        )

    # 4. Check if associated event is active
    event = db.events.find_one({"_id": ticket["event_id"]})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Associated event not found."
            }
        )
    if event["status"] != EventStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EVENT_NOT_ACTIVE",
                "message": "Event is not active."
            }
        )

    # 5. Generate secure nonce (jti) and expiration
    jti = secrets.token_hex(16)
    now_utc = datetime.now(timezone.utc)
    expires_at = now_utc + timedelta(seconds=settings.QR_TOKEN_TTL_SECONDS)
    
    # 6. Cryptographically protect QR challenge using JWT HS256
    qr_payload_claims = {
        "ticket_id": str(ticket_obj_id),
        "event_id": str(ticket["event_id"]),
        "email": email_normalized,
        "jti": jti,
        "exp": int(expires_at.timestamp()),
        "iat": int(now_utc.timestamp()),
        "token_type": "qr_challenge"
    }
    qr_token = jwt.encode(qr_payload_claims, settings.SECRET_KEY, algorithm="HS256")

    # 7. Insert challenge document to DB
    challenge_doc = {
        "jti": jti,
        "ticket_id": ticket_obj_id,
        "event_id": ticket["event_id"],
        "issued_at": now_utc,
        "expires_at": expires_at,
        "consumed_at": None,
        "consumed_by": None,
        "status": "issued"
    }
    db.ticket_challenges.insert_one(challenge_doc)
    
    # 8. Log Audit Log for QR issuance
    log_audit(
        db=db,
        action="QR_CHALLENGE_ISSUED",
        actor_id=current_user["_id"],
        actor_email=email_normalized,
        target_type="ticket",
        target_id=ticket_obj_id,
        status=AuditStatus.SUCCESS,
        metadata={"jti": jti, "expires_at": expires_at.isoformat()}
    )
    
    return {
        "success": True,
        "data": {
            "qr_token": qr_token,
            "expires_at": expires_at,
            "server_time": now_utc
        }
    }

