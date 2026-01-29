# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-28)

**Core value:** One command turns code into a slide-ready image
**Current focus:** Phase 4 - Rendering

## Current Position

Phase: 4 of 7 (Rendering)
Plan: 3 of 4 in current phase
Status: In progress
Last activity: 2026-01-29 - Completed 04-03-PLAN.md (Shadow Post-Processing)

Progress: [#########-] 87%

## Performance Metrics

**Velocity:**
- Total plans completed: 13
- Average duration: 3.0 min
- Total execution time: 0.65 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 2/2 | 5 min | 2.5 min |
| 1.1 Testing Infrastructure | 2/2 | 5 min | 2.5 min |
| 2. Syntax Highlighting | 3/3 | 9 min | 3 min |
| 3. Layout Engine | 3/3 | 12 min | 4 min |
| 4. Rendering | 3/4 | 8 min | 2.7 min |

**Recent Trend:**
- Last 5 plans: 03-01 (6 min), 03-02 (4 min), 03-03 (2 min), 04-01 (2 min), 04-03 (4 min)
- Trend: Stable at 2-6 min per plan

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: MLIR lexer will use Sublime syntax file (not Pygments custom lexer)
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
- [04-03]: Cairo BGRA converted via Pillow RGBa mode to handle pre-multiplied alpha
- [04-03]: Shadow margin = blur*2 + max(offset) = 125px total expansion

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

Last session: 2026-01-29T09:39:59Z
Stopped at: Completed 04-03-PLAN.md (Shadow Post-Processing)
Resume file: None
