---
type: quick
id: 001
objective: Flatten tests folder structure
autonomous: true
files_modified:
  - tests/test_errors.py
  - tests/core/test_types.py
  - tests/core/test_protocols.py
  - tests/config/test_schema.py
  - tests/config/test_loader.py
  - tests/text/test_normalize.py
files_removed:
  - tests/__init__.py
  - tests/codepicture/__init__.py
  - tests/codepicture/core/__init__.py
  - tests/codepicture/config/__init__.py
  - tests/codepicture/text/__init__.py
  - tests/codepicture/ (entire directory after moves)
---

<objective>
Flatten the tests/ folder structure by removing the unnecessary codepicture/ nesting level and all __init__.py files.

Purpose: Simplify test organization - pytest discovers tests without __init__.py files, and the extra codepicture/ folder adds unnecessary depth.

Output: Clean tests/ directory with test files organized by module (core/, config/, text/).
</objective>

<context>
@pyproject.toml (testpaths = ["tests"] - no changes needed)
@tests/conftest.py (keep in place)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Move test files and remove codepicture nesting</name>
  <files>
    tests/test_errors.py
    tests/core/test_types.py
    tests/core/test_protocols.py
    tests/config/test_schema.py
    tests/config/test_loader.py
    tests/text/test_normalize.py
  </files>
  <action>
Move test files from tests/codepicture/ to tests/:

1. Create new subdirectories directly under tests/:
   - mkdir -p tests/core tests/config tests/text

2. Move files:
   - mv tests/codepicture/test_errors.py tests/test_errors.py
   - mv tests/codepicture/core/test_types.py tests/core/test_types.py
   - mv tests/codepicture/core/test_protocols.py tests/core/test_protocols.py
   - mv tests/codepicture/config/test_schema.py tests/config/test_schema.py
   - mv tests/codepicture/config/test_loader.py tests/config/test_loader.py
   - mv tests/codepicture/text/test_normalize.py tests/text/test_normalize.py

3. Remove old directory structure:
   - rm -rf tests/codepicture/

4. Remove root __init__.py:
   - rm tests/__init__.py

5. Clean up pycache directories:
   - find tests -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  </action>
  <verify>
    - ls tests/ shows: conftest.py, test_errors.py, core/, config/, text/
    - ls tests/core/ shows: test_types.py, test_protocols.py
    - ls tests/config/ shows: test_schema.py, test_loader.py
    - ls tests/text/ shows: test_normalize.py
    - No __init__.py files anywhere in tests/
    - tests/codepicture/ directory does not exist
  </verify>
  <done>Test files moved to flattened structure, no __init__.py files remain</done>
</task>

<task type="auto">
  <name>Task 2: Verify tests still pass</name>
  <files>None (verification only)</files>
  <action>
Run the full test suite to confirm the restructuring didn't break anything:

1. Run pytest with coverage:
   uv run pytest --cov=src/codepicture --cov-report=term-missing

2. Verify:
   - All 95 tests pass
   - Coverage remains at 90%+
   - No import errors or module discovery issues
  </action>
  <verify>pytest exits with code 0, all tests pass</verify>
  <done>All 95 tests pass, coverage at 90%+, test discovery works correctly</done>
</task>

</tasks>

<verification>
- [ ] tests/ structure is flat (no codepicture/ subfolder)
- [ ] No __init__.py files in tests/ tree
- [ ] All 95 tests pass
- [ ] Coverage remains at 90%+
</verification>

<success_criteria>
Tests folder has clean structure:
```
tests/
    conftest.py
    test_errors.py
    core/
        test_types.py
        test_protocols.py
    config/
        test_schema.py
        test_loader.py
    text/
        test_normalize.py
```
All tests pass with no changes to test code itself.
</success_criteria>
