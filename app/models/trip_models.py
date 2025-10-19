from pydantic import BaseModel
from typing import List, Optional
from datetime import date

# --- Child models used in composition ---
class ItineraryItem(BaseModel):
    itemID: int
    startTime: str
    endTime: str
    cost: float
    notes: Optional[str] = None

    async def editItem(self):
        pass

    async def deleteItem(self):
        pass


class DayPlan(BaseModel):
    date: date
    timeline: List[ItineraryItem] = []

    async def addItineraryItem(self, startTime, endTime, cost, notes):
        item = ItineraryItem(
            itemID=len(self.timeline) + 1,
            startTime=startTime,
            endTime=endTime,
            cost=cost,
            notes=notes,
        )
        self.timeline.append(item)

    async def displayTimeline(self):
        pass

    async def removeItem(self):
        pass


class Itinerary(BaseModel):
    dayPlans: List[DayPlan] = []

    async def addDayPlan(self, new_date):
        self.dayPlans.append(DayPlan(date=new_date))

    async def viewItinerary(self):
        pass

    async def saveItinerary(self):
        pass


# --- Composition: Trip *-- Itinerary ---
class Trip(BaseModel):
    tripID: int
    name: str
    destination: str
    startDate: date
    endDate: date
    budget: float
    totalCost: float = 0.0
    itinerary: Itinerary = Itinerary()

    async def displayTripSummary(self):
        pass

    async def calculateTotalCost(self):
        self.totalCost = sum(
            item.cost
            for plan in self.itinerary.dayPlans
            for item in plan.timeline
        )

    async def createTrip(self):
        pass

    async def downloadTrip(self):
        pass
