# Project Milestones: codepicture

## v1.1 Reliability & Testing (Shipped: 2026-02-02)

**Delivered:** Hardened codepicture for real-world usage with MLIR hang fix (186x speedup), timeout protection, visual regression testing (58 tests, 20 reference images), and performance benchmarks (21 benchmarks with CI tracking).

**Phases completed:** 7-11 (14 plans total)

**Key accomplishments:**

- Fixed test.mlir rendering hang — root cause: uncached font resolution called per token (40s → 0.22s)
- Application-level timeout protection with ThreadPoolExecutor, clean error messages, and exit codes (0/1/2)
- Visual regression test suite with pixelmatch-based comparison, 20 reference images, Git LFS, and CI integration
- Parametrized reliability matrix: 5 languages x 3 formats + 7 feature toggle combinations
- Performance benchmarks: 18 per-stage + 3 end-to-end with separate CI workflow
- Comprehensive error handling: file not found, unknown language fallback, timeout — all clean, no tracebacks

**Stats:**

- 109 files created/modified
- 7,818 lines of Python (3,384 source + 4,434 test)
- 5 phases, 14 plans
- 4 days from v1.0 to v1.1 ship (2026-01-30 → 2026-02-02)

**Git range:** `docs(07)` → `docs(11)`

**What's next:** TBD — run `/gsd:new-milestone` to plan next version

---

## v1.0 MVP (Shipped: 2026-01-30)

**Delivered:** Complete CLI tool that transforms code snippets into polished, presentation-ready PNG, SVG, or PDF images with syntax highlighting, macOS window chrome, themes, and custom MLIR lexer support.

**Phases completed:** 1-6 including 1.1 (21 plans total)

**Key accomplishments:**

- Foundation layer with protocol-based architecture, Pydantic config validation, and error hierarchy
- Syntax highlighting engine with Pygments, 55+ themes (including Catppuccin), and auto-detect language
- Layout engine with Cairo text measurement, bundled JetBrains Mono, and HiDPI canvas calculations
- Multi-format rendering (PNG 2x, SVG, PDF) with macOS window chrome and drop shadows
- CLI tool (`codepicture`) with Typer, TOML config, stdin support, and flag overrides
- Custom MLIR lexer as Pygments RegexLexer with dialect support and 100% test coverage

**Stats:**

- 59 files created
- 6,050 lines of Python (3,214 source + 2,836 test)
- 7 phases, 21 plans
- 3 days from start to ship (2026-01-28 to 2026-01-30)

**Git range:** `feat(01-01)` -> `feat(06-02)`

**What's next:** TBD — run `/gsd:new-milestone` to plan next version

---
