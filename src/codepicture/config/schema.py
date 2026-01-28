"""Configuration schema for codepicture.

RenderConfig is the Pydantic model for all rendering configuration.
It validates configuration values at load time with clear error messages.
"""

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core.types import OutputFormat, WindowStyle


class RenderConfig(BaseModel):
    """Render configuration with validation.

    All fields have sensible defaults. Configuration can be loaded from:
    - Global config file (~/.config/codepicture/config.toml)
    - Local config file (.codepicture.toml)
    - CLI arguments (highest priority)

    Unknown fields are rejected (extra='forbid').
    """

    model_config = ConfigDict(
        extra="forbid",  # Reject unknown keys
        validate_default=True,  # Validate defaults too
        str_strip_whitespace=True,  # Clean string inputs
    )

    # Theme
    theme: str = "catppuccin-mocha"

    # Typography
    font_family: str = "JetBrains Mono"
    font_size: Annotated[int, Field(ge=6, le=72)] = 14
    tab_width: Annotated[int, Field(ge=1, le=8)] = 4
    line_height: Annotated[float, Field(ge=1.0, le=3.0)] = 1.4

    # Output
    output_format: OutputFormat = OutputFormat.PNG

    # Visual
    padding: Annotated[int, Field(ge=0, le=500)] = 40
    corner_radius: Annotated[int, Field(ge=0, le=50)] = 12
    show_line_numbers: bool = True
    line_number_offset: Annotated[int, Field(ge=0)] = 1

    # Window chrome
    window_controls: bool = True
    window_style: WindowStyle = WindowStyle.MACOS
    window_title: str | None = None

    # Shadow
    shadow: bool = True
    shadow_blur: Annotated[int, Field(ge=0, le=200)] = 50
    shadow_offset_x: Annotated[int, Field(ge=-100, le=100)] = 0
    shadow_offset_y: Annotated[int, Field(ge=-100, le=100)] = 0

    # Background
    background_color: str | None = None  # hex color or None (use theme background)

    @field_validator("output_format", mode="before")
    @classmethod
    def convert_output_format(cls, v: str | OutputFormat) -> OutputFormat:
        """Convert string to OutputFormat enum."""
        if isinstance(v, OutputFormat):
            return v
        if isinstance(v, str):
            try:
                return OutputFormat(v.lower())
            except ValueError:
                allowed = [fmt.value for fmt in OutputFormat]
                raise ValueError(
                    f"Invalid output_format '{v}'. Must be one of: {', '.join(allowed)}"
                )
        raise ValueError(f"output_format must be a string, got {type(v).__name__}")

    @field_validator("window_style", mode="before")
    @classmethod
    def convert_window_style(cls, v: str | WindowStyle) -> WindowStyle:
        """Convert string to WindowStyle enum."""
        if isinstance(v, WindowStyle):
            return v
        if isinstance(v, str):
            try:
                return WindowStyle(v.lower())
            except ValueError:
                allowed = [style.value for style in WindowStyle]
                raise ValueError(
                    f"Invalid window_style '{v}'. Must be one of: {', '.join(allowed)}"
                )
        raise ValueError(f"window_style must be a string, got {type(v).__name__}")

    @field_validator("background_color", mode="before")
    @classmethod
    def validate_background_color(cls, v: str | None) -> str | None:
        """Validate hex color format if not None."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError(f"background_color must be a string, got {type(v).__name__}")
        # Allow #RGB, #RRGGBB, #RRGGBBAA formats
        if not re.match(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", v):
            raise ValueError(
                f"Invalid hex color '{v}'. Use #RGB, #RRGGBB, or #RRGGBBAA format"
            )
        return v
