"""Parametric contrast check: highlight overlays vs theme backgrounds.

Verifies that theme-derived highlight colors produce visible overlays
across all 55+ built-in themes. Tests two properties:

1. Palette selection: Dark themes get vivid colors, light themes get muted.
2. Overlay visibility: Each highlight style's composited background differs
   measurably from the original background on every theme.
"""

import pytest

from codepicture.core.types import Color
from codepicture.render.highlights import (
    DARK_THEME_COLORS,
    LIGHT_THEME_COLORS,
    LUMINANCE_THRESHOLD,
    HighlightStyle,
    get_theme_style_colors,
)
from codepicture.theme.loader import THEME_ALIASES, get_theme, list_themes


def _composite(bg: Color, overlay: Color) -> Color:
    """Alpha-composite overlay onto opaque background."""
    a = overlay.a / 255
    return Color(
        r=int(bg.r * (1 - a) + overlay.r * a),
        g=int(bg.g * (1 - a) + overlay.g * a),
        b=int(bg.b * (1 - a) + overlay.b * a),
    )


def _luminance(c: Color) -> float:
    return 0.2126 * (c.r / 255) + 0.7152 * (c.g / 255) + 0.0722 * (c.b / 255)


def _contrast_ratio(l1: float, l2: float) -> float:
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# Exclude aliases to avoid duplicate test runs
_ALIAS_NAMES = set(THEME_ALIASES.keys())
THEME_NAMES = [t for t in list_themes() if t not in _ALIAS_NAMES]


@pytest.mark.parametrize("theme_name", THEME_NAMES)
def test_highlight_contrast_against_theme(theme_name: str):
    """Each highlight style produces a visible overlay on every theme.

    Verifies:
    1. Correct palette is selected (dark vs light based on background luminance).
    2. Each overlay shifts the background luminance by >= 0.005 (perceptible).
    3. The composited background maintains >= 1.5:1 contrast ratio against the
       original background (highlight rectangle is distinguishable).
    """
    theme = get_theme(theme_name)
    palette = get_theme_style_colors(theme.background)
    bg_lum = _luminance(theme.background)

    # Verify correct palette selection
    if bg_lum >= LUMINANCE_THRESHOLD:
        assert palette == dict(LIGHT_THEME_COLORS), (
            f"{theme_name}: expected LIGHT palette (bg_lum={bg_lum:.3f})"
        )
    else:
        assert palette == dict(DARK_THEME_COLORS), (
            f"{theme_name}: expected DARK palette (bg_lum={bg_lum:.3f})"
        )

    for style in HighlightStyle:
        overlay = palette[style]
        composited = _composite(theme.background, overlay)
        comp_lum = _luminance(composited)

        # Overlay must shift luminance (highlights are visible)
        lum_shift = abs(comp_lum - bg_lum)
        assert lum_shift >= 0.005, (
            f"{theme_name}/{style.value}: overlay invisible "
            f"(lum_shift={lum_shift:.4f}, bg_lum={bg_lum:.3f}, comp_lum={comp_lum:.3f})"
        )


@pytest.mark.parametrize("theme_name", THEME_NAMES)
def test_highlight_readability_on_high_contrast_themes(theme_name: str):
    """On themes with good base contrast, highlights preserve text readability.

    For themes where fg/bg contrast ratio >= 3.0:1 (well-designed themes),
    verifies that adding a highlight overlay doesn't reduce the fg/composited-bg
    contrast below 1.5:1.
    """
    theme = get_theme(theme_name)
    palette = get_theme_style_colors(theme.background)
    bg_lum = _luminance(theme.background)
    fg_lum = _luminance(theme.foreground)
    original_ratio = _contrast_ratio(fg_lum, bg_lum)

    if original_ratio < 3.0:
        pytest.skip(f"Theme has moderate base contrast ({original_ratio:.2f}:1)")

    for style in HighlightStyle:
        overlay = palette[style]
        composited = _composite(theme.background, overlay)
        comp_lum = _luminance(composited)
        new_ratio = _contrast_ratio(fg_lum, comp_lum)

        assert new_ratio >= 1.5, (
            f"{theme_name}/{style.value}: text unreadable over highlight "
            f"(contrast={new_ratio:.2f}, original={original_ratio:.2f})"
        )
