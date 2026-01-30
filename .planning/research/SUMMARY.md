# Project Research Summary

**Project:** codepicture v1.1 — Reliability & Testing Hardening
**Domain:** Visual regression testing, rendering reliability, and performance profiling for Python image generation CLI
**Researched:** 2026-01-30
**Confidence:** HIGH

## Executive Summary

The v1.1 milestone is a pure hardening effort for codepicture, a Python CLI that converts code to stylized images. The project has a solid v1.0 foundation (260 tests, 80%+ coverage, Cairo/Pygments stack validated), but lacks critical reliability safeguards and visual verification. Research reveals three specific problems: (1) a known rendering hang on test.mlir caused by Pygments regex catastrophic backtracking, (2) no automated verification that images look correct (tests only verify PNG magic bytes, not visual correctness), and (3) no timeout protection anywhere in the pipeline.

The recommended approach is to harden in three sequential phases. First, diagnose and fix the immediate hang issue with instrumentation and subprocess-based timeouts (signal-based timeouts cannot interrupt C extensions like Pygments' regex engine). Second, establish visual regression testing with pytest-image-snapshot and reference images generated in the CI environment (macOS vs Linux font rendering differences will cause false failures otherwise). Third, add performance profiling with pytest-benchmark to detect future regressions. This ordering is critical: fix the rendering pipeline before adding visual tests to lock in correct behavior.

The major risk is choosing the wrong timeout mechanism. Signal-based timeouts (signal.SIGALRM) appear to work in tests but fail on the actual hang because Pygments regex backtracking occurs in C code that blocks signal handlers. The robust solution is concurrent.futures.ThreadPoolExecutor with future.result(timeout=N), accepting that hung threads cannot be killed but the CLI can proceed with a clear error. All new test infrastructure must use real pathological inputs (like test.mlir), not synthetic time.sleep() delays that test the wrong thing.

## Key Findings

### Stack Additions (from STACK.md)

Research focused solely on additions for v1.1 hardening. The v1.0 stack (Python 3.13+, PyCairo, Pygments, Typer, pytest) is validated and requires no changes.

**New development dependencies:**
- **pytest-benchmark 5.2.3** — Benchmark rendering functions with statistical rigor, detect performance regressions in CI via --benchmark-compare, built-in cProfile integration
- **pixelmatch 0.3.0** — Pixel-level image comparison with anti-aliasing detection, prevents font rendering false positives, works with existing Pillow dependency
- **snakeviz 2.2.2** — Browser-based cProfile visualization for development (not CI)

**Timeout implementation (stdlib only):**
- **concurrent.futures.ThreadPoolExecutor** — Primary timeout mechanism; works with C extensions (Pygments/Cairo), cross-platform, stdlib
- **signal.SIGALRM** — Fallback only; POSIX-only, cannot interrupt C code, not recommended as primary solution

**Key decisions:**
- Rejected pytest-image-snapshot plugin in favor of direct pixelmatch usage for threshold control
- Rejected OpenCV (50MB, overkill), timeout-decorator (unmaintained), wrapt-timeout-decorator (pulls multiprocess for no benefit)
- No new runtime dependencies — all reliability code uses stdlib

**Confidence:** HIGH — all versions verified via PyPI, integration patterns validated against official docs

### Expected Features (from FEATURES.md)

v1.1 is purely hardening — no new user-facing features. Research focused on test infrastructure and reliability features.

**Must have (table stakes for claiming "hardened"):**
- Test timeouts (pytest-timeout) — prevents CI hangs, 30-minute implementation
- CI job timeout — GitHub Actions defense-in-depth, 5-minute change
- MLIR lexer hang fix — the specific bug motivating this milestone
- Rendering timeout guards — application-level protection beyond test timeouts
- Visual regression test suite — 5 core languages x 2 themes = 10 golden images
- Rendering reliability matrix — parametrized tests across languages/formats/configs
- Error handling audit — clean error messages for all failure modes including new RenderTimeoutError

**Should have (differentiators):**
- Performance benchmarks (pytest-benchmark) — track render times, detect regressions
- Diff image artifact upload — upload visual diffs to GitHub Actions on failure
- Fuzz testing for MLIR lexer (hypothesis) — property-based testing catches pathological inputs
- Memory usage guards — tracemalloc assertions for large files
- Structured verbose output — timing per pipeline stage

**Defer to post-v1.1:**
- Performance dashboard (Bencher) — overkill for current scale
- Multi-OS CI for visual tests — platform rendering differences are expected, not bugs
- Parallel/async rendering — single-threaded pipeline is sufficient

**Anti-features (explicitly avoid):**
- Custom image diff viewer — use pytest-image-snapshot's built-in diffs
- Testing all 55+ Pygments themes — test 2 representative themes (dark + light)
- Pixel-perfect cross-platform matching — different font rendering is reality, not a bug
- Per-stage timeout hierarchy — one pipeline-level timeout, fix root causes not symptoms

**Critical path:** Test timeouts -> MLIR fix -> rendering timeout guards -> visual regression suite

**Confidence:** HIGH — based on codebase analysis (260 existing tests, test fixtures for 5 languages, known test.mlir hang bug)

### Architecture Approach (from ARCHITECTURE-HARDENING.md)

The existing pipeline is linear and protocol-based (Highlighter -> LayoutEngine -> Renderer). No architectural changes are needed; three new subsystems wrap the existing pipeline externally.

**Subsystem 1: Rendering Timeouts and Safety**
- New `safety.py` module with timeout context manager
- Modified `orchestrator.py` wraps each pipeline stage with timeout
- New `RenderTimeoutError` exception in existing error hierarchy
- Implementation: ThreadPoolExecutor-based timeout (primary) or signal.SIGALRM (POSIX fallback)
- Critical: Timeouts wrap orchestrator, NOT individual protocol implementations (preserves protocol purity)

**Subsystem 2: Visual Regression Testing**
- New `tests/visual/` package with pytest fixtures
- Reference images in `tests/snapshots/` (committed to repo, generated in CI environment)
- Integration: pytest-image-snapshot OR raw pixelmatch with ~30-line custom fixture
- Platform consistency: Generate golden images on ubuntu-latest only (macOS font rendering differs)
- CI workflow: upload diff images as artifacts on failure

**Subsystem 3: Performance Profiling**
- New `tests/benchmarks/` package with pytest-benchmark tests
- Benchmark fixtures: small/medium/large code samples
- Per-stage benchmarks (highlight, layout, render) + end-to-end pipeline
- CI integration: --benchmark-json artifact upload, optional --benchmark-compare for regression detection

**Key architectural principles:**
- Safety and observability are orchestration concerns, not component concerns
- Protocol implementations (Highlighter, Renderer, Canvas) remain unchanged
- All new code is additive, no refactoring of v1.0 pipeline

**Build order (minimizes risk):**
1. Phase 1: Rendering timeouts (small surface area, unblocks testing)
2. Phase 2: Visual regression tests (requires non-hanging pipeline from Phase 1)
3. Phase 3: Performance profiling (lowest urgency, benefits from Phases 1+2)

**Confidence:** HIGH — architecture patterns well-understood from codebase analysis, timeout/profiling integration validated against stdlib docs

### Critical Pitfalls (from PITFALLS.md)

Research identified 12 pitfalls specific to v1.1 hardening work. Top 5 critical:

1. **Signal-based timeouts cannot interrupt C-extension hangs** — signal.SIGALRM only fires between Python bytecodes. Pygments regex backtracking (C code), Cairo rendering (C code), and Pillow blur (C code) block signal delivery indefinitely. **Solution:** Use concurrent.futures.ProcessPoolExecutor with future.result(timeout=N) or multiprocessing.Process.terminate() for true killing. **Phase impact:** Directly blocks the test.mlir fix.

2. **Diagnosing the hang in the wrong pipeline stage** — Assuming the hang is in the lexer without profiling could lead to days spent fixing the wrong component. **Solution:** Instrument each pipeline stage with timing before any fixes. Use py-spy dump to get stack traces of hanging processes. **Phase impact:** First step in v1.1 before any fixes.

3. **Visual regression tests that are flaky across environments** — Font rendering differs between macOS CoreText and Linux FreeType. Tests pass locally, fail in CI. **Solution:** Generate reference images in the same environment as CI (ubuntu-latest Docker). Use perceptual comparison with threshold (pixelmatch), never pixel-perfect. Bundle fonts (already done). **Phase impact:** Design visual regression approach before generating reference images.

4. **Reference image bloat in Git history** — 50+ PNGs updated on every visual change balloons repo size. **Solution:** Use Git LFS for tests/**/*.png tracking BEFORE committing first reference. Use small image dimensions for tests. Minimize reference count (10-15 well-chosen images). **Phase impact:** Set up LFS before visual regression phase.

5. **Testing timeouts with synthetic delays instead of real pathological input** — time.sleep() tests Python-level timeout behavior but not the ability to interrupt C extensions. Tests pass, feature is broken. **Solution:** Test with actual pathological input (test.mlir content). Keep hanging inputs as test fixtures. **Phase impact:** When implementing timeouts, write tests with real input FIRST.

**Moderate pitfalls:**
- Profiling wrong metric (CPU time vs wall time, small inputs vs realistic inputs)
- Pillow GaussianBlur scaling surprise at 2x HiDPI (blur operates on physical pixels, not logical)
- Over-engineering visual regression framework (weeks on infrastructure, zero bugs fixed)
- MLIR lexer regex fix introduces new backtracking (fix one pattern, break another)

**Phase-specific warnings:**
- Diagnosing test.mlir hang: Instrument first, profile with py-spy, confirm stage before fixing
- Adding timeouts: Use subprocess-based, not signal-based; test with real input, not sleep()
- Fixing MLIR lexer: Test with corpus of 10+ MLIR files, add fuzzing tests
- Visual regression: Generate references in CI environment, start with 5-8 images, use LFS
- Performance profiling: Profile realistic inputs, measure wall time per stage first, then drill into bottlenecks

**Confidence:** HIGH — pitfalls verified against Python signal docs, multiple Pygments issues documenting catastrophic backtracking, visual regression testing literature

## Implications for Roadmap

Based on research findings, recommended phase structure for v1.1:

### Phase 1: Diagnose and Fix Hang
**Rationale:** The known test.mlir hang is the primary motivator for v1.1. Must diagnose the root cause before implementing fixes. Cannot build visual tests or performance benchmarks on a hanging pipeline.

**Delivers:**
- Instrumented pipeline with timing per stage
- Diagnosis of which stage (highlight/layout/render/shadow) causes the hang
- Fix for the root cause (likely MLIR lexer regex backtracking)
- Subprocess-based timeout wrapper in safety.py
- RenderTimeoutError exception type
- Tests using real pathological input (test.mlir as fixture)

**Addresses features:**
- MLIR lexer hang fix (table stakes)
- Rendering timeout guards (table stakes)

**Avoids pitfalls:**
- Pitfall 2: Diagnose before fixing (instrument first)
- Pitfall 1: Use subprocess-based timeout, not signal-based
- Pitfall 7: Test with real pathological input, not synthetic delays
- Pitfall 9: Test regex changes with corpus of MLIR files

**Stack used:**
- concurrent.futures.ThreadPoolExecutor (stdlib)
- pytest for testing timeout behavior
- py-spy for profiling (optional, dev tool)

**Research flag:** LOW — Timeout patterns are well-documented stdlib functionality. MLIR regex debugging is manual but straightforward.

### Phase 2: Visual Regression Test Suite
**Rationale:** Once the pipeline is stable (Phase 1), establish visual verification to catch future regressions. Current tests verify output format but not correctness. This is the biggest gap in v1.0 test coverage.

**Delivers:**
- tests/visual/ package with pytest fixtures
- tests/snapshots/ directory with 10-15 reference images (committed via Git LFS)
- Reference images for 5 core languages (Python, Rust, C++, JavaScript, MLIR) x 2 themes (dark + light)
- Edge case references (empty input, long lines, unicode)
- CI workflow step to run visual tests and upload diff artifacts on failure
- pytest marker for visual tests

**Addresses features:**
- Visual regression test suite (table stakes)
- Rendering reliability matrix (table stakes via parametrized tests)
- Diff image artifact upload (should-have differentiator)

**Avoids pitfalls:**
- Pitfall 3: Generate references in CI environment (ubuntu-latest), not macOS
- Pitfall 4: Set up Git LFS BEFORE committing first reference image
- Pitfall 8: Start with 5-8 images, not custom framework
- Pitfall 10: Compare pixel data only, strip metadata

**Stack used:**
- pixelmatch 0.3.0 for anti-aliasing-aware comparison
- Pillow (existing) for image loading and diff visualization
- Git LFS for reference image storage
- pytest parametrize for language/theme/config matrix

**Research flag:** MEDIUM — Font rendering cross-platform differences may require iteration on threshold values. Plan for 1-2 rounds of tuning.

### Phase 3: Test Hardening and CI Protection
**Rationale:** Add defense-in-depth test timeouts and CI safeguards now that pipeline is fixed and visual tests are in place.

**Delivers:**
- pytest-timeout added to dev dependencies with global 30s default in pyproject.toml
- CI job timeout-minutes: 10 in .github/workflows/test.yml
- Error handling audit — verify all failure modes produce clean error messages
- Tests for timeout behavior and error paths

**Addresses features:**
- Test timeouts (table stakes)
- CI job timeout (table stakes)
- Error handling audit (table stakes)

**Avoids pitfalls:**
- None specifically, this is defense-in-depth after root causes fixed

**Stack used:**
- pytest-timeout (dev dependency)
- Existing error hierarchy in errors.py

**Research flag:** LOW — pytest-timeout is straightforward pytest plugin.

### Phase 4: Performance Profiling (Optional/Future)
**Rationale:** Lowest urgency. Pipeline stability and correctness (Phases 1-3) must come first. Performance profiling is most valuable after reliability is established.

**Delivers:**
- tests/benchmarks/ package with pytest-benchmark tests
- Benchmark fixtures for small/medium/large code samples
- Per-stage benchmarks (highlight, layout, render) and end-to-end pipeline
- CI workflow step to run benchmarks and upload JSON artifacts
- Optional: --benchmark-compare for regression detection

**Addresses features:**
- Performance benchmarks (should-have differentiator)
- Memory usage guards (should-have, via tracemalloc in benchmark tests)

**Avoids pitfalls:**
- Pitfall 5: Profile realistic inputs, measure wall time first
- Pitfall 6: If shadow is bottleneck, investigate 2x HiDPI blur scaling
- Pitfall 11: Use pytest-benchmark for statistical rigor, not single runs

**Stack used:**
- pytest-benchmark 5.2.3
- snakeviz 2.2.2 (dev tool for visualization)
- cProfile (stdlib, via --benchmark-cprofile)

**Research flag:** LOW — pytest-benchmark is mature and well-integrated.

### Phase Ordering Rationale

1. **Phase 1 must come first** — Cannot build tests on a hanging pipeline. Diagnosis reveals whether the hang is lexer/layout/render/shadow, informing the fix.

2. **Phase 2 requires Phase 1** — Visual regression tests lock in correct rendering behavior. If the pipeline is broken (hanging or producing wrong output), visual tests lock in broken behavior.

3. **Phase 3 is defense-in-depth** — Test timeouts and CI timeouts prevent future hangs, but only after root causes are fixed. Adding them before Phase 1 would mask the symptoms without fixing the cause.

4. **Phase 4 is optional** — Performance profiling has value but is not essential for "hardening." Can be deferred to v1.2 if time-constrained.

**Dependency graph:**
```
Phase 1 (Diagnose & Fix) ---> Phase 2 (Visual Regression)
        |                             |
        v                             v
Phase 3 (Test Hardening) ---> Phase 4 (Performance) [optional]
```

**Critical path:** Phases 1-3 (Phase 4 can run in parallel or be deferred)

### Research Flags

**Phases needing deeper research during planning:**
- Phase 2 (Visual Regression): Font rendering cross-platform differences may require iteration. Budget time for threshold tuning.

**Phases with standard patterns (skip research-phase):**
- Phase 1 (Timeouts): Well-documented stdlib patterns
- Phase 3 (Test Hardening): pytest-timeout is straightforward
- Phase 4 (Performance): pytest-benchmark is mature

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified via PyPI. Integration patterns validated against stdlib and pytest-benchmark docs. No new runtime dependencies. |
| Features | HIGH | Based on codebase analysis (260 existing tests, 5 language fixtures, known test.mlir bug). v1.1 scope is clear: fix hang, add visual tests, guard against regressions. |
| Architecture | HIGH | Existing pipeline architecture understood via codebase analysis. All new subsystems are additive wrappers, no refactoring needed. Build order minimizes risk. |
| Pitfalls | HIGH | Signal vs subprocess timeout limitations verified in Python docs. Catastrophic backtracking documented in multiple Pygments issues. Visual regression cross-platform issues are well-known. |

**Overall confidence:** HIGH

The v1.1 scope is well-defined (hardening only, no new features), the existing codebase is well-structured and testable, and all research findings are validated against official documentation or multiple corroborating sources.

### Gaps to Address

**Medium-priority gaps:**
- Exact threshold values for pixelmatch visual comparison — will require tuning during Phase 2 based on actual CI rendering variance
- Whether test.mlir hang is in lexer vs layout vs render — must be diagnosed in Phase 1 before proceeding

**Low-priority gaps:**
- Cross-platform font rendering behavior if macOS developers want to run visual tests locally — accept as known limitation, CI is source of truth
- Performance optimization strategy if shadow blur is bottleneck — defer to Phase 4, only relevant if profiling confirms it is the issue

**No blocking gaps.** All critical questions have clear answers or investigation paths.

## Sources

### Primary (HIGH confidence)

**Official documentation:**
- [Python signal module docs](https://docs.python.org/3/library/signal.html) — Signal limitations with C extensions
- [Python concurrent.futures docs](https://docs.python.org/3/library/concurrent.futures.html) — ThreadPoolExecutor timeout patterns
- [Python cProfile docs](https://docs.python.org/3/library/profile.html) — Built-in profiler
- [Pillow ImageChops docs](https://pillow.readthedocs.io/en/stable/reference/ImageChops.html) — Image comparison operations

**Verified via PyPI:**
- [pytest-benchmark 5.2.3](https://pypi.org/project/pytest-benchmark/) — Python 3.9+, pytest 8.1+, cProfile integration
- [pytest-benchmark docs](https://pytest-benchmark.readthedocs.io/) — --benchmark-compare, --benchmark-cprofile
- [pixelmatch 0.3.0](https://pypi.org/project/pixelmatch/) — Python port of mapbox/pixelmatch
- [pixelmatch-py GitHub](https://github.com/whtsky/pixelmatch-py) — API docs, threshold/AA options
- [snakeviz 2.2.2](https://pypi.org/project/snakeviz/) — Python 3.9+, BSD licensed
- [pytest-timeout](https://pypi.org/project/pytest-timeout/) — v2.4.0, SIGALRM and thread methods

**Codebase analysis (HIGH confidence):**
- All source files under `src/codepicture/` — existing pipeline architecture
- `tests/conftest.py` — 13 fixtures, rendering helpers, font registration
- `tests/fixtures/` — 5 language fixture files
- `.github/workflows/test.yml` — CI configuration
- `pyproject.toml` — dev dependencies, pytest config

### Secondary (MEDIUM confidence)

**Pygments issues (multiple corroborating sources):**
- [Pygments Issue #2356](https://github.com/pygments/pygments/issues/2356) — Java properties lexer catastrophic backtracking
- [Pygments Issue #2355](https://github.com/pygments/pygments/issues/2355) — SQL lexer catastrophic backtracking
- [Pygments Issue #2053](https://github.com/pygments/pygments/issues/2053) — Elpi lexer pathological backtracking
- [Pygments Issue #1065](https://github.com/pygments/pygments/issues/1065) — JSON lexer backtracking fix
- [Pygments lexer development docs](https://pygments.org/docs/lexerdevelopment/) — "Beware of catastrophic backtracking"

**Visual regression patterns:**
- [pytest-image-snapshot](https://github.com/bmihelac/pytest-image-snapshot) — Visual regression library with pixelmatch
- [Playwright visual tests with Docker](https://medium.com/@adam_pajda/playwright-visual-tests-with-git-lfs-and-docker-d537ddd6e86a) — Environment consistency
- [Base Web visual regression](https://baseweb.design/blog/visual-regression-testing/) — CI workflow patterns
- [Visual Regression Testing with GitHub Actions](https://www.duncanmackenzie.net/blog/visual-regression-testing/) — CI integration patterns

**Performance and profiling:**
- [pytest-benchmark patterns (Dec 2025)](https://medium.com/@sparknp1/10-pytest-benchmark-patterns-for-honest-performance-claims-6cc674893494) — Best practices
- [Python timeout best practices](https://betterstack.com/community/guides/scaling-python/python-timeouts/) — ThreadPoolExecutor as robust approach
- [Real Python profiling guide](https://realpython.com/python-profiling/) — Profiling workflow

### Tertiary (LOW confidence)

**Reference for comparison, not used:**
- [timeout-decorator](https://github.com/pnpnpn/timeout-decorator) — Signal vs multiprocessing tradeoffs (unmaintained, not recommended)
- [pytest-image-diff](https://github.com/Apkawa/pytest-image-diff) — Alternative visual regression library (less popular)
- [reg-viz/reg-actions](https://github.com/reg-viz/reg-actions) — CI visual regression pattern reference

---
*Research completed: 2026-01-30*
*Ready for roadmap: yes*
