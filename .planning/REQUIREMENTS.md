# Requirements: codepicture v1.1 Reliability & Testing

**Defined:** 2026-01-30
**Core Value:** One command turns code into a slide-ready image

## v1.1 Requirements

### Bug Fixes & Safety

- [ ] **SAFE-01**: Fix MLIR lexer hang on `test.mlir` — diagnose root cause (regex backtracking) and fix without introducing new backtracking risks
- [ ] **SAFE-02**: Application-level rendering timeout guard — abort rendering if any pipeline stage exceeds configurable time limit (default 30s), with clear error message
- [ ] **SAFE-03**: Add `RenderTimeoutError` to error hierarchy with user-friendly CLI output (no Python tracebacks)
- [ ] **SAFE-04**: Add pytest-timeout to test suite with global default timeout (30s) to prevent CI hangs
- [ ] **SAFE-05**: Add CI job timeout to GitHub Actions workflow (10 minutes)

### Visual Regression Testing

- [ ] **VRT-01**: Visual regression test infrastructure — pixelmatch-based comparison with configurable threshold, diff image output on failure
- [ ] **VRT-02**: Reference images for Python fixture rendered with default config
- [ ] **VRT-03**: Reference images for Rust fixture rendered with default config
- [ ] **VRT-04**: Reference images for C++ fixture rendered with default config
- [ ] **VRT-05**: Reference images for JavaScript fixture rendered with default config
- [ ] **VRT-06**: Reference images for MLIR fixture rendered with default config
- [ ] **VRT-07**: Reference images for config variants (shadow on/off, line numbers on/off, chrome on/off)
- [ ] **VRT-08**: Snapshot update mechanism (`--snapshot-update` or equivalent) for intentional visual changes

### Rendering Reliability

- [ ] **REL-01**: Parametrized rendering tests across all 5 core languages x 3 output formats (PNG/SVG/PDF) — assert valid output and completion within timeout
- [ ] **REL-02**: Parametrized rendering tests across feature toggles (shadow, chrome, line numbers) — assert valid output
- [ ] **REL-03**: Error handling audit — all failure modes (bad input file, unsupported language, timeout, invalid config) produce clean error messages and non-zero exit codes

### Performance

- [ ] **PERF-01**: pytest-benchmark integration with per-stage benchmarks (highlight, layout, render) for core language fixtures
- [ ] **PERF-02**: End-to-end pipeline benchmark for small/medium/large inputs
- [ ] **PERF-03**: Benchmark CI integration — run benchmarks as informational step, upload results as artifacts

## Future Requirements

### Deferred to post-v1.1

- **PERF-04**: Fuzz testing for MLIR lexer robustness (hypothesis-based property testing)
- **VRT-09**: Cross-platform reference image management (macOS + Linux golden files)
- **PERF-05**: Memory profiling for large file rendering (tracemalloc-based assertions)
- **VRT-10**: CI diff artifact upload on visual regression failure

## Out of Scope

| Feature | Reason |
|---------|--------|
| Custom image diff viewer | Over-engineering — use pixelmatch diff images + CI artifacts |
| All 55+ themes in visual regression | Combinatorial explosion — test 2 representative themes |
| Pixel-perfect cross-platform matching | Cairo/Pango renders differently on macOS vs Linux — single platform (CI) only |
| Parallel/async rendering | CLI processes one file at a time, no user-facing benefit |
| Performance dashboard (Bencher) | Overkill for a CLI tool — simple threshold assertions sufficient |
| Multi-OS CI matrix for visual tests | Triples CI time — single ubuntu-latest sufficient |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SAFE-01 | TBD | Pending |
| SAFE-02 | TBD | Pending |
| SAFE-03 | TBD | Pending |
| SAFE-04 | TBD | Pending |
| SAFE-05 | TBD | Pending |
| VRT-01 | TBD | Pending |
| VRT-02 | TBD | Pending |
| VRT-03 | TBD | Pending |
| VRT-04 | TBD | Pending |
| VRT-05 | TBD | Pending |
| VRT-06 | TBD | Pending |
| VRT-07 | TBD | Pending |
| VRT-08 | TBD | Pending |
| REL-01 | TBD | Pending |
| REL-02 | TBD | Pending |
| REL-03 | TBD | Pending |
| PERF-01 | TBD | Pending |
| PERF-02 | TBD | Pending |
| PERF-03 | TBD | Pending |

**Coverage:**
- v1.1 requirements: 19 total
- Mapped to phases: 0 (awaiting roadmap)
- Unmapped: 19 ⚠️

---
*Requirements defined: 2026-01-30*
*Last updated: 2026-01-30 after initial definition*
