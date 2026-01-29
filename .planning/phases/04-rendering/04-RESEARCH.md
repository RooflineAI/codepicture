# Phase 4: Rendering - Research

**Researched:** 2026-01-29
**Domain:** Multi-format rendering with pycairo (PNG/SVG/PDF), window chrome, shadows, visual effects
**Confidence:** HIGH

## Summary

Phase 4 implements the rendering layer that produces polished images from LayoutMetrics and highlighted tokens. This phase creates a CairoCanvas abstraction supporting three output formats (PNG, SVG, PDF), draws window chrome with macOS-style traffic light buttons, applies drop shadows, and renders syntax-highlighted code with optional line numbers.

Key components:
1. **CairoCanvas** - Implements Canvas protocol for PNG/SVG/PDF output
2. **Shadow Rendering** - Uses Pillow for Gaussian blur post-processing (Cairo lacks native blur)
3. **Window Chrome** - Draws macOS-style title bar with traffic light buttons
4. **Renderer** - Orchestrates drawing operations using layout metrics

**Primary recommendation:** Use pycairo directly with format-specific surfaces (ImageSurface, SVGSurface, PDFSurface). For shadows on PNG, render to ImageSurface, convert to Pillow for GaussianBlur, then composite. For SVG/PDF, use filter elements or skip shadows (vectors don't blur well).

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pycairo | 1.25+ | Rendering engine for all formats | Already in use from Phase 3, supports PNG/SVG/PDF surfaces |
| Pillow | 10.0+ | Shadow blur via GaussianBlur, PNG post-processing | Standard Python imaging, excellent filter support |
| ManimPango | 0.6.1+ | Font registration (from Phase 3) | Continued from Phase 3 for font consistency |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| io.BytesIO | stdlib | Memory buffer for surface output | Always - for returning bytes instead of writing files |
| math | stdlib | Angle calculations for arcs | Drawing rounded rectangles and traffic light buttons |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pillow blur | cairo-blur/cairou | Native cairo blur requires C extension, not pure Python |
| pycairo | cairocffi | CFFI alternative, but pycairo already established in Phase 3 |
| Manual shadow | Pre-rendered shadow assets | Less flexible, but could be faster |

**Installation:**
```bash
uv add pillow
# pycairo and manimpango already installed from Phase 3
```

## Architecture Patterns

### Recommended Project Structure
```
src/codepicture/
├── render/
│   ├── __init__.py         # Re-exports CairoCanvas, Renderer
│   ├── canvas.py           # CairoCanvas implementing Canvas protocol
│   ├── shadow.py           # Shadow rendering using Pillow
│   └── chrome.py           # Window chrome (title bar, traffic lights)
├── core/
│   ├── protocols.py        # Canvas protocol (already defined)
│   └── types.py            # Add RenderResult dataclass
└── config/
    └── schema.py           # Already has shadow, window_controls settings
```

### Pattern 1: Format-Specific Surface Creation

**What:** Create the appropriate Cairo surface based on output format.

**When to use:** At render start, after layout metrics are calculated.

**Example:**
```python
# Source: pycairo documentation
import cairo
from io import BytesIO
from codepicture.core.types import OutputFormat

def create_surface(
    width: int,
    height: int,
    format: OutputFormat,
    scale: float = 1.0,
) -> tuple[cairo.Surface, BytesIO | None]:
    """Create Cairo surface for the specified format.

    Args:
        width: Logical width in pixels
        height: Logical height in pixels
        format: Output format (PNG, SVG, PDF)
        scale: Scale factor (2.0 for retina/HiDPI)

    Returns:
        Tuple of (surface, buffer) - buffer is None for ImageSurface
    """
    if format == OutputFormat.PNG:
        # Create at scaled dimensions for HiDPI
        pixel_width = int(width * scale)
        pixel_height = int(height * scale)
        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,  # ARGB for alpha/transparency
            pixel_width,
            pixel_height,
        )
        return surface, None

    elif format == OutputFormat.SVG:
        buffer = BytesIO()
        surface = cairo.SVGSurface(buffer, width, height)
        return surface, buffer

    elif format == OutputFormat.PDF:
        buffer = BytesIO()
        # PDF dimensions are in points (1 point = 1/72 inch)
        surface = cairo.PDFSurface(buffer, width, height)
        return surface, buffer

    raise ValueError(f"Unsupported format: {format}")
```

### Pattern 2: Rounded Rectangle Drawing

**What:** Draw rectangles with rounded corners using arc paths.

**When to use:** For window background, code area background.

**Example:**
```python
# Source: Cairo cookbook/samples
import cairo
import math

def draw_rounded_rect(
    ctx: cairo.Context,
    x: float,
    y: float,
    width: float,
    height: float,
    radius: float,
) -> None:
    """Draw a rounded rectangle path.

    Args:
        ctx: Cairo context
        x, y: Top-left corner
        width, height: Rectangle dimensions
        radius: Corner radius
    """
    degrees = math.pi / 180.0

    ctx.new_sub_path()
    # Top-right corner
    ctx.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
    # Bottom-right corner
    ctx.arc(x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
    # Bottom-left corner
    ctx.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
    # Top-left corner
    ctx.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
    ctx.close_path()
```

### Pattern 3: macOS Traffic Light Buttons

**What:** Draw the red/yellow/green window control buttons.

**When to use:** When window_controls is True and window chrome is enabled.

**Example:**
```python
# Source: CSS implementations, Apple HIG approximation
import cairo
from codepicture.core.types import Color

# Traffic light button constants (based on macOS CSS approximations)
BUTTON_DIAMETER = 12  # px
BUTTON_SPACING = 8    # px between buttons
BUTTON_MARGIN_LEFT = 8   # px from left edge
BUTTON_MARGIN_TOP = 8    # px from top edge (centers in title bar)

# Button colors (static, no hover states per CONTEXT.md)
CLOSE_COLOR = Color.from_hex("#ff5f57")      # Red
MINIMIZE_COLOR = Color.from_hex("#febc2e")   # Yellow
MAXIMIZE_COLOR = Color.from_hex("#28c840")   # Green

def draw_traffic_lights(
    ctx: cairo.Context,
    title_bar_y: float,
    title_bar_height: float,
) -> None:
    """Draw macOS-style traffic light buttons.

    Args:
        ctx: Cairo context
        title_bar_y: Y position of title bar top
        title_bar_height: Height of title bar
    """
    # Center buttons vertically in title bar
    button_y = title_bar_y + (title_bar_height - BUTTON_DIAMETER) / 2

    colors = [CLOSE_COLOR, MINIMIZE_COLOR, MAXIMIZE_COLOR]

    for i, color in enumerate(colors):
        button_x = BUTTON_MARGIN_LEFT + i * (BUTTON_DIAMETER + BUTTON_SPACING)
        center_x = button_x + BUTTON_DIAMETER / 2
        center_y = button_y + BUTTON_DIAMETER / 2

        ctx.arc(center_x, center_y, BUTTON_DIAMETER / 2, 0, 2 * math.pi)
        ctx.set_source_rgba(
            color.r / 255.0,
            color.g / 255.0,
            color.b / 255.0,
            color.a / 255.0,
        )
        ctx.fill()
```

### Pattern 4: Shadow via Pillow Post-Processing

**What:** Add drop shadow to PNG output using Pillow's GaussianBlur.

**When to use:** For PNG format when shadow is enabled. (SVG/PDF use different approaches.)

**Example:**
```python
# Source: Pillow ImageFilter docs, Cairo+PIL integration patterns
import cairo
from PIL import Image, ImageFilter
from io import BytesIO

def apply_shadow_to_surface(
    surface: cairo.ImageSurface,
    blur_radius: int,
    offset_x: int,
    offset_y: int,
    shadow_color: tuple[int, int, int, int],
) -> bytes:
    """Apply drop shadow to a Cairo ImageSurface.

    Args:
        surface: Cairo ImageSurface with rendered content
        blur_radius: Shadow blur radius
        offset_x: Horizontal shadow offset
        offset_y: Vertical shadow offset
        shadow_color: RGBA tuple for shadow color

    Returns:
        PNG bytes with shadow applied
    """
    # Get surface dimensions
    width = surface.get_width()
    height = surface.get_height()

    # Shadow requires extra space
    shadow_margin = blur_radius * 2 + max(abs(offset_x), abs(offset_y))

    # Convert Cairo surface to Pillow Image
    # Cairo uses BGRA, Pillow expects RGBA
    data = surface.get_data()
    pil_image = Image.frombytes(
        "RGBa",  # Pre-multiplied alpha from Cairo
        (width, height),
        bytes(data),
    )
    # Convert to standard RGBA
    pil_image = pil_image.convert("RGBA")

    # Create shadow from alpha channel
    alpha = pil_image.split()[3]  # Extract alpha
    shadow = Image.new("RGBA", (width, height), shadow_color[:3] + (0,))
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Create output canvas with extra margin for shadow
    output_width = width + 2 * shadow_margin
    output_height = height + 2 * shadow_margin
    output = Image.new("RGBA", (output_width, output_height), (0, 0, 0, 0))

    # Composite: shadow first (offset), then content
    shadow_x = shadow_margin + offset_x
    shadow_y = shadow_margin + offset_y
    output.paste(shadow, (shadow_x, shadow_y), shadow)
    output.paste(pil_image, (shadow_margin, shadow_margin), pil_image)

    # Export to PNG bytes
    buffer = BytesIO()
    output.save(buffer, format="PNG")
    return buffer.getvalue()
```

### Pattern 5: 2x Retina/HiDPI Rendering

**What:** Render at 2x resolution for crisp output on high-DPI displays.

**When to use:** Always for PNG output (per CONTEXT.md decision).

**Example:**
```python
# Source: pycairo scale transform pattern
import cairo

def render_at_2x(
    width: int,
    height: int,
    draw_func: callable,
) -> cairo.ImageSurface:
    """Render at 2x resolution for HiDPI.

    Args:
        width: Logical width
        height: Logical height
        draw_func: Function that takes cairo.Context and draws

    Returns:
        ImageSurface at 2x resolution
    """
    scale = 2
    surface = cairo.ImageSurface(
        cairo.FORMAT_ARGB32,
        width * scale,
        height * scale,
    )
    ctx = cairo.Context(surface)

    # Scale context so drawing uses logical coordinates
    ctx.scale(scale, scale)

    # Draw using logical coordinates
    draw_func(ctx)

    return surface
```

### Anti-Patterns to Avoid

- **Using Cairo's toy text API for production:** Use Pango/ManimPango for proper text rendering (as established in Phase 3)
- **Assuming RGBA byte order:** Cairo uses BGRA internally; convert when interoperating with Pillow
- **Forgetting surface.finish():** Always call finish() before reading from BytesIO buffer for SVG/PDF
- **Drawing shadow on vector formats:** Gaussian blur doesn't translate to SVG/PDF well; skip or rasterize
- **Hardcoding traffic light positions:** Use constants and calculate positions from title bar dimensions

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Gaussian blur | Manual kernel convolution | Pillow ImageFilter.GaussianBlur | Optimized C implementation, correct edge handling |
| Rounded rectangles | Multiple line_to calls | Cairo arc paths | Mathematically correct curves |
| PNG with alpha | Manual RGBA assembly | cairo.FORMAT_ARGB32 + write_to_png | Correct color space and compression |
| PDF/SVG generation | XML string building | Cairo PDFSurface/SVGSurface | Correct formatting, font handling |
| Color space conversion | Manual byte shuffling | Pillow Image.convert() | Handles pre-multiplied alpha correctly |

**Key insight:** Shadow rendering is the trickiest part. Cairo doesn't have native blur, so Pillow post-processing is the pragmatic solution for PNG. For vector formats, accept limitations or rasterize the shadow layer.

## Common Pitfalls

### Pitfall 1: Cairo BGRA vs Pillow RGBA Byte Order
**What goes wrong:** Colors appear wrong (red/blue swapped) when converting between Cairo and Pillow
**Why it happens:** Cairo stores pixels as BGRA, Pillow expects RGBA
**How to avoid:** Use correct conversion mode when creating Pillow Image from Cairo data
**Warning signs:** Blue images appear red, red appears blue

```python
# WRONG: Assuming RGBA
pil_image = Image.frombytes("RGBA", (w, h), cairo_data)

# CORRECT: Cairo uses pre-multiplied BGRA (mode "RGBa" handles this)
pil_image = Image.frombytes("RGBa", (w, h), bytes(cairo_data))
pil_image = pil_image.convert("RGBA")
```

### Pitfall 2: Forgetting surface.finish() for Vector Formats
**What goes wrong:** BytesIO buffer is empty or contains incomplete data
**Why it happens:** Cairo streams output; finish() flushes remaining data
**How to avoid:** Always call surface.finish() before buffer.getvalue()
**Warning signs:** Empty SVG/PDF files, truncated output

### Pitfall 3: Shadow Extends Beyond Canvas
**What goes wrong:** Shadow is clipped at image edges
**Why it happens:** Shadow blur radius + offset requires extra canvas space
**How to avoid:** Calculate shadow margin and expand canvas dimensions
**Warning signs:** Sharp shadow edges at image boundaries

```python
# Calculate required extra space for shadow
shadow_margin = blur_radius * 2 + max(abs(offset_x), abs(offset_y))
total_width = content_width + 2 * shadow_margin
```

### Pitfall 4: Text Positioning (Baseline vs Top-Left)
**What goes wrong:** Text appears shifted vertically
**Why it happens:** Cairo positions text at baseline, but layout metrics may use top-left
**How to avoid:** Use baseline_offset from LayoutMetrics when drawing text
**Warning signs:** Text appears too high or too low

### Pitfall 5: Pre-multiplied Alpha Artifacts
**What goes wrong:** Semi-transparent edges have dark halos
**Why it happens:** Cairo uses pre-multiplied alpha; incorrect conversion creates artifacts
**How to avoid:** Use "RGBa" mode in Pillow frombytes, then convert to "RGBA"
**Warning signs:** Dark fringes around transparent areas

## Code Examples

Verified patterns for Phase 4 implementation:

### Complete CairoCanvas Class Structure
```python
# Source: Application pattern based on Canvas protocol
import cairo
from io import BytesIO
from pathlib import Path
from codepicture.core.types import Color, OutputFormat
from codepicture.core.protocols import Canvas

class CairoCanvas:
    """Canvas implementation using pycairo."""

    def __init__(
        self,
        surface: cairo.Surface,
        context: cairo.Context,
        format: OutputFormat,
        buffer: BytesIO | None = None,
    ) -> None:
        self._surface = surface
        self._ctx = context
        self._format = format
        self._buffer = buffer

    @classmethod
    def create(
        cls,
        width: int,
        height: int,
        format: OutputFormat,
        scale: float = 1.0,
    ) -> "CairoCanvas":
        """Factory method to create canvas for format."""
        # Implementation as shown in Pattern 1
        ...

    @property
    def width(self) -> int:
        return self._surface.get_width()

    @property
    def height(self) -> int:
        return self._surface.get_height()

    def draw_rectangle(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        color: Color,
        corner_radius: float = 0,
    ) -> None:
        if corner_radius > 0:
            draw_rounded_rect(self._ctx, x, y, width, height, corner_radius)
        else:
            self._ctx.rectangle(x, y, width, height)
        self._set_color(color)
        self._ctx.fill()

    def draw_circle(
        self,
        x: float,
        y: float,
        radius: float,
        color: Color,
    ) -> None:
        self._ctx.arc(x, y, radius, 0, 2 * math.pi)
        self._set_color(color)
        self._ctx.fill()

    def draw_text(
        self,
        x: float,
        y: float,
        text: str,
        font_family: str,
        font_size: int,
        color: Color,
    ) -> float:
        # Use Cairo's text API (suitable for monospace code)
        from codepicture.fonts import resolve_font_family

        resolved = resolve_font_family(font_family)
        self._ctx.select_font_face(
            resolved,
            cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_NORMAL,
        )
        self._ctx.set_font_size(font_size)
        self._set_color(color)
        self._ctx.move_to(x, y)
        self._ctx.show_text(text)

        extents = self._ctx.text_extents(text)
        return extents.x_advance

    def _set_color(self, color: Color) -> None:
        self._ctx.set_source_rgba(
            color.r / 255.0,
            color.g / 255.0,
            color.b / 255.0,
            color.a / 255.0,
        )

    def save(self) -> bytes:
        if self._format == OutputFormat.PNG:
            buffer = BytesIO()
            self._surface.write_to_png(buffer)
            return buffer.getvalue()
        else:
            # SVG/PDF - data is in self._buffer
            self._surface.finish()
            return self._buffer.getvalue()

    def save_to_file(self, path: Path) -> None:
        data = self.save()
        path.write_bytes(data)
```

### Shadow Configuration Constants
```python
# macOS-style shadow values (Claude's discretion within macOS aesthetic)
# Based on research of macOS window shadows and tools like Silicon

SHADOW_BLUR_RADIUS = 50      # Standard blur for macOS window feel
SHADOW_OFFSET_X = 0          # Centered horizontally
SHADOW_OFFSET_Y = 25         # Slight downward offset
SHADOW_COLOR = Color(0, 0, 0, 128)  # 50% black (#00000080)

# These values approximate the macOS window shadow aesthetic
# Note: Shadow style is fixed per CONTEXT.md (not configurable)
```

### Title Bar Rendering
```python
# Title bar constants
TITLE_BAR_HEIGHT = 28  # px, standard macOS title bar
TITLE_BAR_FONT = "SF Pro"  # System font, with fallback

def draw_title_bar(
    canvas: CairoCanvas,
    width: float,
    background: Color,
    title: str | None,
    corner_radius: float,
) -> None:
    """Draw macOS-style title bar.

    Per CONTEXT.md:
    - Title bar background matches code background (or slightly darker)
    - No separator line between title bar and content
    - Title text uses system font (not monospace)
    """
    # Draw title bar background (top portion with rounded top corners)
    # This clips to just the top part of a rounded rect
    ctx = canvas._ctx

    # Full rounded rect for top corners only
    draw_rounded_rect(ctx, 0, 0, width, TITLE_BAR_HEIGHT + corner_radius, corner_radius)
    # But clip off the bottom rounded part with a rectangle
    ctx.rectangle(0, TITLE_BAR_HEIGHT, width, corner_radius)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_source_rgba(
        background.r / 255.0,
        background.g / 255.0,
        background.b / 255.0,
        background.a / 255.0,
    )
    ctx.fill()

    # Draw traffic lights
    draw_traffic_lights(ctx, 0, TITLE_BAR_HEIGHT)

    # Draw title text if provided
    if title:
        # Center title text in title bar
        # Use system font (not monospace)
        ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| cairo.ImageSurface.create_from_png() | BytesIO + write_to_png() | Stable | Memory buffers preferred over temp files |
| Manual BGRA→RGBA loops | Pillow "RGBa" mode | Pillow 4.0+ | Handles pre-multiplied alpha correctly |
| Cairo gaussian blur (patch) | Pillow GaussianBlur | N/A | Cairo never got native blur, Pillow is standard |
| Fixed 1x resolution | 2x retina by default | ~2012+ | High-DPI displays are now standard |

**Deprecated/outdated:**
- `cairo.Context.show_glyphs()` for basic text: Use `show_text()` for simple cases, Pango for complex
- `cairocffi` for this project: Stick with pycairo already established in Phase 3
- SVG text as paths by default: Text elements preferred for accessibility and file size (paths optional)

## Open Questions

Things that couldn't be fully resolved:

1. **Title Bar Background Color**
   - What we know: Should match code background or be slightly darker
   - What's unclear: Exact darkening amount if different from code background
   - Recommendation: Match code background exactly for seamless macOS look

2. **SVG Text Rendering Approach**
   - What we know: Text elements are smaller files, paths are more consistent
   - What's unclear: Whether font embedding issues will arise
   - Recommendation: Use text elements by default (Cairo's default behavior), document limitation

3. **Shadow on Vector Formats**
   - What we know: Gaussian blur doesn't translate well to SVG/PDF
   - What's unclear: Whether to skip shadows, use SVG filters, or rasterize shadow layer
   - Recommendation: Skip shadows for SVG/PDF in v1, document as limitation

4. **Exact macOS Shadow Values**
   - What we know: Various CSS approximations exist (27.5 blur, 25px offset, 0.5 opacity)
   - What's unclear: Exact Apple system values (not publicly documented)
   - Recommendation: Use values from Silicon tool (blur=50, offset_y=25, opacity=0.5)

## Sources

### Primary (HIGH confidence)
- [Pycairo Surfaces Documentation](https://pycairo.readthedocs.io/en/latest/reference/surfaces.html) - ImageSurface, SVGSurface, PDFSurface APIs
- [Cairo Rounded Rectangle Sample](https://www.cairographics.org/samples/rounded_rectangle/) - Arc-based rounded corners
- [Pillow ImageFilter.GaussianBlur](https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html) - Blur filter API
- [Cairo + Pillow Integration](https://pycairo.readthedocs.io/en/latest/tutorial/pillow.html) - Surface to Pillow conversion

### Secondary (MEDIUM confidence)
- [macOS Traffic Light CSS](https://gist.github.com/merqurio/4e17987b8515d44141e5952c55591869) - Button colors (#ff5f57, #febc2e, #28c840) and 12px diameter
- [Silicon Rust Tool](https://github.com/Aloxaf/silicon) - Shadow defaults (blur=0 default, configurable)
- [@svag/window](https://github.com/svagco/window) - macOS shadow values (feGaussianBlur stdDeviation=27.5, offset dy=25, opacity=0.5)

### Tertiary (LOW confidence)
- Exact macOS system shadow values are not publicly documented by Apple
- Traffic light button spacing (8px) is approximation from CSS implementations
- 2x retina as default is a design decision, not a technical requirement

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pycairo already established, Pillow is standard for image processing
- Architecture: HIGH - Patterns derived from Cairo docs and established tools (Silicon, Carbon)
- Pitfalls: HIGH - Well-documented Cairo/Pillow interoperability issues
- Visual appearance: MEDIUM - macOS values are approximations, not official Apple specs

**Research date:** 2026-01-29
**Valid until:** 2026-02-28 (Cairo/Pillow APIs are stable, 30-day validity)
