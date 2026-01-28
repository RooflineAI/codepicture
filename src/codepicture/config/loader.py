"""Configuration loading and merging for codepicture.

Loads configuration from TOML files with precedence:
CLI > local config > global config > defaults
"""

import tomllib
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..errors import ConfigError
from .schema import RenderConfig


DEFAULT_GLOBAL_CONFIG_PATH = Path.home() / ".config" / "codepicture" / "config.toml"
DEFAULT_LOCAL_CONFIG_PATH = Path(".codepicture.toml")


def _load_toml(path: Path) -> dict[str, Any]:
    """Load TOML file, raising ConfigError on failure.

    Args:
        path: Path to TOML file

    Returns:
        Parsed TOML as dict

    Raises:
        ConfigError: If TOML parsing fails
    """
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        # Include file path and line/column info
        msg = f"Invalid TOML in {path}"
        if hasattr(e, "lineno") and e.lineno is not None:
            msg += f" at line {e.lineno}"
            if hasattr(e, "colno") and e.colno is not None:
                msg += f", column {e.colno}"
        msg += f": {e.msg}" if hasattr(e, "msg") else f": {e}"
        raise ConfigError(msg) from e


def load_config(
    global_path: Path | None = None,
    local_path: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
    use_defaults: bool = True,
) -> RenderConfig:
    """Load configuration with precedence: CLI > local > global > defaults.

    Args:
        global_path: Path to global config (default: ~/.config/codepicture/config.toml)
        local_path: Path to local config (default: .codepicture.toml)
        cli_overrides: Dict of CLI flag overrides (None values are filtered out)
        use_defaults: If True, use default paths when global_path/local_path are None

    Returns:
        Validated RenderConfig

    Raises:
        ConfigError: If TOML parsing fails or validation fails
    """
    # Resolve paths
    if use_defaults:
        if global_path is None:
            global_path = DEFAULT_GLOBAL_CONFIG_PATH
        if local_path is None:
            local_path = DEFAULT_LOCAL_CONFIG_PATH

    # Start with empty merged dict (defaults come from RenderConfig)
    merged: dict[str, Any] = {}

    # Load global config (lowest priority after defaults)
    if global_path and global_path.exists():
        merged.update(_load_toml(global_path))

    # Load local config (higher priority than global)
    if local_path and local_path.exists():
        merged.update(_load_toml(local_path))

    # Apply CLI overrides (highest priority)
    if cli_overrides:
        # Filter out None values (unset CLI flags)
        merged.update({k: v for k, v in cli_overrides.items() if v is not None})

    # Validate and return
    try:
        return RenderConfig.model_validate(merged)
    except ValidationError as e:
        # Convert Pydantic errors to ConfigError with details
        error_messages = []
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            error_messages.append(f"  {field}: {err['msg']}")
        msg = "Invalid configuration:\n" + "\n".join(error_messages)
        raise ConfigError(msg) from e
