# codepicture

Generate beautiful images of your source code.

codepicture is a command-line tool that transforms source code files into
presentation-ready images. It applies syntax highlighting, macOS-style window
chrome, drop shadows, and configurable themes to produce PNG, SVG, or PDF
output -- ideal for slides, documentation, and social media.

## Quick Start

**Prerequisites:** Python 3.13+, system Cairo and Pango libraries (see
[System Dependencies](#system-dependencies) below).

```bash
# Install from source
pip install .

# Generate your first image
codepicture snippet.py -o output.png
```

## Features

- **Multiple output formats** -- PNG, SVG, and PDF
- **260+ languages** via Pygments syntax highlighting, plus a custom MLIR lexer
- **Catppuccin themes** and built-in Pygments themes (Dracula, Monokai, One Dark, and more)
- **macOS-style window controls** -- red/yellow/green traffic light buttons
- **Drop shadow effect** for a polished, floating appearance
- **Line numbers** with configurable starting offset
- **Configurable typography** -- bundled JetBrains Mono font, adjustable size and line height
- **Word wrap** -- automatic wrapping when using fixed window width
- **Visual tuning** -- padding, corner radius, background color
- **TOML config file** for persistent defaults
- **Auto-detect language** from file extension
- **Reads from file or stdin**

## Usage

Basic usage -- render a Python file to PNG:

```bash
codepicture hello.py -o hello.png
```

Apply a specific theme:

```bash
codepicture main.rs -o main.png --theme monokai
```

SVG output with shadow disabled:

```bash
codepicture app.tsx -o app.svg --no-shadow
```

Read from stdin (requires `--language`):

```bash
echo 'print("hello")' | codepicture - -o hello.png --language python
```

Custom styling:

```bash
codepicture code.go -o code.png \
  --font-size 18 \
  --padding 60 \
  --no-line-numbers \
  --background "#1e1e2e"
```

## CLI Reference

```
codepicture INPUT_FILE -o OUTPUT [OPTIONS]
```

Use `-` as INPUT_FILE to read from stdin (requires `--language`).

### Output

| Option | Description |
|--------|-------------|
| `-o, --output PATH` | Output image path (required) |
| `-f, --format FORMAT` | Output format: `png`, `svg`, `pdf` (inferred from extension) |

### Theme and Language

| Option | Description |
|--------|-------------|
| `-t, --theme NAME` | Color theme name (default: catppuccin-mocha) |
| `-l, --language NAME` | Source language (auto-detected from extension if omitted) |
| `--list-themes` | List all available themes and exit |

### Typography

| Option | Description |
|--------|-------------|
| `--font NAME` | Font family name (default: JetBrains Mono) |
| `--font-size N` | Font size in points |
| `--line-height N` | Line height multiplier |
| `--tab-width N` | Tab width in spaces |

### Visual

| Option | Description |
|--------|-------------|
| `--padding N` | Padding around code in pixels |
| `--corner-radius N` | Window corner radius |
| `--background COLOR` | Background color (`#RRGGBB`) |

### Line Numbers

| Option | Description |
|--------|-------------|
| `--line-numbers / --no-line-numbers` | Show or hide line numbers |
| `--line-offset N` | Starting line number |

### Window

| Option | Description |
|--------|-------------|
| `--window-controls / --no-window-controls` | Show or hide window controls |
| `--title TEXT` | Window title text |

### Window Size

| Option | Description |
|--------|-------------|
| `--width N` | Window width in pixels (enables word wrap) |
| `--height N` | Window height in pixels |

### Shadow

| Option | Description |
|--------|-------------|
| `--shadow / --no-shadow` | Enable or disable drop shadow |

### Config

| Option | Description |
|--------|-------------|
| `--config PATH` | Config file path (overrides default search) |

### Meta

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Show processing steps on stderr |
| `-V, --version` | Show version and exit |

## Configuration

codepicture supports a TOML config file for persistent defaults. It searches
for config files in this order:

1. `codepicture.toml` in the current directory
2. `~/.config/codepicture/config.toml`

Use `--config` to specify an explicit path.

Example config file:

```toml
theme = "catppuccin-mocha"

[typography]
font_family = "JetBrains Mono"
font_size = 16
line_height = 1.4
tab_width = 4

[line_numbers]
show = true
offset = 1

[window]
controls = true
title = ""

[effects]
shadow = true

[visual]
padding = 20
corner_radius = 8
background_color = "#1e1e2e"
# window_width = 800    # optional: fixed width (enables word wrap)
# window_height = 600   # optional: fixed height
```

CLI flags always override config file values.

## System Dependencies

codepicture uses Cairo and Pango for rendering. Install the system libraries
for your platform before installing codepicture.

**macOS:**

```bash
brew install cairo pango
```

**Ubuntu / Debian:**

```bash
apt install libcairo2-dev libgirepository1.0-dev
```

Python 3.13 or later is required.

## Development

### Setup

Install [system dependencies](#system-dependencies) first, then:

```bash
git clone https://github.com/your-username/codepicture.git
cd codepicture
uv sync
uv run pre-commit install
```

### Linting and Formatting

The project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Check for lint issues
uv run ruff check .

# Check and auto-fix lint issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

Configuration lives in `pyproject.toml` under `[tool.ruff]`.

### Pre-commit Hooks

Pre-commit hooks run ruff lint (with auto-fix) and ruff format automatically on
each commit. Install the hooks once after cloning:

```bash
uv run pre-commit install
```

To run all hooks manually against the entire codebase:

```bash
uv run pre-commit run --all-files
```

### Running Tests

```bash
# Run the full test suite
uv run pytest

# Run with coverage
uv run pytest --cov
```

### Updating Visual Regression References

Visual regression tests compare rendered output against stored reference PNGs in
`tests/visual/references/`. When rendering changes intentionally (e.g. new
defaults, bug fixes), regenerate the baselines:

```bash
uv run pytest --snapshot-update
```

Updated tests show as **skipped** — this is expected (each skip wrote a new
baseline). Verify the images look correct, then commit them:

```bash
git add tests/visual/references/
git commit -m "test: update visual regression baselines"
```

### Running Benchmarks

The project includes pytest-benchmark tests covering four pipeline stages:
highlighting, layout, rendering, and end-to-end.

```bash
# Run all benchmarks
uv run pytest tests/benchmarks/ --benchmark-only -v

# Save results to JSON for comparison
uv run pytest tests/benchmarks/ --benchmark-only --benchmark-json=results.json

# Run a specific stage benchmark
uv run pytest tests/benchmarks/test_bench_pipeline.py --benchmark-only -v
```

The project has 300+ tests with an 80% coverage requirement.

## License

MIT License
