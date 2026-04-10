# Phase 14: Theme Integration & Documentation - Research

**Researched:** 2026-03-31
**Domain:** Color science (luminance-based palette selection), Python rendering pipeline integration, documentation
**Confidence:** HIGH

## Summary

Phase 14 has two distinct workstreams: (1) theme-aware highlight color derivation that selects appropriate palettes based on background luminance, and (2) README documentation with auto-generated visual examples.

The theme integration is well-scoped. The existing `resolve_style_color()` function in `highlights.py` is the single point where theme-derived defaults replace hardcoded `DEFAULT_STYLE_COLORS`. The `Renderer.render()` method already has the theme object available and builds `style_colors` before entering render paths -- the integration is a matter of passing theme background into the color resolution chain. The 55 available themes split cleanly: ~24 dark (luminance < 0.5) and ~31 light (luminance >= 0.5), with no ambiguous middle-ground themes.

The documentation workstream is straightforward but has one constraint: "GitHub Light" (specified in D-10 for visual examples) does not exist as a Pygments theme. The closest light theme is `catppuccin-latte` (luminance 0.913). The planner should substitute `catppuccin-latte` for the light-theme example images.

**Primary recommendation:** Add a `get_theme_style_colors(background: Color) -> dict[HighlightStyle, Color]` function to `highlights.py` that returns the dark or light palette based on luminance. Modify `resolve_style_color()` to accept optional theme-derived defaults, maintaining the existing override precedence chain.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Luminance-based approach: detect if theme background is light or dark via luminance calculation. Use warm/vivid colors on dark themes, cooler/muted colors on light themes.
- **D-02:** Dark theme palette (luminance < threshold): bright green (#00CC4040), bright red (#FF333340), bright blue (#3399FF40), warm yellow (#FFE65040) -- same as current defaults.
- **D-03:** Light theme palette (luminance >= threshold): darker green (#00882240), darker red (#CC000040), darker blue (#0066CC40), muted yellow (#B8960040).
- **D-04:** Luminance threshold value and alpha/opacity behavior across themes: Claude's discretion.
- **D-05:** Full replace precedence chain: explicit user color wins entirely over theme-derived colors. (1) Per-style TOML color, (2) Global --highlight-color CLI flag, (3) Theme-derived color, (4) Hardcoded DEFAULT_STYLE_COLORS fallback.
- **D-06:** Per-style TOML overrides take precedence over the global --highlight-color flag.
- **D-07:** New `## Line Highlighting` section in README after existing feature docs. Subsections: Quick Start, Highlight Styles, Configuration (TOML), Theme Integration.
- **D-08:** TOML config examples should be complete with inline comments -- copy-paste ready.
- **D-09:** Auto-generate example images using codepicture itself. A script (e.g., `docs/generate-examples.sh`) runs codepicture commands to produce images. Images committed to `docs/examples/`.
- **D-10:** Showcase one dark theme (Catppuccin Mocha) and one light theme (GitHub Light), each showing all 4 highlight styles. Plus a focus mode example. ~3 images total in README.
- **D-11:** Parametric contrast check across all 55+ built-in themes. Test parametrized over `list_themes()`.
- **D-12:** Two visual regression snapshots: one dark theme (Catppuccin Mocha) and one light theme (GitHub Light).

### Claude's Discretion
- Luminance threshold value (hardcoded vs configurable, exact cutoff)
- Alpha/opacity adjustment per theme (same alpha or adjusted)
- Exact color values for light theme palette within the specified family
- Contrast ratio threshold for parametric tests
- Example script format (shell script vs Makefile target)
- Demo code snippet content for example images

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HLTHEM-01 | Default highlight colors are derived from the active theme's background color | Luminance calculation on `theme.background` Color object; `get_theme_style_colors()` function returns palette based on luminance; integration in `Renderer.render()` |
| HLTHEM-02 | Theme-aware colors maintain readable contrast for syntax tokens on highlighted lines | Parametric test across all 55 themes; light palette uses darker/muted colors that don't wash out syntax tokens on white backgrounds |
| HLTHEM-03 | User-specified --highlight-color and TOML style colors override theme-derived defaults | Precedence chain in `resolve_style_color()`: TOML per-style > global highlight_color > theme-derived > hardcoded fallback |
| HLDOC-01 | README documents all highlight CLI flags with usage examples | New `## Line Highlighting` section in README with CLI flag table and usage examples |
| HLDOC-02 | README documents TOML config options for highlight styles and colors | Copy-paste-ready TOML examples with inline comments in README |
| HLDOC-03 | README includes visual examples showing highlight styles | Auto-generated images via `docs/generate-examples.sh`; images in `docs/examples/`; ~3 images in README |
</phase_requirements>

## Architecture Patterns

### Integration Point: Renderer.render()

The theme-derived color logic slots into `Renderer.render()` at line ~98 where `style_colors` dict is built. Currently:

```python
# Current (highlights.py line 237-262)
def resolve_style_color(
    style: HighlightStyle,
    style_overrides: dict[str, str | None] | None = None,
) -> Color:
    if style_overrides:
        override = style_overrides.get(style.value)
        if override:
            # ... parse override
            return color
    return DEFAULT_STYLE_COLORS[style]  # <-- this is where theme defaults go
```

**New approach:** Add `theme_defaults` parameter:

```python
def resolve_style_color(
    style: HighlightStyle,
    style_overrides: dict[str, str | None] | None = None,
    theme_defaults: dict[HighlightStyle, Color] | None = None,
) -> Color:
    # 1. TOML per-style override (highest priority)
    if style_overrides:
        override = style_overrides.get(style.value)
        if override:
            return _parse_color_override(override)
    # 2. Theme-derived defaults
    if theme_defaults and style in theme_defaults:
        return theme_defaults[style]
    # 3. Hardcoded fallback
    return DEFAULT_STYLE_COLORS[style]
```

### Luminance Calculation

Standard relative luminance formula (BT.709/sRGB):

```python
def _relative_luminance(color: Color) -> float:
    """Calculate relative luminance per WCAG 2.0 (BT.709 coefficients)."""
    return 0.2126 * (color.r / 255) + 0.7152 * (color.g / 255) + 0.0722 * (color.b / 255)
```

**Note:** This is a simplified linear calculation. Full sRGB linearization (gamma correction) is more accurate but unnecessary here -- we're making a binary light/dark decision, not computing precise WCAG contrast ratios. The simplified version correctly classifies all 55 themes.

### Theme Distribution (verified against all 55 themes)

Using threshold 0.5:
- **Dark themes (24):** catppuccin-mocha (0.098), vim (0.000), rrt (0.000), fruity (0.067), github-dark (0.065), native (0.125), dracula (0.166), monokai (0.154), one-dark (0.171), nord (0.202), zenburn (0.247), and 13 others. All have luminance 0.000-0.247.
- **Light themes (31):** catppuccin-latte (0.913), solarized-light (0.965), gruvbox-light (0.942), default (0.973), and 27 `#ffffff` themes at luminance 1.000.
- **Gap:** No theme has luminance between 0.247 and 0.908. The threshold value anywhere in 0.3-0.8 produces identical results.

**Recommended threshold: 0.5** (simple, standard, well within the gap).

### Palettes (from D-02 and D-03)

```python
DARK_THEME_COLORS: dict[HighlightStyle, Color] = {
    HighlightStyle.HIGHLIGHT: Color(r=255, g=230, b=80, a=64),   # #FFE65040
    HighlightStyle.ADD:       Color(r=0, g=204, b=64, a=64),     # #00CC4040
    HighlightStyle.REMOVE:    Color(r=255, g=51, b=51, a=64),    # #FF333340
    HighlightStyle.FOCUS:     Color(r=51, g=153, b=255, a=64),   # #3399FF40
}

LIGHT_THEME_COLORS: dict[HighlightStyle, Color] = {
    HighlightStyle.HIGHLIGHT: Color(r=184, g=150, b=0, a=64),    # #B8960040
    HighlightStyle.ADD:       Color(r=0, g=136, b=34, a=64),     # #00882240
    HighlightStyle.REMOVE:    Color(r=204, g=0, b=0, a=64),      # #CC000040
    HighlightStyle.FOCUS:     Color(r=0, g=102, b=204, a=64),    # #0066CC40
}
```

**Note:** `DARK_THEME_COLORS` is identical to the current `DEFAULT_STYLE_COLORS`. This means the hardcoded fallback (step 4 in precedence chain) naturally produces the dark theme palette, and theme derivation only changes behavior for light themes. This is a nice backward-compatibility property.

### Recommended Project Structure Changes

```
src/codepicture/render/highlights.py  # Add: LIGHT_THEME_COLORS, get_theme_style_colors(), update resolve_style_color()
src/codepicture/render/renderer.py    # Pass theme.background to color resolution
docs/generate-examples.sh             # NEW: script to generate example images
docs/examples/                        # NEW: directory for generated example images
README.md                             # Add: ## Line Highlighting section
tests/test_highlights.py              # Add: theme color derivation unit tests
tests/theme/test_contrast.py          # NEW: parametric contrast check across all themes
tests/visual/test_visual_regression.py # Add: dark+light theme highlight snapshots
```

### Anti-Patterns to Avoid
- **Modifying theme objects:** Theme derivation should be a pure function on the background Color, not a mutation of PygmentsTheme/TomlTheme.
- **Per-token contrast checking:** D-02/D-03 specify overlay colors at 25% opacity. The contrast check should verify highlight overlay vs background, not per-token readability (tokens are drawn ON TOP of highlights).
- **Breaking existing visual regression baselines:** Current tests use catppuccin-mocha (dark theme). Since dark palette = current palette, existing snapshots should NOT change. Only new light-theme snapshots are added.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Luminance calculation | Custom color space math | BT.709 formula (3 multiplications) | Standard, well-known formula |
| Image comparison | Custom pixel diffing | pixelmatch (already in project) | Used by all existing visual tests |
| SVG rasterization | Headless browser rendering | cairosvg (already in project) | Used by all existing SVG tests |

## Common Pitfalls

### Pitfall 1: "GitHub Light" Theme Does Not Exist
**What goes wrong:** D-10 and D-12 reference "GitHub Light" for visual examples and regression snapshots. Pygments only has `github-dark`.
**Why it happens:** The theme name was assumed available during discussion.
**How to avoid:** Substitute `catppuccin-latte` (luminance 0.913, part of the Catppuccin family matching the dark example). Alternatively use `solarized-light` (0.965) or `gruvbox-light` (0.942).
**Warning signs:** Import errors or ThemeError when running example generation or tests.

### Pitfall 2: Precedence Chain vs --highlight-color Removal
**What goes wrong:** D-05 lists `--highlight-color` as step 2 in the precedence chain, but Phase 13 decision 13-01 removed `--highlight-color` from CLI. The `highlight_color` field still exists in `RenderConfig` schema but is only accessible via TOML config.
**Why it happens:** The precedence chain was written before the Phase 13 removal decision.
**How to avoid:** The precedence chain still works correctly -- `highlight_color` is still in the schema and the legacy migration path. The TOML `highlight_color` value applies as a global default color. Per-style TOML colors override it. Theme-derived colors are the new step 3. No code conflict, but documentation should clarify that `--highlight-color` is not a CLI flag (TOML-only).
**Warning signs:** README documenting a `--highlight-color` flag that doesn't exist.

### Pitfall 3: Existing Snapshot Breakage
**What goes wrong:** Changing how colors are resolved in `resolve_style_color()` could break all existing visual regression tests.
**Why it happens:** If the theme-derived path runs unconditionally for the default theme (catppuccin-mocha), and the dark palette differs from `DEFAULT_STYLE_COLORS`.
**How to avoid:** Dark palette IS the current default palette (identical colors). As long as the dark palette constant matches `DEFAULT_STYLE_COLORS` exactly, no existing test should break. Verify this with an assertion in the code or a unit test.
**Warning signs:** Unexpected visual regression failures on existing tests.

### Pitfall 4: Contrast Check Approach
**What goes wrong:** Testing that syntax tokens remain "readable" on highlighted lines is subjective and hard to automate meaningfully.
**Why it happens:** Highlight overlays are semi-transparent (alpha=64, ~25% opacity). The effective color depends on alpha compositing with the background. Token colors vary widely per theme.
**How to avoid:** The parametric test should verify that the highlight overlay color, when composited onto the theme background, doesn't reduce the luminance contrast ratio between background-with-overlay and foreground-text below a minimum threshold. A practical approach: compute `composite = lerp(background, highlight_rgb, highlight_alpha/255)`, then check `contrast_ratio(composite, foreground) >= minimum` (e.g., 2.0:1 -- less strict than WCAG AA 4.5:1 because these are code editors, not accessibility-critical UIs).
**Warning signs:** Test that passes for all themes but doesn't actually verify anything meaningful.

## Code Examples

### Luminance-based palette selection

```python
# In highlights.py
LUMINANCE_THRESHOLD = 0.5

DARK_THEME_COLORS: dict[HighlightStyle, Color] = {
    HighlightStyle.HIGHLIGHT: Color(r=255, g=230, b=80, a=64),
    HighlightStyle.ADD: Color(r=0, g=204, b=64, a=64),
    HighlightStyle.REMOVE: Color(r=255, g=51, b=51, a=64),
    HighlightStyle.FOCUS: Color(r=51, g=153, b=255, a=64),
}

LIGHT_THEME_COLORS: dict[HighlightStyle, Color] = {
    HighlightStyle.HIGHLIGHT: Color(r=184, g=150, b=0, a=64),
    HighlightStyle.ADD: Color(r=0, g=136, b=34, a=64),
    HighlightStyle.REMOVE: Color(r=204, g=0, b=0, a=64),
    HighlightStyle.FOCUS: Color(r=0, g=102, b=204, a=64),
}


def _relative_luminance(color: Color) -> float:
    """Relative luminance (BT.709) from an RGB Color."""
    return 0.2126 * (color.r / 255) + 0.7152 * (color.g / 255) + 0.0722 * (color.b / 255)


def get_theme_style_colors(background: Color) -> dict[HighlightStyle, Color]:
    """Return highlight palette appropriate for the given background color."""
    lum = _relative_luminance(background)
    if lum >= LUMINANCE_THRESHOLD:
        return dict(LIGHT_THEME_COLORS)
    return dict(DARK_THEME_COLORS)
```

### Integration in Renderer.render()

```python
# In renderer.py, inside render() method, after style_map is built:
from codepicture.render.highlights import get_theme_style_colors

# Get theme-derived defaults
theme_defaults = get_theme_style_colors(theme.background)

# Pre-resolve colors for all styles in use
for style in set(style_map.values()):
    style_colors[style] = resolve_style_color(style, style_overrides, theme_defaults)
```

### Parametric contrast test

```python
# In tests/theme/test_contrast.py
import pytest
from codepicture.theme.loader import list_themes, get_theme
from codepicture.render.highlights import get_theme_style_colors, HighlightStyle

def _composite(bg: Color, overlay: Color) -> Color:
    """Alpha-composite overlay onto bg."""
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

THEME_NAMES = [t for t in list_themes() if t not in ('catppuccin', 'onedark')]  # skip aliases

@pytest.mark.parametrize("theme_name", THEME_NAMES)
def test_highlight_contrast_against_theme(theme_name: str):
    theme = get_theme(theme_name)
    palette = get_theme_style_colors(theme.background)
    fg_lum = _luminance(theme.foreground)
    for style in HighlightStyle:
        overlay = palette[style]
        composited = _composite(theme.background, overlay)
        comp_lum = _luminance(composited)
        ratio = _contrast_ratio(fg_lum, comp_lum)
        assert ratio >= 2.0, (
            f"{theme_name}/{style.value}: contrast {ratio:.2f} < 2.0"
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded DEFAULT_STYLE_COLORS for all themes | Theme-derived palettes (this phase) | Phase 14 | Light themes get appropriate colors |
| `--highlight-color` CLI flag | Removed in Phase 13; TOML-only | Phase 13 | Documentation must not reference CLI flag |

## Open Questions

1. **GitHub Light theme unavailability**
   - What we know: Pygments does not include a "github-light" theme. Only `github-dark` exists.
   - What's unclear: Whether the user specifically wants GitHub Light or any representative light theme.
   - Recommendation: Substitute `catppuccin-latte` (same family as dark example, good luminance at 0.913). Flag in plan for user to confirm.

2. **Contrast ratio threshold for parametric tests**
   - What we know: WCAG AA requires 4.5:1 for normal text. These are semi-transparent overlays on code editor backgrounds, not accessibility-critical text contrast.
   - What's unclear: What ratio meaningfully ensures "readable" syntax tokens on highlighted lines.
   - Recommendation: Use 2.0:1 as the minimum. This is sufficient to ensure the overlay doesn't destroy readability while being achievable for all 55 themes. If any theme fails, adjust the light palette alpha rather than the threshold.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2+ |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_highlights.py tests/theme/ -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HLTHEM-01 | Theme-derived highlight colors based on background luminance | unit | `uv run pytest tests/test_highlights.py -x -k "theme_color"` | Partially (test_highlights.py exists, new tests needed) |
| HLTHEM-02 | Contrast maintained across all 55 themes | unit (parametric) | `uv run pytest tests/theme/test_contrast.py -x` | Wave 0 |
| HLTHEM-03 | User overrides take precedence over theme defaults | unit | `uv run pytest tests/test_highlights.py -x -k "override"` | Partially (existing override tests, extend for theme defaults) |
| HLDOC-01 | README documents CLI flags | manual | Visual inspection of README.md | N/A |
| HLDOC-02 | README documents TOML config | manual | Visual inspection of README.md | N/A |
| HLDOC-03 | README includes visual examples | manual + smoke | `bash docs/generate-examples.sh && ls docs/examples/` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_highlights.py tests/theme/ -x -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/theme/test_contrast.py` -- parametric contrast check across all themes (HLTHEM-02)
- [ ] `docs/generate-examples.sh` -- example image generation script (HLDOC-03)
- [ ] `docs/examples/` -- directory for generated images (HLDOC-03)

## Sources

### Primary (HIGH confidence)
- Direct code inspection of `src/codepicture/render/highlights.py`, `renderer.py`, `theme/pygments_theme.py`, `theme/loader.py`, `config/schema.py`
- Runtime theme luminance audit: `uv run python3` against all 55 themes (verified luminance values and light/dark classification)
- Existing test infrastructure in `tests/visual/conftest.py` and `tests/visual/test_visual_regression.py`

### Secondary (MEDIUM confidence)
- BT.709 luminance formula is a well-established standard (ITU-R BT.709)
- WCAG 2.0 contrast ratio formula is a W3C recommendation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pure Python, no new dependencies, all integration points verified by code inspection
- Architecture: HIGH - single integration point clearly identified, precedence chain well-defined, backward compatibility verified
- Pitfalls: HIGH - GitHub Light unavailability verified empirically, snapshot stability verified by palette identity

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable -- no external dependency changes expected)
