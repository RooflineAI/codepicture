"""Tests for configuration loading and merging."""

from pathlib import Path

import pytest

from codepicture.config.loader import load_config
from codepicture.core.types import OutputFormat
from codepicture.errors import ConfigError


class TestLoadConfig:
    """Test load_config() function."""

    def test_load_defaults(self, tmp_path: Path):
        """load_config() with no files returns defaults."""
        # Use non-existent paths to ensure defaults
        config = load_config(
            global_path=tmp_path / "nonexistent.toml",
            local_path=tmp_path / "also_nonexistent.toml",
            use_defaults=False,
        )
        assert config.theme == "catppuccin-mocha"
        assert config.font_size == 14
        assert config.padding == 40

    def test_load_from_toml(self, valid_config_toml: Path):
        """load_config(local_path=valid_config_toml) loads values."""
        config = load_config(
            global_path=None,
            local_path=valid_config_toml,
            use_defaults=False,
        )
        assert config.theme == "catppuccin-mocha"
        assert config.font_size == 14
        assert config.padding == 40

    def test_invalid_toml_raises_config_error(self, invalid_config_toml: Path):
        """load_config(local_path=invalid_config_toml) raises ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            load_config(
                global_path=None,
                local_path=invalid_config_toml,
                use_defaults=False,
            )
        assert "Invalid TOML" in str(exc_info.value)

    def test_cli_overrides_file(self, config_with_overrides: Path):
        """cli_overrides override file values."""
        config = load_config(
            global_path=None,
            local_path=config_with_overrides,
            cli_overrides={"font_size": 20, "theme": "nord"},
            use_defaults=False,
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
            global_path=None,
            local_path=valid_config_toml,
            cli_overrides={"font_size": None, "theme": "dracula"},
            use_defaults=False,
        )
        # font_size not overridden (None filtered)
        assert config.font_size == 14
        # theme is overridden
        assert config.theme == "dracula"

    def test_file_not_found_uses_defaults(self, tmp_path: Path):
        """Non-existent paths are skipped, uses defaults."""
        nonexistent = tmp_path / "does_not_exist.toml"
        config = load_config(
            global_path=nonexistent,
            local_path=nonexistent,
            use_defaults=False,
        )
        # Should use RenderConfig defaults
        assert config.theme == "catppuccin-mocha"
        assert config.font_size == 14

    def test_validation_error_becomes_config_error(self, tmp_path: Path):
        """Invalid values raise ConfigError."""
        # Create config with invalid value
        bad_config = tmp_path / "bad.toml"
        bad_config.write_text('font_size = 100\n')  # > 72 max
        with pytest.raises(ConfigError) as exc_info:
            load_config(
                global_path=None,
                local_path=bad_config,
                use_defaults=False,
            )
        assert "Invalid configuration" in str(exc_info.value)
        assert "font_size" in str(exc_info.value)

    def test_global_and_local_merge(self, tmp_path: Path):
        """Local config overrides global config."""
        global_config = tmp_path / "global.toml"
        global_config.write_text('''
theme = "nord"
font_size = 12
padding = 20
''')
        local_config = tmp_path / "local.toml"
        local_config.write_text('''
font_size = 16
''')
        config = load_config(
            global_path=global_config,
            local_path=local_config,
            use_defaults=False,
        )
        # Local overrides global
        assert config.font_size == 16
        # Global value preserved
        assert config.theme == "nord"
        assert config.padding == 20

    def test_enum_conversion_from_toml(self, tmp_path: Path):
        """TOML string values convert to enums."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('''
output_format = "svg"
window_style = "linux"
''')
        config = load_config(
            global_path=None,
            local_path=config_file,
            use_defaults=False,
        )
        assert config.output_format == OutputFormat.SVG
        from codepicture.core.types import WindowStyle
        assert config.window_style == WindowStyle.LINUX

    def test_cli_overrides_only(self):
        """CLI overrides work without any config files."""
        config = load_config(
            global_path=None,
            local_path=None,
            cli_overrides={"font_size": 18, "padding": 30},
            use_defaults=False,
        )
        assert config.font_size == 18
        assert config.padding == 30
        # Defaults for unset values
        assert config.theme == "catppuccin-mocha"
