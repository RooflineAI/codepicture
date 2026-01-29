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
from .fonts import register_bundled_fonts, resolve_font_family
from .highlight import PygmentsHighlighter, TokenInfo
from .layout import PangoTextMeasurer
from .theme import get_theme, list_themes

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
    # Fonts
    "register_bundled_fonts",
    "resolve_font_family",
    # Highlight
    "PygmentsHighlighter",
    "TokenInfo",
    # Layout
    "PangoTextMeasurer",
    # Theme
    "get_theme",
    "list_themes",
]
