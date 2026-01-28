# Phase 1: Foundation - Context

**Gathered:** 2026-01-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Core types, protocols, configuration schema, and error handling that all other components depend on. This phase establishes the foundation — no rendering, no CLI, no syntax highlighting yet.

</domain>

<decisions>
## Implementation Decisions

### Configuration format
- Flat structure at top level (theme = "catppuccin", font_size = 14)
- Strict validation — invalid values cause immediate exit with clear error
- No environment variable overrides — config file + CLI flags only
- Global config at ~/.config/codepicture/config.toml
- Project-local config supported: .codepicture.toml in cwd
- Precedence: CLI flags > local config > global config (merge, not replace)
- No --init command — document example config in README

### Tab handling
- Default tab width: 4 spaces
- Tab width configurable via config file and --tab-width CLI flag
- No auto-detection from source — always use configured width

### Default behaviors
- Default theme: Catppuccin Mocha
- Default font family: JetBrains Mono
- Default font size: 14px
- Default output format: PNG

### Claude's Discretion
- Internal protocol/interface design
- Pydantic model structure
- Error message formatting details
- File loading and parsing implementation

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for the foundational infrastructure.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-01-28*
