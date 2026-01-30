# Domain Pitfalls: v1.1 Reliability, Visual Regression & Performance

**Domain:** Adding reliability testing, visual regression, and performance optimization to an existing Python image generation tool
**Researched:** 2026-01-30
**Confidence:** MEDIUM-HIGH
**Scope:** Pitfalls specific to the v1.1 hardening milestone. v1.0 pitfalls (Cairo toy API, DPI, tabs, etc.) documented in previous research and already addressed.

---

## Critical Pitfalls

Mistakes that cause wasted effort, false confidence, or re-introduction of bugs.

### Pitfall 1: Signal-Based Timeouts Cannot Interrupt C-Extension Hangs

**What goes wrong:**
You add `signal.SIGALRM` to timeout Pygments lexing or Cairo rendering, but the hang occurs inside a C extension (Python's `re` engine doing catastrophic backtracking, Cairo's C rendering code, or Pillow's C blur implementation). Signal handlers only execute between Python bytecodes. A C-level hang blocks the signal handler from ever firing, so the "timeout" never triggers.

**Why it happens:**
The Python docs state: "A long-running calculation implemented purely in C may run uninterrupted for an arbitrary amount of time, regardless of any signals received." Since `re.match()` (used by Pygments RegexLexer) is implemented in C, catastrophic backtracking in a regex will block signal delivery until the match attempt completes -- which may be never.

**Consequences:**
- The timeout decorator appears to work in tests (Python-level delays are interruptible) but fails in production on the exact case it was designed to catch
- Users still experience the hang; developers believe it is protected
- False sense of safety

**Prevention:**
1. Use `multiprocessing` with a timeout, not `signal.SIGALRM`. Spawn the lexing/rendering in a subprocess that can be forcefully terminated (`process.kill()`)
2. Alternatively, use `concurrent.futures.ProcessPoolExecutor` with `future.result(timeout=N)` -- this creates a separate process that the OS can kill
3. For tests, use `pytest-timeout` with `method=signal` for Python-level hangs, but understand it has the same C-extension limitation
4. The most practical approach for codepicture: isolate the Pygments `lexer.get_tokens()` call in a subprocess, since that is the most likely hang point (regex backtracking)

**Warning signs:**
- Timeout tests pass with `time.sleep()` but CLI still hangs on `test.mlir`
- `pytest-timeout` kills the test runner process instead of the individual test
- Users report hangs despite "timeout protection" being in place

**Detection:**
- Test the timeout mechanism with actual pathological input, not synthetic delays
- Profile with `py-spy` (sampling profiler that can attach to a hanging process) to see if execution is stuck in C code

**Phase:** This is the FIRST thing to address in v1.1 -- it directly blocks the `test.mlir` fix.

**Confidence:** HIGH -- verified via Python official docs on signal handling and multiple Pygments GitHub issues documenting this exact problem.

**Sources:**
- [Python signal docs](https://docs.python.org/3/library/signal.html) -- "A long-running calculation implemented purely in C..."
- [Pygments Issue #2356](https://github.com/pygments/pygments/issues/2356) -- Java properties lexer catastrophic backtracking
- [Pygments Issue #2355](https://github.com/pygments/pygments/issues/2355) -- SQL lexer catastrophic backtracking
- [timeout-decorator docs](https://github.com/pnpnpn/timeout-decorator) -- documents `use_signals=False` multiprocessing fallback

---

### Pitfall 2: Diagnosing the Hang in the Wrong Pipeline Stage

**What goes wrong:**
You assume the `test.mlir` hang is in the Pygments lexer (because you read about regex backtracking) and spend days optimizing regex patterns. But the actual hang is in layout calculation, Cairo rendering, or Pillow shadow blur. Or vice versa -- you rewrite the shadow system but the lexer was the culprit.

**Why it happens:**
The codepicture pipeline has 4 stages that could hang: lexing (Pygments), layout (LayoutEngine), rendering (Cairo text drawing in a loop), and post-processing (Pillow GaussianBlur). Without profiling, the symptom ("CLI hangs") does not indicate which stage. Developers jump to the most recently-read-about cause.

**Consequences:**
- Days spent fixing the wrong component
- The actual hang remains, eroding confidence
- Possibly introducing bugs in a working component through unnecessary changes

**Prevention:**
1. **Instrument first, fix second.** Add timing to each pipeline stage in `orchestrator.py`:
   ```
   Stage 1: highlight() -- time it
   Stage 2: calculate_metrics() -- time it
   Stage 3: render() -- time it
   Stage 4: apply_shadow() -- time it
   ```
2. Run the instrumented pipeline on `test.mlir` with a process-level timeout (e.g., `timeout 10 python -m codepicture test.mlir`)
3. If the process is killed before any stage completes, the hang is in stage 1. If stage 1 completes but stage 2 does not, the hang is in stage 2. Etc.
4. Use `py-spy dump --pid <PID>` to get a stack trace of a hanging process -- this immediately reveals whether execution is in regex matching, Cairo drawing, or Pillow filtering

**Warning signs:**
- You are "fixing" a component without having confirmed it is the source of the hang
- You added a timeout to lexing but the hang occurs after lexing completes
- Profiling data was not collected before optimization began

**Detection:**
Run `py-spy top --pid $(pgrep -f codepicture)` while the process hangs. The output shows exactly which function is consuming CPU.

**Phase:** First step in v1.1, before any fixes. This is investigation, not implementation.

**Confidence:** HIGH -- based on direct analysis of the codepicture pipeline in `orchestrator.py` (7 sequential stages).

---

### Pitfall 3: Visual Regression Tests That Are Flaky Across Environments

**What goes wrong:**
You generate reference images on macOS, but CI runs on Linux. Font rendering differs between platforms (different font engines: CoreText vs FreeType vs DirectWrite). Anti-aliasing, hinting, and subpixel rendering all vary. Tests pass locally, fail in CI. The team disables the tests.

**Why it happens:**
Font rasterization is platform-dependent by design. Even with the same font file, macOS CoreText and Linux FreeType produce different pixel output. A "pixel-perfect" comparison will always fail across platforms. Cairo surfaces inherit the platform's font backend.

**Consequences:**
- Visual regression tests become untrusted "always-failing" noise
- Developers add `@pytest.mark.skip` or large tolerance thresholds that defeat the purpose
- Real regressions slip through because tests are ignored

**Prevention:**
1. **Generate reference images in the same environment as CI.** Use a Docker container with a fixed Linux + font configuration. Never commit reference images generated on macOS if CI runs Linux.
2. **Use perceptual comparison, not pixel-perfect.** Libraries like `pixelmatch` support anti-aliasing detection and configurable thresholds. Use `allowedMismatchedPixelRatio` (percentage-based) rather than fixed pixel counts.
3. **Bundle fonts.** Codepicture already bundles fonts (JetBrains Mono) -- ensure the test pipeline uses only bundled fonts, never system fonts.
4. **Pin the rendering environment.** Specify exact versions of Cairo, Pango, FreeType, HarfBuzz in CI. Font rendering can change between library versions.
5. **Test at component level, not just full-image.** Compare the code area separately from the chrome/shadow. This isolates failures.

**Warning signs:**
- Reference images committed from a developer's Mac
- CI failures on "visual regression" that nobody investigates
- Tolerance threshold set above 5% (effectively disabling the test)
- Different developers getting different results locally

**Detection:**
- Run the same test on two different machines. If results differ, the environment is not controlled.
- Check if reference images have platform-specific metadata (e.g., macOS color profiles)

**Phase:** Design the visual regression approach BEFORE generating reference images. This is architectural, not incremental.

**Confidence:** HIGH -- this is the most commonly reported pitfall in visual regression testing across all sources surveyed.

**Sources:**
- [Playwright visual tests with Git LFS and Docker](https://medium.com/@adam_pajda/playwright-visual-tests-with-git-lfs-and-docker-d537ddd6e86a) -- environment consistency
- [Base Web visual regression testing](https://baseweb.design/blog/visual-regression-testing/) -- CI workflow patterns
- [pixelmatch-py](https://github.com/whtsky/pixelmatch-py) -- anti-aliasing aware comparison

---

### Pitfall 4: Reference Image Bloat in Git History

**What goes wrong:**
You commit 50+ PNG reference images (each 100KB-500KB at 2x HiDPI) directly to Git. Every time a legitimate rendering change occurs (font update, padding tweak), all reference images are regenerated and recommitted. The repo balloons to hundreds of MB. Clone times increase. `git blame` becomes slow.

**Why it happens:**
Git stores every version of every binary file. Unlike text files, binary diffs are not compressible. A "small" set of 50 reference images updated 10 times creates 500 stored blobs.

**Consequences:**
- Repo size grows 50-200MB per reference image update cycle
- CI clone times increase from seconds to minutes
- Developers avoid updating reference images because the diff is "too large to review"
- PR reviews become painful (GitHub cannot diff PNGs meaningfully in standard view)

**Prevention:**
1. **Use Git LFS** for reference images. Track `tests/**/*.png` with LFS. This keeps the repo lean and stores images externally.
2. **Minimize reference image count.** Test representative cases, not exhaustive ones. 10-15 well-chosen reference images cover more than 50 random ones.
3. **Use small image dimensions for tests.** Test images do not need to be presentation-quality. Use minimal padding, short code snippets, 1x scale (not 2x).
4. **Provide an update command.** `pytest --update-snapshots` or a Makefile target that regenerates reference images. Make updating easy so developers do not avoid it.
5. **Review image changes with GitHub's image comparison tools** (swipe, onion skin, side-by-side). Document this in CONTRIBUTING.md.

**Warning signs:**
- `git clone` takes over 30 seconds
- PRs with "updated reference images" have 20MB+ of binary diffs
- Developers are afraid to touch rendering code because of the image update burden

**Phase:** Set up Git LFS tracking BEFORE committing the first reference image.

**Confidence:** HIGH -- well-documented problem across visual testing literature.

**Sources:**
- [Git LFS for Playwright visual tests](https://medium.com/@adam_pajda/playwright-visual-tests-with-git-lfs-and-docker-d537ddd6e86a)
- [Visual Git baseline management](https://www.browserstack.com/docs/percy/baseline-management/visual-git)

---

## Moderate Pitfalls

Mistakes that cause delays or technical debt but are recoverable.

### Pitfall 5: Profiling the Wrong Thing (Wall Time vs CPU Time vs IO)

**What goes wrong:**
You profile with `cProfile` and find that `apply_shadow()` takes 200ms. You optimize the blur. But the actual user-perceived bottleneck was `register_bundled_fonts()` being called on every invocation (disk I/O), or Pygments lexer discovery iterating all 500+ lexers. The profile was correct but you optimized the wrong metric.

**Why it happens:**
`cProfile` measures CPU time by default, which misses I/O waits. Also, developers profile with small inputs where all stages are fast, then extrapolate. A 200ms blur on a 10-line snippet becomes 2000ms on a 200-line file, but font registration stays constant.

**Prevention:**
1. **Profile with realistic inputs** -- use actual files the user cares about (like `test.mlir` or a 200-line Python file)
2. **Measure wall time per stage** first (simple `time.perf_counter()` around each stage), then drill into the slowest stage with `cProfile` or `line_profiler`
3. **Profile the full pipeline** including startup, not just the rendering hot path
4. **Set a performance budget** before optimizing: "Rendering a 100-line file should complete in under 500ms." Then measure whether you meet it.
5. **Use `py-spy`** for sampling-based profiling that includes C extensions and has lower overhead than `cProfile`

**Warning signs:**
- You optimized a function but end-to-end time did not improve
- Profile was collected on a 5-line test file
- "Rendering is fast" but CLI startup takes 400ms

**Phase:** Profile BEFORE optimizing. Collect baseline metrics at the start of the performance phase.

**Confidence:** HIGH -- standard profiling best practice.

**Sources:**
- [Python Profilers documentation](https://docs.python.org/3/library/profile.html)
- [Real Python profiling guide](https://realpython.com/python-profiling/)

---

### Pitfall 6: Pillow GaussianBlur Scaling Surprise at 2x HiDPI

**What goes wrong:**
Shadow rendering is fast in tests (small images) but slow in production. The codepicture pipeline renders at 2x scale for HiDPI PNG output. A 800x600 logical image becomes 1600x1200 pixels. Pillow's `GaussianBlur` operates on the full pixel dimensions. The blur with `radius=50` on a 1600x1200 RGBA image processes 7.68 million pixels. At 4 bytes per pixel, that is 30MB of data being convolved.

**Why it happens:**
The 2x scale factor is applied at surface creation (`CairoCanvas.create` with `scale=2.0`). The shadow module receives the raw surface dimensions (`surface.get_width()` returns the physical pixel count, not logical). The blur radius was chosen for logical coordinates but is applied to physical pixels.

**Consequences:**
- Shadow rendering takes 200-500ms for typical files, possibly seconds for large files
- Users perceive codepicture as "slow" when shadows are enabled
- Disabling shadows makes it fast, creating a poor default experience

**Prevention:**
1. **Downscale before blur, upscale after.** Blur at 1x resolution, then composite at 2x. Shadow does not need full HiDPI resolution -- it is inherently soft.
2. **Or: Adjust blur radius for scale.** If rendering at 2x, the blur radius is already effectively doubled. Use `radius / scale` to maintain the same visual appearance.
3. **Benchmark the shadow path** with `time.perf_counter()` around `apply_shadow()` using a realistic (200+ line) input file at 2x scale.
4. **Consider pre-computing shadow.** For a fixed corner radius and shadow style, the shadow shape is the same for every render -- only the dimensions change. A cached shadow mask could be scaled per-render.

**Warning signs:**
- `apply_shadow()` appears as top function in profile
- Shadow-enabled renders are 3x+ slower than shadow-disabled
- Users pass `--no-shadow` to get acceptable speed

**Phase:** Performance optimization phase, after profiling confirms shadow is a bottleneck.

**Confidence:** MEDIUM -- based on analysis of the existing `shadow.py` code and Pillow performance characteristics. The actual impact depends on typical image dimensions.

---

### Pitfall 7: Testing Timeouts with Synthetic Delays Instead of Real Pathological Input

**What goes wrong:**
You write a test that uses `time.sleep(10)` to simulate a slow operation, verify that the timeout triggers, and ship it. In production, the actual hang is a C-level regex backtrack that `signal.SIGALRM` cannot interrupt (see Pitfall 1). The test passes; the feature is broken.

**Why it happens:**
`time.sleep()` is a Python-level call that yields to the signal handler. It tests the timeout mechanism's Python-level behavior, not its ability to interrupt C extensions. The test is correct but tests the wrong thing.

**Prevention:**
1. **Test with actual pathological input.** For Pygments, this means strings known to trigger catastrophic backtracking (e.g., `"a" * 1000` for certain lexer patterns, or the actual `test.mlir` content).
2. **Test with a subprocess-based timeout** and verify the subprocess is killed, not just interrupted.
3. **Include an integration test** that runs the full CLI with the known-hanging input and asserts it completes within N seconds.
4. **Keep `test.mlir` (and any other hanging inputs) as test fixtures** -- they are regression tests for the timeout mechanism itself.

**Warning signs:**
- All timeout tests use `time.sleep()` or `unittest.mock.patch`
- No test uses actual pathological input
- The test suite never exercises the timeout kill path

**Phase:** When implementing timeouts. Write the test with real input FIRST, then implement the timeout to make it pass.

**Confidence:** HIGH -- directly follows from Pitfall 1.

---

### Pitfall 8: Over-Engineering the Visual Regression Framework

**What goes wrong:**
You build a custom visual regression framework with diff image generation, HTML reports, automatic baseline updating, threshold configuration per test, and LFS integration. This takes 2-3 weeks. Meanwhile, the actual rendering bugs (the `test.mlir` hang, layout issues with real files) remain unfixed.

**Why it happens:**
Visual regression testing is a well-documented domain with many sophisticated approaches. It is tempting to build the "right" solution upfront. But codepicture has 260 tests and zero visual regression -- any visual testing is an improvement over none.

**Prevention:**
1. **Start with the simplest possible approach.** Generate a PNG, compare it byte-for-byte (or with a small pixel tolerance) against a checked-in reference. Use `pytest-image-snapshot` or even just Pillow's `ImageChops.difference()`.
2. **Limit initial reference image count.** Start with 5-8 reference images covering: Python, Rust, C++, JavaScript, MLIR (the stated core languages), plus edge cases (empty input, very long lines, unicode).
3. **Add sophistication only when needed.** If byte comparison is too flaky, add perceptual comparison. If reference management is painful, add LFS. Do not pre-build infrastructure for problems you have not yet encountered.
4. **Fix the rendering bugs first.** Visual regression tests are most valuable AFTER the rendering is correct. Testing broken rendering just locks in broken behavior.

**Warning signs:**
- More than 1 week spent on test infrastructure before any rendering bug is fixed
- Custom framework code exceeds the code it is testing
- Discussion of "the right way to do visual regression" delays actual testing

**Phase:** Visual regression should be the SECOND focus in v1.1, after rendering bug fixes.

**Confidence:** HIGH -- based on project context (v1.1 goals are fix bugs first, then add regression tests).

---

### Pitfall 9: Regex Fix for MLIR Lexer Introduces New Backtracking

**What goes wrong:**
To fix the `test.mlir` hang, you modify the MLIR lexer regex patterns. The new patterns fix the specific hanging input but introduce new backtracking risks on different inputs. Without systematic testing, the fix is a regression waiting to happen.

**Why it happens:**
Regex backtracking is notoriously difficult to reason about. A pattern that looks correct and passes 100 test cases can catastrophically backtrack on case 101. The relationship between pattern complexity and worst-case performance is not intuitive.

**Prevention:**
1. **Understand the root cause before changing regexes.** Is the hang in the MLIR lexer specifically, or in Pygments' generic lexer machinery?
2. **Test regex changes against a corpus.** Collect 10+ MLIR files of varying complexity. Run the lexer on each with a timeout. All must complete within 1 second.
3. **Use possessive quantifiers or atomic groups where possible.** Python's `re` module does not support these, but you can restructure patterns to avoid ambiguity. For example, the pattern `%[\w\.\$\:\#]+` in the current MLIR lexer includes `\.` which overlaps with the dialect.op pattern `[a-zA-Z_][\w]*\.[\w\.\$\-]+`. This overlap can cause the lexer to try multiple paths.
4. **Consider using the `regex` module** (PyPI) which supports atomic groups and possessive quantifiers, preventing backtracking.
5. **Add a fuzzing test** that generates random strings and verifies the lexer completes within a timeout.

**Warning signs:**
- Changing one regex pattern to fix a specific input
- No corpus of MLIR test files
- Lexer tests only check that tokens are correct, not that lexing completes quickly

**Detection:**
Run `lexer.get_tokens("a" * 1000)` and similar degenerate inputs. If any take more than 100ms, there is a backtracking risk.

**Phase:** When fixing the `test.mlir` hang. Regex changes must be accompanied by performance tests.

**Confidence:** HIGH -- multiple Pygments issues document this exact pattern (fix one backtrack, introduce another).

**Sources:**
- [Pygments lexer development docs](https://pygments.org/docs/lexerdevelopment/) -- "Beware of so-called catastrophic backtracking"
- [Pygments Issue #1065](https://github.com/pygments/pygments/issues/1065) -- JSON lexer backtracking fix that needed multiple iterations
- [Pygments Issue #2053](https://github.com/pygments/pygments/issues/2053) -- Elpi lexer pathological backtracking on simple input

---

## Minor Pitfalls

Mistakes that cause annoyance but are quickly fixable.

### Pitfall 10: Reference Images with Embedded Timestamps or Random Data

**What goes wrong:**
Reference images differ on every run even though the rendering is identical. PNG metadata (creation date, software version) or Cairo surface metadata changes between runs. Byte-for-byte comparison fails; perceptual comparison passes.

**Prevention:**
Strip metadata from reference images before comparison, or use image-content-only comparison (decode PNG to pixels, compare pixel data). Pillow's `Image.tobytes()` gives raw pixel data without metadata.

---

### Pitfall 11: Performance Benchmarks Without Statistical Rigor

**What goes wrong:**
You run the pipeline once, note "200ms", optimize, run again, note "180ms", and declare a 10% improvement. But run-to-run variance is 50ms. The "improvement" is noise.

**Prevention:**
Run benchmarks 10+ times. Report median and standard deviation. Use `timeit` or `pytest-benchmark` for statistical significance. Only claim improvement when the difference exceeds 2 standard deviations.

---

### Pitfall 12: Forgetting That `test.mlir` Is Only 15 Lines

**What goes wrong:**
The `test.mlir` file that causes the hang is only 15 lines. If the hang is in the lexer, it means the regex issue is triggered by specific content patterns (like `#hal.device.topology<links = [...]>` with nested angle brackets and attribute syntax), not by file size. You might focus on "large file handling" when the problem is specific syntax patterns.

**Prevention:**
Read the actual content of `test.mlir` carefully. Look for patterns that are problematic for regex: nested brackets, backtracking-prone repetitions, long attribute values with mixed punctuation. The `#hal.device.affinity<@device_b>` pattern involves `#`, `.`, `<`, `>`, and `@` characters that interact with multiple lexer rules simultaneously.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|---|---|---|
| Diagnosing `test.mlir` hang | Assuming it is the lexer without profiling (Pitfall 2) | Instrument pipeline stages first |
| Adding timeouts | Signal-based timeout cannot interrupt C extensions (Pitfall 1) | Use subprocess-based timeout |
| Fixing MLIR lexer regexes | New patterns introduce new backtracking (Pitfall 9) | Test with corpus + fuzzing |
| Building visual regression tests | Cross-platform font rendering differences (Pitfall 3) | Generate references in CI environment |
| Storing reference images | Git repo bloat (Pitfall 4) | Use Git LFS from the start |
| Reference image comparison | Metadata causes false failures (Pitfall 10) | Compare pixel data only |
| Performance profiling | Profiling wrong metric or wrong input (Pitfall 5) | Profile realistic inputs, wall time first |
| Shadow optimization | 2x HiDPI multiplies blur cost (Pitfall 6) | Downscale before blur |
| Timeout testing | Synthetic delays do not test real hangs (Pitfall 7) | Use actual pathological input as test fixture |
| Test infrastructure | Over-engineering delays bug fixes (Pitfall 8) | Start minimal, fix bugs first |

## Recommended v1.1 Ordering Based on Pitfalls

Based on the pitfall analysis, the v1.1 work should proceed in this order:

1. **Diagnose first** -- Instrument the pipeline, profile `test.mlir`, identify which stage hangs (avoids Pitfall 2)
2. **Fix the hang** -- Apply the correct fix based on diagnosis; if lexer, fix regexes WITH corpus testing (avoids Pitfall 9)
3. **Add timeout protection** -- Use subprocess-based timeout, not signal-based (avoids Pitfall 1); test with real pathological input (avoids Pitfall 7)
4. **Run against real files** -- Test diverse source files, fix rendering issues discovered
5. **Add visual regression** -- Start simple, generate references in CI environment (avoids Pitfalls 3, 4, 8)
6. **Profile and optimize** -- Profile with realistic inputs, optimize confirmed bottlenecks (avoids Pitfalls 5, 6)

This ordering ensures each phase builds on confirmed understanding rather than assumptions.

---

## Sources

- [Python signal documentation](https://docs.python.org/3/library/signal.html) -- C extension signal handling limitations
- [Pygments Issue #2356](https://github.com/pygments/pygments/issues/2356) -- Catastrophic backtracking in Java properties lexer
- [Pygments Issue #2355](https://github.com/pygments/pygments/issues/2355) -- SQL lexer catastrophic backtracking
- [Pygments Issue #2053](https://github.com/pygments/pygments/issues/2053) -- Elpi lexer pathological backtracking
- [Pygments Issue #1065](https://github.com/pygments/pygments/issues/1065) -- JSON lexer backtracking
- [Pygments lexer development guide](https://pygments.org/docs/lexerdevelopment/) -- Catastrophic backtracking warning
- [timeout-decorator](https://github.com/pnpnpn/timeout-decorator) -- Signal vs subprocess timeout strategies
- [pytest-timeout](https://pypi.org/project/pytest-timeout/) -- Test timeout plugin
- [pixelmatch-py](https://github.com/whtsky/pixelmatch-py) -- Perceptual image comparison
- [pytest-image-snapshot](https://github.com/bmihelac/pytest-image-snapshot) -- Snapshot testing for images
- [Playwright visual tests with Docker](https://medium.com/@adam_pajda/playwright-visual-tests-with-git-lfs-and-docker-d537ddd6e86a) -- Environment consistency
- [Base Web visual regression](https://baseweb.design/blog/visual-regression-testing/) -- CI workflow patterns
- [Python Profilers docs](https://docs.python.org/3/library/profile.html) -- cProfile and profiling best practices
- [Real Python profiling guide](https://realpython.com/python-profiling/) -- Profiling workflow
- [Pillow performance](https://python-pillow.github.io/pillow-perf/) -- GaussianBlur implementation details
- [Pycairo Issue #239](https://github.com/pygobject/pycairo/issues/239) -- Large surface memory issues

---
*Pitfalls research for: codepicture v1.1 Reliability, Visual Regression & Performance Hardening*
*Researched: 2026-01-30*
