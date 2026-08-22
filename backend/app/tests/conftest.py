import os
import pytest

# Override configurations for test run
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "9a2b8e3d6f1c4e7a8b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a"
os.environ["MONGO_DB_NAME"] = "event_access_test"

from fastapi.testclient import TestClient
from app.main import app
from app.database import db_manager

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Auto-used fixture that initializes the test database,
    creates indexes, and cleans up collections after the test session.
    """
    try:
        db_manager.connect()
        db_manager.init_indexes()
    except Exception as e:
        pytest.skip(f"Skipping DB-dependent tests: MongoDB is not available ({e})")
        
    yield
    
    try:
        db = db_manager.get_db()
        # Drop all test collections except system collections
        for collection_name in db.list_collection_names():
            if not collection_name.startswith("system."):
                db[collection_name].drop()
        db_manager.close()
    except Exception:
        pass

@pytest.fixture
def client():
    """
    Provides a FastAPI test client utilizing the lifespan context.
    """
    with TestClient(app) as c:
        yield c
