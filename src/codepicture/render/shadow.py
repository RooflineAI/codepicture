"""Shadow post-processing for PNG output.

Applies macOS-style drop shadow using Pillow's GaussianBlur.
Cairo lacks native blur, so this module handles shadow as a post-processing step.

Note: Shadow is only supported for PNG format. SVG/PDF skip shadow rendering.
"""

from io import BytesIO

import cairo
from PIL import Image, ImageFilter

from codepicture.core.types import Color

__all__ = [
    "apply_shadow",
    "calculate_shadow_margin",
    "SHADOW_BLUR_RADIUS",
    "SHADOW_OFFSET_X",
    "SHADOW_OFFSET_Y",
    "SHADOW_COLOR",
]

# macOS-style shadow constants (fixed, not configurable per CONTEXT.md)
# Values based on RESEARCH.md - Silicon tool defaults and macOS aesthetic
SHADOW_BLUR_RADIUS = 50  # Standard blur for macOS window feel
SHADOW_OFFSET_X = 0  # Centered horizontally
SHADOW_OFFSET_Y = 25  # Slight downward offset
SHADOW_COLOR = Color(0, 0, 0, 128)  # 50% black


def calculate_shadow_margin() -> int:
    """Calculate the margin needed for shadow rendering.

    The margin accounts for blur radius and offset to ensure
    the shadow doesn't get clipped at image boundaries.

    Returns:
        Margin in pixels to add around content for shadow
    """
    return SHADOW_BLUR_RADIUS * 2 + max(abs(SHADOW_OFFSET_X), abs(SHADOW_OFFSET_Y))


def apply_shadow(surface: cairo.ImageSurface, enabled: bool = True) -> bytes:
    """Apply drop shadow to a Cairo ImageSurface.

    Converts the Cairo surface to a Pillow Image, creates a shadow from
    the alpha channel, applies Gaussian blur, and composites the shadow
    under the original content.

    Args:
        surface: Cairo ImageSurface with rendered content
        enabled: Whether to apply shadow (if False, returns plain PNG)

    Returns:
        PNG bytes with shadow applied (if enabled) or plain PNG

    Note:
        Cairo uses BGRA byte order with pre-multiplied alpha.
        This is handled by using Pillow's "RGBa" mode during conversion.
    """
    # Get surface dimensions
    width = surface.get_width()
    height = surface.get_height()

    if not enabled:
        # Just return plain PNG without shadow
        buffer = BytesIO()
        surface.write_to_png(buffer)
        return buffer.getvalue()

    # Calculate shadow margin
    shadow_margin = calculate_shadow_margin()

    # Convert Cairo surface to Pillow Image
    # CRITICAL: Cairo FORMAT_ARGB32 stores pixels as native-endian uint32.
    # On little-endian systems the byte layout is B, G, R, A.
    # Pillow's "RGBa" mode expects R, G, B, premultiplied-a and does NOT
    # swap channels -- it only un-premultiplies alpha.
    # We must read as raw BGRA, un-premultiply, then swap B<->R.
    data = bytes(surface.get_data())
    pil_image = Image.frombytes("RGBa", (width, height), data)
    # Convert to standard RGBA (un-premultiply alpha)
    pil_image = pil_image.convert("RGBA")
    # Swap R and B channels to correct Cairo's BGRA byte order
    b, g, r, a = pil_image.split()
    pil_image = Image.merge("RGBA", (r, g, b, a))

    # Create shadow from alpha channel
    # Extract alpha channel which represents the content shape
    alpha = pil_image.split()[3]
    # Create a shadow image with the shadow color (fully transparent initially)
    shadow = Image.new(
        "RGBA", (width, height), (SHADOW_COLOR.r, SHADOW_COLOR.g, SHADOW_COLOR.b, 0)
    )
    # Apply the content's alpha as the shadow's alpha
    shadow.putalpha(alpha)
    # Apply Gaussian blur to create the soft shadow effect
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=SHADOW_BLUR_RADIUS))

    # Create output canvas with margin for shadow
    output_width = width + 2 * shadow_margin
    output_height = height + 2 * shadow_margin
    # Transparent background
    output = Image.new("RGBA", (output_width, output_height), (0, 0, 0, 0))

    # Composite shadow first (with offset), then content on top
    shadow_x = shadow_margin + SHADOW_OFFSET_X
    shadow_y = shadow_margin + SHADOW_OFFSET_Y
    output.paste(shadow, (shadow_x, shadow_y), shadow)
    # Content is centered (no offset)
    output.paste(pil_image, (shadow_margin, shadow_margin), pil_image)

    # Export to PNG bytes
    buffer = BytesIO()
    output.save(buffer, format="PNG")
    return buffer.getvalue()
