"""Tests for codepicture error hierarchy."""

import pytest

from codepicture.errors import (
    CodepictureError,
    ConfigError,
    HighlightError,
    InputError,
    RenderError,
    RenderTimeoutError,
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
        assert issubclass(RenderTimeoutError, CodepictureError)
        assert issubclass(InputError, CodepictureError)


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


class TestRenderTimeoutError:
    """Test RenderTimeoutError behavior."""

    def test_render_timeout_error_message_preserved(self):
        """RenderTimeoutError preserves message."""
        error = RenderTimeoutError("timed out")
        assert str(error) == "timed out"

    def test_render_timeout_error_attributes(self):
        """RenderTimeoutError stores timeout and file_info attributes."""
        error = RenderTimeoutError("timed out", timeout=30.0, file_info="test.py")
        assert error.timeout == 30.0
        assert error.file_info == "test.py"

    def test_render_timeout_error_default_attributes(self):
        """RenderTimeoutError defaults timeout and file_info to None."""
        error = RenderTimeoutError("timed out")
        assert error.timeout is None
        assert error.file_info is None

    def test_render_timeout_error_is_render_error(self):
        """RenderTimeoutError is a RenderError subclass."""
        error = RenderTimeoutError("timed out")
        assert isinstance(error, RenderError)

    def test_render_timeout_error_is_codepicture_error(self):
        """RenderTimeoutError is a CodepictureError subclass."""
        error = RenderTimeoutError("timed out")
        assert isinstance(error, CodepictureError)

    def test_render_timeout_error_caught_as_render_error(self):
        """RenderTimeoutError can be caught as RenderError."""
        with pytest.raises(RenderError):
            raise RenderTimeoutError("timeout")

    def test_render_timeout_error_caught_as_base(self):
        """RenderTimeoutError can be caught as CodepictureError."""
        with pytest.raises(CodepictureError):
            raise RenderTimeoutError("timeout")


class TestInputError:
    """Test InputError behavior."""

    def test_input_error_message_preserved(self):
        """InputError preserves message."""
        error = InputError("file not found")
        assert str(error) == "file not found"

    def test_input_error_input_path_attribute(self):
        """InputError stores input_path attribute."""
        error = InputError("not found", input_path="/tmp/missing.py")
        assert error.input_path == "/tmp/missing.py"

    def test_input_error_default_input_path_none(self):
        """InputError defaults input_path to None."""
        error = InputError("some error")
        assert error.input_path is None

    def test_input_error_caught_as_base(self):
        """InputError can be caught as CodepictureError."""
        with pytest.raises(CodepictureError):
            raise InputError("input issue")
