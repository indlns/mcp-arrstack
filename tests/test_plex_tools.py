"""Tests for PlexTools."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.plex_tools import PlexTools


class TestPlexTools:
    """Tests for PlexTools."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock PlexClient."""
        client = MagicMock()
        client.get = AsyncMock()
        return client

    @pytest.fixture
    def tools(self, mock_client):
        """Create PlexTools instance with mock client."""
        return PlexTools(mock_client)

    # ── search ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_search(self, tools, mock_client):
        """Test searching Plex library."""
        mock_client.get.return_value = {
            "MediaContainer": {
                "Metadata": [
                    {"title": "Test Movie", "type": "movie"},
                ]
            }
        }

        result = await tools.search("Test")
        assert len(result["MediaContainer"]["Metadata"]) == 1
        mock_client.get.assert_called_once_with("/search", {"query": "Test"})

    @pytest.mark.asyncio
    async def test_search_empty(self, tools, mock_client):
        """Test search with no results."""
        mock_client.get.return_value = {"MediaContainer": {"Metadata": []}}

        result = await tools.search("Nobody")
        assert result["MediaContainer"]["Metadata"] == []

    @pytest.mark.asyncio
    async def test_search_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for search."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.search("Test")

    # ── library_sections ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_library_sections(self, tools, mock_client):
        """Test getting library sections."""
        mock_client.get.return_value = {
            "MediaContainer": {
                "Directory": [
                    {"key": "1", "title": "Movies", "type": "movie"},
                    {"key": "2", "title": "Shows", "type": "show"},
                ]
            }
        }

        result = await tools.library_sections()
        assert len(result) == 2
        assert result[0]["title"] == "Movies"

    @pytest.mark.asyncio
    async def test_library_sections_empty(self, tools, mock_client):
        """Test getting empty library sections."""
        mock_client.get.return_value = {"MediaContainer": {"Directory": []}}

        result = await tools.library_sections()
        assert result == []

    @pytest.mark.asyncio
    async def test_library_sections_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for library_sections."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.library_sections()

    # ── recently_added ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_recently_added(self, tools, mock_client):
        """Test getting recently added content."""
        mock_client.get.return_value = {
            "MediaContainer": {
                "Metadata": [
                    {"title": "New Movie", "type": "movie"},
                    {"title": "New Show", "type": "show"},
                ]
            }
        }

        result = await tools.recently_added()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_recently_added_with_limit(self, tools, mock_client):
        """Test recently_added respects limit."""
        mock_client.get.return_value = {
            "MediaContainer": {
                "Metadata": [
                    {"title": f"Item {i}"} for i in range(10)
                ]
            }
        }

        result = await tools.recently_added(limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_recently_added_filter_by_type(self, tools, mock_client):
        """Test recently_added filters by section_type client-side."""
        mock_client.get.return_value = {
            "MediaContainer": {
                "Metadata": [
                    {"title": "Movie 1", "type": "movie"},
                    {"title": "Show 1", "type": "show"},
                    {"title": "Movie 2", "type": "movie"},
                ]
            }
        }

        result = await tools.recently_added(section_type="movie")
        assert len(result) == 2
        assert result[0]["title"] == "Movie 1"
        assert result[1]["title"] == "Movie 2"

    @pytest.mark.asyncio
    async def test_recently_added_filter_no_match(self, tools, mock_client):
        """Test recently_added returns empty when filter matches nothing."""
        mock_client.get.return_value = {
            "MediaContainer": {
                "Metadata": [
                    {"title": "Movie 1", "type": "movie"},
                ]
            }
        }

        result = await tools.recently_added(section_type="show")
        assert result == []

    @pytest.mark.asyncio
    async def test_recently_added_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for recently_added."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.recently_added()

    # ── playlists ─────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_playlists(self, tools, mock_client):
        """Test getting playlists."""
        mock_client.get.return_value = {
            "MediaContainer": {
                "Directory": [
                    {"title": "My Playlist", "type": "playlist"},
                ]
            }
        }

        result = await tools.playlists()
        assert len(result) == 1
        assert result[0]["title"] == "My Playlist"

    @pytest.mark.asyncio
    async def test_playlists_empty(self, tools, mock_client):
        """Test getting empty playlists."""
        mock_client.get.return_value = {"MediaContainer": {"Directory": []}}

        result = await tools.playlists()
        assert result == []

    @pytest.mark.asyncio
    async def test_playlists_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for playlists."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.playlists()

    # ── library ───────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_library(self, tools, mock_client):
        """Test getting items from a library section."""
        mock_client.get.return_value = {
            "MediaContainer": {
                "Metadata": [
                    {"title": "Movie 1"},
                    {"title": "Movie 2"},
                ]
            }
        }

        result = await tools.library(section_key=1, section_type="movie")
        assert len(result) == 2
        mock_client.get.assert_called_once_with(
            "/library/sections/1/all", params={"limit": 50, "type": 1}
        )

    @pytest.mark.asyncio
    async def test_library_no_type_filter(self, tools, mock_client):
        """Test getting library items without type filter."""
        mock_client.get.return_value = {"MediaContainer": {"Metadata": []}}

        await tools.library(section_key=1, section_type="all")
        mock_client.get.assert_called_once_with(
            "/library/sections/1/all", params={"limit": 50}
        )

    @pytest.mark.asyncio
    async def test_library_with_custom_limit(self, tools, mock_client):
        """Test library with custom limit."""
        mock_client.get.return_value = {"MediaContainer": {"Metadata": []}}

        await tools.library(section_key=1, limit=100)
        mock_client.get.assert_called_once_with(
            "/library/sections/1/all", params={"limit": 100}
        )

    @pytest.mark.asyncio
    async def test_library_type_show_mapping(self, tools, mock_client):
        """Test library section_type 'show' maps to Plex API type code 2."""
        mock_client.get.return_value = {"MediaContainer": {"Metadata": []}}

        await tools.library(section_key=2, section_type="show")
        mock_client.get.assert_called_once_with(
            "/library/sections/2/all", params={"limit": 50, "type": 2}
        )

    @pytest.mark.asyncio
    async def test_library_unknown_type_ignored(self, tools, mock_client):
        """Test library with unknown section_type does not add type param."""
        mock_client.get.return_value = {"MediaContainer": {"Metadata": []}}

        await tools.library(section_key=1, section_type="unknown")
        mock_client.get.assert_called_once_with(
            "/library/sections/1/all", params={"limit": 50}
        )

    @pytest.mark.asyncio
    async def test_library_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for library."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.library(section_key=1)

    # ── get_status ────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_status(self, tools, mock_client):
        """Test getting Plex server status."""
        mock_client.get.return_value = {
            "MediaContainer": {
                "title": "My Plex",
                "version": "1.28.0",
                "platform": "Linux",
            }
        }
        mock_client.get.side_effect = [
            {
                "MediaContainer": {
                    "title": "My Plex",
                    "version": "1.28.0",
                    "platform": "Linux",
                }
            },
            {
                "MediaContainer": {
                    "Directory": [
                        {"key": "1", "type": "movie", "size": 100},
                        {"key": "2", "type": "show", "size": 50},
                    ]
                }
            },
        ]

        result = await tools.get_status()
        assert result["name"] == "My Plex"
        assert result["version"] == "1.28.0"
        assert result["total_libraries"] == 2
        assert result["movie_count"] == 100
        assert result["show_count"] == 50

    @pytest.mark.asyncio
    async def test_get_status_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for get_status."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.get_status()
