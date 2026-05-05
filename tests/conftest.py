"""
conftest.py - Shared pytest fixtures for WanderWise tests.

This module provides:
- Mocked MongoDB collections (mongomock)
- TestClient for FastAPI app
- Test database fixtures
- Environment variable mocking
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
import os
from typing import Dict, Any


# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    """Mock environment variables to avoid .env file dependency."""
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017/test_database")
    yield
    # Cleanup happens automatically after test


# ============================================================================
# MONGODB MOCKING
# ============================================================================

@pytest.fixture
def mock_mongo_client():
    """Create a mock MongoDB client using mongomock."""
    client = AsyncMongoMockClient()
    return client


@pytest.fixture
def mock_database(mock_mongo_client):
    """Create a mock database instance."""
    return mock_mongo_client["wanderwise"]


@pytest.fixture
def mock_users_collection(mock_database):
    """Get the users collection from mock database."""
    return mock_database["users"]


@pytest.fixture
def mock_trips_collection(mock_database):
    """Get the trips collection from mock database."""
    return mock_database["trips"]


@pytest.fixture
def mock_communities_collection(mock_database):
    """Get the communities collection from mock database."""
    return mock_database["communities"]


@pytest.fixture
def mock_follows_collection(mock_database):
    """Get the follows collection from mock database."""
    return mock_database["follows"]


# ============================================================================
# FASTAPI TEST CLIENT
# ============================================================================

@pytest.fixture
def test_app():
    """Create a test FastAPI app with mocked database."""
    with patch("app.database.client") as mock_client, \
         patch("app.database.database") as mock_db:
        from app.main import create_app
        app = create_app()
        yield app


@pytest.fixture
def test_client(test_app):
    """Create a TestClient for the FastAPI app."""
    return TestClient(test_app)


# ============================================================================
# SAMPLE TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Return sample user registration data."""
    return {
        "email": "testuser@example.com",
        "password": "SecurePassword123!",
        "userName": "testuser",
        "profilePictureURL": "https://example.com/pic.jpg",
        "location": "New York, USA",
        "preference": "Adventure Travel",
        "userRole": "Traveller"
    }


@pytest.fixture
def sample_registered_user(sample_user_data) -> Dict[str, Any]:
    """Return sample registered user document from database."""
    from hashlib import sha256
    from bson import ObjectId
    
    user_doc = sample_user_data.copy()
    user_doc["_id"] = ObjectId()
    user_doc["passwordHash"] = sha256(user_doc.pop("password").encode()).hexdigest()
    user_doc["followerCount"] = 0
    user_doc["followingCount"] = 0
    return user_doc


@pytest.fixture
def sample_trip_data() -> Dict[str, Any]:
    """Return sample trip data."""
    return {
        "userID": "507f1f77bcf86cd799439011",
        "name": "Paris Summer Vacation",
        "destination": "Paris, France",
        "startDate": "2024-07-01",
        "endDate": "2024-07-10",
        "budget": 5000.0,
        "totalCost": 0.0,
        "itinerary": {
            "dayPlans": []
        }
    }


@pytest.fixture
def sample_trip_document(sample_trip_data) -> Dict[str, Any]:
    """Return sample trip document from database."""
    from bson import ObjectId
    
    trip_doc = sample_trip_data.copy()
    trip_doc["_id"] = ObjectId()
    return trip_doc


@pytest.fixture
def sample_community_data() -> Dict[str, Any]:
    """Return sample community data."""
    return {
        "name": "Europe Travel Enthusiasts",
        "description": "A community for people traveling across Europe",
        "posts": [],
        "creatorID": "507f1f77bcf86cd799439011"
    }


@pytest.fixture
def sample_community_document(sample_community_data) -> Dict[str, Any]:
    """Return sample community document from database."""
    from bson import ObjectId
    
    community_doc = sample_community_data.copy()
    community_doc["_id"] = ObjectId()
    return community_doc


@pytest.fixture
def sample_post_data() -> Dict[str, Any]:
    """Return sample post data."""
    from datetime import datetime
    
    return {
        "postID": 1,
        "title": "Amazing Paris Experience",
        "content": "Just visited the Eiffel Tower! Incredible views!",
        "likes": 0,
        "shares": 0,
        "views": 0,
        "contentType": "text",
        "authorID": "507f1f77bcf86cd799439011",
        "created_at": datetime.utcnow().isoformat(),
        "comments": []
    }


@pytest.fixture
def sample_dayplan_data() -> Dict[str, Any]:
    """Return sample day plan data."""
    return {
        "date": "2024-07-01",
        "timeline": [
            {
                "itemID": 1,
                "startTime": "08:00",
                "endTime": "10:00",
                "cost": 20.0,
                "notes": "Breakfast at café"
            }
        ]
    }


# ============================================================================
# DATABASE HELPER FIXTURES
# ============================================================================

@pytest.fixture
async def populate_test_db_with_user(mock_users_collection, sample_registered_user):
    """Insert a test user into the mock database and return user_id."""
    result = await mock_users_collection.insert_one(sample_registered_user)
    return str(result.inserted_id)


@pytest.fixture
async def populate_test_db_with_trip(mock_trips_collection, sample_trip_document):
    """Insert a test trip into the mock database and return trip_id."""
    result = await mock_trips_collection.insert_one(sample_trip_document)
    return str(result.inserted_id)


@pytest.fixture
async def populate_test_db_with_community(mock_communities_collection, sample_community_document):
    """Insert a test community into the mock database and return community_id."""
    result = await mock_communities_collection.insert_one(sample_community_document)
    return str(result.inserted_id)


# ============================================================================
# MOCK HELPER FIXTURES
# ============================================================================

@pytest.fixture
def mock_motor_client(mock_mongo_client):
    """Return a mocked Motor async MongoDB client."""
    return AsyncMock()


@pytest.fixture
def async_mock():
    """Return AsyncMock for testing async functions."""
    return AsyncMock()
