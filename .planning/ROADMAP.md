# Roadmap: codepicture

## Overview

codepicture transforms code snippets into polished, presentation-ready images via a single CLI command.

## Milestones

- SHIPPED **v1.0 MVP** — Phases 1-6 (shipped 2026-01-30) — [archive](milestones/v1.0-ROADMAP.md)
- **v1.1 Reliability & Testing** — Phases 7-11 (in progress)

## Phases

<details>
<summary>v1.0 MVP (Phases 1-6) — SHIPPED 2026-01-30</summary>

- [x] Phase 1: Foundation (2/2 plans) — completed 2026-01-28
- [x] Phase 1.1: Testing Infrastructure (2/2 plans) — completed 2026-01-28
- [x] Phase 2: Syntax Highlighting (3/3 plans) — completed 2026-01-28
- [x] Phase 3: Layout Engine (3/3 plans) — completed 2026-01-29
- [x] Phase 4: Rendering (5/5 plans) — completed 2026-01-29
- [x] Phase 5: CLI & Orchestration (4/4 plans) — completed 2026-01-29
- [x] Phase 6: MLIR Lexer (2/2 plans) — completed 2026-01-30

</details>

### v1.1 Reliability & Testing (In Progress)

**Milestone Goal:** Harden codepicture for real-world usage — fix rendering bugs, add timeout protection, build visual regression tests, and profile performance.

- [ ] **Phase 7: Safety Nets** — Prevent CI hangs with test-level and job-level timeouts
- [ ] **Phase 8: MLIR Hang Fix** — Diagnose and fix the test.mlir rendering hang
- [ ] **Phase 9: Rendering Timeout Guards** — Application-level timeout protection with clean error handling
- [ ] **Phase 10: Visual Regression & Reliability** — Automated visual verification and parametrized rendering tests
- [ ] **Phase 11: Performance Benchmarks** — Per-stage and end-to-end profiling with CI integration

## Phase Details

### Phase 7: Safety Nets
**Goal**: CI and test suite are protected against hangs, providing immediate safety while deeper fixes are developed
**Depends on**: Nothing (first v1.1 phase, trivial to add)
**Requirements**: SAFE-04, SAFE-05
**Success Criteria** (what must be TRUE):
  1. Running `pytest` with a test that would hang indefinitely is killed after the global timeout (5s default)
  2. A GitHub Actions CI run that exceeds 10 minutes is automatically cancelled
  3. Existing 260+ tests continue to pass with pytest-timeout enabled
**Plans**: 2 plans
Plans:
- [ ] 07-01-PLAN.md — Add pytest-timeout with 5s default and mark slow tests
- [ ] 07-02-PLAN.md — Add CI job timeout and artifact upload on failure

### Phase 8: MLIR Hang Fix
**Goal**: codepicture successfully renders test.mlir and other MLIR files without hanging
**Depends on**: Phase 7 (safety nets catch any remaining hangs during development)
**Requirements**: SAFE-01
**Success Criteria** (what must be TRUE):
  1. `codepicture test.mlir -o output.png` completes within a few seconds, producing a valid image
  2. Root cause of the hang is identified (lexer backtracking, layout, render, or shadow stage) and documented
  3. MLIR lexer regex patterns have no catastrophic backtracking on pathological inputs
  4. A corpus of MLIR test files (including test.mlir) all render successfully
**Plans**: TBD

### Phase 9: Rendering Timeout Guards
**Goal**: The rendering pipeline has application-level timeout protection and all failure modes produce clean, user-friendly error messages
**Depends on**: Phase 8 (hang fix informs timeout design; error audit needs working pipeline)
**Requirements**: SAFE-02, SAFE-03, REL-03
**Success Criteria** (what must be TRUE):
  1. If any pipeline stage exceeds the configurable time limit, rendering aborts with a clear error message (no Python traceback)
  2. `RenderTimeoutError` is part of the error hierarchy and produces a user-friendly CLI message
  3. All failure modes (bad input file, unsupported language, timeout, invalid config) produce clean error messages and non-zero exit codes
  4. Timeout guard uses ThreadPoolExecutor (works with C extensions), not signal-based timeout
**Plans**: TBD

### Phase 10: Visual Regression & Reliability
**Goal**: Rendering output is verified visually against reference images, and all language/format/config combinations produce valid output
**Depends on**: Phase 8 (pipeline must not hang), Phase 9 (timeout guards protect test runs)
**Requirements**: VRT-01, VRT-02, VRT-03, VRT-04, VRT-05, VRT-06, VRT-07, VRT-08, REL-01, REL-02
**Success Criteria** (what must be TRUE):
  1. Reference images exist for all 5 core languages (Python, Rust, C++, JavaScript, MLIR) and visual comparison runs automatically in CI
  2. An intentional rendering change can be accepted via snapshot update mechanism, and an unintentional change fails CI with a diff image
  3. All 5 languages x 3 formats (PNG/SVG/PDF) render valid output within timeout
  4. Feature toggle combinations (shadow on/off, chrome on/off, line numbers on/off) all produce valid, visually verified output
  5. pixelmatch-based comparison uses configurable threshold to handle anti-aliasing without false positives
**Plans**: TBD

### Phase 11: Performance Benchmarks
**Goal**: Rendering performance is measured per-stage and end-to-end, with results tracked in CI
**Depends on**: Phase 10 (benchmarks are most meaningful after pipeline is stable and verified)
**Requirements**: PERF-01, PERF-02, PERF-03
**Success Criteria** (what must be TRUE):
  1. Per-stage benchmarks (highlight, layout, render) run for each core language fixture with statistical rigor (pytest-benchmark)
  2. End-to-end pipeline benchmarks exist for small, medium, and large inputs
  3. CI runs benchmarks as an informational step and uploads results as artifacts
**Plans**: TBD

## Progress

**Execution Order:** Phases 7 through 11 in sequence.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-01-28 |
| 1.1 Testing Infrastructure | v1.0 | 2/2 | Complete | 2026-01-28 |
| 2. Syntax Highlighting | v1.0 | 3/3 | Complete | 2026-01-28 |
| 3. Layout Engine | v1.0 | 3/3 | Complete | 2026-01-29 |
| 4. Rendering | v1.0 | 5/5 | Complete | 2026-01-29 |
| 5. CLI & Orchestration | v1.0 | 4/4 | Complete | 2026-01-29 |
| 6. MLIR Lexer | v1.0 | 2/2 | Complete | 2026-01-30 |
| 7. Safety Nets | v1.1 | 0/2 | Planned | - |
| 8. MLIR Hang Fix | v1.1 | 0/TBD | Not started | - |
| 9. Rendering Timeout Guards | v1.1 | 0/TBD | Not started | - |
| 10. Visual Regression & Reliability | v1.1 | 0/TBD | Not started | - |
| 11. Performance Benchmarks | v1.1 | 0/TBD | Not started | - |

---
*Roadmap created: 2026-01-28*
*v1.0 shipped: 2026-01-30*
*v1.1 roadmap added: 2026-01-30*
