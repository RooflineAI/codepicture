---
quick_id: "014"
slug: focus-mode-clean-no-blue-overlay
status: complete
date: 2026-05-07
---

# Quick Task 014 — Summary

## What changed

Replaced the in-progress hack on focus mode with a clean refactor. FOCUS
is now formally a dim-only marker — it triggers focus mode and exempts
its lines from dimming, but draws no rectangle and no gutter indicator.

### `src/codepicture/render/renderer.py`

- Removed the `if hl_style == HighlightStyle.FOCUS: continue` early-returns
  from both `_render_legacy` and `_render_wrapped`.
- In `Renderer.render()`, split `style_map` into:
  - `decoration_map` — drawing-only entries (FOCUS filtered out).
  - `dim_lines: set[int]` — source-line indices to render dimmed (only
    populated when focus mode is active).
- Helper signatures now take `decoration_map` and `dim_lines` instead of
  `style_map` and `focus_mode`. All `if focus_mode and X not in style_map`
  checks collapse to `if X in dim_lines`.
- Restored the colored-bar `else` branch for HIGHLIGHT-style gutter marks
  (the user's hack had deleted it). HIGHLIGHT lines get their yellow gutter
  bar back; FOCUS lines reach the gutter loop only via filtered-out paths.

### `src/codepicture/render/highlights.py`

- Removed `HighlightStyle.FOCUS` from `DEFAULT_STYLE_COLORS`,
  `DARK_THEME_COLORS`, `LIGHT_THEME_COLORS`, and `GUTTER_INDICATORS`. These
  entries were dead code after the refactor (resolve_style_color is no
  longer called for FOCUS).
- Added a docstring on `HighlightStyle` clarifying decoration vs. marker
  semantics.

### `src/codepicture/config/schema.py`

- Removed `"focus"` from `valid_names` in `validate_highlight_styles`.
  Setting `[highlight_styles.focus]` in TOML now raises a config validation
  error with the message
  `Unknown style 'focus'. Valid styles: add, highlight, remove`.

### Tests

- `tests/test_highlights.py` — replaced the deleted-palette assertions
  (`test_focus_color`, `test_focus_shows_bar`) with `not in`-style guard
  tests that lock the marker contract. Updated
  `test_default_color_for_each_style` (now `_decoration_style`) to skip
  FOCUS. Updated `test_dark_palette_matches_default_style_colors` to
  compare dicts directly instead of iterating the enum.
- `tests/theme/test_contrast.py` — the parametric overlay-visibility test
  iterates `HighlightStyle`; added a `continue` for FOCUS (no overlay to
  test).

### Documentation

- `README.md`:
  - Style table row for `focus` no longer mentions a blue background.
  - Removed the `[highlight_styles.focus]` TOML example; added a note that
    FOCUS does not accept a color override.

### Visual baselines regenerated

All include focus highlights:

- `tests/visual/references/python_png_highlight-style-focus.png`
- `tests/visual/references/python_png_highlight-style-mixed.png`
- `tests/visual/references/python_png_gutter-indicators-visible.png`
- `tests/visual/references/highlight_dark_catppuccin_mocha.png`
- `tests/visual/references/highlight_light_catppuccin_latte.png`

Plus the README example images (`docs/examples/highlight-dark.png`,
`docs/examples/highlight-light.png`, `docs/examples/highlight-focus.png`)
regenerated via `bash docs/generate-examples.sh`.

## Verification

- `uv run pytest -q --no-header` — 572 passed, 51 skipped.
- Visually confirmed `python_png_highlight-style-focus.png`: line 2 (focus)
  has no blue rectangle, no blue bar; non-focus lines are dimmed.
- Visually confirmed `python_png_gutter-indicators-visible.png`: HIGHLIGHT
  line still draws its yellow gutter bar (regression from the hack is
  fixed); FOCUS line is invisible aside from staying full-opacity.

## Notes for future work

- FOCUS is a marker style only. If the project ever wants a "focus
  background" again, it should be a separate style (e.g. `emphasis`) so
  the marker semantics stay clean.
- `resolve_style_color` will now raise `KeyError` if called with
  `HighlightStyle.FOCUS`. The renderer never does this, but it's worth
  asserting in the function if a future caller is introduced.
