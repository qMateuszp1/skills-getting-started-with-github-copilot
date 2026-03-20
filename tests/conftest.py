import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities(client):
    """Reset activities to a known state before each test"""
    # Store original activities
    from src.app import activities
    original = {
        k: {
            "description": v["description"],
            "schedule": v["schedule"],
            "max_participants": v["max_participants"],
            "participants": v["participants"].copy()
        }
        for k, v in activities.items()
    }
    
    yield
    
    # Restore after test
    for key in activities:
        activities[key]["participants"] = original[key]["participants"].copy()
