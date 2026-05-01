# app/models/trip_models.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import time

# --- Leaf Model: ItineraryItem ---
class ItineraryItem(BaseModel):
    itemID: int
    startTime: str  # ISO time string (e.g. "08:30")
    endTime: str
    cost: float
    notes: Optional[str] = None

    async def editItem(self, startTime: Optional[str] = None, endTime: Optional[str] = None,
                       cost: Optional[float] = None, notes: Optional[str] = None):
        if startTime is not None:
            self.startTime = startTime
        if endTime is not None:
            self.endTime = endTime
        if cost is not None:
            self.cost = cost
        if notes is not None:
            self.notes = notes

    async def deleteItem(self):
        # deletion is handled by parent DayPlan
        pass


# --- Mid-level Model: DayPlan ---
class DayPlan(BaseModel):
    date: str  # ISO date string: "YYYY-MM-DD"
    timeline: List["ItineraryItem"] = []

    async def addItineraryItem(self, startTime: str, endTime: str, cost: float, notes: Optional[str] = None):
        item = ItineraryItem(
            itemID=len(self.timeline) + 1,
            startTime=startTime,
            endTime=endTime,
            cost=cost,
            notes=notes
        )
        self.timeline.append(item)

    async def displayTimeline(self):
        return [item.dict() for item in self.timeline]

    async def removeItem(self, itemID: int):
        self.timeline = [item for item in self.timeline if item.itemID != itemID]


# --- Mid-level Model: Itinerary ---
class Itinerary(BaseModel):
    dayPlans: List["DayPlan"] = []

    async def addDayPlan(self, new_date: str):
        self.dayPlans.append(DayPlan(date=new_date))

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
    itinerary: "Itinerary" = Itinerary()

    async def displayTripSummary(self):
        """
        Return a summary for this trip (fresh from db) — model calls service.
        """
        from app.services.trip_service import TripService
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

    async def getItineraryDetais(self):
        return await self.itinerary.viewItinerary()

    @classmethod
    async def getTripsByUser(cls, userID: str) -> List["Trip"]:
        """
        Model method that calls service to fetch trips for a user, then returns Trip instances.
        """
        from app.services.trip_service import TripService
        trips = await TripService.get_trips_by_user(userID)
        return [Trip(**t) for t in trips]

    async def createTrip(self, userID: str):
        """
        Create this trip in DB. Model prepares the data and delegates to service.
        Service returns inserted_id (string); model sets tripID and userID.
        """
        from app.services.trip_service import TripService
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


# --- Dashboard Container ---
# app/models/trip_models.py
class TripDashboard(BaseModel):
    #userID: str
    trips: List["Trip"] = []

    # @staticmethod
    # async def get_user_dashboard(userID: str):
        
        
    async def createTrip(self, userID: str, name: str, destination: str, startDate: str, endDate: str, budget: float):
        # Create trip object
        from app.services.trip_service import TripService
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
    
    @staticmethod
    async def display_trips(userID: str):
        from app.services.trip_service import TripService
        trips_data = await TripService.get_trips_by_user(userID)
        return [Trip(**t) for t in trips_data]

    async def deleteTrip(self, tripID: str):
        from app.services.trip_service import TripService
        deleted = await TripService.delete_trip(tripID)
        if deleted:
            self.trips = [trip for trip in self.trips if trip.tripID != tripID]
            return {"success": True}
        return {"success": False, "error": "Trip not found"}