"""Tests for ReadarrTools."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.readarr_tools import ReadarrTools


class TestReadarrTools:
    """Tests for ReadarrTools."""

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
        """Create ReadarrTools instance with mock client."""
        return ReadarrTools(mock_client)

    # ── search_author ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_search_author(self, tools, mock_client):
        """Test author search."""
        mock_client.get.return_value = [
            {"id": 1, "title": "Test Author", "year": 2020},
        ]

        result = await tools.search_author("Test")
        assert len(result) == 1
        assert result[0]["title"] == "Test Author"
        mock_client.get.assert_called_once_with("/author/lookup", {"term": "Test"})

    @pytest.mark.asyncio
    async def test_search_author_empty(self, tools, mock_client):
        """Test author search with no results."""
        mock_client.get.return_value = []

        result = await tools.search_author("Nobody")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_author_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for search_author."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.search_author("Test")

    # ── get_author ────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_author_by_id(self, tools, mock_client):
        """Test getting author by ID."""
        mock_client.get.return_value = {
            "id": 1,
            "title": "Test Author",
            "year": 2020,
        }

        result = await tools.get_author(author_id=1)
        assert result["title"] == "Test Author"
        mock_client.get.assert_called_once_with("/author/1")

    @pytest.mark.asyncio
    async def test_get_all_authors(self, tools, mock_client):
        """Test getting all authors."""
        mock_client.get.return_value = [
            {"id": 1, "title": "Author 1"},
            {"id": 2, "title": "Author 2"},
        ]

        result = await tools.get_author()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_authors_by_name(self, tools, mock_client):
        """Test getting authors filtered by name."""
        mock_client.get.return_value = [
            {"id": 1, "title": "Test Author"},
        ]

        await tools.get_author(author_name="Test")
        mock_client.get.assert_called_once_with("/author", params={"authorName": "Test"})

    @pytest.mark.asyncio
    async def test_get_author_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for get_author."""
        from httpx import HTTPError

        mock_client.get.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.get_author(author_id=1)

    # ── add_author ────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_add_author(self, tools, mock_client):
        """Test adding a new author without search."""
        mock_client.post.return_value = {"id": 789, "title": "New Author"}

        result = await tools.add_author(
            foreign_id="mb-uuid-123",
            title="New Author",
            root_path="/data/books",
            quality_profile_id=2,
            monitored=True,
            search_for_missing=False,
        )
        assert result["title"] == "New Author"
        mock_client.post.assert_called_once()

        # Verify only one POST call (no command)
        args = mock_client.post.call_args[0][0]
        assert args == "/author"

    @pytest.mark.asyncio
    async def test_add_author_with_search(self, tools, mock_client):
        """Test adding an author with search_for_missing=True triggers command."""
        mock_client.post.side_effect = [
            {"id": 789, "title": "New Author"},
            None,  # second call: /command
        ]

        result = await tools.add_author(
            foreign_id="mb-uuid-456",
            title="New Author",
            root_path="/data/books",
            search_for_missing=True,
        )
        assert result["title"] == "New Author"

        # First call: POST /author to add
        first_call = mock_client.post.call_args_list[0]
        assert first_call[0][0] == "/author"

        # Second call: POST /command
        second_call = mock_client.post.call_args_list[1]
        assert second_call[0][0] == "/command"
        body = second_call[0][1]
        assert body["name"] == "SearchMissing"
        assert body["authorId"] == 789

    @pytest.mark.asyncio
    async def test_add_author_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for add_author."""
        from httpx import HTTPError

        mock_client.post.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.add_author(
                foreign_id="mb-uuid",
                title="New Author",
                root_path="/data/books",
            )

    # ── delete_author ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_delete_author(self, tools, mock_client):
        """Test deleting an author without deleting files."""
        mock_client.delete.return_value = 200

        result = await tools.delete_author(author_id=123)
        assert result["success"] is True
        assert "deleted" in result["message"].lower()
        mock_client.delete.assert_called_once_with("/author", 123, params=None)

    @pytest.mark.asyncio
    async def test_delete_author_with_files(self, tools, mock_client):
        """Test deleting an author and its files from disk."""
        mock_client.delete.return_value = 200

        result = await tools.delete_author(author_id=123, delete_files=True)
        assert result["success"] is True
        mock_client.delete.assert_called_once_with("/author", 123, params={"deleteFiles": True})

    @pytest.mark.asyncio
    async def test_delete_author_api_error_propagates(self, tools, mock_client):
        """Test that API errors propagate for delete_author."""
        from httpx import HTTPError

        mock_client.delete.side_effect = HTTPError("Connection failed")

        with pytest.raises(HTTPError):
            await tools.delete_author(author_id=123)
