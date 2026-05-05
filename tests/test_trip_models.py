"""
test_trip_models.py - Unit tests for trip model classes.

Tests cover:
- ItineraryItem editing and deletion
- DayPlan timeline management
- Itinerary day plan operations
- Trip creation, summary display, and cost calculation
- Model validation and error handling
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from bson import ObjectId
from app.models.trip_models import ItineraryItem, DayPlan, Itinerary, Trip


class TestItineraryItem:
    """Tests for ItineraryItem model."""

    def test_itinerary_item_creation(self):
        """Test creating an itinerary item."""
        item = ItineraryItem(
            itemID=1,
            startTime="08:00",
            endTime="10:00",
            cost=50.0,
            notes="Breakfast at café"
        )
        
        assert item.itemID == 1
        assert item.startTime == "08:00"
        assert item.endTime == "10:00"
        assert item.cost == 50.0
        assert item.notes == "Breakfast at café"

    def test_itinerary_item_without_notes(self):
        """Test creating item without notes."""
        item = ItineraryItem(
            itemID=1,
            startTime="08:00",
            endTime="10:00",
            cost=50.0
        )
        
        assert item.notes is None

    @pytest.mark.asyncio
    async def test_edit_item_update_cost(self):
        """Test editing item cost."""
        item = ItineraryItem(
            itemID=1,
            startTime="08:00",
            endTime="10:00",
            cost=50.0
        )
        
        await item.editItem(cost=75.0)
        
        assert item.cost == 75.0
        assert item.startTime == "08:00"  # Unchanged

    @pytest.mark.asyncio
    async def test_edit_item_update_time(self):
        """Test editing item times."""
        item = ItineraryItem(
            itemID=1,
            startTime="08:00",
            endTime="10:00",
            cost=50.0
        )
        
        await item.editItem(startTime="09:00", endTime="11:00")
        
        assert item.startTime == "09:00"
        assert item.endTime == "11:00"

    @pytest.mark.asyncio
    async def test_edit_item_update_notes(self):
        """Test editing item notes."""
        item = ItineraryItem(
            itemID=1,
            startTime="08:00",
            endTime="10:00",
            cost=50.0,
            notes="Old notes"
        )
        
        await item.editItem(notes="New notes")
        
        assert item.notes == "New notes"

    @pytest.mark.asyncio
    async def test_edit_item_no_changes(self):
        """Test editing item without any changes."""
        item = ItineraryItem(
            itemID=1,
            startTime="08:00",
            endTime="10:00",
            cost=50.0
        )
        original_item = item.copy(deep=True)
        
        await item.editItem()
        
        assert item.dict() == original_item.dict()

    @pytest.mark.asyncio
    async def test_delete_item(self):
        """Test item deletion (no-op in model)."""
        item = ItineraryItem(
            itemID=1,
            startTime="08:00",
            endTime="10:00",
            cost=50.0
        )
        
        # deleteItem is a no-op; deletion is handled by DayPlan
        await item.deleteItem()
        
        assert item.itemID == 1  # Item still exists


class TestDayPlan:
    """Tests for DayPlan model."""

    def test_dayplan_creation(self):
        """Test creating a day plan."""
        dayplan = DayPlan(date="2024-07-01", timeline=[])
        
        assert dayplan.date == "2024-07-01"
        assert len(dayplan.timeline) == 0

    def test_dayplan_with_items(self, sample_dayplan_data):
        """Test creating day plan with timeline items."""
        item_dict = sample_dayplan_data["timeline"][0]
        item = ItineraryItem(**item_dict)
        
        dayplan = DayPlan(date=sample_dayplan_data["date"], timeline=[item])
        
        assert dayplan.date == sample_dayplan_data["date"]
        assert len(dayplan.timeline) == 1
        assert dayplan.timeline[0].itemID == 1

    @pytest.mark.asyncio
    async def test_add_itinerary_item(self):
        """Test adding item to day plan."""
        dayplan = DayPlan(date="2024-07-01")
        
        await dayplan.addItineraryItem(
            startTime="08:00",
            endTime="10:00",
            cost=50.0,
            notes="Breakfast"
        )
        
        assert len(dayplan.timeline) == 1
        assert dayplan.timeline[0].itemID == 1
        assert dayplan.timeline[0].cost == 50.0

    @pytest.mark.asyncio
    async def test_add_multiple_items(self):
        """Test adding multiple items to day plan."""
        dayplan = DayPlan(date="2024-07-01")
        
        await dayplan.addItineraryItem("08:00", "10:00", 50.0, "Breakfast")
        await dayplan.addItineraryItem("12:00", "13:00", 30.0, "Lunch")
        await dayplan.addItineraryItem("18:00", "20:00", 80.0, "Dinner")
        
        assert len(dayplan.timeline) == 3
        assert dayplan.timeline[2].itemID == 3

    @pytest.mark.asyncio
    async def test_display_timeline(self):
        """Test displaying timeline."""
        dayplan = DayPlan(date="2024-07-01")
        await dayplan.addItineraryItem("08:00", "10:00", 50.0, "Breakfast")
        
        timeline = await dayplan.displayTimeline()
        
        assert len(timeline) == 1
        assert timeline[0]["itemID"] == 1

    @pytest.mark.asyncio
    async def test_display_empty_timeline(self):
        """Test displaying empty timeline."""
        dayplan = DayPlan(date="2024-07-01")
        
        timeline = await dayplan.displayTimeline()
        
        assert timeline == []

    @pytest.mark.asyncio
    async def test_remove_item(self):
        """Test removing item from timeline."""
        dayplan = DayPlan(date="2024-07-01")
        await dayplan.addItineraryItem("08:00", "10:00", 50.0)
        await dayplan.addItineraryItem("12:00", "13:00", 30.0)
        
        await dayplan.removeItem(1)
        
        assert len(dayplan.timeline) == 1
        assert dayplan.timeline[0].itemID == 2

    @pytest.mark.asyncio
    async def test_remove_nonexistent_item(self):
        """Test removing non-existent item."""
        dayplan = DayPlan(date="2024-07-01")
        await dayplan.addItineraryItem("08:00", "10:00", 50.0)
        
        await dayplan.removeItem(999)
        
        assert len(dayplan.timeline) == 1  # Item still there


class TestItinerary:
    """Tests for Itinerary model."""

    def test_itinerary_creation(self):
        """Test creating an itinerary."""
        itinerary = Itinerary(dayPlans=[])
        
        assert len(itinerary.dayPlans) == 0

    @pytest.mark.asyncio
    async def test_add_dayplan(self):
        """Test adding a day plan to itinerary."""
        itinerary = Itinerary()
        
        await itinerary.addDayPlan("2024-07-01")
        
        assert len(itinerary.dayPlans) == 1
        assert itinerary.dayPlans[0].date == "2024-07-01"

    @pytest.mark.asyncio
    async def test_add_multiple_dayplans(self):
        """Test adding multiple day plans."""
        itinerary = Itinerary()
        
        await itinerary.addDayPlan("2024-07-01")
        await itinerary.addDayPlan("2024-07-02")
        await itinerary.addDayPlan("2024-07-03")
        
        assert len(itinerary.dayPlans) == 3

    @pytest.mark.asyncio
    async def test_view_itinerary(self):
        """Test viewing itinerary."""
        itinerary = Itinerary()
        await itinerary.addDayPlan("2024-07-01")
        
        view = await itinerary.viewItinerary()
        
        assert len(view) == 1
        assert view[0]["date"] == "2024-07-01"

    @pytest.mark.asyncio
    async def test_view_empty_itinerary(self):
        """Test viewing empty itinerary."""
        itinerary = Itinerary()
        
        view = await itinerary.viewItinerary()
        
        assert view == []

    @pytest.mark.asyncio
    async def test_save_itinerary(self):
        """Test saving itinerary (no-op in model)."""
        itinerary = Itinerary()
        await itinerary.addDayPlan("2024-07-01")
        
        # saveItinerary is a no-op; actual save happens through Trip.save_trip
        await itinerary.saveItinerary()
        
        assert len(itinerary.dayPlans) == 1


class TestTrip:
    """Tests for Trip model."""

    def test_trip_creation(self, sample_trip_data):
        """Test creating a trip."""
        trip = Trip(
            name=sample_trip_data["name"],
            destination=sample_trip_data["destination"],
            startDate=sample_trip_data["startDate"],
            endDate=sample_trip_data["endDate"],
            budget=sample_trip_data["budget"]
        )
        
        assert trip.name == sample_trip_data["name"]
        assert trip.destination == sample_trip_data["destination"]
        assert trip.budget == sample_trip_data["budget"]
        assert trip.totalCost == 0.0

    def test_trip_with_ids(self, sample_trip_data):
        """Test trip with IDs."""
        trip = Trip(
            tripID="507f1f77bcf86cd799439011",
            userID="507f1f77bcf86cd799439012",
            name=sample_trip_data["name"],
            destination=sample_trip_data["destination"],
            startDate=sample_trip_data["startDate"],
            endDate=sample_trip_data["endDate"],
            budget=sample_trip_data["budget"]
        )
        
        assert trip.tripID == "507f1f77bcf86cd799439011"
        assert trip.userID == "507f1f77bcf86cd799439012"

    @pytest.mark.asyncio
    async def test_calculate_total_cost_empty(self, sample_trip_data):
        """Test cost calculation with no items."""
        trip = Trip(**sample_trip_data)
        
        total = await trip.calculateTotalCost()
        
        assert total == 0.0
        assert trip.totalCost == 0.0

    @pytest.mark.asyncio
    async def test_calculate_total_cost_with_items(self):
        """Test cost calculation with itinerary items."""
        trip = Trip(
            name="Trip",
            destination="Paris",
            startDate="2024-07-01",
            endDate="2024-07-10",
            budget=5000.0
        )
        
        # Add items
        dayplan = DayPlan(date="2024-07-01")
        await dayplan.addItineraryItem("08:00", "10:00", 50.0)
        await dayplan.addItineraryItem("12:00", "13:00", 30.0)
        
        trip.itinerary.dayPlans.append(dayplan)
        
        total = await trip.calculateTotalCost()
        
        assert total == 80.0
        assert trip.totalCost == 80.0

    @pytest.mark.asyncio
    async def test_calculate_total_cost_multiple_days(self):
        """Test cost calculation across multiple days."""
        trip = Trip(
            name="Trip",
            destination="Paris",
            startDate="2024-07-01",
            endDate="2024-07-10",
            budget=5000.0
        )
        
        # Day 1
        day1 = DayPlan(date="2024-07-01")
        await day1.addItineraryItem("08:00", "10:00", 50.0)
        await day1.addItineraryItem("12:00", "13:00", 30.0)
        
        # Day 2
        day2 = DayPlan(date="2024-07-02")
        await day2.addItineraryItem("08:00", "11:00", 100.0)
        
        trip.itinerary.dayPlans.append(day1)
        trip.itinerary.dayPlans.append(day2)
        
        total = await trip.calculateTotalCost()
        
        assert total == 180.0

    @pytest.mark.asyncio
    async def test_add_itinerary(self):
        """Test adding itinerary to trip."""
        trip = Trip(
            name="Trip",
            destination="Paris",
            startDate="2024-07-01",
            endDate="2024-07-10",
            budget=5000.0
        )
        
        new_itinerary = Itinerary()
        await new_itinerary.addDayPlan("2024-07-01")
        
        await trip.addItinerary(new_itinerary)
        
        assert len(trip.itinerary.dayPlans) == 1

    @pytest.mark.asyncio
    async def test_display_trip_summary(self):
        """Test displaying trip summary."""
        trip_id = "507f1f77bcf86cd799439011"
        user_id = "507f1f77bcf86cd799439012"
        
        trip = Trip(
            tripID=trip_id,
            userID=user_id,
            name="Paris Trip",
            destination="Paris, France",
            startDate="2024-07-01",
            endDate="2024-07-10",
            budget=5000.0
        )
        
        with patch("app.services.trip_service.TripService.get_trip_summary_from_db") as mock_summary:
            mock_summary.return_value = {
                "tripID": trip_id,
                "name": "Paris Trip",
                "destination": "Paris, France",
                "budget": 5000.0
            }
            
            summary = await trip.displayTripSummary()
            
            assert summary is not None
            assert summary["tripID"] == trip_id

    @pytest.mark.asyncio
    async def test_display_trip_summary_missing_ids(self):
        """Test displaying summary without required IDs."""
        trip = Trip(
            name="Trip",
            destination="Paris",
            startDate="2024-07-01",
            endDate="2024-07-10",
            budget=5000.0
        )
        
        summary = await trip.displayTripSummary()
        
        assert "error" in summary

    @pytest.mark.asyncio
    async def test_trip_serialization(self, sample_trip_data):
        """Test trip model serialization."""
        trip = Trip(**sample_trip_data)
        trip_dict = trip.model_dump()
        
        assert "name" in trip_dict
        assert "destination" in trip_dict
        assert "budget" in trip_dict
        assert "itinerary" in trip_dict


class TestTripEdgeCases:
    """Tests for edge cases in trip models."""

    @pytest.mark.asyncio
    async def test_trip_with_very_long_names(self):
        """Test trip with very long names."""
        long_name = "A" * 1000
        
        trip = Trip(
            name=long_name,
            destination="Paris, France",
            startDate="2024-07-01",
            endDate="2024-07-10",
            budget=5000.0
        )
        
        assert trip.name == long_name

    @pytest.mark.asyncio
    async def test_trip_with_zero_budget(self):
        """Test trip with zero budget."""
        trip = Trip(
            name="Trip",
            destination="Paris",
            startDate="2024-07-01",
            endDate="2024-07-10",
            budget=0.0
        )
        
        assert trip.budget == 0.0

    @pytest.mark.asyncio
    async def test_trip_with_very_large_budget(self):
        """Test trip with very large budget."""
        large_budget = 1_000_000_000.0
        
        trip = Trip(
            name="Luxury Trip",
            destination="World Tour",
            startDate="2024-01-01",
            endDate="2024-12-31",
            budget=large_budget
        )
        
        assert trip.budget == large_budget

    @pytest.mark.asyncio
    async def test_itinerary_item_with_fractional_cost(self):
        """Test itinerary item with fractional cost."""
        item = ItineraryItem(
            itemID=1,
            startTime="08:00",
            endTime="10:00",
            cost=50.99
        )
        
        assert item.cost == 50.99

    @pytest.mark.asyncio
    async def test_dayplan_zero_cost_items(self):
        """Test day plan with zero-cost items."""
        dayplan = DayPlan(date="2024-07-01")
        
        await dayplan.addItineraryItem("08:00", "10:00", 0.0, "Free breakfast")
        
        assert len(dayplan.timeline) == 1
        assert dayplan.timeline[0].cost == 0.0
