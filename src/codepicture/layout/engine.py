"""Layout engine for calculating canvas dimensions and element positions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codepicture.core.protocols import TextMeasurer
    from codepicture.config.schema import RenderConfig
    from codepicture.highlight.pygments_highlighter import TokenInfo

import math

from codepicture.core.types import DisplayLine, LayoutMetrics
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

        gap = self.LINE_NUMBER_GAP if self._config.show_line_numbers else 0
        padding = self._config.padding
        wrap_indent_chars = 2

        window_width = self._config.window_width
        window_height = self._config.window_height

        if window_width is not None:
            # Compute available code area within the fixed window width
            available_code_width = window_width - 2 * padding - gutter_width - gap
            max_code_chars = max(1, math.floor(available_code_width / char_width))

            # Build display_lines by splitting source lines that exceed max_code_chars
            display_lines: list[DisplayLine] = []
            for line_idx, line_tokens in enumerate(lines):
                total_chars = sum(len(t.text) for t in line_tokens)

                if total_chars <= max_code_chars:
                    display_lines.append(
                        DisplayLine(
                            source_line_idx=line_idx,
                            token_start=0,
                            token_end=len(line_tokens),
                            char_offset=0,
                            is_continuation=False,
                        )
                    )
                else:
                    # First chunk gets full width
                    char_pos = 0
                    first_chunk_size = max_code_chars
                    continuation_chunk_size = max(1, max_code_chars - wrap_indent_chars)

                    is_first = True
                    while char_pos < total_chars:
                        chunk_size = first_chunk_size if is_first else continuation_chunk_size
                        chunk_end = min(char_pos + chunk_size, total_chars)

                        # Compute token_start and token_end for this chunk
                        token_start, token_end = self._tokens_for_range(
                            line_tokens, char_pos, chunk_end
                        )

                        display_lines.append(
                            DisplayLine(
                                source_line_idx=line_idx,
                                token_start=token_start,
                                token_end=token_end,
                                char_offset=char_pos,
                                is_continuation=not is_first,
                            )
                        )

                        char_pos = chunk_end
                        is_first = False

            display_lines_tuple = tuple(display_lines)
            num_visual_lines = len(display_lines)
            code_width = available_code_width
            canvas_width = window_width
        else:
            # No wrapping -- legacy auto-size path
            display_lines_tuple = ()
            num_visual_lines = len(lines)
            code_width = max_chars * char_width
            canvas_width = int(gutter_width + gap + code_width + 2 * padding)

        content_width = gutter_width + gap + code_width
        content_height = num_visual_lines * line_height_px

        if window_height is not None:
            canvas_height = window_height
        else:
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
            display_lines=display_lines_tuple,
            wrap_indent_chars=wrap_indent_chars,
        )

    @staticmethod
    def _tokens_for_range(
        tokens: list["TokenInfo"],
        char_start: int,
        char_end: int,
    ) -> tuple[int, int]:
        """Find token index range that overlaps [char_start, char_end).

        Args:
            tokens: Token list for a source line
            char_start: Start character offset (inclusive)
            char_end: End character offset (exclusive)

        Returns:
            (token_start, token_end) indices into the tokens list
        """
        token_start = 0
        token_end = 0
        pos = 0
        found_start = False

        for idx, token in enumerate(tokens):
            token_len = len(token.text)
            token_char_end = pos + token_len

            if not found_start and token_char_end > char_start:
                token_start = idx
                found_start = True

            if found_start:
                token_end = idx + 1

            if token_char_end >= char_end:
                break

            pos = token_char_end

        return token_start, token_end

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
