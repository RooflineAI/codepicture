# Phase 8: MLIR Hang Fix - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Diagnose and fix why `codepicture test.mlir` hangs, ensuring MLIR files render successfully without hanging. This phase finds and fixes the root cause; broader timeout infrastructure is Phase 9.

</domain>

<decisions>
## Implementation Decisions

### Fix strategy
- Minimal patch for the specific root cause — don't overhaul unrelated patterns
- If the hang is in the lexer, fix only the offending pattern(s)
- If the hang is in layout/render, a broader fix is acceptable if the stage has a deeper design issue
- Use systematic bisection to diagnose: isolate each pipeline stage (lex → layout → render → shadow) to pinpoint where time is spent
- Add a timeout-based regression test that renders test.mlir and fails if it exceeds a time threshold

### MLIR test corpus
- Create a small curated set of 3-5 MLIR files in `tests/fixtures/mlir/`
- Mix of real-world MLIR snippets and synthetic edge cases (deeply nested, long lines, unusual tokens)
- Corpus tests verify both successful rendering (no hang) AND basic quality (non-trivial token output, not all plain text)

### Failure behavior
- If an MLIR file can't render: clear error message with non-zero exit code, not a fallback to plain text
- Error message should be specific to the cause (which stage failed: lexer, layout, or render)
- Clean up partial output files on failure — user gets error message only, no half-written PNG
- Fix obvious error handling gaps in the MLIR path encountered during debugging, beyond just the hang fix itself

### Claude's Discretion
- Documentation depth: Claude decides based on complexity of root cause — could be commit message + comments or a detailed write-up
- Whether to document the diagnosis process or just the final answer — based on how complex the investigation is
- Inline regex comments: only for complex patterns, Claude judges which need explanation

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for diagnosis and fix.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-mlir-hang-fix*
*Context gathered: 2026-01-30*
