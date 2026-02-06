---
phase: 12-core-highlighting-infrastructure
plan: 01
subsystem: render
tags: [highlighting, parser, color, tdd, pure-functions]

# Dependency graph
requires: []
provides:
  - "parse_line_ranges() - converts user line specs to 0-based indices"
  - "resolve_highlight_color() - resolves hex color or returns default"
  - "DEFAULT_HIGHLIGHT_COLOR - warm yellow #FFE65040"
  - "HIGHLIGHT_CORNER_RADIUS - sharp rect constant for renderer"
affects: [12-02, 12-03, 12-04, 13, 14]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure function module in render/ for highlight logic"
    - "Regex validation before parsing line specs"
    - "DEFAULT_HIGHLIGHT_ALPHA=64 constant for 6-char hex fallback"

key-files:
  created:
    - "src/codepicture/render/highlights.py"
    - "tests/test_highlights.py"
  modified: []

key-decisions:
  - "DEFAULT_HIGHLIGHT_COLOR = Color(r=255, g=230, b=80, a=64) -- warm yellow at ~25% opacity"
  - "DEFAULT_HIGHLIGHT_ALPHA = 64 shared by both default color and 6-char hex fallback"
  - "HIGHLIGHT_CORNER_RADIUS = 0 exported for future phase flexibility"
  - "Regex pre-validation before int parsing for clear error messages"

patterns-established:
  - "Pure function highlight module: no classes, no state, just parse_line_ranges() and resolve_highlight_color()"
  - "InputError raised for all user-input validation failures (out-of-bounds, bad syntax, reversed ranges)"

# Metrics
duration: 2min
completed: 2026-02-06
---

# Phase 12 Plan 01: Line Range Parser and Highlight Color Resolver Summary

**Pure-function line range parser and highlight color resolver via TDD with 31 tests covering singles, ranges, offsets, error cases, and color resolution**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-06T21:05:49Z
- **Completed:** 2026-02-06T21:08:14Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files created:** 2

## Accomplishments
- `parse_line_ranges()` converts user-facing line numbers to 0-based source indices with full validation
- `resolve_highlight_color()` handles None (default yellow), #RRGGBB (adds 25% alpha), and #RRGGBBAA (explicit alpha)
- 31 unit tests covering single lines, ranges, mixed input, empty input, whitespace, non-default offsets, and all error cases
- All edge cases raise `InputError` with descriptive messages including valid range info

## Task Commits

Each task was committed atomically:

1. **RED - Failing tests** - `1c0febf` (test)
2. **GREEN - Implementation** - `ff4ecc0` (feat)

_TDD plan: RED produced failing tests, GREEN made all 31 pass. No REFACTOR needed -- code was clean on first pass._

## Files Created/Modified
- `src/codepicture/render/highlights.py` - Line range parser, color resolver, constants (parse_line_ranges, resolve_highlight_color, DEFAULT_HIGHLIGHT_COLOR, HIGHLIGHT_CORNER_RADIUS)
- `tests/test_highlights.py` - 31 unit tests across 8 test classes

## Decisions Made
- Used `DEFAULT_HIGHLIGHT_ALPHA = 64` as a shared constant for both the default color and the 6-char hex fallback, ensuring consistent opacity behavior
- Pre-compiled regex `_LINE_SPEC_RE` for spec validation before attempting integer parsing, producing clearer error messages for malformed input
- No refactor phase needed -- implementation was clean and well-structured on first pass

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered
- ruff-format reformatted the implementation file on first commit attempt (pre-commit hook). Re-staged and committed successfully on second attempt.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness
- `parse_line_ranges()` and `resolve_highlight_color()` ready for use by Plan 12-02 (config schema) and Plan 12-03 (renderer integration)
- `HIGHLIGHT_CORNER_RADIUS` exported for Plan 12-03 renderer to use
- All 406 project tests pass (31 new + 375 existing), no regressions

---
*Phase: 12-core-highlighting-infrastructure*
*Completed: 2026-02-06*
