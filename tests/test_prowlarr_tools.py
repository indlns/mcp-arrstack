"""Tests for ProwlarrTools."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.prowlarr_tools import ProwlarrTools


class TestProwlarrTools:
    """Tests for ProwlarrTools."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock ProwlarrClient."""
        client = MagicMock()
        client.get = AsyncMock()
        client.post = AsyncMock()
        return client

    @pytest.fixture
    def tools(self, mock_client):
        """Create ProwlarrTools instance with mock client."""
        return ProwlarrTools(mock_client)

    @pytest.mark.asyncio
    async def test_search_default_type(self, tools, mock_client):
        """Test search with default type='search' — type param must NOT be sent."""
        mock_client.get.return_value = [
            {"title": "Test Release", "indexer": "TestIndexer", "size": 1000},
        ]

        result = await tools.search("TestQuery")
        assert len(result) == 1
        assert result[0]["title"] == "Test Release"
        mock_client.get.assert_called_once_with("/search", params={"query": "TestQuery"})

    @pytest.mark.asyncio
    async def test_search_custom_type(self, tools, mock_client):
        """Test search with non-default type — type param IS sent."""
        mock_client.get.return_value = [
            {"title": "TV Release", "indexer": "TestIndexer", "size": 2000},
        ]

        result = await tools.search("TVShow", type="tvsearch")
        assert len(result) == 1
        mock_client.get.assert_called_once_with("/search", params={"query": "TVShow", "type": "tvsearch"})

    @pytest.mark.asyncio
    async def test_search_moviesearch_type(self, tools, mock_client):
        """Test search with moviesearch type."""
        mock_client.get.return_value = []

        await tools.search("Movie Title", type="moviesearch")
        mock_client.get.assert_called_once_with("/search", params={"query": "Movie Title", "type": "moviesearch"})

    @pytest.mark.asyncio
    async def test_search_audiosearch_type(self, tools, mock_client):
        """Test search with audiosearch type."""
        mock_client.get.return_value = []

        await tools.search("Album Name", type="audiosearch")
        mock_client.get.assert_called_once_with("/search", params={"query": "Album Name", "type": "audiosearch"})

    @pytest.mark.asyncio
    async def test_search_booksearch_type(self, tools, mock_client):
        """Test search with booksearch type."""
        mock_client.get.return_value = []

        await tools.search("Book Title", type="booksearch")
        mock_client.get.assert_called_once_with("/search", params={"query": "Book Title", "type": "booksearch"})

    @pytest.mark.asyncio
    async def test_get_indexers_all(self, tools, mock_client):
        """Test getting all indexers."""
        mock_client.get.return_value = [
            {"id": 1, "name": "Indexer1", "enable": True},
            {"id": 2, "name": "Indexer2", "enable": False},
        ]

        result = await tools.get_indexers()
        assert len(result) == 2
        mock_client.get.assert_called_once_with("/indexer")

    @pytest.mark.asyncio
    async def test_get_indexers_enabled_only(self, tools, mock_client):
        """Test getting only enabled indexers."""
        mock_client.get.return_value = [
            {"id": 1, "name": "Indexer1", "enable": True},
            {"id": 2, "name": "Indexer2", "enable": False},
            {"id": 3, "name": "Indexer3", "enable": True},
        ]

        result = await tools.get_indexers(enabled_only=True)
        assert len(result) == 2
        assert all(i["enable"] for i in result)
        mock_client.get.assert_called_once_with("/indexer")

    @pytest.mark.asyncio
    async def test_get_indexers_empty(self, tools, mock_client):
        """Test getting indexers when none exist."""
        mock_client.get.return_value = []

        result = await tools.get_indexers()
        assert result == []
        mock_client.get.assert_called_once_with("/indexer")

    @pytest.mark.asyncio
    async def test_test_indexers(self, tools, mock_client):
        """Test testing all indexers at once."""
        mock_client.post.return_value = {
            "results": [
                {"indexerId": 1, "success": True, "messages": []},
                {"indexerId": 2, "success": True, "messages": []},
            ]
        }

        result = await tools.test_indexers()
        assert "results" in result
        assert len(result["results"]) == 2
        mock_client.post.assert_called_once_with("/indexer/testall")

    @pytest.mark.asyncio
    async def test_test_indexers_empty(self, tools, mock_client):
        """Test testing indexers when none configured."""
        mock_client.post.return_value = {"results": []}

        result = await tools.test_indexers()
        assert result["results"] == []
        mock_client.post.assert_called_once_with("/indexer/testall")

    @pytest.mark.asyncio
    async def test_get_history_default_limit(self, tools, mock_client):
        """Test getting history with default limit."""
        mock_client.get.return_value = [
            {"title": "Release1", "size": 1000, "time": 1234567890},
        ]

        result = await tools.get_history()
        assert len(result) == 1
        mock_client.get.assert_called_once_with("/history", {"limit": 100})

    @pytest.mark.asyncio
    async def test_get_history_custom_limit(self, tools, mock_client):
        """Test getting history with custom limit."""
        mock_client.get.return_value = []

        await tools.get_history(limit=50)
        mock_client.get.assert_called_once_with("/history", {"limit": 50})

    @pytest.mark.asyncio
    async def test_get_status(self, tools, mock_client):
        """Test getting system status with indexer counts."""
        mock_client.get.side_effect = [
            {
                "version": "1.0.0",
                "buildInfo": {"os": "linux"},
                "connectionStatus": "ok",
                "isDebug": False,
                "isLogging": True,
            },
            [
                {"id": 1, "name": "Indexer1", "enable": True},
                {"id": 2, "name": "Indexer2", "enable": False},
                {"id": 3, "name": "Indexer3", "enable": True},
            ],
        ]

        result = await tools.get_status()
        assert result["version"] == "1.0.0"
        assert result["connectionStatus"] == "ok"
        assert result["isDebug"] is False
        assert result["isLogging"] is True
        assert result["indexers"]["total"] == 3
        assert result["indexers"]["enabled"] == 2
        assert result["indexers"]["disabled"] == 1

        # Verify two calls: /system/status then /indexer
        calls = mock_client.get.call_args_list
        assert calls[0][0][0] == "/system/status"
        assert calls[1][0][0] == "/indexer"

    @pytest.mark.asyncio
    async def test_get_status_no_indexers(self, tools, mock_client):
        """Test getting status when no indexers configured."""
        mock_client.get.side_effect = [
            {
                "version": "1.0.0",
                "buildInfo": {"os": "linux"},
                "connectionStatus": "ok",
                "isDebug": False,
                "isLogging": True,
            },
            [],
        ]

        result = await tools.get_status()
        assert result["indexers"]["total"] == 0
        assert result["indexers"]["enabled"] == 0
        assert result["indexers"]["disabled"] == 0

    @pytest.mark.asyncio
    async def test_search_api_error_propagates(self, tools, mock_client):
        """Test that API errors are propagated (not swallowed)."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.search("Test")

    @pytest.mark.asyncio
    async def test_get_indexers_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for get_indexers."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.get_indexers()

    @pytest.mark.asyncio
    async def test_test_indexers_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for test_indexers."""
        from httpx import HTTPError

        mock_client.post.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.test_indexers()

    @pytest.mark.asyncio
    async def test_get_status_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for get_status."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.get_status()
