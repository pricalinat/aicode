"""Configuration management system."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Config:
    """Application configuration."""
    # Core settings
    debug: bool = False
    log_level: str = "INFO"
    
    # Agent settings
    max_retries: int = 3
    timeout_seconds: int = 30
    
    # Graph settings
    graph_backend: str = "memory"
    graph_persistence_path: str = "./data"
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl: int = 300
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    
    # Feature flags
    enable_async: bool = True
    enable_caching: bool = True
    enable_metrics: bool = True
    
    # Mini-program settings
    default_platform: str = "wechat"


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: str | None = None) -> None:
        self._config = Config()
        self._config_path = config_path
    
    def load(self) -> Config:
        """Load configuration from file."""
        if self._config_path:
            path = Path(self._config_path)
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self._config, key):
                            setattr(self._config, key, value)
        return self._config
    
    def save(self) -> None:
        """Save configuration to file."""
        if self._config_path:
            data = {
                key: getattr(self._config, key)
                for key in dir(self._config)
                if not key.startswith("_") and not callable(getattr(self._config, key))
            }
            path = Path(self._config_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
    
    def get(self) -> Config:
        """Get current configuration."""
        return self._config
    
    def update(self, **kwargs: Any) -> None:
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)


# Global config manager
_config_manager: ConfigManager | None = None


def get_config_manager(config_path: str | None = None) -> ConfigManager:
    """Get the global config manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager


def get_config() -> Config:
    """Get current configuration."""
    return get_config_manager().get()
