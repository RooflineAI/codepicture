"""Theme system for syntax highlighting.

Provides theme loading and application for syntax token colorization.
Supports built-in Pygments themes, Catppuccin flavors, and custom TOML themes.
"""

from .pygments_theme import PygmentsTheme

__all__ = [
    "PygmentsTheme",
]
