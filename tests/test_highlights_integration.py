"""Integration tests for the highlight rendering pipeline.

Tests exercise the full render pipeline (highlighter -> layout -> renderer)
to verify highlight behavior end-to-end, including word-wrap interactions,
empty/None highlight lists, and all-lines highlighting.
"""

from __future__ import annotations

import pytest

from codepicture import (
    LayoutEngine,
    PangoTextMeasurer,
    PygmentsHighlighter,
    Renderer,
    get_theme,
    register_bundled_fonts,
)
from codepicture.config import RenderConfig

# Sample code snippet used across integration tests
SAMPLE_CODE = """\
# greeting
def hello(name):
    msg = f"Hello, {name}!"
    print(msg)
    return msg
"""


@pytest.fixture(scope="module", autouse=True)
def _register_fonts() -> None:
    """Register bundled fonts once for all tests in this module."""
    register_bundled_fonts()


def _render_code(code: str, config: RenderConfig) -> bytes:
    """Run the full codepicture pipeline and return raw output bytes."""
    highlighter = PygmentsHighlighter()
    language = "python"
    tokens = highlighter.highlight(code, language)

    measurer = PangoTextMeasurer()
    engine = LayoutEngine(measurer, config)
    metrics = engine.calculate_metrics(tokens)

    theme = get_theme(config.theme)
    renderer = Renderer(config)
    result = renderer.render(tokens, metrics, theme)
    return result.data


class TestHighlightRenders:
    """Tests that highlight configs render without errors."""

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_highlight_renders_without_error(self):
        """Single highlighted line renders successfully."""
        config = RenderConfig(highlight_lines=["2"])
        data = _render_code(SAMPLE_CODE, config)
        assert len(data) > 0

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_highlight_word_wrap_renders_without_error(self):
        """Highlighted line with word wrap renders successfully."""
        config = RenderConfig(highlight_lines=["1"], window_width=300)
        data = _render_code(SAMPLE_CODE, config)
        assert len(data) > 0

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_highlight_all_lines(self):
        """Highlighting every line in a snippet renders successfully."""
        lines = SAMPLE_CODE.strip().splitlines()
        all_specs = [str(i + 1) for i in range(len(lines))]
        config = RenderConfig(highlight_lines=all_specs)
        data = _render_code(SAMPLE_CODE, config)
        assert len(data) > 0


class TestHighlightNoChange:
    """Tests that empty/None highlights produce identical output to no highlights."""

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_highlight_empty_list_no_change(self):
        """Empty highlight_lines=[] produces identical output to no highlights."""
        config_no_hl = RenderConfig()
        config_empty = RenderConfig(highlight_lines=[])

        data_no_hl = _render_code(SAMPLE_CODE, config_no_hl)
        data_empty = _render_code(SAMPLE_CODE, config_empty)

        assert data_no_hl == data_empty

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_highlight_none_no_change(self):
        """highlight_lines=None produces identical output to no highlights."""
        config_no_hl = RenderConfig()
        config_none = RenderConfig(highlight_lines=None)

        data_no_hl = _render_code(SAMPLE_CODE, config_no_hl)
        data_none = _render_code(SAMPLE_CODE, config_none)

        assert data_no_hl == data_none
