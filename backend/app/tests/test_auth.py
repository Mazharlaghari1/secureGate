import json
from datetime import datetime, timedelta
import pytest
from bson import ObjectId
import jwt

from app.config import settings
from app.database import db_manager
from app.security.auth import hash_password, create_access_token
from app.models.constants import UserRole, AuditStatus

@pytest.fixture(autouse=True)
def clean_db():
    try:
        db = db_manager.get_db()
        db.users.delete_many({})
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
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
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
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
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

# 1. Successful Admin Login
def test_admin_login_success(client, test_admin):
    response = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "token" in data["data"]
    assert data["data"]["user"]["email"] == "admin@test.com"
    assert data["data"]["user"]["role"] == "admin"
    assert "password_hash" not in data["data"]["user"]

# 2. Successful Staff Login
def test_staff_login_success(client, test_staff):
    response = client.post("/api/auth/login", json={
        "email": "staff@test.com",
        "password": "staffpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "token" in data["data"]
    assert data["data"]["user"]["email"] == "staff@test.com"
    assert data["data"]["user"]["role"] == "staff"

# 3. Incorrect Password
def test_login_incorrect_password(client, test_admin):
    response = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"
    # Ensure message is generic and doesn't leak that password was wrong specifically
    assert "password" not in data["error"]["message"].lower()

# 4. Unknown Email
def test_login_unknown_email(client, test_admin):
    response = client.post("/api/auth/login", json={
        "email": "unknown@test.com",
        "password": "somepassword"
    })
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"

# 5. Inactive User
def test_login_inactive_user(client, test_staff):
    db = db_manager.get_db()
    db.users.update_one({"_id": test_staff["_id"]}, {"$set": {"is_active": False}})
    
    response = client.post("/api/auth/login", json={
        "email": "staff@test.com",
        "password": "staffpassword"
    })
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"

# 6. Expired JWT
def test_expired_jwt(client, test_admin):
    token = create_access_token(
        data={"sub": str(test_admin["_id"]), "email": test_admin["email"], "role": test_admin["role"]},
        expires_delta=timedelta(seconds=-10)  # Expired 10 seconds ago
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TOKEN_EXPIRED"

# 7. Invalid JWT Signature
def test_invalid_jwt_signature(client, test_admin):
    token = create_access_token(
        data={"sub": str(test_admin["_id"]), "email": test_admin["email"], "role": test_admin["role"]}
    )
    # Alter the last character of signature to invalidate it
    invalid_token = token[:-1] + ("0" if token[-1] != "0" else "1")
    headers = {"Authorization": f"Bearer {invalid_token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TOKEN_INVALID"

# 8. Missing Authorization Header
def test_missing_auth_header(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TOKEN_INVALID"

# 9. Malformed Authorization Header
def test_malformed_auth_header(client):
    headers = {"Authorization": "MalformedHeaderValue"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TOKEN_INVALID"

# 10. /api/auth/me with valid JWT
def test_get_me_success(client, test_admin):
    headers = get_auth_headers(test_admin)
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == test_admin["email"]
    assert "password_hash" not in data["data"]

# 11. /api/auth/me without JWT
def test_get_me_unauthorized(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401

# 12. Admin Access to Admin Endpoint (Staff Management)
def test_admin_access_admin_endpoint(client, test_admin):
    headers = get_auth_headers(test_admin)
    response = client.get("/api/users/staff", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

# 13. Staff Denied Admin Endpoint
def test_staff_denied_admin_endpoint(client, test_staff):
    headers = get_auth_headers(test_staff)
    response = client.get("/api/users/staff", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

# 14. Admin Can Create Staff
def test_admin_can_create_staff(client, test_admin):
    headers = get_auth_headers(test_admin)
    response = client.post("/api/users/staff", json={
        "name": "New Staff Member",
        "email": "newstaff@test.com",
        "password": "staffsecretpassword"
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "newstaff@test.com"
    assert data["data"]["role"] == "staff"
    assert "password_hash" not in data["data"]

# 15. Staff Cannot Create Staff
def test_staff_cannot_create_staff(client, test_staff):
    headers = get_auth_headers(test_staff)
    response = client.post("/api/users/staff", json={
        "name": "New Staff Member",
        "email": "newstaff@test.com",
        "password": "staffsecretpassword"
    }, headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

# 16. Duplicate Staff Email
def test_create_duplicate_staff_email(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    response = client.post("/api/users/staff", json={
        "name": "Duplicate Staff",
        "email": "staff@test.com",  # Already exists via test_staff fixture
        "password": "staffsecretpassword"
    }, headers=headers)
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "CONFLICT"

# 17. Staff Listing (Admin Only)
def test_staff_listing(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    response = client.get("/api/users/staff", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1  # Only test_staff (test_admin is an admin, role=admin is filtered out)
    assert data["data"][0]["email"] == test_staff["email"]

# 18. Staff Update (Admin Only)
def test_staff_update(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    response = client.put(f"/api/users/staff/{str(test_staff['_id'])}", json={
        "name": "Updated Staff Name",
        "email": "staff_updated@test.com",
        "is_active": True
    }, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Updated Staff Name"
    assert data["data"]["email"] == "staff_updated@test.com"

# 19. Staff Deactivation (Admin Only)
def test_staff_deactivation(client, test_admin, test_staff):
    headers = get_auth_headers(test_admin)
    response = client.delete(f"/api/users/staff/{str(test_staff['_id'])}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "deactivated"
    
    # Confirm DB is updated
    db = db_manager.get_db()
    user = db.users.find_one({"_id": test_staff["_id"]})
    assert user["is_active"] is False

# 20. Deactivated Staff Cannot Authenticate
def test_deactivated_staff_cannot_login(client, test_admin, test_staff):
    # Deactivate
    headers = get_auth_headers(test_admin)
    client.delete(f"/api/users/staff/{str(test_staff['_id'])}", headers=headers)
    
    # Attempt login
    response = client.post("/api/auth/login", json={
        "email": "staff@test.com",
        "password": "staffpassword"
    })
    assert response.status_code == 401

# 21. Deactivated Staff's Previously Issued JWT is Rejected
def test_deactivated_staff_jwt_rejected(client, test_admin, test_staff):
    # Get valid headers first
    staff_headers = get_auth_headers(test_staff)
    
    # Verify me works
    response = client.get("/api/auth/me", headers=staff_headers)
    assert response.status_code == 200
    
    # Deactivate via Admin
    admin_headers = get_auth_headers(test_admin)
    client.delete(f"/api/users/staff/{str(test_staff['_id'])}", headers=admin_headers)
    
    # Attempt me again with previous token -> should fail now
    response = client.get("/api/auth/me", headers=staff_headers)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "USER_INACTIVE"

# 22. Password Hash is Never Returned
def test_password_hash_not_exposed(client, test_admin):
    headers = get_auth_headers(test_admin)
    
    # Check /me
    response = client.get("/api/auth/me", headers=headers)
    assert "password_hash" not in response.text
    
    # Check list staff
    response = client.get("/api/users/staff", headers=headers)
    assert "password_hash" not in response.text

# 23. Password is Never Audited/Logged
def test_password_not_audited(client, test_admin):
    # Log in
    client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpassword"
    })
    
    # Query logs
    db = db_manager.get_db()
    logs = list(db.audit_logs.find({"actor_email": "admin@test.com"}))
    for log in logs:
        assert "password" not in log["metadata"]
        assert "adminpassword" not in json.dumps(log["metadata"])

# 24. Login Audit Success
def test_login_audit_success(client, test_admin):
    client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "adminpassword"
    })
    
    db = db_manager.get_db()
    log = db.audit_logs.find_one({"action": "USER_LOGIN", "status": "success"})
    assert log is not None
    assert log["actor_email"] == "admin@test.com"

# 25. Login Audit Failure
def test_login_audit_failure(client):
    client.post("/api/auth/login", json={
        "email": "nonexistent@test.com",
        "password": "somepassword"
    })
    
    db = db_manager.get_db()
    log = db.audit_logs.find_one({"action": "USER_LOGIN", "status": "failure"})
    assert log is not None
    assert log["actor_email"] == "nonexistent@test.com"
    assert log["metadata"]["reason"] == "User not found"

# 26. Invalid Staff Data Validation
def test_invalid_staff_validation(client, test_admin):
    headers = get_auth_headers(test_admin)
    response = client.post("/api/users/staff", json={
        "name": "", # empty name
        "email": "invalid-email", # invalid email format
        "password": "123" # password too short
    }, headers=headers)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "email" in data["error"]["details"]
    assert "password" in data["error"]["details"]

