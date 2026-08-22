import json
from datetime import datetime, timedelta, timezone
import pytest
from bson import ObjectId

from app.config import settings
from app.database import db_manager
from app.security.auth import hash_password, create_access_token
from app.models.constants import UserRole, EventStatus, AuditStatus

@pytest.fixture(autouse=True)
def clean_db():
    try:
        db = db_manager.get_db()
        db.users.delete_many({})
        db.events.delete_many({})
        db.participants.delete_many({})
        db.audit_logs.delete_many({})
    except Exception:
        pytest.skip("MongoDB not running, skipping database cleanup.")
    yield

@pytest.fixture
def test_admin():
    db = db_manager.get_db()
    admin_data = {
        "name": "Test Admin",
        "email": "admin@test.com",
        "password_hash": hash_password("adminpassword"),
        "role": UserRole.ADMIN.value,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    result = db.users.insert_one(admin_data)
    admin_data["_id"] = result.inserted_id
    return admin_data

@pytest.fixture
def test_staff():
    db = db_manager.get_db()
    staff_data = {
        "name": "Test Staff",
        "email": "staff@test.com",
        "password_hash": hash_password("staffpassword"),
        "role": UserRole.STAFF.value,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    result = db.users.insert_one(staff_data)
    staff_data["_id"] = result.inserted_id
    return staff_data

def get_auth_headers(user):
    token = create_access_token(data={
        "sub": str(user["_id"]),
        "email": user["email"],
        "role": user["role"]
    })
    return {"Authorization": f"Bearer {token}"}

# --- EVENT TESTS ---

# 1. Admin Creates Event
def test_admin_create_event(client, test_admin):
    headers = get_auth_headers(test_admin)
    response = client.post("/api/events", json={
        "name": "Annual Gala 2026",
        "description": "Annual fundraising gala dinner.",
        "venue": "Grand Ballroom",
        "date": "2026-09-01",
        "start_time": "18:00",
        "end_time": "22:00",
        "capacity": 100,
        "timezone": "Asia/Karachi"
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "draft"
    assert data["data"]["name"] == "Annual Gala 2026"
    assert "utc_start" in data["data"]

# 2. Staff Cannot Create Event
def test_staff_cannot_create_event(client, test_staff):
    headers = get_auth_headers(test_staff)
    response = client.post("/api/events", json={
        "name": "Staff Gala",
        "venue": "Hotel",
        "date": "2026-09-01",
        "start_time": "18:00",
        "end_time": "22:00",
        "capacity": 50,
        "timezone": "Asia/Karachi"
    }, headers=headers)
    assert response.status_code == 403

# 3. Event Validation (capacity < 1, format invalid)
def test_event_validation(client, test_admin):
    headers = get_auth_headers(test_admin)
    response = client.post("/api/events", json={
        "name": "",  # Empty name
        "venue": "Venue",
        "date": "invalid-date",
        "start_time": "12:00",
        "end_time": "13:00",
        "capacity": 0,  # Invalid capacity
        "timezone": "Asia/Karachi"
    }, headers=headers)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"

# 4. Invalid Timezone
def test_event_invalid_timezone(client, test_admin):
    headers = get_auth_headers(test_admin)
    response = client.post("/api/events", json={
        "name": "Invalid Timezone Event",
        "venue": "Grand Hall",
        "date": "2026-09-01",
        "start_time": "18:00",
        "end_time": "22:00",
        "capacity": 100,
        "timezone": "Invalid/TimeZone_Name"
    }, headers=headers)
    assert response.status_code == 422
    data = response.json()
    assert "timezone" in data["error"]["details"]

# 4b. Valid Timezone Asia/Karachi Regression Test
def test_event_valid_timezone_karachi(client, test_admin):
    headers = get_auth_headers(test_admin)
    response = client.post("/api/events", json={
        "name": "Valid Timezone Event",
        "venue": "Grand Hall",
        "date": "2026-09-01",
        "start_time": "18:00",
        "end_time": "22:00",
        "capacity": 100,
        "timezone": "Asia/Karachi"
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["timezone"] == "Asia/Karachi"


# 5. Event Listing
def test_event_listing(client, test_admin, test_staff):
    # Setup - Admin creates two events
    headers = get_auth_headers(test_admin)
    client.post("/api/events", json={
        "name": "Event A", "venue": "V1", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 10, "timezone": "UTC"
    }, headers=headers)
    client.post("/api/events", json={
        "name": "Event B", "venue": "V2", "date": "2026-09-02", "start_time": "14:00", "end_time": "16:00", "capacity": 20, "timezone": "UTC"
    }, headers=headers)

    # Listing as Staff (Staff can list events)
    staff_headers = get_auth_headers(test_staff)
    response = client.get("/api/events?page=1&page_size=20", headers=staff_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["total"] == 2

    # Listing with search
    response = client.get("/api/events?search=Event A", headers=staff_headers)
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Event A"

# 6. Event Detail
def test_event_detail(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Detail Event", "venue": "Venue", "date": "2026-09-01", "start_time": "18:00", "end_time": "20:00", "capacity": 100, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]

    staff_headers = get_auth_headers(test_staff)
    response = client.get(f"/api/events/{event_id}", headers=staff_headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Detail Event"

    # Unknown event
    unknown_id = str(ObjectId())
    response = client.get(f"/api/events/{unknown_id}", headers=staff_headers)
    assert response.status_code == 404

# 7. Admin Updates Event
def test_admin_update_event(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Gala V1", "venue": "Hall A", "date": "2026-09-01", "start_time": "18:00", "end_time": "20:00", "capacity": 100, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]

    response = client.put(f"/api/events/{event_id}", json={
        "name": "Gala V2",
        "capacity": 150
    }, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "Gala V2"
    assert data["data"]["capacity"] == 150

# 8. Staff Cannot Update Event
def test_staff_cannot_update_event(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "18:00", "end_time": "20:00", "capacity": 100, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]

    staff_headers = get_auth_headers(test_staff)
    response = client.put(f"/api/events/{event_id}", json={
        "name": "Staff Changed Name"
    }, headers=staff_headers)
    assert response.status_code == 403

# 9. Event Cancellation (DELETE sets status = cancelled)
def test_event_cancellation(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event to Cancel", "venue": "Hall B", "date": "2026-09-01", "start_time": "18:00", "end_time": "20:00", "capacity": 100, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]

    response = client.delete(f"/api/events/{event_id}", headers=headers)
    assert response.status_code == 200
    
    # Detail check
    response = client.get(f"/api/events/{event_id}", headers=headers)
    assert response.json()["data"]["status"] == "cancelled"

# 10. Cancelled Event Cannot Be Reactivated / Updated to draft/active
def test_cancelled_event_cannot_reactivate(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "18:00", "end_time": "20:00", "capacity": 100, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]

    # Cancel
    client.delete(f"/api/events/{event_id}", headers=headers)

    # Reactivate attempt
    response = client.put(f"/api/events/{event_id}", json={
        "status": "active"
    }, headers=headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_EVENT_STATUS_TRANSITION"

# 11. Completed Event Cannot Be Reopened
def test_completed_event_cannot_reopen(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "18:00", "end_time": "20:00", "capacity": 100, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]

    # Move to active
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    # Move to completed
    client.put(f"/api/events/{event_id}", json={"status": "completed"}, headers=headers)

    # Attempt to reopen to active
    response = client.put(f"/api/events/{event_id}", json={
        "status": "active"
    }, headers=headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_EVENT_STATUS_TRANSITION"

# 12. Invalid Status Transition
def test_invalid_status_transition(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "18:00", "end_time": "20:00", "capacity": 100, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]

    # Attempt status draft -> completed (invalid status jump)
    response = client.put(f"/api/events/{event_id}", json={
        "status": "completed"
    }, headers=headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_EVENT_STATUS_TRANSITION"


# --- PARTICIPANT TESTS ---

# 1. Admin Creates Participant
def test_admin_create_participant(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Active Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    response = client.post(f"/api/events/{event_id}/participants", json={
        "name": "Ali Ahmed",
        "email": "ali@example.com",
        "phone": "03001234567"
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Ali Ahmed"
    assert data["data"]["email"] == "ali@example.com"
    assert data["data"]["event_id"] == event_id

# 2. Staff Cannot Create Participant
def test_staff_cannot_create_participant(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    staff_headers = get_auth_headers(test_staff)
    response = client.post(f"/api/events/{event_id}/participants", json={
        "name": "Staff Added",
        "email": "staff_added@test.com"
    }, headers=staff_headers)
    assert response.status_code == 403

# 3. Participant Listing & 4. Pagination
def test_participant_listing(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Listing Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Add three participants
    client.post(f"/api/events/{event_id}/participants", json={"name": "Alice", "email": "a@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "Bob", "email": "b@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "Charlie", "email": "c@test.com"}, headers=headers)

    staff_headers = get_auth_headers(test_staff)
    response = client.get(f"/api/events/{event_id}/participants?page=1&page_size=2", headers=staff_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["total"] == 3

# 5. Search by Name / 6. Search by Email
def test_participant_search(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    client.post(f"/api/events/{event_id}/participants", json={"name": "Sara Khan", "email": "sara@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "Ali Ahmed", "email": "ali@test.com"}, headers=headers)

    staff_headers = get_auth_headers(test_staff)
    response = client.get(f"/api/events/{event_id}/participants?search=Sara", headers=staff_headers)
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Sara Khan"

    response = client.get(f"/api/events/{event_id}/participants?search=ali@test.com", headers=staff_headers)
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Ali Ahmed"

# 7. Participant Detail
def test_participant_detail(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    part_res = client.post(f"/api/events/{event_id}/participants", json={"name": "John Doe", "email": "john@test.com"}, headers=headers)
    part_id = part_res.json()["data"]["id"]

    staff_headers = get_auth_headers(test_staff)
    response = client.get(f"/api/participants/{part_id}", headers=staff_headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "John Doe"

# 8. Admin Update Participant
def test_admin_update_participant(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    part_res = client.post(f"/api/events/{event_id}/participants", json={"name": "John Doe", "email": "john@test.com"}, headers=headers)
    part_id = part_res.json()["data"]["id"]

    response = client.put(f"/api/participants/{part_id}", json={
        "name": "John Updated",
        "phone": "03331112223"
    }, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "John Updated"
    assert data["data"]["phone"] == "03331112223"

# 9. Staff Cannot Update Participant
def test_staff_cannot_update_participant(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    part_res = client.post(f"/api/events/{event_id}/participants", json={"name": "John Doe", "email": "john@test.com"}, headers=headers)
    part_id = part_res.json()["data"]["id"]

    staff_headers = get_auth_headers(test_staff)
    response = client.put(f"/api/participants/{part_id}", json={"name": "Staff Update Attempt"}, headers=staff_headers)
    assert response.status_code == 403

# 10. Duplicate Email within Same Event Rejected
def test_duplicate_email_same_event(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "dup@test.com"}, headers=headers)
    
    response = client.post(f"/api/events/{event_id}/participants", json={"name": "P2", "email": "dup@test.com"}, headers=headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"

# 11. Same Email Allowed in Different Events
def test_same_email_different_events(client, test_admin):
    headers = get_auth_headers(test_admin)
    # Event 1
    res1 = client.post("/api/events", json={
        "name": "Event 1", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id1 = res1.json()["data"]["id"]
    client.put(f"/api/events/{event_id1}", json={"status": "active"}, headers=headers)

    # Event 2
    res2 = client.post("/api/events", json={
        "name": "Event 2", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id2 = res2.json()["data"]["id"]
    client.put(f"/api/events/{event_id2}", json={"status": "active"}, headers=headers)

    # Add to Event 1
    response1 = client.post(f"/api/events/{event_id1}/participants", json={"name": "Participant One", "email": "same@test.com"}, headers=headers)
    assert response1.status_code == 201

    # Add to Event 2 (Allowed)
    response2 = client.post(f"/api/events/{event_id2}/participants", json={"name": "Participant Two", "email": "same@test.com"}, headers=headers)
    assert response2.status_code == 201

# 12. Email Normalization
def test_email_normalization(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    response = client.post(f"/api/events/{event_id}/participants", json={
        "name": "Normalized Email",
        "email": "   Ali@Example.COM   "
    }, headers=headers)
    assert response.status_code == 201
    assert response.json()["data"]["email"] == "ali@example.com"

# 13. Invalid Event ID Format
def test_invalid_event_id_format(client, test_admin):
    headers = get_auth_headers(test_admin)
    response = client.post("/api/events/invalid-id/participants", json={
        "name": "Participant",
        "email": "p@test.com"
    }, headers=headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

# 14. Unknown Event
def test_unknown_event(client, test_admin):
    headers = get_auth_headers(test_admin)
    unknown_id = str(ObjectId())
    response = client.post(f"/api/events/{unknown_id}/participants", json={
        "name": "Participant",
        "email": "p@test.com"
    }, headers=headers)
    assert response.status_code == 404

# 15. Participant Cannot Be Added After Capacity Reached
def test_participant_capacity_reached(client, test_admin):
    headers = get_auth_headers(test_admin)
    # Event capacity = 2
    res = client.post("/api/events", json={
        "name": "Small Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 2, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Register 2 (Allowed)
    client.post(f"/api/events/{event_id}/participants", json={"name": "Participant One", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "Participant Two", "email": "p2@test.com"}, headers=headers)

    # Register 3rd (Fails)
    response = client.post(f"/api/events/{event_id}/participants", json={"name": "Participant Three", "email": "p3@test.com"}, headers=headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EVENT_CAPACITY_REACHED"

# 16. Participant Cannot Be Added to Cancelled Event
def test_add_participant_cancelled_event(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]

    # Cancel
    client.delete(f"/api/events/{event_id}", headers=headers)

    # Attempt register
    response = client.post(f"/api/events/{event_id}/participants", json={"name": "Participant", "email": "p@test.com"}, headers=headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_EVENT_STATUS_TRANSITION"

# 17. Participant Cannot Be Added to Completed Event
def test_add_participant_completed_event(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]

    # Activate
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    # Complete
    client.put(f"/api/events/{event_id}", json={"status": "completed"}, headers=headers)

    # Attempt register
    response = client.post(f"/api/events/{event_id}/participants", json={"name": "Participant", "email": "p@test.com"}, headers=headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_EVENT_STATUS_TRANSITION"

# 18. Safe Participant Deletion/Deactivation
def test_safe_participant_deactivation(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    part_res = client.post(f"/api/events/{event_id}/participants", json={"name": "John Doe", "email": "john@test.com"}, headers=headers)
    part_id = part_res.json()["data"]["id"]

    # Deactivate
    response = client.delete(f"/api/participants/{part_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "deactivated"

    # Verify is_active flag in DB
    db = db_manager.get_db()
    participant = db.participants.find_one({"_id": ObjectId(part_id)})
    assert participant["is_active"] is False

# 19. Audit Logs Generated
def test_event_participant_audit_logs(client, test_admin):
    headers = get_auth_headers(test_admin)
    # Create event
    res = client.post("/api/events", json={
        "name": "Audited Event", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    
    # Activate event
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Register participant
    client.post(f"/api/events/{event_id}/participants", json={"name": "Audited Participant", "email": "audit@test.com"}, headers=headers)

    db = db_manager.get_db()
    
    # Verify EVENT_CREATED audit
    created_log = db.audit_logs.find_one({"action": "EVENT_CREATED", "target_id": ObjectId(event_id)})
    assert created_log is not None
    assert created_log["actor_email"] == test_admin["email"]

    # Verify EVENT_STATUS_CHANGED audit
    status_log = db.audit_logs.find_one({"action": "EVENT_STATUS_CHANGED", "target_id": ObjectId(event_id)})
    assert status_log is not None

    # Verify PARTICIPANT_CREATED audit
    p_log = db.audit_logs.find_one({"action": "PARTICIPANT_CREATED"})
    assert p_log is not None
