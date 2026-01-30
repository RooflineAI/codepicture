# Phase 9: Rendering Timeout Guards - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Application-level timeout protection for the rendering pipeline with clean error handling for all failure modes. The pipeline aborts cleanly on timeout, all errors produce user-friendly messages, and the CLI uses distinct exit codes. No new rendering features or capabilities.

</domain>

<decisions>
## Implementation Decisions

### Timeout configuration
- Single global timeout for the entire pipeline (not per-stage)
- Default: 30 seconds
- CLI flag: `--timeout <seconds>` to override
- `--timeout 0` disables the timeout entirely (for debugging or very large files)
- Implementation: ThreadPoolExecutor-based (works with C extensions like Cairo)

### Error message design
- Detailed diagnostic on timeout: include which stage was running, file info, and suggestion to increase timeout
- Timeout error explicitly states "No output file written."
- All error messages include actionable fix suggestions (e.g., "Unsupported language 'foo'. Supported: python, rust, cpp, js, mlir. Use --language to override.")
- Colored output: red "Error:" prefix, yellow for warnings
- Auto-detect TTY: colors when interactive, plain text when piped

### Partial output handling
- Always clean up partial/incomplete output files on failure — user gets complete result or nothing
- Write to temp file first, move to output path on success — preserves any existing file if render fails
- Distinct exit codes: timeout = exit 2, other errors = exit 1, success = exit 0

### Failure mode catalog
- Unsupported/unrecognized language: fall back to plain text rendering with stderr warning ("Warning: Unknown language 'foo', rendering as plain text.")
- File not found / permission errors: validate upfront before starting pipeline, fail fast with clear message
- Structured exception hierarchy: `CodePictureError` base class with `RenderTimeoutError`, `InputError`, `UnsupportedLanguageError`, etc.
- All failure modes produce clean messages (no Python tracebacks) and non-zero exit codes

### Claude's Discretion
- Exception class naming and module placement
- ThreadPoolExecutor pool size and thread management
- Exact stage identification mechanism for timeout diagnostics
- Temp file naming and placement strategy

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

*Phase: 09-rendering-timeout-guards*
*Context gathered: 2026-01-30*
