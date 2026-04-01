---
phase: 14
slug: theme-integration-documentation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2+ |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/test_highlights.py tests/theme/ -x -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_highlights.py tests/theme/ -x -q`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | HLTHEM-01 | unit | `uv run pytest tests/test_highlights.py -x -k "theme_color"` | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 1 | HLTHEM-02 | unit (parametric) | `uv run pytest tests/theme/test_contrast.py -x` | ❌ W0 | ⬜ pending |
| 14-01-03 | 01 | 1 | HLTHEM-03 | unit | `uv run pytest tests/test_highlights.py -x -k "override"` | ✅ partial | ⬜ pending |
| 14-02-01 | 02 | 2 | HLDOC-01 | manual | Visual inspection of README.md | N/A | ⬜ pending |
| 14-02-02 | 02 | 2 | HLDOC-02 | manual | Visual inspection of README.md | N/A | ⬜ pending |
| 14-02-03 | 02 | 2 | HLDOC-03 | manual + smoke | `bash docs/generate-examples.sh && ls docs/examples/` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/theme/test_contrast.py` — parametric contrast check across all 55 themes (HLTHEM-02)
- [ ] `docs/generate-examples.sh` — example image generation script (HLDOC-03)
- [ ] `docs/examples/` — directory for generated images (HLDOC-03)

*Existing infrastructure covers highlight unit tests and visual regression.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| README documents CLI flags | HLDOC-01 | Content quality requires human review | Verify `--highlight` flag usage, examples, and descriptions in README |
| README documents TOML config | HLDOC-02 | Content quality requires human review | Verify TOML config section has complete copy-paste examples |
| Visual examples show styles | HLDOC-03 | Image quality requires visual inspection | Run `docs/generate-examples.sh`, verify images are clear and representative |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
