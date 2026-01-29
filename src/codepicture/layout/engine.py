"""Layout engine for calculating canvas dimensions and element positions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codepicture.core.protocols import TextMeasurer
    from codepicture.config.schema import RenderConfig
    from codepicture.highlight.pygments_highlighter import TokenInfo

from codepicture.core.types import LayoutMetrics
from codepicture.errors import LayoutError


class LayoutEngine:
    """Calculates positions and sizes for rendering.

    Uses TextMeasurer to determine text dimensions and applies
    configuration settings for padding, line height, etc.
    """

    # Fixed values from CONTEXT.md
    LINE_NUMBER_GAP = 12  # px between line numbers and code

    def __init__(
        self,
        measurer: "TextMeasurer",
        config: "RenderConfig",
    ) -> None:
        """Initialize layout engine.

        Args:
            measurer: TextMeasurer implementation for text dimensions
            config: RenderConfig with typography and padding settings
        """
        self._measurer = measurer
        self._config = config

    def calculate_metrics(
        self,
        lines: list[list["TokenInfo"]],
    ) -> LayoutMetrics:
        """Calculate complete layout metrics for rendering.

        Args:
            lines: Tokenized lines from highlighter

        Returns:
            LayoutMetrics with all dimensions

        Raises:
            LayoutError: If lines is empty (refuse to render empty input)
        """
        if not lines:
            raise LayoutError("Cannot render empty input. Provide code to render.")

        # Measure character dimensions with configured font
        char_width, char_height = self._measurer.measure_text(
            "M",
            self._config.font_family,
            self._config.font_size,
        )

        # Line height from config (multiplier on font height)
        line_height_px = char_height * self._config.line_height

        # Find longest line in characters
        max_chars = max(
            sum(len(token.text) for token in line)
            for line in lines
        )

        # Calculate max line number for gutter width
        max_line_number = len(lines) + self._config.line_number_offset - 1

        # Gutter width (0 if line numbers disabled)
        if self._config.show_line_numbers:
            gutter_width = self._calculate_gutter_width(max_line_number)
        else:
            gutter_width = 0.0

        # Code width based on longest line
        code_width = max_chars * char_width

        # Content dimensions
        gap = self.LINE_NUMBER_GAP if self._config.show_line_numbers else 0
        content_width = gutter_width + gap + code_width
        content_height = len(lines) * line_height_px

        # Canvas with padding
        padding = self._config.padding
        canvas_width = int(content_width + 2 * padding)
        canvas_height = int(content_height + 2 * padding)

        return LayoutMetrics(
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            content_x=float(padding),
            content_y=float(padding),
            content_width=content_width,
            content_height=content_height,
            gutter_width=gutter_width,
            gutter_x=float(padding),
            code_x=float(padding) + gutter_width + gap,
            code_y=float(padding),
            code_width=code_width,
            line_height_px=line_height_px,
            char_width=char_width,
            baseline_offset=char_height * 0.8,  # Approximate baseline
        )

    def _calculate_gutter_width(self, max_line_number: int) -> float:
        """Calculate gutter width based on line number digits.

        Args:
            max_line_number: Highest line number to display

        Returns:
            Width in pixels needed for line numbers
        """
        digits = len(str(max_line_number))
        # Measure actual digit width (use 0 as reference character)
        digit_width, _ = self._measurer.measure_text(
            "0" * digits,
            self._config.font_family,
            self._config.font_size,
        )
        return digit_width
