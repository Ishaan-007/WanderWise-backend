"""
test_user_service.py - Unit tests for UserService.

Tests cover:
- User registration (success, duplicate email, duplicate username)
- User retrieval by email and ID
- User profile updates
- Follow/unfollow relationships
- Error handling and edge cases
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from bson import ObjectId
from app.services.user_service import UserService
from contextlib import asynccontextmanager


class TestUserServiceRegister:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, sample_user_data):
        """Test successful user registration."""
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.find_one.return_value = None  # No duplicate email/username
            mock_users.insert_one.return_value = MagicMock(inserted_id=ObjectId())
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.register_user_service(sample_user_data)
            
            assert result["message"] == "Registration successful"
            assert "inserted_id" in result
            mock_users.find_one.assert_called()
            mock_users.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, sample_user_data):
        """Test registration fails with duplicate email."""
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            # Simulate existing user with same email
            mock_users.find_one.return_value = {"email": sample_user_data["email"]}
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.register_user_service(sample_user_data)
            
            assert result["error"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, sample_user_data):
        """Test registration fails with duplicate username."""
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            # First call: no duplicate email
            # Second call: duplicate username exists
            mock_users.find_one.side_effect = [None, {"userName": sample_user_data["userName"]}]
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.register_user_service(sample_user_data)
            
            assert result["error"] == "Username already taken"

    @pytest.mark.asyncio
    async def test_register_user_initializes_counts(self, sample_user_data):
        """Test that registration initializes follower/following counts."""
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.find_one.return_value = None
            mock_users.insert_one.return_value = MagicMock(inserted_id=ObjectId())
            mock_db.__getitem__.return_value = mock_users
            
            await UserService.register_user_service(sample_user_data)
            
            # Check that insert_one was called with counts initialized
            call_args = mock_users.insert_one.call_args
            inserted_data = call_args[0][0]
            assert inserted_data["followerCount"] == 0
            assert inserted_data["followingCount"] == 0


class TestUserServiceGetUser:
    """Tests for user retrieval."""

    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, sample_registered_user):
        """Test retrieving user by email when user exists."""
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.find_one.return_value = sample_registered_user
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.get_user_by_email(sample_registered_user["email"])
            
            assert result == sample_registered_user
            mock_users.find_one.assert_called_once_with(
                {"email": sample_registered_user["email"]}
            )

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self):
        """Test retrieving user by email when user doesn't exist."""
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.find_one.return_value = None
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.get_user_by_email("nonexistent@example.com")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, sample_registered_user):
        """Test retrieving user by ID when user exists."""
        user_id = str(sample_registered_user["_id"])
        
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.find_one.return_value = sample_registered_user
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.get_user_by_id(user_id)
            
            assert result is not None
            assert result["userID"] == user_id
            assert "_id" not in result

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self):
        """Test retrieving user by ID when user doesn't exist."""
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.find_one.return_value = None
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.get_user_by_id("507f1f77bcf86cd799439011")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_invalid_id(self):
        """Test retrieving user with invalid ObjectId format."""
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.find_one.side_effect = Exception("Invalid ObjectId")
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.get_user_by_id("invalid_id")
            
            assert result is None


class TestUserServiceUpdate:
    """Tests for user profile updates."""

    @pytest.mark.asyncio
    async def test_update_user_success(self, sample_registered_user):
        """Test successful user update by email."""
        email = sample_registered_user["email"]
        update_data = {"userName": "newusername", "location": "London, UK"}
        
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.update_one.return_value = MagicMock(modified_count=1)
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.update_user(email, update_data)
            
            mock_users.update_one.assert_called_once()
            call_args = mock_users.update_one.call_args
            assert call_args[0][0] == {"email": email}
            assert call_args[0][1] == {"$set": update_data}

    @pytest.mark.asyncio
    async def test_update_user_by_id_success(self, sample_registered_user):
        """Test successful user update by ID."""
        user_id = str(sample_registered_user["_id"])
        update_data = {"profilePictureURL": "https://example.com/new_pic.jpg"}
        
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.update_one.return_value = MagicMock(modified_count=1)
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.update_user_by_id(user_id, update_data)
            
            assert "modified_count" in result
            mock_users.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_by_id_ignores_counts(self):
        """Test that update_user_by_id removes follower/following counts."""
        user_id = "507f1f77bcf86cd799439011"
        update_data = {
            "userName": "newname",
            "followerCount": 999,
            "followingCount": 888
        }
        
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.update_one.return_value = MagicMock(modified_count=1)
            mock_db.__getitem__.return_value = mock_users
            
            await UserService.update_user_by_id(user_id, update_data)
            
            call_args = mock_users.update_one.call_args
            updated_data = call_args[0][1]["$set"]
            assert "followerCount" not in updated_data
            assert "followingCount" not in updated_data
            assert updated_data["userName"] == "newname"

    @pytest.mark.asyncio
    async def test_update_user_by_id_invalid_id(self):
        """Test update with invalid ObjectId."""
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.update_one.side_effect = Exception("Invalid ObjectId")
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.update_user_by_id("invalid_id", {"userName": "test"})
            
            assert "error" in result


class TestUserServiceFollow:
    """Tests for follow/unfollow relationships."""

    @pytest.mark.asyncio
    async def test_follow_user_success(self, sample_registered_user):
        """Test successful follow operation."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_follows = AsyncMock()
            
            # Setup mock returns
            mock_users.find_one.side_effect = [sample_registered_user, sample_registered_user]
            mock_follows.find_one.return_value = None  # Not already following
            mock_follows.insert_one.return_value = MagicMock()
            mock_users.update_one.return_value = MagicMock()
            
            # Setup database dictionary access
            def mock_getitem(key):
                if key == "users":
                    return mock_users
                elif key == "follows":
                    return mock_follows
            
            mock_db.__getitem__.side_effect = mock_getitem
            # Bulletproof async context manager mock
            @asynccontextmanager
            async def mock_start_session(*args, **kwargs):
                session_mock = AsyncMock()
                
                @asynccontextmanager
                async def mock_start_transaction(*args, **kwargs):
                    yield  # This perfectly simulates the 'async with' block
                    
                session_mock.start_transaction = mock_start_transaction
                yield session_mock

            mock_db.client.start_session = mock_start_session
            
            result = await UserService.follow_user(follower_id, target_id)
            
            assert "error" not in result, f"Expected success, got: {result.get('error')}"
            assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_follow_user_not_found(self):
        """Test follow fails when user not found."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_users.find_one.return_value = None  # User not found
            mock_db.__getitem__.return_value = mock_users
            
            result = await UserService.follow_user(follower_id, target_id)
            
            assert result["error"] == "One or both users not found"

    @pytest.mark.asyncio
    async def test_follow_already_following(self, sample_registered_user):
        """Test follow fails when already following."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_follows = AsyncMock()
            
            mock_users.find_one.side_effect = [sample_registered_user, sample_registered_user]
            mock_follows.find_one.return_value = {"followerID": follower_id}  # Already following
            
            def mock_getitem(key):
                if key == "users":
                    return mock_users
                elif key == "follows":
                    return mock_follows
            
            mock_db.__getitem__.side_effect = mock_getitem
            
            result = await UserService.follow_user(follower_id, target_id)
            
            assert result["error"] == "Already following this user"

    @pytest.mark.asyncio
    async def test_unfollow_user_success(self, sample_registered_user):
        """Test successful unfollow operation."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_follows = AsyncMock()
            
            mock_users.find_one.side_effect = [sample_registered_user, sample_registered_user]
            mock_follows.find_one.return_value = {"_id": ObjectId()}  # Following exists
            mock_follows.delete_one.return_value = MagicMock()
            mock_users.update_one.return_value = MagicMock()
            
            def mock_getitem(key):
                if key == "users":
                    return mock_users
                elif key == "follows":
                    return mock_follows
            
            mock_db.__getitem__.side_effect = mock_getitem
            # Bulletproof async context manager mock
            @asynccontextmanager
            async def mock_start_session(*args, **kwargs):
                session_mock = AsyncMock()
                
                @asynccontextmanager
                async def mock_start_transaction(*args, **kwargs):
                    yield  # This perfectly simulates the 'async with' block
                    
                session_mock.start_transaction = mock_start_transaction
                yield session_mock

            mock_db.client.start_session = mock_start_session
            
            result = await UserService.unfollow_user(follower_id, target_id)
            
            assert "error" not in result, f"Expected success, got: {result.get('error')}"
            assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_unfollow_follow_relationship_not_found(self, sample_registered_user):
        """Test unfollow fails when follow relationship doesn't exist."""
        follower_id = "507f1f77bcf86cd799439011"
        target_id = "507f1f77bcf86cd799439012"
        
        with patch("app.services.user_service.database") as mock_db:
            mock_users = AsyncMock()
            mock_follows = AsyncMock()
            
            mock_users.find_one.side_effect = [sample_registered_user, sample_registered_user]
            mock_follows.find_one.return_value = None  # No follow relationship
            
            def mock_getitem(key):
                if key == "users":
                    return mock_users
                elif key == "follows":
                    return mock_follows
            
            mock_db.__getitem__.side_effect = mock_getitem
            
            result = await UserService.unfollow_user(follower_id, target_id)
            
            assert result["error"] == "Follow relationship not found"
