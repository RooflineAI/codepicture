# codepicture

## What This Is

A Python CLI tool that transforms code snippets into polished, presentation-ready images. Takes a source file, applies syntax highlighting with 55+ themes (including Catppuccin), adds macOS window chrome and drop shadows, and outputs PNG (2x HiDPI), SVG, or PDF. Includes a custom MLIR lexer for first-class MLIR syntax highlighting.

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
- ✓ Line numbers in gutter — v1.0

### Active

- [ ] Fix rendering hang on test.mlir (and any other files that fail)
- [ ] Run codepicture against real-world source files and fix rendering issues
- [ ] Build visual regression test suite for core languages (Python, Rust, C++, JS, MLIR)
- [ ] Profile and optimize rendering performance

### Out of Scope

- Line highlighting — deferred to v2
- Gradient backgrounds — deferred to v2
- Clipboard input/output — nice-to-have for later
- Font ligatures — deferred to v2
- GUI or web UI — v1 is CLI-only, web UI is future consideration
- Windows support — macOS and Linux only for now
- Real-time preview — batch processing only
- Animations / GIFs — static images only, different tool category
- Cloud accounts / web service — CLI-first, no infrastructure complexity

## Current Milestone: v1.1 Reliability & Testing

**Goal:** Harden codepicture for real-world usage — fix rendering bugs, build visual regression tests, and optimize performance.

**Target work:**
- Investigate and fix rendering hang on `test.mlir` (could be lexer backtracking, rendering pipeline bug, or shadow blur issue)
- Run against diverse real source files across core languages and fix issues
- Build automated visual regression test suite with reference images
- Profile rendering pipeline and address bottlenecks

**Known issue:** `test.mlir` causes codepicture to hang indefinitely. User will provide additional MLIR examples for testing.

## Context

Shipped v1.0 MVP with 6,050 lines of Python (3,214 source + 2,836 test).
Tech stack: Python 3.13+, Cairo/Pango, Pygments, Typer, Pydantic.
260 tests passing with 80%+ coverage and GitHub Actions CI.

This is a Python rewrite inspired by Silicon (Rust). Python chosen because performance isn't critical, better ecosystem for SVG manipulation, and easier open source contribution.

User works with MLIR, which requires custom lexer support — this is a core use case, shipped with custom Pygments RegexLexer.

Intended trajectory: personal use → startup internal tool → open source.

## Constraints

- **Stack**: Python 3.13+, Cairo/Pango, Pygments, Typer, Pydantic
- **Platform**: Must work on macOS and Linux
- **Config**: TOML format at ~/.config/codepicture/config.toml

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python over Rust | Performance not critical, better SVG ecosystem | ✓ Good — 6K LOC in 3 days |
| Cairo/Pango for rendering | Mature, handles fonts well, supports PNG/SVG/PDF | ✓ Good — PNG/SVG/PDF all working |
| Pygments for highlighting | Standard Python choice, extensive language support, custom lexers | ✓ Good — 55+ themes, custom MLIR lexer |
| Typer for CLI | Modern, type-hint based, good DX | ✓ Good — clean CLI with flag overrides |
| Pydantic for config | Validation at load time, clear error messages | ✓ Good — catches config errors early |
| Protocol-based architecture | Enables future backends (Skia, browser) and testability | ✓ Good — clean component boundaries |
| Cairo text API over Pango | macOS library linking issues with PyGObject | ⚠️ Revisit — works for monospace, may need Pango for ligatures |
| RegexLexer for MLIR | 80% coverage with 20% effort vs Sublime syntax parser | ✓ Good — covers common MLIR constructs |
| Fixed shadow style (on/off) | Reduces config complexity, macOS-standard look | ✓ Good — clean visual result |

---
*Last updated: 2026-01-30 after v1.1 milestone started*
