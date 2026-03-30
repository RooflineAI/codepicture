# Phase 13: Named Styles, Focus Mode & Gutter Indicators - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 13-named-styles-focus-mode-gutter-indicators
**Areas discussed:** CLI flag design, Focus mode dimming, Gutter indicators, Style color palette, Testing

---

## CLI Flag Design

### --highlight vs --highlight-lines

| Option | Description | Selected |
|--------|-------------|----------|
| Replace it | --highlight replaces --highlight-lines. Old flag removed. --highlight '3-5' uses default 'highlight' style. | ✓ |
| Keep both | --highlight-lines stays for simple use. --highlight adds named-style support. Can't mix. | |
| Deprecate gracefully | --highlight-lines prints deprecation warning. Removed later. | |

**User's choice:** Replace it
**Notes:** Clean break preferred over gradual deprecation.

### --highlight-color disposition

| Option | Description | Selected |
|--------|-------------|----------|
| Keep as global default | --highlight-color sets color for default 'highlight' style. Named styles use own defaults. | |
| Remove it | All color customization moves to TOML. | |
| You decide | Claude picks cleanest approach. | ✓ |

**User's choice:** You decide
**Notes:** Claude has discretion on whether to keep or remove this flag.

### Overlapping styles

| Option | Description | Selected |
|--------|-------------|----------|
| Last style wins | Last --highlight flag wins for overlapping lines. | ✓ |
| Error on conflict | Reject overlapping combinations. | |
| You decide | Claude picks. | |

**User's choice:** Last style wins
**Notes:** Matches REQUIREMENTS.md rule.

### TOML config format

| Option | Description | Selected |
|--------|-------------|----------|
| Inline list syntax | [[highlights.entries]] array-of-tables with [highlight_styles.add] for color overrides. | ✓ |
| Style-keyed sections | Group lines under each style name. | |
| You decide | Claude picks. | |

**User's choice:** Inline list syntax
**Notes:** Selected after previewing both formats.

### Custom style names

| Option | Description | Selected |
|--------|-------------|----------|
| Built-ins only | Only highlight, add, remove, focus. Customize colors via TOML. | ✓ |
| Allow custom names | Any style name works if defined in TOML. | |
| You decide | Claude picks. | |

**User's choice:** Built-ins only
**Notes:** Keeps the system simple.

---

## Focus Mode Dimming

### Dimming method

| Option | Description | Selected |
|--------|-------------|----------|
| Reduced text opacity | ~30-40% opacity. Preserves syntax colors as muted. Works across formats. | ✓ |
| Semi-transparent overlay | Background-colored rectangle over unfocused lines. | |
| Desaturated text | Single muted gray for unfocused lines. | |

**User's choice:** Reduced text opacity
**Notes:** None.

### Dimming scope

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, dim everything | Line numbers, text, gutter indicators all dimmed. | ✓ |
| Text only | Only code text dimmed. Line numbers stay full opacity. | |
| You decide | Claude picks. | |

**User's choice:** Yes, dim everything
**Notes:** Creates a strong visual corridor toward focused lines.

### Focus + other styles

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, combine freely | Focus dims unfocused, but add/remove lines stay full brightness. | ✓ |
| Focus is exclusive | Only focus-styled lines highlighted when focus is used. | |
| You decide | Claude picks. | |

**User's choice:** Yes, combine freely
**Notes:** None.

---

## Gutter Indicators

### Position

| Option | Description | Selected |
|--------|-------------|----------|
| Between line numbers and code | Narrow column between gutter and code text. | ✓ |
| Left of line numbers | Leftmost element. | |
| You decide | Claude picks. | |

**User's choice:** Between line numbers and code
**Notes:** Selected after previewing both layouts.

### Bar style for highlight/focus

| Option | Description | Selected |
|--------|-------------|----------|
| Thin colored bar | 2-3px vertical bar in style's color. | ✓ |
| Colored dot | Small filled circle. | |
| No indicator | Only add/remove get indicators. | |

**User's choice:** Thin colored bar
**Notes:** Selected after previewing both options.

### Visibility without line numbers

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, still show indicators | Gutter column appears even without line numbers. | |
| No, hide with line numbers | Whole gutter hidden when line numbers off. | |
| You decide | Claude picks. | ✓ |

**User's choice:** You decide
**Notes:** Claude has discretion.

---

## Style Color Palette

### Palette feel

| Option | Description | Selected |
|--------|-------------|----------|
| Vivid & distinct | Bold saturated colors at ~25% opacity. Maximum differentiation. | ✓ |
| Muted & cohesive | Softer desaturated colors. Less jarring but harder to distinguish. | |
| You decide | Claude picks for best cross-theme results. | |

**User's choice:** Vivid & distinct
**Notes:** Selected specific hex values: add #00CC4040, remove #FF333340, focus #3399FF40, highlight #FFE65040.

### Gutter indicator opacity

| Option | Description | Selected |
|--------|-------------|----------|
| Full opacity version | ~80-100% opacity for gutter symbols. | ✓ |
| Same as highlight | Same semi-transparent color as background. | |
| You decide | Claude picks. | |

**User's choice:** Full opacity version
**Notes:** Small elements need clear visibility.

---

## Testing

### Visual regression approach

| Option | Description | Selected |
|--------|-------------|----------|
| One snapshot per style | 4 baseline images, one per style. Same pixelmatch approach. | ✓ |
| Combo snapshot | Single image with all styles. | |
| Both | Individual + combo. | |

**User's choice:** One snapshot per style
**Notes:** None.

### Focus mode dimming verification

| Option | Description | Selected |
|--------|-------------|----------|
| Visual regression only | Snapshot baseline of focused vs unfocused. | |
| Visual + unit test | Snapshot PLUS unit test verifying opacity value passed to canvas. | ✓ |
| You decide | Claude picks. | |

**User's choice:** Visual + unit test
**Notes:** Belt-and-suspenders approach for dimming correctness.

---

## Claude's Discretion

- --highlight-color flag disposition (keep or remove)
- Gutter indicator visibility when line numbers disabled
- Exact dimming opacity within ~30-40%
- Exact gutter bar width within 2-3px
- TOML config field naming details
- Migration of existing highlight_lines/highlight_color config fields

## Deferred Ideas

None — discussion stayed within phase scope
