"""
test_trip_routes.py - Integration tests for trip routes.

Tests cover:
- Trip creation (success, validation)
- Get trip by ID (success, not found)
- Update trip (success, partial updates, no changes)
- Delete trip (success, not found)
- Error handling and HTTP status codes
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from bson import ObjectId
from app.routes import trip_routes


@pytest.fixture
def test_app_with_trip_routes():
    """Create a test app with only trip routes."""
    app = FastAPI()
    app.include_router(trip_routes.router, prefix="/api")
    return app


@pytest.fixture
def client(test_app_with_trip_routes):
    """Create a test client."""
    return TestClient(test_app_with_trip_routes)


class TestCreateTripRoute:
    """Tests for POST /trip/create endpoint."""

    def test_create_trip_success(self, client, sample_trip_data):
        """Test successfully creating a trip."""
        with patch("app.models.trip_models.TripDashboard.createTrip") as mock_create:
            trip_response = sample_trip_data.copy()
            trip_response["tripID"] = "507f1f77bcf86cd799439011"
            mock_create.return_value = {"success": True, "trip": trip_response}
            
            response = client.post(
                "/api/trip/create",
                data={
                    "userID": sample_trip_data["userID"],
                    "name": sample_trip_data["name"],
                    "destination": sample_trip_data["destination"],
                    "startDate": sample_trip_data["startDate"],
                    "endDate": sample_trip_data["endDate"],
                    "budget": sample_trip_data["budget"]
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_create_trip_missing_fields(self, client):
        """Test trip creation with missing required fields."""
        response = client.post(
            "/api/trip/create",
            data={
                "userID": "507f1f77bcf86cd799439011",
                "name": "Test Trip"
                # Missing destination, startDate, endDate, budget
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_trip_invalid_budget(self, client, sample_trip_data):
        """Test trip creation with invalid budget."""
        with patch("app.models.trip_models.TripDashboard.createTrip") as mock_create:
            mock_create.return_value = {"error": "Invalid budget"}
            
            response = client.post(
                "/api/trip/create",
                data={
                    "userID": sample_trip_data["userID"],
                    "name": sample_trip_data["name"],
                    "destination": sample_trip_data["destination"],
                    "startDate": sample_trip_data["startDate"],
                    "endDate": sample_trip_data["endDate"],
                    "budget": -100  # Invalid negative budget
                }
            )
            
            # The endpoint may return error in response
            assert response.status_code == 200

    def test_create_trip_inverted_dates(self, client, sample_trip_data):
        """Test trip creation with end date before start date."""
        trip_data = sample_trip_data.copy()
        trip_data["startDate"] = "2024-07-10"
        trip_data["endDate"] = "2024-07-01"
        
        with patch("app.models.trip_models.TripDashboard.createTrip") as mock_create:
            mock_create.return_value = {"error": "End date must be after start date"}
            
            response = client.post(
                "/api/trip/create",
                data=trip_data
            )
            
            assert response.status_code == 200


class TestGetTripRoute:
    """Tests for GET /trip/{tripID} endpoint."""

    def test_get_trip_success(self, client, sample_trip_document):
        """Test retrieving trip successfully."""
        user_id = sample_trip_document["userID"]
        trip_id = str(sample_trip_document["_id"])
        
        with patch("app.services.trip_service.TripService.get_trip_summary_from_db") as mock_get:
            trip_summary = {
                "tripID": trip_id,
                "name": sample_trip_document["name"],
                "destination": sample_trip_document["destination"],
                "startDate": sample_trip_document["startDate"],
                "endDate": sample_trip_document["endDate"],
                "budget": sample_trip_document["budget"],
                "totalCost": 0.0
            }
            mock_get.return_value = trip_summary
            
            response = client.get(f"/api/trip/{trip_id}?userID={user_id}")
            
            assert response.status_code == 200
            assert response.json()["tripID"] == trip_id

    def test_get_trip_not_found(self, client):
        """Test retrieving non-existent trip."""
        user_id = "507f1f77bcf86cd799439011"
        trip_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.trip_service.TripService.get_trip_summary_from_db") as mock_get:
            mock_get.return_value = {"error": "Trip not found"}
            
            response = client.get(f"/api/trip/{trip_id}?userID={user_id}")
            
            assert response.status_code == 404
            assert response.json()["detail"] == "Trip not found"

    def test_get_trip_invalid_id(self, client):
        """Test retrieving trip with invalid ID format."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.TripService.get_trip_summary_from_db") as mock_get:
            mock_get.return_value = {"error": "Invalid trip id"}
            
            response = client.get(f"/api/trip/invalid_id?userID={user_id}")
            
            assert response.status_code == 404

    def test_get_trip_missing_user_id(self, client, sample_trip_document):
        """Test retrieving trip without providing userID."""
        trip_id = str(sample_trip_document["_id"])
        
        response = client.get(f"/api/trip/{trip_id}")
        
        # userID is required as query parameter
        assert response.status_code == 422


class TestUpdateTripRoute:
    """Tests for PUT /trip/update/{tripID} endpoint."""

    def test_update_trip_success(self, client):
        """Test successfully updating trip."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.TripService.update_trip") as mock_update:
            mock_update.return_value = MagicMock(modified_count=1)
            
            response = client.put(
                f"/api/trip/update/{trip_id}",
                data={
                    "name": "Updated Trip Name",
                    "budget": 6000.0
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_update_trip_single_field(self, client):
        """Test updating single trip field."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.TripService.update_trip") as mock_update:
            mock_update.return_value = MagicMock(modified_count=1)
            
            response = client.put(
                f"/api/trip/update/{trip_id}",
                data={"destination": "Barcelona, Spain"}
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_update_trip_no_changes(self, client):
        """Test update with no valid fields provided."""
        trip_id = "507f1f77bcf86cd799439011"
        
        response = client.put(
            f"/api/trip/update/{trip_id}",
            data={}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is False

    def test_update_trip_placeholder_values(self, client):
        """Test update ignores placeholder string values."""
        trip_id = "507f1f77bcf86cd799439011"
        
        response = client.put(
            f"/api/trip/update/{trip_id}",
            data={
                "name": "string",  # Placeholder value, should be ignored
                "destination": "New Destination"
            }
        )
        
        assert response.status_code == 200

    def test_update_trip_invalid_budget(self, client):
        """Test update with zero/negative budget."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.TripService.update_trip") as mock_update:
            mock_update.return_value = MagicMock(modified_count=1)
            
            response = client.put(
                f"/api/trip/update/{trip_id}",
                data={
                    "destination": "Paris",
                    "budget": 0  # Invalid, should be ignored
                }
            )
            
            assert response.status_code == 200

    def test_update_nonexistent_trip(self, client):
        """Test updating non-existent trip."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.TripService.update_trip") as mock_update:
            mock_update.return_value = MagicMock(modified_count=0)
            
            response = client.put(
                f"/api/trip/update/{trip_id}",
                data={"name": "New Name"}
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is False


class TestDeleteTripRoute:
    """Tests for DELETE /trip/delete/{tripID} endpoint."""

    def test_delete_trip_success(self, client):
        """Test successfully deleting trip."""
        user_id = "507f1f77bcf86cd799439011"
        trip_id = "507f1f77bcf86cd799439012"
        
        with patch("app.models.trip_models.TripDashboard.deleteTrip") as mock_delete:
            mock_delete.return_value = {"success": True, "deleted": True}
            
            response = client.delete(
                f"/api/trip/delete/{trip_id}",
                params={"userID": user_id}
            )
            
            assert response.status_code == 200

    def test_delete_trip_not_found(self, client):
        """Test deleting non-existent trip."""
        user_id = "507f1f77bcf86cd799439011"
        trip_id = "507f1f77bcf86cd799439012"
        
        with patch("app.models.trip_models.TripDashboard.deleteTrip") as mock_delete:
            mock_delete.return_value = {"error": "Trip not found"}
            
            response = client.delete(
                f"/api/trip/delete/{trip_id}",
                params={"userID": user_id}
            )
            
            assert response.status_code == 200

    def test_delete_trip_missing_user_id(self, client):
        """Test deletion without userID."""
        trip_id = "507f1f77bcf86cd799439011"
        
        response = client.delete(f"/api/trip/delete/{trip_id}")
        
        # userID is required
        assert response.status_code == 422

    def test_delete_trip_wrong_user(self, client):
        """Test deletion by non-owner."""
        trip_id = "507f1f77bcf86cd799439011"
        wrong_user_id = "507f1f77bcf86cd799439999"
        
        with patch("app.models.trip_models.TripDashboard.deleteTrip") as mock_delete:
            mock_delete.return_value = {"error": "Unauthorized"}
            
            response = client.delete(
                f"/api/trip/delete/{trip_id}",
                params={"userID": wrong_user_id}
            )
            
            assert response.status_code == 200


class TestTripRouteEdgeCases:
    """Tests for edge cases in trip routes."""

    def test_create_trip_very_large_budget(self, client, sample_trip_data):
        """Test creating trip with very large budget."""
        large_budget = 1_000_000_000.0
        
        with patch("app.models.trip_models.TripDashboard.createTrip") as mock_create:
            mock_create.return_value = {"success": True}
            
            response = client.post(
                "/api/trip/create",
                data={
                    "userID": sample_trip_data["userID"],
                    "name": "Luxury World Tour",
                    "destination": "Multiple",
                    "startDate": "2024-01-01",
                    "endDate": "2024-12-31",
                    "budget": large_budget
                }
            )
            
            assert response.status_code == 200

    def test_create_trip_special_characters_in_name(self, client, sample_trip_data):
        """Test creating trip with special characters in name."""
        with patch("app.models.trip_models.TripDashboard.createTrip") as mock_create:
            mock_create.return_value = {"success": True}
            
            response = client.post(
                "/api/trip/create",
                data={
                    "userID": sample_trip_data["userID"],
                    "name": "Trip #1: Europe! 🌍",
                    "destination": sample_trip_data["destination"],
                    "startDate": sample_trip_data["startDate"],
                    "endDate": sample_trip_data["endDate"],
                    "budget": sample_trip_data["budget"]
                }
            )
            
            assert response.status_code == 200

    def test_create_trip_same_date(self, client, sample_trip_data):
        """Test creating trip with same start and end date."""
        with patch("app.models.trip_models.TripDashboard.createTrip") as mock_create:
            mock_create.return_value = {"success": True}
            
            response = client.post(
                "/api/trip/create",
                data={
                    "userID": sample_trip_data["userID"],
                    "name": "Day Trip",
                    "destination": sample_trip_data["destination"],
                    "startDate": "2024-07-01",
                    "endDate": "2024-07-01",
                    "budget": 200.0
                }
            )
            
            assert response.status_code == 200

    def test_update_trip_all_fields(self, client):
        """Test updating all trip fields at once."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.TripService.update_trip") as mock_update:
            mock_update.return_value = MagicMock(modified_count=1)
            
            response = client.put(
                f"/api/trip/update/{trip_id}",
                data={
                    "name": "New Name",
                    "destination": "New Destination",
                    "budget": 7000.0
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert len(response.json()["updated_fields"]) == 3
