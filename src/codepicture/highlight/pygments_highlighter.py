"""Pygments-based syntax highlighter with position tracking.

Implements the Highlighter protocol using Pygments for tokenization.
Tracks line:column positions for each token to support accurate rendering.
"""

from dataclasses import dataclass
from typing import Any

from pygments.lexers import (
    get_all_lexers,
    get_lexer_by_name,
    get_lexer_for_filename,
    guess_lexer,
)
from pygments.util import ClassNotFound

from codepicture.errors import HighlightError

from .language_aliases import resolve_language_alias


@dataclass(frozen=True, slots=True)
class TokenInfo:
    """Information about a single token.

    Attributes:
        text: The token's text content
        token_type: Pygments token type (e.g., Token.Keyword)
        line: 0-indexed line number
        column: 0-indexed column position
    """

    text: str
    token_type: Any
    line: int
    column: int


class PygmentsHighlighter:
    """Syntax highlighter using Pygments.

    Implements the Highlighter protocol with position tracking for each token.
    Handles language detection from filename extensions and explicit language names.
    """

    def highlight(self, code: str, language: str) -> list[list[TokenInfo]]:
        """Tokenize code with position tracking.

        Args:
            code: Source code string
            language: Language identifier (e.g., 'python', 'rust')

        Returns:
            List of lines, where each line is a list of TokenInfo objects
            containing text, token_type, line, and column.

        Raises:
            HighlightError: If language is unknown
        """
        # Resolve language alias (e.g., yml -> yaml)
        resolved_language = resolve_language_alias(language)

        # Get the lexer
        try:
            lexer = get_lexer_by_name(resolved_language)
        except ClassNotFound as err:
            available = self.list_languages()[:20]
            raise HighlightError(
                f"Unknown language: {language}. "
                f"Available languages include: {', '.join(sorted(available))}..."
            ) from err

        # Tokenize with position tracking
        lines: list[list[TokenInfo]] = [[]]
        current_line = 0
        current_column = 0

        for token_type, text in lexer.get_tokens(code):
            # Handle tokens that span multiple lines (e.g., multiline strings)
            parts = text.split("\n")

            for i, part in enumerate(parts):
                if i > 0:
                    # Start a new line
                    lines.append([])
                    current_line += 1
                    current_column = 0

                if part:
                    # Non-empty text creates a token
                    lines[current_line].append(
                        TokenInfo(
                            text=part,
                            token_type=token_type,
                            line=current_line,
                            column=current_column,
                        )
                    )
                    current_column += len(part)

        # Pygments always adds a trailing newline. Remove the extra empty line
        # if the original code didn't end with a newline.
        if lines and not lines[-1] and not code.endswith("\n"):
            lines.pop()

        return lines

    def detect_language(self, code: str, filename: str | None = None) -> str:
        """Auto-detect language from filename or content.

        Args:
            code: Source code string
            filename: Optional filename for extension-based detection

        Returns:
            Language identifier (first canonical alias)

        Raises:
            HighlightError: If language cannot be detected
        """
        try:
            if filename:
                lexer = get_lexer_for_filename(filename, code)
            else:
                lexer = guess_lexer(code)
            # Return the first (canonical) alias
            return lexer.aliases[0] if lexer.aliases else lexer.name.lower()
        except ClassNotFound as err:
            raise HighlightError(
                "Could not detect language"
                + (f" for file: {filename}" if filename else " from content")
            ) from err

    def list_languages(self) -> list[str]:
        """Return sorted list of all available language aliases.

        Returns:
            Sorted list of supported language identifiers
        """
        aliases: set[str] = set()
        for _name, alias_list, _patterns, _mimetypes in get_all_lexers():
            aliases.update(alias_list)
        return sorted(aliases)
