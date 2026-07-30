"""Tests for LidarrTools."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.lidarr_tools import LidarrTools


class TestLidarrTools:
    """Tests for LidarrTools."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock BaseARRClient."""
        client = MagicMock()
        client.get = AsyncMock()
        client.post = AsyncMock()
        client.delete = AsyncMock(return_value=200)
        return client

    @pytest.fixture
    def tools(self, mock_client):
        """Create LidarrTools instance with mock client."""
        return LidarrTools(mock_client)

    # ── search_artist ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_search_artist(self, tools, mock_client):
        """Test artist search."""
        mock_client.get.return_value = [
            {"id": 1, "title": "Test Artist", "year": 2020},
        ]

        result = await tools.search_artist("Test")
        assert len(result) == 1
        assert result[0]["title"] == "Test Artist"
        mock_client.get.assert_called_once_with("/artist/lookup", {"term": "Test"})

    @pytest.mark.asyncio
    async def test_search_artist_empty(self, tools, mock_client):
        """Test artist search with no results."""
        mock_client.get.return_value = []

        result = await tools.search_artist("Nobody")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_artist_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for search_artist."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.search_artist("Test")

    # ── get_artist ────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_artist_by_id(self, tools, mock_client):
        """Test getting artist by ID."""
        mock_client.get.return_value = {
            "id": 1,
            "title": "Test Artist",
            "year": 2020,
        }

        result = await tools.get_artist(artist_id=1)
        assert result["title"] == "Test Artist"
        mock_client.get.assert_called_once_with("/artist/1")

    @pytest.mark.asyncio
    async def test_get_all_artists(self, tools, mock_client):
        """Test getting all artists."""
        mock_client.get.return_value = [
            {"id": 1, "title": "Artist 1"},
            {"id": 2, "title": "Artist 2"},
        ]

        result = await tools.get_artist()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_artists_by_name(self, tools, mock_client):
        """Test getting artists filtered by name."""
        mock_client.get.return_value = [
            {"id": 1, "title": "Test Artist"},
        ]

        await tools.get_artist(artist_name="Test")
        mock_client.get.assert_called_once_with("/artist", params={"artistName": "Test"})

    @pytest.mark.asyncio
    async def test_get_artist_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for get_artist."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.get_artist(artist_id=1)

    # ── add_artist ────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_add_artist(self, tools, mock_client):
        """Test adding a new artist without search."""
        mock_client.post.return_value = {"id": 789, "title": "New Artist"}

        result = await tools.add_artist(
            musicbrainz_id="mb-uuid-123",
            title="New Artist",
            root_path="/data/music",
            quality_profile_id=2,
            monitored=True,
            search_for_missing=False,
        )
        assert result["title"] == "New Artist"
        mock_client.post.assert_called_once()

        # Verify only one POST call (no command)
        args = mock_client.post.call_args[0][0]
        assert args == "/artist"

    @pytest.mark.asyncio
    async def test_add_artist_with_search(self, tools, mock_client):
        """Test adding an artist with search_for_missing=True triggers ArtistSearch command."""
        mock_client.post.side_effect = [
            {"id": 789, "title": "New Artist"},
            None,  # second call: /command
        ]

        result = await tools.add_artist(
            musicbrainz_id="mb-uuid-456",
            title="New Artist",
            root_path="/data/music",
            search_for_missing=True,
        )
        assert result["title"] == "New Artist"

        # First call: POST /artist to add
        first_call = mock_client.post.call_args_list[0]
        assert first_call[0][0] == "/artist"

        # Second call: POST /command with ArtistSearch command
        second_call = mock_client.post.call_args_list[1]
        assert second_call[0][0] == "/command"
        body = second_call[0][1]
        assert body["name"] == "ArtistSearch"
        assert body["artistId"] == 789

    @pytest.mark.asyncio
    async def test_add_artist_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for add_artist."""
        from httpx import HTTPError

        mock_client.post.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.add_artist(
                musicbrainz_id="mb-uuid",
                title="New Artist",
                root_path="/data/music",
            )

    # ── delete_artist ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_delete_artist(self, tools, mock_client):
        """Test deleting an artist without deleting files."""
        mock_client.delete.return_value = 200

        result = await tools.delete_artist(artist_id=123)
        assert result["success"] is True
        assert "deleted" in result["message"].lower()
        mock_client.delete.assert_called_once_with("/artist", 123, params=None)

    @pytest.mark.asyncio
    async def test_delete_artist_with_files(self, tools, mock_client):
        """Test deleting an artist and its files from disk."""
        mock_client.delete.return_value = 200

        result = await tools.delete_artist(artist_id=123, delete_files=True)
        assert result["success"] is True
        mock_client.delete.assert_called_once_with("/artist", 123, params={"deleteFiles": True})

    @pytest.mark.asyncio
    async def test_delete_artist_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for delete_artist."""
        from httpx import HTTPError

        mock_client.delete.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.delete_artist(artist_id=123)
