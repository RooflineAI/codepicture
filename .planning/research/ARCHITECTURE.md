# Architecture Research

**Domain:** Code screenshot/code image generation tools
**Researched:** 2026-01-28
**Confidence:** HIGH

## Standard Architecture

### System Overview

Code-to-image tools consistently follow a layered pipeline architecture with clear component boundaries:

```
+-----------------------------------------------------------------------+
|                         INPUT LAYER                                    |
|  +----------------+  +----------------+  +----------------+           |
|  |   File Input   |  | Stdin/Pipe     |  |   Clipboard    |           |
|  +-------+--------+  +-------+--------+  +-------+--------+           |
|          |                   |                   |                    |
+----------+-------------------+-------------------+--------------------+
           |                   |                   |
           v                   v                   v
+-----------------------------------------------------------------------+
|                      ORCHESTRATION LAYER                               |
|                                                                        |
|  +------------------------------------------------------------------+ |
|  |                     Application Facade                            | |
|  |  - Unified API (CLI and GUI share this)                          | |
|  |  - Configuration merging                                          | |
|  |  - Component lifecycle management                                 | |
|  +------------------------------------------------------------------+ |
|                               |                                        |
+-------------------------------+----------------------------------------+
                                |
                                v
+-----------------------------------------------------------------------+
|                       PROCESSING LAYER                                 |
|                                                                        |
|  +------------------+    +------------------+    +------------------+  |
|  |    Highlighter   |    |  Layout Engine   |    |     Renderer     |  |
|  |                  |    |                  |    |                  |  |
|  | Code -> Tokens   |    | Tokens -> Layout |    | Layout -> Image  |  |
|  +--------+---------+    +--------+---------+    +--------+---------+  |
|           |                       |                       |           |
|           v                       v                       v           |
|  +------------------+    +------------------+    +------------------+  |
|  |  Theme/Styles    |    |  Text Measurer   |    | Canvas Protocol  |  |
|  +------------------+    +------------------+    +------------------+  |
|                                                                        |
+-----------------------------------------------------------------------+
                                |
                                v
+-----------------------------------------------------------------------+
|                        OUTPUT LAYER                                    |
|                                                                        |
|  +----------------+  +----------------+  +----------------+            |
|  |      PNG       |  |      SVG       |  |      PDF       |            |
|  | (Raster)       |  | (Vector)       |  | (Document)     |            |
|  +----------------+  +----------------+  +----------------+            |
|                                                                        |
+-----------------------------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Application Facade** | Single entry point for all operations; configuration merging; progress callbacks | SiliconApp class wrapping all subsystems |
| **Highlighter** | Code string -> Token stream with semantic types | Pygments (Python), Syntect (Rust), Shiki (JS) |
| **Theme/Styles** | Token type -> Visual styling (color, bold, italic) | Pygments styles, TextMate themes |
| **Text Measurer** | Calculate text dimensions without drawing | Pango (via PangoCairo), Font metrics APIs |
| **Layout Engine** | Calculate positions, sizes, dimensions for all elements | Custom calculations based on metrics |
| **Canvas/Renderer** | Abstract drawing operations; format-specific output | Cairo (pycairo/cairocffi) |
| **Window Chrome** | Draw decorative window frame with controls | Custom drawing (circles for macOS style) |
| **Effects Engine** | Shadows, rounded corners, gradients | Cairo operators, blur algorithms |

## Recommended Project Structure

```
codepicture/
├── src/
│   └── codepicture/
│       ├── __init__.py           # Public API exports
│       ├── app.py                # Application facade (CodePictureApp)
│       ├── errors.py             # Exception hierarchy
│       │
│       ├── core/                 # Core abstractions
│       │   ├── __init__.py
│       │   ├── types.py          # Color, Token, Dimensions, Position, Rect
│       │   ├── protocols.py      # Highlighter, Canvas, Theme, TextMeasurer
│       │   ├── formatter.py      # Orchestrates rendering pipeline
│       │   └── layout.py         # LayoutEngine, LayoutMetrics
│       │
│       ├── highlight/            # Syntax highlighting
│       │   ├── __init__.py
│       │   └── pygments_impl.py  # PygmentsHighlighter
│       │
│       ├── render/               # Image generation
│       │   ├── __init__.py
│       │   ├── cairo_canvas.py   # CairoCanvas (PNG/SVG/PDF)
│       │   └── effects.py        # Shadow, blur implementations
│       │
│       ├── theme/                # Theming system
│       │   ├── __init__.py
│       │   ├── pygments_theme.py # Pygments style adapter
│       │   └── loader.py         # Theme discovery and loading
│       │
│       ├── config/               # Configuration
│       │   ├── __init__.py
│       │   ├── loader.py         # TOML parsing, merging
│       │   └── schema.py         # Pydantic RenderConfig model
│       │
│       └── cli/                  # Command-line interface
│           ├── __init__.py
│           └── main.py           # Typer CLI
│
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

### Structure Rationale

- **`core/`:** Protocol definitions and orchestration. No implementation dependencies. Enables swapping implementations.
- **`highlight/`:** Isolated highlighting. Only depends on `core/types.py`. Easy to add alternative highlighters.
- **`render/`:** All Cairo-specific code. Contains format-specific surface handling (PNG vs SVG vs PDF differences).
- **`theme/`:** Theme loading and style resolution. Decoupled from highlighting to allow custom themes.
- **`config/`:** Pydantic models and TOML parsing. Validation happens here, not at render time.
- **`cli/`:** Typer CLI that calls the facade. GUI would be a sibling directory using same facade.

## Architectural Patterns

### Pattern 1: Protocol-Based Abstraction

**What:** Define interfaces (Python Protocols) for all major components. Implementations satisfy the protocol.
**When to use:** Always. This is the foundation pattern for extensibility.
**Trade-offs:**
- PRO: Swap implementations (e.g., different highlighter, different canvas backend)
- PRO: Easy testing with mocks
- CON: Slight indirection overhead
- CON: Must maintain protocol compatibility

**Example:**
```python
from typing import Protocol

class TextMeasurer(Protocol):
    def measure_text(
        self, text: str, font_family: str, font_size: int
    ) -> tuple[float, float]:
        """Return (width, height) in pixels."""
        ...

class Canvas(Protocol):
    @property
    def dimensions(self) -> Dimensions: ...

    def draw_text(
        self, x: float, y: float, text: str,
        font_family: str, font_size: int, style: TextStyle
    ) -> float:
        """Draw text, return advance width."""
        ...

    def save(self) -> bytes:
        """Serialize to output format."""
        ...
```

### Pattern 2: Two-Phase Rendering (Measure, then Draw)

**What:** Separate layout calculation from actual drawing. First pass measures everything to determine canvas size, second pass renders.
**When to use:** When canvas dimensions depend on content (auto-sizing).
**Trade-offs:**
- PRO: Accurate dimensions before committing to canvas
- PRO: Can preview dimensions without rendering
- CON: Two passes over data
- CON: Must ensure measurement matches rendering

**Example:**
```python
# Phase 1: Measure (lightweight, no canvas)
measurer = CairoCanvas.create_measurer()
layout_engine = LayoutEngine(measurer, config)
metrics = layout_engine.calculate_metrics(highlighted_lines)

# Phase 2: Draw (full canvas with known dimensions)
canvas = CairoCanvas.create(metrics.total_width, metrics.total_height, format)
formatter.render_to_canvas(canvas, highlighted_lines, metrics)
```

### Pattern 3: Application Facade

**What:** Single class that orchestrates all subsystems. CLI and GUI call the same facade.
**When to use:** When multiple interfaces (CLI, GUI, library API) need the same functionality.
**Trade-offs:**
- PRO: One place to understand the full workflow
- PRO: Consistent behavior across interfaces
- PRO: GUI-readiness built in
- CON: Facade can become bloated

**Example:**
```python
class CodePictureApp:
    def __init__(
        self,
        highlighter: Highlighter | None = None,
        base_config: RenderConfig | None = None,
    ):
        self._highlighter = highlighter or PygmentsHighlighter()
        self._config = base_config or RenderConfig()

    def render(
        self, code: str, language: str | None = None, **overrides
    ) -> RenderResult:
        """Main entry point for rendering."""
        config = self._config.merge(**overrides)
        # ... orchestrate pipeline ...
```

### Pattern 4: Configuration Layering

**What:** Merge configuration from multiple sources with clear precedence.
**When to use:** When users can configure via file, CLI, and programmatic API.
**Trade-offs:**
- PRO: Flexible user experience
- PRO: Sensible defaults with easy overrides
- CON: Must clearly document precedence

**Precedence (lowest to highest):**
1. Built-in defaults (in Pydantic model)
2. User config file (~/.config/codepicture/config.toml)
3. CLI arguments
4. Programmatic overrides

## Data Flow

### Request Flow

```
[Code String]
     |
     v
[Language Detection] -- (optional, if language not specified)
     |
     v
[Highlighter.highlight()] --> [list[Line]] where Line = list[Token]
     |                              |
     v                              v
[Theme.get_style(token_type)] --> [TextStyle] (color, bold, italic)
     |
     v
[TextMeasurer.measure_text()] --> (width, height) per token/line
     |
     v
[LayoutEngine.calculate_metrics()] --> [LayoutMetrics]
     |                                      |
     |  (now dimensions are known)          |
     v                                      v
[Canvas.create(width, height, format)]
     |
     v
[Render background, shadow, window chrome]
     |
     v
[Render line numbers (if enabled)]
     |
     v
[Render code lines with token styles]
     |
     v
[Canvas.save()] --> [bytes] (PNG/SVG/PDF)
     |
     v
[Write to file / clipboard / return]
```

### Key Data Structures

```
Token:
  - text: str
  - token_type: TokenType (from Pygments)

Line = list[Token]

TextStyle:
  - color: Color
  - bold: bool
  - italic: bool
  - underline: bool

LayoutMetrics:
  - total_width: int
  - total_height: int
  - content_width: int
  - content_height: int
  - gutter_width: int
  - line_height_px: float
  - char_width: float  (for monospace)
  - code_start_x: float
  - code_start_y: float

RenderResult:
  - data: bytes
  - format: OutputFormat
  - width: int
  - height: int
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Small files (<1000 lines) | Current architecture handles perfectly. No adjustments needed. |
| Medium files (1000-10000 lines) | May need progress callbacks for GUI responsiveness. Consider chunked highlighting. |
| Large files (>10000 lines) | Stream processing: highlight/render in chunks. Tiled canvas rendering. Memory limits on ImageSurface. |

### Scaling Priorities

1. **First bottleneck:** Memory for large raster images. A 4K code screenshot at scale 2.0 uses significant memory. SVG/PDF don't have this issue.
2. **Second bottleneck:** Highlighting speed for very large files. Pygments is reasonably fast but not optimized for streaming.

**Note:** For a CLI tool targeting presentation screenshots, files >1000 lines are unusual. Optimize for common case (small-medium files) first.

## Anti-Patterns

### Anti-Pattern 1: Tight Coupling to Pygments Internals

**What people do:** Directly import Pygments token classes throughout the codebase; assume Pygments-specific behavior everywhere.
**Why it's wrong:** Makes it impossible to swap highlighters. Pygments updates can break code in unexpected places.
**Do this instead:** Define a Token abstraction in `core/types.py`. The PygmentsHighlighter converts Pygments tokens to your abstraction. Other code works with the abstraction.

### Anti-Pattern 2: Drawing Before Measuring

**What people do:** Create a canvas with guessed dimensions, then try to fit content, then resize if needed.
**Why it's wrong:** Resizing raster canvases is wasteful; some backends (PDF, SVG) can't resize. Results in multiple render passes or clipped content.
**Do this instead:** Always measure first (Phase 1), then create canvas with exact dimensions (Phase 2).

### Anti-Pattern 3: Validation at Render Time

**What people do:** Accept configuration, start rendering, then fail halfway through when invalid value encountered.
**Why it's wrong:** Wastes CPU cycles; poor user experience with partial outputs; harder to debug.
**Do this instead:** Use Pydantic for configuration. Validate everything at load time. By render time, all values are guaranteed valid.

### Anti-Pattern 4: CLI Logic in Core

**What people do:** Import Typer in core modules; put CLI-specific behavior (like clipboard handling) in render code.
**Why it's wrong:** Breaks GUI usage; creates unnecessary dependencies; makes testing harder.
**Do this instead:** Core returns `RenderResult` with bytes. CLI decides to write to file, clipboard, or stdout. GUI decides to display preview.

### Anti-Pattern 5: Ignoring Font Fallbacks

**What people do:** Assume specified font exists; crash or render boxes when it doesn't.
**Why it's wrong:** Different systems have different fonts. "JetBrains Mono" doesn't exist on default macOS/Linux.
**Do this instead:** Support font fallback lists (e.g., "JetBrains Mono, Fira Code, monospace"). Fall back gracefully; log warning but don't crash.

## Integration Points

### External Dependencies

| Dependency | Integration Pattern | Notes |
|------------|---------------------|-------|
| **Pygments** | Lexer selection, token generation | Thread-safe for reading; custom lexer registration is not thread-safe |
| **PyCairo** | Surface creation, drawing operations | Create separate instances per render; not thread-safe |
| **Pango/PangoCairo** | Text measurement, text rendering | Create PangoLayout per text operation; handles complex scripts |
| **Pydantic** | Configuration validation | Immutable models; validate at load time |
| **Pyperclip** | Clipboard I/O (optional) | May not be available on all systems; graceful degradation |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI <-> Facade | Method calls with dataclasses | CLI never imports from core directly |
| Facade <-> Highlighter | Protocol interface | Highlighter is injected; can be mocked |
| Facade <-> Renderer | Protocol interface | Canvas protocol; CairoCanvas is default |
| LayoutEngine <-> TextMeasurer | Protocol interface | Measurer injected for testability |
| Theme <-> Formatter | Protocol interface | Theme maps token types to styles |

## Build Order Implications

Based on the architecture, components should be built in this order (each phase depends on previous):

### Phase 1: Foundation
- `core/types.py` - Color, Token, Dimensions, Position, enums
- `core/protocols.py` - All Protocol definitions
- `errors.py` - Exception hierarchy
- `config/schema.py` - Pydantic RenderConfig

**Rationale:** Everything else depends on these. No external rendering dependencies yet.

### Phase 2: Highlighting
- `highlight/pygments_impl.py` - PygmentsHighlighter
- `theme/pygments_theme.py` - Theme wrapper for Pygments styles
- `theme/loader.py` - Theme discovery

**Rationale:** Can be tested in isolation. Output is token stream (pure data).

### Phase 3: Layout
- `core/layout.py` - LayoutEngine, LayoutMetrics
- Text measurement (depends on Phase 4 technically, but can mock for testing)

**Rationale:** Pure calculations. Can test with mock TextMeasurer.

### Phase 4: Rendering
- `render/cairo_canvas.py` - CairoCanvas implementation
- `render/effects.py` - Shadow, blur algorithms

**Rationale:** Requires Cairo. Most complex; has format-specific behavior.

### Phase 5: Orchestration
- `core/formatter.py` - Formatter (orchestrates pipeline)
- `app.py` - Application facade

**Rationale:** Ties everything together. Requires all previous phases.

### Phase 6: Interface
- `cli/main.py` - Typer CLI
- `config/loader.py` - TOML loading

**Rationale:** Presentation layer. Calls facade. Last to implement.

## Sources

**Primary (HIGH confidence):**
- [Pygments API Documentation](https://pygments.org/docs/api/)
- [PyCairo Surfaces Reference](https://pycairo.readthedocs.io/en/latest/reference/surfaces.html)
- [PangoCairo Documentation](https://docs.gtk.org/PangoCairo/pango_cairo.html)
- [Pango Rendering Pipeline](https://docs.gtk.org/Pango/pango_rendering.html)
- Existing architecture document: `PYTHON_REWRITE_ARCHITECTURE.md`

**Secondary (MEDIUM confidence):**
- [Silicon Rust crate](https://github.com/Aloxaf/silicon) - Alternative implementation study
- [Silicon docs.rs](https://docs.rs/silicon/latest/silicon/)
- [Carbon GitHub](https://github.com/carbon-app/carbon) - Web-based approach
- [Ray.so GitHub](https://github.com/raycast/ray-so) - Next.js approach

**Ecosystem Survey (LOW-MEDIUM confidence):**
- [Code Snippet Image Generators Survey](https://dev.to/madza/14-code-snippet-image-generators-to-turn-your-code-into-stunning-visuals-5220)
- [Ray.so Alternatives](https://snappify.com/blog/best-ray-so-alternatives)

---
*Architecture research for: Code screenshot/code image generation tools*
*Researched: 2026-01-28*
