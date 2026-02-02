"""Typer CLI application for codepicture.

Usage: codepicture FILE -o OUTPUT [OPTIONS]
"""

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from codepicture import __version__, list_themes, load_config
from codepicture.core.types import OutputFormat
from codepicture.errors import CodepictureError, InputError, RenderTimeoutError

from .orchestrator import generate_image_with_timeout

app = typer.Typer(
    name="codepicture",
    help="Generate beautiful images of source code.",
    add_completion=True,
    no_args_is_help=True,
)

err_console = Console(stderr=True)

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_TIMEOUT = 2


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"codepicture {__version__}")
        raise typer.Exit()


def list_themes_callback(value: bool) -> None:
    """Print available themes and exit."""
    if value:
        for theme in list_themes():
            typer.echo(theme)
        raise typer.Exit()


def infer_format(output_path: Path, explicit_format: str | None) -> OutputFormat:
    """Infer output format from path extension or explicit flag."""
    if explicit_format:
        return OutputFormat(explicit_format.lower())

    ext = output_path.suffix.lower()
    format_map = {
        ".png": OutputFormat.PNG,
        ".svg": OutputFormat.SVG,
        ".pdf": OutputFormat.PDF,
    }
    return format_map.get(ext, OutputFormat.PNG)  # Default to PNG


def read_input(input_path: str, language: str | None) -> tuple[str, str | None]:
    """Read code from file or stdin.

    Returns:
        Tuple of (code, filename) where filename is None for stdin
    """
    if input_path == "-":
        if language is None:
            raise typer.BadParameter(
                "stdin input (-) requires --language flag", param_hint="'INPUT_FILE'"
            )
        return sys.stdin.read(), None

    path = Path(input_path)
    if not path.exists():
        raise InputError(f"File not found: {input_path}", input_path=input_path)
    if not path.is_file():
        raise InputError(f"Not a file: {input_path}", input_path=input_path)
    try:
        return path.read_text(), path.name
    except PermissionError as err:
        raise InputError(
            f"Permission denied: {input_path}", input_path=input_path
        ) from err


@app.command()
def main(
    input_file: Annotated[
        str, typer.Argument(help="Source code file path, or - for stdin")
    ],
    output: Annotated[
        Path, typer.Option("-o", "--output", help="Output image path (required)")
    ],
    # Config file
    config_file: Annotated[
        Path | None,
        typer.Option("--config", help="Config file path (overrides search)"),
    ] = None,
    # Theme & language
    theme: Annotated[
        str | None, typer.Option("-t", "--theme", help="Color theme name")
    ] = None,
    language: Annotated[
        str | None,
        typer.Option(
            "-l", "--language", help="Source language (auto-detected if omitted)"
        ),
    ] = None,
    # Output format
    format: Annotated[
        str | None, typer.Option("-f", "--format", help="Output format: png, svg, pdf")
    ] = None,
    # Typography
    font_family: Annotated[
        str | None, typer.Option("--font", help="Font family name")
    ] = None,
    font_size: Annotated[
        int | None, typer.Option("--font-size", help="Font size in points")
    ] = None,
    line_height: Annotated[
        float | None, typer.Option("--line-height", help="Line height multiplier")
    ] = None,
    tab_width: Annotated[
        int | None, typer.Option("--tab-width", help="Tab width in spaces")
    ] = None,
    # Visual
    padding: Annotated[
        int | None, typer.Option("--padding", help="Padding around code in pixels")
    ] = None,
    corner_radius: Annotated[
        int | None, typer.Option("--corner-radius", help="Window corner radius")
    ] = None,
    window_width: Annotated[
        int | None,
        typer.Option("--width", help="Window width in pixels (enables word wrap)"),
    ] = None,
    window_height: Annotated[
        int | None, typer.Option("--height", help="Window height in pixels")
    ] = None,
    background_color: Annotated[
        str | None, typer.Option("--background", help="Background color (#RRGGBB)")
    ] = None,
    # Line numbers
    line_numbers: Annotated[
        bool | None,
        typer.Option("--line-numbers/--no-line-numbers", help="Show line numbers"),
    ] = None,
    line_number_offset: Annotated[
        int | None, typer.Option("--line-offset", help="Starting line number")
    ] = None,
    # Window chrome
    window_controls: Annotated[
        bool | None,
        typer.Option(
            "--window-controls/--no-window-controls", help="Show window controls"
        ),
    ] = None,
    window_title: Annotated[
        str | None, typer.Option("--title", help="Window title text")
    ] = None,
    # Shadow
    shadow: Annotated[
        bool | None, typer.Option("--shadow/--no-shadow", help="Enable drop shadow")
    ] = None,
    # Timeout
    timeout: Annotated[
        float,
        typer.Option("--timeout", help="Rendering timeout in seconds (0 to disable)"),
    ] = 30.0,
    # Meta options
    verbose: Annotated[
        bool, typer.Option("-v", "--verbose", help="Show processing steps")
    ] = False,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
    list_themes_opt: Annotated[
        bool,
        typer.Option(
            "--list-themes",
            callback=list_themes_callback,
            is_eager=True,
            help="List available themes and exit",
        ),
    ] = False,
) -> None:
    """Generate a beautiful image from source code."""
    effective_timeout = None if timeout == 0 else timeout

    try:
        # Read input
        if verbose:
            err_console.print(f"[dim]Reading {input_file}...[/dim]")
        code, filename = read_input(input_file, language)

        # Build CLI overrides dict (only set values)
        cli_overrides: dict = {}
        if theme is not None:
            cli_overrides["theme"] = theme
        if font_family is not None:
            cli_overrides["font_family"] = font_family
        if font_size is not None:
            cli_overrides["font_size"] = font_size
        if line_height is not None:
            cli_overrides["line_height"] = line_height
        if tab_width is not None:
            cli_overrides["tab_width"] = tab_width
        if padding is not None:
            cli_overrides["padding"] = padding
        if corner_radius is not None:
            cli_overrides["corner_radius"] = corner_radius
        if background_color is not None:
            cli_overrides["background_color"] = background_color
        if line_numbers is not None:
            cli_overrides["show_line_numbers"] = line_numbers
        if line_number_offset is not None:
            cli_overrides["line_number_offset"] = line_number_offset
        if window_controls is not None:
            cli_overrides["window_controls"] = window_controls
        if window_title is not None:
            cli_overrides["window_title"] = window_title
        if shadow is not None:
            cli_overrides["shadow"] = shadow
        if window_width is not None:
            cli_overrides["window_width"] = window_width
        if window_height is not None:
            cli_overrides["window_height"] = window_height

        # Infer output format and add to overrides
        output_format = infer_format(output, format)
        cli_overrides["output_format"] = output_format

        # Load config
        if verbose:
            if config_file:
                err_console.print(f"[dim]Loading config from {config_file}...[/dim]")
            else:
                err_console.print("[dim]Loading config...[/dim]")

        config = load_config(
            config_path=config_file,
            cli_overrides=cli_overrides,
        )

        # Generate image
        if verbose:
            err_console.print(
                f"[dim]Rendering to {output} "
                f"(timeout: {effective_timeout or 'disabled'}s)...[/dim]"
            )

        generate_image_with_timeout(
            code=code,
            output_path=output,
            config=config,
            language=language,
            filename=filename,
            timeout=effective_timeout,
        )

        if verbose:
            err_console.print("[green]Done![/green]")

    except RenderTimeoutError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(EXIT_TIMEOUT) from None
    except CodepictureError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(EXIT_ERROR) from None
    except Exception as e:
        err_console.print(f"[red]Error:[/red] Unexpected error: {e}")
        raise typer.Exit(EXIT_ERROR) from None
