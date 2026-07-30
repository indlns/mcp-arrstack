#!/usr/bin/env python3
"""MCP Server for ARR Stack — Main entry point.

Provides tools for LLMs to interact with home media automation services:
Sonarr, Radarr, Lidarr, Prowlarr, Readarr, Seerr, Tautulli, Plex.
"""

import anyio
import argparse
import json
import logging
import os
import sys
from typing import Any

import mcp.server.stdio
from mcp.server import Server
from mcp.types import Tool, TextContent

from .config import load_config, get_enabled_services
from .client import BaseARRClient, ProwlarrClient, LidarrClient, ReadarrClient, SeerrClient, TautulliClient, PlexClient


# ─── Logging Setup ───────────────────────────────────────────────────────────

def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the server."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    handlers = [logging.StreamHandler(sys.stdout)]
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


# ─── Tool Factories ──────────────────────────────────────────────────────────

def _make_sonarr_tools(client: BaseARRClient):
    """Import and return SonarrTools instance."""
    from .tools.sonarr_tools import SonarrTools
    return SonarrTools(client)


def _make_radarr_tools(client: BaseARRClient):
    """Import and return RadarrTools instance."""
    from .tools.radarr_tools import RadarrTools
    return RadarrTools(client)


def _make_prowlarr_tools(client: BaseARRClient):
    """Import and return ProwlarrTools instance."""
    from .tools.prowlarr_tools import ProwlarrTools
    return ProwlarrTools(client)


def _make_seerr_tools(client: SeerrClient):
    """Import and return SeerrTools instance."""
    from .tools.seerr_tools import SeerrTools
    return SeerrTools(client)


def _make_tautulli_tools(client: TautulliClient):
    """Import and return TautulliTools instance."""
    from .tools.tautulli_tools import TautulliTools
    return TautulliTools(client)


def _make_plex_tools(client: PlexClient):
    """Import and return PlexTools instance."""
    from .tools.plex_tools import PlexTools
    return PlexTools(client)


def _make_lidarr_tools(client: BaseARRClient):
    """Import and return LidarrTools instance."""
    from .tools.lidarr_tools import LidarrTools
    return LidarrTools(client)


def _make_readarr_tools(client: BaseARRClient):
    """Import and return ReadarrTools instance."""
    from .tools.readarr_tools import ReadarrTools
    return ReadarrTools(client)


# ─── Tool Definitions ────────────────────────────────────────────────────────

SONARR_TOOLS = [
    Tool(
        name="sonarr_search_series",
        description=(
            "Search for TV series by title. Returns matching series "
            "with ID, title, year, TVDB ID, and other metadata."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Series title to search for",
                },
            },
            "required": ["title"],
        },
    ),
    Tool(
        name="sonarr_get_series",
        description=(
            "Get details of a specific series by ID, or list all "
            "series in Sonarr. Pass series_id for a single series, "
            "or title to filter the list."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "series_id": {
                    "type": "integer",
                    "description": "Series ID to fetch details",
                },
                "title": {
                    "type": "string",
                    "description": "Filter series list by title",
                },
            },
        },
    ),
    Tool(
        name="sonarr_get_episodes",
        description=(
            "Get episode details for a specific series, including "
            "season/episode numbers, titles, air dates, and download status."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "series_id": {
                    "type": "integer",
                    "description": "Series ID to get episodes for",
                },
                "episode_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Specific episode IDs (optional)",
                },
                "season_number": {
                    "type": "integer",
                    "description": "Filter by season number (optional)",
                },
            },
            "required": ["series_id"],
        },
    ),
    Tool(
        name="sonarr_add_series",
        description=(
            "Add a new TV series to Sonarr. Requires the TVDB ID of "
            "the series (get it via sonarr_search_series first). "
            "Also adds and searches for existing episodes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "tvdb_id": {
                    "type": "integer",
                    "description": "TVDB ID of the series",
                },
                "title": {
                    "type": "string",
                    "description": "Series title",
                },
                "root_path": {
                    "type": "string",
                    "description": "Root folder path on disk (e.g., '/data/series')",
                },
                "quality_profile_id": {
                    "type": "integer",
                    "default": 1,
                    "description": "Quality profile ID (default: 1)",
                },
                "language_profile_id": {
                    "type": "integer",
                    "default": 1,
                    "description": "Language profile ID (default: 1)",
                },
                "monitored": {
                    "type": "boolean",
                    "default": True,
                    "description": "Monitor all episodes (default: True)",
                },
                "search_for_missing": {
                    "type": "boolean",
                    "default": False,
                    "description": "Search for missing episodes immediately (default: False)",
                },
                "series_type": {
                    "type": "string",
                    "default": "standard",
                    "description": "Series type: 'standard', 'daily', or 'anime' (default: 'standard')",
                },
            },
            "required": ["tvdb_id", "title", "root_path"],
        },
    ),
    Tool(
        name="sonarr_delete_series",
        description=(
            "Delete a series from Sonarr. Optionally delete files "
            "from disk as well."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "series_id": {
                    "type": "integer",
                    "description": "Series ID to delete",
                },
                "delete_files": {
                    "type": "boolean",
                    "default": False,
                    "description": "Also delete files from disk (default: False)",
                },
            },
            "required": ["series_id"],
        },
    ),
    Tool(
        name="sonarr_get_quality_profile",
        description=(
            "Get quality profiles available in Sonarr. Optionally "
            "filter by specific profile ID."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "profile_id": {
                    "type": "integer",
                    "description": "Specific profile ID to get (optional)",
                },
            },
        },
    ),
    Tool(
        name="sonarr_get_root_folder",
        description="Get available root folders on disk for series storage.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="sonarr_get_series_status",
        description=(
            "Get detailed status of a series including episode counts: "
            "total, monitored, aired, downloaded, and missing episodes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "series_id": {
                    "type": "integer",
                    "description": "Series ID to get status for",
                },
            },
            "required": ["series_id"],
        },
    ),
]

RADARR_TOOLS = [
    Tool(
        name="radarr_search_movie",
        description=(
            "Search for movies by title. Returns matching movies "
            "with ID, title, year, TMDb ID, and other metadata."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Movie title to search for",
                },
            },
            "required": ["title"],
        },
    ),
    Tool(
        name="radarr_get_movies",
        description=(
            "Get details of a specific movie by ID, or list all "
            "movies in Radarr."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "movie_id": {
                    "type": "integer",
                    "description": "Movie ID to fetch details",
                },
                "title": {
                    "type": "string",
                    "description": "Filter movie list by title",
                },
            },
        },
    ),
    Tool(
        name="radarr_add_movie",
        description=(
            "Add a new movie to Radarr. Requires the TMDb ID of "
            "the movie (get it via radarr_search_movie first)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "tmdb_id": {
                    "type": "integer",
                    "description": "TMDb ID of the movie",
                },
                "title": {
                    "type": "string",
                    "description": "Movie title",
                },
                "root_path": {
                    "type": "string",
                    "description": "Root folder path on disk (e.g., '/data/movies')",
                },
                "quality_profile_id": {
                    "type": "integer",
                    "default": 1,
                    "description": "Quality profile ID (default: 1)",
                },
                "monitored": {
                    "type": "boolean",
                    "default": True,
                    "description": "Monitor the movie (default: True)",
                },
                "search_for_movie": {
                    "type": "boolean",
                    "default": False,
                    "description": "Search for the movie immediately (default: False)",
                },
            },
            "required": ["tmdb_id", "title", "root_path"],
        },
    ),
    Tool(
        name="radarr_delete_movie",
        description=(
            "Delete a movie from Radarr. Optionally delete files "
            "from disk as well."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "movie_id": {
                    "type": "integer",
                    "description": "Movie ID to delete",
                },
                "delete_files": {
                    "type": "boolean",
                    "default": False,
                    "description": "Also delete files from disk (default: False)",
                },
            },
            "required": ["movie_id"],
        },
    ),
    Tool(
        name="radarr_get_quality_profile",
        description="Get quality profiles available in Radarr.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="radarr_get_root_folder",
        description="Get available root folders on disk for movie storage.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="radarr_get_movie_status",
        description=(
            "Get detailed status of a movie including file size, "
            "quality, and path information."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "movie_id": {
                    "type": "integer",
                    "description": "Movie ID to get status for",
                },
            },
            "required": ["movie_id"],
        },
    ),
]

PROWLARR_TOOLS = [
    Tool(
        name="prowlarr_search",
        description=(
            "Search across all Prowlarr indexers for content. "
            "Returns results with indexer name, size, seeders, "
            "and download links."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "type": {
                    "type": "string",
                    "description": (
                        "Search type: 'search', 'tvsearch', 'moviesearch', "
                        "'booksearch', 'audiosearch' (default: 'search')"
                    ),
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="prowlarr_get_indexers",
        description=(
            "Get list of configured indexers in Prowlarr with "
            "their status (enabled/disabled) and configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "enabled_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only return enabled indexers (default: False)",
                },
            },
        },
    ),
    Tool(
        name="prowlarr_test_indexers",
        description=(
            "Test the connection to all configured indexers at once. "
            "Returns success status and any error messages for each indexer. "
            "Note: Prowlarr API does not support per-indexer testing by ID; "
            "this tests all indexers simultaneously."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="prowlarr_get_history",
        description=(
            "Get download history from Prowlarr. "
            "Returns recent download events with title, size, indexer, age, etc."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 100,
                    "description": "Maximum number of history entries to return (default: 100)",
                },
            },
        },
    ),
    Tool(
        name="prowlarr_get_status",
        description=(
            "Get Prowlarr system status including version, "
            "connection status, and indexer summary."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
]

SEERR_TOOLS = [
    Tool(
        name="seerr_search",
        description=(
            "Search for media (movies and TV shows) via Seerr. "
            "Uses TMDB/TVDB databases."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                },
                "page": {
                    "type": "integer",
                    "default": 1,
                    "description": "Page number (default: 1)",
                },
                "language": {
                    "type": "string",
                    "description": "Language code (e.g. 'en', optional)",
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="seerr_get_requests",
        description=(
            "Get list of media requests in Seerr with their "
            "current status (pending, approved, available, etc.). "
            "Returns a dict with 'pageInfo' and 'results' keys."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "take": {
                    "type": "integer",
                    "default": 20,
                    "description": "Number of results to return (default: 20)",
                },
                "skip": {
                    "type": "integer",
                    "default": 0,
                    "description": "Number of results to skip for pagination (default: 0)",
                },
                "filter": {
                    "type": "string",
                    "enum": ["all", "approved", "available", "pending",
                             "processing", "unavailable", "failed", "deleted",
                             "completed"],
                    "description": "Filter by status (optional)",
                },
                "sort": {
                    "type": "string",
                    "enum": ["added", "modified"],
                    "default": "added",
                    "description": "Sort field (default: 'added')",
                },
                "sort_direction": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "default": "desc",
                    "description": "Sort order (default: 'desc')",
                },
                "requested_by": {
                    "type": "integer",
                    "description": "Filter by user ID (optional)",
                },
                "media_type": {
                    "type": "string",
                    "enum": ["movie", "tv", "all"],
                    "description": "Filter by media type (optional)",
                },
            },
        },
    ),
    Tool(
        name="seerr_request_media",
        description=(
            "Request a movie or TV show in Seerr. This searches for the "
            "media by title, matches by exact TMDb ID, and creates a request "
            "that can be approved and automatically added to Radarr/Sonarr. "
            "For TV shows, use 'seasons' to specify which seasons to request."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "tmdb_id": {
                    "type": "integer",
                    "description": "TMDb ID of the media",
                },
                "title": {
                    "type": "string",
                    "description": "Title of the media (used for lookup)",
                },
                "media_type": {
                    "type": "string",
                    "enum": ["movie", "tv"],
                    "default": "movie",
                    "description": "Type: 'movie' or 'tv' (default: 'movie')",
                },
                "quality_profile_id": {
                    "type": "integer",
                    "description": "Quality profile ID (optional)",
                },
                "root_folder": {
                    "type": "string",
                    "description": "Root folder path (optional)",
                },
                "ignore_quota": {
                    "type": "boolean",
                    "default": False,
                    "description": "Ignore quota limits (default: False)",
                },
                "seasons": {
                    "oneOf": [
                        {"type": "array", "items": {"type": "integer"}},
                        {"type": "string"},
                    ],
                    "description": "Season numbers to request for TV as array (e.g. [1, 2]), JSON string (e.g. '[1, 2]'), or 'all' (optional)",
                },
                "media_id": {
                    "type": "integer",
                    "description": "Direct Seerr internal media ID — skips the search step when provided (optional)",
                },
            },
            "required": ["tmdb_id", "title", "media_type"],
        },
    ),
    Tool(
        name="seerr_approve",
        description=(
            "Approve a pending request in Seerr. The media "
            "will be automatically added to Radarr/Sonarr."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "request_id": {
                    "type": "integer",
                    "description": "Request ID to approve",
                },
            },
            "required": ["request_id"],
        },
    ),
    Tool(
        name="seerr_reject",
        description=(
            "Reject a pending request in Seerr."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "request_id": {
                    "type": "integer",
                    "description": "Request ID to reject",
                },
            },
            "required": ["request_id"],
        },
    ),
    Tool(
        name="seerr_get_request",
        description=(
            "Get details of a specific request by ID, including "
            "media info, status, and approval state."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "request_id": {
                    "type": "integer",
                    "description": "Request ID to fetch details for",
                },
            },
            "required": ["request_id"],
        },
    ),
]

TAUTULLI_TOOLS = [
    Tool(
        name="tautulli_get_activity",
        description=(
            "Get current Plex activity — who is watching what, "
            "streaming details, and total active sessions."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="tautulli_get_library_stats",
        description=(
            "Get list of Plex libraries with section IDs, names, "
            "and item counts (movies, shows, episodes, etc.)."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="tautulli_get_history",
        description=(
            "Get watch history from Tautulli. Shows what was watched, "
            "by whom, when, and for how long."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "length": {
                    "type": "integer",
                    "default": 25,
                    "description": "Max results (default: 25)",
                },
                "grouping": {
                    "type": "integer",
                    "enum": [0, 1],
                    "default": 0,
                    "description": "Group multi-episode watches, 0 or 1 (default: 0)",
                },
            },
        },
    ),
    Tool(
        name="tautulli_get_user_stats",
        description=(
            "Get user watch time statistics from Tautulli — "
            "total plays and duration over 1, 7, 30 days, and all time."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The Plex user ID (required)",
                },
            },
            "required": ["user_id"],
        },
    ),
    Tool(
        name="tautulli_get_recently_added",
        description=(
            "Get recently added content to the Plex library."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "media_type": {
                    "type": "string",
                    "enum": ["movie", "show", "artist"],
                    "description": "Filter by media type (omit for all)",
                },
                "count": {
                    "type": "integer",
                    "default": 25,
                    "description": "Number of items to return (default: 25)",
                },
            },
        },
    ),
]

PLEX_TOOLS = [
    Tool(
        name="plex_search",
        description=(
            "Search the Plex library for content by title or keyword."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="plex_library_sections",
        description=(
            "Get all Plex library sections (Movies, TV Shows, etc.) "
            "with their keys and item counts."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="plex_recently_added",
        description=(
            "Get recently added content to Plex. Optionally filter "
            "by section type (movie/show)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "section_type": {
                    "type": "string",
                    "enum": ["movie", "show", None],
                    "description": "Filter by type (default: all)",
                },
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "description": "Max results (default: 20)",
                },
            },
        },
    ),
    Tool(
        name="plex_playlists",
        description="Get all playlists from Plex.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="plex_library",
        description=(
            "Get items from a specific Plex library section. "
            "section_key is the section integer ID (1=movies, 2=shows). "
            "section_type filters by content type using Plex API integer codes: "
            "1=movie, 2=show, 3=season, 4=episode, 8=artist, 9=album, 10=track."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "section_key": {
                    "type": "integer",
                    "description": "Section key (1=movies, 2=shows, etc.)",
                },
                "section_type": {
                    "type": "string",
                    "enum": ["movie", "show", "season", "episode", "artist", "album", "track", "all"],
                    "default": "all",
                    "description": "Filter by content type (default: 'all'). Maps to Plex API integer: movie=1, show=2, season=3, episode=4, artist=8, album=9, track=10.",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Max results (default: 50)",
                },
            },
            "required": ["section_key"],
        },
    ),
    Tool(
        name="plex_get_status",
        description=(
            "Get Plex server status — name, version, library counts."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
]

LIDARR_TOOLS = [
    Tool(
        name="lidarr_search_artist",
        description=(
            "Search for music artists/albums by name. Returns "
            "matching artists with IDs and metadata."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "term": {
                    "type": "string",
                    "description": "Artist or album name to search for",
                },
            },
            "required": ["term"],
        },
    ),
    Tool(
        name="lidarr_get_artist",
        description=(
            "Get artist details or list all artists in Lidarr."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "artist_id": {
                    "type": "integer",
                    "description": "Artist ID to fetch details",
                },
                "artist_name": {
                    "type": "string",
                    "description": "Filter by artist name",
                },
            },
        },
    ),
    Tool(
        name="lidarr_add_artist",
        description=(
            "Add a new music artist to Lidarr. Requires the "
            "MusicBrainz artist ID."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "musicbrainz_id": {
                    "type": "string",
                    "description": "MusicBrainz artist ID",
                },
                "title": {
                    "type": "string",
                    "description": "Artist name",
                },
                "root_path": {
                    "type": "string",
                    "description": "Root folder path on disk (e.g., '/data/music')",
                },
                "quality_profile_id": {
                    "type": "integer",
                    "default": 1,
                    "description": "Quality profile ID (default: 1)",
                },
                "monitored": {
                    "type": "boolean",
                    "default": True,
                    "description": "Monitor new albums (default: True)",
                },
            },
            "required": ["musicbrainz_id", "title", "root_path"],
        },
    ),
    Tool(
        name="lidarr_delete_artist",
        description=(
            "Delete an artist from Lidarr. Optionally delete files."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "artist_id": {
                    "type": "integer",
                    "description": "Artist ID to delete",
                },
                "delete_files": {
                    "type": "boolean",
                    "default": False,
                    "description": "Also delete files from disk (default: False)",
                },
            },
            "required": ["artist_id"],
        },
    ),
]

READARR_TOOLS = [
    Tool(
        name="readarr_search_author",
        description=(
            "Search for authors/books by term. Returns matching authors "
            "with ID, title, year, foreignAuthorId, and other metadata."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "term": {
                    "type": "string",
                    "description": "Author or book title to search for",
                },
            },
            "required": ["term"],
        },
    ),
    Tool(
        name="readarr_get_author",
        description=(
            "Get details of a specific author by ID, or list all "
            "authors in Readarr. Pass author_id for a single author, "
            "or author_name to filter the list."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "author_id": {
                    "type": "integer",
                    "description": "Author ID to fetch details",
                },
                "author_name": {
                    "type": "string",
                    "description": "Filter authors by name",
                },
            },
        },
    ),
    Tool(
        name="readarr_add_author",
        description=(
            "Add a new author to Readarr. Requires the foreignAuthorId "
            "(e.g. Goodreads author ID) of the author. "
            "Also searches for existing books when search_for_missing is enabled."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "foreign_id": {
                    "type": "string",
                    "description": "Foreign author ID (e.g. MusicBrainz or Goodreads ID)",
                },
                "title": {
                    "type": "string",
                    "description": "Author name",
                },
                "root_path": {
                    "type": "string",
                    "description": "Root folder path on disk (e.g., '/data/books')",
                },
                "quality_profile_id": {
                    "type": "integer",
                    "default": 1,
                    "description": "Quality profile ID (default: 1)",
                },
                "monitored": {
                    "type": "boolean",
                    "default": True,
                    "description": "Monitor new books (default: True)",
                },
                "search_for_missing": {
                    "type": "boolean",
                    "default": False,
                    "description": "Search for missing books immediately (default: False)",
                },
            },
            "required": ["foreign_id", "title", "root_path"],
        },
    ),
    Tool(
        name="readarr_delete_author",
        description=(
            "Delete an author from Readarr. Optionally delete files "
            "from disk as well."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "author_id": {
                    "type": "integer",
                    "description": "Author ID to delete",
                },
                "delete_files": {
                    "type": "boolean",
                    "default": False,
                    "description": "Also delete files from disk (default: False)",
                },
            },
            "required": ["author_id"],
        },
    ),
]

# Service → (tool_definitions, factory, config_attr) mapping
SERVICE_MAP = {
    "sonarr": (SONARR_TOOLS, _make_sonarr_tools, "sonarr"),
    "radarr": (RADARR_TOOLS, _make_radarr_tools, "radarr"),
    "prowlarr": (PROWLARR_TOOLS, _make_prowlarr_tools, "prowlarr"),
    "seerr": (SEERR_TOOLS, _make_seerr_tools, "seerr"),
    "tautulli": (TAUTULLI_TOOLS, _make_tautulli_tools, "tautulli"),
    "plex": (PLEX_TOOLS, _make_plex_tools, "plex"),
    "lidarr": (LIDARR_TOOLS, _make_lidarr_tools, "lidarr"),
    "readarr": (READARR_TOOLS, _make_readarr_tools, "readarr"),
}

# Tool → (service_name, method_name) mapping
TOOL_HANDLERS: dict[str, tuple[str, str]] = {}


def _register_handlers() -> None:
    """Build the tool-to-handler dispatch table."""
    for service_name, (tools, _, _) in SERVICE_MAP.items():
        for tool in tools:
            # Tool names are like "radarr_add_movie", but methods are named
            # without the service prefix, e.g. "add_movie". Strip it.
            method_name = tool.name.replace("-", "_")
            prefix = f"{service_name}_"
            if method_name.startswith(prefix):
                method_name = method_name[len(prefix):]
            TOOL_HANDLERS[tool.name] = (service_name, method_name)


_register_handlers()


# ─── Tool Dispatch ───────────────────────────────────────────────────────────

async def _dispatch_tool(name: str, args: dict, clients: dict) -> list[TextContent]:
    """Dispatch a tool call to the appropriate handler."""
    try:
        if name not in TOOL_HANDLERS:
            available = ", ".join(sorted(TOOL_HANDLERS.keys()))
            return [TextContent(
                type="text",
                text=f"Unknown tool: '{name}'.\n\nAvailable tools:\n{available}"
            )]

        service_name, method_name = TOOL_HANDLERS[name]

        if service_name not in clients:
            return [TextContent(
                type="text",
                text=f"Service '{service_name}' is not configured. "
                     f"Please check your environment variables."
            )]

        client = clients[service_name]

        # Get the tools instance
        factory_fn = SERVICE_MAP[service_name][1]
        tools_instance = factory_fn(client)

        # Call the method
        method = getattr(tools_instance, method_name, None)
        if method is None:
            return [TextContent(
                type="text",
                text=f"Method '{method_name}' not found on {service_name} tools."
            )]

        result = await method(**args)
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2, default=str)
        )]

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error handling tool '{name}': {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ─── MCP Server Factory ──────────────────────────────────────────────


def create_mcp_server(clients: dict[str, Any]) -> Server:
    """Create and configure the MCP server instance.

    Registers available tools based on enabled services and returns
    a configured Server app ready for any transport.

    Args:
        clients: Dict of service name to client instance mapping.

    Returns:
        Configured MCP Server instance.
    """
    app = Server("mcp-arr-stack")

    # Register all available tools based on enabled services
    available_tools: list[Tool] = []
    for service_name, (tools, _, _) in SERVICE_MAP.items():
        if service_name in clients:
            available_tools.extend(tools)

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        return available_tools

    @app.call_tool()
    async def call_tool(
        name: str, arguments: list[Any] | dict[str, Any] | None
    ) -> list[TextContent]:
        if arguments is None:
            arguments = {}
        # MCP SDK may pass arguments as a list for positional params
        if isinstance(arguments, list):
            return [
                TextContent(
                    type="text",
                    text=f"Error: tool '{name}' expects keyword arguments, got positional.",
                )
            ]
        return await _dispatch_tool(name, arguments, clients)

    return app


# ─── Main Entry Point ────────────────────────────────────────────────────────


async def run_server(config: Any = None) -> None:
    """Start the MCP server with the configured transport.

    Args:
        config: AppConfig instance. If None, loaded from environment.
    """
    if config is None:
        config = load_config()

    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting MCP ARR Stack Server...")
    logger.info(f"Enabled services: {', '.join(get_enabled_services(config))}")

    # Build clients for enabled services
    clients: dict[str, Any] = {}
    if config.sonarr.enabled:
        clients["sonarr"] = BaseARRClient(
            config.sonarr.host, config.sonarr.api_key, config.request_timeout
        )
    if config.radarr.enabled:
        clients["radarr"] = BaseARRClient(
            config.radarr.host, config.radarr.api_key, config.request_timeout
        )
    if config.lidarr.enabled:
        clients["lidarr"] = LidarrClient(
            config.lidarr.host, config.lidarr.api_key, config.request_timeout
        )
    if config.prowlarr.enabled:
        clients["prowlarr"] = ProwlarrClient(
            config.prowlarr.host, config.prowlarr.api_key, config.request_timeout
        )
    if config.readarr.enabled:
        clients["readarr"] = ReadarrClient(
            config.readarr.host, config.readarr.api_key, config.request_timeout
        )
    if config.seerr.enabled:
        clients["seerr"] = SeerrClient(
            config.seerr.host, config.seerr.api_key, config.request_timeout
        )
    if config.tautulli.enabled:
        clients["tautulli"] = TautulliClient(
            config.tautulli.host, config.tautulli.api_key, config.request_timeout
        )
    if config.plex.enabled:
        clients["plex"] = PlexClient(
            config.plex.host, config.plex.token, config.request_timeout
        )

    # Create MCP server
    app = create_mcp_server(clients)

    # Select transport
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport == "http":
        from .http_server import run_http_server

        await run_http_server(app, config)
    else:
        # Stdio transport (default)
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP ARR Stack Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="Transport protocol (default: stdio or MCP_TRANSPORT env)",
    )
    args = parser.parse_args()

    # Override transport via CLI arg
    os.environ["MCP_TRANSPORT"] = args.transport

    anyio.run(run_server)
