---
phase: 11-performance-benchmarks
plan: 02
subsystem: benchmarks
tags: [pytest-benchmark, highlight, layout, render, performance]
dependency-graph:
  requires: [11-01]
  provides: ["per-stage benchmark tests for highlight, layout, render"]
  affects: [11-03, 11-04]
tech-stack:
  added: []
  patterns: ["parametrized benchmarks per pipeline stage", "feature toggle benchmark variants"]
file-tracking:
  key-files:
    created:
      - tests/benchmarks/test_bench_highlight.py
      - tests/benchmarks/test_bench_layout.py
      - tests/benchmarks/test_bench_render.py
    modified: []
decisions: []
metrics:
  duration: "2 min"
  completed: "2026-02-02"
---

# Phase 11 Plan 02: Per-Stage Pipeline Benchmarks Summary

Per-stage benchmark tests for highlight, layout, and render stages across 5 languages with render feature toggle variants.

## What Was Done

### Task 1: Highlight and Layout Benchmark Tests
- Created `test_bench_highlight.py` with parametrized benchmarks for 5 languages (python, rust, cpp, javascript, mlir)
- Created `test_bench_layout.py` with parametrized benchmarks for 5 languages using pre-tokenized inputs
- Both use `@pytest.mark.timeout(0)` to disable the 5s pytest-timeout during benchmarking
- Commit: `63582d5`

### Task 2: Render Benchmark Tests with Feature Toggles
- Created `test_bench_render.py` with two test sets:
  - Per-language render benchmarks (5 languages, default config)
  - Feature toggle variants (minimal, with_line_numbers, full) using Python code
- Feature toggle tests re-compute metrics per config since layout depends on config settings
- Commit: `43ca5ea`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed invalid RenderConfig field name `show_chrome`**
- **Found during:** Task 2
- **Issue:** Plan specified `show_chrome` as a RenderConfig field, but the actual field is `window_controls`
- **Fix:** Replaced `show_chrome` with `window_controls` in all FEATURE_CONFIGS entries
- **Files modified:** tests/benchmarks/test_bench_render.py
- **Commit:** 43ca5ea

## Verification Results

- 18 benchmark tests across 3 files (5 highlight + 5 layout + 5 render + 3 feature toggle)
- All benchmarks produce statistical output (min, max, mean, stddev, rounds, OPS)
- Each stage benchmarked independently using pre-computed inputs from prior stages
- Regular pytest run unaffected (benchmarks skipped by default)

## Key Observations

Benchmark results from verification run:
- **Highlight:** javascript fastest (~88us), cpp/mlir slowest (~1.1-1.5ms) due to complex grammars
- **Layout:** javascript fastest (~4.5us), cpp slowest (~14us) -- layout is very fast overall
- **Render:** javascript fastest (~10ms), cpp/mlir slowest (~69-71ms) due to more tokens
- **Feature toggles:** minimal (~10.2ms) vs full (~11.3ms) -- ~10% overhead from chrome/shadow/line numbers

## Next Phase Readiness

All 18 per-stage benchmarks operational. Ready for remaining Phase 11 plans.
