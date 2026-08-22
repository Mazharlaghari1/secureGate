import io
import json
import pytest
import secrets
from datetime import datetime, timezone, timedelta
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
        db.tickets.delete_many({})
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

# --- CSV IMPORT TESTS ---

def test_valid_csv_import(client, test_admin):
    headers = get_auth_headers(test_admin)
    # Create active event
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    csv_data = "name,email,phone\nAli Ahmed,ali@test.com,03001112223\nSara Khan,sara@test.com,03004445556"
    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", csv_data, "text/csv")},
        headers=headers
    )
    assert response.status_code == 201
    assert response.json()["data"]["imported"] == 2

    # Verify audit log
    db = db_manager.get_db()
    audit = db.audit_logs.find_one({"action": "CSV_BULK_IMPORT_SUCCESS"})
    assert audit is not None
    assert audit["metadata"]["imported"] == 2

def test_empty_csv(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", "", "text/csv")},
        headers=headers
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "empty" in response.json()["error"]["message"].lower()

def test_missing_header_invalid_header(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Missing header / wrong column name
    csv_data = "name,email,number\nAli Ahmed,ali@test.com,03001112223"
    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", csv_data, "text/csv")},
        headers=headers
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["details"]["errors"][0]["field"] == "header"

def test_missing_required_field_invalid_email(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Missing email on row 2, invalid email on row 3
    csv_data = "name,email,phone\nAli Ahmed,,03001112223\nSara Khan,invalid-email,03004445556"
    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", csv_data, "text/csv")},
        headers=headers
    )
    assert response.status_code == 400
    data = response.json()
    assert len(data["error"]["details"]["errors"]) >= 2

def test_name_length_bounds(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Row 2: Name too short (length 1)
    # Row 3: Name too long (length 101)
    csv_data = f"name,email,phone\nA,ali@test.com,03001112223\n{'X'*101},sara@test.com,03004445556"
    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", csv_data, "text/csv")},
        headers=headers
    )
    assert response.status_code == 400
    data = response.json()
    assert len(data["error"]["details"]["errors"]) >= 2

def test_duplicate_email_inside_csv(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Identical emails, one with capitalization
    csv_data = "name,email,phone\nAli,ali@test.com,\nSara,ALI@test.com,"
    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", csv_data, "text/csv")},
        headers=headers
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "duplicate email" in data["error"]["details"]["errors"][0]["message"].lower()

def test_existing_database_duplicate(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Register ali@test.com first
    client.post(f"/api/events/{event_id}/participants", json={
        "name": "Ali Ahmed",
        "email": "ali@test.com"
    }, headers=headers)

    # Upload CSV containing same email
    csv_data = "name,email,phone\nSara Khan,ali@test.com,"
    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", csv_data, "text/csv")},
        headers=headers
    )
    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "CONFLICT"

def test_file_larger_than_2mb(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Generate massive body
    large_csv = b"name,email,phone\n" + b"A,a@test.com,\n" * 150000 # ~2.2 MB
    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", large_csv, "text/csv")},
        headers=headers
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"

def test_csv_capacity_exceeded(client, test_admin):
    headers = get_auth_headers(test_admin)
    # Capacity = 2
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 2, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Register 1 participant
    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)

    # Attempt to upload CSV with 2 participants (total 3 > capacity 2)
    csv_data = "name,email,phone\nP2,p2@test.com,\nP3,p3@test.com,"
    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", csv_data, "text/csv")},
        headers=headers
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EVENT_CAPACITY_REACHED"

    # Verify atomic fallback (P2 and P3 must NOT be in DB)
    db = db_manager.get_db()
    p2 = db.participants.find_one({"email": "p2@test.com"})
    p3 = db.participants.find_one({"email": "p3@test.com"})
    assert p2 is None
    assert p3 is None

def test_cancelled_or_completed_event_upload(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    
    # Move to completed
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)
    client.put(f"/api/events/{event_id}", json={"status": "completed"}, headers=headers)

    csv_data = "name,email,phone\nSara Khan,sara@test.com,"
    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", csv_data, "text/csv")},
        headers=headers
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_EVENT_STATUS_TRANSITION"

def test_staff_cannot_upload(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    staff_headers = get_auth_headers(test_staff)
    csv_data = "name,email,phone\nSara Khan,sara@test.com,"
    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", csv_data, "text/csv")},
        headers=staff_headers
    )
    assert response.status_code == 403

def test_invalid_csv_causes_zero_imported_records(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Valid Ali, but invalid Sara (missing email)
    csv_data = "name,email,phone\nAli Ahmed,ali@test.com,\nSara Khan,,"
    response = client.post(
        f"/api/events/{event_id}/participants/bulk",
        files={"file": ("test.csv", csv_data, "text/csv")},
        headers=headers
    )
    assert response.status_code == 400
    
    # Assert neither participant is created
    db = db_manager.get_db()
    ali = db.participants.find_one({"email": "ali@test.com"})
    assert ali is None


# --- TICKET GENERATION & MANAGEMENT TESTS ---

def test_generate_tickets(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Add 3 participants
    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "P2", "email": "p2@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "P3", "email": "p3@test.com"}, headers=headers)

    # Generate
    response = client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)
    assert response.status_code == 201
    assert response.json()["data"]["generated"] == 3

    # Generating again should yield 0 new tickets (idempotency)
    response_again = client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)
    assert response_again.status_code == 201
    assert response_again.json()["data"]["generated"] == 0

def test_ticket_uniqueness_and_entropy(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Add 2 participants
    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/participants", json={"name": "P2", "email": "p2@test.com"}, headers=headers)

    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    tickets = list(db.tickets.find({"event_id": ObjectId(event_id)}))
    assert len(tickets) == 2

    t1, t2 = tickets[0], tickets[1]
    
    # Assert unique tokens and ticket codes
    assert t1["token"] != t2["token"]
    assert t1["ticket_code"] != t2["ticket_code"]

    # Token high entropy check: secrets.token_urlsafe(32) produces a 43-character base64-like string
    assert len(t1["token"]) >= 40
    # Codes format check
    assert t1["ticket_code"].startswith("EVT-")
    assert t1["status"] == "active"

    # Expire check: expires_at is timezone-safe event end (12:00 UTC) + 2 hours = 14:00 UTC
    expected_exp = datetime.strptime("2026-09-01 14:00", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    assert t1["expires_at"].replace(tzinfo=timezone.utc) == expected_exp

def test_ticket_listing_token_privacy_leakage(client, test_admin):
    # This test satisfies the mandatory SECRET LEAKAGE TEST (Section 30)
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    # 1. Capture secret token from DB
    db = db_manager.get_db()
    db_ticket = db.tickets.find_one({"event_id": ObjectId(event_id)})
    secret_token = db_ticket["token"]
    assert secret_token is not None

    # 2. Call admin ticket listing endpoint
    response = client.get(f"/api/events/{event_id}/tickets", headers=headers)
    assert response.status_code == 200
    listing_data = response.json()
    
    # 3. Assert token is NOT present in API list response
    for ticket in listing_data["data"]:
        assert "token" not in ticket
        # String representation checks in JSON dump to guarantee no secret token leaked
        assert secret_token not in json.dumps(ticket)

    # 4. Check audit logs to assert secret token is not written there
    audit_logs = list(db.audit_logs.find({}))
    for audit in audit_logs:
        # Check all string contents of audits
        assert secret_token not in json.dumps(audit, default=str)

def test_admin_can_revoke_ticket(client, test_admin):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    db_ticket = db.tickets.find_one({"event_id": ObjectId(event_id)})
    ticket_id = str(db_ticket["_id"])

    # Revoke
    response = client.post(f"/api/tickets/{ticket_id}/revoke", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "revoked"

    # Revoke again should fail
    response_again = client.post(f"/api/tickets/{ticket_id}/revoke", headers=headers)
    assert response_again.status_code == 400

def test_staff_cannot_generate_or_revoke(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    db_ticket = db.tickets.find_one({"event_id": ObjectId(event_id)})
    ticket_id = str(db_ticket["_id"])

    staff_headers = get_auth_headers(test_staff)
    # Generate attempt by Staff
    response_gen = client.post(f"/api/events/{event_id}/tickets/generate", headers=staff_headers)
    assert response_gen.status_code == 403

    # Revoke attempt by Staff
    response_rev = client.post(f"/api/tickets/{ticket_id}/revoke", headers=staff_headers)
    assert response_rev.status_code == 403
