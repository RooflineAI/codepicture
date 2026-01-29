"""Rendering module for codepicture.

Provides canvas implementations for drawing code images in various formats.
"""

from .canvas import CairoCanvas
from .shadow import (
    SHADOW_BLUR_RADIUS,
    SHADOW_COLOR,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
    apply_shadow,
    calculate_shadow_margin,
)

__all__ = [
    "CairoCanvas",
    "apply_shadow",
    "calculate_shadow_margin",
    "SHADOW_BLUR_RADIUS",
    "SHADOW_OFFSET_X",
    "SHADOW_OFFSET_Y",
    "SHADOW_COLOR",
]
