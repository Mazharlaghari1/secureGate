from datetime import datetime, timezone
import csv
import io
import logging
from bson import ObjectId
from typing import Optional
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status
from pydantic import ValidationError
from app.models.constants import EventStatus, AuditStatus
from app.services.audit import log_audit
from app.services.events import get_event_by_id
from app.schemas.participants import ParticipantCreate

logger = logging.getLogger("event_access")

def create_participant(
    db: Database,
    current_admin: dict,
    event_id: ObjectId,
    name: str,
    email: str,
    phone: Optional[str]
) -> dict:
    """
    Creates a participant under an event. Enforces capacity limits and uniqueness constraints.
    Checks that the event is active (not cancelled or completed). Audits PARTICIPANT_CREATED.
    """
    event = get_event_by_id(db, event_id)

    event_status = event.get("status")
    if event_status == EventStatus.CANCELLED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_EVENT_STATUS_TRANSITION",
                "message": "Cannot register a participant for a cancelled event."
            }
        )
    if event_status == EventStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_EVENT_STATUS_TRANSITION",
                "message": "Cannot register a participant for a completed event."
            }
        )

    # Count active participants
    current_count = db.participants.count_documents({
        "event_id": event_id,
        "is_active": True
    })
    if current_count >= event.get("capacity", 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EVENT_CAPACITY_REACHED",
                "message": f"Event capacity limit of {event['capacity']} is reached."
            }
        )

    email_normalized = email.strip().lower()

    # Check for duplicate registration
    existing = db.participants.find_one({
        "event_id": event_id,
        "email": email_normalized,
        "is_active": True
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONFLICT",
                "message": f"Participant with email '{email_normalized}' is already registered for this event."
            }
        )

    now_utc = datetime.now(timezone.utc)
    participant_doc = {
        "event_id": event_id,
        "name": name.strip(),
        "email": email_normalized,
        "phone": phone.strip() if phone else "",
        "is_active": True,
        "created_at": now_utc,
        "updated_at": now_utc
    }

    try:
        result = db.participants.insert_one(participant_doc)
        participant_doc["_id"] = result.inserted_id

        log_audit(
            db=db,
            action="PARTICIPANT_CREATED",
            actor_id=current_admin["_id"],
            actor_email=current_admin["email"],
            target_type="participant",
            target_id=result.inserted_id,
            status=AuditStatus.SUCCESS,
            metadata={"event_id": str(event_id), "email": email_normalized}
        )

        return participant_doc
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONFLICT",
                "message": f"Participant with email '{email_normalized}' is already registered for this event."
            }
        )

def list_participants(
    db: Database,
    event_id: ObjectId,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None
) -> dict:
    """
    Lists participants registered under an event with queries and pagination.
    """
    query = {"event_id": event_id, "is_active": True}

    if search:
        clean_search = search.strip()
        query["$or"] = [
            {"name": {"$regex": clean_search, "$options": "i"}},
            {"email": {"$regex": clean_search, "$options": "i"}},
            {"phone": {"$regex": clean_search, "$options": "i"}}
        ]

    skip = (page - 1) * page_size
    cursor = db.participants.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    items = list(cursor)
    total = db.participants.count_documents(query)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

def get_participant_by_id(db: Database, participant_id: ObjectId) -> dict:
    """
    Retrieves safe detail fields for a single participant.
    """
    participant = db.participants.find_one({"_id": participant_id})
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Participant not found."
            }
        )
    return participant

def update_participant(
    db: Database,
    current_admin: dict,
    participant_id: ObjectId,
    update_fields: dict
) -> dict:
    """
    Updates participant profile details (name, email, phone). Blocks event transfers.
    Re-validates email uniqueness if updated. Audits edits.
    """
    participant = db.participants.find_one({"_id": participant_id})
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Participant not found."
            }
        )

    if "event_id" in update_fields:
        update_fields.pop("event_id")

    update_data = {"updated_at": datetime.now(timezone.utc)}
    metadata = {}

    if "name" in update_fields and update_fields["name"] is not None:
        update_data["name"] = update_fields["name"].strip()
        metadata["name"] = update_data["name"]

    if "phone" in update_fields:
        phone = update_fields["phone"]
        update_data["phone"] = phone.strip() if phone else ""
        metadata["phone"] = update_data["phone"]

    if "email" in update_fields and update_fields["email"] is not None:
        email_normalized = update_fields["email"].strip().lower()
        if email_normalized != participant["email"]:
            existing = db.participants.find_one({
                "event_id": participant["event_id"],
                "email": email_normalized,
                "is_active": True
            })
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "CONFLICT",
                        "message": f"Participant with email '{email_normalized}' is already registered for this event."
                    }
                )
            update_data["email"] = email_normalized
            metadata["email"] = email_normalized

    if "is_active" in update_fields and update_fields["is_active"] is not None:
        update_data["is_active"] = update_fields["is_active"]
        metadata["is_active"] = update_fields["is_active"]

    db.participants.update_one({"_id": participant_id}, {"$set": update_data})
    updated_participant = db.participants.find_one({"_id": participant_id})

    log_audit(
        db=db,
        action="PARTICIPANT_UPDATED",
        actor_id=current_admin["_id"],
        actor_email=current_admin["email"],
        target_type="participant",
        target_id=participant_id,
        status=AuditStatus.SUCCESS,
        metadata=metadata
    )

    return updated_participant

def deactivate_participant(db: Database, current_admin: dict, participant_id: ObjectId) -> dict:
    """
    Deactivates a participant by marking is_active = False to preserve historical integrity.
    Audits PARTICIPANT_DEACTIVATED.
    """
    participant = db.participants.find_one({"_id": participant_id})
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Participant not found."
            }
        )

    if not participant.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "BAD_REQUEST",
                "message": "Participant is already inactive."
            }
        )

    db.participants.update_one(
        {"_id": participant_id},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    log_audit(
        db=db,
        action="PARTICIPANT_DEACTIVATED",
        actor_id=current_admin["_id"],
        actor_email=current_admin["email"],
        target_type="participant",
        target_id=participant_id,
        status=AuditStatus.SUCCESS
    )

    return {"status": "deactivated"}

def import_participants_csv(
    db: Database,
    current_admin: dict,
    event_id: ObjectId,
    content: bytes
) -> dict:
    """
    Validates and imports participants in bulk from CSV byte content.
    Enforces file checks, validation pipeline, capacity, and all-or-nothing atomicity.
    """
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        log_audit(
            db=db,
            action="CSV_BULK_IMPORT_FAILURE",
            actor_id=current_admin["_id"],
            actor_email=current_admin["email"],
            target_type="event",
            target_id=event_id,
            status=AuditStatus.FAILURE,
            metadata={"message": "Could not decode CSV as UTF-8."}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Could not decode CSV file as UTF-8."
            }
        )

    csv_file = io.StringIO(csv_text)
    reader = csv.reader(csv_file)

    try:
        header = next(reader)
    except StopIteration:
        log_audit(
            db=db,
            action="CSV_BULK_IMPORT_FAILURE",
            actor_id=current_admin["_id"],
            actor_email=current_admin["email"],
            target_type="event",
            target_id=event_id,
            status=AuditStatus.FAILURE,
            metadata={"message": "CSV file is empty."}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "CSV file is empty."
            }
        )

    # Validate header matches name,email,phone strictly
    if header != ["name", "email", "phone"]:
        log_audit(
            db=db,
            action="CSV_BULK_IMPORT_FAILURE",
            actor_id=current_admin["_id"],
            actor_email=current_admin["email"],
            target_type="event",
            target_id=event_id,
            status=AuditStatus.FAILURE,
            metadata={"message": "Invalid CSV header."}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "CSV validation failed",
                "details": {
                    "errors": [
                        {
                            "row": 1,
                            "field": "header",
                            "message": "CSV header must be exactly 'name,email,phone'"
                        }
                    ]
                }
            }
        )

    errors = []
    parsed_rows = []
    inner_emails = set()

    for idx, row in enumerate(reader, start=2):
        if not row or all(cell.strip() == "" for cell in row):
            continue

        if len(row) != 3:
            errors.append({
                "row": idx,
                "field": "row",
                "message": f"Row must have exactly 3 columns, found {len(row)}."
            })
            continue

        name, email, phone = row

        try:
            p = ParticipantCreate(
                name=name,
                email=email,
                phone=phone or None
            )
            normalized_name = p.name
            normalized_email = p.email
            normalized_phone = p.phone or ""
        except ValidationError as val_err:
            for e in val_err.errors():
                field_name = e["loc"][0] if e["loc"] else "row"
                errors.append({
                    "row": idx,
                    "field": field_name,
                    "message": e["msg"]
                })
            continue
        except Exception as e:
            errors.append({
                "row": idx,
                "field": "row",
                "message": str(e)
            })
            continue

        if normalized_email in inner_emails:
            errors.append({
                "row": idx,
                "field": "email",
                "message": f"Duplicate email address inside CSV: '{normalized_email}'"
            })
        else:
            inner_emails.add(normalized_email)

        parsed_rows.append({
            "row": idx,
            "name": normalized_name,
            "email": normalized_email,
            "phone": normalized_phone
        })

    if errors:
        log_audit(
            db=db,
            action="CSV_BULK_IMPORT_FAILURE",
            actor_id=current_admin["_id"],
            actor_email=current_admin["email"],
            target_type="event",
            target_id=event_id,
            status=AuditStatus.FAILURE,
            metadata={"errors_count": len(errors)}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "CSV validation failed",
                "details": {"errors": errors}
            }
        )

    # Validate event state and bounds
    event = get_event_by_id(db, event_id)
    if event["status"] != EventStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_EVENT_STATUS_TRANSITION",
                "message": f"Bulk import only allowed for active events. Current status is '{event['status']}'."
            }
        )

    # Database duplicate conflicts checking
    db_conflicts = []
    for p_row in parsed_rows:
        existing = db.participants.find_one({
            "event_id": event_id,
            "email": p_row["email"],
            "is_active": True
        })
        if existing:
            db_conflicts.append({
                "row": p_row["row"],
                "field": "email",
                "message": f"Participant with email '{p_row['email']}' is already registered for this event."
            })

    if db_conflicts:
        log_audit(
            db=db,
            action="CSV_BULK_IMPORT_FAILURE",
            actor_id=current_admin["_id"],
            actor_email=current_admin["email"],
            target_type="event",
            target_id=event_id,
            status=AuditStatus.FAILURE,
            metadata={"message": "Database duplicate conflicts detected.", "conflicts_count": len(db_conflicts)}
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONFLICT",
                "message": "CSV database duplicate conflicts detected",
                "details": {"errors": db_conflicts}
            }
        )

    # Capacity check
    current_count = db.participants.count_documents({
        "event_id": event_id,
        "is_active": True
    })
    csv_count = len(parsed_rows)
    if current_count + csv_count > event.get("capacity", 0):
        log_audit(
            db=db,
            action="CSV_BULK_IMPORT_FAILURE",
            actor_id=current_admin["_id"],
            actor_email=current_admin["email"],
            target_type="event",
            target_id=event_id,
            status=AuditStatus.FAILURE,
            metadata={"message": "Event capacity reached."}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EVENT_CAPACITY_REACHED",
                "message": f"Bulk import would exceed event capacity limit of {event['capacity']}."
            }
        )

    def do_insert(session):
        now_utc = datetime.now(timezone.utc)
        docs = []
        for p_row in parsed_rows:
            docs.append({
                "event_id": event_id,
                "name": p_row["name"],
                "email": p_row["email"],
                "phone": p_row["phone"],
                "is_active": True,
                "created_at": now_utc,
                "updated_at": now_utc
            })
        try:
            db.participants.insert_many(docs, session=session)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "CONFLICT",
                    "message": "Concurrent registration conflict: email already exists for this event."
                }
            )

    try:
        with db.client.start_session() as session:
            with session.start_transaction():
                do_insert(session)
    except Exception as e:
        if "Transaction numbers are only allowed" in str(e) or "sessions are not supported" in str(e):
            do_insert(None)
        else:
            raise e

    log_audit(
        db=db,
        action="CSV_BULK_IMPORT_SUCCESS",
        actor_id=current_admin["_id"],
        actor_email=current_admin["email"],
        target_type="event",
        target_id=event_id,
        status=AuditStatus.SUCCESS,
        metadata={"imported": csv_count}
    )

    return {"imported": csv_count}
