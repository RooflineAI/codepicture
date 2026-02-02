# Domain Pitfalls: Line Highlighting for codepicture

**Domain:** Adding line highlighting (colored background rectangles) to an existing Cairo-based code-to-image renderer
**Researched:** 2026-02-02
**Confidence:** HIGH (based on codebase analysis + Cairo documentation + VS Code issue tracker precedent)

---

## Critical Pitfalls

Mistakes that cause visual breakage or require rearchitecting.

### Pitfall 1: Wrong Z-Order -- Drawing Highlights Over Text

**What goes wrong:** Highlight rectangles are drawn *after* syntax tokens, painting over already-rendered text. The text disappears behind the colored rectangle.

**Why it happens:** The existing rendering pipeline in `renderer.py` draws background, then chrome, then line numbers and tokens. A naive addition might insert highlight drawing at the wrong point in this sequence -- especially if highlights are implemented as a separate pass rather than integrated into the existing draw order.

**Consequences:** Text is invisible on highlighted lines. Looks correct for fully opaque backgrounds only if you happen to draw text afterward, but breaks if draw order changes.

**Prevention:** Highlight rectangles MUST be drawn after the main background but BEFORE line numbers and syntax tokens. In the current `_render_wrapped` and `_render_legacy` methods, highlights should be the first thing drawn inside those methods (after `code_y_offset` is established), before either the line number loop or the token loop.

Specifically, the draw order must be:
1. Canvas background (existing `draw_rectangle` call)
2. Window chrome (existing `draw_title_bar` call)
3. **Line highlight rectangles** (NEW -- inserted here)
4. Line numbers
5. Syntax tokens

**Detection:** Visual test: render a highlighted line and verify text is readable. If text vanishes, z-order is wrong.

**Phase:** Must be correct from the initial implementation. This is a day-one concern.

---

### Pitfall 2: Word-Wrapped Lines -- Highlighting Only One Display Line Instead of All

**What goes wrong:** Source line 5 wraps into display lines 5a, 5b, 5c. The highlight is only applied to display line 5a (the first segment), leaving 5b and 5c unhighlighted. The user sees a partial colored band that abruptly stops mid-logical-line.

**Why it happens:** The highlight spec says "highlight line 5." The code maps this to a single display line index, not to ALL display lines belonging to source line 5. This is exactly the bug VS Code had ([issue #85530](https://github.com/microsoft/vscode/issues/85530)): "Highlight current line should highlight the complete logical line when word wrap is enabled."

**Consequences:** Confusing visual output. Users expect the highlight to cover the entire logical line. Partial highlighting looks like a rendering bug.

**Prevention:** Highlight lookups must operate on **source line indices**, not display line indices. When drawing highlights:
1. Receive highlight spec as `{source_line_index: style}`.
2. In the display line loop, check `dline.source_line_idx` against the highlight map.
3. Draw a rectangle for EVERY display line that belongs to a highlighted source line.

The `DisplayLine.source_line_idx` field already exists in `core/types.py` and provides exactly the mapping needed. The `is_continuation` field tells you whether to show a line number, but the highlight should appear regardless.

**Detection:** Test case: wrap-enabled file with a long highlighted line. Verify all continuation lines have the background color.

**Phase:** Must be handled when implementing the wrapped rendering path. Cannot be deferred.

---

### Pitfall 3: Highlight Width Inconsistency -- Gutter vs. Code Area

**What goes wrong:** Highlight rectangles span only the code area (from `code_x` to `code_x + code_width`), leaving the line number gutter unhighlighted. Or the reverse: highlights span the full canvas width including padding, creating colored bands that extend into margins and break the rounded corner clipping of the overall background.

**Why it happens:** No clear decision about what "full width" means. The layout has several horizontal zones: left padding, gutter (`gutter_x` to `gutter_x + gutter_width`), gap, code area (`code_x` to `code_x + code_width`), right padding. Different editors make different choices.

**Consequences:** Looks unpolished. If highlights go too wide, they bleed into rounded corners. If too narrow, the gutter has a jarring color discontinuity.

**Prevention:** Define the highlight rectangle explicitly as:
- **x:** `content_x` (left edge of content, after padding)
- **width:** `content_width` (covers gutter + gap + code area, but not outer padding)

This matches what VS Code, Sublime, and most code editors do: the highlight covers the gutter and code area but respects the outer padding/margin. The values `content_x` and `content_width` already exist in `LayoutMetrics`.

For the auto-width (non-wrapped) path where `canvas_width` is computed from content, the highlight should still use `content_x` and `content_width` to avoid bleeding into padding.

**Detection:** Visual test with line numbers enabled. The highlight should appear as a continuous band across both gutter and code columns.

**Phase:** Decide during design, implement from the start.

---

## Moderate Pitfalls

Mistakes that cause visual artifacts or require non-trivial fixes.

### Pitfall 4: Semi-Transparent Highlights on SVG/PDF -- Cairo Alpha Blending Differences

**What goes wrong:** Highlight colors use alpha transparency (e.g., `rgba(0, 255, 0, 0.15)` for a subtle green tint). This looks correct in PNG output but appears different in SVG or PDF output. PDF may render the alpha differently, or the SVG may show premultiplied alpha artifacts.

**Why it happens:** Cairo's PNG surface uses `ARGB32` with premultiplied alpha and handles blending in-memory. The SVG and PDF surfaces emit vector markup and delegate alpha compositing to the viewer (browser, PDF reader). Different viewers composite differently. Cairo may also fall back to rasterizing semi-transparent regions in PDF, producing unexpected bitmap patches in an otherwise vector output.

**Consequences:** Inconsistent appearance across output formats. Users generate a PNG that looks good, switch to PDF for printing, and get a different look.

**Prevention:**
- **Prefer opaque or near-opaque highlight colors.** Instead of `rgba(r, g, b, 0.15)` blended over the theme background, pre-compute the blended result as a solid color: `blended = alpha * highlight + (1 - alpha) * background`. This produces identical results across all three backends since no runtime alpha compositing is needed.
- **If alpha is truly desired**, test all three output formats explicitly. Use `set_source_rgba` (which the canvas already uses correctly) and avoid changing the Cairo operator from the default `OVER`.
- Do NOT use `OPERATOR_SOURCE` for highlights, as it would overwrite the background's rounded corner clipping.

**Detection:** Generate the same file in PNG, SVG, and PDF. Open all three and compare highlight color visually.

**Phase:** Address during theme/color integration. If pre-blending is chosen, it eliminates this entire class of bugs.

---

### Pitfall 5: Highlight Colors That Clash With Theme Foreground

**What goes wrong:** A "remove" highlight (red background) works on dark themes but makes dark-colored tokens invisible on light themes (dark red text on red background = unreadable). Or a green "add" highlight makes green tokens (strings in many themes) disappear.

**Why it happens:** Highlight colors are defined independently of the 55+ themes. The highlight color that provides good contrast against one theme's background may destroy contrast for tokens in another theme.

**Consequences:** Highlighted lines become unreadable for certain theme + highlight style combinations. This is subtle because it only affects specific token types on specific themes.

**Prevention:**
- **Derive highlight colors from the theme background**, not from fixed constants. For a dark background like `#1e1e2e`, an "add" green highlight could be `#1e2e1e` (slight green tint). For a light background like `#fafafa`, it could be `#e8f5e9`.
- **Use low-saturation, low-contrast tints.** The highlight should be a subtle shift from the background, not a vivid color that competes with syntax tokens.
- **Test formula:** Blend the highlight as `lerp(theme.background, tint_color, 0.10..0.20)`. This guarantees the result stays close to the background and preserves token readability.
- **Consider adding highlight color fields to the Theme protocol** so that TOML themes can override highlight colors per-theme.

**Detection:** Automated: for each theme, compute contrast ratio between every token color and each highlight background. Flag any ratio below 3:1 (WCAG AA minimum for large text).

**Phase:** Address during theme integration. Define the color derivation formula before implementing rendering.

---

### Pitfall 6: Highlight Rectangle Height Does Not Match Line Height

**What goes wrong:** The highlight rectangle is `char_height` tall, but lines are spaced at `line_height_px` (which is `char_height * line_height_multiplier`). With a 1.4x line height multiplier, there is a visible gap between consecutive highlighted lines, showing the raw background color between them. Or the rectangle overshoots and overlaps adjacent non-highlighted lines.

**Why it happens:** Confusing `char_height` (the font metric) with `line_height_px` (the spacing between baselines). The layout engine computes `line_height_px = char_height * self._config.line_height` but this value represents baseline-to-baseline distance, not the visual height of a line's "slot."

**Consequences:** Gaps between consecutive highlighted lines (looks like horizontal stripes). Or overlapping rectangles on adjacent lines (double-blending artifacts with semi-transparent colors).

**Prevention:** The highlight rectangle height MUST be exactly `metrics.line_height_px`. The y-position must be `metrics.content_y + code_y_offset + display_idx * metrics.line_height_px` (the TOP of the line slot, not the baseline). The rectangle runs from the top of this line slot to the top of the next line slot. This ensures consecutive highlighted lines produce a seamless colored band.

**Detection:** Test case: three consecutive highlighted lines. Verify no gap or overlap between highlight rectangles.

**Phase:** Initial implementation. Get the geometry right from the start.

---

### Pitfall 7: Forgetting the Legacy (Non-Wrapped) Rendering Path

**What goes wrong:** Highlights are implemented only in `_render_wrapped` and not in `_render_legacy`. When `window_width` is not set (auto-sizing mode), `display_lines` is an empty tuple, the code takes the legacy path, and highlights silently do nothing.

**Why it happens:** The renderer has two distinct code paths: `_render_wrapped` (when `display_lines` is populated) and `_render_legacy` (when it is not). A developer working on highlights may only modify the wrapped path, since that is the more complex and "current" path.

**Consequences:** Highlights work with `--window-width` but not without it. Users who do not use word wrap never see highlights.

**Prevention:** Either:
1. Add highlight drawing to BOTH `_render_legacy` and `_render_wrapped`.
2. Or refactor to always produce `display_lines` (even without wrapping, each source line maps 1:1 to a display line), eliminating the legacy path. This is the cleaner option but has a larger blast radius.

Option 1 is safer for a milestone that should not refactor existing behavior. Add highlight logic to both paths and test both.

**Detection:** Test highlights with and without `window_width` set.

**Phase:** Must be addressed in the initial implementation. Easy to miss.

---

## Minor Pitfalls

Mistakes that cause annoyance or minor visual issues.

### Pitfall 8: Off-by-One in Line Number Specification

**What goes wrong:** Users specify `--highlight-lines 5` expecting line 5 in their editor (1-based), but the renderer highlights line 4 or line 6 because of confusion between 0-based internal indices, 1-based user-facing numbers, and the `line_number_offset` configuration.

**Why it happens:** The existing code has `line_number_offset` (default 1) that offsets displayed line numbers. Source line indices are 0-based in the `lines` list. When the user says "highlight line 5," does that mean source index 4, displayed number 5, or source index 5?

**Prevention:**
- Define clearly: user-facing line numbers are **1-based** (or `line_number_offset`-based).
- Convert to 0-based source index at the CLI/config boundary: `source_idx = user_line_number - config.line_number_offset`.
- Validate that the resulting index is within bounds.
- Document this conversion in one place.

**Detection:** Test with `line_number_offset` set to a non-default value (e.g., 10).

**Phase:** CLI/config integration phase.

---

### Pitfall 9: Highlight Rectangles Extend Past Rounded Corner Clipping

**What goes wrong:** On the first or last line of code, the highlight rectangle extends into the rounded corner area of the main background, creating visible colored corners that break the rounded rectangle aesthetic.

**Why it happens:** The main background is drawn as a rounded rectangle, but highlight rectangles are drawn as sharp-cornered rectangles that can extend into the corner areas.

**Prevention:**
- If the code area is inset enough from the edges (due to padding), this will not be visible. With the default padding, the first code line is far enough below the top corners.
- If padding is reduced to near-zero, use `push_clip` with the same rounded rectangle path before drawing any highlights, ensuring they are clipped to the background shape. The canvas already has `push_clip`/`pop_clip` methods.
- Alternatively, only apply corner radius to highlight rectangles on the first/last visible lines. This is more complex but avoids the clipping overhead.

**Detection:** Test with very small padding values and highlights on the first/last lines.

**Phase:** Polish phase. Not critical for initial implementation if default padding provides sufficient inset.

---

### Pitfall 10: No Visual Distinction Between Highlight Styles in Printed/Grayscale Output

**What goes wrong:** "add" (green), "remove" (red), and "focus" (blue/yellow) highlights are distinguishable on screen but become identical gray bands when printed in grayscale or viewed by colorblind users.

**Why it happens:** The three highlight styles differ only by hue, not by lightness or pattern. In grayscale conversion, similar-lightness colors become indistinguishable.

**Prevention:**
- Ensure highlight styles differ in **lightness**, not just hue. "Remove" could be slightly darker than "add."
- Consider adding a subtle left-border accent (a 3px colored bar on the left edge of highlighted lines) as a secondary visual cue, similar to how GitHub renders diff views.
- This is a nice-to-have, not a blocker for initial implementation.

**Detection:** Convert output to grayscale and verify styles are distinguishable.

**Phase:** Post-MVP polish.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|---|---|---|
| Core rectangle drawing | Pitfall 1 (z-order), Pitfall 6 (height) | Get draw order and geometry right from first implementation |
| Word wrap integration | Pitfall 2 (partial highlight), Pitfall 7 (legacy path) | Use `source_line_idx` mapping; implement in both render paths |
| Theme integration | Pitfall 5 (color clashing), Pitfall 4 (alpha differences) | Derive colors from background; consider pre-blending alpha |
| CLI/config | Pitfall 8 (off-by-one) | Convert at boundary, test with non-default offset |
| Layout geometry | Pitfall 3 (width), Pitfall 9 (corners) | Use `content_x`/`content_width` from LayoutMetrics |
| Multi-format output | Pitfall 4 (SVG/PDF alpha) | Test all three formats; prefer opaque blended colors |

## Architecture Notes for codepicture Specifically

Based on reading the codebase, these are integration-specific observations:

1. **`draw_rectangle` already handles alpha correctly.** The `CairoCanvas.draw_rectangle` method uses `set_source_rgba` with `color.a / 255.0`. No changes needed to the canvas layer -- just pass a `Color` with the desired alpha to the existing method.

2. **`LayoutMetrics` already has the fields you need.** `content_x`, `content_width`, `line_height_px`, and `display_lines[].source_line_idx` provide all the geometry for positioning highlights.

3. **The Theme protocol needs extension.** Currently `Theme` has `background`, `foreground`, `line_number_fg`, `line_number_bg`, and `get_style()`. It does not have highlight colors. Either add `highlight_add`, `highlight_remove`, `highlight_focus` properties to the protocol, or compute them from `background` at render time. The latter is simpler and avoids changing the protocol for 55+ existing themes.

4. **The `Color` type supports alpha.** `Color.from_hex` already handles `#RRGGBBAA` format, so highlight colors with transparency can be specified directly in configuration.

## Sources

- [Cairo compositing operators](https://www.cairographics.org/operators/) -- z-order and alpha blending behavior
- [VS Code issue #85530](https://github.com/microsoft/vscode/issues/85530) -- word wrap + line highlighting interaction
- [Pycairo transparency](https://zetcode.com/gfx/pycairo/transparency/) -- `set_source_rgba` usage patterns
- [Pycairo groups and masks](https://engineeredjoy.com/blog/pycairo-alpha-mask-group/) -- advanced alpha compositing
- [Syntax highlighting and color contrast accessibility](https://maxchadwick.xyz/blog/syntax-highlighting-and-color-contrast-accessibility) -- contrast requirements
- [a11y-syntax-highlighting](https://github.com/ericwbailey/a11y-syntax-highlighting) -- WCAG-compliant theme patterns
- [Cairo PDF opacity issues](https://github.com/GiovineItalia/Compose.jl/issues/181) -- PDF alpha rendering differences
- [Emacs Cairo SVG transparency fix](https://lists.gnu.org/archive/html/bug-gnu-emacs/2019-05/msg01122.html) -- premultiplied alpha correction

---
*Pitfalls research for: codepicture v2.0 Line Highlighting*
*Researched: 2026-02-02*
