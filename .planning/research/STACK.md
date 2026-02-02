# Technology Stack: Line Highlighting Feature

**Project:** codepicture
**Milestone:** v2.0 -- Line highlighting with multiple styles (add/remove/focus)
**Researched:** 2026-02-02
**Overall confidence:** HIGH

## Executive Finding

**No new dependencies are needed.** Line highlighting is a pure rendering feature -- colored background rectangles drawn behind specific lines of code. The existing Cairo/Pango stack already provides every required primitive. The work is entirely in new application code (config modeling, rendering logic, line range parsing), not in adding libraries.

## Existing Stack (Relevant to Line Highlighting)

| Technology | Current Pin | Role in Line Highlighting | Confidence |
|------------|-------------|---------------------------|------------|
| pycairo | >=1.25 (latest: 1.29.0) | `CairoCanvas.draw_rectangle()` draws highlight background rectangles. Already exists with alpha support. | HIGH |
| Pydantic | >=2.5 (latest: 2.12.5) | Model new config fields: highlight style definitions, line-to-style mappings. `RenderConfig` extends naturally with nested models. | HIGH |
| Typer | >=0.21.1 | New CLI options for specifying highlighted lines (e.g., `--highlight-add 3,5,7-9`). | HIGH |
| Pygments | >=2.19 | No changes needed. Syntax highlighting is orthogonal to line background highlighting. | HIGH |
| TOML (stdlib `tomllib`) | Python 3.13 stdlib | Highlight styles definable in TOML config files. No new parser needed. | HIGH |

## What NOT to Add (and Why)

| Do Not Add | Why Not | What Exists Instead |
|------------|---------|---------------------|
| Color manipulation library (`colour`, `colormath`) | Highlight colors are user-specified RGBA hex values. `Color.from_hex()` already handles `#RRGGBB` and `#RRGGBBAA`. Alpha for semi-transparent overlays (e.g., `#00FF0033`) is already supported by both `Color` and `CairoCanvas.draw_rectangle()`. | `Color.from_hex()` in `core/types.py` |
| Diff parsing library (`unidiff`, stdlib `difflib`) | Highlight styles (add/remove/focus) are user-specified line ranges, not computed from diffs. The user says "lines 3-5 are additions" -- the tool does not parse unified diff format. Diff-based highlighting would be a separate feature built on top of this line-range primitive. | Simple line range parser (~30 lines) |
| New rendering library | Cairo's `rectangle()` + `set_source_rgba()` + `fill()` is the exact primitive needed. Semi-transparent rectangle behind a line of code is a single call to an existing method. | `CairoCanvas.draw_rectangle()` in `render/canvas.py` |
| Animation/transition library | codepicture produces static images (PNG/SVG/PDF). Highlights are static colored rectangles. | N/A |

## Integration Points with Existing Stack

### 1. Config Schema (`config/schema.py`)

The `RenderConfig` Pydantic model needs new fields. Two design options evaluated:

**Option A (Recommended): Structured highlight styles as nested Pydantic models**

```python
class HighlightStyle(BaseModel):
    """A named highlight style with background color."""
    color: str  # hex color with alpha, e.g. "#00FF0033"

class RenderConfig(BaseModel):
    # ... existing fields ...
    highlight_lines: dict[str, list[int | str]] | None = None
    # e.g. {"add": [3, 5, "7-9"], "remove": [12], "focus": [1]}
    highlight_styles: dict[str, HighlightStyle] | None = None
    # Custom style colors; sensible defaults for add/remove/focus
```

Maps cleanly to TOML config:

```toml
[highlight_styles.add]
color = "#00FF0033"

[highlight_styles.remove]
color = "#FF000033"

[highlight_lines]
add = [3, 5, "7-9"]
remove = [12]
```

**Option B (Rejected): Flat CLI-oriented fields**

```python
highlight_add: list[str] | None = None      # --highlight-add 3,5,7-9
highlight_remove: list[str] | None = None   # --highlight-remove 12
highlight_focus: list[str] | None = None     # --highlight-focus 1
```

**Why Option A:** More extensible. Users can define arbitrary custom styles in TOML (not just the three built-in ones). Pydantic v2 handles `dict[str, BaseModel]` validation natively.

**Why not Option B:** Hard-codes three styles. Adding a new style means adding a new CLI flag and a new config field. Does not scale.

### 2. Core Types (`core/types.py`)

A small addition for highlight data flowing through the rendering pipeline:

```python
@dataclass(frozen=True, slots=True)
class LineHighlight:
    """A highlight applied to a specific source line."""
    line_index: int      # 0-based source line index
    color: Color         # Background color (typically semi-transparent)
    style_name: str      # e.g. "add", "remove", "focus"
```

This is the intermediate representation between config parsing and rendering. The renderer receives a `list[LineHighlight]` alongside the existing `lines`, `metrics`, and `theme` parameters.

### 3. Rendering Pipeline (`render/renderer.py`)

Line highlight rectangles must be drawn **after** the full background but **before** code text, so text remains readable on top of the colored rectangle. The insertion point in the existing flow is unambiguous:

```
1. draw_rectangle (full background with rounded corners)  -- existing
2. draw_title_bar (window chrome)                         -- existing
3. >>> DRAW LINE HIGHLIGHT RECTANGLES <<<                 -- NEW STEP
4. draw line numbers                                      -- existing
5. draw code tokens                                       -- existing
```

Each highlight rectangle:
- **X position:** `0` (full canvas width) or `content_x` (content area only) -- design choice
- **Y position:** `content_y + code_y_offset + line_idx * line_height_px` -- same formula used by line numbers and code tokens
- **Width:** `canvas_width` (full bleed) or `content_width` (within padding)
- **Height:** `line_height_px` (from `LayoutMetrics`)
- **Color:** From `LineHighlight.color` (semi-transparent RGBA)

The existing `CairoCanvas.draw_rectangle()` method already accepts `Color` with alpha channel. No canvas API changes needed.

**Word-wrap interaction:** For wrapped code, highlights should cover ALL display lines belonging to a highlighted source line. The `DisplayLine.source_line_idx` field already maps display lines back to source lines, making this lookup trivial:

```python
for dline_idx, dline in enumerate(metrics.display_lines):
    if dline.source_line_idx in highlighted_source_lines:
        # draw rectangle at this display line position
```

### 4. Layout Engine (`layout/engine.py`)

**No changes needed.** Highlight rectangles use the same `content_x`, `content_y`, `line_height_px`, and `canvas_width` metrics already computed by `calculate_metrics()`. Highlighting is a rendering concern, not a layout concern -- it does not change the size or position of any existing element.

### 5. CLI (`cli/app.py`)

Typer options for specifying highlighted lines per style:

```
codepicture render code.py --highlight-add 3,5,7-9 --highlight-remove 12 --highlight-focus 1
```

Line range parsing (`"3,5,7-9"` to `[3, 5, 7, 8, 9]`) is trivial string parsing -- no library needed. Approximately 20-30 lines of code including error handling.

### 6. Default Highlight Colors

Sensible defaults with low alpha (20% opacity) that work as overlays on both light and dark theme backgrounds:

| Style | Default Color | Hex | Visual |
|-------|---------------|-----|--------|
| add | Green, 20% alpha | `#00FF0033` | Light green overlay |
| remove | Red, 20% alpha | `#FF000033` | Light red overlay |
| focus | Yellow, 20% alpha | `#FFFF0033` | Light yellow overlay |

These defaults are overridable in TOML config. They are NOT theme-dependent -- highlights overlay on top of whatever theme background is active.

## Version Compatibility

No version bumps required. No new dependencies.

| Dependency | Current Pin | Latest Verified | Needed API | Status |
|------------|-------------|-----------------|------------|--------|
| pycairo | >=1.25 | 1.29.0 (Nov 2025) | `draw_rectangle()` with alpha Color | Already exists |
| pydantic | >=2.5 | 2.12.5 (Jan 2026) | Nested `BaseModel`, `dict[str, Model]` | Supported since v2.0 |
| typer | >=0.21.1 | 0.21.1+ | `list[str]` option type | Already supported |
| pygments | >=2.19 | 2.19+ | No changes | N/A |
| pillow | >=10.0 | 10.0+ | No changes (shadow only) | N/A |

## Files to Create or Modify

| Action | File | What Changes |
|--------|------|--------------|
| Modify | `config/schema.py` | Add `highlight_lines`, `highlight_styles`, `HighlightStyle` model |
| Modify | `core/types.py` | Add `LineHighlight` dataclass |
| Modify | `render/renderer.py` | Add highlight rectangle drawing step between background and code |
| Modify | `cli/app.py` | Add `--highlight-add`, `--highlight-remove`, `--highlight-focus` options |
| Create | `highlight/line_ranges.py` (or similar) | Line range parser: `"3,5,7-9"` to `[3, 5, 7, 8, 9]` |
| Modify | `config/loader.py` | Wire highlight config from TOML into `RenderConfig` (may work automatically via Pydantic) |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Alpha blending looks wrong on some themes | Low | Low | Test with 3+ themes (dark, light, colorful). Adjust default alpha if needed. |
| Highlights obscure text readability | Low | Medium | Use low alpha (20%). Document that users should keep alpha below 40%. |
| Word-wrap + highlighting edge cases | Medium | Low | Test wrapped lines with highlights. `DisplayLine.source_line_idx` mapping handles this. |
| Overlapping highlight styles on same line | Low | Low | Last-specified style wins (simple), or blend colors (complex). Start with last-wins. |

## Summary

| Question | Answer |
|----------|--------|
| New runtime dependencies? | **None** |
| New dev dependencies? | **None** |
| Dependency upgrades? | **None required** |
| New files? | Line range parser module (~1 file) |
| Modified files? | `config/schema.py`, `core/types.py`, `render/renderer.py`, `cli/app.py` |
| Cairo API used? | `draw_rectangle()` with alpha `Color` -- already exists in `CairoCanvas` |
| Pydantic API used? | Nested `BaseModel`, `dict[str, Model]` validation -- supported since v2.0 |
| Risk level? | **Low** -- pure additive feature using existing primitives |

## Sources

**Verified via PyPI (HIGH confidence):**
- [pycairo 1.29.0 on PyPI](https://pypi.org/project/pycairo/) -- latest release Nov 2025
- [Pydantic 2.12.5 on PyPI](https://pypi.org/project/pydantic/) -- latest release Jan 2026

**Verified via codebase inspection (HIGH confidence):**
- `CairoCanvas.draw_rectangle()` with alpha `Color` support: `src/codepicture/render/canvas.py` lines 162-192
- `Color.from_hex()` with `#RRGGBBAA` support: `src/codepicture/core/types.py` lines 35-98
- `RenderConfig` Pydantic model: `src/codepicture/config/schema.py`
- `LayoutMetrics` with `line_height_px`, `content_x`, `content_y`: `src/codepicture/core/types.py` lines 154-188
- `DisplayLine.source_line_idx` for word-wrap mapping: `src/codepicture/core/types.py` lines 141-152
- Rendering pipeline order: `src/codepicture/render/renderer.py` lines 47-153

---
*Stack research for: codepicture v2.0 line highlighting feature*
*Researched: 2026-02-02*
*Overall confidence: HIGH -- No new dependencies needed; all required primitives verified in existing codebase*
