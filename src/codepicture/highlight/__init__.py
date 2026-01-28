"""Syntax highlighting module.

Re-exports the main highlighter implementation and supporting types.
"""

from .language_aliases import EXTRA_ALIASES, resolve_language_alias

__all__ = [
    "EXTRA_ALIASES",
    "resolve_language_alias",
]
