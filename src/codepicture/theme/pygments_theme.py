"""Pygments theme wrapper implementing the Theme protocol.

Wraps Pygments Style classes to provide a Theme implementation that maps
token types to TextStyle objects.
"""

from typing import Any

from pygments.styles import get_style_by_name
from pygments.token import Token

from ..core.types import Color, TextStyle


class PygmentsTheme:
    """Theme implementation wrapping a Pygments Style.

    Provides the Theme protocol interface by wrapping a Pygments style class.
    Handles token type inheritance and color fallbacks.

    Attributes:
        name: Theme name (e.g., 'monokai', 'catppuccin-mocha')
        background: Editor background color
        foreground: Default text color
        line_number_fg: Line number text color
        line_number_bg: Line number gutter background color
    """

    __slots__ = (
        "_name",
        "_style",
        "_background",
        "_foreground",
        "_line_number_fg",
        "_line_number_bg",
    )

    def __init__(self, style_name: str) -> None:
        """Initialize theme from a Pygments style name.

        Args:
            style_name: Name of a Pygments style (e.g., 'monokai')

        Raises:
            pygments.util.ClassNotFound: If style_name is not a valid style
        """
        self._name = style_name
        self._style = get_style_by_name(style_name)

        # Extract background color from style class
        bg_color = getattr(self._style, "background_color", "#1e1e2e")
        if bg_color:
            self._background = Color.from_hex(bg_color)
        else:
            self._background = Color.from_hex("#1e1e2e")  # Default dark background

        # Extract foreground from default Token style
        default_style = self._style.style_for_token(Token)
        fg_hex = default_style.get("color")
        if fg_hex:
            self._foreground = Color.from_hex(f"#{fg_hex}")
        else:
            self._foreground = Color.from_hex("#cdd6f4")  # Default light text

        # Line numbers: derive from foreground with reduced brightness
        # Use a muted version of foreground color
        self._line_number_fg = Color(
            r=max(0, self._foreground.r - 60),
            g=max(0, self._foreground.g - 60),
            b=max(0, self._foreground.b - 60),
            a=self._foreground.a,
        )

        # Line number background: slightly different from main background
        self._line_number_bg = Color(
            r=max(0, self._background.r - 10),
            g=max(0, self._background.g - 10),
            b=max(0, self._background.b - 10),
            a=self._background.a,
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

        Uses Pygments style_for_token() which handles token type inheritance.
        Falls back to foreground color if token has no color defined.

        Args:
            token_type: Pygments token type (e.g., Token.Keyword)

        Returns:
            TextStyle with color and formatting
        """
        style_dict = self._style.style_for_token(token_type)

        # Color is hex string without # or None
        color_hex = style_dict.get("color")
        if color_hex:
            color = Color.from_hex(f"#{color_hex}")
        else:
            # Fallback to foreground color (per RESEARCH.md Pitfall 5)
            color = self._foreground

        return TextStyle(
            color=color,
            bold=style_dict.get("bold", False) or False,
            italic=style_dict.get("italic", False) or False,
            underline=style_dict.get("underline", False) or False,
        )
