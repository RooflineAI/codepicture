"""Tests for text normalization utilities."""

import pytest

from codepicture.text.normalize import normalize_tabs


class TestNormalizeTabs:
    """Test normalize_tabs function."""

    def test_single_tab(self):
        """One tab becomes 4 spaces (default)."""
        result = normalize_tabs("\thello")
        assert result == "    hello"

    def test_multiple_tabs(self):
        """Multiple tabs all converted."""
        result = normalize_tabs("\t\thello\tworld")
        assert result == "        hello    world"

    def test_custom_tab_width(self):
        """tab_width=2 produces 2 spaces."""
        result = normalize_tabs("\thello", tab_width=2)
        assert result == "  hello"
        result_8 = normalize_tabs("\thello", tab_width=8)
        assert result_8 == "        hello"

    def test_no_tabs(self):
        """String without tabs unchanged."""
        original = "    hello world"
        result = normalize_tabs(original)
        assert result == original

    def test_mixed_content(self):
        """Tabs and spaces preserved correctly."""
        # Tab followed by spaces
        result = normalize_tabs("\t  hello")
        assert result == "      hello"  # 4 spaces + 2 original spaces

        # Spaces followed by tab
        result = normalize_tabs("  \thello")
        assert result == "      hello"  # 2 original spaces + 4 from tab

    def test_tab_width_range_min(self):
        """tab_width < 1 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            normalize_tabs("hello", tab_width=0)
        assert "tab_width must be 1-8" in str(exc_info.value)

    def test_tab_width_range_max(self):
        """tab_width > 8 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            normalize_tabs("hello", tab_width=9)
        assert "tab_width must be 1-8" in str(exc_info.value)

    def test_tab_width_boundary_valid(self):
        """tab_width 1 and 8 are valid."""
        result_1 = normalize_tabs("\thello", tab_width=1)
        assert result_1 == " hello"
        result_8 = normalize_tabs("\thello", tab_width=8)
        assert result_8 == "        hello"

    def test_empty_string(self):
        """Empty string returns empty."""
        assert normalize_tabs("") == ""

    def test_multiline_tabs(self):
        """Tabs in multiline strings all converted."""
        code = "def foo():\n\treturn 42\n"
        result = normalize_tabs(code)
        assert result == "def foo():\n    return 42\n"

    def test_only_tabs(self):
        """String with only tabs."""
        result = normalize_tabs("\t\t\t")
        assert result == "            "  # 3 * 4 = 12 spaces
