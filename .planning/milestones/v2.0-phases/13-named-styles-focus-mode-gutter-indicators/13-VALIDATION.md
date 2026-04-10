---
phase: 13
slug: named-styles-focus-mode-gutter-indicators
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0+ |
| **Config file** | pyproject.toml `[tool.pytest]` section |
| **Quick run command** | `pytest tests/test_highlights.py -x -q` |
| **Full suite command** | `pytest --timeout=60` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_highlights.py tests/test_highlights_integration.py -x -q`
- **After every plan wave:** Run `pytest --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-xx | 01 | 1 | HLSTYL-01, HLSTYL-02, HLSTYL-05 | unit | `pytest tests/test_highlights.py -x -q -k style` | ❌ W0 | ⬜ pending |
| 13-02-xx | 02 | 1 | HLSTYL-03, HLSTYL-04 | unit | `pytest tests/test_highlights.py -x -q -k color` | ❌ W0 | ⬜ pending |
| 13-03-xx | 03 | 2 | HLFOC-01, HLFOC-02, HLFOC-03 | unit+visual | `pytest tests/test_highlights.py -x -q -k focus` | ❌ W0 | ⬜ pending |
| 13-04-xx | 04 | 2 | HLGUT-01, HLGUT-02 | visual | `pytest tests/visual/test_visual_regression.py -x -q -k gutter` | ❌ W0 | ⬜ pending |
| 13-05-xx | 05 | 3 | HLTEST-02, HLTEST-04, HLTEST-06, HLTEST-08 | all | `pytest --timeout=60` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_highlights.py` — extend with style parsing tests, style resolution tests, focus dimming opacity tests
- [ ] `tests/visual/test_visual_regression.py` — add style-specific visual tests (4 baselines)
- [ ] `tests/test_highlights_integration.py` — extend with focus mode and gutter indicator CLI tests
- [ ] Visual reference images for each style (generated during first `--snapshot-update` run)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual quality of gutter indicators | HLGUT-01, HLGUT-02 | Subjective alignment assessment | Run `codepicture snippet.py --highlight '3:add' --highlight '5:remove' -o test.png` and visually inspect indicator positioning |
| Focus dimming readability | HLFOC-03 | Subjective readability judgment | Run `codepicture snippet.py --highlight '3-5:focus' -o test.png` and verify unfocused lines are muted but readable |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
