"""Seerr tools for MCP ARR Stack."""

import json
import logging
from typing import Any

from src.client import SeerrClient

logger = logging.getLogger(__name__)


class SeerrTools:
    """Tools for interacting with Seerr API."""

    def __init__(self, client: SeerrClient):
        self.client = client

    async def search(self, query: str, page: int = 1, language: str | None = None) -> dict[str, Any]:
        """Search for media by query string.

        Searches across movies and TV shows via TMDB/TVDB.

        Args:
            query: Search query string.
            page: Page number (default: 1).
            language: Language code (e.g. 'en', optional).

        Returns:
            Dict with 'movies' and 'tv' lists of results.
        """
        try:
            params: dict[str, Any] = {"query": query}
            if page > 1:
                params["page"] = page
            if language is not None:
                params["language"] = language

            result = await self.client.get("/search", params)
            logger.info(f"Seerr search for '{query}': {result}")
            return result
        except Exception as e:
            logger.error(f"Error searching Seerr for '{query}': {e}")
            raise

    async def get_requests(
        self,
        take: int = 20,
        skip: int = 0,
        filter: str | None = None,
        sort: str = "added",
        sort_direction: str = "desc",
        requested_by: int | None = None,
        media_type: str | None = None,
    ) -> dict:
        """Get list of media requests in Seerr.

        Args:
            take: Number of results to return (default: 20).
            skip: Number of results to skip for pagination (default: 0).
            filter: Filter by status — 'all', 'approved', 'available',
                'pending', 'processing', 'unavailable', 'failed',
                'deleted', 'completed' (optional).
            sort: Sort field — 'added' or 'modified' (default: 'added').
            sort_direction: Sort order — 'asc' or 'desc' (default: 'desc').
            requested_by: Filter by user ID (optional).
            media_type: Filter by media type — 'movie', 'tv', or 'all' (optional).

        Returns:
            Dict with 'pageInfo' (containing 'page', 'pages', 'results')
            and 'results' list, matching the Seerr API response shape.
        """
        try:
            params: dict[str, Any] = {
                "take": take,
                "skip": skip,
            }
            if filter is not None:
                params["filter"] = filter
            if sort is not None:
                params["sort"] = sort
            if sort_direction is not None:
                params["sortDirection"] = sort_direction
            if requested_by is not None:
                params["requestedBy"] = requested_by
            if media_type is not None:
                params["mediaType"] = media_type

            result = await self.client.get("/request", params=params)
            logger.info(f"Got requests from Seerr (take={take}, skip={skip})")
            return result
        except Exception as e:
            logger.error(f"Error getting requests: {e}")
            raise

    async def request_media(
        self,
        tmdb_id: int,
        title: str,
        media_type: str = "movie",
        quality_profile_id: int | None = None,
        root_folder: str | None = None,
        ignore_quota: bool = False,
        seasons: list[int] | str | None = None,
        media_id: int | None = None,
    ) -> dict:
        """Request a movie or TV show in Seerr.

        Searches for the media by title in Seerr, matches by exact TMDb ID,
        and creates a request. The optional ``media_id`` parameter allows
        bypassing the search step entirely when the internal Seerr media ID
        is already known.

        For TV shows the ``seasons`` parameter can specify which seasons to
        request — either a list of season numbers (e.g. ``[1, 2]``) or the
        string ``"all"`` for every season.

        Args:
            tmdb_id: TMDb ID for the media.
            title: Title of the media (used for lookup).
            media_type: 'movie' or 'tv' (default: 'movie').
            quality_profile_id: Quality profile ID (optional).
            root_folder: Root folder path (optional).
            ignore_quota: Ignore quota limits (default: False).
            seasons: Season numbers to request for TV, or "all" (optional).
            media_id: Direct Seerr internal media ID — skips the search step
                when provided (optional).

        Returns:
            Created request object.

        Raises:
            ValueError: If no exact TMDb match is found.
        """
        try:
            media_id_found: int | None = media_id

            if media_id_found is None:
                # Look up the media entry in Seerr to get the internal mediaId.
                # The POST /request endpoint requires 'mediaId' (Seerr's DB ID),
                # not 'tmdbId'. Search by title and match TMDb ID from mediaInfo.
                search_result = await self.client.get(
                    "/search", {"query": title}
                )
                results = search_result.get("results", [])
                logger.debug(
                    f"Seerr search for '{title}' (tmdbId={tmdb_id}): "
                    f"returned {len(results)} results"
                )
                # Strict match: find exact tmdbId for the given mediaType.
                # For media already in Seerr's library, tmdbId lives in mediaInfo.
                # For media not yet added, mediaInfo is absent — fall back to
                # using entry["id"] which equals the external TMDB ID.
                for entry in results:
                    if entry.get("mediaType") != media_type:
                        continue

                    info = entry.get("mediaInfo")
                    if info and info.get("tmdbId") is not None:
                        entry_tmdb_id = info["tmdbId"]
                    else:
                        entry_tmdb_id = entry.get("id")

                    if entry_tmdb_id is not None and str(entry_tmdb_id) == str(tmdb_id):
                        media_id_found = entry["id"]
                        break

                if media_id_found is None:
                    return {
                        "error": f"Could not find media with tmdbId={tmdb_id} "
                                 f"type={media_type}. Search returned {len(results)} results. "
                                 "The media may not be in Seerr's database. "
                                 "Try using the 'media_id' parameter directly if you know the "
                                 "internal Seerr media ID.",
                    }

            # POST /request — required: mediaType (string), mediaId (number)
            data: dict = {
                "mediaType": media_type,
                "mediaId": media_id_found,
            }

            if quality_profile_id is not None:
                data["profileId"] = quality_profile_id
            if root_folder is not None:
                data["rootFolder"] = root_folder
            if ignore_quota:
                data["ignoreQuota"] = True
            if seasons is not None:
                if isinstance(seasons, str) and seasons != "all":
                    try:
                        parsed = json.loads(seasons)
                        if isinstance(parsed, list):
                            data["seasons"] = [int(s) for s in parsed]
                        else:
                            data["seasons"] = seasons
                    except (json.JSONDecodeError, ValueError, TypeError):
                        data["seasons"] = seasons
                else:
                    data["seasons"] = seasons

            result = await self.client.post("/request", data)
            logger.info(f"Requested '{title}' in Seerr (mediaId={media_id_found})")
            return result
        except Exception as e:
            logger.error(f"Error requesting '{title}' in Seerr: {e}")
            raise

    async def approve(self, request_id: int) -> dict:
        """Approve a pending request.

        Args:
            request_id: Request ID to approve.

        Returns:
            Updated request with approval status.
        """
        try:
            result = await self.client.post(f"/request/{request_id}/approve", None)
            logger.info(f"Approved request {request_id}")
            return result
        except Exception as e:
            logger.error(f"Error approving request {request_id}: {e}")
            raise

    async def reject(self, request_id: int) -> dict:
        """Reject a pending request.

        Args:
            request_id: Request ID to reject.

        Returns:
            Updated request with rejection status.
        """
        try:
            result = await self.client.post(f"/request/{request_id}/decline", None)
            logger.info(f"Rejected request {request_id}")
            return result
        except Exception as e:
            logger.error(f"Error rejecting request {request_id}: {e}")
            raise

    async def get_request(self, request_id: int) -> dict:
        """Get details of a specific request.

        Args:
            request_id: Request ID.

        Returns:
            Full request details with media info and status.
        """
        try:
            return await self.client.get(f"/request/{request_id}")
        except Exception as e:
            logger.error(f"Error getting request {request_id}: {e}")
            raise
