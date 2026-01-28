"""Theme system for syntax highlighting.

Provides theme loading and application for syntax token colorization.
Supports built-in Pygments themes, Catppuccin flavors, and custom TOML themes.
"""

from .loader import get_theme, list_themes
from .pygments_theme import PygmentsTheme
from .toml_theme import TomlTheme, load_toml_theme

__all__ = [
    "PygmentsTheme",
    "TomlTheme",
    "get_theme",
    "list_themes",
    "load_toml_theme",
]
