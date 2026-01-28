"""Tests for RenderConfig schema validation."""

import pytest
from pydantic import ValidationError

from codepicture.config.schema import RenderConfig
from codepicture.core.types import OutputFormat, WindowStyle


class TestRenderConfig:
    """Test RenderConfig validation."""

    def test_defaults(self):
        """Check default values."""
        config = RenderConfig()
        assert config.theme == "catppuccin-mocha"
        assert config.font_family == "JetBrains Mono"
        assert config.font_size == 14
        assert config.tab_width == 4
        assert config.line_height == 1.4
        assert config.output_format == OutputFormat.PNG
        assert config.padding == 40
        assert config.corner_radius == 12
        assert config.show_line_numbers is True
        assert config.line_number_offset == 1
        assert config.window_controls is True
        assert config.window_style == WindowStyle.MACOS
        assert config.window_title is None
        assert config.shadow is True
        assert config.shadow_blur == 50
        assert config.shadow_offset_x == 0
        assert config.shadow_offset_y == 0
        assert config.background_color is None

    def test_font_size_range_min(self):
        """font_size < 6 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RenderConfig(font_size=5)
        errors = exc_info.value.errors()
        assert any("font_size" in str(e["loc"]) for e in errors)

    def test_font_size_range_max(self):
        """font_size > 72 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RenderConfig(font_size=73)
        errors = exc_info.value.errors()
        assert any("font_size" in str(e["loc"]) for e in errors)

    def test_font_size_range_valid(self):
        """font_size 6-72 is valid."""
        config_min = RenderConfig(font_size=6)
        assert config_min.font_size == 6
        config_max = RenderConfig(font_size=72)
        assert config_max.font_size == 72

    def test_padding_range_invalid(self):
        """Negative or >500 padding raises ValidationError."""
        with pytest.raises(ValidationError):
            RenderConfig(padding=-1)
        with pytest.raises(ValidationError):
            RenderConfig(padding=501)

    def test_padding_range_valid(self):
        """Padding 0-500 is valid."""
        config_min = RenderConfig(padding=0)
        assert config_min.padding == 0
        config_max = RenderConfig(padding=500)
        assert config_max.padding == 500

    def test_extra_fields_rejected(self):
        """Unknown fields raise ValidationError with extra_forbidden."""
        with pytest.raises(ValidationError) as exc_info:
            RenderConfig(unknown_field="value")
        errors = exc_info.value.errors()
        assert any("extra" in e["type"] for e in errors)

    def test_output_format_string_conversion(self):
        """"svg" converts to OutputFormat.SVG."""
        config = RenderConfig(output_format="svg")
        assert config.output_format == OutputFormat.SVG
        config_png = RenderConfig(output_format="png")
        assert config_png.output_format == OutputFormat.PNG
        config_pdf = RenderConfig(output_format="pdf")
        assert config_pdf.output_format == OutputFormat.PDF

    def test_output_format_case_insensitive(self):
        """Output format conversion is case insensitive."""
        config = RenderConfig(output_format="SVG")
        assert config.output_format == OutputFormat.SVG
        config_mixed = RenderConfig(output_format="Png")
        assert config_mixed.output_format == OutputFormat.PNG

    def test_output_format_invalid(self):
        """Invalid format string raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RenderConfig(output_format="gif")
        errors = exc_info.value.errors()
        assert any("output_format" in str(e["loc"]) for e in errors)

    def test_output_format_enum_direct(self):
        """OutputFormat enum can be passed directly."""
        config = RenderConfig(output_format=OutputFormat.PDF)
        assert config.output_format == OutputFormat.PDF

    def test_window_style_string_conversion(self):
        """"macos" converts to WindowStyle.MACOS."""
        config = RenderConfig(window_style="macos")
        assert config.window_style == WindowStyle.MACOS
        config_win = RenderConfig(window_style="windows")
        assert config_win.window_style == WindowStyle.WINDOWS
        config_linux = RenderConfig(window_style="linux")
        assert config_linux.window_style == WindowStyle.LINUX
        config_none = RenderConfig(window_style="none")
        assert config_none.window_style == WindowStyle.NONE

    def test_window_style_invalid(self):
        """Invalid window style raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RenderConfig(window_style="gnome")
        errors = exc_info.value.errors()
        assert any("window_style" in str(e["loc"]) for e in errors)

    def test_background_color_valid_formats(self):
        """#RGB, #RRGGBB, #RRGGBBAA all accepted."""
        config_rgb = RenderConfig(background_color="#abc")
        assert config_rgb.background_color == "#abc"
        config_rrggbb = RenderConfig(background_color="#aabbcc")
        assert config_rrggbb.background_color == "#aabbcc"
        config_rgba = RenderConfig(background_color="#aabbccdd")
        assert config_rgba.background_color == "#aabbccdd"

    def test_background_color_case_insensitive(self):
        """Hex colors are case insensitive."""
        config = RenderConfig(background_color="#AABBCC")
        assert config.background_color == "#AABBCC"
        config_lower = RenderConfig(background_color="#aabbcc")
        assert config_lower.background_color == "#aabbcc"

    def test_background_color_invalid(self):
        """"red" or "#GGG" raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RenderConfig(background_color="red")
        errors = exc_info.value.errors()
        assert any("background_color" in str(e["loc"]) for e in errors)

        with pytest.raises(ValidationError):
            RenderConfig(background_color="#GGG")

        with pytest.raises(ValidationError):
            RenderConfig(background_color="#12")

        with pytest.raises(ValidationError):
            RenderConfig(background_color="#12345")

    def test_background_color_none(self):
        """None is accepted for background_color."""
        config = RenderConfig(background_color=None)
        assert config.background_color is None

    def test_tab_width_range(self):
        """tab_width must be 1-8."""
        with pytest.raises(ValidationError):
            RenderConfig(tab_width=0)
        with pytest.raises(ValidationError):
            RenderConfig(tab_width=9)
        config_min = RenderConfig(tab_width=1)
        assert config_min.tab_width == 1
        config_max = RenderConfig(tab_width=8)
        assert config_max.tab_width == 8

    def test_line_height_range(self):
        """line_height must be 1.0-3.0."""
        with pytest.raises(ValidationError):
            RenderConfig(line_height=0.9)
        with pytest.raises(ValidationError):
            RenderConfig(line_height=3.1)
        config_min = RenderConfig(line_height=1.0)
        assert config_min.line_height == 1.0
        config_max = RenderConfig(line_height=3.0)
        assert config_max.line_height == 3.0

    def test_corner_radius_range(self):
        """corner_radius must be 0-50."""
        with pytest.raises(ValidationError):
            RenderConfig(corner_radius=-1)
        with pytest.raises(ValidationError):
            RenderConfig(corner_radius=51)
        config = RenderConfig(corner_radius=25)
        assert config.corner_radius == 25

    def test_shadow_blur_range(self):
        """shadow_blur must be 0-200."""
        with pytest.raises(ValidationError):
            RenderConfig(shadow_blur=-1)
        with pytest.raises(ValidationError):
            RenderConfig(shadow_blur=201)

    def test_shadow_offset_range(self):
        """shadow offsets must be -100 to 100."""
        with pytest.raises(ValidationError):
            RenderConfig(shadow_offset_x=-101)
        with pytest.raises(ValidationError):
            RenderConfig(shadow_offset_y=101)
