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
    TextStyle,
    WindowStyle,
)

__all__ = [
    # Protocols
    "Canvas",
    "Highlighter",
    "TextMeasurer",
    "Theme",
    # Types
    "Color",
    "Dimensions",
    "LayoutMetrics",
    "OutputFormat",
    "Position",
    "Rect",
    "TextStyle",
    "WindowStyle",
]
