# Requirements: codepicture

**Defined:** 2026-01-28
**Core Value:** One command turns code into a slide-ready image

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core

- [ ] **CORE-01**: CLI accepts source file path and outputs image to specified path
- [ ] **CORE-02**: TOML config file support (~/.config/codepicture/config.toml)
- [ ] **CORE-03**: CLI flags override config file settings

### Output Formats

- [ ] **OUT-01**: PNG output format
- [ ] **OUT-02**: SVG output format
- [ ] **OUT-03**: PDF output format

### Syntax Highlighting

- [ ] **HIGH-01**: Syntax highlighting via Pygments tokenization
- [ ] **HIGH-02**: Auto-detect language from file extension
- [ ] **HIGH-03**: Explicit language override via --language flag
- [ ] **HIGH-04**: Custom lexer support for domain-specific languages (MLIR via Sublime syntax)

### Theming

- [ ] **THEME-01**: Catppuccin theme support
- [ ] **THEME-02**: Built-in Pygments themes (Dracula, Monokai, One Dark, etc.)

### Visual Styling

- [ ] **VIS-01**: macOS-style window controls (red/yellow/green traffic lights)
- [ ] **VIS-02**: Drop shadow effect with configurable blur/offset
- [ ] **VIS-03**: Line numbers in gutter
- [ ] **VIS-04**: Configurable padding around code
- [ ] **VIS-05**: Configurable corner radius
- [ ] **VIS-06**: Configurable background color

### Typography

- [ ] **TYPO-01**: Configurable font family
- [ ] **TYPO-02**: Configurable font size
- [ ] **TYPO-03**: Configurable line height
- [ ] **TYPO-04**: Tab-to-space normalization

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Visual Enhancements

- **VIS-07**: Line highlighting (highlight specific lines with different background)
- **VIS-08**: Gradient backgrounds

### I/O

- **IO-01**: Clipboard input (read code from clipboard)
- **IO-02**: Clipboard output (copy image to clipboard)

### Typography

- **TYPO-05**: Font ligatures support

### Interface

- **UI-01**: Local web UI for interactive preview

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Windows support | macOS and Linux only for v1; can add later if demand |
| Real-time preview | Batch processing only; web UI is future |
| Animations / GIFs | Static images only; different tool category |
| Cloud accounts / web service | CLI-first; no infrastructure complexity |
| Image watermarks | Not needed for presentation use case |
| Automatic code formatting | Out of scope; user provides formatted code |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | Phase 5 | Pending |
| CORE-02 | Phase 1 | Complete |
| CORE-03 | Phase 5 | Pending |
| OUT-01 | Phase 4 | Pending |
| OUT-02 | Phase 4 | Pending |
| OUT-03 | Phase 4 | Pending |
| HIGH-01 | Phase 2 | Complete |
| HIGH-02 | Phase 2 | Complete |
| HIGH-03 | Phase 2 | Complete |
| HIGH-04 | Phase 6 | Pending |
| THEME-01 | Phase 2 | Complete |
| THEME-02 | Phase 2 | Complete |
| VIS-01 | Phase 4 | Pending |
| VIS-02 | Phase 4 | Pending |
| VIS-03 | Phase 4 | Pending |
| VIS-04 | Phase 4 | Pending |
| VIS-05 | Phase 4 | Pending |
| VIS-06 | Phase 4 | Pending |
| TYPO-01 | Phase 3 | Pending |
| TYPO-02 | Phase 3 | Pending |
| TYPO-03 | Phase 3 | Pending |
| TYPO-04 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0

---
*Requirements defined: 2026-01-28*
*Last updated: 2026-01-28 after roadmap creation*
