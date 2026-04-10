# Phase 14: Theme Integration & Documentation - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Highlight colors automatically adapt to the active theme for readable contrast, and all v2.0 highlighting features are documented with examples in the README. Theme-aware color derivation replaces the current hardcoded `DEFAULT_STYLE_COLORS` as the default when no user override is specified.

</domain>

<decisions>
## Implementation Decisions

### Theme-aware color derivation
- **D-01:** Luminance-based approach: detect if theme background is light or dark via luminance calculation. Use warm/vivid colors on dark themes, cooler/muted colors on light themes.
- **D-02:** Dark theme palette (luminance < threshold): bright green (#00CC4040), bright red (#FF333340), bright blue (#3399FF40), warm yellow (#FFE65040) — same as current defaults.
- **D-03:** Light theme palette (luminance >= threshold): darker green (#00882240), darker red (#CC000040), darker blue (#0066CC40), muted yellow (#B8960040).
- **D-04:** Luminance threshold value and alpha/opacity behavior across themes: Claude's discretion. Pick what produces the best visual result.

### User override behavior
- **D-05:** Full replace precedence chain: explicit user color wins entirely over theme-derived colors.
  1. Per-style TOML color (`[highlight_styles.add] color = "..."`) — highest priority
  2. Global `--highlight-color` CLI flag — applies to styles without TOML override
  3. Theme-derived color (auto, based on luminance) — default behavior
  4. Hardcoded `DEFAULT_STYLE_COLORS` — fallback if theme derivation fails
- **D-06:** Per-style TOML overrides take precedence over the global `--highlight-color` flag. TOML style colors are more intentional.

### Documentation structure
- **D-07:** New `## Line Highlighting` section in README after existing feature docs. Subsections: Quick Start, Highlight Styles, Configuration (TOML), Theme Integration.
- **D-08:** TOML config examples should be complete with inline comments — copy-paste ready. Show all highlight options including `[[highlights.entries]]` and `[highlight_styles.<name>]` sections.

### Visual example generation
- **D-09:** Auto-generate example images using codepicture itself. A script (e.g., `docs/generate-examples.sh`) runs codepicture commands to produce images. Images committed to `docs/examples/`.
- **D-10:** Showcase one dark theme (Catppuccin Mocha) and one light theme (GitHub Light), each showing all 4 highlight styles. Plus a focus mode example. ~3 images total in README.

### Testing strategy
- **D-11:** Parametric contrast check across all 55+ built-in themes. Test parametrized over `list_themes()`, verifying derived highlight colors have sufficient contrast against each theme's background.
- **D-12:** Two visual regression snapshots: one dark theme (Catppuccin Mocha) and one light theme (GitHub Light), each showing all 4 highlight styles. Same pixelmatch approach as Phase 12/13.

### Claude's Discretion
- Luminance threshold value (hardcoded vs configurable, exact cutoff)
- Alpha/opacity adjustment per theme (same alpha or adjusted)
- Exact color values for light theme palette within the specified family
- Contrast ratio threshold for parametric tests
- Example script format (shell script vs Makefile target)
- Demo code snippet content for example images

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — HLTHEM-01 through HLTHEM-03 (theme integration), HLDOC-01 through HLDOC-03 (documentation)

### Prior phase context
- `.planning/phases/12-core-highlighting-infrastructure/12-CONTEXT.md` — Phase 12 decisions on highlight appearance, default color/opacity, line range syntax
- `.planning/phases/13-named-styles-focus-mode-gutter-indicators/13-CONTEXT.md` — Phase 13 decisions on named styles, style color palette (D-12), focus mode dimming, gutter indicators, CLI flag design

### Existing implementation
- `src/codepicture/render/highlights.py` — `DEFAULT_STYLE_COLORS`, `HighlightStyle` enum, `resolve_style_color()`, `resolve_highlight_color()`. Theme derivation logic extends these.
- `src/codepicture/theme/pygments_theme.py` — `PygmentsTheme` class with `.background` property exposing theme background color. Entry point for luminance detection.
- `src/codepicture/theme/toml_theme.py` — `TomlTheme` class with `.background` property. Same interface as PygmentsTheme.
- `src/codepicture/theme/loader.py` — `get_theme()`, `list_themes()`, `BUILTIN_THEMES` dict. Used for parametric testing across all themes.
- `src/codepicture/render/renderer.py` — `style_colors` dict built in `render()`. Integration point where theme-derived colors replace hardcoded defaults.
- `src/codepicture/config/schema.py` — `RenderConfig` with `highlight_color` and `highlight_styles` fields. Override precedence chain terminates here.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PygmentsTheme.background` / `TomlTheme.background`: Already expose `Color` objects with RGB values — luminance calculation can use these directly.
- `resolve_style_color()` in `highlights.py`: Currently resolves user overrides against `DEFAULT_STYLE_COLORS`. Can be extended to accept theme-derived defaults.
- `Color.from_hex()` in `core/types.py`: Parses hex color strings — reusable for light palette constants.
- `list_themes()`: Returns all available theme names — drives parametric testing.

### Established Patterns
- `DEFAULT_STYLE_COLORS` dict maps `HighlightStyle` -> `Color`. Theme-derived colors follow the same shape.
- `Renderer.render()` builds `style_colors` dict before entering render paths. Theme derivation slots in here.
- Visual regression tests use pixelmatch with threshold-based comparison in `tests/snapshots/`.

### Integration Points
- `Renderer.render()` method: currently builds `style_colors` from `DEFAULT_STYLE_COLORS` + user overrides. Must be extended to: (1) get theme background, (2) derive theme palette, (3) apply user overrides on top.
- `README.md`: 308 lines, no highlight docs yet. New section added after existing content.

</code_context>

<specifics>
## Specific Ideas

No specific references — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 14-theme-integration-documentation*
*Context gathered: 2026-04-01*
