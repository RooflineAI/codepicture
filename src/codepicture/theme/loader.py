"""Theme discovery and loading.

Provides get_theme() for loading themes by name and list_themes() for
discovering available themes.
"""

import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from pygments.styles import get_all_styles

from ..errors import ThemeError
from .pygments_theme import PygmentsTheme
from .toml_theme import load_toml_theme

if TYPE_CHECKING:
    from ..core.protocols import Theme


# Built-in themes available via get_theme()
# These map to Pygments styles (including Catppuccin via catppuccin[pygments])
BUILTIN_THEMES: set[str] = {
    # Classic themes
    "dracula",
    "monokai",
    "one-dark",
    # Catppuccin flavors (registered by catppuccin[pygments] package)
    "catppuccin-mocha",
    "catppuccin-macchiato",
    "catppuccin-frappe",
    "catppuccin-latte",
}

# Theme aliases for user convenience
THEME_ALIASES: dict[str, str] = {
    "catppuccin": "catppuccin-mocha",  # Default Catppuccin flavor
    "onedark": "one-dark",
}

# Default theme when none specified
DEFAULT_THEME = "catppuccin-mocha"


def get_theme(
    name: str | None = None,
    custom_path: Path | None = None,
) -> "Theme":
    """Load a theme by name or from a custom TOML file.

    Priority:
    1. If custom_path provided, load TOML theme (may use inheritance)
    2. If name is an alias, resolve it
    3. If name is a built-in theme, return PygmentsTheme
    4. Try loading as a Pygments style (for themes not in BUILTIN_THEMES)
    5. Raise ThemeError with available themes

    Args:
        name: Theme name (e.g., "monokai", "catppuccin-mocha")
              Defaults to DEFAULT_THEME if None
        custom_path: Optional path to a custom TOML theme file

    Returns:
        Theme instance

    Raises:
        ThemeError: If theme not found or custom file invalid
    """
    # Handle custom TOML theme
    if custom_path is not None:
        # Build base themes dict for inheritance
        base_themes = _get_base_themes()
        return load_toml_theme(custom_path, base_themes)

    # Use default if no name specified
    if name is None:
        name = DEFAULT_THEME

    # Resolve aliases
    name = THEME_ALIASES.get(name, name)

    # Try as built-in or Pygments style
    try:
        return PygmentsTheme(name)
    except Exception as err:
        available = list_themes()
        raise ThemeError(
            f"Unknown theme: {name}. Available: {', '.join(sorted(available))}"
        ) from err


def list_themes() -> list[str]:
    """Return sorted list of available theme names.

    Includes:
    - Built-in themes (Catppuccin, Dracula, etc.)
    - All Pygments styles
    - Theme aliases

    Returns:
        Sorted list of theme names
    """
    themes = set(BUILTIN_THEMES)

    # Add all Pygments styles
    themes.update(get_all_styles())

    # Add aliases
    themes.update(THEME_ALIASES.keys())

    return sorted(themes)


def _get_base_themes() -> dict[str, "Theme"]:
    """Build dictionary of available base themes for inheritance.

    Returns:
        Dictionary mapping theme names to Theme instances
    """
    base_themes: dict[str, Theme] = {}

    # Add built-in themes
    for name in BUILTIN_THEMES:
        with contextlib.suppress(Exception):
            base_themes[name] = PygmentsTheme(name)

    # Add all Pygments styles
    for name in get_all_styles():
        if name not in base_themes:
            with contextlib.suppress(Exception):
                base_themes[name] = PygmentsTheme(name)

    return base_themes
