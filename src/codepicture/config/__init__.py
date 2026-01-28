"""Configuration management for codepicture."""

from .loader import (
    DEFAULT_GLOBAL_CONFIG_PATH,
    DEFAULT_LOCAL_CONFIG_PATH,
    load_config,
)
from .schema import RenderConfig

__all__ = [
    "DEFAULT_GLOBAL_CONFIG_PATH",
    "DEFAULT_LOCAL_CONFIG_PATH",
    "load_config",
    "RenderConfig",
]
