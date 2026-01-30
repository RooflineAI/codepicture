"""Pipeline orchestration for codepicture.

Separates business logic from CLI argument handling for testability.
"""

import concurrent.futures
import os
import shutil
import sys
import tempfile
from pathlib import Path

from codepicture import (
    RenderConfig,
    PygmentsHighlighter,
    LayoutEngine,
    PangoTextMeasurer,
    Renderer,
    register_bundled_fonts,
    get_theme,
)
from codepicture.errors import HighlightError, RenderTimeoutError


def generate_image(
    code: str,
    output_path: Path,
    config: RenderConfig,
    language: str | None = None,
    filename: str | None = None,
) -> None:
    """Orchestrate the full rendering pipeline.

    Args:
        code: Source code to render
        output_path: Where to write the output image
        config: Render configuration
        language: Explicit language override (auto-detected if None)
        filename: Original filename for language detection

    Raises:
        HighlightError: If tokenization fails
        LayoutError: If layout calculation fails
        RenderError: If rendering fails
    """
    # 1. Register fonts
    register_bundled_fonts()

    # 2. Create highlighter and detect/validate language
    highlighter = PygmentsHighlighter()
    if language is None and filename:
        language = highlighter.detect_language(code, filename)
    elif language is None:
        # Fallback to text if no filename and no language
        language = "text"

    # 3. Tokenize code (fall back to plain text on unknown language)
    try:
        tokens = highlighter.highlight(code, language)
    except HighlightError:
        print(
            f"Warning: Unknown language '{language}', rendering as plain text.",
            file=sys.stderr,
        )
        language = "text"
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

    # 7. Write output atomically
    _write_output_atomic(result.data, output_path)


def _write_output_atomic(data: bytes, output_path: Path) -> None:
    """Write render result atomically -- complete file or nothing.

    Creates a temporary file in the same directory as the output,
    writes data to it, then moves it to the final path. If anything
    fails, the temp file is cleaned up and no partial output remains.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd = tempfile.NamedTemporaryFile(
        dir=output_path.parent,
        prefix=".codepicture-",
        suffix=output_path.suffix,
        delete=False,
    )
    tmp_path = tmp_fd.name
    try:
        tmp_fd.write(data)
        tmp_fd.close()
        shutil.move(tmp_path, str(output_path))
    except BaseException:
        tmp_fd.close()
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def generate_image_with_timeout(
    code: str,
    output_path: Path,
    config: RenderConfig,
    language: str | None = None,
    filename: str | None = None,
    timeout: float | None = 30.0,
) -> None:
    """Run generate_image with a timeout guard.

    Args:
        code: Source code to render.
        output_path: Where to write the output image.
        config: Render configuration.
        language: Explicit language override (auto-detected if None).
        filename: Original filename for language detection.
        timeout: Seconds to wait before aborting. None disables timeout.

    Raises:
        RenderTimeoutError: If rendering exceeds the timeout.
        HighlightError: If tokenization fails.
        LayoutError: If layout calculation fails.
        RenderError: If rendering fails.
    """
    if timeout is None:
        # Timeout disabled (--timeout 0 maps to None)
        generate_image(code, output_path, config, language, filename)
        return

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        generate_image, code, output_path, config, language, filename
    )
    try:
        future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        # Shut down without waiting for the background thread
        executor.shutdown(wait=False, cancel_futures=True)
        raise RenderTimeoutError(
            f"Rendering timed out after {timeout:.0f}s while processing "
            f"'{filename or '<stdin>'}'. "
            f"No output file written. "
            f"Try increasing the timeout with --timeout {int(timeout * 2)}",
            timeout=timeout,
            file_info=filename or "<stdin>",
        )
    else:
        executor.shutdown(wait=True)
