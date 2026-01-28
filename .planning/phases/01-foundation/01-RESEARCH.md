# Phase 1: Foundation - Research

**Researched:** 2026-01-28
**Domain:** Python configuration management, type protocols, error handling
**Confidence:** HIGH

## Summary

Phase 1 establishes the foundational abstractions for codepicture: configuration schema with TOML support, protocol definitions for core components, tab normalization, and error handling. The research confirms that Python's standard library (`tomllib`) combined with Pydantic v2 provides a robust, well-documented approach for type-safe configuration management.

The key insight is that Pydantic v2's `model_validate()` combined with manual TOML loading via `tomllib` offers the cleanest approach for this project's specific needs (flat config structure, strict validation, multi-source merging). While `pydantic-settings` exists, the project's decision to avoid environment variable overrides and use a simple flat TOML structure makes direct `tomllib` + Pydantic the simpler path.

For protocols, Python's `typing.Protocol` provides structural subtyping that matches the architecture's need for Canvas, Highlighter, Theme, and TextMeasurer abstractions. The key is using `@property` for read-only attributes and avoiding `@runtime_checkable` for performance.

**Primary recommendation:** Use `tomllib` for TOML parsing, Pydantic v2 BaseModel for validation, and `typing.Protocol` for component abstractions. Keep config flat at root level per user decision.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tomllib | stdlib (3.11+) | TOML parsing | Python standard library since 3.11; read-only but sufficient for config loading; no external dependency |
| pydantic | 2.12+ | Schema validation | Industry standard for Python data validation; clear error messages; type-safe; ConfigDict for customization |
| typing | stdlib | Protocol definitions | Built-in structural subtyping via Protocol class; mypy integration |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | 2.7+ | Settings management | Only if env var support needed (NOT recommended per user decision) |
| tomli-w | 1.0+ | TOML writing | Only if config file generation needed (NOT in scope for Phase 1) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tomllib | toml (pypi) | Legacy; tomllib is stdlib since 3.11 |
| tomllib | tomlkit | Only if need style-preserving edits; overkill for read-only |
| pydantic | dataclasses | No validation, no clear error messages |
| pydantic-settings | pydantic + tomllib | pydantic-settings adds env var complexity we explicitly don't want |

**Installation:**
```bash
# Pydantic is the only external dependency for Phase 1
uv add pydantic

# tomllib is stdlib (Python 3.11+), no install needed
# typing is stdlib, no install needed
```

## Architecture Patterns

### Recommended Project Structure
```
src/codepicture/
├── __init__.py           # Public API exports
├── errors.py             # Error hierarchy (ConfigError, etc.)
├── config/
│   ├── __init__.py       # ConfigLoader export
│   ├── schema.py         # Pydantic RenderConfig model
│   ├── loader.py         # TOML loading + merging logic
│   └── defaults.py       # Default values as constants
├── core/
│   ├── __init__.py
│   ├── types.py          # Color, Dimensions, Position, etc.
│   └── protocols.py      # Canvas, Highlighter, Theme, TextMeasurer
└── text/
    ├── __init__.py
    └── normalize.py      # Tab-to-space normalization
```

### Pattern 1: Flat Config with Pydantic Model

**What:** Single Pydantic BaseModel with all config fields at root level
**When to use:** When config is flat (per user decision)
**Example:**
```python
# Source: https://docs.pydantic.dev/latest/concepts/models/
from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated

class RenderConfig(BaseModel):
    model_config = ConfigDict(
        extra='forbid',           # Reject unknown keys
        validate_default=True,    # Validate defaults too
        str_strip_whitespace=True # Clean string inputs
    )

    # Typography
    theme: str = "catppuccin-mocha"
    font_family: str = "JetBrains Mono"
    font_size: Annotated[int, Field(ge=6, le=72)] = 14
    tab_width: Annotated[int, Field(ge=1, le=8)] = 4

    # Output
    output_format: str = "png"
```

### Pattern 2: Config Merging (Global + Local + CLI)

**What:** Load multiple sources, merge with precedence
**When to use:** Multi-layer configuration (global, project-local, CLI)
**Example:**
```python
# Source: Manual implementation (simpler than pydantic-settings for this use case)
import tomllib
from pathlib import Path
from typing import Any

def load_config(
    global_path: Path | None = None,
    local_path: Path | None = None,
    cli_overrides: dict[str, Any] | None = None
) -> RenderConfig:
    """Load config with precedence: CLI > local > global > defaults."""
    merged: dict[str, Any] = {}

    # Load global config
    if global_path and global_path.exists():
        with open(global_path, 'rb') as f:
            merged.update(tomllib.load(f))

    # Load local config (higher priority)
    if local_path and local_path.exists():
        with open(local_path, 'rb') as f:
            merged.update(tomllib.load(f))

    # Apply CLI overrides (highest priority)
    if cli_overrides:
        # Filter out None values (unset CLI flags)
        merged.update({k: v for k, v in cli_overrides.items() if v is not None})

    return RenderConfig.model_validate(merged)
```

### Pattern 3: Protocol Definition for Components

**What:** Use typing.Protocol for structural subtyping
**When to use:** Define interfaces for Canvas, Highlighter, Theme, TextMeasurer
**Example:**
```python
# Source: https://typing.python.org/en/latest/reference/protocols.html
from typing import Protocol

class TextMeasurer(Protocol):
    """Measures text dimensions without rendering."""

    def measure_text(
        self,
        text: str,
        font_family: str,
        font_size: int
    ) -> tuple[float, float]:
        """Return (width, height) in pixels."""
        ...

class Canvas(Protocol):
    """Abstract drawing surface."""

    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...

    def draw_rectangle(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        color: "Color",
        corner_radius: float = 0
    ) -> None: ...

    def draw_text(
        self,
        x: float,
        y: float,
        text: str,
        font_family: str,
        font_size: int,
        color: "Color"
    ) -> float:
        """Draw text, return width of rendered text."""
        ...
```

### Pattern 4: Custom Error Hierarchy

**What:** Single base exception with specific subclasses
**When to use:** Application-wide error handling
**Example:**
```python
# Source: https://docs.python.org/3/library/exceptions.html
class CodepictureError(Exception):
    """Base exception for all codepicture errors."""
    pass

class ConfigError(CodepictureError):
    """Configuration loading or validation failed."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)

class ThemeError(CodepictureError):
    """Theme loading or parsing failed."""
    pass

class RenderError(CodepictureError):
    """Rendering pipeline failed."""
    pass

class HighlightError(CodepictureError):
    """Syntax highlighting failed."""
    pass
```

### Anti-Patterns to Avoid

- **Using pydantic-settings when not needed:** User explicitly decided against env var overrides; don't add that complexity
- **Nested TOML config when flat is decided:** User wants `theme = "catppuccin"`, not `[theming]\nname = "catppuccin"`
- **@runtime_checkable on Protocols:** Performance overhead for isinstance() checks; use static type checking instead
- **Mutable Protocol attributes:** Use `@property` for read-only attributes to avoid invariance issues
- **Catching generic Exception:** Catch specific error types (ConfigError, etc.)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TOML parsing | Custom parser | tomllib (stdlib) | TOML 1.0 compliant; handles edge cases (multiline strings, dates, etc.) |
| Schema validation | Manual if/else checks | Pydantic BaseModel | Automatic type coercion; clear error messages; field constraints |
| Hex color parsing | Regex-only validation | Pydantic AfterValidator + Color class | Need to handle #RGB, #RRGGBB, #RRGGBBAA formats; validation + conversion |
| Path expansion | Manual ~ expansion | Path.expanduser() | Stdlib handles platform differences |
| Config file discovery | Manual file existence checks | Structured loader function | Centralize logic for global/local config paths |

**Key insight:** The stdlib + Pydantic combination handles all the edge cases (Unicode in TOML, type coercion, constraint validation). Custom validation code will miss edge cases.

## Common Pitfalls

### Pitfall 1: Opening TOML Files in Text Mode

**What goes wrong:** `tomllib.load()` requires binary mode; text mode raises TypeError
**Why it happens:** Habit from reading other file types
**How to avoid:** Always use `open(path, 'rb')` not `open(path, 'r')`
**Warning signs:** `TypeError: File must be opened in binary mode`

### Pitfall 2: Forgetting to Validate Defaults

**What goes wrong:** Default values bypass validation unless explicitly enabled
**Why it happens:** Pydantic optimizes by not validating defaults
**How to avoid:** Set `validate_default=True` in ConfigDict
**Warning signs:** Invalid default passes silently; caught only at runtime

### Pitfall 3: Swallowing ValidationError Details

**What goes wrong:** Generic "Invalid config" message loses actionable info
**Why it happens:** Catching ValidationError without accessing `.errors()`
**How to avoid:** Format each error with field location and expected type
**Warning signs:** Users can't fix their config without guessing

```python
# Good pattern:
from pydantic import ValidationError

try:
    config = RenderConfig.model_validate(data)
except ValidationError as e:
    for err in e.errors():
        field = '.'.join(str(loc) for loc in err['loc'])
        print(f"  {field}: {err['msg']}")
    raise ConfigError("Invalid configuration") from e
```

### Pitfall 4: Protocol Attribute Invariance

**What goes wrong:** Mutable Protocol attributes cause type checker complaints
**Why it happens:** Protocols are covariant for methods but invariant for attributes
**How to avoid:** Use `@property` for attributes that shouldn't be mutated
**Warning signs:** mypy errors about incompatible attribute types

### Pitfall 5: Missing Config File Not Handled

**What goes wrong:** FileNotFoundError when global config doesn't exist (normal case)
**Why it happens:** Not checking file existence before opening
**How to avoid:** Check `path.exists()` before `tomllib.load()`; missing global config is OK, missing explicitly-specified config is an error
**Warning signs:** Crash on first run before user creates config

### Pitfall 6: Tab Width Applied Inconsistently

**What goes wrong:** Tab normalization happens in wrong place; some code paths miss it
**Why it happens:** Normalizing in highlighter or renderer instead of at input
**How to avoid:** Normalize tabs immediately when code string is received (before any processing)
**Warning signs:** Inconsistent indentation in output; some tabs converted, some not

## Code Examples

### TOML Config Loading

```python
# Source: https://docs.python.org/3/library/tomllib.html
import tomllib
from pathlib import Path

def load_toml_config(path: Path) -> dict:
    """Load TOML file, raising ConfigError on parse failure."""
    try:
        with open(path, 'rb') as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(
            f"Invalid TOML at {path}:{e.lineno}:{e.colno}: {e.msg}"
        ) from e
```

### Pydantic Model with Constraints

```python
# Source: https://docs.pydantic.dev/latest/concepts/validators/
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Annotated
import re

class Color:
    """RGBA color value."""
    def __init__(self, r: int, g: int, b: int, a: int = 255):
        self.r, self.g, self.b, self.a = r, g, b, a

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        """Parse #RGB, #RRGGBB, or #RRGGBBAA format."""
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 3:
            hex_str = ''.join(c * 2 for c in hex_str)
        if len(hex_str) == 6:
            hex_str += 'ff'
        if len(hex_str) != 8:
            raise ValueError(f"Invalid hex color: #{hex_str}")
        return cls(
            int(hex_str[0:2], 16),
            int(hex_str[2:4], 16),
            int(hex_str[4:6], 16),
            int(hex_str[6:8], 16)
        )

class RenderConfig(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        validate_default=True,
        str_strip_whitespace=True
    )

    # Theme
    theme: str = "catppuccin-mocha"

    # Typography (per user decisions)
    font_family: str = "JetBrains Mono"
    font_size: Annotated[int, Field(ge=6, le=72)] = 14
    tab_width: Annotated[int, Field(ge=1, le=8)] = 4
    line_height: Annotated[float, Field(ge=1.0, le=3.0)] = 1.4

    # Output
    output_format: str = "png"

    # Visual
    padding: Annotated[int, Field(ge=0, le=500)] = 40
    corner_radius: Annotated[int, Field(ge=0, le=50)] = 12
    show_line_numbers: bool = True
    window_controls: bool = True
    shadow: bool = True

    # Colors (validated via field_validator)
    background_color: str | None = None

    @field_validator('background_color', mode='before')
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not re.match(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$', v):
            raise ValueError(
                f"Invalid hex color '{v}'. Use #RGB, #RRGGBB, or #RRGGBBAA format"
            )
        return v

    @field_validator('output_format')
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        allowed = {'png', 'svg', 'pdf'}
        if v.lower() not in allowed:
            raise ValueError(f"output_format must be one of: {', '.join(allowed)}")
        return v.lower()
```

### Tab Normalization

```python
def normalize_tabs(code: str, tab_width: int = 4) -> str:
    """Convert all tab characters to spaces.

    Args:
        code: Source code string
        tab_width: Number of spaces per tab (1-8)

    Returns:
        Code with tabs replaced by spaces
    """
    return code.replace('\t', ' ' * tab_width)
```

### Protocol Definition

```python
# Source: https://typing.python.org/en/latest/reference/protocols.html
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Color, TextStyle
    from pygments.token import _TokenType

class Highlighter(Protocol):
    """Syntax highlighting abstraction."""

    def highlight(self, code: str, language: str) -> list[list[tuple[str, "_TokenType"]]]:
        """Tokenize code by language.

        Args:
            code: Source code string
            language: Language identifier (e.g., 'python', 'rust')

        Returns:
            List of lines, each line is list of (text, token_type) tuples
        """
        ...

    def detect_language(self, code: str, filename: str | None = None) -> str:
        """Auto-detect language from content and/or filename."""
        ...

    def list_languages(self) -> list[str]:
        """Return available language identifiers."""
        ...

class Theme(Protocol):
    """Color and style definitions."""

    @property
    def name(self) -> str: ...

    @property
    def background(self) -> "Color": ...

    @property
    def foreground(self) -> "Color": ...

    def get_style(self, token_type: "_TokenType") -> "TextStyle":
        """Get text style for a Pygments token type."""
        ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| configparser (INI) | tomllib (TOML) | Python 3.11 (Oct 2022) | TOML is standard for Python config; richer types |
| Pydantic v1 Config class | Pydantic v2 ConfigDict | Pydantic 2.0 (Jun 2023) | Config class deprecated; use model_config |
| dataclasses + manual validation | Pydantic BaseModel | Industry trend | Type-safe validation with clear errors |
| ABC for interfaces | Protocol | Python 3.8+ (PEP 544) | Structural subtyping; no inheritance required |

**Deprecated/outdated:**
- `configparser`: Still works but TOML is the modern standard for Python
- `Pydantic Config class`: Deprecated in v2; use `model_config = ConfigDict(...)` instead
- `parse_raw()`, `parse_file()`: Deprecated; use `model_validate_json()` or load then `model_validate()`

## Open Questions

1. **Color class implementation details**
   - What we know: Need to handle #RGB, #RRGGBB, #RRGGBBAA formats
   - What's unclear: Whether to use a Pydantic custom type or separate class
   - Recommendation: Use a simple dataclass/NamedTuple for Color with `from_hex()` classmethod; keep separate from Pydantic model for cleaner separation

2. **Config file error messages**
   - What we know: Pydantic provides detailed errors; tomllib provides line/column
   - What's unclear: Exact format for user-facing error output
   - Recommendation: Format with file path, line number (if available), field name, and expected vs actual; this is "Claude's Discretion" per CONTEXT.md

## Sources

### Primary (HIGH confidence)
- [Python tomllib documentation](https://docs.python.org/3/library/tomllib.html) - stdlib TOML parsing
- [Pydantic Models documentation](https://docs.pydantic.dev/latest/concepts/models/) - BaseModel patterns
- [Pydantic Validators documentation](https://docs.pydantic.dev/latest/concepts/validators/) - field_validator, Annotated
- [Pydantic Validation Errors](https://docs.pydantic.dev/latest/errors/validation_errors/) - error structure
- [Python Protocols documentation](https://typing.python.org/en/latest/reference/protocols.html) - structural subtyping
- [PEP 544](https://peps.python.org/pep-0544/) - Protocol specification

### Secondary (MEDIUM confidence)
- [Pydantic Settings Management](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - multi-source config patterns (not using directly, but informed approach)
- [Real Python: Python Protocol](https://realpython.com/python-protocol/) - Protocol best practices

### Tertiary (LOW confidence)
- WebSearch results on exception hierarchy best practices - general patterns, not library-specific

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries are stdlib or well-documented (Pydantic official docs)
- Architecture: HIGH - Patterns from official documentation
- Pitfalls: HIGH - Common issues documented in official sources

**Research date:** 2026-01-28
**Valid until:** 60 days (stable libraries; Pydantic v2 is mature)
