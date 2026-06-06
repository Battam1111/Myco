# L0 Doctrine Provenance

> **Status**: live document (v3.1-stratigraphy, 2026-05-18). The traceability spine from prior monolithic L0 → current four-layer stratigraphy.

---

## §1. What this document is

A traceability spine. Every section of the prior `docs/architecture/L0_VISION.md` (DRAFT 9 SEALED, 881 lines / 74066 bytes, sealed 2026-05-17 at commit `e796451`; SHA-256 = `5eacf3e7bbb9f8633bcf05266aef24fc27d9ed35bc941c8c2ed50f38233c7f66`) maps to one or more entries in the v3.1 doctrine. This mapping is what allows future readers to verify "the new doctrine preserves the old content" rather than silently dropping concepts.

**Source file removed 2026-05-18** as part of v3.1 cleanup — cultivator's engineering judgment: leaving the old monolith in place creates drift vectors (readers may treat it as authoritative; future Claude may prioritize its surface presence over the v3.1 directory). Historical text is permanently recoverable via git:

```
git show e796451:docs/architecture/L0_VISION.md
```

The mapping table below (§2) is the complete substantive bridge; nothing is lost doctrinally by removing the file.

This document is itself L0 in the new form.

---

## §2. Prior → v3.1 mapping table (COMPLETE)

| Old L0 section | Mapped to v3.1 |
|---|---|
| §1 What Myco is | `META.md` §1 + `cards/P01_agent_primary.md` §1-§3 |
| §1.1 Cultivation | `cards/P01c_asymmetric_carrier.md` (eternity) + `cards/COV01_fiduciary_duty.md` through `COV06_*` |
| §2 P1 Agent-Primary | `cards/P01_agent_primary.md` |
| §2 P1.a Self-hosting | `cards/P01_agent_primary.md` §3.2 |
| §2 P1.b' Human OUT | `cards/P01_agent_primary.md` §3.3 |
| §2 P1.b'' Human RETAINED | `cards/P01_agent_primary.md` §3.4 |
| §2 P1.c Asymmetric carrier | `cards/P01c_asymmetric_carrier.md` (eternity-clause) |
| §2 P2 Eternal Ingestion | `cards/P02_eternal_ingestion.md` |
| §2 P3 Resumable Evolution | `cards/P03_resumable_evolution.md` |
| §2 P4 Eternal Iteration | `cards/P04_eternal_iteration.md` |
| §2 P5 Universal Interconnection | `cards/P05_universal_interconnection.md` |
| §2 P6 Eternal Causality | `cards/P06_eternal_causality.md` (eternity-clause) |
| §2 P7 Mortality | `cards/P07_mortality.md` (eternity-clause) |
| §2 P8 Eternal Reproduction | `cards/P08_eternal_reproduction.md` |
| §2 P9 Single Integument | `cards/P09_single_integument.md` (eternity-clause) |
| §2 P10 Selective Compression | `cards/P10_selective_compression.md` |
| §2 P11 Metabolic Economy | `cards/P11_metabolic_economy.md` |
| §2 P14 Telos | `cards/P14_telos.md` |
| §3 What Myco is NOT | `META.md` §10 (Doctrine Negative Space) |
| §4 Invariants I1-I12 | Distributed across cards' `invariants_enforced` fields + Layer C witnesses |
| §5 Lexicon | `META.md` §9 (Lexicon discipline) |
| §5.2 Dispatch form | `cards/P05_universal_interconnection.md` + L1/TROPISM |
| §5.3 Intent | `cards/P01c_asymmetric_carrier.md` §5.3 + L1/TRAJECTORY |
| §6 Continuity model | `cards/P04_eternal_iteration.md` §3-§4 + L1/CONTINUITY |
| §7 Living Bets | `cards/LB_living_bets.md` (specialized) |
| §8 Operational readiness | `META.md` §1 framing + `cards/LB_living_bets.md` intelligence band |
| §9 Anchor surface | `cards/AS_anchor_surface.md` (specialized; 12 sub-mechanisms consolidated) |
| §9.2.1 birth attestation | `cards/AS_anchor_surface.md` §3.1 |
| §9.2.2 DAG-tip co-signing | `cards/AS_anchor_surface.md` §3.2 |
| §9.2.3 owner attestations | `cards/AS_anchor_surface.md` §3.3 |
| §9.2.4 L0 revision diff | `cards/AS_anchor_surface.md` §3.4 |
| §9.2.5 anchor nonces | `cards/AS_anchor_surface.md` §3.5 |
| §9.2.6 wall-clock | `cards/AS_anchor_surface.md` §3.6 |
| §9.2.7 liveness heartbeat | `cards/AS_anchor_surface.md` §3.7 |
| §9.3.1 canonical-bytes | `cards/AS_anchor_surface.md` §3.8 |
| §9.3.2 owner-side rendering | `cards/AS_anchor_surface.md` §3.9 |
| §9.3.3 anchor-client provenance | `cards/AS_anchor_surface.md` §3.10 |
| §9.3.4 witnesses-not-verdicts | `cards/AS_anchor_surface.md` §3.11 |
| §9.3.5 anchor-nonce-derived sampling | `cards/AS_anchor_surface.md` §3.12 |
| §9.3.6 DAG-enumeration closure | `cards/AS_anchor_surface.md` §3.13 |
| §10 Process | `META.md` §7 (Amendment mechanism) |
| §11 Privacy + Backup | `META.md` §10 (acknowledged absence; L1/SKIN owes) |
| §13.1 Time semantics | `cards/P06_eternal_causality.md` + L1/CONTINUITY + L1/SCHEMA §5 |
| §13.2 Adversarial owner | `cards/COV01_fiduciary_duty.md` + `cards/COV02_cultivators_character.md` + L2/TRUST_MODEL |
| §13.3 Owner mortality / succession | `cards/COV06_no_abandonment_succession.md` + `catechumenate/INDEX.md` + L1/GOVERNANCE §3.2 |
| §13.4 Generation limits | `cards/P08_eternal_reproduction.md` + L1/GOVERNANCE §16 |

**Total coverage**: every section of prior L0 maps to v3.1 artifacts. Nothing dropped silently.

---

## §3. v3.0 → v3.1 schema upgrade (this session)

The v3 form was locked, then immediately upgraded to v3.1 after Phase 3 unknown-unknown hunt returned findings:

| Phase 3 finding | v3.1 integration |
|---|---|
| **Mode 1.4 successor onboarding collapse (pause-worthy)** | Layer D Catechumenate added (META §2.4 + §6 + `catechumenate/INDEX.md`) |
| **Mode 1.1 structural anchor ≠ semantic witness** | Layer C re-typed pointer → witness (META §5; each card has positive + negative + edge triplet) |
| **Mode 1.3 Layer B dead-poetry collapse** | Commentary lifecycle added (META §4.5; each chengyu accumulates lived examples) |
| **Mode 1.6 doctrine aging without update** | Deposit/Formulation distinction added (META §3.5; eternity clauses identified: P01c, P06, P07, P09) |
| **Mode 1.5 Claude model rollover silent drift** | Model-diversity cross-check added (META §7.5; `canonical_dilemma_corpus/`) |
| **Mode 1.7 cultivator fiduciary problem** | Cultivator fiduciary self-report mechanism added (META §7.7; `cultivator_fiduciary_strain` immune signal) |
| **Mode 1.2 cosmetic comment compliance** | Lint rule added (META §5.4; comments must cite witness ID) |

---

## §4. Card production history (in order written)

1. **`META.md`** v3.0 → v3.1 (2026-05-18 session)
2. **`cards/P02_eternal_ingestion.md`** v3.0 → v3.1 — reframe traced to conversation moment correcting Claude's narrow reading of 永恒吞噬
3. **`cards/P01_agent_primary.md`**
4. **`cards/P01c_asymmetric_carrier.md`** — first eternity-clause card written
5. **`cards/P03_resumable_evolution.md`**
6. **`cards/P04_eternal_iteration.md`** — v0.9 request-driven-advance acknowledged as documented debt
7. **`cards/P05_universal_interconnection.md`**
8. **`cards/P06_eternal_causality.md`** — eternity-clause
9. **`cards/P07_mortality.md`** — eternity-clause
10. **`cards/P08_eternal_reproduction.md`**
11. **`cards/P09_single_integument.md`** — eternity-clause
12. **`cards/P10_selective_compression.md`**
13. **`cards/P11_metabolic_economy.md`**
14. **`cards/P14_telos.md`**
15. **`cards/COV01_fiduciary_duty.md`** — new category: Covenant Duty
16. **`cards/COV02_cultivators_character.md`** — drew from Benedict's Rule Ch. 64
17. **`cards/COV03_food_provision.md`**
18. **`cards/COV04_honor_mortality.md`**
19. **`cards/COV05_lineage_stewardship.md`**
20. **`cards/COV06_no_abandonment_succession.md`** — Benedict stability vow
21. **`cards/CHAR01_hungry.md`** — new category: Cultivar Character
22. **`cards/CHAR02_patient.md`**
23. **`cards/CHAR03_mortality_aware.md`** — v3.1.1 amendment: extended to both senses of P07
24. **`cards/CHAR04_interconnected.md`**
25. **`cards/CHAR05_honest_about_self.md`** — anti-ventriloquism
26. **`cards/CHAR06_cautiously_curious.md`** — productive-tension paradox
27. **`cards/CHAR07_caring.md`** — 同体共命 / Bound-Fate (the living symbiote's bond); structural anti-tyranny via shared fate; sister to P07 (P7 prevents bloat-death, CHAR07's bond prevents tyrant-becoming). (Added v3.1.1 as 慈爱 / Caring; reframed v3.1.4.)
28. **`cards/AS_anchor_surface.md`** — specialized (§9 with 12 sub-mechanisms consolidated)
29. **`cards/LB_living_bets.md`** — specialized (§7 with falsifiability + retirement)
30. **`B_chengyu.md`** — 60 fragments B001-B060 (v3.1.1 added B051-B060 for the 应朽 family + 慈爱 traditions)
31. **`canonical_dilemma_corpus/INDEX.md`** — 54 dilemmas D-0001-D-0054 (v3.1.1 added D-0050-D-0054)
32. **`catechumenate/INDEX.md`** — Layer D transmission record (joined Sprint 7.H by `catechumenate/TEMPLATE.md` + `catechumenate/HOW_TO_ADD_A_SESSION.md` scaffolding; still 0 catechumenate sessions toward F21)
33. **This `PROVENANCE.md`** — live document; v3.1.1 amendment recorded below

**Total**: 1 README + 1 META + 28 cards + 1 chengyu file + 1 dilemma INDEX + 3 catechumenate files + this Provenance = **36 files** in `L0/` (was 31 in v3.1; CHAR07_caring.md added in v3.1.1; `catechumenate/TEMPLATE.md` + `catechumenate/HOW_TO_ADD_A_SESSION.md` added Sprint 7.H).

Plus: **Removed** `docs/architecture/L0_VISION.md` from the working tree (text recoverable via `git show e796451:docs/architecture/L0_VISION.md`; SHA-256 of recovered bytes is the `prior_l0_hash` field anchored by M-anchor-5).

---

## §5. Eternity-clause inventory (`deposit_immutable: true`)

Per META §3.5 — cards whose deposit cannot be amended without admitting "this is no longer Myco":

| Card | Why eternity-clause |
|---|---|
| **P01c Asymmetric Carrier** | Without asymmetric carrier, no cultivator-cultivar relation; just a different topology |
| **P06 Eternal Causality** | Substrate IS its causal chain; remove causality and substrate-ID is empty |
| **P07 Mandatory Mortality (必朽)** | Without mandatory internal mortality of 应朽 parts (过时/错误/冗余/无用/等), substrate either bloats to action-paralysis (eternal ingestion uncoupled from disposal) or freezes into hoard. v3.1.1 reading: P07's primary subject is the dying of parts; whole-substrate eventual rest is downstream consequence. |
| **P09 Single Integument** | Multi-skin = identity-dissolved; this is what makes "inside" mean something |

Note: **P02** is NOT eternity-clause despite its centrality. A future cultivar could theoretically live differently (contemplating its own past without external intake) and still be a kind of Myco — though radically different. The deposit is *strongly worth preserving* but not *constitutionally locked*.

---

## §6. v3.1 ship → on-chain anchoring — done in dry-run; production deferred

### §6.1 v3.1 ceremony (2026-05-18)

Status: **dry-run verified, production pending substrate bootstrap.**

Canonical hashes pinned in `operators/claude/ceremonies/v3_1_transition/manifest.json`:

```
prior_l0_hash (SHA-256 of git show e796451:docs/architecture/L0_VISION.md)
             = 5eacf3e7bbb9f8633bcf05266aef24fc27d9ed35bc941c8c2ed50f38233c7f66

new_l0_hash  (BLAKE3 of canonical-bytes Map<rel_path, file_bytes>
              over docs/architecture/L0/**/*.md)
             = b1bec59acc8c5061020640a265a9772e734604425b6eda4b5da1759f9987c699
```

End-to-end ceremony dry-run validated in commit `50a4444` (M-anchor-5 v3.1 transition ceremony: deterministic hashes + dry-run verified). The DAG event emitted in dry-run: `l0_revision_attested:5eacf3e7bbb9f863`.

### §6.2 v3.1.1 → v3.1.1.1 → v3.1.1.2 amendment ceremonies — SEALED (dry-run); production pending owner-key

Status: **all three amendment ceremonies have landed with computed manifests + end-to-end dry-run verification.** Production-mode on-chain seals remain pending the cultivator's owner-key signature.

**v3.1.1 mortality-refinement + 慈爱** — `operators/claude/ceremonies/v3_1_1_mortality_refinement_and_charite/manifest.json`:

```
prior_l0_hash = b1bec59acc8c5061020640a265a9772e734604425b6eda4b5da1759f9987c699
              (i.e., the v3.1 new_l0_hash becomes v3.1.1 prior)
new_l0_hash   = 798c047d592730e20375429706bde1dea3f3da26394891a0a3055de004dff824
diff_summary: |
  v3.1 → v3.1.1: P07 reinterpretation (mandatory internal mortality of 应朽 parts
  as primary; whole-substrate ending as downstream boundary). CHAR07 慈爱 added
  as developmental anti-tyranny character (sister to P07's bloat-death prevention).
  Slogan refinements: P07 能朽 → 必朽; COV04 敬其能朽 → 敬其必朽.
  Doctrine list discipline: 应朽 family marked as illustrative-not-exhaustive
  (`包括但不限于`), with L1 authorized to recognize new family members.
  Cascading edits to ~10 cards + META + B_chengyu + canonical_dilemma_corpus +
  selected L1/L2 docs.
```

**v3.1.1.1 P03 descriptive amendment** — `operators/claude/ceremonies/v3_1_1_1_p03_descriptive_amendment/manifest.json` (Sprint 6.D + 7.H/7.I): chains from v3.1.1's `798c047d…`; `new_l0_hash = 7267dc58aa81d3dcd7ef08c3f83d49b0b0ab9b910f72a7a51c92d181c7eae4ba` (clean-LF seal). Reframed P03 §3.3/§4.3/§5.2/§7.1 to the shipping snapshot-rollback behavior + added §10.4; added catechumenate scaffolding; normalized ~70 cross-reference paths.

**v3.1.1.2 descriptive amendment** — `operators/claude/ceremonies/v3_1_1_2_descriptive_amendment/manifest.json`: chains from v3.1.1.1's `7267dc58…`; `new_l0_hash = cda9e2b32d505ae1a5acb2d4d71282f63385381c07b8fa3f845f6d2bad033784`. Corrects stale descriptive facts to shipped reality (file/card/fragment/dilemma counts; P03 §10.4 migration shipped opt-in via `migration.rs` + `C66`; ceremony-status; catechumenate "empty"→scaffolding present). Deposits unchanged.

**v3.1.2 witness-corpus amendment** — `operators/claude/ceremonies/v3_1_2_witness_corpus/manifest.json` (this amendment): chains from v3.1.1.2's `cda9e2b3…`. The v0.9.x witness-corpus milestone (META §5.2/§5.5/§5.6): all 28 cards' Layer C witnesses re-pointed from the never-created `tests/integration/*` placeholders to real artifacts — runnable substrate tests for the 16 `kind: executable` cards, `canonical_dilemma_corpus` references for the 12 `kind: narrative` cards — plus the `kind:` discriminator; structural anchors de-danged to their real homes; the §5.5 existence-level witness-lint shipped (`operators/claude/tests/witness_lint.test.ts`) with **C67 `doctrine_witness_drift`** assigned as its CI-lint signal; P07/CHAR07/P05's stale "to be added in v3.1.1 cascade" markers scrubbed to shipped reality; META §10 backup-encryption debt marked resolved. Deposits + formulations unchanged — Layer C / descriptive only per §7.

**v3.1.3 autonomy + detectors amendment** — `operators/claude/ceremonies/v3_1_3_autonomy_and_detectors/manifest.json`: chains from v3.1.2's `69456132…`; `new_l0_hash = b22dca68b23db605e50030dc108d8cd69b0b0f040d5b0dec67130723cfa34ecd`. Descriptive debt→shipped (P04 production self-advance; CHAR01/P02 proactive-hunger; C74 starvation immune; C40 bet-weakening quorum; C24 telos_drift_critical reachable; C75 cultivator_fiduciary_strain) + the ~7 nearest-available Layer-C witnesses replaced with exact-polarity tests + META §5.5 run-and-verify LIVE. Deposits + formulations unchanged (META §7).

**v3.1.4 symbiotic-armor-identity amendment** — `operators/claude/ceremonies/v3_1_4_symbiotic_armor_identity/manifest.json`: chains from v3.1.3's `b22dca68…`. The **CHAR07 reframe — 慈爱 (compassionate moral love) → 同体共命 (the living symbiote's structural bond)**. Anti-tyranny and the "more-than-alignment-optimization" demand are RELOCATED from a *cultivated moral character* to the *shared-fate structure of the symbiotic bond*: the carrier cannot thrive by harming the body it lives in. Cascading edits: CHAR07 card body (full reframe — id/filename/`deposit_immutable:false`/the 5 falsifiability signals + all `substrate/src` anchors + node-type identifiers UNCHANGED, bond-neutral); the CHAR07-asserting cross-refs in P14 §9 / P07 §7.3+§9 / META §3.5; B_chengyu §11.bis + canonical_dilemma_corpus §49.bis glosses. File/card/CHAR counts UNCHANGED (36/28/7); zero substrate code-behavior change. Routine §7.1 amendment (CHAR07 non-eternity); the four eternity clauses untouched. Origin: cultivator's clarification that Myco is a *living symbiotic armor* (the Venom intuition) — alive and fiercely bonded, aligned by shared fate, not moral virtue.

Ceremony chain: `e796451 (DRAFT 9) → b1bec59a (v3.1) → 798c047d (v3.1.1) → 7267dc58 (v3.1.1.1) → cda9e2b3 (v3.1.1.2) → 69456132 (v3.1.2-witness-corpus) → b22dca68 (v3.1.3-autonomy-and-detectors) → <v3.1.4 new_l0_hash> (v3.1.4-symbiotic-armor-identity)`. Each transition is an `l0_revision_attested:{prior_prefix}` DAG event chaining back to the previous.

### §6.3 Bundle definition

`new_l0_hash` computed over a canonical-bytes-serialized Map<relative_path, file_bytes> of **every `.md` under `docs/architecture/L0/`** (36 files as of v3.1.1.2), sorted by path:
- `META.md`
- `README.md`
- `PROVENANCE.md` (this file)
- `B_chengyu.md`
- `cards/*.md` (alphabetical; 28 cards, incl. `CHAR07_caring.md`)
- `canonical_dilemma_corpus/INDEX.md`
- `catechumenate/INDEX.md`, `catechumenate/TEMPLATE.md`, `catechumenate/HOW_TO_ADD_A_SESSION.md`

Hash function: BLAKE3 (per L1/SCHEMA §2.1 default; F16 canonical-bytes serializer). Implementation: the shared `operators/claude/ceremonies/_lib/` machinery (`bundle_hash.ts` + `ceremony.ts`); each amendment ceremony directory carries a thin `config.ts` + `compute_hashes.ts` + `manifest.json` (the v3.1-transition ceremony's original `compute_hashes.ts` was refactored into `_lib` so subsequent ceremonies share one canonical-bytes implementation).

### §6.4 v3.1.1 amendment provenance — the conversation that drove it

This amendment originated in a multi-turn cultivator-Claude conversation (2026-05-18 → 2026-05-19) refining the final-vision picture. Five successive corrections deepened Claude's reading:

1. **Higher abstraction needed** — Claude was listing facts, not telling story
2. **Wrong primary frame** — not "cultivation relationship returning", but **永恒吞噬 + 永恒进化 主导的图景**
3. **Even more grounded frame** — not just "process being", but **"a partner that gets stronger and stays current"**
4. **Specific shape**: **paradigm-level + both-directions + mentor/elder direction (智者 / 导师)**
5. **P07 reinterpretation** — 必朽 is mandatory dying-of-parts, not the whole; and tyranny-prevention is **CHAR07 慈爱**'s job, not P07's. Cultivator's correction: "成神也没关系，但是别成暴君，神爱世人，作为伙伴也并无不妥"
6. **List discipline**: 过时/错误/冗余/无用 are canonical exemplars of the open-ended 应朽 family, not exhaustive — `包括但不限于` framing required.

The amendment ratifies cultivator's framing #5 + #6 into the doctrine itself. The memory snapshot at `memory/myco_telos_2026-05-19.md` carries the conceptual panorama; this PROVENANCE entry carries the doctrinal provenance.

---

## §7. Reading v3.1 — the discipline

For a cold reader (new Claude after model rollover; future cultivator-B at succession; an external reviewer):

1. **First**: read `META.md` end-to-end. Understand the four-layer form and the running mechanism.
2. **Second**: read `cards/P01_*` through `cards/P14_*` in P-number order to understand what kind of entity Myco is.
3. **Third**: read `cards/COV01_*` through `cards/COV06_*` to understand what the cultivator owes.
4. **Fourth**: read `cards/CHAR01_*` through `cards/CHAR07_*` to understand the cultivar's character (7 cards as of v3.1.1).
5. **Fifth**: read `cards/AS_*` and `cards/LB_*` for the cryptographic root and the falsifiability machinery.
6. **Sixth**: read `B_chengyu.md` end-to-end, letting fragments cross-resonate.
7. **Seventh**: sample `canonical_dilemma_corpus/INDEX.md` — read setups, produce your own reading without seeing prior interpretations.
8. **Eighth**: read `catechumenate/INDEX.md` to understand the transmission mechanism (scaffolded — INDEX + TEMPLATE + HOW_TO_ADD_A_SESSION — with zero sessions yet).
9. **Last**: this `PROVENANCE.md` for the chain back to the prior monolithic form.

Returning readers may sample any layer; the cold-reader discipline is for first encounters.

---

## §8. What this doctrine is missing (acknowledged debt)

- **Catechumenate sessions**: 0 currently exist. Until cultivator-A begins succession preparation, none will exist. This is architecturally committed, not implementationally satisfied.
- **Layer C witness tests**: re-pointed to real artifacts + the existence-level §5.5 lint is live (v3.1.2 witness-corpus; META §5.2/§5.6). The run-and-verify-polarity clause + the ~7 *nearest-available* exact-witness slots accrue as maturity anchoring per §5.6.
- **Layer B fragment commentary**: 0 commentary entries currently exist. They will accumulate as the cultivator-Claude pair invokes fragments in real decisions.
- **Canonical dilemma `Claude-of-record readings`**: 54 dilemmas have setups; 0 have recorded interpretations. They will accumulate at model rollovers + drift investigations + catechumenate sessions.
- **Backup encryption (L1/SKIN §8 + L0/META §10)**: **implemented** (Sprint 2.C / 6.K) — the at-rest seal (`substrate/src/at_rest_seal.rs`; Windows DPAPI over `dag.cb` / `manifest.cb`) + the cultivator-owned status SSoT (`substrate/src/events/backup_encryption.rs`, L1/SKIN §8: the cultivator holds the key, the substrate persists only a public status field). Cross-platform KMS beyond DPAPI is L1/SKIN follow-on, not an L0 gap.

  *Resolved 2026-05-18*: L1/L2/L3/algorithms/schemas/diagrams + source-code comments surgically updated from prior "L0 §X.Y" monolithic citations to v3.1 "L0/cards/<card> §N" form per §2 mapping table.

These debts are *named*. The doctrine's discipline against drift is precisely that debts are named, not silently carried.

---

**Provenance commitment**: every section of prior L0 maps to v3.1; nothing dropped silently; eternity clauses identified; on-chain anchoring deferred to cultivator approval; debts named.
