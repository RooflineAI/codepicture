---
phase: 09-rendering-timeout-guards
plan: 01
subsystem: error-handling, orchestration
tags: [timeout, exceptions, atomic-writes, ThreadPoolExecutor]
depends_on:
  requires: []
  provides: [RenderTimeoutError, InputError, generate_image_with_timeout, atomic-writes]
  affects: [09-02, 09-03]
tech-stack:
  added: []
  patterns: [ThreadPoolExecutor-timeout-wrapper, atomic-file-write]
key-files:
  created: []
  modified: [src/codepicture/errors.py, src/codepicture/cli/orchestrator.py]
decisions: []
metrics:
  duration: ~2 min
  completed: 2026-01-30
---

# Phase 9 Plan 01: Error Hierarchy and Timeout Wrapper Summary

Extended error hierarchy with RenderTimeoutError (RenderError subclass) and InputError, added ThreadPoolExecutor-based timeout wrapper around the rendering pipeline, and replaced direct file writes with atomic temp-file-plus-move.

## Tasks Completed

| # | Task | Commit | Key Changes |
|---|------|--------|-------------|
| 1 | Add RenderTimeoutError and InputError to error hierarchy | 065c380 | errors.py: two new exception classes with structured attributes |
| 2 | Add timeout wrapper and atomic writes to orchestrator | 5d84dd7 | orchestrator.py: _write_output_atomic, generate_image_with_timeout |

## What Was Built

### Error Classes (errors.py)

**RenderTimeoutError(RenderError)** -- carries `timeout` (float) and `file_info` (str) attributes. Subclasses RenderError so existing `except RenderError` handlers catch it.

**InputError(CodepictureError)** -- carries `input_path` (str) attribute. For file-not-found, permission denied, unreadable files.

### Timeout Wrapper (orchestrator.py)

**generate_image_with_timeout()** -- wraps `generate_image` in a `ThreadPoolExecutor(max_workers=1)`. On timeout, calls `executor.shutdown(wait=False, cancel_futures=True)` to avoid blocking, then raises `RenderTimeoutError` with diagnostic message including timeout value, filename, and suggestion to increase timeout.

When `timeout=None` (disabled), calls `generate_image` directly with no executor overhead.

### Atomic Writes (orchestrator.py)

**_write_output_atomic()** -- writes to a `tempfile.NamedTemporaryFile` in the output directory (prefix `.codepicture-`), then `shutil.move` to final path. On any exception, cleans up the temp file. Replaces the previous direct `write_bytes` call.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

- All 272 existing tests pass
- RenderTimeoutError and InputError importable from codepicture.errors
- generate_image_with_timeout importable from codepicture.cli.orchestrator
- RenderTimeoutError is catchable as both RenderError and CodepictureError

## Next Phase Readiness

Plan 09-02 (CLI error handling) can proceed -- it imports `generate_image_with_timeout` and `RenderTimeoutError` from the modules modified here. Plan 09-03 (tests) can proceed -- all new classes and functions are importable and ready for testing.
