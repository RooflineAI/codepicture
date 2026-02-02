"""High-level renderer orchestrating all drawing operations.

Renderer takes highlighted code, layout metrics, theme, and config,
then produces the final output image by coordinating CairoCanvas,
chrome, and shadow modules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from codepicture.config.schema import RenderConfig
from codepicture.core.types import (
    LayoutMetrics,
    OutputFormat,
    RenderResult,
    WindowStyle,
)
from codepicture.render.canvas import CairoCanvas
from codepicture.render.chrome import TITLE_BAR_HEIGHT, draw_title_bar
from codepicture.render.shadow import apply_shadow, calculate_shadow_margin

if TYPE_CHECKING:
    from codepicture.core.protocols import Theme
    from codepicture.highlight import TokenInfo

__all__ = ["Renderer"]


class Renderer:
    """Orchestrates rendering of syntax-highlighted code to images.

    Coordinates CairoCanvas, chrome, and shadow modules to produce
    complete code images in PNG, SVG, or PDF format.
    """

    __slots__ = ("_config",)

    def __init__(self, config: RenderConfig) -> None:
        """Initialize renderer with configuration.

        Args:
            config: Render configuration with styling options
        """
        self._config = config

    def render(
        self,
        lines: list[list[TokenInfo]],
        metrics: LayoutMetrics,
        theme: Theme,
    ) -> RenderResult:
        """Render highlighted code to image bytes.

        Args:
            lines: Tokenized lines from highlighter
            metrics: Pre-calculated layout dimensions
            theme: Color theme for styling

        Returns:
            RenderResult with image data and dimensions
        """
        config = self._config
        output_format = config.output_format

        # Determine if chrome should be drawn
        has_chrome = config.window_controls and config.window_style != WindowStyle.NONE
        title_bar_height = TITLE_BAR_HEIGHT if has_chrome else 0

        # Calculate base dimensions (content + title bar)
        base_width = metrics.canvas_width
        base_height = metrics.canvas_height + title_bar_height

        # Calculate final dimensions with shadow margin for PNG
        has_shadow = config.shadow and output_format == OutputFormat.PNG
        shadow_margin = calculate_shadow_margin() if has_shadow else 0

        # For PNG, we draw content at full size, shadow is applied post-process
        # and expands the image. So canvas is base size, final is with margin.
        canvas_width = base_width
        canvas_height = base_height
        final_width = base_width + 2 * shadow_margin
        final_height = base_height + 2 * shadow_margin

        # Create canvas with appropriate scale
        # PNG: 2x scale for HiDPI per CONTEXT.md
        # SVG/PDF: 1x scale (vector formats)
        scale = 2.0 if output_format == OutputFormat.PNG else 1.0

        canvas = CairoCanvas.create(
            width=canvas_width,
            height=canvas_height,
            format=output_format,
            scale=scale,
        )

        # Draw background (full canvas with rounded corners)
        canvas.draw_rectangle(
            x=0,
            y=0,
            width=canvas_width,
            height=canvas_height,
            color=theme.background,
            corner_radius=config.corner_radius,
        )

        # Draw window chrome if enabled
        if has_chrome:
            draw_title_bar(
                canvas=canvas,
                width=canvas_width,
                background=theme.background,
                title=config.window_title,
                corner_radius=config.corner_radius,
            )

        # Calculate code area offset (below title bar if present)
        code_y_offset = title_bar_height

        if metrics.display_lines:
            # Word-wrap aware rendering path
            self._render_wrapped(canvas, lines, metrics, theme, code_y_offset)
        else:
            # Legacy rendering path (no wrapping)
            self._render_legacy(canvas, lines, metrics, theme, code_y_offset)

        # --- end drawing code/line numbers ---

        # Save and apply shadow (PNG only)
        if output_format == OutputFormat.PNG:
            # apply_shadow handles both enabled and disabled cases
            data = apply_shadow(canvas._surface, enabled=config.shadow)
        else:
            # SVG and PDF: no shadow support (documented limitation)
            data = canvas.save()

        # Return result with final dimensions
        # For PNG with shadow, dimensions include shadow margin
        # For SVG/PDF or PNG without shadow, dimensions are base size
        if has_shadow:
            return RenderResult(
                data=data,
                format=output_format,
                width=final_width,
                height=final_height,
            )
        else:
            return RenderResult(
                data=data,
                format=output_format,
                width=base_width,
                height=base_height,
            )

    def _render_legacy(
        self,
        canvas: CairoCanvas,
        lines: list[list[TokenInfo]],
        metrics: LayoutMetrics,
        theme: Theme,
        code_y_offset: float,
    ) -> None:
        """Render code using the original (non-wrapped) path."""
        config = self._config

        # Draw line numbers if enabled
        if config.show_line_numbers:
            line_number_color = theme.line_number_fg

            for line_idx, _line_tokens in enumerate(lines):
                line_num = line_idx + config.line_number_offset
                line_num_text = str(line_num)

                baseline_y = (
                    metrics.content_y
                    + code_y_offset
                    + line_idx * metrics.line_height_px
                    + metrics.baseline_offset
                )

                text_width, _ = canvas.measure_text(
                    line_num_text, config.font_family, config.font_size
                )
                line_num_x = metrics.gutter_x + metrics.gutter_width - text_width

                canvas.draw_text(
                    x=line_num_x,
                    y=baseline_y,
                    text=line_num_text,
                    font_family=config.font_family,
                    font_size=config.font_size,
                    color=line_number_color,
                )

        # Draw code tokens
        for line_idx, line_tokens in enumerate(lines):
            baseline_y = (
                metrics.content_y
                + code_y_offset
                + line_idx * metrics.line_height_px
                + metrics.baseline_offset
            )

            current_x = metrics.code_x

            for token in line_tokens:
                style = theme.get_style(token.token_type)

                text_width = canvas.draw_text(
                    x=current_x,
                    y=baseline_y,
                    text=token.text,
                    font_family=config.font_family,
                    font_size=config.font_size,
                    color=style.color,
                )

                current_x += text_width

    def _render_wrapped(
        self,
        canvas: CairoCanvas,
        lines: list[list[TokenInfo]],
        metrics: LayoutMetrics,
        theme: Theme,
        code_y_offset: float,
    ) -> None:
        """Render code with word-wrap aware display lines."""
        config = self._config

        # Pre-build flat char maps per source line for efficient slicing
        # Each entry: list of (char, token_type)
        char_maps: dict[int, list[tuple[str, str]]] = {}
        for line_idx, line_tokens in enumerate(lines):
            chars: list[tuple[str, str]] = []
            for token in line_tokens:
                for ch in token.text:
                    chars.append((ch, token.token_type))
            char_maps[line_idx] = chars

        wrap_indent_px = metrics.wrap_indent_chars * metrics.char_width

        for display_idx, dline in enumerate(metrics.display_lines):
            baseline_y = (
                metrics.content_y
                + code_y_offset
                + display_idx * metrics.line_height_px
                + metrics.baseline_offset
            )

            # Draw line number (only for non-continuation lines)
            if config.show_line_numbers and not dline.is_continuation:
                line_num = dline.source_line_idx + config.line_number_offset
                line_num_text = str(line_num)

                text_width, _ = canvas.measure_text(
                    line_num_text, config.font_family, config.font_size
                )
                line_num_x = metrics.gutter_x + metrics.gutter_width - text_width

                canvas.draw_text(
                    x=line_num_x,
                    y=baseline_y,
                    text=line_num_text,
                    font_family=config.font_family,
                    font_size=config.font_size,
                    color=theme.line_number_fg,
                )

            # Determine X start (continuations are indented)
            if dline.is_continuation:
                x_start = metrics.code_x + wrap_indent_px
            else:
                x_start = metrics.code_x

            # Determine char range for this display line
            source_chars = char_maps[dline.source_line_idx]
            char_start = dline.char_offset

            # Find end of this chunk by looking at next display line with same source
            char_end = len(source_chars)
            for next_dline in metrics.display_lines[display_idx + 1 :]:
                if next_dline.source_line_idx == dline.source_line_idx:
                    char_end = next_dline.char_offset
                    break
                elif next_dline.source_line_idx != dline.source_line_idx:
                    break

            chunk_chars = source_chars[char_start:char_end]

            # Group consecutive chars with same token_type into spans
            if not chunk_chars:
                continue

            current_x = x_start
            span_start = 0
            for i in range(1, len(chunk_chars) + 1):
                if (
                    i == len(chunk_chars)
                    or chunk_chars[i][1] != chunk_chars[span_start][1]
                ):
                    # Emit span
                    span_text = "".join(c[0] for c in chunk_chars[span_start:i])
                    token_type = chunk_chars[span_start][1]
                    style = theme.get_style(token_type)

                    text_width = canvas.draw_text(
                        x=current_x,
                        y=baseline_y,
                        text=span_text,
                        font_family=config.font_family,
                        font_size=config.font_size,
                        color=style.color,
                    )
                    current_x += text_width
                    span_start = i
