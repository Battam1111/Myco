---
type: craft
topic: v0_5_9_release
slug: v0_5_9_release
kind: audit
date: 2026-04-21
rounds: 3
craft_protocol_version: 1
status: APPROVED
---

# V0.5.9 Release — Craft

> **Date**: 2026-04-21
> **Layer**: L3 (release engineering) + governance.
> **Upward**: honors L0 principle 3 (永恒进化 — release cadence is
> normal) and L1 R7 (every release passes a contract molt through
> the same loop).
> **Governs**: the v0.5.9 artefact on PyPI + GitHub.

---

## Round 1 — 主张 (claim)

**Claim**: v0.5.9 is a **cleanup-only release**, not a feature
release. Its two jobs are (a) land the immune-zero baseline from
the [discipline craft](v0_5_9_immune_zero_craft_2026-04-21.md),
(b) ship IDE-level canon validation + the migration guides that
v0.5.8 deferred. Zero contract shape changes. Zero behavioural
breaks at the R1-R7 layer. The load-bearing claim: **a release
whose sole purpose is cleanup has value** — it flattens the
baseline against which the next feature release (v0.6.0) will be
judged for drift.

## Round 1.5 — 自我反驳 (self-rebuttal)

- **T1**: Cleanup releases are discounted by adoption. If nothing
  user-visible changes, downstream substrates won't upgrade.
- **T2**: Two releases in two days (v0.5.8 → v0.5.9 both on
  2026-04-21) looks like overactivity. PyPI consumers will wonder
  if v0.5.8 was ship-broken and v0.5.9 is a hotfix.
- **T3**: The JSON-Schema and migration guides are non-code
  artefacts. They could live in the repo without a release bump.

## Round 2 — 修正 (revision)

- **R1** (T1): CHANGELOG frames v0.5.9 as "no urgency, every
  substrate benefits when you get around to it". Two concrete
  carrots: cleaner lint baseline + IDE canon validation. Adoption
  is slow by design.
- **R2** (T2): Two same-day releases are fine when the second is
  strictly additive. contract_changelog opens with "no contract
  shape changes" so operators understand v0.5.9 is not a hotfix.
- **R3** (T3): JSON-Schema's `$id` URL points at `main`. Without
  a tag, IDEs pulling by URL still work, but there's no pinning.
  Release ties known-state filename to known contract version.
  Migration guide only makes sense if v0.5.9 is a shipped thing.

## Round 2.5 — 再驳 (counter-rebuttal)

- **T4** (re R2): "Additive-only" is credible to a CHANGELOG
  reader. PyPI skimmers see only the version list.
- **T5** (re R1): Immune-zero assumes operators run `myco immune`.
  Most don't; they care whether verbs work.

## Round 3 — 收敛 (convergence)

- **R4** (T4): Accepted; out of our control. GitHub release notes
  cover the clickthrough reader. PyPI-only readers get a clean
  version number.
- **R5** (T5): Accepted. Cleanup primarily serves future-Agent
  readers + maintainers doing drift audits. Operator value is
  real but secondary.

## Decision

Approved. Ship v0.5.9 via the 4-channel loop: main + tag + GitHub
release + PyPI.

## Mechanism

### Release-gate checklist

Every item must be green before `twine upload`:

- `python -m pytest -q` → 755 passing
- `python -m ruff check src tests` + `ruff format --check` → clean
- `python -m mypy src/myco` → 0 errors
- `myco immune` (default `critical` gate) → exit 0
- `myco immune --exit-on=high` → exit 0
- `myco immune` **findings total = 0** (headline claim)
- `myco hunger` → `contract_drift: false`, `raw_backlog: 0`, empty reflex
- `python -m build` → wheel + sdist
- `twine check dist/*` → PASSED × 2
- `jsonschema`-validate live `_canon.yaml` against schema → OK

### Sequencing

Top-down verification. Red light aborts the release.

### Post-release

- Monitor PyPI / GitHub for 24 h.
- Regression path: v0.5.10 (no PyPI yanks — L0 principle 3 says
  forward-evolve).
- Queue v0.6.0 design craft ~2 weeks out.

## Governing crafts

- [v0.5.9 Immune Zero craft](v0_5_9_immune_zero_craft_2026-04-21.md)
- [v0.5.8 Release craft](v0_5_8_release_craft_2026-04-21.md)

## Why this matters (L0 tie-in)

v0.5.9 is the discipline-by-example release: it demonstrates that
Myco can ship a "nothing changes at contract layer, only noise
drops" release without pretending it's a feature release. The
Agent reading the CHANGELOG understands cleanup as a first-class
release shape. Sclerosis (L0 principle 3's opposite) is averted
not by feverish feature additions but by regular baseline
flattening.
