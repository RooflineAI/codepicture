"""Line range parser and highlight color resolver.

Pure functions for converting user-specified line ranges into 0-based
source line indices and resolving highlight colors from hex strings.

These are the core logic building blocks for line highlighting. The parser
handles single lines (``"3"``), ranges (``"7-12"``), and mixed input.
The color resolver handles ``#RRGGBB`` (adding default alpha) and
``#RRGGBBAA`` formats.

Typical usage::

    from codepicture.render.highlights import (
        parse_line_ranges,
        resolve_highlight_color,
        DEFAULT_HIGHLIGHT_COLOR,
    )

    indices = parse_line_ranges(["3", "7-12"], total_lines=15)
    color = resolve_highlight_color("#FF000040")
"""

from __future__ import annotations

import re

from codepicture.core.types import Color
from codepicture.errors import InputError

__all__ = [
    "DEFAULT_HIGHLIGHT_COLOR",
    "HIGHLIGHT_CORNER_RADIUS",
    "parse_line_ranges",
    "resolve_highlight_color",
]

DEFAULT_HIGHLIGHT_ALPHA = 64
"""Default alpha for highlight colors (~25% opacity, 64/255)."""

DEFAULT_HIGHLIGHT_COLOR = Color(r=255, g=230, b=80, a=DEFAULT_HIGHLIGHT_ALPHA)
"""Warm yellow at ~25% opacity (#FFE65040)."""

HIGHLIGHT_CORNER_RADIUS = 0
"""Corner radius for highlight rectangles.

Sharp rectangles for now; extracted as a constant so Phase 13/14 can
switch to rounded/merged blocks without changing calling code.
"""

_LINE_SPEC_RE = re.compile(r"^\d+(-\d+)?$")


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
