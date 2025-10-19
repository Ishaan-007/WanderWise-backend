from app.database import database

class UserService:
    @staticmethod
    async def get_user_by_email(email: str):
        return await database["users"].find_one({"email": email})

    @staticmethod
    async def update_user(email: str, data: dict):
        return await database["users"].update_one({"email": email}, {"$set": data})
