---
quick_id: "014"
slug: focus-mode-clean-no-blue-overlay
description: Refactor focus mode to remove blue overlay/bar; FOCUS becomes a dim-only marker
date: 2026-05-07
---

# Quick Task 014: Focus mode — remove blue overlay, dim-only marker

## Problem

The user noticed that focus mode currently draws a blue rectangle over the
focused line plus a blue gutter bar (the "blue par[t]"). They want focus
mode to mean only "dim everything else" — focused lines render normally
with no special background or gutter indicator.

The codebase already contains a partial in-progress hack on
`src/codepicture/render/renderer.py` (uncommitted) that:

1. Adds `if hl_style == HighlightStyle.FOCUS: continue` mid-loop in two places.
2. Deletes the entire "colored bar for highlight/focus" else-branch — which
   inadvertently removes the colored gutter bar for HIGHLIGHT too, not just
   FOCUS. This is a regression for HIGHLIGHT-styled lines.

The hack also leaves dead palette entries (`DEFAULT_STYLE_COLORS[FOCUS]`,
theme dicts, `GUTTER_INDICATORS[FOCUS]`) and a config option
(`[highlight_styles.focus]`) that resolve to a color that is never drawn.

## Goal

Reshape FOCUS into a marker style:

- It triggers `focus_mode` (already does).
- It identifies lines that should NOT be dimmed.
- It draws no rectangle and no gutter indicator.
- Configuring its color is rejected at config validation (no longer meaningful).

Keep HIGHLIGHT/ADD/REMOVE behaviour intact: HIGHLIGHT keeps its yellow rect
and yellow gutter bar; ADD/REMOVE keep their bg + `+`/`-` gutter symbols.

## Tasks

### Task 1 — Refactor renderer.py

- Revert the in-progress hack on `src/codepicture/render/renderer.py`.
- In `Renderer.render()`, after building `style_map`, build:
  - `decoration_map: dict[int, HighlightStyle]` — entries from `style_map`
    excluding any with style `FOCUS`. Used for drawing rectangles and gutter
    indicators.
  - `dim_lines: set[int]` — when `focus_mode` is true, the set of source-line
    indices that should be rendered dimmed (i.e. lines NOT in `style_map`).
    Empty when focus mode is off.
- Resolve `style_colors` and `indicator_colors` only over
  `set(decoration_map.values())` so FOCUS never appears as a key (this also
  means no resolve_style_color call for FOCUS, which avoids needing
  DEFAULT_STYLE_COLORS[FOCUS]).
- Replace `style_map` and `focus_mode` parameters on `_render_legacy` /
  `_render_wrapped` with `decoration_map` and `dim_lines`.
  - All `if focus_mode and line_idx not in style_map` checks become
    `if line_idx in dim_lines`.
  - All `if line_idx in style_map` (or `dline.source_line_idx in style_map`)
    checks for visual decoration become `... in decoration_map`.
- Restore the colored-bar branch that draws a gutter bar for HIGHLIGHT
  (the user's diff dropped this). FOCUS no longer reaches this code because
  it's filtered out at the orchestration level.

### Task 2 — Clean up highlights.py palette

- Remove the `HighlightStyle.FOCUS` entry from:
  - `DEFAULT_STYLE_COLORS`
  - `DARK_THEME_COLORS`
  - `LIGHT_THEME_COLORS`
  - `GUTTER_INDICATORS`
- Update the `HighlightStyle.FOCUS` enum docstring (or surrounding comment)
  to clarify FOCUS is a dim-only marker — it triggers focus mode but is
  never drawn.
- Keep `FOCUS_DIM_OPACITY` and the `FOCUS` enum member (still used).

### Task 3 — Reject focus in highlight_styles config

In `src/codepicture/config/schema.py`, remove `"focus"` from the
`valid_names` set inside `validate_highlight_styles`. Update the error
message naturally (since the set is sorted in the message, no extra wording
needed). Add a single short comment near the validator noting that FOCUS is
a dim-only marker so per-style color overrides do not apply.

### Task 4 — Update unit tests

In `tests/test_highlights.py`:

- `TestDefaultStyleColors.test_focus_color` — delete (FOCUS no longer in
  `DEFAULT_STYLE_COLORS`).
- `TestLightThemeColors.test_focus_color` — delete (FOCUS no longer in
  `LIGHT_THEME_COLORS`).
- `TestGutterIndicators.test_focus_shows_bar` — delete (FOCUS no longer
  in `GUTTER_INDICATORS`); rename leftover `test_highlight_shows_bar` if its
  meaning shifts (HIGHLIGHT still has `None`, still drawn as a colored bar
  in the renderer — meaning unchanged).
- `tests/test_highlights_integration.py` — review; current focus tests
  assert "produces non-empty output" and that mixing focus + add still
  works. They should still pass (focus still parses, FOCUS still in
  `style_map`, just no rectangle drawn). No code changes expected.

If any config-schema test asserted that `[highlight_styles.focus]` was
accepted, flip it to assert it now raises a validation error.

### Task 5 — Update README

In `README.md`:

- Line 222 row of the styles table — replace
  `Blue background; all other lines are dimmed`
  with `All other lines are dimmed (no background or gutter mark)`.
- Lines 261–263 — delete the `[highlight_styles.focus]` example block; FOCUS
  no longer accepts a configurable color.
- Line 251 — keep the `"15-20:focus"` example in the highlights list (still
  valid).
- Line 241–243 — keep the focus mode example image reference; the rendered
  example image gets regenerated.

### Task 6 — Update visual snapshots and example images

These rendered references all encode the now-removed blue overlay and need
to be regenerated:

- `tests/visual/references/python_png_highlight-style-focus.png`
  (single line in focus mode)
- `tests/visual/references/python_png_highlight-style-mixed.png`
  (`["1:add", "3:remove", "5:focus"]`)
- `tests/visual/references/python_png_gutter-indicators-visible.png`
  (`["1:add", "2:remove", "3:focus", "4:highlight"]`)
- `tests/visual/references/highlight_dark_catppuccin_mocha.png` — check
  whether it includes a focus line; regenerate if so.
- `tests/visual/references/highlight_light_catppuccin_latte.png` — same.
- `docs/examples/highlight-focus.png` (regenerate via
  `docs/generate-examples.sh` or pytest snapshot update).
- `docs/examples/highlight-dark.png` — regenerate if the source command in
  `docs/generate-examples.sh` includes a focus directive (it does, line 18
  / 27).

Approach: run pytest with `--snapshot-update` for the visual regression
tests, then regenerate the example images via `docs/generate-examples.sh`.
Spot-check at least the focus reference visually before committing — the
focused line should look identical to a normal (non-dimmed) line; non-focus
lines should be dim.

## Done when

- `git diff src/codepicture/render/renderer.py` no longer contains the
  `if hl_style == HighlightStyle.FOCUS: continue` early-returns or the
  dropped colored-bar branch.
- HIGHLIGHT-style lines still render with their colored gutter bar.
- FOCUS-styled lines render with no rectangle and no gutter mark.
- `[highlight_styles.focus]` in TOML raises a config validation error.
- Affected unit tests pass; visual regression tests pass against
  regenerated baselines.
- README's style table and TOML example reflect the new behaviour.
