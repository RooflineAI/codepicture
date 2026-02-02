# Silicon Python Rewrite - Architecture Plan

## Overview

A Python rewrite of Silicon focused on clean architecture, extensibility, and multiple output formats (PNG, SVG, PDF).

**Tools:** UV (environment), Typer (CLI), Cairo/Pango (rendering), Pygments (highlighting), TOML (config), Pydantic (validation)

## Design Principles

- **Loose coupling** - Components communicate through protocols (interfaces)
- **Dependency injection** - All dependencies passed in, not instantiated internally
- **GUI-ready** - Core logic separated from CLI via application facade
- **Fail fast** - Validate configuration at load time, not render time
- **Pythonic errors** - Use typed exceptions, not Result wrappers

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACES                             │
├────────────────────────────────┬────────────────────────────────────────┤
│           CLI (Typer)          │           Future GUI                   │
│                                │                                        │
│  - Parses arguments            │  - Renders preview                     │
│  - Reads stdin/files/clipboard │  - Handles user interaction            │
│  - Writes output/clipboard     │  - Shows progress                      │
└───────────────┬────────────────┴──────────────────┬─────────────────────┘
                │                                    │
                ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION FACADE                             │
│                              SiliconApp                                  │
│                                                                          │
│  - Unified API for CLI and GUI                                          │
│  - Manages component lifecycle                                          │
│  - Merges configuration layers                                          │
│  - Progress callbacks for GUI                                           │
└───────────────┬─────────────────────────────────────────────────────────┘
                │
                │ uses
                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              CORE LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │  Formatter  │───▶│LayoutEngine│───▶│   Canvas    │                 │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                 │
│         │                  │                   │                        │
│         │ uses             │ uses              │ implements             │
│         ▼                  ▼                   ▼                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │ Highlighter │    │TextMeasurer │    │CairoCanvas  │                 │
│  └──────┬──────┘    │  (protocol) │    │(PNG/SVG/PDF)│                 │
│         │           └─────────────┘    └─────────────┘                 │
│         │ implements       △                                            │
│         ▼                  │ implements                                 │
│  ┌─────────────┐           │           ┌─────────────┐                 │
│  │  Pygments   │           │           │    Theme    │                 │
│  │ Highlighter │    CairoCanvas        │   Loader    │                 │
│  └─────────────┘    .create_measurer() └─────────────┘                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                │
                │ configured by
                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           CONFIGURATION                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │ CLI Options │───▶│ConfigLoader │◀───│  TOML File  │                 │
│  └─────────────┘    └──────┬──────┘    └─────────────┘                 │
│                            │                                            │
│                            ▼                                            │
│                     ┌─────────────┐                                     │
│                     │RenderConfig │  (Pydantic validated)              │
│                     └─────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Error Handling

### Error Hierarchy

Four error types cover all failure modes:

```python
class SiliconError(Exception):
    """Base error for all Silicon operations."""
    pass

class ConfigError(SiliconError):
    """Configuration validation or loading failed.

    Examples: invalid hex color, font_size out of range,
    missing config file, malformed TOML.
    """
    pass

class HighlightError(SiliconError):
    """Syntax highlighting failed.

    Examples: unknown language, failed language detection,
    custom lexer failed to load.
    """
    pass

class RenderError(SiliconError):
    """Rendering pipeline failed.

    Examples: font not found, canvas creation failed,
    file write failed, clipboard unavailable.
    """
    pass

class ThemeError(SiliconError):
    """Theme loading failed.

    Examples: unknown theme name, malformed theme file.
    """
    pass
```

### Error Handling Strategy

1. **Use exceptions idiomatically** - No Result wrappers, just raise and catch
2. **Fail fast on config** - Validation errors raised at config load time
3. **Graceful degradation for fonts** - Fall back to system monospace; log warning
4. **Specific messages** - Error message contains details (e.g., "Unknown theme 'foo', available: dracula, monokai, ...")

---

## Class Diagrams

### Core Protocols (Interfaces)

```
┌─────────────────────────────────────┐
│         <<protocol>>                │
│         TextMeasurer                │
├─────────────────────────────────────┤
│ + measure_text(text, font_family,   │
│     font_size) -> tuple[float,float]│
└─────────────────────────────────────┘
                 △
                 │ implements
                 │
          CairoCanvas
          (via class method)


┌─────────────────────────────────────┐
│         <<protocol>>                │
│          Highlighter                │
├─────────────────────────────────────┤
│ + highlight(code, lang) -> list[Line]│
│ + detect_language(code, filename)   │
│     -> str                          │
│ + list_languages() -> list[str]     │
│ + add_lexer_directory(path)         │
└─────────────────────────────────────┘
                 △
                 │ implements
                 │
┌─────────────────────────────────────┐
│       PygmentsHighlighter           │
├─────────────────────────────────────┤
│ - custom_lexers_paths: list[Path]   │
├─────────────────────────────────────┤
│ + highlight(code, lang) -> list[Line]│
│   raises HighlightError             │
│ + detect_language(code, filename)   │
│   -> str, raises HighlightError     │
│ + list_languages() -> list[str]     │
│ + add_lexer_directory(path)         │
│   raises HighlightError             │
└─────────────────────────────────────┘


┌─────────────────────────────────────┐
│         <<protocol>>                │
│            Canvas                   │
├─────────────────────────────────────┤
│ + dimensions: Dimensions            │
│ + format: OutputFormat              │
├─────────────────────────────────────┤
│ + draw_rectangle(x, y, w, h, color, │
│     corner_radius, fill)            │
│ + draw_circle(x, y, radius, color)  │
│ + draw_text(x, y, text, font_family,│
│     font_size, style) -> float      │
│ + measure_text(text, font_family,   │
│     font_size) -> tuple[float,float]│
│ + push_clip(x, y, w, h)             │
│ + pop_clip()                        │
│ + apply_shadow(blur_radius,         │
│     offset_x, offset_y, color)      │
│ + save() -> bytes                   │
│ + save_to_file(path)                │
└─────────────────────────────────────┘
                 △
                 │ implements
                 │
┌─────────────────────────────────────┐
│          CairoCanvas                │
├─────────────────────────────────────┤
│ - surface: cairo.Surface            │
│ - ctx: cairo.Context                │
│ - _format: OutputFormat             │
├─────────────────────────────────────┤
│ + create(width, height, format)     │
│   -> CairoCanvas  [class method]    │
│ + create_measurer()                 │
│   -> TextMeasurer [class method]    │
│ + draw_rectangle(...)               │
│ + draw_text(...) -> float           │
│ + apply_shadow(...)                 │
│ + save() -> bytes                   │
└─────────────────────────────────────┘


┌─────────────────────────────────────┐
│         <<protocol>>                │
│             Theme                   │
├─────────────────────────────────────┤
│ + name: str                         │
│ + background: Color                 │
│ + foreground: Color                 │
│ + line_number_fg: Color             │
│ + line_number_bg: Color             │
│ + highlight_bg: Color               │
│ + gutter_bg: Color                  │
├─────────────────────────────────────┤
│ + get_style(token: TokenType)       │
│   -> TextStyle                      │
└─────────────────────────────────────┘
                 △
                 │ implements
                 │
┌─────────────────────────────────────┐
│         PygmentsTheme               │
├─────────────────────────────────────┤
│ - pygments_style: Style             │
│ - overrides: dict[str, Color]       │
├─────────────────────────────────────┤
│ + get_style(token: TokenType)       │
│   -> TextStyle                      │
│ + from_name(name: str)              │
│   -> PygmentsTheme [class method]   │
│   raises ThemeError                 │
│ + from_file(path: Path)             │
│   -> PygmentsTheme [class method]   │
│   raises ThemeError                 │
└─────────────────────────────────────┘
```

### Core Classes

```
┌─────────────────────────────────────┐
│            SiliconApp               │
│         (Application Facade)        │
├─────────────────────────────────────┤
│ - highlighter: Highlighter          │
│ - theme_loader: ThemeLoader         │
│ - base_config: RenderConfig         │
│ - progress_callback: Callable | None│
│ - _cancelled: bool                  │
├─────────────────────────────────────┤
│ + render(code, lang, **overrides)   │
│   -> RenderResult                   │
│   raises SiliconError               │
│ + render_file(path, **overrides)    │
│   -> RenderResult                   │
│   raises SiliconError               │
│ + list_languages() -> list[str]     │
│ + list_themes() -> list[str]        │
│ + add_lexer_directory(path)         │
│   raises HighlightError             │
│ + on_progress(callback)             │
│ + cancel()                          │
└─────────────────────────────────────┘
        │
        │ creates & uses
        ▼
┌─────────────────────────────────────┐
│            Formatter                │
│      (Orchestrates rendering)       │
├─────────────────────────────────────┤
│ - highlighter: Highlighter          │
│ - theme: Theme                      │
├─────────────────────────────────────┤
│ + format(code, lang, config)        │
│   -> RenderResult                   │
│   raises SiliconError               │
│ - _calculate_dimensions(lines,      │
│     config, measurer) -> Dimensions │
│ - _render_background(canvas)        │
│ - _render_window_controls(canvas)   │
│ - _render_line_highlights(canvas)   │
│ - _render_line_numbers(canvas)      │
│ - _render_code(canvas, lines)       │
└─────────────────────────────────────┘
        │
        │ uses
        ▼
┌─────────────────────────────────────┐
│          LayoutEngine               │
│   (Calculates positions & sizes)    │
├─────────────────────────────────────┤
│ - measurer: TextMeasurer            │
│ - config: RenderConfig              │
├─────────────────────────────────────┤
│ + calculate_metrics(lines)          │
│   -> LayoutMetrics                  │
│ + get_line_position(index)          │
│   -> Position                       │
│ + get_line_number_position(index)   │
│   -> Position                       │
│ + get_code_area() -> Rect           │
│ + get_gutter_area() -> Rect         │
└─────────────────────────────────────┘
```

### Data Classes

```
┌─────────────────────────────────────┐
│          <<enum>>                   │
│         OutputFormat                │
├─────────────────────────────────────┤
│ PNG = "png"                         │
│ SVG = "svg"                         │
│ PDF = "pdf"                         │
└─────────────────────────────────────┘


┌─────────────────────────────────────┐
│          <<enum>>                   │
│         WindowStyle                 │
├─────────────────────────────────────┤
│ MACOS = "macos"                     │
│ WINDOWS = "windows"                 │
│ LINUX = "linux"                     │
│ NONE = "none"                       │
└─────────────────────────────────────┘


┌───────────────────────────────────────────────────┐
│                  RenderConfig                     │
│             (All rendering options)               │
│          Validated with Pydantic                  │
├───────────────────────────────────────────────────┤
│ # Dimensions                                      │
│ + width: int | None = None      # auto if None   │
│ + height: int | None = None     # auto if None   │
│ + scale: float = 1.0            # 0.1 - 10.0     │
│ + padding: int = 40             # 0 - 500        │
│                                                   │
│ # Typography                                      │
│ + font_family: str = "monospace"                 │
│ + font_size: int = 14           # 6 - 72         │
│ + line_height: float = 1.4      # 1.0 - 3.0      │
│ + tab_width: int = 4            # 1 - 8          │
│                                                   │
│ # Line numbers                                    │
│ + show_line_numbers: bool = True                 │
│ + line_number_offset: int = 1   # >= 0           │
│ + line_number_pad: int = 2      # 0 - 10         │
│                                                   │
│ # Line highlighting                               │
│ + highlight_lines: list[int] = []                │
│                                                   │
│ # Window chrome                                   │
│ + window_controls: bool = True                   │
│ + window_title: str | None = None                │
│ + window_style: WindowStyle = MACOS              │
│                                                   │
│ # Effects                                         │
│ + shadow: bool = True                            │
│ + shadow_blur: int = 50         # 0 - 200        │
│ + shadow_offset_x: int = 0      # -100 - 100     │
│ + shadow_offset_y: int = 0      # -100 - 100     │
│ + shadow_color: Color = Color(0,0,0,100)         │
│ + corner_radius: int = 12       # 0 - 50         │
│                                                   │
│ # Background                                      │
│ + background_color: Color | None = None          │
│ + background_image: Path | None = None           │
│                                                   │
│ # Theme                                           │
│ + theme: str = "dracula"                         │
│                                                   │
│ # Output                                          │
│ + output_format: OutputFormat = PNG              │
├───────────────────────────────────────────────────┤
│ + merge(**overrides) -> RenderConfig             │
└───────────────────────────────────────────────────┘


# Re-exported from pygments.token
TokenType = type[Token]  # e.g., Token.Keyword, Token.String


┌───────────────┐  ┌───────────────────┐  ┌───────────────┐
│     Color     │  │       Token       │  │   TextStyle   │
├───────────────┤  ├───────────────────┤  ├───────────────┤
│ + r: int 0-255│  │ + text: str       │  │ + color: Color│
│ + g: int 0-255│  │ + token_type:     │  │ + bold: bool  │
│ + b: int 0-255│  │     TokenType     │  │ + italic: bool│
│ + a: int 0-255│  └───────────────────┘  │ + underline:  │
├───────────────┤                         │     bool      │
│ + from_hex(s) │  Line = list[Token]     └───────────────┘
│   -> Color    │
│ + to_hex()    │
│   -> str      │  ┌───────────────┐  ┌───────────────┐
└───────────────┘  │  Dimensions   │  │   Position    │
                   ├───────────────┤  ├───────────────┤
                   │ + width: int  │  │ + x: float    │
                   │ + height: int │  │ + y: float    │
                   └───────────────┘  └───────────────┘


┌───────────────────────────────────────┐
│              Rect                     │
├───────────────────────────────────────┤
│ + x: float                            │
│ + y: float                            │
│ + width: float                        │
│ + height: float                       │
└───────────────────────────────────────┘


┌─────────────────────────────────────┐
│          LayoutMetrics              │
├─────────────────────────────────────┤
│ + total_width: int                  │
│ + total_height: int                 │
│ + content_width: int                │
│ + content_height: int               │
│ + gutter_width: int                 │
│ + line_height_px: float             │
│ + char_width: float                 │
│ + code_start_x: float               │
│ + code_start_y: float               │
└─────────────────────────────────────┘


┌─────────────────────────────────────┐
│          RenderResult               │
├─────────────────────────────────────┤
│ + data: bytes                       │
│ + format: OutputFormat              │
│ + width: int                        │
│ + height: int                       │
├─────────────────────────────────────┤
│ + save(path: Path)                  │
│   raises RenderError                │
│ + to_clipboard()                    │
│   raises RenderError                │
└─────────────────────────────────────┘
```

---

## Data Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   Code   │────▶│Highlighter────▶│  Tokens  │────▶│ Formatter│
│  (str)   │     │          │     │(list[Line])    │          │
└──────────┘     └──────────┘     └──────────┘     └────┬─────┘
                                                        │
    ┌───────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│ CairoCanvas.create_measurer()
└────────────┬─────────────┘
             │
             ▼
      ┌─────────────┐
      │LayoutEngine │
      │             │
      │ Calculates: │
      │ - positions │
      │ - sizes     │
      │ - metrics   │
      └──────┬──────┘
             │ LayoutMetrics
             │ (dimensions now known)
             ▼
┌──────────────────────────┐
│ CairoCanvas.create(w, h, fmt)
└────────────┬─────────────┘
             │
             ▼
      ┌─────────────┐     ┌─────────────┐
      │   Canvas    │────▶│   Output    │
      │             │     │             │
      │ Draws:      │     │ - PNG bytes │
      │ - background│     │ - SVG bytes │
      │ - controls  │     │ - PDF bytes │
      │ - text      │     │             │
      │ - effects   │     └─────────────┘
      └─────────────┘
```

---

## Component Responsibilities

### SiliconApp (Facade)

**Purpose:** Single entry point for all rendering operations

**Responsibilities:**
- Creates and wires together all components
- Loads configuration from TOML files
- Merges CLI options with file config
- Provides clean API for both CLI and future GUI
- Manages progress callbacks for GUI responsiveness
- Handles cancellation for long-running renders

**Thread Safety:** Not thread-safe. Create one instance per thread, or wrap calls with locks.

---

### Formatter

**Purpose:** Orchestrates the rendering pipeline

**Responsibilities:**
- Coordinates highlighting, layout, and drawing
- Delegates each rendering step to appropriate component
- Uses `CairoCanvas.create_measurer()` for layout, then `CairoCanvas.create()` with known dimensions

---

### LayoutEngine

**Purpose:** Calculate positions and sizes

**Responsibilities:**
- Measures text to determine dimensions via TextMeasurer
- Calculates line positions, number widths
- Handles auto-sizing vs explicit dimensions
- Pure calculations, no rendering

---

### TextMeasurer (Protocol)

**Purpose:** Measure text dimensions without creating a full canvas

**Implementation:** `CairoCanvas.create_measurer()` returns a lightweight Pango-based measurer.

---

### Canvas (Protocol)

**Purpose:** Abstract drawing surface

**Responsibilities:**
- Draw primitives (rect, circle, text)
- Measure text without drawing
- Apply effects (shadow with abstract parameters)
- Serialize to output format

**Shadow Abstraction:** `apply_shadow(blur_radius, offset_x, offset_y, color)` is format-agnostic. CairoCanvas handles implementation details internally.

---

### CairoCanvas

**Purpose:** Cairo-based implementation of Canvas

**Class Methods:**
- `create(width, height, format)` - Create a canvas with the given dimensions
- `create_measurer()` - Create a lightweight text measurer (no full surface)

**Responsibilities:**
- Creates appropriate surface (ImageSurface, SVGSurface, PDFSurface)
- Uses Pango for text rendering (font fallbacks, ligatures)
- Implements shadows per format internally

**Thread Safety:** Not thread-safe. Each thread needs its own instance.

---

### Highlighter (Protocol)

**Purpose:** Syntax highlighting abstraction

**Responsibilities:**
- Convert code string to styled tokens with Pygments TokenTypes
- Auto-detect language from content/filename
- Support custom lexer loading

---

### Theme (Protocol)

**Purpose:** Color and style definitions

**Responsibilities:**
- Map Pygments TokenTypes to TextStyles
- Provide UI colors (background, line numbers, gutter, highlights)

---

### ThemeLoader

**Purpose:** Load themes from various sources

**Theme Sources (in precedence order):**
1. User theme directory: `~/.config/silicon/themes/*.toml`
2. Built-in Pygments styles: `dracula`, `monokai`, `one-dark`, etc.

---

### ConfigLoader

**Purpose:** Load and merge configuration

**Responsibilities:**
- Parse TOML config files
- Search default paths (~/.config/silicon/config.toml)
- Convert TOML structure to RenderConfig
- Pydantic validates at load time

---

## Configuration

### Configuration Layers

```
Priority (lowest to highest):

┌─────────────────────────────────┐
│     Built-in Defaults           │  RenderConfig defaults
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│     TOML Config File            │  ~/.config/silicon/config.toml
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│     CLI Arguments               │  --width, --theme, etc.
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│     Pydantic Validation         │  Raises ConfigError if invalid
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│     Final RenderConfig          │  Used for rendering
└─────────────────────────────────┘
```

### Validation Rules

All validation via Pydantic validators:

| Field | Constraint |
|-------|------------|
| `scale` | 0.1 - 10.0 |
| `padding` | 0 - 500 |
| `font_size` | 6 - 72 |
| `line_height` | 1.0 - 3.0 |
| `tab_width` | 1 - 8 |
| `shadow_blur` | 0 - 200 |
| `shadow_offset_x/y` | -100 - 100 |
| `corner_radius` | 0 - 50 |
| `background_color` | valid hex/rgba |
| `background_image` | file exists (if set) |
| `highlight_lines` | all positive |

### TOML Config Structure

```toml
# ~/.config/silicon/config.toml

[dimensions]
width = 800              # optional, auto if omitted
height = 600             # optional, auto if omitted
scale = 2.0
padding = 40

[typography]
font_family = "JetBrains Mono, Fira Code, monospace"
font_size = 14
line_height = 1.4
tab_width = 4

[line_numbers]
enabled = true
offset = 1
padding = 2

[highlighting]
lines = [1, 5, "10-15"]  # individual lines or ranges

[window]
controls = true
style = "macos"          # macos | windows | linux | none
title = ""

[effects]
shadow = true
shadow_blur = 50
shadow_offset_x = 0
shadow_offset_y = 0
shadow_color = "#00000064"
corner_radius = 12

[background]
color = "#282a36"
# image = "/path/to/bg.png"  # alternative

[theme]
name = "dracula"

[output]
format = "png"           # png | svg | pdf
```

---

## Concurrency Model

### Threading

- **Core components are NOT thread-safe**
- CairoCanvas uses thread-local Cairo contexts
- Pygments is thread-safe for reading, not for custom lexer registration

### Recommended Usage

**CLI:** Single-threaded, synchronous

**GUI:**
```python
import asyncio

async def render_preview(code: str):
    app = SiliconApp()
    result = await asyncio.to_thread(app.render, code, "python")
    return result
```

### Cancellation

```python
app = SiliconApp()

# From another thread/task:
app.cancel()  # Sets internal flag, checked during render
```

### Progress Callbacks

```python
def on_progress(stage: str, percent: float):
    """
    stage: "highlighting" | "layout" | "rendering" | "effects"
    percent: 0.0 - 1.0
    """
    update_progress_bar(percent)

app.on_progress(on_progress)
```

---

## Project Structure

```
silicon-py/
├── pyproject.toml
├── src/silicon/
│   ├── __init__.py         # Public API exports
│   ├── app.py              # SiliconApp facade
│   ├── errors.py           # SiliconError, ConfigError, etc.
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py         # Typer CLI
│   ├── core/
│   │   ├── __init__.py
│   │   ├── types.py        # Color, Token, Dimensions, etc.
│   │   ├── protocols.py    # Highlighter, Canvas, Theme, TextMeasurer
│   │   ├── formatter.py
│   │   └── layout.py
│   ├── highlight/
│   │   ├── __init__.py
│   │   └── pygments_impl.py
│   ├── render/
│   │   ├── __init__.py
│   │   └── cairo_canvas.py
│   ├── theme/
│   │   ├── __init__.py
│   │   ├── pygments_theme.py
│   │   └── loader.py
│   └── config/
│       ├── __init__.py
│       ├── loader.py
│       └── schema.py       # Pydantic RenderConfig
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_color.py
    │   ├── test_config.py
    │   ├── test_layout.py
    │   └── test_highlighter.py
    ├── integration/
    │   ├── test_render_pipeline.py
    │   └── test_config_merge.py
    └── visual/
        ├── baselines/
        └── test_visual_regression.py
```

---

## Testing Strategy

### Unit Tests

- **LayoutEngine:** Mock `TextMeasurer` with `unittest.mock`, verify position calculations
- **ConfigLoader:** Parse various TOML structures, verify validation errors
- **Color:** Hex parsing, roundtrips
- **Theme:** Token type to style mapping

### Integration Tests

- **Full render pipeline:** Code → PNG/SVG bytes, verify non-empty output
- **Config merging:** TOML + CLI → final config with correct precedence
- **Error propagation:** Verify errors bubble up correctly

### Visual Regression Tests

- Render known inputs, compare to baseline images
- Use pixel-diff with configurable threshold
- Store baselines in git

### Mocking Example

```python
from unittest.mock import Mock, call

def test_formatter_draws_line_numbers():
    canvas = Mock(spec=Canvas)
    canvas.measure_text.return_value = (100.0, 20.0)

    formatter._render_line_numbers(canvas, lines=["a", "b", "c"], config)

    text_calls = [c for c in canvas.draw_text.call_args_list]
    assert len(text_calls) == 3
```

---

## Dependencies

```toml
[project]
name = "silicon-py"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pygments>=2.17",
    "pycairo>=1.25",
    "PyGObject>=3.46",
    "typer[all]>=0.9",
    "pydantic>=2.5",
    "pyperclip>=1.8",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "ruff>=0.1",
    "mypy>=1.7",
    "pillow>=10.0",  # Image comparison for visual tests
]
```

---

## CLI Interface

```bash
silicon [OPTIONS] [INPUT_FILE]

Arguments:
  INPUT_FILE              Source file (omit for stdin or clipboard)

Options:
  -o, --output PATH       Output file path
  -l, --language TEXT     Language (auto-detect if omitted)
  -t, --theme TEXT        Theme name [default: dracula]
  --list-themes           List available themes
  --list-languages        List available languages

  # I/O
  --from-clipboard        Read code from clipboard
  --to-clipboard          Copy output to clipboard
  -f, --format TEXT       Output format: png|svg|pdf [default: png]

  # Dimensions
  --width INT             Image width (auto if omitted)
  --height INT            Image height (auto if omitted)
  --scale FLOAT           Scale factor [default: 1.0]
  --padding INT           Padding [default: 40]

  # Typography
  --font TEXT             Font family [default: monospace]
  --font-size INT         Font size [default: 14]
  --line-height FLOAT     Line height [default: 1.4]
  --tab-width INT         Tab width [default: 4]

  # Line numbers
  --line-numbers/--no-line-numbers  [default: True]
  --line-offset INT       Starting line number [default: 1]
  --highlight-lines TEXT  Lines to highlight (e.g., "1,5,10-15")

  # Window
  --window-controls/--no-window-controls  [default: True]
  --window-title TEXT     Window title
  --window-style TEXT     macos|windows|linux|none [default: macos]

  # Effects
  --shadow/--no-shadow    [default: True]
  --shadow-blur INT       [default: 50]
  --corner-radius INT     [default: 12]

  # Background
  --background TEXT       Background color (hex)
  --background-image PATH

  # Config
  -c, --config PATH       Config file path

  --help
  --version
```

---

## GUI Readiness

1. **SiliconApp facade** - GUI uses same API as CLI
2. **Progress callbacks** - `app.on_progress(fn)` for progress bars
3. **Cancellation** - `app.cancel()` for responsive UI
4. **No CLI imports in core** - Core doesn't depend on Typer
5. **Async-friendly** - Wrap in `asyncio.to_thread()`
6. **Typed errors** - GUI can show specific error messages

---

## Future Considerations

### Streaming for Large Files

Current architecture processes entire files in memory. For files >10,000 lines:

1. **Chunked highlighting** - Process N lines at a time
2. **Streaming layout** - Calculate incrementally
3. **Tiled rendering** - Render canvas sections separately

The architecture supports this:
- `Highlighter.highlight()` could accept an iterator
- `LayoutEngine` could process line batches

### Additional Backends

Canvas protocol enables future backends:
- **SkiaCanvas** - Better performance
- **BrowserCanvas** - Web/WASM deployment
- **ANSICanvas** - Terminal preview

---

## Migration Phases

| Phase | Tasks |
|-------|-------|
| 1 | Project setup, types, protocols, errors, Pydantic config |
| 2 | Highlighter + themes |
| 3 | Layout engine + text measurement |
| 4 | Cairo canvas (PNG, SVG, PDF) |
| 5 | Formatter + SiliconApp facade |
| 6 | CLI + tests |
