---
phase: quick-005
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/visual/test_visual_regression.py
  - tests/visual/references/python_png_wordwrap-600.png
  - tests/visual/references/python_png_wordwrap-400.png
  - tests/visual/references/python_png_fixed-800x300.png
  - tests/visual/references/python_png_fixed-600x400_wordwrap.png
autonomous: true

must_haves:
  truths:
    - "Word wrap with fixed window_width produces a visually distinct reference image"
    - "Fixed window_width + window_height produces a visually distinct reference image"
    - "Combined word wrap + fixed size produces a visually distinct reference image"
    - "All new reference tests pass via pixelmatch comparison against stored baselines"
  artifacts:
    - path: "tests/visual/test_visual_regression.py"
      provides: "New parametrized visual regression tests for word wrap and fixed sizes"
      contains: "test_visual_wordwrap_fixedsize"
    - path: "tests/visual/references/python_png_wordwrap-600.png"
      provides: "Baseline for word wrap at 600px width"
    - path: "tests/visual/references/python_png_fixed-800x300.png"
      provides: "Baseline for fixed 800x300 window"
  key_links:
    - from: "tests/visual/test_visual_regression.py"
      to: "tests/visual/conftest.py"
      via: "render_fixture, compare_images imports"
      pattern: "from .conftest import"
---

<objective>
Add visual regression reference tests for word wrapping and fixed window sizes.

Purpose: The word wrap and fixed window_width/window_height features (added in quick-004) have unit tests but no visual regression coverage. Reference image tests catch rendering regressions that unit tests miss (e.g., text clipping, layout overflow, incorrect wrap indentation).

Output: New parametrized test cases in `test_visual_regression.py` with stored PNG baselines in `tests/visual/references/`.
</objective>

<execution_context>
@/Users/bartel/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bartel/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@tests/visual/test_visual_regression.py
@tests/visual/conftest.py
@tests/test_word_wrap.py
@tests/conftest.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add word wrap and fixed size visual regression tests</name>
  <files>tests/visual/test_visual_regression.py</files>
  <action>
Add a new test section at the bottom of `tests/visual/test_visual_regression.py` following the exact same patterns as the existing `test_visual_config_variant` test.

Add a new constant `WORDWRAP_FIXEDSIZE_VARIANTS` as a list of tuples `(variant_name, config_overrides)`:

1. `("wordwrap-600", {"window_width": 600})` - word wrap at 600px width (forces wrapping on the longer lines in the Python fixture)
2. `("wordwrap-400", {"window_width": 400})` - word wrap at 400px width (forces more aggressive wrapping)
3. `("fixed-800x300", {"window_width": 800, "window_height": 300})` - fixed dimensions, no wrapping needed
4. `("fixed-600x400_wordwrap", {"window_width": 600, "window_height": 400})` - fixed dimensions with word wrapping

Add a new test function `test_visual_wordwrap_fixedsize` parametrized over `WORDWRAP_FIXEDSIZE_VARIANTS`. The test should:
- Use `visual_fixtures_dir / "python_visual.py"` as fixture (same as config variant tests)
- Use `"python"` as language
- Use `"png"` as output_format
- Name references as `python_png_{variant_name}.png` (e.g., `python_png_wordwrap-600.png`)
- Create `RenderConfig(output_format="png", **overrides)` and render via `render_fixture`
- Convert to PIL Image via `Image.open(BytesIO(data)).convert("RGBA")`
- Handle snapshot_update / reference creation (same pattern as existing tests)
- Compare with `compare_images` (same pattern as existing tests)
- Use `@pytest.mark.timeout(30)` decorator (same as existing tests)

The test function signature should accept the same fixtures: `snapshot_update`, `visual_fixtures_dir`, `references_dir`, `diff_output_dir`.

Do NOT modify any existing tests or constants. Only append the new section.
  </action>
  <verify>
Run `cd /Users/bartel/Documents/newclone/codepicture && python -m pytest tests/visual/test_visual_regression.py -k "wordwrap or fixedsize" -v` to verify tests are discovered. They will skip on first run (creating reference images).
  </verify>
  <done>New parametrized test function `test_visual_wordwrap_fixedsize` exists with 4 variants, follows existing patterns exactly.</done>
</task>

<task type="auto">
  <name>Task 2: Generate baseline reference images</name>
  <files>
    tests/visual/references/python_png_wordwrap-600.png
    tests/visual/references/python_png_wordwrap-400.png
    tests/visual/references/python_png_fixed-800x300.png
    tests/visual/references/python_png_fixed-600x400_wordwrap.png
  </files>
  <action>
Run the new tests with `--snapshot-update` to generate baseline reference images:

```bash
cd /Users/bartel/Documents/newclone/codepicture && python -m pytest tests/visual/test_visual_regression.py -k "wordwrap or fixedsize" --snapshot-update -v
```

This will create/update the 4 reference PNG files in `tests/visual/references/`.

After generating, run the tests again WITHOUT `--snapshot-update` to confirm they pass against the freshly created baselines:

```bash
cd /Users/bartel/Documents/newclone/codepicture && python -m pytest tests/visual/test_visual_regression.py -k "wordwrap or fixedsize" -v
```

Also run the full visual regression suite to confirm no existing tests were broken:

```bash
cd /Users/bartel/Documents/newclone/codepicture && python -m pytest tests/visual/ -v
```

All tests (new and existing) must pass.
  </action>
  <verify>
1. All 4 reference PNGs exist in `tests/visual/references/` with non-zero file sizes
2. `python -m pytest tests/visual/test_visual_regression.py -k "wordwrap or fixedsize" -v` shows 4 PASSED
3. `python -m pytest tests/visual/ -v` shows all tests passing (no regressions)
  </verify>
  <done>4 baseline reference images stored, all new tests pass against baselines, no existing visual regression tests broken.</done>
</task>

</tasks>

<verification>
- `python -m pytest tests/visual/ -v` -- all visual tests pass (existing + new)
- `ls tests/visual/references/python_png_wordwrap*.png tests/visual/references/python_png_fixed*.png` -- 4 new reference images exist
- New test names follow `python_png_{variant}` naming convention matching existing patterns
</verification>

<success_criteria>
- 4 new visual regression test cases covering word wrap and fixed window sizes
- 4 new reference PNG baseline images stored in `tests/visual/references/`
- All existing visual regression tests still pass
- Tests follow identical patterns to existing `test_visual_config_variant`
</success_criteria>

<output>
After completion, create `.planning/quick/005-add-reference-tests-wordwrap-fixed-sizes/005-SUMMARY.md`
</output>
