import pytest
from datetime import datetime, timezone
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

# --- AUTHORIZATION TESTS ---

def test_admin_dashboard_auth(client, test_admin, test_staff):
    admin_headers = get_auth_headers(test_admin)
    staff_headers = get_auth_headers(test_staff)

    # Admin access dashboard (200 OK)
    res_admin = client.get("/api/reports/dashboard", headers=admin_headers)
    assert res_admin.status_code == 200

    # Staff access dashboard (403 Forbidden)
    res_staff = client.get("/api/reports/dashboard", headers=staff_headers)
    assert res_staff.status_code == 403

def test_admin_event_report_auth(client, test_admin, test_staff):
    admin_headers = get_auth_headers(test_admin)
    staff_headers = get_auth_headers(test_staff)

    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=admin_headers)
    event_id = res.json()["data"]["id"]

    # Admin access event report (200 OK)
    res_admin = client.get(f"/api/reports/event/{event_id}", headers=admin_headers)
    assert res_admin.status_code == 200

    # Staff access event report (403 Forbidden)
    res_staff = client.get(f"/api/reports/event/{event_id}", headers=staff_headers)
    assert res_staff.status_code == 403

def test_admin_csv_export_auth(client, test_admin, test_staff):
    admin_headers = get_auth_headers(test_admin)
    staff_headers = get_auth_headers(test_staff)

    res = client.post("/api/events", json={
        "name": "Event A", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 100, "timezone": "UTC"
    }, headers=admin_headers)
    event_id = res.json()["data"]["id"]

    # Admin access export (200 OK)
    res_admin = client.get(f"/api/reports/event/{event_id}/export", headers=admin_headers)
    assert res_admin.status_code == 200

    # Staff access export (403 Forbidden)
    res_staff = client.get(f"/api/reports/event/{event_id}/export", headers=staff_headers)
    assert res_staff.status_code == 403

# --- CALCULATIONS & STATS TESTS ---

def test_dashboard_calculations(client, test_admin):
    headers = get_auth_headers(test_admin)

    # 1. Create two events (one draft, one active)
    e1 = client.post("/api/events", json={
        "name": "Event One", "venue": "Venue A", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 10, "timezone": "UTC"
    }, headers=headers).json()["data"]
    e2 = client.post("/api/events", json={
        "name": "Event Two", "venue": "Venue B", "date": "2026-09-02", "start_time": "14:00", "end_time": "16:00", "capacity": 20, "timezone": "UTC"
    }, headers=headers).json()["data"]

    client.put(f"/api/events/{e2['id']}", json={"status": "active"}, headers=headers)

    # 2. Add participants to e2
    client.post(f"/api/events/{e2['id']}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers)
    client.post(f"/api/events/{e2['id']}/participants", json={"name": "P2", "email": "p2@test.com"}, headers=headers)

    # 3. Generate tickets for e2 (yields 2 tickets)
    client.post(f"/api/events/{e2['id']}/tickets/generate", headers=headers)

    # Fetch stats
    res = client.get("/api/reports/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    
    assert data["total_events"] == 2
    assert data["active_events"] == 1
    assert data["total_registered_participants"] == 2
    assert data["total_allocated_tickets"] == 2

def test_event_report_details_and_exports(client, test_admin):
    headers = get_auth_headers(test_admin)
    
    # Event
    res = client.post("/api/events", json={
        "name": "Annual Conference", "venue": "Grand Hall", "date": "2026-09-20",
        "start_time": "09:00", "end_time": "17:00", "capacity": 50, "timezone": "Asia/Karachi"
    }, headers=headers)
    event_id = res.json()["data"]["id"]
    client.put(f"/api/events/{event_id}", json={"status": "active"}, headers=headers)

    # Add participants
    p1 = client.post(f"/api/events/{event_id}/participants", json={"name": "P1", "email": "p1@test.com"}, headers=headers).json()["data"]
    p2 = client.post(f"/api/events/{event_id}/participants", json={"name": "P2", "email": "p2@test.com"}, headers=headers).json()["data"]
    
    # Tickets
    client.post(f"/api/events/{event_id}/tickets/generate", headers=headers)

    db = db_manager.get_db()
    t1 = db.tickets.find_one({"participant_id": ObjectId(p1["id"])})
    t2 = db.tickets.find_one({"participant_id": ObjectId(p2["id"])})

    # Check-in P1
    import jwt
    import secrets
    from datetime import timedelta
    jti = secrets.token_hex(16)
    db.ticket_challenges.insert_one({
        "jti": jti,
        "ticket_id": t1["_id"],
        "event_id": t1["event_id"],
        "issued_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=60),
        "consumed_at": None,
        "consumed_by": None,
        "status": "issued"
    })
    qr_payload_claims = {
        "ticket_id": str(t1["_id"]),
        "event_id": str(t1["event_id"]),
        "email": "p1@test.com",
        "jti": jti,
        "exp": int((datetime.now(timezone.utc) + timedelta(seconds=60)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "token_type": "qr_challenge"
    }
    qr_token = jwt.encode(qr_payload_claims, settings.SECRET_KEY, algorithm="HS256")
    client.post("/api/attendance/verify", json={"token": qr_token, "event_id": event_id}, headers=headers)

    # Fetch report
    rep_res = client.get(f"/api/reports/event/{event_id}", headers=headers)
    assert rep_res.status_code == 200
    data = rep_res.json()["data"]
    
    assert data["tickets_issued"] == 2
    assert data["checked_in"] == 1
    assert data["remaining"] == 1
    assert data["attendance_percentage"] == 50.0
    assert len(data["check_ins_over_time"]) >= 1

    # Verify CSV Export
    csv_res = client.get(f"/api/reports/event/{event_id}/export", headers=headers)
    assert csv_res.status_code == 200
    csv_text = csv_res.text
    
    assert "Ticket Code" in csv_text
    assert "Participant Name" in csv_text
    assert "Participant Email" in csv_text
    assert "Check-In Time" in csv_text
    assert "Staff Name" in csv_text
    
    assert t1["ticket_code"] in csv_text
    assert "P1" in csv_text
    assert "p1@test.com" in csv_text

    # Strictly verify NO secret token leakage in report or CSV
    assert t1["token"] not in csv_text
    assert t1["token"] not in rep_res.text

# --- AUDIT LOGS PAGINATION & FILTERING TESTS ---

def test_audit_logs_pagination_and_filtering(client, test_admin, test_staff):
    admin_headers = get_auth_headers(test_admin)
    staff_headers = get_auth_headers(test_staff)

    # Unauthorized access (403 Forbidden)
    res_staff = client.get("/api/audit-logs", headers=staff_headers)
    assert res_staff.status_code == 403

    # Generate some audits
    client.post("/api/events", json={
        "name": "Event One", "venue": "Venue", "date": "2026-09-01", "start_time": "10:00", "end_time": "12:00", "capacity": 10, "timezone": "UTC"
    }, headers=admin_headers)

    # Fetch paginated logs
    res_admin = client.get("/api/audit-logs?page=1&page_size=20", headers=admin_headers)
    assert res_admin.status_code == 200
    data = res_admin.json()
    
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] >= 1
    assert len(data["data"]) >= 1

    # Filter by action
    action_filtered = client.get("/api/audit-logs?action=EVENT_CREATED", headers=admin_headers).json()["data"]
    for log in action_filtered:
        assert log["action"] == "EVENT_CREATED"
