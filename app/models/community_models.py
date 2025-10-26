from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.database import database


class Post(BaseModel):
    postID: int
    title: str
    content: str
    likes: int = 0
    shares: int = 0
    views: int = 0
    contentType: str = "text"  # e.g., text, image, video
    authorID: Optional[str] = None  # registered user id (string)
    created_at: Optional[str] = None  # ISO timestamp
    # simple comments list (each comment is a dict with authorID, text, created_at)
    comments: List[Dict[str, Any]] = []

    @classmethod
    async def create(cls, community_id: str, author_id: str, title: str, content: str, content_type: str = "text") -> Dict[str, Any]:
        """Create a Post inside the specified community. Returns the created post or error."""
        try:
            # Fetch community
            comm = await database["communities"].find_one({"_id": ObjectId(community_id)})
            if not comm:
                return {"error": "Community not found"}

            # Determine next postID
            posts = comm.get("posts", [])
            next_id = max((p.get("postID", 0) for p in posts), default=0) + 1

            post = {
                "postID": next_id,
                "title": title,
                "content": content,
                "likes": 0,
                "shares": 0,
                "views": 0,
                "contentType": content_type,
                "authorID": author_id,
                "created_at": datetime.utcnow().isoformat(),
                "comments": []
            }

            res = await database["communities"].update_one(
                {"_id": ObjectId(community_id)},
                {"$push": {"posts": post}}
            )
            if getattr(res, "modified_count", 0) > 0:
                return {"created_post": post}
            return {"error": "Could not create post"}
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    async def add_comment(cls, community_id: str, post_id: int, author_id: str, text: str) -> Dict[str, Any]:
        """Add a comment to a post."""
        try:
            comment = {"authorID": author_id, "text": text, "created_at": datetime.utcnow().isoformat()}
            res = await database["communities"].update_one(
                {"_id": ObjectId(community_id), "posts.postID": post_id},
                {"$push": {"posts.$.comments": comment}}
            )
            if getattr(res, "modified_count", 0) > 0:
                return {"added": True}
            return {"error": "Post not found"}
        except Exception as e:
            return {"error": str(e)}
        
    @classmethod    
    async def add_like(cls, community_id: str, post_id: int) -> Dict[str, Any]:
        """Increment the like count of a post."""
        try:
            res = await database["communities"].find_one_and_update(
                {"_id": ObjectId(community_id), "posts.postID": post_id},
                {"$inc": {"posts.$.likes": 1}},
                return_document=True
            )

            if not res:
                return {"error": "Post not found"}

            # Get updated likes count for that post
            updated_post = next((p for p in res.get("posts", []) if p["postID"] == post_id), None)
            return {"likes": updated_post.get("likes")} if updated_post else {"error": "Post not found after update"}
        except Exception as e:
            return {"error": str(e)}


class Community(BaseModel):
    communityID: Optional[str] = None
    name: str
    description: Optional[str] = None
    posts: List[Post] = []

    @classmethod
    async def create_community(cls, name: str, creator_id: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new community document. Store creator's user id if provided."""
        try:
            doc = {"name": name, "description": description, "posts": [], "creatorID": creator_id}
            res = await database["communities"].insert_one(doc)
            return {"inserted_id": str(res.inserted_id)}
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    async def publish_post(cls, community_id: str, author_id: str, title: str, content: str, content_type: str = "text") -> Dict[str, Any]:
        """Wrapper to create a Post in the community."""
        return await Post.create(community_id, author_id, title, content, content_type)

    @classmethod
    async def view_posts(cls, community_id: str) -> Dict[str, Any]:
        """Return posts for a community (visible to everyone including guest users)."""
        try:
            comm = await database["communities"].find_one({"_id": ObjectId(community_id)})
            if not comm:
                return {"error": "Community not found"}
            
            # Get posts with author names
            posts = comm.get("posts", [])
            enhanced_posts = []
            
            for post in posts:
                post_copy = post.copy()
                # Get author name if authorID exists
                if post.get("authorID"):
                    author = await database["users"].find_one({"_id": ObjectId(post["authorID"])})
                    if author:
                        post_copy["authorName"] = author.get("userName", "Unknown User")
                    else:
                        post_copy["authorName"] = "Unknown User"
                else:
                    post_copy["authorName"] = "Guest User"
                
                enhanced_posts.append(post_copy)
            
            return {"posts": enhanced_posts}
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    async def get_all_posts(cls) -> List[Dict[str, Any]]:
        """Return all posts across communities (for a global feed)."""
        posts = []
        try:
            cursor = database["communities"].find({}, {"posts": 1, "name": 1})
            async for comm in cursor:
                for p in comm.get("posts", []):
                    p_copy = p.copy()
                    p_copy["communityName"] = comm.get("name")
                    
                    # Get author name if authorID exists
                    if p.get("authorID"):
                        author = await database["users"].find_one({"_id": ObjectId(p["authorID"])})
                        if author:
                            p_copy["authorName"] = author.get("userName", "Unknown User")
                        else:
                            p_copy["authorName"] = "Unknown User"
                    else:
                        p_copy["authorName"] = "Guest User"
                    
                    posts.append(p_copy)
        except Exception:
            pass
        return posts
