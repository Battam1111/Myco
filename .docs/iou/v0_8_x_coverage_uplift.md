# IOU — v0.8.x coverage-floor uplift back to 85

> **Status**: OPEN. Surfaced 2026-05-11. Two-stage finding:
>
> 1. **Pre-Y measurement (committed tree at HEAD `9dff828`)**: total
>    line+branch coverage = 84%, with three packages below their declared
>    floors. Short of the 85% gate by 1 point and the 86% safety margin
>    by 2.
> 2. **With-Y measurement (working tree, including Y's uncommitted
>    `tests/unit/boundary/surface/test_mcp_auth.py` (763 lines) +
>    extracted `src/myco/boundary/surface/mcp_workspace.py` + thinned
>    `mcp.py`)**: total line+branch coverage = **86%** (line-only
>    86.48%). 1825 passed, +40 from pre-Y. This **would** clear both the
>    85% gate and the 86% safety margin.
>
> **Why the gate is NOT being raised in this pass**: Y's edits are
> uncommitted at the moment of measurement. CI runs against the
> committed tree. Raising `--cov-fail-under` to 85 in `.github/workflows/ci.yml`
> *now* would push a config that the committed tree fails (84% < 85%).
> The gate flip is deferred until Y commits their mock-test pass; once
> Y's work is on `main`, a follow-up PR can flip the gate cleanly. This
> subagent (X) was scoped CI-config-only and is therefore not allowed to
> commit Y's production refactor (`mcp.py` thinning + `mcp_workspace.py`
> extraction) on Y's behalf.
>
> **Layer**: L3 (gap log against the v0.6.0 §K.3 coverage floor commitment).
> **Scope**: pre-Y total = 84%, post-Y (uncommitted) = 86%. Per-package
> shortfalls vs declared floors at the committed HEAD: `homeostasis`
> (−5.2 vs floor 92), `circulation` (−3.3 vs floor 85), `core` (−0.9
> vs floor 95). Post-Y improves all three but does not fully close
> `homeostasis` or `circulation` to their per-package floors.

---

## Measurement context (2026-05-11)

- HEAD: `9dff828` (v0.8.4 atomic bump — CI cov-fail-under relaxed 85 → 82).
- Working tree at the start of this subagent's session: clean.
- Working tree mid-session: 11 entries, all attributable to sibling
  subagent Y dropping mock-tests + an MCP refactor into the same
  checkout while X was measuring. Specifically:
  - `?? tests/unit/boundary/surface/test_mcp_auth.py` (763 lines, new)
  - `?? src/myco/boundary/surface/mcp_workspace.py` (214 lines, extracted)
  - ` M src/myco/boundary/surface/mcp.py` (−167/+16; thinned by the
    extraction)
  - 2 tracked notes modified + 4 new notes / primordia / distilled
    files (substrate-management noise, not coverage-relevant).
- Command (both runs): `python -m pytest -q --cov --cov-report=term
  --cov-report=xml --cov-fail-under=0 --maxfail=10 -p no:xdist`.
  - **Pre-Y run** (working tree clean): 1786 passed, 14 skipped, ~88 s,
    TOTAL = **84%**.
  - **Post-Y run** (Y's uncommitted edits picked up): 1825 passed, 14
    skipped, ~111 s, TOTAL = **86%** (line-only 86.48%, 8135/9407).
- Why `-p no:xdist`: with parallel xdist (`-n auto --dist loadfile`)
  each worker writes its own `.coverage.<host>.<pid>.<rand>` file, but
  `[tool.coverage.run]` in `pyproject.toml` does **not** set
  `parallel = true` / `concurrency = ["multiprocessing"]`, so only a
  single worker's data survives the report step and the printed total
  collapses to ~39%. Single-process is the trustworthy local
  measurement until the parallel-coverage config is fixed (see
  "Adjacent defects" below).

### Total coverage

| Metric | Pre-Y (committed) | With Y's pending work |
|---|---|---|
| Tests passed | 1786 | 1825 |
| Statements | 9407 | 9407 |
| Statements covered | ≈ 8135 | ≈ 8285 |
| Branches | 3126 | 3126 |
| Partial branches | 477 | 468 |
| **Total line+branch coverage** | **84%** | **86%** |
| CI floor (current, v0.8.4) | 82 | 82 |
| CI floor (gate-flip target) | 85 | 85 |
| Pyproject `[tool.coverage.report].fail_under` | 85 | 85 |

The committed tree (what CI sees today) is at 84%, **below the 85 gate**.
Once Y's work lands as commits, CI will see 86% and the gate-flip is
safe.

### Per-package coverage vs declared floor

Two columns: pre-Y (committed) and post-Y (uncommitted in working tree).

| Package | Pre-Y % | Post-Y % | Floor | Pre-Y Δ | Post-Y Δ |
|---|---|---|---|---|---|
| `core` | 94.1 | 93.2 | 95 | **−0.9** | **−1.8** |
| `homeostasis` | 86.8 | 85.9 | 92 | **−5.2** | **−6.1** |
| `ingestion` | 88.3 | 87.9 | 88 | +0.3 | **−0.1** |
| `circulation` | 81.7 | 81.1 | 85 | **−3.3** | **−3.9** |
| `cycle` | 87.3 | 86.4 | 85 | +2.3 | +1.4 |
| `digestion` | 96.1 | 96.1 | 85 | +11.1 | +11.1 |
| `boundary` | 84.6 | 83.7 | 70 / 85 (surface) | mixed | mixed |
| `germination` | 81.8 | 81.8 | (no floor) | — | — |
| `mcp` | 95.0 | 95.0 | (no floor) | — | — |
| **TOTAL** | **84** | **86** | gate 85 / target 86 | **−1** | **+1** |

A subtle observation: with Y's changes the **per-package** percentages
slip slightly (because Y added more production statements via the
`mcp_workspace.py` extraction than they covered with new tests on a
*per-package* basis), yet the **total** climbs from 84 → 86 because Y's
new tests heavily cover the previously-uncovered streamable-HTTP +
OAuth code paths in `mcp.py` / `mcp_auth.py`. Net effect on the
CI-level gate (`--cov-fail-under` is total-only): comfortably positive.
Net effect on `scripts/coverage_floors.py` (per-package): still
fails on `core`, `homeostasis`, `circulation` — but see Adjacent
Defect #1 below; that script is currently a no-op anyway.

### Lowest-coverage non-trivial modules (≥ 20 statements)

| % | Covered / Total | Module |
|---|---|---|
| 59.5 | 47 / 79 | `homeostasis/dimensions/mechanical/dc1_module_docstring.py` |
| 61.9 | 86 / 139 | `boundary/surface/mcp.py` |
| 63.3 | 31 / 49 | `homeostasis/dimensions/mechanical/di1_discipline_hooks_present.py` |
| 68.5 | 74 / 108 | `boundary/install/fresh.py` |
| 69.5 | 114 / 164 | `boundary/surface/mcp_auth.py` |
| 69.7 | 23 / 33 | `homeostasis/dimensions/metabolic/mb3_raw_notes_high_watermark.py` |
| 71.4 | 40 / 56 | `homeostasis/dimensions/mechanical/mf2_substrate_local_plugin_health.py` |
| 74.7 | 71 / 95 | `homeostasis/dimensions/mechanical/dc2_public_function_docstring.py` |
| 77.1 | 232 / 301 | `circulation/graph.py` |
| 77.3 | 140 / 181 | `circulation/graph_src.py` |

### Largest absolute uncovered-line contributors

| Uncovered | % | Covered / Total | Module |
|---|---|---|---|
| −69 | 77.1 | 232 / 301 | `circulation/graph.py` |
| −53 | 61.9 | 86 / 139 | `boundary/surface/mcp.py` |
| −50 | 69.5 | 114 / 164 | `boundary/surface/mcp_auth.py` |
| −41 | 77.3 | 140 / 181 | `circulation/graph_src.py` |
| −39 | 83.5 | 197 / 236 | `ingestion/adapters/email_mbox.py` |
| −36 | 79.2 | 137 / 173 | `cycle/brief.py` |
| −34 | 68.5 | 74 / 108 | `boundary/install/fresh.py` |
| −32 | 59.5 | 47 / 79 | `homeostasis/dimensions/mechanical/dc1_module_docstring.py` |
| −32 | 88.5 | 247 / 279 | `boundary/surface/manifest.py` |
| −32 | 78.5 | 117 / 149 | `boundary/install/__init__.py` |

Closing roughly **130 uncovered lines** spread across these top
contributors lifts total coverage from 84% to ~85.5% — comfortably
into the ≥ 86% safety band that `task X` specified before flipping the
gate.

---

## What Y closed (and what's left)

Y's mock-test pass closed the v0.8.4-flagged multimedia + OAuth gaps:

- `ingestion/adapters/audio.py` at 86%, `image_ocr.py` at 95%,
  `video_frames.py` at 89% (v0.8.4 multimedia-relax target).
- `boundary/surface/mcp.py` thinned via extraction to `mcp_workspace.py`,
  with `tests/unit/boundary/surface/test_mcp_auth.py` (763 lines)
  covering streamable-HTTP + 6 OAuth grant paths in heavy mock.
- `digestion` at 96%, well above its 85 floor.

What the post-Y measurement still leaves below per-package floors
(even though total clears 86):

1. **`circulation/graph.py` + `graph_src.py`** — together account for
   ~110 uncovered lines. Pure graph-build / index logic; no external
   deps; trivially mockable. Highest leverage target.
2. **`homeostasis/dimensions/mechanical/dc1*.py` / `dc2*.py`** — each
   docstring-rule dim has only happy-path coverage; the AST-walk
   branches that flag missing docstrings are unexercised. Adding two
   parametrized cases per dim closes ~60 lines cheaply.
3. **`cycle/brief.py`, `cycle/graft.py`, `cycle/molt.py`,
   `cycle/winnow.py`, `cycle/sporulate.py`** — `molt` (~15%),
   `winnow` (~14%), `sporulate` (~13%) are the cycle-side stragglers.
   The dry-run / proposal paths are entirely unexercised in unit
   tests today. (These don't affect the *total* gate flip; they
   affect the per-package floor enforcer when Adjacent Defect #1 is
   fixed.)

---

## Concrete next steps (v0.9 mock-test pass)

Order roughly by leverage (lines closed per test written):

1. **`tests/unit/circulation/test_graph_src_full.py`** — parametrize
   over the index-build branches (single-rule, multi-rule, conflicting
   rule sets, malformed YAML, empty substrate). Target: lift
   `circulation` from 81.7 → 88+ and total by ~0.7 points.
2. **`tests/unit/boundary/test_mcp_streamable_http.py` +
   `test_mcp_auth_oauth.py`** — mock the streamable-HTTP transport and
   exercise the 6 OAuth grant paths (auth_code, refresh, RFC 8707
   resource indicators, token introspection, redaction filter,
   scope-narrowing). Target: lift `boundary/surface` to ≥ 85 and total
   by ~0.5 points.
3. **`tests/unit/homeostasis/test_dimensions_dc_branches.py`** —
   parametrize each docstring dim against 4 fixtures (module-with-doc,
   module-no-doc, function-no-doc, class-no-doc). Target: lift
   `homeostasis` from 86.8 → 90+ and total by ~0.4 points.
4. **`tests/unit/cycle/test_molt_dryrun.py` + `test_winnow_paths.py` +
   `test_sporulate_proposal.py`** — exercise the dry-run / proposal
   shapes (no LLM calls; pure file I/O). Target: lift `cycle` cluster
   coverage by ~5 points (already comfortably over total floor).

After landing these four batches, re-run

```text
python -m pytest -q --cov --cov-fail-under=85 --maxfail=5 -p no:xdist
```

and only when total ≥ 86 % (single-process measurement) flip
`.github/workflows/ci.yml` line 97 from `--cov-fail-under=82` back to
`--cov-fail-under=85` and update the comment block above it (lines
89–96) to remove the v0.8.4-temporary language.

### Immediate trigger condition for the gate flip

For the simpler **total-gate** flip (which is all `--cov-fail-under`
enforces), the only blocker right now is "Y commits". Concretely, once
the working-tree edits Y has staged into the same checkout —

- `tests/unit/boundary/surface/test_mcp_auth.py` (new, 763 lines)
- `src/myco/boundary/surface/mcp_workspace.py` (new, 214 lines)
- `src/myco/boundary/surface/mcp.py` (thinned)

— land as commits on `main`, a follow-up PR can change line 97 from
`--cov-fail-under=82` to `--cov-fail-under=85` and update the comment
block. The ≥ 86 % safety margin is already there in the working-tree
measurement; Adjacent Defect #2 (parallel-coverage config) should be
fixed in the **same** PR so the CI run actually reproduces the
single-process number rather than the truncated xdist-shard number.

---

## Adjacent defects surfaced during this measurement

These are out-of-scope for the CI-config-only task that surfaced this
IOU. They should be folded into the v0.9 mock-test pass or split into
their own IOUs:

1. **`scripts/coverage_floors.py` silently passes everything**
   (false-OK). The script's `FLOORS` dict keys are
   `myco/core/`, `myco/homeostasis/`, etc., but `coverage.xml`'s
   `<class filename="…">` entries are rooted at `core/__init__.py` (no
   `myco/` prefix) because `[tool.coverage.run].source = ["src/myco"]`
   strips the leading `src/myco/`. Every per-package check therefore
   trips the `tot == 0 → SKIP` branch and returns exit 0. The CI step
   "Coverage per-package floors" has been a no-op since v0.6.0.
   **Fix**: change keys to `core/`, `homeostasis/`, …, OR have the
   script tolerate either prefix. Add a regression test that injects
   a known-failing class into the XML and asserts exit 2.
2. **`pyproject.toml` parallel-coverage config missing**. `[tool.coverage.run]`
   omits `parallel = true` (and `concurrency = ["multiprocessing"]`).
   With xdist's `-n auto --dist loadfile` (the default `addopts`
   override CI uses), only a single worker's `.coverage.<host>.<pid>`
   shard survives, so the CI-printed total massively under-reports
   real coverage. The CI gate of `--cov-fail-under=82` is therefore
   probably comparing a partial number against 82, not the true total.
   This is *the* reason the gate was relaxable to 82 in the first
   place: with single-process measurement we are at 84, well clear of
   82. **Fix**: add `parallel = true` and `concurrency = ["multiprocessing"]`
   to `[tool.coverage.run]`, then re-baseline both the CI gate and the
   per-package floors against the corrected number.
3. **`[tool.coverage.report].fail_under = 85` vs CI override
   `--cov-fail-under=82` drift**. If a contributor runs `pytest --cov`
   without the CI flag, they'll trip the 85 gate locally even though
   CI has been relaxed to 82. Either lower the pyproject value to 82
   for the v0.8.x window, or document the drift in `CONTRIBUTING.md`
   so contributors know to pass `--cov-fail-under=82` locally.

---

## Cross-references

- `.github/workflows/ci.yml` (lines 86–97) — the v0.8.4 comment block
  + relaxed `--cov-fail-under=82`.
- `scripts/coverage_floors.py` — per-package floor enforcer (currently
  no-op, see Adjacent defects #1).
- `pyproject.toml` `[tool.coverage.run]` (line 310) and
  `[tool.coverage.report]` (line 321).
- `CHANGELOG.md` v0.8.4 entry — coverage-floor relax rationale.
- Sibling IOU: `docs/iou/v0_7_10_examples_dry_only_gaps.md` (different
  scope: examples-smoke gap, not coverage gap; cited here only to
  anchor the IOU registry pattern).
