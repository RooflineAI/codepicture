"""Tests for shadow post-processing."""

from io import BytesIO

from PIL import Image

from codepicture.core.types import Color, OutputFormat
from codepicture.render import CairoCanvas, apply_shadow
from codepicture.render.shadow import (
    SHADOW_BLUR_RADIUS,
    SHADOW_COLOR,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
    calculate_shadow_margin,
)


class TestShadowConstants:
    """Test shadow constants match macOS aesthetic."""

    def test_blur_radius(self):
        assert SHADOW_BLUR_RADIUS == 50

    def test_offset(self):
        assert SHADOW_OFFSET_X == 0
        assert SHADOW_OFFSET_Y == 25

    def test_shadow_color(self):
        assert Color(0, 0, 0, 128) == SHADOW_COLOR


class TestCalculateShadowMargin:
    """Test shadow margin calculation."""

    def test_margin_includes_blur_and_offset(self):
        margin = calculate_shadow_margin()
        expected = SHADOW_BLUR_RADIUS * 2 + max(
            abs(SHADOW_OFFSET_X), abs(SHADOW_OFFSET_Y)
        )
        assert margin == expected

    def test_margin_is_125(self):
        """Shadow margin = 50*2 + 25 = 125."""
        assert calculate_shadow_margin() == 125


class TestApplyShadow:
    """Test shadow application to Cairo surfaces."""

    def test_disabled_returns_plain_png(self):
        canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=1.0)
        canvas.draw_rectangle(10, 10, 80, 80, Color(255, 0, 0))
        data = apply_shadow(canvas._surface, enabled=False)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_enabled_returns_larger_png(self):
        canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=1.0)
        canvas.draw_rectangle(10, 10, 80, 80, Color(0, 255, 0))
        data_without = apply_shadow(canvas._surface, enabled=False)
        data_with = apply_shadow(canvas._surface, enabled=True)
        # Shadow version should be larger due to margin
        assert len(data_with) > len(data_without)

    def test_returns_valid_png(self):
        canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=1.0)
        canvas.draw_rectangle(0, 0, 100, 100, Color(100, 100, 100))
        data = apply_shadow(canvas._surface, enabled=True)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"


class TestShadowColorPreservation:
    """Regression: verify shadow pipeline does not swap R/B channels."""

    def test_red_stays_red_with_shadow(self):
        canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=1.0)
        canvas.draw_rectangle(0, 0, 100, 100, Color(255, 0, 0))
        data = apply_shadow(canvas._surface, enabled=True)

        img = Image.open(BytesIO(data)).convert("RGBA")
        # Sample center pixel (content is at shadow_margin offset)
        margin = calculate_shadow_margin()
        r, g, b, _a = img.getpixel((margin + 50, margin + 50))
        assert r == 255, f"Red channel should be 255, got {r}"
        assert g == 0, f"Green channel should be 0, got {g}"
        assert b == 0, f"Blue channel should be 0, got {b}"

    def test_blue_stays_blue_with_shadow(self):
        canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=1.0)
        canvas.draw_rectangle(0, 0, 100, 100, Color(0, 0, 255))
        data = apply_shadow(canvas._surface, enabled=True)

        img = Image.open(BytesIO(data)).convert("RGBA")
        margin = calculate_shadow_margin()
        r, g, b, _a = img.getpixel((margin + 50, margin + 50))
        assert r == 0, f"Red channel should be 0, got {r}"
        assert g == 0, f"Green channel should be 0, got {g}"
        assert b == 255, f"Blue channel should be 255, got {b}"

    def test_color_preserved_without_shadow(self):
        canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=1.0)
        canvas.draw_rectangle(0, 0, 100, 100, Color(255, 0, 0))
        data = apply_shadow(canvas._surface, enabled=False)

        img = Image.open(BytesIO(data)).convert("RGBA")
        r, g, b, _a = img.getpixel((50, 50))
        assert r == 255, f"Red channel should be 255, got {r}"
        assert g == 0, f"Green channel should be 0, got {g}"
        assert b == 0, f"Blue channel should be 0, got {b}"
