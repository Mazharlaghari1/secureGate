from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional
from pymongo.database import Database
from fastapi import HTTPException, status
from app.utils.timezone import local_to_utc
from app.models.constants import EventStatus, AuditStatus
from app.services.audit import log_audit

def create_event(
    db: Database,
    current_admin: dict,
    name: str,
    description: Optional[str],
    venue: str,
    date: str,
    start_time: str,
    end_time: str,
    capacity: int,
    timezone_name: str
) -> dict:
    """
    Creates a new event with DRAFT status. Local date/times are converted
    to timezone-aware UTC timestamps for database storage. Audits EVENT_CREATED.
    """
    try:
        utc_start = local_to_utc(date, start_time, timezone_name)
        utc_end = local_to_utc(date, end_time, timezone_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": f"Could not interpret local event time bounds: {str(e)}"
            }
        )

    if utc_start >= utc_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Event start time must be strictly before end time."
            }
        )

    now_utc = datetime.now(timezone.utc)
    event_doc = {
        "name": name.strip(),
        "description": description.strip() if description else "",
        "venue": venue.strip(),
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "capacity": capacity,
        "timezone": timezone_name,
        "status": EventStatus.DRAFT.value,
        "utc_start": utc_start,
        "utc_end": utc_end,
        "created_at": now_utc,
        "updated_at": now_utc
    }

    result = db.events.insert_one(event_doc)
    event_doc["_id"] = result.inserted_id

    log_audit(
        db=db,
        action="EVENT_CREATED",
        actor_id=current_admin["_id"],
        actor_email=current_admin["email"],
        target_type="event",
        target_id=result.inserted_id,
        status=AuditStatus.SUCCESS,
        metadata={"name": name.strip()}
    )

    return event_doc

def list_events(
    db: Database,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    date_filter: Optional[str] = None,
    search: Optional[str] = None
) -> dict:
    """
    Retrieves a paginated list of events with query name search, date and status filters.
    """
    query = {}
    if status_filter:
        query["status"] = status_filter
    if date_filter:
        query["date"] = date_filter
    if search:
        query["name"] = {"$regex": search.strip(), "$options": "i"}

    skip = (page - 1) * page_size
    cursor = db.events.find(query).skip(skip).limit(page_size).sort("utc_start", 1)
    items = list(cursor)
    total = db.events.count_documents(query)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

def get_event_by_id(db: Database, event_id: ObjectId) -> dict:
    """
    Retrieves detail fields for a single event. Returns NOT_FOUND if it does not exist.
    """
    event = db.events.find_one({"_id": event_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Event not found."
            }
        )
    return event

def update_event(
    db: Database,
    current_admin: dict,
    event_id: ObjectId,
    update_fields: dict
) -> dict:
    """
    Updates event configurations. Validates status transitions and capacity limits.
    Recalculates timezone UTC bounds if local inputs change. Audits changes.
    """
    event = db.events.find_one({"_id": event_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Event not found."
            }
        )

    # Validate controlled lifecycle transitions
    if "status" in update_fields and update_fields["status"] is not None:
        old_status = event.get("status")
        new_status = update_fields["status"].value if hasattr(update_fields["status"], "value") else update_fields["status"]
        if old_status != new_status:
            valid_transition = False
            if old_status == EventStatus.DRAFT.value:
                if new_status in [EventStatus.ACTIVE.value, EventStatus.CANCELLED.value]:
                    valid_transition = True
            elif old_status == EventStatus.ACTIVE.value:
                if new_status in [EventStatus.COMPLETED.value, EventStatus.CANCELLED.value]:
                    valid_transition = True

            if not valid_transition:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_EVENT_STATUS_TRANSITION",
                        "message": f"Invalid status transition from '{old_status}' to '{new_status}'."
                    }
                )

    # Recalculate time parameters if any components change
    date = update_fields.get("date", event.get("date")) or event.get("date")
    start_time = update_fields.get("start_time", event.get("start_time")) or event.get("start_time")
    end_time = update_fields.get("end_time", event.get("end_time")) or event.get("end_time")
    timezone_name = update_fields.get("timezone", event.get("timezone")) or event.get("timezone")

    try:
        utc_start = local_to_utc(date, start_time, timezone_name)
        utc_end = local_to_utc(date, end_time, timezone_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": f"Could not interpret local event time bounds: {str(e)}"
            }
        )

    if utc_start >= utc_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Event start time must be strictly before end time."
            }
        )

    update_data = {
        "utc_start": utc_start,
        "utc_end": utc_end,
        "updated_at": datetime.now(timezone.utc)
    }

    # Map other fields
    for k, v in update_fields.items():
        if v is not None:
            val = v.value if hasattr(v, "value") else v
            if k in ["name", "description", "venue"]:
                update_data[k] = val.strip()
            elif k in ["capacity", "status", "timezone", "date", "start_time", "end_time"]:
                update_data[k] = val

    db.events.update_one({"_id": event_id}, {"$set": update_data})
    updated_event = db.events.find_one({"_id": event_id})

    action = "EVENT_UPDATED"
    if "status" in update_fields and update_fields["status"] != event.get("status"):
        action = "EVENT_STATUS_CHANGED"
        
    log_audit(
        db=db,
        action=action,
        actor_id=current_admin["_id"],
        actor_email=current_admin["email"],
        target_type="event",
        target_id=event_id,
        status=AuditStatus.SUCCESS,
        metadata={"changes": list(update_fields.keys())}
    )

    return updated_event

def cancel_event(db: Database, current_admin: dict, event_id: ObjectId) -> dict:
    """
    Sets event status to cancelled. Blocks cancellation of completed events.
    Excludes hard deletions. Audits EVENT_CANCELLED.
    """
    event = db.events.find_one({"_id": event_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Event not found."
            }
        )

    old_status = event.get("status")
    if old_status == EventStatus.CANCELLED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_EVENT_STATUS_TRANSITION",
                "message": "Event is already cancelled."
            }
        )
    if old_status == EventStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_EVENT_STATUS_TRANSITION",
                "message": "Completed events cannot be cancelled."
            }
        )

    db.events.update_one(
        {"_id": event_id},
        {
            "$set": {
                "status": EventStatus.CANCELLED.value,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    log_audit(
        db=db,
        action="EVENT_CANCELLED",
        actor_id=current_admin["_id"],
        actor_email=current_admin["email"],
        target_type="event",
        target_id=event_id,
        status=AuditStatus.SUCCESS
    )

    return {"status": "cancelled"}
