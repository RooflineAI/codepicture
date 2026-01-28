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
    "OutputFormat",
    "Position",
    "Rect",
    "TextStyle",
    "WindowStyle",
]
