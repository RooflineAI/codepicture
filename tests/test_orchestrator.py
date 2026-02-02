"""Tests for codepicture pipeline orchestrator.

Tests the timeout wrapper (generate_image_with_timeout) and atomic file writes
(_write_output_atomic) introduced in Phase 9.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from codepicture.errors import RenderError, RenderTimeoutError


class TestGenerateImageWithTimeout:
    """Tests for generate_image_with_timeout wrapper."""

    @patch("codepicture.cli.orchestrator.generate_image")
    def test_timeout_none_calls_directly(self, mock_generate):
        """When timeout is None, generate_image is called directly (no executor)."""
        from codepicture.cli.orchestrator import generate_image_with_timeout

        mock_generate.return_value = None
        config = MagicMock()

        generate_image_with_timeout(
            code="print('hi')",
            output_path=Path("/tmp/out.png"),
            config=config,
            language="python",
            filename="test.py",
            timeout=None,
        )

        mock_generate.assert_called_once_with(
            "print('hi')", Path("/tmp/out.png"), config, "python", "test.py"
        )

    @pytest.mark.timeout(10)
    @patch("codepicture.cli.orchestrator.generate_image")
    def test_timeout_raises_render_timeout_error(self, mock_generate):
        """When rendering exceeds timeout, RenderTimeoutError is raised."""
        from codepicture.cli.orchestrator import generate_image_with_timeout

        def slow_render(*args, **kwargs):
            time.sleep(5)

        mock_generate.side_effect = slow_render
        config = MagicMock()

        with pytest.raises(RenderTimeoutError) as exc_info:
            generate_image_with_timeout(
                code="print('hi')",
                output_path=Path("/tmp/out.png"),
                config=config,
                language="python",
                filename="test.py",
                timeout=0.1,
            )

        assert exc_info.value.timeout == 0.1
        assert exc_info.value.file_info == "test.py"

    @pytest.mark.timeout(10)
    @patch("codepicture.cli.orchestrator.generate_image")
    def test_success_returns_normally(self, mock_generate):
        """When rendering succeeds within timeout, no exception is raised."""
        from codepicture.cli.orchestrator import generate_image_with_timeout

        mock_generate.return_value = None
        config = MagicMock()

        # Should not raise
        generate_image_with_timeout(
            code="print('hi')",
            output_path=Path("/tmp/out.png"),
            config=config,
            language="python",
            filename="test.py",
            timeout=5.0,
        )

        mock_generate.assert_called_once()

    @pytest.mark.timeout(10)
    @patch("codepicture.cli.orchestrator.generate_image")
    def test_pipeline_error_propagates(self, mock_generate):
        """When generate_image raises RenderError, it propagates unwrapped."""
        from codepicture.cli.orchestrator import generate_image_with_timeout

        mock_generate.side_effect = RenderError("rendering failed")
        config = MagicMock()

        with pytest.raises(RenderError, match="rendering failed"):
            generate_image_with_timeout(
                code="print('hi')",
                output_path=Path("/tmp/out.png"),
                config=config,
                language="python",
                filename="test.py",
                timeout=5.0,
            )


class TestAtomicWrite:
    """Tests for _write_output_atomic."""

    def test_atomic_write_creates_file(self, tmp_path):
        """Atomic write creates a file with correct content."""
        from codepicture.cli.orchestrator import _write_output_atomic

        output = tmp_path / "out.png"
        _write_output_atomic(b"image data", output)

        assert output.exists()
        assert output.read_bytes() == b"image data"

    def test_atomic_write_creates_parent_dirs(self, tmp_path):
        """Atomic write creates parent directories if needed."""
        from codepicture.cli.orchestrator import _write_output_atomic

        output = tmp_path / "nested" / "out.png"
        _write_output_atomic(b"image data", output)

        assert output.exists()
        assert output.read_bytes() == b"image data"

    @patch("codepicture.cli.orchestrator.shutil.move")
    def test_atomic_write_no_partial_on_failure(self, mock_move, tmp_path):
        """On failure during move, no output file exists and temp is cleaned."""
        from codepicture.cli.orchestrator import _write_output_atomic

        mock_move.side_effect = OSError("disk full")
        output = tmp_path / "out.png"

        with pytest.raises(OSError, match="disk full"):
            _write_output_atomic(b"image data", output)

        assert not output.exists()
        # Verify no temp files left behind
        remaining = list(tmp_path.glob(".codepicture-*"))
        assert len(remaining) == 0

    @patch("codepicture.cli.orchestrator.shutil.move")
    def test_atomic_write_preserves_existing_on_failure(self, mock_move, tmp_path):
        """On failure, existing output file is untouched."""
        from codepicture.cli.orchestrator import _write_output_atomic

        output = tmp_path / "out.png"
        output.write_bytes(b"original content")

        mock_move.side_effect = OSError("disk full")

        with pytest.raises(OSError, match="disk full"):
            _write_output_atomic(b"new content", output)

        # Original file should be untouched
        assert output.read_bytes() == b"original content"
