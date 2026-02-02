"""Shared benchmark fixtures with pre-computed inputs for stage benchmarking."""

from pathlib import Path

import pytest

from codepicture import (
    LayoutEngine,
    PangoTextMeasurer,
    PygmentsHighlighter,
    RenderConfig,
    register_bundled_fonts,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
BENCHMARK_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

LANGUAGE_MAP = {
    "python": "sample_python.py",
    "rust": "sample_rust.rs",
    "cpp": "sample_cpp.cpp",
    "javascript": "sample_javascript.js",
    "mlir": "sample_mlir.mlir",
}

SIZED_INPUT_FILES = {
    "small": "small.py",
    "medium": "medium.py",
    "large": "large.py",
}


@pytest.fixture(scope="session", autouse=True)
def register_fonts():
    """Register bundled fonts once for the entire benchmark session."""
    register_bundled_fonts()


@pytest.fixture(scope="session")
def code_samples() -> dict[str, str]:
    """Code strings for each supported language, read from fixture files."""
    samples = {}
    for language, filename in LANGUAGE_MAP.items():
        filepath = FIXTURES_DIR / filename
        samples[language] = filepath.read_text()
    return samples


@pytest.fixture(scope="session")
def highlighter() -> PygmentsHighlighter:
    """Shared PygmentsHighlighter instance."""
    return PygmentsHighlighter()


@pytest.fixture(scope="session")
def pre_tokenized(code_samples, highlighter) -> dict[str, list]:
    """Pre-tokenized output from highlighter.highlight() for each language."""
    tokenized = {}
    for language, code in code_samples.items():
        tokenized[language] = highlighter.highlight(code, language)
    return tokenized


@pytest.fixture(scope="session")
def default_config() -> RenderConfig:
    """Default RenderConfig for benchmarks."""
    return RenderConfig()


@pytest.fixture(scope="session")
def layout_engine(default_config) -> LayoutEngine:
    """Shared LayoutEngine with PangoTextMeasurer."""
    return LayoutEngine(PangoTextMeasurer(), default_config)


@pytest.fixture(scope="session")
def pre_computed_metrics(pre_tokenized, layout_engine) -> dict[str, object]:
    """Pre-computed layout metrics for each language."""
    metrics = {}
    for language, tokens in pre_tokenized.items():
        metrics[language] = layout_engine.calculate_metrics(tokens)
    return metrics


@pytest.fixture(scope="session")
def sized_inputs() -> dict[str, str]:
    """Code strings of varying sizes: small (~10 lines), medium (~50), large (~200)."""
    inputs = {}
    for size, filename in SIZED_INPUT_FILES.items():
        filepath = BENCHMARK_FIXTURES_DIR / filename
        inputs[size] = filepath.read_text()
    return inputs
