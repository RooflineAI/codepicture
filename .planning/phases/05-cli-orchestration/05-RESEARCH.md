# Phase 5: CLI & Orchestration - Research

**Researched:** 2026-01-29
**Domain:** Python CLI frameworks, command orchestration, config file handling
**Confidence:** HIGH

## Summary

This phase delivers a working command-line tool that users can install and run via `codepicture FILE -o OUTPUT`. The CLI orchestrates the existing codepicture pipeline: read input, detect/specify language, tokenize code, calculate layout, render to image, write output.

The standard approach uses **Typer** (0.21.1) for CLI argument parsing with type hints. Typer provides automatic help text, shell completion, and Rich-formatted error output. Config file handling uses the existing `load_config()` function with modifications to support the CONTEXT.md requirement that local config REPLACES global (current implementation MERGES them).

Key implementation considerations:
- stdin reading via `-` requires manual handling (check for `-` value, read `sys.stdin`)
- Exit codes follow POSIX convention: 0 success, 1 general error, 2 usage error
- Verbose mode uses Rich Console for stderr output
- Testing uses Typer's `CliRunner` for unit tests, subprocess for integration tests

**Primary recommendation:** Use Typer with explicit CLI option/argument definitions (not typer-config decorator), keeping config loading logic in the existing `load_config()` function.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| typer | 0.21.1 | CLI framework | Official "FastAPI of CLIs", type-hint based, auto-help |
| rich | (bundled) | Formatted output | Bundled with Typer, stderr errors, verbose mode |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tomllib | stdlib | TOML parsing | Config file loading (already used in loader.py) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| typer | click | Typer wraps Click with type hints - use Typer directly |
| typer | argparse | argparse is stdlib but verbose, no auto-completion |
| typer-config | manual config | typer-config adds `--config` but we need custom search order - manual is cleaner |

**Installation:**
```bash
# Add to pyproject.toml dependencies
uv add typer
```

## Architecture Patterns

### Recommended Project Structure
```
src/codepicture/
├── cli/                    # CLI module (new)
│   ├── __init__.py        # Re-export main app
│   ├── app.py             # Typer app and commands
│   └── orchestrator.py    # Pipeline orchestration logic
├── config/                 # (existing)
│   ├── loader.py          # Modify: local replaces global
│   └── schema.py          # (unchanged)
└── __main__.py            # Entry point: from .cli import app; app()
```

### Pattern 1: Typer App with Callback
**What:** Use `@app.callback()` for version flag, main command as default
**When to use:** Single-command CLI with global options
**Example:**
```python
# Source: https://typer.tiangolo.com/tutorial/options/version/
from typing import Annotated
import typer

app = typer.Typer()

def version_callback(value: bool):
    if value:
        from codepicture import __version__
        typer.echo(f"codepicture {__version__}")
        raise typer.Exit()

@app.command()
def main(
    input_file: Annotated[str, typer.Argument(help="Source code file, or - for stdin")],
    output: Annotated[str, typer.Option("-o", "--output", help="Output image path")],
    theme: Annotated[str | None, typer.Option("-t", "--theme")] = None,
    language: Annotated[str | None, typer.Option("-l", "--language")] = None,
    format: Annotated[str | None, typer.Option("-f", "--format")] = None,
    config: Annotated[str | None, typer.Option("--config")] = None,
    list_themes: Annotated[bool, typer.Option("--list-themes")] = False,
    verbose: Annotated[bool, typer.Option("-v", "--verbose")] = False,
    version: Annotated[bool | None, typer.Option(
        "--version", "-V",
        callback=version_callback,
        is_eager=True
    )] = None,
):
    """Generate beautiful images from source code."""
    ...
```

### Pattern 2: Orchestrator Function
**What:** Separate orchestration logic from CLI argument handling
**When to use:** When business logic should be testable without CLI
**Example:**
```python
# src/codepicture/cli/orchestrator.py
from pathlib import Path
from codepicture import (
    RenderConfig, load_config, get_theme, list_themes,
    PygmentsHighlighter, LayoutEngine, PangoTextMeasurer,
    Renderer, register_bundled_fonts,
)
from codepicture.errors import CodepictureError

def generate_image(
    code: str,
    output_path: Path,
    config: RenderConfig,
    language: str | None = None,
    filename: str | None = None,
) -> None:
    """Orchestrate the full rendering pipeline."""
    # 1. Register fonts
    register_bundled_fonts()

    # 2. Detect/validate language
    highlighter = PygmentsHighlighter()
    if language is None:
        language = highlighter.detect_language(code, filename)

    # 3. Tokenize
    tokens = highlighter.highlight(code, language)

    # 4. Load theme
    theme = get_theme(config.theme)

    # 5. Calculate layout
    measurer = PangoTextMeasurer()
    engine = LayoutEngine(measurer, config)
    metrics = engine.calculate_metrics(tokens)

    # 6. Render
    renderer = Renderer(config)
    result = renderer.render(tokens, metrics, theme)

    # 7. Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result.data)
```

### Pattern 3: Error Handling to Exit Codes
**What:** Map CodepictureError subtypes to appropriate exit codes
**When to use:** CLI error handling
**Example:**
```python
# Source: https://typer.tiangolo.com/tutorial/terminating/
from codepicture.errors import (
    CodepictureError, ConfigError, ThemeError,
    HighlightError, RenderError
)
from rich.console import Console

err_console = Console(stderr=True)

def handle_error(e: Exception) -> int:
    """Convert exception to exit code and print message."""
    if isinstance(e, ConfigError):
        err_console.print(f"Error: {e}", style="red")
        return 1
    elif isinstance(e, (ThemeError, HighlightError)):
        err_console.print(f"Error: {e}", style="red")
        return 1
    elif isinstance(e, RenderError):
        err_console.print(f"Error: {e}", style="red")
        return 1
    elif isinstance(e, FileNotFoundError):
        err_console.print(f"Error: file not found: {e.filename}", style="red")
        return 1
    else:
        err_console.print(f"Error: {e}", style="red")
        return 1
```

### Pattern 4: stdin Reading
**What:** Handle `-` as special value for stdin input
**When to use:** `codepicture - -o out.png --language python`
**Example:**
```python
# Source: https://github.com/fastapi/typer/issues/345
import sys

def read_input(input_path: str, language: str | None) -> tuple[str, str | None]:
    """Read code from file or stdin.

    Returns:
        Tuple of (code, filename) where filename is None for stdin
    """
    if input_path == "-":
        if language is None:
            raise typer.BadParameter(
                "stdin input (-) requires --language flag",
                param_hint="'INPUT_FILE'"
            )
        return sys.stdin.read(), None

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(input_path)
    return path.read_text(), path.name
```

### Anti-Patterns to Avoid
- **Mixing CLI and business logic:** Keep orchestration in separate module for testability
- **Hardcoding exit codes:** Use named constants (EXIT_SUCCESS=0, EXIT_ERROR=1)
- **Printing to stdout on error:** All errors should go to stderr via Rich Console
- **Swallowing exceptions:** Always log/display the actual error message

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI argument parsing | Custom argparse wrapper | Typer | Auto-help, completion, type validation |
| Colored error output | ANSI escape codes | Rich Console(stderr=True) | Cross-platform, bundled with Typer |
| TOML parsing | Custom parser | tomllib (stdlib) | Already in use, Python 3.11+ stdlib |
| Path expansion | Manual ~ handling | Path.expanduser() | Handles platform differences |
| Version flag | Custom --version | Typer callback pattern | Standard Typer pattern |
| Config file discovery | Custom search | Existing load_config() | Already implemented, just needs modification |

**Key insight:** The existing codebase already has config loading, theme management, and rendering. The CLI is primarily orchestration and argument parsing - avoid duplicating existing functionality.

## Common Pitfalls

### Pitfall 1: Config Merge vs Replace
**What goes wrong:** Current `load_config()` MERGES global+local configs. CONTEXT.md specifies local REPLACES global entirely.
**Why it happens:** Original implementation assumed merge semantics
**How to avoid:** Modify `load_config()` to stop at first found config file (local first, then global)
**Warning signs:** Config values unexpectedly coming from wrong file

### Pitfall 2: stdin Without Language
**What goes wrong:** Cannot detect language from stdin (no filename)
**Why it happens:** Pygments `guess_lexer` is unreliable for short snippets
**How to avoid:** Require `--language` flag when input is `-`
**Warning signs:** Random language detection, wrong highlighting

### Pitfall 3: Output Format Inference
**What goes wrong:** Ambiguous output format when no extension and no `--format`
**Why it happens:** `output.file` has no extension
**How to avoid:** Default to PNG when format cannot be inferred (per CONTEXT.md)
**Warning signs:** Unexpected file format, file extension mismatch

### Pitfall 4: Verbose Output on Success
**What goes wrong:** Printing info messages to stdout pollutes pipeable output
**Why it happens:** Using print() instead of Rich Console(stderr=True)
**How to avoid:** Verbose mode only outputs to stderr
**Warning signs:** `codepicture input.py -o - | other_tool` fails due to text in stdout

### Pitfall 5: Exit Code Inconsistency
**What goes wrong:** Different error types return same exit code, hard to script
**Why it happens:** Using generic `raise typer.Exit(1)` everywhere
**How to avoid:** Define EXIT_* constants, map error types to codes consistently
**Warning signs:** Scripts can't distinguish configuration error from runtime error

### Pitfall 6: Unknown Config Keys Silently Ignored
**What goes wrong:** Typos in config file (e.g., `thme` instead of `theme`) are not caught
**Why it happens:** Pydantic's default behavior with extra fields
**How to avoid:** RenderConfig already has `extra="forbid"` - this is handled
**Warning signs:** Config values not taking effect despite being in file

## Code Examples

Verified patterns from official sources:

### Typer Command with Required Option
```python
# Source: https://typer.tiangolo.com/tutorial/options/required/
from typing import Annotated
import typer

@app.command()
def main(
    output: Annotated[str, typer.Option("-o", "--output", help="Output file path")]
):
    """Output option is required because no default is provided."""
    ...
```

### Version Flag with Eager Callback
```python
# Source: https://typer.tiangolo.com/tutorial/options/version/
from typing import Annotated
import typer

def version_callback(value: bool):
    if value:
        print(f"my-app version: 1.0.0")
        raise typer.Exit()

@app.command()
def main(
    version: Annotated[bool | None, typer.Option(
        "--version", "-V",
        callback=version_callback,
        is_eager=True,  # Process before other options
    )] = None,
):
    ...
```

### List-Themes Early Exit
```python
# Similar to version pattern
def list_themes_callback(value: bool):
    if value:
        from codepicture import list_themes
        for theme in list_themes():
            typer.echo(theme)
        raise typer.Exit()

@app.command()
def main(
    list_themes: Annotated[bool, typer.Option(
        "--list-themes",
        callback=list_themes_callback,
        is_eager=True,
    )] = False,
):
    ...
```

### Rich Console for stderr
```python
# Source: https://typer.tiangolo.com/tutorial/printing/
from rich.console import Console

err_console = Console(stderr=True)

def log_verbose(message: str, verbose: bool):
    """Print message to stderr if verbose mode is enabled."""
    if verbose:
        err_console.print(f"[dim]{message}[/dim]")
```

### Testing with CliRunner
```python
# Source: https://typer.tiangolo.com/tutorial/testing/
from typer.testing import CliRunner
from codepicture.cli import app

runner = CliRunner()

def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Generate beautiful images" in result.output

def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "codepicture" in result.output
```

### Integration Test with subprocess
```python
# Source: Best practice pattern
import subprocess
import sys
from pathlib import Path

def test_cli_integration(tmp_path: Path):
    """Test CLI via subprocess for true isolation."""
    input_file = tmp_path / "test.py"
    input_file.write_text("print('hello')")
    output_file = tmp_path / "output.png"

    result = subprocess.run(
        [sys.executable, "-m", "codepicture", str(input_file), "-o", str(output_file)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output_file.exists()
    # Check PNG magic bytes
    assert output_file.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| argparse | Typer (Click-based) | ~2020 | Type hints, auto-completion, less boilerplate |
| Custom TOML parsing | tomllib (stdlib) | Python 3.11 | No external dependency |
| print() for errors | Rich Console | Typer 0.4+ | Formatted, colored stderr output |

**Deprecated/outdated:**
- `typer-cli` package: Merged into `typer` core, no longer needed
- Click 7.x patterns: Typer uses Click 8.x internally

## Open Questions

Things that couldn't be fully resolved:

1. **Shell completion installation**
   - What we know: Typer supports `--install-completion` and `--show-completion`
   - What's unclear: Whether to include these flags or leave for users to discover
   - Recommendation: Include them (Typer default behavior), document in help

2. **Progress bar for large files**
   - What we know: Rich provides progress bars, Typer integrates well
   - What's unclear: Whether rendering is slow enough to warrant progress
   - Recommendation: Skip for MVP, verbose mode is sufficient

## Sources

### Primary (HIGH confidence)
- [Typer Official Documentation](https://typer.tiangolo.com/) - Tutorial, testing, termination
- [Typer PyPI](https://pypi.org/project/typer/) - Version 0.21.1, dependencies
- [Click Documentation](https://click.palletsprojects.com/en/stable/) - File handling, stdin patterns

### Secondary (MEDIUM confidence)
- [typer-config GitHub](https://github.com/maxb2/typer-config) - Config file patterns (not using, but informed design)
- [POSIX Exit Codes](https://www.baeldung.com/linux/status-codes) - Exit code conventions

### Tertiary (LOW confidence)
- WebSearch results for Typer best practices 2026 - General patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Typer is well-documented, official docs consulted
- Architecture: HIGH - Patterns from official Typer tutorial
- Pitfalls: MEDIUM - Some based on CONTEXT.md requirements, some general experience

**Research date:** 2026-01-29
**Valid until:** 60 days (Typer is stable, patterns unlikely to change)
