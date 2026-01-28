# Phase 3: Layout Engine - Research

**Researched:** 2026-01-28
**Domain:** Text measurement, typography configuration, canvas sizing with Cairo/Pango
**Confidence:** HIGH

## Summary

Phase 3 implements the layout engine that calculates exact canvas dimensions and element positions before rendering. This is the measurement layer between syntax highlighting (tokens from Phase 2) and rendering (pixels in Phase 4). The standard approach uses Pango for text measurement and Cairo for the eventual rendering surface.

Key components:
1. **TextMeasurer** - Wraps Pango layout for measuring text dimensions without rendering
2. **LayoutEngine** - Calculates canvas dimensions, line positions, gutter width, and code area
3. **Typography Configuration** - Extends RenderConfig with font family, size, and line height
4. **Font Management** - Bundles JetBrains Mono as default with system font fallback

**Primary recommendation:** Use PyGObject (`gi.repository`) for Pango/PangoCairo access. Use ManimPango for cross-platform font registration. Bundle JetBrains Mono TTF files using `importlib.resources` for reliable default font.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyGObject | 3.46+ | Pango/PangoCairo bindings | Official GObject introspection, well-maintained, GTK ecosystem |
| PyCairo | 1.25+ | Cairo surface for text measurement | Companion to Pango, needed for PangoCairo context |
| ManimPango | 0.6.1+ | Cross-platform font registration | Simplifies fontconfig API, works on Windows/macOS/Linux |
| JetBrains Mono | 2.304 | Bundled default monospace font | SIL OFL license, excellent ligatures, popular developer font |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| importlib.resources | stdlib | Load bundled font files | Always - for accessing package data files reliably |
| pathlib | stdlib | Path manipulation | When working with font file paths |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyGObject Pango | pangocffi/pangocairocffi | CFFI-based, incomplete coverage, harder to use |
| ManimPango | Direct fontconfig API | ManimPango simplifies cross-platform, fontconfig is C API |
| Bundled font | System fonts only | Inconsistent results across systems, font may not exist |

**Installation:**
```bash
uv add pygobject pycairo manimpango
# JetBrains Mono bundled as package data, no install needed
```

## Architecture Patterns

### Recommended Project Structure
```
src/codepicture/
├── core/
│   ├── types.py            # Add LayoutMetrics dataclass
│   └── protocols.py        # TextMeasurer protocol (already exists)
├── layout/
│   ├── __init__.py         # Re-exports
│   ├── engine.py           # LayoutEngine class
│   └── measurer.py         # Pango-based TextMeasurer implementation
├── fonts/
│   ├── __init__.py         # Font management utilities
│   ├── JetBrainsMono-Regular.ttf
│   └── JetBrainsMono-Bold.ttf
└── config/
    └── schema.py           # Typography fields (font_family, font_size, line_height)
```

### Pattern 1: Pango Layout for Text Measurement

**What:** Create a Pango layout to measure text dimensions without actually rendering.

**When to use:** Always - accurate text measurement requires Pango, not Cairo's toy text API.

**Example:**
```python
# Source: PyGObject Pango documentation
import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo
import cairo

class PangoTextMeasurer:
    """Text measurer using Pango for accurate dimensions."""

    def __init__(self) -> None:
        # Create minimal surface for measurement context
        self._surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
        self._context = cairo.Context(self._surface)
        self._layout = PangoCairo.create_layout(self._context)

    def measure_text(
        self, text: str, font_family: str, font_size: int
    ) -> tuple[float, float]:
        """Measure text dimensions in pixels.

        Args:
            text: Text to measure
            font_family: Font family name
            font_size: Font size in pixels

        Returns:
            Tuple of (width, height) in pixels
        """
        # Create font description
        font_desc = Pango.FontDescription()
        font_desc.set_family(font_family)
        font_desc.set_size(font_size * Pango.SCALE)  # Pango uses 1024 units per point

        self._layout.set_font_description(font_desc)
        self._layout.set_text(text, -1)

        # get_pixel_size returns (width, height) already in device units
        width, height = self._layout.get_pixel_size()
        return float(width), float(height)
```

### Pattern 2: Bundled Font Loading with ManimPango

**What:** Register bundled font files before using them with Pango.

**When to use:** At application startup, before any text measurement.

**Example:**
```python
# Source: ManimPango documentation, importlib.resources
from importlib.resources import files, as_file
import manimpango

def register_bundled_fonts() -> bool:
    """Register bundled JetBrains Mono fonts.

    Returns:
        True if registration succeeded, False otherwise
    """
    fonts_package = files('codepicture.fonts')

    for font_file in ['JetBrainsMono-Regular.ttf', 'JetBrainsMono-Bold.ttf']:
        font_resource = fonts_package.joinpath(font_file)

        # as_file provides actual filesystem path for ManimPango
        with as_file(font_resource) as font_path:
            if not manimpango.register_font(str(font_path)):
                return False

    return True
```

### Pattern 3: Layout Metrics Calculation

**What:** Calculate all layout dimensions before creating the canvas.

**When to use:** Before rendering - dimensions must be known to create the surface.

**Example:**
```python
# Source: Application-specific pattern based on CONTEXT.md decisions
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class LayoutMetrics:
    """Complete layout measurements for rendering."""

    # Canvas dimensions
    canvas_width: int
    canvas_height: int

    # Content area (inside padding)
    content_x: float
    content_y: float
    content_width: float
    content_height: float

    # Gutter (line numbers)
    gutter_width: float
    gutter_x: float

    # Code area (after gutter)
    code_x: float
    code_y: float
    code_width: float

    # Typography metrics
    line_height_px: float
    char_width: float
    baseline_offset: float

class LayoutEngine:
    """Calculates positions and sizes for rendering."""

    # Fixed values from CONTEXT.md
    LINE_NUMBER_GAP = 12  # px between line numbers and code
    CORNER_RADIUS = 8     # px

    def __init__(self, measurer: TextMeasurer, config: RenderConfig) -> None:
        self._measurer = measurer
        self._config = config

    def calculate_metrics(
        self, lines: list[list[TokenInfo]], max_line_number: int
    ) -> LayoutMetrics:
        """Calculate complete layout metrics.

        Args:
            lines: Tokenized lines from highlighter
            max_line_number: Highest line number to display

        Returns:
            LayoutMetrics with all dimensions
        """
        # Measure character dimensions with the configured font
        char_width, char_height = self._measurer.measure_text(
            "M", self._config.font_family, self._config.font_size
        )

        # Line height from config (multiplier on font height)
        line_height_px = char_height * self._config.line_height

        # Find longest line in characters
        max_chars = max(
            sum(len(token.text) for token in line)
            for line in lines
        ) if lines else 0

        # Calculate widths
        gutter_width = self._calculate_gutter_width(max_line_number) if self._config.show_line_numbers else 0
        code_width = max_chars * char_width

        # Content area
        content_width = gutter_width + self.LINE_NUMBER_GAP + code_width
        content_height = len(lines) * line_height_px

        # Canvas with padding
        padding = self._config.padding
        canvas_width = int(content_width + 2 * padding)
        canvas_height = int(content_height + 2 * padding)

        return LayoutMetrics(
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            content_x=padding,
            content_y=padding,
            content_width=content_width,
            content_height=content_height,
            gutter_width=gutter_width,
            gutter_x=padding,
            code_x=padding + gutter_width + self.LINE_NUMBER_GAP,
            code_y=padding,
            code_width=code_width,
            line_height_px=line_height_px,
            char_width=char_width,
            baseline_offset=char_height * 0.8,  # Approximate baseline
        )

    def _calculate_gutter_width(self, max_line_number: int) -> float:
        """Calculate gutter width based on line number digits."""
        digits = len(str(max_line_number))
        # Measure actual digit width
        digit_width, _ = self._measurer.measure_text(
            "0" * digits, self._config.font_family, self._config.font_size
        )
        return digit_width
```

### Pattern 4: Font Fallback with Warning

**What:** Try configured font, fall back to bundled default if not found.

**When to use:** When initializing the measurer with user-configured font.

**Example:**
```python
# Source: CONTEXT.md decisions
import logging
import manimpango

logger = logging.getLogger(__name__)

def resolve_font_family(requested: str, default: str = "JetBrains Mono") -> str:
    """Resolve font family with fallback.

    Args:
        requested: User-requested font family
        default: Bundled default font

    Returns:
        Font family name that is available
    """
    available = manimpango.list_fonts()

    if requested in available:
        return requested

    logger.warning(
        f"Font '{requested}' not found. "
        f"Falling back to bundled default: {default}"
    )

    if default not in available:
        raise RenderError(
            f"Default font '{default}' not available. "
            "Font registration may have failed."
        )

    return default
```

### Anti-Patterns to Avoid

- **Using Cairo's toy text API:** Cairo's `show_text()` is for demos only. Use Pango for real text.
- **Forgetting PANGO_SCALE:** Pango uses 1024 units per point. Always multiply/divide appropriately.
- **Caching layouts across fonts:** Font description affects layout. Create new layouts or reset font.
- **Assuming monospace uniformity:** Even monospace fonts may have varying widths for some characters.
- **Measuring without surface:** Pango needs a Cairo context. Create a dummy surface for measurement.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Text measurement | Manual pixel counting | Pango Layout | Handles kerning, ligatures, Unicode properly |
| Font registration | Direct fontconfig calls | ManimPango | Cross-platform abstraction, simpler API |
| Package data loading | `__file__` path manipulation | `importlib.resources` | Works with zip imports, proper resource API |
| Unit conversion | Manual SCALE division | `get_pixel_size()` | Already returns device units |
| Font fallback | Try/except chains | `manimpango.list_fonts()` | Reliable cross-platform font enumeration |

**Key insight:** Text measurement is deceptively complex. Unicode, ligatures, kerning, and font metrics all interact. Pango has decades of experience handling these correctly.

## Common Pitfalls

### Pitfall 1: Pango Units vs Device Units
**What goes wrong:** Text renders at wrong size (1024x too big or small)
**Why it happens:** Pango uses scaled units (PANGO_SCALE = 1024) for sub-pixel precision
**How to avoid:** Use `get_pixel_size()` not `get_size()`, multiply font size by PANGO_SCALE
**Warning signs:** Enormous text or microscopic text in output

```python
# WRONG: Raw Pango units
width, height = layout.get_size()

# CORRECT: Device units (pixels)
width, height = layout.get_pixel_size()
```

### Pitfall 2: Text Origin Difference (Cairo vs Pango)
**What goes wrong:** Text renders in wrong position
**Why it happens:** Cairo positions at baseline, Pango at top-left of logical extents
**How to avoid:** Account for baseline when positioning with Cairo after Pango measurement
**Warning signs:** Text appears shifted up or down

### Pitfall 3: Font Not Found Silent Failure
**What goes wrong:** Text renders in system default font, looks wrong
**Why it happens:** Pango silently falls back if font family not found
**How to avoid:** Verify font availability with `list_fonts()` before use
**Warning signs:** Different font appearance than expected

### Pitfall 4: Empty Code Input
**What goes wrong:** Zero-dimension canvas or division by zero
**Why it happens:** Empty input has no lines to measure
**How to avoid:** CONTEXT.md says "error and exit" for empty input - validate early
**Warning signs:** Zero-size images, crashes on empty files

### Pitfall 5: Thread Safety with Font Maps
**What goes wrong:** Crashes or wrong fonts in multi-threaded code
**Why it happens:** Pango font maps are per-thread since 1.32.6
**How to avoid:** Create measurer per-thread or use single-threaded design
**Warning signs:** Intermittent font issues, crashes under load

## Code Examples

Verified patterns from official documentation and testing:

### Complete Pango Measurement Setup
```python
# Source: PyGObject documentation, PangoCairo-1.0
import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo
import cairo

# Create measurement context
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
context = cairo.Context(surface)
layout = PangoCairo.create_layout(context)

# Configure font
font_desc = Pango.FontDescription.new()
font_desc.set_family("JetBrains Mono")
font_desc.set_size(16 * Pango.SCALE)  # 16px
font_desc.set_weight(Pango.Weight.NORMAL)

layout.set_font_description(font_desc)

# Measure text
layout.set_text("Hello, World!", -1)
width, height = layout.get_pixel_size()
print(f"Text size: {width}x{height} pixels")
```

### Bundling Fonts in pyproject.toml
```toml
# Source: Hatch/setuptools documentation
[tool.hatch.build.targets.wheel]
packages = ["src/codepicture"]

[tool.hatch.build.targets.wheel.force-include]
# Include font files in package
"fonts/JetBrainsMono-Regular.ttf" = "codepicture/fonts/JetBrainsMono-Regular.ttf"
"fonts/JetBrainsMono-Bold.ttf" = "codepicture/fonts/JetBrainsMono-Bold.ttf"
```

### Font Metrics for Line Height
```python
# Source: Pango FontMetrics documentation
def get_font_metrics(
    font_family: str, font_size: int
) -> tuple[float, float, float]:
    """Get font metrics for layout calculations.

    Returns:
        Tuple of (ascent, descent, height) in pixels
    """
    # Get font map and context
    font_map = PangoCairo.font_map_get_default()
    pango_context = font_map.create_context()

    # Create font description
    font_desc = Pango.FontDescription.new()
    font_desc.set_family(font_family)
    font_desc.set_size(font_size * Pango.SCALE)

    # Get metrics
    metrics = pango_context.get_metrics(font_desc, None)

    # Convert from Pango units to pixels
    ascent = metrics.get_ascent() / Pango.SCALE
    descent = metrics.get_descent() / Pango.SCALE
    height = metrics.get_height() / Pango.SCALE

    return ascent, descent, height
```

### Line Position Calculation
```python
# Source: Application pattern based on CONTEXT.md
def get_line_position(
    line_index: int, metrics: LayoutMetrics
) -> tuple[float, float]:
    """Get top-left position for a line of code.

    Args:
        line_index: 0-based line index
        metrics: Calculated layout metrics

    Returns:
        Tuple of (x, y) coordinates
    """
    x = metrics.code_x
    y = metrics.code_y + (line_index * metrics.line_height_px)
    return x, y

def get_line_number_position(
    line_index: int, metrics: LayoutMetrics
) -> tuple[float, float]:
    """Get position for line number (right-aligned in gutter)."""
    # Line number x is right edge of gutter minus text width
    # (Actual width computed per number at render time)
    y = metrics.code_y + (line_index * metrics.line_height_px)
    return metrics.gutter_x, y
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pangocairo module | PyGObject gi.repository | ~2012 | Use `from gi.repository import Pango, PangoCairo` |
| pango.SCALE constant | Pango.SCALE | PyGObject migration | Access via module attribute |
| fontconfig C API | ManimPango | 2020+ | Python wrapper for cross-platform font registration |
| pkg_resources | importlib.resources | Python 3.9+ | Modern resource API, works with zip imports |

**Deprecated/outdated:**
- `pangocairo` and `pango` modules: Use `gi.repository.PangoCairo` and `gi.repository.Pango`
- `cairo.Context.show_text()`: Toy API only, not for production text rendering
- `pkg_resources.resource_filename()`: Use `importlib.resources.as_file()` instead

## Open Questions

Things that couldn't be fully resolved:

1. **Font Ligatures Default Setting**
   - What we know: JetBrains Mono has excellent ligature support
   - What's unclear: Whether ligatures should be on or off by default
   - Recommendation: Enable ligatures by default (more modern look), allow config override

2. **DPI/Scale Factor Handling**
   - What we know: Pango has resolution settings (default 96 DPI)
   - What's unclear: Whether to expose DPI/scale configuration or hardcode
   - Recommendation: Hardcode 1.0 scale for v1, add scale factor later if needed

3. **Dynamic vs Fixed Line Number Width**
   - What we know: CONTEXT.md lists this as Claude's discretion
   - What's unclear: Performance impact of dynamic calculation per-render
   - Recommendation: Dynamic based on max line number (handles 1000+ line files correctly)

## Sources

### Primary (HIGH confidence)
- [Pango Layout Documentation](https://docs.gtk.org/Pango/class.Layout.html) - Layout API and measurement methods
- [PangoCairo Functions](https://lazka.github.io/pgi-docs/PangoCairo-1.0/functions.html) - create_layout, show_layout
- [Pango FontDescription](https://lazka.github.io/pgi-docs/Pango-1.0/classes/FontDescription.html) - Font configuration
- [ManimPango register_font](https://manimpango.manim.community/en/latest/reference/manimpango.register_font.html) - Font registration API
- [PyGObject Pango](https://api.pygobject.gnome.org/Pango-1.0/index.html) - Python bindings reference

### Secondary (MEDIUM confidence)
- [Cairo and Pango in Python](https://aperiodic.net/pip/archives/Geekery/cairo-pango-python/) - Practical integration guide
- [Custom Application Fonts with Pango](https://notes.naveenmk.me/blog/custom-application-fonts-pango/) - Font loading patterns
- [setuptools Data Files](https://setuptools.pypa.io/en/latest/userguide/datafiles.html) - Package data configuration

### Tertiary (LOW confidence)
- JetBrains Mono bundling approach is application-specific design
- Exact pyproject.toml syntax for font bundling varies by build backend

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PyGObject/Pango is the established approach, verified with official docs
- Architecture: HIGH - Patterns derived from Pango documentation and Manim project
- Pitfalls: HIGH - Documented gotchas from official sources and community experience

**Research date:** 2026-01-28
**Valid until:** 2026-02-28 (Pango/Cairo APIs are stable, 30-day validity)
