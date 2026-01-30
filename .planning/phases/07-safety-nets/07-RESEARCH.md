# Phase 7: Safety Nets - Research

**Researched:** 2026-01-30
**Domain:** pytest-timeout plugin, GitHub Actions job timeouts, test suite safety
**Confidence:** HIGH

## Summary

Phase 7 adds two layers of timeout protection: pytest-timeout for individual test timeouts and GitHub Actions `timeout-minutes` for CI job-level safety. This is a well-understood domain with mature, stable tooling.

The project has 260 tests that currently pass in ~31 seconds total. Duration profiling reveals ~14 tests that exceed 1 second (the slowest at 2.33s), all in `test_render_renderer.py` and `test_cli.py`. These need `@pytest.mark.slow` markers. The `slow` marker is already declared in `pyproject.toml` but not yet used by any test. No test currently approaches the 5s default timeout, so enabling pytest-timeout should be non-disruptive.

The project uses `uv` for dependency management, pytest 9.x, and has an existing GitHub Actions workflow at `.github/workflows/test.yml` with a single `test` job and no timeout configured. The `test.mlir` file exists at the repo root but is not referenced by any test -- it is the known-hanging file mentioned in context.

**Primary recommendation:** Install `pytest-timeout>=2.4.0` with `signal` method, configure 5s default in `pyproject.toml`, mark ~14 slow tests, and add `timeout-minutes: 10` to the GHA job.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest-timeout | >=2.4.0 | Per-test timeout enforcement | Only maintained pytest timeout plugin; 2.4.0 is current stable (May 2025) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| actions/upload-artifact | v4 | Upload test output on CI failure | When CI job times out or tests fail, for diagnosis |

**Note on upload-artifact version:** v4 is the widely deployed stable version. v6 exists but requires Actions Runner 2.327.1+. Use v4 for maximum compatibility with GitHub-hosted runners, which is what this project uses.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest-timeout | func_timeout / wrapt_timeout_decorator | pytest-timeout is purpose-built for pytest; alternatives require manual wrapping per-test |
| pytest-timeout signal method | pytest-timeout thread method | Thread method terminates the entire process on timeout (no teardown, no JUnit XML); signal is cleaner but POSIX-only. Since CI runs on Ubuntu and macOS dev machines are also POSIX, signal is appropriate |

**Installation:**
```bash
uv add --dev pytest-timeout
```

## Architecture Patterns

### Configuration in pyproject.toml

All timeout configuration lives in `pyproject.toml` under `[tool.pytest.ini_options]`, consistent with existing pytest config:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
timeout = 5
timeout_method = "signal"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

Key points:
- `timeout = 5` sets the global default (5 seconds per test)
- `timeout_method = "signal"` uses SIGALRM (clean, allows pytest to continue)
- Per-test override via `@pytest.mark.timeout(15)` for slow tests
- The `slow` marker is already declared -- just needs to be applied to tests

### Per-Test Timeout Override Pattern

For tests that legitimately need more time:

```python
@pytest.mark.slow
@pytest.mark.timeout(15)
def test_render_different_themes():
    ...
```

Both markers should be applied together: `slow` for filtering (`-m 'not slow'`) and `timeout(15)` for the actual limit.

### GitHub Actions Job Timeout Pattern

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      ...
```

The `timeout-minutes` key goes directly on the job, not the workflow. This is the outer safety net -- if pytest-timeout somehow fails to kill a hanging test, the entire job is cancelled after 10 minutes.

### Artifact Upload on Failure Pattern

```yaml
- name: Run tests with coverage
  id: tests
  run: uv run pytest --cov --cov-report=xml --cov-report=term 2>&1 | tee test-output.txt
  continue-on-error: true

- name: Upload test output on failure
  if: steps.tests.outcome == 'failure'
  uses: actions/upload-artifact@v4
  with:
    name: test-output
    path: test-output.txt
    retention-days: 7

- name: Fail if tests failed
  if: steps.tests.outcome == 'failure'
  run: exit 1
```

This pattern captures test output to a file, uploads it as an artifact only on failure, then re-fails the step. The `continue-on-error` + re-fail pattern is needed because `tee` would mask the exit code otherwise.

**Alternative (simpler):** Redirect output to file and use `$?` to preserve exit code:

```yaml
- name: Run tests with coverage
  run: |
    uv run pytest --cov --cov-report=xml --cov-report=term 2>&1 | tee test-output.txt
    exit ${PIPESTATUS[0]}

- name: Upload test output on failure
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: test-output
    path: test-output.txt
    retention-days: 7
```

Using `if: failure()` is the standard GitHub Actions idiom for "run this step only if a previous step failed." Combined with `set -o pipefail` (bash default in GHA) or explicit `${PIPESTATUS[0]}`, this cleanly captures output while preserving the failure signal.

### Anti-Patterns to Avoid
- **Workflow-level timeout instead of job-level:** `timeout-minutes` at the workflow level does not exist in GitHub Actions; it must be per-job.
- **Using thread method on POSIX:** Thread method terminates the entire pytest process on timeout, losing all subsequent test results and coverage data. Signal method allows the test suite to continue.
- **Setting timeout=0 to disable:** This disables timeout for that test. The context explicitly requires every test to have a limit. Never use `timeout=0`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Per-test timeouts | `signal.alarm()` in conftest | pytest-timeout plugin | Handles fixtures, teardown, stack traces, cross-platform, pytest integration |
| Timeout summary reporting | Custom conftest hook | pytest-timeout's built-in reporting | Plugin already dumps all thread stacks on timeout, appears as FAILED with clear reason |
| CI job timeout | Custom watchdog script | `timeout-minutes` on GHA job | Built-in, reliable, no maintenance |
| Artifact upload | Custom script to save logs | `actions/upload-artifact@v4` | Standard GHA action, handles retention, accessible from UI |

**Key insight:** Both timeout layers (pytest-timeout and GHA timeout-minutes) are single-line configuration changes. There is nothing to "build" here -- this is purely configuration.

## Common Pitfalls

### Pitfall 1: Timeout Too Aggressive for CI
**What goes wrong:** Tests pass locally (fast machine) but timeout in CI (shared runner, slower).
**Why it happens:** GitHub Actions runners are slower than local dev machines. Tests near the timeout boundary become flaky.
**How to avoid:** The 5s default is generous given the slowest test is 2.33s. The 15s slow timeout gives 6x headroom over the current slowest test. Current total suite time is ~31s, well within the 10-minute job timeout.
**Warning signs:** Tests that pass locally but timeout in CI.

### Pitfall 2: Signal Method and SIGALRM Conflicts
**What goes wrong:** pytest-timeout's signal method uses SIGALRM. If test code or fixtures also use SIGALRM, they can interfere.
**Why it happens:** Only one SIGALRM handler can be active at a time on POSIX.
**How to avoid:** This project does not use SIGALRM anywhere (it's a code-to-image tool using Cairo/Pango). No conflict expected.
**Warning signs:** Random timeout failures in tests that shouldn't be slow.

### Pitfall 3: Forgetting to Mark Slow Tests
**What goes wrong:** Tests over 2s are not marked `@pytest.mark.slow`, so they can't be skipped locally.
**Why it happens:** Easy to forget the audit step.
**How to avoid:** Phase 7 explicitly includes auditing all tests. The `--durations=20` output (see Current Test Timings below) identifies exactly which tests need marking.
**Warning signs:** `pytest -m 'not slow'` still takes a long time.

### Pitfall 4: Artifact Upload Masking Failure
**What goes wrong:** Using `continue-on-error: true` without re-failing causes CI to appear green when tests actually failed.
**Why it happens:** `continue-on-error` marks the step as successful regardless of exit code.
**How to avoid:** Always re-fail after artifact upload, or use `if: failure()` pattern which doesn't require `continue-on-error`.

### Pitfall 5: test.mlir Hanging Test Not Skipped
**What goes wrong:** If the known-hanging `test.mlir` file gets picked up by a test, it hangs the suite.
**Why it happens:** Context mentions this file hangs and should be skipped until Phase 8.
**How to avoid:** The `test.mlir` file at the repo root is NOT referenced by any existing test. No test imports or reads it. The MLIR lexer tests use `tests/fixtures/sample_mlir.mlir` which works fine. No skip is currently needed -- there is no test that triggers the hang. If a test is added that uses `test.mlir`, it should be marked with `@pytest.mark.skip(reason="hangs -- fix in Phase 8")`.
**Current status:** No action needed for `test.mlir` -- it is not under test.

## Code Examples

### pyproject.toml Configuration (Complete)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
timeout = 5
timeout_method = "signal"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

Source: pytest-timeout official docs (PyPI/GitHub README)

### Marking a Slow Test

```python
import pytest

@pytest.mark.slow
@pytest.mark.timeout(15)
def test_render_different_themes():
    """This test renders multiple themes and takes >2s."""
    ...
```

Source: pytest-timeout official docs

### GitHub Actions Workflow with Timeout and Artifact Upload

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.13

      - name: Install dependencies
        run: uv sync --locked --dev

      - name: Run tests with coverage
        run: |
          uv run pytest --cov --cov-report=xml --cov-report=term 2>&1 | tee test-output.txt
          exit ${PIPESTATUS[0]}

      - name: Upload test output on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: test-output
          path: test-output.txt
          retention-days: 7

      - name: Upload coverage to Codecov
        if: success()
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
          fail_ci_if_error: false
```

Source: GitHub Actions docs, actions/upload-artifact README

## Current Test Timings (Audit Data)

Tests exceeding 2 seconds (need `@pytest.mark.slow` + `@pytest.mark.timeout(15)`):

| Test | Duration | File |
|------|----------|------|
| `TestRendererIntegration::test_render_different_themes` | 2.33s | `tests/test_render_renderer.py` |

Tests between 1-2 seconds (within 5s default, but candidates for `@pytest.mark.slow`):

| Test | Duration | File |
|------|----------|------|
| `TestRendererWithShadow::test_png_with_shadow_produces_larger_output` | 1.87s | `tests/test_render_renderer.py` |
| `TestRendererIntegration::test_full_render_with_all_features` | 1.80s | `tests/test_render_renderer.py` |
| `TestRendererPNG::test_render_png_with_line_numbers` | 1.57s | `tests/test_render_renderer.py` |
| `TestCliIntegration::test_cli_silent_on_success` | 1.52s | `tests/test_cli.py` |
| `TestCliIntegration::test_cli_generate_subprocess` | 1.48s | `tests/test_cli.py` |
| `TestCliVerbose::test_verbose_shows_steps` | 1.32s | `tests/test_cli.py` |
| `TestCliGeneration::test_stdin_with_language` | 1.32s | `tests/test_cli.py` |
| `TestCliGeneration::test_config_file` | 1.32s | `tests/test_cli.py` |
| `TestCliGeneration::test_generate_svg` | 1.31s | `tests/test_cli.py` |
| `TestCliGeneration::test_theme_flag` | 1.29s | `tests/test_cli.py` |
| `TestCliGeneration::test_generate_png` | 1.29s | `tests/test_cli.py` |
| `TestCliGeneration::test_format_flag_overrides_extension` | 1.28s | `tests/test_cli.py` |
| `TestCliGeneration::test_creates_parent_directories` | 1.27s | `tests/test_cli.py` |

The context says to mark tests >2 seconds as slow. Only 1 test (2.33s) strictly exceeds 2 seconds. However, 13 more are between 1-2 seconds and may be slower on CI runners. **Recommendation:** Mark all tests above 1.2s as `@pytest.mark.slow` since CI runners are typically 1.5-2x slower than local machines, which would push the 1.2s+ tests over 2s in CI.

Total: ~14 tests to mark as slow across 2 files (`test_render_renderer.py` and `test_cli.py`).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No test timeouts | pytest-timeout plugin | Stable since 2015+ | Standard practice for CI safety |
| Manual CI timeout scripts | `timeout-minutes` on GHA jobs | Available since GHA launch (2019) | Built-in, no maintenance |
| upload-artifact@v3 | upload-artifact@v4 | 2023 | v4 uses new artifact backend; v3 deprecated |

**Deprecated/outdated:**
- `upload-artifact@v3`: Deprecated, uses legacy artifact backend
- pytest-timeout thread method on POSIX: Works but loses teardown and subsequent test results

## Open Questions

1. **Exact threshold for `@pytest.mark.slow`**
   - What we know: Context says ">2 seconds." Only 1 test is currently >2s locally. But CI is slower.
   - What's unclear: Whether to mark the 1.2-2.0s tests as slow too (they'd likely exceed 2s on CI).
   - Recommendation: Mark all tests currently >1.2s. This gives developers a fast local `-m 'not slow'` experience and accounts for CI slowness. The planner can decide the exact threshold.

2. **Timed-out test summary section**
   - What we know: Context wants timed-out tests listed separately in summary. pytest-timeout marks them as FAILED with "Timeout" in the message and dumps stack traces.
   - What's unclear: Whether the default pytest-timeout reporting is sufficient or if a custom conftest hook is needed.
   - Recommendation: Start with pytest-timeout's default reporting (it's already clear). If insufficient, a `pytest_terminal_summary` hook in conftest.py can filter and re-list timeout failures. This is a Claude's Discretion item.

## Sources

### Primary (HIGH confidence)
- pytest-timeout PyPI page (v2.4.0, May 2025) -- configuration options, methods, behavior
- pytest-timeout GitHub README -- detailed signal vs thread explanation, per-test markers, pyproject.toml config
- Project's own `pyproject.toml` -- current pytest config, markers, dependencies
- Project's own `.github/workflows/test.yml` -- current CI workflow structure
- Project's own test suite -- `uv run pytest --durations=20` timing audit (260 tests, 30.64s total)
- actions/upload-artifact GitHub page -- v4 usage, YAML syntax

### Secondary (MEDIUM confidence)
- GitHub Actions docs -- `timeout-minutes` per-job configuration, `if: failure()` syntax

### Tertiary (LOW confidence)
- None -- all findings verified with primary or secondary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- pytest-timeout is the only maintained pytest timeout plugin; verified version and config via PyPI and GitHub
- Architecture: HIGH -- configuration is straightforward pyproject.toml + GHA YAML; verified against existing project files
- Pitfalls: HIGH -- derived from actual test timing data and verified pytest-timeout behavior
- Audit data: HIGH -- generated from actual `pytest --durations=20` run against the live test suite

**Research date:** 2026-01-30
**Valid until:** 2026-03-01 (stable domain, unlikely to change)
