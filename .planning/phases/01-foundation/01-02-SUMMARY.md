---
phase: 01-foundation
plan: 02
subsystem: config
tags: [protocols, pydantic, toml, config]

dependency_graph:
  requires: ["01-01"]
  provides: ["protocols", "config-system"]
  affects: ["02-*", "03-*"]

tech_stack:
  added: []
  patterns: ["protocol-based-abstractions", "pydantic-validation", "toml-config"]

key_files:
  created:
    - src/codepicture/core/protocols.py
    - src/codepicture/config/schema.py
    - src/codepicture/config/loader.py
    - src/codepicture/config/__init__.py
  modified:
    - src/codepicture/core/__init__.py
    - src/codepicture/__init__.py

decisions: []

metrics:
  duration: 3 min
  completed: 2026-01-28
---

# Phase 1 Plan 02: Protocols and Configuration Summary

**Protocol definitions for Canvas/Highlighter/Theme/TextMeasurer with Pydantic RenderConfig and TOML config loading (CLI > local > global > defaults)**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-28T14:05:07Z
- **Completed:** 2026-01-28T14:07:48Z
- **Tasks:** 3
- **Files created:** 4
- **Files modified:** 2

## Accomplishments

- Created TextMeasurer protocol for text dimension measurement
- Created Canvas protocol with drawing, clipping, shadow, and save methods
- Created Highlighter protocol for syntax tokenization with language detection
- Created Theme protocol for color/style definitions with token-based styling
- Implemented RenderConfig Pydantic model with all configuration fields
- Added field validators for string-to-enum conversion (output_format, window_style)
- Added hex color validation for background_color (#RGB, #RRGGBB, #RRGGBBAA)
- Implemented load_config() with multi-layer config merging
- Defined DEFAULT_GLOBAL_CONFIG_PATH and DEFAULT_LOCAL_CONFIG_PATH
- Graceful handling of missing config files
- ConfigError wrapping for TOML parse errors and validation errors

## Files Created/Modified

- `src/codepicture/core/protocols.py` - TextMeasurer, Canvas, Highlighter, Theme protocols
- `src/codepicture/config/schema.py` - RenderConfig Pydantic model with validators
- `src/codepicture/config/loader.py` - load_config() with TOML support and merging
- `src/codepicture/config/__init__.py` - Module exports
- `src/codepicture/core/__init__.py` - Added protocol exports
- `src/codepicture/__init__.py` - Added RenderConfig and load_config exports

## Decisions Made

- Used TYPE_CHECKING guard for Color/TextStyle imports in protocols (avoids circular imports)
- Did NOT use @runtime_checkable on protocols (per RESEARCH.md anti-patterns)
- ConfigError wraps both TOML parse errors and Pydantic validation errors with detailed messages
- None values in cli_overrides are filtered out (allows partial CLI overrides)

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Hash    | Type | Description                              |
|---------|------|------------------------------------------|
| ee8f77f | feat | Create protocol definitions              |
| 74e7cf7 | feat | Create RenderConfig Pydantic model       |
| 5c1ba3a | feat | Create config loader with TOML support   |

## Next Phase Readiness

Phase 1 foundation is now complete. Ready for Phase 2 (Rendering):
- Protocols define interfaces for Canvas, Highlighter, Theme, TextMeasurer
- RenderConfig provides validated configuration for all rendering options
- Config loading supports global, local, and CLI override precedence
