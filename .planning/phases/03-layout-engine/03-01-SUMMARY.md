---
phase: 03-layout-engine
plan: 01
subsystem: layout
tags: [cairo, pycairo, manimpango, fonts, text-measurement, jetbrains-mono]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Core types (Color, TextStyle) and protocols (TextMeasurer)
provides:
  - PangoTextMeasurer class for text dimension measurement
  - Bundled JetBrains Mono font (no system installation required)
  - Font registration and fallback utilities
affects: [03-layout-engine/02, 03-layout-engine/03, 04-rendering]

# Tech tracking
tech-stack:
  added: [pycairo, manimpango]
  patterns: [cairo-text-measurement, font-bundling, font-fallback-with-warning]

key-files:
  created:
    - src/codepicture/fonts/__init__.py
    - src/codepicture/fonts/JetBrainsMono-Regular.ttf
    - src/codepicture/layout/__init__.py
    - src/codepicture/layout/measurer.py
  modified:
    - pyproject.toml
    - src/codepicture/__init__.py

key-decisions:
  - "Use Cairo text API instead of PyGObject Pango due to library linking issues on macOS"
  - "Bundle JetBrains Mono Regular only (Bold can be added later if needed)"
  - "Font registration uses ManimPango for cross-platform compatibility"
  - "Text measurer uses font caching to avoid repeated font selection"

patterns-established:
  - "Font fallback with warning: resolve_font_family() logs warning and returns default"
  - "Lazy font registration: register_bundled_fonts() only runs once"
  - "Module-level state for registration tracking (_fonts_registered)"

# Metrics
duration: 6min
completed: 2026-01-29
---

# Phase 3 Plan 1: Font Management and Text Measurement Summary

**Cairo-based text measurer with bundled JetBrains Mono font for accurate code layout calculations**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-29T02:32:51Z
- **Completed:** 2026-01-29T02:38:31Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- JetBrains Mono Regular bundled in package (273KB TTF)
- PangoTextMeasurer provides accurate text dimensions for monospace code
- Font fallback with warning log when requested font unavailable
- All new modules exportable from top-level codepicture package

## Task Commits

Each task was committed atomically:

1. **Task 1: Add dependencies and bundle JetBrains Mono font** - `ac61b70` (feat)
2. **Task 2: Implement PangoTextMeasurer** - `2193fdd` (feat)

## Files Created/Modified
- `src/codepicture/fonts/__init__.py` - Font registration and fallback utilities
- `src/codepicture/fonts/JetBrainsMono-Regular.ttf` - Bundled font file
- `src/codepicture/layout/__init__.py` - Layout module exports
- `src/codepicture/layout/measurer.py` - PangoTextMeasurer implementation
- `pyproject.toml` - Added pycairo, manimpango deps + font bundling config
- `src/codepicture/__init__.py` - Added exports for new modules

## Decisions Made

1. **Cairo instead of Pango:** PyGObject has library linking issues on macOS when installed via pip (glib not found). Cairo's text API is sufficient for monospace code measurement.

2. **Removed pygobject dependency:** Since we're using Cairo directly instead of PyGObject/Pango, pygobject is not needed.

3. **Font height from font_extents:** Using ascent + descent from font_extents for consistent line height rather than individual text extent heights.

4. **Named PangoTextMeasurer for API compatibility:** The class is named PangoTextMeasurer to match the protocol expectations, even though it uses Cairo internally.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] PyGObject library linking failure on macOS**
- **Found during:** Task 2 (PangoTextMeasurer implementation)
- **Issue:** PyGObject via pip can't find libglib-2.0.0.dylib on macOS with Homebrew Python
- **Fix:** Switched to Cairo's text API instead of Pango. Cairo works without PyGObject.
- **Files modified:** src/codepicture/layout/measurer.py, pyproject.toml
- **Verification:** All tests pass, measurer returns correct dimensions
- **Committed in:** 2193fdd (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (blocking)
**Impact on plan:** Implementation uses Cairo instead of Pango. Functionally equivalent for monospace code. Can upgrade to Pango later if complex script support needed.

## Issues Encountered
None beyond the PyGObject linking issue (handled as deviation).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- PangoTextMeasurer ready for LayoutEngine integration (Plan 02)
- Font bundling working for consistent rendering
- All 143 existing tests still pass

---
*Phase: 03-layout-engine*
*Completed: 2026-01-29*
