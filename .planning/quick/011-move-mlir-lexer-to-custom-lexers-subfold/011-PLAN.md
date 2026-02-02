---
phase: quick-011
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/codepicture/highlight/custom_lexers/__init__.py
  - src/codepicture/highlight/custom_lexers/mlir_lexer.py
  - src/codepicture/highlight/__init__.py
  - pyproject.toml
  - tests/highlight/test_mlir_lexer.py
  - tests/integration/test_mlir_rendering.py
autonomous: true
must_haves:
  truths:
    - "MLIR lexer lives under src/codepicture/highlight/custom_lexers/"
    - "All existing tests pass without modification to test logic"
    - "Pygments entry point still registers the MLIR lexer correctly"
  artifacts:
    - path: "src/codepicture/highlight/custom_lexers/__init__.py"
      provides: "Custom lexers package, re-exports MlirLexer"
    - path: "src/codepicture/highlight/custom_lexers/mlir_lexer.py"
      provides: "MLIR lexer implementation (moved from highlight/)"
  key_links:
    - from: "src/codepicture/highlight/__init__.py"
      to: "src/codepicture/highlight/custom_lexers/mlir_lexer.py"
      via: "from .custom_lexers.mlir_lexer import MlirLexer"
      pattern: "from \\.custom_lexers"
    - from: "pyproject.toml"
      to: "src/codepicture/highlight/custom_lexers/mlir_lexer.py"
      via: "pygments.lexers entry point"
      pattern: "codepicture\\.highlight\\.custom_lexers\\.mlir_lexer"
---

<objective>
Move the MLIR lexer from `src/codepicture/highlight/mlir_lexer.py` into a dedicated `custom_lexers` subfolder to keep custom lexer implementations separate from generic highlight infrastructure.

Purpose: Clean up source tree so custom lexers don't sit alongside core highlight utilities.
Output: MLIR lexer relocated to `src/codepicture/highlight/custom_lexers/mlir_lexer.py` with all imports updated.
</objective>

<execution_context>
@/Users/bartel/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bartel/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@src/codepicture/highlight/__init__.py
@src/codepicture/highlight/mlir_lexer.py
@pyproject.toml
@tests/highlight/test_mlir_lexer.py
@tests/integration/test_mlir_rendering.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create custom_lexers package and move MLIR lexer</name>
  <files>
    src/codepicture/highlight/custom_lexers/__init__.py
    src/codepicture/highlight/custom_lexers/mlir_lexer.py
    src/codepicture/highlight/mlir_lexer.py (delete)
  </files>
  <action>
1. Create directory `src/codepicture/highlight/custom_lexers/`.
2. Create `custom_lexers/__init__.py` that re-exports MlirLexer:
   ```python
   """Custom lexer implementations for languages not supported by Pygments."""
   from .mlir_lexer import MlirLexer
   __all__ = ["MlirLexer"]
   ```
3. Move (git mv) `src/codepicture/highlight/mlir_lexer.py` to `src/codepicture/highlight/custom_lexers/mlir_lexer.py`. The file contents stay exactly the same.
4. Delete the old `src/codepicture/highlight/mlir_lexer.py` (handled by git mv).
  </action>
  <verify>
    `ls src/codepicture/highlight/custom_lexers/mlir_lexer.py` exists.
    `ls src/codepicture/highlight/mlir_lexer.py` should NOT exist.
    `python -c "from codepicture.highlight.custom_lexers.mlir_lexer import MlirLexer; print(MlirLexer.name)"` prints "MLIR".
  </verify>
  <done>MLIR lexer file lives at custom_lexers/mlir_lexer.py and is importable from the new location.</done>
</task>

<task type="auto">
  <name>Task 2: Update all imports and entry points</name>
  <files>
    src/codepicture/highlight/__init__.py
    pyproject.toml
    tests/highlight/test_mlir_lexer.py
    tests/integration/test_mlir_rendering.py
  </files>
  <action>
1. In `src/codepicture/highlight/__init__.py`, change:
   `from .mlir_lexer import MlirLexer`
   to:
   `from .custom_lexers.mlir_lexer import MlirLexer`
   Keep the re-export in __all__ unchanged.

2. In `pyproject.toml`, update the Pygments entry point from:
   `mlir = "codepicture.highlight.mlir_lexer:MlirLexer"`
   to:
   `mlir = "codepicture.highlight.custom_lexers.mlir_lexer:MlirLexer"`

3. In `tests/highlight/test_mlir_lexer.py`, update:
   `from codepicture.highlight.mlir_lexer import MlirLexer`
   to:
   `from codepicture.highlight.custom_lexers.mlir_lexer import MlirLexer`

4. In `tests/integration/test_mlir_rendering.py`, update:
   `from codepicture.highlight.mlir_lexer import MlirLexer`
   to:
   `from codepicture.highlight.custom_lexers.mlir_lexer import MlirLexer`

5. Run `uv pip install -e .` to refresh the entry point registration.
  </action>
  <verify>
    `python -c "from codepicture.highlight import MlirLexer; print(MlirLexer.name)"` prints "MLIR".
    `cd /Users/bartel/Documents/newclone/codepicture && python -m pytest tests/highlight/test_mlir_lexer.py tests/integration/test_mlir_rendering.py -x -q` all pass.
  </verify>
  <done>All imports resolve to new location, Pygments entry point updated, all MLIR-related tests pass.</done>
</task>

</tasks>

<verification>
- `python -m pytest tests/ -x -q` -- full test suite passes
- `python -c "from codepicture.highlight import MlirLexer"` -- public API unchanged
- `ls src/codepicture/highlight/mlir_lexer.py` -- old file gone (should error)
- `ls src/codepicture/highlight/custom_lexers/mlir_lexer.py` -- new file exists
</verification>

<success_criteria>
- MLIR lexer lives at src/codepicture/highlight/custom_lexers/mlir_lexer.py
- Old mlir_lexer.py removed from highlight/ root
- All tests pass
- Public API (from codepicture.highlight import MlirLexer) still works
- Pygments entry point resolves correctly
</success_criteria>

<output>
After completion, create `.planning/quick/011-move-mlir-lexer-to-custom-lexers-subfold/011-SUMMARY.md`
</output>
