"""Radarr tools for MCP ARR Stack."""

import logging
from typing import Any

from src.client import BaseARRClient

logger = logging.getLogger(__name__)


class RadarrTools:
    """Tools for interacting with Radarr API."""

    def __init__(self, client: BaseARRClient):
        self.client = client

    async def search_movie(self, title: str) -> list[dict[str, Any]]:
        """Search for movies by title.

        Searches Radarr's movie database (TMDB/IMDb).

        Args:
            title: Movie title to search for.

        Returns:
            List of matching movies with id, title, year, tmdbId, etc.
        """
        try:
            results = await self.client.get("/movie/lookup", {"term": title})
            logger.info(f"Radarr search for '{title}': found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching movie '{title}': {e}")
            raise

    async def get_movies(self, movie_id: int | None = None, title: str | None = None) -> dict | list[dict]:
        """Get movie details or list all movies.

        Args:
            movie_id: Specific movie ID to fetch.
            title: Filter by title.

        Returns:
            Single movie dict if movie_id provided, else list of all movies.
        """
        try:
            if movie_id:
                result = await self.client.get(f"/movie/{movie_id}")
                logger.info(f"Got movie details for ID {movie_id}: {result.get('title', 'N/A')}")
                return result
            else:
                params = {"title": title} if title else None
                results = await self.client.get("/movie", params=params)
                logger.info(f"Got {len(results)} movies from Radarr")
                return results
        except Exception as e:
            logger.error(f"Error getting movies: {e}")
            raise

    async def add_movie(
        self,
        tmdb_id: int,
        title: str,
        root_path: str,
        quality_profile_id: int = 1,
        monitored: bool = True,
        search_for_movie: bool = False,
        minimum_availability: str = "released",
        tags: list[int] | None = None,
    ) -> dict:
        """Add a new movie to Radarr.

        Args:
            tmdb_id: TMDb ID for the movie.
            title: Movie title.
            root_path: Root folder path on disk.
            quality_profile_id: Quality profile ID (default: 1).
            monitored: Monitor the movie (default: True).
            search_for_movie: Search for the movie immediately (default: False).
            minimum_availability: Minimum availability level (default: 'released').
            tags: List of tag IDs (optional).

        Returns:
            Created movie data.
        """
        try:
            data = {
                "tmdbId": tmdb_id,
                "title": title,
                "rootFolderPath": root_path,
                "qualityProfileId": quality_profile_id,
                "monitored": monitored,
                "minimumAvailability": minimum_availability,
            }

            result = await self.client.post("/movie", {"monitored": monitored, **data})

            if search_for_movie:
                movie_id = result.get("id")
                if movie_id:
                    await self.client.post("/command", {"name": "MoviesSearch", "movieIds": [movie_id]})
                    logger.info(f"Triggered search for movie '{title}'")

            logger.info(f"Added movie '{title}' (tmdb:{tmdb_id}) to Radarr")
            return result
        except Exception as e:
            logger.error(f"Error adding movie '{title}': {e}")
            raise

    async def delete_movie(self, movie_id: int, delete_files: bool = False) -> dict:
        """Delete a movie from Radarr.

        Args:
            movie_id: Movie ID to delete.
            delete_files: Also delete files from disk.

        Returns:
            Status of the deletion.
        """
        try:
            params = {"deleteFiles": delete_files} if delete_files else None
            status_code = await self.client.delete("/movie", movie_id, params=params)
            logger.info(f"Deleted movie {movie_id} (status={status_code})")
            return {
                "success": 200 <= status_code < 300,
                "status_code": status_code,
                "message": f"Movie {movie_id} deleted successfully" if status_code == 200 else f"Delete returned status {status_code}",
            }
        except Exception as e:
            logger.error(f"Error deleting movie {movie_id}: {e}")
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

    async def get_movie_status(self, movie_id: int) -> dict:
        """Get detailed status of a movie.

        Args:
            movie_id: Movie ID.

        Returns:
            Movie status with file size, quality, etc.
        """
        try:
            movie = await self.get_movies(movie_id=movie_id)

            return {
                "movie": {
                    "id": movie.get("id"),
                    "title": movie.get("title"),
                    "year": movie.get("year"),
                    "status": movie.get("status"),
                    "overview": movie.get("overview", "")[:200],
                },
                "file": {
                    "size_on_disk": movie.get("sizeOnDisk"),
                    "quality": movie.get("movieFile", {}).get("quality", {}).get("quality", {}).get("name") if movie.get("movieFile") else None,
                    "path": movie.get("movieFile", {}).get("path") if movie.get("movieFile") else None,
                },
            }
        except Exception as e:
            logger.error(f"Error getting movie status for {movie_id}: {e}")
            raise
