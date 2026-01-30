# Phase 7: Safety Nets - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Prevent CI hangs with test-level and job-level timeouts. Add pytest-timeout to the test suite and configure GitHub Actions job timeouts. Existing 260+ tests must continue passing. Deeper fixes (MLIR hang, application-level timeouts) are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Timeout thresholds
- Default per-test timeout: 5 seconds
- Tests marked `@pytest.mark.slow` get 15 seconds
- No ability to disable timeout entirely — every test has a limit
- Configuration lives in `pyproject.toml` under `[tool.pytest.ini_options]`
- No environment variable overrides — single source of truth in config
- Known-hanging test.mlir test: skip with reason ("hangs — fix in Phase 8")

### Timeout failure behavior
- Timed-out tests appear as FAILED with timeout reason in the message
- Stack trace always included on timeout — shows where the test was stuck
- Other tests continue running after a timeout (no fail-fast)
- Summary section at end lists timed-out tests separately from other failures

### CI job protection
- GitHub Actions workflow already exists — add timeout to it
- Per-job `timeout-minutes: 10` on each job (not workflow-level)
- Both layers enforced: pytest-timeout kills individual tests + GHA job timeout as outer safety net
- On timeout, upload test output as artifact for diagnosis

### Slow test handling
- `@pytest.mark.slow` marker for tests >2 seconds
- Developers can skip slow tests locally with `-m 'not slow'`; CI always runs everything
- Phase 7 includes auditing existing tests to identify and mark any that are already slow
- No warning zone — binary pass/fail, no near-timeout alerts

### Claude's Discretion
- pytest-timeout method (signal vs thread) — pick based on project dependencies and platform needs
- Exact pytest-timeout plugin configuration details
- How to implement the timed-out test summary section (plugin hook vs conftest)
- Artifact upload step configuration in GitHub Actions

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

*Phase: 07-safety-nets*
*Context gathered: 2026-01-30*
