---
type: craft
topic: v0_5_9_immune_zero
slug: v0_5_9_immune_zero
kind: design
date: 2026-04-21
rounds: 3
craft_protocol_version: 1
status: APPROVED
---

# V0.5.9 Immune Zero — Craft

> **Date**: 2026-04-21
> **Layer**: L2–L3. The DC2 refinement is L2 (homeostasis doctrine
> semantics); the cross-cutting doctrine-anchor additions are L3
> (per-module kernel work).
> **Upward**: Reinforces L0 principle 5 (万物互联 — every module
> now links up to doctrine), honours L1 R6/R7.
> **Governs**: every `src/myco/` module's docstring anchor + the
> `DC2` dimension's public-function rule + the `bounded_read_text`
> rollout + the canon JSON-Schema at `docs/schema/`.

---

## Round 1 — 主张 (claim)

**Claim**: v0.5.8 shipped a 25-dimension immune surface but the
substrate itself reported 121 LOW findings against that surface
(mostly DC4 pre-existing modules missing doctrine anchors + DC2
public-function docstrings). A lint surface that routinely reports
>100 LOW findings against its own host substrate trains the agent
to ignore the surface. v0.5.9's load-bearing claim: **get immune
to 0 findings on myco-self, WITHOUT gutting the dimensions that
catch real regressions**.

Five mechanical moves:

1. **DC2 refinement** — exempt `@property` decorated methods
   (attribute accessors that inherit class-doc intent) and methods
   that override an abstract protocol method (Protocol / ABC /
   Adapter / Dimension base classes).
2. **DC4 + CG1 + CG2 + SE2 cleanup** — add doctrine-ref lines to
   the 32 kernel modules that predated v0.5.8's dim expansion;
   link the 6 v0.5.8 audit consolidation notes from the craft
   that consumed them.
3. **`bounded_read_text` rollout** — v0.5.8 shipped the helper
   with 0 callsites outside its module. v0.5.9 wires it into
   every canon / note / dim-scan / graph / propagate /
   `.gitignore` read path.
4. **Canon JSON-Schema** at `docs/schema/canon.schema.json`.
5. **Migration guides** at `docs/migration/` for v0.5.7 → v0.5.8
   and v0.5.8 → v0.5.9.

## Round 1.5 — 自我反驳 (self-rebuttal)

- **T1**: Getting immune to 0 is vanity. The agent works with
  findings; suppressing findings even at LOW feels like gaming.
- **T2**: DC2 exemption (@property + abstract overrides) adds a
  heuristic that false-negatives on third-party substrates with
  non-standard inheritance.
- **T3**: 32 doctrine-ref lines across working modules is churn.
- **T4**: `bounded_read_text` rollout changes failure modes:
  `MycoError` where pre-v0.5.9 got `OSError`. Narrow `except`
  tuples crash instead of degrading.
- **T5**: Canon JSON-Schema duplicates `load_canon` logic. Schema
  drift is inevitable.

## Round 2 — 修正 (revision)

- **R1** (T1): Suppression is semantic — `@property` accessors are
  documented by the class docstring (Python semantics); abstract-
  protocol overrides inherit their contract from the parent.
  Both match DC2's docstring-stated scope. Adding a counter-test
  proves DC2 still fires on normal public functions.
- **R2** (T2): Whitelist is narrow: `Adapter`, `Protocol`,
  `Dimension`. Third parties inheriting from `Dimension` are
  caught; those with custom classes aren't (correct — their
  code, their obligation). Broader heuristic needs ABC
  introspection, impossible from pure AST walk.
- **R3** (T3): Each addition is one line; each is a correctness
  win (mycelium graph now anchors every src to doctrine).
  Alternative: permanent 48 DC4 findings + agent skim-training.
- **R4** (T4): Every new callsite widens the `except` tuple to
  include `MycoError`. Uniform + pre-commit grep-audited.
- **R5** (T5): Schema-drift risk real; schema README flags it;
  planned v0.6 dim `SC1` (schema-consistency cross-checker) will
  mechanically close. Until then: maintainer discipline, same as
  every other multi-SSoT Myco contract.

## Round 2.5 — 再驳 (counter-rebuttal)

- **T6** (re R2): Whitelist hardcodes three class names. Fourth
  abstract base class silently over-reports until someone adds it.
- **T7** (re R5): "Until SC1 ships" is the same deferred-commit
  language v0.5.8 acknowledged can drift.

## Round 3 — 收敛 (convergence)

- **R6** (T6): Accepted. Whitelist exposed as module-level
  `_ABSTRACT_PARENT_NAMES: frozenset[str]`. One-line future edit.
  Comment flags future maintenance.
- **R7** (T7): Accepted. Deferrals documented openly under §"Not
  in v0.5.9 scope". v0.6.0 revisit commitment. Alternative —
  block v0.5.9 until SC1 ships — pushes clean release backward
  for a purity concern; worse than landing 0 today + SC1 next.

## Decision

Approved. Ship v0.5.9 as the immune-zero-baseline release.

## Mechanism

### DC2 refinement

Two new exemption predicates in `DC2PublicFunctionDocstring.run`:

```python
def _is_property(node) -> bool:
    """True iff @property (or setter/deleter/getter) present."""

def _is_abstract_override(func_node) -> bool:
    """True iff containing class inherits from {Adapter, Protocol, Dimension}."""
```

Update class docstring "Excluded" section.

### Doctrine-ref backfill — 32 modules

Mapping (one-line `Governing doctrine: docs/architecture/…md` added
to each file's existing docstring):

- `circulation/*` → `circulation.md`
- `digestion/*` → `digestion.md`
- `homeostasis/*` → `homeostasis.md`
- `ingestion/*` + adapters → `ingestion.md`
- `cycle/ramify.py` / `cycle/graft.py` → `extensibility.md`
- `core/version.py` → `L1_CONTRACT/versioning.md`
- `core/paths.py` → `L1_CONTRACT/canon_schema.md`
- `surface/*` → `L3_IMPLEMENTATION/command_manifest.md` (or
  `L2_DOCTRINE/circulation.md` for MCP)
- `install/*` → `L2_DOCTRINE/genesis.md` + `extensibility.md` for
  clients

### `bounded_read_text` rollout

For each of ~25 `path.read_text(encoding="utf-8")` calls:

1. Import `bounded_read_text`.
2. Replace the call.
3. Widen `except` to include `MycoError`.

Out of scope: package-resource reads (trusted internal bytes).

### Canon JSON-Schema

`docs/schema/canon.schema.json` (Draft 2020-12) + README with IDE
wiring snippets for VS Code, JetBrains, Neovim.

### Migration guides

`docs/migration/{README.md, v0_5_7_to_v0_5_8.md, v0_5_8_to_v0_5_9.md}`.

### Not in v0.5.9 scope

- **SC1 schema-consistency dim** (v0.6+)
- **Full `bounded_read_text` coverage** of package-resource reads
- **DC2 third-party ABC detection** beyond the three whitelisted names

## Why this matters (L0 tie-in)

- **Only For Agent**: noisy baseline → skimming. Zero baseline →
  new findings are signal.
- **万物互联**: 32 doctrine-ref additions complete code → doctrine
  mycelium edges. No module is a graph orphan.
- **永恒吞噬**: `bounded_read_text` makes ingestion
  "unbounded content, bounded DoS exposure".
- **永恒进化**: JSON-Schema moves at contract cadence. Two
  validators, one contract — both evolve together.

## Source notes

- [v0.5.8 release self-audit findings](../../notes/integrated/n_20260420T192123Z_v0-5-8-iter-4-consolidated-4-lenses-lens.md)
- [v0.5.8 discipline-enforcement craft](v0_5_8_discipline_enforcement_craft_2026-04-21.md)
