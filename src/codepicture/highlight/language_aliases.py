"""Supplemental language aliases for Pygments.

Pygments handles most language aliases (py->python, js->javascript), but
misses some common user expectations. This module provides additional
aliases that users expect to work.

Reference: RESEARCH.md Pitfall 1 - Missing Language Alias (yml)
"""

# Supplemental aliases that Pygments doesn't handle
EXTRA_ALIASES: dict[str, str] = {
    "yml": "yaml",
    # Add others as users report them
}


def resolve_language_alias(language: str) -> str:
    """Resolve a language alias to its canonical form.

    Checks EXTRA_ALIASES first, then returns the original language name
    if no alias is found. Pygments will handle its own aliases.

    Args:
        language: Language name or alias (e.g., 'yml', 'python')

    Returns:
        Canonical language name (e.g., 'yaml', 'python')
    """
    return EXTRA_ALIASES.get(language.lower(), language)
