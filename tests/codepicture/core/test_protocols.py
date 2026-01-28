"""Tests for protocol compliance with mock implementations.

Tests verify that mock classes can satisfy protocols via structural subtyping.
"""

from pathlib import Path
from typing import Any

from codepicture.core.protocols import Canvas, Highlighter, TextMeasurer, Theme
from codepicture.core.types import Color, TextStyle


class MockTextMeasurer:
    """Mock TextMeasurer for testing protocol compliance."""

    def measure_text(
        self, text: str, font_family: str, font_size: int
    ) -> tuple[float, float]:
        """Return fixed dimensions for testing."""
        return (len(text) * font_size * 0.6, font_size * 1.2)


class MockCanvas:
    """Mock Canvas for testing protocol compliance."""

    def __init__(self):
        self._width = 800
        self._height = 600

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def draw_rectangle(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        color: Color,
        corner_radius: float = 0,
    ) -> None:
        pass

    def draw_circle(self, x: float, y: float, radius: float, color: Color) -> None:
        pass

    def draw_text(
        self,
        x: float,
        y: float,
        text: str,
        font_family: str,
        font_size: int,
        color: Color,
    ) -> float:
        return len(text) * font_size * 0.6

    def measure_text(
        self, text: str, font_family: str, font_size: int
    ) -> tuple[float, float]:
        return (len(text) * font_size * 0.6, font_size * 1.2)

    def push_clip(self, x: float, y: float, width: float, height: float) -> None:
        pass

    def pop_clip(self) -> None:
        pass

    def apply_shadow(
        self,
        blur_radius: float,
        offset_x: float,
        offset_y: float,
        color: Color,
    ) -> None:
        pass

    def save(self) -> bytes:
        return b"mock-image-data"

    def save_to_file(self, path: Path) -> None:
        pass


class MockHighlighter:
    """Mock Highlighter for testing protocol compliance."""

    def highlight(self, code: str, language: str) -> list[list[tuple[str, Any]]]:
        """Return simple tokenization for testing."""
        lines = code.split("\n")
        return [[(line, "text")] for line in lines]

    def detect_language(self, code: str, filename: str | None = None) -> str:
        """Return 'text' as default language."""
        if filename and filename.endswith(".py"):
            return "python"
        return "text"

    def list_languages(self) -> list[str]:
        """Return list of supported languages."""
        return ["python", "javascript", "rust", "text"]


class MockTheme:
    """Mock Theme for testing protocol compliance."""

    def __init__(self):
        self._bg = Color(r=30, g=30, b=46, a=255)
        self._fg = Color(r=205, g=214, b=244, a=255)
        self._ln_fg = Color(r=108, g=112, b=134, a=255)
        self._ln_bg = Color(r=30, g=30, b=46, a=255)

    @property
    def name(self) -> str:
        return "mock-theme"

    @property
    def background(self) -> Color:
        return self._bg

    @property
    def foreground(self) -> Color:
        return self._fg

    @property
    def line_number_fg(self) -> Color:
        return self._ln_fg

    @property
    def line_number_bg(self) -> Color:
        return self._ln_bg

    def get_style(self, token_type: Any) -> TextStyle:
        """Return default style for any token."""
        return TextStyle(color=self._fg)


class TestTextMeasurerProtocol:
    """Test TextMeasurer protocol compliance."""

    def test_mock_implements_protocol(self):
        """MockTextMeasurer satisfies TextMeasurer protocol."""
        measurer: TextMeasurer = MockTextMeasurer()
        width, height = measurer.measure_text("hello", "JetBrains Mono", 14)
        assert isinstance(width, float)
        assert isinstance(height, float)

    def test_type_annotation_works(self):
        """Protocol-typed variable accepts mock implementation."""
        # This should not raise type errors at runtime
        measurer: TextMeasurer = MockTextMeasurer()
        assert hasattr(measurer, "measure_text")


class TestCanvasProtocol:
    """Test Canvas protocol compliance."""

    def test_mock_implements_protocol(self):
        """MockCanvas satisfies Canvas protocol."""
        canvas: Canvas = MockCanvas()
        assert canvas.width == 800
        assert canvas.height == 600

    def test_draw_methods_callable(self):
        """Canvas draw methods are callable."""
        canvas: Canvas = MockCanvas()
        color = Color(r=255, g=0, b=0, a=255)

        # Should not raise
        canvas.draw_rectangle(0, 0, 100, 100, color)
        canvas.draw_circle(50, 50, 25, color)
        width = canvas.draw_text(0, 0, "test", "Arial", 14, color)
        assert isinstance(width, float)

    def test_clip_methods_callable(self):
        """Canvas clip methods are callable."""
        canvas: Canvas = MockCanvas()
        canvas.push_clip(0, 0, 100, 100)
        canvas.pop_clip()

    def test_save_methods_callable(self):
        """Canvas save methods are callable."""
        canvas: Canvas = MockCanvas()
        data = canvas.save()
        assert isinstance(data, bytes)
        canvas.save_to_file(Path("/tmp/test.png"))


class TestHighlighterProtocol:
    """Test Highlighter protocol compliance."""

    def test_mock_implements_protocol(self):
        """MockHighlighter satisfies Highlighter protocol."""
        highlighter: Highlighter = MockHighlighter()

        # Test highlight
        result = highlighter.highlight("print('hello')", "python")
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], list)
        assert isinstance(result[0][0], tuple)

    def test_detect_language_works(self):
        """Highlighter can detect language."""
        highlighter: Highlighter = MockHighlighter()
        lang = highlighter.detect_language("def foo():", filename="test.py")
        assert lang == "python"

    def test_list_languages_works(self):
        """Highlighter returns list of languages."""
        highlighter: Highlighter = MockHighlighter()
        languages = highlighter.list_languages()
        assert isinstance(languages, list)
        assert "python" in languages


class TestThemeProtocol:
    """Test Theme protocol compliance."""

    def test_mock_implements_protocol(self):
        """MockTheme satisfies Theme protocol."""
        theme: Theme = MockTheme()
        assert theme.name == "mock-theme"
        assert isinstance(theme.background, Color)
        assert isinstance(theme.foreground, Color)
        assert isinstance(theme.line_number_fg, Color)
        assert isinstance(theme.line_number_bg, Color)

    def test_get_style_returns_text_style(self):
        """Theme.get_style returns TextStyle."""
        theme: Theme = MockTheme()
        style = theme.get_style("keyword")
        assert isinstance(style, TextStyle)
        assert isinstance(style.color, Color)
