---
phase: 04-rendering
plan: 02
summary: "macOS window chrome with traffic light buttons and title bar"

dependency-graph:
  requires:
    - 04-01 (CairoCanvas for drawing operations)
  provides:
    - Window chrome rendering (draw_title_bar, draw_traffic_lights)
    - Title bar height constant for layout calculations
  affects:
    - 04-04 (Renderer will use chrome functions)

tech-stack:
  added: []
  patterns:
    - TYPE_CHECKING guard for canvas import

file-tracking:
  key-files:
    created:
      - src/codepicture/render/chrome.py
    modified:
      - src/codepicture/render/__init__.py

decisions:
  - id: "04-02-title-color"
    choice: "Auto-detect title color from background brightness"
    rationale: "Dark backgrounds get light title text, light backgrounds get dark title text"

metrics:
  duration: "2 min"
  completed: "2026-01-29"
---

# Phase 04 Plan 02: Window Chrome Summary

macOS window chrome with traffic light buttons (red/yellow/green) and optional title bar

## What Was Built

### Chrome Module (`src/codepicture/render/chrome.py`)

Created window chrome rendering module with:

1. **Constants** (per RESEARCH.md macOS values):
   - `TITLE_BAR_HEIGHT = 28` (px, macOS standard)
   - `BUTTON_DIAMETER = 12` (px)
   - `BUTTON_SPACING = 8` (px between buttons)
   - `BUTTON_MARGIN_LEFT = 8` (px from left edge)
   - Button colors: `#ff5f57` (red), `#febc2e` (yellow), `#28c840` (green)

2. **`draw_traffic_lights(canvas, title_bar_y)`**:
   - Draws three circular buttons at left edge
   - Centers buttons vertically in title bar
   - Uses CairoCanvas.draw_circle() for each button

3. **`draw_title_bar(canvas, width, background, title=None, corner_radius=0)`**:
   - Draws title bar background (matches code background per CONTEXT.md)
   - Calls draw_traffic_lights() for window controls
   - Centers optional title text horizontally
   - Auto-detects title color based on background brightness
   - Supports rounded top corners for window appearance

### Module Exports

Updated `src/codepicture/render/__init__.py` to export:
- `draw_title_bar`
- `draw_traffic_lights`
- `TITLE_BAR_HEIGHT`

## Commits

| Hash | Description |
|------|-------------|
| b1301b0 | feat(04-02): create chrome module with traffic lights and title bar |
| a69831b | feat(04-02): export chrome functions from render module |

## Verification Results

- All 160 tests pass
- Traffic light button colors match RESEARCH.md values (#ff5f57, #febc2e, #28c840)
- Buttons are 12px diameter with 8px spacing
- Title bar is 28px height
- Functions exported from render module
- No circular import errors

## Deviations from Plan

None - plan executed exactly as written.

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Title text color | Auto-detect from background | Dark backgrounds get light text (200,200,200,200), light backgrounds get dark text (80,80,80,200) |
| Title font family | SF Pro with fallbacks | Uses TITLE_FONT_FAMILIES tuple: ("SF Pro", "Helvetica Neue", "Helvetica", "Arial") |
| Title font size | 13px | macOS title bar standard |

## Next Phase Readiness

**Ready for 04-03 (Shadow Post-Processing):**
- Chrome module provides title bar height for layout calculations
- Traffic lights draw correctly using CairoCanvas
- Window chrome is complete and ready for shadow integration

**Blockers:** None
