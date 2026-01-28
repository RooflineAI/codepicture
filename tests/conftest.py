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
