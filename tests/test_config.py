"""Tests for configuration module."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import (
    AppConfig,
    SonarrConfig,
    SeerrConfig,
    load_config,
    get_enabled_services,
)


class TestSonarrConfig:
    """Tests for SonarrConfig."""

    def test_defaults_disabled(self):
        cfg = SonarrConfig()
        assert not cfg.enabled
        assert cfg.host == ""
        assert cfg.api_key == ""

    def test_enabled_with_both_fields(self):
        cfg = SonarrConfig(host="http://sonarr:8989", api_key="test-key")
        assert cfg.enabled
        assert cfg.host == "http://sonarr:8989"
        assert cfg.api_key == "test-key"

    def test_disabled_with_only_host(self):
        cfg = SonarrConfig(host="http://sonarr:8989", api_key="")
        assert not cfg.enabled


class TestLoadConfig:
    """Tests for load_config function."""

    @pytest.mark.parametrize("service,host_var,key_var", [
        ("sonarr", "SONARR_HOST", "SONARR_API_KEY"),
        ("radarr", "RADARR_HOST", "RADARR_API_KEY"),
        ("lidarr", "LIDARR_HOST", "LIDARR_API_KEY"),
        ("prowlarr", "PROWLARR_HOST", "PROWLARR_API_KEY"),
        ("readarr", "READARR_HOST", "READARR_API_KEY"),
        ("seerr", "SEERR_HOST", "SEERR_API_KEY"),
        ("tautulli", "TAUTULLI_HOST", "TAUTULLI_API_KEY"),
    ])
    def test_load_config_from_env(self, service, host_var, key_var):
        """Test that config loads from environment variables."""
        env = {
            host_var: f"http://{service}:1234",
            key_var: f"{service}-api-key",
            "LOG_LEVEL": "DEBUG",
        }

        with patch.dict(os.environ, env, clear=False):
            config = load_config()

        service_cfg = getattr(config, service)
        assert service_cfg.host == f"http://{service}:1234"
        assert service_cfg.api_key == f"{service}-api-key"
        assert service_cfg.enabled
        assert config.log_level == "DEBUG"

    def test_load_config_defaults(self):
        """Test default values when no env vars are set."""
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()

        # All services should be disabled by default
        for service in ["sonarr", "radarr", "lidarr", "prowlarr",
                        "readarr", "seerr", "tautulli", "plex"]:
            assert not getattr(config, service).enabled

        # Default global settings
        assert config.log_level == "INFO"
        assert config.cache_enabled is True
        assert config.cache_ttl == 300
        assert config.request_timeout == 30.0


class TestGetEnabledServices:
    """Tests for get_enabled_services."""

    def test_all_disabled(self):
        config = AppConfig()
        services = get_enabled_services(config)
        assert services == []

    def test_some_enabled(self):
        config = AppConfig(
            sonarr=SonarrConfig(host="http://sonarr:8989", api_key="key"),
            radarr=SonarrConfig(host="http://radarr:7878", api_key="key"),
        )
        services = get_enabled_services(config)
        assert "sonarr" in services
        assert "radarr" in services
        assert len(services) == 2

    def test_all_enabled(self):
        config = AppConfig(
            sonarr=SonarrConfig(host="h", api_key="k"),
            radarr=SonarrConfig(host="h", api_key="k"),
            lidarr=SonarrConfig(host="h", api_key="k"),
            prowlarr=SonarrConfig(host="h", api_key="k"),
            readarr=SonarrConfig(host="h", api_key="k"),
            seerr=SeerrConfig(host="h", api_key="k"),
            tautulli=SonarrConfig(host="h", api_key="k"),
            plex=SonarrConfig(host="h", api_key="k"),
        )
        services = get_enabled_services(config)
        expected = ["sonarr", "radarr", "lidarr", "prowlarr",
                    "readarr", "seerr", "tautulli", "plex"]
        assert sorted(services) == sorted(expected)
