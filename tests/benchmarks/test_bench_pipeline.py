"""End-to-end pipeline benchmarks for generate_image with varying input sizes."""

import pytest

from codepicture import RenderConfig
from codepicture.cli.orchestrator import generate_image

SIZES = ["small", "medium", "large"]


@pytest.mark.timeout(0)
@pytest.mark.parametrize("size", SIZES)
def test_bench_pipeline_e2e(benchmark, sized_inputs, size, tmp_path):
    """Benchmark full pipeline for different input sizes."""
    code = sized_inputs[size]
    config = RenderConfig()
    output_file = tmp_path / f"bench_{size}.png"

    def run():
        generate_image(
            code=code,
            output_path=output_file,
            config=config,
            language="python",
            filename=f"bench_{size}.py",
        )

    benchmark(run)
    # Verify output was actually created
    assert output_file.exists()
    assert output_file.stat().st_size > 0
