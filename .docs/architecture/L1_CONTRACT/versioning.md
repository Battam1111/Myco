# L1 — Versioning Contract

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L1. Subordinate to `L0_VISION.md` and `protocol.md`.

---

## Two version axes

Myco has **two orthogonal version numbers**. Confusing them was a recurring
pre-rewrite bug (audit finding: v0.46.0 → v0.6.0 → v0.45.0 non-monotonicity).

### Package version

The Python package version, tagged in git, published to PyPI, and imported
as `myco.__version__`.

- **Source of truth**: `src/myco/__init__.py::__version__`.
- **Propagation**: `pyproject.toml` uses Hatchling `dynamic = ["version"]`
  with `[tool.hatch.version] path = "src/myco/__init__.py"`.
- **Mechanical enforcement**: lint dimension "Version Single Source"
  (immune kernel, see `L3_IMPLEMENTATION/`). Any static `version = "…"`
  in `pyproject.toml` alongside `dynamic = ["version"]` is a CRITICAL error.
- **SemVer**: MAJOR.MINOR.PATCH. Breaking kernel-contract change ⇒ MAJOR
  bump. New feature, no breakage ⇒ MINOR bump. Internal fix ⇒ PATCH bump.
- **Monotonicity**: tags must be strictly increasing. `v0.6.1` after
  the legacy `v0.3.3` predecessor is forbidden. The v0.4.0 rewrite
  starts a clean, monotone sequence from `v0.4.0` onward.

### Contract version

The version of **this layer** (L1 rules + L2 doctrine) that the substrate
is currently aligned with. Lives in `_canon.yaml::contract_version`.

- **Bump triggers**: any change to R1–R7 wording/semantics, subsystem
  definition, exit-code policy grammar, lint-dimension inventory, or
  command manifest.
- **Independent of package version**: a patch-level package release may
  coincide with a contract change, or may not.
- **Synced field**: `_canon.yaml::synced_contract_version` records the
  latest contract version the substrate has reflected against. Drift
  (`contract_version ≠ synced_contract_version`) is a HIGH lint.
- **Defense against ahead-of-kernel canon (v0.6.0+ SH2 dim)**: if
  `contract_version` exceeds `__version__` (canon was bumped by a
  newer kernel and read by an older kernel), SH2 emits HIGH —
  prevents a stale kernel from silently writing v(N) canon shape
  while reading v(N+1) substrate.

## Starting points (v0.4.0)

| Field | Value at v0.4.0 tag |
|-------|---------------------|
| `__version__` | `"0.4.0"` |
| `_canon.yaml::contract_version` | `"v0.4.0-alpha.1"` during development; `"v0.4.0"` at release |
| `_canon.yaml::synced_contract_version` | same as `contract_version` on a clean `assimilate` (alias `reflect` still resolves) |
| Wave numbering | resets to **Wave 1** at v0.4.0 (per §9 E5) |

## Current state (v0.6.0)

| Field | Value at v0.6.0 tag |
|-------|---------------------|
| `__version__` | `"0.6.0"` |
| `_canon.yaml::schema_version` | `"2"` (was `"1"` at v0.5.x; v1→v2 upgrader registered) |
| `_canon.yaml::contract_version` | `"v0.6.0"` |
| `_canon.yaml::synced_contract_version` | `"v0.6.0"` (equal after a clean `assimilate`) |
| Wave numbering | Wave 19 |

Per `L0_VISION.md:223-228`, **v0.6.0 is a MAJOR-class release** in
Myco's contract semantics — it triggers the Living Bets re-audit
cadence (sibling craft
`docs/primordia/_landed/v0_6_x/v0_6_0_living_bets_audit_craft_2026-04-28.md`). The
SemVer label "0.6.0" reads as MINOR by external naming convention but
Myco contract treats it as MAJOR-class for review-cadence and
breaking-change-permission purposes. This dual interpretation is
sanctioned by the v0.6.0 unified-evolution craft Round 2 §F1.

## Dual-layer versioning (introduced v0.6.0)

Per craft v0.6.0 §F23, Myco distinguishes two layers within a single
contract version:

- **Contract-frozen**: canon schema, R1-R7 + their mechanical
  enforcement, lint inventory, verb manifest, fixable-set,
  governance tier rules. Bumps require `molt` + `contract_changelog`.
- **Ecosystem-thawed**: host adapter implementations, framework
  demos, Glama/MCP-Registry metadata, CHANGELOG hatch hook. Can be
  patched within v0.6.x without contract bump.

Spec drift in Anthropic Cowork / MCP 2026-Q3 / Glama TDQS lands as
patch releases without re-running the contract-frozen part. Contract
version bumps only on the contract-frozen layer; package version
bumps on both.

## Schema version (introduced v0.6.0)

`_canon.yaml::schema_version` distinct from `contract_version`. Schema
version is the canon **document shape**; contract version is the
**rule semantics**. They are correlated but independent:

- Schema v1 covered all v0.4.0 → v0.5.24 substrates.
- Schema v2 lands at v0.6.0 with the bool→enum + federation_peers
  additive field. The `_v1_to_v2` upgrader auto-applies on first
  parse of any v1 substrate; v1 substrates parse cleanly without
  warning. See `core/canon.py::_v1_to_v2` for the partial-function
  composition.
- Schema v2.1 (planned post-v0.6.0): lint.dimensions table extracted
  to sibling `_canon_lint.yaml`. Separate upgrader.

The "Starting points" row from v0.4.0 and the "Current state" rows
for v0.5.7 and v0.6.0 are retained for historical reference.

## Pre-rewrite tags

The pre-rewrite lineage ends at `v0.3.4-final` (annotated tag on commit
c51a8da). The stray tags `v0.5.0`, `v0.6.0`, `v0.6.1` from older
experimentation are considered historical noise and are **not** continued;
v0.4.0 is the authoritative next release.

## Change log

All contract-version bumps are recorded in `docs/contract_changelog.md`
with: date, old → new version, summary of changes, approving party.
Omitting the changelog entry is an immune error.
