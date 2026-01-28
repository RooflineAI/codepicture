# Stack Research

**Domain:** Python CLI code screenshot/image generation tool
**Researched:** 2026-01-28
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python | 3.13+ | Runtime | Project specifies 3.13; PyCairo 1.29.0 requires 3.10+; all core libraries support 3.13 | HIGH |
| PyCairo | 1.29.0 | 2D vector graphics rendering | Industry-standard for high-quality vector graphics; outputs PNG, SVG, PDF natively; mature and stable | HIGH |
| PyGObject | 3.54.5 | Access to Pango text layout | Required for PangoCairo text rendering; provides professional text layout with kerning, ligatures, and multi-script support | HIGH |
| Pygments | 2.19.2 | Syntax highlighting | De facto standard for Python syntax highlighting; 598+ languages; outputs tokenized text for custom rendering | HIGH |
| Typer | 0.21.1 | CLI framework | Modern CLI framework using type hints; built on Click; auto-completion; Rich integration for beautiful output | HIGH |
| Pydantic | 2.12.5 | Configuration/validation | Type-safe configuration schemas; validation with clear error messages; serialization for config files | HIGH |

### Rendering Stack Detail

| Component | Library | Role | Notes |
|-----------|---------|------|-------|
| Graphics Engine | PyCairo | Renders shapes, shadows, rounded corners | Outputs to PNG, SVG, PDF directly |
| Text Layout | PangoCairo (via PyGObject) | Professional text rendering | Handles fonts, kerning, line wrapping |
| Syntax Parsing | Pygments | Tokenizes code by language | Returns token stream with style info |
| Color Themes | Pygments styles | Provides syntax colors | 50+ built-in styles (Monokai, Dracula, etc.) |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Rich | 14.3.1 | Terminal output formatting | CLI progress bars, error display, tables; bundled with Typer |
| Pillow | 12.1.0 | Image manipulation (optional) | Only if post-processing PNG output (resize, composite); not for primary rendering |
| CairoSVG | 2.8.2 | SVG to PNG/PDF conversion | Only if accepting SVG input; not needed for SVG output (Cairo does that) |
| ReportLab | 4.4.9 | Advanced PDF features (optional) | Only if needing PDF metadata, bookmarks, or multi-page documents |

### Development Tools

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| pytest | 9.0.2 | Testing framework | Use `typer.testing.CliRunner` for CLI tests |
| pytest-image-snapshot | 0.4.5 | Visual regression testing | Compare generated images against reference snapshots |
| ruff | 0.14.14 | Linting + formatting | Replaces flake8, isort, black; extremely fast (Rust-based) |
| mypy | 1.19.1 | Static type checking | Validates Pydantic models and type hints |
| uv | latest | Package/project management | Fast dependency resolution; lockfile support |

## Installation

```bash
# Core dependencies (using uv)
uv add pycairo pygobject pygments typer pydantic

# Or with pip
pip install pycairo pygobject pygments typer pydantic

# Dev dependencies
uv add --dev pytest pytest-image-snapshot ruff mypy

# System dependencies (required before pip install)
# macOS:
brew install cairo pango gobject-introspection pkg-config

# Ubuntu/Debian:
sudo apt-get install libcairo2-dev libpango1.0-dev libgirepository1.0-dev

# Fedora:
sudo dnf install cairo-devel pango-devel gobject-introspection-devel
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| PyCairo + PangoCairo | Pillow (PIL) | Simple image manipulation only; Pillow lacks vector output (no SVG/PDF) and has inferior text rendering (no kerning, poor multi-line support) |
| PyCairo + PangoCairo | Pygments ImageFormatter | Quick prototypes only; uses Pillow internally; limited customization; cannot produce SVG/PDF |
| PyCairo + PangoCairo | Playwright (browser rendering) | When you need exact browser CSS rendering; adds ~100MB dependency; requires browser install; slower |
| PyCairo + PangoCairo | svgwrite | SVG-only output; no PNG/PDF; unmaintained as of 2025 |
| Typer | Click | Legacy projects; Typer wraps Click with better ergonomics |
| Typer | argparse | Stdlib-only constraints; missing auto-completion and Rich integration |
| Pydantic | dataclasses | Simpler needs; lacks validation, serialization, schema generation |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Pillow for primary rendering | Cannot output SVG or PDF; text rendering lacks kerning and proper line wrapping; limited font control | PyCairo + PangoCairo |
| Pygments ImageFormatter alone | Uses Pillow internally; no SVG/PDF; limited window chrome customization | Use Pygments for tokenization only, render with Cairo |
| pangocairocffi | Incomplete CFFI bindings; difficult to work with; PyGObject is the maintained approach | PyGObject for PangoCairo access |
| svgwrite | Unmaintained (GitHub says "UNMAINTAINED"); Cairo can output SVG directly | PyCairo with SVGSurface |
| Playwright/Selenium | Massive dependencies (~100MB+); requires browser; network latency if using web service; overkill for code screenshots | PyCairo renders locally, no browser needed |
| Click directly | More verbose than Typer; requires decorator boilerplate; Typer provides better DX | Typer (built on Click) |
| Python 3.9-3.10 | PyCairo 1.29.0 dropped Python 3.9 support (Nov 2025); pytest 9.0 requires 3.10+ | Python 3.13+ |

## Stack Patterns

**Standard Pattern (Recommended):**
```
Code Input -> Pygments (tokenize) -> Token Stream
                                         |
                                         v
                           PangoCairo (layout text with colors)
                                         |
                                         v
                           PyCairo (draw window chrome, shadows)
                                         |
                                         v
                           Output: PNG / SVG / PDF
```

**If SVG input/processing needed:**
```
SVG Input -> CairoSVG (parse) -> Cairo operations -> Output
```

**If PDF with metadata needed:**
```
Cairo PNG/SVG -> ReportLab (embed, add metadata) -> Final PDF
```

## Version Compatibility Matrix

| Package | Min Python | Max Python | Notes |
|---------|------------|------------|-------|
| PyCairo 1.29.0 | 3.10 | 3.14 | Dropped 3.9 in Nov 2025 |
| PyGObject 3.54.5 | 3.9 | 3.14 | Requires system GObject libs |
| Pygments 2.19.2 | 3.8 | 3.13 | Very stable |
| Typer 0.21.1 | 3.9 | 3.14 | Includes Rich by default |
| Pydantic 2.12.5 | 3.9 | 3.14 | Use v2, not v1 |
| pytest 9.0.2 | 3.10 | 3.14 | Dropped 3.9 in Dec 2025 |
| Pillow 12.1.0 | 3.10 | 3.14 | Optional; dropped 3.9 |

**Minimum viable Python: 3.10** (PyCairo, pytest constraint)
**Recommended Python: 3.13** (project spec; all libs support it)

## System Dependencies

Cairo and Pango are C libraries. PyCairo and PyGObject are Python bindings that require:

| Platform | Required Packages | Install Command |
|----------|------------------|-----------------|
| macOS | cairo, pango, gobject-introspection, pkg-config | `brew install cairo pango gobject-introspection pkg-config` |
| Ubuntu/Debian | libcairo2-dev, libpango1.0-dev, libgirepository1.0-dev | `apt-get install libcairo2-dev libpango1.0-dev libgirepository1.0-dev` |
| Fedora | cairo-devel, pango-devel, gobject-introspection-devel | `dnf install cairo-devel pango-devel gobject-introspection-devel` |
| Alpine | cairo-dev, pango-dev, gobject-introspection-dev | `apk add cairo-dev pango-dev gobject-introspection-dev` |

**Note:** These must be installed BEFORE `pip install pycairo pygobject`. The Python packages compile against these headers.

## Font Considerations

PangoCairo uses system fonts. For consistent cross-platform rendering:

| Approach | Pros | Cons |
|----------|------|------|
| Bundle fonts (e.g., JetBrains Mono, Fira Code) | Consistent output everywhere | Increases package size; licensing considerations |
| Use system fonts with fallbacks | No bundling needed | Output varies by system |
| Specify font stack | Best of both worlds | Requires font availability logic |

**Recommendation:** Bundle a single high-quality monospace font (JetBrains Mono is OFL-licensed, supports ligatures) and use it as default, with fallback to system monospace.

## Testing Strategy

| Test Type | Tool | Purpose |
|-----------|------|---------|
| Unit tests | pytest | Test token parsing, color calculation, config validation |
| CLI tests | pytest + typer.testing.CliRunner | Test CLI argument parsing, output files created |
| Visual regression | pytest-image-snapshot | Compare generated images to reference snapshots |
| Type checking | mypy | Validate Pydantic models and function signatures |

```python
# Example CLI test
from typer.testing import CliRunner
from codepicture.cli import app

runner = CliRunner()

def test_generates_png():
    result = runner.invoke(app, ["input.py", "-o", "output.png"])
    assert result.exit_code == 0
    assert Path("output.png").exists()
```

## Sources

**Package Versions (verified via PyPI, Jan 2026):**
- [PyCairo 1.29.0](https://pypi.org/project/pycairo/) - Python 3.10+, released Nov 2025
- [PyGObject 3.54.5](https://pypi.org/project/PyGObject/) - Python 3.9+, released Oct 2025
- [Pygments 2.19.2](https://pypi.org/project/Pygments/) - Python 3.8+, released Jun 2025
- [Typer 0.21.1](https://pypi.org/project/typer/) - Python 3.9+, released Jan 2026
- [Pydantic 2.12.5](https://pypi.org/project/pydantic/) - Python 3.9+, released Nov 2025
- [pytest 9.0.2](https://pypi.org/project/pytest/) - Python 3.10+, released Dec 2025
- [Rich 14.3.1](https://pypi.org/project/rich/) - Python 3.8+, released Jan 2026
- [Pillow 12.1.0](https://pypi.org/project/Pillow/) - Python 3.10+, released Jan 2026
- [ruff 0.14.14](https://pypi.org/project/ruff/) - Python 3.7+, released Jan 2026
- [mypy 1.19.1](https://pypi.org/project/mypy/) - Python 3.9+, released Dec 2025

**Architecture References:**
- [PyCairo + Pango integration](https://aperiodic.net/pip/archives/Geekery/cairo-pango-python/) - PyGObject approach (HIGH confidence)
- [Pygments formatters](https://pygments.org/docs/formatters/) - Official docs (HIGH confidence)
- [Typer testing](https://typer.tiangolo.com/tutorial/testing/) - Official docs (HIGH confidence)
- [pytest-image-snapshot](https://github.com/bmihelac/pytest-image-snapshot) - Visual testing plugin

**Ecosystem Research:**
- [Real Python code image generator tutorial](https://realpython.com/python-code-image-generator/) - Flask+Playwright approach (not recommended for CLI)
- [Silicon (Rust)](https://github.com/Aloxaf/silicon) - Reference for feature set; local rendering, no browser
- [Carbon.now.sh](https://carbon.now.sh/) - Reference for UI/UX; web-based approach

---
*Stack research for: Python CLI code screenshot tool*
*Researched: 2026-01-28*
*Overall confidence: HIGH - All versions verified via PyPI; architecture validated against official documentation*
