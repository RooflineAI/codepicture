"""Syntax highlighting module.

Re-exports the main highlighter implementation and supporting types.
"""

from .language_aliases import EXTRA_ALIASES, resolve_language_alias
from .custom_lexers.mlir_lexer import MlirLexer
from .pygments_highlighter import PygmentsHighlighter, TokenInfo

__all__ = [
    "EXTRA_ALIASES",
    "MlirLexer",
    "PygmentsHighlighter",
    "TokenInfo",
    "resolve_language_alias",
]
