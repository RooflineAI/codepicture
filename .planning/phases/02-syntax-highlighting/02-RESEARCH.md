# Phase 2: Syntax Highlighting - Research

**Researched:** 2026-01-28
**Domain:** Pygments tokenization, theme system, language detection
**Confidence:** HIGH

## Summary

Phase 2 implements syntax highlighting using Pygments for tokenization and a custom theme system that maps Pygments token types to colors. The standard approach is well-established: Pygments provides robust lexer and tokenization APIs, and its style system offers a clear pattern for mapping token types to visual attributes.

Key components:
1. **Highlighter** - Wraps Pygments lexer selection and tokenization with position tracking
2. **Theme** - Maps Pygments token types to TextStyle (color, bold, italic) with inheritance
3. **Theme Loader** - Loads built-in Pygments styles and custom TOML themes with inheritance support

**Primary recommendation:** Use Pygments directly via `get_lexer_by_name()`, `get_lexer_for_filename()`, and `get_tokens()`. For themes, wrap Pygments `Style.style_for_token()` with custom TOML loading and token inheritance.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pygments | 2.19.2 | Tokenization, lexers, built-in styles | De facto Python syntax highlighting library, 500+ languages, extensible |
| catppuccin[pygments] | 2.5.0 | Catppuccin color palettes + Pygments styles | Official Catppuccin Python implementation with Pygments integration |
| tomllib | stdlib (3.11+) | Parse custom theme TOML files | Python standard library, no external dependency |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tomli | 2.0+ | TOML parsing for Python <3.11 | Not needed - project requires Python 3.13+ |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pygments | tree-sitter | More accurate parsing but Python bindings less mature, overkill for this use case |
| tomllib | tomlkit | tomlkit preserves formatting but we only need read support |

**Installation:**
```bash
uv add pygments "catppuccin[pygments]"
# tomllib is stdlib, no install needed
```

## Architecture Patterns

### Recommended Project Structure
```
src/codepicture/
├── highlight/
│   ├── __init__.py         # Re-exports
│   ├── pygments_highlighter.py  # Highlighter protocol implementation
│   └── language_aliases.py      # Custom alias mappings (yml->yaml, etc.)
└── theme/
    ├── __init__.py         # Re-exports
    ├── loader.py           # Theme discovery and loading
    ├── pygments_theme.py   # Theme protocol implementation wrapping Pygments
    └── toml_theme.py       # Custom TOML theme parsing with inheritance
```

### Pattern 1: Token Position Tracking

**What:** Pygments `get_tokens()` returns `(token_type, text)` tuples without positions. Track positions manually while iterating.

**When to use:** Always - the CONTEXT.md requires source positions (line:column) for each token.

**Example:**
```python
# Source: Pygments get_tokens() returns flat stream, track positions ourselves
from pygments.lexers import get_lexer_by_name
from pygments.token import Token

def tokenize_with_positions(code: str, language: str) -> list[list[TokenInfo]]:
    """Tokenize code and track line:column positions."""
    lexer = get_lexer_by_name(language)
    lines: list[list[TokenInfo]] = [[]]
    line = 0
    column = 0

    for token_type, text in lexer.get_tokens(code):
        # Handle tokens that span multiple lines
        parts = text.split('\n')
        for i, part in enumerate(parts):
            if i > 0:  # Start a new line
                lines.append([])
                line += 1
                column = 0
            if part:  # Non-empty text
                lines[line].append(TokenInfo(
                    text=part,
                    token_type=token_type,
                    line=line,
                    column=column,
                ))
                column += len(part)

    return lines
```

### Pattern 2: Token Type Inheritance for Styling

**What:** Pygments token types form a hierarchy (e.g., `String.Escape in String` is True). Styles should inherit up the chain.

**When to use:** When looking up styles for token types - if no exact match, walk up the parent chain.

**Example:**
```python
# Source: Pygments token.py - tokens have .parent attribute and support 'in' operator
from pygments.token import Token

def get_style_for_token(token_type, style_map: dict) -> TextStyle:
    """Get style for token with inheritance fallback."""
    # Walk up the token hierarchy
    current = token_type
    while current is not None:
        if current in style_map:
            return style_map[current]
        current = current.parent
    # Fallback to base Token style
    return style_map.get(Token, DEFAULT_STYLE)
```

### Pattern 3: Theme TOML Format with Inheritance

**What:** Custom themes defined in TOML with optional `extends` to inherit from another theme.

**When to use:** For user-defined themes and shipping Catppuccin flavors.

**Example:**
```toml
# ~/.config/codepicture/themes/my-theme.toml
extends = "catppuccin-mocha"

[colors]
background = "#1a1a2e"
foreground = "#e0e0e0"

[tokens]
# Override specific tokens - unspecified tokens inherit from base
Keyword = { color = "#ff79c6", bold = true }
String = { color = "#50fa7b" }
Comment = { color = "#6272a4", italic = true }
```

### Anti-Patterns to Avoid

- **Caching lexers globally:** Lexers can have options that vary. Create new instances or use a keyed cache.
- **Assuming token colors exist:** Pygments `style_for_token()` may return `color=None` - always have a fallback.
- **Hardcoding aliases:** Pygments already handles most aliases (py->python, js->javascript). Only add missing ones.
- **Parsing TOML with regex:** Use `tomllib` - TOML syntax is more complex than it appears.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Language detection from extension | Filename -> language mapping | `get_lexer_for_filename()` | Pygments handles 500+ languages, multiple extensions per language, priority scoring |
| Language aliases (py, js, etc.) | Custom alias dict | `get_lexer_by_name()` handles aliases | Pygments already maps ~1000+ aliases across all languages |
| Token inheritance | Manual parent walking | `Style.style_for_token()` or `token in parent_token` | Pygments implements this correctly including `noinherit` |
| Color parsing | Regex for hex colors | Existing `Color.from_hex()` in types.py | Already handles #RGB, #RRGGBB, #RRGGBBAA |
| Built-in themes | Embed color palettes | `get_style_by_name()` | Dracula, Monokai, One Dark, Catppuccin all built-in |

**Key insight:** Pygments has been solving syntax highlighting for 20+ years. Its APIs handle edge cases we wouldn't think of. Wrap, don't reimplement.

## Common Pitfalls

### Pitfall 1: Missing Language Alias (yml)
**What goes wrong:** User specifies `--language yml` and gets an error
**Why it happens:** Pygments maps `yaml` but NOT `yml` as an alias
**How to avoid:** Maintain a small supplemental alias map for common user expectations
**Warning signs:** Test with common shorthand aliases before shipping

```python
# Supplemental aliases not in Pygments
EXTRA_ALIASES = {
    'yml': 'yaml',
    # Add others as users report them
}
```

### Pitfall 2: Whitespace Token Handling
**What goes wrong:** Whitespace renders as foreground color instead of invisible
**Why it happens:** `Token.Text.Whitespace` may have a color assigned in some themes
**How to avoid:** Don't apply foreground color to whitespace tokens (or make it configurable for visible whitespace feature)
**Warning signs:** Colored dots/arrows appearing where spaces should be invisible

### Pitfall 3: Multiline Token Splitting
**What goes wrong:** A single token spans multiple lines (e.g., multiline string), but output expects per-line tokens
**Why it happens:** Pygments returns tokens as-is, including `\n` characters in text
**How to avoid:** Split tokens on newlines while preserving token type
**Warning signs:** Line-based rendering breaks or positions are wrong

### Pitfall 4: Empty Lines After Tokenization
**What goes wrong:** Empty lines disappear from output or render incorrectly
**Why it happens:** No tokens exist for empty lines (or only a newline character)
**How to avoid:** Ensure line list always contains an entry for each line, even if empty
**Warning signs:** Line numbers don't match original source

### Pitfall 5: Theme Style None Values
**What goes wrong:** TypeError when trying to use `color` that is `None`
**Why it happens:** Pygments `style_for_token()` returns `{'color': None}` for unstyled tokens
**How to avoid:** Always fall back to foreground color when color is None
**Warning signs:** Crashes on uncommon token types

## Code Examples

Verified patterns from Pygments source and official documentation:

### Getting a Lexer Safely
```python
# Source: Pygments lexers/__init__.py
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
from pygments.util import ClassNotFound
from codepicture.errors import HighlightError

def get_lexer(language: str | None, filename: str | None) -> Lexer:
    """Get lexer by language name or filename.

    Args:
        language: Explicit language (takes precedence)
        filename: Filename for extension-based detection

    Raises:
        HighlightError: If language unknown or can't be detected
    """
    # Check supplemental aliases first
    if language and language.lower() in EXTRA_ALIASES:
        language = EXTRA_ALIASES[language.lower()]

    try:
        if language:
            return get_lexer_by_name(language)
        elif filename:
            return get_lexer_for_filename(filename)
        else:
            raise HighlightError("No language specified and no filename for detection")
    except ClassNotFound as e:
        available = list_available_languages()
        raise HighlightError(
            f"Unknown language: {language or filename}. "
            f"Available: {', '.join(sorted(available)[:20])}..."
        ) from e
```

### Extracting Style from Pygments Style Class
```python
# Source: Pygments style.py - style_for_token returns dict with color, bold, italic, etc.
from pygments.styles import get_style_by_name
from pygments.token import Token
from codepicture.core.types import Color, TextStyle

def extract_text_style(pygments_style, token_type) -> TextStyle:
    """Convert Pygments style dict to TextStyle."""
    style_dict = pygments_style.style_for_token(token_type)

    # Color is hex string without # or None
    color_hex = style_dict.get('color')
    if color_hex:
        color = Color.from_hex(f"#{color_hex}")
    else:
        # Fallback to foreground
        color = Color.from_hex(pygments_style.background_color or "#ffffff")

    return TextStyle(
        color=color,
        bold=style_dict.get('bold', False),
        italic=style_dict.get('italic', False),
        underline=style_dict.get('underline', False),
    )
```

### Loading Theme with Inheritance
```python
# Source: Application-specific pattern for TOML theme inheritance
import tomllib
from pathlib import Path

def load_theme_toml(path: Path, base_themes: dict[str, Theme]) -> Theme:
    """Load theme from TOML with optional inheritance."""
    with open(path, 'rb') as f:
        data = tomllib.load(f)

    # Handle inheritance
    if 'extends' in data:
        base_name = data['extends']
        if base_name not in base_themes:
            raise ThemeError(f"Unknown base theme: {base_name}")
        base = base_themes[base_name]
    else:
        base = None

    # Build token styles, inheriting from base if not specified
    # ... implementation details
```

### Listing Available Languages
```python
# Source: Pygments lexers/__init__.py - get_all_lexers()
from pygments.lexers import get_all_lexers

def list_available_languages() -> list[str]:
    """Return sorted list of all language aliases."""
    aliases = set()
    for name, alias_list, patterns, mimetypes in get_all_lexers():
        aliases.update(alias_list)
    return sorted(aliases)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pygments TextFormatter | Direct token iteration | Always available | Don't use formatters - they're for output formats, not data extraction |
| Python 2 style strings | Python 3 only | Pygments 2.0 | All our code is Python 3.13+ |
| Manual style dict | `style_for_token()` method | Pygments 2.x | Use the method, it handles inheritance |

**Deprecated/outdated:**
- `Python3Lexer`: Use `PythonLexer` (they're the same now, Python3Lexer is alias)
- Manually accessing `Style.styles` dict: Use `style_for_token()` instead

## Open Questions

Things that couldn't be fully resolved:

1. **TOML Theme File Format Standardization**
   - What we know: Need to support `extends`, `[colors]`, and `[tokens]` sections
   - What's unclear: Exact mapping from TOML token names to Pygments token types (e.g., "Keyword" vs "Token.Keyword")
   - Recommendation: Accept both forms, normalize to Pygments token types on load

2. **Visible Whitespace Token Type**
   - What we know: CONTEXT.md wants `visible whitespace option: for spaces, for tabs`
   - What's unclear: Should these be separate token types or just string replacement before tokenization?
   - Recommendation: Post-process whitespace tokens after tokenization, replacing chars while preserving token type

3. **Catppuccin Source: Package vs Embedded**
   - What we know: catppuccin[pygments] provides styles via `get_style_by_name()`
   - What's unclear: Should we depend on the package or embed the palettes in our TOML files?
   - Recommendation: Use the package (simpler, auto-updates) but allow override via user themes

## Sources

### Primary (HIGH confidence)
- Pygments 2.19.2 source code (token.py, style.py, lexers/__init__.py) - Direct inspection of installed package
- [Pygments API Documentation](https://pygments.org/docs/api/) - Lexer selection and tokenization
- [Pygments Token Types](https://pygments.org/docs/tokens/) - Token hierarchy and standard types
- [Pygments Style Development](https://pygments.org/docs/styledevelopment/) - Custom style creation

### Secondary (MEDIUM confidence)
- [Catppuccin Python Package](https://github.com/catppuccin/python) - Pygments integration confirmed via PyPI
- catppuccin 2.5.0 installed and tested - All 4 flavors work with `get_style_by_name()`

### Tertiary (LOW confidence)
- Custom TOML theme format is application-specific design, not an external standard

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Pygments is the de facto standard, verified APIs work as documented
- Architecture: HIGH - Patterns derived directly from Pygments source and official docs
- Pitfalls: MEDIUM - Based on inspection and testing, but real-world usage may reveal more

**Research date:** 2026-01-28
**Valid until:** 2026-02-28 (Pygments is stable, 30-day validity)
