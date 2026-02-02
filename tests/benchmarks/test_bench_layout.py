"""Benchmark tests for the layout (metrics calculation) pipeline stage."""

import pytest

from codepicture import LayoutEngine, PangoTextMeasurer

LANGUAGES = ["python", "rust", "cpp", "javascript", "mlir"]


@pytest.mark.timeout(0)
@pytest.mark.parametrize("lang", LANGUAGES)
def test_bench_layout(benchmark, pre_tokenized, default_config, lang):
    """Benchmark LayoutEngine.calculate_metrics() for a single language."""
    tokens = pre_tokenized[lang]
    measurer = PangoTextMeasurer()
    engine = LayoutEngine(measurer, default_config)
    benchmark(engine.calculate_metrics, tokens)
