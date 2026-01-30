# Phase 10: Visual Regression & Reliability - Research

**Researched:** 2026-01-30
**Domain:** Visual regression testing, image comparison, parametrized rendering validation
**Confidence:** HIGH

## Summary

This phase adds two capabilities: (1) pixelmatch-based visual regression testing that compares rendered output against reference images, and (2) parametrized reliability testing across all language/format/config combinations. The project already renders PNG, SVG, and PDF via pycairo + Pillow, so the infrastructure exists to generate images programmatically. What's new is the comparison framework, reference image management, and systematic matrix testing.

The standard approach uses the `pixelmatch` Python library (v0.3.0) with its PIL contrib module for pixel-level comparison, combined with Pillow for diff composite generation and CairoSVG/PyMuPDF for converting SVG/PDF to PNG before comparison. Reference images are stored in Git LFS, tracked via `.gitattributes`, with a pytest `--snapshot-update` flag for regeneration.

**Primary recommendation:** Use `pixelmatch` (PIL contrib) for comparison, build a thin custom `compare_images()` helper rather than adopting `pytest-image-snapshot` (which adds unnecessary abstraction over what's essentially 20 lines of comparison code), and use `pytest.mark.parametrize` for the full test matrix.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pixelmatch` | 0.3.0 | Pixel-level image comparison with anti-aliasing detection | Python port of mapbox/pixelmatch, the standard for VRT. Handles AA detection, perceptual color diff. Used by Playwright, jest-image-snapshot |
| `Pillow` | >=10.0 (already dep) | Diff composite generation, image I/O | Already in project. `ImageChops.difference()` for raw diffs, `Image.new()`/`paste()` for composite assembly |
| `cairosvg` | >=2.7 | SVG-to-PNG rasterization for comparison | Cairo-based (matches project), converts SVG bytes to PNG bytes. Needed because SVG text comparison is unreliable |
| `pymupdf` | >=1.24 | PDF-to-PNG rasterization for comparison | Fast, no external deps. `page.get_pixmap()` renders PDF pages to PNG. Needed for PDF visual comparison |
| Git LFS | (system) | Reference image storage | Keeps binary images out of git objects. Standard for storing test fixtures >100KB |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | >=9.0 (already dep) | Test framework, parametrize, fixtures, custom markers | Core test runner |
| `pytest-timeout` | >=2.4 (already dep) | Timeout guards on rendering tests | Already configured at 5s global default |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `pixelmatch` | Pillow `ImageChops.difference()` only | No anti-aliasing detection, no perceptual color diff. Would cause false positives on AA pixels |
| `pixelmatch` | SSIM (scikit-image) | Structural similarity is better for perceptual comparison but overkill here. Adds heavy scipy dep. pixelmatch is purpose-built for screenshot VRT |
| `pytest-image-snapshot` | Custom helper | Plugin adds directory conventions, snapshot naming, CLI flag handling. But it's a thin wrapper and the project needs custom composite generation. Rolling our own ~30 lines is simpler and more controllable |
| `cairosvg` | `svglib` + ReportLab | CairoSVG is cairo-based (matching project stack), faster, and simpler API. svglib adds ReportLab dependency |
| `pymupdf` | `pdf2image` (poppler) | pymupdf has no external binary deps (poppler requires system install). Pure Python + C extension |

### Installation

```bash
uv add --dev pixelmatch cairosvg pymupdf
```

Note: `pixelmatch` requires PIL (already satisfied by Pillow dependency). `cairosvg` requires cairo (already satisfied by pycairo dependency). `pymupdf` is self-contained.

## Architecture Patterns

### Recommended Project Structure

```
tests/
├── conftest.py                          # Add snapshot-update flag, VRT fixtures
├── visual/
│   ├── __init__.py
│   ├── conftest.py                      # VRT-specific fixtures and helpers
│   ├── fixtures/                        # Purpose-built visual test code snippets
│   │   ├── python_visual.py
│   │   ├── rust_visual.rs
│   │   ├── cpp_visual.cpp
│   │   ├── javascript_visual.js
│   │   └── mlir_visual.mlir
│   ├── references/                      # Git LFS tracked reference images
│   │   ├── python_png_default.png
│   │   ├── python_svg_default.png       # (rasterized from SVG for comparison)
│   │   ├── python_pdf_default.png       # (rasterized from PDF for comparison)
│   │   ├── ...                          # All language x format x config combos
│   │   ├── python_png_shadow-off_chrome-off_lines-off.png
│   │   └── ...
│   ├── test_visual_regression.py        # VRT-01 through VRT-08
│   └── test_reliability_matrix.py       # REL-01, REL-02
├── ...existing test files...
```

### Pattern 1: Image Comparison Helper

**What:** A reusable comparison function that wraps pixelmatch and generates composites on failure.
**When to use:** Every visual regression test assertion.

```python
from pathlib import Path
from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch

def compare_images(
    actual: Image.Image,
    reference_path: Path,
    diff_output_dir: Path,
    test_name: str,
    threshold: float = 0.1,
    fail_percent: float = 0.001,  # 0.1% default
) -> tuple[bool, float]:
    """Compare actual image against reference.

    Returns:
        (passed, mismatch_pct) tuple
    """
    reference = Image.open(reference_path).convert("RGBA")
    actual_rgba = actual.convert("RGBA")

    # Sizes must match
    if actual_rgba.size != reference.size:
        return False, 100.0

    diff_img = Image.new("RGBA", reference.size)
    num_diff = pixelmatch(
        reference, actual_rgba, diff_img,
        threshold=threshold, includeAA=False
    )

    total_pixels = reference.size[0] * reference.size[1]
    mismatch_pct = (num_diff / total_pixels) * 100

    passed = mismatch_pct <= fail_percent

    if not passed:
        # Generate side-by-side composite: expected | actual | diff
        composite = _build_composite(reference, actual_rgba, diff_img)
        diff_output_dir.mkdir(parents=True, exist_ok=True)
        composite.save(diff_output_dir / f"{test_name}_composite.png")
        actual_rgba.save(diff_output_dir / f"{test_name}_actual.png")

    return passed, mismatch_pct


def _build_composite(
    expected: Image.Image,
    actual: Image.Image,
    diff: Image.Image,
) -> Image.Image:
    """Build side-by-side composite: expected | actual | diff."""
    w, h = expected.size
    gap = 4  # pixels between panels
    composite = Image.new("RGBA", (w * 3 + gap * 2, h), (40, 40, 40, 255))
    composite.paste(expected, (0, 0))
    composite.paste(actual, (w + gap, 0))
    composite.paste(diff, (w * 2 + gap * 2, 0))
    return composite
```

### Pattern 2: Render-to-PNG for SVG/PDF Comparison

**What:** Convert SVG/PDF output to PNG raster for pixel comparison against PNG references.
**When to use:** All SVG and PDF visual regression tests.

```python
import cairosvg
import pymupdf
from io import BytesIO
from PIL import Image

def svg_bytes_to_png(svg_data: bytes, scale: float = 2.0) -> Image.Image:
    """Rasterize SVG bytes to PIL Image for comparison."""
    png_bytes = cairosvg.svg2png(bytestring=svg_data, scale=scale)
    return Image.open(BytesIO(png_bytes)).convert("RGBA")

def pdf_bytes_to_png(pdf_data: bytes, dpi: int = 144) -> Image.Image:
    """Rasterize first page of PDF bytes to PIL Image for comparison."""
    doc = pymupdf.open(stream=pdf_data, filetype="pdf")
    page = doc[0]
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, alpha=True)
    img = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
    doc.close()
    return img
```

### Pattern 3: Snapshot Update Mechanism

**What:** CLI flag to regenerate reference images instead of comparing.
**When to use:** After intentional visual changes.

```python
# In conftest.py
def pytest_addoption(parser):
    parser.addoption(
        "--snapshot-update",
        action="store_true",
        default=False,
        help="Update visual regression reference images instead of comparing",
    )

@pytest.fixture
def snapshot_update(request):
    return request.config.getoption("--snapshot-update")
```

### Pattern 4: Parametrized Test Matrix

**What:** `pytest.mark.parametrize` for systematic coverage of language x format x config.
**When to use:** REL-01 (language x format) and REL-02 (feature toggles).

```python
LANGUAGES = ["python", "rust", "cpp", "javascript", "mlir"]
FORMATS = ["png", "svg", "pdf"]

@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("fmt", FORMATS)
@pytest.mark.slow
@pytest.mark.timeout(15)
def test_render_language_format(language, fmt, tmp_path, visual_fixture_path):
    """All language x format combinations produce valid output."""
    # ... render and validate
```

### Anti-Patterns to Avoid

- **Comparing SVG/PDF as text/bytes:** SVG output from Cairo contains non-deterministic attributes (IDs, whitespace). PDF has internal object IDs, timestamps. Always rasterize first.
- **Using pixel-exact comparison (threshold=0):** Anti-aliasing differs across systems. Even with pinned fonts, sub-pixel rendering varies. Always use a threshold.
- **Storing references in regular git:** PNG reference images are 50-150KB each. With 30+ references, this bloats git history. Use Git LFS.
- **Mixing test fixtures with visual fixtures:** Existing `tests/fixtures/` files are for unit tests. Visual fixtures need purpose-built short snippets covering key syntax.
- **Running VRT in the same CI job as unit tests:** VRT is slower (renders real images). Separate CI job enables parallelism and cleaner failure reporting.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Anti-aliasing-aware pixel comparison | Custom pixel diff loop | `pixelmatch` with `includeAA=False` | AA detection uses perceptual color distance algorithm. Reimplementing is error-prone and slower |
| SVG-to-PNG rasterization | Parse SVG XML manually | `cairosvg.svg2png()` | CairoSVG handles SVG 1.1 spec, text rendering, transforms. Building an SVG rasterizer is months of work |
| PDF-to-PNG rasterization | Cairo PDF surface re-render | `pymupdf` `page.get_pixmap()` | MuPDF handles PDF spec, font embedding, compositing. Reliable single-call conversion |
| Git large file tracking | Custom binary storage | Git LFS | Standard, integrated with GitHub, transparent after setup |
| Snapshot update CLI flag | Custom test runner script | pytest `addoption` + fixture | Standard pytest pattern, works with all test runners and CI systems |

**Key insight:** The comparison pipeline has three tricky parts (AA detection, SVG rasterization, PDF rasterization) that each have battle-tested libraries. The actual test infrastructure is just plumbing around these.

## Common Pitfalls

### Pitfall 1: Cross-Platform Font Rendering Differences

**What goes wrong:** Reference images generated on macOS look different than CI (Ubuntu) renders due to different font rasterization, hinting, and sub-pixel rendering.
**Why it happens:** Font rendering is system-level (FreeType on Linux, CoreText on macOS). Even the same font file renders differently.
**How to avoid:**
1. Generate all reference images on the CI platform (Ubuntu), not locally
2. Pin font (JetBrains Mono is already bundled in the project)
3. Use a permissive-enough threshold (0.1% should work, may need tuning)
4. Document that references must be regenerated on CI, not locally
**Warning signs:** Tests pass locally but fail on CI (or vice versa).

### Pitfall 2: CairoSVG Font Rendering vs Project Cairo Rendering

**What goes wrong:** CairoSVG rasterizes SVG with different font handling than the project's direct Cairo rendering, causing SVG reference mismatches even when the SVG is correct.
**Why it happens:** CairoSVG re-parses the SVG and re-renders it, potentially with different font resolution/fallback than the original Cairo context that generated it.
**How to avoid:** Use separate reference images per format. Don't compare PNG reference against SVG-rasterized-to-PNG. Each format gets its own reference.
**Warning signs:** SVG tests fail while PNG tests pass for the same content.

### Pitfall 3: Non-Deterministic SVG/PDF Output

**What goes wrong:** Cairo SVG/PDF surfaces produce slightly different byte output on different runs (internal IDs, timestamps, metadata).
**Why it happens:** Cairo's SVG/PDF writers embed metadata that varies between runs.
**How to avoid:** Always rasterize to PNG for comparison. Never compare SVG/PDF bytes directly.
**Warning signs:** Byte-level comparison fails on identical-looking output.

### Pitfall 4: Shadow Rendering Variability

**What goes wrong:** Pillow's GaussianBlur produces slightly different results across versions or platforms.
**Why it happens:** Floating-point arithmetic in blur kernel can vary.
**How to avoid:** Pin Pillow version in lock file (already done via `uv.lock`). May need slightly higher threshold for shadow-enabled tests.
**Warning signs:** Shadow tests are flaky, passing intermittently.

### Pitfall 5: Git LFS Not Initialized in CI

**What goes wrong:** CI checkout gets LFS pointer files (text stubs) instead of actual images. Tests fail with "cannot open image" or compare against tiny text files.
**Why it happens:** `actions/checkout@v4` doesn't fetch LFS files by default.
**How to avoid:** Add `lfs: true` to the checkout step in the CI workflow.
**Warning signs:** All VRT tests fail with file format errors or 100% mismatch.

### Pitfall 6: Image Size Mismatch on Comparison

**What goes wrong:** Actual render is a different size than reference (e.g., after layout change), and pixelmatch crashes or gives meaningless results.
**Why it happens:** Layout calculation changes affect canvas dimensions.
**How to avoid:** Check size match before pixelmatch call. On size mismatch, fail immediately with a clear message showing expected vs actual dimensions. The `--snapshot-update` flow handles regeneration.
**Warning signs:** Cryptic errors from pixelmatch about buffer lengths.

## Code Examples

### Complete VRT Test Example

```python
"""Visual regression tests for rendered output."""
import pytest
from pathlib import Path
from PIL import Image
from io import BytesIO

from codepicture.cli.orchestrator import generate_image
from codepicture.config.schema import RenderConfig
from codepicture.core.types import OutputFormat

REFERENCES_DIR = Path(__file__).parent / "references"
FIXTURES_DIR = Path(__file__).parent / "fixtures"

LANGUAGES = [
    ("python", "python_visual.py"),
    ("rust", "rust_visual.rs"),
    ("cpp", "cpp_visual.cpp"),
    ("javascript", "javascript_visual.js"),
    ("mlir", "mlir_visual.mlir"),
]


@pytest.mark.slow
@pytest.mark.timeout(15)
@pytest.mark.parametrize("language,fixture", LANGUAGES)
def test_visual_default_config(
    language, fixture, tmp_path, snapshot_update
):
    """Reference image matches for default config rendering."""
    code = (FIXTURES_DIR / fixture).read_text()
    output = tmp_path / f"{language}_default.png"
    config = RenderConfig()  # default config = PNG + all features

    generate_image(
        code=code, output_path=output, config=config,
        language=language, filename=fixture,
    )

    actual = Image.open(output).convert("RGBA")
    ref_path = REFERENCES_DIR / f"{language}_png_default.png"

    if snapshot_update:
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        actual.save(ref_path)
        return

    assert ref_path.exists(), f"Reference not found: {ref_path}. Run with --snapshot-update"
    passed, mismatch_pct = compare_images(
        actual, ref_path, tmp_path / "diffs", f"{language}_png_default"
    )
    print(f"  {language} PNG default: {mismatch_pct:.4f}% mismatch")
    assert passed, f"Visual mismatch: {mismatch_pct:.4f}% (threshold: 0.1%)"
```

### Git LFS Setup

```bash
# One-time setup
git lfs install
git lfs track "tests/visual/references/*.png"
git add .gitattributes
```

### CI Workflow for VRT Job

```yaml
visual-regression:
  runs-on: ubuntu-latest
  timeout-minutes: 10
  steps:
    - uses: actions/checkout@v4
      with:
        lfs: true  # CRITICAL: fetch LFS files

    - name: Install uv
      uses: astral-sh/setup-uv@v5
      with:
        enable-cache: true

    - name: Set up Python
      run: uv python install 3.13

    - name: Install dependencies
      run: uv sync --locked --dev

    - name: Run visual regression tests
      run: uv run pytest tests/visual/ -v --tb=long -m "slow"

    - name: Upload diff artifacts on failure
      if: failure()
      uses: actions/upload-artifact@v4
      with:
        name: visual-regression-diffs
        path: |
          /tmp/pytest-*/pytest-*/test_visual_*/*_composite.png
          /tmp/pytest-*/pytest-*/test_visual_*/*_actual.png
        retention-days: 14
```

### Fixture Content Design Pattern (Per Language)

```python
# tests/visual/fixtures/python_visual.py
# Purpose: Cover key Python syntax for visual regression
# Requirements: 5-10 lines, keywords, strings, comments, numbers, functions
def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b  # Returns the nth value
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pillow ImageChops.difference() only | pixelmatch with AA detection | ~2020+ | Eliminates false positives from anti-aliasing differences |
| Byte-level SVG/PDF comparison | Rasterize-then-compare | Standard practice | Only reliable approach for vector format VRT |
| Per-platform reference images | Single reference + threshold | Current best practice | Reduces maintenance burden from N platforms to 1 |
| Manual screenshot comparison | Automated CI comparison | Standard practice | Catches regressions before merge |

**Deprecated/outdated:**
- `imgcompare` library: Thin wrapper around Pillow ImageChops, no AA detection. Use pixelmatch instead.
- `needle` library: Selenium-focused, overkill for non-browser image comparison.

## Open Questions

1. **Exact threshold per format**
   - What we know: 0.1% is standard starting point for PNG. SVG and PDF rasterization may introduce additional variance.
   - What's unclear: Whether SVG/PDF rasterized comparisons need a higher threshold (e.g., 0.5%) due to CairoSVG/PyMuPDF rendering differences.
   - Recommendation: Start with 0.1% globally. Tune per-format if CI reveals consistent failures. The comparison helper supports per-test threshold override.

2. **Reference image generation environment**
   - What we know: Cross-platform font rendering differs. References should be generated on CI (Ubuntu) for consistency.
   - What's unclear: Whether initial reference generation requires a special CI run (e.g., `--snapshot-update` workflow).
   - Recommendation: First run generates references locally for development. Then regenerate on CI using `--snapshot-update` and commit the CI-generated references. Document this in a CONTRIBUTING note.

3. **Full Cartesian vs curated matrix**
   - What we know: 5 languages x 3 formats = 15 reliability tests. 3 toggles (shadow, chrome, lines) = 8 combinations for VRT-07.
   - What's unclear: Whether full Cartesian (5 x 3 x 8 = 120 tests) is worth it or curated core + edges is sufficient.
   - Recommendation: REL-01 uses full 5x3 matrix (15 tests). VRT-07 uses config variants on a single language (Python) only (8 tests). Total VRT: 5 (per-language default) + 8 (config variants) = 13 reference images for PNG, plus similar for SVG/PDF rasterized = ~39 references total. This is manageable.

4. **pymupdf vs pdf2image**
   - What we know: pymupdf is self-contained (no poppler). pdf2image requires poppler system install.
   - What's unclear: Whether pymupdf's PDF rendering matches Cairo's PDF output closely enough.
   - Recommendation: Use pymupdf. If rendering fidelity is insufficient, the threshold can absorb minor differences. Self-contained install is a significant CI advantage.

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `src/codepicture/render/renderer.py`, `canvas.py`, `shadow.py` - verified rendering pipeline, output formats, shadow behavior
- Codebase inspection: `pyproject.toml` - verified existing dependencies (Pillow, pycairo, pytest, pytest-timeout)
- Codebase inspection: `tests/` - verified test patterns, conftest.py fixtures, parametrize usage
- Codebase inspection: `.github/workflows/tests.yml` - verified CI setup (ubuntu-latest, uv, Python 3.13)

### Secondary (MEDIUM confidence)
- [pixelmatch-py GitHub](https://github.com/whtsky/pixelmatch-py) - API, PIL contrib module, threshold/AA parameters
- [pytest-image-snapshot GitHub](https://github.com/bmihelac/pytest-image-snapshot) - Snapshot update mechanism pattern
- [Pillow ImageChops docs](https://pillow.readthedocs.io/en/stable/reference/ImageChops.html) - difference() API
- [CairoSVG docs](https://cairosvg.org/documentation/) - svg2png API, bytestring parameter
- [PyMuPDF docs](https://pymupdf.readthedocs.io/en/latest/recipes-images.html) - page.get_pixmap() API
- [Git LFS docs](https://git-lfs.com/) - track, .gitattributes setup
- [GitHub Actions upload-artifact](https://github.com/actions/upload-artifact) - `if: failure()` pattern

### Tertiary (LOW confidence)
- WebSearch results on cross-platform font rendering differences - confirmed as common VRT pitfall but specific threshold guidance varies

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pixelmatch, CairoSVG, PyMuPDF are well-established, verified via multiple sources
- Architecture: HIGH - patterns derived from codebase inspection + established VRT practices
- Pitfalls: HIGH - cross-platform rendering, LFS checkout, size mismatch are well-documented issues

**Research date:** 2026-01-30
**Valid until:** 2026-03-01 (stable domain, libraries change slowly)
