"""Tests for core data types."""

import pytest

from codepicture.core.types import (
    Color,
    Dimensions,
    OutputFormat,
    Position,
    Rect,
    TextStyle,
    WindowStyle,
)


class TestColor:
    """Test Color dataclass."""

    def test_from_hex_six_char(self):
        """#RRGGBB format parses correctly."""
        color = Color.from_hex("#89b4fa")
        assert color.r == 137
        assert color.g == 180
        assert color.b == 250
        assert color.a == 255  # Default alpha

    def test_from_hex_with_alpha(self):
        """#RRGGBBAA format parses alpha correctly."""
        color = Color.from_hex("#89b4fa80")
        assert color.r == 137
        assert color.g == 180
        assert color.b == 250
        assert color.a == 128

    def test_from_hex_short_format(self):
        """#RGB expands correctly to #RRGGBB."""
        color = Color.from_hex("#abc")
        assert color.r == 0xAA
        assert color.g == 0xBB
        assert color.b == 0xCC
        assert color.a == 255

    def test_from_hex_invalid_raises(self):
        """Invalid hex formats raise ValueError."""
        with pytest.raises(ValueError, match="Invalid hex color"):
            Color.from_hex("#GGG")

        with pytest.raises(ValueError, match="Invalid hex color"):
            Color.from_hex("#12")

        with pytest.raises(ValueError, match="Invalid hex color"):
            Color.from_hex("#12345")

        with pytest.raises(ValueError, match="Invalid hex color"):
            Color.from_hex("not-a-color")

    def test_immutability(self):
        """Frozen dataclass rejects mutation."""
        color = Color(r=100, g=150, b=200, a=255)
        with pytest.raises(AttributeError):
            color.r = 50

    def test_to_hex_roundtrip(self):
        """to_hex -> from_hex preserves values."""
        original = Color(r=137, g=180, b=250, a=200)
        hex_str = original.to_hex()
        restored = Color.from_hex(hex_str)
        assert restored == original

    def test_equality(self):
        """Same values are equal."""
        color1 = Color(r=100, g=150, b=200, a=255)
        color2 = Color(r=100, g=150, b=200, a=255)
        assert color1 == color2

    def test_inequality(self):
        """Different values are not equal."""
        color1 = Color(r=100, g=150, b=200, a=255)
        color2 = Color(r=100, g=150, b=200, a=128)
        assert color1 != color2

    def test_default_alpha(self):
        """Default alpha is 255."""
        color = Color(r=100, g=150, b=200)
        assert color.a == 255

    def test_to_hex_output_format(self):
        """to_hex returns lowercase #RRGGBBAA format."""
        color = Color(r=255, g=0, b=128, a=255)
        assert color.to_hex() == "#ff0080ff"

    def test_from_hex_without_hash(self):
        """from_hex strips leading hash if present."""
        # The implementation uses lstrip("#") so it handles with or without
        color1 = Color.from_hex("#ff0000")
        color2 = Color.from_hex("ff0000")
        assert color1 == color2


class TestDimensions:
    """Test Dimensions NamedTuple."""

    def test_creation(self):
        """Width and height are accessible."""
        dims = Dimensions(width=800, height=600)
        assert dims.width == 800
        assert dims.height == 600

    def test_is_named_tuple(self):
        """Dimensions is a NamedTuple."""
        from typing import NamedTuple

        dims = Dimensions(width=100, height=100)
        # NamedTuples are tuples
        assert isinstance(dims, tuple)
        # Can access by index
        assert dims[0] == 100
        assert dims[1] == 100

    def test_unpacking(self):
        """Dimensions can be unpacked."""
        dims = Dimensions(width=1920, height=1080)
        w, h = dims
        assert w == 1920
        assert h == 1080


class TestPosition:
    """Test Position NamedTuple."""

    def test_creation(self):
        """X and Y are accessible."""
        pos = Position(x=10.5, y=20.5)
        assert pos.x == 10.5
        assert pos.y == 20.5

    def test_is_named_tuple(self):
        """Position is a NamedTuple."""
        pos = Position(x=0, y=0)
        assert isinstance(pos, tuple)
        assert pos[0] == 0
        assert pos[1] == 0


class TestRect:
    """Test Rect NamedTuple."""

    def test_creation(self):
        """x, y, width, height are accessible."""
        rect = Rect(x=10.0, y=20.0, width=100.0, height=50.0)
        assert rect.x == 10.0
        assert rect.y == 20.0
        assert rect.width == 100.0
        assert rect.height == 50.0

    def test_is_named_tuple(self):
        """Rect is a NamedTuple."""
        rect = Rect(x=0, y=0, width=10, height=10)
        assert isinstance(rect, tuple)
        assert len(rect) == 4

    def test_unpacking(self):
        """Rect can be unpacked."""
        rect = Rect(x=1, y=2, width=3, height=4)
        x, y, w, h = rect
        assert (x, y, w, h) == (1, 2, 3, 4)


class TestTextStyle:
    """Test TextStyle dataclass."""

    def test_defaults(self, sample_color):
        """Bold, italic, underline default to False."""
        style = TextStyle(color=sample_color)
        assert style.bold is False
        assert style.italic is False
        assert style.underline is False

    def test_immutability(self, sample_color):
        """Frozen dataclass rejects mutation."""
        style = TextStyle(color=sample_color)
        with pytest.raises(AttributeError):
            style.bold = True

    def test_with_all_flags(self, sample_color):
        """All style flags can be set."""
        style = TextStyle(color=sample_color, bold=True, italic=True, underline=True)
        assert style.bold is True
        assert style.italic is True
        assert style.underline is True

    def test_equality(self, sample_color):
        """Same values are equal."""
        style1 = TextStyle(color=sample_color, bold=True)
        style2 = TextStyle(color=sample_color, bold=True)
        assert style1 == style2


class TestOutputFormat:
    """Test OutputFormat enum."""

    def test_values(self):
        """PNG, SVG, PDF have correct string values."""
        assert OutputFormat.PNG.value == "png"
        assert OutputFormat.SVG.value == "svg"
        assert OutputFormat.PDF.value == "pdf"

    def test_from_string(self):
        """Can create from string value."""
        assert OutputFormat("png") == OutputFormat.PNG
        assert OutputFormat("svg") == OutputFormat.SVG
        assert OutputFormat("pdf") == OutputFormat.PDF

    def test_all_members(self):
        """All expected members exist."""
        members = list(OutputFormat)
        assert len(members) == 3
        assert OutputFormat.PNG in members
        assert OutputFormat.SVG in members
        assert OutputFormat.PDF in members


class TestWindowStyle:
    """Test WindowStyle enum."""

    def test_values(self):
        """MACOS, WINDOWS, LINUX, NONE have correct string values."""
        assert WindowStyle.MACOS.value == "macos"
        assert WindowStyle.WINDOWS.value == "windows"
        assert WindowStyle.LINUX.value == "linux"
        assert WindowStyle.NONE.value == "none"

    def test_from_string(self):
        """Can create from string value."""
        assert WindowStyle("macos") == WindowStyle.MACOS
        assert WindowStyle("windows") == WindowStyle.WINDOWS
        assert WindowStyle("linux") == WindowStyle.LINUX
        assert WindowStyle("none") == WindowStyle.NONE

    def test_all_members(self):
        """All expected members exist."""
        members = list(WindowStyle)
        assert len(members) == 4
