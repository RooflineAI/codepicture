# Phase 12: Core Highlighting Infrastructure - Research

**Researched:** 2026-02-06
**Domain:** Line highlighting rendering with Cairo, CLI/config integration, line range parsing
**Confidence:** HIGH

## Summary

Phase 12 adds single-style line highlighting to codepicture: users specify which lines to highlight via a repeatable `--highlight-lines` CLI flag or TOML config, and those lines render with a semi-transparent yellow background across all output formats (PNG, SVG, PDF). A single `--highlight-color` flag allows customizing the highlight color.

The existing codebase already contains every primitive needed. `CairoCanvas.draw_rectangle()` supports RGBA colors with alpha blending, `LayoutMetrics` provides all the geometry (content positions, line height, canvas width), and `DisplayLine.source_line_idx` maps display lines back to source lines for word-wrap support. No new dependencies are required. The work is purely additive application code: a line range parser, config schema additions, renderer modifications, and CLI flag wiring.

Key architectural decisions from CONTEXT.md that constrain this phase: highlights span the full code area edge-to-edge, fill exactly the line height with no gaps, use sharp rectangles now but must be designed for future rounded/merged blocks, and out-of-bounds line numbers cause an error and exit (strict validation).

**Primary recommendation:** Build in this order: (1) line range parser with strict validation, (2) config schema additions, (3) renderer integration drawing behind text in both legacy and wrapped paths, (4) CLI flag wiring. Each layer is independently testable.

## Standard Stack

No new dependencies needed. The existing stack provides everything required.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pycairo | >=1.25 (latest 1.29.0) | `CairoCanvas.draw_rectangle()` draws highlight rectangles with alpha | Already exists in codebase, supports RGBA via `set_source_rgba` |
| Pydantic | >=2.5 (latest 2.12.5) | Validate new `highlight_lines` and `highlight_color` config fields | Already used for `RenderConfig`, handles list and hex validation |
| Typer | >=0.21.1 | Repeatable `--highlight-lines` option via `list[str]` annotation | Already used for CLI, supports `list[str]` type for repeatable flags |
| Python stdlib `tomllib` | 3.13+ | Parse highlight config from TOML files | Already used for config loading, handles lists of strings natively |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pixelmatch | (existing) | Visual regression tests for highlight rendering | Verify highlight appearance across PNG/SVG/PDF |
| cairosvg + pymupdf | (existing) | Rasterize SVG/PDF for visual comparison | Compare highlight rendering across all formats |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom line range parser | `pyparsing` or `lark` | Overkill -- the grammar is `INT('-'INT)?(','INT('-'INT)?)*`, ~30 lines of code |
| Manual hex validation | `colour` library | Unnecessary -- `Color.from_hex()` already handles `#RRGGBB` and `#RRGGBBAA` |

**Installation:**
```bash
# No new packages needed
```

## Architecture Patterns

### Recommended Project Structure
```
src/codepicture/
  config/schema.py        # ADD: highlight_lines, highlight_color fields to RenderConfig
  cli/app.py              # ADD: --highlight-lines, --highlight-color flags
  render/
    highlights.py          # NEW: line range parser + highlight resolution
    renderer.py            # MODIFY: draw highlight rectangles in both render paths
  core/types.py            # NO CHANGE: existing Color, LayoutMetrics sufficient
  layout/engine.py         # NO CHANGE: highlight geometry derives from existing metrics
```

### Pattern 1: Line Range Parser as Pure Function Module
**What:** A standalone module (`render/highlights.py`) containing pure functions for parsing line specs and resolving highlights. No classes, no state -- just functions that take strings and return sets/dicts.
**When to use:** Always -- this is the primary new logic.
**Example:**
```python
# Source: codebase analysis + CONTEXT.md decisions
def parse_line_ranges(specs: list[str], total_lines: int, line_number_offset: int) -> set[int]:
    """Parse line range specs into a set of 0-based source line indices.

    Args:
        specs: List of range strings, e.g. ["3", "7-12", "15"]
        total_lines: Number of source lines in the code
        line_number_offset: Starting line number (default 1)

    Returns:
        Set of 0-based source line indices

    Raises:
        InputError: If any line number is out of bounds
        InputError: If range syntax is invalid
    """
    result: set[int] = set()
    for spec in specs:
        if "-" in spec:
            parts = spec.split("-", 1)
            start, end = int(parts[0]), int(parts[1])
            # Both are user-facing line numbers (line_number_offset-based)
            for line_num in range(start, end + 1):  # inclusive range
                idx = line_num - line_number_offset
                if idx < 0 or idx >= total_lines:
                    raise InputError(
                        f"Line {line_num} is out of range "
                        f"(valid: {line_number_offset}-{total_lines + line_number_offset - 1})"
                    )
                result.add(idx)
        else:
            line_num = int(spec)
            idx = line_num - line_number_offset
            if idx < 0 or idx >= total_lines:
                raise InputError(
                    f"Line {line_num} is out of range "
                    f"(valid: {line_number_offset}-{total_lines + line_number_offset - 1})"
                )
            result.add(idx)
    return result
```

### Pattern 2: Highlight Drawing Integrated into Existing Render Loops
**What:** Draw highlight rectangles as the FIRST operation inside the per-line loop in both `_render_legacy()` and `_render_wrapped()`. No separate rendering pass.
**When to use:** Always -- this is the rendering integration pattern.
**Example:**
```python
# In _render_legacy:
for line_idx, line_tokens in enumerate(lines):
    # Draw highlight rectangle FIRST (behind text)
    if line_idx in highlighted_lines:
        highlight_y = (
            metrics.content_y + code_y_offset
            + line_idx * metrics.line_height_px
        )
        canvas.draw_rectangle(
            x=metrics.content_x,
            y=highlight_y,
            width=metrics.content_width,
            height=metrics.line_height_px,
            color=highlight_color,
        )
    # Then draw line number (existing code)
    # Then draw tokens (existing code)

# In _render_wrapped:
for display_idx, dline in enumerate(metrics.display_lines):
    # Draw highlight rectangle FIRST (behind text)
    if dline.source_line_idx in highlighted_lines:
        highlight_y = (
            metrics.content_y + code_y_offset
            + display_idx * metrics.line_height_px
        )
        canvas.draw_rectangle(
            x=metrics.content_x,
            y=highlight_y,
            width=metrics.content_width,
            height=metrics.line_height_px,
            color=highlight_color,
        )
    # Then draw line number (existing code)
    # Then draw tokens (existing code)
```

### Pattern 3: Repeatable Typer Option with list[str]
**What:** Use `list[str] | None` type annotation for the `--highlight-lines` flag to allow repeated invocations.
**When to use:** For the CLI flag.
**Example:**
```python
# Source: Typer docs - Multiple CLI Options
@app.command()
def main(
    # ... existing params ...
    highlight_lines: Annotated[
        list[str] | None,
        typer.Option("--highlight-lines", help="Lines to highlight (e.g. 3, 7-12)"),
    ] = None,
    highlight_color: Annotated[
        str | None,
        typer.Option("--highlight-color", help="Highlight color (#RRGGBB or #RRGGBBAA)"),
    ] = None,
):
    # Usage: --highlight-lines 3 --highlight-lines 7-12 --highlight-lines 15
    pass
```

### Pattern 4: Config Fields with Pydantic Validation
**What:** Add `highlight_lines` and `highlight_color` to `RenderConfig` with validators.
**When to use:** For config schema.
**Example:**
```python
class RenderConfig(BaseModel):
    # ... existing fields ...

    # Highlighting
    highlight_lines: list[str] | None = None  # e.g. ["3", "7-12", "15"]
    highlight_color: str | None = None  # e.g. "#FFDD3340"

    @field_validator("highlight_color", mode="before")
    @classmethod
    def validate_highlight_color(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError(f"highlight_color must be a string, got {type(v).__name__}")
        if not re.match(r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", v):
            raise ValueError(
                f"Invalid highlight color '{v}'. Use #RRGGBB or #RRGGBBAA format"
            )
        return v

    @field_validator("highlight_lines", mode="before")
    @classmethod
    def validate_highlight_lines(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("highlight_lines must be a list of strings")
        for spec in v:
            s = str(spec)
            if not re.match(r"^\d+(-\d+)?$", s):
                raise ValueError(
                    f"Invalid line spec '{s}'. Use N or N-M format"
                )
        return [str(s) for s in v]
```

### Anti-Patterns to Avoid
- **Do NOT add highlight data to LayoutMetrics:** Highlights are a visual/color concern, not a geometry concern. LayoutMetrics must remain pure geometry. The renderer computes highlight positions from existing metrics fields.
- **Do NOT create a separate rendering pass for highlights:** Drawing highlights in a separate loop before the line/token loop creates unnecessary complexity. Both loops iterate the same data and compute the same Y positions. Inline the highlight draw as the first operation per line.
- **Do NOT modify the Canvas protocol:** `draw_rectangle(x, y, width, height, color)` is sufficient. No new canvas operations needed.
- **Do NOT resolve line ranges in Pydantic validators:** Validators should check format validity (is this a valid range string?). Resolution to 0-based indices happens at render time when `total_lines` is known.
- **Do NOT store resolved highlights in config:** `RenderConfig` stores the user's intent (`["3", "7-12"]`). Resolution to a `set[int]` of 0-based indices happens at render time. This keeps config serializable and resolution testable in isolation.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Drawing semi-transparent rectangles | Custom alpha blending code | `CairoCanvas.draw_rectangle()` with `Color(a=64)` | Already handles RGBA via `set_source_rgba`, works across PNG/SVG/PDF |
| Hex color parsing with alpha | Custom parser | `Color.from_hex('#RRGGBBAA')` | Already supports `#RGB`, `#RRGGBB`, `#RRGGBBAA` formats |
| Mapping display lines to source lines | Custom index tracking | `DisplayLine.source_line_idx` field | Already exists in `core/types.py`, set by layout engine |
| Config validation | Manual if/else checks | Pydantic `field_validator` | Follows existing pattern in `RenderConfig` |
| Repeatable CLI flag | Custom argument accumulation | Typer `list[str]` annotation | Native Typer feature: `--flag val1 --flag val2` becomes `["val1", "val2"]` |
| TOML list parsing | Custom TOML handling | `tomllib` (stdlib) | `highlight_lines = ["3", "7-12"]` parses to `list[str]` automatically |

**Key insight:** Every primitive needed for line highlighting already exists in the codebase. The work is wiring these primitives together, not building new capabilities.

## Common Pitfalls

### Pitfall 1: Wrong Z-Order -- Drawing Highlights Over Text
**What goes wrong:** Highlight rectangles are drawn AFTER syntax tokens, painting over already-rendered text. Text disappears behind the colored rectangle.
**Why it happens:** The existing rendering pipeline draws background, chrome, then text. A naive addition might insert highlights at the wrong point.
**How to avoid:** Highlight rectangles MUST be drawn BEFORE line numbers and syntax tokens. In both `_render_wrapped()` and `_render_legacy()`, the highlight rectangle is the FIRST operation per line, before line number and token drawing.
**Warning signs:** Text on highlighted lines is invisible or partially obscured.

### Pitfall 2: Word-Wrapped Lines -- Highlighting Only One Display Line
**What goes wrong:** Source line 5 wraps into display lines 5a, 5b, 5c. Only display line 5a gets highlighted. User sees a partial colored band that stops mid-logical-line.
**Why it happens:** The code maps a highlight line number to a single display line index instead of ALL display lines belonging to that source line.
**How to avoid:** Highlight lookups must use `dline.source_line_idx` (which maps each display line back to its source line). Check this field against the highlighted set for EVERY display line.
**Warning signs:** Wrapped highlighted lines show partial highlighting.

### Pitfall 3: Forgetting the Legacy (Non-Wrapped) Rendering Path
**What goes wrong:** Highlights work with `--window-width` (wrapped path) but not without it (legacy path). When `window_width` is not set, `display_lines` is empty, renderer takes the legacy path, and highlights do nothing.
**Why it happens:** The renderer has TWO distinct code paths: `_render_wrapped` (when `display_lines` is populated) and `_render_legacy` (when it is not). A developer may only modify the wrapped path.
**How to avoid:** Add highlight drawing to BOTH `_render_legacy` and `_render_wrapped`. Test with and without `window_width`.
**Warning signs:** Highlights only work when `--width` is specified.

### Pitfall 4: Highlight Rectangle Height Does Not Match Line Height
**What goes wrong:** Highlight rectangle is `char_height` tall but lines are spaced at `line_height_px` (which is `char_height * line_height_multiplier`). With 1.4x line height, there are visible gaps between consecutive highlighted lines.
**Why it happens:** Confusing `char_height` (font metric) with `line_height_px` (baseline-to-baseline distance).
**How to avoid:** Highlight rectangle height MUST be exactly `metrics.line_height_px`. Y-position is the TOP of the line slot: `content_y + code_y_offset + display_idx * line_height_px`.
**Warning signs:** Horizontal stripes of background color between consecutive highlighted lines.

### Pitfall 5: Off-by-One in Line Number Mapping
**What goes wrong:** User specifies `--highlight-lines 5` expecting line 5 in their editor (1-based), but the renderer highlights line 4 or line 6 due to confusion between 0-based internal indices and `line_number_offset`.
**Why it happens:** Source line indices are 0-based in the `lines` list. `line_number_offset` (default 1) offsets displayed line numbers. The conversion `source_idx = user_line_number - line_number_offset` must be applied consistently.
**How to avoid:** Define clearly: user-facing line numbers match what appears in the output (respecting `line_number_offset`). Convert at the boundary (in `parse_line_ranges`). Test with non-default `line_number_offset` values.
**Warning signs:** Highlighted line is one off from what the user specified.

### Pitfall 6: Semi-Transparent Highlights Look Different Across PNG/SVG/PDF
**What goes wrong:** Highlight color with alpha looks correct in PNG but different in SVG or PDF because viewers composite alpha differently.
**Why it happens:** Cairo's PNG surface blends in-memory, but SVG/PDF surfaces emit markup and delegate compositing to the viewer.
**How to avoid:** Test all three output formats explicitly. The default operator (`cairo.Operator.OVER`) handles this correctly for `set_source_rgba`. Do NOT change the operator. Keep alpha in the ~20-30% range where cross-format differences are minimal. Visual regression tests across all 3 formats will catch any discrepancies.
**Warning signs:** Highlight color appears different when comparing PNG vs SVG vs PDF output.

### Pitfall 7: Highlight Rectangles Extend Past Rounded Corners
**What goes wrong:** On the first or last line of code, the highlight rectangle extends into the rounded corner area, creating visible colored corners.
**Why it happens:** The main background is a rounded rectangle, but highlights are sharp rectangles that can poke into corner areas.
**How to avoid:** With the default padding of 20px, the first code line is far enough from the corners that this is not visible. For future-proofing, the highlight width uses `content_x` and `content_width` (inside padding), not `0` and `canvas_width`. If extreme low-padding cases arise, `push_clip` with the background's rounded rectangle path can be added.
**Warning signs:** Colored corners visible at very low padding values.

## Code Examples

### Complete Line Range Parser
```python
# Source: codebase analysis + CONTEXT.md decisions
import re
from codepicture.core.types import Color
from codepicture.errors import InputError

# Default: yellow family, ~25% opacity (per CONTEXT.md)
DEFAULT_HIGHLIGHT_COLOR = Color(r=255, g=230, b=80, a=64)  # #FFE65040

def parse_line_ranges(
    specs: list[str],
    total_lines: int,
    line_number_offset: int = 1,
) -> set[int]:
    """Parse line range specs into 0-based source line indices.

    Accepts: ["3", "7-12", "15"]
    Returns: {2, 6, 7, 8, 9, 10, 11, 14}  (0-based)

    Raises InputError for out-of-bounds or invalid syntax.
    """
    result: set[int] = set()
    max_line_num = total_lines + line_number_offset - 1

    for spec in specs:
        spec = spec.strip()
        if not re.match(r"^\d+(-\d+)?$", spec):
            raise InputError(
                f"Invalid line spec '{spec}'. Use N or N-M format "
                f"(e.g. '3' or '7-12')"
            )

        if "-" in spec:
            parts = spec.split("-", 1)
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


def resolve_highlight_color(
    color_str: str | None,
) -> Color:
    """Resolve highlight color from user string or return default.

    Accepts #RRGGBB (adds ~25% alpha) or #RRGGBBAA.
    """
    if color_str is None:
        return DEFAULT_HIGHLIGHT_COLOR

    color = Color.from_hex(color_str)

    # If user provided 6-char hex, apply default alpha
    if len(color_str.lstrip("#")) == 6:
        color = Color(r=color.r, g=color.g, b=color.b, a=64)  # ~25% opacity

    return color
```

### Renderer Integration (Highlight Rectangle Drawing)
```python
# Source: existing renderer.py pattern + CONTEXT.md decisions
# In Renderer.render():
def render(self, lines, metrics, theme):
    config = self._config

    # Resolve highlights (returns set[int] of 0-based source line indices)
    highlighted_lines: set[int] = set()
    highlight_color = DEFAULT_HIGHLIGHT_COLOR
    if config.highlight_lines:
        highlighted_lines = parse_line_ranges(
            config.highlight_lines,
            total_lines=len(lines),
            line_number_offset=config.line_number_offset,
        )
        highlight_color = resolve_highlight_color(config.highlight_color)

    # ... existing canvas creation, background, chrome ...

    if metrics.display_lines:
        self._render_wrapped(canvas, lines, metrics, theme, code_y_offset,
                            highlighted_lines, highlight_color)
    else:
        self._render_legacy(canvas, lines, metrics, theme, code_y_offset,
                           highlighted_lines, highlight_color)
```

### TOML Config Format (Claude's Discretion Decision)
```toml
# Recommended: flat fields at top level (consistent with other config fields)
highlight_lines = ["3", "7-12", "15"]
highlight_color = "#FFE65040"
```

This is the recommended TOML format because:
- Consistent with how all other config fields work (flat, top-level)
- `highlight_lines` naturally maps to `list[str]` in TOML
- No nested tables needed -- simpler for users
- Pydantic loads it directly into `RenderConfig.highlight_lines`

### Typer Repeatable Flag
```python
# Source: Typer docs - Multiple CLI Options
highlight_lines: Annotated[
    list[str] | None,
    typer.Option(
        "--highlight-lines",
        help="Lines to highlight (e.g. 3 or 7-12). Repeatable.",
    ),
] = None,
highlight_color: Annotated[
    str | None,
    typer.Option(
        "--highlight-color",
        help="Highlight color (#RRGGBB or #RRGGBBAA)",
    ),
] = None,
```

### Visual Regression Test Pattern
```python
# Source: existing visual regression test pattern in tests/visual/
HIGHLIGHT_VARIANTS = [
    ("highlight-single", {"highlight_lines": ["3"]}),
    ("highlight-range", {"highlight_lines": ["2-4"]}),
    ("highlight-mixed", {"highlight_lines": ["1", "3-5", "7"]}),
    ("highlight-color", {"highlight_lines": ["3"], "highlight_color": "#FF000040"}),
    ("highlight-wrap", {"highlight_lines": ["1"], "window_width": 400}),
]

@pytest.mark.parametrize("variant_name,overrides", HIGHLIGHT_VARIANTS)
def test_visual_highlight(variant_name, overrides, ...):
    config = RenderConfig(output_format="png", **overrides)
    # ... render and compare against reference snapshot ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| N/A (new feature) | Semi-transparent rectangle behind text via Cairo `set_source_rgba` | N/A | Standard approach -- same as VS Code, Sublime, etc. |

**Deprecated/outdated:**
- Nothing deprecated. This is a new feature building on stable Cairo primitives.

## Discretion Decisions (Recommendations)

Per CONTEXT.md, these are areas where Claude has discretion:

### Edge Treatment: Use Sharp Rectangles
**Recommendation:** Start with sharp (no corner_radius) rectangles. The design must support future rounded/merged blocks, which means:
- Do NOT hard-code `corner_radius=0` in the draw call. Instead, introduce a constant or parameter (e.g., `HIGHLIGHT_CORNER_RADIUS = 0`) that Phase 13/14 can change.
- The existing `draw_rectangle` method already accepts `corner_radius`. No API changes needed.

### Rendering Layer Order: Draw Behind Text
**Recommendation:** Draw highlight rectangles AFTER the main background but BEFORE line numbers and syntax tokens. This is the standard approach in every code editor (VS Code, Sublime, JetBrains). The semi-transparent color blends with the background, and text is drawn on top at full opacity. This produces the best visual result because:
- Text remains fully readable (no alpha interaction)
- The highlight color is a consistent tint of the background
- Works identically across PNG/SVG/PDF

### TOML Config Format: Flat Top-Level Fields
**Recommendation:** Use flat fields at the top level:
```toml
highlight_lines = ["3", "7-12", "15"]
highlight_color = "#FFE65040"
```
This is most natural for TOML because it matches the existing config pattern (all fields are flat at the top level) and maps directly to `RenderConfig` fields without any nesting or special handling in the loader.

### Default Yellow Shade: `#FFE650` at 25% Opacity
**Recommendation:** Use `Color(r=255, g=230, b=80, a=64)` which is hex `#FFE65040`. This is a warm yellow that:
- Is noticeable but not overwhelming (~25% opacity, alpha=64/255)
- Works on both dark backgrounds (Catppuccin Mocha `#1e1e2e`) and light backgrounds
- Matches the "yellow family" requirement from CONTEXT.md
- Has enough saturation to be clearly visible as a highlight

### Highlight Width: Content Area Edge-to-Edge
**Recommendation:** Use `metrics.content_x` as the X position and `metrics.content_width` as the width. This spans the gutter (line numbers) and code area but stays inside the padding. This matches the CONTEXT.md decision of "full code area edge-to-edge" while not bleeding into the outer padding/rounded corners.

Specifically:
- **X:** `metrics.content_x` (= `padding`)
- **Width:** `metrics.content_width` (= `gutter_width + gap + code_width`)
- **Y:** `metrics.content_y + code_y_offset + line_index * metrics.line_height_px`
- **Height:** `metrics.line_height_px`

## Open Questions

1. **Validation timing for out-of-bounds lines**
   - What we know: CONTEXT.md says "error and exit" for out-of-bounds. The line count is only known after tokenization (step 3 in the pipeline). Validation must happen after tokenization but before rendering.
   - What's unclear: Should validation happen in the orchestrator (between tokenization and rendering) or at the start of `Renderer.render()`?
   - Recommendation: Validate in `Renderer.render()` at the start, before any canvas operations. This is the earliest point where both `total_lines` and config are available. Raise `InputError` which is caught by the CLI error handler and produces a clean error message.

2. **Empty highlight_lines list behavior**
   - What we know: `--highlight-lines` with no value would produce `[]` from Typer, which is different from `None` (unset).
   - What's unclear: Should `highlight_lines = []` be treated as "no highlights" or as an error?
   - Recommendation: Treat `[]` as "no highlights" (same as `None`). This is the principle of least surprise.

3. **Interaction with very low padding**
   - What we know: With `padding=0`, highlight rectangles at `content_x=0` could visually clash with the background's rounded corners.
   - What's unclear: Whether this is a real concern with the Phase 12 implementation.
   - Recommendation: Not a blocker for Phase 12. The default padding is 20px which provides ample inset. If needed later, `push_clip` with the background shape can clip highlights to the rounded rectangle.

## Sources

### Primary (HIGH confidence)
- **Existing codebase** (direct inspection):
  - `src/codepicture/render/renderer.py` -- render pipeline, both legacy and wrapped paths
  - `src/codepicture/render/canvas.py` -- `CairoCanvas.draw_rectangle()` with RGBA support
  - `src/codepicture/config/schema.py` -- `RenderConfig` Pydantic model, field_validator patterns
  - `src/codepicture/core/types.py` -- `Color.from_hex()`, `LayoutMetrics`, `DisplayLine`
  - `src/codepicture/layout/engine.py` -- `calculate_metrics()`, display line generation
  - `src/codepicture/cli/app.py` -- CLI flag pattern, `cli_overrides` dict pattern
  - `src/codepicture/cli/orchestrator.py` -- pipeline flow
  - `src/codepicture/errors.py` -- error hierarchy (InputError for validation)
  - `tests/visual/` -- visual regression test patterns
  - `tests/test_cli.py` -- CLI test patterns with CliRunner
  - `tests/conftest.py` -- shared test fixtures

- **Existing research** (from `.planning/research/`):
  - `ARCHITECTURE-LINE-HIGHLIGHTING.md` -- render pipeline analysis, component boundaries
  - `PITFALLS-LINE-HIGHLIGHTING.md` -- z-order, word wrap, width, alpha issues
  - `STACK.md` -- no new dependencies needed confirmation

### Secondary (MEDIUM confidence)
- [Pycairo Context documentation](https://pycairo.readthedocs.io/en/latest/reference/context.html) -- `set_source_rgba`, default `OVER` operator
- [Typer Multiple CLI Options](https://typer.tiangolo.com/tutorial/multiple-values/multiple-options/) -- `list[str]` repeatable flag pattern
- [Cairo compositing operators](https://www.cairographics.org/operators/) -- alpha blending behavior

### Tertiary (LOW confidence)
- [ZetCode PyCairo Transparency](https://zetcode.com/gfx/pycairo/transparency/) -- general alpha patterns (tutorial, not authoritative)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- verified by direct codebase inspection, no new dependencies
- Architecture: HIGH -- verified by reading all relevant source files, patterns confirmed by existing research
- Pitfalls: HIGH -- catalogued from codebase analysis + existing pitfall research, verified against CONTEXT.md decisions
- Code examples: HIGH -- derived from existing codebase patterns and verified library documentation

**Research date:** 2026-02-06
**Valid until:** 2026-03-06 (stable -- no external dependency changes expected)
