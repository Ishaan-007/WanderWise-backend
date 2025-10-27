# app/models/trip_models.py
from fastapi import File, Form, UploadFile
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import time, datetime
from app.services.trip_service_2 import TripService
import base64

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
        2) Create ItineraryItem object
        3) delegate to service.add_itinerary_item
        """
        itinerary = await TripService.get_itinerary(trip_id)
        if itinerary is None:
            return {"error": "Trip not found"}

        day_plan = next((d for d in itinerary.get("dayPlans", []) if d.get("date") == date), None)
        if day_plan:
            next_id = max((it.get("itemID", 0) for it in day_plan.get("timeline", [])), default=0) + 1
        else:
            next_id = 1

        # Create ItineraryItem object to demonstrate object creation
        new_item = ItineraryItem(
            itemID=next_id,
            startTime=startTime,
            endTime=endTime,
            cost=cost,
            notes=notes
        )
        
        return await TripService.add_itinerary_item(trip_id, date, new_item.model_dump())
    
    # async def addItineraryItem(self, startTime: str, endTime: str, cost: float, notes: Optional[str] = None):
    #     item = ItineraryItem(
    #         itemID=len(self.timeline) + 1,
    #         startTime=startTime,
    #         endTime=endTime,
    #         cost=cost,
    #         notes=notes
    #     )
    #     self.timeline.append(item)

    @classmethod
    async def displayTimeline(cls, trip_id: str, date: str) -> Optional[Dict[str, Any]]:
        response = await TripService.get_timeline(trip_id, date)
        return response
        return [item.dict() for item in cls.timeline]

    @classmethod
    async def removeItem(cls, trip_id: str, date: str, itemID: int) -> Dict[str, Any]:
        return await TripService.remove_itinerary_item(trip_id, date, itemID)
    # async def removeItem(self, itemID: int):
    #     self.timeline = [item for item in self.timeline if item.itemID != itemID]


# --- Mid-level Model: Itinerary ---
class Itinerary(BaseModel):
    dayPlans: List[DayPlan] = []

    @classmethod
    async def addDayPlan(cls, trip_id: str, date: str) -> Dict[str, Any]:
        # Create DayPlan object to demonstrate object creation
        created_dayplan = DayPlan(
            date=date,
            timeline=[]  # Initialize with empty timeline, ready for ItineraryItems
        )
        
        # Add to database through service
        service_resp = await TripService.add_dayplan(trip_id, created_dayplan.model_dump())
        result = {"created_dayplan": created_dayplan.model_dump()}
        result.update(service_resp or {})
        return result
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


# --- Booking Model ---
class Booking(BaseModel):
    bookingID: int
    bookingType: str  # e.g., "flight", "hotel", "train", etc.
    provider: str  # e.g., "Airline Name", "Hotel Name", etc.
    bookingDate: str  # ISO date string "YYYY-MM-DD"
    bookingReference: str
    amount: float
    status: str = "confirmed"  # "confirmed", "pending", "cancelled"
    pdfData: Optional[str] = None  # Base64 encoded PDF
    notes: Optional[str] = None

    @classmethod
    async def addBooking(cls, trip_id: str, booking_type: str, provider: str, 
                        booking_date: str, booking_reference: str, amount: float,
                        pdf_file: Optional[bytes] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """Add a new booking with optional PDF attachment."""
        try:
            # Get existing bookings to determine next ID
            bookings = await TripService.get_bookings(trip_id)
            next_id = max((b.get("bookingID", 0) for b in bookings), default=0) + 1

            # Create new booking object
            booking = {
                "bookingID": next_id,
                "bookingType": booking_type,
                "provider": provider,
                "bookingDate": booking_date,
                "bookingReference": booking_reference,
                "amount": amount,
                "status": "confirmed",
                "notes": notes
            }

            # If PDF provided, encode and add to booking
            if pdf_file:
                booking["pdfData"] = base64.b64encode(pdf_file).decode('utf-8')

            return await TripService.add_booking(trip_id, booking)
        except Exception as e:
            return {"error": f"Could not add booking: {str(e)}"}

    @classmethod
    async def getBookingPDF(cls, trip_id: str, booking_id: int) -> Optional[bytes]:
        """Retrieve PDF data for a specific booking."""
        booking = await TripService.get_booking(trip_id, booking_id)
        if booking and booking.get("pdfData"):
            try:
                return base64.b64decode(booking["pdfData"])
            except Exception:
                return None
        return None

# --- Bookings Collection Model ---
class Bookings(BaseModel):
    bookings: List[Booking] = []
    totalBookingAmount: float = 0.0

    async def calculateTotalAmount(self):
        """Calculate total amount of all confirmed bookings."""
        self.totalBookingAmount = sum(
            b.amount for b in self.bookings 
            if b.status == "confirmed"
        )
        return self.totalBookingAmount

    @classmethod
    async def getBookings(cls, trip_id: str) -> Dict[str, Any]:
        """Get all bookings for a trip."""
        return await TripService.get_bookings(trip_id)

    @classmethod
    async def deleteBooking(cls, trip_id: str, booking_id: int) -> Dict[str, Any]:
        """Delete a booking by ID."""
        return await TripService.remove_booking(trip_id, booking_id)

    @classmethod
    async def updateBookingStatus(cls, trip_id: str, booking_id: int, 
                                new_status: str) -> Dict[str, Any]:
        """Update booking status."""
        if new_status not in ["confirmed", "pending", "cancelled"]:
            return {"error": "Invalid status"}
        return await TripService.update_booking_status(trip_id, booking_id, new_status)

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
    bookings: Bookings = Bookings()

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
        self.itinerary = Itinerary(**itinerary_data.model_dump())

    async def addBooking(self, tripID: str,
    bookingType: str,  # "flight", "hotel", etc.
    provider: str,
    bookingDate: str,  # "YYYY-MM-DD"
    bookingReference: str,
    amount: float,
    notes: Optional[str],
    pdfFile: Optional[UploadFile]):
        try:
            pdf_data = None
            if pdfFile:
                pdf_data = await pdfFile.read()

            result = await Booking.addBooking(
                trip_id=tripID,
                booking_type=bookingType,
                provider=provider,
                booking_date=bookingDate,
                booking_reference=bookingReference,
                amount=amount,
                pdf_file=pdf_data,
                notes=notes
            )
            
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, "booking": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def shareTrip(self, community_id: str, author_id: str, title: str, content: str) -> Dict[str, Any]:
        """
        Share this trip as a post in a community.
        Includes the trip's itinerary information in the post.
        """
        try:
            from app.models.community_models import Post
            
            # Get the trip's itinerary details
            itinerary_data = await TripService.get_itinerary(self.tripID)
            if not itinerary_data:
                return {"error": "Trip itinerary not found"}
            
            # Prepare trip summary for the post
            trip_summary = {
                "tripID": self.tripID,
                "name": self.name,
                "destination": self.destination,
                "startDate": self.startDate,
                "endDate": self.endDate,
                "budget": self.budget,
                "totalCost": self.totalCost,
                "itinerary": itinerary_data
            }
            
            # Create enhanced content that includes trip details
            # enhanced_content = f"{content}\n\n--- Trip Details ---\n"
            # enhanced_content += f"Destination: {self.destination}\n"
            # enhanced_content += f"Duration: {self.startDate} to {self.endDate}\n"
            # enhanced_content += f"Budget: ${self.budget}\n"
            # enhanced_content += f"Total Cost: ${self.totalCost}\n\n"
            # enhanced_content += "Full itinerary details are included in this post."
            
            # Create the post with trip information
            result = await Post.create(
                community_id=community_id,
                author_id=author_id,
                title=title,
                content=content,
                content_type="trip_share"
            )
            
            if "error" in result:
                return result
            
            # Add trip data to the created post
            created_post = result["created_post"]
            created_post["tripData"] = trip_summary
            
            # Update the post in the database with trip data
            from app.database import database
            from bson import ObjectId
            
            await database["communities"].update_one(
                {"_id": ObjectId(community_id), "posts.postID": created_post["postID"]},
                {"$set": {"posts.$.tripData": trip_summary}}
            )
            
            return {"success": True, "post": created_post}
            
        except Exception as e:
            return {"error": f"Could not share trip: {str(e)}"}

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
        # Create Itinerary object if not exists
        if not self.itinerary:
            self.itinerary = Itinerary(dayPlans=[])
            
        # Prepare payload with proper object creation
        payload = self.model_dump()
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
