"""Plex tools for MCP ARR Stack."""

import logging
from typing import Any

from src.client import PlexClient

logger = logging.getLogger(__name__)


class PlexTools:
    """Tools for interacting with Plex Media Server."""

    # Mapping from human-readable type names to Plex API integer type codes
    TYPE_MAP: dict[str, int] = {
        "movie": 1,
        "show": 2,
        "season": 3,
        "episode": 4,
        "artist": 8,
        "album": 9,
        "track": 10,
    }

    def __init__(self, client: PlexClient):
        self.client = client

    async def search(self, query: str) -> dict[str, Any]:
        """Search Plex library for content.

        Args:
            query: Search query string.

        Returns:
            Search results with matches across all library sections.
        """
        try:
            result = await self.client.get("/search", {"query": query})
            logger.info(f"Plex search for '{query}': {len(result.get('Metadata', []))} results")
            return result
        except Exception as e:
            logger.error(f"Error searching Plex for '{query}': {e}")
            raise

    async def library_sections(self) -> list[dict]:
        """Get all library sections.

        Returns:
            List of sections with key, title, type (movie, show, etc.).
        """
        try:
            result = await self.client.get("/library/sections")
            sections = result.get("MediaContainer", {}).get("Directory", [])
            logger.info(f"Got {len(sections)} Plex library sections")
            return sections
        except Exception as e:
            logger.error(f"Error getting library sections: {e}")
            raise

    async def recently_added(self, section_type: str | None = None, limit: int = 20) -> list[dict]:
        """Get recently added content to Plex.

        Note: Plex API does not support filtering recentlyAdded by type
        via URL. Filtering by section_type is performed client-side.

        Args:
            section_type: Filter by 'movie' or 'show' (default: None for all).
            limit: Max results (default: 20).

        Returns:
            List of recently added items.
        """
        try:
            result = await self.client.get("/library/recentlyAdded")
            items = result.get("MediaContainer", {}).get("Metadata", [])

            # Client-side filtering by type since Plex API doesn't support it
            if section_type:
                items = [
                    item for item in items
                    if item.get("type") == section_type
                ]

            logger.info(f"Got {len(items)} recently added Plex items")
            return items[:limit]
        except Exception as e:
            logger.error(f"Error getting recently added from Plex: {e}")
            raise

    async def playlists(self) -> list[dict]:
        """Get all playlists.

        Returns:
            List of playlist objects.
        """
        try:
            result = await self.client.get("/playlists")
            playlists = result.get("MediaContainer", {}).get("Directory", [])
            logger.info(f"Got {len(playlists)} Plex playlists")
            return playlists
        except Exception as e:
            logger.error(f"Error getting playlists: {e}")
            raise

    async def library(self, section_key: int, section_type: str = "all", limit: int = 50) -> list[dict]:
        """Get items from a specific library section.

        Args:
            section_key: Section key (1=movies, 2=shows, etc.).
            section_type: 'movie', 'show', or 'all' (default: 'all').
            limit: Max results (default: 50).

        Returns:
            List of items in the library section.
        """
        try:
            endpoint = f"/library/sections/{section_key}/all"
            params = {"limit": limit}
            if section_type and section_type != "all":
                type_code = self.TYPE_MAP.get(section_type)
                if type_code is not None:
                    params["type"] = type_code
            result = await self.client.get(endpoint, params=params)
            items = result.get("MediaContainer", {}).get("Metadata", [])
            logger.info(f"Got {len(items)} items from library section {section_key}")
            return items
        except Exception as e:
            logger.error(f"Error getting library items for section {section_key}: {e}")
            raise

    async def get_status(self) -> dict:
        """Get Plex server status.

        Returns:
            Server info including name, version, total libraries, etc.
        """
        try:
            result = await self.client.get("/")
            server_info = result.get("MediaContainer", {})

            sections = await self.library_sections()
            movie_count = 0
            show_count = 0
            for section in sections:
                if section.get("type") == "movie":
                    movie_count = section.get("size", 0)
                elif section.get("type") == "show":
                    show_count = section.get("size", 0)

            return {
                "name": server_info.get("title"),
                "version": server_info.get("version"),
                "platform": server_info.get("platform"),
                "total_libraries": len(sections),
                "movie_count": movie_count,
                "show_count": show_count,
            }
        except Exception as e:
            logger.error(f"Error getting Plex status: {e}")
            raise
