# Phase 3: Layout Engine - Context

**Gathered:** 2026-01-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Calculate exact canvas dimensions and element positions before any rendering. This is the measurement layer between syntax highlighting (tokens) and rendering (pixels). Includes text measurement, typography configuration, and canvas sizing.

</domain>

<decisions>
## Implementation Decisions

### Text Measurement
- Bundle JetBrains Mono as default font (don't rely on system fonts)
- Allow system font override via configuration
- If requested font not found: warn and fall back to bundled default
- Default font size: 16px
- Default line height: 1.4x
- Default tab width: 4 spaces

### Layout Boundaries
- Line numbers enabled by default
- Fixed gap (12px) between line numbers and code
- Padding is configurable, default 16px (compact)
- Fixed corner radius: 8px
- Shadow is overlay effect, not part of canvas dimensions
- Transparent background outside the window
- Line numbers always start at 1 (no --start-line option for v1)

### Configuration Design
- Strict validation of configuration values
- Font size range: 8-32px
- Maximum padding: 128px
- Values outside range produce clear error messages

### Edge Case Handling
- Empty input: error and exit (refuse to render)
- Long lines: best effort (may produce wide images)
- Emoji/non-monospace: best effort, may have alignment issues
- Files with hundreds of lines: render all lines, no cap

### Testing Approach
- Unit tests only (no visual snapshots)
- Standard cases sufficient: normal code, empty code, long lines
- No exhaustive unicode/emoji edge case coverage for v1

### Claude's Discretion
- Font ligatures: on or off by default
- Font weight: fixed or configurable
- Whether layout engine positions code only vs code+chrome
- DPI/scale multiplier support
- Configuration units (px vs pt)
- Test fixtures vs computed expectations
- Line number width calculation (fixed vs dynamic)

</decisions>

<specifics>
## Specific Ideas

- JetBrains Mono chosen for its excellent ligature support and popularity
- Padding default 16px for compact look (user can increase for presentations)
- Corner radius 8px for macOS-like feel
- Transparent canvas allows compositing the image anywhere

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-layout-engine*
*Context gathered: 2026-01-28*
