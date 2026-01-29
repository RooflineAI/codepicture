# Phase 6: MLIR Lexer - Research

**Researched:** 2026-01-29
**Domain:** Sublime syntax parsing, Pygments custom lexer integration, MLIR syntax highlighting
**Confidence:** HIGH

## Summary

Phase 6 implements MLIR syntax highlighting by integrating a Sublime syntax file with the existing Pygments-based highlighting pipeline. Research identified two viable approaches: (1) a simple Pygments `RegexLexer` that directly translates the MLIR syntax patterns, or (2) a full Sublime syntax parser using `onigurumacffi` for regex compatibility.

Key findings:
1. **LLVM has an official MLIR Pygments lexer** in `mlir/utils/pygments/mlir_lexer.py` - a simple 37-line RegexLexer that covers core MLIR constructs
2. **The existing Sublime syntax file** (222 lines) is more comprehensive but requires a state machine parser
3. **onigurumacffi** (v1.4.1, Jan 2025) provides Python bindings for Oniguruma regex, enabling Sublime syntax compatibility
4. **pysyntect** (Python bindings for syntect) is unmaintained and lacks Python 3.11+ wheels

**Primary recommendation:** Implement a Pygments RegexLexer based on the LLVM approach but enhanced with patterns from the existing Sublime syntax file. This provides 80% coverage with 20% effort, matching the CONTEXT.md requirement for graceful fallback on unrecognized constructs.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pygments | 2.19+ | Lexer base class, token types | Already in project dependencies, proven integration |
| pyyaml | 6.0+ | Parse sublime-syntax YAML (if parsing approach used) | Standard YAML parser, handles most sublime-syntax files |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| onigurumacffi | 1.4.1 | Oniguruma regex engine bindings | Only if full sublime-syntax parser needed |
| ruamel.yaml | 0.18+ | YAML parsing with better compatibility | If pyyaml fails on edge cases |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom RegexLexer | pysyntect (syntect bindings) | pysyntect unmaintained, no Python 3.11+ wheels |
| Hand-rolled patterns | LLVM mlir_lexer.py | LLVM lexer is minimal, misses dialect-specific patterns |
| RegexLexer | Full sublime-syntax parser | Parser is complex (~500+ lines), overkill for single language |

**Installation:**
```bash
# Minimal approach (recommended)
# No new dependencies - uses existing pygments

# Full sublime-syntax approach (if needed later)
uv add onigurumacffi pyyaml
```

## Architecture Patterns

### Recommended Project Structure
```
src/codepicture/
├── highlight/
│   ├── __init__.py              # Re-exports
│   ├── pygments_highlighter.py  # Main highlighter
│   ├── language_aliases.py      # Alias mappings
│   └── mlir_lexer.py           # Custom MLIR Pygments lexer
├── syntaxes/                    # NEW: Bundled syntax files
│   └── MLIR.sublime-syntax      # Copied from ~/.config/silicon/
```

### Pattern 1: Custom Pygments Lexer for MLIR

**What:** A `RegexLexer` subclass with MLIR-specific patterns mapped to Pygments token types.

**When to use:** Always - this is the integration point with the existing highlight pipeline.

**Example:**
```python
# Source: Derived from LLVM mlir/utils/pygments/mlir_lexer.py
from pygments.lexer import RegexLexer, bygroups
from pygments.token import (
    Comment, Keyword, Name, Number, Operator, Punctuation, String, Text
)

class MlirLexer(RegexLexer):
    """Lexer for MLIR intermediate representation."""

    name = 'MLIR'
    aliases = ['mlir']
    filenames = ['*.mlir']

    tokens = {
        'root': [
            # Comments
            (r'//.*$', Comment.Single),

            # SSA values: %name, %0, %arg0
            (r'%[\w\.\$\:\#]+', Name.Variable),

            # Block labels: ^bb0, ^entry
            (r'\^[\w\d_$\.\-]+', Name.Label),

            # Function/symbol references: @main, @"quoted name"
            (r'@[\w+\$\-\.]+', Name.Function),
            (r'@"[^"]*"', Name.Function),

            # Attribute aliases: #map, #set
            (r'#[\w\$\-\.]+', Name.Constant),

            # Type aliases and types: !type, !dialect.type<...>
            (r'![\w\$\-\.]+', Keyword.Type),

            # Built-in types: i32, f64, index, memref
            (r'\b(index|none|bf16|f16|f32|f64|f80|f128)\b', Keyword.Type),
            (r'\b[su]?i[0-9]+\b', Keyword.Type),
            (r'\b(memref|tensor|vector|complex|tuple)\b', Keyword.Type),

            # Operations: dialect.operation
            (r'[\w]+\.[\w\.\$\-]+', Name.Builtin),

            # Keywords
            (r'\b(affine_map|affine_set|dense|opaque|sparse)\b', Keyword.Reserved),
            (r'\b(true|false|unit)\b', Keyword.Constant),

            # Affine operators
            (r'\b(floordiv|ceildiv|mod|symbol)\b', Operator.Word),

            # Numbers
            (r'0x[0-9a-fA-F]+', Number.Hex),
            (r'[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?', Number.Float),
            (r'[0-9]+', Number.Integer),

            # Strings
            (r'"', String.Double, 'string'),

            # Operators and punctuation
            (r'[+\-*/]', Operator),
            (r'->', Punctuation),
            (r'[()[\]<>,{}=:]', Punctuation),

            # Whitespace
            (r'\s+', Text.Whitespace),
        ],
        'string': [
            (r'\\[nt"]', String.Escape),
            (r'[^"\\]+', String.Double),
            (r'"', String.Double, '#pop'),
        ],
    }
```

### Pattern 2: Lexer Registration with Pygments

**What:** Register the custom lexer so `get_lexer_by_name('mlir')` works seamlessly.

**When to use:** During module initialization or via entry points.

**Example:**
```python
# Option A: Manual registration in highlighter
from pygments.lexers import LEXERS
from codepicture.highlight.mlir_lexer import MlirLexer

def register_custom_lexers():
    """Register custom lexers with Pygments."""
    LEXERS['MlirLexer'] = (
        'codepicture.highlight.mlir_lexer',  # Module path
        'MLIR',                               # Name
        ('mlir',),                            # Aliases
        ('*.mlir',),                          # Filenames
        ('text/x-mlir',),                     # Mimetypes
    )

# Option B: Entry point in pyproject.toml
# [project.entry-points."pygments.lexers"]
# mlir = "codepicture.highlight.mlir_lexer:MlirLexer"
```

### Pattern 3: Scope-to-Token Mapping (for Sublime syntax approach)

**What:** Map Sublime Text scope names to Pygments token types.

**When to use:** Only if implementing a full sublime-syntax parser.

**Example:**
```python
# Sublime scope -> Pygments token mapping
SCOPE_TO_TOKEN = {
    # Comments
    'comment': Comment,
    'comment.line': Comment.Single,
    'comment.block': Comment.Multiline,

    # Strings
    'string': String,
    'string.quoted.double': String.Double,
    'constant.character.escape': String.Escape,

    # Constants
    'constant.numeric': Number,
    'constant.language': Keyword.Constant,

    # Keywords
    'keyword': Keyword,
    'keyword.control': Keyword.Reserved,
    'keyword.other': Keyword,

    # Entities
    'entity.name.function': Name.Function,
    'entity.name.type': Name.Class,

    # Variables
    'variable': Name.Variable,
    'variable.other': Name.Variable,
    'variable.other.enummember': Name.Constant,

    # Punctuation
    'punctuation': Punctuation,
}

def scope_to_token(scope: str) -> TokenType:
    """Convert Sublime scope to Pygments token with inheritance."""
    # Try exact match first
    if scope in SCOPE_TO_TOKEN:
        return SCOPE_TO_TOKEN[scope]

    # Walk up scope hierarchy (e.g., comment.line.mlir -> comment.line -> comment)
    parts = scope.split('.')
    while parts:
        parts.pop()
        parent = '.'.join(parts)
        if parent in SCOPE_TO_TOKEN:
            return SCOPE_TO_TOKEN[parent]

    # Fallback
    return Text
```

### Anti-Patterns to Avoid

- **Building a full sublime-syntax parser for one language:** Massive complexity for marginal benefit. The RegexLexer approach handles MLIR well.
- **Depending on pysyntect:** Unmaintained since 2021, no Python 3.11+ support, would require building from source with uncertain success.
- **Copying regex patterns verbatim from Sublime syntax:** Oniguruma regex features (lookahead, etc.) may not work with Python `re`. Translate patterns carefully.
- **Global lexer registration at import time:** Use lazy registration or entry points to avoid import-time side effects.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MLIR base lexer | Start from scratch | LLVM's mlir_lexer.py | Already handles core syntax, 37 lines |
| Sublime syntax parser | Custom parser | onigurumacffi + pyyaml | Regex engine compatibility is critical |
| Token type mapping | Hardcoded dict | Pygments `string_to_tokentype()` | Handles "Keyword" -> Token.Keyword |
| Language detection | Custom extension check | Pygments `get_lexer_for_filename()` + registration | Works after lexer is registered |

**Key insight:** The LLVM MLIR lexer demonstrates that a simple RegexLexer covers 80% of use cases. Invest in enhancing that rather than building complex parsing infrastructure.

## Common Pitfalls

### Pitfall 1: Oniguruma vs Python Regex Incompatibility
**What goes wrong:** Sublime syntax uses Oniguruma regex, Python `re` module doesn't support all features
**Why it happens:** Oniguruma has features like `\K` (keep), advanced lookahead, possessive quantifiers
**How to avoid:** Either use `onigurumacffi` for full compatibility, or translate patterns to Python `re` syntax
**Warning signs:** Regex compilation errors, patterns that match differently than expected

### Pitfall 2: Missing Lexer Registration
**What goes wrong:** `get_lexer_by_name('mlir')` raises `ClassNotFound`
**Why it happens:** Custom lexer not registered with Pygments' internal mapping
**How to avoid:** Call registration function before any lexer lookups, or use entry points
**Warning signs:** Works in tests but not in installed package

### Pitfall 3: YAML Parsing Edge Cases
**What goes wrong:** `yaml.load()` fails on sublime-syntax files
**Why it happens:** Sublime syntax files may use unquoted scalars that confuse some YAML parsers
**How to avoid:** Use `ruamel.yaml` if `pyyaml` fails, or pre-process problematic files
**Warning signs:** Parser errors on `|` (literal blocks) or unquoted colons

### Pitfall 4: Token Type Fallback Chain
**What goes wrong:** Unknown constructs render with wrong or no color
**Why it happens:** Scope doesn't match any mapping, falls through to default
**How to avoid:** Define `Text` as ultimate fallback, test with diverse MLIR samples
**Warning signs:** Parts of MLIR code appearing in default text color

### Pitfall 5: State Machine Complexity
**What goes wrong:** Nested regions/attributes don't highlight correctly
**Why it happens:** Sublime syntax uses context stack (push/pop), RegexLexer uses simpler states
**How to avoid:** For RegexLexer, use multi-state approach similar to string handling
**Warning signs:** Highlighting breaks inside `{ }` blocks or `< >` type parameters

## Code Examples

Verified patterns from official sources:

### LLVM Official MLIR Lexer (Reference)
```python
# Source: https://github.com/llvm/llvm-project/pull/120942
# File: mlir/utils/pygments/mlir_lexer.py
from pygments.lexer import RegexLexer
from pygments.token import *

class MlirLexer(RegexLexer):
    name = 'MLIR'
    aliases = ['mlir']
    filenames = ['*.mlir']

    tokens = {
        'root': [
            (r'%[a-zA-Z0-9_]+', Name.Variable),
            (r'@[a-zA-Z_][a-zA-Z0-9_]+', Name.Function),
            (r'\^[a-zA-Z0-9_]+', Name.Label),
            (r'#[a-zA-Z0-9_]+', Name.Constant),
            (r'![a-zA-Z0-9_]+', Keyword.Type),
            # ... additional patterns
            (r'//.*\n', Comment.Single),
        ]
    }
```

### Registering Lexer via Entry Point
```toml
# pyproject.toml
[project.entry-points."pygments.lexers"]
mlir = "codepicture.highlight.mlir_lexer:MlirLexer"
```

### Language Alias Registration
```python
# language_aliases.py - extend existing
EXTRA_ALIASES: dict[str, str] = {
    "yml": "yaml",
    # MLIR is registered directly via lexer, but add alias if needed
}
```

### Integration with Existing Highlighter
```python
# pygments_highlighter.py - no changes needed if lexer properly registered
# get_lexer_by_name('mlir') will find MlirLexer automatically
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pysyntect for Sublime syntax | Custom RegexLexer | 2024+ | pysyntect unmaintained, avoid |
| TextMate grammar (.tmLanguage) | Sublime syntax (.sublime-syntax) | Sublime Text 3 (2016) | Sublime syntax is YAML, easier to parse |
| Manual lexer per language | Entry point registration | Pygments 2.x | Entry points are cleaner than manual LEXERS dict |

**Deprecated/outdated:**
- pysyntect: Last release May 2021, no Python 3.11+ wheels
- TextMate grammar bundles: Sublime syntax is the modern format

## Open Questions

Things that couldn't be fully resolved:

1. **Dialect-Specific Patterns**
   - What we know: MLIR has dialects (arith, scf, linalg) with different operation names
   - What's unclear: Should we add patterns for common dialects or keep it generic?
   - Recommendation: Keep generic (any `dialect.operation`), dialects share syntax structure

2. **Entry Point vs Manual Registration**
   - What we know: Entry points are cleaner but require package install
   - What's unclear: Does `pip install -e .` activate entry points for dev testing?
   - Recommendation: Use entry points for production, add fallback manual registration for dev

3. **Sublime Syntax File Bundling**
   - What we know: CONTEXT.md says copy from `~/.config/silicon/MLIR.sublime-syntax`
   - What's unclear: Should we include it even if using RegexLexer approach?
   - Recommendation: Include for reference and potential future use, but RegexLexer is primary

## Sources

### Primary (HIGH confidence)
- [Pygments Lexer Development](https://pygments.org/docs/lexerdevelopment/) - Custom lexer API
- [LLVM MLIR Pygments Lexer PR #120942](https://github.com/llvm/llvm-project/pull/120942) - Official MLIR lexer
- [Sublime Text Syntax Definitions](http://www.sublimetext.com/docs/syntax.html) - Sublime syntax format spec
- [Sublime Text Scope Naming](https://www.sublimetext.com/docs/scope_naming.html) - Scope conventions
- [Pygments Token Types](https://pygments.org/docs/tokens/) - Token hierarchy

### Secondary (MEDIUM confidence)
- [onigurumacffi on PyPI](https://pypi.org/project/onigurumacffi/) - Python Oniguruma bindings (v1.4.1, Jan 2025)
- [syntect on GitHub](https://github.com/trishume/syntect) - Rust Sublime syntax parser (for algorithm reference)

### Tertiary (LOW confidence)
- [pysyntect on PyPI](https://pypi.org/project/pysyntect/) - Python syntect bindings (unmaintained since 2021)
- MLIR.sublime-syntax at `~/.config/silicon/` - User's local syntax file (not version controlled)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Pygments is already in use, pattern is proven
- Architecture: HIGH - LLVM lexer provides verified reference implementation
- Pitfalls: MEDIUM - Based on analysis, real-world edge cases may emerge

**Research date:** 2026-01-29
**Valid until:** 2026-02-28 (Pygments is stable, MLIR syntax unlikely to change significantly)
