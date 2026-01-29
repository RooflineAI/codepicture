"""Pipeline orchestration for codepicture.

Separates business logic from CLI argument handling for testability.
"""

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

    # 3. Tokenize code
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
