"""TOML theme loading with inheritance support.

Provides custom theme definition via TOML files with optional inheritance
from built-in themes.
"""

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pygments.token import STANDARD_TYPES, Token, string_to_tokentype

from ..core.types import Color, TextStyle
from ..errors import ThemeError

if TYPE_CHECKING:
    from ..core.protocols import Theme


def parse_token_name(name: str) -> Any:
    """Convert token name string to Pygments token type.

    Accepts formats:
    - "Keyword" -> Token.Keyword
    - "Keyword.Constant" -> Token.Keyword.Constant
    - "Token.String" -> Token.String

    Args:
        name: Token name string

    Returns:
        Pygments token type

    Raises:
        ThemeError: If token name is invalid
    """
    # Handle Token prefix
    if name.startswith("Token."):
        name = name[6:]  # Remove "Token." prefix

    try:
        return string_to_tokentype(name)
    except (ValueError, KeyError) as e:
        raise ThemeError(f"Invalid token name: {name}") from e


class TomlTheme:
    """Theme loaded from TOML file with optional inheritance.

    TOML format:
    ```toml
    extends = "catppuccin-mocha"  # Optional base theme

    [colors]
    background = "#1a1a2e"
    foreground = "#e0e0e0"

    [tokens]
    Keyword = { color = "#ff79c6", bold = true }
    String = { color = "#50fa7b" }
    Comment = { color = "#6272a4", italic = true }
    ```

    Attributes:
        name: Theme name (derived from filename)
        background: Editor background color
        foreground: Default text color
        line_number_fg: Line number text color
        line_number_bg: Line number gutter background color
    """

    __slots__ = (
        "_name",
        "_base_theme",
        "_background",
        "_foreground",
        "_line_number_fg",
        "_line_number_bg",
        "_token_styles",
    )

    def __init__(
        self,
        name: str,
        data: dict[str, Any],
        base_theme: "Theme | None" = None,
    ) -> None:
        """Initialize theme from parsed TOML data.

        Args:
            name: Theme name
            data: Parsed TOML dictionary
            base_theme: Optional base theme for inheritance
        """
        self._name = name
        self._base_theme = base_theme
        self._token_styles: dict[Any, TextStyle] = {}

        # Parse colors section
        colors = data.get("colors", {})

        if "background" in colors:
            self._background = Color.from_hex(colors["background"])
        elif base_theme:
            self._background = base_theme.background
        else:
            self._background = Color.from_hex("#1e1e2e")

        if "foreground" in colors:
            self._foreground = Color.from_hex(colors["foreground"])
        elif base_theme:
            self._foreground = base_theme.foreground
        else:
            self._foreground = Color.from_hex("#cdd6f4")

        # Line number colors: derive or inherit
        if "line_number_fg" in colors:
            self._line_number_fg = Color.from_hex(colors["line_number_fg"])
        elif base_theme:
            self._line_number_fg = base_theme.line_number_fg
        else:
            self._line_number_fg = Color(
                r=max(0, self._foreground.r - 60),
                g=max(0, self._foreground.g - 60),
                b=max(0, self._foreground.b - 60),
                a=self._foreground.a,
            )

        if "line_number_bg" in colors:
            self._line_number_bg = Color.from_hex(colors["line_number_bg"])
        elif base_theme:
            self._line_number_bg = base_theme.line_number_bg
        else:
            self._line_number_bg = Color(
                r=max(0, self._background.r - 10),
                g=max(0, self._background.g - 10),
                b=max(0, self._background.b - 10),
                a=self._background.a,
            )

        # Parse token styles
        tokens = data.get("tokens", {})
        for token_name, style_data in tokens.items():
            token_type = parse_token_name(token_name)
            self._token_styles[token_type] = self._parse_style(style_data)

    def _parse_style(self, style_data: dict[str, Any]) -> TextStyle:
        """Parse style dictionary to TextStyle.

        Args:
            style_data: Dictionary with color, bold, italic, underline keys

        Returns:
            TextStyle instance
        """
        color_hex = style_data.get("color")
        if color_hex:
            color = Color.from_hex(color_hex)
        else:
            color = self._foreground

        return TextStyle(
            color=color,
            bold=style_data.get("bold", False),
            italic=style_data.get("italic", False),
            underline=style_data.get("underline", False),
        )

    @property
    def name(self) -> str:
        """Theme name."""
        return self._name

    @property
    def background(self) -> Color:
        """Editor background color."""
        return self._background

    @property
    def foreground(self) -> Color:
        """Default text color."""
        return self._foreground

    @property
    def line_number_fg(self) -> Color:
        """Line number foreground (text) color."""
        return self._line_number_fg

    @property
    def line_number_bg(self) -> Color:
        """Line number background (gutter) color."""
        return self._line_number_bg

    def get_style(self, token_type: Any) -> TextStyle:
        """Get text style for a syntax token type.

        Implements token type inheritance:
        1. Check exact match in this theme's styles
        2. Walk up token parent chain in this theme
        3. Fall back to base theme if available
        4. Default to foreground color

        Args:
            token_type: Pygments token type (e.g., Token.Keyword)

        Returns:
            TextStyle with color and formatting
        """
        # Walk up the token hierarchy in this theme
        current = token_type
        while current is not None:
            if current in self._token_styles:
                return self._token_styles[current]
            current = current.parent

        # Fall back to base theme
        if self._base_theme:
            return self._base_theme.get_style(token_type)

        # Default to foreground color with no formatting
        return TextStyle(color=self._foreground)


def load_toml_theme(
    path: Path,
    base_themes: dict[str, "Theme"] | None = None,
) -> TomlTheme:
    """Load theme from TOML file with optional inheritance.

    Args:
        path: Path to TOML theme file
        base_themes: Dictionary of available base themes for inheritance

    Returns:
        TomlTheme instance

    Raises:
        ThemeError: If file not found, invalid TOML, or unknown base theme
    """
    if not path.exists():
        raise ThemeError(f"Theme file not found: {path}")

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ThemeError(f"Invalid TOML in theme file {path}: {e}") from e

    # Handle inheritance
    base_theme = None
    if "extends" in data:
        base_name = data["extends"]
        if base_themes is None or base_name not in base_themes:
            raise ThemeError(
                f"Unknown base theme: {base_name}. "
                f"Available: {', '.join(sorted(base_themes.keys())) if base_themes else 'none'}"
            )
        base_theme = base_themes[base_name]

    # Derive name from filename (without extension)
    name = path.stem

    return TomlTheme(name, data, base_theme)
