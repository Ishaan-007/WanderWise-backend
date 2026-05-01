# app/routes/trip_routes.py
from typing import Optional
from fastapi import APIRouter, Form, HTTPException

router = APIRouter()


# def serialize_trip(trip_doc: dict) -> dict:
#     """Ensure response doesn't contain ObjectId and has tripID string"""
#     trip_doc = dict(trip_doc)  # copy
#     if "_id" in trip_doc:
#         trip_doc["tripID"] = str(trip_doc["_id"])
#         trip_doc.pop("_id", None)
#     return trip_doc

@router.post("/trip/create")
async def create_trip(
    userID: str = Form(...),
    name: str = Form(...),
    destination: str = Form(...),
    startDate: str = Form(...),
    endDate: str = Form(...),
    budget: float = Form(...)
):
    from app.models.trip_models import TripDashboard
    dashboard = TripDashboard()
    # await dashboard.display_trips()  # load existing trips for the user
    result = await dashboard.createTrip(userID, name, destination, startDate, endDate, budget)
    return result

# @router.get("/trips/{userID}")
# async def get_user_trips(userID: str):
#     dashboard = TripDashboard(userID=userID)
#     await dashboard.loadTripsFromDB()
#     return [trip.dict() for trip in dashboard.trips]


@router.get("/trip/{tripID}")
async def get_trip(tripID: str, userID: str):
    from app.services.trip_service import TripService
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
    from app.services.trip_service import TripService
    update_data = {}

    if name not in (None, "", "string"):
        update_data["name"] = name

    if destination not in (None, "", "string"):
        update_data["destination"] = destination

    if budget is not None and budget != 0:
        update_data["budget"] = budget

    if not update_data:
        return {"success": False, "error": "No valid fields provided for update"}

    result = await TripService.update_trip(tripID, update_data)
    if getattr(result, "modified_count", 0):
        return {"success": True, "updated_fields": update_data}

    return {"success": False, "error": "No changes made or trip not found"}



@router.delete("/trip/delete/{tripID}")
async def delete_trip(userID: str, tripID: str):
    from app.models.trip_models import TripDashboard
    dashboard = TripDashboard(userID=userID)
    #await dashboard.loadTripsFromDB()
    return await dashboard.deleteTrip(tripID)