"""
test_user_models.py - Unit tests for user model classes.

Tests cover:
- GuestUser model initialization and methods
- RegisteredUser registration and login
- User profile display and updates
- Follow/unfollow functionality
- Model validation and error handling
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from hashlib import sha256
from bson import ObjectId
from app.models.user_models import User, GuestUser, RegisteredUser


class TestUserModel:
    """Tests for base User model."""

    def test_user_creation(self):
        """Test basic user model creation."""
        user = User(userID="507f1f77bcf86cd799439011", userName="testuser")
        
        assert user.userID == "507f1f77bcf86cd799439011"
        assert user.userName == "testuser"

    def test_user_with_no_name(self):
        """Test user creation without userName."""
        user = User(userID="507f1f77bcf86cd799439011")
        
        assert user.userID == "507f1f77bcf86cd799439011"
        assert user.userName is None

    def test_user_model_serialization(self):
        """Test user model serialization to dict."""
        user = User(userID="507f1f77bcf86cd799439011", userName="testuser")
        user_dict = user.model_dump()
        
        assert "userID" in user_dict
        assert "userName" in user_dict


class TestGuestUser:
    """Tests for GuestUser model."""

    def test_guest_user_creation(self):
        """Test guest user creation."""
        guest = GuestUser(userID="guest")
        
        assert guest.userID == "guest"
        assert isinstance(guest, User)

    def test_guest_user_with_username(self):
        """Test guest user with username."""
        guest = GuestUser(userID="guest", userName="Anonymous User")
        
        assert guest.userID == "guest"
        assert guest.userName == "Anonymous User"

    @pytest.mark.asyncio
    async def test_guest_user_open_community(self):
        """Test guest user opening communities."""
        with patch("app.services.user_service.UserService.get_all_communities") as mock_get:
            mock_get.return_value = [{"communityID": "1", "name": "Community 1"}]
            
            guest = GuestUser(userID="guest")
            result = await guest.openCommunity()
            
            assert result == [{"communityID": "1", "name": "Community 1"}]


class TestRegisteredUserRegistration:
    """Tests for RegisteredUser registration."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, sample_user_data):
        """Test successful user registration."""
        with patch("app.services.user_service.UserService.register_user_service") as mock_register:
            inserted_id = ObjectId()
            mock_register.return_value = {
                "message": "Registration successful",
                "inserted_id": inserted_id
            }
            
            result = await RegisteredUser.register(
                email=sample_user_data["email"],
                password=sample_user_data["password"],
                userName=sample_user_data["userName"],
                profilePictureURL=sample_user_data.get("profilePictureURL"),
                location=sample_user_data.get("location"),
                preference=sample_user_data.get("preference")
            )
            
            assert result["success"] is True
            assert "user" in result

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, sample_user_data):
        """Test registration with duplicate email."""
        with patch("app.services.user_service.UserService.register_user_service") as mock_register:
            mock_register.return_value = {"error": "Email already registered"}
            
            result = await RegisteredUser.register(
                email=sample_user_data["email"],
                password=sample_user_data["password"],
                userName=sample_user_data["userName"]
            )
            
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, sample_user_data):
        """Test registration with duplicate username."""
        with patch("app.services.user_service.UserService.register_user_service") as mock_register:
            mock_register.return_value = {"error": "Username already taken"}
            
            result = await RegisteredUser.register(
                email=sample_user_data["email"],
                password=sample_user_data["password"],
                userName=sample_user_data["userName"]
            )
            
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_register_user_password_hashing(self, sample_user_data):
        """Test that password is hashed during registration."""
        password = sample_user_data["password"]
        
        with patch("app.services.user_service.UserService.register_user_service") as mock_register:
            mock_register.return_value = {
                "message": "Registration successful",
                "inserted_id": ObjectId()
            }
            
            await RegisteredUser.register(
                email=sample_user_data["email"],
                password=password,
                userName=sample_user_data["userName"]
            )
            
            # Verify that the service was called with hashed password
            call_args = mock_register.call_args
            user_data = call_args[0][0]
            expected_hash = sha256(password.encode()).hexdigest()
            assert user_data["passwordHash"] == expected_hash

    @pytest.mark.asyncio
    async def test_register_user_minimal_fields(self):
        """Test registration with only required fields."""
        with patch("app.services.user_service.UserService.register_user_service") as mock_register:
            mock_register.return_value = {
                "message": "Registration successful",
                "inserted_id": ObjectId()
            }
            
            result = await RegisteredUser.register(
                email="test@example.com",
                password="password123",
                userName="testuser"
            )
            
            assert result["success"] is True


class TestRegisteredUserLogin:
    """Tests for RegisteredUser login."""

    @pytest.mark.asyncio
    async def test_login_success(self, sample_registered_user):
        """Test successful login."""
        email = sample_registered_user["email"]
        password = "SecurePassword123!"
        
        with patch("app.services.user_service.UserService.get_user_by_email") as mock_get:
            mock_get.return_value = sample_registered_user
            
            result = await RegisteredUser.login(email, password)
            
            assert result["success"] is True
            assert "user" in result

    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        """Test login with non-existent email."""
        with patch("app.services.user_service.UserService.get_user_by_email") as mock_get:
            mock_get.return_value = None
            
            result = await RegisteredUser.login("nonexistent@example.com", "password123")
            
            assert result["success"] is False
            assert result["error"] == "Email not registered"

    @pytest.mark.asyncio
    async def test_login_incorrect_password(self, sample_registered_user):
        """Test login with incorrect password."""
        email = sample_registered_user["email"]
        
        with patch("app.services.user_service.UserService.get_user_by_email") as mock_get:
            mock_get.return_value = sample_registered_user
            
            result = await RegisteredUser.login(email, "wrongpassword")
            
            assert result["success"] is False
            assert result["error"] == "Incorrect password"

    @pytest.mark.asyncio
    async def test_login_password_case_sensitive(self, sample_registered_user):
        """Test that password login is case-sensitive."""
        email = sample_registered_user["email"]
        password = "SecurePassword123!"
        wrong_case = "securepassword123!"  # lowercase 's'
        
        with patch("app.services.user_service.UserService.get_user_by_email") as mock_get:
            mock_get.return_value = sample_registered_user
            
            result = await RegisteredUser.login(email, wrong_case)
            
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_login_converts_id_to_userid(self, sample_registered_user):
        """Test that _id is converted to userID during login."""
        email = sample_registered_user["email"]
        password = "SecurePassword123!"
        
        with patch("app.services.user_service.UserService.get_user_by_email") as mock_get:
            mock_get.return_value = sample_registered_user
            
            result = await RegisteredUser.login(email, password)
            
            assert result["success"] is True
            user = result["user"]
            assert "userID" in user
            assert user["userID"] == str(sample_registered_user["_id"])


class TestRegisteredUserDisplayProfile:
    """Tests for displaying user profile."""

    @pytest.mark.asyncio
    async def test_display_profile_success(self, sample_registered_user):
        """Test successfully displaying user profile."""
        user_id = str(sample_registered_user["_id"])
        
        with patch("app.services.user_service.UserService.get_user_by_id") as mock_get:
            mock_get.return_value = {
                **sample_registered_user,
                "userID": user_id
            }
            
            result = await RegisteredUser.displayProfile(user_id)
            
            assert result["success"] is True
            assert "profile" in result
            assert result["profile"]["userID"] == user_id

    @pytest.mark.asyncio
    async def test_display_profile_not_found(self):
        """Test displaying profile for non-existent user."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.user_service.UserService.get_user_by_id") as mock_get:
            mock_get.return_value = None
            
            result = await RegisteredUser.displayProfile(user_id)
            
            assert result["success"] is False
            assert result["error"] == "User not found"

    @pytest.mark.asyncio
    async def test_display_profile_includes_all_fields(self, sample_registered_user):
        """Test that profile includes all required fields."""
        user_id = str(sample_registered_user["_id"])
        
        with patch("app.services.user_service.UserService.get_user_by_id") as mock_get:
            mock_get.return_value = {
                **sample_registered_user,
                "userID": user_id
            }
            
            result = await RegisteredUser.displayProfile(user_id)
            
            profile = result["profile"]
            required_fields = ["userID", "userName", "email", "profilePictureURL", 
                             "location", "preference", "followerCount", "followingCount"]
            for field in required_fields:
                assert field in profile


class TestRegisteredUserUpdateProfile:
    """Tests for updating user profile."""

    @pytest.mark.asyncio
    async def test_update_profile_success(self, sample_registered_user):
        """Test successfully updating profile."""
        user_id = str(sample_registered_user["_id"])
        update_data = {"userName": "newusername", "location": "London, UK"}
        
        with patch("app.services.user_service.UserService.update_user_by_id") as mock_update:
            mock_update.return_value = {"modified_count": 1}
            
            result = await RegisteredUser.updateProfile(user_id, update_data)
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_update_profile_not_found(self):
        """Test updating profile for non-existent user."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.user_service.UserService.update_user_by_id") as mock_update:
            mock_update.return_value = {"modified_count": 0}
            
            result = await RegisteredUser.updateProfile(user_id, {"userName": "newname"})
            
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_update_profile_single_field(self):
        """Test updating single profile field."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.user_service.UserService.update_user_by_id") as mock_update:
            mock_update.return_value = {"modified_count": 1}
            
            result = await RegisteredUser.updateProfile(
                user_id,
                {"profilePictureURL": "https://example.com/new_pic.jpg"}
            )
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_update_profile_multiple_fields(self):
        """Test updating multiple profile fields."""
        user_id = "507f1f77bcf86cd799439011"
        update_data = {
            "userName": "newname",
            "location": "Barcelona",
            "preference": "Beach Travel",
            "profilePictureURL": "https://example.com/pic.jpg"
        }
        
        with patch("app.services.user_service.UserService.update_user_by_id") as mock_update:
            mock_update.return_value = {"modified_count": 1}
            
            result = await RegisteredUser.updateProfile(user_id, update_data)
            
            assert result["success"] is True


class TestRegisteredUserFollowUnfollow:
    """Tests for follow/unfollow functionality."""

    @pytest.mark.asyncio
    async def test_follow_user_success(self):
        """Test successfully following a user."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.user_service.UserService.follow_user") as mock_follow:
            mock_follow.return_value = {"success": True}
            
            result = await RegisteredUser.follow(follower_id, target_id)
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_follow_already_following(self):
        """Test follow when already following."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.user_service.UserService.follow_user") as mock_follow:
            mock_follow.return_value = {"error": "Already following this user"}
            
            result = await RegisteredUser.follow(follower_id, target_id)
            
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_follow_user_not_found(self):
        """Test follow when user doesn't exist."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.user_service.UserService.follow_user") as mock_follow:
            mock_follow.return_value = {"error": "One or both users not found"}
            
            result = await RegisteredUser.follow(follower_id, target_id)
            
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_unfollow_success(self):
        """Test successfully unfollowing a user."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.user_service.UserService.unfollow_user") as mock_unfollow:
            mock_unfollow.return_value = {"success": True}
            
            result = await RegisteredUser.unfollow(follower_id, target_id)
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_unfollow_not_following(self):
        """Test unfollow when not following."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.user_service.UserService.unfollow_user") as mock_unfollow:
            mock_unfollow.return_value = {"error": "Follow relationship not found"}
            
            result = await RegisteredUser.unfollow(follower_id, target_id)
            
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_unfollow_user_not_found(self):
        """Test unfollow when user doesn't exist."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.user_service.UserService.unfollow_user") as mock_unfollow:
            mock_unfollow.return_value = {"error": "One or both users not found"}
            
            result = await RegisteredUser.unfollow(follower_id, target_id)
            
            assert result["success"] is False


class TestRegisteredUserOpenDashboard:
    """Tests for opening user dashboard."""

    @pytest.mark.asyncio
    async def test_open_dashboard_success(self):
        """Test successfully opening dashboard."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.user_service.UserService.get_user_by_id") as mock_get:
            mock_get.return_value = {
                "userID": user_id,
                "userName": "testuser",
                "email": "test@example.com"
            }
            
            result = await RegisteredUser.openDashboard(user_id)
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_open_dashboard_user_not_found(self):
        """Test opening dashboard for non-existent user."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch("app.services.user_service.UserService.get_user_by_id") as mock_get:
            mock_get.return_value = None
            
            result = await RegisteredUser.openDashboard(user_id)
            
            assert result is not None  # Should return error dict
