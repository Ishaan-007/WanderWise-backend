"""
test_trip_service.py - Unit tests for TripService and ItineraryService.

Tests cover:
- Trip CRUD operations (create, read, update, delete)
- Trip retrieval by user
- Itinerary management (add dayplan, add items, remove items, update items)
- Error handling for invalid IDs and missing data
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from bson import ObjectId
from app.services.trip_service import TripService, ItineraryService


class TestTripServiceCreate:
    """Tests for trip creation."""

    @pytest.mark.asyncio
    async def test_create_trip_success(self, sample_trip_data):
        """Test successful trip creation."""
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            inserted_id = ObjectId()
            mock_trips.insert_one.return_value = MagicMock(inserted_id=inserted_id)
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.create_trip(sample_trip_data)
            
            assert result["inserted_id"] == str(inserted_id)
            mock_trips.insert_one.assert_called_once_with(sample_trip_data)

    @pytest.mark.asyncio
    async def test_create_trip_with_all_fields(self, sample_trip_data):
        """Test trip creation with all fields populated."""
        trip_data = sample_trip_data.copy()
        trip_data["totalCost"] = 4500.0
        trip_data["itinerary"]["dayPlans"] = [
            {
                "date": "2024-07-01",
                "timeline": [{"itemID": 1, "startTime": "08:00", "endTime": "10:00", "cost": 50.0}]
            }
        ]
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.insert_one.return_value = MagicMock(inserted_id=ObjectId())
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.create_trip(trip_data)
            
            assert "inserted_id" in result


class TestTripServiceGetTrip:
    """Tests for trip retrieval."""

    @pytest.mark.asyncio
    async def test_get_trip_by_id_found(self, sample_trip_document):
        """Test retrieving trip by ID when trip exists."""
        trip_id = str(sample_trip_document["_id"])
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.find_one.return_value = sample_trip_document
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.get_trip_by_id(trip_id)
            
            assert result is not None
            assert result["tripID"] == trip_id
            assert "_id" not in result

    @pytest.mark.asyncio
    async def test_get_trip_by_id_not_found(self):
        """Test retrieving trip by ID when trip doesn't exist."""
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.find_one.return_value = None
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.get_trip_by_id("507f1f77bcf86cd799439011")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_trips_by_user_success(self, sample_trip_document):
        """Test retrieving all trips for a user."""
        user_id = sample_trip_document["userID"]
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            
            # Mock async cursor
            async def async_iter():
                yield sample_trip_document
            
            mock_trips.find = MagicMock(return_value=async_iter())
            mock_db.__getitem__.return_value = mock_trips
            
            expected_id = str(sample_trip_document["_id"])
            result = await TripService.get_trips_by_user(user_id)
            
            assert len(result) == 1
            assert result[0]["tripID"] == expected_id

    @pytest.mark.asyncio
    async def test_get_trips_by_user_empty(self):
        """Test retrieving trips when user has no trips."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            
            async def async_iter():
                return
                yield  # Empty generator
            
            mock_trips.find = MagicMock(return_value=async_iter())
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.get_trips_by_user(user_id)
            
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_trip_summary_success(self, sample_trip_document):
        """Test retrieving trip summary."""
        user_id = sample_trip_document["userID"]
        trip_id = str(sample_trip_document["_id"])
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.find_one.return_value = sample_trip_document
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.get_trip_summary_from_db(user_id, trip_id)
            
            assert "tripID" in result
            assert "name" in result
            assert "destination" in result
            assert "budget" in result

    @pytest.mark.asyncio
    async def test_get_trip_summary_not_found(self):
        """Test trip summary when trip doesn't exist."""
        user_id = "507f1f77bcf86cd799439011"
        trip_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.find_one.return_value = None
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.get_trip_summary_from_db(user_id, trip_id)
            
            assert "error" in result
            assert result["error"] == "Trip not found"

    @pytest.mark.asyncio
    async def test_get_trip_summary_invalid_id(self):
        """Test trip summary with invalid trip ID."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.find_one.side_effect = Exception("Invalid ObjectId")
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.get_trip_summary_from_db(user_id, "invalid_id")
            
            assert "error" in result
            assert result["error"] == "Invalid trip id"


class TestTripServiceUpdate:
    """Tests for trip updates."""

    @pytest.mark.asyncio
    async def test_update_trip_success(self):
        """Test successful trip update."""
        trip_id = "507f1f77bcf86cd799439011"
        update_data = {"name": "Updated Trip Name", "budget": 6000.0}
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.update_one.return_value = MagicMock(modified_count=1)
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.update_trip(trip_id, update_data)
            
            mock_trips.update_one.assert_called_once()
            call_args = mock_trips.update_one.call_args
            assert call_args[0][1] == {"$set": update_data}

    @pytest.mark.asyncio
    async def test_update_trip_no_changes(self):
        """Test update when trip doesn't exist."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.update_one.return_value = MagicMock(modified_count=0)
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.update_trip(trip_id, {"name": "New Name"})
            
            # Check return value has modified_count
            assert hasattr(result, "modified_count")


class TestTripServiceDelete:
    """Tests for trip deletion."""

    @pytest.mark.asyncio
    async def test_delete_trip_success(self):
        """Test successful trip deletion."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.delete_one.return_value = MagicMock(deleted_count=1)
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.delete_trip(trip_id)
            
            assert result == 1
            mock_trips.delete_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_trip_not_found(self):
        """Test deletion when trip doesn't exist."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.delete_one.return_value = MagicMock(deleted_count=0)
            mock_db.__getitem__.return_value = mock_trips
            
            result = await TripService.delete_trip(trip_id)
            
            assert result == 0


class TestItineraryServiceGetItinerary:
    """Tests for retrieving itineraries."""

    @pytest.mark.asyncio
    async def test_get_itinerary_found(self, sample_dayplan_data):
        """Test retrieving itinerary when it exists."""
        trip_id = "507f1f77bcf86cd799439011"
        
        trip_doc = {
            "_id": ObjectId(trip_id),
            "itinerary": {"dayPlans": [sample_dayplan_data]}
        }
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.find_one.return_value = trip_doc
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.get_itinerary(trip_id)
            
            assert result is not None
            assert "dayPlans" in result
            assert len(result["dayPlans"]) == 1

    @pytest.mark.asyncio
    async def test_get_itinerary_empty(self):
        """Test retrieving itinerary with no dayplans."""
        trip_id = "507f1f77bcf86cd799439011"
        
        trip_doc = {"_id": ObjectId(trip_id), "itinerary": {"dayPlans": []}}
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.find_one.return_value = trip_doc
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.get_itinerary(trip_id)
            
            assert result is not None
            assert len(result["dayPlans"]) == 0

    @pytest.mark.asyncio
    async def test_get_itinerary_not_found(self):
        """Test retrieving itinerary when trip doesn't exist."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.find_one.return_value = None
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.get_itinerary(trip_id)
            
            assert result is None


class TestItineraryServiceAddDayplan:
    """Tests for adding dayplans."""

    @pytest.mark.asyncio
    async def test_add_dayplan_success(self, sample_dayplan_data):
        """Test successfully adding a dayplan."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.update_one.return_value = MagicMock(modified_count=1)
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.add_dayplan(trip_id, sample_dayplan_data)
            
            assert result["modified_count"] == 1
            mock_trips.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_dayplan_invalid_trip(self):
        """Test adding dayplan to non-existent trip."""
        trip_id = "507f1f77bcf86cd799439011"
        dayplan_data = {"date": "2024-07-01", "timeline": []}
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.update_one.return_value = MagicMock(modified_count=0)
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.add_dayplan(trip_id, dayplan_data)
            
            assert result["modified_count"] == 0


class TestItineraryServiceAddItem:
    """Tests for adding itinerary items."""

    @pytest.mark.asyncio
    async def test_add_itinerary_item_to_existing_dayplan(self):
        """Test adding item to existing dayplan."""
        trip_id = "507f1f77bcf86cd799439011"
        date = "2024-07-01"
        item = {"itemID": 1, "startTime": "08:00", "endTime": "10:00", "cost": 50.0}
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.update_one.return_value = MagicMock(modified_count=1)
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.add_itinerary_item(trip_id, date, item)
            
            assert result["modified_count"] == 1
            assert result["created_dayplan"] is False

    @pytest.mark.asyncio
    async def test_add_itinerary_item_create_dayplan(self):
        """Test adding item creates new dayplan if not exists."""
        trip_id = "507f1f77bcf86cd799439011"
        date = "2024-07-01"
        item = {"itemID": 1, "startTime": "08:00", "endTime": "10:00", "cost": 50.0}
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            # First update fails (dayplan doesn't exist), second succeeds
            mock_trips.update_one.side_effect = [
                MagicMock(modified_count=0),
                MagicMock(modified_count=1)
            ]
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.add_itinerary_item(trip_id, date, item)
            
            assert result["modified_count"] == 1
            assert result["created_dayplan"] is True


class TestItineraryServiceRemoveItem:
    """Tests for removing itinerary items."""

    @pytest.mark.asyncio
    async def test_remove_itinerary_item_success(self):
        """Test successfully removing an itinerary item."""
        trip_id = "507f1f77bcf86cd799439011"
        date = "2024-07-01"
        item_id = 1
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.update_one.return_value = MagicMock(modified_count=1)
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.remove_itinerary_item(trip_id, date, item_id)
            
            assert result["modified_count"] == 1

    @pytest.mark.asyncio
    async def test_remove_itinerary_item_not_found(self):
        """Test removing item that doesn't exist."""
        trip_id = "507f1f77bcf86cd799439011"
        date = "2024-07-01"
        item_id = 999
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.update_one.return_value = MagicMock(modified_count=0)
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.remove_itinerary_item(trip_id, date, item_id)
            
            assert result["modified_count"] == 0

    @pytest.mark.asyncio
    async def test_remove_itinerary_item_error(self):
        """Test error handling when removing item."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.update_one.side_effect = Exception("Database error")
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.remove_itinerary_item(trip_id, "2024-07-01", 1)
            
            assert "error" in result


class TestItineraryServiceUpdateItem:
    """Tests for updating itinerary items."""

    @pytest.mark.asyncio
    async def test_update_itinerary_item_success(self):
        """Test successfully updating an itinerary item."""
        trip_id = "507f1f77bcf86cd799439011"
        date = "2024-07-01"
        item_id = 1
        updates = {"cost": 60.0, "notes": "Updated notes"}
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.update_one.return_value = MagicMock(modified_count=1)
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.update_itinerary_item(trip_id, date, item_id, updates)
            
            assert result["modified_count"] == 1

    @pytest.mark.asyncio
    async def test_update_itinerary_item_empty_updates(self):
        """Test update with no fields provided."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.database") as mock_db:
            result = await ItineraryService.update_itinerary_item(trip_id, "2024-07-01", 1, {})
            
            assert result["modified_count"] == 0

    @pytest.mark.asyncio
    async def test_update_itinerary_item_error(self):
        """Test error handling when updating item."""
        trip_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.trip_service.database") as mock_db:
            mock_trips = AsyncMock()
            mock_trips.update_one.side_effect = Exception("Database error")
            mock_db.__getitem__.return_value = mock_trips
            
            result = await ItineraryService.update_itinerary_item(
                trip_id, "2024-07-01", 1, {"cost": 100.0}
            )
            
            assert "error" in result
