---
phase: quick-009
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/fixtures/mlir/test.mlir
  - tests/integration/test_mlir_rendering.py
autonomous: true

must_haves:
  truths:
    - "test.mlir no longer exists at the project root"
    - "test.mlir lives in tests/fixtures/mlir/ alongside other MLIR fixtures"
    - "All tests that referenced the root test.mlir still pass"
  artifacts:
    - path: "tests/fixtures/mlir/test.mlir"
      provides: "Real-world MLIR test fixture (regression for hang fix)"
    - path: "tests/integration/test_mlir_rendering.py"
      provides: "Updated paths pointing to fixtures dir instead of project root"
  key_links:
    - from: "tests/integration/test_mlir_rendering.py"
      to: "tests/fixtures/mlir/test.mlir"
      via: "FIXTURES_DIR / test.mlir"
      pattern: "FIXTURES_DIR.*test\\.mlir"
---

<objective>
Move `test.mlir` from the project root into `tests/fixtures/mlir/` where all other MLIR test fixtures already live, and update the integration test file that references it.

Purpose: Clean up the project root by placing the test fixture alongside its peers.
Output: test.mlir relocated, tests still passing.
</objective>

<execution_context>
@/Users/bartel/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bartel/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@tests/integration/test_mlir_rendering.py
@tests/fixtures/mlir/
</context>

<tasks>

<task type="auto">
  <name>Task 1: Move test.mlir and update references</name>
  <files>
    tests/fixtures/mlir/test.mlir
    tests/integration/test_mlir_rendering.py
  </files>
  <action>
    1. Move `test.mlir` from the project root to `tests/fixtures/mlir/test.mlir`:
       ```
       git mv test.mlir tests/fixtures/mlir/test.mlir
       ```

    2. Update `tests/integration/test_mlir_rendering.py`:
       - In `test_mlir_render_completes` (line 32): change `PROJECT_ROOT / "test.mlir"` to `FIXTURES_DIR / "test.mlir"`
       - In `test_mlir_lexer_minimal_error_tokens` (line 53): change `PROJECT_ROOT / "test.mlir"` to `FIXTURES_DIR / "test.mlir"`
       - Remove the `PROJECT_ROOT` constant (line 16) if it is no longer used anywhere in the file after these changes
       - Update the module docstring to not specifically mention "test.mlir" at project root

    3. Verify no other Python files reference the root-level `test.mlir` path. (Grep already confirmed only `tests/integration/test_mlir_rendering.py` references it in code.)
  </action>
  <verify>
    Run the full test suite: `python -m pytest tests/ -x -v`
    Confirm test.mlir does NOT exist at project root: `! test -f test.mlir`
    Confirm test.mlir exists at new location: `test -f tests/fixtures/mlir/test.mlir`
  </verify>
  <done>
    - test.mlir lives at tests/fixtures/mlir/test.mlir
    - No test.mlir at project root
    - All tests pass (especially test_mlir_render_completes, test_mlir_lexer_minimal_error_tokens, test_mlir_corpus_renders)
  </done>
</task>

</tasks>

<verification>
- `ls test.mlir` returns "No such file"
- `ls tests/fixtures/mlir/test.mlir` succeeds
- `python -m pytest tests/integration/test_mlir_rendering.py -v` all pass
- `python -m pytest tests/ -x` full suite passes
</verification>

<success_criteria>
- test.mlir relocated from project root to tests/fixtures/mlir/
- Integration tests updated to use FIXTURES_DIR instead of PROJECT_ROOT for test.mlir
- All tests pass
</success_criteria>

<output>
After completion, create `.planning/quick/009-move-the-top-level-test-mlir-file-into-a/009-SUMMARY.md`
</output>
