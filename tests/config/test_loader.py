"""Tests for configuration loading.

Tests verify:
- First-found config wins (no merge between files)
- CLI overrides applied on top
- Explicit config_path skips default search
"""

import os
from pathlib import Path

import pytest

from codepicture.config.loader import (
    DEFAULT_GLOBAL_CONFIG_PATH,
    DEFAULT_LOCAL_CONFIG_PATH,
    load_config,
)
from codepicture.core.types import OutputFormat
from codepicture.errors import ConfigError


class TestLoadConfig:
    """Test load_config() function."""

    def test_load_defaults_no_config_files(self, tmp_path: Path, monkeypatch):
        """load_config() with no config files returns defaults."""
        # Change to tmp_path so no local config exists
        monkeypatch.chdir(tmp_path)
        # Also ensure global config doesn't exist by using a fake home
        monkeypatch.setenv("HOME", str(tmp_path))

        config = load_config()
        assert config.theme == "catppuccin-mocha"
        assert config.font_size == 14
        assert config.padding == 40

    def test_load_from_explicit_config_path(self, valid_config_toml: Path):
        """load_config(config_path=...) loads from explicit path."""
        config = load_config(config_path=valid_config_toml)
        assert config.theme == "catppuccin-mocha"
        assert config.font_size == 14
        assert config.padding == 40

    def test_invalid_toml_raises_config_error(self, invalid_config_toml: Path):
        """Invalid TOML raises ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            load_config(config_path=invalid_config_toml)
        assert "Invalid TOML" in str(exc_info.value)

    def test_cli_overrides_file(self, config_with_overrides: Path):
        """cli_overrides override file values."""
        config = load_config(
            config_path=config_with_overrides,
            cli_overrides={"font_size": 20, "theme": "nord"},
        )
        # CLI override values
        assert config.font_size == 20
        assert config.theme == "nord"
        # File value preserved where no override
        assert config.padding == 60
        assert config.show_line_numbers is False

    def test_cli_overrides_filter_none(self, valid_config_toml: Path):
        """None values in cli_overrides are ignored."""
        config = load_config(
            config_path=valid_config_toml,
            cli_overrides={"font_size": None, "theme": "dracula"},
        )
        # font_size not overridden (None filtered)
        assert config.font_size == 14
        # theme is overridden
        assert config.theme == "dracula"

    def test_explicit_path_not_found_uses_defaults(self, tmp_path: Path):
        """Non-existent explicit config_path uses defaults."""
        nonexistent = tmp_path / "does_not_exist.toml"
        config = load_config(config_path=nonexistent)
        # Should use RenderConfig defaults
        assert config.theme == "catppuccin-mocha"
        assert config.font_size == 14

    def test_validation_error_becomes_config_error(self, tmp_path: Path):
        """Invalid values raise ConfigError."""
        # Create config with invalid value
        bad_config = tmp_path / "bad.toml"
        bad_config.write_text('font_size = 100\n')  # > 72 max
        with pytest.raises(ConfigError) as exc_info:
            load_config(config_path=bad_config)
        assert "Invalid configuration" in str(exc_info.value)
        assert "font_size" in str(exc_info.value)

    def test_local_config_replaces_global_no_merge(self, tmp_path: Path, monkeypatch):
        """Local config replaces global entirely (no merge)."""
        # Set up global config with multiple values
        global_dir = tmp_path / ".config" / "codepicture"
        global_dir.mkdir(parents=True)
        global_config = global_dir / "config.toml"
        global_config.write_text('''
theme = "nord"
font_size = 12
padding = 20
''')
        # Set up local config with only one value
        local_config = tmp_path / "codepicture.toml"
        local_config.write_text('''
font_size = 16
''')
        # Change to tmp_path and set HOME
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))

        # Reload module to pick up new HOME for DEFAULT_GLOBAL_CONFIG_PATH
        import importlib
        import codepicture.config.loader as loader_module
        original_global = loader_module.DEFAULT_GLOBAL_CONFIG_PATH
        loader_module.DEFAULT_GLOBAL_CONFIG_PATH = global_config

        try:
            config = load_config()
            # Local has font_size=16, rest should be DEFAULTS (not global!)
            assert config.font_size == 16
            # These are defaults, NOT from global config (no merge)
            assert config.theme == "catppuccin-mocha"  # default, not "nord"
            assert config.padding == 40  # default, not 20
        finally:
            loader_module.DEFAULT_GLOBAL_CONFIG_PATH = original_global

    def test_global_config_used_when_no_local(self, tmp_path: Path, monkeypatch):
        """Global config is used when local doesn't exist."""
        # Set up global config
        global_dir = tmp_path / ".config" / "codepicture"
        global_dir.mkdir(parents=True)
        global_config = global_dir / "config.toml"
        global_config.write_text('''
theme = "nord"
font_size = 12
''')
        # Change to tmp_path (no local config)
        monkeypatch.chdir(tmp_path)

        import codepicture.config.loader as loader_module
        original_global = loader_module.DEFAULT_GLOBAL_CONFIG_PATH
        loader_module.DEFAULT_GLOBAL_CONFIG_PATH = global_config

        try:
            config = load_config()
            # Global values should be used
            assert config.theme == "nord"
            assert config.font_size == 12
        finally:
            loader_module.DEFAULT_GLOBAL_CONFIG_PATH = original_global

    def test_enum_conversion_from_toml(self, tmp_path: Path):
        """TOML string values convert to enums."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('''
output_format = "svg"
window_style = "linux"
''')
        config = load_config(config_path=config_file)
        assert config.output_format == OutputFormat.SVG
        from codepicture.core.types import WindowStyle
        assert config.window_style == WindowStyle.LINUX

    def test_cli_overrides_only(self, tmp_path: Path, monkeypatch):
        """CLI overrides work without any config files."""
        # Ensure no config files exist
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))

        config = load_config(cli_overrides={"font_size": 18, "padding": 30})
        assert config.font_size == 18
        assert config.padding == 30
        # Defaults for unset values
        assert config.theme == "catppuccin-mocha"

    def test_default_local_config_path_is_codepicture_toml(self):
        """DEFAULT_LOCAL_CONFIG_PATH is codepicture.toml (not .codepicture.toml)."""
        assert DEFAULT_LOCAL_CONFIG_PATH == Path("codepicture.toml")
        assert not str(DEFAULT_LOCAL_CONFIG_PATH).startswith(".")
