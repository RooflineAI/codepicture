"""Tests for codepicture error hierarchy."""

import pytest

from codepicture.errors import (
    CodepictureError,
    ConfigError,
    HighlightError,
    RenderError,
    ThemeError,
)


class TestCodepictureError:
    """Test base exception behavior."""

    def test_base_error_can_be_raised(self):
        """Base error can be raised with a message."""
        with pytest.raises(CodepictureError, match="test message"):
            raise CodepictureError("test message")

    def test_all_errors_inherit_from_base(self):
        """All custom errors inherit from CodepictureError."""
        assert issubclass(ConfigError, CodepictureError)
        assert issubclass(ThemeError, CodepictureError)
        assert issubclass(RenderError, CodepictureError)
        assert issubclass(HighlightError, CodepictureError)


class TestConfigError:
    """Test ConfigError behavior."""

    def test_config_error_message_preserved(self):
        """ConfigError preserves message."""
        error = ConfigError("invalid config")
        assert str(error) == "invalid config"

    def test_config_error_field_attribute(self):
        """ConfigError stores optional field attribute."""
        error = ConfigError("bad value", field="font_size")
        assert error.field == "font_size"
        assert str(error) == "bad value"

    def test_config_error_field_default_none(self):
        """ConfigError field defaults to None."""
        error = ConfigError("message")
        assert error.field is None

    def test_config_error_caught_as_base(self):
        """ConfigError can be caught as CodepictureError."""
        with pytest.raises(CodepictureError):
            raise ConfigError("config issue")


class TestThemeError:
    """Test ThemeError behavior."""

    def test_theme_error_message_preserved(self):
        """ThemeError preserves message."""
        error = ThemeError("theme not found")
        assert str(error) == "theme not found"

    def test_theme_error_caught_as_base(self):
        """ThemeError can be caught as CodepictureError."""
        with pytest.raises(CodepictureError):
            raise ThemeError("theme issue")


class TestRenderError:
    """Test RenderError behavior."""

    def test_render_error_message_preserved(self):
        """RenderError preserves message."""
        error = RenderError("rendering failed")
        assert str(error) == "rendering failed"

    def test_render_error_caught_as_base(self):
        """RenderError can be caught as CodepictureError."""
        with pytest.raises(CodepictureError):
            raise RenderError("render issue")


class TestHighlightError:
    """Test HighlightError behavior."""

    def test_highlight_error_message_preserved(self):
        """HighlightError preserves message."""
        error = HighlightError("unknown language")
        assert str(error) == "unknown language"

    def test_highlight_error_caught_as_base(self):
        """HighlightError can be caught as CodepictureError."""
        with pytest.raises(CodepictureError):
            raise HighlightError("highlight issue")
