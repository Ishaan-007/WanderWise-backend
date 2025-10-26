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

    @staticmethod
    async def get_all_communities():
        """Get all communities with their basic information (excluding posts for performance)"""
        try:
            communities = []
            cursor = database["communities"].find({}, {
                "_id": 1,
                "name": 1,
                "description": 1,
                "creatorID": 1,
                "posts": {"$slice": 0}  # Exclude posts for performance
            })
            async for community in cursor:
                community["communityID"] = str(community["_id"])
                del community["_id"]  # Remove MongoDB _id
                communities.append(community)
            return {"success": True, "communities": communities}
        except Exception as e:
            return {"success": False, "error": str(e)}