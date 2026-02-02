---
phase: 11-performance-benchmarks
plan: 01
subsystem: testing
tags: [pytest-benchmark, fixtures, benchmarking]
dependency-graph:
  requires: []
  provides: [benchmark-infrastructure, pre-computed-fixtures, sized-inputs]
  affects: [11-02, 11-03, 11-04]
tech-stack:
  added: [pytest-benchmark]
  patterns: [session-scoped-fixtures, pre-computed-stage-isolation]
key-files:
  created:
    - tests/benchmarks/__init__.py
    - tests/benchmarks/conftest.py
    - tests/benchmarks/fixtures/__init__.py
    - tests/benchmarks/fixtures/small.py
    - tests/benchmarks/fixtures/medium.py
    - tests/benchmarks/fixtures/large.py
    - tests/fixtures/sample_cpp.cpp
  modified:
    - pyproject.toml
    - uv.lock
decisions: []
metrics:
  duration: 2 min
  completed: 2026-02-02
---

# Phase 11 Plan 01: Benchmark Infrastructure Summary

**One-liner:** pytest-benchmark with --benchmark-skip default and session-scoped pre-computed fixtures for isolated stage benchmarking

## What Was Done

### Task 1: Install pytest-benchmark and configure pytest
- Added `pytest-benchmark>=5.2.3` to dev dependencies via `uv add --dev`
- Added `--benchmark-skip` to pytest addopts so benchmarks never run during normal `pytest`
- Verified all 300 existing tests pass unaffected

### Task 2: Create benchmark directory structure, conftest, and fixtures
- Created `tests/benchmarks/` with `conftest.py` providing 8 session-scoped fixtures:
  - `register_fonts` (autouse): registers bundled fonts once
  - `code_samples`: dict of language -> code string for all 5 languages
  - `highlighter`: shared PygmentsHighlighter instance
  - `pre_tokenized`: dict of language -> tokenized output (pre-computed highlighting)
  - `default_config`: RenderConfig with defaults
  - `layout_engine`: LayoutEngine with PangoTextMeasurer
  - `pre_computed_metrics`: dict of language -> layout metrics
  - `sized_inputs`: dict with "small", "medium", "large" code strings
- Created `tests/fixtures/sample_cpp.cpp` (37 lines) with templates, lambdas, modern C++ features
- Created sized input fixtures: small (12 lines), medium (60 lines), large (267 lines)

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

1. `uv run pytest -x -q` -- 300 tests pass (benchmark-skip active)
2. `uv run pytest tests/benchmarks/ --co -q` -- directory discovered, 0 tests collected (expected), no errors
3. `tests/fixtures/sample_cpp.cpp` exists with 37 lines of realistic C++
4. Sized fixtures exist: small=12, medium=60, large=267 lines (all exceed minimums)
5. All 5 language fixtures present: Python, Rust, C++, JavaScript, MLIR

## Commits

| Hash | Message |
|------|---------|
| 2b8d352 | chore(11-01): install pytest-benchmark and add --benchmark-skip to addopts |
| f77ac2b | feat(11-01): create benchmark infrastructure with conftest and fixtures |

## Next Phase Readiness

Plans 11-02 through 11-04 can now use the shared conftest fixtures to benchmark individual pipeline stages (highlighting, layout, rendering) in isolation without measuring upstream work.
