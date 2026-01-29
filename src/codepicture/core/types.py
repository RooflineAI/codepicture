"""Core data types for codepicture.

These types are used throughout the rendering pipeline:
- Color: RGBA color values with hex parsing
- Dimensions: Width/height pairs
- Position: X/Y coordinates
- Rect: Rectangle with position and size
- TextStyle: Text styling (color, bold, italic, underline)
- OutputFormat: Supported output formats (PNG, SVG, PDF)
- WindowStyle: Window chrome styles (macOS, Windows, Linux, None)
"""

from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


class OutputFormat(Enum):
    """Supported output formats."""

    PNG = "png"
    SVG = "svg"
    PDF = "pdf"


class WindowStyle(Enum):
    """Window chrome styles."""

    MACOS = "macos"
    WINDOWS = "windows"
    LINUX = "linux"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class Color:
    """RGBA color value.

    All components are integers in range 0-255.
    Alpha defaults to 255 (fully opaque).
    """

    r: int
    g: int
    b: int
    a: int = 255

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        """Parse color from hex string.

        Supports:
        - #RGB (3 chars, expanded to 6)
        - #RRGGBB (6 chars)
        - #RRGGBBAA (8 chars, with alpha)

        Args:
            hex_str: Hex color string starting with #

        Returns:
            Color instance

        Raises:
            ValueError: If hex_str is not a valid hex color
        """
        hex_str = hex_str.lstrip("#")

        if len(hex_str) == 3:
            # Expand #RGB to #RRGGBB
            hex_str = "".join(c * 2 for c in hex_str)

        if len(hex_str) == 6:
            # Add fully opaque alpha
            hex_str += "ff"

        if len(hex_str) != 8:
            raise ValueError(
                f"Invalid hex color: #{hex_str}. "
                "Use #RGB, #RRGGBB, or #RRGGBBAA format."
            )

        try:
            return cls(
                r=int(hex_str[0:2], 16),
                g=int(hex_str[2:4], 16),
                b=int(hex_str[4:6], 16),
                a=int(hex_str[6:8], 16),
            )
        except ValueError as e:
            raise ValueError(f"Invalid hex color: #{hex_str}") from e

    def to_hex(self) -> str:
        """Convert to #RRGGBBAA hex string.

        Returns:
            Hex color string in #RRGGBBAA format
        """
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}{self.a:02x}"


class Dimensions(NamedTuple):
    """Width and height dimensions."""

    width: int
    height: int


class Position(NamedTuple):
    """X and Y coordinates."""

    x: float
    y: float


class Rect(NamedTuple):
    """Rectangle with position and size."""

    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class TextStyle:
    """Text styling for syntax highlighting.

    Attributes:
        color: Text color
        bold: Whether text is bold
        italic: Whether text is italic
        underline: Whether text is underlined
    """

    color: Color
    bold: bool = False
    italic: bool = False
    underline: bool = False


@dataclass(frozen=True, slots=True)
class LayoutMetrics:
    """Complete layout measurements for rendering.

    All dimensions are in pixels. Positions are relative to canvas origin (0, 0).
    """

    # Canvas dimensions
    canvas_width: int
    canvas_height: int

    # Content area (inside padding)
    content_x: float
    content_y: float
    content_width: float
    content_height: float

    # Gutter (line numbers) - 0 if line numbers disabled
    gutter_width: float
    gutter_x: float

    # Code area (after gutter + gap)
    code_x: float
    code_y: float
    code_width: float

    # Typography metrics
    line_height_px: float
    char_width: float
    baseline_offset: float


@dataclass(frozen=True, slots=True)
class RenderResult:
    """Result of rendering operation.

    Attributes:
        data: Raw image bytes (PNG, SVG, or PDF)
        format: Output format
        width: Final image width in pixels
        height: Final image height in pixels
    """

    data: bytes
    format: OutputFormat
    width: int
    height: int
