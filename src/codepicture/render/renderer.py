"""High-level renderer orchestrating all drawing operations.

Renderer takes highlighted code, layout metrics, theme, and config,
then produces the final output image by coordinating CairoCanvas,
chrome, and shadow modules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from codepicture.config.schema import RenderConfig
from codepicture.core.types import (
    Color,
    LayoutMetrics,
    OutputFormat,
    RenderResult,
    WindowStyle,
)
from codepicture.render.canvas import CairoCanvas
from codepicture.render.chrome import TITLE_BAR_HEIGHT, draw_title_bar
from codepicture.render.highlights import (
    FOCUS_DIM_OPACITY,
    GUTTER_BAR_WIDTH,
    GUTTER_INDICATORS,
    HIGHLIGHT_CORNER_RADIUS,
    HighlightStyle,
    parse_highlight_specs,
    resolve_style_color,
)
from codepicture.render.shadow import apply_shadow, calculate_shadow_margin

if TYPE_CHECKING:
    from codepicture.core.protocols import Theme
    from codepicture.highlight import TokenInfo

__all__ = ["Renderer", "_dim_color"]


def _dim_color(color: Color, factor: float) -> Color:
    """Reduce color opacity for focus mode dimming."""
    return Color(r=color.r, g=color.g, b=color.b, a=int(color.a * factor))


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

        # Resolve named highlight styles
        style_map: dict[int, HighlightStyle] = {}
        style_colors: dict[HighlightStyle, Color] = {}
        style_overrides: dict[str, str | None] | None = None

        if config.highlight_styles:
            style_overrides = {
                name: sc.color for name, sc in config.highlight_styles.items()
            }

        if config.highlights:
            style_map = parse_highlight_specs(
                config.highlights,
                total_lines=len(lines),
                line_number_offset=config.line_number_offset,
            )
            # Pre-resolve colors for all styles in use
            for style in set(style_map.values()):
                style_colors[style] = resolve_style_color(style, style_overrides)

        # Detect focus mode (per D-08)
        focus_mode = any(s == HighlightStyle.FOCUS for s in style_map.values())

        # Pre-compute gutter indicator colors (high opacity for small elements)
        indicator_colors: dict[HighlightStyle, Color] = {}
        if style_map and config.show_line_numbers:
            for style in set(style_map.values()):
                base = resolve_style_color(style, style_overrides)
                indicator_colors[style] = Color(
                    r=base.r,
                    g=base.g,
                    b=base.b,
                    a=min(255, int(base.a * 255 / 64 * 0.9))
                    if base.a < 255
                    else 230,
                )

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
            self._render_wrapped(
                canvas,
                lines,
                metrics,
                theme,
                code_y_offset,
                style_map,
                style_colors,
                focus_mode,
                indicator_colors,
            )
        else:
            # Legacy rendering path (no wrapping)
            self._render_legacy(
                canvas,
                lines,
                metrics,
                theme,
                code_y_offset,
                style_map,
                style_colors,
                focus_mode,
                indicator_colors,
            )

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
        style_map: dict[int, HighlightStyle],
        style_colors: dict[HighlightStyle, Color],
        focus_mode: bool,
        indicator_colors: dict[HighlightStyle, Color],
    ) -> None:
        """Render code using the original (non-wrapped) path."""
        config = self._config

        # Draw highlight rectangles (behind all text)
        if style_map:
            for line_idx in range(len(lines)):
                if line_idx in style_map:
                    hl_style = style_map[line_idx]
                    highlight_y = (
                        metrics.content_y
                        + code_y_offset
                        + line_idx * metrics.line_height_px
                    )
                    canvas.draw_rectangle(
                        x=metrics.content_x,
                        y=highlight_y,
                        width=metrics.content_width,
                        height=metrics.line_height_px,
                        color=style_colors[hl_style],
                        corner_radius=HIGHLIGHT_CORNER_RADIUS,
                    )

        # Draw gutter indicators (between line numbers and code)
        if config.show_line_numbers and style_map:
            for line_idx in range(len(lines)):
                if line_idx in style_map:
                    hl_style = style_map[line_idx]
                    ind_color = indicator_colors[hl_style]

                    baseline_y = (
                        metrics.content_y
                        + code_y_offset
                        + line_idx * metrics.line_height_px
                        + metrics.baseline_offset
                    )
                    symbol = GUTTER_INDICATORS.get(hl_style)
                    if symbol:  # "+" or "-"
                        canvas.draw_text(
                            x=metrics.gutter_indicator_x,
                            y=baseline_y,
                            text=symbol,
                            font_family=config.font_family,
                            font_size=config.font_size,
                            color=ind_color,
                        )
                    else:  # colored bar for highlight/focus
                        bar_y = (
                            metrics.content_y
                            + code_y_offset
                            + line_idx * metrics.line_height_px
                        )
                        canvas.draw_rectangle(
                            x=metrics.gutter_indicator_x
                            + (metrics.gutter_indicator_width - GUTTER_BAR_WIDTH) / 2,
                            y=bar_y,
                            width=GUTTER_BAR_WIDTH,
                            height=metrics.line_height_px,
                            color=ind_color,
                        )

        # Draw line numbers if enabled
        if config.show_line_numbers:
            for line_idx, _line_tokens in enumerate(lines):
                line_number_color = theme.line_number_fg
                if focus_mode and line_idx not in style_map:
                    line_number_color = _dim_color(
                        line_number_color, FOCUS_DIM_OPACITY
                    )

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
                token_style = theme.get_style(token.token_type)
                token_color = token_style.color
                if focus_mode and line_idx not in style_map:
                    token_color = _dim_color(token_color, FOCUS_DIM_OPACITY)

                text_width = canvas.draw_text(
                    x=current_x,
                    y=baseline_y,
                    text=token.text,
                    font_family=config.font_family,
                    font_size=config.font_size,
                    color=token_color,
                )

                current_x += text_width

    def _render_wrapped(
        self,
        canvas: CairoCanvas,
        lines: list[list[TokenInfo]],
        metrics: LayoutMetrics,
        theme: Theme,
        code_y_offset: float,
        style_map: dict[int, HighlightStyle],
        style_colors: dict[HighlightStyle, Color],
        focus_mode: bool,
        indicator_colors: dict[HighlightStyle, Color],
    ) -> None:
        """Render code with word-wrap aware display lines."""
        config = self._config

        # Draw highlight rectangles (behind all text)
        if style_map:
            for display_idx, dline in enumerate(metrics.display_lines):
                if dline.source_line_idx in style_map:
                    hl_style = style_map[dline.source_line_idx]
                    highlight_y = (
                        metrics.content_y
                        + code_y_offset
                        + display_idx * metrics.line_height_px
                    )
                    canvas.draw_rectangle(
                        x=metrics.content_x,
                        y=highlight_y,
                        width=metrics.content_width,
                        height=metrics.line_height_px,
                        color=style_colors[hl_style],
                        corner_radius=HIGHLIGHT_CORNER_RADIUS,
                    )

        # Draw gutter indicators (non-continuation lines only)
        if config.show_line_numbers and style_map:
            for display_idx, dline in enumerate(metrics.display_lines):
                if not dline.is_continuation and dline.source_line_idx in style_map:
                    hl_style = style_map[dline.source_line_idx]
                    ind_color = indicator_colors[hl_style]

                    baseline_y = (
                        metrics.content_y
                        + code_y_offset
                        + display_idx * metrics.line_height_px
                        + metrics.baseline_offset
                    )
                    symbol = GUTTER_INDICATORS.get(hl_style)
                    if symbol:  # "+" or "-"
                        canvas.draw_text(
                            x=metrics.gutter_indicator_x,
                            y=baseline_y,
                            text=symbol,
                            font_family=config.font_family,
                            font_size=config.font_size,
                            color=ind_color,
                        )
                    else:  # colored bar for highlight/focus
                        bar_y = (
                            metrics.content_y
                            + code_y_offset
                            + display_idx * metrics.line_height_px
                        )
                        canvas.draw_rectangle(
                            x=metrics.gutter_indicator_x
                            + (metrics.gutter_indicator_width - GUTTER_BAR_WIDTH) / 2,
                            y=bar_y,
                            width=GUTTER_BAR_WIDTH,
                            height=metrics.line_height_px,
                            color=ind_color,
                        )

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
                line_number_color = theme.line_number_fg
                if focus_mode and dline.source_line_idx not in style_map:
                    line_number_color = _dim_color(
                        line_number_color, FOCUS_DIM_OPACITY
                    )

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
                    color=line_number_color,
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

            # Determine if this line should be dimmed
            is_dimmed = focus_mode and dline.source_line_idx not in style_map

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
                    token_style = theme.get_style(token_type)
                    token_color = token_style.color
                    if is_dimmed:
                        token_color = _dim_color(token_color, FOCUS_DIM_OPACITY)

                    text_width = canvas.draw_text(
                        x=current_x,
                        y=baseline_y,
                        text=span_text,
                        font_family=config.font_family,
                        font_size=config.font_size,
                        color=token_color,
                    )
                    current_x += text_width
                    span_start = i
