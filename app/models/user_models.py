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
        userName: str,
        profilePictureURL: Optional[str] = None,
        location: Optional[str] = None,
        preference: Optional[str] = None
    ):
        user_data = {
            "userRole": "Traveller",
            "email": email,
            "userName": userName,
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

        # Convert _id to userID and ensure userName exists
        user_doc["userID"] = str(user_doc["_id"])
        if "userName" not in user_doc:
            user_doc["userName"] = None  # Use None as default if userName is missing
        return {"success": True, "user": RegisteredUser(**user_doc).model_dump()}
        
# ---------- Guest ----------
class GuestUser(User):
    
    async def openCommunity(self):
        """Return all community information for guest users"""
        from app.services.user_service import UserService
        return await UserService.get_all_communities()


# ---------- Registered User ----------
class RegisteredUser(User):
    email: EmailStr
    userName: Optional[str] = None  # Making userName optional to match parent class
    passwordHash: str
    profilePictureURL: Optional[str] = None
    location: Optional[str] = None
    preference: Optional[str] = None
    followerCount: int = 0
    followingCount: int = 0

    @classmethod
    async def displayProfile(cls, userID: str):
        """Get user profile details from service."""
        user = await UserService.get_user_by_id(userID)
        if not user:
            return {"success": False, "error": "User not found"}
        return {
            "success": True,
            "profile": {
                "userID": user.get("userID"),
                "userName": user.get("userName"),
                "email": user.get("email"),
                "profilePictureURL": user.get("profilePictureURL"),
                "location": user.get("location"),
                "preference": user.get("preference"),
                "followerCount": user.get("followerCount", 0),
                "followingCount": user.get("followingCount", 0)
            }
        }

    @classmethod
    async def updateProfile(cls, userID: str, update_data: dict):
        """Update user profile using service."""
        result = await UserService.update_user_by_id(userID, update_data)
        if "error" in result:
            return {"success": False, "error": result["error"]}
        if result.get("modified_count", 0) > 0:
            return {"success": True}
        return {"success": False, "error": "No changes made"}

    @classmethod
    async def followUser(cls, userID: str, targetUserID: str):
        """Follow another user using service."""
        if userID == targetUserID:
            return {"success": False, "error": "Cannot follow yourself"}
        result = await UserService.follow_user(userID, targetUserID)
        if "error" in result:
            return {"success": False, "error": result["error"]}
        return {"success": True}

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
        """Return all community information for registered users"""
        from app.services.user_service import UserService
        return await UserService.get_all_communities()

    async def displayProfileDetails(self, userID: str):
        """Get user profile details from service."""
        user = await UserService.get_user_by_id(userID)
        if not user:
            return {"success": False, "error": "User not found"}
        return {
            "success": True,
            "profile": {
                "userID": user.get("userID"),
                "userName": user.get("userName"),
                "email": user.get("email"),
                "profilePictureURL": user.get("profilePictureURL"),
                "location": user.get("location"),
                "preference": user.get("preference"),
                "followerCount": user.get("followerCount", 0),
                "followingCount": user.get("followingCount", 0)
            }
        }

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
