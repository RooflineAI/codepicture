# Phase 2: Syntax Highlighting - Context

**Gathered:** 2026-01-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Transform raw code into structured token streams with theme-mapped colors. This phase covers Pygments tokenization, theme loading and application, and language detection. Rendering and layout are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Theme System
- Custom themes via TOML files supported (not just built-in)
- Ship all 4 Catppuccin flavors (Mocha, Macchiato, Frappé, Latte) plus Dracula, Monokai, One Dark
- Default theme: catppuccin-mocha (when no config)
- Theme files can live in `~/.config/codepicture/themes/` OR inline in config.toml
- Theme inheritance supported: `extends = "catppuccin-mocha"` then override specific tokens
- Invalid/missing theme: error and exit (no silent fallback)
- `--list-themes` flag to show available themes (no preview command)
- No light/dark metadata in theme files — just colors

### Token Mapping
- Coarse granularity: Pygments standard ~15 categories (Keyword, String, Comment, etc.)
- Token type inheritance: String.Escape falls back to String, then Text
- No per-token background colors — only global background
- Visible whitespace option: `·` for spaces, `→` for tabs
- No special styling for line continuation characters
- Escape sequences same color as containing string
- Syntax error tokens: red/error color (make errors obvious)

### Language Handling
- `--language` flag wins over file extension
- Common aliases supported: js→javascript, py→python, etc.
- Unknown `--language` value: error and exit with list of available languages

### Output Format
- Include source positions: each token knows its line:column
- Include language metadata in output
- Preserve trailing whitespace exactly as in source
- Partial highlighting failure: all or nothing (fail completely)
- No caching — re-highlight for each render

### Testing
- Unit tests only (no snapshot tests)
- Sample code fixtures in `tests/fixtures/` for various languages (Python, JS, Rust, etc.)

### Claude's Discretion
- Bold/italic support for token styles
- Output structure (list of styled spans vs token objects)
- Line structure (line-based vs flat stream)
- Empty line representation
- Language fallback when can't detect and not specified
- Theme testing approach (validation vs output comparison)
- Edge case test coverage

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-syntax-highlighting*
*Context gathered: 2026-01-28*
