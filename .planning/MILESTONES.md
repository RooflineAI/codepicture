# Project Milestones: codepicture

## v1.0 MVP (Shipped: 2026-01-30)

**Delivered:** Complete CLI tool that transforms code snippets into polished, presentation-ready PNG, SVG, or PDF images with syntax highlighting, macOS window chrome, themes, and custom MLIR lexer support.

**Phases completed:** 1-6 including 1.1 (21 plans total)

**Key accomplishments:**

- Foundation layer with protocol-based architecture, Pydantic config validation, and error hierarchy
- Syntax highlighting engine with Pygments, 55+ themes (including Catppuccin), and auto-detect language
- Layout engine with Cairo text measurement, bundled JetBrains Mono, and HiDPI canvas calculations
- Multi-format rendering (PNG 2x, SVG, PDF) with macOS window chrome and drop shadows
- CLI tool (`codepicture`) with Typer, TOML config, stdin support, and flag overrides
- Custom MLIR lexer as Pygments RegexLexer with dialect support and 100% test coverage

**Stats:**

- 59 files created
- 6,050 lines of Python (3,214 source + 2,836 test)
- 7 phases, 21 plans
- 3 days from start to ship (2026-01-28 to 2026-01-30)

**Git range:** `feat(01-01)` -> `feat(06-02)`

**What's next:** TBD — run `/gsd:new-milestone` to plan next version

---
