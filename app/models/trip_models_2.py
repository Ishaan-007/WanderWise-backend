# app/models/trip_models.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import time
from app.services.trip_service_2 import TripService

# --- Leaf Model: ItineraryItem ---
class ItineraryItem(BaseModel):
    itemID: int
    startTime: str  # ISO time string (e.g. "08:30")
    endTime: str
    cost: float
    notes: Optional[str] = None

    @classmethod
    async def editItem(cls, trip_id: str, date: str, itemID: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an itinerary item — model sanitizes updates and calls service."""
        if not updates:
            return {"modified_count": 0}
        return await TripService.update_itinerary_item(trip_id, date, itemID, updates)
    
    # async def editItem(self, startTime: Optional[str] = None, endTime: Optional[str] = None,
    #                    cost: Optional[float] = None, notes: Optional[str] = None):
    #     if startTime is not None:
    #         self.startTime = startTime
    #     if endTime is not None:
    #         self.endTime = endTime
    #     if cost is not None:
    #         self.cost = cost
    #     if notes is not None:
    #         self.notes = notes

    # async def deleteItem(self):
    #     # deletion is handled by parent DayPlan
    #     pass


# --- Mid-level Model: DayPlan ---
class DayPlan(BaseModel):
    date: str  # ISO date string: "YYYY-MM-DD"
    timeline: List[ItineraryItem] = []

    @classmethod
    async def addItineraryItem(cls, trip_id: str, date: str, startTime: str, endTime: str, cost: float, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Add an itinerary item:
        1) fetch itinerary via service to compute next itemID
        2) delegate to service.add_itinerary_item
        """
        itinerary = await TripService.get_itinerary(trip_id)
        if itinerary is None:
            return {"error": "Trip not found"}

        day_plan = next((d for d in itinerary.get("dayPlans", []) if d.get("date") == date), None)
        if day_plan:
            next_id = max((it.get("itemID", 0) for it in day_plan.get("timeline", [])), default=0) + 1
        else:
            next_id = 1

        item = {
            "itemID": next_id,
            "startTime": startTime,
            "endTime": endTime,
            "cost": cost,
            "notes": notes
        }
        return await TripService.add_itinerary_item(trip_id, date, item)
    
    # async def addItineraryItem(self, startTime: str, endTime: str, cost: float, notes: Optional[str] = None):
    #     item = ItineraryItem(
    #         itemID=len(self.timeline) + 1,
    #         startTime=startTime,
    #         endTime=endTime,
    #         cost=cost,
    #         notes=notes
    #     )
    #     self.timeline.append(item)

    async def displayTimeline(self):
        return [item.dict() for item in self.timeline]

    @classmethod
    async def removeItem(cls, trip_id: str, date: str, itemID: int) -> Dict[str, Any]:
        """Remove an itinerary item via service."""
        return await TripService.remove_itinerary_item(trip_id, date, itemID)
    # async def removeItem(self, itemID: int):
    #     self.timeline = [item for item in self.timeline if item.itemID != itemID]


# --- Mid-level Model: Itinerary ---
class Itinerary(BaseModel):
    dayPlans: List[DayPlan] = []

    @classmethod
    async def addDayPlan(cls, trip_id: str, date: str) -> Dict[str, Any]:
        """Add a day plan to a trip via service."""
        return await TripService.add_dayplan(trip_id, {"date": date, "timeline": []})
    # async def addDayPlan(self, new_date: str):
    #     self.dayPlans.append(DayPlan(date=new_date))

    @classmethod
    async def deleteDayPlan(cls, trip_id: str, date: str) -> Dict[str, Any]:
        """
        Remove a day plan (by date) from the itinerary via service.
        """
        return await TripService.remove_dayplan(trip_id, date)

    async def viewItinerary(self):
        return [plan.dict() for plan in self.dayPlans]

    async def saveItinerary(self):
        # Models should not directly access DB — Trip model will call the service when saving
        pass


# --- Top-level Model: Trip ---
class Trip(BaseModel):
    # NOTE: tripID is a string (MongoDB _id as string). Diagram used int, but Mongo _id must be string here.
    tripID: Optional[str] = None
    userID: Optional[str] = None
    name: str
    destination: str
    startDate: str  # ISO date string "YYYY-MM-DD"
    endDate: str    # ISO date string
    budget: float
    totalCost: float = 0.0
    itinerary: Itinerary = Itinerary()

    async def displayTripSummary(self):
        """
        Return a summary for this trip (fresh from db) — model calls service.
        """
        if not self.tripID or not self.userID:
            return {"error": "tripID and userID required"}
        return await TripService.get_trip_summary_from_db(self.userID, self.tripID)

    async def calculateTotalCost(self):
        self.totalCost = sum(
            item.cost
            for plan in self.itinerary.dayPlans
            for item in plan.timeline
        )
        return self.totalCost

    async def addItinerary(self, itinerary_data: Itinerary):
        self.itinerary = itinerary_data

    async def addBooking(self, booking_data: dict):
        # Placeholder for future booking integration
        pass

    async def shareTrip(self):
        pass

    async def publishOnWanderWise(self, content: str):
        pass

    async def shareOnExternalApp(self, appName: str):
        pass

    async def generateSharingLink(self):
        return f"https://wanderwise.app/trip/{self.tripID}"

    @classmethod
    async def getItineraryDetails(cls, trip_id: str) -> Optional[Dict[str, Any]]:
        """Return itinerary object for the trip (calls service)."""
        return await TripService.get_itinerary(trip_id)
    # async def getItineraryDetais(self):
    #     return await self.itinerary.viewItinerary()

    @classmethod
    async def getTripsByUser(cls, userID: str) -> List["Trip"]:
        """
        Model method that calls service to fetch trips for a user, then returns Trip instances.
        """
        trips = await TripService.get_trips_by_user(userID)
        return [Trip(**t) for t in trips]

    async def createTrip(self, userID: str):
        """
        Create this trip in DB. Model prepares the data and delegates to service.
        Service returns inserted_id (string); model sets tripID and userID.
        """
        payload = self.dict()
        payload["userID"] = userID
        # remove tripID if None so DB will create _id
        if payload.get("tripID") is None:
            payload.pop("tripID", None)

        result = await TripService.create_trip(payload)
        if result.get("inserted_id"):
            self.tripID = result["inserted_id"]
            self.userID = userID
            return {"success": True, "trip": self.dict()}
        return {"success": False, "error": "Trip creation failed"}

    async def downloadTrip(self):
        return self.dict()


    # ------------------------
    # ITINERARY / DAYPLAN / ITEM OPERATIONS (Model → Service)
    # ------------------------

    

    # @classmethod
    # async def add_dayplan(cls, trip_id: str, date: str) -> Dict[str, Any]:
    #     """Add a day plan to a trip via service."""
    #     return await TripService.add_dayplan(trip_id, {"date": date, "timeline": []})

    # @classmethod
    # async def add_itinerary_item(cls, trip_id: str, date: str, startTime: str, endTime: str, cost: float, notes: Optional[str] = None) -> Dict[str, Any]:
    #     """
    #     Add an itinerary item:
    #     1) fetch itinerary via service to compute next itemID
    #     2) delegate to service.add_itinerary_item
    #     """
    #     itinerary = await TripService.get_itinerary(trip_id)
    #     if itinerary is None:
    #         return {"error": "Trip not found"}

    #     day_plan = next((d for d in itinerary.get("dayPlans", []) if d.get("date") == date), None)
    #     if day_plan:
    #         next_id = max((it.get("itemID", 0) for it in day_plan.get("timeline", [])), default=0) + 1
    #     else:
    #         next_id = 1

    #     item = {
    #         "itemID": next_id,
    #         "startTime": startTime,
    #         "endTime": endTime,
    #         "cost": cost,
    #         "notes": notes
    #     }
    #     return await TripService.add_itinerary_item(trip_id, date, item)

    # @classmethod
    # async def update_itinerary_item(cls, trip_id: str, date: str, itemID: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    #     """Update an itinerary item — model sanitizes updates and calls service."""
    #     if not updates:
    #         return {"modified_count": 0}
    #     return await TripService.update_itinerary_item(trip_id, date, itemID, updates)

    # @classmethod
    # async def remove_itinerary_item(cls, trip_id: str, date: str, itemID: int) -> Dict[str, Any]:
    #     """Remove an itinerary item via service."""
    #     return await TripService.remove_itinerary_item(trip_id, date, itemID)


# --- Dashboard Container ---
class TripDashboard(BaseModel):
    #userID: str
    trips: List[Trip] = []

    async def createTrip(self, userID: str, name: str, destination: str, startDate: str, endDate: str, budget: float):
        # Create trip object
        new_trip = Trip(
            userID=userID,
            name=name,
            destination=destination,
            startDate=startDate,
            endDate=endDate,
            budget=budget
        )
        payload = new_trip.model_dump()
        payload.pop("tripID", None)  # ensure DB generates _id

        # Save to DB via service
        result = await TripService.create_trip(payload)
        if result.get("inserted_id"):
            new_trip.tripID = result["inserted_id"]
            self.trips.append(new_trip)
            return {"success": True, "trip": new_trip.model_dump()}
        return {"success": False, "error": "Creation failed"}
    
    async def display_trips(self, userID: str):
        trips_data = await TripService.get_trips_by_user(userID)
        self.trips = [Trip(**t) for t in trips_data]
        return self.trips

    async def loadTripsFromDB(self):
        # convenience wrapper used by routes to populate self.trips
        # if no userID provided on the dashboard instance, this function is called with user parameter in routes
        # We'll keep a no-arg version that returns empty if no trips available
        return self.trips

    async def deleteTrip(self, tripID: str):
        deleted = await TripService.delete_trip(tripID)
        if deleted:
            self.trips = [trip for trip in self.trips if trip.tripID != tripID]
            return {"success": True}
        return {"success": False, "error": "Trip not found"}
