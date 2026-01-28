"""Protocol definitions for codepicture components.

These protocols define the interfaces that implementations must satisfy:
- TextMeasurer: Measures text dimensions without rendering
- Canvas: Abstract drawing surface
- Highlighter: Syntax highlighting abstraction
- Theme: Color and style definitions

Note: These protocols use structural subtyping (duck typing).
Do NOT use @runtime_checkable for performance reasons.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from codepicture.highlight.pygments_highlighter import TokenInfo

    from .types import Color, TextStyle


class TextMeasurer(Protocol):
    """Measures text dimensions without rendering."""

    def measure_text(
        self, text: str, font_family: str, font_size: int
    ) -> tuple[float, float]:
        """Measure text dimensions.

        Args:
            text: Text string to measure
            font_family: Font family name (e.g., "JetBrains Mono")
            font_size: Font size in pixels

        Returns:
            Tuple of (width, height) in pixels
        """
        ...


class Canvas(Protocol):
    """Abstract drawing surface.

    Provides a unified interface for drawing shapes, text, and
    managing clipping regions. Implementations may use different
    backends (Pillow, Cairo, Skia, etc.).
    """

    @property
    def width(self) -> int:
        """Canvas width in pixels."""
        ...

    @property
    def height(self) -> int:
        """Canvas height in pixels."""
        ...

    def draw_rectangle(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        color: "Color",
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
        ...

    def draw_circle(
        self, x: float, y: float, radius: float, color: "Color"
    ) -> None:
        """Draw a filled circle.

        Args:
            x: Center X coordinate
            y: Center Y coordinate
            radius: Circle radius
            color: Fill color
        """
        ...

    def draw_text(
        self,
        x: float,
        y: float,
        text: str,
        font_family: str,
        font_size: int,
        color: "Color",
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
            Width of the rendered text in pixels
        """
        ...

    def measure_text(
        self, text: str, font_family: str, font_size: int
    ) -> tuple[float, float]:
        """Measure text dimensions without drawing.

        Args:
            text: Text string to measure
            font_family: Font family name
            font_size: Font size in pixels

        Returns:
            Tuple of (width, height) in pixels
        """
        ...

    def push_clip(self, x: float, y: float, width: float, height: float) -> None:
        """Push a clipping rectangle onto the clip stack.

        All subsequent drawing operations will be clipped to this region.

        Args:
            x: Left edge X coordinate
            y: Top edge Y coordinate
            width: Clipping region width
            height: Clipping region height
        """
        ...

    def pop_clip(self) -> None:
        """Pop the most recent clipping rectangle from the stack."""
        ...

    def apply_shadow(
        self,
        blur_radius: float,
        offset_x: float,
        offset_y: float,
        color: "Color",
    ) -> None:
        """Apply a drop shadow effect to subsequent drawing.

        Args:
            blur_radius: Shadow blur radius
            offset_x: Horizontal shadow offset
            offset_y: Vertical shadow offset
            color: Shadow color
        """
        ...

    def save(self) -> bytes:
        """Save the canvas to bytes in the appropriate format.

        Returns:
            Image data as bytes
        """
        ...

    def save_to_file(self, path: Path) -> None:
        """Save the canvas to a file.

        Args:
            path: Output file path
        """
        ...


class Highlighter(Protocol):
    """Syntax highlighting abstraction.

    Provides tokenization of source code for syntax highlighting.
    """

    def highlight(self, code: str, language: str) -> list[list["TokenInfo"]]:
        """Tokenize code by language.

        Args:
            code: Source code string
            language: Language identifier (e.g., 'python', 'rust')

        Returns:
            List of lines, where each line is a list of TokenInfo objects
            containing text, token_type, line, and column.
        """
        ...

    def detect_language(self, code: str, filename: str | None = None) -> str:
        """Auto-detect language from content and/or filename.

        Args:
            code: Source code string
            filename: Optional filename for extension-based detection

        Returns:
            Language identifier
        """
        ...

    def list_languages(self) -> list[str]:
        """Return available language identifiers.

        Returns:
            List of supported language identifiers
        """
        ...


class Theme(Protocol):
    """Color and style definitions for syntax highlighting.

    Provides colors for the editor background, foreground text,
    line numbers, and syntax token styles.
    """

    @property
    def name(self) -> str:
        """Theme name (e.g., 'catppuccin-mocha')."""
        ...

    @property
    def background(self) -> "Color":
        """Editor background color."""
        ...

    @property
    def foreground(self) -> "Color":
        """Default text color."""
        ...

    @property
    def line_number_fg(self) -> "Color":
        """Line number foreground (text) color."""
        ...

    @property
    def line_number_bg(self) -> "Color":
        """Line number background (gutter) color."""
        ...

    def get_style(self, token_type: Any) -> "TextStyle":
        """Get text style for a syntax token type.

        Args:
            token_type: Token type (implementation-specific)

        Returns:
            TextStyle with color, bold, italic, underline settings
        """
        ...
