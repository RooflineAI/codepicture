# Phase 14: Theme Integration & Documentation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-01
**Phase:** 14-theme-integration-documentation
**Areas discussed:** Theme-aware color derivation, User override behavior, Documentation structure, Visual example generation, Testing

---

## Theme-aware color derivation

### Q1: How should highlight colors adapt to the active theme?

| Option | Description | Selected |
|--------|-------------|----------|
| Luminance-based inversion | Detect light/dark via luminance, use vivid on dark, muted on light | ✓ |
| Complementary color shift | Derive by shifting hue/saturation relative to bg | |
| Two fixed palettes (light/dark) | Exactly two color sets, switch on luminance | |

**User's choice:** Luminance-based inversion
**Notes:** None

### Q2: Where should the luminance threshold live?

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded 0.5 threshold | Simple luminance midpoint | |
| Configurable threshold | Allow tuning via TOML | |
| You decide | Claude picks | ✓ |

**User's choice:** You decide
**Notes:** None

### Q3: Should alpha/opacity adjust based on theme?

| Option | Description | Selected |
|--------|-------------|----------|
| Same alpha across themes | Keep ~25% for all themes | |
| Adjust alpha per theme | Light themes may need higher opacity | |
| You decide | Claude picks based on visual testing | ✓ |

**User's choice:** You decide
**Notes:** None

---

## User override behavior

### Q1: Explicit color vs theme-derived — replace or blend?

| Option | Description | Selected |
|--------|-------------|----------|
| Full replace | User color wins entirely, theme only when no explicit color | ✓ |
| Partial override | User RGB but alpha influenced by theme | |
| You decide | Claude picks | |

**User's choice:** Full replace
**Notes:** None

### Q2: Per-style TOML vs global --highlight-color precedence?

| Option | Description | Selected |
|--------|-------------|----------|
| Per-style TOML > global flag | TOML style colors are more intentional | ✓ |
| Global flag > TOML styles | CLI always overrides config file | |
| You decide | Claude picks | |

**User's choice:** Per-style TOML > global flag
**Notes:** None

---

## Documentation structure

### Q1: How should highlight docs be organized in README?

| Option | Description | Selected |
|--------|-------------|----------|
| New section after features | ## Line Highlighting with subsections | ✓ |
| Inline with existing CLI docs | Weave into existing reference | |
| Separate HIGHLIGHTING.md | Standalone doc linked from README | |

**User's choice:** New section after features
**Notes:** None

### Q2: How detailed should TOML config examples be?

| Option | Description | Selected |
|--------|-------------|----------|
| Complete example with comments | Full copy-paste TOML with inline comments | ✓ |
| Minimal examples | Essential fields only | |
| You decide | Claude picks | |

**User's choice:** Complete example with comments
**Notes:** None

---

## Visual example generation

### Q1: How should visual examples be produced?

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-generated via codepicture | Script generates images from code snippets | ✓ |
| Manually curated screenshots | Screenshots, more control but hard to maintain | |
| You decide | Claude picks | |

**User's choice:** Auto-generated via codepicture
**Notes:** None

### Q2: Which styles/themes to showcase?

| Option | Description | Selected |
|--------|-------------|----------|
| One dark + one light theme | Catppuccin Mocha + GitHub Light, all 4 styles + focus | ✓ |
| Dark theme only | Default dark only | |
| Comprehensive gallery | 4-5 themes with all styles | |

**User's choice:** One dark + one light theme
**Notes:** ~3 images total: dark styles, light styles, focus mode

---

## Testing

### Q1: How to test theme-aware colors across 55+ themes?

| Option | Description | Selected |
|--------|-------------|----------|
| Parametric contrast check | Parametrize across all themes, assert contrast ratio | ✓ |
| Visual regression per theme | Snapshot per theme via pixelmatch | |
| Spot-check 5-6 themes | Representative sample only | |

**User's choice:** Parametric contrast check
**Notes:** None

### Q2: Additional visual regression snapshots?

| Option | Description | Selected |
|--------|-------------|----------|
| 2 snapshots: dark + light | Catppuccin Mocha + GitHub Light, all 4 styles each | ✓ |
| No extra snapshots | Rely on parametric tests only | |
| You decide | Claude picks | |

**User's choice:** 2 snapshots: dark + light
**Notes:** Same pixelmatch approach as Phase 12/13

---

## Claude's Discretion

- Luminance threshold value and implementation
- Alpha/opacity behavior across themes
- Exact light palette color values
- Contrast ratio threshold for parametric tests
- Example script format
- Demo code snippet content

## Deferred Ideas

None — discussion stayed within phase scope
