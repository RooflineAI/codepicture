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

    def test_file_not_found_clean_message(self, tmp_path: Path):
        """Missing file error has no Python traceback."""
        result = runner.invoke(app, ["nonexistent.py", "-o", str(tmp_path / "out.png")])
        assert result.exit_code != 0
        assert "Traceback" not in result.output


class TestCliGeneration:
    """Tests for CLI image generation."""

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_generate_png(self, sample_py: Path, tmp_path: Path):
        """Generate PNG from Python file."""
        output = tmp_path / "output.png"
        result = runner.invoke(app, [str(sample_py), "-o", str(output)])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()
        # Check PNG magic bytes
        assert output.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_generate_svg(self, sample_py: Path, tmp_path: Path):
        """Generate SVG from Python file."""
        output = tmp_path / "output.svg"
        result = runner.invoke(app, [str(sample_py), "-o", str(output)])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()
        content = output.read_text()
        assert "<svg" in content

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_format_flag_overrides_extension(self, sample_py: Path, tmp_path: Path):
        """--format overrides extension inference."""
        output = tmp_path / "output.png"  # .png extension
        result = runner.invoke(app, [str(sample_py), "-o", str(output), "-f", "svg"])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        # File should be SVG despite .png extension
        content = output.read_text()
        assert "<svg" in content

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_theme_flag(self, sample_py: Path, tmp_path: Path):
        """--theme flag changes output colors."""
        output = tmp_path / "output.png"
        result = runner.invoke(app, [str(sample_py), "-o", str(output), "-t", "dracula"])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_config_file(self, sample_py: Path, sample_config: Path, tmp_path: Path):
        """--config flag loads config from file."""
        output = tmp_path / "output.png"
        result = runner.invoke(app, [
            str(sample_py), "-o", str(output),
            "--config", str(sample_config)
        ])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_creates_parent_directories(self, sample_py: Path, tmp_path: Path):
        """Output path parent directories are created."""
        output = tmp_path / "nested" / "deep" / "output.png"
        result = runner.invoke(app, [str(sample_py), "-o", str(output)])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()

    @pytest.mark.slow
    @pytest.mark.timeout(15)
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

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_verbose_shows_steps(self, sample_py: Path, tmp_path: Path):
        """--verbose shows processing steps on stderr."""
        output = tmp_path / "output.png"
        result = runner.invoke(app, [str(sample_py), "-o", str(output), "-v"])

        assert result.exit_code == 0
        # Verbose output should mention reading/loading/rendering
        assert "Reading" in result.output or "Loading" in result.output or "Rendering" in result.output


# =============================================================================
# Integration Tests - subprocess
# =============================================================================

class TestCliTimeout:
    """Tests for CLI --timeout flag."""

    def test_timeout_appears_in_help(self):
        """--timeout flag appears in help output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--timeout" in result.output

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_timeout_flag_accepted(self, sample_py: Path, tmp_path: Path):
        """--timeout flag is accepted and renders successfully."""
        output = tmp_path / "out.png"
        result = runner.invoke(app, [str(sample_py), "-o", str(output), "--timeout", "5"])
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_timeout_zero_disables(self, sample_py: Path, tmp_path: Path):
        """--timeout 0 disables timeout and renders successfully."""
        output = tmp_path / "out.png"
        result = runner.invoke(app, [str(sample_py), "-o", str(output), "--timeout", "0"])
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()


class TestCliExitCodes:
    """Tests for CLI exit codes via subprocess."""

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_success_exits_zero(self, tmp_path: Path):
        """Successful render exits with code 0."""
        input_file = tmp_path / "test.py"
        input_file.write_text('print("hello")')
        output_file = tmp_path / "output.png"

        result = subprocess.run(
            [sys.executable, "-m", "codepicture", str(input_file), "-o", str(output_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_file_not_found_exits_nonzero(self, tmp_path: Path):
        """Nonexistent file exits with non-zero code."""
        output_file = tmp_path / "output.png"

        result = subprocess.run(
            [sys.executable, "-m", "codepicture", "nonexistent.py", "-o", str(output_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_error_message_no_traceback(self, tmp_path: Path):
        """Error messages do not contain Python tracebacks."""
        output_file = tmp_path / "output.png"

        result = subprocess.run(
            [sys.executable, "-m", "codepicture", "nonexistent.py", "-o", str(output_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Traceback" not in result.stderr
        assert "error" in result.stderr.lower() or "not found" in result.stderr.lower()


class TestCliLanguageFallback:
    """Tests for unknown language fallback."""

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_unknown_language_renders_as_text(self, sample_py: Path, tmp_path: Path):
        """Unknown language falls back to plain text and renders successfully."""
        output = tmp_path / "out.png"
        result = runner.invoke(
            app, [str(sample_py), "-o", str(output), "-l", "notareallanguage"]
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output.exists()

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_unknown_language_warns_on_stderr(self, sample_py: Path, tmp_path: Path):
        """Unknown language produces a warning about plain text fallback."""
        output = tmp_path / "out.png"
        result = runner.invoke(
            app, [str(sample_py), "-o", str(output), "-l", "notareallanguage"]
        )
        assert result.exit_code == 0
        # CliRunner merges stdout/stderr; check for warning text
        assert "Warning" in result.output or "plain text" in result.output


class TestCliIntegration:
    """Integration tests using subprocess for true end-to-end testing."""

    def test_cli_help_subprocess(self):
        """CLI help works via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "codepicture", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Generate a beautiful image" in result.stdout

    def test_cli_version_subprocess(self):
        """CLI version works via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "codepicture", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert __version__ in result.stdout

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_cli_generate_subprocess(self, tmp_path: Path):
        """End-to-end image generation via subprocess."""
        # Create input file
        input_file = tmp_path / "test.py"
        input_file.write_text('print("hello")')
        output_file = tmp_path / "output.png"

        result = subprocess.run(
            [sys.executable, "-m", "codepicture", str(input_file), "-o", str(output_file)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output_file.exists()
        # Check PNG magic bytes
        assert output_file.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'

    def test_cli_error_subprocess(self, tmp_path: Path):
        """CLI error handling via subprocess."""
        output_file = tmp_path / "output.png"

        result = subprocess.run(
            [sys.executable, "-m", "codepicture", "nonexistent.py", "-o", str(output_file)],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        # Error should be on stderr
        assert "error" in result.stderr.lower() or "not found" in result.stderr.lower()

    @pytest.mark.slow
    @pytest.mark.timeout(15)
    def test_cli_silent_on_success(self, tmp_path: Path):
        """CLI is silent on success (no stdout)."""
        input_file = tmp_path / "test.py"
        input_file.write_text('print("hello")')
        output_file = tmp_path / "output.png"

        result = subprocess.run(
            [sys.executable, "-m", "codepicture", str(input_file), "-o", str(output_file)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert result.stdout == ""  # Silent on success
