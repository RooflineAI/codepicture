# Phase 04 Plan 01: CairoCanvas Implementation Summary

---
phase: 04-rendering
plan: 01
subsystem: rendering
tags: [cairo, canvas, png, svg, pdf, drawing]

dependency-graph:
  requires: [03-layout]
  provides: [cairo-canvas, format-surfaces]
  affects: [04-02-window-chrome, 04-03-shadows, 04-04-rendering-tests]

tech-stack:
  added: [pillow]
  patterns: [factory-method, protocol-implementation]

key-files:
  created:
    - src/codepicture/render/__init__.py
    - src/codepicture/render/canvas.py
  modified:
    - pyproject.toml
    - src/codepicture/__init__.py

decisions:
  - id: "04-01-01"
    description: "PNG surfaces created at 2x scale with logical coordinate drawing"
  - id: "04-01-02"
    description: "SVG/PDF surfaces write to BytesIO for in-memory generation"
  - id: "04-01-03"
    description: "apply_shadow is no-op stub (Plan 04-03 implements real shadow)"

metrics:
  duration: "2 min"
  completed: "2026-01-29"
---

**One-liner:** CairoCanvas with PNG (2x HiDPI), SVG, and PDF surfaces via factory method

## What Was Built

CairoCanvas class implementing the Canvas protocol for unified drawing across output formats:

- **PNG surfaces**: Created at 2x resolution for HiDPI, with logical coordinate scaling
- **SVG surfaces**: Write to BytesIO buffer at logical dimensions
- **PDF surfaces**: Write to BytesIO buffer at logical dimensions

Drawing primitives:
- `draw_rectangle()` with optional rounded corners via arc paths
- `draw_circle()` for filled circles
- `draw_text()` returning advance width for layout
- `measure_text()` for dimension queries without rendering
- `push_clip()`/`pop_clip()` for clipping regions
- `apply_shadow()` stub (real implementation in Plan 04-03)

## Key Implementation Details

### Factory Method Pattern

```python
canvas = CairoCanvas.create(width, height, OutputFormat.PNG, scale=2.0)
```

The `create()` classmethod handles format-specific surface creation, letting callers work with a uniform interface.

### HiDPI Support

PNG surfaces are created at `width * scale` x `height * scale` resolution, with the Cairo context scaled so drawing operations use logical coordinates. This produces crisp 2x images for Retina displays.

### Rounded Rectangles

Custom `_draw_rounded_rect()` helper uses Cairo arc paths to create rounded corners, with radius clamped to half the smallest dimension.

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 37a0c16 | feat | Create render module with CairoCanvas class |
| 1edc5cb | chore | Add Pillow dependency and export CairoCanvas |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

- All 160 existing tests pass
- CairoCanvas creates PNG, SVG, PDF surfaces successfully
- PNG output has valid header (`\x89PNG`)
- SVG output contains `<svg` marker
- Text drawing returns positive advance width (42.0 for "Hello")

## Next Phase Readiness

**Ready for:** 04-02-PLAN.md (Window Chrome)

CairoCanvas provides all drawing primitives needed for window chrome rendering:
- `draw_rectangle()` for title bar background
- `draw_circle()` for traffic light buttons
- `draw_text()` for title text

Pillow is installed and ready for Plan 04-03 shadow processing.
