# codepicture

## What This Is

A Python CLI tool that transforms code snippets into beautiful, presentation-ready images. Takes a source file, applies syntax highlighting and visual styling (macOS window controls, shadows, themes), and outputs PNG, SVG, or PDF. Built for developers who want polished code visuals for slides without fussing with screenshot tools.

## Core Value

One command turns code into a slide-ready image: `codepicture snippet.py -o slide.png`

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] CLI accepts source file path and outputs image
- [ ] PNG output format
- [ ] SVG output format
- [ ] PDF output format
- [ ] Syntax highlighting via Pygments
- [ ] Custom lexer support (e.g., MLIR)
- [ ] Catppuccin theme support
- [ ] Built-in Pygments themes (Dracula, Monokai, One Dark, etc.)
- [ ] macOS-style window controls (traffic light buttons)
- [ ] Drop shadow effect
- [ ] TOML config file support (~/.config/codepicture/config.toml)
- [ ] Configurable font family and size
- [ ] Configurable padding
- [ ] Configurable corner radius
- [ ] Configurable shadow parameters
- [ ] Auto-detect language from file extension
- [ ] Explicit language override via CLI flag

### Out of Scope

- Line highlighting — deferred to v2
- Clipboard input/output — nice-to-have for later
- GUI or web UI — v1 is CLI-only, web UI is future consideration
- Windows support — macOS and Linux only for now
- Real-time preview — batch processing only

## Context

This is a Python rewrite inspired by Silicon (Rust). Python chosen because:
- Performance isn't critical for this use case
- Better Python ecosystem for SVG manipulation
- Easier contribution for open source

Architecture document exists at `PYTHON_REWRITE_ARCHITECTURE.md` with detailed component design:
- Application facade pattern (SiliconApp) for future GUI readiness
- Protocol-based abstractions (Canvas, Highlighter, Theme, TextMeasurer)
- Cairo/Pango for rendering, Pygments for highlighting
- Pydantic for config validation

User works with MLIR, which requires custom lexer support — this is a core use case.

Intended trajectory: personal use → startup internal tool → open source.

## Constraints

- **Stack**: Python 3.11+, Cairo/Pango, Pygments, Typer, Pydantic — per architecture doc
- **Platform**: Must work on macOS and Linux
- **Config**: TOML format at ~/.config/codepicture/config.toml

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python over Rust | Performance not critical, better SVG ecosystem | — Pending |
| Cairo/Pango for rendering | Mature, handles fonts well, supports PNG/SVG/PDF | — Pending |
| Pygments for highlighting | Standard Python choice, extensive language support, custom lexers | — Pending |
| Typer for CLI | Modern, type-hint based, good DX | — Pending |
| Pydantic for config | Validation at load time, clear error messages | — Pending |
| Protocol-based architecture | Enables future backends (Skia, browser) and testability | — Pending |

---
*Last updated: 2026-01-28 after initialization*
