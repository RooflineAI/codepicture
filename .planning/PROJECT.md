# codepicture

## What This Is

A Python CLI tool that transforms code snippets into polished, presentation-ready images. Takes a source file, applies syntax highlighting with 55+ themes (including Catppuccin), adds macOS window chrome and drop shadows, and outputs PNG (2x HiDPI), SVG, or PDF. Supports line highlighting with named styles (add/remove/focus), theme-aware colors, gutter indicators, and focus mode dimming. Includes a custom MLIR lexer for first-class MLIR syntax highlighting, timeout protection, and visual regression testing.

## Core Value

One command turns code into a slide-ready image: `codepicture snippet.py -o slide.png`

## Requirements

### Validated

- ✓ CLI accepts source file path and outputs image — v1.0
- ✓ PNG output format — v1.0
- ✓ SVG output format — v1.0
- ✓ PDF output format — v1.0
- ✓ Syntax highlighting via Pygments — v1.0
- ✓ Custom lexer support (MLIR via Pygments RegexLexer) — v1.0
- ✓ Catppuccin theme support — v1.0
- ✓ Built-in Pygments themes (Dracula, Monokai, One Dark, etc.) — v1.0
- ✓ macOS-style window controls (traffic light buttons) — v1.0
- ✓ Drop shadow effect (on/off toggle) — v1.0
- ✓ TOML config file support (~/.config/codepicture/config.toml) — v1.0
- ✓ Configurable font family and size — v1.0
- ✓ Configurable padding — v1.0
- ✓ Configurable corner radius — v1.0
- ✓ Configurable background color — v1.0
- ✓ Auto-detect language from file extension — v1.0
- ✓ Explicit language override via CLI flag — v1.0
- ✓ Line numbers in gutter — v1.0
- ✓ Configurable line height — v1.0
- ✓ Tab-to-space normalization — v1.0
- ✓ CLI flags override config file settings — v1.0
- ✓ MLIR rendering without hang (font caching + lexer fix) — v1.1
- ✓ Application-level rendering timeout guard (--timeout flag) — v1.1
- ✓ Clean error messages for all failure modes (no tracebacks) — v1.1
- ✓ Visual regression test suite (5 languages x 3 formats) — v1.1
- ✓ Performance benchmarks (per-stage + end-to-end with CI) — v1.1
- ✓ Highlight specific lines with colored backgrounds via --highlight flag — v2.0
- ✓ Line number ranges (e.g., 3,7-12) with comma-separated syntax — v2.0
- ✓ Named highlight styles: highlight (yellow), add (green), remove (red), focus (blue) — v2.0
- ✓ Focus mode: unfocused lines dimmed at 35% opacity — v2.0
- ✓ Gutter indicators: + for add, - for remove, colored bar for focus/highlight — v2.0
- ✓ Theme-aware highlight colors: luminance-based palette selection across 55+ themes — v2.0
- ✓ Per-style TOML color overrides with 3-tier precedence chain — v2.0
- ✓ Highlight works across all output formats (PNG, SVG, PDF) — v2.0
- ✓ README documents all highlight CLI flags, TOML config, and includes visual examples — v2.0

### Active

(No active milestone — planning next)

### Out of Scope

- Gradient backgrounds — deferred to future
- Clipboard input/output — nice-to-have for later
- Font ligatures — deferred to future
- GUI or web UI — CLI-only, web UI is future consideration
- Windows support — macOS and Linux only for now
- Real-time preview — batch processing only
- Animations / GIFs — static images only, different tool category
- Cloud accounts / web service — CLI-first, no infrastructure complexity
- Inline source annotations (`// [highlight]`) — deferred to v2.1+
- Word-level highlighting — separate milestone
- Diff-based automatic highlighting — separate milestone

## Context

Shipped v2.0 with 10,489 lines of Python (4,284 source + 6,205 test).
Tech stack: Python 3.13+, Cairo/Pango, Pygments, Typer, Pydantic.
572 tests passing with visual regression, parametric theme contrast tests, benchmarks, and GitHub Actions CI.

This is a Python rewrite inspired by Silicon (Rust). Python chosen because performance isn't critical, better ecosystem for SVG manipulation, and easier open source contribution.

User works with MLIR, which requires custom lexer support — this is a core use case, shipped with custom Pygments RegexLexer. MLIR rendering hang fixed in v1.1 (186x speedup).

Intended trajectory: personal use → startup internal tool → open source.

## Constraints

- **Stack**: Python 3.13+, Cairo/Pango, Pygments, Typer, Pydantic
- **Platform**: Must work on macOS and Linux
- **Config**: TOML format at ~/.config/codepicture/config.toml

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python over Rust | Performance not critical, better SVG ecosystem | ✓ Good — 10K LOC across 3 milestones |
| Cairo/Pango for rendering | Mature, handles fonts well, supports PNG/SVG/PDF | ✓ Good — PNG/SVG/PDF all working |
| Pygments for highlighting | Standard Python choice, extensive language support, custom lexers | ✓ Good — 55+ themes, custom MLIR lexer |
| Typer for CLI | Modern, type-hint based, good DX | ✓ Good — clean CLI with flag overrides |
| Pydantic for config | Validation at load time, clear error messages | ✓ Good — catches config errors early, legacy migration via model_validator |
| Protocol-based architecture | Enables future backends (Skia, browser) and testability | ✓ Good — clean component boundaries |
| Cairo text API over Pango | macOS library linking issues with PyGObject | ⚠️ Revisit — works for monospace, may need Pango for ligatures |
| RegexLexer for MLIR | 80% coverage with 20% effort vs Sublime syntax parser | ✓ Good — covers common MLIR constructs, 0 Error tokens |
| Fixed shadow style (on/off) | Reduces config complexity, macOS-standard look | ✓ Good — clean visual result |
| lru_cache for font resolution | Eliminates repeated system font enumeration per token | ✓ Good — 186x speedup on MLIR files |
| Instance-level font caching in CairoCanvas | Avoids redundant Cairo select_font_face/set_font_size calls | ✓ Good — measurable render speedup |
| ThreadPoolExecutor for timeout | Works with Cairo C extensions, unlike signal-based timeout | ✓ Good — clean timeout handling |
| pixelmatch for visual regression | Python-native, configurable threshold, composite diff output | ✓ Good — 58+ baselines, no false positives |
| Separate CI benchmark workflow | Non-blocking, informational only, doesn't slow PR merges | ✓ Good — weekly + manual triggers |
| Atomic file writes | Prevents partial output on timeout/failure | ✓ Good — no corrupted files |
| Luminance-based theme detection | BT.709 luminance formula to classify light/dark themes | ✓ Good — clean split across 55+ themes, no edge cases |
| 3-tier color precedence | TOML per-style > theme-derived > hardcoded defaults | ✓ Good — predictable, user overrides always win |
| --highlight replaces --highlight-lines | Phase 13 unified flag with style syntax | ✓ Good — cleaner CLI surface, backward compat via Pydantic migration |
| Auto-generated doc images | docs/generate-examples.sh uses codepicture itself | ✓ Good — images stay in sync with code |

---
*Last updated: 2026-04-10 after v2.0 milestone (line highlighting, named styles, theme integration, documentation)*
