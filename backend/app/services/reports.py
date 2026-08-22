import csv
import io
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from bson import ObjectId
from pymongo.database import Database
from fastapi import HTTPException, status
from app.services.events import get_event_by_id

def get_dashboard_stats(db: Database) -> dict:
    """
    Computes top-level counts for all events, active events, active participants, and allocated tickets.
    """
    total_events = db.events.count_documents({})
    active_events = db.events.count_documents({"status": "active"})
    total_participants = db.participants.count_documents({"is_active": True})
    total_tickets = db.tickets.count_documents({})

    return {
        "total_events": total_events,
        "active_events": active_events,
        "total_registered_participants": total_participants,
        "total_allocated_tickets": total_tickets
    }

def get_event_stats(db: Database, event_id: ObjectId) -> dict:
    """
    Computes ticket counts, remaining quotas, check-in percentages,
    and groups scans hourly, localizing UTC timestamps to the event's local timezone.
    """
    event = get_event_by_id(db, event_id)

    tickets_issued = db.tickets.count_documents({"event_id": event_id})
    checked_in = db.tickets.count_documents({"event_id": event_id, "status": "used"})
    remaining = tickets_issued - checked_in
    attendance_pct = (checked_in / tickets_issued * 100) if tickets_issued > 0 else 0.0

    # Scans over time (hourly)
    attendance_records = list(db.attendance.find({"event_id": event_id}))
    local_tz = ZoneInfo(event.get("timezone", "Asia/Karachi"))

    hourly_counts = {}
    for att in attendance_records:
        # Convert UTC to local event timezone
        utc_scanned = att["scanned_at"].replace(tzinfo=timezone.utc)
        local_scanned = utc_scanned.astimezone(local_tz)
        hour_str = local_scanned.strftime("%H:00")
        hourly_counts[hour_str] = hourly_counts.get(hour_str, 0) + 1

    sorted_hours = sorted(hourly_counts.keys())
    check_ins_over_time = [
        {"hour": h, "count": hourly_counts[h]} for h in sorted_hours
    ]

    return {
        "tickets_issued": tickets_issued,
        "checked_in": checked_in,
        "remaining": remaining,
        "attendance_percentage": round(attendance_pct, 2),
        "check_ins_over_time": check_ins_over_time
    }

def generate_event_csv_report(db: Database, event_id: ObjectId) -> bytes:
    """
    Generates a secure check-in CSV export stream for an event.
    Ticket Codes are used as safe identifiers. **Secret tokens are strictly excluded.**
    """
    event = get_event_by_id(db, event_id)
    
    # Retrieve all attendance records for this event
    attendance_records = list(db.attendance.find({"event_id": event_id}).sort("scanned_at", 1))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Ticket Code",
        "Participant Name",
        "Participant Email",
        "Check-In Time",
        "Staff Name",
        "Status"
    ])

    for att in attendance_records:
        ticket = db.tickets.find_one({"_id": att["ticket_id"]})
        participant = db.participants.find_one({"_id": att["participant_id"]})
        staff = db.users.find_one({"_id": att["scanned_by"]})

        ticket_code = ticket["ticket_code"] if ticket else "N/A"
        part_name = participant["name"] if participant else "N/A"
        part_email = participant["email"] if participant else "N/A"
        scanned_at_iso = att["scanned_at"].replace(tzinfo=timezone.utc).isoformat()
        staff_name = staff["name"] if staff else "N/A"

        writer.writerow([
            ticket_code,
            part_name,
            part_email,
            scanned_at_iso,
            staff_name,
            "used"
        ])

    csv_data = output.getvalue()
    return csv_data.encode("utf-8")
