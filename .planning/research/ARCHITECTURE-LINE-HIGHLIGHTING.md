# Architecture: Line Highlighting Integration

**Domain:** Line highlighting for code-to-image renderer
**Researched:** 2026-02-02
**Confidence:** HIGH (based on direct source code analysis, no external dependencies needed)

## Current Rendering Pipeline

The existing render order in `Renderer.render()` (`src/codepicture/render/renderer.py`) is:

```
1. Create CairoCanvas
2. Draw background rectangle (full canvas, rounded corners)
3. Draw window chrome (title bar + traffic lights) if enabled
4. Draw code content via _render_wrapped() or _render_legacy():
   a. Draw line numbers
   b. Draw syntax tokens
5. Apply shadow (PNG only, post-process)
6. Save to bytes
```

Line highlights are colored rectangles behind specific lines of code. They must be drawn **after the main background but before text** so that text remains readable on top of the highlight color.

## Recommended Architecture

### Render Order Change

Insert line highlight drawing into the existing render methods. The revised order within `_render_wrapped()` and `_render_legacy()` becomes:

```
For each line:
  1. Draw line highlight rectangle (if line is highlighted)  <-- NEW
  2. Draw line number (existing)
  3. Draw syntax tokens (existing)
```

Rationale for per-line ordering (highlight, then number, then tokens) rather than a separate full pass:

- Both render methods already iterate over lines/display_lines. Adding the highlight draw as the first operation in the loop body keeps the code localized.
- Highlight rectangles span the full content width (gutter + code area), so they naturally cover the area where line numbers and tokens will be drawn on top.
- A separate pass would require iterating the same data structure twice and computing the same Y positions twice.

### Highlight Rectangle Geometry

Each highlight rectangle should span:

- **X:** `0` (left edge of canvas) -- full-bleed gives the "editor-style" look where the highlight extends behind the gutter. This matches VS Code and most editors.
- **Y:** `content_y + code_y_offset + display_idx * line_height_px` (top of the display line)
- **Width:** `canvas_width` (full width)
- **Height:** `line_height_px` (one display line tall)

For word-wrapped lines: ALL display lines belonging to the same highlighted source line should be highlighted. The existing `display_lines` structure stores `source_line_idx`, so any display line whose source line is in the highlight set gets a highlight rectangle.

### Component Boundaries

```
CLI (app.py)              -- Parse --highlight-lines flag
    |
Config (schema.py)        -- Add highlight_lines and highlight_colors fields
    |
Orchestrator              -- Pass config through (no changes needed)
    |
Layout (engine.py)        -- No changes needed
    |
Renderer (renderer.py)    -- Call resolve_highlights(), draw rectangles
    |
highlights.py (NEW)       -- Resolution logic: style names + ranges -> dict[int, Color]
    |
Canvas (canvas.py)        -- No changes needed (draw_rectangle already exists)
```

### Data Flow

```
CLI input:
  --highlight-lines "add:1-3,5;remove:10-12;focus:20"

    |  (string parsing in CLI layer)
    v

RenderConfig.highlight_lines = {
    "add": ["1-3", "5"],
    "remove": ["10-12"],
    "focus": ["20"]
}

    |  (resolution in render/highlights.py)
    v

resolved: dict[int, Color] = {
    1: Color(r=72, g=199, b=116, a=60),   # add (green, semi-transparent)
    2: Color(r=72, g=199, b=116, a=60),
    3: Color(r=72, g=199, b=116, a=60),
    5: Color(r=72, g=199, b=116, a=60),
    10: Color(r=248, g=81, b=73, a=60),    # remove (red, semi-transparent)
    11: Color(r=248, g=81, b=73, a=60),
    12: Color(r=248, g=81, b=73, a=60),
    20: Color(r=255, g=213, b=79, a=60),   # focus (yellow, semi-transparent)
}

    |  (consumed by Renderer)
    v

Renderer._render_wrapped / _render_legacy:
  For each display line:
    source_line_num = source_line_idx + line_number_offset
    if source_line_num in resolved_highlights:
        canvas.draw_rectangle(x=0, y=line_top, w=canvas_width, h=line_height, color=...)
    # then draw line number, then tokens (existing code)
```

### Where Resolution Happens

The style-name-to-color and range-to-lines resolution should live in a new file `src/codepicture/render/highlights.py`. The Renderer calls it at the start of `render()` to produce a `dict[int, Color]`. This keeps highlight logic self-contained and testable without touching layout or config internals.

```python
# src/codepicture/render/highlights.py

DEFAULT_HIGHLIGHT_STYLES: dict[str, Color] = {
    "add": Color(r=72, g=199, b=116, a=60),
    "remove": Color(r=248, g=81, b=73, a=60),
    "focus": Color(r=255, g=213, b=79, a=50),
    "highlight": Color(r=130, g=170, b=255, a=50),
}

def parse_line_spec(spec: str) -> list[int]:
    """Expand '5-10' into [5, 6, 7, 8, 9, 10], or '5' into [5]."""
    ...

def resolve_highlights(
    highlight_lines: dict[str, list[str]] | None,
    highlight_colors: dict[str, str] | None = None,
) -> dict[int, Color]:
    """Resolve highlight config into line_number -> Color mapping.

    Line numbers are 1-based, matching what the user sees in output.
    """
    ...
```

## Modified Components

### 1. `config/schema.py` -- RenderConfig (MODIFY)

Add two optional fields:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `highlight_lines` | `dict[str, list[str]] \| None` | `None` | Style-name to line specs |
| `highlight_colors` | `dict[str, str] \| None` | `None` | Custom style-name to hex color |

Validation: reject malformed range strings, negative line numbers. Accept both `"5"` and `"5-10"` formats.

Example TOML config:
```toml
[highlight_lines]
add = ["1-3", "5"]
remove = ["10-12"]

[highlight_colors]
add = "#48c77440"
remove = "#f8514940"
```

### 2. `cli/app.py` -- CLI flag (MODIFY)

Add `--highlight-lines` option (string, parsed into dict format):

```
--highlight-lines "add:1-3,5;remove:10-12;focus:20"
```

Format: `style:spec[,spec...][;style:spec...]`

Shorthand for un-styled highlights:
```
--highlight-lines "1-3,5,10"   # Uses default "highlight" style
```

Parsing: if the value contains `:`, treat as styled. Otherwise, treat all specs as the default "highlight" style.

### 3. `render/highlights.py` (NEW)

Contains:
- `DEFAULT_HIGHLIGHT_STYLES` dict -- default Color for each named style
- `parse_line_spec(spec: str) -> list[int]` -- expand ranges
- `resolve_highlights(highlight_lines, highlight_colors) -> dict[int, Color]` -- produce resolved mapping

### 4. `render/renderer.py` -- Renderer (MODIFY)

Changes to `render()`:
1. Call `resolve_highlights(config.highlight_lines, config.highlight_colors)` once
2. Pass resolved map to `_render_wrapped()` and `_render_legacy()`

Changes to `_render_legacy()`:
1. Before the line number loop, add highlight rectangle draw per line
2. ~8 lines of new code

Changes to `_render_wrapped()`:
1. Before line number draw per display line, add highlight rectangle draw
2. ~8 lines of new code

## Components NOT Modified

| Component | Why Unchanged |
|-----------|---------------|
| `layout/engine.py` | Highlight geometry derives from existing LayoutMetrics (content_y, line_height_px, canvas_width). No layout pre-computation needed. |
| `render/canvas.py` | `draw_rectangle()` already exists with Color alpha support. |
| `core/types.py` | Existing `Color` dataclass already supports alpha. No new types needed -- the resolved data is `dict[int, Color]`. |
| `core/protocols.py` | No new protocols. Highlights are a rendering concern, not an interface boundary. |
| `render/chrome.py` | Window chrome is independent of line highlights. |
| `render/shadow.py` | Shadow is applied post-render, unaffected. |
| `cli/orchestrator.py` | Config flows through unchanged. |

## Suggested Build Order

Build in this sequence for working, testable increments at each step:

### Step 1: Config fields (foundation)

- Add `highlight_lines` and `highlight_colors` to `RenderConfig`
- Add Pydantic validation for range syntax and hex colors
- Unit tests for config validation

**Why first:** Everything downstream depends on config fields existing.

### Step 2: Resolution logic (core logic)

- Create `src/codepicture/render/highlights.py`
- Implement `parse_line_spec()` and `resolve_highlights()`
- Unit tests for range parsing, style-to-color mapping, custom color overrides, edge cases

**Why second:** This is the most logic-heavy piece. Thorough testing before wiring into renderer.

### Step 3: Renderer integration (visual output)

- Modify `Renderer.render()` to call `resolve_highlights()`
- Add highlight rectangle drawing to `_render_legacy()` and `_render_wrapped()`
- Integration tests and visual regression tests

**Why third:** Depends on steps 1 and 2. The actual draw call is trivial -- `canvas.draw_rectangle()`.

### Step 4: CLI integration (user interface)

- Add `--highlight-lines` flag to `cli/app.py`
- Parse string format into dict, wire into `cli_overrides`
- CLI integration tests

**Why last:** Thinnest layer. Just parses a string into the overrides dict.

## Edge Cases and Design Decisions

### Word Wrap Interaction

When a highlighted source line wraps into multiple display lines, ALL display lines for that source line get highlighted. The `DisplayLine.source_line_idx` field already enables this -- check `source_line_idx + line_number_offset` against the highlight map.

### Overlapping Highlights

If two styles specify the same line (e.g., `add:5;focus:5`), last-specified style wins. Document this. The dict naturally handles it since later entries overwrite earlier ones during resolution.

### Line Number Offset

Highlight line numbers are user-facing and match what appears in the output. If `--line-offset 10` is set, then `--highlight-lines "add:10"` highlights the first line of code (displayed as line 10). Resolution: `internal_idx = user_line - line_number_offset`.

### Out-of-Range Lines

Lines that don't exist in the code are silently ignored. No error, no warning. This supports reusing highlight specs across files of different lengths.

### Alpha/Transparency

Default highlight colors use low alpha (~60/255, roughly 24% opacity). This ensures syntax highlighting and line numbers remain readable through the highlight. Cairo and `draw_rectangle` already handle RGBA.

### Full-Bleed vs Content-Width

**Decision:** Full-bleed (`x=0` to `canvas_width`). Matches VS Code and most editors. Simpler to implement -- no need to compute separate gutter/code rectangles.

## Anti-Patterns to Avoid

### Do NOT add highlights to LayoutMetrics

Highlights are a visual/color concern, not a geometry concern. LayoutMetrics should remain pure geometry. The renderer computes highlight rectangle positions from existing metrics fields.

### Do NOT create a separate rendering pass

Drawing highlights in a separate loop before the line number/token loop creates unnecessary complexity. Both loops iterate the same data and compute the same Y positions. Inline the highlight draw as the first operation per line.

### Do NOT modify the Canvas protocol

The existing `draw_rectangle(x, y, width, height, color)` is sufficient. No new canvas operations needed.

### Do NOT parse highlight specs in Pydantic validators

Validators should check format validity (is this a valid range string?). They should NOT resolve ranges into line lists or map style names to colors. Keep resolution in `render/highlights.py` where `Color` objects live.

### Do NOT store resolved highlights in config

`RenderConfig` stores the user's intent (`{"add": ["1-3"]}`). Resolution to `{1: Color(...), 2: Color(...), 3: Color(...)}` happens at render time. This keeps config serializable and the resolution logic testable in isolation.

## Sources

All findings based on direct source code analysis:

- `src/codepicture/render/renderer.py` -- render pipeline and draw order (lines 47-317)
- `src/codepicture/render/canvas.py` -- `CairoCanvas.draw_rectangle` with Color alpha (lines 162-192)
- `src/codepicture/config/schema.py` -- `RenderConfig` Pydantic model (lines 15-111)
- `src/codepicture/core/types.py` -- `Color`, `LayoutMetrics`, `DisplayLine` (lines 36-205)
- `src/codepicture/layout/engine.py` -- `LayoutEngine.calculate_metrics` (lines 42-176)
- `src/codepicture/cli/app.py` -- CLI flag pattern and `cli_overrides` (lines 88-281)
- `src/codepicture/cli/orchestrator.py` -- pipeline orchestration (lines 26-83)

---
*Architecture research for: Line highlighting integration*
*Researched: 2026-02-02*
