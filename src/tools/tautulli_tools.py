"""Tautulli tools for MCP ARR Stack."""

import logging
from typing import Any

from src.client import TautulliClient

logger = logging.getLogger(__name__)


class TautulliTools:
    """Tools for interacting with Tautulli API."""

    def __init__(self, client: TautulliClient):
        self.client = client

    async def get_activity(self) -> dict:
        """Get current Plex activity.

        Returns:
            Dict with 'active_connections' (list of now playing)
            and 'total_sessions'.
        """
        try:
            result = await self.client.get("get_activity", {"count": 10})
            logger.info(f"Got Tautulli activity: {result.get('total_sessions', 0)} sessions")
            return result
        except Exception as e:
            logger.error(f"Error getting Tautulli activity: {e}")
            raise

    async def get_library_stats(self) -> list[dict]:
        """Get library list with counts.

        Returns:
            List of library sections with section_id, section_name, count, etc.
        """
        try:
            result = await self.client.get("get_libraries")
            data = result if isinstance(result, list) else result.get("data", [])
            logger.info(f"Got {len(data)} libraries from Tautulli")
            return data
        except Exception as e:
            logger.error(f"Error getting library stats: {e}")
            raise

    async def get_history(
        self,
        grouping: int = 0,
        length: int = 25,
        order_column: str = "date",
        order_dir: str = "desc",
    ) -> list[dict]:
        """Get watch history.

        Args:
            grouping: Group multi-episode watches, 0 or 1 (default: 0).
            length: Max results (default: 25).
            order_column: Sort field (default: 'date').
            order_dir: Sort direction 'asc' or 'desc' (default: 'desc').

        Returns:
            List of watched items with user, title, date, duration, etc.
        """
        try:
            result = await self.client.get(
                "get_history",
                {
                    "grouping": grouping,
                    "length": length,
                    "order_column": order_column,
                    "order_dir": order_dir,
                },
            )
            data = result.get("data", []) if isinstance(result, dict) else result
            logger.info(f"Got {len(data)} history entries from Tautulli")
            return data
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            raise

    async def get_user_stats(self, user_id: str | None = None) -> dict:
        """Get user watch time statistics.

        Args:
            user_id: Specific user ID.

        Returns:
            User stats with watch time over different periods (1, 7, 30 days, all time).
        """
        try:
            if not user_id:
                raise ValueError("user_id is required for get_user_stats")

            result = await self.client.get(
                "get_user_watch_time_stats", {"user_id": user_id}
            )
            data = result if isinstance(result, list) else result.get("data", [])
            logger.info(f"Got user watch time stats for user {user_id}")
            return {"user_id": user_id, "stats": data}
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            raise

    async def get_recently_added(self, media_type: str | None = None, count: int = 25) -> list[dict]:
        """Get recently added media to Plex library.

        Args:
            media_type: Filter by 'movie', 'show', or 'artist', or None for all (default: None).
            count: Number of items to return (default: 25).

        Returns:
            List of recently added items.
        """
        try:
            params: dict[str, Any] = {"count": str(count)}
            if media_type:
                params["media_type"] = media_type

            result = await self.client.get("get_recently_added", params)
            data = result.get("recently_added", []) if isinstance(result, dict) else result
            logger.info(f"Got {len(data)} recently added items")
            return data
        except Exception as e:
            logger.error(f"Error getting recently added: {e}")
            raise

    async def get_streaming_users(self) -> list[dict]:
        """Get users currently streaming content.

        Returns:
            List of active streaming sessions with user, title, progress, etc.
        """
        try:
            activity = await self.get_activity()
            active = activity.get("active_connections", [])
            logger.info(f"Got {len(active)} active streaming users")
            return active
        except Exception as e:
            logger.error(f"Error getting streaming users: {e}")
            raise
