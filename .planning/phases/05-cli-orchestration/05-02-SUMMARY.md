---
phase: 05-cli-orchestration
plan: 02
subsystem: cli
tags: [typer, cli, orchestration, pipeline]

# Dependency graph
requires:
  - phase: 05-01
    provides: Config loader with load_config function
  - phase: 01-04
    provides: Core types (OutputFormat, RenderConfig)
  - phase: 02
    provides: PygmentsHighlighter for tokenization
  - phase: 03
    provides: LayoutEngine and PangoTextMeasurer
  - phase: 04
    provides: Renderer for image generation
provides:
  - Pipeline orchestrator (generate_image function)
  - Typer CLI app with all config options as flags
  - --version and --list-themes eager callbacks
  - Stdin support for piped input
affects: [05-03, 05-04]

# Tech tracking
tech-stack:
  added: [typer, rich]
  patterns: [orchestrator-separation, cli-overrides]

key-files:
  created:
    - src/codepicture/cli/__init__.py
    - src/codepicture/cli/orchestrator.py
    - src/codepicture/cli/app.py

key-decisions:
  - "Orchestrator is a pure function that takes already-loaded config"
  - "CLI builds override dict from flags, passes to load_config"
  - "Stdin input requires --language flag"
  - "Output format inferred from extension, overridable with -f"

patterns-established:
  - "Orchestrator pattern: separate business logic from CLI parsing"
  - "CLI override pattern: build dict of non-None values"

# Metrics
duration: 2min
completed: 2026-01-29
---

# Phase 05 Plan 02: CLI Module Summary

**Typer CLI app with orchestrator wiring all codepicture components into single generate_image pipeline**

## Performance

- **Duration:** 2 min
- **Started:** 2026-01-29T10:49:48Z
- **Completed:** 2026-01-29T10:51:30Z
- **Tasks:** 2
- **Files created:** 3

## Accomplishments

- Created orchestrator module with generate_image function wiring all components
- Built Typer CLI with all config options as command-line flags
- Implemented --version and --list-themes as eager callbacks
- Added stdin support requiring --language flag

## Task Commits

Each task was committed atomically:

1. **Task 1: Create orchestrator module** - `a09e528` (feat)
2. **Task 2: Create Typer CLI app** - `5286693` (feat)

## Files Created

- `src/codepicture/cli/__init__.py` - Module exports (app, generate_image)
- `src/codepicture/cli/orchestrator.py` - Pipeline orchestration (68 lines)
- `src/codepicture/cli/app.py` - Typer CLI application (260 lines)

## Decisions Made

- **Orchestrator is pure function:** Takes already-loaded config, returns None on success. CLI handles config loading. This separation enables easy testing and reuse.
- **CLI builds override dict:** Only non-None flag values added to overrides dict, passed to load_config which handles merging.
- **Stdin requires --language:** Cannot auto-detect language from stdin, so --language flag is required when using `-` for input.
- **Format inference:** Output format inferred from -o extension (.png, .svg, .pdf), overridable with -f/--format flag.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- CLI module complete and importable
- Ready for 05-03 entry point and console script registration
- Ready for 05-04 integration testing

---
*Phase: 05-cli-orchestration*
*Completed: 2026-01-29*
