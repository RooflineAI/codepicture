---
phase: 03-layout-engine
plan: 02
subsystem: layout
tags: [layout, rendering, canvas, typography, metrics]

# Dependency graph
requires:
  - phase: 03-01
    provides: PangoTextMeasurer for text dimension calculations
  - phase: 01-01
    provides: Core types (dataclasses, protocols)
  - phase: 02-01
    provides: TokenInfo for tokenized lines
provides:
  - LayoutMetrics frozen dataclass with all rendering dimensions
  - LayoutEngine.calculate_metrics() for canvas calculations
  - LayoutError exception for empty input handling
  - Dynamic gutter width calculation for any line count
affects: [03-03, 04-renderer]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Dependency injection for TextMeasurer protocol
    - Frozen dataclass for layout state
    - Layout calculations before rendering

key-files:
  created:
    - src/codepicture/layout/engine.py
  modified:
    - src/codepicture/core/types.py
    - src/codepicture/errors.py
    - src/codepicture/core/__init__.py
    - src/codepicture/layout/__init__.py
    - src/codepicture/__init__.py

key-decisions:
  - "LINE_NUMBER_GAP constant (12px) for gutter spacing from CONTEXT.md"
  - "Baseline offset approximated at 0.8 * char_height"
  - "Gutter width measured using actual digit characters for accuracy"

patterns-established:
  - "LayoutMetrics as complete render state: all dimensions pre-calculated"
  - "LayoutEngine takes measurer + config, returns metrics"

# Metrics
duration: 4min
completed: 2026-01-29
---

# Phase 3 Plan 2: Layout Engine Implementation Summary

**LayoutEngine calculates canvas dimensions and element positions from tokenized code using TextMeasurer and RenderConfig**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-29T02:40:00Z
- **Completed:** 2026-01-29T02:44:25Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- LayoutMetrics frozen dataclass with 14 layout fields (canvas, content, gutter, code, typography)
- LayoutEngine.calculate_metrics() produces complete render layout
- Dynamic gutter width scales with line count (tested 10, 100, 1000+ lines)
- Line height multiplier correctly applied to typography calculations
- Empty input raises LayoutError with helpful message

## Task Commits

Each task was committed atomically:

1. **Task 1: Add LayoutMetrics dataclass and LayoutError** - `daf9732` (feat)
2. **Task 2: Implement LayoutEngine** - `ab9b7e9` (feat)

## Files Created/Modified
- `src/codepicture/layout/engine.py` - LayoutEngine class with calculate_metrics()
- `src/codepicture/core/types.py` - Added LayoutMetrics frozen dataclass
- `src/codepicture/errors.py` - Added LayoutError exception
- `src/codepicture/core/__init__.py` - Export LayoutMetrics
- `src/codepicture/layout/__init__.py` - Export LayoutEngine
- `src/codepicture/__init__.py` - Public API exports for LayoutEngine, LayoutMetrics, LayoutError

## Decisions Made
- LINE_NUMBER_GAP set to 12px (from CONTEXT.md)
- Baseline offset approximated at 80% of character height (standard approximation)
- Gutter width measured using "0" digits repeated for accuracy with monospace fonts

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- LayoutEngine ready for integration with renderer
- 03-03 (Layout Tests) can verify all calculations
- Complete layout pipeline: PangoTextMeasurer -> LayoutEngine -> LayoutMetrics

---
*Phase: 03-layout-engine*
*Completed: 2026-01-29*
