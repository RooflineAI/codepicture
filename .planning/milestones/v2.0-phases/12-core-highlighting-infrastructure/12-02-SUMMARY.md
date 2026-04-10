---
phase: 12-core-highlighting-infrastructure
plan: 02
subsystem: config
tags: [pydantic, typer, highlight, validation, cli]

# Dependency graph
requires:
  - phase: none
    provides: existing RenderConfig and CLI app
provides:
  - highlight_lines and highlight_color fields on RenderConfig with format validators
  - --highlight-lines and --highlight-color CLI flags wired into cli_overrides
  - TOML highlight_lines and highlight_color field loading
affects: [12-03, 12-04, 13, 14]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pydantic field_validator for highlight_color: #RRGGBB/#RRGGBBAA only (no #RGB)"
    - "Pydantic field_validator for highlight_lines: N or N-M format strings, auto-converts integers"
    - "Typer list[str] | None for repeatable CLI options"

key-files:
  created: []
  modified:
    - src/codepicture/config/schema.py
    - src/codepicture/cli/app.py

key-decisions:
  - "highlight_color rejects #RGB format (3-char hex is ambiguous for alpha channel)"
  - "highlight_lines validator converts integers to strings for TOML compatibility"
  - "Format validation only in validators; range resolution deferred to render time"

patterns-established:
  - "Highlight config stored as user intent strings, not resolved indices"
  - "Repeatable CLI flag via list[str] | None Typer annotation"

# Metrics
duration: 2min
completed: 2026-02-06
---

# Phase 12 Plan 02: Highlight Config and CLI Summary

**RenderConfig highlight_lines/highlight_color fields with Pydantic validators, plus --highlight-lines/--highlight-color CLI flags wired through cli_overrides**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-06T21:06:24Z
- **Completed:** 2026-02-06T21:08:47Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added highlight_lines (list[str] | None) and highlight_color (str | None) fields to RenderConfig with None defaults
- Added format validators: highlight_color accepts only #RRGGBB/#RRGGBBAA, highlight_lines accepts only N or N-M specs
- Added --highlight-lines (repeatable) and --highlight-color CLI flags to Typer app
- Wired both flags into cli_overrides dict for config loading pipeline
- Verified TOML loading works end-to-end via load_config

## Task Commits

Each task was committed atomically:

1. **Task 1: Add highlight fields to RenderConfig** - `1119387` (feat)
2. **Task 2: Add CLI flags for highlight-lines and highlight-color** - `371f1a1` (feat)

## Files Created/Modified
- `src/codepicture/config/schema.py` - Added highlight_lines and highlight_color fields with field_validators
- `src/codepicture/cli/app.py` - Added --highlight-lines and --highlight-color CLI flags and cli_overrides wiring

## Decisions Made
- highlight_color rejects #RGB (3-char hex) because it is ambiguous for alpha channel specification; only #RRGGBB and #RRGGBBAA accepted
- highlight_lines validator auto-converts integers to strings so TOML integer arrays (e.g. `[3, 12]`) work alongside string arrays
- Validators check FORMAT validity only; resolution to 0-based indices deferred to render time when total_lines is known (keeps config serializable)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- RenderConfig now carries highlight fields, ready for Plan 03 (renderer integration) to read them
- CLI flags are live, values flow through the full config loading pipeline
- TOML config fields work automatically via existing model_validate path

---
*Phase: 12-core-highlighting-infrastructure*
*Completed: 2026-02-06*
