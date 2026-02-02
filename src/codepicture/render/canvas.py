"""Cairo-based canvas implementation for rendering code images.

CairoCanvas provides a unified drawing interface for PNG, SVG, and PDF output,
implementing the Canvas protocol from core.protocols.
"""

from __future__ import annotations

import math
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import cairo

from codepicture.core.types import Color, OutputFormat
from codepicture.fonts import resolve_font_family

if TYPE_CHECKING:
    pass

__all__ = ["CairoCanvas"]


def _draw_rounded_rect(
    ctx: cairo.Context,
    x: float,
    y: float,
    width: float,
    height: float,
    radius: float,
) -> None:
    """Draw a rounded rectangle path using arc segments.

    Args:
        ctx: Cairo context to draw on
        x: Left edge X coordinate
        y: Top edge Y coordinate
        width: Rectangle width
        height: Rectangle height
        radius: Corner radius
    """
    # Clamp radius to half of the smallest dimension
    radius = min(radius, width / 2, height / 2)

    # Start at top-left, after the corner radius
    ctx.new_path()
    ctx.arc(x + width - radius, y + radius, radius, -math.pi / 2, 0)
    ctx.arc(x + width - radius, y + height - radius, radius, 0, math.pi / 2)
    ctx.arc(x + radius, y + height - radius, radius, math.pi / 2, math.pi)
    ctx.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
    ctx.close_path()


class CairoCanvas:
    """Cairo-based canvas implementing the Canvas protocol.

    Provides drawing operations for PNG, SVG, and PDF output formats.
    PNG surfaces are created at 2x resolution for HiDPI display.
    SVG and PDF surfaces write to BytesIO buffers.
    """

    __slots__ = (
        "_buffer",
        "_ctx",
        "_current_font",
        "_format",
        "_height",
        "_scale",
        "_surface",
        "_width",
    )

    def __init__(
        self,
        surface: cairo.Surface,
        ctx: cairo.Context,
        format: OutputFormat,
        buffer: BytesIO | None,
        scale: float,
        width: int,
        height: int,
    ) -> None:
        """Initialize canvas with Cairo surface and context.

        Args:
            surface: Cairo surface to draw on
            ctx: Cairo context for drawing operations
            format: Output format (PNG, SVG, PDF)
            buffer: BytesIO buffer for SVG/PDF output (None for PNG)
            scale: Scale factor (2.0 for HiDPI PNG)
            width: Logical width in pixels
            height: Logical height in pixels
        """
        self._surface = surface
        self._ctx = ctx
        self._format = format
        self._buffer = buffer
        self._scale = scale
        self._width = width
        self._height = height
        self._current_font: tuple[str, int] | None = None

    @classmethod
    def create(
        cls,
        width: int,
        height: int,
        format: OutputFormat,
        scale: float = 2.0,
    ) -> CairoCanvas:
        """Create a new canvas with the specified dimensions and format.

        Args:
            width: Logical width in pixels
            height: Logical height in pixels
            format: Output format (PNG, SVG, PDF)
            scale: Scale factor for PNG (default 2.0 for HiDPI)

        Returns:
            New CairoCanvas instance
        """
        buffer: BytesIO | None = None

        if format == OutputFormat.PNG:
            # Create image surface at scaled resolution for HiDPI
            surface = cairo.ImageSurface(
                cairo.FORMAT_ARGB32,
                int(width * scale),
                int(height * scale),
            )
            ctx = cairo.Context(surface)
            # Scale context so drawing uses logical coordinates
            ctx.scale(scale, scale)
        elif format == OutputFormat.SVG:
            # SVG surface writes to buffer at logical dimensions
            buffer = BytesIO()
            surface = cairo.SVGSurface(buffer, width, height)
            ctx = cairo.Context(surface)
            scale = 1.0
        elif format == OutputFormat.PDF:
            # PDF surface writes to buffer at logical dimensions
            buffer = BytesIO()
            surface = cairo.PDFSurface(buffer, width, height)
            ctx = cairo.Context(surface)
            scale = 1.0
        else:
            raise ValueError(f"Unsupported output format: {format}")

        return cls(surface, ctx, format, buffer, scale, width, height)

    @property
    def width(self) -> int:
        """Canvas width in logical pixels."""
        return self._width

    @property
    def height(self) -> int:
        """Canvas height in logical pixels."""
        return self._height

    def draw_rectangle(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        color: Color,
        corner_radius: float = 0,
    ) -> None:
        """Draw a filled rectangle.

        Args:
            x: Left edge X coordinate
            y: Top edge Y coordinate
            width: Rectangle width
            height: Rectangle height
            color: Fill color
            corner_radius: Corner radius for rounded corners (default: 0)
        """
        if corner_radius > 0:
            _draw_rounded_rect(self._ctx, x, y, width, height, corner_radius)
        else:
            self._ctx.rectangle(x, y, width, height)

        self._ctx.set_source_rgba(
            color.r / 255.0,
            color.g / 255.0,
            color.b / 255.0,
            color.a / 255.0,
        )
        self._ctx.fill()

    def draw_circle(
        self,
        x: float,
        y: float,
        radius: float,
        color: Color,
    ) -> None:
        """Draw a filled circle.

        Args:
            x: Center X coordinate
            y: Center Y coordinate
            radius: Circle radius
            color: Fill color
        """
        self._ctx.arc(x, y, radius, 0, 2 * math.pi)
        self._ctx.set_source_rgba(
            color.r / 255.0,
            color.g / 255.0,
            color.b / 255.0,
            color.a / 255.0,
        )
        self._ctx.fill()

    def draw_text(
        self,
        x: float,
        y: float,
        text: str,
        font_family: str,
        font_size: int,
        color: Color,
    ) -> float:
        """Draw text at the specified position.

        Args:
            x: Left edge X coordinate
            y: Baseline Y coordinate
            text: Text string to draw
            font_family: Font family name
            font_size: Font size in pixels
            color: Text color

        Returns:
            Width of the rendered text in pixels (x_advance)
        """
        # Resolve font family (falls back to bundled font if not found)
        font_name = resolve_font_family(font_family)

        # Set up font (cached to avoid redundant calls)
        font_key = (font_name, font_size)
        if self._current_font != font_key:
            self._ctx.select_font_face(
                font_name,
                cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_NORMAL,
            )
            self._ctx.set_font_size(font_size)
            self._current_font = font_key

        # Set color and draw
        self._ctx.set_source_rgba(
            color.r / 255.0,
            color.g / 255.0,
            color.b / 255.0,
            color.a / 255.0,
        )
        self._ctx.move_to(x, y)
        self._ctx.show_text(text)

        # Return advance width
        extents = self._ctx.text_extents(text)
        return extents.x_advance

    def measure_text(
        self,
        text: str,
        font_family: str,
        font_size: int,
    ) -> tuple[float, float]:
        """Measure text dimensions without drawing.

        Args:
            text: Text string to measure
            font_family: Font family name
            font_size: Font size in pixels

        Returns:
            Tuple of (width, height) in pixels
        """
        # Resolve font family
        font_name = resolve_font_family(font_family)

        # Set up font (cached to avoid redundant calls)
        font_key = (font_name, font_size)
        if self._current_font != font_key:
            self._ctx.select_font_face(
                font_name,
                cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_NORMAL,
            )
            self._ctx.set_font_size(font_size)
            self._current_font = font_key

        # Get text extents for width
        text_extents = self._ctx.text_extents(text)
        # Get font extents for height
        font_extents = self._ctx.font_extents()

        return (text_extents.x_advance, font_extents[2])  # height is index 2

    def push_clip(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        """Push a clipping rectangle onto the clip stack.

        Args:
            x: Left edge X coordinate
            y: Top edge Y coordinate
            width: Clipping region width
            height: Clipping region height
        """
        self._ctx.save()
        self._ctx.rectangle(x, y, width, height)
        self._ctx.clip()

    def pop_clip(self) -> None:
        """Pop the most recent clipping rectangle from the stack."""
        self._ctx.restore()

    def apply_shadow(
        self,
        blur_radius: float,
        offset_x: float,
        offset_y: float,
        color: Color,
    ) -> None:
        """Apply a drop shadow effect.

        Note: This is a no-op stub. Real shadow implementation
        will be added in Plan 04-03 using Pillow for blur processing.

        Args:
            blur_radius: Shadow blur radius
            offset_x: Horizontal shadow offset
            offset_y: Vertical shadow offset
            color: Shadow color
        """
        # No-op stub - Plan 04-03 implements real shadow
        pass

    def save(self) -> bytes:
        """Save the canvas to bytes in the appropriate format.

        Returns:
            Image data as bytes (PNG, SVG, or PDF format)
        """
        if self._format == OutputFormat.PNG:
            # Write PNG to BytesIO buffer
            buffer = BytesIO()
            self._surface.write_to_png(buffer)
            return buffer.getvalue()
        else:
            # SVG and PDF: finish surface and get buffer contents
            self._surface.finish()
            if self._buffer is None:
                raise RuntimeError("Buffer not available for SVG/PDF format")
            return self._buffer.getvalue()

    def save_to_file(self, path: Path) -> None:
        """Save the canvas to a file.

        Args:
            path: Output file path
        """
        path.write_bytes(self.save())
