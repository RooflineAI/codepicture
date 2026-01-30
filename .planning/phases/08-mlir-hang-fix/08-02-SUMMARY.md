---
phase: 08-mlir-hang-fix
plan: 02
subsystem: testing
tags: [mlir, regression-test, corpus, fixtures, integration]
dependency-graph:
  requires: ["08-01"]
  provides: ["mlir-test-corpus", "mlir-regression-tests"]
  affects: ["09", "10", "11"]
tech-stack:
  patterns: ["parametrized-corpus-testing", "timeout-guarded-regression"]
file-tracking:
  key-files:
    created:
      - tests/fixtures/mlir/basic_module.mlir
      - tests/fixtures/mlir/complex_attributes.mlir
      - tests/fixtures/mlir/deep_nesting.mlir
      - tests/fixtures/mlir/long_lines.mlir
      - tests/fixtures/mlir/edge_cases.mlir
      - tests/integration/test_mlir_rendering.py
decisions: []
metrics:
  duration: "2 min"
  completed: "2026-01-30"
---

# Phase 8 Plan 2: MLIR Test Corpus & Regression Tests Summary

**One-liner:** 5-file MLIR corpus with timeout-guarded rendering regression tests and lexer quality assertions (12 test cases, all pass)

## What Was Done

### Task 1: MLIR Test Corpus Fixtures

Created `tests/fixtures/mlir/` with 5 curated MLIR files covering diverse syntax patterns:

| File | Lines | Tokens | Errors | Coverage |
|------|-------|--------|--------|----------|
| basic_module.mlir | 6 | 51 | 0 | SSA values, func, return |
| complex_attributes.mlir | 15 | 201 | 0 | Real-world test.mlir (hang trigger) |
| deep_nesting.mlir | 14 | 137 | 0 | Affine loops, memref |
| long_lines.mlir | 9 | 155 | 0 | Wide signatures, many params |
| edge_cases.mlir | 11 | 94 | 0 | Quoted refs, hex, escapes, block labels |

All files tokenize with 0 Error tokens.

### Task 2: MLIR Rendering Regression Tests

Created `tests/integration/test_mlir_rendering.py` with 4 test functions (12 test cases):

1. **test_mlir_render_completes** - Timeout-guarded (10s) rendering of test.mlir. Key hang regression guard.
2. **test_mlir_lexer_minimal_error_tokens** - Asserts <10 Error tokens on test.mlir.
3. **test_mlir_corpus_renders** (parametrized x5) - All corpus files render to valid PNG.
4. **test_mlir_corpus_lexer_quality** (parametrized x5) - All corpus files tokenize cleanly.

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

- All 12 new tests pass (0.43s)
- Full suite: 272 tests pass (1.93s)
- No existing tests affected

## Commits

| Hash | Message |
|------|---------|
| e9a8d8d | test(08-02): create MLIR test corpus fixtures |
| 3bdfd2c | test(08-02): create MLIR rendering regression tests |

## Next Phase Readiness

Phase 8 is now complete. The MLIR hang fix (08-01) is validated by automated regression tests (08-02). Ready for Phase 9 (Timeout Guards).
