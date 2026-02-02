"""Core types and protocols for codepicture."""

from .protocols import (
    Canvas,
    Highlighter,
    TextMeasurer,
    Theme,
)
from .types import (
    Color,
    Dimensions,
    LayoutMetrics,
    OutputFormat,
    Position,
    Rect,
    RenderResult,
    TextStyle,
    WindowStyle,
)

__all__ = [
    "Canvas",
    "Color",
    "Dimensions",
    "Highlighter",
    "LayoutMetrics",
    "OutputFormat",
    "Position",
    "Rect",
    "RenderResult",
    "TextMeasurer",
    "TextStyle",
    "Theme",
    "WindowStyle",
]
