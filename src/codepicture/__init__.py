"""Codepicture - Generate beautiful images of source code.

One command turns code into a slide-ready image.
"""

__version__ = "0.1.0"

from .config import RenderConfig, load_config
from .core.types import DisplayLine, LayoutMetrics, OutputFormat, RenderResult
from .errors import (
    CodepictureError,
    ConfigError,
    HighlightError,
    LayoutError,
    RenderError,
    ThemeError,
)
from .fonts import register_bundled_fonts, resolve_font_family
from .highlight import PygmentsHighlighter, TokenInfo
from .layout import LayoutEngine, PangoTextMeasurer
from .render import CairoCanvas, Renderer
from .theme import get_theme, list_themes

__all__ = [
    "CairoCanvas",
    "CodepictureError",
    "ConfigError",
    "DisplayLine",
    "HighlightError",
    "LayoutEngine",
    "LayoutError",
    "LayoutMetrics",
    "OutputFormat",
    "PangoTextMeasurer",
    "PygmentsHighlighter",
    "RenderConfig",
    "RenderError",
    "RenderResult",
    "Renderer",
    "ThemeError",
    "TokenInfo",
    "__version__",
    "get_theme",
    "list_themes",
    "load_config",
    "register_bundled_fonts",
    "resolve_font_family",
]
