import json
from datetime import datetime, timedelta, timezone
import pytest
from bson import ObjectId
from unittest.mock import patch
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.config import settings
from app.database import db_manager
from app.security.auth import hash_password, create_access_token
from app.models.constants import UserRole, EventStatus, TicketStatus, AuditStatus

@pytest.fixture(autouse=True)
def clean_db():
    try:
        db = db_manager.get_db()
        db.users.delete_many({})
        db.events.delete_many({})
        db.participants.delete_many({})
        db.tickets.delete_many({})
        db.attendance.delete_many({})
        db.audit_logs.delete_many({})
    except Exception:
        pytest.skip("MongoDB not running, skipping database cleanup.")
    yield

def test_attendee_registration_and_login(client):
    # 1. Register attendee
    reg_payload = {
        "name": "Attendee One",
        "email": "attendee1@test.com",
        "password": "attendee1password"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201
    assert res.json()["success"] is True
    assert res.json()["data"]["email"] == "attendee1@test.com"
    assert res.json()["data"]["role"] == "attendee"

    # 2. Login
    login_payload = {
        "email": "attendee1@test.com",
        "password": "attendee1password"
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "token" in res.json()["data"]
    assert res.json()["data"]["user"]["role"] == "attendee"

def test_attendee_me_profile(client):
    db = db_manager.get_db()
    attendee_data = {
        "name": "Attendee User",
        "email": "attendee@test.com",
        "password_hash": hash_password("attpassword"),
        "role": UserRole.ATTENDEE.value,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_db = db.users.insert_one(attendee_data)
    token = create_access_token({"sub": str(res_db.inserted_id), "email": "attendee@test.com", "role": "attendee"})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/portal/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["email"] == "attendee@test.com"

    update_payload = {"name": "Updated Attendee"}
    res = client.put("/api/portal/profile", headers=headers, json=update_payload)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["name"] == "Updated Attendee"

def test_attendee_events_and_tickets(client):
    db = db_manager.get_db()
    attendee_data = {
        "name": "John Doe",
        "email": "john@test.com",
        "password_hash": hash_password("johnpassword"),
        "role": "attendee",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_db = db.users.insert_one(attendee_data)
    token = create_access_token({"sub": str(res_db.inserted_id), "email": "john@test.com", "role": "attendee"})
    headers = {"Authorization": f"Bearer {token}"}

    event_data = {
        "name": "SaaS Conference 2026",
        "description": "Tech summit",
        "venue": "Convention Hall",
        "date": "2026-09-10",
        "start_time": "09:00",
        "end_time": "17:00",
        "timezone": "Asia/Karachi",
        "capacity": 200,
        "status": EventStatus.ACTIVE.value,
        "utc_start": datetime.utcnow(),
        "utc_end": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_event = db.events.insert_one(event_data)
    event_id = res_event.inserted_id

    part_data = {
        "name": "John Doe",
        "email": "john@test.com",
        "phone": "+923001234567",
        "event_id": event_id,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_part = db.participants.insert_one(part_data)
    part_id = res_part.inserted_id

    ticket_data = {
        "event_id": event_id,
        "participant_id": part_id,
        "ticket_code": "EVT-JOHNDOE1",
        "token": "secrettoken123",
        "status": TicketStatus.ACTIVE.value,
        "expires_at": datetime.utcnow() + timedelta(days=2),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_ticket = db.tickets.insert_one(ticket_data)
    ticket_id = res_ticket.inserted_id

    res = client.get("/api/portal/events", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1
    assert res.json()["data"][0]["name"] == "SaaS Conference 2026"
    assert res.json()["data"][0]["ticket_code"] == "EVT-JOHNDOE1"

    res = client.get(f"/api/portal/events/{event_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["event"]["name"] == "SaaS Conference 2026"
    assert res.json()["data"]["ticket_code"] == "EVT-JOHNDOE1"

    res = client.get("/api/portal/tickets", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1
    assert res.json()["data"][0]["ticket_code"] == "EVT-JOHNDOE1"

    res = client.get(f"/api/portal/tickets/{ticket_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["ticket_code"] == "EVT-JOHNDOE1"
    assert "qr_payload" in res.json()["data"]

def test_unauthorized_idor_access(client):
    db = db_manager.get_db()
    a_data = {
        "name": "Attendee A",
        "email": "a@test.com",
        "password_hash": hash_password("apass"),
        "role": "attendee",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_a = db.users.insert_one(a_data)
    token_a = create_access_token({"sub": str(res_a.inserted_id), "email": "a@test.com", "role": "attendee"})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    b_data = {
        "name": "Attendee B",
        "email": "b@test.com",
        "password_hash": hash_password("bpass"),
        "role": "attendee",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_b = db.users.insert_one(b_data)

    event_data = {
        "name": "SaaS Conference 2026",
        "description": "Tech summit",
        "venue": "Convention Hall",
        "date": "2026-09-10",
        "start_time": "09:00",
        "end_time": "17:00",
        "timezone": "Asia/Karachi",
        "capacity": 200,
        "status": EventStatus.ACTIVE.value,
        "utc_start": datetime.utcnow(),
        "utc_end": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_event = db.events.insert_one(event_data)
    event_id = res_event.inserted_id

    part_b = {
        "name": "Attendee B",
        "email": "b@test.com",
        "phone": "+123",
        "event_id": event_id,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_part_b = db.participants.insert_one(part_b)
    part_b_id = res_part_b.inserted_id

    ticket_b = {
        "event_id": event_id,
        "participant_id": part_b_id,
        "ticket_code": "EVT-B-CODE",
        "token": "tokenb123",
        "status": TicketStatus.ACTIVE.value,
        "expires_at": datetime.utcnow() + timedelta(days=2),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_ticket_b = db.tickets.insert_one(ticket_b)
    ticket_b_id = res_ticket_b.inserted_id

    res = client.get(f"/api/portal/events/{event_id}", headers=headers_a)
    assert res.status_code == 403

    res = client.get(f"/api/portal/tickets/{ticket_b_id}", headers=headers_a)
    assert res.status_code == 403

def test_role_permissions_rejection(client):
    db = db_manager.get_db()
    a_data = {
        "name": "Attendee User",
        "email": "a@test.com",
        "password_hash": hash_password("apass"),
        "role": "attendee",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_a = db.users.insert_one(a_data)
    token = create_access_token({"sub": str(res_a.inserted_id), "email": "a@test.com", "role": "attendee"})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/users/staff", headers=headers)
    assert res.status_code == 403

    res = client.get("/api/audit-logs", headers=headers)
    assert res.status_code == 403

    res = client.post("/api/attendance/verify", headers=headers, json={"token": "test", "event_id": "test"})
    assert res.status_code == 403

# --- DISCOVERY & BOOKING TESTS ---

def test_attendee_available_events(client):
    db = db_manager.get_db()
    
    # 1. Create attendee
    a_data = {
        "name": "Attendee User",
        "email": "a@test.com",
        "password_hash": hash_password("apass"),
        "role": "attendee",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_a = db.users.insert_one(a_data)
    token = create_access_token({"sub": str(res_a.inserted_id), "email": "a@test.com", "role": "attendee"})
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Active event
    evt_active = db.events.insert_one({
        "name": "Active Event", "venue": "Hall A", "date": "2030-01-01", "start_time": "10:00", "end_time": "12:00",
        "timezone": "Asia/Karachi", "capacity": 100, "status": EventStatus.ACTIVE.value
    })
    
    # 3. Create Draft event
    evt_draft = db.events.insert_one({
        "name": "Draft Event", "venue": "Hall B", "date": "2030-01-01", "start_time": "10:00", "end_time": "12:00",
        "timezone": "Asia/Karachi", "capacity": 100, "status": EventStatus.DRAFT.value
    })

    # 4. Create Cancelled event
    evt_cancelled = db.events.insert_one({
        "name": "Cancelled Event", "venue": "Hall C", "date": "2030-01-01", "start_time": "10:00", "end_time": "12:00",
        "timezone": "Asia/Karachi", "capacity": 100, "status": EventStatus.CANCELLED.value
    })

    # 5. Create Completed event
    evt_completed = db.events.insert_one({
        "name": "Completed Event", "venue": "Hall D", "date": "2020-01-01", "start_time": "10:00", "end_time": "12:00",
        "timezone": "Asia/Karachi", "capacity": 100, "status": EventStatus.COMPLETED.value
    })

    # Fetch available events
    res = client.get("/api/portal/events/available", headers=headers)
    assert res.status_code == 200
    events = res.json()["data"]
    # Only ACTIVE should be listed
    assert len(events) == 1
    assert events[0]["name"] == "Active Event"

    # Try viewing active event detail
    res_det = client.get(f"/api/portal/events/available/{evt_active.inserted_id}", headers=headers)
    assert res_det.status_code == 200
    assert res_det.json()["data"]["name"] == "Active Event"

    # Try viewing draft event detail -> should be rejected with 400 or 404
    res_draft_det = client.get(f"/api/portal/events/available/{evt_draft.inserted_id}", headers=headers)
    assert res_draft_det.status_code == 400

def test_attendee_booking_success(client):
    db = db_manager.get_db()
    
    # 1. Create attendee
    a_data = {
        "name": "Attendee User",
        "email": "a@test.com",
        "password_hash": hash_password("apass"),
        "role": "attendee",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_a = db.users.insert_one(a_data)
    token = create_access_token({"sub": str(res_a.inserted_id), "email": "a@test.com", "role": "attendee"})
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Event
    evt = db.events.insert_one({
        "name": "Tech Event", "venue": "Hall A", "date": "2030-01-01", "start_time": "10:00", "end_time": "12:00",
        "timezone": "Asia/Karachi", "capacity": 5, "status": EventStatus.ACTIVE.value
    })
    event_id = evt.inserted_id

    # 3. Book event
    res = client.post(f"/api/portal/events/{event_id}/book", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "ticket" in data
    ticket = data["ticket"]
    assert ticket["status"] == "active"
    assert "qr_payload" in ticket
    
    # 4. Verify participant record created
    part = db.participants.find_one({"event_id": event_id, "email": "a@test.com"})
    assert part is not None
    assert part["name"] == "Attendee User"

    # 5. Verify ticket record created
    tkt = db.tickets.find_one({"event_id": event_id, "participant_id": part["_id"]})
    assert tkt is not None
    assert tkt["status"] == "active"
    assert tkt["token"] is not None  # Secure opaque token exists

    # 6. Verify audit log created
    audit = db.audit_logs.find_one({"action": "ATTENDEE_BOOKED_EVENT", "actor_email": "a@test.com"})
    assert audit is not None
    assert audit["status"] == AuditStatus.SUCCESS.value
    assert audit["metadata"]["ticket_id"] == str(tkt["_id"])

def test_attendee_booking_failures(client):
    db = db_manager.get_db()
    
    # Create attendee
    a_data = {
        "name": "Attendee User",
        "email": "a@test.com",
        "password_hash": hash_password("apass"),
        "role": "attendee",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_a = db.users.insert_one(a_data)
    token = create_access_token({"sub": str(res_a.inserted_id), "email": "a@test.com", "role": "attendee"})
    headers = {"Authorization": f"Bearer {token}"}

    # Event 1: Expired Event
    evt_expired = db.events.insert_one({
        "name": "Expired Event", "venue": "Hall A", "date": "2020-01-01", "start_time": "10:00", "end_time": "12:00",
        "timezone": "Asia/Karachi", "capacity": 50, "status": EventStatus.ACTIVE.value
    })
    res = client.post(f"/api/portal/events/{evt_expired.inserted_id}/book", headers=headers)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "EVENT_EXPIRED"

    # Event 2: Full Event (Capacity 0)
    evt_full = db.events.insert_one({
        "name": "Full Event", "venue": "Hall A", "date": "2030-01-01", "start_time": "10:00", "end_time": "12:00",
        "timezone": "Asia/Karachi", "capacity": 0, "status": EventStatus.ACTIVE.value
    })
    res = client.post(f"/api/portal/events/{evt_full.inserted_id}/book", headers=headers)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "EVENT_FULL"

    # Event 3: Duplicate booking
    evt_dup = db.events.insert_one({
        "name": "Dup Event", "venue": "Hall A", "date": "2030-01-01", "start_time": "10:00", "end_time": "12:00",
        "timezone": "Asia/Karachi", "capacity": 10, "status": EventStatus.ACTIVE.value
    })
    # book first time
    res = client.post(f"/api/portal/events/{evt_dup.inserted_id}/book", headers=headers)
    assert res.status_code == 200
    # book second time
    res2 = client.post(f"/api/portal/events/{evt_dup.inserted_id}/book", headers=headers)
    assert res2.status_code == 400
    assert res2.json()["error"]["code"] == "ALREADY_REGISTERED"

def test_inactive_attendee_rejected(client):
    db = db_manager.get_db()
    
    # Inactive attendee
    a_data = {
        "name": "Inactive User",
        "email": "inactive@test.com",
        "password_hash": hash_password("apass"),
        "role": "attendee",
        "is_active": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_a = db.users.insert_one(a_data)
    token = create_access_token({"sub": str(res_a.inserted_id), "email": "inactive@test.com", "role": "attendee"})
    headers = {"Authorization": f"Bearer {token}"}

    # Should be rejected with 401 Unauthorized since the require_attendee guard checks user activity
    res = client.get("/api/portal/events/available", headers=headers)
    assert res.status_code == 401

def test_failed_ticket_creation_rolls_back(client):
    db = db_manager.get_db()
    
    # Create attendee
    a_data = {
        "name": "Attendee User",
        "email": "rollback@test.com",
        "password_hash": hash_password("apass"),
        "role": "attendee",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_a = db.users.insert_one(a_data)
    token = create_access_token({"sub": str(res_a.inserted_id), "email": "rollback@test.com", "role": "attendee"})
    headers = {"Authorization": f"Bearer {token}"}

    evt = db.events.insert_one({
        "name": "Rollback Event", "venue": "Hall A", "date": "2030-01-01", "start_time": "10:00", "end_time": "12:00",
        "timezone": "Asia/Karachi", "capacity": 100, "status": EventStatus.ACTIVE.value
    })
    event_id = evt.inserted_id

    # Mock Collection.insert_one to raise exception specifically on tickets insert
    original_insert = Collection.insert_one
    def mock_insert(self, document, *args, **kwargs):
        if self.name == 'tickets':
            raise Exception("Simulated DB ticket insert error")
        return original_insert(self, document, *args, **kwargs)

    with patch.object(Collection, 'insert_one', side_effect=mock_insert, autospec=True):
        res = client.post(f"/api/portal/events/{event_id}/book", headers=headers)
        assert res.status_code == 500
        assert res.json()["error"]["code"] == "TICKET_CREATION_FAILED"

    # Verify participant was deleted (rolled back!)
    part = db.participants.find_one({"event_id": event_id, "email": "rollback@test.com"})
    assert part is None

def test_admin_created_participant_visible(client):
    db = db_manager.get_db()
    
    # Create attendee
    a_data = {
        "name": "Attendee User",
        "email": "admincreated@test.com",
        "password_hash": hash_password("apass"),
        "role": "attendee",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res_a = db.users.insert_one(a_data)
    token = create_access_token({"sub": str(res_a.inserted_id), "email": "admincreated@test.com", "role": "attendee"})
    headers = {"Authorization": f"Bearer {token}"}

    # Event
    evt = db.events.insert_one({
        "name": "Admin Created Event", "venue": "Hall A", "date": "2030-01-01", "start_time": "10:00", "end_time": "12:00",
        "timezone": "Asia/Karachi", "capacity": 100, "status": EventStatus.ACTIVE.value
    })
    event_id = evt.inserted_id

    # Admin registers participant
    part = db.participants.insert_one({
        "event_id": event_id, "name": "Attendee User", "email": "admincreated@test.com",
        "phone": "+123", "is_active": True, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()
    })
    part_id = part.inserted_id

    # Admin generates ticket
    tkt = db.tickets.insert_one({
        "event_id": event_id, "participant_id": part_id, "ticket_code": "SG-ADMINCRE",
        "token": "admincretoken", "status": "active", "expires_at": datetime.utcnow() + timedelta(days=2),
        "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()
    })

    # Fetch via attendee portal
    res = client.get("/api/portal/events", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1
    assert res.json()["data"][0]["ticket_code"] == "SG-ADMINCRE"
