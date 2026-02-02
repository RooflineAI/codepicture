"""Tests for the layout module."""

import pytest

from codepicture import LayoutEngine, LayoutMetrics, PangoTextMeasurer, LayoutError
from codepicture.config import RenderConfig
from codepicture.highlight import TokenInfo


class TestPangoTextMeasurer:
    """Tests for PangoTextMeasurer."""

    def test_measure_text_returns_positive_dimensions(self, pango_measurer):
        """Text measurement returns positive width and height."""
        width, height = pango_measurer.measure_text("Hello", "JetBrains Mono", 16)
        assert width > 0
        assert height > 0

    def test_measure_empty_string_returns_zero_dimensions(self, pango_measurer):
        """Empty string returns zero width and zero height."""
        width, height = pango_measurer.measure_text("", "JetBrains Mono", 16)
        assert width == 0.0
        assert height == 0.0

    def test_measure_monospace_consistency(self, pango_measurer):
        """Monospace font has consistent character widths."""
        w1, _ = pango_measurer.measure_text("M", "JetBrains Mono", 16)
        w2, _ = pango_measurer.measure_text("i", "JetBrains Mono", 16)
        # In a true monospace font, all characters should have same width
        assert abs(w1 - w2) < 0.1  # Allow tiny floating point variance

    def test_measure_font_size_affects_dimensions(self, pango_measurer):
        """Larger font size produces larger dimensions."""
        w1, h1 = pango_measurer.measure_text("M", "JetBrains Mono", 12)
        w2, h2 = pango_measurer.measure_text("M", "JetBrains Mono", 24)
        assert w2 > w1
        assert h2 > h1

    def test_measure_text_length_affects_width(self, pango_measurer):
        """Longer text produces wider measurement."""
        w1, _ = pango_measurer.measure_text("a", "JetBrains Mono", 16)
        w2, _ = pango_measurer.measure_text("aaaa", "JetBrains Mono", 16)
        assert w2 > w1
        # Should be approximately 4x for monospace
        assert 3.5 < (w2 / w1) < 4.5

    def test_measure_font_fallback(self, pango_measurer, caplog):
        """Unknown font falls back to JetBrains Mono with warning."""
        import logging
        with caplog.at_level(logging.WARNING):
            width, height = pango_measurer.measure_text(
                "Hello", "NonexistentFontXYZ", 16
            )
        assert width > 0
        assert height > 0
        assert "not found" in caplog.text.lower() or "falling back" in caplog.text.lower()


class TestLayoutEngine:
    """Tests for LayoutEngine."""

    def test_calculate_metrics_returns_layout_metrics(
        self, layout_engine, sample_tokens
    ):
        """calculate_metrics returns a LayoutMetrics instance."""
        metrics = layout_engine.calculate_metrics(sample_tokens)
        assert isinstance(metrics, LayoutMetrics)

    def test_empty_input_raises_layout_error(self, layout_engine):
        """Empty input raises LayoutError."""
        with pytest.raises(LayoutError, match="empty"):
            layout_engine.calculate_metrics([])

    def test_canvas_dimensions_positive(self, layout_engine, sample_tokens):
        """Canvas dimensions are positive integers."""
        metrics = layout_engine.calculate_metrics(sample_tokens)
        assert metrics.canvas_width > 0
        assert metrics.canvas_height > 0
        assert isinstance(metrics.canvas_width, int)
        assert isinstance(metrics.canvas_height, int)

    def test_padding_affects_canvas_size(self, pango_measurer, sample_tokens):
        """Larger padding increases canvas dimensions."""
        config_small = RenderConfig(padding=10)
        config_large = RenderConfig(padding=50)

        engine_small = LayoutEngine(pango_measurer, config_small)
        engine_large = LayoutEngine(pango_measurer, config_large)

        metrics_small = engine_small.calculate_metrics(sample_tokens)
        metrics_large = engine_large.calculate_metrics(sample_tokens)

        # Difference should be 2 * (50 - 10) = 80 per dimension
        assert metrics_large.canvas_width - metrics_small.canvas_width == 80
        assert metrics_large.canvas_height - metrics_small.canvas_height == 80

    def test_line_height_affects_vertical_spacing(self, pango_measurer, sample_tokens):
        """Line height multiplier affects total height."""
        config_normal = RenderConfig(line_height=1.0)
        config_tall = RenderConfig(line_height=2.0)

        engine_normal = LayoutEngine(pango_measurer, config_normal)
        engine_tall = LayoutEngine(pango_measurer, config_tall)

        metrics_normal = engine_normal.calculate_metrics(sample_tokens)
        metrics_tall = engine_tall.calculate_metrics(sample_tokens)

        # Tall line height should produce ~2x content height
        ratio = metrics_tall.content_height / metrics_normal.content_height
        assert 1.9 < ratio < 2.1

    def test_gutter_width_scales_with_line_count(self, pango_measurer):
        """Gutter width increases with more lines (more digits)."""
        config = RenderConfig()
        engine = LayoutEngine(pango_measurer, config)

        # Single digit line numbers (1-9)
        lines_9 = [[TokenInfo("x", "Token.Text", i, 0)] for i in range(9)]
        metrics_9 = engine.calculate_metrics(lines_9)

        # Triple digit line numbers (100+)
        lines_100 = [[TokenInfo("x", "Token.Text", i, 0)] for i in range(100)]
        metrics_100 = engine.calculate_metrics(lines_100)

        # Gutter should be wider for 100 lines (3 digits vs 1 digit)
        assert metrics_100.gutter_width > metrics_9.gutter_width

    def test_line_numbers_disabled(self, pango_measurer, sample_tokens):
        """Disabling line numbers sets gutter width to zero."""
        config = RenderConfig(show_line_numbers=False)
        engine = LayoutEngine(pango_measurer, config)
        metrics = engine.calculate_metrics(sample_tokens)

        assert metrics.gutter_width == 0

    def test_font_size_affects_dimensions(self, pango_measurer, sample_tokens):
        """Larger font size produces larger canvas."""
        config_small = RenderConfig(font_size=10)
        config_large = RenderConfig(font_size=20)

        engine_small = LayoutEngine(pango_measurer, config_small)
        engine_large = LayoutEngine(pango_measurer, config_large)

        metrics_small = engine_small.calculate_metrics(sample_tokens)
        metrics_large = engine_large.calculate_metrics(sample_tokens)

        assert metrics_large.canvas_width > metrics_small.canvas_width
        assert metrics_large.canvas_height > metrics_small.canvas_height

    def test_code_x_after_gutter(self, layout_engine, sample_tokens):
        """Code area starts after gutter plus gap."""
        metrics = layout_engine.calculate_metrics(sample_tokens)

        # code_x should be padding + gutter_width + LINE_NUMBER_GAP
        expected_code_x = (
            metrics.content_x + metrics.gutter_width + LayoutEngine.LINE_NUMBER_GAP
        )
        assert abs(metrics.code_x - expected_code_x) < 0.01

    def test_metrics_consistency(self, layout_engine, sample_tokens):
        """Metrics are internally consistent."""
        metrics = layout_engine.calculate_metrics(sample_tokens)

        # Content fits within canvas
        assert metrics.content_x >= 0
        assert metrics.content_y >= 0
        assert metrics.content_x + metrics.content_width <= metrics.canvas_width
        assert metrics.content_y + metrics.content_height <= metrics.canvas_height

        # Code area within content
        assert metrics.code_x >= metrics.content_x
        assert metrics.code_y >= metrics.content_y


    def test_window_width_none_backward_compatible(self, pango_measurer, sample_tokens):
        """Setting window_width=None produces identical LayoutMetrics as default."""
        config_default = RenderConfig()
        config_none = RenderConfig(window_width=None, window_height=None)

        engine_default = LayoutEngine(pango_measurer, config_default)
        engine_none = LayoutEngine(pango_measurer, config_none)

        metrics_default = engine_default.calculate_metrics(sample_tokens)
        metrics_none = engine_none.calculate_metrics(sample_tokens)

        assert metrics_default.canvas_width == metrics_none.canvas_width
        assert metrics_default.canvas_height == metrics_none.canvas_height
        assert metrics_default.code_x == metrics_none.code_x
        assert metrics_default.code_width == metrics_none.code_width
        assert metrics_default.gutter_width == metrics_none.gutter_width
        assert metrics_default.content_height == metrics_none.content_height
        assert metrics_none.display_lines == ()


class TestLayoutMetrics:
    """Tests for LayoutMetrics dataclass."""

    def test_layout_metrics_immutable(self):
        """LayoutMetrics is immutable (frozen)."""
        metrics = LayoutMetrics(
            canvas_width=800,
            canvas_height=600,
            content_x=40.0,
            content_y=40.0,
            content_width=720.0,
            content_height=520.0,
            gutter_width=30.0,
            gutter_x=40.0,
            code_x=82.0,
            code_y=40.0,
            code_width=688.0,
            line_height_px=22.4,
            char_width=9.6,
            baseline_offset=12.8,
        )

        with pytest.raises(AttributeError):
            metrics.canvas_width = 1000
