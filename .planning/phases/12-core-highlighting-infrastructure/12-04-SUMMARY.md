---
phase: 12-core-highlighting-infrastructure
plan: 04
subsystem: testing
tags: [highlighting, cli-tests, visual-regression, integration-tests, baselines]

# Dependency graph
requires:
  - phase: 12-01
    provides: "parse_line_ranges(), resolve_highlight_color() pure functions"
  - phase: 12-02
    provides: "RenderConfig.highlight_lines, highlight_color fields + CLI flags"
  - phase: 12-03
    provides: "Highlight rectangle drawing in both render paths"
provides:
  - "CLI integration tests for --highlight-lines and --highlight-color flags"
  - "Visual regression baselines for 8 highlight variants (PNG/SVG/PDF)"
  - "Integration tests for highlight rendering pipeline including word-wrap"
affects: [13, 14]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Highlight CLI tests use multi-line fixture (5 lines) for range/out-of-bounds testing"
    - "Visual regression highlight variants follow CONFIG_VARIANTS pattern exactly"
    - "Integration tests use direct pipeline (highlighter->layout->renderer) not CLI"

key-files:
  created:
    - tests/test_highlights_integration.py
  modified:
    - tests/test_cli.py
    - tests/visual/test_visual_regression.py

key-decisions:
  - "Multi-line fixture (5 lines) for highlight CLI tests to exercise ranges and out-of-bounds"
  - "Visual regression highlight-wrap variant uses window_width=400 to force wrap on Python fixture"
  - "Cross-format highlight tests use highlight_lines=['3'] as canonical single-line highlight"
  - "Integration no-change tests compare raw bytes (PNG output) for empty vs None vs no highlights"

patterns-established:
  - "Highlight visual regression: python_png_{variant} naming for highlight variants"
  - "Highlight cross-format: python_{format}_highlight-default naming for format variants"

# Metrics
duration: 5min
completed: 2026-02-06
---

# Phase 12 Plan 04: End-to-End Highlight Tests Summary

**CLI integration tests for highlight flags, visual regression baselines across PNG/SVG/PDF, and pipeline integration tests for word-wrap + highlight interactions**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-06T21:16:47Z
- **Completed:** 2026-02-06T21:21:58Z
- **Tasks:** 2
- **Files modified:** 3 (+ 8 reference images created)

## Accomplishments
- 8 CLI integration tests covering single line, multiple lines, custom color (8-char and 6-char hex), out-of-bounds error, invalid syntax error, invalid color error, and TOML config loading
- 8 visual regression baselines: 5 highlight variants (single, range, mixed, custom color, word-wrap) + 3 cross-format (PNG/SVG/PDF)
- 5 integration tests: basic highlight render, word-wrap + highlight, all-lines highlight, empty list no-change, None no-change
- Full test suite: 427 passed, 21 skipped, 0 failures

## Task Commits

Each task was committed atomically:

1. **Task 1: Add CLI integration tests for highlight flags** - `476ed46` (test)
2. **Task 2: Add visual regression and integration tests for highlights** - `ce74bbd` (test)

## Files Created/Modified
- `tests/test_cli.py` - Added TestCliHighlightLines class with 8 tests and multiline_py fixture
- `tests/visual/test_visual_regression.py` - Added HIGHLIGHT_VARIANTS (5 variants), HIGHLIGHT_FORMATS cross-format test (3 formats)
- `tests/test_highlights_integration.py` - New file with 5 integration tests exercising full render pipeline
- `tests/visual/references/python_png_highlight-*.png` - 6 PNG reference baselines for highlight variants
- `tests/visual/references/python_svg_highlight-default.png` - SVG highlight baseline
- `tests/visual/references/python_pdf_highlight-default.png` - PDF highlight baseline

## Decisions Made
- Used a dedicated 5-line multiline_py fixture for highlight CLI tests (existing sample_py is single-line, insufficient for range/out-of-bounds testing)
- Visual regression highlight-wrap variant uses window_width=400 to force word wrapping on the Python fixture's longer lines
- Cross-format tests use highlight_lines=["3"] as the canonical single-line test case across all 3 formats
- Integration no-change tests compare raw PNG bytes directly to verify empty/None highlights produce identical output

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered
- ruff-format reformatted multi-line string in multiline_py fixture to single-line concatenation (cosmetic, auto-fixed by pre-commit hook)
- ruff removed unused `Path` and `register_bundled_fonts` imports from integration test file (auto-fixed by pre-commit hook)

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness
- Phase 12 (Core Highlighting Infrastructure) is now complete: all 4 plans delivered
- Full highlight pipeline tested end-to-end: parser (31 unit tests), config (validation), CLI (8 tests), renderer (visual baselines), integration (5 tests)
- Ready for Phase 13 (Highlight Style Refinements) and Phase 14 (Theme Integration)
- All 427 project tests pass, no regressions

---
*Phase: 12-core-highlighting-infrastructure*
*Completed: 2026-02-06*
