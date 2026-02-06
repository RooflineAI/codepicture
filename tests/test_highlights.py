"""Tests for line range parser and highlight color resolver.

Tests cover:
- parse_line_ranges: single lines, ranges, mixed, empty input, whitespace,
  out-of-bounds, reversed ranges, invalid syntax, non-default line_number_offset
- resolve_highlight_color: None (default), 6-char hex, 8-char hex
- DEFAULT_HIGHLIGHT_COLOR constant
"""

import pytest

from codepicture.errors import InputError
from codepicture.render.highlights import (
    DEFAULT_HIGHLIGHT_COLOR,
    HIGHLIGHT_CORNER_RADIUS,
    parse_line_ranges,
    resolve_highlight_color,
)


class TestDefaultHighlightColor:
    """Tests for the DEFAULT_HIGHLIGHT_COLOR constant."""

    def test_default_color_is_warm_yellow(self):
        """Default highlight color is warm yellow (#FFE650) at ~25% opacity."""
        assert DEFAULT_HIGHLIGHT_COLOR.r == 255
        assert DEFAULT_HIGHLIGHT_COLOR.g == 230
        assert DEFAULT_HIGHLIGHT_COLOR.b == 80
        assert DEFAULT_HIGHLIGHT_COLOR.a == 64

    def test_highlight_corner_radius_is_zero(self):
        """Highlight corner radius starts at 0 (sharp rectangles)."""
        assert HIGHLIGHT_CORNER_RADIUS == 0


class TestParseLineRangesSingleLines:
    """Tests for parsing single line numbers."""

    def test_single_line(self):
        """Single line spec converts to 0-based index."""
        result = parse_line_ranges(["3"], 10)
        assert result == {2}

    def test_first_line(self):
        """First line (1) converts to index 0."""
        result = parse_line_ranges(["1"], 10)
        assert result == {0}

    def test_last_line(self):
        """Last line converts to last index."""
        result = parse_line_ranges(["10"], 10)
        assert result == {9}

    def test_whitespace_stripped(self):
        """Whitespace around spec is stripped."""
        result = parse_line_ranges([" 3 "], 10)
        assert result == {2}


class TestParseLineRangesRanges:
    """Tests for parsing line ranges."""

    def test_range(self):
        """Range spec converts to set of 0-based indices."""
        result = parse_line_ranges(["7-12"], 15)
        assert result == {6, 7, 8, 9, 10, 11}

    def test_single_line_range(self):
        """Range with same start and end is valid (single line)."""
        result = parse_line_ranges(["5-5"], 10)
        assert result == {4}

    def test_full_range(self):
        """Range covering all lines returns all indices."""
        result = parse_line_ranges(["1-5"], 5)
        assert result == {0, 1, 2, 3, 4}


class TestParseLineRangesMixed:
    """Tests for parsing mixed specs."""

    def test_mixed_singles_and_ranges(self):
        """Mixed single lines and ranges combine correctly."""
        result = parse_line_ranges(["3", "7-12", "15"], 15)
        assert result == {2, 6, 7, 8, 9, 10, 11, 14}

    def test_overlapping_specs(self):
        """Overlapping specs produce a set (no duplicates)."""
        result = parse_line_ranges(["3", "2-4"], 10)
        assert result == {1, 2, 3}

    def test_multiple_ranges(self):
        """Multiple range specs combine correctly."""
        result = parse_line_ranges(["1-3", "5-7"], 10)
        assert result == {0, 1, 2, 4, 5, 6}


class TestParseLineRangesEmpty:
    """Tests for empty input."""

    def test_empty_list(self):
        """Empty specs list returns empty set."""
        result = parse_line_ranges([], 10)
        assert result == set()


class TestParseLineRangesOffset:
    """Tests for non-default line_number_offset."""

    def test_offset_zero_single(self):
        """With offset=0, line 1 maps to index 1."""
        result = parse_line_ranges(["1"], 5, line_number_offset=0)
        assert result == {1}

    def test_offset_zero_first_line(self):
        """With offset=0, line 0 maps to index 0."""
        result = parse_line_ranges(["0"], 5, line_number_offset=0)
        assert result == {0}

    def test_offset_zero_range(self):
        """With offset=0, range maps correctly."""
        result = parse_line_ranges(["0-2"], 5, line_number_offset=0)
        assert result == {0, 1, 2}


class TestParseLineRangesErrors:
    """Tests for error cases."""

    def test_out_of_bounds_high(self):
        """Line number exceeding total_lines raises InputError."""
        with pytest.raises(InputError, match="out of range"):
            parse_line_ranges(["11"], 10)

    def test_out_of_bounds_zero_with_default_offset(self):
        """Line 0 with default offset=1 raises InputError."""
        with pytest.raises(InputError, match="out of range"):
            parse_line_ranges(["0"], 5)

    def test_out_of_bounds_in_range(self):
        """Range extending past total_lines raises InputError."""
        with pytest.raises(InputError, match="out of range"):
            parse_line_ranges(["8-12"], 10)

    def test_reversed_range(self):
        """Reversed range (start > end) raises InputError."""
        with pytest.raises(InputError, match="must not exceed end"):
            parse_line_ranges(["5-3"], 10)

    def test_invalid_syntax_letters(self):
        """Non-numeric spec raises InputError."""
        with pytest.raises(InputError, match="Invalid line spec"):
            parse_line_ranges(["abc"], 10)

    def test_invalid_syntax_special_chars(self):
        """Special characters in spec raise InputError."""
        with pytest.raises(InputError, match="Invalid line spec"):
            parse_line_ranges(["3..5"], 10)

    def test_invalid_syntax_empty_string(self):
        """Empty string spec raises InputError."""
        with pytest.raises(InputError, match="Invalid line spec"):
            parse_line_ranges([""], 10)

    def test_invalid_syntax_negative(self):
        """Negative number raises InputError (no match for leading -)."""
        with pytest.raises(InputError, match="Invalid line spec"):
            parse_line_ranges(["-3"], 10)

    def test_out_of_bounds_offset_zero(self):
        """With offset=0, line number >= total_lines raises InputError."""
        with pytest.raises(InputError, match="out of range"):
            parse_line_ranges(["5"], 5, line_number_offset=0)


class TestResolveHighlightColor:
    """Tests for resolve_highlight_color."""

    def test_none_returns_default(self):
        """None input returns DEFAULT_HIGHLIGHT_COLOR."""
        color = resolve_highlight_color(None)
        assert color == DEFAULT_HIGHLIGHT_COLOR

    def test_eight_char_hex(self):
        """8-char hex (#RRGGBBAA) is parsed with explicit alpha."""
        color = resolve_highlight_color("#FF000040")
        assert color.r == 255
        assert color.g == 0
        assert color.b == 0
        assert color.a == 64

    def test_six_char_hex_gets_default_alpha(self):
        """6-char hex (#RRGGBB) gets default ~25% alpha (64)."""
        color = resolve_highlight_color("#FF0000")
        assert color.r == 255
        assert color.g == 0
        assert color.b == 0
        assert color.a == 64

    def test_six_char_hex_green(self):
        """6-char hex green gets default alpha."""
        color = resolve_highlight_color("#00FF00")
        assert color.r == 0
        assert color.g == 255
        assert color.b == 0
        assert color.a == 64

    def test_eight_char_hex_full_alpha(self):
        """8-char hex with full alpha preserves alpha."""
        color = resolve_highlight_color("#FF0000FF")
        assert color.r == 255
        assert color.g == 0
        assert color.b == 0
        assert color.a == 255

    def test_eight_char_hex_zero_alpha(self):
        """8-char hex with zero alpha preserves alpha."""
        color = resolve_highlight_color("#FF000000")
        assert color.r == 255
        assert color.g == 0
        assert color.b == 0
        assert color.a == 0
