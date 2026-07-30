"""Configuration module for MCP ARR Stack server."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SonarrConfig:
    """Configuration for Sonarr service."""
    host: str = ""
    api_key: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.api_key)


@dataclass
class RadarrConfig:
    """Configuration for Radarr service."""
    host: str = ""
    api_key: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.api_key)


@dataclass
class LidarrConfig:
    """Configuration for Lidarr service."""
    host: str = ""
    api_key: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.api_key)


@dataclass
class ProwlarrConfig:
    """Configuration for Prowlarr service."""
    host: str = ""
    api_key: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.api_key)


@dataclass
class ReadarrConfig:
    """Configuration for Readarr service."""
    host: str = ""
    api_key: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.api_key)


@dataclass
class SeerrConfig:
    """Configuration for Seerr service."""
    host: str = ""
    api_key: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.api_key)


@dataclass
class TautulliConfig:
    """Configuration for Tautulli service."""
    host: str = ""
    api_key: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.api_key)


@dataclass
class PlexConfig:
    """Configuration for Plex service."""
    host: str = ""
    token: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.token)


@dataclass
class AppConfig:
    """Application-wide configuration."""
    sonarr: SonarrConfig = field(default_factory=SonarrConfig)
    radarr: RadarrConfig = field(default_factory=RadarrConfig)
    lidarr: LidarrConfig = field(default_factory=LidarrConfig)
    prowlarr: ProwlarrConfig = field(default_factory=ProwlarrConfig)
    readarr: ReadarrConfig = field(default_factory=ReadarrConfig)
    seerr: SeerrConfig = field(default_factory=SeerrConfig)
    tautulli: TautulliConfig = field(default_factory=TautulliConfig)
    plex: PlexConfig = field(default_factory=PlexConfig)

    # Global settings
    log_level: str = "INFO"
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
    request_timeout: float = 30.0

    # HTTP transport settings
    http_host: str = "0.0.0.0"
    http_port: int = 8080
    http_api_key: str = ""  # Bearer token for client authentication
    http_cors_origins: str = "*"  # Comma-separated origins or "*"
    http_ssl_certfile: str = ""  # Path to SSL certificate (optional)
    http_ssl_keyfile: str = ""  # Path to SSL private key (optional)


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    return AppConfig(
        sonarr=SonarrConfig(
            host=os.getenv("SONARR_HOST", ""),
            api_key=os.getenv("SONARR_API_KEY", ""),
        ),
        radarr=RadarrConfig(
            host=os.getenv("RADARR_HOST", ""),
            api_key=os.getenv("RADARR_API_KEY", ""),
        ),
        lidarr=LidarrConfig(
            host=os.getenv("LIDARR_HOST", ""),
            api_key=os.getenv("LIDARR_API_KEY", ""),
        ),
        prowlarr=ProwlarrConfig(
            host=os.getenv("PROWLARR_HOST", ""),
            api_key=os.getenv("PROWLARR_API_KEY", ""),
        ),
        readarr=ReadarrConfig(
            host=os.getenv("READARR_HOST", ""),
            api_key=os.getenv("READARR_API_KEY", ""),
        ),
        seerr=SeerrConfig(
            host=os.getenv("SEERR_HOST", ""),
            api_key=os.getenv("SEERR_API_KEY", ""),
        ),
        tautulli=TautulliConfig(
            host=os.getenv("TAUTULLI_HOST", ""),
            api_key=os.getenv("TAUTULLI_API_KEY", ""),
        ),
        plex=PlexConfig(
            host=os.getenv("PLEX_HOST", ""),
            token=os.getenv("PLEX_TOKEN", ""),
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
        cache_ttl=int(os.getenv("CACHE_TTL", "300")),
        request_timeout=float(os.getenv("REQUEST_TIMEOUT", "30.0")),
        http_host=os.getenv("HTTP_HOST", "0.0.0.0"),
        http_port=int(os.getenv("HTTP_PORT", "8080")),
        http_api_key=os.getenv("HTTP_API_KEY", ""),
        http_cors_origins=os.getenv("HTTP_CORS_ORIGINS", "*"),
        http_ssl_certfile=os.getenv("HTTP_SSL_CERTFILE", "").strip(),
        http_ssl_keyfile=os.getenv("HTTP_SSL_KEYFILE", "").strip(),
    )


def get_enabled_services(config: AppConfig) -> list[str]:
    """Return list of enabled service names."""
    services = []
    if config.sonarr.enabled:
        services.append("sonarr")
    if config.radarr.enabled:
        services.append("radarr")
    if config.lidarr.enabled:
        services.append("lidarr")
    if config.prowlarr.enabled:
        services.append("prowlarr")
    if config.readarr.enabled:
        services.append("readarr")
    if config.seerr.enabled:
        services.append("seerr")
    if config.tautulli.enabled:
        services.append("tautulli")
    if config.plex.enabled:
        services.append("plex")
    return services
