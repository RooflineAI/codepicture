---
phase: quick
plan: 013
type: execute
wave: 1
depends_on: []
files_modified: [README.md]
autonomous: true

must_haves:
  truths:
    - "README documents how to install and run pre-commit hooks"
    - "README documents ruff linting and formatting commands"
  artifacts:
    - path: "README.md"
      provides: "Linting/formatting and pre-commit documentation"
      contains: "pre-commit"
  key_links: []
---

<objective>
Add linting/formatting and pre-commit hook documentation to the README Development section.

Purpose: Contributors need to know how to set up pre-commit hooks and run ruff for linting/formatting. This was added in quick-012 but not yet documented.
Output: Updated README.md with new subsections under Development.
</objective>

<execution_context>
@/Users/bartel/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bartel/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@README.md
@pyproject.toml (ruff config in [tool.ruff] sections)
@.pre-commit-config.yaml (ruff pre-commit hooks)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add linting and pre-commit sections to README</name>
  <files>README.md</files>
  <action>
In README.md, add two new subsections inside the existing `## Development` section, placed between the "### Setup" subsection and the "### Running Tests" subsection.

**Add "### Linting and Formatting" subsection** with:
- Brief note that the project uses ruff for linting and formatting
- Commands to run linting check, linting with auto-fix, and formatting:
  ```bash
  uv run ruff check .
  uv run ruff check --fix .
  uv run ruff format .
  ```
- One-line note that configuration lives in `pyproject.toml` under `[tool.ruff]`

**Add "### Pre-commit Hooks" subsection** with:
- Brief note that pre-commit hooks run ruff lint (with auto-fix) and ruff format automatically on each commit
- Install command:
  ```bash
  uv run pre-commit install
  ```
- Manual run command:
  ```bash
  uv run pre-commit run --all-files
  ```

Also update the "### Setup" subsection to append `uv run pre-commit install` after the existing `uv sync` command, so new contributors get hooks installed as part of initial setup.

Keep the writing style consistent with the rest of the README: concise, no filler, code blocks with bash syntax highlighting.
  </action>
  <verify>
Read README.md and confirm:
1. "### Linting and Formatting" section exists with ruff commands
2. "### Pre-commit Hooks" section exists with install/run commands
3. Setup section includes `uv run pre-commit install`
4. Sections appear in correct order: Setup > Linting and Formatting > Pre-commit Hooks > Running Tests
  </verify>
  <done>README Development section documents ruff linting/formatting and pre-commit hook setup with accurate commands matching the project's actual configuration</done>
</task>

</tasks>

<verification>
- README.md contains "### Linting and Formatting" heading
- README.md contains "### Pre-commit Hooks" heading
- All commands use `uv run` prefix (project convention)
- Section ordering is logical within Development
</verification>

<success_criteria>
A new contributor reading the Development section knows how to:
1. Set up pre-commit hooks during initial setup
2. Run linting and formatting manually
3. Run pre-commit hooks manually on all files
</success_criteria>

<output>
After completion, create `.planning/quick/013-add-pre-commit-and-linting-to-readme/013-SUMMARY.md`
</output>
