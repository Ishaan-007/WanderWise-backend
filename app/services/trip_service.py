# app/services/trip_service.py
from app.database import database
from bson import ObjectId
from typing import List, Dict, Any

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
