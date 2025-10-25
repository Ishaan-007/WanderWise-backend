# app/routes/trip_routes.py
from typing import Optional
from fastapi import APIRouter, Form, HTTPException
from app.models.trip_models_2 import DayPlan, Itinerary, ItineraryItem, Trip, TripDashboard
from app.services.trip_service_2 import TripService

router = APIRouter()


@router.post("/trip/create")
async def create_trip(
    userID: str = Form(...),
    name: str = Form(...),
    destination: str = Form(...),
    startDate: str = Form(...),
    endDate: str = Form(...),
    budget: float = Form(...)
):
    dashboard = TripDashboard()
    # await dashboard.display_trips()  # load existing trips for the user (kept commented as before)
    result = await dashboard.createTrip(userID, name, destination, startDate, endDate, budget)
    return result


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
    dashboard = TripDashboard(userID=userID)
    await dashboard.loadTripsFromDB()
    return await dashboard.deleteTrip(tripID)


# -----------------------
# NEW ITINERARY ENDPOINTS
# Router → Model → Service flow (routes call Trip model methods)
# -----------------------

@router.get("/trip/{tripID}/itinerary")
async def get_itinerary(tripID: str):
    itinerary = await Trip.getItineraryDetails(tripID)
    if itinerary is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"success": True, "itinerary": itinerary}


@router.post("/trip/{tripID}/itinerary/dayplan/add")
async def add_dayplan(
    tripID: str,
    date: str = Form(...),  # "YYYY-MM-DD"
):
    result = await Itinerary.addDayPlan(tripID, date)
    if result.get("modified_count", 0) > 0:
        return {"success": True}
    return {"success": False, "error": "Could not add day plan"}

@router.post("/trip/{tripID}/itinerary/dayplan/timeline")
async def showTimeline(
    tripID: str,
    date: str = Form(...),  # "YYYY-MM-DD"
):
    result = await DayPlan.displayTimeline(tripID, date)
    return result
    if result.get("modified_count", 0) > 0:
        return {"success": True}
    return {"success": False, "error": "Could not add day plan"}

@router.post("/trip/{tripID}/itinerary/dayplan/delete")
async def delete_dayplan(
    tripID: str,
    date: str = Form(...),  # "YYYY-MM-DD"
):
    """
    Delete an entire DayPlan (by date) from a trip's itinerary.
    Calls Itinerary.remove_dayplan(model) -> TripService.remove_dayplan(service).
    """
    result = await Itinerary.deleteDayPlan(tripID, date)
    if result.get("modified_count", 0) > 0:
        return {"success": True}
    return {"success": False, "error": result.get("error", "DayPlan not found or nothing deleted")}



@router.post("/trip/{tripID}/itinerary/item/add")
async def add_itinerary_item(
    tripID: str,
    date: str = Form(...),
    startTime: str = Form(...),
    endTime: str = Form(...),
    cost: float = Form(...),
    notes: Optional[str] = Form(None),
):
    result = await DayPlan.addItineraryItem(tripID, date, startTime, endTime, cost, notes)
    if result.get("modified_count", 0) > 0:
        return {"success": True, "created_dayplan": result.get("created_dayplan", False), "item": result.get("item")}
    return {"success": False, "error": "Could not add itinerary item"}


@router.put("/trip/{tripID}/itinerary/item/update")
async def update_itinerary_item(
    tripID: str,
    date: str = Form(...),
    itemID: int = Form(...),
    startTime: Optional[str] = Form(None),
    endTime: Optional[str] = Form(None),
    cost: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
):
    result = await ItineraryItem.editItem(tripID, date, itemID, {
        k: v for k, v in {
            "startTime": startTime,
            "endTime": endTime,
            "cost": cost,
            "notes": notes
        }.items() if v is not None and v != "" and v != "string"
    })
    if result.get("modified_count", 0) > 0:
        return {"success": True}
    return {"success": False, "error": result.get("error", "No changes made or item not found")}


@router.delete("/trip/{tripID}/itinerary/item/delete")
async def delete_itinerary_item(
    tripID: str,
    date: str = Form(...),
    itemID: int = Form(...)
):
    result = await DayPlan.removeItem(tripID, date, itemID)
    if result.get("modified_count", 0) > 0:
        return {"success": True}
    return {"success": False, "error": result.get("error", "Item not found")}
