---
phase: quick-004
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/codepicture/config/schema.py
  - src/codepicture/layout/engine.py
  - src/codepicture/core/types.py
  - src/codepicture/render/renderer.py
  - src/codepicture/cli/app.py
  - tests/test_layout.py
  - tests/test_word_wrap.py
autonomous: true

must_haves:
  truths:
    - "User can set window width and height via CLI flags --width and --height"
    - "Lines exceeding window width wrap to next visual line with indent, like VSCode"
    - "Wrapped continuation lines have NO line number in the gutter"
    - "Wrapped continuation lines are indented by 2 chars relative to code_x"
    - "Window height clips or constrains the visible area (canvas uses explicit height)"
    - "When width/height are None (default), behavior is unchanged from current auto-sizing"
  artifacts:
    - path: "src/codepicture/config/schema.py"
      provides: "window_width and window_height optional fields on RenderConfig"
    - path: "src/codepicture/layout/engine.py"
      provides: "Word-wrapping logic that splits lines exceeding max code width"
    - path: "src/codepicture/render/renderer.py"
      provides: "Rendering of wrapped lines with indent and no line numbers"
  key_links:
    - from: "src/codepicture/layout/engine.py"
      to: "src/codepicture/core/types.py"
      via: "LayoutMetrics now includes wrapped line mapping"
      pattern: "display_lines"
    - from: "src/codepicture/render/renderer.py"
      to: "LayoutMetrics"
      via: "Uses display_lines to render with wrap awareness"
      pattern: "display_lines"
---

<objective>
Add window width/height controls and VSCode-style word wrapping to codepicture.

When a user sets `--width`, lines that exceed the available code area wrap to the next visual line. Wrapped continuation lines are indented (like VSCode) but have no line number. When `--height` is set, the canvas uses that explicit height. When neither is set, behavior is identical to current auto-sizing.

Purpose: Allow users to control output image dimensions and handle long lines gracefully.
Output: Working width/height CLI options with word-wrap rendering.
</objective>

<execution_context>
@/Users/bartel/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bartel/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@src/codepicture/config/schema.py
@src/codepicture/layout/engine.py
@src/codepicture/layout/measurer.py
@src/codepicture/core/types.py
@src/codepicture/render/renderer.py
@src/codepicture/cli/app.py
@src/codepicture/cli/orchestrator.py
@tests/test_layout.py
@tests/conftest.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add config fields, LayoutMetrics display_lines, and word-wrap in LayoutEngine</name>
  <files>
    src/codepicture/config/schema.py
    src/codepicture/core/types.py
    src/codepicture/layout/engine.py
  </files>
  <action>
**config/schema.py** - Add two optional fields to RenderConfig:
- `window_width: Annotated[int | None, Field(ge=100, le=10000)] = None` -- explicit window width in pixels (None = auto-size as today)
- `window_height: Annotated[int | None, Field(ge=50, le=10000)] = None` -- explicit window height in pixels (None = auto-size as today)

**core/types.py** - Add a `DisplayLine` dataclass and extend `LayoutMetrics`:

```python
@dataclass(frozen=True, slots=True)
class DisplayLine:
    """A visual line on screen (may be a source line or a wrap continuation)."""
    source_line_idx: int       # Index into original `lines` list
    token_start: int           # Start index into source line's token list
    token_end: int             # End index (exclusive) into source line's token list
    char_offset: int           # Character offset within source line where this display line starts
    is_continuation: bool      # True if this is a wrapped continuation (no line number)
```

Add to LayoutMetrics:
- `display_lines: tuple[DisplayLine, ...] = ()` -- ordered list of visual lines (empty tuple = no wrapping, old behavior)
- `wrap_indent_chars: int = 2` -- number of characters to indent continuation lines

**layout/engine.py** - Modify `calculate_metrics`:

1. After computing `char_width`, `gutter_width`, `gap`, and `code_width`, check if `config.window_width` is set.
2. If `window_width` is set, compute `available_code_width`:
   - `available_code_width = window_width - 2 * padding - gutter_width - gap`
   - `max_code_chars = floor(available_code_width / char_width)`
3. Build `display_lines` list by iterating over each source line:
   - For each source line, compute total chars: `sum(len(t.text) for t in line)`
   - If total chars <= max_code_chars, add ONE DisplayLine with is_continuation=False, token_start=0, token_end=len(line), char_offset=0
   - If total chars > max_code_chars, split the line into chunks:
     - First chunk: max_code_chars characters, is_continuation=False
     - Subsequent chunks: (max_code_chars - wrap_indent_chars) characters each, is_continuation=True
     - For each chunk, compute token_start/token_end by walking the tokens and counting chars. A token may span chunks -- in that case, the renderer will need to split the token text. Store char_offset for each chunk.
4. Use `len(display_lines)` instead of `len(lines)` for content_height calculation.
5. For canvas_width: if window_width is set, use `window_width`. Otherwise use existing auto-sized calculation.
6. For canvas_height: if window_height is set, use `window_height`. Otherwise use `int(content_height + 2 * padding)` (using display_lines count for content_height).
7. `code_width` should be `available_code_width` when window_width is set, otherwise `max_chars * char_width` as before.
8. Store `display_lines` as tuple in returned LayoutMetrics, and `wrap_indent_chars=2`.

When window_width is None, display_lines should be empty tuple (signals renderer to use legacy path for backward compatibility).

IMPORTANT: The wrap_indent_chars (2) is in character units, not pixels. The renderer will multiply by char_width.
  </action>
  <verify>
Run `cd /Users/bartel/Documents/newclone/codepicture && python -c "from codepicture.config.schema import RenderConfig; c = RenderConfig(window_width=600); print(c.window_width)"` prints 600.
Run `cd /Users/bartel/Documents/newclone/codepicture && python -c "from codepicture.core.types import DisplayLine; d = DisplayLine(0, 0, 1, 0, False); print(d)"` works.
Run existing tests: `cd /Users/bartel/Documents/newclone/codepicture && python -m pytest tests/test_layout.py -x -q` -- all pass (no regression).
  </verify>
  <done>RenderConfig accepts window_width/window_height. LayoutEngine produces display_lines when window_width is set. Existing tests pass unchanged.</done>
</task>

<task type="auto">
  <name>Task 2: Update Renderer to handle display_lines and add CLI flags</name>
  <files>
    src/codepicture/render/renderer.py
    src/codepicture/cli/app.py
  </files>
  <action>
**render/renderer.py** - Update the `render` method to handle word-wrapped display lines:

After the existing code, add a branching path. If `metrics.display_lines` is non-empty, use the new path. Otherwise use legacy path (existing code, untouched).

**New rendering path (when display_lines is present):**

1. **Line numbers:** Iterate over display_lines. For each display_line where `is_continuation is False`, draw the line number (using `source_line_idx + config.line_number_offset`). For continuations, skip (no line number drawn).

2. **Code tokens:** For each display_line in metrics.display_lines:
   - Calculate baseline_y using the display_line's index (0-based position in display_lines), NOT source_line_idx.
   - Get the source line's tokens: `line_tokens = lines[display_line.source_line_idx]`
   - Determine x_start: if `is_continuation`, start at `metrics.code_x + metrics.wrap_indent_chars * metrics.char_width`. Otherwise start at `metrics.code_x`.
   - Walk through tokens from token_start to token_end. For each token:
     - Compute the visible portion of the token text for this display line based on char_offset. The first token in a chunk may be partially visible (text starting from some offset within the token). The last token may also be partially visible.
     - Specifically: track a running `chars_seen` counter starting at 0. For each token, the token covers chars `[token_char_start, token_char_start + len(token.text))` relative to the source line. The display line covers chars `[display_line.char_offset, next_display_line.char_offset or end)`. Intersect to get the visible slice.
     - A simpler approach: reconstruct the full source line text from tokens, slice it for this display line's char range, then re-walk the tokens to emit styled spans. This avoids complex offset math.

   **Recommended simpler approach for token rendering per display line:**
   - For each source line, build a flat list of `(char_index, char, token_type)` by iterating tokens.
   - For each display line, slice this flat list from `char_offset` to the end of the chunk.
   - Group consecutive chars with same token_type into spans.
   - Render each span with the appropriate style.

3. Ensure the rendering path uses `len(metrics.display_lines)` for Y positioning, using enumerate index as the visual line number.

**cli/app.py** - Add two new CLI options to the `main` function:

```python
window_width: Annotated[
    int | None,
    typer.Option("--width", help="Window width in pixels (enables word wrap)")
] = None,
window_height: Annotated[
    int | None,
    typer.Option("--height", help="Window height in pixels")
] = None,
```

Add to cli_overrides dict:
```python
if window_width is not None:
    cli_overrides["window_width"] = window_width
if window_height is not None:
    cli_overrides["window_height"] = window_height
```

Place these options in the "Visual" section alongside padding and corner_radius.
  </action>
  <verify>
Test with a real file that has long lines:
```bash
cd /Users/bartel/Documents/newclone/codepicture
echo 'def very_long_function_name_that_will_definitely_need_wrapping(parameter_one, parameter_two, parameter_three, parameter_four, parameter_five):
    return parameter_one + parameter_two + parameter_three + parameter_four + parameter_five' > /tmp/test_wrap.py
python -m codepicture /tmp/test_wrap.py -o /tmp/test_wrap_no_width.png
python -m codepicture /tmp/test_wrap.py -o /tmp/test_wrap_with_width.png --width 500
python -m codepicture /tmp/test_wrap.py -o /tmp/test_wrap_with_both.png --width 500 --height 300
```
Verify all three commands succeed without errors.
Verify /tmp/test_wrap_with_width.png is 500px wide (approximately, accounting for HiDPI 2x).
Run `python -m pytest tests/ -x -q` to ensure no regressions.
  </verify>
  <done>Renderer correctly draws wrapped continuation lines with indent and no line number. CLI accepts --width and --height flags. All existing tests pass.</done>
</task>

<task type="auto">
  <name>Task 3: Add tests for word wrapping and width/height</name>
  <files>
    tests/test_word_wrap.py
    tests/test_layout.py
  </files>
  <action>
**tests/test_word_wrap.py** - Create new test file with these tests:

1. `test_window_width_none_produces_empty_display_lines` -- RenderConfig with default window_width=None, verify display_lines is empty tuple (backward compat).

2. `test_window_width_auto_sizes_without_wrap` -- When window_width is wide enough for all content, display_lines still maps 1:1 with source lines, none are continuations.

3. `test_window_width_wraps_long_line` -- Create a source line with 100 chars, set window_width such that max_code_chars is ~50. Verify display_lines has 2+ entries for that source line. First entry is_continuation=False, subsequent are True.

4. `test_continuation_lines_have_no_line_number_gap` -- Verify that when rendering, continuations don't get line numbers. (This can be a layout-level test checking display_line.is_continuation flags.)

5. `test_wrap_indent_chars_applied` -- Verify that continuation display lines have char capacity reduced by wrap_indent_chars (i.e., fewer chars fit on a continuation line due to indent).

6. `test_window_height_sets_canvas_height` -- Set window_height=400, verify metrics.canvas_height == 400.

7. `test_window_width_sets_canvas_width` -- Set window_width=600, verify metrics.canvas_width == 600.

8. `test_display_lines_count_affects_content_height` -- A long line that wraps into 3 display lines should produce taller content_height than the same line without wrapping (or with wider window_width).

Use the existing `pango_measurer` fixture from conftest.py. Create tokens inline using TokenInfo. Follow the patterns in test_layout.py.

**tests/test_layout.py** - Add one test:

9. `test_window_width_none_backward_compatible` -- Verify that setting window_width=None produces identical LayoutMetrics (canvas_width, canvas_height, code_x, etc.) as the existing behavior. This ensures the feature is purely additive.
  </action>
  <verify>
Run `cd /Users/bartel/Documents/newclone/codepicture && python -m pytest tests/test_word_wrap.py tests/test_layout.py -x -v` -- all tests pass.
Run full test suite: `python -m pytest tests/ -x -q` -- no regressions.
  </verify>
  <done>Comprehensive test coverage for word wrapping, width/height config, continuation line behavior, and backward compatibility.</done>
</task>

</tasks>

<verification>
1. `python -m pytest tests/ -x -q` -- full suite passes with no regressions
2. `python -m codepicture /tmp/test_wrap.py -o /tmp/out.png --width 500` -- produces valid image with wrapped lines
3. `python -m codepicture /tmp/test_wrap.py -o /tmp/out.png` -- auto-sizing still works identically to before
4. `python -m codepicture /tmp/test_wrap.py -o /tmp/out.png --width 500 --height 300` -- both dimensions honored
</verification>

<success_criteria>
- --width and --height CLI flags are accepted and validated (100-10000 range)
- Lines exceeding window width wrap with VSCode-style indent on continuations
- Continuation lines show NO line number in the gutter
- Default behavior (no --width/--height) is identical to current output
- All existing tests pass unchanged
- New tests cover wrapping, continuation logic, and backward compatibility
</success_criteria>

<output>
After completion, create `.planning/quick/004-add-window-width-height-and-word-wrap/004-SUMMARY.md`
</output>
