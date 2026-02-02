"""Tests for theme loader."""

import pytest

from codepicture.errors import ThemeError
from codepicture.theme import get_theme, list_themes


class TestGetTheme:
    """Tests for get_theme function."""

    def test_loads_monokai(self) -> None:
        """Verify get_theme('monokai') works."""
        theme = get_theme("monokai")
        assert theme.name == "monokai"

    def test_loads_dracula(self) -> None:
        """Verify get_theme('dracula') works."""
        theme = get_theme("dracula")
        assert theme.name == "dracula"

    def test_loads_catppuccin_mocha(self) -> None:
        """Verify get_theme('catppuccin-mocha') works."""
        theme = get_theme("catppuccin-mocha")
        assert theme.name == "catppuccin-mocha"

    @pytest.mark.parametrize(
        "flavor",
        [
            "catppuccin-mocha",
            "catppuccin-macchiato",
            "catppuccin-frappe",
            "catppuccin-latte",
        ],
    )
    def test_loads_all_catppuccin_flavors(self, flavor: str) -> None:
        """Verify all 4 Catppuccin flavors load."""
        theme = get_theme(flavor)
        assert theme.name == flavor

    def test_unknown_theme_raises_error(self) -> None:
        """Verify ThemeError for unknown theme."""
        with pytest.raises(ThemeError) as exc_info:
            get_theme("notarealtheme")

        assert "Unknown theme: notarealtheme" in str(exc_info.value)

    def test_error_includes_available_themes(self) -> None:
        """Verify ThemeError message lists available themes."""
        with pytest.raises(ThemeError) as exc_info:
            get_theme("notarealtheme")

        error_msg = str(exc_info.value)
        assert "Available:" in error_msg
        # Should include at least one built-in theme
        assert "monokai" in error_msg or "dracula" in error_msg

    def test_default_theme_when_none(self) -> None:
        """Verify default theme (catppuccin-mocha) when None."""
        theme = get_theme(None)
        assert theme.name == "catppuccin-mocha"

    def test_resolves_theme_alias(self) -> None:
        """Verify theme alias resolution (catppuccin -> catppuccin-mocha)."""
        theme = get_theme("catppuccin")
        assert theme.name == "catppuccin-mocha"


class TestListThemes:
    """Tests for list_themes function."""

    def test_returns_list(self) -> None:
        """Verify list_themes() returns list."""
        themes = list_themes()
        assert isinstance(themes, list)
        assert len(themes) > 0

    def test_includes_builtin_themes(self) -> None:
        """Verify monokai, dracula, catppuccin-mocha in list."""
        themes = list_themes()
        assert "monokai" in themes
        assert "dracula" in themes
        assert "catppuccin-mocha" in themes

    def test_list_is_sorted(self) -> None:
        """Verify alphabetical order."""
        themes = list_themes()
        assert themes == sorted(themes)

    def test_includes_theme_aliases(self) -> None:
        """Verify aliases are in list."""
        themes = list_themes()
        assert "catppuccin" in themes  # Alias for catppuccin-mocha
