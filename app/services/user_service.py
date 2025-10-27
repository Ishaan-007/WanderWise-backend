from fastapi import HTTPException
from app.database import database
from bson import ObjectId
from datetime import datetime

class UserService:
    @staticmethod
    async def register_user_service(user_data: dict):
        # Check if email already exists
        existing_email = await database["users"].find_one({"email": user_data["email"]})
        if existing_email:
            return {"error": "Email already registered"}
        
        # Check if userName already exists
        existing_username = await database["users"].find_one({"userName": user_data["userName"]})
        if existing_username:
            return {"error": "Username already taken"}
        
        # Initialize follower and following counts
        user_data["followerCount"] = 0
        user_data["followingCount"] = 0
        result = await database["users"].insert_one(user_data)
        return {"message": "Registration successful", "inserted_id": result.inserted_id}

    @staticmethod
    async def get_user_by_email(email: str):
        """Fetch user document by email"""
        user_doc = await database["users"].find_one({"email": email})
        return user_doc

    @staticmethod
    async def get_user_by_id(user_id: str):
        """Fetch user document by ID"""
        try:
            user_doc = await database["users"].find_one({"_id": ObjectId(user_id)})
            if user_doc:
                user_doc["userID"] = str(user_doc["_id"])
                user_doc.pop("_id", None)
            return user_doc
        except Exception:
            return None

    @staticmethod
    async def update_user(email: str, data: dict):
        return await database["users"].update_one({"email": email}, {"$set": data})

    @staticmethod
    async def update_user_by_id(user_id: str, data: dict):
        """Update user document by ID"""
        try:
            # Don't allow modifying follower/following counts via this method
            data.pop("followerCount", None)
            data.pop("followingCount", None)
            result = await database["users"].update_one(
                {"_id": ObjectId(user_id)}, 
                {"$set": data}
            )
            return {"modified_count": getattr(result, "modified_count", 0)}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def follow_user(follower_id: str, target_id: str):
        """User follower_id follows user target_id"""
        try:
            # Check if both users exist
            follower = await database["users"].find_one({"_id": ObjectId(follower_id)})
            target = await database["users"].find_one({"_id": ObjectId(target_id)})
            if not follower or not target:
                return {"error": "One or both users not found"}

            # Check if already following
            following = await database["follows"].find_one({
                "followerID": follower_id,
                "targetID": target_id
            })
            if following:
                return {"error": "Already following this user"}

            # Create follow record and increment counts
            async with await database.client.start_session() as session:
                async with session.start_transaction():
                    # Create follow record
                    await database["follows"].insert_one({
                        "followerID": follower_id,
                        "targetID": target_id,
                        "followedAt": datetime.utcnow()
                    }, session=session)

                    # Increment follower's following count
                    await database["users"].update_one(
                        {"_id": ObjectId(follower_id)},
                        {"$inc": {"followingCount": 1}},
                        session=session
                    )

                    # Increment target's follower count
                    await database["users"].update_one(
                        {"_id": ObjectId(target_id)},
                        {"$inc": {"followerCount": 1}},
                        session=session
                    )

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
        
    @staticmethod
    async def unfollow_user(follower_id: str, target_id: str):
        """User follower_id unfollows user target_id

        Removes the follow record (if present) and decrements the
        follower/following counters inside a transaction to keep counts consistent.
        """
        try:
            # Check if both users exist
            follower = await database["users"].find_one({"_id": ObjectId(follower_id)})
            target = await database["users"].find_one({"_id": ObjectId(target_id)})
            if not follower or not target:
                return {"error": "One or both users not found"}

            # Check if follow record exists
            following = await database["follows"].find_one({
                "followerID": follower_id,
                "targetID": target_id
            })
            if not following:
                return {"error": "Follow relationship not found"}

            # Delete follow record and decrement counts atomically
            async with await database.client.start_session() as session:
                async with session.start_transaction():
                    # Remove follow record
                    del_res = await database["follows"].delete_one(
                        {"_id": following.get("_id")}, session=session
                    )

                    # Decrement follower's following count (min 0)
                    await database["users"].update_one(
                        {"_id": ObjectId(follower_id)},
                        {"$inc": {"followingCount": -1}},
                        session=session
                    )

                    # Decrement target's follower count (min 0)
                    await database["users"].update_one(
                        {"_id": ObjectId(target_id)},
                        {"$inc": {"followerCount": -1}},
                        session=session
                    )

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}


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