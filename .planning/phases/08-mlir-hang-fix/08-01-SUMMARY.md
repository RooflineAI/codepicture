---
phase: 08-mlir-hang-fix
plan: 01
subsystem: performance
tags: [font-caching, mlir-lexer, cairo, lru-cache]
depends:
  requires: [phase-06, phase-07]
  provides: [cached-font-resolution, mlir-identifier-tokenization, canvas-font-caching]
  affects: [phase-08-plan-02, phase-09, phase-11]
tech-stack:
  added: []
  patterns: [lru_cache-for-expensive-lookups, instance-level-font-caching]
key-files:
  created: []
  modified:
    - src/codepicture/fonts/__init__.py
    - src/codepicture/highlight/mlir_lexer.py
    - src/codepicture/render/canvas.py
decisions:
  - id: DEC-22
    summary: "Use functools.lru_cache(maxsize=16) for resolve_font_family"
    rationale: "Eliminates repeated manimpango.list_fonts() calls which are O(system fonts) each"
  - id: DEC-23
    summary: "Instance-level _current_font caching in CairoCanvas"
    rationale: "Avoids redundant select_font_face/set_font_size per token when font unchanged"
metrics:
  duration: "2 min"
  completed: 2026-01-30
---

# Phase 08 Plan 01: Cache Font Resolution and Fix MLIR Lexer Summary

**One-liner:** lru_cache on resolve_font_family + MLIR catch-all identifier rule + CairoCanvas font caching drops test.mlir render from ~40s hang to 0.22s

## What Was Done

### Task 1: Cache resolve_font_family() and add MLIR lexer catch-all
- Added `@functools.lru_cache(maxsize=16)` to `resolve_font_family()` in fonts/__init__.py -- this is the primary fix, eliminating repeated `manimpango.list_fonts()` system calls
- Added `(r"\.\.\.", Punctuation)` rule for MLIR ellipsis syntax
- Added `(r"[a-zA-Z_][\w]*", Name)` catch-all identifier rule after all specific keyword/type/builtin rules
- MLIR Error tokens dropped from many to 0

### Task 2: Cache font setup in CairoCanvas.draw_text()
- Added `_current_font` slot to CairoCanvas
- Both `draw_text()` and `measure_text()` now skip redundant `select_font_face`/`set_font_size` calls when font is unchanged
- Combined with Task 1's lru_cache, test.mlir renders in 0.22s

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 3fa193a | feat | Cache resolve_font_family() and add MLIR lexer catch-all |
| 148c034 | perf | Cache font setup in CairoCanvas draw_text and measure_text |

## Verification Results

- All 260 tests pass (1.77s)
- 59 highlight tests pass (0.07s)
- test.mlir: 201 tokens, 0 Error tokens
- test.mlir renders in 0.22s (budget: 5s)
- Output: 175,091 bytes PNG

## Deviations from Plan

None -- plan executed exactly as written.

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| DEC-22 | lru_cache(maxsize=16) for resolve_font_family | Both args are strings (hashable); 16 slots covers all realistic font variations |
| DEC-23 | Instance-level _current_font tuple caching | Avoids Cairo API overhead per-token; resets naturally per canvas instance |

## Next Phase Readiness

Plan 08-02 (MLIR test corpus and regression tests) can proceed immediately. The rendering pipeline is now performant for MLIR files. No blockers.
