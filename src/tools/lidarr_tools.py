"""Lidarr tools for MCP ARR Stack."""

import logging
from typing import Any

from src.client import BaseARRClient

logger = logging.getLogger(__name__)


class LidarrTools:
    """Tools for interacting with Lidarr API."""

    def __init__(self, client: BaseARRClient):
        self.client = client

    async def search_artist(self, term: str) -> list[dict[str, Any]]:
        """Search for artists/albums by term.

        Args:
            term: Search query for artist or album name.

        Returns:
            List of matching artists with id, title, metalarchivesId, etc.
        """
        try:
            results = await self.client.get("/artist/lookup", {"term": term})
            logger.info(f"Lidarr search for '{term}': found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching artist in Lidarr: {e}")
            raise

    async def get_artist(self, artist_id: int | None = None, artist_name: str | None = None) -> dict | list[dict]:
        """Get artist details or list all artists.

        Args:
            artist_id: Specific artist ID.
            artist_name: Filter by artist name.

        Returns:
            Single artist dict or list of artists.
        """
        try:
            if artist_id:
                return await self.client.get(f"/artist/{artist_id}")
            params = {"artistName": artist_name} if artist_name else None
            return await self.client.get("/artist", params=params)
        except Exception as e:
            logger.error(f"Error getting artists from Lidarr: {e}")
            raise

    async def add_artist(
        self,
        musicbrainz_id: str,
        title: str,
        root_path: str,
        quality_profile_id: int = 1,
        monitored: bool = True,
        search_for_missing: bool = False,
    ) -> dict:
        """Add a new artist to Lidarr.

        Args:
            musicbrainz_id: MusicBrainz artist ID.
            title: Artist name.
            root_path: Root folder path on disk.
            quality_profile_id: Quality profile ID (default: 1).
            monitored: Monitor new albums (default: True).
            search_for_missing: Search for missing albums (default: False).

        Returns:
            Created artist data.
        """
        try:
            data = {
                "musicBrainzArtistId": musicbrainz_id,
                "title": title,
                "rootFolderPath": root_path,
                "qualityProfileId": quality_profile_id,
                "monitored": monitored,
            }

            result = await self.client.post("/artist", data)

            if search_for_missing:
                artist_id = result.get("id")
                if artist_id:
                    await self.client.post("/command", {"name": "ArtistSearch", "artistId": artist_id})

            logger.info(f"Added artist '{title}' to Lidarr")
            return result
        except Exception as e:
            logger.error(f"Error adding artist '{title}' to Lidarr: {e}")
            raise

    async def delete_artist(self, artist_id: int, delete_files: bool = False) -> dict:
        """Delete an artist from Lidarr.

        Args:
            artist_id: Artist ID to delete.
            delete_files: Also delete files from disk.

        Returns:
            Status of the deletion.
        """
        try:
            params = {"deleteFiles": delete_files} if delete_files else None
            status_code = await self.client.delete("/artist", artist_id, params=params)
            return {
                "success": 200 <= status_code < 300,
                "status_code": status_code,
                "message": f"Artist {artist_id} deleted successfully" if status_code == 200 else f"Delete returned status {status_code}",
            }
        except Exception as e:
            logger.error(f"Error deleting artist {artist_id}: {e}")
            raise
