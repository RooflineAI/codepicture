"""Tests for word wrapping and window width/height features."""

import pytest

from codepicture import LayoutEngine
from codepicture.config import RenderConfig
from codepicture.highlight import TokenInfo


@pytest.fixture
def measurer(pango_measurer):
    """Reuse the shared pango_measurer fixture."""
    return pango_measurer


def _make_line(text: str, line_idx: int = 0) -> list[TokenInfo]:
    """Create a single-token line from a text string."""
    return [TokenInfo(text, "Token.Text", line_idx, 0)]


def _make_long_line(length: int, line_idx: int = 0) -> list[TokenInfo]:
    """Create a line of repeating 'x' characters."""
    return [TokenInfo("x" * length, "Token.Text", line_idx, 0)]


class TestWindowWidthNone:
    """Tests for default behavior when window_width is None."""

    def test_window_width_none_produces_empty_display_lines(self, measurer):
        """RenderConfig with default window_width=None produces empty display_lines."""
        config = RenderConfig()
        engine = LayoutEngine(measurer, config)
        lines = [_make_line("hello")]
        metrics = engine.calculate_metrics(lines)
        assert metrics.display_lines == ()

    def test_window_width_none_backward_compatible(self, measurer):
        """Setting window_width=None produces identical metrics to current behavior."""
        config_default = RenderConfig()
        config_explicit_none = RenderConfig(window_width=None, window_height=None)

        engine_default = LayoutEngine(measurer, config_default)
        engine_explicit = LayoutEngine(measurer, config_explicit_none)

        lines = [
            _make_line("def foo():", 0),
            _make_line("    pass", 1),
        ]

        metrics_default = engine_default.calculate_metrics(lines)
        metrics_explicit = engine_explicit.calculate_metrics(lines)

        assert metrics_default.canvas_width == metrics_explicit.canvas_width
        assert metrics_default.canvas_height == metrics_explicit.canvas_height
        assert metrics_default.code_x == metrics_explicit.code_x
        assert metrics_default.code_y == metrics_explicit.code_y
        assert metrics_default.gutter_width == metrics_explicit.gutter_width


class TestWindowWidthAutoSize:
    """Tests when window_width is wide enough for all content."""

    def test_window_width_auto_sizes_without_wrap(self, measurer):
        """When window_width is wide enough, display_lines maps 1:1."""
        config = RenderConfig(window_width=2000)
        engine = LayoutEngine(measurer, config)
        lines = [_make_line("short", 0), _make_line("also short", 1)]
        metrics = engine.calculate_metrics(lines)

        assert len(metrics.display_lines) == 2
        for i, dline in enumerate(metrics.display_lines):
            assert dline.source_line_idx == i
            assert dline.is_continuation is False
            assert dline.char_offset == 0


class TestWindowWidthWrapping:
    """Tests for word wrapping behavior."""

    def test_window_width_wraps_long_line(self, measurer):
        """A source line exceeding max_code_chars produces multiple display_lines."""
        # Use a narrow width to force wrapping of a 100-char line
        config = RenderConfig(window_width=300, padding=20, show_line_numbers=False)
        engine = LayoutEngine(measurer, config)

        lines = [_make_long_line(100)]
        metrics = engine.calculate_metrics(lines)

        # Should have more than 1 display line
        assert len(metrics.display_lines) > 1

        # First display line is not a continuation
        assert metrics.display_lines[0].is_continuation is False
        assert metrics.display_lines[0].char_offset == 0

        # Subsequent display lines are continuations
        for dline in metrics.display_lines[1:]:
            assert dline.is_continuation is True
            assert dline.source_line_idx == 0

    def test_continuation_lines_have_no_line_number_gap(self, measurer):
        """Continuation display lines have is_continuation=True (no line number)."""
        config = RenderConfig(window_width=200, padding=10, show_line_numbers=True)
        engine = LayoutEngine(measurer, config)

        lines = [_make_long_line(200)]
        metrics = engine.calculate_metrics(lines)

        continuations = [d for d in metrics.display_lines if d.is_continuation]
        assert len(continuations) > 0
        for c in continuations:
            assert c.is_continuation is True

    def test_wrap_indent_chars_applied(self, measurer):
        """Continuation display lines have reduced capacity due to wrap indent."""
        config = RenderConfig(window_width=300, padding=10, show_line_numbers=False)
        engine = LayoutEngine(measurer, config)

        lines = [_make_long_line(200)]
        metrics = engine.calculate_metrics(lines)

        assert metrics.wrap_indent_chars == 2

        # First display line should cover more chars than continuations
        first = metrics.display_lines[0]
        if len(metrics.display_lines) > 2:
            second = metrics.display_lines[1]
            third = metrics.display_lines[2]
            # Calculate chars per chunk
            first_chars = second.char_offset - first.char_offset
            second_chars = third.char_offset - second.char_offset
            # First chunk should be wider by wrap_indent_chars
            assert first_chars == second_chars + metrics.wrap_indent_chars


class TestWindowHeight:
    """Tests for window height control."""

    def test_window_height_sets_canvas_height(self, measurer):
        """Setting window_height directly controls canvas_height."""
        config = RenderConfig(window_height=400)
        engine = LayoutEngine(measurer, config)
        lines = [_make_line("hello")]
        metrics = engine.calculate_metrics(lines)
        assert metrics.canvas_height == 400

    def test_window_width_sets_canvas_width(self, measurer):
        """Setting window_width directly controls canvas_width."""
        config = RenderConfig(window_width=600)
        engine = LayoutEngine(measurer, config)
        lines = [_make_line("hello")]
        metrics = engine.calculate_metrics(lines)
        assert metrics.canvas_width == 600


class TestDisplayLinesContentHeight:
    """Tests for content height behavior with wrapping."""

    def test_display_lines_count_affects_content_height(self, measurer):
        """Wrapped lines produce taller content_height than unwrapped."""
        lines = [_make_long_line(200)]

        # Narrow window forces wrapping
        config_narrow = RenderConfig(
            window_width=300, padding=10, show_line_numbers=False
        )
        engine_narrow = LayoutEngine(measurer, config_narrow)
        metrics_narrow = engine_narrow.calculate_metrics(lines)

        # Wide window avoids wrapping
        config_wide = RenderConfig(
            window_width=5000, padding=10, show_line_numbers=False
        )
        engine_wide = LayoutEngine(measurer, config_wide)
        metrics_wide = engine_wide.calculate_metrics(lines)

        # Narrow (wrapped) should have taller content than wide (not wrapped)
        assert metrics_narrow.content_height > metrics_wide.content_height
        assert len(metrics_narrow.display_lines) > len(metrics_wide.display_lines)
