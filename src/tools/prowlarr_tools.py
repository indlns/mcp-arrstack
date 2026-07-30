"""Prowlarr tools for MCP ARR Stack."""

import logging
from typing import Any

try:
    from src.client import BaseARRClient
except ImportError:
    from client import BaseARRClient

logger = logging.getLogger(__name__)


class ProwlarrTools:
    """Tools for interacting with Prowlarr API."""

    def __init__(self, client: BaseARRClient):
        self.client = client

    async def search(self, query: str, type: str = "search") -> list[dict[str, Any]]:
        """Search across all indexers.

        Args:
            query: Search query.
            type: Search type - 'search', 'tvsearch', 'moviesearch',
                'booksearch', 'audiosearch' (default: 'search').

        Returns:
            List of search results with title, indexer, size, seeders, etc.
        """
        try:
            params = {"query": query}
            if type and type != "search":
                params["type"] = type
            results = await self.client.get("/search", params=params)
            logger.info(f"Prowlarr search for '{query}': found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching Prowlarr for '{query}': {e}")
            raise

    async def get_indexers(self, enabled_only: bool = False) -> list[dict]:
        """Get list of indexers.

        Args:
            enabled_only: Only return enabled indexers.

        Returns:
            List of indexer configurations and status.
        """
        try:
            result = await self.client.get("/indexer")
            if enabled_only:
                result = [i for i in result if i.get("enable")]
            logger.info(f"Got {len(result)} indexers from Prowlarr")
            return result
        except Exception as e:
            logger.error(f"Error getting indexers: {e}")
            raise

    async def test_indexers(self) -> dict:
        """Test connections to all configured indexers at once.

        Note: Prowlarr API does not support per-indexer testing by ID.
        This calls the /indexer/testall endpoint to test all indexers.

        Returns:
            Test results with success status and messages for each indexer.
        """
        try:
            result = await self.client.post("/indexer/testall")
            logger.info(
                f"Tested all indexers: "
                f"{len(result.get('results', []))} indexers tested"
            )
            return result
        except Exception as e:
            logger.error(f"Error testing indexers: {e}")
            raise

    async def get_history(self, limit: int = 100) -> list[dict]:
        """Get download history.

        Args:
            limit: Maximum number of results (default: 100).

        Returns:
            List of recent download history entries.
        """
        try:
            result = await self.client.get("/history", {"limit": limit})
            logger.info(f"Got {len(result)} history entries from Prowlarr")
            return result
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            raise

    async def get_status(self) -> dict:
        """Get Prowlarr system status.

        Returns:
            System status including connection status, version, etc.
        """
        try:
            status = await self.client.get("/system/status")
            indexers = await self.get_indexers()
            enabled_count = sum(1 for i in indexers if i.get("enable"))
            total_count = len(indexers)

            return {
                "version": status.get("version"),
                "buildInfo": status.get("buildInfo"),
                "connectionStatus": status.get("connectionStatus"),
                "isDebug": status.get("isDebug"),
                "isLogging": status.get("isLogging"),
                "indexers": {
                    "total": total_count,
                    "enabled": enabled_count,
                    "disabled": total_count - enabled_count,
                },
            }
        except Exception as e:
            logger.error(f"Error getting Prowlarr status: {e}")
            raise
