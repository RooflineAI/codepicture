# Phase 13: Named Styles, Focus Mode & Gutter Indicators - Research

**Researched:** 2026-03-30
**Domain:** Python/Cairo rendering pipeline -- multi-style highlights, opacity dimming, gutter drawing
**Confidence:** HIGH

## Summary

Phase 13 extends the single-style highlight infrastructure from Phase 12 into a multi-style system with four named styles (highlight, add, remove, focus), focus-mode dimming for unfocused lines, and gutter indicators between line numbers and code. The codebase is well-structured for this extension -- the existing `highlights.py` parser needs a `:style` suffix, the renderer's per-line highlight check changes from a `set[int]` to a `dict[int, HighlightStyle]`, and Cairo's existing `set_source_rgba` handles dimming via alpha multiplication without new canvas APIs.

The main architectural challenge is the gutter indicator column, which requires modifying the layout engine to reserve space between line numbers and code (currently `LINE_NUMBER_GAP = 12px` is just empty space). The focus mode dimming is straightforward -- multiply all color alphas by ~0.35 for unfocused lines during the text/line-number drawing loops.

**Primary recommendation:** Work bottom-up: (1) data model and parser, (2) config schema with TOML support, (3) renderer integration for per-style colors and focus dimming, (4) gutter indicators with layout changes, (5) tests.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `--highlight '3-5:add'` replaces `--highlight-lines`. Old flag removed entirely. `--highlight '3-5'` (no style) uses the default `highlight` style, preserving behavioral compatibility.
- **D-03:** Overlapping lines with different styles: last `--highlight` flag wins. `--highlight '3-5:add' --highlight '5:remove'` results in line 5 being `remove`.
- **D-04:** Only 4 built-in style names: `highlight` (default), `add`, `remove`, `focus`. No custom style names. Users customize colors of these 4 via TOML.
- **D-05:** TOML config uses inline list syntax with `[[highlights.entries]]` array-of-tables pattern. Per-style color overrides in `[highlight_styles.<name>]` sections.
- **D-06:** Unfocused lines dimmed via reduced text opacity (~30-40%). Preserves syntax colors as muted versions. Works consistently across PNG/SVG/PDF.
- **D-07:** Dimming applies to everything on unfocused lines: line numbers, text, and gutter indicators.
- **D-08:** Focus style combines freely with other styles. `--highlight '3-5:focus' --highlight '10:add'` results in: lines 3-5 focused at full brightness, line 10 fully visible with add-style, all other lines dimmed.
- **D-09:** Gutter indicator column positioned between line numbers and code text. Reading flow: number -> indicator -> code.
- **D-10:** Add style shows `+`, remove shows `-`, highlight and focus show a thin vertical colored bar (2-3px).
- **D-12:** Vivid, distinct default colors at ~25% opacity for backgrounds: add `#00CC4040`, remove `#FF333340`, focus `#3399FF40`, highlight `#FFE65040`.
- **D-13:** Gutter indicator symbols (+/-/bar) rendered at ~80-100% opacity of the style's base color.
- **D-14:** Visual regression: one snapshot baseline per style (4 images).
- **D-15:** Focus mode dimming: visual regression snapshot PLUS a unit test verifying the opacity value passed to the canvas for unfocused lines.

### Claude's Discretion
- `--highlight-color` flag: keep as global default or remove (D-02)
- Gutter indicator visibility when line numbers disabled (D-11)
- Exact dimming opacity within the ~30-40% range
- Exact gutter bar width within 2-3px
- TOML config field naming details
- How `highlight_lines` / `highlight_color` config fields migrate to new format

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HLSTYL-01 | Named highlight styles via `--highlight '3-5:add'` repeated flag | Parser extension in highlights.py; new HighlightStyle enum; CLI flag replacement |
| HLSTYL-02 | Built-in styles: highlight (default), add (green), remove (red), focus (blue) | Style enum + DEFAULT_STYLE_COLORS dict with D-12 palette |
| HLSTYL-03 | Each built-in style has a distinct default color | Color constants defined per D-12 |
| HLSTYL-04 | User can customize style colors via TOML `[highlight_styles.add]` | Pydantic nested model HighlightStyleConfig; config loader handles TOML sections |
| HLSTYL-05 | No style specified defaults to `highlight` style | Parser returns `highlight` when no `:style` suffix |
| HLFOC-01 | Focus style dims all non-focused lines | Renderer checks if any line has focus style; if so, non-highlighted lines get dimmed alpha |
| HLFOC-02 | Focused lines remain at full brightness | Lines with any highlight style (including focus) render at normal opacity |
| HLFOC-03 | Dimming is visually effective without making unfocused lines unreadable | ~35% opacity multiplier preserves syntax colors as muted versions |
| HLGUT-01 | Gutter indicators beside line numbers (+, -, colored bar) | Layout engine reserves gutter indicator column; renderer draws symbols/bars |
| HLGUT-02 | Gutter indicators use same color as corresponding style | Indicator color derived from style's base color at ~90% opacity |
| HLTEST-02 | Unit tests for style-to-color mapping, custom overrides, defaults | Test HighlightStyle resolution and color override logic |
| HLTEST-04 | Visual regression tests per named style | 4 snapshot baselines using existing pixelmatch infrastructure |
| HLTEST-06 | Integration tests for focus mode dimming | Visual snapshot + unit test verifying opacity value |
| HLTEST-08 | Tests for gutter indicators with named styles | Visual snapshots showing +/- symbols and colored bars |

</phase_requirements>

## Architecture Patterns

### Data Flow: Highlight Resolution

The current flow is:
```
CLI --highlight-lines -> config.highlight_lines (list[str]) -> parse_line_ranges() -> set[int] -> renderer checks membership
```

The new flow will be:
```
CLI --highlight (repeated) -> config.highlights (list[HighlightEntry]) -> parse_highlight_specs() -> dict[int, HighlightStyle] -> renderer uses per-line style
```

### Core Data Types

```python
# In highlights.py or a new types location
from enum import Enum

class HighlightStyle(str, Enum):
    """Built-in highlight style names."""
    HIGHLIGHT = "highlight"
    ADD = "add"
    REMOVE = "remove"
    FOCUS = "focus"

# Default colors per D-12
DEFAULT_STYLE_COLORS: dict[HighlightStyle, Color] = {
    HighlightStyle.HIGHLIGHT: Color(r=255, g=230, b=80, a=64),   # #FFE65040
    HighlightStyle.ADD:       Color(r=0,   g=204, b=64, a=64),   # #00CC4040
    HighlightStyle.REMOVE:    Color(r=255, g=51,  b=51, a=64),   # #FF333340
    HighlightStyle.FOCUS:     Color(r=51,  g=153, b=255, a=64),  # #3399FF40
}

# Gutter indicators per D-10
GUTTER_INDICATORS: dict[HighlightStyle, str | None] = {
    HighlightStyle.HIGHLIGHT: None,  # colored bar (drawn as rect)
    HighlightStyle.ADD:       "+",
    HighlightStyle.REMOVE:    "-",
    HighlightStyle.FOCUS:     None,  # colored bar (drawn as rect)
}
```

### Parser Extension

The existing `_LINE_SPEC_RE` pattern `^\d+(-\d+)?$` must be extended to handle the optional `:style` suffix:

```python
# New regex: "N", "N-M", "N:style", "N-M:style"
_HIGHLIGHT_SPEC_RE = re.compile(r"^(\d+(?:-\d+)?)(?::(\w+))?$")

def parse_highlight_specs(
    specs: list[str],
    total_lines: int,
    line_number_offset: int = 1,
) -> dict[int, HighlightStyle]:
    """Parse highlight specs into a per-line style map.

    Last flag wins for overlapping lines (D-03).
    Returns dict mapping 0-based line index to HighlightStyle.
    """
    result: dict[int, HighlightStyle] = {}
    for spec in specs:
        match = _HIGHLIGHT_SPEC_RE.match(spec.strip())
        # extract line_part and style_name
        # parse line_part using existing range logic
        # resolve style_name (default: "highlight")
        # assign to result dict (last-wins semantics via dict overwrite)
    return result
```

### Config Schema Extension

Pydantic v2 nested models for TOML config:

```python
class HighlightStyleConfig(BaseModel):
    """Per-style color override."""
    color: str | None = None  # #RRGGBB or #RRGGBBAA

class RenderConfig(BaseModel):
    # ... existing fields ...

    # NEW: replaces highlight_lines + highlight_color
    highlights: list[str] | None = None  # ["3-5:add", "10:remove"]
    highlight_styles: dict[str, HighlightStyleConfig] | None = None

    # DEPRECATED but kept for backward compat during transition
    highlight_lines: list[str] | None = None
    highlight_color: str | None = None
```

TOML config example:
```toml
highlights = ["3-5:add", "10:remove"]

[highlight_styles.add]
color = "#00FF0040"

[highlight_styles.remove]
color = "#FF000060"
```

### Renderer Changes

Key changes to `renderer.py`:

1. **Resolve highlights** -- change from `set[int]` + single color to `dict[int, HighlightStyle]` + per-style color lookup
2. **Detect focus mode** -- check if any line has `HighlightStyle.FOCUS`; if so, set `focus_mode = True`
3. **Draw highlight rects** -- iterate highlighted lines, use per-style color
4. **Draw gutter indicators** -- between line number and code, draw `+`/`-` text or a colored bar rect
5. **Apply focus dimming** -- when drawing text/line-numbers for non-highlighted lines in focus mode, multiply color alpha by dimming factor

```python
# Focus dimming approach (in both _render_legacy and _render_wrapped)
FOCUS_DIM_OPACITY = 0.35  # ~35% of original opacity

def _dim_color(color: Color, factor: float) -> Color:
    """Reduce color opacity for focus mode dimming."""
    return Color(r=color.r, g=color.g, b=color.b, a=int(color.a * factor))

# In the text drawing loop:
if focus_mode and line_idx not in style_map:
    effective_color = _dim_color(style.color, FOCUS_DIM_OPACITY)
else:
    effective_color = style.color
```

### Layout Engine Changes for Gutter Indicators

The gutter indicator column needs reserved space between line numbers and code. Currently `LINE_NUMBER_GAP = 12px` separates them. The indicator column fits within or alongside this gap.

```python
# In LayoutEngine
GUTTER_INDICATOR_WIDTH = 12  # px -- space for +/- char or colored bar

# Modify calculate_metrics to add indicator column:
# gutter_x -> [line numbers] -> [indicator column] -> [code]
# code_x = padding + gutter_width + indicator_width + gap
```

The `LayoutMetrics` dataclass needs a new field:
```python
# New field in LayoutMetrics
gutter_indicator_x: float = 0.0  # X position for gutter indicators
gutter_indicator_width: float = 0.0  # Width reserved for indicators
```

### Recommended Project Structure

No new files needed beyond extending existing modules:

```
src/codepicture/
  render/
    highlights.py      # EXTEND: HighlightStyle enum, parse_highlight_specs(), style colors
    renderer.py        # EXTEND: per-style rendering, focus dimming, gutter indicators
  config/
    schema.py          # EXTEND: HighlightStyleConfig model, highlights field
  layout/
    engine.py          # EXTEND: gutter indicator column in metrics
  core/
    types.py           # EXTEND: LayoutMetrics with gutter_indicator_x/width
  cli/
    app.py             # EXTEND: replace --highlight-lines with --highlight
```

### Anti-Patterns to Avoid
- **Separate renderer per style:** Do not create per-style renderer classes. All style logic belongs in the style map lookup, not in polymorphic renderers.
- **Modifying canvas API for dimming:** Do not add `set_opacity()` or `push_group()` to CairoCanvas. Cairo's existing `set_source_rgba` handles opacity per-call. Simply pass a dimmed Color.
- **Global dimming state:** Do not use a canvas-level opacity multiplier. Compute the final color before passing it to draw_text/draw_rectangle.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Color alpha manipulation | Manual bit math | `Color(r=c.r, g=c.g, b=c.b, a=int(c.a * factor))` | Color dataclass already supports construction |
| TOML nested config | Manual dict parsing | Pydantic v2 nested BaseModel with `model_validate()` | Pydantic handles TOML dict -> nested model automatically |
| Enum validation | String comparison chains | `HighlightStyle(str, Enum)` with Pydantic field_validator | Pydantic auto-validates enum members |
| Visual regression | Custom pixel comparison | Existing pixelmatch infrastructure in `tests/visual/conftest.py` | Already proven in Phase 12 |

## Common Pitfalls

### Pitfall 1: Focus Mode + Other Styles Interaction
**What goes wrong:** Implementing focus mode as "only focus lines are visible" rather than "all highlighted lines are visible, only unhighlighted lines are dimmed."
**Why it happens:** D-08 specifies that focus combines freely with other styles. Line 10 with `add` style should be fully visible even when focus mode is active.
**How to avoid:** The dimming check is `if focus_mode and line_idx not in style_map` -- any line with ANY style stays at full opacity. Only unhighlighted lines get dimmed.
**Warning signs:** Add/remove highlighted lines appear dimmed when focus is also used.

### Pitfall 2: Last-Flag-Wins Ordering
**What goes wrong:** Using a set or first-wins logic instead of last-wins for overlapping lines.
**Why it happens:** Python dicts naturally support last-wins via overwrite, but if processing is done per-range-then-per-line, the order matters.
**How to avoid:** Process `--highlight` flags in order. For each flag, resolve all lines in the range, then overwrite the style_map entries. Dict assignment naturally implements last-wins.
**Warning signs:** `--highlight '3-5:add' --highlight '5:remove'` shows line 5 as `add` instead of `remove`.

### Pitfall 3: Gutter Column Layout Shift
**What goes wrong:** Adding the gutter indicator column shifts all code to the right, breaking existing visual regression baselines.
**Why it happens:** The indicator column adds width between line numbers and code.
**How to avoid:** Only reserve gutter indicator space when highlights are active (i.e., when `style_map` is non-empty). When no highlights, layout matches Phase 12 exactly.
**Warning signs:** All existing visual regression tests fail after gutter changes.

### Pitfall 4: Backward Compatibility with highlight_lines
**What goes wrong:** Removing `highlight_lines` from schema breaks existing TOML configs.
**Why it happens:** D-01 says old CLI flag is removed, but existing TOML files may use `highlight_lines`.
**How to avoid:** Accept both `highlight_lines` (legacy) and `highlights` (new) in RenderConfig, with a validator that converts `highlight_lines` entries to `highlights` entries with default style. Emit a deprecation note or silently migrate.
**Warning signs:** Users with existing `highlight_lines` in TOML get validation errors.

### Pitfall 5: SVG/PDF Opacity Consistency
**What goes wrong:** Focus dimming looks different across PNG/SVG/PDF.
**Why it happens:** All three formats use Cairo's `set_source_rgba`, but PDF viewers and SVG renderers may interpret alpha differently at edges.
**How to avoid:** Cairo's RGBA is consistent across all three surface types. The same alpha value produces the same visual. No format-specific logic needed.
**Warning signs:** Dimmed text appears different in SVG vs PNG visual regression tests.

### Pitfall 6: Pydantic extra='forbid' Blocks New Fields
**What goes wrong:** Adding `highlights` or `highlight_styles` to RenderConfig works, but old TOML files with `highlight_lines` would still validate fine. The real risk is that `extra='forbid'` rejects unknown TOML keys, so adding a `[highlight_styles]` section requires the schema to expect it.
**Why it happens:** RenderConfig uses `ConfigDict(extra="forbid")`.
**How to avoid:** Add the new fields to the schema before TOML parsing expects them. Both `highlights` and `highlight_styles` must be declared fields.
**Warning signs:** TOML files with `[highlight_styles.add]` raise "extra fields not permitted" errors.

## Code Examples

### Parsing highlight specs with style suffix

```python
# Source: Extension of existing highlights.py pattern
_HIGHLIGHT_SPEC_RE = re.compile(r"^(\d+(?:-\d+)?)(?::(\w+))?$")

VALID_STYLES = {"highlight", "add", "remove", "focus"}

def parse_highlight_specs(
    specs: list[str],
    total_lines: int,
    line_number_offset: int = 1,
) -> dict[int, HighlightStyle]:
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
        indices = parse_line_ranges(
            [line_part], total_lines, line_number_offset
        )

        # Last-wins: dict overwrite for overlapping lines
        for idx in indices:
            result[idx] = style

    return result
```

### Focus dimming in renderer

```python
# Source: Extension of renderer.py _render_legacy pattern
FOCUS_DIM_OPACITY = 0.35

def _dim_color(color: Color, factor: float) -> Color:
    return Color(r=color.r, g=color.g, b=color.b, a=int(color.a * factor))

# In _render_legacy, after resolving style_map:
focus_mode = any(s == HighlightStyle.FOCUS for s in style_map.values())

# When drawing line numbers:
line_number_color = theme.line_number_fg
if focus_mode and line_idx not in style_map:
    line_number_color = _dim_color(line_number_color, FOCUS_DIM_OPACITY)

# When drawing code tokens:
token_color = style.color
if focus_mode and line_idx not in style_map:
    token_color = _dim_color(token_color, FOCUS_DIM_OPACITY)
```

### Gutter indicator drawing

```python
# Source: New code in renderer.py
GUTTER_BAR_WIDTH = 3  # px, per D-10

def _draw_gutter_indicator(
    canvas: CairoCanvas,
    style: HighlightStyle,
    style_color: Color,
    x: float,
    y: float,
    height: float,
    font_family: str,
    font_size: int,
) -> None:
    """Draw gutter indicator for a highlighted line."""
    # Base color at high opacity for visibility (D-13)
    indicator_color = Color(
        r=style_color.r, g=style_color.g, b=style_color.b,
        a=int(min(255, style_color.a * 255 / 64 * 0.9))  # ~90% of base RGB
    )

    symbol = GUTTER_INDICATORS.get(style)
    if symbol:  # "+" or "-"
        canvas.draw_text(
            x=x, y=y, text=symbol,
            font_family=font_family, font_size=font_size,
            color=indicator_color,
        )
    else:  # colored bar for highlight/focus
        canvas.draw_rectangle(
            x=x, y=y - height * 0.8,  # align with text baseline
            width=GUTTER_BAR_WIDTH, height=height,
            color=indicator_color,
        )
```

### TOML config with nested style overrides

```toml
# Example codepicture.toml
highlights = ["3-5:add", "10:remove", "15-20:focus"]

[highlight_styles.add]
color = "#00FF0050"

[highlight_styles.remove]
color = "#FF000050"
```

```python
# Pydantic schema
class HighlightStyleConfig(BaseModel):
    """Per-style color override from TOML config."""
    model_config = ConfigDict(extra="forbid")
    color: str | None = None

    @field_validator("color", mode="before")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not re.match(r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", v):
            raise ValueError(f"Invalid color '{v}'. Use #RRGGBB or #RRGGBBAA")
        return v
```

## Discretion Recommendations

### D-02: --highlight-color disposition
**Recommendation: Remove `--highlight-color` CLI flag.** The new `--highlight` flag with per-style TOML config provides all color customization. Keeping `--highlight-color` adds confusion about which color applies to which style. The TOML `[highlight_styles.highlight] color = "..."` replaces it cleanly. For the RenderConfig field, keep `highlight_color` as a deprecated field that maps to the default `highlight` style color if present (backward compat).

### D-11: Gutter indicators without line numbers
**Recommendation: Hide gutter indicators when line numbers are disabled.** The gutter column only exists when `show_line_numbers = True`. Without line numbers, there is no gutter area, and adding one just for indicators would require a layout change that contradicts the "no line numbers" intent. This is visually cleaner.

### Exact dimming opacity
**Recommendation: 0.35 (35%).** This is in the middle of the D-06 range (30-40%), provides clear visual distinction while keeping syntax colors recognizable.

### Gutter bar width
**Recommendation: 3px.** At the upper end of D-10's range (2-3px), provides better visibility at standard font sizes (14px).

### TOML field naming
**Recommendation:** `highlights` (list of strings) and `highlight_styles` (dict of style configs). The `highlights` field name is short and clear. Matches the CLI `--highlight` flag name.

### Legacy field migration
**Recommendation:** If `highlight_lines` is present in config but `highlights` is not, auto-convert `highlight_lines` entries to `highlights` entries with no style suffix (defaults to `highlight`). If `highlight_color` is present, use it as the color for the `highlight` style. A `model_validator(mode='before')` on RenderConfig handles this transparently.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0+ |
| Config file | pyproject.toml `[tool.pytest]` section |
| Quick run command | `pytest tests/test_highlights.py -x -q` |
| Full suite command | `pytest --timeout=60` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HLTEST-02 | Style-to-color mapping, custom overrides, defaults | unit | `pytest tests/test_highlights.py -x -q` | Needs extension |
| HLTEST-04 | Visual regression per named style (4 baselines) | visual | `pytest tests/visual/test_visual_regression.py -x -q -k style` | Wave 0 |
| HLTEST-06 | Focus mode dimming integration | integration+unit | `pytest tests/test_highlights.py -x -q -k focus` | Wave 0 |
| HLTEST-08 | Gutter indicators with named styles | visual | `pytest tests/visual/test_visual_regression.py -x -q -k gutter` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_highlights.py tests/test_highlights_integration.py -x -q`
- **Per wave merge:** `pytest --timeout=60`
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
- [ ] `tests/test_highlights.py` -- extend with style parsing tests, style resolution tests, focus dimming opacity tests
- [ ] `tests/visual/test_visual_regression.py` -- add style-specific visual tests (4 baselines)
- [ ] `tests/test_highlights_integration.py` -- extend with focus mode and gutter indicator CLI tests
- [ ] Visual reference images for each style (generated during first `--snapshot-update` run)

## Open Questions

1. **Legacy TOML migration edge cases**
   - What we know: `highlight_lines` and `highlight_color` must be accepted for backward compat
   - What's unclear: Should both old and new format be allowed simultaneously? If both present, which wins?
   - Recommendation: New `highlights` field takes precedence. If only old fields present, auto-migrate. If both present, ignore old fields (new wins).

2. **Gutter indicator alignment with wrapped lines**
   - What we know: Continuation lines do not show line numbers (per Phase 12). Should they show gutter indicators?
   - What's unclear: Whether the indicator repeats on wrapped continuations.
   - Recommendation: Only show gutter indicator on the first display line of a source line (consistent with line number behavior). Wrapped continuation lines show no indicator.

## Sources

### Primary (HIGH confidence)
- `src/codepicture/render/highlights.py` -- existing parser and color resolver
- `src/codepicture/render/renderer.py` -- current highlight rendering in both paths
- `src/codepicture/config/schema.py` -- RenderConfig with Pydantic v2
- `src/codepicture/render/canvas.py` -- CairoCanvas draw_text/draw_rectangle use set_source_rgba
- `src/codepicture/layout/engine.py` -- layout metrics calculation, gutter width, LINE_NUMBER_GAP
- `src/codepicture/core/types.py` -- Color, LayoutMetrics, DisplayLine

### Secondary (MEDIUM confidence)
- Phase 12 CONTEXT.md -- inherited patterns and decisions
- Cairo documentation -- set_source_rgba handles per-call opacity (well-established Cairo behavior)
- Pydantic v2 docs -- nested BaseModel with dict field for TOML sections

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all extends existing code
- Architecture: HIGH -- clear extension points identified in renderer, parser, config
- Pitfalls: HIGH -- based on direct code analysis of existing patterns

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable codebase, no external dependency changes)
