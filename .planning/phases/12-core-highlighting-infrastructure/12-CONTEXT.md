# Phase 12: Core Highlighting Infrastructure - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Single-style line highlighting with configurable color across all output formats (PNG, SVG, PDF). Users specify lines via CLI flag or TOML config, and those lines render with a colored background overlay. Named styles, focus mode, gutter indicators, and theme-aware colors are separate phases (13 and 14).

</domain>

<decisions>
## Implementation Decisions

### Highlight appearance
- Full-width highlight: background spans the entire code area edge-to-edge, not just behind the text
- No extra vertical padding: highlight fills exactly the line height, no gaps between consecutive highlighted lines
- Edge treatment is Claude's discretion, but must be designed so both sharp rectangles and merged rounded blocks can be supported later (or both offered)
- Rendering layer order is Claude's discretion — pick whichever produces the best visual result across PNG/SVG/PDF

### Line range syntax
- CLI flag: `--highlight-lines` (no short alias in Phase 12)
- Repeatable flag: `--highlight-lines 3 --highlight-lines 7-12 --highlight-lines 15`
- Out-of-bounds line numbers: error and exit (strict validation)
- TOML config format: Claude's discretion — pick what's most natural for TOML

### Word-wrap behavior
- Users specify source (logical) line numbers, not display line numbers
- When a highlighted source line wraps, ALL wrapped display lines get the highlight background
- No continuation markers needed — the continuous highlight block is sufficient
- Highlighting works identically whether word wrap is on or off (wrap-off is the simpler subset)

### Default color & opacity
- Default highlight color: yellow family
- Default opacity: noticeable range (~20-30% opacity)
- Color flag: `--highlight-color '#RRGGBBAA'` (8-char hex with alpha)
- Also accept `#RRGGBB` (6-char hex) which defaults to the standard ~25% opacity
- TOML equivalent for color: follows same format as CLI

### Claude's Discretion
- Edge treatment approach (sharp vs rounded) — design for future flexibility
- Highlight rendering layer order (behind text vs semi-transparent overlay)
- TOML config format for highlight_lines
- Exact yellow shade and precise opacity value within the ~20-30% range
- Loading/error state handling during rendering

</decisions>

<specifics>
## Specific Ideas

No specific references — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-core-highlighting-infrastructure*
*Context gathered: 2026-02-03*
