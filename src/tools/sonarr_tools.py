"""Sonarr tools for MCP ARR Stack."""

import logging
from typing import Any

from src.client import BaseARRClient

logger = logging.getLogger(__name__)


class SonarrTools:
    """Tools for interacting with Sonarr API."""

    def __init__(self, client: BaseARRClient):
        self.client = client

    async def search_series(self, title: str) -> list[dict[str, Any]]:
        """Search for TV series by title.

        Searches Sonarr's TV series database (TMDB/ZAP2IT).

        Args:
            title: Series title to search for.

        Returns:
            List of matching series with id, title, year, tvdbId, etc.
        """
        try:
            results = await self.client.get("/series/lookup", {"term": title})
            # Sort by relevance (results already sorted by Sonarr)
            logger.info(f"Sonarr search for '{title}': found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching series '{title}': {e}")
            raise

    async def get_series(self, series_id: int | None = None, title: str | None = None) -> dict | list[dict]:
        """Get series details or list all series.

        Args:
            series_id: Specific series ID to fetch.
            title: Filter by title.

        Returns:
            Single series dict if series_id provided, else list of all series.
        """
        try:
            if series_id:
                result = await self.client.get(f"/series/{series_id}")
                logger.info(f"Got series details for ID {series_id}: {result.get('title', 'N/A')}")
                return result
            else:
                params = {"title": title} if title else None
                results = await self.client.get("/series", params=params)
                logger.info(f"Got {len(results)} series from Sonarr")
                return results
        except Exception as e:
            logger.error(f"Error getting series: {e}")
            raise

    async def get_episodes(
        self,
        series_id: int,
        episode_ids: list[int] | None = None,
        season_number: int | None = None,
    ) -> list[dict]:
        """Get episode details for a series.

        Args:
            series_id: Series ID to get episodes for.
            episode_ids: Specific episode IDs (optional).
            season_number: Filter by season number (optional).

        Returns:
            List of episode dicts with season/episode numbers, titles, status.
        """
        try:
            params = {"seriesId": series_id}
            if episode_ids:
                params["episodeIds"] = ",".join(str(eid) for eid in episode_ids)
            if season_number is not None:
                params["seasonNumber"] = season_number

            results = await self.client.get("/episode", params=params)
            logger.info(f"Got {len(results)} episodes for series {series_id}")
            return results
        except Exception as e:
            logger.error(f"Error getting episodes for series {series_id}: {e}")
            raise

    async def add_series(
        self,
        tvdb_id: int,
        title: str,
        root_path: str,
        language_profile_id: int = 1,
        quality_profile_id: int = 1,
        season_folder: bool = True,
        monitored: bool = True,
        search_for_missing: bool = False,
        series_type: str = "standard",
        tags: list[int] | None = None,
    ) -> dict:
        """Add a new series to Sonarr.

        Args:
            tvdb_id: TVDB ID for the series.
            title: Series title.
            root_path: Root folder path on disk.
            language_profile_id: Language profile ID (default: 1).
            quality_profile_id: Quality profile ID (default: 1).
            season_folder: Enable season folders (default: True).
            monitored: Monitor all episodes (default: True).
            search_for_missing: Search for missing episodes (default: False).
            series_type: Series type - 'standard', 'daily', 'anime' (default: 'standard').
            tags: List of tag IDs (optional).

        Returns:
            Created series data.
        """
        try:
            data = {
                "tvdbId": tvdb_id,
                "title": title,
                "rootFolderPath": root_path,
                "languageProfileId": language_profile_id,
                "qualityProfileId": quality_profile_id,
                "seasonFolders": season_folder,
                "monitored": monitored,
                "addOptions": {
                    "searchForMissingEpisodes": search_for_missing,
                },
                "seriesType": series_type,
            }
            if tags:
                data["tags"] = tags

            result = await self.client.post("/series", {"monitorNewItems": monitored, **data})
            logger.info(f"Added series '{title}' (tvdb:{tvdb_id}) to Sonarr")
            return result
        except Exception as e:
            logger.error(f"Error adding series '{title}': {e}")
            raise

    async def delete_series(self, series_id: int, delete_files: bool = False, remove_from_client: bool = True) -> dict:
        """Delete a series from Sonarr.

        Args:
            series_id: Series ID to delete.
            delete_files: Also delete files from disk.
            remove_from_client: Remove from download client.

        Returns:
            Status of the deletion.
        """
        try:
            params = {
                "deleteFiles": delete_files,
                "addImportListExclusion": True,
            }
            status_code = await self.client.delete("/series", series_id, params=params)
            logger.info(f"Deleted series {series_id} (status={status_code})")
            return {
                "success": 200 <= status_code < 300,
                "status_code": status_code,
                "message": f"Series {series_id} deleted successfully" if status_code == 200 else f"Delete returned status {status_code}",
            }
        except Exception as e:
            logger.error(f"Error deleting series {series_id}: {e}")
            raise

    async def get_quality_profile(self, profile_id: int | None = None) -> dict | list[dict]:
        """Get quality profiles.

        Args:
            profile_id: Specific profile ID (optional).

        Returns:
            Single profile or list of all profiles.
        """
        try:
            if profile_id:
                return await self.client.get(f"/qualityprofile/{profile_id}")
            return await self.client.get("/qualityprofile")
        except Exception as e:
            logger.error(f"Error getting quality profiles: {e}")
            raise

    async def get_root_folder(self) -> list[dict]:
        """Get available root folders.

        Returns:
            List of root folder paths.
        """
        try:
            return await self.client.get("/rootfolder")
        except Exception as e:
            logger.error(f"Error getting root folders: {e}")
            raise

    async def get_series_status(self, series_id: int) -> dict:
        """Get detailed status of a series including episode progress.

        Args:
            series_id: Series ID.

        Returns:
            Series status with episode counts (aired, monitored, missing, etc.).
        """
        try:
            series = await self.get_series(series_id=series_id)
            episodes = await self.get_episodes(series_id=series_id)

            total = len(episodes)
            monitored = sum(1 for e in episodes if e.get("monitored"))
            aired = sum(1 for e in episodes if e.get("aired"))
            has_file = sum(1 for e in episodes if e.get("hasFile"))
            missing = sum(1 for e in episodes if not e.get("aired") and e.get("monitored"))

            return {
                "series": {
                    "id": series.get("id"),
                    "title": series.get("title"),
                    "year": series.get("year"),
                    "status": series.get("status"),
                    "seasonCount": series.get("seasonCount"),
                },
                "episodes": {
                    "total": total,
                    "monitored": monitored,
                    "aired": aired,
                    "hasFile": has_file,
                    "missing": missing,
                    "downloaded": has_file,
                },
            }
        except Exception as e:
            logger.error(f"Error getting series status for {series_id}: {e}")
            raise
