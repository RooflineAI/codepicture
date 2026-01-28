"""Codepicture - Generate beautiful images of source code.

One command turns code into a slide-ready image.
"""

__version__ = "0.1.0"

from .config import RenderConfig, load_config
from .errors import (
    CodepictureError,
    ConfigError,
    HighlightError,
    RenderError,
    ThemeError,
)

__all__ = [
    "__version__",
    # Config
    "RenderConfig",
    "load_config",
    # Errors
    "CodepictureError",
    "ConfigError",
    "HighlightError",
    "RenderError",
    "ThemeError",
]
