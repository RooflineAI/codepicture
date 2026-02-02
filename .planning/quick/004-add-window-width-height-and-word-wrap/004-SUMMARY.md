---
phase: quick-004
plan: 01
subsystem: layout-rendering
tags: [word-wrap, window-dimensions, cli, layout, rendering]
dependency-graph:
  requires: []
  provides: [window-width-height, word-wrap-rendering]
  affects: []
tech-stack:
  added: []
  patterns: [display-line-abstraction, char-map-rendering]
key-files:
  created:
    - tests/test_word_wrap.py
  modified:
    - src/codepicture/config/schema.py
    - src/codepicture/core/types.py
    - src/codepicture/layout/engine.py
    - src/codepicture/render/renderer.py
    - src/codepicture/cli/app.py
    - src/codepicture/__init__.py
    - tests/test_layout.py
decisions:
  - id: QD-004-1
    description: "DisplayLine dataclass as abstraction for visual lines (source or continuation)"
    rationale: "Clean separation between source lines and visual lines enables wrap-aware rendering without modifying token data"
  - id: QD-004-2
    description: "Empty display_lines tuple signals legacy path, non-empty signals wrap path"
    rationale: "Zero-cost backward compatibility -- renderer uses existing code when no wrapping needed"
  - id: QD-004-3
    description: "Char-map approach for token slicing in wrapped rendering"
    rationale: "Building flat (char, token_type) lists per source line avoids complex offset math when tokens span chunk boundaries"
metrics:
  duration: "4m 34s"
  completed: "2026-02-02"
---

# Quick Task 004: Window Width/Height and Word Wrap Summary

**One-liner:** VSCode-style character-level word wrapping via --width/--height CLI flags using DisplayLine abstraction

## What Was Done

### Task 1: Config fields, DisplayLine type, and word-wrap in LayoutEngine
- Added `window_width` (100-10000) and `window_height` (50-10000) optional fields to `RenderConfig`
- Created `DisplayLine` frozen dataclass: `source_line_idx`, `token_start`, `token_end`, `char_offset`, `is_continuation`
- Extended `LayoutMetrics` with `display_lines: tuple[DisplayLine, ...]` and `wrap_indent_chars: int`
- Implemented wrapping logic in `LayoutEngine.calculate_metrics`: first chunk gets full width, continuations get (max_chars - 2) chars
- When `window_width=None`, `display_lines` is empty tuple (backward compatible)
- **Commit:** `c5dea14`

### Task 2: Renderer word-wrap path and CLI flags
- Extracted `_render_legacy` method (existing rendering, untouched logic)
- Added `_render_wrapped` method using per-source-line char maps for efficient token slicing
- Continuations rendered with 2-char indent (in pixels) and no line number
- Added `--width` and `--height` CLI options to `app.py`
- **Commit:** `65efe79`

### Task 3: Comprehensive test suite
- Created `tests/test_word_wrap.py` with 9 tests across 5 test classes
- Added backward compatibility test to `tests/test_layout.py`
- Coverage: wrapping, continuations, indent reduction, canvas dimensions, content height
- **Commit:** `6e8243b`

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

1. `python -m pytest tests/ -x -q --ignore=tests/visual` -- 313 passed, 21 skipped (benchmarks)
2. `codepicture /tmp/test_wrap.py -o /tmp/out.png --width 500` -- produces wrapped image at 500px width
3. `codepicture /tmp/test_wrap.py -o /tmp/out.png` -- auto-sizing identical to before
4. `codepicture /tmp/test_wrap.py -o /tmp/out.png --width 500 --height 300` -- both dimensions honored

## Success Criteria Status

- [x] --width and --height CLI flags accepted and validated (100-10000 / 50-10000)
- [x] Lines exceeding window width wrap with VSCode-style indent on continuations
- [x] Continuation lines show NO line number in the gutter
- [x] Default behavior (no --width/--height) identical to current output
- [x] All existing tests pass unchanged
- [x] New tests cover wrapping, continuation logic, and backward compatibility
