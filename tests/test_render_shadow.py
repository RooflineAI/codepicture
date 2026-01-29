"""Tests for shadow post-processing."""

import pytest
from codepicture.render import CairoCanvas, apply_shadow
from codepicture.render.shadow import (
    SHADOW_BLUR_RADIUS,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
    SHADOW_COLOR,
    calculate_shadow_margin,
)
from codepicture.core.types import Color, OutputFormat


class TestShadowConstants:
    """Test shadow constants match macOS aesthetic."""

    def test_blur_radius(self):
        assert SHADOW_BLUR_RADIUS == 50

    def test_offset(self):
        assert SHADOW_OFFSET_X == 0
        assert SHADOW_OFFSET_Y == 25

    def test_shadow_color(self):
        assert SHADOW_COLOR == Color(0, 0, 0, 128)


class TestCalculateShadowMargin:
    """Test shadow margin calculation."""

    def test_margin_includes_blur_and_offset(self):
        margin = calculate_shadow_margin()
        expected = SHADOW_BLUR_RADIUS * 2 + max(abs(SHADOW_OFFSET_X), abs(SHADOW_OFFSET_Y))
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
        assert data[:8] == b'\x89PNG\r\n\x1a\n'

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
        assert data[:8] == b'\x89PNG\r\n\x1a\n'
