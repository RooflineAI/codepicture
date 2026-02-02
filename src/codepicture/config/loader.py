"""Configuration loading for codepicture.

Config file search: ./codepicture.toml -> ~/.config/codepicture/config.toml
First found wins (no merge between files).
CLI overrides are applied on top of the loaded config.
"""

import tomllib
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..errors import ConfigError
from .schema import RenderConfig

DEFAULT_GLOBAL_CONFIG_PATH = Path.home() / ".config" / "codepicture" / "config.toml"
DEFAULT_LOCAL_CONFIG_PATH = Path("codepicture.toml")


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
    config_path: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> RenderConfig:
    """Load configuration from file with CLI overrides.

    Config file search (first found wins, no merge):
      1. ./codepicture.toml (local config)
      2. ~/.config/codepicture/config.toml (global config)

    If config_path is provided, ONLY that file is used (skips search).
    CLI overrides are always applied on top of loaded config.

    Args:
        config_path: Explicit path to config file (skips default search)
        cli_overrides: Dict of CLI flag overrides (None values are filtered out)

    Returns:
        Validated RenderConfig

    Raises:
        ConfigError: If TOML parsing fails or validation fails
    """
    # Start with empty dict (defaults come from RenderConfig)
    config_data: dict[str, Any] = {}

    if config_path is not None:
        # Explicit config path provided - use only this file
        if config_path.exists():
            config_data = _load_toml(config_path)
        # If explicit path doesn't exist, use defaults (no error)
    else:
        # Search for config file: local first, then global
        # Local config replaces global entirely (no merge)
        search_paths = [
            DEFAULT_LOCAL_CONFIG_PATH,
            DEFAULT_GLOBAL_CONFIG_PATH,
        ]
        for path in search_paths:
            if path.exists():
                config_data = _load_toml(path)
                break  # First found wins - stop searching

    # Apply CLI overrides (highest priority)
    if cli_overrides:
        # Filter out None values (unset CLI flags)
        config_data.update({k: v for k, v in cli_overrides.items() if v is not None})

    # Validate and return
    try:
        return RenderConfig.model_validate(config_data)
    except ValidationError as e:
        # Convert Pydantic errors to ConfigError with details
        error_messages = []
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            error_messages.append(f"  {field}: {err['msg']}")
        msg = "Invalid configuration:\n" + "\n".join(error_messages)
        raise ConfigError(msg) from e
