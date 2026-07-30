"""Tests for RadarrTools."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.radarr_tools import RadarrTools


class TestRadarrTools:
    """Tests for RadarrTools."""

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
        """Create RadarrTools instance with mock client."""
        return RadarrTools(mock_client)

    @pytest.mark.asyncio
    async def test_search_movie(self, tools, mock_client):
        """Test movie search."""
        mock_client.get.return_value = [
            {"id": 1, "title": "Test Movie", "year": 2023},
        ]

        result = await tools.search_movie("Test")
        assert len(result) == 1
        assert result[0]["title"] == "Test Movie"
        mock_client.get.assert_called_once_with("/movie/lookup", {"term": "Test"})

    @pytest.mark.asyncio
    async def test_get_movies_by_id(self, tools, mock_client):
        """Test getting movie by ID."""
        mock_client.get.return_value = {
            "id": 1,
            "title": "Test Movie",
            "year": 2023,
        }

        result = await tools.get_movies(movie_id=1)
        assert result["title"] == "Test Movie"
        mock_client.get.assert_called_once_with("/movie/1")

    @pytest.mark.asyncio
    async def test_add_movie(self, tools, mock_client):
        """Test adding a new movie."""
        mock_client.post.return_value = {"id": 456, "title": "New Movie"}

        result = await tools.add_movie(
            tmdb_id=123456,
            title="New Movie",
            root_path="/data/movies",
        )
        assert result["title"] == "New Movie"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_movie_with_search(self, tools, mock_client):
        """Test adding a movie with search_for_movie=True triggers MoviesSearch command."""
        mock_client.post.side_effect = [
            {"id": 456, "title": "New Movie"},
            None,  # second call: /command
        ]

        result = await tools.add_movie(
            tmdb_id=123456,
            title="New Movie",
            root_path="/data/movies",
            search_for_movie=True,
        )
        assert result["title"] == "New Movie"

        # First call: POST /movie to add the movie
        first_call = mock_client.post.call_args_list[0]
        assert first_call[0][0] == "/movie"

        # Second call: POST /command with correct command name and array param
        second_call = mock_client.post.call_args_list[1]
        assert second_call[0][0] == "/command"
        body = second_call[0][1]
        assert body["name"] == "MoviesSearch"
        assert body["movieIds"] == [456]

    @pytest.mark.asyncio
    async def test_add_movie_without_search(self, tools, mock_client):
        """Test adding a movie with search_for_movie=False only calls /movie."""
        mock_client.post.return_value = {"id": 789, "title": "Another Movie"}

        result = await tools.add_movie(
            tmdb_id=7890,
            title="Another Movie",
            root_path="/data/movies",
            search_for_movie=False,
        )
        assert result["title"] == "Another Movie"

        # Only one POST call (to /movie), no /command call
        assert mock_client.post.call_count == 1
        assert mock_client.post.call_args[0][0] == "/movie"

    @pytest.mark.asyncio
    async def test_delete_movie(self, tools, mock_client):
        """Test deleting a movie without deleting files."""
        mock_client.delete.return_value = 200

        result = await tools.delete_movie(movie_id=456)
        assert result["success"] is True
        mock_client.delete.assert_called_once_with("/movie", 456, params=None)

    @pytest.mark.asyncio
    async def test_delete_movie_with_files(self, tools, mock_client):
        """Test deleting a movie and its files from disk."""
        mock_client.delete.return_value = 200

        result = await tools.delete_movie(movie_id=456, delete_files=True)
        assert result["success"] is True
        mock_client.delete.assert_called_once_with("/movie", 456, params={"deleteFiles": True})

    @pytest.mark.asyncio
    async def test_get_movie_status(self, tools, mock_client):
        """Test getting movie status."""
        mock_client.get.side_effect = [
            {
                "id": 1,
                "title": "Test Movie",
                "year": 2023,
                "status": "released",
                "overview": "A test movie",
                "sizeOnDisk": 10000000000,
                "movieFile": {
                    "quality": {"quality": {"name": "1080p"}},
                    "path": "/data/movies/test.mp4",
                },
            },
        ]

        result = await tools.get_movie_status(movie_id=1)
        assert "movie" in result
        assert "file" in result
        assert result["movie"]["title"] == "Test Movie"
        assert result["file"]["quality"] == "1080p"
