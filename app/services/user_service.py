from fastapi import HTTPException
from app.database import database

class UserService:
    @staticmethod
    async def register_user_service(user_data: dict):
        existing = await database["users"].find_one({"email": user_data["email"]})
        if existing:
            return {"error": "Email already registered"}
        result = await database["users"].insert_one(user_data)
        return {"message": "Registration successful", "inserted_id": result.inserted_id}


    @staticmethod
    async def get_user_by_email(email: str):
        """Fetch user document by email"""
        user_doc = await database["users"].find_one({"email": email})
        return user_doc


    @staticmethod
    async def update_user(email: str, data: dict):
        return await database["users"].update_one({"email": email}, {"$set": data})
