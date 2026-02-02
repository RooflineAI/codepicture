"""Visual regression testing infrastructure.

Provides image comparison helpers, rasterization utilities, and fixtures
for snapshot-based visual regression tests.
"""

from __future__ import annotations

import os
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from PIL import Image, ImageDraw, ImageFont
from pixelmatch.contrib.PIL import pixelmatch

if TYPE_CHECKING:
    from codepicture.config import RenderConfig

# ---------------------------------------------------------------------------
# Ensure cairocffi can find the Homebrew Cairo library on macOS.
#
# pycairo links at build time and works fine, but cairocffi (used by
# cairosvg for SVG visual tests) uses ctypes.util.find_library() at
# import time, which doesn't search Homebrew paths on macOS.
# ---------------------------------------------------------------------------

if sys.platform == "darwin" and "DYLD_LIBRARY_PATH" not in os.environ:
    try:
        prefix = subprocess.check_output(
            ["brew", "--prefix", "cairo"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        lib_dir = os.path.join(prefix, "lib")
        if os.path.isfile(os.path.join(lib_dir, "libcairo.2.dylib")):
            os.environ["DYLD_LIBRARY_PATH"] = lib_dir
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def snapshot_update(request) -> bool:
    """Whether --snapshot-update was passed on the CLI."""
    return request.config.getoption("--snapshot-update")


@pytest.fixture
def visual_fixtures_dir() -> Path:
    """Path to visual test fixture source files."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def references_dir() -> Path:
    """Path to visual regression reference images."""
    ref = Path(__file__).parent / "references"
    ref.mkdir(exist_ok=True)
    return ref


@pytest.fixture
def diff_output_dir(tmp_path: Path) -> Path:
    """Temporary directory for diff composites on failure."""
    d = tmp_path / "visual_diffs"
    d.mkdir(exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Image comparison helpers
# ---------------------------------------------------------------------------


def compare_images(
    actual_image: Image.Image,
    reference_path: Path,
    diff_output_dir: Path,
    test_name: str,
    threshold: float = 0.1,
    fail_percent: float = 0.001,
) -> tuple[bool, float]:
    """Compare an actual image against a reference snapshot.

    Args:
        actual_image: The rendered image to check.
        reference_path: Path to the reference PNG on disk.
        diff_output_dir: Directory where failure composites are saved.
        test_name: Label used in file names and diagnostics.
        threshold: Per-pixel colour-distance threshold (0-1). Default 0.1.
        fail_percent: Maximum percentage of differing pixels before failure.

    Returns:
        (passed, mismatch_pct) where *passed* is True when the mismatch
        percentage is at or below *fail_percent*.
    """
    reference = Image.open(reference_path).convert("RGBA")
    actual = actual_image.convert("RGBA")

    # Size mismatch is an automatic failure
    if reference.size != actual.size:
        note = f"Size mismatch: reference {reference.size} vs actual {actual.size}"
        note_path = diff_output_dir / f"{test_name}_size_mismatch.txt"
        note_path.write_text(note)
        print(f"  {test_name}: FAIL — {note}")
        return False, 100.0

    # Run pixelmatch
    diff_img = Image.new("RGBA", reference.size)
    num_diff = pixelmatch(
        reference,
        actual,
        diff_img,
        threshold=threshold,
        includeAA=False,
    )
    total_pixels = reference.size[0] * reference.size[1]
    mismatch_pct = (num_diff / total_pixels) * 100 if total_pixels > 0 else 0.0

    passed = mismatch_pct <= fail_percent
    status = "PASS" if passed else "FAIL"
    print(f"  {test_name}: {status} — {mismatch_pct:.4f}% pixels differ")

    if not passed:
        composite = build_composite(reference, actual, diff_img)
        composite_path = diff_output_dir / f"{test_name}_composite.png"
        composite.save(composite_path)
        print(f"  Composite saved: {composite_path}")

    return passed, mismatch_pct


def build_composite(
    expected: Image.Image,
    actual: Image.Image,
    diff: Image.Image,
) -> Image.Image:
    """Build a side-by-side composite: expected | actual | diff.

    Each panel is labelled at the top for quick visual triage.
    """
    w, h = expected.size
    label_height = 24
    composite = Image.new("RGBA", (w * 3, h + label_height), (30, 30, 30, 255))
    draw = ImageDraw.Draw(composite)

    # Try to use a reasonable font; fall back to default if unavailable
    try:
        font = ImageFont.truetype("Arial", 14)
    except OSError:
        font = ImageFont.load_default()

    labels = ["Expected", "Actual", "Diff"]
    for idx, (label, img) in enumerate(
        zip(labels, [expected, actual, diff], strict=True)
    ):
        x_offset = idx * w
        draw.text((x_offset + 4, 4), label, fill=(255, 255, 255, 255), font=font)
        composite.paste(img, (x_offset, label_height))

    return composite


# ---------------------------------------------------------------------------
# Rasterization helpers
# ---------------------------------------------------------------------------


def svg_to_png(svg_data: bytes, scale: float = 2.0) -> Image.Image:
    """Rasterize SVG bytes to a Pillow RGBA Image.

    Uses cairosvg for high-fidelity SVG rendering.  Raises pytest.skip
    if cairocffi (the cairosvg backend) cannot find the system Cairo library.
    """
    try:
        import cairosvg
    except OSError as exc:
        pytest.skip(f"cairosvg unavailable (cairocffi cannot find Cairo): {exc}")

    png_bytes = cairosvg.svg2png(bytestring=svg_data, scale=scale)
    return Image.open(BytesIO(png_bytes)).convert("RGBA")


def pdf_to_png(pdf_data: bytes, dpi: int = 144) -> Image.Image:
    """Rasterize the first page of a PDF to a Pillow RGBA Image.

    Uses PyMuPDF (pymupdf) for rendering.
    """
    import pymupdf

    doc = pymupdf.open(stream=pdf_data, filetype="pdf")
    page = doc[0]
    # Scale matrix: default PDF is 72 dpi, target *dpi*
    zoom = dpi / 72
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=True)
    img = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
    doc.close()
    return img


# ---------------------------------------------------------------------------
# Full-pipeline render helper
# ---------------------------------------------------------------------------


def render_fixture(
    fixture_path: Path,
    config: RenderConfig,
    language: str | None = None,
) -> tuple[bytes, str]:
    """Run the full codepicture pipeline on a fixture file and return raw bytes.

    Args:
        fixture_path: Path to the source code fixture.
        config: RenderConfig controlling output format, theme, etc.
        language: Explicit language override. Auto-detected from extension if None.

    Returns:
        (data_bytes, format_extension) — e.g. (b'...', 'png').
    """
    from codepicture import (
        LayoutEngine,
        PangoTextMeasurer,
        PygmentsHighlighter,
        Renderer,
        get_theme,
        register_bundled_fonts,
    )

    register_bundled_fonts()

    code = fixture_path.read_text()

    # Highlight
    highlighter = PygmentsHighlighter()
    if language is None:
        language = highlighter.detect_language(code, fixture_path.name)
    tokens = highlighter.highlight(code, language)

    # Layout
    measurer = PangoTextMeasurer()
    engine = LayoutEngine(measurer, config)
    metrics = engine.calculate_metrics(tokens)

    # Render
    theme = get_theme(config.theme)
    renderer = Renderer(config)
    result = renderer.render(tokens, metrics, theme)

    return result.data, result.format.value
