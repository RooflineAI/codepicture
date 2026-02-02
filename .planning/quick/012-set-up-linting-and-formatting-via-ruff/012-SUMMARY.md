---
phase: quick-012
plan: 01
subsystem: tooling
tags: [ruff, linting, formatting, pre-commit, code-quality]

# Dependency graph
requires: []
provides:
  - "ruff linter and formatter configured in pyproject.toml"
  - "pre-commit hooks for automatic lint/format on every commit"
  - "all Python files passing ruff check and ruff format"
affects: [all-future-development]

# Tech tracking
tech-stack:
  added: [ruff>=0.9, pre-commit>=4.0]
  patterns: [pre-commit hooks for code quality, ruff as unified linter+formatter]

key-files:
  created: [.pre-commit-config.yaml]
  modified: [pyproject.toml]

key-decisions:
  - "Selected E, F, W, I, UP, B, SIM, RUF rule sets for comprehensive but not overly strict linting"
  - "Excluded visual fixture files from ruff to preserve baseline image integrity"
  - "Used per-file-ignores for Pygments lexer (RUF012) and benchmark fixtures instead of blanket ignores"

patterns-established:
  - "Pre-commit hooks: ruff check --fix and ruff format run on every commit"
  - "Visual fixtures excluded from formatting to prevent baseline drift"

# Metrics
duration: 7min
completed: 2026-02-02
---

# Quick Task 012: Set Up Linting and Formatting via Ruff Summary

**Ruff linter+formatter with 8 rule sets, pre-commit hooks, and 109 lint issues fixed across 48 files**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-02T21:51:46Z
- **Completed:** 2026-02-02T21:59:08Z
- **Tasks:** 2
- **Files modified:** 48

## Accomplishments
- Configured ruff with py313 target, 88-char line length, and 8 lint rule sets (E, F, W, I, UP, B, SIM, RUF)
- Set up pre-commit hooks via astral-sh/ruff-pre-commit for automatic enforcement
- Fixed 109 lint issues across entire codebase: 60 auto-fixed + 49 manual fixes
- All 375 tests pass, pre-commit hooks pass on full codebase

## Task Commits

Each task was committed atomically:

1. **Task 1: Configure ruff and pre-commit in project files** - `3507c02` (chore)
2. **Task 2: Run ruff across the codebase and fix all issues** - `70c4606` (style)

## Files Created/Modified
- `.pre-commit-config.yaml` - Pre-commit config with ruff-pre-commit hooks
- `pyproject.toml` - Added ruff config, dev dependencies, per-file-ignores
- `src/codepicture/**/*.py` - Formatting + lint fixes (B904, SIM105, RUF022, etc.)
- `tests/**/*.py` - Formatting + lint fixes (unused vars, line length, etc.)

## Decisions Made
- **Rule selection:** E, F, W, I, UP, B, SIM, RUF -- comprehensive coverage without being overly noisy
- **Visual fixture exclusion:** `tests/visual/fixtures` excluded from ruff entirely because formatting changes (e.g., adding blank lines) alter rendered images and break visual regression baselines
- **Per-file-ignores over blanket ignores:** MLIR lexer gets RUF012 exemption (Pygments API convention); benchmark fixtures get exemptions for intentional code patterns (B007, F841, etc.)
- **B904 fixes:** Added `from err` or `from None` to all re-raises in except clauses for proper exception chaining
- **SIM105:** Replaced try/except/pass with `contextlib.suppress()` where appropriate

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Visual fixture formatting caused baseline regression**
- **Found during:** Task 2 (ruff format run)
- **Issue:** `ruff format` added a blank line in `tests/visual/fixtures/python_visual.py`, which changed the rendered image height and broke all visual regression tests
- **Fix:** Excluded `tests/visual/fixtures` from ruff via `extend-exclude` and reverted the fixture file
- **Files modified:** `pyproject.toml`
- **Verification:** All 375 tests pass including 24 visual regression tests
- **Committed in:** `70c4606` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary fix to prevent visual regression test breakage. No scope creep.

## Issues Encountered
- Visual regression tests failed after formatting because `ruff format` modified a fixture file that gets rendered as an image. Resolved by excluding visual fixture directory from ruff.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ruff and pre-commit are fully operational
- All future commits will automatically run ruff check and ruff format
- No blockers or concerns

---
*Quick Task: 012*
*Completed: 2026-02-02*
