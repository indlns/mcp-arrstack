"""Tests for SeerrTools."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add project root to path so that `src` is importable as a package
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.seerr_tools import SeerrTools


class TestSeerrTools:
    """Tests for SeerrTools."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock SeerrClient."""
        client = MagicMock()
        client.get = AsyncMock()
        client.post = AsyncMock()
        return client

    @pytest.fixture
    def tools(self, mock_client):
        """Create SeerrTools instance with mock client."""
        return SeerrTools(mock_client)

    # ── search ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_search_basic(self, tools, mock_client):
        """Test basic search with only query."""
        mock_client.get.return_value = {
            "results": [
                {"id": 1, "title": "Test Movie", "mediaType": "movie"},
            ]
        }

        result = await tools.search("Test Movie")
        assert len(result["results"]) == 1
        mock_client.get.assert_called_once_with(
            "/search", {"query": "Test Movie"}
        )

    @pytest.mark.asyncio
    async def test_search_with_page(self, tools, mock_client):
        """Test search with page > 1."""
        mock_client.get.return_value = {"results": []}

        await tools.search("Query", page=3)
        mock_client.get.assert_called_once_with(
            "/search", {"query": "Query", "page": 3}
        )

    @pytest.mark.asyncio
    async def test_search_with_language(self, tools, mock_client):
        """Test search with language parameter."""
        mock_client.get.return_value = {"results": []}

        await tools.search("Query", language="ru")
        mock_client.get.assert_called_once_with(
            "/search", {"query": "Query", "language": "ru"}
        )

    @pytest.mark.asyncio
    async def test_search_with_all_params(self, tools, mock_client):
        """Test search with page and language."""
        mock_client.get.return_value = {"results": []}

        await tools.search("Query", page=2, language="en")
        mock_client.get.assert_called_once_with(
            "/search", {"query": "Query", "page": 2, "language": "en"}
        )

    # ── get_requests ──────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_requests_defaults(self, tools, mock_client):
        """Test get_requests with default parameters."""
        mock_client.get.return_value = {
            "pageInfo": {"page": 1, "pages": 5, "results": 50},
            "results": [],
        }

        result = await tools.get_requests()
        assert "pageInfo" in result
        assert "results" in result
        mock_client.get.assert_called_once_with(
            "/request",
            params={"take": 20, "skip": 0, "sort": "added", "sortDirection": "desc"},
        )

    @pytest.mark.asyncio
    async def test_get_requests_pagination(self, tools, mock_client):
        """Test get_requests with take/skip pagination."""
        mock_client.get.return_value = {"pageInfo": {}, "results": []}

        await tools.get_requests(take=10, skip=30)
        mock_client.get.assert_called_once_with(
            "/request",
            params={"take": 10, "skip": 30, "sort": "added", "sortDirection": "desc"},
        )

    @pytest.mark.asyncio
    async def test_get_requests_with_filter(self, tools, mock_client):
        """Test get_requests with filter parameter."""
        mock_client.get.return_value = {"pageInfo": {}, "results": []}

        await tools.get_requests(filter="pending")
        mock_client.get.assert_called_once_with(
            "/request",
            params={
                "take": 20,
                "skip": 0,
                "filter": "pending",
                "sort": "added",
                "sortDirection": "desc",
            },
        )

    @pytest.mark.asyncio
    async def test_get_requests_with_sort(self, tools, mock_client):
        """Test get_requests with sort parameters."""
        mock_client.get.return_value = {"pageInfo": {}, "results": []}

        await tools.get_requests(sort="modified", sort_direction="asc")
        call_kwargs = mock_client.get.call_args
        params = call_kwargs[1]["params"]
        assert params["sort"] == "modified"
        assert params["sortDirection"] == "asc"

    @pytest.mark.asyncio
    async def test_get_requests_with_requested_by(self, tools, mock_client):
        """Test get_requests with requested_by filter."""
        mock_client.get.return_value = {"pageInfo": {}, "results": []}

        await tools.get_requests(requested_by=42)
        call_kwargs = mock_client.get.call_args
        params = call_kwargs[1]["params"]
        assert params["requestedBy"] == 42

    @pytest.mark.asyncio
    async def test_get_requests_with_media_type(self, tools, mock_client):
        """Test get_requests with media_type filter."""
        mock_client.get.return_value = {"pageInfo": {}, "results": []}

        await tools.get_requests(media_type="movie")
        call_kwargs = mock_client.get.call_args
        params = call_kwargs[1]["params"]
        assert params["mediaType"] == "movie"

    @pytest.mark.asyncio
    async def test_get_requests_all_params(self, tools, mock_client):
        """Test get_requests with all parameters."""
        mock_client.get.return_value = {"pageInfo": {}, "results": []}

        await tools.get_requests(
            take=50,
            skip=100,
            filter="approved",
            sort="modified",
            sort_direction="desc",
            requested_by=7,
            media_type="tv",
        )
        call_kwargs = mock_client.get.call_args
        params = call_kwargs[1]["params"]
        assert params["take"] == 50
        assert params["skip"] == 100
        assert params["filter"] == "approved"
        assert params["sort"] == "modified"
        assert params["sortDirection"] == "desc"
        assert params["requestedBy"] == 7
        assert params["mediaType"] == "tv"

    # ── request_media ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_request_media_exact_match(self, tools, mock_client):
        """Test request_media with exact TMDb ID match."""
        search_result = {
            "results": [
                {
                    "id": 99,
                    "mediaType": "movie",
                    "mediaInfo": {"tmdbId": 12345},
                },
            ]
        }
        mock_client.get.return_value = search_result
        mock_client.post.return_value = {"id": 1, "status": "PENDING"}

        result = await tools.request_media(
            tmdb_id=12345, title="Test Movie", media_type="movie"
        )
        assert result["id"] == 1
        # Verify search was called with title
        mock_client.get.assert_called_with(
            "/search", {"query": "Test Movie"}
        )
        # Verify POST body
        post_call = mock_client.post.call_args
        assert post_call[0][0] == "/request"
        assert post_call[0][1]["mediaType"] == "movie"
        assert post_call[0][1]["mediaId"] == 99

    @pytest.mark.asyncio
    async def test_request_media_no_exact_match(self, tools, mock_client):
        """Test request_media returns error when no exact TMDb match."""
        search_result = {
            "results": [
                {
                    "id": 1,
                    "mediaType": "movie",
                    "mediaInfo": {"tmdbId": 99999},  # Different ID
                },
            ]
        }
        mock_client.get.return_value = search_result

        result = await tools.request_media(
            tmdb_id=12345, title="Test Movie", media_type="movie"
        )
        assert "error" in result
        assert "tmdbId=12345" in result["error"]

    @pytest.mark.asyncio
    async def test_request_media_no_results(self, tools, mock_client):
        """Test request_media with empty search results."""
        mock_client.get.return_value = {"results": []}

        result = await tools.request_media(
            tmdb_id=12345, title="Unknown Movie", media_type="movie"
        )
        assert "error" in result
        assert "Search returned 0 results" in result["error"]

    @pytest.mark.asyncio
    async def test_request_media_with_media_id_direct(self, tools, mock_client):
        """Test request_media bypasses search when media_id is provided."""
        mock_client.post.return_value = {"id": 1, "status": "PENDING"}

        await tools.request_media(
            tmdb_id=12345, title="Test", media_type="movie", media_id=777
        )
        # POST should use the provided media_id directly
        post_call = mock_client.post.call_args
        assert post_call[0][1]["mediaId"] == 777

    @pytest.mark.asyncio
    async def test_request_media_tv_with_seasons(self, tools, mock_client):
        """Test request_media for TV with seasons parameter."""
        search_result = {
            "results": [
                {
                    "id": 88,
                    "mediaType": "tv",
                    "mediaInfo": {"tmdbId": 54321},
                },
            ]
        }
        mock_client.get.return_value = search_result
        mock_client.post.return_value = {"id": 2, "status": "PENDING"}

        await tools.request_media(
            tmdb_id=54321, title="Test Show", media_type="tv", seasons=[1, 2]
        )
        post_call = mock_client.post.call_args
        assert post_call[0][1]["seasons"] == [1, 2]

    @pytest.mark.asyncio
    async def test_request_media_tv_seasons_all(self, tools, mock_client):
        """Test request_media for TV with seasons='all'."""
        search_result = {
            "results": [
                {
                    "id": 88,
                    "mediaType": "tv",
                    "mediaInfo": {"tmdbId": 54321},
                },
            ]
        }
        mock_client.get.return_value = search_result

        await tools.request_media(
            tmdb_id=54321, title="Test Show", media_type="tv", seasons="all"
        )
        post_call = mock_client.post.call_args
        assert post_call[0][1]["seasons"] == "all"

    @pytest.mark.asyncio
    async def test_request_media_tv_seasons_json_string_single(self, tools, mock_client):
        """BUG-58: seasons as JSON string '[1]' should be parsed to [1]."""
        search_result = {
            "results": [
                {
                    "id": 88,
                    "mediaType": "tv",
                    "mediaInfo": {"tmdbId": 54321},
                },
            ]
        }
        mock_client.get.return_value = search_result
        mock_client.post.return_value = {"id": 2, "status": "PENDING"}

        await tools.request_media(
            tmdb_id=54321, title="Test Show", media_type="tv", seasons="[1]"
        )
        post_call = mock_client.post.call_args
        assert post_call[0][1]["seasons"] == [1]

    @pytest.mark.asyncio
    async def test_request_media_tv_seasons_json_string_multiple(self, tools, mock_client):
        """BUG-58: seasons as JSON string '[1, 2, 3]' should be parsed to [1, 2, 3]."""
        search_result = {
            "results": [
                {
                    "id": 88,
                    "mediaType": "tv",
                    "mediaInfo": {"tmdbId": 54321},
                },
            ]
        }
        mock_client.get.return_value = search_result

        await tools.request_media(
            tmdb_id=54321, title="Test Show", media_type="tv", seasons="[1, 2, 3]"
        )
        post_call = mock_client.post.call_args
        assert post_call[0][1]["seasons"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_request_media_tv_seasons_invalid_json_passthrough(self, tools, mock_client):
        """BUG-58: non-parseable string seasons (not 'all', not JSON) pass through as-is."""
        search_result = {
            "results": [
                {
                    "id": 88,
                    "mediaType": "tv",
                    "mediaInfo": {"tmdbId": 54321},
                },
            ]
        }
        mock_client.get.return_value = search_result

        await tools.request_media(
            tmdb_id=54321, title="Test Show", media_type="tv", seasons="not-json"
        )
        post_call = mock_client.post.call_args
        assert post_call[0][1]["seasons"] == "not-json"

    @pytest.mark.asyncio
    async def test_request_media_ignore_quota(self, tools, mock_client):
        """Test request_media with ignore_quota=True."""
        search_result = {
            "results": [
                {
                    "id": 99,
                    "mediaType": "movie",
                    "mediaInfo": {"tmdbId": 12345},
                },
            ]
        }
        mock_client.get.return_value = search_result

        await tools.request_media(
            tmdb_id=12345, title="Test", media_type="movie", ignore_quota=True
        )
        post_call = mock_client.post.call_args
        assert post_call[0][1]["ignoreQuota"] is True

    @pytest.mark.asyncio
    async def test_request_media_quality_and_folder(self, tools, mock_client):
        """Test request_media with quality_profile_id and root_folder."""
        search_result = {
            "results": [
                {
                    "id": 99,
                    "mediaType": "movie",
                    "mediaInfo": {"tmdbId": 12345},
                },
            ]
        }
        mock_client.get.return_value = search_result

        await tools.request_media(
            tmdb_id=12345,
            title="Test",
            media_type="movie",
            quality_profile_id=5,
            root_folder="/data/movies",
        )
        post_call = mock_client.post.call_args
        assert post_call[0][1]["profileId"] == 5
        assert post_call[0][1]["rootFolder"] == "/data/movies"

    @pytest.mark.asyncio
    async def test_request_media_no_fallback_to_arbitrary(self, tools, mock_client):
        """BUG-3 regression: ensure no fallback to first matching mediaType.

        The old code would pick the first result with a matching mediaType
        even if the TMDb ID didn't match. This test verifies that behavior
        is gone — if no exact TMDb match, return error.
        """
        search_result = {
            "results": [
                {
                    "id": 10,
                    "mediaType": "movie",
                    "mediaInfo": {"tmdbId": 111},  # Not matching
                },
                {
                    "id": 20,
                    "mediaType": "movie",
                    "mediaInfo": {"tmdbId": 222},  # Not matching either
                },
            ]
        }
        mock_client.get.return_value = search_result

        result = await tools.request_media(
            tmdb_id=999, title="Any Movie", media_type="movie"
        )
        assert "error" in result
        # Should NOT contain a success with id=10 or id=20
        assert result.get("id") is None

    @pytest.mark.asyncio
    async def test_request_media_type_mismatch_no_match(self, tools, mock_client):
        """Test that TV results don't match movie search."""
        search_result = {
            "results": [
                {
                    "id": 50,
                    "mediaType": "tv",  # Wrong type
                    "mediaInfo": {"tmdbId": 12345},  # Correct ID but wrong type
                },
            ]
        }
        mock_client.get.return_value = search_result

        result = await tools.request_media(
            tmdb_id=12345, title="Test", media_type="movie"
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_request_media_tv_no_media_info(self, tools, mock_client):
        """BUG-58: TV show not yet in Seerr library has no mediaInfo.

        When media is not in Seerr's library the search result lacks
        ``mediaInfo`` — the code must fall back to using ``entry["id"]``
        (which equals the TMDB ID) for matching.
        """
        search_result = {
            "results": [
                {
                    "id": 42009,
                    "mediaType": "tv",
                    "name": "Черное зеркало",
                    # No mediaInfo — not yet in Seerr library
                },
                {
                    "id": 99999,
                    "mediaType": "movie",
                    "mediaInfo": {"tmdbId": 99999},
                },
            ]
        }
        mock_client.get.return_value = search_result
        mock_client.post.return_value = {"id": 1, "status": "PENDING"}

        result = await tools.request_media(
            tmdb_id=42009, title="Black Mirror", media_type="tv"
        )
        assert result["status"] == "PENDING"
        # Should use entry["id"] (42009) as mediaId
        post_call = mock_client.post.call_args
        assert post_call[0][1]["mediaId"] == 42009
        assert post_call[0][1]["mediaType"] == "tv"

    @pytest.mark.asyncio
    async def test_request_media_no_media_info_no_match(self, tools, mock_client):
        """BUG-58 regression: fallback to entry['id'] still requires exact match."""
        search_result = {
            "results": [
                {
                    "id": 11111,
                    "mediaType": "tv",
                    # No mediaInfo — id=11111 acts as TMDB ID, doesn't match
                },
            ]
        }
        mock_client.get.return_value = search_result

        result = await tools.request_media(
            tmdb_id=42009, title="Unknown Show", media_type="tv"
        )
        assert "error" in result
        assert "tmdbId=42009" in result["error"]

    # ── approve ───────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_approve(self, tools, mock_client):
        """Test approve with no body."""
        mock_client.post.return_value = {"id": 1, "status": "APPROVED"}

        result = await tools.approve(42)
        assert result["status"] == "APPROVED"
        mock_client.post.assert_called_once_with(
            "/request/42/approve", None
        )

    @pytest.mark.asyncio
    async def test_approve_no_is_4k_param(self, tools, mock_client):
        """BUG-6 regression: approve should not accept is_4k parameter."""
        # The method signature should only have request_id
        import inspect
        sig = inspect.signature(tools.approve)
        params = list(sig.parameters.keys())
        assert params == ["request_id"], f"Expected ['request_id'], got {params}"

    # ── reject ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_reject(self, tools, mock_client):
        """Test reject with no body."""
        mock_client.post.return_value = {"id": 1, "status": "DECLINED"}

        result = await tools.reject(42)
        assert result["status"] == "DECLINED"
        mock_client.post.assert_called_once_with(
            "/request/42/decline", None
        )

    # ── get_request ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_request(self, tools, mock_client):
        """Test getting a single request."""
        expected = {
            "id": 5,
            "status": "PENDING",
            "media": {"title": "Test Movie"},
        }
        mock_client.get.return_value = expected

        result = await tools.get_request(5)
        assert result["id"] == 5
        mock_client.get.assert_called_once_with("/request/5")

    # ── Error handling ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_search_error_propagation(self, tools, mock_client):
        """Test that search errors are propagated."""
        mock_client.get.side_effect = Exception("API down")

        with pytest.raises(Exception, match="API down"):
            await tools.search("Query")

    @pytest.mark.asyncio
    async def test_get_requests_error_propagation(self, tools, mock_client):
        """Test that get_requests errors are propagated."""
        mock_client.get.side_effect = Exception("Server error")

        with pytest.raises(Exception, match="Server error"):
            await tools.get_requests()
