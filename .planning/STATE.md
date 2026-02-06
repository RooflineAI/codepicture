# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-02)

**Core value:** One command turns code into a slide-ready image
**Current focus:** v2.0 Line Highlighting -- Phase 12 (Core Highlighting Infrastructure)

## Current Position

Phase: 12 of 14 (Core Highlighting Infrastructure)
Plan: 1 of 4 in current phase
Status: In progress
Last activity: 2026-02-06 -- Completed 12-01-PLAN.md (line range parser + color resolver)

Progress: [###.......] 1/4 plans in phase 12 (v2.0)

## Performance Metrics

**Velocity (v1.0):**
- Total plans completed: 21
- Average duration: 2.6 min
- Total execution time: 0.93 hours

**Velocity (v1.1):**
- Total plans completed: 14
- Phases: 5
- Timeline: 4 days (2026-01-30 -> 2026-02-02)

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table (15 decisions total).

**v2.0 execution decisions:**
- 12-01: DEFAULT_HIGHLIGHT_COLOR = Color(r=255, g=230, b=80, a=64) -- warm yellow #FFE65040 at ~25% opacity
- 12-01: DEFAULT_HIGHLIGHT_ALPHA = 64 shared by default color and 6-char hex fallback
- 12-01: HIGHLIGHT_CORNER_RADIUS = 0 (sharp rects now, constant exported for future phases)

### Pending Todos

None.

### Blockers/Concerns

- Phase 14 (Theme Integration): Research flagged that theme-aware color derivation heuristics may need deeper investigation. Start with `lerp(background, tint, 0.15)` and escalate if needed.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 003 | Fix PNG colour difference vs SVG/PDF (BGRA channel swap) | 2026-02-02 | b25efe0 | [003](./quick/003-fix-png-colour-difference-vs-svg-pdf-sha/) |
| 004 | Add window width/height and word wrap | 2026-02-02 | 6e8243b | [004](./quick/004-add-window-width-height-and-word-wrap/) |
| 005 | Add reference tests for wordwrap/fixed sizes | 2026-02-02 | a407ea7 | [005](./quick/005-add-reference-tests-wordwrap-fixed-sizes/) |
| 006 | Reduce default padding to 20px, update README | 2026-02-02 | 6da16c7 | [006](./quick/006-reduce-padding-update-readme-window-s/) |
| 007 | Add visual reference update command to README | 2026-02-02 | 38633ed | [007](./quick/007-add-readme-reference-update-command/) |
| 008 | Fix cairocffi discovery, regenerate baselines | 2026-02-02 | 3c70695 | [008](./quick/008-fix-pytest-snapshot-update/) |
| 009 | Move test.mlir to tests/fixtures/mlir/ | 2026-02-02 | 9df2b4c | [009](./quick/009-move-the-top-level-test-mlir-file-into-a/) |
| 010 | Add benchmark instructions to README | 2026-02-02 | a158e38 | [010](./quick/010-add-to-the-readme-how-to-run-the-benchma/) |
| 011 | Move MLIR lexer to custom_lexers subfolder | 2026-02-02 | 90706e9 | [011](./quick/011-move-mlir-lexer-to-custom-lexers-subfold/) |
| 012 | Set up linting and formatting via ruff | 2026-02-02 | 70c4606 | [012](./quick/012-set-up-linting-and-formatting-via-ruff/) |
| 013 | Add pre-commit and linting to README | 2026-02-02 | cdc30a4 | [013](./quick/013-add-pre-commit-and-linting-to-readme/) |

### Roadmap Evolution

- v1.0 shipped 2026-01-30 (Phases 1-6, 21 plans)
- v1.1 shipped 2026-02-02 (Phases 7-11, 14 plans)
- v2.0 roadmap created 2026-02-02 (Phases 12-14)

## Session Continuity

Last session: 2026-02-06
Stopped at: Completed 12-01-PLAN.md (line range parser + color resolver)
Resume file: None
