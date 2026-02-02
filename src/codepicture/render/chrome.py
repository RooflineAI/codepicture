"""Window chrome rendering for macOS-style title bar and traffic light buttons.

Provides functions to draw the macOS window decoration including:
- Title bar with optional title text
- Traffic light buttons (close, minimize, maximize)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from codepicture.core.types import Color

if TYPE_CHECKING:
    from codepicture.render.canvas import CairoCanvas

__all__ = [
    "BUTTON_DIAMETER",
    "BUTTON_MARGIN_LEFT",
    "BUTTON_SPACING",
    "TITLE_BAR_HEIGHT",
    "draw_title_bar",
    "draw_traffic_lights",
]

# Title bar constants (macOS standard)
TITLE_BAR_HEIGHT = 28  # px, standard macOS title bar height

# Traffic light button constants (based on RESEARCH.md macOS values)
BUTTON_DIAMETER = 12  # px
BUTTON_SPACING = 8  # px between buttons
BUTTON_MARGIN_LEFT = 8  # px from left edge
BUTTON_MARGIN_TOP = 8  # px from title bar top (centers in 28px title bar)

# Button colors (static, per CONTEXT.md - no hover states)
CLOSE_COLOR = Color.from_hex("#ff5f57")  # Red
MINIMIZE_COLOR = Color.from_hex("#febc2e")  # Yellow
MAXIMIZE_COLOR = Color.from_hex("#28c840")  # Green

# Title text font settings
TITLE_FONT_SIZE = 13  # px, macOS title font size
TITLE_FONT_FAMILIES = ("SF Pro", "Helvetica Neue", "Helvetica", "Arial")


def draw_traffic_lights(canvas: CairoCanvas, title_bar_y: float) -> None:
    """Draw macOS-style traffic light buttons.

    Draws the three window control buttons (close, minimize, maximize) as
    filled circles in the standard macOS red/yellow/green colors.

    Args:
        canvas: CairoCanvas to draw on
        title_bar_y: Y position of the title bar top edge
    """
    # Center buttons vertically in title bar
    button_y = title_bar_y + (TITLE_BAR_HEIGHT - BUTTON_DIAMETER) / 2

    colors = [CLOSE_COLOR, MINIMIZE_COLOR, MAXIMIZE_COLOR]

    for i, color in enumerate(colors):
        # Calculate button position (left-aligned per CONTEXT.md)
        button_x = BUTTON_MARGIN_LEFT + i * (BUTTON_DIAMETER + BUTTON_SPACING)
        center_x = button_x + BUTTON_DIAMETER / 2
        center_y = button_y + BUTTON_DIAMETER / 2

        canvas.draw_circle(center_x, center_y, BUTTON_DIAMETER / 2, color)


def draw_title_bar(
    canvas: CairoCanvas,
    width: float,
    background: Color,
    title: str | None = None,
    corner_radius: float = 0,
) -> None:
    """Draw macOS-style title bar with traffic light buttons.

    Per CONTEXT.md:
    - Title bar background matches code background (seamless macOS look)
    - No separator line between title bar and content
    - Title text (when provided) uses system font, not monospace
    - Traffic light buttons are always left-aligned

    Args:
        canvas: CairoCanvas to draw on
        width: Full width of the title bar
        background: Background color for the title bar
        title: Optional title text to display centered in title bar
        corner_radius: Corner radius for rounded top corners (default: 0)
    """
    # Draw title bar background
    if corner_radius > 0:
        # Draw rounded rectangle for title bar (rounds top corners only visually)
        # We draw a rounded rect but only show the title bar height portion
        # The content area below will cover the bottom rounded corners
        canvas.draw_rectangle(
            x=0,
            y=0,
            width=width,
            height=TITLE_BAR_HEIGHT,
            color=background,
            corner_radius=corner_radius,
        )
        # Cover the bottom portion that shouldn't be rounded
        # This creates the effect of only rounded top corners
        if corner_radius < TITLE_BAR_HEIGHT:
            canvas.draw_rectangle(
                x=0,
                y=TITLE_BAR_HEIGHT - corner_radius,
                width=width,
                height=corner_radius,
                color=background,
                corner_radius=0,
            )
    else:
        # Simple rectangle for no rounded corners
        canvas.draw_rectangle(
            x=0,
            y=0,
            width=width,
            height=TITLE_BAR_HEIGHT,
            color=background,
            corner_radius=0,
        )

    # Draw traffic light buttons
    draw_traffic_lights(canvas, 0)

    # Draw title text if provided
    if title:
        # Try system font families in order
        font_family = TITLE_FONT_FAMILIES[0]  # Default to SF Pro

        # Measure title text to center it
        title_width, title_height = canvas.measure_text(
            title, font_family, TITLE_FONT_SIZE
        )

        # Center horizontally
        title_x = (width - title_width) / 2

        # Center vertically (baseline positioning)
        # Title bar center is TITLE_BAR_HEIGHT / 2
        # Position baseline (~0.7 of font height above center)
        title_baseline_y = (TITLE_BAR_HEIGHT + title_height * 0.7) / 2

        # Draw title with slightly muted foreground color
        # Use the background brightness to determine title color
        # For dark backgrounds, use light text; for light backgrounds, use dark text
        avg_brightness = (background.r + background.g + background.b) / 3
        if avg_brightness < 128:
            # Dark background - light title text (slightly muted)
            title_color = Color(200, 200, 200, 200)
        else:
            # Light background - dark title text (slightly muted)
            title_color = Color(80, 80, 80, 200)

        canvas.draw_text(
            x=title_x,
            y=title_baseline_y,
            text=title,
            font_family=font_family,
            font_size=TITLE_FONT_SIZE,
            color=title_color,
        )
