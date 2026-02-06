# Requirements: codepicture v2.0

**Defined:** 2026-02-02
**Core Value:** One command turns code into a slide-ready image

## v2.0 Requirements

Requirements for the Line Highlighting milestone. Each maps to roadmap phases.

### Core Highlighting

- [x] **HLCORE-01**: User can highlight specific lines via `--highlight-lines '1,3-5,7'` CLI flag
- [x] **HLCORE-02**: User can specify line ranges with comma-separated syntax (individual lines and inclusive ranges)
- [x] **HLCORE-03**: Highlighted lines display a semi-transparent colored background overlay spanning the full content width
- [x] **HLCORE-04**: User can customize highlight color via `--highlight-color '#RRGGBBAA'` flag
- [x] **HLCORE-05**: Line highlighting works across all output formats (PNG, SVG, PDF)
- [x] **HLCORE-06**: Highlight settings are configurable via TOML config file
- [x] **HLCORE-07**: Highlighted word-wrapped lines highlight ALL display lines for the source line

### Named Styles

- [ ] **HLSTYL-01**: User can specify named highlight styles via `--highlight '3-5:add'` repeated flag syntax
- [ ] **HLSTYL-02**: Built-in styles: `highlight` (default), `add` (green), `remove` (red), `focus` (yellow/blue)
- [ ] **HLSTYL-03**: Each built-in style has a distinct default color
- [ ] **HLSTYL-04**: User can customize style colors via TOML config (`[highlight_styles.add] color = "#RRGGBBAA"`)
- [ ] **HLSTYL-05**: When no style specified (`--highlight '3-5'`), uses default `highlight` style

### Focus Mode

- [ ] **HLFOC-01**: When `focus` style is used, all non-focused lines are dimmed (reduced opacity)
- [ ] **HLFOC-02**: Focused lines remain at full brightness/opacity
- [ ] **HLFOC-03**: Focus dimming level is visually effective without making unfocused lines unreadable

### Theme Integration

- [ ] **HLTHEM-01**: Default highlight colors are derived from the active theme's background color
- [ ] **HLTHEM-02**: Theme-aware colors maintain readable contrast for syntax tokens on highlighted lines
- [ ] **HLTHEM-03**: User-specified `--highlight-color` and TOML style colors override theme-derived defaults

### Gutter Indicators

- [ ] **HLGUT-01**: Named styles display gutter indicators beside line numbers (`+` for add, `-` for remove, colored bar for focus/highlight)
- [ ] **HLGUT-02**: Gutter indicators use the same color as the corresponding highlight style

### Documentation

- [ ] **HLDOC-01**: README documents all highlight CLI flags with usage examples
- [ ] **HLDOC-02**: README documents TOML config options for highlight styles and colors
- [ ] **HLDOC-03**: README includes visual examples showing highlight styles (add/remove/focus)

### Testing

- [x] **HLTEST-01**: Unit tests for line range parser (individual lines, ranges, mixed, edge cases)
- [ ] **HLTEST-02**: Unit tests for highlight resolution (style-to-color mapping, custom overrides, defaults)
- [x] **HLTEST-03**: Visual regression tests for highlighted output across all 3 formats (PNG, SVG, PDF)
- [ ] **HLTEST-04**: Visual regression tests for each named style (add, remove, focus, highlight)
- [x] **HLTEST-05**: Integration tests for word-wrapped highlighted lines
- [ ] **HLTEST-06**: Integration tests for focus mode dimming
- [x] **HLTEST-07**: Tests for CLI flag parsing and TOML config loading of highlight options
- [ ] **HLTEST-08**: Tests for gutter indicators with named styles

## Future Requirements

Deferred to post-v2.0. Tracked but not in current roadmap.

### Inline Annotations

- **HLANN-01**: User can mark highlights via inline source comments (`// [highlight]`, `# [add]`)
- **HLANN-02**: Annotation comments are stripped from rendered output

### Advanced Features

- **HLADV-01**: Word-level highlighting within a line
- **HLADV-02**: Diff-based automatic highlighting from unified diff input

## Out of Scope

| Feature | Reason |
|---------|--------|
| Step-through animation syntax | codepicture produces static images, not presentations |
| Blur/grayscale effects for unfocused lines | Opacity reduction is sufficient and consistent across formats |
| Color picker / theme builder | CLI tool — hex values are sufficient |
| Overlapping styles on same line (blending) | Last style wins — simpler and more predictable |
| Inline source annotations | Different input paradigm, deferred to v2.1 |
| Word-level highlighting | Different feature category, separate milestone |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| HLCORE-01 | Phase 12 | Complete |
| HLCORE-02 | Phase 12 | Complete |
| HLCORE-03 | Phase 12 | Complete |
| HLCORE-04 | Phase 12 | Complete |
| HLCORE-05 | Phase 12 | Complete |
| HLCORE-06 | Phase 12 | Complete |
| HLCORE-07 | Phase 12 | Complete |
| HLSTYL-01 | Phase 13 | Pending |
| HLSTYL-02 | Phase 13 | Pending |
| HLSTYL-03 | Phase 13 | Pending |
| HLSTYL-04 | Phase 13 | Pending |
| HLSTYL-05 | Phase 13 | Pending |
| HLFOC-01 | Phase 13 | Pending |
| HLFOC-02 | Phase 13 | Pending |
| HLFOC-03 | Phase 13 | Pending |
| HLTHEM-01 | Phase 14 | Pending |
| HLTHEM-02 | Phase 14 | Pending |
| HLTHEM-03 | Phase 14 | Pending |
| HLGUT-01 | Phase 13 | Pending |
| HLGUT-02 | Phase 13 | Pending |
| HLDOC-01 | Phase 14 | Pending |
| HLDOC-02 | Phase 14 | Pending |
| HLDOC-03 | Phase 14 | Pending |
| HLTEST-01 | Phase 12 | Complete |
| HLTEST-02 | Phase 13 | Pending |
| HLTEST-03 | Phase 12 | Complete |
| HLTEST-04 | Phase 13 | Pending |
| HLTEST-05 | Phase 12 | Complete |
| HLTEST-06 | Phase 13 | Pending |
| HLTEST-07 | Phase 12 | Complete |
| HLTEST-08 | Phase 13 | Pending |

**Coverage:**
- v2.0 requirements: 31 total
- Mapped to phases: 31
- Unmapped: 0

---
*Requirements defined: 2026-02-02*
*Last updated: 2026-02-06 after Phase 12 completion*
