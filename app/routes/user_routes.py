from typing import Optional
from fastapi import APIRouter, Form, HTTPException
from app.models.user_models import User
from app.database import database
from bson import ObjectId

router = APIRouter()

@router.post("/register")
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    profilePictureURL: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    preference: Optional[str] = Form(None)
):
    return await User.register(email, password, profilePictureURL, location, preference)

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
