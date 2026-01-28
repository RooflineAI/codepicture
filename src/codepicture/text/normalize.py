"""Text normalization utilities for consistent code rendering."""


def normalize_tabs(code: str, tab_width: int = 4) -> str:
    """Convert all tab characters to spaces.

    Tab normalization is applied immediately when code is received,
    before any processing (highlighting, layout, rendering).

    Args:
        code: Source code string
        tab_width: Number of spaces per tab (1-8)

    Returns:
        Code with tabs replaced by spaces

    Raises:
        ValueError: If tab_width is not in range 1-8
    """
    if not 1 <= tab_width <= 8:
        raise ValueError(f"tab_width must be 1-8, got {tab_width}")

    return code.replace("\t", " " * tab_width)
