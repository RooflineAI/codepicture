# Pitfalls Research

**Domain:** Code Screenshot / Code Image Generation Tool
**Researched:** 2026-01-28
**Confidence:** MEDIUM-HIGH (verified via WebSearch with multiple sources, some Cairo/Pango specifics from official docs)

## Critical Pitfalls

### Pitfall 1: Using Cairo's "Toy" Text API Instead of Pango

**What goes wrong:**
The application uses Cairo's built-in text rendering functions (`show_text`, `text_path`, `text_extents`) which are explicitly labeled as a "toy API" by Cairo documentation. This results in:
- No support for complex scripts (Arabic, Hebrew, Indic scripts)
- No kerning or diacritical mark positioning
- Limited font selection that doesn't handle fallback fonts
- Broken rendering for non-Latin code comments/strings

**Why it happens:**
Cairo's text API is simpler to use initially. Developers find `context.show_text("Hello")` in tutorials and use it without realizing its limitations. The toy API works fine for ASCII-only demos but fails in production.

**How to avoid:**
Use PangoCairo from the start. Access via PyGObject:
```python
import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo
```
This provides proper text shaping, font fallback, and Unicode support.

**Warning signs:**
- Characters appearing as boxes or question marks
- Inconsistent spacing between characters
- Comments in non-Latin scripts rendering incorrectly
- Font weight/style not applying correctly

**Phase to address:**
Phase 1 (Foundation) - Must be architected correctly from the beginning. Retrofitting Pango onto a Cairo toy-API codebase is a significant rewrite.

---

### Pitfall 2: Hardcoded Pixel Dimensions Without DPI/Scale Factor Support

**What goes wrong:**
Images look blurry or pixelated on Retina/HiDPI displays. Or conversely, images are 4x larger than expected on high-DPI systems. Text appears at inconsistent sizes across different machines.

**Why it happens:**
Developers test on a single display type (usually 1x DPI) and hardcode pixel values. Cairo surfaces are created at fixed sizes without accounting for `set_device_scale()`.

**How to avoid:**
1. Always expose a scale factor parameter (default 2x for Retina-quality output)
2. Use `surface.set_device_scale(scale, scale)` to handle HiDPI correctly
3. Work in logical coordinates internally, convert to physical pixels at surface creation
4. Test on both 1x and 2x displays

```python
# Good pattern
def create_surface(width, height, scale=2):
    surface = cairo.ImageSurface(
        cairo.FORMAT_ARGB32,
        int(width * scale),
        int(height * scale)
    )
    surface.set_device_scale(scale, scale)
    return surface  # Now draw using logical coordinates
```

**Warning signs:**
- Images look "crisp" on dev machine but blurry in presentations
- File sizes unexpectedly large or small
- Users complaining about "low quality" output

**Phase to address:**
Phase 1 (Foundation) - Surface creation is foundational. Add `--scale` CLI option early.

---

### Pitfall 3: Shadow Blur Implementation from Scratch (No Native Cairo Support)

**What goes wrong:**
Developers assume Cairo has built-in shadow/blur effects like CSS `box-shadow`. It does not. They either:
1. Skip shadows entirely (resulting in flat, unprofessional images)
2. Implement naive blur algorithms that are slow or incorrect
3. Create hard-edged shadows that look dated

**Why it happens:**
Every other graphics library (CSS, SVG, Figma) has drop shadows as a primitive. Cairo intentionally omits this for simplicity. The feature gap is not obvious until implementation.

**How to avoid:**
Plan for blur implementation from the start. Options:
1. Use the Cairo Cookbook's Gaussian blur C implementation (adapted for Python)
2. Apply box blur 3 times (approximates Gaussian blur, much faster)
3. Use the Cairou library which provides blur filters
4. Pre-render shadow as a separate layer, blur with Pillow, composite back

Recommended approach for Python:
```python
# Use Pillow for blur, composite with Cairo
from PIL import Image, ImageFilter

def add_shadow(surface, blur_radius=10, offset=(5, 5), opacity=0.5):
    # Export Cairo surface to PIL
    # Apply GaussianBlur
    # Composite shadow layer under main content
```

**Warning signs:**
- Shadows taking seconds to render
- Shadows appearing blocky or banded
- No shadow option in MVP (users notice immediately)

**Phase to address:**
Phase 2 (Visual Polish) - Shadows are expected but can ship MVP without. Prototype early to validate approach.

---

### Pitfall 4: Tab Character Width Inconsistency

**What goes wrong:**
Code containing tab characters renders with wrong indentation. Python code that looks correct in an editor appears mangled in the image because tabs render as 8 spaces (or 1, or 4, depending on font/system).

**Why it happens:**
Tab width is not standardized - different systems/fonts/editors use different widths. Developers test with space-indented code and miss the issue entirely. When tabs are encountered, the rendering falls back to system defaults.

**How to avoid:**
1. Normalize tabs to spaces before rendering (configurable tab width, default 4)
2. Document this behavior and provide `--tab-width` CLI option
3. Use Pango's `set_tabs()` method for explicit tab stop control if preserving tabs

```python
def normalize_tabs(code: str, tab_width: int = 4) -> str:
    """Convert tabs to spaces for consistent rendering."""
    return code.replace('\t', ' ' * tab_width)
```

**Warning signs:**
- Go or Makefile code looking wrong (these use tabs)
- Inconsistent indentation between lines
- User-reported "my code looks broken" issues

**Phase to address:**
Phase 1 (Foundation) - Part of input processing pipeline.

---

### Pitfall 5: Pygments Lexer Regex Catastrophic Backtracking

**What goes wrong:**
Certain inputs cause Pygments to hang "forever" or consume excessive memory, making the CLI unresponsive. This is especially problematic with malformed or adversarial input.

**Why it happens:**
Pygments lexers are regex-based. Some patterns can exhibit exponential backtracking on certain inputs. Pygments documentation explicitly warns: "Pygments provides no guarantees on execution time."

**How to avoid:**
1. Implement a timeout for syntax highlighting (5-10 seconds max)
2. Catch and gracefully handle timeout, fall back to plain text
3. For custom lexers (like MLIR), test extensively with fuzzing
4. Consider input length limits for CLI use

```python
import signal

def highlight_with_timeout(code, lexer, timeout=5):
    def handler(signum, frame):
        raise TimeoutError("Syntax highlighting timed out")

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    try:
        return pygments.highlight(code, lexer, formatter)
    except TimeoutError:
        return plain_text_fallback(code)
    finally:
        signal.alarm(0)
```

**Warning signs:**
- CLI hanging on certain inputs
- Memory usage spiking
- User reports of "stuck" processing

**Phase to address:**
Phase 2 or Phase 3 - After basic highlighting works. Custom MLIR lexer phase should include timeout protection.

---

### Pitfall 6: Font Embedding Assumptions in SVG/PDF Output

**What goes wrong:**
SVG or PDF output looks correct on the developer's machine but wrong on users' machines because fonts aren't embedded. Users see fallback fonts (often serif fonts for code, which looks terrible).

**Why it happens:**
Cairo/CairoSVG doesn't embed fonts in SVG - SVG format wasn't designed for font embedding. PDF embedding works but requires fonts to be installed on the rendering system. Developers test locally where fonts exist.

**How to avoid:**
For SVG:
1. Convert text to paths (loses editability but guarantees rendering)
2. Or: Document font requirements clearly
3. Or: Provide base64-embedded WOFF in CSS within SVG

For PDF:
1. Use fonts that can be embedded (check licensing)
2. Verify embedding with `pdffonts` tool
3. Test on a clean system without dev fonts

**Warning signs:**
- SVG files rendering differently in browsers vs Inkscape
- PDF code appearing in Times New Roman
- User reports of "weird fonts"

**Phase to address:**
Phase 3 (Multi-format output) - Address when implementing SVG/PDF export.

---

### Pitfall 7: MLIR Custom Lexer Incomplete Coverage

**What goes wrong:**
The MLIR lexer highlights some constructs correctly but misses others, resulting in inconsistent or incorrect coloring. New MLIR dialects/operations appear unhighlighted.

**Why it happens:**
MLIR is a rapidly evolving ecosystem with many dialects. Existing Pygments MLIR lexers explicitly note they are "incomplete and support mostly core IR with a subset of built-in types."

**How to avoid:**
1. Start with an existing MLIR lexer as base (LLVM project has one: PR #120942)
2. Document which dialects are supported
3. Design lexer to gracefully handle unknown operations (highlight as generic identifier)
4. Include escape hatch for users to add dialect-specific patterns

**Warning signs:**
- Some MLIR operations appearing as plain text
- Inconsistent highlighting between dialects
- User reports of missing highlighting for their dialect

**Phase to address:**
Dedicated MLIR Lexer Phase - Custom lexer development should be its own milestone with testing.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using Cairo toy text API | Faster initial implementation | Complete rewrite for i18n support | Never for production |
| Hardcoded theme colors | Quick to implement | Every new theme requires code changes | MVP only, then refactor to config |
| Synchronous rendering | Simpler code | CLI freezes on large files | MVP only if files are small |
| Skip input validation | Faster development | Crashes on edge cases | Never |
| PIL for all image ops | Single dependency | Slower, less vector support | When Cairo is too complex |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Pygments + Pango | Assuming token positions map directly to rendered positions | Re-measure text after Pango shaping; tokens are logical, not visual |
| Cairo + SVG export | Expecting pixel-perfect SVG | Accept vector approximation; test in target renderers |
| Typer + Rich | Importing Rich eagerly | Lazy-load Rich to avoid 200ms+ startup penalty |
| Pango font selection | Using "Times New Roman 14" format | Use "Times New Roman, 14" (comma!) - "Roman" is also a style keyword |
| Cairo context + Pango layout | Modifying Cairo CTM after layout creation | Call `PangoCairo.update_layout()` after any CTM changes |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Re-creating Pango layouts per line | Slow rendering, 2+ seconds for 50 lines | Reuse layout, just update text | > 20 lines of code |
| Full Gaussian blur per frame | 500ms+ shadow rendering | Box blur 3x, or pre-render shadow layer | Any shadow usage |
| Loading fonts on every render | Noticeable delay per image | Cache font descriptions | Multiple images in sequence |
| Eager Pygments lexer loading | 100ms+ startup for unused lexers | Use `get_lexer_by_name()` lazily | Any CLI invocation |
| Not caching Catppuccin color parsing | Repeated hex-to-RGB conversion | Parse once at theme load | Negligible, but adds up |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| No input size limit | DoS via massive file input | Limit input to reasonable size (1MB?) |
| No highlighting timeout | DoS via pathological regex input | 5-10 second timeout, fallback to plain text |
| Executing code from input | RCE if input is parsed as code | Treat all input as pure data |
| Trusting filename for lexer selection | Misleading extension causes confusion | Allow explicit lexer override |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No line number option | Users manually add line numbers | Provide `--line-numbers` flag |
| Fixed window width | Long lines wrap awkwardly or get cut | Auto-size to content, or provide width option |
| No padding/margin control | Images feel cramped | Sensible defaults (16-24px) with override options |
| Only light theme | Dark-themed code looks washed out | Default to dark theme (Catppuccin Mocha) |
| No way to highlight specific lines | Can't emphasize code sections | Support line highlighting syntax |
| Ignoring stdin | Can't pipe code to tool | Support `codepicture - < file.py` |

## "Looks Done But Isn't" Checklist

- [ ] **Syntax highlighting:** Works with ASCII but breaks on Unicode operators (Haskell, APL)
- [ ] **Font rendering:** Looks good with Latin but boxes for CJK characters
- [ ] **Line numbers:** Aligned for single digits but misaligned for 100+ lines
- [ ] **Window controls:** Traffic lights look right at 1x but blurry at 2x scale
- [ ] **Theme:** Colors correct for keywords but wrong for string interpolation
- [ ] **Tab handling:** Tested with spaces but tabs render as 8-wide
- [ ] **Empty lines:** Code with blank lines renders correctly
- [ ] **Trailing whitespace:** Doesn't cause extra width in output
- [ ] **Very long lines:** Either wrap or scroll, not break layout
- [ ] **Single-line input:** Produces valid image, not error

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Cairo toy API for text | HIGH | Rewrite text rendering layer with Pango; preserve API |
| No DPI support | MEDIUM | Add scale parameter to surface creation; update all dimension calculations |
| Hardcoded theme | LOW | Extract colors to config dict; update references |
| No timeout on highlighting | LOW | Wrap highlight call with signal-based timeout |
| Tab handling broken | LOW | Add normalize_tabs() in input processing |
| Missing shadow blur | MEDIUM | Add Pillow-based blur layer; composite with Cairo |
| Font embedding issues | MEDIUM | Add text-to-path option for SVG; verify PDF embedding |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Cairo toy text API | Phase 1 (Foundation) | Test with Unicode: `"def foo(): # \u4e2d\u6587"` renders correctly |
| DPI/scale issues | Phase 1 (Foundation) | Compare 1x and 2x output; text remains sharp at both |
| Shadow blur | Phase 2 (Visual Polish) | Shadow has soft edges, renders in < 100ms |
| Tab width | Phase 1 (Foundation) | Makefile renders with correct indentation |
| Pygments timeout | Phase 3 (Robustness) | Pathological input doesn't hang CLI |
| Font embedding | Phase 4 (Multi-format) | SVG renders correctly on fresh machine |
| MLIR lexer incomplete | MLIR Phase | Test with MLIR samples from major dialects |
| Traffic light fidelity | Phase 2 (Visual Polish) | macOS buttons match real window at 2x scale |
| Line number alignment | Phase 2 (Features) | 3-digit line numbers align correctly |
| Catppuccin theme accuracy | Phase 2 (Theming) | Compare output to official Catppuccin screenshots |

## Sources

- [Cairo Pango Cookbook](https://www.cairographics.org/cookbook/pycairo_pango/) - Authoritative on Cairo+Pango integration
- [Pycairo Text Documentation](https://pycairo.readthedocs.io/en/latest/reference/text.html) - Official warning about toy API
- [Pygments FAQ](https://pygments.org/faq/) - Security and performance warnings
- [LLVM MLIR Pygments Lexer PR](https://github.com/llvm/llvm-project/pull/120942) - Reference MLIR lexer
- [Cairo Gaussian Blur Cookbook](https://www.cairographics.org/cookbook/) - Blur implementation approaches
- [Steve Hanov's Cairo Blur](https://stevehanov.ca/blog/index.php?id=53) - Public domain blur implementation
- [PangoCairo Tutorial](http://jcoppens.com/soft/howto/pygtk/pangocairo.en.php) - Font description gotchas
- [Catppuccin Style Guide Discussion](https://github.com/catppuccin/catppuccin/pull/2109) - Theme consistency issues
- [Typer Performance Discussion](https://github.com/fastapi/typer/discussions/744) - Rich import latency
- [DEV: Problems with Code Screenshots](https://dev.to/savvasstephnds/the-problem-with-code-screenshots-and-how-to-fix-it-2ka0) - Accessibility concerns
- [Carbon GitHub](https://github.com/carbon-app/carbon) - Reference tool limitations
- [Silicon GitHub](https://github.com/Aloxaf/silicon) - Rust alternative learnings
- [Matplotlib HiDPI Issue](https://github.com/matplotlib/matplotlib/issues/21024) - Cairo HiDPI handling

---
*Pitfalls research for: Code Screenshot / Code Image Generation (Python CLI)*
*Researched: 2026-01-28*
