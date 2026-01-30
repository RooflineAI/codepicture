# Phase 9: Rendering Timeout Guards - Research

**Researched:** 2026-01-30
**Domain:** Python timeout mechanisms, error handling patterns, CLI error UX
**Confidence:** HIGH

## Summary

This phase adds application-level timeout protection to the rendering pipeline using `concurrent.futures.ThreadPoolExecutor`, builds a structured exception hierarchy with user-friendly error messages, and ensures all failure modes produce clean output with distinct exit codes.

The codebase already has a solid foundation: a `CodepictureError` base class with five subclasses (`ConfigError`, `ThemeError`, `RenderError`, `HighlightError`, `LayoutError`), a clean 7-step pipeline orchestrator (`cli/orchestrator.py:generate_image`), and a CLI layer that catches `CodepictureError` and prints formatted messages via Rich. The work is extending what exists, not building from scratch.

Key technical concerns are: (1) `ThreadPoolExecutor` threads cannot be cancelled once running -- timeout only controls how long the caller waits, the thread continues in the background; (2) the current orchestrator writes output directly via `output_path.write_bytes()` with no temp-file atomicity; (3) the CLI currently uses `exit(1)` for all errors with no distinction between timeout and other failures.

**Primary recommendation:** Wrap the `generate_image` call in `ThreadPoolExecutor.submit()` with `future.result(timeout=N)`, catch `concurrent.futures.TimeoutError`, add `RenderTimeoutError` to the error hierarchy, implement atomic writes via `tempfile.NamedTemporaryFile`, and map error types to distinct exit codes in the CLI layer.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `concurrent.futures` | stdlib (Python 3.13) | ThreadPoolExecutor-based timeout | stdlib, works with C extensions (unlike `signal.alarm` which is main-thread-only and doesn't interrupt C code) |
| `tempfile` | stdlib | Atomic write via NamedTemporaryFile | stdlib, OS-level temp file management |
| `shutil.move` | stdlib | Atomic file move (temp to final) | Cross-filesystem safe move |
| `rich` | 14.3.1 (transitive via typer) | Colored error/warning output | Already used in `cli/app.py` for `Console(stderr=True)` |
| `typer` | 0.21.1 | CLI framework, exit code control | Already the CLI framework; `typer.Exit(code=N)` for exit codes |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `os` | stdlib | File cleanup (`os.unlink`) | Cleaning up temp files on failure |
| `sys` | stdlib | `sys.stderr` for warnings | Unsupported language fallback warning |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ThreadPoolExecutor | `signal.alarm` | signal-based is simpler but main-thread-only and cannot interrupt C extensions (Cairo, Pango). ThreadPoolExecutor works everywhere. |
| ThreadPoolExecutor | `multiprocessing.Process` | Process-based allows true kill, but adds IPC complexity and serialization overhead for passing render results back. Overkill for a timeout guard. |
| `tempfile.NamedTemporaryFile` | Write to `output.tmp` | NamedTemporaryFile handles unique naming and cleanup automatically. Manual `.tmp` suffix risks collisions. |

**Installation:** No new dependencies required. All are stdlib or already installed.

## Architecture Patterns

### Current Pipeline Structure (from `cli/orchestrator.py`)

```
generate_image(code, output_path, config, language, filename)
  1. register_bundled_fonts()
  2. Create highlighter, detect language
  3. Tokenize code (highlight)
  4. Load theme
  5. Calculate layout
  6. Render to bytes
  7. Write output file
```

### Pattern 1: ThreadPoolExecutor Timeout Wrapper

**What:** Wrap the pipeline call in a ThreadPoolExecutor future with configurable timeout.
**When to use:** At the orchestrator or CLI level to protect the entire pipeline.
**Where to place:** In `cli/orchestrator.py` around the existing pipeline, or as a new function that wraps `generate_image`.

```python
# Source: Python 3.13 stdlib concurrent.futures
import concurrent.futures

def generate_image_with_timeout(
    code: str,
    output_path: Path,
    config: RenderConfig,
    language: str | None = None,
    filename: str | None = None,
    timeout: float | None = 30.0,
) -> None:
    """Run generate_image with a timeout guard.

    timeout=None or timeout=0 disables the timeout.
    """
    if not timeout:
        # No timeout -- run directly
        generate_image(code, output_path, config, language, filename)
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            generate_image, code, output_path, config, language, filename
        )
        try:
            future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise RenderTimeoutError(
                f"Rendering timed out after {timeout:.0f}s",
                timeout=timeout,
                file_info=filename or "<stdin>",
            )
```

**Key detail:** `executor.shutdown(wait=False)` is called implicitly by the context manager's `__exit__` -- but in Python 3.9+ the default is `wait=True` which blocks. For timeout scenarios, we must use `executor.shutdown(wait=False, cancel_futures=True)` explicitly or use the `with` block which calls `shutdown(wait=True)`. Since the thread cannot be killed, the `with` block will actually block until the thread finishes even after timeout. This is an important design consideration -- see Pitfall 1 below.

### Pattern 2: Atomic File Write (Temp + Move)

**What:** Write to a temporary file first, then atomically move to the final path on success.
**When to use:** Always, to prevent partial output files on failure.

```python
import tempfile
import shutil

def write_output_atomic(data: bytes, output_path: Path) -> None:
    """Write data to output_path atomically via temp file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in the same directory (ensures same filesystem for rename)
    fd = tempfile.NamedTemporaryFile(
        dir=output_path.parent,
        suffix=output_path.suffix,
        delete=False,
    )
    try:
        fd.write(data)
        fd.close()
        shutil.move(fd.name, output_path)
    except BaseException:
        # Clean up temp file on any failure
        try:
            os.unlink(fd.name)
        except OSError:
            pass
        raise
```

### Pattern 3: Structured Exception Hierarchy

**What:** Extend the existing error hierarchy with timeout and input validation errors.
**Current hierarchy:**

```
CodepictureError (base)
├── ConfigError (field attribute)
├── ThemeError
├── RenderError
├── HighlightError
└── LayoutError
```

**Target hierarchy:**

```
CodepictureError (base)
├── ConfigError (field attribute)
├── ThemeError
├── RenderError
│   └── RenderTimeoutError (timeout, file_info, stage attributes)
├── HighlightError
├── LayoutError
└── InputError (input_path attribute)
```

**Design notes:**
- `RenderTimeoutError` subclasses `RenderError` (it IS a render failure, just timeout-specific)
- `InputError` is new for file-not-found, permission errors, unreadable files
- Both carry structured attributes for building diagnostic messages

### Pattern 4: Exit Code Mapping in CLI

**What:** Map exception types to specific exit codes.
**Where:** In `cli/app.py`'s `main()` exception handler.

```python
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_TIMEOUT = 2

# In the except block:
except RenderTimeoutError as e:
    err_console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(EXIT_TIMEOUT)
except CodepictureError as e:
    err_console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(EXIT_ERROR)
```

### Anti-Patterns to Avoid

- **signal.alarm for timeout:** Does not work with C extensions (Cairo/Pango), only works on main thread, and is Unix-only. The CONTEXT.md explicitly requires ThreadPoolExecutor.
- **Catching TimeoutError broadly:** `concurrent.futures.TimeoutError` is a subclass of Python's built-in `TimeoutError` (since Python 3.3). Catch the specific `concurrent.futures.TimeoutError` to avoid swallowing other timeout exceptions.
- **Blocking on shutdown after timeout:** If you use `with ThreadPoolExecutor(...)` naively, the context manager's `__exit__` calls `shutdown(wait=True)`, which blocks until the timed-out thread completes. For a 30s timeout on a hang, this could block indefinitely.
- **Writing output before pipeline completes:** The current code writes output at the end of `generate_image`. With atomic writes, the data should stay in memory until the full pipeline succeeds, then write atomically.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Timeout mechanism | Custom thread + timer | `concurrent.futures.ThreadPoolExecutor` + `future.result(timeout=)` | stdlib, handles exceptions cleanly, well-tested |
| Atomic file writes | Manual `.tmp` + rename | `tempfile.NamedTemporaryFile(delete=False)` + `shutil.move` | Handles unique naming, same-directory creation, cleanup |
| Colored terminal output | ANSI escape codes | `rich.console.Console` | Already in use, handles TTY detection automatically |
| TTY detection | `os.isatty()` checks | Rich's `Console.is_terminal` | Rich already does this; `Console(stderr=True)` auto-detects |
| Exit code management | `sys.exit()` | `typer.Exit(code=N)` | Integrates with Typer's lifecycle, allows cleanup |

**Key insight:** Everything needed is either stdlib or already a dependency. No new packages required.

## Common Pitfalls

### Pitfall 1: ThreadPoolExecutor Thread Cannot Be Killed

**What goes wrong:** After `future.result(timeout=N)` raises `TimeoutError`, the worker thread is still running. If it's stuck in a C extension (Cairo/Pango), it cannot be interrupted. The thread continues consuming resources until it completes or the process exits.

**Why it happens:** Python's threading model has no safe thread termination. `future.cancel()` only works if the task hasn't started yet (which it always has by timeout time -- verified: returns `False` for running tasks).

**How to avoid:**
1. Don't use `with ThreadPoolExecutor(...)` for the timeout case -- the `__exit__` will block.
2. Instead, create the executor explicitly, call `executor.shutdown(wait=False, cancel_futures=True)` after timeout.
3. Accept that the thread will finish in the background. For a CLI tool that exits after one render, this is fine -- process exit will clean up.
4. For very long hangs, the `cancel_futures=True` parameter (Python 3.9+) prevents queued futures from running but does NOT stop running ones.

**Warning signs:** CLI appears to hang after printing a timeout error (because `shutdown(wait=True)` is blocking).

### Pitfall 2: Temp File Left Behind on Crash

**What goes wrong:** If the process is killed between creating the temp file and moving it, the temp file remains on disk.

**Why it happens:** `tempfile.NamedTemporaryFile(delete=False)` deliberately leaves the file around.

**How to avoid:**
1. Use a `try/except/finally` block that unlinks the temp file on any error.
2. Place the temp file in the same directory as the output (ensures same filesystem, enables atomic `os.rename`).
3. Use a recognizable prefix like `.codepicture-` so stale temp files can be identified.

**Warning signs:** `.codepicture-*.png` files accumulating in output directories.

### Pitfall 3: Rich Console Color Detection in Tests

**What goes wrong:** Tests capture stderr and check for error messages, but Rich may or may not include ANSI escape codes depending on the test environment's TTY status.

**Why it happens:** Rich's `Console` auto-detects TTY. In test environments (CliRunner, subprocess), stderr may not be a TTY.

**How to avoid:**
1. The existing code already uses `Console(stderr=True)` which auto-detects.
2. In tests, use Typer's `CliRunner` which captures output as plain text by default.
3. When testing subprocess output, strip ANSI codes or check for the plain-text content.
4. For explicit control, `Console(stderr=True, no_color=True)` forces plain text.

**Warning signs:** Tests fail with "Error:" not found in output because it's wrapped in ANSI codes.

### Pitfall 4: Typer BadParameter vs CodepictureError for Input Validation

**What goes wrong:** The current code uses `typer.BadParameter` for file-not-found and missing language flag. This produces Typer's built-in error formatting which may not match the desired clean error format.

**Why it happens:** `typer.BadParameter` was the natural choice during initial CLI development, but Phase 9 wants ALL errors to have a consistent format with colored "Error:" prefix and actionable suggestions.

**How to avoid:**
1. Decide whether to keep `typer.BadParameter` for argument-level errors (file not found, missing flag) or replace with custom `InputError`.
2. `typer.BadParameter` produces `Error: Invalid value for 'INPUT_FILE': file not found: foo.py` -- this is already clean but doesn't include the "Error:" prefix with red coloring.
3. Consider validating inputs early (before the pipeline) and raising `InputError` with structured messages.

**Warning signs:** Inconsistent error formats between Typer-generated errors and CodepictureError-based errors.

### Pitfall 5: Timeout Value of 0 Semantics

**What goes wrong:** `--timeout 0` should disable the timeout, but `future.result(timeout=0)` will immediately raise `TimeoutError`.

**Why it happens:** `future.result(timeout=0)` means "check immediately, don't wait." A timeout of `None` means "wait forever."

**How to avoid:**
1. Map `--timeout 0` to `timeout=None` in the CLI layer.
2. When `timeout is None`, skip the `ThreadPoolExecutor` wrapper entirely and call `generate_image` directly. This avoids unnecessary thread overhead.

**Warning signs:** `--timeout 0` immediately fails with "Rendering timed out after 0s."

## Code Examples

### Example 1: RenderTimeoutError Exception Class

```python
# Source: extending existing codepicture/errors.py pattern
class RenderTimeoutError(RenderError):
    """Rendering exceeded the configured time limit.

    Attributes:
        timeout: The timeout value in seconds that was exceeded.
        file_info: The file being rendered when timeout occurred.
    """

    def __init__(
        self,
        message: str,
        timeout: float | None = None,
        file_info: str | None = None,
    ):
        self.timeout = timeout
        self.file_info = file_info
        super().__init__(message)
```

### Example 2: InputError Exception Class

```python
class InputError(CodepictureError):
    """Input file validation failed.

    Examples: file not found, permission denied, unreadable file.

    Attributes:
        input_path: Path to the input that caused the error.
    """

    def __init__(self, message: str, input_path: str | None = None):
        self.input_path = input_path
        super().__init__(message)
```

### Example 3: Timeout Guard with Proper Shutdown

```python
import concurrent.futures

def generate_image_with_timeout(
    code: str,
    output_path: Path,
    config: RenderConfig,
    timeout: float | None = 30.0,
    language: str | None = None,
    filename: str | None = None,
) -> None:
    if timeout is None:
        # Timeout disabled (--timeout 0)
        _run_pipeline(code, output_path, config, language, filename)
        return

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        _run_pipeline, code, output_path, config, language, filename
    )
    try:
        future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        # Shut down without waiting for the thread to finish
        executor.shutdown(wait=False, cancel_futures=True)
        raise RenderTimeoutError(
            f"Rendering timed out after {timeout:.0f}s while processing "
            f"'{filename or '<stdin>'}'. "
            f"No output file written. "
            f"Try increasing the timeout with --timeout {int(timeout * 2)}",
            timeout=timeout,
            file_info=filename or "<stdin>",
        )
    else:
        executor.shutdown(wait=True)
```

### Example 4: CLI Error Handler with Exit Codes

```python
# In cli/app.py main()
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_TIMEOUT = 2

try:
    # ... pipeline ...
    pass
except RenderTimeoutError as e:
    err_console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(EXIT_TIMEOUT)
except CodepictureError as e:
    err_console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(EXIT_ERROR)
except Exception as e:
    err_console.print(f"[red]Error:[/red] Unexpected error: {e}")
    raise typer.Exit(EXIT_ERROR)
```

### Example 5: Atomic File Write in Orchestrator

```python
import os
import tempfile
import shutil

def _write_output_atomic(data: bytes, output_path: Path) -> None:
    """Write render result atomically -- complete file or nothing."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd = tempfile.NamedTemporaryFile(
        dir=output_path.parent,
        prefix=".codepicture-",
        suffix=output_path.suffix,
        delete=False,
    )
    tmp_path = tmp_fd.name
    try:
        tmp_fd.write(data)
        tmp_fd.close()
        shutil.move(tmp_path, str(output_path))
    except BaseException:
        tmp_fd.close()
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
```

### Example 6: Unsupported Language Fallback with Warning

```python
# In orchestrator.py, modify language detection:
import sys

def _resolve_language(
    highlighter: PygmentsHighlighter,
    code: str,
    language: str | None,
    filename: str | None,
) -> str:
    if language is not None:
        # Explicit language -- validate it exists, fallback to text
        try:
            highlighter.highlight("", language)  # validate
            return language
        except HighlightError:
            print(
                f"Warning: Unknown language '{language}', rendering as plain text.",
                file=sys.stderr,
            )
            return "text"
    if filename:
        return highlighter.detect_language(code, filename)
    return "text"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `signal.alarm()` for timeouts | `ThreadPoolExecutor` + `future.result(timeout=)` | Always preferred for C-extension-heavy code | Works with Cairo/Pango; cross-platform |
| Direct file write | Temp file + atomic move | Best practice | Prevents partial output on crash/timeout |
| Generic Exception + traceback | Structured error hierarchy + clean messages | Modern CLI best practice | Users see actionable messages, not stack traces |
| Single exit code (0 or 1) | Distinct exit codes per failure class | POSIX convention | Scripts can distinguish timeout from other errors |

**Deprecated/outdated:**
- `signal.alarm()`: Unix-only, main-thread-only, cannot interrupt C extensions. Not suitable for this project.
- `threading.Timer` + `thread.daemon`: Unreliable for timeout; daemon threads can leave resources in inconsistent state.

## Open Questions

1. **Thread cleanup on timeout**
   - What we know: The rendering thread cannot be killed after timeout. It will continue running until it finishes or the process exits.
   - What's unclear: For a CLI tool that exits after one render, this is fine (process exit cleans up). For future library use, this could leak threads.
   - Recommendation: Accept the limitation for now. Document it. A CLI tool exits immediately after printing the timeout error, so process cleanup handles everything. If library use is needed later, consider `multiprocessing.Process` with `.terminate()`.

2. **Unsupported language: error vs warning**
   - What we know: CONTEXT.md says "fall back to plain text rendering with stderr warning." Current code raises `HighlightError` for unknown languages.
   - What's unclear: Should the `HighlightError` be replaced with a fallback, or should both behaviors coexist (CLI falls back, library raises)?
   - Recommendation: Change the orchestrator to catch `HighlightError` for unknown languages and fall back to `"text"` with a stderr warning. The library layer (`PygmentsHighlighter`) continues to raise `HighlightError` -- the orchestrator handles the fallback policy.

3. **Where to add `--timeout` to config**
   - What we know: `--timeout` is a CLI flag. It's operational, not aesthetic.
   - What's unclear: Should `timeout` be added to `RenderConfig` (Pydantic model) or kept as a separate parameter?
   - Recommendation: Keep `timeout` as a separate CLI-level parameter, NOT in `RenderConfig`. Timeout is an execution concern (how long to wait), not a rendering concern (how the image looks). Pass it directly to the timeout wrapper function.

## Sources

### Primary (HIGH confidence)

- **Python 3.13 stdlib `concurrent.futures`** -- ThreadPoolExecutor API, `future.result(timeout=)`, `TimeoutError` exception, `shutdown(wait, cancel_futures)` parameters. Verified via runtime testing on Python 3.13.5.
- **Python 3.13 stdlib `tempfile`** -- `NamedTemporaryFile(delete=False)` behavior verified via runtime testing.
- **Codebase inspection** -- All findings about existing architecture (`errors.py`, `cli/app.py`, `cli/orchestrator.py`, `config/schema.py`, `render/renderer.py`) verified by reading source files directly.
- **Rich 14.3.1** -- Console TTY auto-detection, colored output. Already in use in `cli/app.py`. Verified via runtime.
- **Typer 0.21.1** -- `typer.Exit(code=N)` for exit code control. Already in use. Verified via runtime.

### Secondary (MEDIUM confidence)

- **Phase 8 verification report** -- Confirms pipeline renders in ~0.2s for normal files (MLIR test.mlir). Timeout of 30s gives >100x headroom for normal operation.
- **CONTEXT.md decisions** -- ThreadPoolExecutor requirement, 30s default, `--timeout 0` disables, distinct exit codes (0/1/2), atomic writes, structured error hierarchy.

### Tertiary (LOW confidence)

- None. All findings are verified against stdlib documentation or runtime behavior.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All stdlib or existing dependencies, verified via runtime
- Architecture: HIGH -- Building on well-understood existing codebase, clear patterns
- Pitfalls: HIGH -- ThreadPoolExecutor timeout behavior verified experimentally (thread continues running, cancel returns False, shutdown(wait=True) blocks)

**Research date:** 2026-01-30
**Valid until:** 2026-03-01 (stable -- stdlib and existing deps, unlikely to change)
