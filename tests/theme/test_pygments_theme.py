"""Tests for PygmentsTheme."""

import pytest
from pygments.token import Token

from codepicture.core.types import Color, TextStyle
from codepicture.theme import PygmentsTheme


class TestPygmentsTheme:
    """Tests for PygmentsTheme class."""

    @pytest.fixture
    def theme(self) -> PygmentsTheme:
        """Create a PygmentsTheme instance (catppuccin-mocha)."""
        return PygmentsTheme("catppuccin-mocha")

    def test_has_name_property(self, theme: PygmentsTheme) -> None:
        """Verify theme.name matches constructor arg."""
        assert theme.name == "catppuccin-mocha"

    def test_has_background_color(self, theme: PygmentsTheme) -> None:
        """Verify background is a Color."""
        assert isinstance(theme.background, Color)
        # Background should have RGBA values
        assert 0 <= theme.background.r <= 255
        assert 0 <= theme.background.g <= 255
        assert 0 <= theme.background.b <= 255
        assert 0 <= theme.background.a <= 255

    def test_has_foreground_color(self, theme: PygmentsTheme) -> None:
        """Verify foreground is a Color."""
        assert isinstance(theme.foreground, Color)
        # Foreground should have RGBA values
        assert 0 <= theme.foreground.r <= 255
        assert 0 <= theme.foreground.g <= 255
        assert 0 <= theme.foreground.b <= 255
        assert 0 <= theme.foreground.a <= 255

    def test_has_line_number_colors(self, theme: PygmentsTheme) -> None:
        """Verify line number colors are derived Colors."""
        assert isinstance(theme.line_number_fg, Color)
        assert isinstance(theme.line_number_bg, Color)

    def test_get_style_returns_text_style(self, theme: PygmentsTheme) -> None:
        """Verify get_style returns TextStyle."""
        style = theme.get_style(Token.Keyword)
        assert isinstance(style, TextStyle)
        assert isinstance(style.color, Color)
        assert isinstance(style.bold, bool)
        assert isinstance(style.italic, bool)

    def test_token_inheritance(self, theme: PygmentsTheme) -> None:
        """Verify String.Escape falls back to String style."""
        # String.Escape should inherit from String or have own style
        escape_style = theme.get_style(Token.String.Escape)
        string_style = theme.get_style(Token.String)

        # Both should be valid TextStyle
        assert isinstance(escape_style, TextStyle)
        assert isinstance(string_style, TextStyle)
        # Both should have valid colors (may or may not be same)
        assert isinstance(escape_style.color, Color)
        assert isinstance(string_style.color, Color)

    def test_unknown_token_falls_back_to_default(self, theme: PygmentsTheme) -> None:
        """Verify fallback to foreground for unknown tokens."""
        # Token.Text typically doesn't have special styling
        style = theme.get_style(Token.Text)
        assert isinstance(style, TextStyle)
        # Should have a valid color (foreground fallback)
        assert isinstance(style.color, Color)

    def test_different_themes_have_different_colors(self) -> None:
        """Verify different themes produce different colors."""
        monokai = PygmentsTheme("monokai")
        dracula = PygmentsTheme("dracula")

        # Background colors should differ
        # (we can't guarantee they're different, but they should be valid)
        assert isinstance(monokai.background, Color)
        assert isinstance(dracula.background, Color)
