---
phase: quick-012
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - pyproject.toml
  - .pre-commit-config.yaml
  - src/codepicture/**/*.py
  - tests/**/*.py
autonomous: true

must_haves:
  truths:
    - "ruff check passes with zero errors on the entire codebase"
    - "ruff format reports no formatting changes needed"
    - "pre-commit hooks run ruff check and ruff format on every commit"
    - "pytest still passes after all lint/format fixes"
  artifacts:
    - path: "pyproject.toml"
      provides: "ruff configuration (tool.ruff section)"
      contains: "tool.ruff"
    - path: ".pre-commit-config.yaml"
      provides: "pre-commit hook configuration for ruff"
      contains: "ruff-pre-commit"
  key_links:
    - from: ".pre-commit-config.yaml"
      to: "ruff"
      via: "pre-commit hook invocation"
      pattern: "astral-sh/ruff-pre-commit"
---

<objective>
Set up ruff as the linter and formatter for the codepicture project, configure it in pyproject.toml, add pre-commit hooks, run both tools across the entire codebase to fix all issues, and verify tests still pass.

Purpose: Enforce consistent code quality and style automatically on every commit.
Output: Configured ruff + pre-commit hooks, all existing code passing lint/format checks.
</objective>

<execution_context>
@/Users/bartel/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bartel/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@pyproject.toml
</context>

<tasks>

<task type="auto">
  <name>Task 1: Configure ruff and pre-commit in project files</name>
  <files>pyproject.toml, .pre-commit-config.yaml</files>
  <action>
    1. Add ruff to the dev dependency group in pyproject.toml:
       - Add "ruff>=0.9" to [dependency-groups] dev list
       - Add "pre-commit>=4.0" to [dependency-groups] dev list

    2. Add [tool.ruff] configuration to pyproject.toml:
       - target-version = "py313"
       - line-length = 88
       - src = ["src", "tests"]

    3. Add [tool.ruff.lint] section:
       - select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF"]
         (pycodestyle errors/warnings, pyflakes, isort, pyupgrade, bugbear, simplify, ruff-specific)
       - No ignore rules initially -- let ruff tell us what needs fixing

    4. Add [tool.ruff.lint.isort] section:
       - known-first-party = ["codepicture"]

    5. Add [tool.ruff.format] section:
       - quote-style = "double"

    6. Create .pre-commit-config.yaml at project root:
       ```yaml
       repos:
         - repo: https://github.com/astral-sh/ruff-pre-commit
           rev: v0.9.6
           hooks:
             - id: ruff
               args: [--fix]
             - id: ruff-format
       ```

    7. Run `uv sync` to install ruff and pre-commit into the venv.

    8. Run `uv run pre-commit install` to set up the git hook.
  </action>
  <verify>
    - `uv run ruff --version` outputs a version
    - `uv run pre-commit --version` outputs a version
    - `.pre-commit-config.yaml` exists
    - `[tool.ruff]` section exists in pyproject.toml
    - `.git/hooks/pre-commit` exists (hook installed)
  </verify>
  <done>ruff and pre-commit are configured and installed, hooks are active</done>
</task>

<task type="auto">
  <name>Task 2: Run ruff across the codebase and fix all issues</name>
  <files>src/codepicture/**/*.py, tests/**/*.py</files>
  <action>
    1. Run `uv run ruff format .` to auto-format all Python files.

    2. Run `uv run ruff check --fix .` to auto-fix all fixable lint issues.

    3. Review any remaining (unfixable) lint errors from `uv run ruff check .`.
       - For each remaining error, fix manually OR add a targeted per-line noqa comment OR add the rule to [tool.ruff.lint] ignore list in pyproject.toml if it is a project-wide false positive.
       - Do NOT blanket-ignore rules. Only ignore specific rules that genuinely do not apply.

    4. Run `uv run ruff check .` -- must exit 0 with no errors.

    5. Run `uv run ruff format --check .` -- must exit 0 with no changes needed.

    6. Run `uv run pytest` to ensure all tests still pass after the changes.
       - If any tests fail, determine if the failure is from a lint fix (e.g., import reorder breaking a fixture) and adjust accordingly.

    7. Run `uv run pre-commit run --all-files` to verify the full pre-commit pipeline passes on the entire codebase.
  </action>
  <verify>
    - `uv run ruff check .` exits 0
    - `uv run ruff format --check .` exits 0
    - `uv run pytest` passes (same number of tests as before)
    - `uv run pre-commit run --all-files` exits 0
  </verify>
  <done>All Python files pass ruff lint and format checks, all tests pass, pre-commit hooks pass on full codebase</done>
</task>

</tasks>

<verification>
1. `uv run ruff check .` -- zero errors
2. `uv run ruff format --check .` -- zero reformats needed
3. `uv run pytest` -- all tests pass
4. `uv run pre-commit run --all-files` -- all hooks pass
</verification>

<success_criteria>
- ruff configured in pyproject.toml with sensible rule selection
- .pre-commit-config.yaml exists with ruff hooks
- pre-commit git hook installed
- All existing Python files pass ruff check and ruff format
- All existing tests still pass
</success_criteria>

<output>
After completion, create `.planning/quick/012-set-up-linting-and-formatting-via-ruff/012-SUMMARY.md`
</output>
