---
phase: 13-named-styles-focus-mode-gutter-indicators
plan: 02
subsystem: rendering
tags: [highlight-styles, focus-mode, gutter-indicators, renderer, layout]

# Dependency graph
requires:
  - phase: 13-named-styles-focus-mode-gutter-indicators
    plan: 01
    provides: HighlightStyle, parse_highlight_specs, resolve_style_color, constants
provides:
  - Per-style colored highlight backgrounds in renderer
  - Focus mode dimming (35% opacity) for unfocused lines
  - Gutter indicators (+/- text, colored bar) between line numbers and code
  - LayoutMetrics gutter_indicator_x/gutter_indicator_width fields
  - Layout engine gutter indicator column reservation
affects: [13-03-PLAN, 14-theme-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: [pre-computed indicator colors, focus dimming via _dim_color helper]

key-files:
  created: []
  modified:
    - src/codepicture/core/types.py
    - src/codepicture/layout/engine.py
    - src/codepicture/render/renderer.py

key-decisions:
  - "Gutter indicator fields placed after baseline_offset (with defaults) to preserve dataclass ordering"
  - "GUTTER_INDICATOR_WIDTH = 14px module constant in layout engine"
  - "Indicator colors pre-computed at high opacity (~90%) for visibility on small gutter elements"
  - "Color import moved from TYPE_CHECKING to runtime for _dim_color function"

patterns-established:
  - "Focus dimming via _dim_color(color, FOCUS_DIM_OPACITY) on unfocused lines"
  - "Gutter indicators only drawn on highlighted lines (no dimming needed)"
  - "Layout engine reads config.highlights to determine gutter column reservation"

requirements-completed: [HLFOC-01, HLFOC-02, HLFOC-03, HLGUT-01, HLGUT-02]

# Metrics
duration: 3min
completed: 2026-03-31
---

# Phase 13 Plan 02: Renderer Integration for Named Styles, Focus Mode, and Gutter Indicators Summary

**Per-style highlight rendering with focus dimming at 35% opacity and +/-/bar gutter indicators in both legacy and wrapped render paths**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-31T07:23:52Z
- **Completed:** 2026-03-31T07:27:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- LayoutMetrics extended with gutter_indicator_x and gutter_indicator_width fields (default 0.0)
- Layout engine conditionally reserves 14px gutter indicator column when highlights active + line numbers on
- Renderer uses parse_highlight_specs for per-style highlight resolution (replacing parse_line_ranges)
- Per-style colored highlight rectangles drawn in both legacy and wrapped paths
- Focus mode detection: any HighlightStyle.FOCUS triggers dimming of unfocused lines
- _dim_color helper applies FOCUS_DIM_OPACITY (0.35) to line numbers and code tokens on unfocused lines
- Gutter indicators: "+" for add, "-" for remove, colored bar for highlight/focus styles
- Gutter indicator colors pre-computed at high opacity for visibility
- Wrapped path: gutter indicators only on non-continuation display lines

## Task Commits

Each task was committed atomically:

1. **Task 1: Add gutter indicator fields to LayoutMetrics and update layout engine** - `bbf5ac8` (feat)
2. **Task 2: Update renderer for per-style highlights, focus dimming, and gutter indicators** - `2d7deb3` (feat)

## Files Created/Modified
- `src/codepicture/core/types.py` - Added gutter_indicator_x, gutter_indicator_width fields to LayoutMetrics
- `src/codepicture/layout/engine.py` - GUTTER_INDICATOR_WIDTH constant, conditional column reservation in calculate_metrics
- `src/codepicture/render/renderer.py` - Per-style highlights, _dim_color, focus dimming, gutter indicators in both render paths

## Decisions Made
- Gutter indicator fields placed after baseline_offset with defaults to preserve dataclass field ordering
- GUTTER_INDICATOR_WIDTH = 14px as module-level constant
- Indicator colors pre-computed at ~90% opacity (scaled from base alpha) for small gutter elements
- Color import moved from TYPE_CHECKING to runtime since _dim_color needs it at execution time

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Dataclass field ordering for gutter_indicator fields**
- **Found during:** Task 1
- **Issue:** Plan placed default fields (gutter_indicator_x=0.0) before non-default fields (code_x), which causes dataclass TypeError
- **Fix:** Moved gutter_indicator fields after baseline_offset (last non-default field), before display_lines
- **Files modified:** src/codepicture/core/types.py
- **Commit:** bbf5ac8

**2. [Rule 1 - Bug] Color import behind TYPE_CHECKING**
- **Found during:** Task 2
- **Issue:** Color was only imported under TYPE_CHECKING but _dim_color function needs it at runtime
- **Fix:** Moved Color to regular imports from codepicture.core.types
- **Files modified:** src/codepicture/render/renderer.py
- **Commit:** 2d7deb3

**3. [Rule 3 - Blocking] Plan 01 changes not in worktree**
- **Found during:** Pre-execution
- **Issue:** Worktree branch was behind main, missing Plan 01 commits (HighlightStyle, parse_highlight_specs, etc.)
- **Fix:** Merged main into worktree branch (fast-forward)
- **Files modified:** N/A (git merge)

## Known Pre-existing Issues
- TestCliHighlightLines tests fail because Plan 01 renamed --highlight-lines to --highlight but CLI tests not updated (out of scope for this plan, tracked for Plan 03)

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All rendering integration complete for Plan 03 (end-to-end tests)
- Both legacy and wrapped paths support per-style highlights, focus dimming, gutter indicators
- Layout engine correctly reserves/omits gutter column based on highlight presence

---
*Phase: 13-named-styles-focus-mode-gutter-indicators*
*Completed: 2026-03-31*
