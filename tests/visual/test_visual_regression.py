"""Visual regression tests for codepicture rendering output.

Compares rendered images against stored reference snapshots.
Covers 5 core languages x 3 output formats (PNG, SVG, PDF) plus
config variant combinations for feature toggles.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from codepicture.config import RenderConfig

from .conftest import compare_images, pdf_to_png, render_fixture, svg_to_png

# ---------------------------------------------------------------------------
# Language x Format matrix (15 combinations)
# ---------------------------------------------------------------------------

LANGUAGES = [
    ("python", "python_visual.py"),
    ("rust", "rust_visual.rs"),
    ("cpp", "cpp_visual.cpp"),
    ("javascript", "javascript_visual.js"),
    ("mlir", "mlir_visual.mlir"),
]

FORMATS = ["png", "svg", "pdf"]


def _render_to_image(
    fixture_path: Path, language: str, output_format: str
) -> Image.Image:
    """Render a fixture and return the result as a Pillow RGBA Image."""
    config = RenderConfig(output_format=output_format)
    data, _ext = render_fixture(fixture_path, config, language=language)

    if output_format == "png":
        return Image.open(BytesIO(data)).convert("RGBA")
    elif output_format == "svg":
        return svg_to_png(data)
    elif output_format == "pdf":
        return pdf_to_png(data)
    else:
        raise ValueError(f"Unknown format: {output_format}")


# ---------------------------------------------------------------------------
# Core visual regression tests: 5 languages x 3 formats
# ---------------------------------------------------------------------------


@pytest.mark.timeout(30)
@pytest.mark.parametrize(
    "language,fixture_file",
    LANGUAGES,
    ids=[lang for lang, _ in LANGUAGES],
)
@pytest.mark.parametrize("output_format", FORMATS)
def test_visual_regression(
    language: str,
    fixture_file: str,
    output_format: str,
    snapshot_update: bool,
    visual_fixtures_dir: Path,
    references_dir: Path,
    diff_output_dir: Path,
) -> None:
    """Compare rendered output against reference snapshot.

    Parametrized over LANGUAGES x FORMATS for 15 total combinations.
    """
    fixture_path = visual_fixtures_dir / fixture_file
    test_name = f"{language}_{output_format}_default"
    reference_path = references_dir / f"{test_name}.png"

    actual = _render_to_image(fixture_path, language, output_format)

    if snapshot_update or not reference_path.exists():
        actual.save(reference_path)
        action = "updated" if snapshot_update else "created"
        pytest.skip(f"Reference image {action}: {reference_path.name}")

    passed, mismatch_pct = compare_images(
        actual, reference_path, diff_output_dir, test_name
    )
    assert passed, (
        f"Visual regression failed for {test_name}: "
        f"{mismatch_pct:.4f}% pixels differ (threshold: 0.001%)"
    )


# ---------------------------------------------------------------------------
# Config variant tests (Python fixture only, PNG format)
# ---------------------------------------------------------------------------

CONFIG_VARIANTS = [
    ("shadow-off", {"shadow": False}),
    ("chrome-off", {"window_controls": False}),
    ("lines-off", {"show_line_numbers": False}),
    ("shadow-off_chrome-off", {"shadow": False, "window_controls": False}),
    (
        "shadow-off_chrome-off_lines-off",
        {"shadow": False, "window_controls": False, "show_line_numbers": False},
    ),
]


@pytest.mark.timeout(30)
@pytest.mark.parametrize(
    "variant_name,overrides",
    CONFIG_VARIANTS,
    ids=[name for name, _ in CONFIG_VARIANTS],
)
def test_visual_config_variant(
    variant_name: str,
    overrides: dict,
    snapshot_update: bool,
    visual_fixtures_dir: Path,
    references_dir: Path,
    diff_output_dir: Path,
) -> None:
    """Compare config variant rendering against reference snapshot.

    Tests feature toggle combinations (shadow, chrome, line numbers)
    using the Python fixture in PNG format only.
    """
    fixture_path = visual_fixtures_dir / "python_visual.py"
    test_name = f"python_png_{variant_name}"
    reference_path = references_dir / f"{test_name}.png"

    config = RenderConfig(output_format="png", **overrides)
    data, _ext = render_fixture(fixture_path, config, language="python")
    actual = Image.open(BytesIO(data)).convert("RGBA")

    if snapshot_update or not reference_path.exists():
        actual.save(reference_path)
        pytest.skip(
            f"Reference image {'updated' if snapshot_update else 'created'}: "
            f"{reference_path.name}"
        )

    passed, mismatch_pct = compare_images(
        actual, reference_path, diff_output_dir, test_name
    )
    assert passed, (
        f"Visual regression failed for {test_name}: "
        f"{mismatch_pct:.4f}% pixels differ (threshold: 0.001%)"
    )


# ---------------------------------------------------------------------------
# Word wrap and fixed size tests (Python fixture only, PNG format)
# ---------------------------------------------------------------------------

WORDWRAP_FIXEDSIZE_VARIANTS = [
    ("wordwrap-600", {"window_width": 600}),
    ("wordwrap-400", {"window_width": 400}),
    ("fixed-800x300", {"window_width": 800, "window_height": 300}),
    ("fixed-600x400_wordwrap", {"window_width": 600, "window_height": 400}),
]


@pytest.mark.timeout(30)
@pytest.mark.parametrize(
    "variant_name,overrides",
    WORDWRAP_FIXEDSIZE_VARIANTS,
    ids=[name for name, _ in WORDWRAP_FIXEDSIZE_VARIANTS],
)
def test_visual_wordwrap_fixedsize(
    variant_name: str,
    overrides: dict,
    snapshot_update: bool,
    visual_fixtures_dir: Path,
    references_dir: Path,
    diff_output_dir: Path,
) -> None:
    """Compare word wrap / fixed size rendering against reference snapshot.

    Tests word wrapping at various widths and fixed window dimensions
    using the Python fixture in PNG format only.
    """
    fixture_path = visual_fixtures_dir / "python_visual.py"
    test_name = f"python_png_{variant_name}"
    reference_path = references_dir / f"{test_name}.png"

    config = RenderConfig(output_format="png", **overrides)
    data, _ext = render_fixture(fixture_path, config, language="python")
    actual = Image.open(BytesIO(data)).convert("RGBA")

    if snapshot_update or not reference_path.exists():
        actual.save(reference_path)
        pytest.skip(
            f"Reference image {'updated' if snapshot_update else 'created'}: "
            f"{reference_path.name}"
        )

    passed, mismatch_pct = compare_images(
        actual, reference_path, diff_output_dir, test_name
    )
    assert passed, (
        f"Visual regression failed for {test_name}: "
        f"{mismatch_pct:.4f}% pixels differ (threshold: 0.001%)"
    )
