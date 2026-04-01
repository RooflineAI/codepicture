"""Line range parser, highlight color resolver, and named highlight styles.

Pure functions for converting user-specified line ranges into 0-based
source line indices, resolving highlight colors from hex strings, and
parsing named highlight style specifications.

The parser handles single lines (``"3"``), ranges (``"7-12"``), and mixed
input. The color resolver handles ``#RRGGBB`` (adding default alpha) and
``#RRGGBBAA`` formats. Named styles support ``"3-5:add"`` syntax.

Typical usage::

    from codepicture.render.highlights import (
        parse_line_ranges,
        resolve_highlight_color,
        parse_highlight_specs,
        HighlightStyle,
        DEFAULT_HIGHLIGHT_COLOR,
    )

    indices = parse_line_ranges(["3", "7-12"], total_lines=15)
    color = resolve_highlight_color("#FF000040")
    styles = parse_highlight_specs(["3-5:add", "10:remove"], total_lines=15)
"""

from __future__ import annotations

import re
from enum import Enum

from codepicture.core.types import Color
from codepicture.errors import InputError

__all__ = [
    "DARK_THEME_COLORS",
    "DEFAULT_HIGHLIGHT_COLOR",
    "DEFAULT_STYLE_COLORS",
    "FOCUS_DIM_OPACITY",
    "GUTTER_BAR_WIDTH",
    "GUTTER_INDICATORS",
    "HIGHLIGHT_CORNER_RADIUS",
    "HighlightStyle",
    "LIGHT_THEME_COLORS",
    "LUMINANCE_THRESHOLD",
    "_relative_luminance",
    "get_theme_style_colors",
    "parse_highlight_specs",
    "parse_line_ranges",
    "resolve_highlight_color",
    "resolve_style_color",
]


class HighlightStyle(str, Enum):
    """Built-in highlight style names."""

    HIGHLIGHT = "highlight"
    ADD = "add"
    REMOVE = "remove"
    FOCUS = "focus"

DEFAULT_HIGHLIGHT_ALPHA = 64
"""Default alpha for highlight colors (~25% opacity, 64/255)."""

DEFAULT_HIGHLIGHT_COLOR = Color(r=255, g=230, b=80, a=DEFAULT_HIGHLIGHT_ALPHA)
"""Warm yellow at ~25% opacity (#FFE65040)."""

HIGHLIGHT_CORNER_RADIUS = 0
"""Corner radius for highlight rectangles.

Sharp rectangles for now; extracted as a constant so Phase 13/14 can
switch to rounded/merged blocks without changing calling code.
"""

DEFAULT_STYLE_COLORS: dict[HighlightStyle, Color] = {
    HighlightStyle.HIGHLIGHT: Color(r=255, g=230, b=80, a=64),  # #FFE65040
    HighlightStyle.ADD: Color(r=0, g=204, b=64, a=64),  # #00CC4040
    HighlightStyle.REMOVE: Color(r=255, g=51, b=51, a=64),  # #FF333340
    HighlightStyle.FOCUS: Color(r=51, g=153, b=255, a=64),  # #3399FF40
}
"""Default background colors for each highlight style (D-12 palette)."""

LUMINANCE_THRESHOLD = 0.5
"""Luminance threshold for dark/light theme detection (BT.709)."""

DARK_THEME_COLORS: dict[HighlightStyle, Color] = {
    HighlightStyle.HIGHLIGHT: Color(r=255, g=230, b=80, a=64),  # #FFE65040
    HighlightStyle.ADD: Color(r=0, g=204, b=64, a=64),  # #00CC4040
    HighlightStyle.REMOVE: Color(r=255, g=51, b=51, a=64),  # #FF333340
    HighlightStyle.FOCUS: Color(r=51, g=153, b=255, a=64),  # #3399FF40
}
"""Vivid highlight colors for dark themes (matches DEFAULT_STYLE_COLORS)."""

LIGHT_THEME_COLORS: dict[HighlightStyle, Color] = {
    HighlightStyle.HIGHLIGHT: Color(r=184, g=150, b=0, a=64),  # #B8960040
    HighlightStyle.ADD: Color(r=0, g=136, b=34, a=64),  # #00882240
    HighlightStyle.REMOVE: Color(r=204, g=0, b=0, a=64),  # #CC000040
    HighlightStyle.FOCUS: Color(r=0, g=102, b=204, a=64),  # #0066CC40
}
"""Muted highlight colors for light themes (D-03)."""

GUTTER_INDICATORS: dict[HighlightStyle, str | None] = {
    HighlightStyle.HIGHLIGHT: None,  # colored bar (drawn as rect)
    HighlightStyle.ADD: "+",
    HighlightStyle.REMOVE: "-",
    HighlightStyle.FOCUS: None,  # colored bar (drawn as rect)
}
"""Gutter indicator characters for each highlight style (D-10)."""

FOCUS_DIM_OPACITY = 0.35
"""Opacity for non-focused lines when focus mode is active."""

GUTTER_BAR_WIDTH = 3
"""Width in pixels for gutter indicator bars (D-10)."""

def _relative_luminance(color: Color) -> float:
    """Relative luminance (BT.709) from an RGB Color."""
    return 0.2126 * (color.r / 255) + 0.7152 * (color.g / 255) + 0.0722 * (color.b / 255)


def get_theme_style_colors(background: Color) -> dict[HighlightStyle, Color]:
    """Return highlight palette appropriate for the given background color.

    Per D-01: Uses luminance-based detection. Dark themes get vivid colors (D-02),
    light themes get muted colors (D-03).
    """
    lum = _relative_luminance(background)
    if lum >= LUMINANCE_THRESHOLD:
        return dict(LIGHT_THEME_COLORS)
    return dict(DARK_THEME_COLORS)


_LINE_SPEC_RE = re.compile(r"^\d+(-\d+)?$")

_HIGHLIGHT_SPEC_RE = re.compile(r"^(\d+(?:-\d+)?)(?::(\w+))?$")
VALID_STYLES = frozenset(s.value for s in HighlightStyle)


def parse_line_ranges(
    specs: list[str],
    total_lines: int,
    line_number_offset: int = 1,
) -> set[int]:
    """Parse line range specs into 0-based source line indices.

    Converts user-facing line numbers (matching what appears in the gutter)
    into 0-based indices suitable for the rendering pipeline.

    Args:
        specs: Line range strings, e.g. ``["3", "7-12", "15"]``.
            Each element is either a single number or a dash-separated range.
        total_lines: Number of source lines in the code.
        line_number_offset: Starting line number shown in the gutter.
            Default is ``1`` (standard 1-based numbering).

    Returns:
        Set of 0-based source line indices.

    Raises:
        InputError: If any spec has invalid syntax (not ``N`` or ``N-M``).
        InputError: If a range has start greater than end (e.g. ``"5-3"``).
        InputError: If any line number is out of bounds.
    """
    result: set[int] = set()
    max_line_num = total_lines + line_number_offset - 1

    for spec in specs:
        spec = spec.strip()

        if not _LINE_SPEC_RE.match(spec):
            raise InputError(
                f"Invalid line spec '{spec}'. Use N or N-M format (e.g. '3' or '7-12')"
            )

        if "-" in spec:
            parts = spec.split("-", maxsplit=1)
            start_num, end_num = int(parts[0]), int(parts[1])

            if start_num > end_num:
                raise InputError(
                    f"Invalid range '{spec}': start ({start_num}) "
                    f"must not exceed end ({end_num})"
                )

            for line_num in range(start_num, end_num + 1):
                idx = line_num - line_number_offset
                if idx < 0 or idx >= total_lines:
                    raise InputError(
                        f"Line {line_num} is out of range "
                        f"(valid: {line_number_offset}-{max_line_num})"
                    )
                result.add(idx)
        else:
            line_num = int(spec)
            idx = line_num - line_number_offset
            if idx < 0 or idx >= total_lines:
                raise InputError(
                    f"Line {line_num} is out of range "
                    f"(valid: {line_number_offset}-{max_line_num})"
                )
            result.add(idx)

    return result


def resolve_highlight_color(color_str: str | None) -> Color:
    """Resolve a highlight color from a hex string or return the default.

    Accepts ``#RRGGBB`` (6-char) and ``#RRGGBBAA`` (8-char) formats.
    When a 6-char hex is provided, the alpha is set to the default ~25%
    opacity (64/255) to ensure the highlight is visible but not
    overwhelming.

    Args:
        color_str: Hex color string (``"#FF0000"`` or ``"#FF000040"``),
            or ``None`` to use the default highlight color.

    Returns:
        Resolved :class:`~codepicture.core.types.Color` instance.
    """
    if color_str is None:
        return DEFAULT_HIGHLIGHT_COLOR

    color = Color.from_hex(color_str)

    # 6-char hex: user specified RGB but not alpha -- apply default opacity
    if len(color_str.lstrip("#")) == 6:
        color = Color(r=color.r, g=color.g, b=color.b, a=DEFAULT_HIGHLIGHT_ALPHA)

    return color


def parse_highlight_specs(
    specs: list[str],
    total_lines: int,
    line_number_offset: int = 1,
) -> dict[int, HighlightStyle]:
    """Parse highlight specs into per-line style map.

    Each spec is 'N', 'N-M', 'N:style', or 'N-M:style'.
    Last spec wins for overlapping lines (per D-03).
    Returns dict mapping 0-based line index to HighlightStyle.

    Args:
        specs: Highlight spec strings, e.g. ``["3-5:add", "10:remove"]``.
        total_lines: Number of source lines in the code.
        line_number_offset: Starting line number shown in the gutter.

    Returns:
        Dict mapping 0-based line indices to their highlight style.

    Raises:
        InputError: If any spec has invalid syntax or unknown style name.
    """
    result: dict[int, HighlightStyle] = {}
    for spec in specs:
        spec = spec.strip()
        match = _HIGHLIGHT_SPEC_RE.match(spec)
        if not match:
            raise InputError(
                f"Invalid highlight spec '{spec}'. "
                "Use N, N-M, N:style, or N-M:style format"
            )
        line_part = match.group(1)
        style_name = match.group(2) or "highlight"
        if style_name not in VALID_STYLES:
            raise InputError(
                f"Unknown highlight style '{style_name}'. "
                f"Valid styles: {', '.join(sorted(VALID_STYLES))}"
            )
        style = HighlightStyle(style_name)
        indices = parse_line_ranges([line_part], total_lines, line_number_offset)
        for idx in indices:
            result[idx] = style
    return result


def resolve_style_color(
    style: HighlightStyle,
    style_overrides: dict[str, str | None] | None = None,
    theme_defaults: dict[HighlightStyle, Color] | None = None,
) -> Color:
    """Resolve the color for a highlight style.

    Precedence chain (per D-05):
    1. TOML per-style override (style_overrides)
    2. Theme-derived defaults (theme_defaults)
    3. Hardcoded DEFAULT_STYLE_COLORS fallback

    Args:
        style: The highlight style to resolve color for.
        style_overrides: Dict mapping style name to hex color string.
            Comes from config highlight_styles section.
        theme_defaults: Theme-derived palette from get_theme_style_colors().
            If provided, used as fallback before DEFAULT_STYLE_COLORS.

    Returns:
        Resolved Color for the style.
    """
    if style_overrides:
        override = style_overrides.get(style.value)
        if override:
            color = Color.from_hex(override)
            # 6-char hex: apply default alpha
            if len(override.lstrip("#")) == 6:
                color = Color(r=color.r, g=color.g, b=color.b, a=DEFAULT_HIGHLIGHT_ALPHA)
            return color
    if theme_defaults:
        return theme_defaults[style]
    return DEFAULT_STYLE_COLORS[style]
