from typing import Optional
from fastapi import APIRouter, Form, HTTPException
from app.models.user_models import User, RegisteredUser
from app.database import database
from bson import ObjectId

router = APIRouter()

@router.post("/register")
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    userName: str = Form(...),
    profilePictureURL: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    preference: Optional[str] = Form(None)
):
    return await User.register(email, password, userName, profilePictureURL, location, preference)

@router.post("/login")
async def login_user(
    email: str = Form(...),
    password: str = Form(...)
):
    result = await User.login(email, password)
    return result
    
def serialize_user(user_doc):
    """Convert MongoDB _id to string for JSON serialization."""
    user_doc["_id"] = str(user_doc["_id"])
    return user_doc

@router.get("/users")
async def get_users():
    users = await database["users"].find().to_list(100)
    serialized_users = [serialize_user(user) for user in users]
    return serialized_users

@router.get("/dashboard/{userID}")
async def open_dashboard(userID: str):
    #user = RegisteredUser(userID=userID)  # Normally injected via auth
    dashboard = await RegisteredUser.openDashboard(userID)
    return dashboard

@router.get("/communities")
async def get_communities():
    """Get all communities - accessible by both registered and guest users"""
    from app.models.user_models import GuestUser
    guest_user = GuestUser(userID="guest")
    return await guest_user.openCommunity()

@router.get("/user/profile/{userID}")
async def get_user_profile(userID: str):
    """Get a user's profile details."""
    result = await RegisteredUser.displayProfile(userID)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.put("/user/profile/{userID}/update")
async def update_user_profile(
    userID: str,
    userName: Optional[str] = Form(None),
    profilePictureURL: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    preference: Optional[str] = Form(None)
):
    """Update a user's profile details."""
    # Build update data from provided fields
    update_data = {}
    if userName not in (None, "", "string"):
        update_data["userName"] = userName
    if profilePictureURL not in (None, "", "string"):
        update_data["profilePictureURL"] = profilePictureURL
    if location not in (None, "", "string"):
        update_data["location"] = location
    if preference not in (None, "", "string"):
        update_data["preference"] = preference

    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    result = await RegisteredUser.updateProfile(userID, update_data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/user/{userID}/follow/{targetUserID}")
async def follow_user(userID: str, targetUserID: str):
    """Follow another user - requires both user IDs."""
    result = await RegisteredUser.follow(userID, targetUserID)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/user/{userID}/unfollow/{targetUserID}")
async def unfollow_user(userID: str, targetUserID: str):
    """Unfollow another user - requires both user IDs."""
    result = await RegisteredUser.unfollow(userID, targetUserID)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result