---
phase: quick
plan: 003
subsystem: render
tags: [cairo, pillow, bgra, rgba, png, shadow, colour]

# Dependency graph
requires:
  - phase: 04-shadow
    provides: Shadow post-processing pipeline for PNG output
provides:
  - Correct BGRA-to-RGBA channel conversion in shadow pipeline
  - Colour preservation regression tests
affects: [visual-regression, render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cairo BGRA byte order requires explicit B<->R channel swap after Pillow un-premultiplication"

key-files:
  created: []
  modified:
    - src/codepicture/render/shadow.py
    - tests/test_render_shadow.py
    - tests/visual/references/*.png

key-decisions:
  - "Two-step conversion: RGBa for un-premultiplication then channel swap, since Pillow has no BGRa mode"

patterns-established:
  - "Cairo-to-Pillow conversion: always swap B and R channels after RGBa un-premultiplication"

# Metrics
duration: 3min
completed: 2026-02-02
---

# Quick 003: Fix PNG Colour Difference vs SVG/PDF Summary

**Fixed BGRA-to-RGBA channel swap in shadow pipeline so PNG output colours match SVG/PDF**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-02T20:09:44Z
- **Completed:** 2026-02-02T20:12:28Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Fixed red/blue channel swap in PNG output caused by Cairo's BGRA byte order
- Added 3 regression tests verifying colour preservation through shadow pipeline
- Updated all 10 PNG visual regression baselines to reflect correct colours

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix BGRA channel swap in shadow.py** - `e46bd71` (fix)
2. **Task 2: Add colour preservation regression test** - `ccb38a6` (test)

Additional commit from deviation:

3. **Update visual regression baselines** - `bab65cc` (fix)

## Files Created/Modified
- `src/codepicture/render/shadow.py` - Added B<->R channel swap after RGBa un-premultiplication
- `tests/test_render_shadow.py` - Added TestShadowColorPreservation with 3 regression tests
- `tests/visual/references/*_png_*.png` - 10 PNG baselines regenerated with correct colours

## Decisions Made
- Used two-step approach (RGBa un-premultiplication then channel swap) since Pillow has no "BGRa" mode for pre-multiplied BGRA data
- Only the shadow-enabled path needed fixing; the shadow-disabled path uses Cairo's write_to_png which handles BGRA internally

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated visual regression baselines**
- **Found during:** Verification (full test suite)
- **Issue:** PNG visual regression tests failed because baselines were generated with old buggy BGRA code
- **Fix:** Regenerated all 10 PNG reference snapshots using --snapshot-update
- **Files modified:** 10 files in tests/visual/references/
- **Verification:** All PNG visual regression tests pass
- **Committed in:** `bab65cc`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Baseline update was necessary consequence of the colour fix. No scope creep.

## Issues Encountered
- SVG visual regression tests fail due to missing cairosvg library in this environment -- pre-existing issue, not related to this change

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- PNG colour output is now correct and verified
- All existing tests pass (excluding pre-existing SVG environment issue)

---
*Phase: quick-003*
*Completed: 2026-02-02*
