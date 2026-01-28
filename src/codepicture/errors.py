"""Error hierarchy for codepicture.

All exceptions inherit from CodepictureError to enable:
- Catching all codepicture errors with a single except clause
- Specific error handling per exception type
"""


class CodepictureError(Exception):
    """Base exception for all codepicture errors."""

    pass


class ConfigError(CodepictureError):
    """Configuration loading or validation failed.

    Examples: invalid hex color, font_size out of range,
    missing config file, malformed TOML.

    Attributes:
        field: Optional field name that caused the error.
    """

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


class ThemeError(CodepictureError):
    """Theme loading or parsing failed.

    Examples: unknown theme name, malformed theme file.
    """

    pass


class RenderError(CodepictureError):
    """Rendering pipeline failed.

    Examples: font not found, canvas creation failed,
    file write failed, clipboard unavailable.
    """

    pass


class HighlightError(CodepictureError):
    """Syntax highlighting failed.

    Examples: unknown language, failed language detection,
    custom lexer failed to load.
    """

    pass
