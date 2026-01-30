---
phase: 10-visual-regression-reliability
plan: 02
subsystem: testing
tags: [visual-regression, snapshot-testing, parametrized-tests, reference-images]
depends_on: [10-01]
provides: [visual-regression-tests, reference-images, config-variant-tests]
affects: [10-03, 10-04]
tech-stack:
  added: []
  patterns: [snapshot-comparison, parametrized-matrix-testing]
key-files:
  created:
    - tests/visual/test_visual_regression.py
    - tests/visual/references/.gitkeep
    - tests/visual/references/python_png_default.png
    - tests/visual/references/rust_png_default.png
    - tests/visual/references/cpp_png_default.png
    - tests/visual/references/javascript_png_default.png
    - tests/visual/references/mlir_png_default.png
    - tests/visual/references/python_svg_default.png
    - tests/visual/references/rust_svg_default.png
    - tests/visual/references/cpp_svg_default.png
    - tests/visual/references/javascript_svg_default.png
    - tests/visual/references/mlir_svg_default.png
    - tests/visual/references/python_pdf_default.png
    - tests/visual/references/rust_pdf_default.png
    - tests/visual/references/cpp_pdf_default.png
    - tests/visual/references/javascript_pdf_default.png
    - tests/visual/references/mlir_pdf_default.png
    - tests/visual/references/python_png_shadow-off.png
    - tests/visual/references/python_png_chrome-off.png
    - tests/visual/references/python_png_lines-off.png
    - tests/visual/references/python_png_shadow-off_chrome-off.png
    - tests/visual/references/python_png_shadow-off_chrome-off_lines-off.png
  modified: []
decisions: []
metrics:
  duration: 3 min
  completed: 2026-01-31
---

# Phase 10 Plan 02: Core Snapshot Tests & Reference Images Summary

**One-liner:** 20 parametrized visual regression tests (5 languages x 3 formats + 5 config variants) with pixelmatch comparison against stored reference PNGs.

## What Was Done

### Task 1: Create parametrized visual regression tests and generate initial reference images
- Created `tests/visual/test_visual_regression.py` with `test_visual_regression` parametrized over 5 languages (Python, Rust, C++, JavaScript, MLIR) x 3 formats (PNG, SVG, PDF)
- Reference naming convention: `{language}_{format}_default.png` (SVG/PDF rasterized to PNG for comparison)
- Helper function `_render_to_image()` handles format-specific conversion (PNG direct, SVG via cairosvg, PDF via pymupdf)
- Auto-generates missing references on first run; `--snapshot-update` regenerates all
- All 15 core tests pass with 0.0000% pixel mismatch
- Marked with `@pytest.mark.timeout(30)` to handle rendering time

### Task 2: Create config variant visual tests
- Added `test_visual_config_variant` parametrized over 5 feature toggle combinations:
  - shadow-off, chrome-off, lines-off, shadow-off+chrome-off, shadow-off+chrome-off+lines-off
- Uses Python fixture in PNG format only (keeps matrix manageable)
- Generated 5 additional reference images (total: 20)
- All 5 variant tests pass with 0.0000% pixel mismatch

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

1. `ls tests/visual/references/*.png | wc -l` — 20 reference images
2. `uv run pytest tests/visual/test_visual_regression.py -v` — all 20 tests pass
3. `--snapshot-update` regenerates all references (15 skipped on first run, 5 skipped on variant run)
4. All 300 existing tests pass unaffected

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 52e5d0f | Create parametrized visual regression tests with 15 reference images |
| 2 | 8fca743 | Add config variant visual tests for feature toggle combinations |

## Next Phase Readiness

Plan 10-03 (deliberate change detection / diff artifact tests) can proceed:
- 20 reference images available for comparison
- compare_images() produces composite diff artifacts on mismatch
- Test infrastructure proven with 0% false positive rate
