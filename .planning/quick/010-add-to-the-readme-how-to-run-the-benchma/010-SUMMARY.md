---
phase: quick
plan: 010
subsystem: docs
tags: [readme, benchmarks, pytest-benchmark]

requires:
  - phase: quick-008
    provides: benchmark test infrastructure
provides:
  - "README documents how to run benchmarks locally"
affects: []

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified: [README.md]

key-decisions:
  - "Combined all three benchmark commands into a single fenced code block for compactness"

duration: 1min
completed: 2026-02-02
---

# Quick 010: Add Benchmark Instructions to README Summary

**Added "Running Benchmarks" subsection to README with commands for all benchmarks, JSON output, and single-stage runs**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-02T21:41:53Z
- **Completed:** 2026-02-02T21:42:30Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added "Running Benchmarks" subsection to Development section of README
- Documented three benchmark commands: run all, save JSON, run single stage
- Placed section logically after visual regression references

## Task Commits

1. **Task 1: Add benchmarks subsection to README Development section** - `a158e38` (docs)

## Files Created/Modified
- `README.md` - Added "Running Benchmarks" subsection with pytest-benchmark commands

## Decisions Made
- Combined all three commands (run all, JSON output, single stage) into one code block with comments, matching existing README style

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- README now documents all key development workflows (tests, visual regression, benchmarks)

---
*Phase: quick-010*
*Completed: 2026-02-02*
