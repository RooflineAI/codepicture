"""Reliability matrix tests for all language/format/config combinations.

REL-01: 5 languages x 3 formats = 15 combinations must produce valid output.
REL-02: Feature toggle combinations must all produce valid output.
"""

from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from codepicture.config import RenderConfig
from codepicture.core.types import OutputFormat

from .conftest import render_fixture

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"

LANGUAGES = [
    ("python", "python_visual.py"),
    ("rust", "rust_visual.rs"),
    ("cpp", "cpp_visual.cpp"),
    ("javascript", "javascript_visual.js"),
    ("mlir", "mlir_visual.mlir"),
]

FORMATS = [
    OutputFormat.PNG,
    OutputFormat.SVG,
    OutputFormat.PDF,
]

# Build parametrized pairs for the language x format matrix
LANG_FORMAT_COMBOS = [
    pytest.param(lang, fixture, fmt, id=f"{lang}-{fmt.value}")
    for lang, fixture in LANGUAGES
    for fmt in FORMATS
]


# ---------------------------------------------------------------------------
# REL-01: Language x Format Matrix
# ---------------------------------------------------------------------------


@pytest.mark.timeout(30)
@pytest.mark.parametrize("language,fixture_file,output_format", LANG_FORMAT_COMBOS)
def test_render_language_format(
    language: str,
    fixture_file: str,
    output_format: OutputFormat,
) -> None:
    """Every language x format combination produces valid, non-empty output."""
    fixture_path = FIXTURES_DIR / fixture_file
    config = RenderConfig(output_format=output_format)

    data, fmt_ext = render_fixture(fixture_path, config, language=language)

    # Non-empty output
    assert len(data) > 0, f"{language}/{output_format.value} produced empty output"

    # Format-specific validation
    if output_format is OutputFormat.PNG:
        assert data[:4] == b"\x89PNG", "PNG output missing magic bytes"
        img = Image.open(BytesIO(data))
        assert img.width > 0 and img.height > 0, "PNG has zero dimensions"

    elif output_format is OutputFormat.SVG:
        text = data.decode("utf-8")
        assert "<svg" in text, "SVG output missing <svg tag"

    elif output_format is OutputFormat.PDF:
        assert data[:4] == b"%PDF", "PDF output missing %PDF header"


@pytest.mark.timeout(30)
@pytest.mark.parametrize("language,fixture_file,output_format", LANG_FORMAT_COMBOS)
def test_render_completes_within_timeout(
    language: str,
    fixture_file: str,
    output_format: OutputFormat,
) -> None:
    """No language/format combination takes more than 10 seconds."""
    fixture_path = FIXTURES_DIR / fixture_file
    config = RenderConfig(output_format=output_format)

    start = time.monotonic()
    render_fixture(fixture_path, config, language=language)
    elapsed = time.monotonic() - start

    assert elapsed < 10.0, (
        f"{language}/{output_format.value} took {elapsed:.2f}s (limit: 10s)"
    )
