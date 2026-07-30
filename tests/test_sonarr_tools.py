"""Tests for SonarrTools."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.sonarr_tools import SonarrTools


class TestSonarrTools:
    """Tests for SonarrTools."""

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
        """Create SonarrTools instance with mock client."""
        return SonarrTools(mock_client)

    @pytest.mark.asyncio
    async def test_search_series(self, tools, mock_client):
        """Test series search."""
        mock_client.get.return_value = [
            {"id": 1, "title": "Test Series", "year": 2023},
        ]

        result = await tools.search_series("Test")
        assert len(result) == 1
        assert result[0]["title"] == "Test Series"
        mock_client.get.assert_called_once_with("/series/lookup", {"term": "Test"})

    @pytest.mark.asyncio
    async def test_get_series_by_id(self, tools, mock_client):
        """Test getting series by ID."""
        mock_client.get.return_value = {
            "id": 1,
            "title": "Test Series",
            "year": 2023,
        }

        result = await tools.get_series(series_id=1)
        assert result["title"] == "Test Series"
        mock_client.get.assert_called_once_with("/series/1")

    @pytest.mark.asyncio
    async def test_get_all_series(self, tools, mock_client):
        """Test getting all series."""
        mock_client.get.return_value = [
            {"id": 1, "title": "Series 1"},
            {"id": 2, "title": "Series 2"},
        ]

        result = await tools.get_series()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_episodes(self, tools, mock_client):
        """Test getting episodes for a series."""
        mock_client.get.return_value = [
            {"id": 1, "season_number": 1, "episode_number": 1, "title": "Pilot"},
        ]

        result = await tools.get_episodes(series_id=1)
        assert len(result) == 1
        assert result[0]["title"] == "Pilot"
        mock_client.get.assert_called_once_with("/episode", params={"seriesId": 1})

    @pytest.mark.asyncio
    async def test_get_episodes_with_filters(self, tools, mock_client):
        """Test getting episodes with filters."""
        mock_client.get.return_value = []

        await tools.get_episodes(series_id=1, season_number=3)
        mock_client.get.assert_called_once_with("/episode", params={"seriesId": 1, "seasonNumber": 3})

    @pytest.mark.asyncio
    async def test_add_series(self, tools, mock_client):
        """Test adding a new series."""
        mock_client.post.return_value = {"id": 123, "title": "New Series"}

        result = await tools.add_series(
            tvdb_id=123456,
            title="New Series",
            root_path="/data/series",
        )
        assert result["title"] == "New Series"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_series(self, tools, mock_client):
        """Test deleting a series."""
        mock_client.delete.return_value = 200

        result = await tools.delete_series(series_id=123)
        assert result["success"] is True
        assert "deleted" in result["message"].lower()
        mock_client.delete.assert_called_once_with("/series", 123, params={"deleteFiles": False, "addImportListExclusion": True})

    @pytest.mark.asyncio
    async def test_get_quality_profile(self, tools, mock_client):
        """Test getting quality profiles."""
        mock_client.get.return_value = [
            {"id": 1, "name": "Standard"},
        ]

        result = await tools.get_quality_profile()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_root_folder(self, tools, mock_client):
        """Test getting root folders."""
        mock_client.get.return_value = [
            {"id": 1, "path": "/data", "freeSpace": 1000000},
        ]

        result = await tools.get_root_folder()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_series_status(self, tools, mock_client):
        """Test getting series status."""
        mock_client.get.side_effect = [
            {"id": 1, "title": "Test", "year": 2023, "status": "continuing", "seasonCount": 3},
            [
                {"aired": True, "hasFile": True, "monitored": True},
                {"aired": False, "hasFile": False, "monitored": True},
                {"aired": True, "hasFile": True, "monitored": False},
            ],
        ]

        result = await tools.get_series_status(series_id=1)
        assert "series" in result
        assert "episodes" in result
        assert result["series"]["title"] == "Test"
        assert result["episodes"]["total"] == 3
        assert result["episodes"]["aired"] == 2
