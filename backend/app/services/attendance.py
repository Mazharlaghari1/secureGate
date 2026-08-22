from datetime import datetime, timezone
from bson import ObjectId
from pymongo.database import Database
from fastapi import HTTPException, status
from app.models.constants import EventStatus, AuditStatus
from app.services.audit import log_audit

import jwt
from app.config import settings

def verify_and_check_in_ticket(
    db: Database,
    current_user: dict,
    token: str,
    event_id: ObjectId
) -> dict:
    """
    Authoritatively verifies a ticket by its rotating QR challenge token and registers a check-in.
    Enforces cryptographic signature checks, temporal validity with leeway, jti single-use
    replay protection, and executes atomic ticket status transitions.
    """
    # 1. Decode and cryptographically validate the rotating QR challenge token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"], leeway=3)
    except jwt.ExpiredSignatureError:
        # Check audit log if possible, but first raise QR_EXPIRED
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "QR_EXPIRED",
                "message": "The QR code has expired."
            }
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_QR",
                "message": "The scanned QR signature or format is invalid."
            }
        )

    # 2. Extract claims and validate type
    token_type = payload.get("token_type")
    if token_type != "qr_challenge":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_QR",
                "message": "Invalid token type."
            }
        )

    ticket_id_claim = payload.get("ticket_id")
    event_id_claim = payload.get("event_id")
    jti = payload.get("jti")

    if not ticket_id_claim or not event_id_claim or not jti:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_QR",
                "message": "QR token claims are incomplete."
            }
        )

    # 3. Match scanner event context with QR claim event
    if event_id_claim != str(event_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "TICKET_WRONG_EVENT",
                "message": "This ticket belongs to another event."
            }
        )

    ticket_obj_id = ObjectId(ticket_id_claim)

    # 4. Retrieve ticket document
    ticket = db.tickets.find_one({"_id": ticket_obj_id})
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TICKET_INVALID",
                "message": "Ticket does not exist."
            }
        )

    # 5. Check ticket state
    if ticket["status"] == "used":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "TICKET_ALREADY_USED",
                "message": "Ticket has already been checked in."
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

    # 6. Retrieve and check event status
    event = db.events.find_one({"_id": event_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Selected event not found."
            }
        )
    if event["status"] != EventStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EVENT_NOT_ACTIVE",
                "message": f"Event check-in is not open. Event status is '{event['status']}'."
            }
        )

    # 7. Check ticket expiration
    now_utc = datetime.now(timezone.utc)
    ticket_expires_at = ticket["expires_at"]
    if ticket_expires_at.tzinfo is None:
        ticket_expires_at = ticket_expires_at.replace(tzinfo=timezone.utc)
    if now_utc >= ticket_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "TICKET_EXPIRED",
                "message": "Ticket has expired."
            }
        )

    # 8. Check challenge validity and replay prevention
    challenge = db.ticket_challenges.find_one({"jti": jti})
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_QR",
                "message": "Invalid challenge code."
            }
        )
    if challenge.get("status") == "consumed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "TICKET_ALREADY_USED",
                "message": "This challenge has already been used."
            }
        )

    # 9. Verify participant profile
    participant = db.participants.find_one({"_id": ticket["participant_id"]})
    if not participant or not participant.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PARTICIPANT_INACTIVE",
                "message": "The participant profile is inactive."
            }
        )

    scanned_at_time = datetime.now(timezone.utc)

    # 10. Execute atomic updates for double check-in prevention
    def do_check_in(session):
        # Consume the QR challenge atomically
        updated_challenge = db.ticket_challenges.find_one_and_update(
            {
                "jti": jti,
                "status": "issued"
            },
            {
                "$set": {
                    "status": "consumed",
                    "consumed_at": scanned_at_time,
                    "consumed_by": current_user["_id"]
                }
            },
            session=session,
            return_document=True
        )

        if not updated_challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "TICKET_ALREADY_USED",
                    "message": "This QR challenge has already been consumed."
                }
            )

        # Mark ticket checked in atomically
        updated_ticket = db.tickets.find_one_and_update(
            {
                "_id": ticket_obj_id,
                "status": "active"
            },
            {
                "$set": {
                    "status": "used",
                    "updated_at": scanned_at_time
                }
            },
            session=session,
            return_document=True
        )

        if not updated_ticket:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "TICKET_ALREADY_USED",
                    "message": "Ticket has already been checked in."
                }
            )

        try:
            db.attendance.insert_one({
                "event_id": event_id,
                "ticket_id": ticket_obj_id,
                "participant_id": ticket["participant_id"],
                "scanned_by": current_user["_id"],
                "scanned_at": scanned_at_time
            }, session=session)
        except Exception as e:
            if not session:
                # Manual rollback for standalone MongoDB dev setup
                db.tickets.update_one(
                    {"_id": ticket_obj_id},
                    {"$set": {"status": "active", "updated_at": datetime.now(timezone.utc)}}
                )
                db.ticket_challenges.update_one(
                    {"jti": jti},
                    {"$set": {"status": "issued", "consumed_at": None, "consumed_by": None}}
                )
            raise e

    # 11. Run under Transaction or standard execution
    try:
        with db.client.start_session() as session:
            with session.start_transaction():
                do_check_in(session)
    except Exception as e:
        if "Transaction numbers are only allowed" in str(e) or "sessions are not supported" in str(e):
            do_check_in(None)
        else:
            raise e

    # 12. Audit scan success
    log_audit(
        db=db,
        action="TICKET_CHECKED_IN",
        actor_id=current_user["_id"],
        actor_email=current_user["email"],
        target_type="ticket",
        target_id=ticket["_id"],
        status=AuditStatus.SUCCESS,
        metadata={"ticket_code": ticket["ticket_code"]}
    )

    return {
        "status": "valid",
        "participant": {
            "name": participant["name"]
        },
        "ticket_code": ticket["ticket_code"],
        "event": {
            "name": event["name"]
        },
        "scanned_at": scanned_at_time,
        "scanned_by": {
            "name": current_user["name"]
        }
    }

def list_staff_scans(
    db: Database,
    user_id: ObjectId,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """
    Lists checking sessions executed strictly by the authenticated staff user.
    """
    query = {"scanned_by": user_id}
    skip = (page - 1) * page_size
    cursor = db.attendance.find(query).skip(skip).limit(page_size).sort("scanned_at", -1)

    items = []
    for att in cursor:
        ticket = db.tickets.find_one({"_id": att["ticket_id"]})
        participant = db.participants.find_one({"_id": att["participant_id"]})
        event = db.events.find_one({"_id": att["event_id"]})

        items.append({
            "ticket_code": ticket["ticket_code"] if ticket else "N/A",
            "participant_name": participant["name"] if participant else "N/A",
            "event_name": event["name"] if event else "N/A",
            "scanned_at": att["scanned_at"],
            "status": "valid"
        })

    total = db.attendance.count_documents(query)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }
