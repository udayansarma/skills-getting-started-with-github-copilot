"""
Test configuration and fixtures for the FastAPI application tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Fixture to reset activities data before each test."""
    # Store original activities data
    original_activities = copy.deepcopy(activities)
    
    yield
    
    # Restore original activities data after test
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def sample_activity_data():
    """Sample activity data for testing."""
    return {
        "Test Activity": {
            "description": "A test activity for testing purposes",
            "schedule": "Mondays, 3:00 PM - 4:00 PM",
            "max_participants": 5,
            "participants": ["test1@mergington.edu", "test2@mergington.edu"]
        }
    }