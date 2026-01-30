# Phase 10: Visual Regression & Reliability - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Automated visual verification of rendering output against reference images, plus parametrized reliability testing across all language/format/config combinations. Reference images are maintained in Git LFS. Unintentional visual changes block CI. All 5 core languages x 3 formats produce valid, visually verified output.

</domain>

<decisions>
## Implementation Decisions

### Reference image workflow
- Store reference images in Git LFS (keeps repo lean, still versioned)
- Cover all three output formats (PNG, SVG, PDF) — not just PNG
- Single set of references (not per-platform), with threshold to handle cross-platform font differences
- Descriptive naming: `python_png_shadow-on_chrome-on.png` — encodes language, format, and toggles in filename
- On failure, generate side-by-side composite image: expected | actual | diff in one file
- Pinned fonts in CI (e.g., JetBrains Mono) to ensure consistent rendering matching references

### Comparison & thresholds
- Global default threshold of 0.1% (strict) with per-test override capability via pytest marker/param
- Always report mismatch percentage in test output, even on pass — useful for tracking drift over time

### Matrix test design
- Dedicated visual fixtures: minimal 5-10 line snippets per language covering key syntax (keywords, strings, comments, numbers)
- Not reusing existing test fixtures — purpose-built for visual verification

### CI integration
- Visual regression tests run as a separate CI job (parallel with unit tests)
- Tests are blocking — failures prevent merge
- Failure artifacts (diff composites, actual outputs) uploaded as GitHub Actions artifacts
- CI job installs pinned font set for consistent rendering

### Claude's Discretion
- Snapshot update mechanism (CLI command vs script)
- Full output only vs full + cropped region checks
- SVG/PDF comparison approach (render-to-PNG vs format-native)
- Comparison algorithm (pixelmatch-style vs SSIM vs hybrid)
- Matrix structure (full cartesian vs curated core + edges)
- pytest parametrize approach
- Exact threshold tuning per format if needed
- Fixture content design per language

</decisions>

<specifics>
## Specific Ideas

- Side-by-side composite for failure artifacts: expected | actual | diff — all in one image for quick inspection
- Mismatch percentage always printed, even on pass, to monitor visual drift over time
- Descriptive filenames encoding the full config: `{language}_{format}_{toggles}.{ext}`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-visual-regression-reliability*
*Context gathered: 2026-01-30*
