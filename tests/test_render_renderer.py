"""Tests for Renderer class."""

import pytest

from codepicture import Renderer, RenderResult
from codepicture.config import RenderConfig
from codepicture.core.types import OutputFormat
from codepicture.fonts import register_bundled_fonts
from codepicture.theme import get_theme


# Ensure fonts are registered for all tests in this module
@pytest.fixture(autouse=True)
def setup_fonts():
    """Register bundled fonts before each test."""
    register_bundled_fonts()


class TestRendererCreation:
    """Test Renderer instantiation."""

    def test_create_with_default_config(self):
        config = RenderConfig()
        renderer = Renderer(config)
        assert renderer is not None

    def test_create_with_custom_config(self):
        config = RenderConfig(
            shadow=False,
            window_controls=False,
            font_size=16,
        )
        renderer = Renderer(config)
        assert renderer is not None


class TestRendererPNG:
    """Test PNG rendering."""

    def test_render_png_produces_valid_output(
        self, minimal_render_config, render_tokens, render_metrics
    ):
        theme = get_theme("catppuccin-mocha")
        renderer = Renderer(minimal_render_config)
        result = renderer.render(render_tokens, render_metrics, theme)

        assert isinstance(result, RenderResult)
        assert result.format == OutputFormat.PNG
        assert result.data[:8] == b"\x89PNG\r\n\x1a\n"
        assert result.width > 0
        assert result.height > 0

    def test_render_png_with_chrome(self, render_tokens):
        config = RenderConfig(
            shadow=False,
            window_controls=True,
            show_line_numbers=False,
        )
        theme = get_theme("catppuccin-mocha")
        renderer = Renderer(config)
        # Need to recalculate metrics with this config
        from codepicture.layout import LayoutEngine, PangoTextMeasurer

        measurer = PangoTextMeasurer()
        engine = LayoutEngine(measurer, config)
        metrics = engine.calculate_metrics(render_tokens)

        result = renderer.render(render_tokens, metrics, theme)
        assert result.format == OutputFormat.PNG

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_render_png_with_line_numbers(self, render_tokens):
        config = RenderConfig(
            shadow=False,
            window_controls=False,
            show_line_numbers=True,
        )
        theme = get_theme("catppuccin-mocha")
        from codepicture.layout import LayoutEngine, PangoTextMeasurer

        measurer = PangoTextMeasurer()
        engine = LayoutEngine(measurer, config)
        metrics = engine.calculate_metrics(render_tokens)
        renderer = Renderer(config)

        result = renderer.render(render_tokens, metrics, theme)
        assert result.format == OutputFormat.PNG


class TestRendererSVG:
    """Test SVG rendering."""

    def test_render_svg_produces_valid_output(self, render_tokens):
        config = RenderConfig(
            output_format=OutputFormat.SVG,
            shadow=False,
            window_controls=False,
            show_line_numbers=False,
        )
        theme = get_theme("catppuccin-mocha")
        from codepicture.layout import LayoutEngine, PangoTextMeasurer

        measurer = PangoTextMeasurer()
        engine = LayoutEngine(measurer, config)
        metrics = engine.calculate_metrics(render_tokens)
        renderer = Renderer(config)

        result = renderer.render(render_tokens, metrics, theme)
        assert result.format == OutputFormat.SVG
        assert b"<svg" in result.data or b"<?xml" in result.data


class TestRendererPDF:
    """Test PDF rendering."""

    def test_render_pdf_produces_valid_output(self, render_tokens):
        config = RenderConfig(
            output_format=OutputFormat.PDF,
            shadow=False,
            window_controls=False,
            show_line_numbers=False,
        )
        theme = get_theme("catppuccin-mocha")
        from codepicture.layout import LayoutEngine, PangoTextMeasurer

        measurer = PangoTextMeasurer()
        engine = LayoutEngine(measurer, config)
        metrics = engine.calculate_metrics(render_tokens)
        renderer = Renderer(config)

        result = renderer.render(render_tokens, metrics, theme)
        assert result.format == OutputFormat.PDF
        assert result.data[:4] == b"%PDF"


class TestRendererWithShadow:
    """Test shadow rendering (PNG only)."""

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_png_with_shadow_produces_larger_output(self, render_tokens):
        config_no_shadow = RenderConfig(
            shadow=False,
            window_controls=False,
            show_line_numbers=False,
        )
        config_with_shadow = RenderConfig(
            shadow=True,
            window_controls=False,
            show_line_numbers=False,
        )
        theme = get_theme("catppuccin-mocha")
        from codepicture.layout import LayoutEngine, PangoTextMeasurer

        measurer = PangoTextMeasurer()

        engine = LayoutEngine(measurer, config_no_shadow)
        metrics_no = engine.calculate_metrics(render_tokens)
        renderer_no = Renderer(config_no_shadow)
        result_no = renderer_no.render(render_tokens, metrics_no, theme)

        engine = LayoutEngine(measurer, config_with_shadow)
        metrics_with = engine.calculate_metrics(render_tokens)
        renderer_with = Renderer(config_with_shadow)
        result_with = renderer_with.render(render_tokens, metrics_with, theme)

        # Shadow version should have larger dimensions (due to margin)
        assert result_with.width >= result_no.width
        assert result_with.height >= result_no.height


class TestRendererIntegration:
    """Integration tests verifying end-to-end rendering."""

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_full_render_with_all_features(self, render_tokens):
        """Test render with chrome, line numbers, and shadow."""
        config = RenderConfig(
            shadow=True,
            window_controls=True,
            show_line_numbers=True,
            window_title="test.py",
        )
        theme = get_theme("catppuccin-mocha")
        from codepicture.layout import LayoutEngine, PangoTextMeasurer

        measurer = PangoTextMeasurer()
        engine = LayoutEngine(measurer, config)
        metrics = engine.calculate_metrics(render_tokens)
        renderer = Renderer(config)

        result = renderer.render(render_tokens, metrics, theme)

        assert result.format == OutputFormat.PNG
        assert result.data[:8] == b"\x89PNG\r\n\x1a\n"
        assert result.width > 0
        assert result.height > 0

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_render_different_themes(
        self, render_tokens, minimal_render_config, render_metrics
    ):
        """Test rendering with different themes."""
        renderer = Renderer(minimal_render_config)

        for theme_name in ["catppuccin-mocha", "dracula", "one-dark"]:
            theme = get_theme(theme_name)
            result = renderer.render(render_tokens, render_metrics, theme)
            assert result.data[:8] == b"\x89PNG\r\n\x1a\n"
