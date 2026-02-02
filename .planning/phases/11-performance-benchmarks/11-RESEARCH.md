# Phase 11: Performance Benchmarks - Research

**Researched:** 2026-02-02
**Domain:** Python performance benchmarking with pytest-benchmark
**Confidence:** HIGH

## Summary

This phase adds performance benchmarking to the codepicture rendering pipeline using pytest-benchmark. The pipeline has three distinct stages that map directly to benchmark targets: highlight (PygmentsHighlighter.highlight), layout (LayoutEngine.calculate_metrics), and render (Renderer.render). Each stage has clear inputs and outputs, making isolated benchmarking straightforward.

pytest-benchmark 5.2.3 (latest, Nov 2025) integrates as a pytest plugin with a `benchmark` fixture. It provides auto-calibration for rounds/iterations, warmup support, JSON export for CI artifacts, and built-in `--benchmark-skip` / `--benchmark-only` flags that align perfectly with the decision to exclude benchmarks from regular `pytest` runs. The project already uses `pytest >= 9.0.2` which is compatible.

The key architectural insight is that benchmarks should NOT use pytest markers for exclusion. Instead, use pytest-benchmark's built-in `--benchmark-skip` in `addopts` (enabled by default) and `--benchmark-only` when running benchmarks explicitly. This avoids conflating custom markers with the plugin's own infrastructure.

**Primary recommendation:** Add pytest-benchmark to dev dependencies, use `--benchmark-skip` in default addopts, organize benchmarks in `tests/benchmarks/` directory, and use `--benchmark-json` for CI artifact export.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest-benchmark | 5.2.3 | Benchmark fixture, auto-calibration, stats, JSON export | The standard Python benchmarking plugin for pytest; 5.2.3 confirmed compatible with pytest 9.0 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=9.0.2 | Test runner (already installed) | Already in dev dependencies |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest-benchmark | manual time.perf_counter | Loses auto-calibration, warmup, statistical rigor, JSON export |
| pytest-benchmark | asv (airspeed velocity) | Heavier, separate runner, overkill for informational benchmarks |

**Installation:**
```bash
uv add --dev pytest-benchmark
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
  benchmarks/
    __init__.py
    conftest.py            # Shared fixtures: code strings, pre-tokenized lines, pre-computed metrics
    test_bench_highlight.py  # Per-language highlight benchmarks
    test_bench_layout.py     # Per-language layout benchmarks
    test_bench_render.py     # Per-language render benchmarks
    test_bench_pipeline.py   # End-to-end pipeline benchmarks (small/medium/large)
```

### Pattern 1: Isolated Stage Benchmarking
**What:** Benchmark each pipeline stage in isolation, feeding it pre-computed inputs from the previous stage.
**When to use:** Always for per-stage benchmarks -- prevents measuring upstream stages.
**Example:**
```python
# Source: pytest-benchmark docs + project API
import pytest
from codepicture import PygmentsHighlighter

PYTHON_CODE = '''def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"
'''

@pytest.mark.benchmark(group="highlight")
def test_highlight_python(benchmark):
    highlighter = PygmentsHighlighter()
    result = benchmark(highlighter.highlight, PYTHON_CODE, "python")
    assert len(result) > 0
```

### Pattern 2: Pre-computed Inputs via Conftest Fixtures
**What:** conftest.py provides pre-tokenized lines and pre-computed metrics so downstream stages do not re-measure upstream work.
**When to use:** Layout benchmarks need pre-tokenized input; render benchmarks need both tokens and metrics.
**Example:**
```python
# tests/benchmarks/conftest.py
import pytest
from codepicture import PygmentsHighlighter, PangoTextMeasurer, LayoutEngine, RenderConfig
from codepicture.fonts import register_bundled_fonts

register_bundled_fonts()

FIXTURE_CODES = {
    "python": ("python", open("tests/fixtures/sample_python.py").read()),
    "rust": ("rust", open("tests/fixtures/sample_rust.rs").read()),
    # ... etc
}

@pytest.fixture(params=FIXTURE_CODES.keys())
def language_tokens(request):
    """Pre-tokenized lines for each language."""
    lang, code = FIXTURE_CODES[request.param]
    highlighter = PygmentsHighlighter()
    return request.param, highlighter.highlight(code, lang)

@pytest.fixture
def default_config():
    return RenderConfig()

@pytest.fixture
def measurer():
    return PangoTextMeasurer()
```

### Pattern 3: End-to-End Pipeline Benchmarks
**What:** Benchmark the full generate_image pipeline (without file I/O) for different input sizes.
**When to use:** For the end-to-end benchmarks with small/medium/large inputs.
**Example:**
```python
import io
import pytest
from codepicture import (
    PygmentsHighlighter, LayoutEngine, PangoTextMeasurer,
    Renderer, RenderConfig, get_theme
)
from codepicture.fonts import register_bundled_fonts

register_bundled_fonts()

def run_pipeline(code: str, language: str, config: RenderConfig):
    highlighter = PygmentsHighlighter()
    tokens = highlighter.highlight(code, language)
    measurer = PangoTextMeasurer()
    engine = LayoutEngine(measurer, config)
    metrics = engine.calculate_metrics(tokens)
    theme = get_theme(config.theme)
    renderer = Renderer(config)
    return renderer.render(tokens, metrics, theme)

@pytest.mark.benchmark(group="pipeline")
def test_pipeline_small(benchmark):
    code = SMALL_PYTHON  # ~10 lines
    config = RenderConfig()
    result = benchmark(run_pipeline, code, "python", config)
    assert result.data
```

### Pattern 4: Feature Toggle Combinations
**What:** Benchmark render stage with different feature combinations to measure impact.
**When to use:** For shadow, chrome, line_numbers toggle impact measurement.
**Example:**
```python
TOGGLE_CONFIGS = {
    "minimal": RenderConfig(window_controls=False, shadow=False, show_line_numbers=False),
    "with_line_numbers": RenderConfig(window_controls=False, shadow=False, show_line_numbers=True),
    "with_chrome": RenderConfig(window_controls=True, shadow=False, show_line_numbers=False),
    "full": RenderConfig(window_controls=True, shadow=True, show_line_numbers=True),
}

@pytest.fixture(params=TOGGLE_CONFIGS.keys())
def toggle_config(request):
    return request.param, TOGGLE_CONFIGS[request.param]
```

### Anti-Patterns to Avoid
- **Benchmarking file I/O alongside rendering:** Isolate the pipeline from filesystem operations. Benchmark `Renderer.render()` return value, not writing to disk.
- **Creating new PangoTextMeasurer per benchmark iteration:** Font registration and measurer setup should happen once in fixture setup, not inside the benchmarked function (unless you specifically want to measure setup cost).
- **Using pedantic mode without good reason:** Auto-calibration is correct for this use case. Pedantic mode requires manual tuning of iterations and rounds.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Statistical rigor (min/max/mean/stddev/rounds) | Custom timing + statistics | pytest-benchmark auto-calibration | Handles timer resolution, warmup, outlier detection |
| JSON export for CI | Custom JSON serialization | `--benchmark-json output.json` | Standardized format, includes machine info, git commit hash |
| Benchmark exclusion from regular tests | Custom pytest markers + conftest logic | `--benchmark-skip` in addopts | Built-in to plugin, no marker maintenance needed |
| Warmup runs | Manual loop before timing | `--benchmark-warmup=on` | Properly excluded from stats |
| Comparing results across runs | Manual diff scripts | `--benchmark-compare` and `pytest-benchmark compare` CLI | Built-in comparison with threshold support |

**Key insight:** pytest-benchmark handles all the statistical and infrastructure complexity. The only custom code needed is the benchmark test functions themselves and their fixtures.

## Common Pitfalls

### Pitfall 1: Not Excluding Benchmarks from Default Test Runs
**What goes wrong:** Running `pytest` includes benchmark tests, slowing down the test suite significantly.
**Why it happens:** pytest-benchmark runs benchmarks by default unless told otherwise.
**How to avoid:** Add `--benchmark-skip` to `addopts` in `pyproject.toml`. Run benchmarks explicitly with `pytest --benchmark-only tests/benchmarks/`.
**Warning signs:** Regular test runs taking much longer than expected.

### Pitfall 2: Measuring Setup Inside Benchmark Loop
**What goes wrong:** Font registration, highlighter creation, or measurer instantiation measured as part of the benchmark.
**Why it happens:** Setup code placed inside the function passed to `benchmark()`.
**How to avoid:** Create objects in fixtures or outside the benchmarked callable. Only the target operation should be inside `benchmark()`.
**Warning signs:** Benchmark times much higher than expected, high variance from GC during object creation.

### Pitfall 3: CI Variance Causing False Alarm
**What goes wrong:** GitHub Actions runners have variable performance, leading to inconsistent benchmark results.
**Why it happens:** Shared infrastructure, noisy neighbors, CPU throttling.
**How to avoid:** Decision already made: informational only, no regression gating. Use `--benchmark-min-rounds=5` (default) and accept variance. Do NOT set `--benchmark-compare-fail` thresholds in CI.
**Warning signs:** Benchmark results varying by 50%+ between runs on same code.

### Pitfall 4: Forgetting to Register Fonts Before Layout/Render Benchmarks
**What goes wrong:** Font resolution fails or uses fallback font, producing incorrect benchmark results.
**Why it happens:** `register_bundled_fonts()` not called before benchmarks that use PangoTextMeasurer or CairoCanvas.
**How to avoid:** Call `register_bundled_fonts()` at module level in `tests/benchmarks/conftest.py`.
**Warning signs:** LayoutError or different metrics than expected.

### Pitfall 5: Benchmark Timeout Conflicts
**What goes wrong:** The project sets `timeout = 5` in pytest config. Benchmark auto-calibration may need more time per test.
**Why it happens:** pytest-benchmark runs the function many times; with 5s timeout, complex benchmarks may be killed.
**How to avoid:** Set `timeout = 0` (disabled) for benchmark tests, either via marker `@pytest.mark.timeout(0)` or by configuring a separate timeout in the benchmark workflow.
**Warning signs:** Tests failing with timeout errors during benchmark calibration.

## Code Examples

### pytest configuration for benchmark exclusion
```toml
# pyproject.toml additions
[tool.pytest.ini_options]
addopts = "-v --tb=short --benchmark-skip"
markers = [
    "slow: marks tests as slow",
    "benchmark: marks tests as benchmarks",
]
```

### Running benchmarks explicitly
```bash
# Run only benchmarks
uv run pytest tests/benchmarks/ --benchmark-only --benchmark-warmup=on -v

# Run benchmarks and export JSON
uv run pytest tests/benchmarks/ --benchmark-only --benchmark-warmup=on --benchmark-json=benchmark-results.json

# Group output by benchmark group
uv run pytest tests/benchmarks/ --benchmark-only --benchmark-group-by=group
```

### Highlight stage benchmark
```python
# tests/benchmarks/test_bench_highlight.py
import pytest
from codepicture import PygmentsHighlighter

HIGHLIGHTER = PygmentsHighlighter()

@pytest.mark.benchmark(group="highlight")
@pytest.mark.timeout(0)
def test_highlight_python(benchmark, python_code):
    benchmark(HIGHLIGHTER.highlight, python_code, "python")

@pytest.mark.benchmark(group="highlight")
@pytest.mark.timeout(0)
def test_highlight_rust(benchmark, rust_code):
    benchmark(HIGHLIGHTER.highlight, rust_code, "rust")
```

### Layout stage benchmark
```python
# tests/benchmarks/test_bench_layout.py
import pytest
from codepicture import LayoutEngine, PangoTextMeasurer, RenderConfig
from codepicture.fonts import register_bundled_fonts

register_bundled_fonts()
MEASURER = PangoTextMeasurer()

@pytest.mark.benchmark(group="layout")
@pytest.mark.timeout(0)
def test_layout_python(benchmark, python_tokens):
    config = RenderConfig()
    engine = LayoutEngine(MEASURER, config)
    benchmark(engine.calculate_metrics, python_tokens)
```

### Render stage benchmark
```python
# tests/benchmarks/test_bench_render.py
import pytest
from codepicture import Renderer, RenderConfig, get_theme
from codepicture.fonts import register_bundled_fonts

register_bundled_fonts()

@pytest.mark.benchmark(group="render")
@pytest.mark.timeout(0)
def test_render_python(benchmark, python_tokens, python_metrics):
    config = RenderConfig()
    theme = get_theme(config.theme)
    renderer = Renderer(config)
    result = benchmark(renderer.render, python_tokens, python_metrics, theme)
    assert result.data
```

### CI workflow (benchmark.yml)
```yaml
name: Benchmarks

on:
  workflow_dispatch:
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6am UTC

jobs:
  benchmark:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.13

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y libcairo2-dev libpango1.0-dev fonts-jetbrains-mono

      - name: Install dependencies
        run: uv sync --locked --dev

      - name: Run benchmarks
        run: |
          uv run pytest tests/benchmarks/ \
            --benchmark-only \
            --benchmark-warmup=on \
            --benchmark-json=benchmark-results.json \
            --benchmark-group-by=group \
            -v 2>&1 | tee benchmark-output.txt
        env:
          PANGOCAIRO_BACKEND: fontconfig

      - name: Upload benchmark results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: |
            benchmark-results.json
            benchmark-output.txt
          retention-days: 30
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pytest-benchmark 4.x | pytest-benchmark 5.2.3 | 2025 | Added pytest 9.0 compat, per-round teardown in pedantic mode |
| `--benchmark-disable` for skipping | `--benchmark-skip` for skipping | Stable in 4.x+ | `--benchmark-skip` skips entirely; `--benchmark-disable` still runs function once |

**Deprecated/outdated:**
- None relevant. pytest-benchmark API has been stable across 4.x and 5.x.

## Open Questions

1. **C++ fixture does not exist yet**
   - What we know: Existing fixtures are Python, Rust, JavaScript, MLIR. No C++ file in `tests/fixtures/`.
   - What's unclear: Whether to add one or use an existing language.
   - Recommendation: Create `tests/fixtures/sample_cpp.cpp` as part of this phase. Small file, ~8 lines like other fixtures.

2. **Exact fixture content for small/medium/large inputs**
   - What we know: Existing fixtures are ~7-8 lines (small). Need medium (~50 lines) and large (~200 lines).
   - What's unclear: Whether to generate them or write them manually.
   - Recommendation: Write them manually for Python (the baseline language). Use realistic code patterns, not synthetic repetition. Store in `tests/benchmarks/fixtures/` to keep them separate from unit test fixtures.

3. **Which feature toggle combinations to benchmark**
   - What we know: User left this to Claude's discretion. Available toggles: shadow, window_controls, show_line_numbers.
   - Recommendation: Benchmark 3 configurations: minimal (all off), with_line_numbers (only line numbers on), and full (all on). This captures the two most impactful toggles (line numbers affect layout measurement, shadow affects post-processing) without combinatorial explosion.

## Sources

### Primary (HIGH confidence)
- pytest-benchmark official docs (readthedocs.io) - usage, calibration, pedantic mode, comparing
- PyPI pytest-benchmark page - version 5.2.3, Python compatibility
- Project source code - pipeline stages, orchestrator, existing test structure, pyproject.toml

### Secondary (MEDIUM confidence)
- pytest-benchmark GitHub releases - version history and changelog

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pytest-benchmark is the established tool, version verified on PyPI
- Architecture: HIGH - based on direct reading of project source code and pytest-benchmark docs
- Pitfalls: HIGH - derived from known pytest-benchmark behavior and project configuration (timeout=5)

**Research date:** 2026-02-02
**Valid until:** 2026-03-04 (stable library, low churn)
