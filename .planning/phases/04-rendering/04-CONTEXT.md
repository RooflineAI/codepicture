# Phase 4: Rendering - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce polished images with window chrome, shadows, and all visual effects. Outputs PNG, SVG, and PDF formats. Users can view rendered code images with optional line numbers, macOS-style window decoration, and drop shadow.

</domain>

<decisions>
## Implementation Decisions

### Window Chrome Style
- Include title bar with traffic light buttons AND optional title text
- Title text empty by default — requires explicit `--title` flag to show
- Traffic light buttons are static only — no hover/click states
- Buttons always positioned on the left (macOS style), not configurable
- `--no-chrome` flag removes title bar entirely
- Follow macOS window appearance — seamless transition between title bar and content (no separator line)
- Title text uses system sans-serif font (not monospace code font)

### Shadow Appearance
- macOS-style window shadow — follow macOS window shadow aesthetic
- Shadow is on by default, `--no-shadow` to disable
- Shadow style is fixed (not configurable blur/offset) — just on/off toggle
- PNG background is transparent (alpha channel) — shadow composites over any background

### Line Number Styling
- Line numbers shown by default, `--no-line-numbers` to disable
- No visual separator between gutter and code — just spacing
- Line number color is muted foreground — dimmer version of text color
- Line numbers always start at 1 (configurable start line deferred to future version)

### Output Format Behavior
- Default format is PNG
- PNG always rendered at 2x resolution for crisp high-DPI output
- Output filename is required — user must specify `-o output.png`

### Claude's Discretion
- Title bar background color (match code background vs slightly darker)
- SVG text rendering approach (text elements vs outlined paths)
- Testing strategy (golden files vs standard unit tests)
- Exact traffic light button sizing and spacing
- Shadow blur radius, offset, and opacity values (within macOS aesthetic)
- Gutter padding and spacing values

</decisions>

<specifics>
## Specific Ideas

- "Think of macOS how windows normally look like" — follow native macOS window aesthetic throughout
- v1 simplicity preferred — configurable start line deferred to later version

</specifics>

<deferred>
## Deferred Ideas

- Configurable line number start (`--start-line 42`) — future version
- Configurable shadow parameters (blur, offset) — keep macOS fixed style for v1
- Windows-style button positioning — macOS left-side buttons only for v1

</deferred>

---

*Phase: 04-rendering*
*Context gathered: 2026-01-29*
