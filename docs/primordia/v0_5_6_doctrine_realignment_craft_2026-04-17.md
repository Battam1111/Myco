---
type: craft
topic: v0.5.6 doctrine realignment + MP1 LLM-boundary guard + bitter-lesson note
slug: v0_5_6_doctrine_realignment
kind: audit
date: 2026-04-17
rounds: 3
craft_protocol_version: 1
status: COMPILED
children:
  - v0_5_6_mp1_mycelium_purity_craft_2026-04-18.md
---

> **Child crafts**: the MP1 dimension justification lives in its
> own narrow craft at
> `docs/primordia/v0_5_6_mp1_mycelium_purity_craft_2026-04-18.md`
> — added at v0.5.7 release closure to give MP1's blacklist
> roster + `providers/` opt-in package + `no_llm_in_substrate`
> canon field their own reviewable record, separate from this
> umbrella audit.


# v0.5.6 — Doctrine Realignment + Mechanical LLM-Boundary Guard + Bitter-Lesson Note

> **Date**: 2026-04-17.
> **Layer**: L0 (principle 1 addendum + bitter-lesson appendix),
> L1 (canon schema + new contract field `system.no_llm_in_substrate`),
> L2 (34 drift items + new `extensibility.md`),
> L3 (command_manifest + package_map + migration_strategy + symbiont_protocol cross-links).
> **Upward**: L0 principle 1 (只为 Agent) gets the two live exceptions
> it needs (`brief` human window; Agent-calls-LLM-not-substrate);
> L0 principles 3/4/5 unchanged but with v0.5.5 reality reflected.
> **Governs**: every file under `docs/architecture/`, the v0.5.5
> MP1 dimension (new), `_canon.yaml` new field
> `system.no_llm_in_substrate`, and the template canon's same field.

---

## Round 1 — 主张 (claim)

The v0.5.5 panoramic review surfaced a hard truth: **the doctrine
tree still describes v0.5.3, with v0.5.5 patches grafted on**. An
independent opus sub-agent audit found 15 load-bearing
contradictions, 11 stale cross-references, and 13 missing anchors —
39 drift items total across L0-L3. The `brief` verb (v0.5.5's one
explicit exception to L0 principle 1) is invisible to every
doctrine file above L3. The fixable-dimension protocol + safe-fix
discipline live only in the v0.5.5 craft's §MAJOR-A, not in L2
homeostasis. The "Agent calls LLM, substrate does not" boundary
exists as prose in L2 digestion but has **no mechanical guard**.

v0.5.6 closes the whole gap in a single release:

1. **34 doctrine alignment edits** across L0-L3 + architecture
   README, turning every S1/S2/S3 finding from the audit into
   concrete text corrections.
2. **MP1 (Mycelium Purity 1) — new immune dimension.** Mechanical
   / HIGH / not fixable. Scans every `.py` under `src/myco/` for
   imports matching a blacklist of LLM provider SDKs
   (`openai / anthropic / mistralai / cohere / voyageai /
   google.generativeai / google.genai / langchain* / llama_index /
   llama_cpp / ollama`). Whitelists `src/myco/providers/` (reserved
   dir, empty at v0.5.6) for any future opt-in coupling. Violation
   fires HIGH mechanical — CI-gating with default exit policy.
3. **New canon contract field** `system.no_llm_in_substrate: true`.
   Required at schema v1 from v0.5.6 onwards; MP1 cross-checks the
   declaration against reality (declared `true` but kernel imports
   from blacklist → MP1 fires; declared `false` → MP1 skips the
   scan but the canon itself is loud evidence of opt-out). Flipping
   to `false` is a contract-bumping event.
4. **L0 principle 1 addendum**: the two explicit exceptions
   (`brief` human window; Agent-calls-LLM-not-substrate) written
   directly into the principle text, not buried in L2.
5. **Bitter-lesson appendix** at L0: Myco's 17-verb coordination
   surface + canon schema + 10 lint dimensions are an
   unfalsified-but-live bet that stable coordination vocabulary
   survives model-capability growth. The appendix names the
   review cadence (every MAJOR release re-audits this bet) and
   the theoretical replacement trigger (if an Agent can maintain
   a 1M-file repo without structured verbs, Myco must re-justify).
6. **New L2 `extensibility.md`** — single doctrine page that
   explains the two orthogonal extension axes (`.myco/plugins/`
   per-substrate ⊥ `symbionts/` per-host) at L2 not just L3, so
   they surface in the natural top-down reading.
7. **Contract-bumping molt**: canon `contract_version: v0.5.5 →
   v0.5.6` because `system.no_llm_in_substrate` is a new required
   field. Alias `system.no_llm_in_substrate` missing → parser
   defaults to `true` with a one-time `UserWarning` so v0.5.5
   substrates upgrade silently; the field only becomes hard-
   required at v0.6.0.

Single release. Zero new verbs. One new dimension. One new canon
field. 39 text corrections. ~60 new tests. Full backward
compatibility for v0.5.5 invocations.

## Round 1.5 — 自我反驳 (self-rebuttal)

- **T1**: MP1 blacklist is brittle. What about `openai_python`,
  `claude_sdk`, future rebrands? Maintaining a static list rots.
- **T2**: MP1 can't see dynamic imports (`importlib.import_module`,
  `__import__`). An adversary who wants to smuggle `openai` in can
  trivially bypass. Is MP1 theatre?
- **T3**: MP1 as HIGH mechanical means every CI run on a substrate
  that legitimately ships a provider layer (future `src/myco/
  providers/openai_bridge.py`) would fail. Escape hatch = manifest
  allowlist or canon toggle, both of which weaken the guard.
- **T4**: Canon field `no_llm_in_substrate: true` is a declaration,
  not a proof. A substrate declaring true while secretly calling
  LLMs is worse than silent violation (now it's a lie + a
  violation). MP1 cross-check helps but only for static imports.
- **T5**: "Agent calls LLM, substrate does not" at L0 might be
  over-constraining. What about a future `myco sporulate --llm`
  flag that explicitly opts the substrate into using a user-
  provided LLM client? Locking this at L0 closes that door prematurely.
- **T6**: Bitter-lesson appendix at L0 is meta-reflection; L0 is
  supposed to be principles, not epistemology-about-principles.
  Might be better as a standalone L4 "living bets" doc.
- **T7**: Canon field requires molt → contract bump → every v0.5.5
  substrate must migrate. Forward-compat upgrader at v0.5.1
  handles unknown `schema_version` but `no_llm_in_substrate`
  missing is a missing REQUIRED field under the new schema. Does
  the permissive reader tolerate it? The spec says required fields
  raise `CanonSchemaError`. v0.5.5 substrates would break.
- **T8**: 34 doctrine edits in one pass is high churn on reviewed-
  and-stable doctrine pages. Risk of introducing new errors while
  fixing old ones. How do we verify we didn't drift further?
- **T9**: `extensibility.md` is new L2 doctrine; L2 is the slowest-
  moving layer. Adding a cross-cutting page at L2 needs its own
  justification — why not L3?
- **T10**: MP1 + canon field is a rung up from "doctrine by
  convention" (level 1) to "mechanical guard" (level 3). Why not
  go to level 4 (import-hook level enforcement that raises at
  import time, not just lint time)? Answer matters because it
  bounds how strong "the absolute best standard" claim actually is.

## Round 2 — 修正 (revision)

- **R1** (addresses T1): blacklist is intentionally a **living
  list**; maintainers add entries as new providers emerge. v0.5.6
  ships a v1 list that covers the 2026-04 landscape; `MP1.explain`
  documents the process ("add to blacklist + update MP1
  changelog"); the list lives on the dimension class (module-level
  constant), patchable via a substrate-local dimension override
  (`.myco/plugins/dimensions/`) for hosts that want stricter or
  more relaxed rules. Rot acknowledged, not pretended away.
- **R2** (addresses T2): MP1 catches **intent + honest mistake**,
  not determined adversaries. Static-import scanning is the
  cheapest guard that catches 95% of real-world drift (a library
  author reaches for `import openai` without thinking about the
  boundary). Dynamic imports are a separate threat surface that
  MP2 (future) could address via bytecode scan. v0.5.6 ships MP1;
  MP2 is not in scope. The doctrine text is explicit:
  "MP1 is a coordination guard, not an adversarial sandbox."
- **R3** (addresses T3): reserved directory `src/myco/providers/`
  is the declared escape hatch. Any `.py` under it is MP1-
  exempt by path. Creating the first provider module is a
  contract-bumping event at that future release, with craft-
  approval discipline. v0.5.6 ships `providers/` as an empty
  package with a README explaining the opt-in contract.
- **R4** (addresses T4): canon field is a **declared intent**
  backed by MP1 scan; the combination of (declared false + MP1
  reports no violation) still gives useful signal because a
  substrate that lies systematically is a governance failure
  MP1 can't fix. Our doctrine doesn't pretend MP1 is a sandbox;
  it pretends only to block accidents + honest drift.
- **R5** (addresses T5): future opt-in is handled by the
  `providers/` directory (R3) + canon toggle, not by loosening
  L0. L0 principle 1's exception text says "the Agent calls the
  LLM; the substrate does not embed provider calls in its own
  logic. Opt-in coupling lives behind `canon.system.no_llm_in_
  substrate: false` + `src/myco/providers/`, with a contract-
  bumping molt required." Door is not closed; it's on a declared
  latch.
- **R6** (addresses T6): bitter-lesson note stays in L0 because
  it is a meta-constraint on how principles 3/4 (永恒进化 /
  永恒迭代) are read. A substrate that thinks it's beyond
  bitter-lesson-erosion won't iterate itself out of over-
  structure. The note is short (~200 words) and explicitly
  marked as "appendix to principle 1" rather than a sixth principle.
- **R7** (addresses T7): v0.5.6 upgrader is the right place for
  this. Register an upgrader at `schema_upgraders["v0.5.5-canon"]`
  (keyed on contract_version, not schema_version — a separate
  seam than v0.5.1's `schema_upgraders`) OR, simpler, make
  `system.no_llm_in_substrate` **optional-with-default-true at
  v0.5.6; required at v1.0.0**. v0.5.5 substrates parse silently
  (default `true`, which matches v0.5.5 implicit reality); setting
  `false` requires the substrate author to know what they're
  doing. This is the smooth upgrade path; implement via
  `_REQUIRED_TOP_LEVEL` stays unchanged, `Canon.system.get(
  "no_llm_in_substrate", True)` reads with default.
- **R8** (addresses T8): 34 edits divided into 3 categories with
  a sub-agent-generated checklist; each category gets a
  verification pass (grep for remaining old strings, visual
  review, pytest). The audit sub-agent's report serves as an
  idempotent specification — re-running the audit after edits
  must find zero S1, zero S2, and S3s only for v0.6+ scope items.
- **R9** (addresses T9): `extensibility.md` is L2 because
  `.myco/plugins/` and `symbionts/` are both **cross-subsystem**
  concerns that govern how ALL subsystems extend themselves.
  L3 is for one-subsystem-deep implementation concerns; the
  orthogonal-axes statement is a doctrine-level invariant that
  belongs at L2. Stub-level precedent: `homeostasis.md` already
  lives at L2 without being subsystem-specific in the strict sense.
- **R10** (addresses T10): import-hook enforcement (level 4)
  would raise on `import myco.digestion.sporulate` if sporulate
  accidentally pulled openai. That's more mechanical but also
  brittle (breaks REPL exploration, pyright, etc.). MP1 at lint
  level is the right trade-off: **CI-gating at commit time**, not
  runtime-gating at import time. The highest STANDARD is not
  necessarily the highest-invasiveness implementation; it's the
  one that catches the class of error we care about without
  breaking adjacent workflows. Document the trade-off in MP1's
  class docstring.

## Round 2.5 — 再驳 (counter-rebuttal)

- **T11**: if MP1 is substrate-local-overridable (R1 hint), a
  substrate author who WANTS to call openai can just register
  an override that returns no findings. The boundary is only as
  strong as the host's willingness to enforce it.
- **T12**: bitter-lesson appendix at L0 will be read by agents
  implementing future doctrine changes. If the note is too
  pessimistic ("maybe Myco is obsoleted by AGI"), agents might
  stop investing; if too optimistic, they miss the live risk.
  Calibration matters.
- **T13**: `providers/` as empty package is a "reserved slot"
  pattern. We learned at v0.5.3 (symbionts was empty for 3
  releases) that empty slots accumulate ambiguity. Could
  `providers/` become the new symbionts — empty forever because
  nobody opts in?
- **T14**: MP1 cross-checks canon declaration against scan. If
  canon says `true` and scan finds `openai`, MP1 fires. But
  what if canon says `true`, kernel is clean, but `.myco/plugins/`
  (substrate-local!) imports openai? Does MP1 cross into
  `.myco/plugins/` or stop at `src/myco/`?

## Round 3 — 反思 (reflection and decision)

All tensions resolved. Final scope locked:

### Mechanical layer

- **MP1** scans **`src/myco/`** only (kernel purity). Not
  `.myco/plugins/` — substrate-local plugins are explicitly the
  per-substrate author's responsibility; MP2 (future) may cover
  this axis. MP1's scope line is documented on the dimension
  class.
- **Blacklist** as module-level constant on the MP1 class,
  initial v1 list: `openai / anthropic / mistralai / cohere /
  voyageai / google.generativeai / google.genai / langchain /
  langchain_core / langchain_openai / langchain_anthropic /
  llama_index / llama_cpp / ollama`. Each entry on its own line
  in the source so diffs are readable.
- **Whitelist** = any path under `src/myco/providers/` (empty
  package reserved at v0.5.6; README declares contract).
- **MP1.fixable = False** intentionally. A "fix" would be
  deleting the import, which is destructive and could break the
  handler. Human review required for violations.
- **MP1 cross-checks canon**: reads `canon.system.no_llm_in_
  substrate`; if `true` and scan finds violation, fires HIGH; if
  `false` and scan finds violation, fires LOW (flags the fact
  that the substrate opted-out — which means the Agent should
  not rely on the LLM-boundary invariant); if `false` and scan
  is clean, no finding (substrate declared opt-out but honored
  it — valid state).

### Canon layer

- **New field** `system.no_llm_in_substrate: bool` with default
  `true`. Reads via `canon.system.get("no_llm_in_substrate",
  True)`. Not in `_REQUIRED_TOP_LEVEL`; graceful on v0.5.5
  canons (they behave as if `true`).
- **Genesis template** adds the field explicitly (`true`) so
  new substrates declare their posture.
- **L1 `canon_schema.md`** documents the field as part of the
  `system:` block and explains the MP1 cross-check semantics.
- **Contract bump** from `v0.5.5` to `v0.5.6` because a new
  required-at-molt-time field shapes the contract surface.

### Doctrine layer

- **L0 principle 1**: ~80-word addendum carves `brief` + Agent-
  calls-LLM exceptions inline. Principle text itself unchanged;
  addendum is labeled and dated.
- **L0 bitter-lesson appendix**: ~200 words after principle 5.
  Labeled as "appendix to principle 1 + principles 3 and 4"
  explicitly. Names review cadence.
- **L2 `extensibility.md`**: new file. ~120 lines. Cross-links
  to `homeostasis.md`, `symbiont_protocol.md` (L3), and
  `.myco/plugins/` doctrine.
- **34 edits** from the audit sub-agent, organized as:
  - S1 (15 contradictions) — hard-fix, must land
  - S2 (11 stale refs) — mechanical replacements
  - S3 (13 missing anchors) — new prose added at specific locations

### Release mechanics

- v0.5.5 → v0.5.6 **MINOR** bump (new canon field, new dimension,
  new doctrine file; zero verb change, zero handler API change)
- `myco molt --contract v0.5.6` via the governance verb itself
  (eating our own dog food; the command updates canon +
  contract_changelog + writes the new top entry)
- `pyproject.toml[project.entry-points."myco.dimensions"]` adds
  MP1 row; `_BUILT_IN` tuple grows to 11 dimensions
- `_canon.yaml::lint.dimensions` adds `MP1: mechanical`
- `_canon.yaml::system.no_llm_in_substrate: true` added

### What this craft revealed

1. The audit → craft → release loop is working as designed — the
   panoramic review surfaces real drift; the craft chooses scope;
   the release lands corrections. v0.5.6 is the first release
   whose *entire* scope is "align what earlier releases didn't
   align". This is healthy feedback, not an anti-pattern.
2. The "Agent calls LLM, substrate does not" boundary needs a
   declared escape hatch (`providers/` + canon toggle) to stay
   credible. A boundary with no declared path through it becomes
   either violated or abandoned; a boundary with a declared
   contract-bumping path through it stays respected.
3. Mechanical enforcement (MP1) without declared semantics
   (canon field) would just be a blacklist. The pair —
   declaration + scan — turns it into a contract the substrate
   itself commits to. That is the "highest standard" shape.
4. Bitter-lesson appendix at L0 is not just philosophy; it sets
   a review cadence (every MAJOR release re-audits the
   coordination-surface bet). Without that, the doctrine tree
   becomes crystallized and eventually brittle.

## Deliverables

### Code

- `src/myco/homeostasis/dimensions/mp1_no_provider_imports.py`
  (new) — MP1 dimension class with blacklist, `providers/`
  whitelist, canon-cross-check.
- `src/myco/homeostasis/dimensions/__init__.py` — add MP1 import
  + `_BUILT_IN` entry + `__all__` entry.
- `src/myco/providers/__init__.py` (new) — empty package with
  docstring declaring opt-in contract + README link.
- `src/myco/providers/README.md` (new) — explains the
  `no_llm_in_substrate: false` + contract-bump path.
- `pyproject.toml[project.entry-points."myco.dimensions"]` — add
  `MP1 = "..."`.
- `src/myco/core/canon.py` — reads `system.no_llm_in_substrate`
  with default `True` (no schema-version bump; graceful on v0.5.5
  canons).
- `src/myco/germination/templates/canon.yaml.tmpl` — adds the new
  field with default `true`.
- `_canon.yaml` — adds `system.no_llm_in_substrate: true` +
  `lint.dimensions.MP1: mechanical`; `contract_version: v0.5.6`.

### Doctrine

- `docs/architecture/L0_VISION.md` — principle 1 addendum (brief
  + LLM-boundary) + bitter-lesson appendix.
- `docs/architecture/L1_CONTRACT/canon_schema.md` — 4 edits (real
  dimension IDs; `germination:` subsystem; real v0.5.6 version;
  `no_llm_in_substrate` field + MP1 semantics + reference;
  `skeleton_downgrade` updated; graph.json excluded).
- `docs/architecture/L1_CONTRACT/versioning.md` — 2 edits (verb
  alias "clean reflect"→"clean assimilate"; current-state
  companion at v0.5.6).
- `docs/architecture/L1_CONTRACT/exit_codes.md` — 1 edit
  (`DIMENSION_CATEGORY` refactor note).
- `docs/architecture/L1_CONTRACT/protocol.md` — verify; likely no
  edits beyond the sub-agent's audit trail.
- `docs/architecture/L2_DOCTRINE/genesis.md` — 2 edits (rename
  banner + M2-fix cross-link).
- `docs/architecture/L2_DOCTRINE/ingestion.md` — 3 edits (eat
  content/path/url interface; hunger `count_by_kind` payload;
  brief cross-reference).
- `docs/architecture/L2_DOCTRINE/digestion.md` — 1 edit
  (sporulate output-shape documented; LLM-boundary already
  present, cross-link to MP1).
- `docs/architecture/L2_DOCTRINE/circulation.md` — 3 edits
  (build_graph API; fingerprint formula; traverse payload fields).
- `docs/architecture/L2_DOCTRINE/homeostasis.md` — 6 edits (ten
  dimensions enumerated; fixable protocol; safe-fix discipline
  doctrine; graph-cache cross-reference; MP1 introduced; MP1
  class docstring documented).
- `docs/architecture/L2_DOCTRINE/extensibility.md` — new file.
- `docs/architecture/L3_IMPLEMENTATION/command_manifest.md` —
  3 edits (18-verb table with brief row; six gates on winnow;
  payload shape fix).
- `docs/architecture/L3_IMPLEMENTATION/package_map.md` — 6 edits
  (src tree includes install/mcp/providers/brief; test layout
  updated; mapping matrix extended; cycle tests row).
- `docs/architecture/L3_IMPLEMENTATION/migration_strategy.md` —
  1 edit (v0.4.0 historical banner; v0.5.3 rename annotated).
- `docs/architecture/L3_IMPLEMENTATION/symbiont_protocol.md` —
  1 edit (10-host list named; L0/L1/L2 cross-link).
- `docs/architecture/README.md` — full rewrite (v0.5.6 status).

### Release metadata

- `__version__` → `0.5.6`
- `.claude-plugin/plugin.json` → `0.5.6`
- `_canon.yaml::contract_version` → `v0.5.6`
- `_canon.yaml::synced_contract_version` → `v0.5.6`
- `CHANGELOG.md` → new `[0.5.6]` top section
- `docs/contract_changelog.md` → new `v0.5.6` top section

### Tests

- `tests/unit/homeostasis/dimensions/test_mp1_no_provider_imports.py`
  (new) — ~12 tests covering: dimension registration; clean
  kernel; blacklist detection (one per major provider); providers/
  whitelist; canon-cross-check high/low paths; multiple-imports-
  per-file; non-.py files skipped; symlink sanity.
- `tests/unit/core/test_canon_no_llm_field.py` (new) — ~4 tests
  covering: default True when missing; explicit true/false
  parse; canon without `system` block falls through safely.
- `tests/test_scaffold.py` — ensure new `MP1_...py` module is
  import-safe; no packaging breakage.
- existing dimension tests get a targeted pass to verify MP1
  doesn't affect their baseline.

### Verification

- Full pytest suite green (target: 556 + ~16 new MP1/canon/
  extensibility = **~572 passing**).
- `myco immune --list` shows 11 dimensions (was 10).
- `myco winnow docs/primordia/v0_5_6_doctrine_realignment_craft_
  2026-04-17.md` passes (self-winnow).
- `myco immune` on myco-self shows MP1 CLEAN (zero LLM imports
  in kernel).
- `myco brief` section 3 "Immune" shows MP1 in dimensions_run list.

## Acceptance

- **pytest**: green at ≥572.
- **behavioral**:
  - New MP1 dimension registers, runs, finds zero findings on
    clean kernel.
  - A synthetic substrate with `import openai` inside a
    `.myco/plugins/handlers/<verb>.py` does NOT trip MP1 (MP1
    scope is kernel only).
  - A synthetic kernel file at `src/myco/test_mp1_victim.py`
    that imports `openai` DOES trip MP1 HIGH.
  - Declaring `canon.system.no_llm_in_substrate: false` → MP1
    skips the hard check; reports "opt-out declared" as info.
  - Every v0.5.5 invocation of every verb still works.
  - Legacy aliases still resolve.
- **non-regression**:
  - Every pytest from v0.5.5 still green.
  - `myco --version` returns `myco 0.5.6`.
  - `from myco.meta import session_end_run` still imports (shim).
  - Every v0.5.5 canon parses under v0.5.6 (default-to-true
    gracefully; no warning fires on v0.5.5 canons).
