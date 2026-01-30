"""Error hierarchy for codepicture.

All exceptions inherit from CodepictureError to enable:
- Catching all codepicture errors with a single except clause
- Specific error handling per exception type

Exception classes:
    CodepictureError — base for all codepicture errors
    ConfigError — configuration loading/validation failures
    ThemeError — theme loading/parsing failures
    RenderError — rendering pipeline failures
    RenderTimeoutError — render exceeded configured time limit
    HighlightError — syntax highlighting failures
    LayoutError — layout calculation failures
    InputError — input file validation failures
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


class RenderTimeoutError(RenderError):
    """Rendering exceeded the configured time limit.

    Attributes:
        timeout: The timeout value in seconds that was exceeded.
        file_info: The file being rendered when timeout occurred.
    """

    def __init__(
        self,
        message: str,
        timeout: float | None = None,
        file_info: str | None = None,
    ):
        self.timeout = timeout
        self.file_info = file_info
        super().__init__(message)


class HighlightError(CodepictureError):
    """Syntax highlighting failed.

    Examples: unknown language, failed language detection,
    custom lexer failed to load.
    """

    pass


class LayoutError(CodepictureError):
    """Raised when layout calculation fails.

    Common causes:
    - Empty input (no code to render)
    - Invalid configuration values
    """

    pass


class InputError(CodepictureError):
    """Input file validation failed.

    Examples: file not found, permission denied, unreadable file.

    Attributes:
        input_path: Path to the input that caused the error.
    """

    def __init__(self, message: str, input_path: str | None = None):
        self.input_path = input_path
        super().__init__(message)
