# Architecture Patterns: Hardening Milestone

**Domain:** Visual regression testing, rendering reliability, and performance profiling for an existing Python rendering pipeline
**Researched:** 2026-01-30
**Confidence:** HIGH (architecture patterns well-understood from codebase analysis + ecosystem research)

## Existing Architecture Overview

The codepicture pipeline is a linear, protocol-based rendering chain:

```
Input (code string)
  |
  v
PygmentsHighlighter.highlight()     --> list[list[TokenInfo]]
  |
  v
LayoutEngine.calculate_metrics()    --> LayoutMetrics
  |
  v
Renderer.render()                   --> RenderResult (bytes)
  |    uses: CairoCanvas, chrome, shadow
  v
Output (write bytes to file)
```

Orchestrated by `generate_image()` in `cli/orchestrator.py`, which calls each step sequentially. No timeouts, no performance instrumentation, no visual validation exist today.

### Current Component Map

| Component | File | Protocol | Hang Risk |
|-----------|------|----------|-----------|
| PygmentsHighlighter | `highlight/pygments_highlighter.py` | Highlighter | HIGH -- Pygments lexer `get_tokens()` iterates the entire input; pathological regexes in lexers (e.g., MLIR) can hang |
| PangoTextMeasurer | `layout/measurer.py` | TextMeasurer | LOW -- single-char measurement, Cairo-backed |
| LayoutEngine | `layout/engine.py` | N/A (concrete) | MEDIUM -- iterates all lines to find `max_chars`; O(lines x tokens) |
| Renderer | `render/renderer.py` | N/A (concrete) | MEDIUM -- iterates all tokens for drawing; O(lines x tokens) |
| CairoCanvas | `render/canvas.py` | Canvas | LOW -- Cairo ops are native C, fast per call |
| apply_shadow | `render/shadow.py` | N/A (function) | MEDIUM -- Pillow GaussianBlur on large images is CPU-intensive |

### Error Hierarchy (existing)

```
CodepictureError
  +-- ConfigError
  +-- ThemeError
  +-- HighlightError
  +-- LayoutError
  +-- RenderError
```

Currently no timeout-related errors exist. A `RenderTimeoutError` is needed.

---

## Recommended Architecture: Three New Subsystems

### Subsystem 1: Rendering Timeouts and Safety

**Problem:** The `test.mlir` file causes a hang -- likely in `PygmentsHighlighter.highlight()` where Pygments' lexer regex engine enters pathological backtracking. The pipeline has no timeout protection at any layer.

**Design: Timeout wrapper at the orchestrator level, with per-stage granularity.**

#### Where to Add Timeouts

Timeouts should wrap the orchestrator pipeline, not individual protocol implementations. This avoids polluting the clean protocol interfaces and keeps timeout policy centralized.

```
generate_image()
  |
  +-- with_timeout(highlight, timeout=HIGHLIGHT_TIMEOUT)
  |     PygmentsHighlighter.highlight(code, language)
  |
  +-- with_timeout(layout, timeout=LAYOUT_TIMEOUT)
  |     LayoutEngine.calculate_metrics(tokens)
  |
  +-- with_timeout(render, timeout=RENDER_TIMEOUT)
  |     Renderer.render(tokens, metrics, theme)
  |
  +-- output write (no timeout needed -- filesystem I/O)
```

#### Timeout Implementation: `signal.alarm()` (recommended)

Use `signal.SIGALRM` for timeout enforcement because:

1. **codepicture is a CLI tool** -- always runs in the main thread
2. **No pickling needed** -- unlike multiprocessing approaches, signal-based timeouts do not require serializing Cairo surfaces, Pygments tokens, or Pillow images (none of which are picklable)
3. **Zero overhead** -- no process spawning, no IPC
4. **Sub-second not needed** -- integer-second timeouts are fine for "is this hanging?" detection

**Limitation:** Unix-only (`signal.alarm` not available on Windows). This is acceptable because the existing CI runs on `ubuntu-latest` and the tool uses Cairo/Pango which are Linux/macOS native.

**Fallback for cross-platform (if ever needed):** `threading.Timer` + `ctypes.pythonapi.PyThreadState_SetAsyncExc` to raise an exception in the target thread -- but this is fragile with C extensions like Cairo. Not recommended unless Windows support becomes a requirement.

#### New Components

| Component | Location | Type | Purpose |
|-----------|----------|------|---------|
| `RenderTimeoutError` | `errors.py` | Exception class | New error in existing hierarchy |
| `TimeoutContext` | `safety.py` (new) | Context manager | `signal.alarm`-based timeout with configurable duration |
| Orchestrator changes | `cli/orchestrator.py` | Modified | Wrap each pipeline stage with `TimeoutContext` |

#### Suggested `safety.py` Structure

```python
# src/codepicture/safety.py
"""Rendering safety: timeouts and resource limits."""

import signal
from contextlib import contextmanager
from codepicture.errors import RenderTimeoutError

# Default timeouts in seconds
HIGHLIGHT_TIMEOUT = 10   # Lexing/tokenization
LAYOUT_TIMEOUT = 5       # Layout calculation
RENDER_TIMEOUT = 30      # Canvas drawing + shadow

@contextmanager
def timeout(seconds: int, stage: str):
    """Raise RenderTimeoutError if stage exceeds time limit.

    Uses signal.SIGALRM (Unix-only, main thread only).
    """
    def handler(signum, frame):
        raise RenderTimeoutError(
            f"{stage} timed out after {seconds}s"
        )

    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)  # Cancel alarm
        signal.signal(signal.SIGALRM, old_handler)
```

#### Modified Orchestrator (sketch)

```python
from codepicture.safety import timeout, HIGHLIGHT_TIMEOUT, LAYOUT_TIMEOUT, RENDER_TIMEOUT

def generate_image(code, output_path, config, language=None, filename=None):
    register_bundled_fonts()
    highlighter = PygmentsHighlighter()
    # ... language detection (fast, no timeout needed) ...

    with timeout(HIGHLIGHT_TIMEOUT, "Syntax highlighting"):
        tokens = highlighter.highlight(code, language)

    theme = get_theme(config.theme)
    measurer = PangoTextMeasurer()
    engine = LayoutEngine(measurer, config)

    with timeout(LAYOUT_TIMEOUT, "Layout calculation"):
        metrics = engine.calculate_metrics(tokens)

    renderer = Renderer(config)
    with timeout(RENDER_TIMEOUT, "Rendering"):
        result = renderer.render(tokens, metrics, theme)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result.data)
```

---

### Subsystem 2: Visual Regression Testing

**Problem:** No automated verification that rendered images look correct. Refactoring could silently break output.

**Design: pytest-based snapshot testing with reference images committed to the repo.**

#### Recommended Library: `pytest-image-snapshot`

**Why this over alternatives:**

| Library | Verdict | Reason |
|---------|---------|--------|
| `pytest-image-snapshot` | **RECOMMENDED** | PIL-native, pixelmatch integration, threshold control, auto-create snapshots, clean pytest fixture API |
| `pytest-image-diff` | Alternative | Similar capability but less actively maintained; splinter integration irrelevant |
| `pytest-vtestify` | Not recommended | SSIM-based comparison is less intuitive for pixel-exact rendering |
| pixelmatch-py (raw) | Viable fallback | No pytest integration, would need custom fixture (~30 lines) |
| pytest-regtest | Not applicable | Text/data snapshots only, not images |

**Confidence: MEDIUM** -- `pytest-image-snapshot` is a relatively small project. If it proves problematic, falling back to raw pixelmatch-py with a custom fixture (approximately 30 lines of code) is straightforward.

#### Reference Image Storage Strategy

**Recommendation: Commit reference images to the repository in `tests/snapshots/`.**

Rationale:
- The project is small (few snapshot configurations)
- Reference images are PNGs of code snippets -- typically 10-50KB each
- Git LFS is unnecessary at this scale
- Keeping images in-repo ensures they version alongside code changes
- CI consistency: run on `ubuntu-latest` which matches CI environment

**Critical: Platform consistency.** Cairo rendering is deterministic on the same platform but produces pixel-level differences across macOS vs Linux due to font rendering differences. Two options:

1. **CI as source of truth (recommended):** Generate and update reference images on CI only. Developers can run visual tests locally but mismatches on macOS are expected and non-blocking.
2. **Platform-specific snapshots:** Maintain separate `snapshots/linux/` and `snapshots/darwin/` directories. Adds maintenance burden, not recommended.

#### Test Structure

```
tests/
  snapshots/                          # NEW: reference images (committed)
    test_visual/
      python_hello_world.png
      python_with_line_numbers.png
      python_with_shadow.png
      svg_output.png
      ...
  visual/                             # NEW: visual regression test module
    __init__.py
    conftest.py                       # Visual test fixtures
    test_visual_regression.py         # Snapshot comparison tests
    test_visual_themes.py             # Theme rendering tests
```

#### Visual Test Fixtures

```python
# tests/visual/conftest.py
import pytest
from pathlib import Path
from codepicture import (
    PygmentsHighlighter, LayoutEngine, PangoTextMeasurer,
    Renderer, RenderConfig, register_bundled_fonts, get_theme,
)

SNAPSHOTS_DIR = Path(__file__).parent.parent / "snapshots"

@pytest.fixture(scope="session", autouse=True)
def register_fonts():
    register_bundled_fonts()

@pytest.fixture
def render_to_bytes():
    """Factory fixture: render code to PNG bytes."""
    def _render(code: str, language: str = "python", **config_overrides) -> bytes:
        config = RenderConfig(**config_overrides)
        highlighter = PygmentsHighlighter()
        tokens = highlighter.highlight(code, language)
        theme = get_theme(config.theme)
        measurer = PangoTextMeasurer()
        engine = LayoutEngine(measurer, config)
        metrics = engine.calculate_metrics(tokens)
        renderer = Renderer(config)
        result = renderer.render(tokens, metrics, theme)
        return result.data
    return _render
```

#### Integration with Existing pytest Suite

- Visual tests go in `tests/visual/` -- a separate directory so they can be run independently
- Add pytest marker: `@pytest.mark.visual` for selective execution
- CI workflow step: run visual tests as a separate job or step (they need Cairo/fonts)
- Update `pyproject.toml` markers:
  ```
  "visual: marks visual regression tests (may require reference image updates)",
  ```

#### CI Integration

```yaml
# Addition to .github/workflows/test.yml
- name: Run visual regression tests
  run: uv run pytest tests/visual/ -m visual

- name: Upload visual diff artifacts
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: visual-diffs
    path: tests/snapshots/**/diff_*.png
    retention-days: 7
```

On failure, diff images are uploaded as artifacts for manual review. This is the standard pattern for visual regression in CI.

#### Updating Reference Images

When an intentional visual change is made:
1. Run `pytest tests/visual/ --snapshot-update` locally (or in CI)
2. Review the updated images
3. Commit the new reference images with the code change

---

### Subsystem 3: Performance Profiling

**Problem:** No way to detect performance regressions or identify which pipeline stage is the bottleneck for large inputs.

**Design: pytest-benchmark for regression detection + cProfile integration for bottleneck analysis.**

#### Recommended Tools

| Tool | Purpose | When Used |
|------|---------|-----------|
| `pytest-benchmark` | Track render times across commits, detect regressions | CI (every run) |
| `cProfile` (stdlib) | Identify which functions consume time | Manual profiling / debugging |
| `--benchmark-cprofile` | Combined: benchmark + profile in one run | On-demand deep analysis |

**Why not py-spy or Pyinstrument?** They are better for production profiling but add unnecessary complexity for a CLI tool. `cProfile` + `pytest-benchmark` covers the use case fully: detect regressions in CI, drill into bottlenecks when needed.

#### Benchmark Test Structure

```
tests/
  benchmarks/                         # NEW: performance benchmark module
    __init__.py
    conftest.py                       # Benchmark fixtures (sample files of varying size)
    test_bench_highlight.py           # Highlight stage benchmarks
    test_bench_layout.py              # Layout stage benchmarks
    test_bench_render.py              # Full render benchmarks
    test_bench_pipeline.py            # End-to-end pipeline benchmarks
    fixtures/                         # Sample code files for benchmarking
      small.py                        # ~10 lines
      medium.py                       # ~100 lines
      large.py                        # ~1000 lines
```

#### Benchmark Fixture Design

```python
# tests/benchmarks/conftest.py
import pytest
from pathlib import Path

BENCH_FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture(params=["small.py", "medium.py", "large.py"])
def sample_code(request):
    """Parametrized fixture providing code samples of varying size."""
    path = BENCH_FIXTURES / request.param
    return path.read_text(), request.param
```

#### Per-Stage Benchmarks

```python
# tests/benchmarks/test_bench_highlight.py
def test_highlight_performance(benchmark, sample_code):
    code, name = sample_code
    highlighter = PygmentsHighlighter()
    benchmark(highlighter.highlight, code, "python")

# tests/benchmarks/test_bench_pipeline.py
def test_end_to_end(benchmark, sample_code, tmp_path):
    code, name = sample_code
    output = tmp_path / "out.png"
    config = RenderConfig(shadow=False, window_controls=False)
    benchmark(generate_image, code, output, config, language="python")
```

#### CI Integration

```yaml
# Benchmarks run but don't fail CI (informational)
- name: Run performance benchmarks
  run: uv run pytest tests/benchmarks/ --benchmark-only --benchmark-json=benchmark.json
  continue-on-error: true

- name: Store benchmark results
  uses: actions/upload-artifact@v4
  with:
    name: benchmarks
    path: benchmark.json
```

For regression detection, `pytest-benchmark` can compare against saved baselines:
```bash
# Compare against saved baseline
pytest tests/benchmarks/ --benchmark-compare=0001_baseline
```

---

## Component Boundaries: New vs Modified

### New Files

| File | Purpose | Dependencies |
|------|---------|-------------|
| `src/codepicture/safety.py` | Timeout context manager + constants | `signal`, `errors.py` |
| `tests/visual/__init__.py` | Visual test package | -- |
| `tests/visual/conftest.py` | Visual test fixtures | codepicture, pytest-image-snapshot |
| `tests/visual/test_visual_regression.py` | Snapshot comparison tests | visual fixtures |
| `tests/snapshots/` | Reference images directory | -- |
| `tests/benchmarks/__init__.py` | Benchmark test package | -- |
| `tests/benchmarks/conftest.py` | Benchmark fixtures | codepicture |
| `tests/benchmarks/test_bench_*.py` | Per-stage benchmarks | pytest-benchmark |
| `tests/benchmarks/fixtures/` | Sample code files of varying size | -- |

### Modified Files

| File | Change | Reason |
|------|--------|--------|
| `src/codepicture/errors.py` | Add `RenderTimeoutError` | New error type for timeout handling |
| `src/codepicture/__init__.py` | Export `RenderTimeoutError` | Public API |
| `src/codepicture/cli/orchestrator.py` | Wrap pipeline stages with `timeout()` | Timeout enforcement |
| `pyproject.toml` | Add dev deps, pytest markers | `pytest-image-snapshot`, `pytest-benchmark`, markers |
| `.github/workflows/test.yml` | Add visual + benchmark steps | CI integration |

### NOT Modified (protocol integrity preserved)

These files remain unchanged -- timeouts and profiling are orthogonal concerns that wrap the pipeline externally:

- `core/protocols.py` -- No timeout concepts in protocols
- `render/renderer.py` -- No changes to rendering logic
- `render/canvas.py` -- No changes to canvas implementation
- `layout/engine.py` -- No changes to layout logic
- `highlight/pygments_highlighter.py` -- No changes to highlighting

This is critical: the protocol-based architecture stays clean. Safety and observability are orchestration concerns, not component concerns.

---

## Data Flow: With New Subsystems

```
generate_image()  [MODIFIED: adds timeout wrappers]
  |
  +-- register_bundled_fonts()
  |
  +-- [timeout: HIGHLIGHT_TIMEOUT]
  |     PygmentsHighlighter.highlight()
  |     |-- On timeout --> RenderTimeoutError("Syntax highlighting timed out")
  |
  +-- get_theme()
  |
  +-- [timeout: LAYOUT_TIMEOUT]
  |     LayoutEngine.calculate_metrics()
  |     |-- On timeout --> RenderTimeoutError("Layout calculation timed out")
  |
  +-- [timeout: RENDER_TIMEOUT]
  |     Renderer.render()
  |     |-- On timeout --> RenderTimeoutError("Rendering timed out")
  |
  +-- write output

Visual tests:                          Benchmarks:
  render_to_bytes() fixture              benchmark() fixture wraps
    --> PIL.Image                           each pipeline stage
    --> compare to snapshot                --> timing data
    --> pass/fail + diff image             --> JSON report
```

---

## Suggested Build Order

The three subsystems are independent and could be built in parallel, but this ordering minimizes risk:

### Phase 1: Rendering Timeouts (build first)

**Rationale:** Fixes the immediate `test.mlir` hang problem. Small surface area (one new file + two modified files). Unblocks safe testing of large/pathological inputs.

**Components:**
1. `RenderTimeoutError` in `errors.py`
2. `safety.py` with `timeout()` context manager
3. Modified `orchestrator.py` with timeout wrappers
4. Tests for timeout behavior (mock `signal.alarm`)

**Risk:** LOW -- `signal.alarm` is well-understood stdlib functionality.

### Phase 2: Visual Regression Tests (build second)

**Rationale:** Requires a working, non-hanging pipeline (Phase 1). Reference images must be generated from a stable build. Most value for catching regressions during future refactoring.

**Components:**
1. Install `pytest-image-snapshot` (or `pixelmatch-py` if custom fixture preferred)
2. Visual test fixtures (`render_to_bytes`)
3. Initial visual regression tests (5-10 configurations covering key features)
4. Generate and commit reference images
5. CI workflow additions

**Risk:** MEDIUM -- Cross-platform rendering differences may cause CI-only test setup. Font availability on CI (`ubuntu-latest`) needs verification.

### Phase 3: Performance Profiling (build third)

**Rationale:** Lowest urgency -- no correctness impact. Benefits from timeouts (Phase 1) preventing benchmark hangs. Benefits from visual tests (Phase 2) ensuring optimizations don't break output.

**Components:**
1. Install `pytest-benchmark`
2. Create sample code fixtures (small/medium/large)
3. Per-stage benchmark tests
4. End-to-end pipeline benchmark
5. CI workflow additions (artifact upload)

**Risk:** LOW -- pytest-benchmark is mature and well-integrated with pytest.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Timeouts Inside Protocol Implementations
**What:** Adding timeout logic into `PygmentsHighlighter.highlight()` or `Renderer.render()`.
**Why bad:** Violates protocol purity. Makes components harder to test. Mixes safety policy with business logic.
**Instead:** Wrap at the orchestration layer (`generate_image()`).

### Anti-Pattern 2: Reference Images Generated on Developer Machines
**What:** Generating visual regression baselines on macOS then running tests on Linux CI.
**Why bad:** Font rendering differences between platforms cause false failures. Cairo text rendering is not pixel-identical across platforms.
**Instead:** Generate reference images on CI (or in a Docker container matching CI).

### Anti-Pattern 3: Benchmarks That Block CI
**What:** Making benchmark regressions fail the CI build.
**Why bad:** Benchmark variance on shared CI runners (GitHub Actions) is high -- 10-20% variance is normal. This causes flaky failures.
**Instead:** Run benchmarks as informational, upload JSON artifacts, compare manually or with explicit thresholds.

### Anti-Pattern 4: Testing the Entire Pipeline as One Unit Only
**What:** Only having end-to-end visual tests with no per-stage benchmarks.
**Why bad:** When a test fails or performance regresses, you cannot tell which stage is responsible.
**Instead:** Have both per-stage benchmarks and end-to-end visual tests. The per-stage tests pinpoint where issues occur.

### Anti-Pattern 5: Pixel-Perfect Comparison With Zero Threshold
**What:** Using threshold=0 for visual comparison.
**Why bad:** Anti-aliasing, subpixel rendering, and minor font hinting differences cause false failures even on the same platform across library updates.
**Instead:** Use a small but nonzero threshold (e.g., 0.1 for pixelmatch, which is its default).

---

## Scalability Considerations

| Concern | Current (test.mlir) | At 50 visual tests | At 200 benchmarks |
|---------|---------------------|---------------------|---------------------|
| CI time | Hangs indefinitely | ~2-3 min (with timeouts) | ~5 min (benchmarks are fast per iteration) |
| Repo size | N/A | +5-25MB for snapshots | Negligible (JSON) |
| Maintenance | N/A | Update snapshots on visual changes | Update baselines quarterly |

---

## Sources

**HIGH confidence (official documentation, codebase analysis):**
- Codebase analysis of all source files under `src/codepicture/`
- [Python signal module documentation](https://docs.python.org/3/library/signal.html) -- `signal.alarm` behavior
- [Python cProfile documentation](https://docs.python.org/3/library/profile.html) -- Built-in profiler
- [pytest-benchmark on PyPI](https://pypi.org/project/pytest-benchmark/) -- Performance benchmarking with `--benchmark-cprofile` integration

**MEDIUM confidence (verified with multiple sources):**
- [pytest-image-snapshot](https://github.com/bmihelac/pytest-image-snapshot) -- Visual regression library with pixelmatch
- [pixelmatch-py](https://github.com/whtsky/pixelmatch-py) -- Underlying comparison engine
- [timeout-decorator](https://pypi.org/project/timeout-decorator/) -- Reference for signal vs multiprocessing timeout tradeoffs
- [Visual Regression Testing with GitHub Actions](https://www.duncanmackenzie.net/blog/visual-regression-testing/) -- CI integration patterns

**LOW confidence (single-source, inform but verify):**
- [pytest-image-diff](https://github.com/Apkawa/pytest-image-diff) -- Alternative visual regression library
- [reg-viz/reg-actions](https://github.com/reg-viz/reg-actions) -- CI visual regression pattern reference

---
*Architecture research for: Hardening milestone -- visual regression, timeouts, profiling*
*Researched: 2026-01-30*
