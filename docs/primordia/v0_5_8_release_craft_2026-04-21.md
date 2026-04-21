---
type: craft
topic: v0_5_8_release
slug: v0_5_8_release
kind: audit
date: 2026-04-21
rounds: 3
craft_protocol_version: 1
status: APPROVED
---

# V0.5.8 Release — Craft

> **Date**: 2026-04-21
> **Layer**: L3 (release engineering) + governance.
> **Upward**: L1 R6 (write-surface) gets the first mechanical fence
> (new `write_surface.py` helper) and R2 discipline gets a direct
> lint anchor (`DI1`). Every L0 principle gets at least one new
> mechanical signal via the 14-dim expansion.
> **Governs**: the v0.5.8 release artefact — package on PyPI, git
> tag `v0.5.8`, GitHub release notes, and the bundled doctrine /
> code / test updates.

---

## Round 1 — 主张 (claim)

**Claim**: v0.5.8 is a **cleanup release** that shares the shape of
v0.5.6 (panoramic doctrine + mechanical alignment) but trades
subsystem-scope invariants (MP1 was narrow) for surface-scope
invariants (14 dims touching purity, documentation, contract
hygiene, substrate shape, graph integrity, rule discoverability).
It is simultaneously:

- An audit response (13+ concrete P0/P1 bug fixes from a four-
  iteration opus lens audit).
- A contract cleanup (exit codes differentiated; fresh-substrate
  directories pre-created; contract-sync elevated to lint).
- A doctrine alignment (homeostasis.md + canon_schema.md updated
  to the 25-dim roster).
- A security sweep (.env removed from ingestion, credential
  denylist, adapter size caps, SSRF guard, HTTP streaming abort).
- A foundation bump (four new core helpers ready to be wired into
  every write/read site in v0.5.9).

The load-bearing claim: **this is the last release shippable
without the helpers landing**. v0.5.9+ makes every write flow
through `atomic_utf8_write` and every trust boundary through
`trust.safe_*`. v0.5.8 lands the helpers themselves, wires them at
the highest-leverage sites, and ships.

## Round 1.5 — 自我反驳 (self-rebuttal)

- **T1**: Cleanup releases are historically forgettable — they
  don't add user-visible features, so adoption is slow, and the
  next feature release obscures the cleanup's intent.
- **T2**: 14 new dimensions + 4 new helpers + 13+ fixes is a lot
  for one release. Bundling them inflates the diff and makes
  cherry-picking hard if any one piece needs to be reverted.
- **T3**: The release is shipping from a single-session multi-
  phase execution (no parallel review). If any fix introduces a
  regression, it was only caught by the existing test suite —
  which we know has gaps (the 14 new dims proves it).
- **T4**: Shipping while `mcp-server-myco.exe` is in use
  (editable-install refresh blocked mid-session) means the
  pushed wheel contains the new entry-points but the live MCP
  server is stale. Fresh installs work; upgrade-in-place sessions
  see the old 11 dims until they restart.

## Round 2 — 修正 (revision)

- **R1** (T1 — cleanup forgettable): v0.5.8 advertises itself as
  a cleanup release in the CHANGELOG and GitHub notes; the
  14-dim expansion is surfaced as the headline. Operators running
  `myco immune --list` immediately see the new set. Adoption is
  driven by the discipline improvement, not by shiny new features.
- **R2** (T2 — bundle inflation): every change is independently
  revertable at the dimension-file level (dimensions are one-per-
  file); every helper sits in its own module; every fix is
  git-traceable to a single line edit. The bundle is structural
  (coherent cleanup theme) not monolithic.
- **R3** (T3 — single-session risk): the test suite grew from
  613 → 668 during the cleanup (55 new tests, ~9 % increase).
  Every new dimension has a happy-path + no-finding + edge-case
  test. The audit's four iterations of opus-lens review are
  themselves a parallel review substitute.
- **R4** (T4 — in-flight upgrade gap): documented in the release
  notes. Users upgrading MCP-attached sessions are instructed to
  restart the MCP server (or run `pip install -e . --force-
  reinstall`) to pick up the new dims. The gap is session-scoped,
  not durable.

## Round 2.5 — 再驳 (counter-rebuttal)

- **T5** (re R2): the foundation helpers (`io_atomic`, `trust`,
  `skip_dirs`, `write_surface`) are shipped but not yet wired
  into every callsite. A revert of the helpers means silently
  breaking the new callsites that do use them. Not clean.
- **T6** (re R3): 55 new tests is short of the aspirational
  "~100 new test files" in the v0.5.8 plan. Coverage of the new
  dims is good; coverage of the new helpers (`atomic_utf8_write`,
  `guarded_write`, …) is thinner. Some paths only exercised via
  the wired callsites.

## Round 3 — 收敛 (convergence)

- **R5** (T5 — helper revert risk): accepted. The release notes
  mark foundation helpers as "wired at the top-N sites for
  v0.5.8; full surface rollout in v0.5.9". A revert of a specific
  helper would reinstate the pre-helper code at the wired sites
  via git history. Not elegant, but doable and documented.
- **R6** (T6 — test coverage of helpers): the helpers have
  existing tests from Phase 5. New wired-site tests exercise the
  helpers transitively (e.g. `test_append_note_*` exercises the
  atomic-write retry loop). v0.5.9 dedicated-helper tests will
  close the direct-coverage gap.

## Decision

Approved. Ship v0.5.8 via:

1. Bump `src/myco/__init__.py::__version__` to `v0.5.8`.
2. Bump `_canon.yaml::contract_version` and
   `synced_contract_version` in lockstep via `myco molt --contract
   v0.5.8` (auto-appends `docs/contract_changelog.md` + increments
   `waves.current`).
3. Commit the tree; tag `v0.5.8`; push.
4. GitHub release notes mirror the CHANGELOG v0.5.8 section.
5. `python -m build` + `twine upload dist/*` to PyPI.

## Mechanism

### Release-gate checklist (every item must be green before `twine upload`)

- `python -m pytest -q` → 668/668 pass.
- `python -m ruff check src tests` → 0 errors.
- `python -m ruff format --check src tests` → 0 files need reformat.
- `python -m mypy src/myco` → 0 errors at the permissive baseline.
- `myco immune --exit-on=mechanical:critical,shipped:critical` → exit 0.
- `python -m build` → wheel + sdist both build.
- `twine check dist/*` → metadata valid.
- `myco winnow docs/primordia/v0_5_8_release_craft_2026-04-21.md` →
  APPROVED status + rounds ≥ 3.
- `myco hunger` → `contract_drift: false`, `raw_backlog: 0`.

### Sequencing rule

Execute verification top-down. Any red light aborts the release;
the failing check is fixed, then the chain restarts from pytest.
No partial ships.

### Post-release

- Watch PyPI / GitHub release for 24 h; a reported regression
  triggers v0.5.9 rollback planning, not a yank (L0 principle 3 —
  forward-evolve, don't rewind).
- Queue v0.5.9 agent-first audit craft for 2026-04-28 (7 days
  post-release) to verify the new dim surface doesn't carry
  hidden noise.

## Why this matters (L0 tie-in)

v0.5.8 is the first release where "discipline enforcement" is
plural — multiple dims carry the load instead of one megadim. The
bitter-lesson pattern (hand-coded list → learned/declarative) is
visible in the skip-dirs unification (3 lists → 1 module), the
foundation helpers (per-site custom writes → shared atomic helper),
and the dim roster (doctrine-enforcement by convention → enforcement
by 14 specific mechanical checks).

Each new dim is a little less trust in the agent remembering, and
a little more trust in the substrate surfacing the signal. That
tradeoff is the craft's thesis and v0.5.8's shipped form.
