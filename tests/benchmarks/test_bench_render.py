"""Benchmark tests for the render pipeline stage with feature toggle variants."""

import pytest

from codepicture import (
    LayoutEngine,
    PangoTextMeasurer,
    RenderConfig,
    Renderer,
    get_theme,
)

LANGUAGES = ["python", "rust", "cpp", "javascript", "mlir"]

FEATURE_CONFIGS = [
    (
        "minimal",
        {"shadow": False, "window_controls": False, "show_line_numbers": False},
    ),
    (
        "with_line_numbers",
        {"shadow": False, "window_controls": False, "show_line_numbers": True},
    ),
    ("full", {"shadow": True, "window_controls": True, "show_line_numbers": True}),
]


@pytest.mark.timeout(0)
@pytest.mark.parametrize("lang", LANGUAGES)
def test_bench_render(
    benchmark, pre_tokenized, pre_computed_metrics, default_config, lang
):
    """Benchmark Renderer.render() for a single language with default config."""
    tokens = pre_tokenized[lang]
    metrics = pre_computed_metrics[lang]
    theme = get_theme(default_config.theme)
    renderer = Renderer(default_config)
    benchmark(renderer.render, tokens, metrics, theme)


@pytest.mark.timeout(0)
@pytest.mark.parametrize(
    "config_name,overrides", FEATURE_CONFIGS, ids=[c[0] for c in FEATURE_CONFIGS]
)
def test_bench_render_features(
    benchmark, highlighter, code_samples, config_name, overrides
):
    """Benchmark Renderer.render() with different feature toggles (Python)."""
    config = RenderConfig(**overrides)
    code = code_samples["python"]
    tokens = highlighter.highlight(code, "python")
    measurer = PangoTextMeasurer()
    engine = LayoutEngine(measurer, config)
    metrics = engine.calculate_metrics(tokens)
    theme = get_theme(config.theme)
    renderer = Renderer(config)
    benchmark(renderer.render, tokens, metrics, theme)
