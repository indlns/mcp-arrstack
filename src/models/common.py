"""Common Pydantic models for ARR Stack APIs."""

from pydantic import BaseModel, Field
from typing import Any, Optional


class APIResponse(BaseModel):
    """Base response model."""
    success: bool = True
    message: str = ""
    data: Any = None
    error: Optional[str] = None


class SonarrSeries(BaseModel):
    """Sonarr series model."""
    id: Optional[int] = None
    title: Optional[str] = None
    year: Optional[int] = None
    tvdb_id: Optional[int] = Field(None, alias="tvdbId")
    tvrage_id: Optional[int] = Field(None, alias="tvRageId")
    tmdb_id: Optional[int] = Field(None, alias="tmdbId")
    season_count: Optional[int] = Field(None, alias="seasonCount")
    status: Optional[str] = None
    overview: Optional[str] = None
    network: Optional[str] = None
    air_time: Optional[str] = Field(None, alias="airTime")
    images: Optional[list[dict]] = None
    season_folders: Optional[bool] = Field(None, alias="seasonFolders")
    path: Optional[str] = None
    quality_profile_id: Optional[int] = Field(None, alias="qualityProfileId")
    monitored: Optional[bool] = None
    use_scene_numbering: Optional[bool] = Field(None, alias="useSceneNumbering")


class SonarrEpisode(BaseModel):
    """Sonarr episode model."""
    id: Optional[int] = None
    series_id: Optional[int] = Field(None, alias="seriesId")
    season_number: Optional[int] = Field(None, alias="seasonNumber")
    episode_number: Optional[int] = Field(None, alias="episodeNumber")
    title: Optional[str] = None
    aired: Optional[bool] = None
    grabbed: Optional[bool] = None
    ended: Optional[bool] = None
    monitored: Optional[bool] = None
    absolute_number: Optional[int] = Field(None, alias="absoluteNumber")
    has_file: Optional[bool] = Field(None, alias="hasFile")
    media_info: Optional[dict] = Field(None, alias="mediaInfo")
    overview: Optional[str] = None
    scene_episode_number: Optional[int] = Field(None, alias="sceneEpisodeNumber")
    scene_season_number: Optional[int] = Field(None, alias="sceneSeasonNumber")


class RadarrMovie(BaseModel):
    """Radarr movie model."""
    id: Optional[int] = None
    title: Optional[str] = None
    year: Optional[int] = None
    tmdb_id: Optional[int] = Field(None, alias="tmdbId")
    imdb_id: Optional[str] = Field(None, alias="imdbId")
    overview: Optional[str] = None
    in_cinemas: Optional[str] = Field(None, alias="inCinemas")
    physical_release: Optional[str] = Field(None, alias="physicalRelease")
    digital_release: Optional[str] = Field(None, alias="digitalRelease")
    images: Optional[list[dict]] = None
    size_on_disk: Optional[int] = Field(None, alias="sizeOnDisk")
    status: Optional[str] = None
    runtime: Optional[int] = None
    country: Optional[dict] = None
    cut: Optional[str] = None
    path: Optional[str] = None
    quality_profile_id: Optional[int] = Field(None, alias="qualityProfileId")
    monitored: Optional[bool] = None
    available_restriction: Optional[int] = Field(None, alias="availableRestriction")


class ProwlarrIndexer(BaseModel):
    """Prowlarr indexer model."""
    id: Optional[int] = None
    name: Optional[str] = None
    enable: Optional[bool] = None
    priority: Optional[int] = None
    protocol: Optional[str] = None
    info_url: Optional[str] = Field(None, alias="infoUrl")
    supports_rss: Optional[bool] = Field(None, alias="supportsRss")
    supports_search: Optional[bool] = Field(None, alias="supportsSearch")


class SeerrRequest(BaseModel):
    """Seerr request model."""
    id: Optional[int] = None
    status: Optional[int] = None
    status4k: Optional[int] = None
    created_at: Optional[str] = Field(None, alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    request_by_email: Optional[str] = Field(None, alias="requestByEmail")
    media: Optional[dict] = None


class ProwlarrSearchResult(BaseModel):
    """Prowlarr search result model."""
    id: Optional[int] = None
    title: Optional[str] = None
    indexer: Optional[str] = None
    protocol: Optional[str] = None
    download_count: Optional[int] = Field(None, alias="downloadCount")
    age: Optional[int] = None
    agebytes: Optional[str] = Field(None, alias="agebytes")
    grabs: Optional[int] = None
    size: Optional[float] = None
    seeders: Optional[int] = None
    peers: Optional[int] = None
    info_url: Optional[str] = Field(None, alias="infoUrl")
    download_url: Optional[str] = Field(None, alias="downloadUrl")
    publish_date: Optional[str] = Field(None, alias="publishDate")


class TautulliActivity(BaseModel):
    """Tautulli activity model."""
    username: Optional[str] = None
    user_id: Optional[str] = Field(None, alias="user_id")
    title: Optional[str] = None
    media_type: Optional[str] = Field(None, alias="media_type")
    progress: Optional[int] = None
    started: Optional[bool] = None
    paused_at: Optional[int] = Field(None, alias="paused_at")
    duration: Optional[int] = None
    thumb: Optional[str] = None


class PlexLibrarySection(BaseModel):
    """Plex library section model."""
    key: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    agent: Optional[str] = None


def format_series_summary(series: dict) -> str:
    """Format a Sonarr series dict into a readable summary string."""
    lines = [
        f"📺 {series.get('title', 'N/A')}",
        f"   Year: {series.get('year', 'N/A')}",
        f"   Status: {series.get('status', 'N/A')}",
        f"   Seasons: {series.get('season_count', series.get('seasonCount', 'N/A'))}",
    ]
    if series.get('overview'):
        overview = series['overview']
        if len(overview) > 200:
            overview = overview[:200] + "..."
        lines.append(f"   📝 {overview}")
    return "\n".join(lines)


def format_movie_summary(movie: dict) -> str:
    """Format a Radarr movie dict into a readable summary string."""
    lines = [
        f"🎬 {movie.get('title', 'N/A')}",
        f"   Year: {movie.get('year', 'N/A')}",
        f"   Status: {movie.get('status', 'N/A')}",
    ]
    if movie.get('overview'):
        overview = movie['overview']
        if len(overview) > 200:
            overview = overview[:200] + "..."
        lines.append(f"   📝 {overview}")
    return "\n".join(lines)
