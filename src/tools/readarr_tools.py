"""Readarr tools for MCP ARR Stack."""

import logging
from typing import Any

from src.client import BaseARRClient

logger = logging.getLogger(__name__)


class ReadarrTools:
    """Tools for interacting with Readarr API."""

    def __init__(self, client: BaseARRClient):
        self.client = client

    async def search_author(self, term: str) -> list[dict[str, Any]]:
        """Search for authors/books by term via external metadata providers.

        Uses the ``/author/lookup`` endpoint which searches providers
        such as Goodreads and MusicBrainz.

        Args:
            term: Search query for author or book title.

        Returns:
            List of matching authors with id, title, metadata, etc.
        """
        try:
            results = await self.client.get("/author/lookup", {"term": term})
            logger.info(f"Readarr search for '{term}': found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching author in Readarr: {e}")
            raise

    async def get_author(self, author_id: int | None = None, author_name: str | None = None) -> dict | list[dict]:
        """Get author details or list all authors.

        Args:
            author_id: Specific author ID.
            author_name: Filter by author name.

        Returns:
            Single author dict or list of authors.
        """
        try:
            if author_id:
                return await self.client.get(f"/author/{author_id}")
            params = {"authorName": author_name} if author_name else None
            return await self.client.get("/author", params=params)
        except Exception as e:
            logger.error(f"Error getting authors from Readarr: {e}")
            raise

    async def add_author(
        self,
        foreign_id: str,
        title: str,
        root_path: str,
        quality_profile_id: int = 1,
        monitored: bool = True,
        search_for_missing: bool = False,
    ) -> dict:
        """Add a new author to Readarr.

        Args:
            foreign_id: MusicBrainz artist ID.
            title: Author name.
            root_path: Root folder path on disk.
            quality_profile_id: Quality profile ID (default: 1).
            monitored: Monitor new books (default: True).
            search_for_missing: Search for missing books (default: False).

        Returns:
            Created author data.
        """
        try:
            data = {
                "foreignAuthorId": foreign_id,
                "title": title,
                "rootFolderPath": root_path,
                "qualityProfileId": quality_profile_id,
                "monitored": monitored,
            }

            result = await self.client.post("/author", data)

            if search_for_missing:
                author_id = result.get("id")
                if author_id:
                    await self.client.post("/command", {"name": "SearchMissing", "authorId": author_id})

            logger.info(f"Added author '{title}' to Readarr")
            return result
        except Exception as e:
            logger.error(f"Error adding author '{title}' to Readarr: {e}")
            raise

    async def delete_author(self, author_id: int, delete_files: bool = False) -> dict:
        """Delete an author from Readarr.

        Args:
            author_id: Author ID to delete.
            delete_files: Also delete files from disk.

        Returns:
            Status of the deletion.
        """
        try:
            params = {"deleteFiles": delete_files} if delete_files else None
            status_code = await self.client.delete("/author", author_id, params=params)
            return {
                "success": 200 <= status_code < 300,
                "status_code": status_code,
                "message": f"Author {author_id} deleted successfully" if status_code == 200 else f"Delete returned status {status_code}",
            }
        except Exception as e:
            logger.error(f"Error deleting author {author_id}: {e}")
            raise
