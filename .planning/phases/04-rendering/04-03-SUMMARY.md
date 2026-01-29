---
phase: 04-rendering
plan: 03
subsystem: render
tags: [pillow, cairo, shadow, gaussian-blur, png]

# Dependency graph
requires:
  - phase: 04-01
    provides: CairoCanvas with ImageSurface for PNG rendering
provides:
  - apply_shadow function for PNG shadow post-processing
  - Shadow constants (BLUR_RADIUS, OFFSET_X, OFFSET_Y, COLOR)
  - calculate_shadow_margin helper for canvas pre-expansion
affects: [04-04, rendering-integration]

# Tech tracking
tech-stack:
  added: []  # Pillow already installed from prior phase
  patterns: [Cairo-to-Pillow conversion with RGBa mode, alpha-channel shadow extraction]

key-files:
  created: [src/codepicture/render/shadow.py]
  modified: [src/codepicture/render/__init__.py]

key-decisions:
  - "Cairo BGRA converted via Pillow RGBa mode to handle pre-multiplied alpha"
  - "Shadow margin = blur*2 + max(offset) = 125px total expansion"

patterns-established:
  - "Cairo-to-Pillow: Use Image.frombytes('RGBa', ...) then convert('RGBA')"
  - "Alpha-based shadow: Extract alpha channel, apply to shadow color, then blur"

# Metrics
duration: 4min
completed: 2026-01-29
---

# Phase 4 Plan 3: Shadow Post-Processing Summary

**Pillow-based shadow post-processing with 50px Gaussian blur and 25px downward offset for macOS aesthetic**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-29T09:35:14Z
- **Completed:** 2026-01-29T09:39:59Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- apply_shadow function converts Cairo ImageSurface to Pillow, applies GaussianBlur, composites shadow under content
- Shadow enabled returns expanded canvas with 125px margin (50*2 + 25)
- Shadow disabled returns plain PNG via Cairo's write_to_png
- Correct Cairo BGRA to Pillow RGBA conversion using "RGBa" mode (handles pre-multiplied alpha)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create shadow module with apply_shadow function** - `128241e` (feat)
2. **Task 2: Update render module exports** - `2bc77b6` (feat)

## Files Created/Modified
- `src/codepicture/render/shadow.py` - Shadow post-processing with apply_shadow and constants
- `src/codepicture/render/__init__.py` - Added shadow exports to render module

## Decisions Made
- **Cairo BGRA conversion:** Use Pillow's "RGBa" mode for frombytes to correctly handle Cairo's pre-multiplied alpha, then convert to standard "RGBA"
- **Shadow margin calculation:** blur_radius * 2 + max(abs(offset_x), abs(offset_y)) = 50*2 + 25 = 125px
- **Fixed shadow style:** Per CONTEXT.md, shadow is on/off only - no configurable blur/offset

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed without issues.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Shadow module ready for integration with Renderer (Plan 04-04)
- calculate_shadow_margin provides pre-expansion calculation for correct canvas sizing
- SVG/PDF shadow skipping documented as limitation (per RESEARCH.md decision)

---
*Phase: 04-rendering*
*Completed: 2026-01-29*
