import json
import pytest
import secrets
import concurrent.futures
import jwt
from datetime import datetime, timezone, timedelta
from bson import ObjectId
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
        db.ticket_challenges.delete_many({})
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
    db.users.delete_many({"email": admin_data["email"]})
    result = db.users.insert_one(admin_data)
    admin_data["_id"] = result.inserted_id
    return admin_data

@pytest.fixture
def test_staff1():
    db = db_manager.get_db()
    staff_data = {
        "name": "Test Staff One",
        "email": "staff1@test.com",
        "password_hash": hash_password("staffpassword"),
        "role": UserRole.STAFF.value,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    db.users.delete_many({"email": staff_data["email"]})
    result = db.users.insert_one(staff_data)
    staff_data["_id"] = result.inserted_id
    return staff_data

@pytest.fixture
def test_staff2():
    db = db_manager.get_db()
    staff_data = {
        "name": "Test Staff Two",
        "email": "staff2@test.com",
        "password_hash": hash_password("staffpassword"),
        "role": UserRole.STAFF.value,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    db.users.delete_many({"email": staff_data["email"]})
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

def generate_test_qr_token(db, ticket, email="ali@test.com", ttl_seconds=60, jti=None, status="issued", expires_at=None):
    if not jti:
        jti = secrets.token_hex(16)
    now_utc = datetime.now(timezone.utc)
    if not expires_at:
        expires_at = now_utc + timedelta(seconds=ttl_seconds)
    
    db.ticket_challenges.insert_one({
        "jti": jti,
        "ticket_id": ticket["_id"],
        "event_id": ticket["event_id"],
        "issued_at": now_utc,
        "expires_at": expires_at,
        "consumed_at": None,
        "consumed_by": None,
        "status": status
    })
    
    qr_payload_claims = {
        "ticket_id": str(ticket["_id"]),
        "event_id": str(ticket["event_id"]),
        "email": email,
        "jti": jti,
        "exp": int(expires_at.timestamp()),
        "iat": int(now_utc.timestamp()),
        "token_type": "qr_challenge"
    }
    return jwt.encode(qr_payload_claims, settings.SECRET_KEY, algorithm="HS256")

# --- PUBLIC TICKET VIEW TESTS ---

def test_public_ticket_retrieval_and_privacy(client, test_admin):
    headers = get_auth_headers(test_admin)
    
    res = client.post("/api/events", json={
        "name": "Annual Tech", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    p_res = client.post(f"/api/events/{event_id}/participants", json={
        "name": "Muhammad Ali", "email": "ali@test.com"
    }, headers=headers)
    
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({"event_id": ObjectId(event_id)})
    token = ticket["token"]

    response = client.get(f"/api/tickets/{token}")
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["ticket_code"] == ticket["ticket_code"]
    assert data["status"] == "active"
    assert data["participant"]["name"] == "Muhammad Ali"
    assert data["event"]["name"] == "Annual Tech"
    assert data["event"]["timezone"] == "Asia/Karachi"
    assert "qr_payload" in data

def test_public_ticket_invalid_token(client):
    response = client.get("/api/tickets/invalidtoken123")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TICKET_INVALID"

# --- ROTATING QR CHALLENGE ENDPOINT TESTS ---

def test_attendee_get_rotating_qr_success(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Annual Tech", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "Muhammad Ali", "email": "ali@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({"event_id": ObjectId(event_id)})
    
    attendee_data = {
        "name": "Muhammad Ali",
        "email": "ali@test.com",
        "password_hash": hash_password("attpassword"),
        "role": UserRole.ATTENDEE.value,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    res_db = db.users.insert_one(attendee_data)
    attendee_token = create_access_token({"sub": str(res_db.inserted_id), "email": "ali@test.com", "role": "attendee"})
    attendee_headers = {"Authorization": f"Bearer {attendee_token}"}

    qr_res = client.get(f"/api/portal/tickets/{ticket['_id']}/qr", headers=attendee_headers)
    assert qr_res.status_code == 200
    qr_data = qr_res.json()["data"]
    assert "qr_token" in qr_data
    
    claims = jwt.decode(qr_data["qr_token"], settings.SECRET_KEY, algorithms=["HS256"])
    challenge_doc = db.ticket_challenges.find_one({"jti": claims["jti"]})
    assert challenge_doc is not None
    assert challenge_doc["status"] == "issued"

def test_attendee_get_rotating_qr_forbidden(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Annual Tech", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "Muhammad Ali", "email": "ali@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({"event_id": ObjectId(event_id)})
    
    intruder_data = {
        "name": "Intruder User",
        "email": "intruder@test.com",
        "password_hash": hash_password("attpassword"),
        "role": UserRole.ATTENDEE.value,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    res_db = db.users.insert_one(intruder_data)
    intruder_token = create_access_token({"sub": str(res_db.inserted_id), "email": "intruder@test.com", "role": "attendee"})
    intruder_headers = {"Authorization": f"Bearer {intruder_token}"}

    qr_res = client.get(f"/api/portal/tickets/{ticket['_id']}/qr", headers=intruder_headers)
    assert qr_res.status_code == 403

# --- CHECK-IN VERIFICATION TESTS ---

def test_staff_successful_verification(client, test_admin, test_staff1):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Annual Tech", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "Muhammad Ali", "email": "ali@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({})

    qr_token = generate_test_qr_token(db, ticket)

    staff_headers = get_auth_headers(test_staff1)
    verify_res = client.post("/api/attendance/verify", json={
        "token": qr_token,
        "event_id": event_id
    }, headers=staff_headers)

    assert verify_res.status_code == 200
    data = verify_res.json()["data"]
    assert data["status"] == "valid"
    assert data["participant"]["name"] == "Muhammad Ali"
    assert data["ticket_code"] == ticket["ticket_code"]
    assert data["scanned_by"]["name"] == "Test Staff One"

    updated_ticket = db.tickets.find_one({"_id": ticket["_id"]})
    assert updated_ticket["status"] == "used"

def test_admin_successful_verification(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Annual Tech", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "Muhammad Ali", "email": "ali@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({})

    qr_token = generate_test_qr_token(db, ticket)

    verify_res = client.post("/api/attendance/verify", json={
        "token": qr_token,
        "event_id": event_id
    }, headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["status"] == "valid"

def test_unauthenticated_verification_rejected(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Annual Tech", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "Muhammad Ali", "email": "ali@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({})

    qr_token = generate_test_qr_token(db, ticket)

    verify_res = client.post("/api/attendance/verify", json={
        "token": qr_token,
        "event_id": event_id
    })
    assert verify_res.status_code == 401

def test_wrong_event_rejected(client, test_admin, test_staff1):
    headers = get_auth_headers(test_admin)
    res1 = client.post("/api/events", json={
        "name": "Event One", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id1 = res1.json()["data"]["id"]
    client.put(f"/api/events/{event_id1}", json={"status": "active"}, headers=headers)
    client.post(f"/api/events/{event_id1}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id1}/tickets/generate", headers=headers)

    res2 = client.post("/api/events", json={
        "name": "Event Two", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id2 = res2.json()["data"]["id"]
    client.put(f"/api/events/{event_id2}", json={"status": "active"}, headers=headers)

    db = db_manager.get_db()
    ticket1 = db.tickets.find_one({"event_id": ObjectId(event_id1)})

    qr_token = generate_test_qr_token(db, ticket1)

    staff_headers = get_auth_headers(test_staff1)
    verify_res = client.post("/api/attendance/verify", json={
        "token": qr_token,
        "event_id": event_id2
    }, headers=staff_headers)

    assert verify_res.status_code == 400
    assert verify_res.json()["error"]["code"] == "TICKET_WRONG_EVENT"

def test_inactive_event_rejected(client, test_admin, test_staff1):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Draft Event", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({})

    qr_token = generate_test_qr_token(db, ticket)

    staff_headers = get_auth_headers(test_staff1)
    verify_res = client.post("/api/attendance/verify", json={
        "token": qr_token,
        "event_id": event_id
    }, headers=staff_headers)

    assert verify_res.status_code == 400
    assert verify_res.json()["error"]["code"] == "EVENT_NOT_ACTIVE"

def test_inactive_participant_rejected(client, test_admin, test_staff1):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    p_res = client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    participant_id = p_res.json()["data"]["id"]
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    client.delete(f"/api/participants/{participant_id}", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({})

    qr_token = generate_test_qr_token(db, ticket)

    staff_headers = get_auth_headers(test_staff1)
    verify_res = client.post("/api/attendance/verify", json={
        "token": qr_token,
        "event_id": event_id
    }, headers=staff_headers)

    assert verify_res.status_code == 400
    assert verify_res.json()["error"]["code"] == "PARTICIPANT_INACTIVE"

def test_revoked_ticket_rejected(client, test_admin, test_staff1):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({})
    
    client.post(f"/api/tickets/{ticket['_id']}/revoke", headers=headers)

    qr_token = generate_test_qr_token(db, ticket)

    staff_headers = get_auth_headers(test_staff1)
    verify_res = client.post("/api/attendance/verify", json={
        "token": qr_token,
        "event_id": event_id
    }, headers=staff_headers)

    assert verify_res.status_code == 400
    assert verify_res.json()["error"]["code"] == "TICKET_REVOKED"

def test_expired_qr_challenge_rejected(client, test_admin, test_staff1):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({})

    # Generate QR challenge that is already expired
    qr_token = generate_test_qr_token(db, ticket, ttl_seconds=-5)

    staff_headers = get_auth_headers(test_staff1)
    verify_res = client.post("/api/attendance/verify", json={
        "token": qr_token,
        "event_id": event_id
    }, headers=staff_headers)

    assert verify_res.status_code == 400
    assert verify_res.json()["error"]["code"] == "QR_EXPIRED"

def test_duplicate_verification_fails_and_does_not_duplicate_attendance(client, test_admin, test_staff1):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({})

    qr_token1 = generate_test_qr_token(db, ticket, jti="nonce1")

    staff_headers = get_auth_headers(test_staff1)
    
    # Check-in 1 (Success)
    v1 = client.post("/api/attendance/verify", json={"token": qr_token1, "event_id": event_id}, headers=staff_headers)
    assert v1.status_code == 200

    # Check-in 2 with same challenge (Failure due to consumed challenge)
    v2 = client.post("/api/attendance/verify", json={"token": qr_token1, "event_id": event_id}, headers=staff_headers)
    assert v2.status_code == 400
    assert v2.json()["error"]["code"] == "TICKET_ALREADY_USED"

    # Assert exactly 1 attendance record created
    attendance_count = db.attendance.count_documents({"ticket_id": ticket["_id"]})
    assert attendance_count == 1

# --- STAFF SCAN HISTORY API ---

def test_staff_scan_history_and_pagination(client, test_admin, test_staff1, test_staff2):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Venue", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "P2", "email": "p2@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    tickets = list(db.tickets.find({}))

    qr_token1 = generate_test_qr_token(db, tickets[0], jti="noncep1")
    qr_token2 = generate_test_qr_token(db, tickets[1], jti="noncep2")

    staff1_headers = get_auth_headers(test_staff1)
    staff2_headers = get_auth_headers(test_staff2)

    # Staff 1 scans P1
    client.post("/api/attendance/verify", json={"token": qr_token1, "event_id": event_id}, headers=staff1_headers)
    # Staff 2 scans P2
    client.post("/api/attendance/verify", json={"token": qr_token2, "event_id": event_id}, headers=staff2_headers)

    # Check Staff 1 scans history
    s1_history = client.get("/api/attendance/my-scans?page=1&page_size=10", headers=staff1_headers)
    assert s1_history.status_code == 200
    s1_data = s1_history.json()
    assert s1_data["total"] == 1
    assert s1_data["data"][0]["participant_name"] == "P1"

# --- CONCURRENCY DOUBLE CHECK-IN PROTECTION ---

def test_concurrent_duplicate_scan_protection(client, test_admin, test_staff1):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({})

    qr_token = generate_test_qr_token(db, ticket)

    staff_headers = get_auth_headers(test_staff1)

    # Dispatch 5 simultaneous scans
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(
                client.post,
                "/api/attendance/verify",
                json={"token": qr_token, "event_id": event_id},
                headers=staff_headers
            )
            for _ in range(5)
        ]
        results = [f.result() for f in futures]

    # Verify exactly ONE succeeded and the rest were rejected with 400 TICKET_ALREADY_USED
    successes = [r for r in results if r.status_code == 200]
    failures = [r for r in results if r.status_code == 400]

    assert len(successes) == 1
    assert len(failures) == 4
    for fail in failures:
        assert fail.json()["error"]["code"] == "TICKET_ALREADY_USED"

    assert db.attendance.count_documents({"ticket_id": ticket["_id"]}) == 1


def test_attendee_cannot_get_qr_for_used_ticket(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event", "venue": "Main Hall", "date": "2026-09-20",
        "start_time": "10:00", "end_time": "17:00", "capacity": 10, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "Muhammad Ali", "email": "ali@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    ticket = db.tickets.find_one({})
    
    db.tickets.update_one({"_id": ticket["_id"]}, {"$set": {"status": "used"}})

    attendee_data = {
        "name": "Muhammad Ali",
        "email": "ali@test.com",
        "password_hash": hash_password("attpassword"),
        "role": UserRole.ATTENDEE.value,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    res_db = db.users.insert_one(attendee_data)
    attendee_token = create_access_token({"sub": str(res_db.inserted_id), "email": "ali@test.com", "role": "attendee"})
    attendee_headers = {"Authorization": f"Bearer {attendee_token}"}

    qr_res = client.get(f"/api/portal/tickets/{ticket['_id']}/qr", headers=attendee_headers)
    assert qr_res.status_code == 400
    assert qr_res.json()["error"]["code"] == "TICKET_ALREADY_USED"
