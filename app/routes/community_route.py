from fastapi import APIRouter, Form, HTTPException
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.community_models import Community, Post

router = APIRouter()


@router.post("/community/create")
async def create_community(
    userID: str = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None)
):
    """Create a community. userID (creator) must be provided."""
    from app.models.community_models import Community
    result = await Community.create_community(name=name, creator_id=userID, description=description)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "community_id": result.get("inserted_id")}


@router.post("/community/{communityID}/post/create")
async def publish_post(
    communityID: str,
    userID: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    contentType: Optional[str] = Form("text")
):
    """Publish a post in a community. Only registered users should have userID."""
    from app.models.community_models import Community
    result = await Community.publish_post(communityID, userID, title, content, contentType)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "post": result.get("created_post")}


@router.get("/community/{communityID}/posts")
async def view_posts(communityID: str):
    """View posts in a community (visible to guests)."""
    from app.models.community_models import Community
    result = await Community.view_posts(communityID)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"success": True, "posts": result.get("posts")}


@router.post("/community/{communityID}/post/{postID}/comment")
async def add_comment(
    communityID: str,
    postID: int,
    userID: str = Form(...),
    text: str = Form(...)
):
    """Add a comment to a post. userID required (registered user)."""
    from app.models.community_models import Post
    result = await Post.add_comment(communityID, postID, userID, text)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True}

@router.get("/community/{communityID}/posts/trips")
async def view_trip_posts(communityID: str):
    """View posts that contain trip data in a community."""
    try:
        from app.database import database
        from bson import ObjectId
        
        # Get posts that have tripData field
        community = await database["communities"].find_one(
            {"_id": ObjectId(communityID)},
            {"posts": 1, "name": 1}
        )
        
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Filter posts that contain trip data and add author names
        trip_posts = []
        for post in community.get("posts", []):
            if "tripData" in post:
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
                
                trip_posts.append(post_copy)
        
        return {
            "success": True, 
            "community_name": community.get("name"),
            "trip_posts": trip_posts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/community/{communityID}/post/{postID}/like")
async def like_post(communityID: str, postID: int):
    """Like a post. Increments the like count."""
    from app.models.community_models import Post
    result = await Post.add_like(communityID, postID)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "likes": result.get("likes")}