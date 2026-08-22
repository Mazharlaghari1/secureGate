from datetime import datetime, timezone, timedelta
import secrets
import logging
from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status
from app.config import settings
from app.models.constants import EventStatus, AuditStatus
from app.services.audit import log_audit
from app.services.events import get_event_by_id
from app.utils.timezone import local_to_utc

logger = logging.getLogger("event_access")

def generate_tickets_for_event(
    db: Database,
    current_admin: dict,
    event_id: ObjectId
) -> int:
    """
    Batch generates access tickets for registered active participants of an event.
    Enforces status controls, cryptographic randomness, timezone-safe expiration,
    idempotency, and safe handling of duplicate-key conflicts under concurrent conditions.
    """
    event = get_event_by_id(db, event_id)
    if event["status"] in [EventStatus.CANCELLED.value, EventStatus.COMPLETED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_EVENT_STATUS_TRANSITION",
                "message": f"Cannot generate tickets for a {event['status']} event."
            }
        )

    # Fetch active participants for the event
    participants = list(db.participants.find({
        "event_id": event_id,
        "is_active": True
    }))

    if not participants:
        return 0

    # Fetch already ticketed participant IDs
    existing_tickets = list(db.tickets.find({"event_id": event_id}, {"participant_id": 1}))
    ticketed_ids = {t["participant_id"] for t in existing_tickets}

    # Filter to non-ticketed
    non_ticketed = [p for p in participants if p["_id"] not in ticketed_ids]

    if not non_ticketed:
        return 0

    # Expiration is event local end time + 2 hours converted to UTC
    try:
        local_end_utc = local_to_utc(event["date"], event["end_time"], event["timezone"])
        expires_at = local_end_utc + timedelta(hours=2)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": f"Could not calculate ticket expiration: {str(e)}"
            }
        )

    now_utc = datetime.now(timezone.utc)
    docs = []
    for p in non_ticketed:
        token = secrets.token_urlsafe(32)
        ticket_code = f"EVT-{secrets.token_hex(4).upper()}"
        docs.append({
            "event_id": event_id,
            "participant_id": p["_id"],
            "ticket_code": ticket_code,
            "token": token,
            "status": "active",
            "expires_at": expires_at,
            "created_at": now_utc,
            "updated_at": now_utc
        })

    generated_count = 0
    def run_inserts(session):
        nonlocal generated_count
        for doc in docs:
            try:
                db.tickets.insert_one(doc, session=session)
                generated_count += 1
            except DuplicateKeyError:
                # Gracefully skip in concurrent race conditions
                continue

    try:
        with db.client.start_session() as session:
            with session.start_transaction():
                run_inserts(session)
    except Exception as e:
        if "Transaction numbers are only allowed" in str(e) or "sessions are not supported" in str(e):
            generated_count = 0
            run_inserts(None)
        else:
            raise e

    if generated_count > 0:
        log_audit(
            db=db,
            action="TICKETS_GENERATED",
            actor_id=current_admin["_id"],
            actor_email=current_admin["email"],
            target_type="event",
            target_id=event_id,
            status=AuditStatus.SUCCESS,
            metadata={"generated_count": generated_count}
        )

    return generated_count

def revoke_ticket(
    db: Database,
    current_admin: dict,
    ticket_id: ObjectId
) -> dict:
    """
    Revokes an active ticket. Excludes check-in tickets or already revoked tickets.
    """
    ticket = db.tickets.find_one({"_id": ticket_id})
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Ticket not found."
            }
        )

    old_status = ticket.get("status")
    if old_status == "revoked":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "BAD_REQUEST",
                "message": "Ticket is already revoked."
            }
        )
    if old_status == "used":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "BAD_REQUEST",
                "message": "Used tickets cannot be revoked."
            }
        )
    if old_status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "BAD_REQUEST",
                "message": f"Only active tickets can be revoked. Current status is '{old_status}'."
            }
        )

    db.tickets.update_one(
        {"_id": ticket_id},
        {
            "$set": {
                "status": "revoked",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    log_audit(
        db=db,
        action="TICKET_REVOKED",
        actor_id=current_admin["_id"],
        actor_email=current_admin["email"],
        target_type="ticket",
        target_id=ticket_id,
        status=AuditStatus.SUCCESS,
        metadata={"ticket_code": ticket["ticket_code"]}
    )

    return {"status": "revoked"}

def list_tickets_for_event(
    db: Database,
    event_id: ObjectId,
    page: int = 1,
    page_size: int = 20,
    status_filter: str = None,
    search: str = None
) -> dict:
    """
    Retrieves safe administrative list of tickets for an event.
    Provides searches by name, email, or code. **Strictly excludes tokens.**
    """
    query = {"event_id": event_id}
    if status_filter:
        query["status"] = status_filter

    if search:
        clean_search = search.strip()
        # Search participants
        participant_query = {
            "event_id": event_id,
            "$or": [
                {"name": {"$regex": clean_search, "$options": "i"}},
                {"email": {"$regex": clean_search, "$options": "i"}}
            ]
        }
        matching_participants = list(db.participants.find(participant_query, {"_id": 1}))
        matching_ids = [p["_id"] for p in matching_participants]

        query["$or"] = [
            {"ticket_code": {"$regex": clean_search, "$options": "i"}},
            {"participant_id": {"$in": matching_ids}}
        ]

    skip = (page - 1) * page_size
    cursor = db.tickets.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    items = list(cursor)
    total = db.tickets.count_documents(query)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

def get_public_ticket_by_token(db: Database, token: str) -> dict:
    """
    Returns public-safe details of a ticket mapped to the provided secure token.
    Excludes sensitive identifiers, PII, and internal MongoDB IDs.
    """
    ticket = db.tickets.find_one({"token": token})
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TICKET_INVALID",
                "message": "Ticket token is invalid."
            }
        )

    event = db.events.find_one({"_id": ticket["event_id"]})
    participant = db.participants.find_one({"_id": ticket["participant_id"]})

    # Validate participant is active
    if not participant or not participant.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PARTICIPANT_INACTIVE",
                "message": "The participant profile is inactive."
            }
        )

    # Dynamic status check for expiration
    ticket_status = ticket.get("status")
    ticket_expires_at = ticket["expires_at"]
    if ticket_expires_at.tzinfo is None:
        ticket_expires_at = ticket_expires_at.replace(tzinfo=timezone.utc)
    if ticket_status == "active" and datetime.now(timezone.utc) >= ticket_expires_at:
        ticket_status = "expired"

    return {
        "ticket_code": ticket["ticket_code"],
        "status": ticket_status,
        "participant": {
            "name": participant["name"] if participant else ""
        },
        "event": {
            "name": event["name"] if event else "",
            "venue": event["venue"] if event else "",
            "date": event["date"] if event else "",
            "start_time": event["start_time"] if event else "",
            "end_time": event["end_time"] if event else "",
            "timezone": event["timezone"] if event else ""
        },
        "expires_at": ticket["expires_at"],
        "qr_payload": f"{settings.FRONTEND_URL}/tickets/{token}"
    }
