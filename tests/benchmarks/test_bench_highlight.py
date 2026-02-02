"""Benchmark tests for the highlight (tokenization) pipeline stage."""

import pytest

LANGUAGES = [
    ("python", "python"),
    ("rust", "rust"),
    ("cpp", "cpp"),
    ("javascript", "javascript"),
    ("mlir", "mlir"),
]


@pytest.mark.timeout(0)
@pytest.mark.parametrize(
    "lang_key,lang_id", LANGUAGES, ids=[lang[0] for lang in LANGUAGES]
)
def test_bench_highlight(benchmark, highlighter, code_samples, lang_key, lang_id):
    """Benchmark highlighter.highlight() for a single language."""
    code = code_samples[lang_key]
    benchmark(highlighter.highlight, code, lang_id)
