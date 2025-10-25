from pydantic import BaseModel, EmailStr
from typing import Optional
from hashlib import sha256
from app.models.trip_models import TripDashboard
#from app.services.trip_service import TripService
from app.services.user_service import UserService

# ---------- Base User ----------
class User(BaseModel):
    userID: str
    userName: Optional[str] = None

    @classmethod
    async def register(
        cls,
        email: EmailStr,
        password: str,
        profilePictureURL: Optional[str] = None,
        location: Optional[str] = None,
        preference: Optional[str] = None
    ):
        user_data = {
            "userRole": "Traveller",
            "email": email,
            "passwordHash": sha256(password.encode()).hexdigest(),
            "profilePictureURL": profilePictureURL,
            "location": location,
            "preference": preference,
            "followerCount": 0,
            "followingCount": 0
        }

        inserted = await UserService.register_user_service(user_data)
        if inserted.get("message") == "Registration successful":
            user_data["userID"] = str(inserted.get("inserted_id"))  # Add this
            return {"success": True, "user": RegisteredUser(**user_data).model_dump()}
        else:
            return {"success": False, "error": inserted.get("error")}


    @classmethod   
    async def login(
        cls,
        email: EmailStr,
        password: str
    ):
        user_doc = await UserService.get_user_by_email(email)
        if not user_doc:
            return {"success": False, "error": "Email not registered"}

        hashed_password = sha256(password.encode()).hexdigest()
        if hashed_password != user_doc.get("passwordHash"):
            return {"success": False, "error": "Incorrect password"}

        user_doc["userID"] = str(user_doc["_id"])
        return {"success": True, "user": RegisteredUser(**user_doc).model_dump()}
        
# ---------- Guest ----------
class GuestUser(User):
    
    async def openCommunity(self):
        pass


# ---------- Registered User ----------
class RegisteredUser(User):
    email: EmailStr
    passwordHash: str
    profilePictureURL: Optional[str] = None
    location: Optional[str] = None
    preference: Optional[str] = None
    followerCount: int = 0
    followingCount: int = 0

    async def updateProfile(self):
        pass

    async def changePassword(self):
        pass

    @staticmethod
    async def openDashboard(userID: str):
        """
        Create a TripDashboard instance for this user, load trips from DB and return the dashboard.
        Route code expects a model (so caller can call .model_dump()).
        """
        #dashboard = TripDashboard(userID=userID)
        dashboard = await TripDashboard.display_trips(userID)
        return dashboard


    async def openExploration(self):
        pass

    async def openSearchEngine(self):
        pass

    async def openCommunity(self):
        pass

    async def displayProfileDetails(self):
        pass

    async def follow(self):
        pass

    async def unfollow(self):
        pass


# ---------- Admin ----------
class Admin(User):
    async def moderateContent(self, post) -> bool:
        pass


# ---------- Data Analyst ----------
class DataAnalyst(User):
    async def checkUserTraffic(self):
        pass

    async def getDataAnalytics(self):
        pass
