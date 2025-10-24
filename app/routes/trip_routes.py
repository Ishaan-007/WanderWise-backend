# app/routes/trip_routes.py
from typing import Optional
from fastapi import APIRouter, Form, HTTPException
from app.models.trip_models import Trip
from app.services.trip_service import TripService

router = APIRouter()


def serialize_trip(trip_doc: dict) -> dict:
    """Ensure response doesn't contain ObjectId and has tripID string"""
    trip_doc = dict(trip_doc)  # copy
    if "_id" in trip_doc:
        trip_doc["tripID"] = str(trip_doc["_id"])
        trip_doc.pop("_id", None)
    return trip_doc


@router.post("/trip/create")
async def create_trip(
    userID: str = Form(...),
    name: str = Form(...),
    destination: str = Form(...),
    startDate: str = Form(...),  # expect "YYYY-MM-DD"
    endDate: str = Form(...),
    budget: float = Form(...)
):
    trip = Trip(
        name=name,
        destination=destination,
        startDate=startDate,
        endDate=endDate,
        budget=budget
    )
    result = await trip.createTrip(userID)
    return result


@router.get("/trips/{userID}")
async def get_user_trips(userID: str):
    trips = await Trip.getTripsByUser(userID)  # model method (calls service internally)
    # return list of dicts
    return [t.dict() for t in trips]


@router.get("/trip/{tripID}")
async def get_trip(tripID: str, userID: str):
    # Use model->service path: TripService provides summary, model can wrap it
    summary = await TripService.get_trip_summary_from_db(userID, tripID)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    return summary


@router.put("/trip/update/{tripID}")
async def update_trip(
    tripID: str,
    name: Optional[str] = Form(None),
    destination: Optional[str] = Form(None),
    budget: Optional[float] = Form(None)
):
    update_data = {}
    if name is not "":
        update_data["name"] = name
    if destination is not "":
        update_data["destination"] = destination
    if budget is not None:
        update_data["budget"] = budget

    result = await TripService.update_trip(tripID, update_data)
    if getattr(result, "modified_count", 0):
        return {"success": True}
    return {"success": False, "error": "No changes made or trip not found"}


@router.delete("/trip/delete/{tripID}")
async def delete_trip(tripID: str):
    deleted_count = await TripService.delete_trip(tripID)
    if deleted_count:
        return {"success": True}
    return {"success": False, "error": "Trip not found"}
