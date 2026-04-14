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
  `v0.3.3` is forbidden. The v0.4.0 rewrite starts a clean, monotone
  sequence from `v0.4.0` onward.

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

## Starting points (v0.4.0)

| Field | Value at v0.4.0 tag |
|-------|---------------------|
| `__version__` | `"0.4.0"` |
| `_canon.yaml::contract_version` | `"v0.4.0-alpha.1"` during development; `"v0.4.0"` at release |
| `_canon.yaml::synced_contract_version` | same as `contract_version` on a clean reflect |
| Wave numbering | resets to **Wave 1** at v0.4.0 (per §9 E5) |

## Pre-rewrite tags

The pre-rewrite lineage ends at `v0.3.4-final` (annotated tag on commit
c51a8da). The stray tags `v0.5.0`, `v0.6.0`, `v0.6.1` from older
experimentation are considered historical noise and are **not** continued;
v0.4.0 is the authoritative next release.

## Change log

All contract-version bumps are recorded in `docs/contract_changelog.md`
with: date, old → new version, summary of changes, approving party.
Omitting the changelog entry is an immune error.
