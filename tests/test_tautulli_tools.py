"""Tests for TautulliTools."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.tautulli_tools import TautulliTools


class TestTautulliTools:
    """Tests for TautulliTools."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock TautulliClient."""
        client = MagicMock()
        client.get = AsyncMock()
        return client

    @pytest.fixture
    def tools(self, mock_client):
        """Create TautulliTools instance with mock client."""
        return TautulliTools(mock_client)

    # ── get_activity ──────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_activity(self, tools, mock_client):
        """Test getting current activity."""
        mock_client.get.return_value = {
            "total_sessions": 3,
            "active_connections": [
                {"user": "user1", "title": "Movie 1"},
                {"user": "user2", "title": "Show S01E01"},
                {"user": "user3", "title": "Movie 2"},
            ],
        }

        result = await tools.get_activity()
        assert result["total_sessions"] == 3
        assert len(result["active_connections"]) == 3

    @pytest.mark.asyncio
    async def test_get_activity_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for get_activity."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.get_activity()

    # ── get_library_stats ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_library_stats(self, tools, mock_client):
        """Test getting library list with counts."""
        mock_client.get.return_value = [
            {
                "section_id": "1",
                "section_name": "Movies",
                "section_type": "movie",
                "count": "500",
            },
            {
                "section_id": "2",
                "section_name": "TV Shows",
                "section_type": "show",
                "count": "50",
            },
        ]

        result = await tools.get_library_stats()
        assert len(result) == 2
        assert result[0]["section_name"] == "Movies"
        mock_client.get.assert_called_once_with("get_libraries")

    @pytest.mark.asyncio
    async def test_get_library_stats_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for get_library_stats."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.get_library_stats()

    # ── get_history ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_history(self, tools, mock_client):
        """Test getting watch history."""
        mock_client.get.return_value = {
            "data": [
                {"user": "user1", "title": "Movie 1", "date": "2024-01-01"},
                {"user": "user2", "title": "Show S01E01", "date": "2024-01-02"},
            ]
        }

        result = await tools.get_history(length=10)
        assert len(result) == 2
        assert result[0]["user"] == "user1"
        mock_client.get.assert_called_once_with(
            "get_history",
            {"grouping": 0, "length": 10, "order_column": "date", "order_dir": "desc"},
        )

    @pytest.mark.asyncio
    async def test_get_history_with_custom_params(self, tools, mock_client):
        """Test getting history with custom parameters."""
        mock_client.get.return_value = {"data": []}

        await tools.get_history(grouping=1, length=50, order_column="full_title", order_dir="asc")
        mock_client.get.assert_called_once_with(
            "get_history",
            {"grouping": 1, "length": 50, "order_column": "full_title", "order_dir": "asc"},
        )

    @pytest.mark.asyncio
    async def test_get_history_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for get_history."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.get_history()

    # ── get_user_stats ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_user_stats_by_user_id(self, tools, mock_client):
        """Test getting user watch time stats by user_id."""
        mock_client.get.return_value = [
            {"query_days": 1, "total_plays": 2, "total_time": 3600},
            {"query_days": 7, "total_plays": 10, "total_time": 18000},
            {"query_days": 30, "total_plays": 50, "total_time": 90000},
            {"query_days": 0, "total_plays": 100, "total_time": 180000},
        ]

        result = await tools.get_user_stats(user_id="1")
        assert result["user_id"] == "1"
        assert len(result["stats"]) == 4
        mock_client.get.assert_called_once_with(
            "get_user_watch_time_stats", {"user_id": "1"}
        )

    @pytest.mark.asyncio
    async def test_get_user_stats_no_user_id_raises(self, tools, mock_client):
        """Test that get_user_stats raises ValueError without user_id."""
        with pytest.raises(ValueError, match="user_id is required"):
            await tools.get_user_stats()

    @pytest.mark.asyncio
    async def test_get_user_stats_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for get_user_stats."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.get_user_stats(user_id="1")

    # ── get_recently_added ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_recently_added(self, tools, mock_client):
        """Test getting recently added media."""
        mock_client.get.return_value = {
            "recently_added": [
                {"title": "New Movie", "type": "movie"},
                {"title": "New Show S01", "type": "episode"},
            ]
        }

        result = await tools.get_recently_added()
        assert len(result) == 2
        assert result[0]["title"] == "New Movie"

    @pytest.mark.asyncio
    async def test_get_recently_added_with_filter(self, tools, mock_client):
        """Test getting recently added with media_type filter."""
        mock_client.get.return_value = {"recently_added": [{"title": "New Movie"}]}

        await tools.get_recently_added(media_type="movie")
        mock_client.get.assert_called_once_with(
            "get_recently_added", {"count": "25", "media_type": "movie"}
        )

    @pytest.mark.asyncio
    async def test_get_recently_added_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for get_recently_added."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.get_recently_added()

    # ── get_streaming_users ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_streaming_users(self, tools, mock_client):
        """Test getting currently streaming users."""
        mock_client.get.return_value = {
            "total_sessions": 2,
            "active_connections": [
                {"user": "user1", "title": "Movie 1", "progress": 50},
            ],
        }

        result = await tools.get_streaming_users()
        assert len(result) == 1
        assert result[0]["user"] == "user1"

    @pytest.mark.asyncio
    async def test_get_streaming_users_no_sessions(self, tools, mock_client):
        """Test getting streaming users when no one is streaming."""
        mock_client.get.return_value = {
            "total_sessions": 0,
            "active_connections": [],
        }

        result = await tools.get_streaming_users()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_streaming_users_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for get_streaming_users."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.get_streaming_users()
