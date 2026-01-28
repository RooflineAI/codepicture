---
phase: 02-syntax-highlighting
plan: 02
subsystem: theme
tags: [pygments, catppuccin, toml, theme-system]
dependency-graph:
  requires:
    - 01-01: Color and TextStyle types
    - 01-02: Theme protocol definition
  provides:
    - PygmentsTheme: Theme implementation wrapping Pygments styles
    - TomlTheme: Custom TOML theme with inheritance
    - get_theme(): Theme loading by name or file
    - list_themes(): Theme discovery
  affects:
    - 02-03: Integration will use get_theme() for token colorization
    - config: Config system may use get_theme() for theme setting
tech-stack:
  added:
    - pygments>=2.19 (tokenization and built-in styles)
    - catppuccin[pygments]>=2.5 (Catppuccin color palettes)
  patterns:
    - Wrapper pattern: PygmentsTheme wraps Pygments Style
    - Inheritance: TomlTheme extends base themes via 'extends' key
    - Token inheritance: Walk parent chain before base fallback
key-files:
  created:
    - src/codepicture/theme/__init__.py
    - src/codepicture/theme/pygments_theme.py
    - src/codepicture/theme/toml_theme.py
    - src/codepicture/theme/loader.py
  modified:
    - src/codepicture/__init__.py
    - pyproject.toml (dependencies added in 02-01)
decisions:
  - PygmentsTheme uses slots for memory efficiency
  - Line number colors derived from foreground/background (not explicit in Pygments)
  - Token type inheritance walks parent chain in theme before base theme
  - Default theme is catppuccin-mocha per CONTEXT.md
  - Theme aliases support (catppuccin -> catppuccin-mocha, onedark -> one-dark)
metrics:
  duration: 3 min
  completed: 2026-01-28
---

# Phase 02 Plan 02: Theme System Summary

Pygments style wrapping and TOML theme loading with inheritance for flexible token colorization.

## What Was Built

### PygmentsTheme (pygments_theme.py)
Implements Theme protocol by wrapping Pygments Style classes:
- Extracts background, foreground from style class attributes
- Uses `style_for_token()` for token-specific colors with inheritance
- Derives line number colors from main colors (muted foreground, darker background)
- Handles None colors by falling back to foreground (RESEARCH.md Pitfall 5)

### TomlTheme (toml_theme.py)
Custom theme definition via TOML files:
- Supports `extends = "theme-name"` for inheritance
- `[colors]` section for background, foreground, line numbers
- `[tokens]` section for per-token styles (color, bold, italic, underline)
- Token name parsing: "Keyword" or "Token.Keyword.Constant" both work

### Theme Loader (loader.py)
Discovery and loading functions:
- `get_theme(name, custom_path)`: Load by name or TOML file
- `list_themes()`: Returns all available themes (Pygments + Catppuccin + aliases)
- `ThemeError` with helpful message listing available options

## Key Implementation Details

```python
# PygmentsTheme wraps Pygments styles
theme = PygmentsTheme('monokai')
style = theme.get_style(Keyword)  # Returns TextStyle with color, bold, etc.

# get_theme() for simple loading
theme = get_theme('catppuccin-mocha')

# TOML themes can extend built-in themes
# my-theme.toml:
# extends = "catppuccin-mocha"
# [tokens]
# Keyword = { color = "#ff79c6", bold = true }
```

## Available Themes

Built-in themes include:
- Catppuccin: mocha, macchiato, frappe, latte
- Classic: dracula, monokai, one-dark
- All Pygments styles: solarized-dark, github-dark, gruvbox-dark, etc.

Total: 55+ themes via `list_themes()`

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Line numbers derived from colors | Pygments doesn't provide these explicitly |
| Token inheritance in TomlTheme | Walk parent chain before base theme for predictable behavior |
| Theme aliases | User convenience (catppuccin -> catppuccin-mocha) |
| __slots__ on PygmentsTheme | Memory efficiency for many theme instances |

## Deviations from Plan

None - plan executed exactly as written.

## Integration Points

```python
# From codepicture package
from codepicture import get_theme, list_themes

# Theme provides colors for rendering
theme = get_theme('catppuccin-mocha')
background = theme.background  # Color for editor background
style = theme.get_style(token_type)  # TextStyle for token
```

## Verification Results

- All 4 Catppuccin flavors load correctly
- Built-in Pygments themes (dracula, monokai, one-dark) accessible
- ThemeError raised with available themes for unknown name
- Token type inheritance works (String.Escape falls back to String)
- PygmentsTheme satisfies Theme protocol

## Next Phase Readiness

Ready for 02-03 integration:
- `get_theme()` provides Theme instances
- Theme.get_style() maps token types to TextStyle
- All success criteria met
