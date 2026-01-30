---
phase: 10-visual-regression-reliability
plan: 01
subsystem: testing
tags: [visual-regression, pixelmatch, cairosvg, pymupdf, testing-infrastructure]
depends_on: []
provides: [compare_images, svg_to_png, pdf_to_png, render_fixture, snapshot-update-flag, visual-fixtures]
affects: [10-02, 10-03, 10-04]
tech-stack:
  added: [pixelmatch, cairosvg, pymupdf]
  patterns: [snapshot-comparison, composite-diff-output]
key-files:
  created:
    - tests/visual/__init__.py
    - tests/visual/conftest.py
    - tests/visual/fixtures/python_visual.py
    - tests/visual/fixtures/rust_visual.rs
    - tests/visual/fixtures/cpp_visual.cpp
    - tests/visual/fixtures/javascript_visual.js
    - tests/visual/fixtures/mlir_visual.mlir
  modified:
    - pyproject.toml
    - tests/conftest.py
decisions: []
metrics:
  duration: 3 min
  completed: 2026-01-31
---

# Phase 10 Plan 01: VRT Infrastructure & Fixtures Summary

**One-liner:** Pixelmatch-based image comparison with cairosvg/pymupdf rasterizers and 5 language fixture files for visual regression testing.

## What Was Done

### Task 1: Install VRT dependencies and create visual fixture files
- Added pixelmatch, cairosvg, and pymupdf as dev dependencies via `uv add --dev`
- Created `tests/visual/` package with `__init__.py`
- Created 5 purpose-built visual fixture files covering key syntax constructs:
  - **Python** — function def, type hints, docstring, list ops, f-string comment
  - **Rust** — doc comment, match expression, macro invocation, string interpolation
  - **C++** — includes, template, range-based for, const ref
  - **JavaScript** — async/await, try/catch, default params, arrow-like patterns
  - **MLIR** — func.func, memref types, affine.for, arith.constant

### Task 2: Build image comparison infrastructure and pytest --snapshot-update flag
- Added `--snapshot-update` CLI option via `pytest_addoption` in root `tests/conftest.py`
- Created `tests/visual/conftest.py` with:
  - **Fixtures:** `snapshot_update`, `visual_fixtures_dir`, `references_dir`, `diff_output_dir`
  - **`compare_images()`** — pixelmatch-based comparison returning `(bool, float)` with configurable threshold and fail_percent; generates composite diff on failure
  - **`build_composite()`** — creates expected|actual|diff side-by-side PNG with labels
  - **`svg_to_png()`** — rasterizes SVG bytes to Pillow RGBA via cairosvg
  - **`pdf_to_png()`** — rasterizes first PDF page to Pillow RGBA via pymupdf
  - **`render_fixture()`** — runs full codepicture pipeline (fonts, highlight, layout, render) returning raw bytes without writing to disk

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

1. `import pixelmatch; import cairosvg; import pymupdf` — all import successfully (cairosvg requires DYLD_LIBRARY_PATH on macOS due to cairocffi needing the Homebrew cairo library path)
2. All 5 fixture files exist under `tests/visual/fixtures/`
3. `compare_images`, `svg_to_png`, `pdf_to_png`, `render_fixture` all importable from `tests.visual.conftest`
4. `--snapshot-update` flag recognized by pytest
5. All 300 existing tests pass

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 798b051 | Install VRT dependencies and create visual fixture files |
| 2 | 052900c | Build image comparison infrastructure and snapshot-update flag |

## Next Phase Readiness

Plan 10-02 (core snapshot tests) can proceed — all infrastructure is in place:
- compare_images() ready for use in test assertions
- render_fixture() returns raw bytes for any fixture + config combination
- svg_to_png() and pdf_to_png() enable vector format testing
- --snapshot-update flag available for regenerating reference images
