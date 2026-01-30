---
phase: 09-rendering-timeout-guards
plan: 02
subsystem: cli, error-handling
tags: [timeout-flag, exit-codes, language-fallback, InputError]
depends_on:
  requires: [09-01]
  provides: [--timeout CLI flag, exit-code-mapping, language-fallback-warning]
  affects: [09-03]
tech-stack:
  added: []
  patterns: [exit-code-mapping, graceful-language-fallback]
key-files:
  created: []
  modified: [src/codepicture/cli/app.py, src/codepicture/cli/orchestrator.py]
decisions: []
metrics:
  duration: ~2 min
  completed: 2026-01-30
---

# Phase 9 Plan 02: CLI Error Handling and Timeout Flag Summary

Wired timeout guard and error hierarchy into CLI layer: added --timeout flag (default 30s, 0 disables), mapped exception types to distinct exit codes (timeout=2, error=1, success=0), replaced typer.BadParameter with InputError for file validation, and added language fallback with stderr warning for unknown languages.

## Tasks Completed

| # | Task | Commit | Key Changes |
|---|------|--------|-------------|
| 1 | Add --timeout flag and exit code mapping to CLI | 51f4d67 | app.py: EXIT_TIMEOUT=2, --timeout param, generate_image_with_timeout call, InputError for file validation |
| 2 | Add language fallback with stderr warning in orchestrator | 7cbe42e | orchestrator.py: HighlightError catch with plain text fallback and stderr warning |

## What Was Built

### CLI Timeout Flag (app.py)

**--timeout** parameter with default 30.0 seconds. `--timeout 0` maps to `None` (disabled). Passed through to `generate_image_with_timeout`.

### Exit Code Constants (app.py)

- `EXIT_SUCCESS = 0` -- successful render
- `EXIT_ERROR = 1` -- CodepictureError or unexpected error
- `EXIT_TIMEOUT = 2` -- RenderTimeoutError specifically

RenderTimeoutError caught before CodepictureError (subclass ordering).

### Input Validation (app.py)

`read_input` now raises `InputError` instead of `typer.BadParameter` for file-not-found, not-a-file, and permission-denied. These get caught by the `except CodepictureError` handler and exit with code 1. stdin-requires-language still uses `typer.BadParameter` (CLI argument error).

### Language Fallback (orchestrator.py)

`generate_image` wraps the `highlighter.highlight()` call in try/except `HighlightError`. On unknown language, prints a warning to stderr and re-highlights as plain text. Pipeline no longer crashes on `--language foo`.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

- `python -m codepicture --help` shows --timeout with default 30.0
- `python -m codepicture nonexistent.py -o /tmp/test.png` exits with code 1, clean "File not found" message
- All 272 existing tests pass
- `python -m codepicture test.mlir -o /tmp/test.png --timeout 30` succeeds

## Next Phase Readiness

Plan 09-03 (tests) can proceed -- all CLI error paths and language fallback are testable. The exit code constants, InputError usage, and HighlightError fallback are all in place.
