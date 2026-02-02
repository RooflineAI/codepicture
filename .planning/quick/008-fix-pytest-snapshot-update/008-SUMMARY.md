# Quick Task 008 Summary

## Description
Fix `pytest --snapshot-update` — SVG visual tests crashed because `cairocffi`
could not find the Homebrew Cairo library on macOS.

## Root Cause
`cairocffi` uses `ctypes.util.find_library('cairo')` at import time, which
returns `None` on macOS because it doesn't search Homebrew's `/opt/homebrew/lib`.
This caused an `OSError` crash when `cairosvg` (which depends on `cairocffi`)
was imported in the SVG visual tests. The library was installed — just not
discoverable.

## Fix
Added auto-detection in `tests/visual/conftest.py`:
- On macOS, runs `brew --prefix cairo` to find the Homebrew Cairo prefix
- Sets `DYLD_LIBRARY_PATH` to the Cairo lib directory before `cairocffi` is imported
- Added graceful skip in `svg_to_png()` if `cairocffi` still can't load

## Additional Changes
- Regenerated all 24 visual regression baselines (padding 40px → 20px from quick-006)
- Updated README Development section with clearer setup and test instructions

## Files Changed
- `tests/visual/conftest.py` — cairocffi library path fix + graceful skip
- `tests/visual/references/*.png` — 24 regenerated baselines
- `README.md` — rewritten Development section

## Verification
- `uv run pytest tests/visual/` — 62 passed, 0 failed
- `uv run pytest --snapshot-update` — all baselines regenerated successfully

## Commit
- `3c70695`: fix(quick-008): fix cairocffi library discovery and regenerate baselines
