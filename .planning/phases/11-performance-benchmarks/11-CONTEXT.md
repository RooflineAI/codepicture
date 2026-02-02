# Phase 11: Performance Benchmarks - Context

**Gathered:** 2026-02-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Measure rendering performance per-stage and end-to-end using pytest-benchmark, with results tracked as CI artifacts. This phase adds observability into pipeline performance — it does not optimize or change rendering behavior.

</domain>

<decisions>
## Implementation Decisions

### Benchmark scope
- Benchmark all 3 core pipeline stages individually: highlight, layout, render
- Each stage benchmarked per language fixture (all 5 core: Python, Rust, C++, JavaScript, MLIR)
- End-to-end benchmarks for 3 input sizes: small (~10 lines), medium (~50 lines), large (~200 lines)
- Feature toggle combinations: Claude's discretion on which combos give useful performance signal

### Output & reporting
- Use pytest-benchmark default table output (min, max, mean, stddev, rounds)
- Invocation via pytest markers only (`pytest -m benchmark`) — no new CLI surface
- Benchmarks excluded from regular `pytest` runs by default — only run with explicit `-m benchmark`

### CI integration
- Separate workflow file (benchmark.yml) — independent from main CI
- Trigger: manual (workflow_dispatch) and/or scheduled — not on every push
- Informational only — never blocks merge
- Artifact uploads: Claude's discretion on what's useful for an informational job

### Baselines & thresholds
- No committed baselines for now — purely observational, establish baselines after a few runs
- pytest-benchmark auto-calibration for rounds/iterations
- Warmup runs enabled — first runs excluded from stats
- Accept CI variance as-is — informational purposes, no regression gating

### Claude's Discretion
- Feature toggle combinations to benchmark (shadow, chrome, line numbers)
- CI artifact format (JSON, console log, or both)
- Machine-readable export format/location
- Exact fixture content for small/medium/large inputs

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-performance-benchmarks*
*Context gathered: 2026-02-02*
