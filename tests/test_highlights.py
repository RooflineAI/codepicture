"""Tests for line range parser, highlight color resolver, and named styles.

Tests cover:
- parse_line_ranges: single lines, ranges, mixed, empty input, whitespace,
  out-of-bounds, reversed ranges, invalid syntax, non-default line_number_offset
- resolve_highlight_color: None (default), 6-char hex, 8-char hex
- DEFAULT_HIGHLIGHT_COLOR constant
- HighlightStyle enum: members, values, string enum behavior
- DEFAULT_STYLE_COLORS: D-12 palette verification
- GUTTER_INDICATORS: D-10 indicator mapping
- parse_highlight_specs: spec parsing with/without style, last-wins, errors
- resolve_style_color: default colors, overrides, alpha handling
- FOCUS_DIM_OPACITY: constant value and range
"""

import pytest

from codepicture.core.types import Color
from codepicture.errors import InputError
from codepicture.render.highlights import (
    DEFAULT_HIGHLIGHT_COLOR,
    DEFAULT_STYLE_COLORS,
    FOCUS_DIM_OPACITY,
    GUTTER_BAR_WIDTH,
    GUTTER_INDICATORS,
    HIGHLIGHT_CORNER_RADIUS,
    HighlightStyle,
    parse_highlight_specs,
    parse_line_ranges,
    resolve_highlight_color,
    resolve_style_color,
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


# --- Phase 13 tests: Named highlight styles ---


class TestHighlightStyleEnum:
    """Tests for the HighlightStyle enum."""

    def test_four_styles_exist(self):
        """HighlightStyle has exactly 4 members."""
        assert len(HighlightStyle) == 4

    def test_style_values(self):
        """Enum values match expected string names."""
        assert HighlightStyle.HIGHLIGHT.value == "highlight"
        assert HighlightStyle.ADD.value == "add"
        assert HighlightStyle.REMOVE.value == "remove"
        assert HighlightStyle.FOCUS.value == "focus"

    def test_style_is_string_enum(self):
        """HighlightStyle members are also strings."""
        assert isinstance(HighlightStyle.ADD, str)
        assert isinstance(HighlightStyle.REMOVE, str)


class TestDefaultStyleColors:
    """Tests for DEFAULT_STYLE_COLORS (D-12 palette)."""

    def test_highlight_color(self):
        assert DEFAULT_STYLE_COLORS[HighlightStyle.HIGHLIGHT] == Color(255, 230, 80, 64)

    def test_add_color(self):
        assert DEFAULT_STYLE_COLORS[HighlightStyle.ADD] == Color(0, 204, 64, 64)

    def test_remove_color(self):
        assert DEFAULT_STYLE_COLORS[HighlightStyle.REMOVE] == Color(255, 51, 51, 64)

    def test_focus_color(self):
        assert DEFAULT_STYLE_COLORS[HighlightStyle.FOCUS] == Color(51, 153, 255, 64)


class TestGutterIndicators:
    """Tests for GUTTER_INDICATORS (D-10)."""

    def test_add_shows_plus(self):
        assert GUTTER_INDICATORS[HighlightStyle.ADD] == "+"

    def test_remove_shows_minus(self):
        assert GUTTER_INDICATORS[HighlightStyle.REMOVE] == "-"

    def test_highlight_shows_bar(self):
        assert GUTTER_INDICATORS[HighlightStyle.HIGHLIGHT] is None

    def test_focus_shows_bar(self):
        assert GUTTER_INDICATORS[HighlightStyle.FOCUS] is None


class TestParseHighlightSpecs:
    """Tests for parse_highlight_specs."""

    def test_simple_line_no_style(self):
        """Line without style defaults to HIGHLIGHT."""
        result = parse_highlight_specs(["3"], 10)
        assert result == {2: HighlightStyle.HIGHLIGHT}

    def test_range_no_style(self):
        """Range without style defaults to HIGHLIGHT for all lines."""
        result = parse_highlight_specs(["3-5"], 10)
        assert result == {
            2: HighlightStyle.HIGHLIGHT,
            3: HighlightStyle.HIGHLIGHT,
            4: HighlightStyle.HIGHLIGHT,
        }

    def test_line_with_style(self):
        """Line with :add style suffix."""
        result = parse_highlight_specs(["3:add"], 10)
        assert result == {2: HighlightStyle.ADD}

    def test_range_with_style(self):
        """Range with :remove style suffix."""
        result = parse_highlight_specs(["3-5:remove"], 10)
        assert result[2] == HighlightStyle.REMOVE
        assert result[3] == HighlightStyle.REMOVE
        assert result[4] == HighlightStyle.REMOVE

    def test_last_wins_overlap(self):
        """Last spec wins for overlapping lines (D-03)."""
        result = parse_highlight_specs(["3-5:add", "5:remove"], 10)
        assert result[2] == HighlightStyle.ADD
        assert result[3] == HighlightStyle.ADD
        assert result[4] == HighlightStyle.REMOVE

    def test_multiple_styles(self):
        """Multiple specs with different styles."""
        result = parse_highlight_specs(["1:add", "3:remove", "5:focus"], 10)
        assert len(result) == 3
        assert result[0] == HighlightStyle.ADD
        assert result[2] == HighlightStyle.REMOVE
        assert result[4] == HighlightStyle.FOCUS

    def test_invalid_style_name(self):
        """Unknown style name raises InputError."""
        with pytest.raises(InputError, match="Unknown highlight style"):
            parse_highlight_specs(["3:unknown"], 10)

    def test_invalid_spec_format(self):
        """Invalid spec format raises InputError."""
        with pytest.raises(InputError, match="Invalid highlight spec"):
            parse_highlight_specs(["abc"], 10)

    def test_empty_list(self):
        """Empty specs list returns empty dict."""
        result = parse_highlight_specs([], 10)
        assert result == {}

    def test_whitespace_handling(self):
        """Whitespace around spec is stripped."""
        result = parse_highlight_specs(["  3:add  "], 10)
        assert result == {2: HighlightStyle.ADD}


class TestResolveStyleColor:
    """Tests for resolve_style_color."""

    def test_default_color_for_each_style(self):
        """No overrides returns DEFAULT_STYLE_COLORS for each style."""
        for style in HighlightStyle:
            assert resolve_style_color(style, None) == DEFAULT_STYLE_COLORS[style]

    def test_override_color_8char_hex(self):
        """8-char hex override is used with explicit alpha."""
        color = resolve_style_color(HighlightStyle.ADD, {"add": "#00FF0080"})
        assert color == Color(0, 255, 0, 128)

    def test_override_color_6char_hex_gets_default_alpha(self):
        """6-char hex override gets default alpha (64)."""
        color = resolve_style_color(HighlightStyle.ADD, {"add": "#00FF00"})
        assert color == Color(0, 255, 0, 64)

    def test_override_for_different_style_ignored(self):
        """Override for a different style doesn't affect current style."""
        color = resolve_style_color(HighlightStyle.ADD, {"remove": "#FF0000"})
        assert color == DEFAULT_STYLE_COLORS[HighlightStyle.ADD]

    def test_none_override_uses_default(self):
        """None value in overrides falls back to default."""
        color = resolve_style_color(HighlightStyle.ADD, {"add": None})
        assert color == DEFAULT_STYLE_COLORS[HighlightStyle.ADD]


class TestFocusDimOpacity:
    """Tests for FOCUS_DIM_OPACITY constant."""

    def test_focus_dim_opacity_value(self):
        assert FOCUS_DIM_OPACITY == 0.35

    def test_focus_dim_opacity_in_range(self):
        assert 0.3 <= FOCUS_DIM_OPACITY <= 0.4
