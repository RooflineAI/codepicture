# Phase 5: CLI & Orchestration - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a working command-line tool that users can install and run. Users invoke `codepicture FILE -o OUTPUT` to convert code files into styled images. Supports TOML config files and CLI flag overrides. Does NOT include clipboard integration or config file generation.

</domain>

<decisions>
## Implementation Decisions

### Command structure
- Invocation: `codepicture FILE -o OUTPUT` (input positional, output required flag)
- Output flag -o/--output is required — error if not provided
- Stdin via `-`: `codepicture - -o out.png` (requires --language flag)
- Short flags for common options: -o output, -t theme, -l language, -f format
- Version flag: --version / -V
- Discovery: --list-themes shows available themes and exits

### Config file behavior
- Search order: ./codepicture.toml first, then ~/.config/codepicture/config.toml
- Local config replaces global entirely (no merge)
- CLI flags always override config values
- Unknown keys in config file cause an error (fail fast on typos)
- --config PATH overrides default search locations
- --config file only needs to specify overrides, missing keys use defaults

### Output defaults
- Format inferred from -o extension (.png, .svg, .pdf)
- -f/--format flag overrides inferred format
- No extension and no -f defaults to PNG
- Overwrite existing files silently (no --force needed)
- Auto-create parent directories for output path

### Error messages & feedback
- Silent on success (no output if everything works)
- -v/--verbose shows processing steps: loading config, detecting language, etc.
- Errors are simple messages: "Error: file not found: input.py"
- All errors go to stderr

### Testing approach
- Unit tests for config loading, arg parsing, orchestration logic
- Integration tests via subprocess: run CLI, check exit codes and output
- Verify output files exist and are valid format (not empty, correct magic bytes)
- Comprehensive error case testing: missing file, bad config, invalid flags
- Config tests use real temp files (not mocked filesystem)

### Claude's Discretion
- Exact help text wording
- Progress message format in verbose mode
- Exit code values for different error types
- Typer configuration details

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-cli-orchestration*
*Context gathered: 2026-01-29*
