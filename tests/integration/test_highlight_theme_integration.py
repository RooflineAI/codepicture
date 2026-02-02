"""Integration tests for highlight and theme modules.

Verifies the full chain from code tokenization to themed styling:
highlighter.highlight() -> theme.get_style() -> TextStyle with colors
"""

import pytest

from codepicture.core.types import Color, TextStyle
from codepicture.highlight import PygmentsHighlighter
from codepicture.theme import get_theme


class TestHighlightThemeIntegration:
    """Integration tests chaining highlighter through theme styling."""

    def test_highlight_then_style_produces_valid_text_styles(self) -> None:
        """Verify token streams can be styled through theme.get_style()."""
        highlighter = PygmentsHighlighter()
        theme = get_theme("catppuccin-mocha")

        code = "def greet(name):\n    return f'Hello, {name}!'"
        lines = highlighter.highlight(code, "python")

        # Chain through theme styling
        styled_tokens = []
        for line in lines:
            for token in line:
                style = theme.get_style(token.token_type)
                styled_tokens.append((token.text, style))

        # Verify: all tokens got valid TextStyle objects
        assert len(styled_tokens) > 0
        for _text, style in styled_tokens:
            assert isinstance(style, TextStyle)
            assert style.color is not None  # Theme mapped a color
            assert isinstance(style.color, Color)

    @pytest.mark.parametrize(
        "theme_name",
        [
            "monokai",
            "dracula",
            "catppuccin-mocha",
        ],
    )
    def test_all_token_types_get_valid_colors(self, theme_name: str) -> None:
        """Verify every token_type from highlight gets a Color via get_style()."""
        highlighter = PygmentsHighlighter()
        theme = get_theme(theme_name)

        # Use Python code that exercises many token types
        code = """
# Comment
import os
from pathlib import Path

class Greeter:
    '''Docstring.'''

    def __init__(self, name: str) -> None:
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"

if __name__ == "__main__":
    g = Greeter("World")
    print(g.greet())
"""
        lines = highlighter.highlight(code, "python")

        # Collect all unique token types and verify each gets a valid style
        token_types_seen = set()
        for line in lines:
            for token in line:
                token_types_seen.add(token.token_type)
                style = theme.get_style(token.token_type)

                # Every token must get a valid TextStyle with a Color
                assert isinstance(style, TextStyle), (
                    f"Token type {token.token_type} did not return TextStyle"
                )
                assert isinstance(style.color, Color), (
                    f"Token type {token.token_type} did not get a Color"
                )

        # We should have exercised multiple token types
        assert len(token_types_seen) > 5, (
            f"Expected many token types, got {len(token_types_seen)}"
        )

    def test_multiline_code_preserves_structure(self) -> None:
        """Verify multiline code maintains line structure through styling."""
        highlighter = PygmentsHighlighter()
        theme = get_theme("catppuccin-mocha")

        code = "x = 1\ny = 2\nz = 3"
        lines = highlighter.highlight(code, "python")

        # Should have 3 lines
        assert len(lines) == 3

        # Each line should produce styled tokens
        for line_idx, line in enumerate(lines):
            for token in line:
                style = theme.get_style(token.token_type)
                assert isinstance(style, TextStyle)
                # Token should know its line
                assert token.line == line_idx

    def test_rust_code_styling(self) -> None:
        """Verify Rust code tokenization and styling works."""
        highlighter = PygmentsHighlighter()
        theme = get_theme("dracula")

        code = """fn main() {
    let name = "World";
    println!("Hello, {}!", name);
}"""
        lines = highlighter.highlight(code, "rust")

        # Collect and verify all tokens
        all_tokens = []
        for line in lines:
            for token in line:
                style = theme.get_style(token.token_type)
                all_tokens.append((token.text, style))
                assert isinstance(style, TextStyle)
                assert isinstance(style.color, Color)

        # Should have tokens for keywords, strings, punctuation
        assert len(all_tokens) > 10

    def test_javascript_code_styling(self) -> None:
        """Verify JavaScript code tokenization and styling works."""
        highlighter = PygmentsHighlighter()
        theme = get_theme("monokai")

        code = """function greet(name) {
    return `Hello, ${name}!`;
}

console.log(greet("World"));"""
        lines = highlighter.highlight(code, "javascript")

        # Verify all tokens get valid styles
        for line in lines:
            for token in line:
                style = theme.get_style(token.token_type)
                assert isinstance(style, TextStyle)
                assert isinstance(style.color, Color)

        # Should have at least 5 lines
        assert len(lines) >= 5
