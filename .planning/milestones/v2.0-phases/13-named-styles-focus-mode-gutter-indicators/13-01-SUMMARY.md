---
phase: 13-named-styles-focus-mode-gutter-indicators
plan: 01
subsystem: rendering
tags: [enum, highlight-styles, parser, pydantic, typer]

# Dependency graph
requires:
  - phase: 12-core-highlighting-infrastructure
    provides: parse_line_ranges, resolve_highlight_color, Color, InputError
provides:
  - HighlightStyle enum with 4 members (highlight, add, remove, focus)
  - parse_highlight_specs() for parsing "N-M:style" syntax
  - resolve_style_color() for per-style color resolution with overrides
  - DEFAULT_STYLE_COLORS, GUTTER_INDICATORS, FOCUS_DIM_OPACITY, GUTTER_BAR_WIDTH constants
  - HighlightStyleConfig model and highlights/highlight_styles config fields
  - CLI --highlight flag replacing --highlight-lines
  - Legacy migration from highlight_lines/highlight_color to new format
affects: [13-02-PLAN, 13-03-PLAN, 14-theme-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: [str-enum for style names, model_validator for legacy migration, last-wins semantics]

key-files:
  created: []
  modified:
    - src/codepicture/render/highlights.py
    - src/codepicture/config/schema.py
    - src/codepicture/cli/app.py
    - tests/test_highlights.py

key-decisions:
  - "HighlightStyle is str+Enum for easy serialization and comparison"
  - "Last-wins semantics for overlapping line specs (D-03)"
  - "Legacy migration via model_validator(mode='before') preserves backward compat"
  - "Removed --highlight-color CLI flag; per-style color customization via TOML only"

patterns-established:
  - "Named style specs: 'N-M:style' parsed by parse_highlight_specs()"
  - "Style color resolution: defaults -> TOML overrides chain"

requirements-completed: [HLSTYL-01, HLSTYL-02, HLSTYL-03, HLSTYL-04, HLSTYL-05, HLTEST-02]

# Metrics
duration: 4min
completed: 2026-03-31
---

# Phase 13 Plan 01: Named Highlight Styles Data Model Summary

**HighlightStyle enum with 4 named styles, spec parser with last-wins semantics, config schema with legacy migration, and CLI --highlight flag**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-31T07:16:16Z
- **Completed:** 2026-03-31T07:20:04Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- HighlightStyle enum (highlight/add/remove/focus) with D-12 palette colors and D-10 gutter indicators
- parse_highlight_specs() parses "N-M:style" syntax with last-wins overlap resolution
- Config schema with highlights list, highlight_styles dict, and automatic legacy migration
- CLI --highlight flag replaces --highlight-lines and --highlight-color
- 28 new unit tests (59 total) covering styles, parsing, color resolution, and constants

## Task Commits

Each task was committed atomically:

1. **Task 1: Add HighlightStyle enum, constants, and parse functions** - `fcf761b` (feat)
2. **Task 2: Update config schema and CLI flag** - `c15e29d` (feat)
3. **Task 3: Add unit tests for named styles** - `8c513cf` (test)

## Files Created/Modified
- `src/codepicture/render/highlights.py` - HighlightStyle enum, DEFAULT_STYLE_COLORS, GUTTER_INDICATORS, FOCUS_DIM_OPACITY, GUTTER_BAR_WIDTH, parse_highlight_specs(), resolve_style_color()
- `src/codepicture/config/schema.py` - HighlightStyleConfig model, highlights/highlight_styles fields, migrate_legacy_highlights validator
- `src/codepicture/cli/app.py` - --highlight flag replacing --highlight-lines, removed --highlight-color
- `tests/test_highlights.py` - 28 new tests in 6 test classes

## Decisions Made
- HighlightStyle uses str+Enum for easy string comparison and serialization
- Last-wins semantics for overlapping line specs (consistent with D-03)
- Legacy migration via model_validator(mode='before') auto-converts old fields
- Removed --highlight-color from CLI; per-style colors configured via TOML highlight_styles section

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All data types, parsing, and config ready for Plan 02 (renderer integration)
- Plan 02 can import HighlightStyle, parse_highlight_specs, resolve_style_color directly
- Plan 03 (tests) has the full API surface to test against

---
*Phase: 13-named-styles-focus-mode-gutter-indicators*
*Completed: 2026-03-31*
