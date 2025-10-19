from pydantic import BaseModel, EmailStr
from typing import Optional

# ---------- Base User ----------
class User(BaseModel):
    userID: int
    userName: str

    async def login(self):
        pass

    async def register(self):
        pass


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

    async def openDashboard(self):
        pass

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
