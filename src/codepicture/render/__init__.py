"""Rendering module for codepicture.

Provides canvas implementations for drawing code images in various formats.
"""

from .canvas import CairoCanvas
from .chrome import (
    TITLE_BAR_HEIGHT,
    draw_title_bar,
    draw_traffic_lights,
)
from .renderer import Renderer
from .shadow import (
    SHADOW_BLUR_RADIUS,
    SHADOW_COLOR,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
    apply_shadow,
    calculate_shadow_margin,
)

__all__ = [
    "SHADOW_BLUR_RADIUS",
    "SHADOW_COLOR",
    "SHADOW_OFFSET_X",
    "SHADOW_OFFSET_Y",
    "TITLE_BAR_HEIGHT",
    "CairoCanvas",
    "Renderer",
    "apply_shadow",
    "calculate_shadow_margin",
    "draw_title_bar",
    "draw_traffic_lights",
]
