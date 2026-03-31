"""Configuration schema for codepicture.

RenderConfig is the Pydantic model for all rendering configuration.
It validates configuration values at load time with clear error messages.
"""

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..core.types import OutputFormat, WindowStyle


class HighlightStyleConfig(BaseModel):
    """Per-style color override from TOML config."""

    model_config = ConfigDict(extra="forbid")
    color: str | None = None

    @field_validator("color", mode="before")
    @classmethod
    def validate_style_color(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError(f"color must be a string, got {type(v).__name__}")
        if not re.match(r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", v):
            raise ValueError(f"Invalid color '{v}'. Use #RRGGBB or #RRGGBBAA")
        return v


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
    padding: Annotated[int, Field(ge=0, le=500)] = 20
    corner_radius: Annotated[int, Field(ge=0, le=50)] = 12
    window_width: Annotated[int | None, Field(ge=100, le=10000)] = None
    window_height: Annotated[int | None, Field(ge=50, le=10000)] = None
    show_line_numbers: bool = True
    line_number_offset: Annotated[int, Field(ge=0)] = 1

    # Window chrome
    window_controls: bool = True
    window_style: WindowStyle = WindowStyle.MACOS
    window_title: str | None = None

    # Shadow (on/off only - style is fixed macOS aesthetic per CONTEXT.md)
    shadow: bool = True

    # Background
    background_color: str | None = None  # hex color or None (use theme background)

    # Highlighting (legacy fields kept for backward compatibility)
    highlight_lines: list[str] | None = None  # e.g. ["3", "7-12", "15"]
    highlight_color: str | None = None  # e.g. "#FFE65040"

    # Named highlight styles (replaces highlight_lines for new usage)
    highlights: list[str] | None = None  # ["3-5:add", "10:remove"]
    highlight_styles: dict[str, HighlightStyleConfig] | None = None

    @field_validator("output_format", mode="before")
    @classmethod
    def convert_output_format(cls, v: str | OutputFormat) -> OutputFormat:
        """Convert string to OutputFormat enum."""
        if isinstance(v, OutputFormat):
            return v
        if isinstance(v, str):
            try:
                return OutputFormat(v.lower())
            except ValueError as err:
                allowed = [fmt.value for fmt in OutputFormat]
                raise ValueError(
                    f"Invalid output_format '{v}'. Must be one of: {', '.join(allowed)}"
                ) from err
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
            except ValueError as err:
                allowed = [style.value for style in WindowStyle]
                raise ValueError(
                    f"Invalid window_style '{v}'. Must be one of: {', '.join(allowed)}"
                ) from err
        raise ValueError(f"window_style must be a string, got {type(v).__name__}")

    @field_validator("background_color", mode="before")
    @classmethod
    def validate_background_color(cls, v: str | None) -> str | None:
        """Validate hex color format if not None."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError(
                f"background_color must be a string, got {type(v).__name__}"
            )
        # Allow #RGB, #RRGGBB, #RRGGBBAA formats
        if not re.match(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", v):
            raise ValueError(
                f"Invalid hex color '{v}'. Use #RGB, #RRGGBB, or #RRGGBBAA format"
            )
        return v

    @field_validator("highlight_color", mode="before")
    @classmethod
    def validate_highlight_color(cls, v: str | None) -> str | None:
        """Validate highlight color hex format (#RRGGBB or #RRGGBBAA only)."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError(
                f"highlight_color must be a string, got {type(v).__name__}"
            )
        # Only #RRGGBB and #RRGGBBAA (not #RGB -- 3-char hex is ambiguous for alpha)
        if not re.match(r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", v):
            raise ValueError(
                f"Invalid highlight color '{v}'. Use #RRGGBB or #RRGGBBAA format"
            )
        return v

    @field_validator("highlight_lines", mode="before")
    @classmethod
    def validate_highlight_lines(cls, v: list[str] | None) -> list[str] | None:
        """Validate highlight line specs (N or N-M format only)."""
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("highlight_lines must be a list of strings")
        for spec in v:
            s = str(spec)
            if not re.match(r"^\d+(-\d+)?$", s):
                raise ValueError(
                    f"Invalid line spec '{s}'. Use N or N-M format (e.g. '3' or '7-12')"
                )
        return [str(s) for s in v]

    @field_validator("highlights", mode="before")
    @classmethod
    def validate_highlights(cls, v: list[str] | None) -> list[str] | None:
        """Validate highlight specs (N, N-M, N:style, or N-M:style format)."""
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("highlights must be a list of strings")
        spec_re = re.compile(r"^\d+(?:-\d+)?(?::\w+)?$")
        for spec in v:
            s = str(spec).strip()
            if not spec_re.match(s):
                raise ValueError(
                    f"Invalid highlight spec '{s}'. "
                    "Use N, N-M, N:style, or N-M:style format"
                )
        return [str(s) for s in v]

    @field_validator("highlight_styles", mode="before")
    @classmethod
    def validate_highlight_styles(cls, v: dict | None) -> dict | None:
        """Validate highlight_styles keys are valid style names."""
        if v is None:
            return None
        valid_names = {"highlight", "add", "remove", "focus"}
        for key in v:
            if key not in valid_names:
                raise ValueError(
                    f"Unknown style '{key}'. "
                    f"Valid styles: {', '.join(sorted(valid_names))}"
                )
        return v

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_highlights(cls, data: dict) -> dict:
        """Auto-migrate highlight_lines/highlight_color to new format."""
        if not isinstance(data, dict):
            return data
        # Only migrate if new field not already set
        if data.get("highlights") is None and data.get("highlight_lines") is not None:
            data["highlights"] = [str(s) for s in data["highlight_lines"]]
        if (
            data.get("highlight_styles") is None
            and data.get("highlight_color") is not None
        ):
            data["highlight_styles"] = {
                "highlight": {"color": data["highlight_color"]}
            }
        return data
