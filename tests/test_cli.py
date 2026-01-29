"""Tests for codepicture CLI.

Unit tests use Typer's CliRunner for fast, isolated testing.
Integration tests use subprocess for true end-to-end verification.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from codepicture import __version__
from codepicture.cli import app


runner = CliRunner()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_py(tmp_path: Path) -> Path:
    """Create a sample Python file."""
    sample = tmp_path / "sample.py"
    sample.write_text('print("hello")')
    return sample


@pytest.fixture
def sample_config(tmp_path: Path) -> Path:
    """Create a sample config file."""
    config = tmp_path / "codepicture.toml"
    config.write_text('theme = "dracula"\npadding = 20\n')
    return config


# =============================================================================
# Unit Tests - CliRunner
# =============================================================================

class TestCliHelp:
    """Tests for CLI help and meta options."""

    def test_help(self):
        """--help shows usage information."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Generate a beautiful image" in result.output
        assert "--output" in result.output

    def test_version(self):
        """--version shows version string."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_list_themes(self):
        """--list-themes shows available themes."""
        result = runner.invoke(app, ["--list-themes"])
        assert result.exit_code == 0
        assert "catppuccin-mocha" in result.output
        assert "dracula" in result.output


class TestCliErrors:
    """Tests for CLI error handling."""

    def test_no_args_shows_help(self):
        """Running with no args shows help (exit code 0 or 2 depending on typer version)."""
        result = runner.invoke(app, [])
        # no_args_is_help=True causes exit code 0 on some typer versions, 2 on others
        assert result.exit_code in (0, 2)
        assert "Usage:" in result.output

    def test_missing_output_flag(self, sample_py: Path):
        """Missing -o flag is an error."""
        result = runner.invoke(app, [str(sample_py)])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_missing_input_file(self, tmp_path: Path):
        """Missing input file shows error."""
        result = runner.invoke(app, ["nonexistent.py", "-o", str(tmp_path / "out.png")])
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_stdin_requires_language(self, tmp_path: Path):
        """stdin input (-) requires --language flag."""
        result = runner.invoke(app, ["-", "-o", str(tmp_path / "out.png")], input="print('hi')")
        assert result.exit_code != 0
        assert "language" in result.output.lower()


class TestCliGeneration:
    """Tests for CLI image generation."""

    def test_generate_png(self, sample_py: Path, tmp_path: Path):
        """Generate PNG from Python file."""
        output = tmp_path / "output.png"
        result = runner.invoke(app, [str(sample_py), "-o", str(output)])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()
        # Check PNG magic bytes
        assert output.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'

    def test_generate_svg(self, sample_py: Path, tmp_path: Path):
        """Generate SVG from Python file."""
        output = tmp_path / "output.svg"
        result = runner.invoke(app, [str(sample_py), "-o", str(output)])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()
        content = output.read_text()
        assert "<svg" in content

    def test_format_flag_overrides_extension(self, sample_py: Path, tmp_path: Path):
        """--format overrides extension inference."""
        output = tmp_path / "output.png"  # .png extension
        result = runner.invoke(app, [str(sample_py), "-o", str(output), "-f", "svg"])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        # File should be SVG despite .png extension
        content = output.read_text()
        assert "<svg" in content

    def test_theme_flag(self, sample_py: Path, tmp_path: Path):
        """--theme flag changes output colors."""
        output = tmp_path / "output.png"
        result = runner.invoke(app, [str(sample_py), "-o", str(output), "-t", "dracula"])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()

    def test_config_file(self, sample_py: Path, sample_config: Path, tmp_path: Path):
        """--config flag loads config from file."""
        output = tmp_path / "output.png"
        result = runner.invoke(app, [
            str(sample_py), "-o", str(output),
            "--config", str(sample_config)
        ])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()

    def test_creates_parent_directories(self, sample_py: Path, tmp_path: Path):
        """Output path parent directories are created."""
        output = tmp_path / "nested" / "deep" / "output.png"
        result = runner.invoke(app, [str(sample_py), "-o", str(output)])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()

    def test_stdin_with_language(self, tmp_path: Path):
        """stdin input works with --language flag."""
        output = tmp_path / "output.png"
        result = runner.invoke(
            app,
            ["-", "-o", str(output), "-l", "python"],
            input='print("hello")'
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()


class TestCliVerbose:
    """Tests for verbose mode."""

    def test_verbose_shows_steps(self, sample_py: Path, tmp_path: Path):
        """--verbose shows processing steps on stderr."""
        output = tmp_path / "output.png"
        result = runner.invoke(app, [str(sample_py), "-o", str(output), "-v"])

        assert result.exit_code == 0
        # Verbose output should mention reading/loading/rendering
        assert "Reading" in result.output or "Loading" in result.output or "Rendering" in result.output
