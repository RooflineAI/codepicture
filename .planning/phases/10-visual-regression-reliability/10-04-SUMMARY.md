---
phase: 10-visual-regression-reliability
plan: 04
subsystem: ci
tags: [ci, git-lfs, visual-regression, github-actions, artifact-upload]
depends_on: [10-02, 10-03]
provides: [visual-ci-job, lfs-tracking, diff-artifact-upload]
affects: [11]
tech-stack:
  added: [git-lfs]
  patterns: [parallel-ci-jobs, artifact-upload-on-failure]
key-files:
  created:
    - .gitattributes
  modified:
    - .github/workflows/test.yml
decisions: []
metrics:
  duration: 1 min
  completed: 2026-01-31
---

# Phase 10 Plan 04: CI Integration & Git LFS Summary

**One-liner:** Parallel visual regression CI job with JetBrains Mono font install, diff artifact upload on failure, and Git LFS tracking for reference PNGs.

## What Was Done

### Task 1: Add Git LFS tracking for reference images
- Created `.gitattributes` with LFS filter for `tests/visual/references/*.png`
- Initialized Git LFS tracking via `git lfs install` and `git lfs track`
- Ensures reference images are stored efficiently and don't bloat the Git history

### Task 2: Add visual regression CI job to GitHub Actions workflow
- Added `visual` job to `.github/workflows/test.yml` running in parallel with existing `test` job
- Visual job installs system dependencies: `libcairo2-dev`, `libpango1.0-dev`, `fonts-jetbrains-mono`
- Checks out with `lfs: true` to pull reference images
- Runs `pytest tests/visual/ -v --tb=short` with `PANGOCAIRO_BACKEND=fontconfig` for consistent font rendering
- Uploads diff composites and test output as artifacts on failure (7-day retention)
- Existing `test` job completely unchanged

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

1. `.gitattributes` exists with LFS tracking rule for `tests/visual/references/*.png`
2. `.github/workflows/test.yml` has both `test` and `visual` jobs
3. `visual` job installs Cairo, Pango, and JetBrains Mono font
4. `visual` job uploads diff artifacts on failure
5. Existing `test` job unchanged (verified by diff)
6. 338 non-visual tests pass; 1 pre-existing local cairosvg library path issue on macOS (works in CI)

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | d621def | Add Git LFS tracking for reference images |
| 2 | 6497800 | Add visual regression CI job to GitHub Actions workflow |

## Next Phase Readiness

Phase 10 is complete. Phase 11 (Performance Benchmarks) can proceed:
- Full visual regression test suite (20 snapshot + 38 reliability tests) in place
- CI runs visual tests in parallel with unit tests
- Reference images tracked via Git LFS
- Diff composites uploaded as artifacts on failure for debugging
