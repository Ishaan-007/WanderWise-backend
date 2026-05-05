"""
test_user_routes.py - Integration tests for user routes.

Tests cover:
- User registration (success, validation errors, duplicates)
- User login (success, incorrect credentials, user not found)
- Get all users
- Get user profile
- Update user profile
- Follow/unfollow operations
- HTTP status codes and error responses
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.routes import user_routes


@pytest.fixture
def test_app_with_user_routes():
    """Create a test app with only user routes."""
    app = FastAPI()
    app.include_router(user_routes.router, prefix="/api")
    return app


@pytest.fixture
def client(test_app_with_user_routes):
    """Create a test client."""
    return TestClient(test_app_with_user_routes)


class TestUserRegisterRoute:
    """Tests for POST /register endpoint."""

    def test_register_user_success(self, client, sample_user_data):
        """Test successful user registration."""
        with patch("app.models.user_models.RegisteredUser.register") as mock_register:
            mock_register.return_value = {"success": True, "user": sample_user_data}
            
            response = client.post(
                "/api/register",
                data={
                    "email": sample_user_data["email"],
                    "password": sample_user_data["password"],
                    "userName": sample_user_data["userName"],
                    "profilePictureURL": sample_user_data.get("profilePictureURL"),
                    "location": sample_user_data.get("location"),
                    "preference": sample_user_data.get("preference")
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_register_user_duplicate_email(self, client, sample_user_data):
        """Test registration fails with duplicate email."""
        with patch("app.models.user_models.RegisteredUser.register") as mock_register:
            mock_register.return_value = {"success": False, "error": "Email already registered"}
            
            response = client.post(
                "/api/register",
                data={
                    "email": sample_user_data["email"],
                    "password": sample_user_data["password"],
                    "userName": sample_user_data["userName"]
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is False

    def test_register_user_missing_required_fields(self, client):
        """Test registration fails with missing required fields."""
        response = client.post(
            "/api/register",
            data={
                "email": "test@example.com"
                # Missing password and userName
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestUserLoginRoute:
    """Tests for POST /login endpoint."""

    def test_login_success(self, client, sample_user_data):
        """Test successful user login."""
        with patch("app.models.user_models.RegisteredUser.login") as mock_login:
            user_response = sample_user_data.copy()
            user_response["userID"] = "507f1f77bcf86cd799439011"
            mock_login.return_value = {"success": True, "user": user_response}
            
            response = client.post(
                "/api/login",
                data={
                    "email": sample_user_data["email"],
                    "password": sample_user_data["password"]
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert "user" in response.json()

    def test_login_invalid_email(self, client):
        """Test login with unregistered email."""
        with patch("app.models.user_models.RegisteredUser.login") as mock_login:
            mock_login.return_value = {"success": False, "error": "Email not registered"}
            
            response = client.post(
                "/api/login",
                data={
                    "email": "nonexistent@example.com",
                    "password": "password123"
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is False

    def test_login_incorrect_password(self, client, sample_user_data):
        """Test login with incorrect password."""
        with patch("app.models.user_models.RegisteredUser.login") as mock_login:
            mock_login.return_value = {"success": False, "error": "Incorrect password"}
            
            response = client.post(
                "/api/login",
                data={
                    "email": sample_user_data["email"],
                    "password": "wrongpassword"
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is False

    def test_login_missing_fields(self, client):
        """Test login with missing email or password."""
        response = client.post(
            "/api/login",
            data={"email": "test@example.com"}
            # Missing password
        )
        
        assert response.status_code == 422  # Validation error


class TestGetUsersRoute:
    """Tests for GET /users endpoint."""

    def test_get_users_success(self, client, sample_registered_user):
        """Test retrieving all users."""
        with patch("app.routes.user_routes.database") as mock_db:
            mock_users = AsyncMock()
            
            mock_cursor = MagicMock()
            mock_cursor.to_list = AsyncMock(return_value=[sample_registered_user])
            mock_users.find = MagicMock(return_value=mock_cursor)
            
            mock_db.__getitem__.return_value = mock_users
            
            response = client.get("/api/users")
            
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_get_users_empty(self, client):
        """Test retrieving users when none exist."""
        with patch("app.routes.user_routes.database") as mock_db:
            mock_users = AsyncMock()
            mock_cursor = MagicMock()
            mock_cursor.to_list = AsyncMock(return_value=[])
            mock_users.find = MagicMock(return_value=mock_cursor)
            mock_db.__getitem__.return_value = mock_users
            
            response = client.get("/api/users")
            
            assert response.status_code == 200
            assert response.json() == []


class TestGetUserProfileRoute:
    """Tests for GET /user/profile/{userID} endpoint."""

    def test_get_user_profile_success(self, client, sample_registered_user):
        """Test retrieving user profile successfully."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.models.user_models.RegisteredUser.displayProfile") as mock_profile:
            mock_profile.return_value = {
                "success": True,
                "profile": {
                    "userID": user_id,
                    "userName": sample_registered_user["userName"],
                    "email": sample_registered_user["email"],
                    "followerCount": 0,
                    "followingCount": 0
                }
            }
            
            response = client.get(f"/api/user/profile/{user_id}")
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert "profile" in response.json()

    def test_get_user_profile_not_found(self, client):
        """Test retrieving profile for non-existent user."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.models.user_models.RegisteredUser.displayProfile") as mock_profile:
            mock_profile.return_value = {"success": False, "error": "User not found"}
            
            response = client.get(f"/api/user/profile/{user_id}")
            
            assert response.status_code == 404
            assert response.json()["detail"] == "User not found"


class TestUpdateUserProfileRoute:
    """Tests for PUT /user/profile/{userID}/update endpoint."""

    def test_update_user_profile_success(self, client):
        """Test successfully updating user profile."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.models.user_models.RegisteredUser.updateProfile") as mock_update:
            mock_update.return_value = {"success": True}
            
            response = client.put(
                f"/api/user/profile/{user_id}/update",
                data={
                    "userName": "newusername",
                    "location": "London, UK"
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_update_user_profile_no_data(self, client):
        """Test update with no data provided."""
        user_id = "507f1f77bcf86cd799439011"
        
        response = client.put(
            f"/api/user/profile/{user_id}/update",
            data={}
        )
        
        assert response.status_code == 400

    def test_update_user_profile_invalid_data(self, client):
        """Test update with invalid data."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.models.user_models.RegisteredUser.updateProfile") as mock_update:
            mock_update.return_value = {"success": False, "error": "Invalid data"}
            
            response = client.put(
                f"/api/user/profile/{user_id}/update",
                data={"userName": "string"}
            )
            
            # Update function filters out "string" placeholder values
            assert response.status_code == 400

    def test_update_user_profile_single_field(self, client):
        """Test updating single profile field."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.models.user_models.RegisteredUser.updateProfile") as mock_update:
            mock_update.return_value = {"success": True}
            
            response = client.put(
                f"/api/user/profile/{user_id}/update",
                data={"profilePictureURL": "https://example.com/newpic.jpg"}
            )
            
            assert response.status_code == 200


class TestFollowUserRoute:
    """Tests for POST /user/{userID}/follow/{targetUserID} endpoint."""

    def test_follow_user_success(self, client):
        """Test successfully following a user."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.models.user_models.RegisteredUser.follow") as mock_follow:
            mock_follow.return_value = {"success": True}
            
            response = client.post(
                f"/api/user/{follower_id}/follow/{target_id}"
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_follow_user_already_following(self, client):
        """Test following user when already following."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.models.user_models.RegisteredUser.follow") as mock_follow:
            mock_follow.return_value = {"success": False, "error": "Already following this user"}
            
            response = client.post(
                f"/api/user/{follower_id}/follow/{target_id}"
            )
            
            assert response.status_code == 400

    def test_follow_user_not_found(self, client):
        """Test following non-existent user."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.models.user_models.RegisteredUser.follow") as mock_follow:
            mock_follow.return_value = {"success": False, "error": "One or both users not found"}
            
            response = client.post(
                f"/api/user/{follower_id}/follow/{target_id}"
            )
            
            assert response.status_code == 400


class TestUnfollowUserRoute:
    """Tests for POST /user/{userID}/unfollow/{targetUserID} endpoint."""

    def test_unfollow_user_success(self, client):
        """Test successfully unfollowing a user."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.models.user_models.RegisteredUser.unfollow") as mock_unfollow:
            mock_unfollow.return_value = {"success": True}
            
            response = client.post(
                f"/api/user/{follower_id}/unfollow/{target_id}"
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_unfollow_user_not_following(self, client):
        """Test unfollowing user when not following."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.models.user_models.RegisteredUser.unfollow") as mock_unfollow:
            mock_unfollow.return_value = {"success": False, "error": "Follow relationship not found"}
            
            response = client.post(
                f"/api/user/{follower_id}/unfollow/{target_id}"
            )
            
            assert response.status_code == 400

    def test_unfollow_user_not_found(self, client):
        """Test unfollowing when user doesn't exist."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.models.user_models.RegisteredUser.unfollow") as mock_unfollow:
            mock_unfollow.return_value = {"success": False, "error": "One or both users not found"}
            
            response = client.post(
                f"/api/user/{follower_id}/unfollow/{target_id}"
            )
            
            assert response.status_code == 400


class TestGetCommunitiesRoute:
    """Tests for GET /communities endpoint."""

    def test_get_communities_success(self, client, sample_community_data):
        """Test retrieving all communities."""
        with patch("app.models.user_models.GuestUser.openCommunity") as mock_open:
            mock_open.return_value = [sample_community_data]
            
            response = client.get("/api/communities")
            
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_get_communities_empty(self, client):
        """Test retrieving communities when none exist."""
        with patch("app.models.user_models.GuestUser.openCommunity") as mock_open:
            mock_open.return_value = []
            
            response = client.get("/api/communities")
            
            assert response.status_code == 200
            assert response.json() == []
