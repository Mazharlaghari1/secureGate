import json
import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
from bson import ObjectId

from app.config import settings
from app.utils.objectid import str_to_object_id
from app.schemas.base import PaginationParams
from app.database import db_manager
from app.middleware.errors import validation_exception_handler

# 1. Health endpoint test
def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code in (200, 503)
    data = response.json()
    if response.status_code == 200:
        assert data["success"] is True
        assert data["data"]["status"] == "ok"
        assert data["data"]["database"] == "connected"
    else:
        assert data["success"] is False
        assert data["error"]["code"] == "DATABASE_DISCONNECTED"

# 2. Configuration validation test
def test_configuration_validation():
    assert settings.ENVIRONMENT == "testing"
    assert settings.MONGO_DB_NAME == "event_access_test"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 480
    assert isinstance(settings.ALLOWED_ORIGINS, list)

# 3. Invalid ObjectId handling test
def test_invalid_objectid_handling():
    # Valid conversion
    valid_id = "507f1f77bcf86cd799439011"
    assert str_to_object_id(valid_id) == ObjectId(valid_id)
    
    # Invalid conversion should throw HTTPException
    with pytest.raises(HTTPException) as exc_info:
        str_to_object_id("invalid-id-format")
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "VALIDATION_ERROR"
    assert "Invalid ID" in exc_info.value.detail["message"]

# 4. Pagination validation test
def test_pagination_validation():
    # Valid params
    params = PaginationParams(page=1, page_size=20)
    assert params.page == 1
    assert params.page_size == 20

    # Invalid page (page < 1)
    with pytest.raises(ValidationError):
        PaginationParams(page=0, page_size=20)

    # Invalid page size (page_size > 100)
    with pytest.raises(ValidationError):
        PaginationParams(page=1, page_size=101)

# 5. Standard API error formatting test
def test_validation_error_format():
    import asyncio
    from pydantic import EmailStr
    class DummyModel(BaseModel):
        age: int
        email: EmailStr

    try:
        DummyModel(age="not-an-int", email="invalid-email")
    except ValidationError as val_err:
        req_exc = RequestValidationError(errors=val_err.errors())
        
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(validation_exception_handler(None, req_exc))
    finally:
        loop.close()
        
    assert response.status_code == 422
    
    body = json.loads(response.body.decode())
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "age" in body["error"]["details"]
    assert "email" in body["error"]["details"]

# 6. Database initialization/index creation test
def test_database_indexes():
    try:
        db = db_manager.get_db()
    except Exception:
        pytest.skip("MongoDB database not running, skipping index assertion.")

    # Check users unique index
    user_indexes = db.users.index_information()
    assert "email_1" in user_indexes
    assert user_indexes["email_1"]["unique"] is True

    # Check participants composite unique index
    participant_indexes = db.participants.index_information()
    assert "event_id_1_email_1" in participant_indexes
    assert participant_indexes["event_id_1_email_1"]["unique"] is True

    # Check tickets index setup
    ticket_indexes = db.tickets.index_information()
    assert "token_1" in ticket_indexes
    assert ticket_indexes["token_1"]["unique"] is True
    assert "ticket_code_1" in ticket_indexes
    assert ticket_indexes["ticket_code_1"]["unique"] is True
    assert "event_id_1_participant_id_1" in ticket_indexes
    assert ticket_indexes["event_id_1_participant_id_1"]["unique"] is True

# 7. Swagger docs page accessibility test
def test_docs_endpoint(client):
    response = client.get("/docs")
    assert response.status_code == 200
