# Technology Stack: v1.1 Reliability Milestone Additions

**Project:** codepicture
**Milestone:** v1.1 -- Reliability, Visual Regression, Performance
**Researched:** 2026-01-30
**Overall confidence:** HIGH

## Context

The v1.0 stack is validated and shipping (Python 3.13+, PyCairo, Pygments, Typer, Pydantic, pytest). This document covers ONLY the stack additions needed for three new capabilities:

1. Visual regression testing (image comparison in CI)
2. Performance profiling (benchmark rendering, detect regressions)
3. Rendering reliability (timeouts for hanging renders)

## Recommended Additions

### Visual Regression Testing

| Library | Version | Purpose | Why This One |
|---------|---------|---------|--------------|
| pixelmatch | 0.3.0 | Pixel-level image comparison | Purpose-built for screenshot comparison in tests. Anti-aliasing detection prevents false positives on font rendering differences. Perceptual color difference metrics. Works with PIL.Image (Pillow already in deps). No heavyweight dependencies like OpenCV. |
| Pillow | (already in deps) | Image loading, diff visualization | Already a project dependency (>=10.0). `ImageChops.difference()` provides quick diff images. `Image.open()` loads reference snapshots. |

**Why pixelmatch over alternatives:**

| Option | Verdict | Reason |
|--------|---------|--------|
| **pixelmatch** | **USE** | Lightweight (pure Python), anti-aliasing aware, configurable threshold, returns mismatch count for assertions. Originally built for screenshot testing. |
| pytest-image-snapshot | SKIP | Adds a fixture layer on top of pixelmatch. We want direct control over comparison logic (threshold per test, custom diff output). Adding our own thin wrapper around pixelmatch is ~20 lines and avoids a plugin dependency. |
| pytest-image-diff | SKIP | Depends on Pillow + additional dependencies. Less popular. Plugin-based approach limits flexibility. |
| Pillow ImageChops only | SKIP | `ImageChops.difference().getbbox()` works for exact matches but has no anti-aliasing tolerance. Font rendering on different platforms produces anti-aliased pixels that differ by 1-2 values -- this causes false failures without pixelmatch's AA detection. |
| OpenCV (cv2) | SKIP | Massive dependency (~50MB). SSIM comparison is overkill for pixel-exact screenshot testing. Adds native compilation complexity to CI. |
| visual-comparison | SKIP | Requires OpenCV. Draws rectangles on differences -- visual but not useful for CI assertions. |

**Integration pattern:**

```python
# tests/conftest.py or tests/visual/conftest.py
import pytest
from pathlib import Path
from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

@pytest.fixture
def assert_image_match():
    """Compare a rendered image against a reference snapshot."""
    def _compare(actual: Image.Image, snapshot_name: str, threshold: float = 0.1):
        ref_path = SNAPSHOT_DIR / f"{snapshot_name}.png"
        if not ref_path.exists():
            # First run: save as reference
            actual.save(ref_path)
            pytest.skip(f"Created reference snapshot: {ref_path}")

        expected = Image.open(ref_path)
        assert actual.size == expected.size, (
            f"Size mismatch: {actual.size} vs {expected.size}"
        )

        # Create diff image for debugging
        diff = Image.new("RGBA", actual.size)
        num_diff = pixelmatch(actual, expected, diff, threshold=threshold)

        if num_diff > 0:
            diff_path = ref_path.with_suffix(".diff.png")
            diff.save(diff_path)

        assert num_diff == 0, (
            f"{num_diff} pixels differ. Diff saved to {diff_path}"
        )
    return _compare
```

**Snapshot management in CI:**
- Store reference snapshots in `tests/snapshots/` under version control
- Generate on one platform only (macOS or Linux) to avoid cross-platform font rendering differences
- Use `--update-snapshots` flag (custom pytest flag) to regenerate references
- Save diff images as CI artifacts on failure for debugging

### Performance Profiling

| Library | Version | Purpose | Why This One |
|---------|---------|---------|--------------|
| pytest-benchmark | 5.2.3 | Benchmark rendering functions | Native pytest integration. Calibrated timing with statistical rigor (rounds, warmup, outlier detection). Regression detection via `--benchmark-compare`. Built-in cProfile integration via `--benchmark-cprofile`. Actively maintained (Nov 2025 release). |
| snakeviz | 2.2.2 | Profile visualization (dev only) | Browser-based visualization of cProfile output. Icicle charts make hotspots obvious. Not a test dependency -- developer tool for investigating slow paths. |

**Why pytest-benchmark over alternatives:**

| Option | Verdict | Reason |
|--------|---------|--------|
| **pytest-benchmark** | **USE** | Already uses pytest (260 tests). Statistical rigor (min/max/mean/stddev). `--benchmark-compare` detects regressions in CI. `--benchmark-cprofile` gives per-function breakdown. Python 3.13 fixes landed in v5.2.x. |
| time.perf_counter manually | SKIP | No statistical rigor. No CI regression detection. Reinventing the wheel. |
| asv (airspeed velocity) | SKIP | Designed for long-running benchmark suites across git history. Overkill for a CLI tool. Separate from pytest -- would need parallel test infrastructure. |
| perftester | SKIP | Lightweight but too simple. No regression detection. No pytest integration. |
| scalene | SKIP | Full profiler (CPU+memory+GPU). Great for investigation but not for CI regression testing. Use ad-hoc, not as a dependency. |

**Integration pattern:**

```python
# tests/benchmarks/test_render_performance.py
import pytest

def test_render_simple_python(benchmark, tmp_path):
    """Benchmark rendering a small Python file."""
    from codepicture.render import render_code_to_image

    code = "def hello():\n    print('world')\n"
    output = tmp_path / "bench.png"

    benchmark(render_code_to_image, code=code, output=output, language="python")

def test_render_large_file(benchmark, tmp_path):
    """Benchmark rendering a large file (100 lines)."""
    from codepicture.render import render_code_to_image

    code = "\n".join(f"line_{i} = {i}" for i in range(100))
    output = tmp_path / "bench.png"

    benchmark(render_code_to_image, code=code, output=output, language="python")
```

**CI integration:**

```yaml
# In GitHub Actions workflow
- name: Run benchmarks
  run: pytest tests/benchmarks/ --benchmark-only --benchmark-json=benchmark.json

- name: Compare with baseline (optional, on PR)
  run: pytest tests/benchmarks/ --benchmark-only --benchmark-compare=0001
```

**pytest configuration:**

```toml
# pyproject.toml addition
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "benchmark: marks benchmark tests",
]
# Exclude benchmarks from normal test runs
addopts = "-v --tb=short --benchmark-disable"
```

This way `pytest` runs all tests WITHOUT benchmarks (fast CI), and `pytest --benchmark-only` runs ONLY benchmarks (performance CI step).

### Rendering Reliability (Timeouts)

| Library | Version | Purpose | Why This One |
|---------|---------|---------|--------------|
| stdlib `signal` | (built-in) | SIGALRM-based render timeouts | Zero dependencies. Python stdlib. Works on macOS and Linux (CI targets). Main thread only -- which is fine for a CLI tool. Simple decorator pattern. |
| stdlib `concurrent.futures` | (built-in) | Thread-based timeout fallback | Cross-platform fallback. `ThreadPoolExecutor` with `future.result(timeout=N)` works on Windows too. Useful if signal approach has issues with Cairo's C code. |

**Why stdlib over third-party timeout libraries:**

| Option | Verdict | Reason |
|--------|---------|--------|
| **signal.SIGALRM** | **USE (primary)** | Zero deps. CLI runs in main thread. Works on macOS/Linux (our CI). Simple and debuggable. |
| **concurrent.futures** | **USE (fallback)** | Stdlib. Cross-platform. Needed if SIGALRM can't interrupt Cairo C code (Cairo holds the GIL during rendering -- signal delivery may be delayed until Cairo returns to Python). |
| timeout-decorator | SKIP | Unmaintained (no releases in 12+ months). Wraps signal.SIGALRM anyway -- we can write 15 lines ourselves. |
| wrapt-timeout-decorator | SKIP | Adds `dill` and `multiprocess` deps for subprocess-based timeouts. Overkill for a CLI tool running in main thread. |
| asyncio.timeout | SKIP | Would require making rendering async. Entire codebase is sync. Not worth the refactor. |

**Critical caveat -- Cairo and SIGALRM:**

Cairo rendering happens in C code. `signal.SIGALRM` is delivered when Python regains control. If Cairo is stuck in a C-level loop (e.g., complex shadow blur), the signal won't fire until Cairo returns. This means:

- **For Pygments lexer hangs** (Python code, regex backtracking): SIGALRM works perfectly.
- **For Cairo rendering hangs** (C code): SIGALRM may be delayed. Use `concurrent.futures.ThreadPoolExecutor` with `future.result(timeout=N)` as the robust approach. The thread won't be killed, but we can raise `TimeoutError` and move on.
- **Nuclear option**: `multiprocessing.Process` with `process.join(timeout=N)` then `process.terminate()`. Kills the entire subprocess including C code. Use only if thread-based timeout is insufficient.

**Recommended implementation (two-tier):**

```python
# codepicture/safety.py
import signal
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from functools import wraps

DEFAULT_RENDER_TIMEOUT = 30  # seconds

def with_timeout(timeout_seconds: int = DEFAULT_RENDER_TIMEOUT):
    """Timeout decorator using ThreadPoolExecutor (works with C extensions)."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=timeout_seconds)
                except TimeoutError:
                    raise RenderTimeoutError(
                        f"Rendering timed out after {timeout_seconds}s. "
                        f"This may indicate a lexer backtracking issue or "
                        f"overly complex rendering operation."
                    )
        return wrapper
    return decorator

class RenderTimeoutError(Exception):
    """Raised when rendering exceeds the allowed time."""
    pass
```

**Why ThreadPoolExecutor over signal.SIGALRM as primary:**

The known hang issue is with MLIR lexer/rendering. Pygments lexing uses regex which IS interruptible by signals, but Cairo shadow blur is C code which is NOT. Using ThreadPoolExecutor as the primary approach covers both cases uniformly, at the cost of not being able to truly kill a stuck thread. For a CLI tool, this is acceptable -- the process exits anyway.

## Complete v1.1 Dev Dependencies Addition

```toml
# pyproject.toml [dependency-groups] update
[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "pytest-cov>=7.0.0",
    "pytest-randomly>=4.0.1",
    "pytest-benchmark>=5.2.3",
    "pixelmatch>=0.3.0",
    "snakeviz>=2.2.2",
]
```

```bash
# Install new dev dependencies
uv add --dev pytest-benchmark pixelmatch snakeviz
```

**No new runtime dependencies.** All timeout/reliability code uses stdlib only.

## What NOT to Add

| Do Not Add | Why Not | What to Use Instead |
|------------|---------|---------------------|
| OpenCV (cv2) | 50MB+ dependency for image comparison. Overkill. Adds native build complexity. | pixelmatch (pure Python, 0.3MB) |
| pytest-image-snapshot | Plugin abstraction over pixelmatch. Hides control over thresholds and diff output. | Direct pixelmatch usage with custom fixture (~20 lines) |
| timeout-decorator | Unmaintained. Just wraps signal.SIGALRM. | stdlib signal + concurrent.futures |
| wrapt-timeout-decorator | Pulls in dill + multiprocess. Designed for complex subprocess scenarios we don't need. | stdlib concurrent.futures |
| hypothesis | Property-based testing is valuable but not the focus of this milestone. Add in a future milestone. | Direct pytest tests for known edge cases |
| memray / scalene | Memory profilers. Useful for investigation but not for CI regression tests. Run ad-hoc. | pytest-benchmark for timing regressions; cProfile for hotspots |
| asv (airspeed velocity) | Separate benchmark infrastructure. Designed for tracking across git history. Overkill. | pytest-benchmark with --benchmark-compare |

## Version Compatibility

| New Package | Min Python | Requires | Notes |
|-------------|------------|----------|-------|
| pytest-benchmark 5.2.3 | 3.9 | pytest>=8.1 | Fixed Python 3.13 counter overflow bug in v5.2.x |
| pixelmatch 0.3.0 | 3.7 | Pillow (already in deps) | Pure Python, no native deps |
| snakeviz 2.2.2 | 3.9 | tornado | Dev-only, browser-based viewer |

All compatible with Python 3.13+ and existing pytest 9.0.2.

## CI Integration Summary

```
Normal CI (every push):
  pytest                          # 260+ tests, benchmarks disabled
  pytest --benchmark-only         # benchmarks only (separate step)

PR CI (compare performance):
  pytest --benchmark-only --benchmark-compare=baseline.json

Visual regression:
  pytest tests/visual/            # compare against snapshots/
  Upload diff images as artifacts on failure
```

## Sources

**Verified via PyPI/official docs (HIGH confidence):**
- [pixelmatch 0.3.0 on PyPI](https://pypi.org/project/pixelmatch/) -- Python port of mapbox/pixelmatch, PIL.Image support
- [pixelmatch-py GitHub](https://github.com/whtsky/pixelmatch-py) -- API docs, threshold/AA options
- [pytest-benchmark 5.2.3 docs](https://pytest-benchmark.readthedocs.io/) -- cProfile integration, compare mode
- [pytest-benchmark PyPI](https://pypi.org/project/pytest-benchmark/) -- v5.2.3, Python 3.9+, pytest 8.1+
- [snakeviz 2.2.2 on PyPI](https://pypi.org/project/snakeviz/) -- Python 3.9+, BSD licensed
- [Python signal module docs](https://docs.python.org/3/library/signal.html) -- SIGALRM limitations with C extensions
- [Pillow ImageChops docs](https://pillow.readthedocs.io/en/stable/reference/ImageChops.html) -- difference() for diff visualization

**Verified via web search (MEDIUM confidence):**
- [pytest-benchmark patterns (Dec 2025)](https://medium.com/@sparknp1/10-pytest-benchmark-patterns-for-honest-performance-claims-6cc674893494) -- Best practices for honest benchmarking
- [Python timeout best practices](https://betterstack.com/community/guides/scaling-python/python-timeouts/) -- ThreadPoolExecutor as robust timeout approach
- [pytest-image-snapshot 0.4.5](https://github.com/bmihelac/pytest-image-snapshot) -- Evaluated, decided against (see rationale above)

---
*Stack research for: codepicture v1.1 reliability milestone*
*Researched: 2026-01-30*
*Overall confidence: HIGH -- All versions verified via PyPI; integration patterns validated against official documentation*
