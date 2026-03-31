# Phase 13: Named Styles, Focus Mode & Gutter Indicators - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can apply distinct highlight styles (add/remove/focus) to different line groups in a single render, with focus mode dimming unfocused lines and gutter indicators beside line numbers. Theme-aware color derivation and documentation are separate (Phase 14).

</domain>

<decisions>
## Implementation Decisions

### CLI flag design
- **D-01:** `--highlight '3-5:add'` replaces `--highlight-lines`. Old flag removed entirely. `--highlight '3-5'` (no style) uses the default `highlight` style, preserving behavioral compatibility.
- **D-02:** `--highlight-color` disposition is Claude's discretion — pick whichever approach is cleanest for the CLI surface area.
- **D-03:** Overlapping lines with different styles: last `--highlight` flag wins. `--highlight '3-5:add' --highlight '5:remove'` results in line 5 being `remove`.
- **D-04:** Only 4 built-in style names: `highlight` (default), `add`, `remove`, `focus`. No custom style names. Users customize colors of these 4 via TOML.
- **D-05:** TOML config uses inline list syntax with `[[highlights.entries]]` array-of-tables pattern. Per-style color overrides in `[highlight_styles.<name>]` sections.

### Focus mode dimming
- **D-06:** Unfocused lines dimmed via reduced text opacity (~30-40%). Preserves syntax colors as muted versions. Works consistently across PNG/SVG/PDF.
- **D-07:** Dimming applies to everything on unfocused lines: line numbers, text, and gutter indicators.
- **D-08:** Focus style combines freely with other styles. `--highlight '3-5:focus' --highlight '10:add'` results in: lines 3-5 focused at full brightness, line 10 fully visible with add-style, all other lines dimmed.

### Gutter indicators
- **D-09:** Gutter indicator column positioned between line numbers and code text. Reading flow: number -> indicator -> code.
- **D-10:** Add style shows `+`, remove shows `-`, highlight and focus show a thin vertical colored bar (2-3px).
- **D-11:** Gutter indicator visibility when line numbers are disabled: Claude's discretion — pick based on implementation and visual coherence.

### Style color palette
- **D-12:** Vivid, distinct default colors at ~25% opacity for backgrounds:
  - `add`: `#00CC4040` (bright green)
  - `remove`: `#FF333340` (bright red)
  - `focus`: `#3399FF40` (bright blue)
  - `highlight`: `#FFE65040` (warm yellow, carried from Phase 12)
- **D-13:** Gutter indicator symbols (+/-/bar) rendered at ~80-100% opacity of the style's base color. Small elements need clear visibility.

### Testing strategy
- **D-14:** Visual regression: one snapshot baseline per style (4 images: add, remove, focus, highlight), each showing a small code snippet. Same pixelmatch approach as Phase 12.
- **D-15:** Focus mode dimming: visual regression snapshot PLUS a unit test verifying the opacity value passed to the canvas for unfocused lines.

### Claude's Discretion
- `--highlight-color` flag: keep as global default or remove (D-02)
- Gutter indicator visibility when line numbers disabled (D-11)
- Exact dimming opacity within the ~30-40% range
- Exact gutter bar width within 2-3px
- TOML config field naming details
- How `highlight_lines` / `highlight_color` config fields migrate to new format

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — HLSTYL-01 through HLSTYL-05 (named styles), HLFOC-01 through HLFOC-03 (focus mode), HLGUT-01/02 (gutter indicators), HLTEST-02/04/06/08 (testing requirements)

### Prior phase context
- `.planning/phases/12-core-highlighting-infrastructure/12-CONTEXT.md` — Phase 12 decisions on highlight appearance, line range syntax, word-wrap behavior, default color/opacity. Establishes patterns this phase extends.

### Existing implementation
- `src/codepicture/render/highlights.py` — Current line range parser and color resolver. Must be extended for named styles.
- `src/codepicture/render/renderer.py` — Current highlight rendering in `_render_legacy` and `_render_wrapped`. Integration point for per-style colors, gutter drawing, and focus dimming.
- `src/codepicture/config/schema.py` — RenderConfig with `highlight_lines` and `highlight_color` fields. Must be migrated to new `--highlight` format.
- `src/codepicture/cli/app.py` — CLI flag definitions. `--highlight-lines` replaced by `--highlight`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `parse_line_ranges()` in `highlights.py`: Parses `N` and `N-M` specs into 0-based indices. Must be extended to parse `N-M:style` syntax.
- `resolve_highlight_color()` in `highlights.py`: Resolves hex color with alpha defaults. Can be extended per-style.
- `DEFAULT_HIGHLIGHT_COLOR` / `HIGHLIGHT_CORNER_RADIUS` constants: Existing defaults to build style palette around.
- `CairoCanvas.draw_rectangle()`: Shared highlight rectangle drawing across all formats. Reusable for styled highlights.

### Established Patterns
- Highlight rectangles drawn behind text in both `_render_legacy` and `_render_wrapped` render paths.
- Color represented as `Color(r, g, b, a)` namedtuple from `core/types.py`.
- Config validation via Pydantic `field_validator` with regex patterns.
- CLI flags as `Annotated` types with Typer `Option`.

### Integration Points
- `Renderer.render()` resolves highlights before entering render path — new style resolution logic goes here.
- Both `_render_legacy` and `_render_wrapped` iterate lines and check `if line_idx in highlighted_lines` — must change to per-line style lookup.
- Line number rendering in both paths — gutter indicators drawn adjacent to line numbers.
- Focus dimming affects text rendering opacity — must modify the token drawing loop.

</code_context>

<specifics>
## Specific Ideas

No specific references — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 13-named-styles-focus-mode-gutter-indicators*
*Context gathered: 2026-03-30*
