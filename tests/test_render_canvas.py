"""Tests for CairoCanvas."""

import pytest
from codepicture.render import CairoCanvas
from codepicture.core.types import Color, OutputFormat


class TestCairoCanvasCreation:
    """Test canvas creation for different formats."""

    def test_create_png_surface(self):
        """PNG surface is created at 2x scale."""
        canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=2.0)
        # Logical dimensions should be 100x100
        assert canvas.width == 100
        assert canvas.height == 100
        # Internal surface is 200x200 (2x)

    def test_create_svg_surface(self):
        """SVG surface is created at logical dimensions."""
        canvas = CairoCanvas.create(100, 100, OutputFormat.SVG)
        assert canvas.width == 100
        assert canvas.height == 100

    def test_create_pdf_surface(self):
        """PDF surface is created at logical dimensions."""
        canvas = CairoCanvas.create(100, 100, OutputFormat.PDF)
        assert canvas.width == 100
        assert canvas.height == 100


class TestCairoCanvasDrawing:
    """Test canvas drawing operations."""

    @pytest.fixture
    def canvas(self):
        return CairoCanvas.create(200, 200, OutputFormat.PNG, scale=1.0)

    def test_draw_rectangle(self, canvas):
        """Rectangle draws without error."""
        canvas.draw_rectangle(10, 10, 50, 50, Color(255, 0, 0))
        # No assertion needed - just verify no exception

    def test_draw_rectangle_with_corner_radius(self, canvas):
        """Rounded rectangle draws without error."""
        canvas.draw_rectangle(10, 10, 50, 50, Color(0, 255, 0), corner_radius=5)

    def test_draw_circle(self, canvas):
        """Circle draws without error."""
        canvas.draw_circle(100, 100, 25, Color(0, 0, 255))

    def test_draw_text_returns_advance(self, canvas):
        """Text drawing returns positive advance width."""
        advance = canvas.draw_text(
            10, 50, "Hello", "JetBrains Mono", 14, Color(255, 255, 255)
        )
        assert advance > 0

    def test_measure_text(self, canvas):
        """Text measurement returns positive dimensions."""
        width, height = canvas.measure_text("Test", "JetBrains Mono", 14)
        assert width > 0
        assert height > 0


class TestCairoCanvasSave:
    """Test canvas save operations."""

    def test_save_png_bytes(self):
        """PNG save returns valid PNG bytes."""
        canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=1.0)
        canvas.draw_rectangle(0, 0, 100, 100, Color(100, 100, 100))
        data = canvas.save()
        assert data[:8] == b'\x89PNG\r\n\x1a\n'  # PNG magic bytes

    def test_save_svg_bytes(self):
        """SVG save returns valid SVG content."""
        canvas = CairoCanvas.create(100, 100, OutputFormat.SVG)
        canvas.draw_rectangle(0, 0, 100, 100, Color(100, 100, 100))
        data = canvas.save()
        assert b'<svg' in data or b'<?xml' in data

    def test_save_pdf_bytes(self):
        """PDF save returns valid PDF content."""
        canvas = CairoCanvas.create(100, 100, OutputFormat.PDF)
        canvas.draw_rectangle(0, 0, 100, 100, Color(100, 100, 100))
        data = canvas.save()
        assert data[:4] == b'%PDF'  # PDF magic bytes


class TestCairoCanvasClipping:
    """Test canvas clipping operations."""

    def test_push_pop_clip(self):
        """Clipping stack works correctly."""
        canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=1.0)
        canvas.push_clip(10, 10, 50, 50)
        canvas.draw_rectangle(0, 0, 100, 100, Color(255, 0, 0))  # Should be clipped
        canvas.pop_clip()
        # No assertion - just verify stack operations work
