"""Tests for window chrome rendering."""

from codepicture.core.types import Color, OutputFormat
from codepicture.render import CairoCanvas
from codepicture.render.chrome import (
    BUTTON_DIAMETER,
    BUTTON_SPACING,
    CLOSE_COLOR,
    MAXIMIZE_COLOR,
    MINIMIZE_COLOR,
    TITLE_BAR_HEIGHT,
    draw_title_bar,
    draw_traffic_lights,
)


class TestChromeConstants:
    """Test chrome constants match macOS values."""

    def test_title_bar_height(self):
        assert TITLE_BAR_HEIGHT == 28

    def test_button_diameter(self):
        assert BUTTON_DIAMETER == 12

    def test_button_spacing(self):
        assert BUTTON_SPACING == 8

    def test_button_colors(self):
        assert Color.from_hex("#ff5f57") == CLOSE_COLOR
        assert Color.from_hex("#febc2e") == MINIMIZE_COLOR
        assert Color.from_hex("#28c840") == MAXIMIZE_COLOR


class TestDrawTrafficLights:
    """Test traffic light button rendering."""

    def test_draws_without_error(self):
        canvas = CairoCanvas.create(200, 100, OutputFormat.PNG, scale=1.0)
        draw_traffic_lights(canvas, 0)
        # No exception means success


class TestDrawTitleBar:
    """Test title bar rendering."""

    def test_draws_without_title(self):
        canvas = CairoCanvas.create(400, 100, OutputFormat.PNG, scale=1.0)
        draw_title_bar(canvas, 400, Color(30, 30, 30), title=None, corner_radius=0)

    def test_draws_with_title(self):
        canvas = CairoCanvas.create(400, 100, OutputFormat.PNG, scale=1.0)
        draw_title_bar(canvas, 400, Color(30, 30, 30), title="test.py", corner_radius=0)

    def test_draws_with_corner_radius(self):
        canvas = CairoCanvas.create(400, 100, OutputFormat.PNG, scale=1.0)
        draw_title_bar(canvas, 400, Color(30, 30, 30), title=None, corner_radius=12)

    def test_draws_with_light_background(self):
        """Title color adapts to light background."""
        canvas = CairoCanvas.create(400, 100, OutputFormat.PNG, scale=1.0)
        # Light background (avg brightness > 128)
        draw_title_bar(
            canvas, 400, Color(200, 200, 200), title="test.py", corner_radius=0
        )
