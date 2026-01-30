# Feature Landscape: v1.1 Hardening

**Domain:** Hardening a Python image-generation CLI (visual regression testing, rendering reliability, performance optimization)
**Project:** codepicture v1.1
**Researched:** 2026-01-30
**Confidence:** HIGH (patterns verified against existing codebase, tool documentation, and ecosystem research)

---

## Context: What Exists Today

Before defining what to build, here is what v1.0 already has:

- **260 tests, 80%+ coverage** across unit, integration, and CLI layers
- **Test fixtures** for 5 languages: Python, Rust, C++, JavaScript, MLIR (`tests/fixtures/`)
- **Rendering tests** that verify PNG magic bytes, SVG `<svg` tags, PDF `%PDF` headers, and dimensional correctness
- **CLI tests** via both Typer's CliRunner (unit) and subprocess (integration)
- **GitHub Actions CI** on ubuntu-latest with coverage upload to Codecov
- **pytest markers** for `slow` tests, randomized test ordering (`pytest-randomly`)
- **Known bug:** `test.mlir` at project root hangs the rendering pipeline indefinitely

**What is missing:** No test verifies that rendered images look *correct*. No timeout protection. No performance baselines. The test suite can hang indefinitely if a lexer or renderer stalls.

---

## Table Stakes

Features the project must have for v1.1 to claim "hardened." Missing any of these means the reliability story is incomplete.

### 1. Test Timeouts (pytest-timeout)

| Aspect | Detail |
|--------|--------|
| **Why Expected** | Without per-test timeouts, a single hanging test blocks the entire CI run. The existing `test.mlir` hang would stall GitHub Actions indefinitely. This is the simplest, highest-value safety net. |
| **Complexity** | Low |
| **Existing Infrastructure** | `pyproject.toml` already has `[tool.pytest.ini_options]` with markers. Just add `timeout = 30`. Dev deps use `pytest>=9.0.2`. |
| **What to Build** | Add `pytest-timeout` to dev dependencies. Set global default timeout (30s) in `pyproject.toml`. Use `@pytest.mark.timeout(60)` for known-slow rendering tests if needed. The existing `slow` marker can coexist. |
| **Implementation Notes** | `pytest-timeout` uses SIGALRM on POSIX by default, which cleanly interrupts hanging tests without killing the process. The thread method is available as fallback. Current version is 2.4.0+. |
| **Confidence** | HIGH |

### 2. CI Job Timeout

| Aspect | Detail |
|--------|--------|
| **Why Expected** | The GitHub Actions workflow (`test.yml`) has no `timeout-minutes`. If every test hangs, the runner burns for 6 hours (GitHub's default). This costs runner minutes and blocks the pipeline. |
| **Complexity** | Trivial |
| **Existing Infrastructure** | `.github/workflows/test.yml` exists with a single `test` job. |
| **What to Build** | Add `timeout-minutes: 10` to the job definition. This is defense-in-depth alongside pytest-timeout. |
| **Confidence** | HIGH |

### 3. MLIR Lexer Hang Fix

| Aspect | Detail |
|--------|--------|
| **Why Expected** | Known bug. `test.mlir` at project root contains real-world MLIR (device topology, HAL attributes, flow transfers) that hangs the custom lexer indefinitely. The simpler `tests/fixtures/sample_mlir.mlir` works fine. This is the specific reliability failure motivating v1.1. |
| **Complexity** | Medium |
| **Existing Infrastructure** | `codepicture/highlight/mlir_lexer.py` is a Pygments `RegexLexer`. The test suite (`tests/highlight/test_mlir_lexer.py`) has 25+ token tests but only exercises the simple fixture, not the adversarial `test.mlir`. |
| **What to Build** | (a) Diagnose which regex pattern causes catastrophic backtracking on `test.mlir` content -- likely nested attribute patterns like `#hal.device.topology<links = [...]>` with recursive angle brackets. (b) Fix the regex to avoid exponential backtracking. (c) Add `test.mlir` as a test fixture with a timeout assertion. (d) Add additional adversarial MLIR patterns as regression tests. |
| **Implementation Notes** | Pygments `RegexLexer` processes input line-by-line with regex patterns. Catastrophic backtracking happens when a pattern like `<[^>]*>` encounters nested `<` characters. The fix is typically to use non-greedy quantifiers or explicitly enumerate expected characters. The `re` module has no built-in timeout; the fix must be in the regex itself. |
| **Confidence** | HIGH -- catastrophic regex backtracking is well-understood |

### 4. Rendering Timeout Guards (Application-Level)

| Aspect | Detail |
|--------|--------|
| **Why Expected** | Even after fixing the MLIR lexer, future inputs could trigger new hangs in the lexer, layout engine, or Cairo renderer. A hardened CLI must have a maximum execution time for any render operation. |
| **Complexity** | Low-Medium |
| **Existing Infrastructure** | The rendering pipeline flows: CLI -> highlight (Pygments) -> layout (Pango) -> render (Cairo) -> save. All synchronous, single-threaded. |
| **What to Build** | A timeout wrapper around the full rendering pipeline. If any stage exceeds a configurable limit (default 30s, overridable via `--timeout`), abort with a clear error message and non-zero exit code. |
| **Implementation Notes** | On POSIX: `signal.alarm(N)` with a SIGALRM handler that raises `TimeoutError`. Simple, zero-overhead, works for the CLI path. For library usage or non-POSIX: `concurrent.futures.ProcessPoolExecutor` with `.result(timeout=N)` is more portable but heavier. Recommend signal-based for CLI, with a clean `RenderTimeoutError` exception type. |
| **Confidence** | HIGH |

### 5. Visual Regression Test Suite (Golden Image Snapshots)

| Aspect | Detail |
|--------|--------|
| **Why Expected** | Current rendering tests only check output format headers (PNG magic bytes, SVG tags). They do NOT verify the image *looks correct*. A regression that produces valid-but-wrong images (wrong colors, broken layout, missing text) passes all current tests silently. This is the biggest gap in the existing test suite. |
| **Complexity** | Medium |
| **Existing Infrastructure** | Fixture files exist for 5 languages. Rendering pipeline produces `RenderResult` with `.data` bytes. `Pillow` is already a dependency. CI runs on ubuntu-latest (single platform). |
| **What to Build** | For each core language fixture, render a reference PNG image (golden file) and store it in `tests/snapshots/`. On each test run, re-render and compare pixel-by-pixel using `pixelmatch-py` or `pytest-image-snapshot`. Fail if difference exceeds threshold. Provide `--snapshot-update` flag for intentional baseline updates. |
| **Key Design Decisions** | |
| *Format* | PNG only for comparisons. SVG text varies across platforms. PDF is binary-opaque. |
| *Platform* | Generate goldens in CI (Linux only). Developer machines (macOS) will not match exactly due to different Pango/fontconfig/FreeType rendering. Run visual regression only in CI, or use generous thresholds locally. |
| *Threshold* | Start with `threshold=0.1` in pixelmatch (range 0-1, lower = stricter). Tune based on actual cross-run variance. Font anti-aliasing can cause 1-2% pixel differences even on the same platform. |
| *Test Matrix* | 5 languages x 2 themes (dark + light) x 1 config (default) = 10 golden images. Optionally: +5 images for chrome/shadow/line-number variants = 15 total. This is manageable in git storage (~50-200KB per PNG). |
| *Tool Choice* | `pytest-image-snapshot` (0.4.5) provides a pytest fixture that handles snapshot creation, comparison, diff image generation, and `--snapshot-update` CLI flag. Uses `pixelmatch` under the hood when installed. Recommend this over rolling custom comparison logic. |
| **Confidence** | HIGH for approach; MEDIUM for cross-platform pixel matching (known hard problem) |

### 6. Rendering Reliability Matrix (Parametrized Integration Tests)

| Aspect | Detail |
|--------|--------|
| **Why Expected** | The project supports 5 core languages x 3 output formats (PNG/SVG/PDF) x several feature toggles (shadow, chrome, line numbers). Current tests exercise some combinations but not systematically. A regression in one combination could go undetected. |
| **Complexity** | Medium |
| **Existing Infrastructure** | `tests/test_render_renderer.py` tests PNG/SVG/PDF individually. `conftest.py` provides `render_tokens` and `render_metrics` fixtures. Fixture files exist for all 5 languages. |
| **What to Build** | Parametrized tests using `@pytest.mark.parametrize` across: (a) 5 language fixtures, (b) 3 output formats, (c) 2-3 feature configs (minimal, full-chrome, line-numbers-only). Assert: completes within timeout, produces valid output (format headers), non-zero dimensions. This is ~30-45 test cases from a single test function. |
| **Implementation Notes** | Use indirect fixtures to load each language's source from `tests/fixtures/`. Highlight with the appropriate lexer. Render with each config. This tests the full pipeline end-to-end for each combination. |
| **Confidence** | HIGH |

### 7. Error Handling Audit

| Aspect | Detail |
|--------|--------|
| **Why Expected** | A hardened CLI must not crash with Python tracebacks. Every failure mode should produce a clear error message and non-zero exit code. Current `test_errors.py` covers some cases but rendering failures (timeout, OOM, corrupt input) are not tested. |
| **Complexity** | Low-Medium |
| **Existing Infrastructure** | `src/codepicture/errors.py` exists. `tests/test_errors.py` (3KB) and `tests/test_cli.py` error class both test some error paths. |
| **What to Build** | (a) Catalog all failure modes: bad input file, unsupported language, lexer timeout/crash, layout failure, render failure, disk write failure, invalid config. (b) Ensure each produces a user-friendly error via `typer.Exit(code=1)` or equivalent. (c) Add tests for the newly possible `RenderTimeoutError` path. (d) Verify no Python tracebacks leak to users in any error scenario. |
| **Confidence** | HIGH |

---

## Differentiators

Features that go beyond basic hardening. Not required for v1.1 but demonstrate engineering maturity.

### 1. Fuzz Testing for Lexer Robustness (hypothesis)

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | The MLIR lexer hang is exactly the class of bug that fuzz testing catches. Property-based testing with `hypothesis` can generate adversarial inputs that exercise pathological regex patterns. |
| **Complexity** | Medium |
| **What to Build** | `@given(st.text())` tests asserting: for any string input, the MLIR lexer terminates within 5 seconds and does not raise unhandled exceptions. Combine with `@pytest.mark.timeout(10)`. |
| **Notes** | Very high value-per-effort for the custom MLIR lexer. Low priority for Pygments built-in lexers (already battle-tested by the Pygments community). Could be marked `slow` and run only in CI. |

### 2. Performance Benchmarks (pytest-benchmark)

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | Track rendering time across commits. Detect regressions where a change makes rendering 2x slower. Establishes a performance baseline for each fixture. |
| **Complexity** | Medium |
| **What to Build** | Benchmark tests for: (a) lexing time per language fixture, (b) layout calculation, (c) full PNG render. Use `pytest-benchmark` with `--benchmark-json` for CI artifact storage. |
| **Notes** | The primary performance concern now is infinite time (hang), not slow-but-finite rendering. Benchmarks are more valuable *after* fixing the hang. Typical code screenshot rendering should be <1s; set assertions at <5s as a regression guard. |

### 3. Memory Usage Guards for Large Files

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | Cairo surfaces for 1000+ line files can consume significant memory. A large-file test with `tracemalloc` assertions prevents silent memory regressions. |
| **Complexity** | Low-Medium |
| **What to Build** | Test that renders a 500-line and 1000-line file, asserts peak memory stays below threshold (e.g., 100MB). Use `tracemalloc` snapshots. |
| **Notes** | Only relevant if users render large files. For typical 10-50 line code screenshots, memory is not a concern. Low priority for v1.1. |

### 4. Diff Image Artifact Upload in CI

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | When a visual regression test fails in CI, upload the actual image, expected image, and diff image as GitHub Actions artifacts. Makes debugging visual failures trivial without reproducing locally. |
| **Complexity** | Low |
| **What to Build** | Add `actions/upload-artifact@v4` step in `test.yml` that uploads `tests/snapshots/*_diff.png` on test failure. `pytest-image-snapshot` generates diff images automatically. |
| **Notes** | Near-zero effort if using `pytest-image-snapshot`, which writes diff images to a predictable path. |

### 5. Structured Verbose/Debug Output

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | When rendering fails or is slow, structured timing output per pipeline stage (lex: 0.2s, layout: 0.1s, render: 4.5s) makes diagnosis immediate. |
| **Complexity** | Low |
| **What to Build** | Extend the existing `--verbose` flag to include timing per stage. Format: `[lex] 0.23s | [layout] 0.11s | [render] 2.45s | [save] 0.08s`. |
| **Notes** | `--verbose` already exists and shows processing steps. Adding timing is a small extension. |

---

## Anti-Features

Features to deliberately NOT build for v1.1. Common over-engineering traps for testing and reliability work.

### 1. DO NOT: Build a Custom Image Diff Viewer

| **Why Avoid** | Tempting to create a web UI or terminal-based diff viewer for visual regression results. This is scope creep for a hardening milestone. |
| **What to Do Instead** | Use `pytest-image-snapshot`'s built-in diff image output. Upload as CI artifacts. View in the GitHub Actions artifact browser or locally in any image viewer. |

### 2. DO NOT: Test Every Theme in Visual Regression

| **Why Avoid** | There are 55+ Pygments themes. Testing every theme x every language x every config is a combinatorial explosion (~800+ golden images). Storage bloat, 10+ minute CI, brittle tests that break on Pygments upgrades. |
| **What to Do Instead** | Test 2 representative themes: one dark (catppuccin-mocha, the default), one light or high-contrast (dracula). This covers the color mapping path without explosion. Theme loading is already unit-tested separately. |

### 3. DO NOT: Chase Pixel-Perfect Cross-Platform Matching

| **Why Avoid** | Cairo/Pango renders differently on macOS vs Linux due to font rendering backends (CoreText vs FreeType/fontconfig). Chasing pixel-perfect parity across platforms is an endless rabbit hole. Different FreeType versions on different Ubuntu releases also produce subtly different results. |
| **What to Do Instead** | Generate golden images on a single platform (ubuntu-latest in CI). Run visual regression tests only in CI. Use a tolerance threshold. Accept that local macOS development may produce slightly different pixels. |

### 4. DO NOT: Add Parallel/Async Rendering

| **Why Avoid** | The CLI processes one file at a time. Adding asyncio or multiprocessing for parallel rendering adds complexity with zero user-facing benefit for the current use case. |
| **What to Do Instead** | Keep the single-threaded pipeline. The signal-based timeout guard is sufficient. If batch processing is needed later, that is a feature milestone, not hardening. |

### 5. DO NOT: Over-Engineer the Timeout Architecture

| **Why Avoid** | Tempting to build per-stage timeouts (lexer: 5s, layout: 5s, render: 10s, save: 5s) with retry logic and escalating termination strategies. This adds complexity without proportional reliability gain. |
| **What to Do Instead** | One timeout wrapping the entire render pipeline. If it exceeds the limit, fail with a clear message. Fix root causes (regex backtracking) rather than papering over them with elaborate timeout hierarchies. |

### 6. DO NOT: Build a Performance Dashboard

| **Why Avoid** | Tools like Bencher for tracking benchmark history across commits are valuable for large projects but overkill for a CLI tool. The main issue is not "rendering got 10% slower" but "rendering hangs forever." |
| **What to Do Instead** | Fix the hang. Add simple threshold assertions (render < 5s) if needed. Use `pytest-benchmark` locally for one-off profiling. A dashboard is warranted only if performance regressions become a recurring problem. |

### 7. DO NOT: Add Multi-OS CI Matrix for Visual Tests

| **Why Avoid** | Running visual regression on macOS + Linux + Windows triples CI time and requires per-platform golden images. Platform rendering differences are expected and not bugs. |
| **What to Do Instead** | Single platform (ubuntu-latest). Unit tests and CLI tests can run on multiple platforms. Visual regression is Linux-only. |

---

## Feature Dependencies

```
Test Timeouts (pytest-timeout) -----> ALL other test features
  [Safety net -- must be first]        (prevents CI hangs during development of new tests)

CI Job Timeout -----> ALL CI features
  [5-minute fix]      (prevents runaway CI regardless of test-level timeouts)

MLIR Lexer Hang Fix -----> Visual Regression Tests
  [Root cause fix]         (cannot generate correct golden images if MLIR hangs)
                    \
                     +---> Rendering Reliability Matrix
                           (cannot parametrize MLIR tests if lexer hangs)

Rendering Timeout Guards -----> Error Handling Audit
  [New error type]               (must test the timeout error path)

Visual Regression Suite -----> CI Diff Artifact Upload
  [Generates diff images]       (upload only makes sense if VRT exists)
```

**Critical path:** Test timeouts -> MLIR fix -> rendering timeout guards -> visual regression suite -> CI artifact upload

---

## MVP Recommendation

For v1.1 hardening milestone, prioritize in this order:

**Phase 1: Safety nets (immediate)**
1. Test timeouts (`pytest-timeout`) -- 30 minutes of work, immediate CI protection
2. CI job timeout -- 5 minutes of work, prevents runaway GitHub Actions

**Phase 2: Root cause fix**
3. MLIR lexer hang fix -- the specific bug motivating this milestone
4. Application-level rendering timeout guards -- defense in depth

**Phase 3: Correctness verification**
5. Rendering reliability matrix -- parametrized tests across languages/formats/configs
6. Visual regression test suite -- golden image snapshot comparisons
7. Error handling audit -- clean error messages for all failure modes

**Defer to post-v1.1:**
- Performance benchmarks (pytest-benchmark) -- fix reliability first, optimize later
- Fuzz testing (hypothesis) -- high value but separate effort after lexer stabilized
- Memory profiling -- only relevant for large-file use cases
- Cross-platform visual consistency -- only if users report platform-specific issues
- Diff artifact upload -- nice CI convenience, add after VRT is stable

---

## Sources

**Tool Documentation (HIGH confidence):**
- [pytest-timeout on PyPI](https://pypi.org/project/pytest-timeout/) -- v2.4.0, SIGALRM and thread methods
- [pytest-image-snapshot on GitHub](https://github.com/bmihelac/pytest-image-snapshot) -- v0.4.5, pytest fixture for image snapshot comparison
- [pixelmatch-py on GitHub](https://github.com/whtsky/pixelmatch-py) -- pixel-level image comparison with anti-aliasing detection
- [pytest-benchmark on PyPI](https://pypi.org/project/pytest-benchmark/) -- v5.2.3, benchmarking fixture

**Pattern Research (MEDIUM confidence):**
- [pytest-timeout usage patterns](https://pytest-with-eric.com/pytest-best-practices/pytest-timeout/) -- SIGALRM vs thread method tradeoffs
- [Golden file testing patterns 2025](https://johal.in/pytest-regressions-data-golden-file-updates-2025/) -- snapshot testing evolution in Python

**Codebase Analysis (HIGH confidence):**
- `tests/conftest.py` -- 13 fixtures, rendering helpers, font registration
- `tests/test_render_renderer.py` -- current rendering tests (format headers only)
- `tests/test_cli.py` -- CLI unit + integration tests
- `tests/fixtures/` -- 5 language fixture files (Python, Rust, C++, JavaScript, MLIR)
- `.github/workflows/test.yml` -- CI config (no timeout, single ubuntu-latest runner)
- `pyproject.toml` -- dev deps, pytest config, coverage settings
- `test.mlir` (project root) -- the file that triggers the known hang bug
