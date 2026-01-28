# Project Research Summary

**Project:** codepicture
**Domain:** Python CLI tool for generating styled code screenshots (PNG, SVG, PDF)
**Researched:** 2026-01-28
**Confidence:** HIGH

## Executive Summary

codepicture is a command-line tool that takes source code as input and produces polished, presentation-ready images of that code -- the same category as Carbon, ray.so, and the Rust-based Silicon. The research consensus is clear: this is a well-understood problem space with a proven rendering pipeline. The correct approach is a layered architecture driven by PyCairo for vector/raster output and PangoCairo (via PyGObject) for professional text layout. Pygments handles syntax tokenization, and Typer provides the CLI surface. The entire stack is mature, well-documented, and high-confidence.

The primary risk is not in the technology choices -- those are settled -- but in the ordering of implementation work. Two architectural decisions must be locked in at the very start or retrofitting them later becomes a significant rewrite: (1) use PangoCairo for all text rendering, never Cairo's "toy" text API, and (2) design the rendering pipeline around a two-phase measure-then-draw approach so canvas dimensions are always computed before any pixels are committed. The competitive differentiators for codepicture are MLIR custom lexer support (no competitor has this), PDF output (unique among the tool set), and native offline speed matching Silicon. These are achievable within the standard architecture without exotic engineering.

The feature set required for a credible v1 launch is well-defined: syntax highlighting with theme selection, PNG and SVG output, macOS-style window chrome with drop shadow, line numbers, configurable padding, file and stdin input, and language auto-detection. The MLIR lexer is explicitly a P1 feature given the stated niche focus. Post-launch additions (PDF output, clipboard I/O, gradient backgrounds, line highlighting, config files) are all low-cost extensions of the core rendering pipeline and should not block the initial release.

## Key Findings

### Recommended Stack

The stack follows a clear hierarchy. PyCairo provides the graphics engine for shapes, shadows, rounded corners, and multi-format output (PNG, SVG, PDF surfaces are all first-class). PangoCairo, accessed through PyGObject, is non-negotiable for text -- it provides kerning, ligatures, font fallback, and multi-script support that Cairo's built-in text functions cannot deliver. Pygments handles syntax tokenization across 300+ languages and ships 50+ color themes out of the box. Typer wraps Click with type-hint-driven ergonomics and pulls in Rich for terminal output formatting. Pydantic v2 provides type-safe configuration with validation at load time.

**Core technologies:**
- PyCairo 1.29.0: 2D vector graphics engine, outputs PNG/SVG/PDF natively -- the rendering backbone
- PyGObject 3.54.5: Access to PangoCairo for professional text layout with kerning and font fallback -- mandatory, not optional
- Pygments 2.19.2: Syntax tokenization across 300+ languages, 50+ built-in themes -- the de facto standard
- Typer 0.21.1: CLI framework with auto-completion and Rich integration -- modern DX over raw Click
- Pydantic 2.12.5: Configuration validation and schema definition -- catches bad config at load time, not render time

**Critical system dependency:** Cairo, Pango, and GObject are C libraries. Their dev headers must be installed via the system package manager before any pip install. This is a deployment consideration, not an architecture one, but it affects CI/CD setup from day one.

**Minimum Python:** 3.10 (PyCairo 1.29.0 constraint). Recommended: 3.13 per project spec.

### Expected Features

The feature research maps neatly onto a priority structure. Table stakes are the features every competitor already has -- missing any of them makes the tool feel incomplete to users arriving from Carbon or Silicon. Differentiators are the features that justify codepicture's existence alongside those tools.

**Must have (table stakes):**
- Syntax highlighting with Pygments -- the core value proposition
- PNG and SVG output -- PNG for sharing, SVG for vector quality in docs
- macOS-style window chrome (traffic light buttons) -- the signature visual identity of "pretty code screenshots"
- Drop shadow -- depth and polish, expected by users
- Theme selection (Monokai, Dracula, GitHub Dark, etc.) -- Pygments provides these for free
- Line numbers (toggleable) -- many use cases need them, some don't
- Font selection (monospace) -- personal preference, easy to expose
- Configurable background color and padding -- basic customization
- File input and stdin input -- CLI fundamentals
- Language auto-detection from file extension -- convenience that competitors provide
- MLIR custom lexer -- the stated differentiator for ML/compiler users

**Should have (competitive, low-cost to add post-launch):**
- PDF output -- unique among competitors, Cairo supports it natively
- Clipboard input/output -- workflow convenience, platform-specific
- Gradient backgrounds -- ray.so's signature look, Cairo gradient patterns
- Line highlighting (e.g., `--highlight 3-5`) -- emphasis on specific lines
- Window title customization -- text in the title bar
- Rounded corners -- modern aesthetic
- Configuration file (TOML) -- saves retyping options
- 2x/retina scale factor -- HiDPI quality

**Defer (v2+):**
- Font ligatures (HarfBuzz integration, HIGH complexity)
- Presets system (only after config files prove useful)
- Image backgrounds behind code
- Additional custom lexers beyond MLIR (demand-driven)
- Configurable window control styles (macOS vs Windows vs none)

**Anti-features to resist:** Real-time web preview, multi-file/diff views, animation output, embedding/iframe hosting, API/web service, editor integrations, cloud save, AI-generated annotations. These are out of scope for a CLI tool and would dilute the product.

### Architecture Approach

The architecture follows a layered pipeline that is industry-standard for this class of tool. An Application Facade (CodePictureApp) orchestrates all subsystems and serves as the single entry point for both the CLI and any future programmatic API. Below it, the pipeline flows: Input handling feeds raw code into a Highlighter (Pygments), which produces a token stream. A Theme adapter maps token types to visual styles. A Text Measurer (PangoCairo) computes dimensions. A Layout Engine calculates positions and canvas size. Finally, a Canvas/Renderer (PyCairo) draws everything and serializes to the output format. This two-phase measure-then-draw pattern is critical: you cannot create a Cairo surface until you know the final dimensions, and you cannot know the final dimensions until you have measured all the text.

**Major components:**
1. Application Facade (app.py) -- single entry point, configuration merging, component lifecycle
2. Highlighter (highlight/) -- Pygments tokenization, isolated behind a Protocol so alternatives are possible
3. Layout Engine (core/layout.py) -- two-phase dimension calculation, depends on Text Measurer
4. Canvas/Renderer (render/) -- PyCairo surface management, effects (shadow, blur), format-specific output
5. Theme System (theme/) -- Pygments style adapter, theme discovery and loading
6. Configuration (config/) -- Pydantic schemas, TOML loading, precedence-based merging (defaults < config file < CLI args < programmatic)
7. CLI Interface (cli/) -- Typer commands, calls Facade only, never imports core directly

**Build order:** Foundation types and protocols first, then highlighting, then layout, then rendering, then orchestration, then CLI. Each layer can be tested in isolation via mocks of the layers below it.

### Critical Pitfalls

1. **Cairo toy text API** -- Cairo's `show_text()` is explicitly a "toy API" in the official docs. It has no kerning, no font fallback, no complex script support. Use PangoCairo from day one. Retrofitting Pango onto a toy-API codebase is a HIGH-cost rewrite. This is a Phase 1 decision, not something to revisit later.

2. **Drawing before measuring** -- Creating a canvas with guessed dimensions, then trying to fit content, is wrong for this pipeline. PDF and SVG surfaces cannot be resized after creation. Always run the measurement phase first to compute exact dimensions, then create the canvas. This is the two-phase rendering pattern.

3. **Shadow blur is not a Cairo primitive** -- Unlike CSS or Figma, Cairo has no built-in drop shadow or Gaussian blur. Plan for this from the start. The recommended approach is to render the shadow as a separate layer, blur it with Pillow's GaussianBlur, and composite it back under the main content using Cairo.

4. **Tab character width inconsistency** -- Tabs render as 8 spaces by default on most systems. Go and Makefile code will look broken if tabs are not normalized. Normalize tabs to configurable spaces (default 4) in the input processing stage, not at render time.

5. **Pygments lexer regex catastrophic backtracking** -- Pygments provides no execution time guarantees. Malformed or adversarial input can cause the highlighter to hang. Wrap highlighting calls with a timeout (5-10 seconds), with graceful fallback to plain text rendering. This is especially important for the custom MLIR lexer.

6. **Font embedding in SVG/PDF** -- SVG does not embed fonts by default. PDF embedding requires fonts that permit it. Output that renders correctly on the developer machine will break on a clean system. For SVG, either convert text to paths or document font requirements. For PDF, verify embedding with `pdffonts`.

## Implications for Roadmap

Based on combined research, the suggested phase structure follows the architecture's natural dependency order while front-loading the critical design decisions that cannot be changed later.

### Phase 1: Foundation and Core Types
**Rationale:** Every other component depends on these abstractions. Locking in the Protocol definitions, data types, and configuration schema here prevents structural debt. The two architectural decisions that are irreversible (PangoCairo for text, two-phase measure-then-draw) must be encoded here.
**Delivers:** core/types.py, core/protocols.py, config/schema.py, errors.py. No rendering output yet, but the contracts are established.
**Addresses:** Configuration validation (anti-pattern: validating at render time), tab normalization (pitfall 4).
**Avoids:** Cairo toy text API (pitfall 1), drawing before measuring (pitfall 2).

### Phase 2: Syntax Highlighting and Theming
**Rationale:** Highlighting is the logical next layer -- it transforms raw code into structured token streams that everything downstream consumes. Theme resolution (token type to color) is a pure data mapping that can be tested independently of any rendering.
**Delivers:** highlight/pygments_impl.py, theme/pygments_theme.py, theme/loader.py. Testable token streams and style resolution.
**Implements:** Highlighter and Theme Protocol implementations.
**Avoids:** Tight coupling to Pygments internals (anti-pattern 1 from ARCHITECTURE.md) -- use the Protocol abstraction.

### Phase 3: Layout Engine
**Rationale:** Layout calculations are pure math that depend on text measurement but not on actual drawing. This phase can be tested with a mock TextMeasurer, isolating it from Cairo entirely. Getting layout right here means the rendering phase has exact coordinates to work with.
**Delivers:** core/layout.py, LayoutMetrics computation. Knows canvas dimensions before any surface is created.
**Uses:** Text measurement via Protocol (mockable for unit tests, PangoCairo in integration).
**Implements:** Two-phase rendering pattern (measure phase).

### Phase 4: Rendering Pipeline
**Rationale:** This is the most complex phase and benefits from the isolation provided by Phases 1-3. Cairo surface management, PangoCairo text rendering, window chrome, and effects (shadow/blur) all live here. PNG output is the primary target; SVG is a surface swap.
**Delivers:** render/cairo_canvas.py, render/effects.py. First working end-to-end images (PNG, SVG).
**Uses:** PyCairo, PangoCairo (via PyGObject), Pillow (for shadow blur compositing).
**Implements:** Canvas Protocol, Effects Engine.
**Avoids:** Shadow blur from scratch without a plan (pitfall 3), hardcoded pixel dimensions without scale factor (pitfall 2).

### Phase 5: Orchestration and CLI
**Rationale:** The Application Facade ties all previous phases together. The CLI is a thin wrapper that calls the Facade. This is the last phase because it has no logic of its own -- it is purely wiring.
**Delivers:** app.py (CodePictureApp), cli/main.py (Typer CLI), config/loader.py (TOML file loading). First user-facing executable.
**Addresses:** All P1 table-stakes features (syntax highlighting, PNG/SVG output, window chrome, shadow, themes, line numbers, file/stdin input, language auto-detection).
**Implements:** Configuration layering pattern (defaults < config file < CLI args).

### Phase 6: MLIR Custom Lexer
**Rationale:** The MLIR lexer is a P1 differentiator but should be built after the highlighting pipeline is proven stable. MLIR is a rapidly evolving language with many dialects -- the lexer needs to gracefully handle unknown constructs rather than breaking. This phase should include dedicated fuzzing and timeout protection.
**Delivers:** MLIR lexer with documented dialect coverage, timeout protection, graceful degradation for unknown constructs.
**Avoids:** Incomplete MLIR coverage without escape hatch (pitfall 7), Pygments regex backtracking (pitfall 5).
**Note:** This is the phase most likely to need iterative refinement based on user feedback.

### Phase 7: Polish and Differentiators
**Rationale:** Post-launch features that are low-cost extensions of the existing pipeline. PDF output is a surface swap in Cairo. Clipboard I/O is platform-specific but isolated. Gradient backgrounds and line highlighting are rendering additions.
**Delivers:** PDF output, clipboard I/O, gradient backgrounds, line highlighting, window title, rounded corners, 2x/retina output, configuration file support.
**Addresses:** Competitive differentiators (PDF unique, clipboard convenience).
**Avoids:** Font embedding issues in SVG/PDF (pitfall 6) -- must be addressed when PDF ships.

### Phase Ordering Rationale

- Phases 1-3 are pure logic with no rendering dependencies. They can be tested via mocks and unit tests alone. This front-loads confidence in the data model before any pixels are drawn.
- Phase 4 (rendering) is isolated from business logic. Changes to how shadows work do not ripple into layout calculations.
- Phase 5 (CLI) is last among core phases because it is the thinnest layer. The Facade pattern means the CLI has no logic -- just argument parsing and Facade invocation.
- Phase 6 (MLIR) is separated from the general highlighting phase because it requires domain-specific testing (fuzzing, dialect coverage) that general highlighting does not.
- Phase 7 (polish) groups features that are all extensions of the rendering pipeline, not new architectural work.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (Rendering):** Shadow blur implementation requires prototyping. The Pillow-composite approach is recommended but untested in this specific Cairo pipeline. Validate before committing to the approach.
- **Phase 6 (MLIR Lexer):** MLIR dialect coverage is sparse in existing Pygments lexers. The LLVM PR #120942 is a reference but incomplete. Needs domain expert validation.
- **Phase 7 (Font Embedding):** SVG and PDF font embedding behavior varies by Cairo version and font licensing. Needs verification on target deployment platforms.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Pydantic models, Protocol definitions, and type hierarchies are well-documented Python patterns.
- **Phase 2 (Highlighting):** Pygments integration is thoroughly documented with official tutorials.
- **Phase 3 (Layout):** Text measurement and coordinate math are deterministic calculations with clear test cases.
- **Phase 5 (CLI):** Typer CLI setup with testing via CliRunner is a documented, low-risk pattern.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified via PyPI. Architecture validated against official PyCairo and PangoCairo documentation. System dependency requirements are explicit. |
| Features | HIGH | Feature set derived from multiple competitors (Carbon, Silicon, ray.so) with direct comparison. MVP definition is well-bounded. |
| Architecture | HIGH | Layered pipeline pattern is industry-standard for this tool class. Build order follows natural dependency graph. Protocol-based design is proven Python practice. |
| Pitfalls | MEDIUM-HIGH | Critical pitfalls (toy text API, measure-before-draw) are verified against official documentation. Performance traps and security issues are inferred from ecosystem experience and may need validation in this specific stack combination. |

**Overall confidence:** HIGH

### Gaps to Address

- **Shadow blur performance:** The Pillow-composite approach for Gaussian blur is recommended but not benchmarked in this pipeline. Prototype early in Phase 4 to validate performance is acceptable (target: under 100ms for typical shadow).
- **PangoCairo font rendering consistency:** Cross-platform font rendering (macOS vs Linux) will produce visually different output even with the same bundled font. Acceptable for a CLI tool, but visual regression tests need platform-specific baselines.
- **MLIR lexer coverage breadth:** No existing Pygments MLIR lexer covers more than core IR plus a subset of built-in types. The scope of dialect support needed for the target user base is undefined. Needs user research or community input.
- **Clipboard platform support:** Linux clipboard access (xclip/xsel) depends on system packages that may not be installed. Graceful degradation strategy needs definition.
- **Rich import latency:** Typer bundles Rich, which adds 200ms+ startup time if eagerly imported. Lazy-load Rich in the CLI to keep `codepicture --help` snappy.

## Sources

### Primary (HIGH confidence)
- PyCairo 1.29.0 official documentation -- surface types, text rendering limitations, SVG/PDF output
- PangoCairo documentation (docs.gtk.org) -- text layout, font description syntax, layout reuse
- Pygments 2.19.2 official docs -- lexer API, formatter API, custom lexer registration, FAQ (security warnings)
- Typer 0.21.1 official docs -- CLI setup, testing with CliRunner
- Pydantic v2 documentation -- model validation, configuration schemas
- Carbon GitHub (carbon-app/carbon) -- feature reference, competitive baseline
- Silicon GitHub (Aloxaf/silicon) -- Rust CLI reference, feature set, config file approach
- LLVM MLIR Pygments Lexer PR #120942 -- reference MLIR lexer implementation

### Secondary (MEDIUM confidence)
- cairo-pango-python integration tutorials -- PyGObject access patterns
- pytest-image-snapshot documentation -- visual regression testing setup
- carbon-now-cli GitHub -- CLI configuration options, preset system
- Snappify blog comparisons -- competitive feature matrix
- ray.so (raycast/ray-so) -- gradient background, visual design reference

### Tertiary (LOW confidence)
- DEV.to accessibility articles -- anti-pattern justification for code screenshots
- Matplotlib HiDPI issues -- Cairo DPI handling patterns (different domain, same library)
- Catppuccin style guide discussions -- theme consistency expectations

---
*Research completed: 2026-01-28*
*Ready for roadmap: yes*
