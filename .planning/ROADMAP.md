# Roadmap: codepicture

## Overview

codepicture transforms code snippets into polished, presentation-ready images via a single CLI command. The roadmap follows a layered architecture: foundation types and configuration first, then syntax highlighting and theming, then layout calculations, then rendering, then CLI orchestration, and finally the MLIR custom lexer that differentiates this tool from competitors. Each phase delivers testable, coherent functionality that builds on the previous.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Core types, protocols, configuration schema, and error handling
- [x] **Phase 1.1: Testing Infrastructure** - Set up pytest, test fixtures, and CI for the foundation code (INSERTED)
- [x] **Phase 2: Syntax Highlighting** - Pygments tokenization, theme system, language detection
- [x] **Phase 3: Layout Engine** - Text measurement, canvas sizing, typography settings
- [x] **Phase 4: Rendering** - Cairo/Pango rendering, visual effects, multi-format output
- [ ] **Phase 5: CLI & Orchestration** - Application facade, Typer CLI, config file loading
- [ ] **Phase 6: MLIR Lexer** - Custom Sublime syntax-based lexer for MLIR with dialect support

## Phase Details

### Phase 1: Foundation
**Goal**: Establish the core abstractions and data types that all other components depend on
**Depends on**: Nothing (first phase)
**Requirements**: CORE-02, TYPO-04
**Success Criteria** (what must be TRUE):
  1. Configuration schema validates settings at load time with clear error messages
  2. Protocol definitions exist for Canvas, Highlighter, Theme, and TextMeasurer
  3. Tab characters are normalized to configurable spaces during input processing
  4. Pydantic models enforce type constraints on all configuration values
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Core types, error hierarchy, and tab normalization
- [x] 01-02-PLAN.md — Protocol definitions and configuration system

### Phase 1.1: Testing Infrastructure (INSERTED)
**Goal**: Set up pytest, test fixtures, and CI for the foundation code
**Depends on**: Phase 1
**Requirements**: None (infrastructure)
**Success Criteria** (what must be TRUE):
  1. pytest is configured with appropriate plugins
  2. Test fixtures exist for core types and config loading
  3. CI pipeline runs tests on push
  4. Coverage reporting is enabled
**Plans**: 2 plans

Plans:
- [x] 01.1-01-PLAN.md — Pytest infrastructure and shared fixtures
- [x] 01.1-02-PLAN.md — Test suite and GitHub Actions CI

### Phase 2: Syntax Highlighting
**Goal**: Transform raw code into structured token streams with theme-mapped colors
**Depends on**: Phase 1
**Requirements**: HIGH-01, HIGH-02, HIGH-03, THEME-01, THEME-02
**Success Criteria** (what must be TRUE):
  1. Code is tokenized via Pygments with correct token types for common languages
  2. Language is auto-detected from file extension (e.g., .py, .rs, .go)
  3. Language can be explicitly overridden via --language flag
  4. Catppuccin theme produces correct colors for all token types
  5. Built-in Pygments themes (Dracula, Monokai, One Dark) are selectable
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — Pygments highlighter with position tracking and language detection
- [x] 02-02-PLAN.md — Theme system with Pygments wrapper and TOML support
- [x] 02-03-PLAN.md — Test suite for highlighting and theme modules

### Phase 3: Layout Engine
**Goal**: Calculate exact canvas dimensions and element positions before any rendering
**Depends on**: Phase 2
**Requirements**: TYPO-01, TYPO-02, TYPO-03
**Success Criteria** (what must be TRUE):
  1. Font family is configurable and affects text measurement
  2. Font size is configurable and correctly scales text dimensions
  3. Line height is configurable and affects vertical spacing
  4. Canvas dimensions are computed exactly before surface creation
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md — Font management and Pango-based text measurement
- [x] 03-02-PLAN.md — LayoutEngine with canvas dimension calculations
- [x] 03-03-PLAN.md — Test suite for layout module

### Phase 4: Rendering
**Goal**: Produce polished images with window chrome, shadows, and all visual effects
**Depends on**: Phase 3
**Requirements**: OUT-01, OUT-02, OUT-03, VIS-01, VIS-02, VIS-03, VIS-04, VIS-05, VIS-06
**Success Criteria** (what must be TRUE):
  1. PNG output produces valid image files with correct dimensions
  2. SVG output produces valid vector files that render correctly in browsers
  3. PDF output produces valid documents suitable for embedding in presentations
  4. macOS-style traffic light buttons (red/yellow/green) appear in window chrome
  5. Drop shadow renders with configurable blur and offset
  6. Line numbers appear in a gutter alongside code
  7. Padding, corner radius, and background color are all configurable
**Plans**: 5 plans

Plans:
- [x] 04-01-PLAN.md — CairoCanvas for PNG/SVG/PDF rendering
- [x] 04-02-PLAN.md — Window chrome (title bar, traffic lights)
- [x] 04-03-PLAN.md — Shadow post-processing with Pillow
- [x] 04-04-PLAN.md — Renderer orchestration
- [x] 04-05-PLAN.md — Render module test suite

### Phase 5: CLI & Orchestration
**Goal**: Deliver a working command-line tool that users can install and run
**Depends on**: Phase 4
**Requirements**: CORE-01, CORE-03
**Success Criteria** (what must be TRUE):
  1. User can run `codepicture input.py -o output.png` and get a styled image
  2. TOML config file at ~/.config/codepicture/config.toml is loaded if present
  3. CLI flags override config file settings (e.g., --theme overrides config theme)
  4. Help text explains all available options
**Plans**: TBD

Plans:
- [ ] 05-01: TBD

### Phase 6: MLIR Lexer
**Goal**: Provide first-class syntax highlighting for MLIR code via Sublime syntax integration
**Depends on**: Phase 2
**Requirements**: HIGH-04
**Success Criteria** (what must be TRUE):
  1. MLIR code is highlighted using a Sublime syntax definition file
  2. Common MLIR constructs (operations, types, attributes, regions) render with appropriate colors
  3. Sublime syntax file integrates with the highlighting pipeline via custom lexer support
  4. Unknown MLIR constructs fall back gracefully without breaking rendering
**Plans**: TBD

Plans:
- [ ] 06-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 1.1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/2 | Complete | 2026-01-28 |
| 1.1 Testing Infrastructure | 2/2 | Complete | 2026-01-28 |
| 2. Syntax Highlighting | 3/3 | Complete | 2026-01-28 |
| 3. Layout Engine | 3/3 | Complete | 2026-01-29 |
| 4. Rendering | 5/5 | Complete | 2026-01-29 |
| 5. CLI & Orchestration | 0/TBD | Not started | - |
| 6. MLIR Lexer | 0/TBD | Not started | - |

---
*Roadmap created: 2026-01-28*
