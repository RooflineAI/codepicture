# Roadmap: codepicture

## Overview

codepicture transforms code snippets into polished, presentation-ready images via a single CLI command.

## Milestones

- SHIPPED **v1.0 MVP** -- Phases 1-6 (shipped 2026-01-30) -- [archive](milestones/v1.0-ROADMAP.md)
- SHIPPED **v1.1 Reliability & Testing** -- Phases 7-11 (shipped 2026-02-02) -- [archive](milestones/v1.1-ROADMAP.md)
- IN PROGRESS **v2.0 Line Highlighting** -- Phases 12-14

## Phases

<details>
<summary>v1.0 MVP (Phases 1-6) -- SHIPPED 2026-01-30</summary>

- [x] Phase 1: Foundation (2/2 plans) -- completed 2026-01-28
- [x] Phase 1.1: Testing Infrastructure (2/2 plans) -- completed 2026-01-28
- [x] Phase 2: Syntax Highlighting (3/3 plans) -- completed 2026-01-28
- [x] Phase 3: Layout Engine (3/3 plans) -- completed 2026-01-29
- [x] Phase 4: Rendering (5/5 plans) -- completed 2026-01-29
- [x] Phase 5: CLI & Orchestration (4/4 plans) -- completed 2026-01-29
- [x] Phase 6: MLIR Lexer (2/2 plans) -- completed 2026-01-30

</details>

<details>
<summary>v1.1 Reliability & Testing (Phases 7-11) -- SHIPPED 2026-02-02</summary>

- [x] Phase 7: Safety Nets (2/2 plans) -- completed 2026-01-30
- [x] Phase 8: MLIR Hang Fix (2/2 plans) -- completed 2026-01-30
- [x] Phase 9: Rendering Timeout Guards (3/3 plans) -- completed 2026-01-30
- [x] Phase 10: Visual Regression & Reliability (4/4 plans) -- completed 2026-01-31
- [x] Phase 11: Performance Benchmarks (3/3 plans) -- completed 2026-02-02

</details>

### v2.0 Line Highlighting (In Progress)

**Milestone Goal:** Add the ability to highlight specific lines with colored backgrounds, supporting multiple named styles (add/remove/focus) for presentation-ready code annotations.

- [x] **Phase 12: Core Highlighting Infrastructure** - Single-style line highlighting with configurable color across all formats -- completed 2026-02-06
- [x] **Phase 13: Named Styles, Focus Mode & Gutter Indicators** - Multiple highlight styles with focus dimming and diff-style gutter markers (completed 2026-03-31)
- [ ] **Phase 14: Theme Integration & Documentation** - Theme-aware default colors and complete documentation

## Phase Details

### Phase 12: Core Highlighting Infrastructure
**Goal**: Users can highlight specific lines of code with a colored background overlay using a CLI flag or TOML config
**Depends on**: Phase 11 (existing rendering pipeline)
**Requirements**: HLCORE-01, HLCORE-02, HLCORE-03, HLCORE-04, HLCORE-05, HLCORE-06, HLCORE-07, HLTEST-01, HLTEST-03, HLTEST-05, HLTEST-07
**Success Criteria** (what must be TRUE):
  1. User can run `codepicture snippet.py --highlight-lines '3,7-12' -o out.png` and see those lines with a colored background
  2. Highlighted output renders correctly in PNG, SVG, and PDF with no visual differences in highlight placement
  3. Word-wrapped source lines highlight ALL their display lines (no partial highlights)
  4. User can customize highlight color via `--highlight-color '#RRGGBBAA'` or TOML config
  5. Line range parser handles edge cases: single lines, ranges, mixed, out-of-bounds, empty input
**Plans**: 4 plans

Plans:
- [x] 12-01-PLAN.md -- Line range parser and highlight color resolver (TDD)
- [x] 12-02-PLAN.md -- Config schema fields and CLI flag wiring
- [x] 12-03-PLAN.md -- Renderer integration (highlight rectangle drawing)
- [x] 12-04-PLAN.md -- Tests: CLI integration, visual regression, word-wrap integration

### Phase 13: Named Styles, Focus Mode & Gutter Indicators
**Goal**: Users can apply distinct highlight styles (add/remove/focus) to different line groups in a single render, with focus mode dimming and gutter indicators
**Depends on**: Phase 12
**Requirements**: HLSTYL-01, HLSTYL-02, HLSTYL-03, HLSTYL-04, HLSTYL-05, HLFOC-01, HLFOC-02, HLFOC-03, HLGUT-01, HLGUT-02, HLTEST-02, HLTEST-04, HLTEST-06, HLTEST-08
**Success Criteria** (what must be TRUE):
  1. User can run `codepicture snippet.py --highlight '3-5:add' --highlight '10:remove' -o out.png` and see green and red highlights on the respective lines
  2. When `focus` style is used, unfocused lines are visibly dimmed while focused lines remain at full brightness
  3. Named styles display gutter indicators beside line numbers (+ for add, - for remove, colored bar for focus/highlight)
  4. User can customize per-style colors via TOML config (`[highlight_styles.add] color = "#..."`)
  5. When no style is specified (`--highlight '3-5'`), the default `highlight` style is applied
**Plans**: 3 plans

Plans:
- [x] 13-01-PLAN.md -- Data model, parser, config schema, CLI flag, and unit tests
- [x] 13-02-PLAN.md -- Renderer integration (per-style highlights, focus dimming, gutter indicators)
- [x] 13-03-PLAN.md -- Visual regression and integration tests

### Phase 14: Theme Integration & Documentation
**Goal**: Highlight colors automatically adapt to the active theme for readable contrast, and all features are documented with examples
**Depends on**: Phase 13
**Requirements**: HLTHEM-01, HLTHEM-02, HLTHEM-03, HLDOC-01, HLDOC-02, HLDOC-03
**Success Criteria** (what must be TRUE):
  1. Default highlight colors are visually appropriate on both light and dark themes without user configuration
  2. Syntax tokens remain readable on highlighted lines across all 55+ themes
  3. User-specified colors via CLI flags or TOML config override theme-derived defaults
  4. README documents all highlight CLI flags, TOML config options, and includes visual examples of each style
**Plans**: TBD

Plans:
- [ ] 14-01: TBD
- [ ] 14-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 12 -> 13 -> 14

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-01-28 |
| 1.1 Testing Infrastructure | v1.0 | 2/2 | Complete | 2026-01-28 |
| 2. Syntax Highlighting | v1.0 | 3/3 | Complete | 2026-01-28 |
| 3. Layout Engine | v1.0 | 3/3 | Complete | 2026-01-29 |
| 4. Rendering | v1.0 | 5/5 | Complete | 2026-01-29 |
| 5. CLI & Orchestration | v1.0 | 4/4 | Complete | 2026-01-29 |
| 6. MLIR Lexer | v1.0 | 2/2 | Complete | 2026-01-30 |
| 7. Safety Nets | v1.1 | 2/2 | Complete | 2026-01-30 |
| 8. MLIR Hang Fix | v1.1 | 2/2 | Complete | 2026-01-30 |
| 9. Rendering Timeout Guards | v1.1 | 3/3 | Complete | 2026-01-30 |
| 10. Visual Regression & Reliability | v1.1 | 4/4 | Complete | 2026-01-31 |
| 11. Performance Benchmarks | v1.1 | 3/3 | Complete | 2026-02-02 |
| 12. Core Highlighting Infrastructure | v2.0 | 4/4 | Complete | 2026-02-06 |
| 13. Named Styles, Focus & Gutter | v2.0 | 3/3 | Complete    | 2026-03-31 |
| 14. Theme Integration & Docs | v2.0 | 0/TBD | Not started | - |

---
*Roadmap created: 2026-01-28*
*v1.0 shipped: 2026-01-30*
*v1.1 shipped: 2026-02-02*
*v2.0 roadmap: 2026-02-02*
