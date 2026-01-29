"""Shared fixtures for codepicture tests."""

from pathlib import Path

import pytest

from codepicture.core.types import Color, TextStyle


@pytest.fixture
def sample_color() -> Color:
    """A standard test color (Catppuccin Blue)."""
    return Color(r=137, g=180, b=250, a=255)


@pytest.fixture
def sample_color_red() -> Color:
    """A red color for testing."""
    return Color(r=255, g=0, b=0, a=255)


@pytest.fixture
def sample_text_style(sample_color: Color) -> TextStyle:
    """A standard text style for testing."""
    return TextStyle(color=sample_color, bold=False, italic=False)


@pytest.fixture
def valid_config_toml(tmp_path: Path) -> Path:
    """Create a valid config.toml file and return its path."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('''
theme = "catppuccin-mocha"
font_size = 14
padding = 40
''')
    return config_file


@pytest.fixture
def invalid_config_toml(tmp_path: Path) -> Path:
    """Create an invalid config.toml file and return its path."""
    config_file = tmp_path / "invalid.toml"
    config_file.write_text("this is [ not valid toml")
    return config_file


@pytest.fixture
def config_with_overrides(tmp_path: Path) -> Path:
    """Create a config.toml with non-default values."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('''
theme = "dracula"
font_size = 16
padding = 60
show_line_numbers = false
''')
    return config_file


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def render_config():
    """Default render configuration for tests."""
    from codepicture.config import RenderConfig
    return RenderConfig()


@pytest.fixture
def pango_measurer():
    """Pango-based text measurer for layout tests."""
    from codepicture import PangoTextMeasurer
    from codepicture.fonts import register_bundled_fonts
    register_bundled_fonts()
    return PangoTextMeasurer()


@pytest.fixture
def layout_engine(pango_measurer, render_config):
    """Layout engine with default config for tests."""
    from codepicture import LayoutEngine
    return LayoutEngine(pango_measurer, render_config)


@pytest.fixture
def sample_tokens():
    """Sample tokenized lines for layout tests."""
    from codepicture.highlight import TokenInfo
    return [
        [TokenInfo("def ", "Token.Keyword", 0, 0), TokenInfo("foo():", "Token.Name.Function", 0, 4)],
        [TokenInfo("    ", "Token.Text", 1, 0), TokenInfo("pass", "Token.Keyword", 1, 4)],
    ]


@pytest.fixture
def minimal_render_config():
    """Minimal render config (no chrome, no shadow)."""
    from codepicture.config import RenderConfig
    return RenderConfig(
        window_controls=False,
        shadow=False,
        show_line_numbers=False,
    )


@pytest.fixture
def render_tokens():
    """Sample tokenized lines for render testing (uses real Pygments tokens)."""
    from codepicture.highlight import TokenInfo
    from pygments.token import Token
    return [
        [
            TokenInfo("def", Token.Keyword, 0, 0),
            TokenInfo(" ", Token.Text, 0, 3),
            TokenInfo("hello", Token.Name.Function, 0, 4),
            TokenInfo("():", Token.Punctuation, 0, 9),
        ],
        [
            TokenInfo("    ", Token.Text, 1, 0),
            TokenInfo("pass", Token.Keyword, 1, 4),
        ],
    ]


@pytest.fixture
def render_metrics(minimal_render_config, render_tokens):
    """Sample layout metrics for render testing."""
    from codepicture.layout import LayoutEngine, PangoTextMeasurer
    from codepicture.fonts import register_bundled_fonts
    register_bundled_fonts()
    measurer = PangoTextMeasurer()
    engine = LayoutEngine(measurer, minimal_render_config)
    return engine.calculate_metrics(render_tokens)
