# Feature Landscape: v2.0 Line Highlighting

**Domain:** Line highlighting in code screenshot / code-to-image tools
**Project:** codepicture v2.0
**Researched:** 2026-02-02
**Confidence:** HIGH (cross-referenced 7+ tools across CLI, web, and library ecosystems)

---

## Competitive Landscape Summary

Before defining features, here is how existing tools handle line highlighting:

| Tool | Type | Highlight Styles | CLI Syntax | Color Control | Dim/Blur Unfocused |
|------|------|-----------------|------------|---------------|-------------------|
| **Silicon** | Rust CLI | Single (overlay) | `--highlight-lines '1-3; 4'` | No (theme-derived) | No |
| **Carbon** | Web + CLI | Single (selected lines) | `selectedLines: "3,4,5,6"` in preset JSON | No | Yes (dims non-selected) |
| **Snappify** | Web + API | Added, Removed, Blur, Gray, Opacity | Per-line in API payload | Yes (full control) | Yes (blur + gray-out) |
| **Chalk.ist** | Web | Added (+), Removed (-) | N/A (GUI only) | No (green/red convention) | No |
| **CodeSnap/VSCodeSnap** | VS Code ext | Blue (focus), Green (+), Red (-) | Click line numbers | 3 preset colors | No |
| **Shiki** | JS library | Highlight, Diff (+/-), Focus, Error, Warning | Inline comments `// [!code highlight]` | CSS-customizable | Yes (focus blurs others) |
| **Reveal.js** | JS library | Single (highlight) | `data-line-numbers="3,8-10"` | CSS-customizable | No |

**Key insight:** The ecosystem has converged on a small set of highlight categories: **highlight** (generic emphasis), **add/remove** (diff-style), and **focus** (dim everything else). No CLI tool offers all three -- this is a clear differentiation opportunity.

---

## Table Stakes

Features users expect from any line highlighting implementation. Missing any of these means the feature feels incomplete or broken.

### 1. Highlight Specific Lines via CLI Flag

| Aspect | Detail |
|--------|--------|
| **Why Expected** | Every tool that supports line highlighting accepts line numbers as input. This is the fundamental interaction. |
| **Complexity** | Low |
| **Existing Dependencies** | CLI already built with Typer; adding a new flag is straightforward. Line numbers already tracked for the gutter feature. |
| **What to Build** | A `--highlight-lines` CLI flag that accepts a line specification string. |
| **Confidence** | HIGH |

### 2. Range Syntax: Individual Lines and Ranges

| Aspect | Detail |
|--------|--------|
| **Why Expected** | Every tool supports ranges. Nobody wants to type `3,4,5,6,7,8` when `3-8` works. Mixed individual+range is universal. |
| **Complexity** | Low |
| **Syntax Convention** | The ecosystem is split between comma-separated (`1,3-5,7` -- Reveal.js, Docusaurus, Carbon) and semicolon-separated (`1-3; 4` -- Silicon). **Recommend comma-separated** because it matches the broader convention: `cut`, `sed`, print page ranges, and most documentation tools all use commas. Silicon's semicolons are the outlier. |
| **What to Build** | Parser for `"1,3-5,7,12-15"` syntax. 1-indexed, inclusive ranges. Validate that line numbers are positive integers within file bounds. |
| **Confidence** | HIGH |

### 3. Visual Overlay on Highlighted Lines

| Aspect | Detail |
|--------|--------|
| **Why Expected** | The visual effect of highlighting is a colored background band spanning the full width of the code area behind the highlighted line(s). This is universal across all tools. |
| **Complexity** | Low-Medium |
| **Existing Dependencies** | Cairo rendering pipeline already draws line-by-line. Need to insert a background rectangle draw before the text draw for highlighted lines. Must span the full code content width (not just text width). |
| **What to Build** | Semi-transparent colored rectangle behind each highlighted line. Default color should be theme-aware (e.g., a muted yellow/amber for dark themes, a muted blue for light themes). |
| **Confidence** | HIGH |

### 4. Works Across All Output Formats (PNG, SVG, PDF)

| Aspect | Detail |
|--------|--------|
| **Why Expected** | codepicture supports PNG, SVG, and PDF. Line highlighting must work in all three. Users will be frustrated if highlights appear in PNG but not SVG. |
| **Complexity** | Low (if architecture is clean) |
| **Existing Dependencies** | Rendering uses a protocol-based architecture with CairoCanvas. All three formats go through Cairo, so a single rectangle-draw implementation should propagate to all formats. SVG may need an explicit `<rect>` element for clean output. |
| **What to Build** | Ensure the highlight rectangle is drawn via the canvas abstraction, not format-specific code. Verify with visual regression tests across all three formats. |
| **Confidence** | HIGH |

### 5. TOML Config File Support

| Aspect | Detail |
|--------|--------|
| **Why Expected** | codepicture already supports TOML config for all other settings. Line highlighting config should follow the same pattern. Users expect to set default highlight colors in config rather than passing long CLI flags every time. |
| **Complexity** | Low |
| **Existing Dependencies** | Pydantic config model already exists. Add highlight-related fields. |
| **What to Build** | Config keys for default highlight color, style, and possibly named style presets. CLI flags override config as with all other settings. |
| **Confidence** | HIGH |

### 6. Configurable Highlight Color

| Aspect | Detail |
|--------|--------|
| **Why Expected** | Silicon notably does NOT support this, and it is a common complaint. Users want control over highlight colors to match their theme, brand, or presentation style. Snappify's full color control is a key selling point. |
| **Complexity** | Low |
| **What to Build** | A `--highlight-color` flag accepting hex colors (e.g., `#FFEB3B80` with alpha channel). Default to a sensible semi-transparent yellow/amber. Support alpha in the hex value for transparency control. |
| **Confidence** | HIGH |

---

## Differentiators

Features that set codepicture apart from competitors. Not universally expected, but high value for the target use case (presentations, tutorials, documentation).

### 1. Multiple Named Highlight Styles (add/remove/focus)

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | This is the single biggest differentiator. No CLI tool currently supports multiple highlight categories in one command. Silicon has one style. Carbon has one style. Only web tools (Snappify, Chalk.ist) and JS libraries (Shiki) offer multiple styles, and they are not CLI tools. |
| **Complexity** | Medium |
| **What to Build** | Named styles with distinct colors and semantics. Recommended set based on ecosystem consensus: |
| | - **highlight** (default): Generic emphasis. Yellow/amber overlay. |
| | - **add**: Line was added. Green overlay (convention from git diff, GitHub, Chalk.ist, Shiki). |
| | - **remove**: Line was removed. Red overlay (convention from git diff, GitHub, Chalk.ist, Shiki). |
| | - **focus**: Draw attention here. Blue overlay or dim everything else (convention from Shiki, Snappify). |
| **CLI Syntax Options** | Two viable approaches, recommend Option A: |
| | **Option A -- Repeated flags:** `--highlight '3-5:add' --highlight '8:remove' --highlight '12-14:focus'` |
| | **Option B -- Multiple flags:** `--highlight-add '3-5' --highlight-remove '8' --highlight-focus '12-14'` |
| | Option A is more flexible (easy to add new styles without new flags) and follows the pattern of tools like `docker run -e` and `curl -H` for repeated key-value flags. Option B is more discoverable via `--help` but rigid. |
| **Confidence** | HIGH for the feature concept; MEDIUM for exact CLI syntax (needs user testing) |

### 2. Focus Mode: Dim Unfocused Lines

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | When "focus" style is used, dim or reduce opacity of all non-focused lines. This is what Carbon does with `selectedLines` and what Shiki does with `transformerNotationFocus`. Extremely effective for presentations and tutorials where you want to draw the eye to specific lines. |
| **Complexity** | Medium |
| **What to Build** | When any line has the `focus` style, reduce the opacity of all other lines (e.g., render text at 30-40% opacity). The focused lines remain at full brightness. This requires modifying the text rendering for non-focused lines, not just adding background rectangles. |
| **Notes** | This is a distinct rendering mode -- it changes how OTHER lines look, not just the highlighted ones. Must be carefully implemented to avoid breaking the visual balance. |
| **Confidence** | HIGH (well-established pattern in Carbon and Shiki) |

### 3. Theme-Aware Default Colors

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | Instead of hardcoded highlight colors, derive sensible defaults from the active theme. A yellow highlight on a yellow-background theme looks terrible. Auto-adapting colors remove this footgun. |
| **Complexity** | Medium |
| **What to Build** | Analyze the theme's background color and select a contrasting highlight color automatically. For dark backgrounds: lighter, warm overlays. For light backgrounds: darker, cooler overlays. User-specified `--highlight-color` overrides this. |
| **Notes** | Snappify handles this by giving users full control. A better DX is smart defaults with override capability. |
| **Confidence** | MEDIUM (heuristics may not work for all 55+ themes; fallback to manual override needed) |

### 4. Gutter Indicators for Highlight Style

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | In addition to (or instead of) background highlighting, show diff-style indicators in the line number gutter: `+` for add, `-` for remove, a colored dot or bar for focus. This mirrors GitHub's diff view and is immediately recognizable. |
| **Complexity** | Low-Medium |
| **Existing Dependencies** | Line number gutter already rendered. Need to add a small symbol or colored bar beside the line number. |
| **What to Build** | Optional gutter markers that appear when named styles are used. `+`/`-` for add/remove (green/red). Colored bar for focus/highlight. Controlled via a `--highlight-gutter` flag or auto-enabled when named styles are used. |
| **Confidence** | MEDIUM |

### 5. Highlight Line Specification via File Annotations

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | Instead of specifying line numbers on the CLI (which break when code changes), allow inline comments in the source file to mark highlights: `// [highlight]`, `// [add]`, `// [remove]`. Inspired by Shiki's `// [!code highlight]` pattern. |
| **Complexity** | Medium-High |
| **What to Build** | A preprocessor that scans for annotation comments, strips them from the rendered output, and applies the corresponding highlight style to those lines. Must handle comment syntax for different languages (`//`, `#`, `--`, `/**/`). |
| **Notes** | This is a v2.1+ feature. It adds significant complexity (language-aware comment parsing) and is a different UX paradigm from CLI flags. Worth noting as a future direction but not for the initial line highlighting release. |
| **Confidence** | HIGH for concept; LOW for v2.0 inclusion |

---

## Anti-Features

Features to deliberately NOT build. Common over-engineering traps for line highlighting.

### 1. DO NOT: Build Word-Level Highlighting

| **Why Avoid** | Shiki supports `// [!code word:Hello]` to highlight specific words within lines. This requires sub-line rendering control, complex text measurement, and significantly complicates the rendering pipeline. It is a different feature category entirely from line highlighting. |
| **What to Do Instead** | Stick to full-line highlighting. If word highlighting is needed later, it is a separate milestone with its own research. |

### 2. DO NOT: Support Step-Through Animation Syntax

| **Why Avoid** | Reveal.js uses `data-line-numbers="3-5|8-10|13-15"` where `|` separates animation steps. codepicture produces static images, not presentations. Animation steps have no meaning in a PNG/SVG/PDF. |
| **What to Do Instead** | If users want multiple highlight states, they run codepicture multiple times with different `--highlight` flags. One command = one image. |

### 3. DO NOT: Support Inline Annotations in v2.0

| **Why Avoid** | Shiki-style `// [!code highlight]` inline annotations require language-aware comment parsing, which is complex and error-prone across 50+ languages. It is a fundamentally different input mechanism from CLI flags. Mixing both in the initial release creates UX confusion. |
| **What to Do Instead** | Ship CLI flag-based line specification first. Inline annotations can be a v2.1 follow-up after the core highlighting rendering is solid. |

### 4. DO NOT: Build a Color Picker / Theme Builder

| **Why Avoid** | Scope creep. Snappify has a full-featured web editor with color pickers. codepicture is a CLI tool. Users who need fine-grained color control can specify hex values. |
| **What to Do Instead** | Accept hex colors with alpha via `--highlight-color '#RRGGBBAA'`. Document the default colors for each named style. |

### 5. DO NOT: Add Blur/Grayscale Effects for Unfocused Lines

| **Why Avoid** | Snappify supports blur and grayscale filters on unfocused lines. These are computationally expensive in Cairo (requires post-processing the rendered surface), look inconsistent across output formats (blur in SVG vs PNG is very different), and add visual complexity without proportional value. |
| **What to Do Instead** | Use opacity reduction for unfocused lines (focus mode). This is simpler, consistent across formats, and achieves the same goal of drawing attention to focused lines. Carbon and Shiki both use opacity, not blur. |

### 6. DO NOT: Support Overlapping Highlight Styles on the Same Line

| **Why Avoid** | What happens when line 5 is both "add" and "focus"? Blending two semi-transparent overlays creates unpredictable colors. The UX for specifying this is confusing. No tool in the ecosystem supports this. |
| **What to Do Instead** | Last style wins, or first style wins (pick one and document it). If a line appears in multiple `--highlight` flags, the last one takes precedence. Warn in verbose mode. |

---

## Feature Dependencies

```
Highlight Line Parser -----> All highlight features
  [Parse "1,3-5,7" syntax]     (everything needs line numbers)

Highlight Renderer -----> Multiple Styles, Focus Mode, Gutter Indicators
  [Draw background rects]     (styles are variations of the renderer)

Configurable Colors -----> Theme-Aware Defaults
  [Accept hex colors]           (theme-aware defaults need color infrastructure)

Named Styles (add/remove/focus) -----> Gutter Indicators
  [Style categories exist]            (gutter shows style-specific markers)

Named Styles -----> Focus Mode (Dim Unfocused)
  [Focus is a named style]     (dimming is focus-specific behavior)
```

**Critical path:** Line parser -> Highlight renderer -> Configurable colors -> Named styles -> Focus mode

---

## MVP Recommendation

For v2.0 line highlighting, prioritize in this order:

**Phase 1: Core highlighting (must ship)**
1. `--highlight-lines '1,3-5,7'` CLI flag with comma-separated range syntax
2. Semi-transparent background overlay on highlighted lines (single color)
3. `--highlight-color '#RRGGBBAA'` for user-specified color
4. Works across PNG, SVG, PDF
5. TOML config support for default highlight color

**Phase 2: Named styles (the differentiator)**
6. Multiple named styles: `--highlight '3-5:add' --highlight '8:remove' --highlight '12-14:focus'`
7. Default colors per style: green (add), red (remove), yellow (highlight), blue (focus)
8. Focus mode: dim unfocused lines when focus style is active

**Phase 3: Polish (if time permits)**
9. Theme-aware default highlight colors
10. Gutter indicators (`+`/`-`/colored bar) for named styles

**Defer to post-v2.0:**
- Inline source annotations (`// [highlight]`) -- different input paradigm, needs its own design
- Word-level highlighting -- different feature category
- Blur/grayscale effects -- opacity reduction is sufficient

---

## Recommended CLI Syntax

Based on ecosystem research, the recommended syntax for codepicture:

```bash
# Basic: highlight lines 3-5 and 7 with default color
codepicture snippet.py -o slide.png --highlight-lines '3-5,7'

# Custom color (hex with alpha)
codepicture snippet.py -o slide.png --highlight-lines '3-5,7' --highlight-color '#FFEB3B80'

# Named styles (the differentiator)
codepicture snippet.py -o slide.png \
  --highlight '3-5:add' \
  --highlight '8-9:remove' \
  --highlight '12:focus'

# Short form for common case (no style = "highlight")
codepicture snippet.py -o slide.png --highlight '3-5'
```

**Rationale for syntax choices:**
- **Commas** for separating line specs (not semicolons): matches broader CLI convention (`cut`, `sed`, print ranges)
- **Colon** for style separator: visually distinct from range hyphen, familiar from key:value patterns
- **Repeated `--highlight` flag**: extensible (new styles require no new flags), follows `docker -e`, `curl -H` pattern
- **`--highlight-lines`** as simple mode: no styles, just lines. `--highlight` as full mode with style support. Both can coexist.

---

## Sources

**Tool Documentation (HIGH confidence):**
- [Silicon GitHub](https://github.com/Aloxaf/silicon) -- `--highlight-lines` flag, semicolon-separated syntax
- [Carbon GitHub](https://github.com/carbon-app/carbon) -- `selectedLines` parameter dims non-selected lines
- [carbon-now-cli GitHub](https://github.com/mixn/carbon-now-cli) -- `selectedLines: "3,4,5,6"` in preset config
- [Shiki transformers docs](https://shiki.style/packages/transformers) -- `transformerNotationHighlight`, `transformerNotationDiff`, `transformerNotationFocus`
- [Reveal.js code docs](https://revealjs.com/code/) -- `data-line-numbers="3,8-10"` comma-separated syntax
- [Material for MkDocs code blocks](https://squidfunk.github.io/mkdocs-material/reference/code-blocks/) -- `hl_lines` space-separated syntax

**Tool Feature Analysis (MEDIUM confidence):**
- [Snappify docs](https://snappify.com/docs/api/simple-snap) -- API with per-line opacity, blur, gray, add/remove
- [Chalk.ist](https://chalk.ist/) -- diff view with `+`/`-` line markers
- [VSCodeSnap GitHub](https://github.com/luisllamasbinaburo/VSCodeSnap) -- blue/green/red click-to-highlight modes
- [CodeSnap-plus GitHub](https://github.com/wacns/CodeSnap-plus) -- click-to-highlight line feature

**Convention Research (MEDIUM confidence):**
- Line range syntax conventions across Reveal.js, Docusaurus, Zola, MkDocs -- comma-separated is most common
- [Snappify blog: best screenshot tools 2026](https://snappify.com/blog/best-screenshot-tools) -- competitive landscape overview
