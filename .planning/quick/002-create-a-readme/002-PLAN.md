---
phase: quick
plan: 002
type: execute
wave: 1
depends_on: []
files_modified: [README.md]
autonomous: true

must_haves:
  truths:
    - "A developer landing on the repo understands what codepicture does within 10 seconds"
    - "A user can install and run their first command by following the README"
    - "All CLI options are documented or discoverable from the README"
    - "The README reflects the actual current state of the tool (v0.1.0, Python 3.13+)"
  artifacts:
    - path: "README.md"
      provides: "Complete project README"
      min_lines: 120
  key_links: []
---

<objective>
Write a comprehensive README.md for codepicture -- a Python CLI tool that transforms code snippets into beautiful, presentation-ready images (PNG, SVG, PDF).

Purpose: The README is the first thing users and contributors see. It must communicate what the tool does, how to install it, and how to use it -- quickly and clearly.

Output: A polished README.md at the project root.
</objective>

<execution_context>
@/Users/bartel/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bartel/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@pyproject.toml
@src/codepicture/cli/app.py
@PYTHON_REWRITE_ARCHITECTURE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Write the README</name>
  <files>README.md</files>
  <action>
Write README.md following CLI tool README best practices. Structure it with these sections in order:

1. **Title + one-line description** -- "codepicture" with a concise tagline like "Generate beautiful images of your source code." No badges yet (no CI, no PyPI).

2. **Visual hook** -- A short paragraph (2-3 sentences) explaining what it does. Mention: takes source code files, applies syntax highlighting and visual styling (macOS window chrome, drop shadows, themes), outputs PNG/SVG/PDF. Position it as useful for presentations, documentation, social media.

3. **Quick start** -- Minimal steps to go from zero to first image:
   - Prerequisites: Python 3.13+, system Cairo/Pango libraries
   - Install: `pip install .` (from source, since not on PyPI yet)
   - Run: `codepicture snippet.py -o output.png`

4. **Features** -- Bullet list of key capabilities:
   - PNG, SVG, and PDF output
   - 260+ languages via Pygments (plus custom MLIR lexer)
   - Catppuccin themes + built-in Pygments themes (Dracula, Monokai, One Dark, etc.)
   - macOS-style window controls (traffic lights)
   - Drop shadow effect
   - Line numbers
   - Configurable font (bundled JetBrains Mono), padding, corner radius, background color
   - TOML config file support
   - Auto-detect language from file extension
   - Reads from file or stdin

5. **Usage examples** -- Show 3-4 real command examples with comments:
   - Basic: `codepicture hello.py -o hello.png`
   - With theme: `codepicture main.rs -o main.png --theme monokai`
   - SVG output, no shadow: `codepicture app.tsx -o app.svg --no-shadow`
   - From stdin: `echo 'print("hello")' | codepicture - -o hello.png --language python`
   - Custom styling: `codepicture code.go -o code.png --font-size 18 --padding 60 --no-line-numbers --background "#1e1e2e"`

6. **CLI reference** -- Full options table or formatted list. Pull directly from the actual CLI options in app.py. Group by category (Output, Theme/Language, Typography, Visual, Line Numbers, Window, Shadow, Config, Meta). Use a clean format -- either a table or grouped `--option` descriptions.

7. **Configuration** -- Explain TOML config file support:
   - Default search path: `~/.config/codepicture/config.toml`
   - Show a sample TOML config with the main sections (typography, line_numbers, window, effects, theme)
   - Note that CLI flags override config file values

8. **System dependencies** -- Platform-specific install instructions:
   - macOS: `brew install cairo pango`
   - Ubuntu/Debian: `apt install libcairo2-dev libgirepository1.0-dev`
   - Note: Python 3.13+ required

9. **Development** -- Brief section for contributors:
   - Clone, `uv sync`
   - Run tests: `pytest`
   - 260 tests, 80%+ coverage requirement

10. **License** -- "MIT" or appropriate placeholder (check if LICENSE file exists; if not, just say "MIT License" as a placeholder).

Important guidelines:
- Use clean, scannable Markdown. No walls of text.
- Code blocks with appropriate language hints (bash, toml, python).
- The CLI command is `codepicture`, NOT `silicon` (the architecture doc references "silicon" which was the old name).
- Python version is 3.13+ (from pyproject.toml), NOT 3.11+ (architecture doc is outdated).
- Keep total length between 150-250 lines. Enough to be comprehensive, short enough to not be overwhelming.
- Do NOT include badges, CI status, or PyPI links (project is not published yet).
- Do NOT use emojis.
  </action>
  <verify>
Verify the README:
1. File exists at project root: `ls -la README.md`
2. Contains all required sections: grep for "Quick Start", "Features", "Usage", "CLI", "Configuration", "Dependencies" (or similar headings)
3. References correct Python version (3.13+)
4. Uses `codepicture` command name (not `silicon`)
5. Line count is in range: `wc -l README.md` should be 120-300
  </verify>
  <done>
README.md exists at project root with all sections: title, description, quick start, features, usage examples, CLI reference, configuration, system dependencies, and development. All information is accurate to the current codebase (Python 3.13+, codepicture command, actual CLI options).
  </done>
</task>

</tasks>

<verification>
- README.md renders correctly as Markdown (no broken formatting)
- All code examples use the `codepicture` command name
- Python version matches pyproject.toml (3.13+)
- CLI options documented match actual options in src/codepicture/cli/app.py
- No references to "silicon" (old project name)
</verification>

<success_criteria>
A developer visiting the repo can: (1) understand what codepicture does in 10 seconds, (2) install it in under 2 minutes, (3) generate their first code image by copying a command from the README.
</success_criteria>

<output>
After completion, create `.planning/quick/002-create-a-readme/002-SUMMARY.md`
</output>
