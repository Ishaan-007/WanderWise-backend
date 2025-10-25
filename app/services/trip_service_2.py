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
    async def add_dayplan(trip_id: str, dayplan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a DayPlan object to itinerary.dayPlans.
        dayplan: {"date": "...", "timeline": [...]}
        """
        res = await database["trips"].update_one(
            {"_id": ObjectId(trip_id)},
            {"$push": {"itinerary.dayPlans": dayplan}}
        )
        return {"modified_count": getattr(res, "modified_count", 0)}

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
        """
        # Try to push onto existing dayPlan.timeline using positional $ operator
        res = await database["trips"].update_one(
            {"_id": ObjectId(trip_id), "itinerary.dayPlans.date": date},
            {"$push": {"itinerary.dayPlans.$.timeline": item}}
        )
        if getattr(res, "modified_count", 0) > 0:
            return {"modified_count": res.modified_count, "created_dayplan": False, "item": item}

        # DayPlan not found — create one
        dayplan = {"date": date, "timeline": [item]}
        res2 = await database["trips"].update_one(
            {"_id": ObjectId(trip_id)},
            {"$push": {"itinerary.dayPlans": dayplan}}
        )
        return {"modified_count": getattr(res2, "modified_count", 0), "created_dayplan": True, "item": item}

    @staticmethod
    async def remove_itinerary_item(trip_id: str, date: str, itemID: int) -> Dict[str, Any]:
        """
        Remove an itinerary item identified by itemID from the DayPlan with given date.
        Uses arrayFilters to target the correct dayPlan.
        """
        try:
            res = await database["trips"].update_one(
                {"_id": ObjectId(trip_id)},
                {"$pull": {"itinerary.dayPlans.$[d].timeline": {"itemID": itemID}}},
                array_filters=[{"d.date": date}]
            )
            return {"modified_count": getattr(res, "modified_count", 0)}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def update_itinerary_item(trip_id: str, date: str, itemID: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update fields of an itinerary item. Uses arrayFilters to pinpoint the item.
        'updates' can contain keys: startTime, endTime, cost, notes
        """
        if not updates:
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
            return {"modified_count": getattr(res, "modified_count", 0)}
        except Exception as e:
            return {"error": str(e)}
