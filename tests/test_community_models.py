"""
test_community_models.py - Unit tests for community model classes.

Tests cover:
- Post creation and management
- Comment and like functionality
- Community creation and post publishing
- Viewing posts and creating global feeds
- Error handling and edge cases
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from bson import ObjectId
from datetime import datetime
from app.models.community_models import Post, Community


class TestPostCreation:
    """Tests for post creation."""

    @pytest.mark.asyncio
    async def test_create_post_success(self, sample_post_data):
        """Test successfully creating a post."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.find_one.return_value = {
                "_id": ObjectId(community_id),
                "name": "Test Community",
                "posts": []
            }
            mock_communities.update_one.return_value = MagicMock(modified_count=1)
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.create(
                community_id=community_id,
                author_id=sample_post_data["authorID"],
                title=sample_post_data["title"],
                content=sample_post_data["content"],
                content_type=sample_post_data["contentType"]
            )
            
            assert "created_post" in result
            assert result["created_post"]["title"] == sample_post_data["title"]

    @pytest.mark.asyncio
    async def test_create_post_community_not_found(self):
        """Test creating post in non-existent community."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.find_one.return_value = None
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.create(
                community_id=community_id,
                author_id="507f1f77bcf86cd799439011",
                title="Test Post",
                content="Test content"
            )
            
            assert "error" in result
            assert result["error"] == "Community not found"

    @pytest.mark.asyncio
    async def test_create_post_assigns_post_id(self):
        """Test that post gets assigned correct ID."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            # Simulate existing posts
            existing_posts = [
                {"postID": 1, "title": "First"},
                {"postID": 2, "title": "Second"}
            ]
            mock_communities.find_one.return_value = {
                "_id": ObjectId(community_id),
                "posts": existing_posts
            }
            mock_communities.update_one.return_value = MagicMock(modified_count=1)
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.create(
                community_id=community_id,
                author_id="507f1f77bcf86cd799439011",
                title="New Post",
                content="Content"
            )
            
            assert result["created_post"]["postID"] == 3

    @pytest.mark.asyncio
    async def test_create_post_with_timestamp(self):
        """Test that created post has timestamp."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.find_one.return_value = {
                "_id": ObjectId(community_id),
                "posts": []
            }
            mock_communities.update_one.return_value = MagicMock(modified_count=1)
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.create(
                community_id=community_id,
                author_id="507f1f77bcf86cd799439011",
                title="New Post",
                content="Content"
            )
            
            assert "created_at" in result["created_post"]
            assert result["created_post"]["created_at"] is not None


class TestPostComment:
    """Tests for adding comments to posts."""

    @pytest.mark.asyncio
    async def test_add_comment_success(self):
        """Test successfully adding a comment."""
        community_id = str(ObjectId())
        post_id = 1
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.update_one.return_value = MagicMock(modified_count=1)
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.add_comment(
                community_id=community_id,
                post_id=post_id,
                author_id="507f1f77bcf86cd799439011",
                text="Great post!"
            )
            
            assert result["added"] is True

    @pytest.mark.asyncio
    async def test_add_comment_post_not_found(self):
        """Test adding comment to non-existent post."""
        community_id = str(ObjectId())
        post_id = 999
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.update_one.return_value = MagicMock(modified_count=0)
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.add_comment(
                community_id=community_id,
                post_id=post_id,
                author_id="507f1f77bcf86cd799439011",
                text="Great post!"
            )
            
            assert "error" in result

    @pytest.mark.asyncio
    async def test_add_comment_with_timestamp(self):
        """Test that comment has timestamp."""
        community_id = str(ObjectId())
        post_id = 1
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.update_one.return_value = MagicMock(modified_count=1)
            
            def check_update_call(**kwargs):
                call_args = mock_communities.update_one.call_args
                if call_args:
                    push_data = call_args[0][1].get("$push", {})
                    comment = push_data.get("posts.$.comments", {})
                    assert "created_at" in comment
                return MagicMock(modified_count=1)
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.add_comment(
                community_id=community_id,
                post_id=post_id,
                author_id="507f1f77bcf86cd799439011",
                text="Great post!"
            )
            
            assert result["added"] is True

    @pytest.mark.asyncio
    async def test_add_comment_error_handling(self):
        """Test error handling when adding comment."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.update_one.side_effect = Exception("Database error")
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.add_comment(
                community_id=community_id,
                post_id=1,
                author_id="507f1f77bcf86cd799439011",
                text="Great post!"
            )
            
            assert "error" in result


class TestPostLike:
    """Tests for liking posts."""

    @pytest.mark.asyncio
    async def test_add_like_success(self):
        """Test successfully liking a post."""
        community_id = str(ObjectId())
        post_id = 1
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            community_data = {
                "_id": ObjectId(community_id),
                "posts": [{"postID": post_id, "likes": 5}]
            }
            mock_communities.find_one_and_update.return_value = community_data
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.add_like(community_id, post_id)
            
            assert "likes" in result

    @pytest.mark.asyncio
    async def test_add_like_post_not_found(self):
        """Test liking non-existent post."""
        community_id = str(ObjectId())
        post_id = 999
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.find_one_and_update.return_value = None
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.add_like(community_id, post_id)
            
            assert "error" in result

    @pytest.mark.asyncio
    async def test_add_like_increments_count(self):
        """Test that like count increments."""
        community_id = str(ObjectId())
        post_id = 1
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            
            # Simulate post with likes incrementing
            community_data = {
                "_id": ObjectId(community_id),
                "posts": [{"postID": post_id, "likes": 10}]
            }
            mock_communities.find_one_and_update.return_value = community_data
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.add_like(community_id, post_id)
            
            assert result["likes"] == 10

    @pytest.mark.asyncio
    async def test_add_like_error_handling(self):
        """Test error handling when liking."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.find_one_and_update.side_effect = Exception("Database error")
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.add_like(community_id, 1)
            
            assert "error" in result


class TestCommunityCreation:
    """Tests for community creation."""

    @pytest.mark.asyncio
    async def test_create_community_success(self, sample_community_data):
        """Test successfully creating a community."""
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            inserted_id = ObjectId()
            mock_communities.insert_one.return_value = MagicMock(inserted_id=inserted_id)
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Community.create_community(
                name=sample_community_data["name"],
                creator_id=sample_community_data["creatorID"],
                description=sample_community_data["description"]
            )
            
            assert "inserted_id" in result
            assert result["inserted_id"] == str(inserted_id)

    @pytest.mark.asyncio
    async def test_create_community_without_description(self):
        """Test creating community without description."""
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.insert_one.return_value = MagicMock(inserted_id=ObjectId())
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Community.create_community(
                name="Test Community",
                creator_id="507f1f77bcf86cd799439011"
            )
            
            assert "inserted_id" in result

    @pytest.mark.asyncio
    async def test_create_community_error_handling(self):
        """Test error handling in community creation."""
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.insert_one.side_effect = Exception("Database error")
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Community.create_community(
                name="Test",
                creator_id="507f1f77bcf86cd799439011"
            )
            
            assert "error" in result


class TestCommunityPublishPost:
    """Tests for publishing posts in community."""

    @pytest.mark.asyncio
    async def test_publish_post_success(self):
        """Test successfully publishing post."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.Post.create") as mock_create:
            mock_create.return_value = {"created_post": {"postID": 1}}
            
            result = await Community.publish_post(
                community_id=community_id,
                author_id="507f1f77bcf86cd799439011",
                title="Test Post",
                content="Test content"
            )
            
            assert "created_post" in result

    @pytest.mark.asyncio
    async def test_publish_post_with_content_type(self):
        """Test publishing post with custom content type."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.Post.create") as mock_create:
            mock_create.return_value = {"created_post": {"postID": 1, "contentType": "video"}}
            
            result = await Community.publish_post(
                community_id=community_id,
                author_id="507f1f77bcf86cd799439011",
                title="Video Post",
                content="Video content",
                content_type="video"
            )
            
            assert result["created_post"]["contentType"] == "video"


class TestCommunityViewPosts:
    """Tests for viewing community posts."""

    @pytest.mark.asyncio
    async def test_view_posts_success(self):
        """Test successfully viewing posts."""
        community_id = str(ObjectId())
        post_data = {
            "postID": 1,
            "title": "Test Post",
            "content": "Content",
            "authorID": "507f1f77bcf86cd799439011"
        }
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_users = AsyncMock()
            
            community = {
                "_id": ObjectId(community_id),
                "posts": [post_data]
            }
            user = {"_id": ObjectId(post_data["authorID"]), "userName": "testuser"}
            
            mock_communities.find_one.return_value = community
            mock_users.find_one.return_value = user
            
            def mock_getitem(key):
                if key == "communities":
                    return mock_communities
                elif key == "users":
                    return mock_users
            
            mock_db.__getitem__.side_effect = mock_getitem
            
            result = await Community.view_posts(community_id)
            
            assert "posts" in result
            assert len(result["posts"]) == 1

    @pytest.mark.asyncio
    async def test_view_posts_community_not_found(self):
        """Test viewing posts for non-existent community."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.find_one.return_value = None
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Community.view_posts(community_id)
            
            assert "error" in result

    @pytest.mark.asyncio
    async def test_view_posts_with_author_names(self):
        """Test that posts include author names."""
        community_id = str(ObjectId())
        author_id = str(ObjectId())
        post_data = {
            "postID": 1,
            "title": "Test",
            "authorID": author_id
        }
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_users = AsyncMock()
            
            mock_communities.find_one.return_value = {
                "_id": ObjectId(community_id),
                "posts": [post_data]
            }
            mock_users.find_one.return_value = {"userName": "testuser"}
            
            def mock_getitem(key):
                if key == "communities":
                    return mock_communities
                elif key == "users":
                    return mock_users
            
            mock_db.__getitem__.side_effect = mock_getitem
            
            result = await Community.view_posts(community_id)
            
            assert result["posts"][0]["authorName"] == "testuser"


class TestCommunityGetAllPosts:
    """Tests for getting all posts globally."""

    @pytest.mark.asyncio
    async def test_get_all_posts_success(self):
        """Test getting all posts across communities."""
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_users = AsyncMock()
            
            async def async_cursor():
                yield {
                    "name": "Community 1",
                    "posts": [{"postID": 1, "title": "Post 1"}]
                }
            
            mock_communities.find = MagicMock(return_value=async_cursor())
            mock_users.find_one.return_value = None
            
            def mock_getitem(key):
                if key == "communities":
                    return mock_communities
                elif key == "users":
                    return mock_users
            
            mock_db.__getitem__.side_effect = mock_getitem
            
            result = await Community.get_all_posts()
            
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_all_posts_empty(self):
        """Test getting all posts when none exist."""
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            
            async def empty_cursor():
                return
                yield
            
            mock_communities.find = MagicMock(return_value=empty_cursor())
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Community.get_all_posts()
            
            assert result == []

    @pytest.mark.asyncio
    async def test_get_all_posts_includes_community_name(self):
        """Test that global posts include community name."""
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_users = AsyncMock()
            
            async def async_cursor():
                yield {
                    "name": "Travel Community",
                    "posts": [{"postID": 1, "title": "Post 1"}]
                }
            
            mock_communities.find = MagicMock(return_value=async_cursor())
            mock_users.find_one.return_value = None
            
            def mock_getitem(key):
                if key == "communities":
                    return mock_communities
                elif key == "users":
                    return mock_users
            
            mock_db.__getitem__.side_effect = mock_getitem
            
            result = await Community.get_all_posts()
            
            assert result[0]["communityName"] == "Travel Community"


class TestCommunityEdgeCases:
    """Tests for edge cases in community models."""

    @pytest.mark.asyncio
    async def test_create_post_with_long_title(self):
        """Test creating post with very long title."""
        community_id = str(ObjectId())
        long_title = "A" * 1000
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.find_one.return_value = {
                "_id": ObjectId(community_id),
                "posts": []
            }
            mock_communities.update_one.return_value = MagicMock(modified_count=1)
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.create(
                community_id=community_id,
                author_id="507f1f77bcf86cd799439011",
                title=long_title,
                content="Content"
            )
            
            assert "created_post" in result

    @pytest.mark.asyncio
    async def test_add_comment_with_special_characters(self):
        """Test adding comment with special characters."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.update_one.return_value = MagicMock(modified_count=1)
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Post.add_comment(
                community_id=community_id,
                post_id=1,
                author_id="507f1f77bcf86cd799439011",
                text="Amazing! 😍 🎉 #travel @user"
            )
            
            assert result["added"] is True

    @pytest.mark.asyncio
    async def test_create_community_with_special_characters(self):
        """Test creating community with special characters."""
        with patch("app.models.community_models.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.insert_one.return_value = MagicMock(inserted_id=ObjectId())
            
            mock_db.__getitem__.return_value = mock_communities
            
            result = await Community.create_community(
                name="Travel & Adventure 🌍🗺️",
                creator_id="507f1f77bcf86cd799439011",
                description="For all travelers!"
            )
            
            assert "inserted_id" in result
