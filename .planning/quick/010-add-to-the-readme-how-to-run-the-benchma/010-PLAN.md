---
phase: quick
plan: 010
type: execute
wave: 1
depends_on: []
files_modified: [README.md]
autonomous: true

must_haves:
  truths:
    - "README documents how to run benchmarks locally"
    - "README shows benchmark command options (basic run, JSON output, verbose)"
  artifacts:
    - path: "README.md"
      provides: "Benchmarks section in Development"
      contains: "tests/benchmarks"
  key_links: []
---

<objective>
Add a "Running Benchmarks" subsection to the Development section of README.md documenting how to run the benchmark suite locally.

Purpose: Users and contributors can discover and run the benchmark suite without reading CI config or test source.
Output: Updated README.md with benchmark instructions.
</objective>

<execution_context>
@/Users/bartel/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bartel/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@README.md
@tests/benchmarks/test_bench_pipeline.py
@tests/benchmarks/test_bench_highlight.py
@tests/benchmarks/test_bench_layout.py
@tests/benchmarks/test_bench_render.py
@.github/workflows/benchmark.yml
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add benchmarks subsection to README Development section</name>
  <files>README.md</files>
  <action>
Add a "### Running Benchmarks" subsection to the Development section of README.md, placed AFTER the "### Updating Visual Regression References" subsection (before the "The project has 300+ tests" line).

Content to add:

1. Brief intro: The project includes pytest-benchmark tests covering four pipeline stages: highlighting, layout, rendering, and end-to-end.

2. Basic command to run all benchmarks:
   ```bash
   uv run pytest tests/benchmarks/ --benchmark-only -v
   ```

3. Save results to JSON for comparison:
   ```bash
   uv run pytest tests/benchmarks/ --benchmark-only --benchmark-json=results.json
   ```

4. Run a specific stage benchmark:
   ```bash
   uv run pytest tests/benchmarks/test_bench_pipeline.py --benchmark-only -v
   ```

Keep the style consistent with existing README sections (short intro sentence, code blocks with comments, no unnecessary prose). Use the same heading level (###) as sibling sections.
  </action>
  <verify>Read README.md and confirm the new subsection exists between "Updating Visual Regression References" and the "The project has 300+ tests" line. Confirm code blocks render valid bash commands.</verify>
  <done>README.md contains a "Running Benchmarks" subsection with commands for running all benchmarks, saving JSON output, and running a single stage.</done>
</task>

</tasks>

<verification>
- README.md contains "### Running Benchmarks" heading
- The section includes `tests/benchmarks/` path in commands
- The section includes `--benchmark-only` flag
- Section placement is within the Development section
</verification>

<success_criteria>
README.md documents how to run the benchmark suite with clear, copy-pasteable commands.
</success_criteria>

<output>
After completion, create `.planning/quick/010-add-to-the-readme-how-to-run-the-benchma/010-SUMMARY.md`
</output>
