"""Syntax highlighting module.

Re-exports the main highlighter implementation and supporting types.
"""

from .language_aliases import EXTRA_ALIASES, resolve_language_alias
from .pygments_highlighter import PygmentsHighlighter, TokenInfo

__all__ = [
    "EXTRA_ALIASES",
    "PygmentsHighlighter",
    "TokenInfo",
    "resolve_language_alias",
]
