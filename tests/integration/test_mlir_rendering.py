"""Integration tests for MLIR rendering.

Regression tests for the MLIR hang fix (Phase 8) and corpus rendering.
Ensures MLIR fixtures render within timeout and produce valid images
with minimal lexer errors.
"""

import pytest
from pathlib import Path

from codepicture.highlight.mlir_lexer import MlirLexer
from codepicture.cli.orchestrator import generate_image
from codepicture.config.schema import RenderConfig
from pygments.token import Error

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "mlir"

CORPUS_FILES = [
    "basic_module.mlir",
    "complex_attributes.mlir",
    "deep_nesting.mlir",
    "long_lines.mlir",
    "edge_cases.mlir",
]


@pytest.mark.slow
@pytest.mark.timeout(10)
def test_mlir_render_completes(tmp_path: Path) -> None:
    """Render test.mlir must complete within timeout -- regression for hang fix."""
    test_mlir = FIXTURES_DIR / "test.mlir"
    assert test_mlir.exists(), f"test.mlir not found at {test_mlir}"

    code = test_mlir.read_text()
    output = tmp_path / "test_output.png"
    config = RenderConfig()

    generate_image(
        code=code,
        output_path=output,
        config=config,
        language=None,
        filename="test.mlir",
    )

    assert output.exists(), "Output image was not created"
    assert output.stat().st_size > 0, "Output image is empty"


def test_mlir_lexer_minimal_error_tokens() -> None:
    """MLIR lexer should not produce excessive Error tokens on valid MLIR."""
    test_mlir = FIXTURES_DIR / "test.mlir"
    assert test_mlir.exists(), f"test.mlir not found at {test_mlir}"

    code = test_mlir.read_text()
    lexer = MlirLexer()
    tokens = list(lexer.get_tokens(code))
    error_tokens = [(t, v) for t, v in tokens if t is Error]

    assert len(error_tokens) < 10, (
        f"Too many Error tokens ({len(error_tokens)}): "
        f"{[v for _, v in error_tokens[:20]]}"
    )


@pytest.mark.slow
@pytest.mark.timeout(10)
@pytest.mark.parametrize("fixture_name", CORPUS_FILES)
def test_mlir_corpus_renders(fixture_name: str, tmp_path: Path) -> None:
    """All MLIR corpus files render successfully."""
    fixture_path = FIXTURES_DIR / fixture_name
    assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

    code = fixture_path.read_text()
    output = tmp_path / f"{fixture_name}.png"
    config = RenderConfig()

    generate_image(
        code=code,
        output_path=output,
        config=config,
        language=None,
        filename=fixture_name,
    )

    assert output.exists(), f"Output image not created for {fixture_name}"
    assert output.stat().st_size > 0, f"Output image empty for {fixture_name}"


@pytest.mark.parametrize("fixture_name", CORPUS_FILES)
def test_mlir_corpus_lexer_quality(fixture_name: str) -> None:
    """MLIR corpus files should tokenize with minimal Error tokens."""
    fixture_path = FIXTURES_DIR / fixture_name
    assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

    code = fixture_path.read_text()
    lexer = MlirLexer()
    tokens = list(lexer.get_tokens(code))
    error_tokens = [(t, v) for t, v in tokens if t is Error]

    assert len(tokens) > 5, f"{fixture_name} produced too few tokens ({len(tokens)})"
    assert len(error_tokens) < 10, (
        f"{fixture_name} has too many Error tokens ({len(error_tokens)}): "
        f"{[v for _, v in error_tokens[:20]]}"
    )
