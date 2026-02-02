# Project Research Summary

**Project:** codepicture v2.0 Line Highlighting
**Domain:** Code-to-image rendering with line highlighting
**Researched:** 2026-02-02
**Confidence:** HIGH

## Executive Summary

Line highlighting for codepicture is a pure rendering feature that requires no new dependencies. The existing Cairo/Pango/Pydantic stack provides all required primitives for drawing semi-transparent colored rectangles behind specific lines of code. This milestone positions codepicture as the first CLI code-to-image tool to support multiple named highlight styles (add/remove/focus) in a single render, a clear differentiator in a market where competitors like Silicon and Carbon support only single-style highlighting.

The recommended implementation leverages existing infrastructure: `CairoCanvas.draw_rectangle()` already supports alpha transparency, `Color.from_hex()` handles RGBA values, and the layout engine provides all needed geometry through `LayoutMetrics`. The core challenge is not technical stack integration but careful design of the rendering pipeline insertion point and handling of word-wrapped lines. Research across 7+ competing tools establishes clear user expectations: comma-separated line range syntax, configurable highlight colors, and visual overlays that work across PNG/SVG/PDF output formats.

Critical risks center on visual correctness rather than functional implementation: wrong z-order (highlights over text), incomplete wrapping support (partial line highlighting), and theme color clashing. All three are addressable through clear architectural boundaries and test-driven development. The research identifies a clean 3-phase delivery path: core highlighting, named styles with focus mode, and theme-aware polish.

## Key Findings

### Recommended Stack

**No new dependencies required.** Line highlighting uses existing primitives from the current stack. The feature is 100% additive application code built on verified existing APIs.

**Core technologies:**
- **pycairo >=1.25** (current: 1.29.0): `CairoCanvas.draw_rectangle()` draws highlight backgrounds with alpha support — API verified in codebase at `src/codepicture/render/canvas.py` lines 162-192
- **Pydantic >=2.5** (current: 2.12.5): Nested `BaseModel` for highlight style definitions, `dict[str, list[str]]` for line-to-style mappings — supported since v2.0
- **Typer >=0.21.1**: New CLI flags for highlight line specification (`--highlight-lines`, `--highlight-add`, etc.) — existing flag pattern extends naturally
- **Pygments >=2.19**: No changes needed — syntax highlighting is orthogonal to line background highlighting

**What NOT to add:**
- Color manipulation libraries (`colour`, `colormath`) — `Color.from_hex()` already handles `#RRGGBBAA` with alpha
- Diff parsing libraries (`unidiff`, `difflib`) — highlights are user-specified line ranges, not computed from diffs
- New rendering libraries — Cairo's existing rectangle primitives are exactly what's needed

### Expected Features

**Must have (table stakes):**
- **Line range syntax** — `1,3-5,7` with comma-separated individual lines and inclusive ranges (universal across all tools)
- **Visual overlay** — Semi-transparent colored background spanning full width of code area (universal pattern)
- **CLI flag input** — `--highlight-lines` or similar for specifying lines (expected in every CLI tool)
- **Multi-format support** — Highlights must work in PNG, SVG, and PDF output (codepicture's existing promise)
- **Configurable colors** — `--highlight-color '#RRGGBBAA'` for user control (Silicon lacks this; common complaint)
- **TOML config support** — Default colors and settings in config file (consistency with codepicture's existing config system)

**Should have (competitive differentiator):**
- **Multiple named styles** — `add` (green), `remove` (red), `focus` (yellow/blue), `highlight` (default) — NO CLI tool currently supports all three in one command; only web tools (Snappify, Chalk.ist) and JS libraries (Shiki) offer this
- **Focus mode** — Dim unfocused lines when `focus` style is active (pattern from Carbon's `selectedLines` and Shiki's `transformerNotationFocus`)
- **Theme-aware default colors** — Derive sensible highlight colors from active theme background for automatic contrast
- **Gutter indicators** — Optional `+`/`-` symbols or colored bars in line number gutter (GitHub diff convention)

**Defer (v2+):**
- **Inline annotations** — Shiki-style `// [!code highlight]` comments in source files (requires language-aware parsing; fundamentally different input paradigm)
- **Word-level highlighting** — Sub-line precision (different feature category; complicates rendering significantly)
- **Animation/step syntax** — Multiple highlight states for presentations (codepicture produces static images)
- **Blur/grayscale effects** — For unfocused lines (opacity reduction achieves same goal with simpler implementation)

### Architecture Approach

**Insertion point:** Line highlight rectangles must be drawn after the main background but before line numbers and code tokens. The modified render order is: (1) canvas background, (2) window chrome, (3) **line highlight rectangles** [NEW], (4) line numbers, (5) syntax tokens. This ensures text remains readable on top of colored overlays.

**Major components:**
1. **Config schema** (`config/schema.py`) — Add `highlight_lines: dict[str, list[str]]` and `highlight_styles: dict[str, HighlightStyle]` fields to `RenderConfig` Pydantic model
2. **Resolution layer** (`render/highlights.py` NEW) — Parse line ranges (`"3,5,7-9"` → `[3,5,7,8,9]`), map style names to colors, produce `dict[int, Color]` consumed by renderer
3. **Renderer integration** (`render/renderer.py`) — Call resolution at render start, insert rectangle draw into both `_render_wrapped()` and `_render_legacy()` before line number/token loops
4. **CLI flags** (`cli/app.py`) — Add `--highlight-lines` with style syntax parsing (`add:1-3,5;remove:10`)

**Data flow:** CLI input → Config model → Resolution layer → Renderer consumes `dict[source_line_num: Color]` → Draw rectangles in display line loop using `DisplayLine.source_line_idx` mapping.

**Highlight geometry:** X=`content_x`, Y=`content_y + code_y_offset + display_idx * line_height_px`, Width=`content_width`, Height=`line_height_px`. All values already computed by `LayoutEngine` in `LayoutMetrics`.

**Word wrap handling:** Highlight lookups operate on source line indices. When drawing, check each `DisplayLine.source_line_idx` against the highlight map — ALL display lines belonging to a highlighted source line get rectangles. This matches VS Code's behavior after their [issue #85530](https://github.com/microsoft/vscode/issues/85530) fix.

**Components NOT modified:** `layout/engine.py` (geometry already available), `render/canvas.py` (existing `draw_rectangle()` sufficient), `core/types.py` (existing `Color` supports alpha), `render/chrome.py` (independent), `render/shadow.py` (post-process, unaffected).

### Critical Pitfalls

1. **Wrong z-order (drawing highlights over text)** — Highlight rectangles drawn AFTER tokens paint over text, making it invisible. **Prevention:** Insert highlight draw immediately after establishing `code_y_offset`, before line number loop. Test with semi-transparent highlights to verify text remains visible.

2. **Partial word-wrapped line highlighting** — Wrapped source line spans multiple display lines, but only first display line gets highlighted. **Prevention:** Use `DisplayLine.source_line_idx` to map display lines to source lines. Highlight ALL display lines belonging to highlighted source indices. Test with long wrapped lines.

3. **Highlight width inconsistency** — Rectangles too narrow (code area only, leaving gutter unhighlighted) or too wide (bleeding into rounded corners). **Prevention:** Use `content_x` and `content_width` from `LayoutMetrics` — covers gutter + code area but respects outer padding. Verify with line numbers enabled.

4. **Semi-transparent highlights differ across PNG/SVG/PDF** — Cairo alpha compositing behaves differently in vector vs raster backends. **Prevention:** Either pre-blend highlight colors with theme background to produce opaque results, OR test all three formats explicitly and document viewer-dependent behavior.

5. **Theme color clashing** — Fixed green "add" highlight makes green string tokens invisible on certain themes. **Prevention:** Derive highlight colors from theme background using low-saturation tints (`lerp(theme.background, tint_color, 0.15)`). Test contrast ratios against token colors (WCAG AA 3:1 minimum).

6. **Rectangle height doesn't match line spacing** — Using `char_height` instead of `line_height_px` creates gaps between consecutive highlighted lines with line height multipliers >1.0. **Prevention:** Rectangle height = `metrics.line_height_px` exactly. Y-position is top of line slot, not baseline.

7. **Forgetting legacy (non-wrapped) render path** — Implementing highlights only in `_render_wrapped()` means they don't appear when `window_width` is unset. **Prevention:** Implement highlight drawing in BOTH `_render_wrapped()` and `_render_legacy()`. Test with and without `--window-width`.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Core Highlighting Infrastructure
**Rationale:** Foundation must be solid before differentiated features. Establishes data flow, config schema, and basic rendering. Dependencies-first: config → resolution → rendering → CLI.

**Delivers:** Single-style line highlighting with configurable color, working across all output formats.

**Addresses:**
- Line range parser (`"1,3-5,7"` syntax)
- Config schema fields (`highlight_lines`, `highlight_colors`)
- Resolution layer (`render/highlights.py`)
- Renderer integration (both wrapped and legacy paths)
- CLI flag (`--highlight-lines` basic form)
- Works in PNG, SVG, PDF

**Avoids:**
- Pitfall 1 (z-order) — design decision made upfront
- Pitfall 6 (height) — geometry correct from start
- Pitfall 7 (legacy path) — both paths implemented together

**Research flag:** No additional research needed — all patterns documented in ARCHITECTURE-LINE-HIGHLIGHTING.md

### Phase 2: Named Styles and Focus Mode
**Rationale:** The competitive differentiator. Builds on Phase 1 infrastructure. Named styles require style-to-color mapping and CLI syntax extension. Focus mode adds opacity modification to non-focused lines.

**Delivers:** `--highlight-add`, `--highlight-remove`, `--highlight-focus` with distinct colors and focus mode dimming.

**Uses:**
- Pydantic `dict[str, BaseModel]` validation for style definitions
- Existing `resolve_highlights()` extended for multi-style resolution
- Renderer opacity control for non-focused lines

**Implements:**
- Default color constants for each style (green, red, yellow/blue)
- CLI syntax parsing (`add:1-3,5;remove:10` format)
- Focus mode: reduce opacity of lines not in focus set
- TOML config for per-style color overrides

**Avoids:**
- Pitfall 5 (color clashing) — use low-saturation defaults, defer theme-awareness to Phase 3

**Research flag:** No additional research needed — patterns established in FEATURES.md and competitive analysis

### Phase 3: Theme Integration and Polish
**Rationale:** Refinement after core functionality proven. Theme-aware colors require analyzing background luminance and deriving contrasting tints. Gutter indicators are visual enhancement.

**Delivers:** Automatic highlight color derivation from theme, optional gutter indicators, contrast validation.

**Addresses:**
- Theme-aware default colors (blend formula based on background)
- Gutter indicators (`+`/`-` symbols or colored bars)
- Contrast ratio testing against all 55+ themes
- Pre-blended opaque colors for consistent cross-format appearance

**Avoids:**
- Pitfall 4 (SVG/PDF alpha) — pre-blending eliminates alpha compositing differences
- Pitfall 5 (color clashing) — computed tints maintain readability across themes

**Research flag:** NEEDS RESEARCH — Theme color analysis heuristics not fully documented. Use `/gsd:research-phase` for color theory and WCAG contrast calculations if automatic derivation is complex.

### Phase Ordering Rationale

**Why this order:**
- **Phase 1 before 2:** Named styles are a parameter to the resolution function — the resolution function must exist first
- **Phase 2 before 3:** Theme integration adjusts color inputs to resolution; resolution and rendering must be working before color derivation can be validated
- **Dependencies respected:** Config → Resolution → Rendering → CLI → Theme integration

**Why this grouping:**
- **Phase 1 (foundation):** All components touched once, integration validated across formats
- **Phase 2 (differentiation):** User-facing value delivered; competitive positioning achieved
- **Phase 3 (polish):** Optional enhancements that improve UX but don't block launch

**Pitfall avoidance:**
- Critical pitfalls (z-order, word wrap, width) addressed in Phase 1 design
- Moderate pitfalls (alpha differences, color clashing) addressed in Phase 3
- Minor pitfalls (off-by-one, corner clipping) deferred to testing/polish

### Research Flags

**Phases with standard patterns (skip additional research):**
- **Phase 1:** Config, resolution, rendering — all patterns documented in existing codebase. `draw_rectangle()` API verified. No unknowns.
- **Phase 2:** Named styles pattern well-established across competing tools. Focus mode implementation clear from Carbon/Shiki examples.

**Phases likely needing deeper research:**
- **Phase 3 (theme integration):** If theme-aware color derivation proves complex, use `/gsd:research-phase` to investigate:
  - Color luminance calculation formulas (HSL/LAB color spaces)
  - Contrast ratio computation (WCAG formulas)
  - Tinting algorithms that preserve readability across light/dark themes
  - Whether to add highlight color fields to Theme protocol vs. runtime derivation

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | No new dependencies. All required APIs verified in existing codebase source. Version compatibility confirmed via PyPI. |
| Features | HIGH | Cross-referenced 7+ tools (Silicon, Carbon, Snappify, Chalk.ist, CodeSnap, Shiki, Reveal.js). User expectations clear. MVP scope well-defined. |
| Architecture | HIGH | Direct source code analysis of rendering pipeline. Integration points identified. Data flow designed. Geometry formulas derived from existing `LayoutMetrics`. |
| Pitfalls | HIGH | 10 pitfalls identified from Cairo documentation, VS Code issue tracker, and domain experience. Prevention strategies concrete and testable. |

**Overall confidence:** HIGH

### Gaps to Address

**Minor uncertainty:**
- **Theme-aware color derivation heuristics:** Research documents the GOAL (derive contrasting tints from background) but not the exact FORMULA. Phase 3 may need color theory research if simple linear interpolation doesn't produce good results across all themes.
- **Handling:** Start Phase 3 with `lerp(background, tint, 0.15)` approach. If visual testing across themes shows poor results, trigger `/gsd:research-phase` for color space analysis (HSL vs. LAB for perceptual uniformity).

**SVG/PDF alpha blending variability:**
- Research notes potential differences in alpha compositing across Cairo backends.
- **Handling:** Phase 1 includes explicit visual regression tests for all three formats. If differences appear, Phase 3 pivots to pre-blended opaque colors as primary recommendation.

**Gutter indicator rendering details:**
- Research identifies the UX goal (diff-style markers) but not the exact rendering approach (text glyphs vs. geometric shapes).
- **Handling:** Phase 3 implementation decision. Try Unicode characters (`+`/`-`) first for simplicity. If alignment issues arise, use Cairo line drawing for colored bars.

## Sources

### Primary (HIGH confidence)

**Technology stack:**
- [pycairo 1.29.0 on PyPI](https://pypi.org/project/pycairo/) — Version compatibility verified
- [Pydantic 2.12.5 on PyPI](https://pypi.org/project/pydantic/) — Nested model validation confirmed

**Codebase verification (direct source analysis):**
- `src/codepicture/render/canvas.py` lines 162-192 — `CairoCanvas.draw_rectangle()` with alpha Color support
- `src/codepicture/core/types.py` lines 35-98 — `Color.from_hex()` with `#RRGGBBAA` support
- `src/codepicture/core/types.py` lines 141-152 — `DisplayLine.source_line_idx` for word-wrap mapping
- `src/codepicture/core/types.py` lines 154-188 — `LayoutMetrics` geometry fields
- `src/codepicture/config/schema.py` — `RenderConfig` Pydantic model structure
- `src/codepicture/render/renderer.py` lines 47-317 — Rendering pipeline order

**Competitive analysis:**
- [Silicon GitHub](https://github.com/Aloxaf/silicon) — `--highlight-lines` flag, single style, semicolon syntax
- [Carbon GitHub](https://github.com/carbon-app/carbon) — `selectedLines` with dimming, single style
- [carbon-now-cli GitHub](https://github.com/mixn/carbon-now-cli) — Comma-separated line syntax
- [Shiki transformers docs](https://shiki.style/packages/transformers) — Multiple styles (highlight, diff, focus), inline annotations
- [Reveal.js code docs](https://revealjs.com/code/) — `data-line-numbers` comma-separated syntax
- [Snappify docs](https://snappify.com/docs/api/simple-snap) — Full color control, blur/gray effects
- [Chalk.ist](https://chalk.ist/) — Diff view with `+`/`-` markers

### Secondary (MEDIUM confidence)

**Pitfalls documentation:**
- [VS Code issue #85530](https://github.com/microsoft/vscode/issues/85530) — Word wrap + line highlighting interaction
- [Cairo compositing operators](https://www.cairographics.org/operators/) — Z-order and alpha blending behavior
- [Pycairo transparency examples](https://zetcode.com/gfx/pycairo/transparency/) — `set_source_rgba` patterns

**Accessibility and color contrast:**
- [Syntax highlighting and color contrast accessibility](https://maxchadwick.xyz/blog/syntax-highlighting-and-color-contrast-accessibility) — WCAG requirements
- [a11y-syntax-highlighting](https://github.com/ericwbailey/a11y-syntax-highlighting) — Contrast ratio patterns

**Cairo backend differences:**
- [Cairo PDF opacity issues](https://github.com/GiovineItalia/Compose.jl/issues/181) — PDF alpha rendering quirks
- [Emacs Cairo SVG transparency fix](https://lists.gnu.org/archive/html/bug-gnu-emacs/2019-05/msg01122.html) — Premultiplied alpha correction

---
*Research completed: 2026-02-02*
*Ready for roadmap: yes*
