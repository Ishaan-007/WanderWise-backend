from fastapi import APIRouter, HTTPException
from app.models.user_models import RegisteredUser
from app.database import database

router = APIRouter()

@router.post("/register")
async def register_user(user: RegisteredUser):
    existing = await database["users"].find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    await database["users"].insert_one(user.dict())
    return {"message": "User registered successfully"}


@router.get("/users")
async def get_users():
    users = await database["users"].find().to_list(100)
    return users
