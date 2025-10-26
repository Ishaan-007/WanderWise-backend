# app/services/trip_service.py
from app.database import database
from bson import ObjectId
from typing import List, Dict, Any, Optional

class TripService:
    @staticmethod
    async def create_trip(trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a new trip into the database. Returns inserted_id as string.
        """
        result = await database["trips"].insert_one(trip_data)
        return {"inserted_id": str(result.inserted_id)}

    @staticmethod
    async def get_trip_by_id(trip_id: str) -> Dict[str, Any] | None:
        trip = await database["trips"].find_one({"_id": ObjectId(trip_id)})
        if trip:
            trip["tripID"] = str(trip["_id"])
            trip.pop("_id", None)
        return trip

    @staticmethod
    async def get_trips_by_user(user_id: str) -> List[Dict[str, Any]]:
        cursor = database["trips"].find({"userID": user_id})
        trips = []
        async for trip in cursor:
            trip["tripID"] = str(trip["_id"])
            trip.pop("_id", None)
            trips.append(trip)
        return trips

    @staticmethod
    async def get_trip_summary_from_db(user_id: str, trip_id: str) -> Dict[str, Any]:
        """
        Return summary fields for a trip belonging to user_id.
        """
        try:
            trip_doc = await database["trips"].find_one({"userID": user_id, "_id": ObjectId(trip_id)})
        except Exception:
            return {"error": "Invalid trip id"}
        if not trip_doc:
            return {"error": "Trip not found"}
        trip_doc["tripID"] = str(trip_doc["_id"])
        trip_doc.pop("_id", None)
        return {
            "tripID": trip_doc["tripID"],
            "name": trip_doc.get("name"),
            "destination": trip_doc.get("destination"),
            "startDate": trip_doc.get("startDate"),
            "endDate": trip_doc.get("endDate"),
            "budget": trip_doc.get("budget"),
            "totalCost": trip_doc.get("totalCost"),
        }

    @staticmethod
    async def update_trip(trip_id: str, data: dict):
        result = await database["trips"].update_one({"_id": ObjectId(trip_id)}, {"$set": data})
        return result

    @staticmethod
    async def delete_trip(trip_id: str):
        result = await database["trips"].delete_one({"_id": ObjectId(trip_id)})
        return result.deleted_count


    # -------------------------
    # BOOKING HELPERS
    # -------------------------
    @staticmethod
    async def get_bookings(trip_id: str) -> List[Dict[str, Any]]:
        """Get all bookings for a trip."""
        try:
            trip = await database["trips"].find_one(
                {"_id": ObjectId(trip_id)},
                {"bookings.bookings": 1}
            )
            return trip.get("bookings", {}).get("bookings", []) if trip else []
        except Exception:
            return []

    @staticmethod
    async def get_booking(trip_id: str, booking_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific booking by ID."""
        try:
            trip = await database["trips"].find_one(
                {
                    "_id": ObjectId(trip_id),
                    "bookings.bookings.bookingID": booking_id
                },
                {"bookings.bookings.$": 1}
            )
            if trip and trip.get("bookings", {}).get("bookings"):
                return trip["bookings"]["bookings"][0]
            return None
        except Exception:
            return None

    @staticmethod
    async def add_booking(trip_id: str, booking: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new booking to the trip."""
        try:
            # First ensure bookings array exists
            await database["trips"].update_one(
                {"_id": ObjectId(trip_id)},
                {"$setOnInsert": {"bookings": {"bookings": [], "totalBookingAmount": 0.0}}}
            )

            # Add the booking
            res = await database["trips"].update_one(
                {"_id": ObjectId(trip_id)},
                {
                    "$push": {"bookings.bookings": booking},
                    "$inc": {"bookings.totalBookingAmount": booking.get("amount", 0)}
                }
            )
            return {"modified_count": getattr(res, "modified_count", 0)}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def remove_booking(trip_id: str, booking_id: int) -> Dict[str, Any]:
        """Remove a booking by ID."""
        try:
            # First get the booking to subtract its amount
            booking = await TripService.get_booking(trip_id, booking_id)
            if booking:
                res = await database["trips"].update_one(
                    {"_id": ObjectId(trip_id)},
                    {
                        "$pull": {"bookings.bookings": {"bookingID": booking_id}},
                        "$inc": {"bookings.totalBookingAmount": -booking.get("amount", 0)}
                    }
                )
                return {"modified_count": getattr(res, "modified_count", 0)}
            return {"error": "Booking not found"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def update_booking_status(trip_id: str, booking_id: int, new_status: str) -> Dict[str, Any]:
        """Update the status of a booking."""
        try:
            res = await database["trips"].update_one(
                {
                    "_id": ObjectId(trip_id),
                    "bookings.bookings.bookingID": booking_id
                },
                {"$set": {"bookings.bookings.$.status": new_status}}
            )
            return {"modified_count": getattr(res, "modified_count", 0)}
        except Exception as e:
            return {"error": str(e)}

    # -------------------------
    # ITINERARY / DAYPLAN / ITEM DB HELPERS (used by Trip model)
    # -------------------------
    @staticmethod
    async def get_itinerary(trip_id: str) -> Optional[Dict[str, Any]]:
        """Return the itinerary object (or None if trip missing)."""
        try:
            trip = await database["trips"].find_one({"_id": ObjectId(trip_id)}, {"itinerary": 1})
        except Exception:
            return None
        if not trip:
            return None
        return trip.get("itinerary", {"dayPlans": []})
    
    @staticmethod
    async def get_timeline(trip_id: str, date: str) -> Optional[Dict[str, Any]]:
        """Return the itinerary object (or None if trip missing)."""
        try:
            trip = await database["trips"].find_one({"_id": ObjectId(trip_id)}, {"itinerary": 1})
            trip["itinerary"]["dayPlans"] = [dp for dp in trip["itinerary"]["dayPlans"] if dp["date"] == date]
        except Exception:
            return None
        if not trip:
            return None
        return trip.get("itinerary", {"dayPlans": []})

    @staticmethod
    async def add_dayplan(trip_id: str, dayplan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a DayPlan object to itinerary.dayPlans.
        dayplan: {"date": "...", "timeline": [...]}
        """
        try:
            # First check if the trip exists and has an itinerary field
            trip = await database["trips"].find_one({"_id": ObjectId(trip_id)})
            if not trip:
                return {"error": "Trip not found"}

            # Initialize itinerary if it doesn't exist
            if "itinerary" not in trip:
                await database["trips"].update_one(
                    {"_id": ObjectId(trip_id)},
                    {"$set": {"itinerary": {"dayPlans": []}}}
                )
            
            # Check if a dayplan with this date already exists
            existing_dayplan = await database["trips"].find_one(
                {
                    "_id": ObjectId(trip_id),
                    "itinerary.dayPlans.date": dayplan["date"]
                }
            )
            if existing_dayplan:
                return {"error": f"Day plan for date {dayplan['date']} already exists"}
            
            # Now add the dayplan
            res = await database["trips"].update_one(
                {"_id": ObjectId(trip_id)},
                {"$push": {"itinerary.dayPlans": dayplan}}
            )
            return {"modified_count": getattr(res, "modified_count", 0)}
        except Exception as e:
            return {"error": f"Could not add day plan: {str(e)}"}

    @staticmethod
    async def remove_dayplan(trip_id: str, date: str) -> Dict[str, Any]:
        """
        Remove a DayPlan from itinerary.dayPlans identified by its date.
        """
        try:
            res = await database["trips"].update_one(
                {"_id": ObjectId(trip_id)},
                {"$pull": {"itinerary.dayPlans": {"date": date}}}
            )
            return {"modified_count": getattr(res, "modified_count", 0)}
        except Exception as e:
            return {"error": str(e)}
        
    @staticmethod
    async def add_itinerary_item(trip_id: str, date: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add an ItineraryItem to an existing DayPlan with the given date.
        If the day plan does not exist, create it with the item as the first timeline entry.
        Also increments trip.totalCost by item['cost'] (if numeric).
        """
        try:
            # Try to push onto existing dayPlan.timeline using positional $ operator
            res = await database["trips"].update_one(
                {"_id": ObjectId(trip_id), "itinerary.dayPlans.date": date},
                {"$push": {"itinerary.dayPlans.$.timeline": item}}
            )
            if getattr(res, "modified_count", 0) > 0:
                # increment totalCost
                try:
                    inc_val = float(item.get("cost", 0))
                except Exception:
                    inc_val = 0.0
                if inc_val != 0.0:
                    await database["trips"].update_one({"_id": ObjectId(trip_id)}, {"$inc": {"totalCost": inc_val}})
                updated = await database["trips"].find_one({"_id": ObjectId(trip_id)}, {"totalCost": 1})
                return {"modified_count": res.modified_count, "created_dayplan": False, "item": item, "totalCost": updated.get("totalCost")}
    
            # DayPlan not found — create one with the item
            dayplan = {"date": date, "timeline": [item]}
            res2 = await database["trips"].update_one(
                {"_id": ObjectId(trip_id)},
                {"$push": {"itinerary.dayPlans": dayplan}}
            )
            modified2 = getattr(res2, "modified_count", 0)
            if modified2 > 0:
                try:
                    inc_val = float(item.get("cost", 0))
                except Exception:
                    inc_val = 0.0
                if inc_val != 0.0:
                    await database["trips"].update_one({"_id": ObjectId(trip_id)}, {"$inc": {"totalCost": inc_val}})
                updated = await database["trips"].find_one({"_id": ObjectId(trip_id)}, {"totalCost": 1})
                return {"modified_count": modified2, "created_dayplan": True, "item": item, "totalCost": updated.get("totalCost")}
    
            return {"modified_count": 0, "created_dayplan": False}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    async def remove_itinerary_item(trip_id: str, date: str, itemID: int) -> Dict[str, Any]:
        """
        Remove a specific itinerary item from a given day in a trip.
        """
        try:
            # First, fetch the trip's dayPlans to find the item and its cost
            trip = await database["trips"].find_one({"_id": ObjectId(trip_id)}, {"itinerary.dayPlans": 1})
            if not trip:
                return {"modified_count": 0, "error": "Trip not found"}

            dayplans = trip.get("itinerary", {}).get("dayPlans", [])
            day = next((d for d in dayplans if d.get("date") == date), None)
            if not day:
                return {"modified_count": 0, "error": "Day plan not found"}

            item = next((it for it in day.get("timeline", []) if it.get("itemID") == itemID), None)
            if not item:
                return {"modified_count": 0, "error": "Item not found"}

            # determine numeric cost to subtract from totalCost
            try:
                cost_to_subtract = float(item.get("cost", 0))
            except Exception:
                cost_to_subtract = 0.0

            # Remove the item
            result = await database["trips"].update_one(
                {"_id": ObjectId(trip_id), "itinerary.dayPlans.date": date},
                {"$pull": {"itinerary.dayPlans.$.timeline": {"itemID": itemID}}}
            )

            modified = getattr(result, "modified_count", 0)
            if modified > 0 and cost_to_subtract != 0.0:
                # decrement totalCost by the removed item's cost
                await database["trips"].update_one({"_id": ObjectId(trip_id)}, {"$inc": {"totalCost": -cost_to_subtract}})
                updated = await database["trips"].find_one({"_id": ObjectId(trip_id)}, {"totalCost": 1})
                return {"modified_count": modified, "totalCost": updated.get("totalCost")}

            return {"modified_count": modified}

        except Exception as e:
            return {"modified_count": 0, "error": str(e)}

    # @staticmethod
    # async def add_itinerary_item(trip_id: str, date: str, item: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Add an ItineraryItem to an existing DayPlan with the given date.
    #     If the day plan does not exist, create it with the item as the first timeline entry.
    #     """
    #     # Try to push onto existing dayPlan.timeline using positional $ operator
    #     res = await database["trips"].update_one(
    #         {"_id": ObjectId(trip_id), "itinerary.dayPlans.date": date},
    #         {"$push": {"itinerary.dayPlans.$.timeline": item}}
    #     )
    #     if getattr(res, "modified_count", 0) > 0:
    #         return {"modified_count": res.modified_count, "created_dayplan": False, "item": item}

    #     # DayPlan not found — create one
    #     dayplan = {"date": date, "timeline": [item]}
    #     res2 = await database["trips"].update_one(
    #         {"_id": ObjectId(trip_id)},
    #         {"$push": {"itinerary.dayPlans": dayplan}}
    #     )
    #     return {"modified_count": getattr(res2, "modified_count", 0), "created_dayplan": True, "item": item}

    @staticmethod
    async def remove_dayplan(trip_id: str, date: str) -> Dict[str, Any]:
        """
        Remove a DayPlan from itinerary.dayPlans identified by its date.
        Decrements totalCost by sum of costs in that dayPlan.
        """
        try:
            # fetch the dayPlan to compute sum of costs
            trip = await database["trips"].find_one({"_id": ObjectId(trip_id)}, {"itinerary.dayPlans": 1})
            if not trip:
                return {"modified_count": 0}
            dayplans = trip.get("itinerary", {}).get("dayPlans", [])
            target = next((dp for dp in dayplans if dp.get("date") == date), None)
            if not target:
                return {"modified_count": 0}
            sum_cost = 0.0
            for it in target.get("timeline", []):
                try:
                    sum_cost += float(it.get("cost", 0))
                except Exception:
                    pass

            # pull the dayplan
            res = await database["trips"].update_one(
                {"_id": ObjectId(trip_id)},
                {"$pull": {"itinerary.dayPlans": {"date": date}}}
            )
            modified = getattr(res, "modified_count", 0)
            if modified > 0 and sum_cost != 0:
                await database["trips"].update_one({"_id": ObjectId(trip_id)}, {"$inc": {"totalCost": -sum_cost}})
                updated = await database["trips"].find_one({"_id": ObjectId(trip_id)}, {"totalCost": 1})
                return {"modified_count": modified, "totalCost": updated.get("totalCost")}
            return {"modified_count": modified}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def update_itinerary_item(trip_id: str, date: str, itemID: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update fields of an itinerary item. Uses arrayFilters to pinpoint the item.
        If 'cost' is being changed, adjust trip.totalCost by the delta.
        """
        if not updates:
            return {"modified_count": 0}

        # If cost is present in updates, find existing cost to compute delta
        old_cost = None
        if "cost" in updates:
            try:
                trip = await database["trips"].find_one({"_id": ObjectId(trip_id)}, {"itinerary.dayPlans": 1})
                if not trip:
                    return {"modified_count": 0}
                dayplans = trip.get("itinerary", {}).get("dayPlans", [])
                day = next((d for d in dayplans if d.get("date") == date), None)
                if not day:
                    return {"modified_count": 0}
                item = next((it for it in day.get("timeline", []) if it.get("itemID") == itemID), None)
                if not item:
                    return {"modified_count": 0}
                try:
                    old_cost = float(item.get("cost", 0))
                except Exception:
                    old_cost = 0.0
            except Exception:
                return {"modified_count": 0}

        set_ops = {}
        for k, v in updates.items():
            set_ops[f"itinerary.dayPlans.$[d].timeline.$[i].{k}"] = v

        try:
            res = await database["trips"].update_one(
                {"_id": ObjectId(trip_id)},
                {"$set": set_ops},
                array_filters=[{"d.date": date}, {"i.itemID": itemID}]
            )
            modified = getattr(res, "modified_count", 0)
            if modified > 0 and old_cost is not None:
                # compute delta
                try:
                    new_cost = float(updates.get("cost", old_cost))
                except Exception:
                    new_cost = old_cost
                delta = new_cost - old_cost
                if delta != 0:
                    await database["trips"].update_one({"_id": ObjectId(trip_id)}, {"$inc": {"totalCost": delta}})
                updated = await database["trips"].find_one({"_id": ObjectId(trip_id)}, {"totalCost": 1})
                return {"modified_count": modified, "totalCost": updated.get("totalCost")}
            return {"modified_count": modified}
        except Exception as e:
            return {"error": str(e)}
