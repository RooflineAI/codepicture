"""Text measurement using Cairo for accurate dimensions.

Provides pixel-accurate text measurement for layout calculations.
Uses Cairo with FreeType for cross-platform consistency.

Note: While Pango would provide more accurate typesetting for complex
scripts, Cairo's text API is sufficient for monospace code rendering
where we primarily measure ASCII characters.
"""

import cairo

__all__ = ["PangoTextMeasurer"]


class PangoTextMeasurer:
    """Text measurer using Cairo for accurate dimensions.

    Creates a minimal Cairo surface for measurement context,
    allowing accurate text dimension calculations without
    actually rendering to screen or file.

    Named PangoTextMeasurer for API compatibility with the TextMeasurer
    protocol, though the current implementation uses Cairo's text API
    which is suitable for monospace code rendering.
    """

    def __init__(self) -> None:
        """Initialize the text measurer with a minimal measurement surface."""
        # Create minimal surface for measurement context
        self._surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
        self._context = cairo.Context(self._surface)
        # Cache for font metrics to avoid repeated font selection
        self._current_font: tuple[str, int] | None = None

    def measure_text(
        self, text: str, font_family: str, font_size: int
    ) -> tuple[float, float]:
        """Measure text dimensions in pixels.

        Uses Cairo for cross-platform text measurement.
        Automatically resolves font family with fallback to bundled font.

        Args:
            text: Text to measure
            font_family: Font family name (e.g., "JetBrains Mono")
            font_size: Font size in pixels

        Returns:
            Tuple of (width, height) in pixels
        """
        from codepicture.fonts import resolve_font_family

        # Resolve font with fallback to bundled JetBrains Mono
        resolved_family = resolve_font_family(font_family)

        # Set up font if changed
        font_key = (resolved_family, font_size)
        if self._current_font != font_key:
            self._context.select_font_face(
                resolved_family,
                cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_NORMAL,
            )
            self._context.set_font_size(font_size)
            self._current_font = font_key

        # Handle empty text
        if not text:
            return 0.0, 0.0

        # Get text extents
        extents = self._context.text_extents(text)

        # Use x_advance for width (accounts for character spacing)
        # and font height from font extents for consistent line height
        font_extents = self._context.font_extents()

        # Width is the advance width (spacing to next character position)
        width = extents.x_advance

        # Height is the font's line height (ascent + descent)
        height = font_extents[0] + font_extents[1]  # ascent + descent

        return float(width), float(height)
