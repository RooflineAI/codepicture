# Phase 6: MLIR Lexer - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Custom Sublime syntax-based lexer for MLIR with dialect support. Integrates an existing Sublime syntax file with the Pygments-based highlighting pipeline. Does not add new visual features or CLI options beyond language detection.

</domain>

<decisions>
## Implementation Decisions

### Syntax file sourcing
- Bundle the existing Sublime syntax file into the repo
- Source file: `~/.config/silicon/MLIR.sublime-syntax` (copy into package)
- Package ships with syntax file included — works out of the box

### Token-to-color mapping
- Use Pygments token conventions as default
- Map Sublime scopes to closest Pygments tokens (keyword → Keyword, string → String, etc.)
- Can revisit with custom mapping if results look off

### Language detection
- Auto-detect MLIR from `.mlir` file extension
- Register "mlir" as explicit language option for `--language` flag

### Fallback behavior
- Unrecognized constructs render as plain text
- No errors or warnings — graceful degradation
- Parser should never break on valid MLIR, just may not highlight everything

### Claude's Discretion
- Sublime syntax parser implementation details
- How to integrate custom lexer with existing Pygments pipeline
- Exact scope-to-token mapping table

</decisions>

<specifics>
## Specific Ideas

- Existing syntax file is already used with Silicon tool — proven to work
- Should feel seamless — user doesn't need to know it's a custom lexer under the hood

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-mlir-lexer*
*Context gathered: 2026-01-29*
