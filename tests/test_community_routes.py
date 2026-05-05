"""
test_community_routes.py - Integration tests for community routes.

Tests cover:
- Community creation
- Post publishing and retrieval
- Comment management
- Like functionality
- Trip-specific posts
- Error handling and validation
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from bson import ObjectId
from app.routes import community_route


@pytest.fixture
def test_app_with_community_routes():
    """Create a test app with only community routes."""
    app = FastAPI()
    app.include_router(community_route.router, prefix="/api")
    return app


@pytest.fixture
def client(test_app_with_community_routes):
    """Create a test client."""
    return TestClient(test_app_with_community_routes)


class TestCreateCommunityRoute:
    """Tests for POST /community/create endpoint."""

    def test_create_community_success(self, client, sample_community_data):
        """Test successfully creating a community."""
        with patch("app.models.community_models.Community.create_community") as mock_create:
            community_id = str(ObjectId())
            mock_create.return_value = {"inserted_id": community_id}
            
            response = client.post(
                "/api/community/create",
                data={
                    "userID": sample_community_data["creatorID"],
                    "name": sample_community_data["name"],
                    "description": sample_community_data["description"]
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert response.json()["community_id"] == community_id

    def test_create_community_missing_name(self, client):
        """Test community creation without name."""
        response = client.post(
            "/api/community/create",
            data={"userID": "507f1f77bcf86cd799439011"}
            # Missing name
        )
        
        assert response.status_code == 422

    def test_create_community_missing_creator(self, client, sample_community_data):
        """Test community creation without creator."""
        response = client.post(
            "/api/community/create",
            data={"name": sample_community_data["name"]}
            # Missing userID
        )
        
        assert response.status_code == 422

    def test_create_community_with_description(self, client, sample_community_data):
        """Test community creation with description."""
        with patch("app.models.community_models.Community.create_community") as mock_create:
            community_id = str(ObjectId())
            mock_create.return_value = {"inserted_id": community_id}
            
            response = client.post(
                "/api/community/create",
                data={
                    "userID": sample_community_data["creatorID"],
                    "name": sample_community_data["name"],
                    "description": "Detailed community description"
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_create_community_database_error(self, client, sample_community_data):
        """Test community creation with database error."""
        with patch("app.models.community_models.Community.create_community") as mock_create:
            mock_create.return_value = {"error": "Database error"}
            
            response = client.post(
                "/api/community/create",
                data={
                    "userID": sample_community_data["creatorID"],
                    "name": sample_community_data["name"]
                }
            )
            
            assert response.status_code == 400


class TestPublishPostRoute:
    """Tests for POST /community/{communityID}/post/create endpoint."""

    def test_publish_post_success(self, client, sample_post_data):
        """Test successfully publishing a post."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.Community.publish_post") as mock_publish:
            mock_publish.return_value = {"created_post": sample_post_data}
            
            response = client.post(
                f"/api/community/{community_id}/post/create",
                data={
                    "userID": sample_post_data["authorID"],
                    "title": sample_post_data["title"],
                    "content": sample_post_data["content"],
                    "contentType": sample_post_data["contentType"]
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert "post" in response.json()

    def test_publish_post_missing_title(self, client):
        """Test publishing post without title."""
        community_id = str(ObjectId())
        
        response = client.post(
            f"/api/community/{community_id}/post/create",
            data={
                "userID": "507f1f77bcf86cd799439011",
                "content": "Post content"
                # Missing title
            }
        )
        
        assert response.status_code == 422

    def test_publish_post_missing_content(self, client):
        """Test publishing post without content."""
        community_id = str(ObjectId())
        
        response = client.post(
            f"/api/community/{community_id}/post/create",
            data={
                "userID": "507f1f77bcf86cd799439011",
                "title": "Post Title"
                # Missing content
            }
        )
        
        assert response.status_code == 422

    def test_publish_post_community_not_found(self, client, sample_post_data):
        """Test publishing post to non-existent community."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.Community.publish_post") as mock_publish:
            mock_publish.return_value = {"error": "Community not found"}
            
            response = client.post(
                f"/api/community/{community_id}/post/create",
                data={
                    "userID": sample_post_data["authorID"],
                    "title": sample_post_data["title"],
                    "content": sample_post_data["content"]
                }
            )
            
            assert response.status_code == 400

    def test_publish_post_with_custom_content_type(self, client, sample_post_data):
        """Test publishing post with custom content type."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.Community.publish_post") as mock_publish:
            mock_publish.return_value = {"created_post": sample_post_data}
            
            response = client.post(
                f"/api/community/{community_id}/post/create",
                data={
                    "userID": sample_post_data["authorID"],
                    "title": sample_post_data["title"],
                    "content": sample_post_data["content"],
                    "contentType": "video"
                }
            )
            
            assert response.status_code == 200


class TestViewPostsRoute:
    """Tests for GET /community/{communityID}/posts endpoint."""

    def test_view_posts_success(self, client, sample_post_data):
        """Test retrieving posts from community."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.Community.view_posts") as mock_view:
            mock_view.return_value = {"posts": [sample_post_data]}
            
            response = client.get(f"/api/community/{community_id}/posts")
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert len(response.json()["posts"]) == 1

    def test_view_posts_empty(self, client):
        """Test viewing posts when community has no posts."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.Community.view_posts") as mock_view:
            mock_view.return_value = {"posts": []}
            
            response = client.get(f"/api/community/{community_id}/posts")
            
            assert response.status_code == 200
            assert len(response.json()["posts"]) == 0

    def test_view_posts_community_not_found(self, client):
        """Test viewing posts for non-existent community."""
        community_id = str(ObjectId())
        
        with patch("app.models.community_models.Community.view_posts") as mock_view:
            mock_view.return_value = {"error": "Community not found"}
            
            response = client.get(f"/api/community/{community_id}/posts")
            
            assert response.status_code == 404

    def test_view_posts_with_author_names(self, client):
        """Test viewing posts includes author information."""
        community_id = str(ObjectId())
        post_with_author = {
            "postID": 1,
            "title": "Test Post",
            "content": "Content",
            "authorID": "507f1f77bcf86cd799439011",
            "authorName": "TestUser"
        }
        
        with patch("app.models.community_models.Community.view_posts") as mock_view:
            mock_view.return_value = {"posts": [post_with_author]}
            
            response = client.get(f"/api/community/{community_id}/posts")
            
            assert response.status_code == 200
            assert response.json()["posts"][0]["authorName"] == "TestUser"


class TestAddCommentRoute:
    """Tests for POST /community/{communityID}/post/{postID}/comment endpoint."""

    def test_add_comment_success(self, client):
        """Test successfully adding a comment."""
        community_id = str(ObjectId())
        post_id = 1
        
        with patch("app.models.community_models.Post.add_comment") as mock_comment:
            mock_comment.return_value = {"added": True}
            
            response = client.post(
                f"/api/community/{community_id}/post/{post_id}/comment",
                data={
                    "userID": "507f1f77bcf86cd799439011",
                    "text": "Great post!"
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_add_comment_missing_text(self, client):
        """Test adding comment without text."""
        community_id = str(ObjectId())
        post_id = 1
        
        response = client.post(
            f"/api/community/{community_id}/post/{post_id}/comment",
            data={"userID": "507f1f77bcf86cd799439011"}
            # Missing text
        )
        
        assert response.status_code == 422

    def test_add_comment_missing_user_id(self, client):
        """Test adding comment without user ID."""
        community_id = str(ObjectId())
        post_id = 1
        
        response = client.post(
            f"/api/community/{community_id}/post/{post_id}/comment",
            data={"text": "Great post!"}
            # Missing userID
        )
        
        assert response.status_code == 422

    def test_add_comment_post_not_found(self, client):
        """Test adding comment to non-existent post."""
        community_id = str(ObjectId())
        post_id = 999
        
        with patch("app.models.community_models.Post.add_comment") as mock_comment:
            mock_comment.return_value = {"error": "Post not found"}
            
            response = client.post(
                f"/api/community/{community_id}/post/{post_id}/comment",
                data={
                    "userID": "507f1f77bcf86cd799439011",
                    "text": "Great post!"
                }
            )
            
            assert response.status_code == 400

    def test_add_comment_long_text(self, client):
        """Test adding comment with very long text."""
        community_id = str(ObjectId())
        post_id = 1
        long_text = "A" * 1000
        
        with patch("app.models.community_models.Post.add_comment") as mock_comment:
            mock_comment.return_value = {"added": True}
            
            response = client.post(
                f"/api/community/{community_id}/post/{post_id}/comment",
                data={
                    "userID": "507f1f77bcf86cd799439011",
                    "text": long_text
                }
            )
            
            assert response.status_code == 200


class TestLikePostRoute:
    """Tests for POST /community/{communityID}/post/{postID}/like endpoint."""

    def test_like_post_success(self, client):
        """Test successfully liking a post."""
        community_id = str(ObjectId())
        post_id = 1
        
        with patch("app.models.community_models.Post.add_like") as mock_like:
            mock_like.return_value = {"likes": 5}
            
            response = client.post(
                f"/api/community/{community_id}/post/{post_id}/like"
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert response.json()["likes"] == 5

    def test_like_post_not_found(self, client):
        """Test liking non-existent post."""
        community_id = str(ObjectId())
        post_id = 999
        
        with patch("app.models.community_models.Post.add_like") as mock_like:
            mock_like.return_value = {"error": "Post not found"}
            
            response = client.post(
                f"/api/community/{community_id}/post/{post_id}/like"
            )
            
            assert response.status_code == 400

    def test_like_post_incrementing_count(self, client):
        """Test like count increments correctly."""
        community_id = str(ObjectId())
        post_id = 1
        
        with patch("app.models.community_models.Post.add_like") as mock_like:
            # Simulate multiple likes
            for expected_count in [1, 2, 3]:
                mock_like.return_value = {"likes": expected_count}
                response = client.post(
                    f"/api/community/{community_id}/post/{post_id}/like"
                )
                assert response.json()["likes"] == expected_count


class TestViewTripPostsRoute:
    """Tests for GET /community/{communityID}/posts/trips endpoint."""

    def test_view_trip_posts_success(self, client):
        """Test retrieving trip posts from community."""
        community_id = str(ObjectId())
        trip_post = {
            "postID": 1,
            "title": "My Paris Trip",
            "content": "Had a great time!",
            "tripData": {"destination": "Paris"}
        }
        
        with patch("app.database.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.find_one.return_value = {
                "_id": ObjectId(community_id),
                "name": "Travel Community",
                "posts": [trip_post]
            }
            
            mock_db.__getitem__.return_value = mock_communities
            
            response = client.get(f"/api/community/{community_id}/posts/trips")
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert len(response.json()["trip_posts"]) == 1

    def test_view_trip_posts_empty(self, client):
        """Test viewing trip posts when none exist."""
        community_id = str(ObjectId())
        
        with patch("app.database.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.find_one.return_value = {
                "_id": ObjectId(community_id),
                "name": "Travel Community",
                "posts": []
            }
            
            mock_db.__getitem__.return_value = mock_communities
            
            response = client.get(f"/api/community/{community_id}/posts/trips")
            
            assert response.status_code == 200
            assert len(response.json()["trip_posts"]) == 0

    def test_view_trip_posts_community_not_found(self, client):
        """Test viewing trip posts for non-existent community."""
        community_id = str(ObjectId())
        
        with patch("app.database.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.find_one.return_value = None
            
            mock_db.__getitem__.return_value = mock_communities
            
            response = client.get(f"/api/community/{community_id}/posts/trips")
            
            assert response.status_code == 404

    def test_view_trip_posts_filters_non_trip_posts(self, client):
        """Test that trip posts endpoint filters out non-trip posts."""
        community_id = str(ObjectId())
        posts = [
            {"postID": 1, "title": "Regular Post", "content": "No tripData"},
            {"postID": 2, "title": "Trip Post", "content": "With trip!", "tripData": {"destination": "Paris"}},
            {"postID": 3, "title": "Another Regular Post", "content": "No tripData"}
        ]
        
        with patch("app.database.database") as mock_db:
            mock_communities = AsyncMock()
            mock_communities.find_one.return_value = {
                "_id": ObjectId(community_id),
                "name": "Travel Community",
                "posts": posts
            }
            
            mock_db.__getitem__.return_value = mock_communities
            
            response = client.get(f"/api/community/{community_id}/posts/trips")
            
            assert response.status_code == 200
            assert len(response.json()["trip_posts"]) == 1
            assert response.json()["trip_posts"][0]["postID"] == 2


class TestCommunityRouteEdgeCases:
    """Tests for edge cases in community routes."""

    def test_create_community_special_characters(self, client):
        """Test creating community with special characters."""
        with patch("app.models.community_models.Community.create_community") as mock_create:
            community_id = str(ObjectId())
            mock_create.return_value = {"inserted_id": community_id}
            
            response = client.post(
                "/api/community/create",
                data={
                    "userID": "507f1f77bcf86cd799439011",
                    "name": "Travel & Adventure 🌍🗺️",
                    "description": "For all travel enthusiasts!"
                }
            )
            
            assert response.status_code == 200

    def test_publish_post_very_long_content(self, client):
        """Test publishing post with very long content."""
        community_id = str(ObjectId())
        long_content = "A" * 5000
        
        with patch("app.models.community_models.Community.publish_post") as mock_publish:
            mock_publish.return_value = {"created_post": {"postID": 1}}
            
            response = client.post(
                f"/api/community/{community_id}/post/create",
                data={
                    "userID": "507f1f77bcf86cd799439011",
                    "title": "Long Post",
                    "content": long_content
                }
            )
            
            assert response.status_code == 200

    def test_add_comment_special_characters(self, client):
        """Test adding comment with special characters."""
        community_id = str(ObjectId())
        post_id = 1
        
        with patch("app.models.community_models.Post.add_comment") as mock_comment:
            mock_comment.return_value = {"added": True}
            
            response = client.post(
                f"/api/community/{community_id}/post/{post_id}/comment",
                data={
                    "userID": "507f1f77bcf86cd799439011",
                    "text": "Amazing! 😍🎉 #travel @friend"
                }
            )
            
            assert response.status_code == 200
