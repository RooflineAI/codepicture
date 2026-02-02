"""Tests for PygmentsHighlighter."""

import pytest
from pygments.token import Token

from codepicture.errors import HighlightError
from codepicture.highlight import PygmentsHighlighter, TokenInfo


class TestHighlight:
    """Tests for PygmentsHighlighter.highlight() method."""

    @pytest.fixture
    def highlighter(self) -> PygmentsHighlighter:
        """Create a highlighter instance."""
        return PygmentsHighlighter()

    def test_tokenizes_python_code(self, highlighter: PygmentsHighlighter) -> None:
        """Verify tokens are returned for Python code."""
        code = "x = 1"
        lines = highlighter.highlight(code, "python")

        assert len(lines) >= 1
        # Flatten all tokens
        tokens = [token for line in lines for token in line]
        assert len(tokens) > 0
        # Check we have token text matching the code
        combined = "".join(t.text for t in tokens)
        assert combined == code

    def test_tokens_have_position_tracking(
        self, highlighter: PygmentsHighlighter
    ) -> None:
        """Verify line/column in TokenInfo."""
        code = "def foo():\n    pass"
        lines = highlighter.highlight(code, "python")

        # First line, first token
        first_token = lines[0][0]
        assert isinstance(first_token, TokenInfo)
        assert first_token.line == 0
        assert first_token.column == 0

        # Second line should have line=1
        assert len(lines) >= 2
        second_line_first = lines[1][0]
        assert second_line_first.line == 1

    def test_multiline_string_splits_correctly(
        self, highlighter: PygmentsHighlighter
    ) -> None:
        """Verify multiline tokens split on newlines."""
        code = '"""line1\nline2"""'
        lines = highlighter.highlight(code, "python")

        # Should have 2 lines (multiline string spans them)
        assert len(lines) == 2

    def test_empty_lines_preserved(self, highlighter: PygmentsHighlighter) -> None:
        """Verify empty lines produce empty token lists."""
        code = "x = 1\n\ny = 2"
        lines = highlighter.highlight(code, "python")

        # Should have 3 lines with middle line potentially empty
        assert len(lines) == 3

    def test_unknown_language_raises_error(
        self, highlighter: PygmentsHighlighter
    ) -> None:
        """Verify HighlightError for unknown language."""
        with pytest.raises(HighlightError) as exc_info:
            highlighter.highlight("code", "notarealang")

        assert "Unknown language: notarealang" in str(exc_info.value)
        # Error should include available languages
        assert "Available languages include:" in str(exc_info.value)

    def test_language_alias_resolved(self, highlighter: PygmentsHighlighter) -> None:
        """Verify 'yml' works (resolves to yaml)."""
        code = "key: value"
        lines = highlighter.highlight(code, "yml")

        # Should not raise and should produce tokens
        assert len(lines) >= 1
        tokens = [token for line in lines for token in line]
        assert len(tokens) > 0

    def test_tokens_have_correct_token_type(
        self, highlighter: PygmentsHighlighter
    ) -> None:
        """Verify token types are Pygments tokens."""
        code = "def foo(): pass"
        lines = highlighter.highlight(code, "python")

        tokens = [token for line in lines for token in line]
        # Find the keyword token
        keyword_tokens = [t for t in tokens if t.text == "def"]
        assert len(keyword_tokens) == 1
        assert keyword_tokens[0].token_type in Token.Keyword


class TestDetectLanguage:
    """Tests for PygmentsHighlighter.detect_language() method."""

    @pytest.fixture
    def highlighter(self) -> PygmentsHighlighter:
        """Create a highlighter instance."""
        return PygmentsHighlighter()

    def test_detects_python_from_extension(
        self, highlighter: PygmentsHighlighter
    ) -> None:
        """Verify .py -> python."""
        lang = highlighter.detect_language("", filename="test.py")
        assert lang in ("python", "python3")

    def test_detects_rust_from_extension(
        self, highlighter: PygmentsHighlighter
    ) -> None:
        """Verify .rs -> rust."""
        lang = highlighter.detect_language("", filename="test.rs")
        assert lang == "rust"

    def test_detects_javascript_from_extension(
        self, highlighter: PygmentsHighlighter
    ) -> None:
        """Verify .js -> javascript."""
        lang = highlighter.detect_language("", filename="test.js")
        assert lang in ("javascript", "js")

    def test_unknown_extension_raises_error(
        self, highlighter: PygmentsHighlighter
    ) -> None:
        """Verify unknown extension raises HighlightError."""
        with pytest.raises(HighlightError) as exc_info:
            highlighter.detect_language("", filename="test.notareallanguage123")

        assert "Could not detect language" in str(exc_info.value)


class TestListLanguages:
    """Tests for PygmentsHighlighter.list_languages() method."""

    @pytest.fixture
    def highlighter(self) -> PygmentsHighlighter:
        """Create a highlighter instance."""
        return PygmentsHighlighter()

    def test_returns_sorted_list(self, highlighter: PygmentsHighlighter) -> None:
        """Verify list is sorted."""
        languages = highlighter.list_languages()
        assert languages == sorted(languages)

    def test_includes_common_languages(self, highlighter: PygmentsHighlighter) -> None:
        """Verify python, rust, javascript in list."""
        languages = highlighter.list_languages()
        assert "python" in languages
        assert "rust" in languages
        assert "javascript" in languages

    def test_returns_list_type(self, highlighter: PygmentsHighlighter) -> None:
        """Verify return type is list."""
        languages = highlighter.list_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
