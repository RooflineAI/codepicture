# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-28)

**Core value:** One command turns code into a slide-ready image
**Current focus:** Phase 6 - MLIR Lexer (complete)

## Current Position

Phase: 6 of 7 (MLIR Lexer)
Plan: 1 of 1 in current phase
Status: Phase complete
Last activity: 2026-01-30 - Completed 06-01-PLAN.md (MLIR Lexer)

Progress: [####################] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 20
- Average duration: 2.7 min
- Total execution time: 0.90 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 2/2 | 5 min | 2.5 min |
| 1.1 Testing Infrastructure | 2/2 | 5 min | 2.5 min |
| 2. Syntax Highlighting | 3/3 | 9 min | 3 min |
| 3. Layout Engine | 3/3 | 12 min | 4 min |
| 4. Rendering | 5/5 | 15 min | 3 min |
| 5. CLI & Orchestration | 4/4 | 9 min | 2.25 min |
| 6. MLIR Lexer | 1/1 | 1 min | 1 min |

**Recent Trend:**
- Last 5 plans: 05-01 (2 min), 05-02 (2 min), 05-03 (2 min), 05-04 (3 min), 06-01 (1 min)
- Trend: Stable at 1-3 min per plan

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: MLIR lexer uses Pygments RegexLexer with entry-point registration
- [06-01]: RegexLexer with ordered token patterns for MLIR syntax
- [06-01]: Entry point registration via pyproject.toml for Pygments discovery
- [01-01]: Color uses frozen dataclass with slots for immutability
- [01-01]: ConfigError includes optional field attribute
- [01-02]: TYPE_CHECKING guard for protocol type imports (avoids circular imports)
- [01-02]: No @runtime_checkable on protocols (performance per RESEARCH.md)
- [01.1-01]: pytest 9.x with verbose output and short tracebacks
- [01.1-01]: 80% coverage threshold with TYPE_CHECKING exclusion
- [01.1-01]: Fixtures use Catppuccin Blue as standard test color
- [01.1-02]: Protocol tests use mock implementations to verify structural subtyping
- [01.1-02]: Test classes organized by module/class (TestColor, TestRenderConfig, etc.)
- [01.1-02]: CI uploads coverage to Codecov but doesn't fail on upload errors
- [02-01]: TokenInfo uses frozen dataclass with slots for immutability
- [02-01]: Trailing empty lines from Pygments trimmed unless code ends with newline
- [02-01]: Language aliases resolved before Pygments lookup
- [02-02]: PygmentsTheme uses __slots__ for memory efficiency
- [02-02]: Line number colors derived from foreground/background (Pygments doesn't provide these)
- [02-02]: Token inheritance walks parent chain in theme before base theme
- [02-02]: Default theme is catppuccin-mocha per CONTEXT.md
- [02-03]: Integration tests verify highlighter -> theme.get_style() -> TextStyle chain
- [02-03]: Sample code fixtures in tests/fixtures/ for multi-language testing
- [03-01]: Use Cairo text API instead of PyGObject Pango (library linking issue on macOS)
- [03-01]: Bundle JetBrains Mono Regular only (Bold can be added later)
- [03-01]: Font registration uses ManimPango for cross-platform compatibility
- [03-01]: Text measurer uses font caching to avoid repeated font selection
- [03-02]: LINE_NUMBER_GAP constant (12px) for gutter spacing
- [03-02]: Baseline offset approximated at 0.8 * char_height
- [03-02]: Gutter width measured using actual digit characters for accuracy
- [03-03]: Empty string measurement returns (0, 0) per Cairo text_extents behavior
- [03-03]: Layout fixtures use lazy imports inside fixture functions
- [04-01]: PNG surfaces created at 2x scale with logical coordinate drawing
- [04-01]: SVG/PDF surfaces write to BytesIO for in-memory generation
- [04-01]: apply_shadow is no-op stub (Plan 04-03 implements real shadow)
- [04-02]: Title text color auto-detected from background brightness
- [04-03]: Cairo BGRA converted via Pillow RGBa mode to handle pre-multiplied alpha
- [04-03]: Shadow margin = blur*2 + max(offset) = 125px total expansion
- [04-04]: RenderResult dataclass holds output bytes plus format and dimensions
- [04-04]: Renderer accesses canvas._surface directly for shadow processing
- [04-04]: OutputFormat added to top-level package exports
- [04-05]: Separate render_tokens fixture uses real Pygments Token types
- [04-05]: Use autouse=True fixture for font registration in renderer tests
- [04-05]: New fixtures (render_tokens, render_metrics) for render testing
- [04-gap]: Removed shadow_blur/offset config fields (shadow is on/off only per CONTEXT.md)
- [05-01]: Config loader uses replace semantics (first-found config wins, no merge)
- [05-01]: Simplified load_config API with config_path parameter for explicit --config override
- [05-01]: DEFAULT_LOCAL_CONFIG_PATH is codepicture.toml (not .codepicture.toml)
- [05-02]: Orchestrator is pure function taking already-loaded config (CLI handles loading)
- [05-02]: CLI builds override dict from non-None flag values
- [05-02]: Stdin input requires --language flag (cannot auto-detect)
- [05-02]: Output format inferred from extension, overridable with -f/--format
- [05-03]: Entry point imports app from cli module and calls it
- [05-04]: Unit tests use CliRunner for fast, isolated testing
- [05-04]: Integration tests use subprocess for true end-to-end verification
- [05-04]: Exit code 0 or 2 accepted for no-args help (typer version variance)

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 001 | Flatten tests folder structure | 2026-01-28 | 83d866c | [001-flatten-tests-folder-structure](./quick/001-flatten-tests-folder-structure/) |

### Roadmap Evolution

- Phase 1.1 inserted after Phase 1: Testing Infrastructure (URGENT) - Set up pytest, fixtures, CI before continuing to Phase 2

## Session Continuity

Last session: 2026-01-30T08:06:43Z
Stopped at: Completed 06-01-PLAN.md (MLIR Lexer) - Phase 6 complete
Resume file: None
