---
phase: quick
plan: 006
type: execute
wave: 1
depends_on: []
files_modified:
  - src/codepicture/config/schema.py
  - tests/conftest.py
  - tests/config/test_loader.py
  - tests/config/test_schema.py
  - README.md
autonomous: true

must_haves:
  truths:
    - "Default padding is 20px (half of previous 40px)"
    - "README documents --width, --height options"
    - "README example config shows updated padding default"
    - "All tests pass with new default"
  artifacts:
    - path: "src/codepicture/config/schema.py"
      provides: "Updated default padding value"
      contains: "padding.*= 20"
    - path: "README.md"
      provides: "Documentation for window size options"
      contains: "--width"
  key_links:
    - from: "src/codepicture/config/schema.py"
      to: "tests/config/test_schema.py"
      via: "default value assertions"
      pattern: "padding == 20"
---

<objective>
Reduce default padding from 40px to 20px and update README to document --width, --height, and word wrap CLI options.

Purpose: Tighter default padding produces better-looking output; README should reflect all available CLI options.
Output: Updated schema default, passing tests, complete README documentation.
</objective>

<execution_context>
@/Users/bartel/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bartel/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@src/codepicture/config/schema.py
@src/codepicture/cli/app.py
@README.md
@tests/conftest.py
@tests/config/test_loader.py
@tests/config/test_schema.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Reduce default padding and fix tests</name>
  <files>
    src/codepicture/config/schema.py
    tests/conftest.py
    tests/config/test_loader.py
    tests/config/test_schema.py
  </files>
  <action>
  1. In `src/codepicture/config/schema.py` line 45, change the default padding from `40` to `20`:
     `padding: Annotated[int, Field(ge=0, le=500)] = 20`

  2. In `tests/conftest.py` line 45, update the config fixture to use padding = 20:
     `padding = 20`

  3. In `tests/config/test_schema.py` line 22, update assertion:
     `assert config.padding == 20`

  4. In `tests/config/test_loader.py`, update all assertions that check `padding == 40` to `padding == 20`:
     - Line 36: `assert config.padding == 20`
     - Line 43: `assert config.padding == 20`
     - Line 125: This test checks that a config WITHOUT padding uses the default (not 20 from file). Update the comment and expected value: `assert config.padding == 20  # default, not overridden`

  5. Regenerate visual reference snapshots since default padding changed:
     `pytest tests/visual/ --snapshot-update -x`

  6. Run full test suite to confirm nothing breaks:
     `pytest`
  </action>
  <verify>`pytest` -- all tests pass</verify>
  <done>Default padding is 20px. All test assertions updated. Visual references regenerated. Full test suite green.</done>
</task>

<task type="auto">
  <name>Task 2: Update README with window size options</name>
  <files>README.md</files>
  <action>
  1. In `README.md`, add a new "Window Size" section to the CLI Reference, after the existing "### Window" section (after line 126). Add this table:

  ```
  ### Window Size

  | Option | Description |
  |--------|-------------|
  | `--width N` | Window width in pixels (enables word wrap) |
  | `--height N` | Window height in pixels |
  ```

  2. Update the example config TOML block (around line 171) to include window size options and the new default padding. Change `padding = 40` to `padding = 20` and add window width/height entries under `[visual]`:

  ```toml
  [visual]
  padding = 20
  corner_radius = 8
  background_color = "#1e1e2e"
  # window_width = 800    # optional: fixed width (enables word wrap)
  # window_height = 600   # optional: fixed height
  ```

  3. In the Features list, add a bullet for word wrap:
     `- **Word wrap** -- automatic wrapping when using fixed window width`
  </action>
  <verify>Review README.md to confirm --width, --height are documented, padding example shows 20, and word wrap feature is listed.</verify>
  <done>README documents all window size CLI options (--width, --height), shows correct default padding (20), and mentions word wrap capability.</done>
</task>

</tasks>

<verification>
- `pytest` passes with zero failures
- `grep -n "padding.*= 20" src/codepicture/config/schema.py` confirms new default
- `grep -n "\-\-width\|\-\-height" README.md` shows documented options
</verification>

<success_criteria>
- Default padding changed from 40 to 20 in schema
- All tests updated and passing
- Visual references regenerated
- README documents --width, --height options with descriptions
- README example config reflects new padding default
- README features list mentions word wrap
</success_criteria>

<output>
After completion, create `.planning/quick/006-reduce-padding-update-readme-window-s/006-SUMMARY.md`
</output>
