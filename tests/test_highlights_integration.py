"""Integration tests for the highlight rendering pipeline.

Tests exercise the full render pipeline (highlighter -> layout -> renderer)
to verify highlight behavior end-to-end, including word-wrap interactions,
empty/None highlight lists, all-lines highlighting, named styles, focus
mode dimming, CLI --highlight flag, and gutter indicators.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from codepicture import (
    LayoutEngine,
    PangoTextMeasurer,
    PygmentsHighlighter,
    Renderer,
    get_theme,
    register_bundled_fonts,
)
from codepicture.cli.app import app
from codepicture.config import RenderConfig
from codepicture.core.types import Color
from codepicture.render.highlights import (
    FOCUS_DIM_OPACITY,
    HighlightStyle,
    parse_highlight_specs,
)
from codepicture.render.renderer import _dim_color

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


# ---------------------------------------------------------------------------
# CLI integration tests for --highlight flag
# ---------------------------------------------------------------------------

runner = CliRunner()


class TestHighlightFlagCLI:
    """CLI integration tests for the --highlight flag."""

    @pytest.mark.slow
    @pytest.mark.timeout(30)
    def test_highlight_flag_single_style(self, tmp_path):
        """--highlight '3:add' produces output without error."""
        src = tmp_path / "code.py"
        src.write_text(SAMPLE_CODE)
        out = tmp_path / "out.png"

        result = runner.invoke(app, [str(src), "-o", str(out), "--highlight", "3:add"])
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert out.exists()
        assert out.stat().st_size > 0

    @pytest.mark.slow
    @pytest.mark.timeout(30)
    def test_highlight_flag_multiple(self, tmp_path):
        """--highlight '1:add' --highlight '3:remove' succeeds."""
        src = tmp_path / "code.py"
        src.write_text(SAMPLE_CODE)
        out = tmp_path / "out.png"

        result = runner.invoke(
            app,
            [str(src), "-o", str(out), "--highlight", "1:add", "--highlight", "3:remove"],
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert out.exists()

    @pytest.mark.slow
    @pytest.mark.timeout(30)
    def test_highlight_flag_no_style_defaults(self, tmp_path):
        """--highlight '3' succeeds (defaults to highlight style)."""
        src = tmp_path / "code.py"
        src.write_text(SAMPLE_CODE)
        out = tmp_path / "out.png"

        result = runner.invoke(app, [str(src), "-o", str(out), "--highlight", "3"])
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert out.exists()

    @pytest.mark.slow
    @pytest.mark.timeout(30)
    def test_highlight_flag_invalid_style(self, tmp_path):
        """--highlight '3:bogus' exits with error."""
        src = tmp_path / "code.py"
        src.write_text(SAMPLE_CODE)
        out = tmp_path / "out.png"

        result = runner.invoke(app, [str(src), "-o", str(out), "--highlight", "3:bogus"])
        assert result.exit_code != 0

    @pytest.mark.timeout(5)
    def test_old_highlight_lines_flag_removed(self, tmp_path):
        """--highlight-lines flag no longer exists and exits with error."""
        src = tmp_path / "code.py"
        src.write_text(SAMPLE_CODE)
        out = tmp_path / "out.png"

        result = runner.invoke(
            app, [str(src), "-o", str(out), "--highlight-lines", "3"]
        )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Focus mode dimming integration tests
# ---------------------------------------------------------------------------


class TestFocusModeDimming:
    """Integration tests for focus mode dimming."""

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_focus_mode_produces_output(self):
        """Render with highlights=["2:focus"] produces non-empty PNG output."""
        config = RenderConfig(highlights=["2:focus"])
        data = _render_code(SAMPLE_CODE, config)
        assert len(data) > 0

    def test_focus_dim_opacity_value(self):
        """FOCUS_DIM_OPACITY == 0.35 (imported from highlights module)."""
        assert FOCUS_DIM_OPACITY == 0.35

    def test_dim_color_function(self):
        """_dim_color reduces alpha by the given factor."""
        result = _dim_color(Color(255, 255, 255, 200), 0.35)
        assert result == Color(r=255, g=255, b=255, a=70)

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_focus_with_other_styles(self):
        """Render with focus + add produces output (both styles visible)."""
        config = RenderConfig(highlights=["2:focus", "4:add"])
        data = _render_code(SAMPLE_CODE, config)
        assert len(data) > 0

    def test_no_focus_no_dimming(self):
        """Without focus style, style_map contains no FOCUS entries."""
        style_map = parse_highlight_specs(["2:add"], total_lines=5)
        assert HighlightStyle.FOCUS not in style_map.values()


# ---------------------------------------------------------------------------
# Gutter indicator integration tests
# ---------------------------------------------------------------------------


class TestGutterIndicatorIntegration:
    """Integration tests for gutter indicators with highlight styles."""

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_gutter_with_add_style(self):
        """Render with add style and line numbers produces output."""
        config = RenderConfig(highlights=["1:add"], show_line_numbers=True)
        data = _render_code(SAMPLE_CODE, config)
        assert len(data) > 0

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_gutter_hidden_without_line_numbers(self):
        """Render with add style but no line numbers does not crash."""
        config = RenderConfig(highlights=["1:add"], show_line_numbers=False)
        data = _render_code(SAMPLE_CODE, config)
        assert len(data) > 0

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_gutter_with_all_styles(self):
        """Render with all 4 styles produces non-empty output."""
        config = RenderConfig(
            highlights=["1:add", "2:remove", "3:focus", "4:highlight"],
            show_line_numbers=True,
        )
        data = _render_code(SAMPLE_CODE, config)
        assert len(data) > 0
