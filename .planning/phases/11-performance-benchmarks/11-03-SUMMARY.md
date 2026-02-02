---
phase: 11-performance-benchmarks
plan: 03
subsystem: benchmarks
tags: [benchmarks, pipeline, ci, github-actions]
dependency-graph:
  requires: ["11-01"]
  provides: ["end-to-end pipeline benchmarks", "CI benchmark workflow"]
  affects: []
tech-stack:
  added: []
  patterns: ["end-to-end benchmark parametrization", "CI benchmark artifact archival"]
key-files:
  created:
    - tests/benchmarks/test_bench_pipeline.py
    - .github/workflows/benchmark.yml
  modified: []
decisions: []
metrics:
  duration: "3 min"
  completed: "2026-02-02"
---

# Phase 11 Plan 03: Pipeline Benchmarks & CI Workflow Summary

End-to-end pipeline benchmarks for small/medium/large inputs via generate_image, plus a standalone GitHub Actions workflow for manual and weekly benchmark runs with JSON artifact uploads.

## What Was Done

### Task 1: End-to-end pipeline benchmarks
Created `tests/benchmarks/test_bench_pipeline.py` with parametrized benchmarks calling `generate_image` directly for three input sizes (small ~10 lines, medium ~50 lines, large ~200 lines). Each benchmark writes to a temp file and verifies the output exists. Uses `@pytest.mark.timeout(0)` to disable the 5s timeout guard during benchmark iterations.

Observed baseline timings:
- Small: ~24ms
- Medium: ~120ms
- Large: ~530ms

### Task 2: CI benchmark workflow
Created `.github/workflows/benchmark.yml` as a standalone workflow (separate from test.yml). Triggers on `workflow_dispatch` for on-demand runs and a weekly cron schedule (Monday 6am UTC). Installs system dependencies (Cairo, Pango, JetBrains Mono), runs all benchmarks with `--benchmark-json`, and uploads both JSON and text output as artifacts with 90-day retention. The job is purely informational -- no merge-blocking gates.

## Deviations from Plan

None -- plan executed exactly as written.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 74e0b5f | feat(11-03): add end-to-end pipeline benchmarks |
| 2 | 57e83f9 | feat(11-03): add CI benchmark workflow |

## Verification Results

- 3 pipeline benchmarks run successfully (small, medium, large)
- Benchmark JSON export produces valid output with 3 benchmarks
- YAML workflow validates correctly
- 318 existing tests pass (21 skipped, visual tests excluded due to local env)

## Next Phase Readiness

Pipeline benchmarks complete. Plan 11-04 (if it exists) can proceed. The benchmark infrastructure is fully operational for tracking performance over time.
