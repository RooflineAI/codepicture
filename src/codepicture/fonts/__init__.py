"""Font management for codepicture.

Provides font registration and fallback utilities using ManimPango.
Bundles JetBrains Mono for consistent rendering across systems.
"""

import logging
from importlib.resources import as_file, files

import manimpango

__all__ = ["register_bundled_fonts", "resolve_font_family"]

_logger = logging.getLogger(__name__)

# Module-level state to avoid re-registration
_fonts_registered: bool = False


def register_bundled_fonts() -> bool:
    """Register bundled JetBrains Mono font with the system.

    Uses ManimPango to register the font so it becomes available
    for text measurement and rendering. Safe to call multiple times;
    registration only happens once.

    Returns:
        True if fonts were registered (or already registered), False on error
    """
    global _fonts_registered

    if _fonts_registered:
        return True

    try:
        # Access bundled font file using importlib.resources
        font_package = files("codepicture.fonts")
        font_file = font_package.joinpath("JetBrainsMono-Regular.ttf")

        with as_file(font_file) as font_path:
            # Register font with ManimPango
            result = manimpango.register_font(str(font_path))
            if result:
                _fonts_registered = True
                _logger.debug("Registered JetBrains Mono font from %s", font_path)
                return True
            else:
                _logger.warning("Failed to register JetBrains Mono font")
                return False
    except Exception as e:
        _logger.warning("Error registering bundled fonts: %s", e)
        return False


def resolve_font_family(requested: str, default: str = "JetBrains Mono") -> str:
    """Resolve a font family name, falling back to default if not available.

    Checks if the requested font is available in the system's font list.
    If not found, logs a warning and returns the default (bundled) font.
    Automatically registers bundled fonts if not already registered.

    Args:
        requested: The requested font family name
        default: Fallback font family name (default: "JetBrains Mono")

    Returns:
        The requested font if available, otherwise the default font
    """
    # Ensure bundled fonts are registered
    register_bundled_fonts()

    # Get list of available fonts
    available_fonts = manimpango.list_fonts()

    # Check if requested font is available
    if requested in available_fonts:
        return requested

    # Log warning and fall back
    _logger.warning(
        "Font '%s' not found, falling back to '%s'",
        requested,
        default,
    )
    return default
