# Phase 8: MLIR Hang Fix - Research

**Researched:** 2026-01-30
**Domain:** Performance diagnosis — rendering pipeline hang on MLIR files
**Confidence:** HIGH

## Summary

The hang when rendering `test.mlir` is **not** in the MLIR lexer. The root cause is in the rendering pipeline: `resolve_font_family()` in `src/codepicture/fonts/__init__.py` calls `manimpango.list_fonts()` on every invocation, and `list_fonts()` takes ~130ms per call. Since `draw_text()` in `CairoCanvas` calls `resolve_font_family()` once per token, and `test.mlir` produces 303 tokens, the render stage takes ~39 seconds.

A secondary contributing factor is the MLIR lexer's lack of a catch-all identifier rule. 120 of the 303 tokens are single-character `Error` tokens produced when Pygments falls back to character-by-character emission for unmatched bare words (`attributes`, `private`, `links`, `to`, `ins`, etc.). This inflates the token count by roughly 100 tokens compared to what proper identifier matching would produce.

**There is no catastrophic regex backtracking.** All MLIR lexer patterns were tested against pathological inputs (1000+ character strings) with zero slowdowns.

**Primary recommendation:** Cache the result of `resolve_font_family()` (a simple module-level dict or `functools.lru_cache`), and add a catch-all identifier rule to the MLIR lexer to reduce error tokens.

## Root Cause Analysis

### Finding 1: `manimpango.list_fonts()` is the bottleneck (HIGH confidence)

**Evidence (direct measurement):**
- Single call: 0.14s
- 303 calls (one per token): 39.3s
- Called from `resolve_font_family()` which is called from `CairoCanvas.draw_text()` for every token

**Call chain:**
```
Renderer.render()
  → for each token: canvas.draw_text()
    → resolve_font_family()
      → manimpango.list_fonts()  ← 0.13s per call
```

**Additional overhead:** `CairoCanvas.measure_text()` also calls `resolve_font_family()`, used during line number rendering and layout. Layout only calls it twice (negligible), but line number rendering calls it once per line (15 calls = ~2s).

**Total overhead per render:** ~(tokens + lines) * 0.13s = ~41s for test.mlir

### Finding 2: MLIR lexer produces excessive Error tokens (HIGH confidence)

**Evidence (direct measurement):**
- 303 total tokens from test.mlir
- 120 are Error tokens (single characters)
- Unmatched words: `attributes`, `links`, `unified_memory`, `transparent_access`, `private`, `on`, `ins`, `to`
- These are bare identifiers with no matching lexer rule

**Impact:** Each single-character error token becomes a separate `draw_text()` call. Proper identifier matching would collapse these ~120 tokens into ~18 tokens (the actual words), reducing total tokens from 303 to ~200.

### Finding 3: No regex backtracking issues (HIGH confidence)

**Evidence:** All regex patterns tested against pathological inputs (1000+ char strings). No pattern exceeded 0.01s. The patterns use non-overlapping character classes and don't have nested quantifiers.

## Pipeline Stage Timing

Measured with `test.mlir` (15 lines, 303 tokens):

| Stage | Time | Status |
|-------|------|--------|
| Font registration | 0.009s | OK |
| Language detection | 0.012s | OK |
| Tokenization (lexer) | 0.001s | OK |
| Theme loading | 0.004s | OK |
| Layout calculation | 0.286s | OK (2 list_fonts calls) |
| **Render: line numbers** | **3.87s** | **SLOW** (15 list_fonts calls) |
| **Render: code tokens** | **>25s** | **HANG** (303 list_fonts calls) |
| Shadow application | not reached | blocked by render |

## Standard Stack

### Core (already in use)

| Library | Purpose | Relevant to Fix |
|---------|---------|-----------------|
| Pygments | Lexer framework | MLIR lexer lives here |
| ManimPango | Font management | `list_fonts()` is the bottleneck |
| Cairo (pycairo) | Canvas rendering | `draw_text()` calls resolve per token |

### Supporting (no new dependencies needed)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `functools.lru_cache` | Cache resolve_font_family result | Primary fix |
| `re` module | Regex validation | Testing lexer patterns |
| `pytest.mark.timeout` | Regression test | Ensure renders complete in time |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `lru_cache` | Module-level dict | Equivalent; lru_cache is cleaner |
| Per-call caching | Pre-resolve once in Renderer | Requires API change; caching is simpler and catches all callers |

## Architecture Patterns

### Fix 1: Cache `resolve_font_family()` result

**File:** `src/codepicture/fonts/__init__.py`

The function's result depends only on `(requested, default)` and the set of available fonts. Since fonts don't change during a process lifetime, caching is safe.

**Pattern:**
```python
# Option A: functools.lru_cache (simplest)
@functools.lru_cache(maxsize=16)
def resolve_font_family(requested: str, default: str = "JetBrains Mono") -> str:
    register_bundled_fonts()
    available_fonts = manimpango.list_fonts()
    if requested in available_fonts:
        return requested
    _logger.warning("Font '%s' not found, falling back to '%s'", requested, default)
    return default
```

```python
# Option B: Module-level cache dict (more explicit)
_font_cache: dict[tuple[str, str], str] = {}

def resolve_font_family(requested: str, default: str = "JetBrains Mono") -> str:
    key = (requested, default)
    if key in _font_cache:
        return _font_cache[key]
    register_bundled_fonts()
    available_fonts = manimpango.list_fonts()
    result = requested if requested in available_fonts else default
    _font_cache[key] = result
    return result
```

**Recommendation:** Use `functools.lru_cache`. It is the standard Python pattern, handles thread-safety for free, and requires minimal code change.

### Fix 2: Add catch-all identifier rule to MLIR lexer

**File:** `src/codepicture/highlight/mlir_lexer.py`

Add a general identifier rule at the end of the `root` state (before whitespace), so bare words like `attributes`, `private`, `to` get a single token instead of N error tokens.

**Pattern:**
```python
# Add before whitespace rule, after all specific rules:
(r"[a-zA-Z_][\w]*", Name),  # General identifiers (catch-all)
```

**Why this position:** Pygments tries rules in order. All specific keyword/type/operator rules come first. This catch-all only triggers for identifiers that don't match any specific rule.

### Fix 3 (optional): Cache font setup in CairoCanvas.draw_text()

**File:** `src/codepicture/render/canvas.py`

Even after caching `resolve_font_family`, `draw_text()` calls `select_font_face()` and `set_font_size()` on every call. These are cheap Cairo operations, but caching the font key (like `PangoTextMeasurer` already does) avoids redundant calls.

```python
# In draw_text, cache font setup like PangoTextMeasurer does:
font_key = (font_name, font_size)
if self._current_font != font_key:
    self._ctx.select_font_face(font_name, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    self._ctx.set_font_size(font_size)
    self._current_font = font_key
```

Note: `PangoTextMeasurer` already implements this pattern (line 59 of `measurer.py`). `CairoCanvas.draw_text()` does not.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Font resolution caching | Custom invalidation logic | `functools.lru_cache` | Standard, thread-safe, zero-maintenance |
| Regex backtracking detection | Manual pattern analysis | `re` module with timeout test | Automated, repeatable |
| Timeout-based regression tests | Custom timing code | `@pytest.mark.timeout(N)` | Already in project, consistent |

**Key insight:** The fix is a one-line cache decorator + one-line lexer rule, not a rewrite. The architecture is sound; the hot path just needs memoization.

## Common Pitfalls

### Pitfall 1: Fixing the wrong stage
**What goes wrong:** Assuming the hang is in the lexer because the context says "regex backtracking" and the file is MLIR.
**Why it happens:** The issue was reported as a lexer problem, but systematic measurement shows the lexer takes 0.5ms. The render stage is the actual bottleneck.
**How to avoid:** Always bisect the pipeline before fixing. The orchestrator already has clear stages.
**Warning signs:** Lexer-only tests pass instantly; full render hangs.

### Pitfall 2: Incomplete caching in resolve_font_family
**What goes wrong:** Caching the result but not the `list_fonts()` call inside.
**Why it happens:** `lru_cache` on the function caches the entire function body, including the `list_fonts()` call. A manual cache that only caches the final string but still calls `list_fonts()` would still be slow.
**How to avoid:** Use `lru_cache` on the whole function, or ensure the manual cache short-circuits before `list_fonts()`.

### Pitfall 3: Catch-all identifier rule matching too eagerly
**What goes wrong:** The catch-all `[a-zA-Z_][\w]*` rule matches words that should be keywords, types, or builtins.
**Why it happens:** Pygments rules are tried in order, and `\b` word boundaries interact with token boundaries.
**How to avoid:** Place the catch-all rule AFTER all keyword/type/builtin rules. The `\b` word boundary in keyword rules ensures they match first. Verify existing tests still pass.

### Pitfall 4: Not testing the Error token reduction
**What goes wrong:** Adding the catch-all rule but not verifying it actually reduces Error tokens.
**Why it happens:** The rule might not match all unrecognized words if it conflicts with other patterns.
**How to avoid:** Add a test that tokenizes `test.mlir` and asserts zero (or near-zero) Error tokens.

### Pitfall 5: Partial output file on failure
**What goes wrong:** If a render fails mid-way, a partial PNG might exist on disk.
**Why it happens:** The orchestrator writes output at the end (`output_path.write_bytes(result.data)`), but if the write is interrupted or a previous run left a file, stale output remains.
**How to avoid:** The CONTEXT.md requires cleanup of partial output on failure. The current orchestrator writes atomically (write_bytes), so partial writes are unlikely, but a previous successful run's output file should be cleaned up on error.

## Code Examples

### Regression test for MLIR render timeout
```python
@pytest.mark.slow
@pytest.mark.timeout(10)
def test_mlir_render_completes(tmp_path):
    """Render test.mlir must complete within timeout — regression for hang fix."""
    from codepicture.cli.orchestrator import generate_image
    from codepicture import RenderConfig
    from pathlib import Path

    code = Path("test.mlir").read_text()
    output = tmp_path / "mlir_output.png"
    config = RenderConfig()
    generate_image(code=code, output_path=output, config=config,
                   language=None, filename="test.mlir")
    assert output.exists()
    assert output.stat().st_size > 0
```

### Test for Error token reduction
```python
def test_mlir_lexer_minimal_error_tokens():
    """MLIR lexer should not produce excessive Error tokens on valid MLIR."""
    from codepicture.highlight.mlir_lexer import MlirLexer
    from pygments.token import Error
    from pathlib import Path

    code = Path("test.mlir").read_text()
    lexer = MlirLexer()
    tokens = list(lexer.get_tokens(code))
    error_tokens = [t for t, v in tokens if t == Error]
    # After fix: should be very few or zero Error tokens
    assert len(error_tokens) < 10, f"Too many Error tokens: {len(error_tokens)}"
```

### MLIR test corpus structure
```
tests/fixtures/mlir/
├── basic_module.mlir        # Simple module with func, return
├── complex_attributes.mlir  # test.mlir content (real-world with attributes, device affinity)
├── deep_nesting.mlir        # Deeply nested affine loops (stress test)
├── long_lines.mlir          # Lines with many tokens (stress test)
└── edge_cases.mlir          # Unusual tokens: quoted refs, hex numbers, escapes
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Call list_fonts() per token | Cache with lru_cache | This fix | 300x speedup for test.mlir |
| No catch-all identifier rule | Add `[a-zA-Z_][\w]*` catch-all | This fix | ~35% fewer tokens, better highlighting |

## Open Questions

1. **Does `manimpango.list_fonts()` performance vary by OS/font count?**
   - What we know: On this macOS system with 331 fonts, each call takes ~130ms
   - What's unclear: Whether Linux CI with fewer fonts would also hang (likely slower, just not as bad)
   - Recommendation: Cache regardless — it's the right fix for all platforms

2. **Should `CairoCanvas.draw_text()` also cache font setup?**
   - What we know: `select_font_face()` and `set_font_size()` are called per-token. These are cheap Cairo ops (~microseconds), but the pattern already exists in `PangoTextMeasurer`.
   - What's unclear: Whether this provides measurable speedup after the primary fix
   - Recommendation: Apply the same caching pattern for consistency. Low effort, zero risk.

3. **Are there other MLIR constructs that the lexer should handle?**
   - What we know: The `...` ellipsis syntax in test.mlir produces Error tokens. MLIR uses `...` as a variadic argument marker.
   - What's unclear: Whether all MLIR syntax is covered
   - Recommendation: Add `...` to the lexer. Beyond that, the catch-all identifier rule handles unknown words gracefully.

## Sources

### Primary (HIGH confidence)
- Direct measurement of `manimpango.list_fonts()`: 0.13s/call, 39s for 303 calls
- Direct measurement of pipeline stages: lexer 0.001s, render >30s
- Direct inspection of source code: `resolve_font_family()` calls `list_fonts()` unconditionally
- Direct token analysis: 120/303 tokens are single-char Error tokens

### Secondary (MEDIUM confidence)
- `functools.lru_cache` is standard Python stdlib — well-documented, thread-safe

### Tertiary (LOW confidence)
- None — all findings are based on direct code inspection and measurement

## Metadata

**Confidence breakdown:**
- Root cause identification: HIGH — directly measured, reproduced, isolated to specific function call
- Fix approach (caching): HIGH — standard Python pattern, zero-risk change
- Lexer improvement: HIGH — standard Pygments pattern, testable
- Test strategy: HIGH — existing patterns in codebase (pytest.mark.slow, timeout)

**Research date:** 2026-01-30
**Valid until:** Indefinite (findings are about this specific codebase's architecture, not external APIs)
