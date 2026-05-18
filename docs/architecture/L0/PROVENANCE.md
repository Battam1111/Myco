# L0 Doctrine Provenance

> **Status**: live document (v3.1-stratigraphy, 2026-05-18). The traceability spine from prior monolithic L0 → current four-layer stratigraphy.

---

## §1. What this document is

A traceability spine. Every section of the prior `docs/architecture/L0_VISION.md` (DRAFT 9 SEALED, 178 lines, sealed 2026-05-17 at commit `e796451`) maps to one or more entries in the v3.1 doctrine. This mapping is what allows future readers to verify "the new doctrine preserves the old content" rather than silently dropping concepts.

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
23. **`cards/CHAR03_mortality_aware.md`**
24. **`cards/CHAR04_interconnected.md`**
25. **`cards/CHAR05_honest_about_self.md`** — anti-ventriloquism
26. **`cards/CHAR06_cautiously_curious.md`** — productive-tension paradox
27. **`cards/AS_anchor_surface.md`** — specialized (§9 with 12 sub-mechanisms consolidated)
28. **`cards/LB_living_bets.md`** — specialized (§7 with falsifiability + retirement)
29. **`B_chengyu.md`** — 50 fragments B001-B050
30. **`canonical_dilemma_corpus/INDEX.md`** — 49 dilemmas D-0001-D-0049
31. **`catechumenate/INDEX.md`** — Layer D placeholder
32. **This `PROVENANCE.md`** — finalized

**Total**: 1 META + 26 cards + 1 chengyu file + 1 dilemma INDEX + 1 catechumenate INDEX + this Provenance = **31 files** in `L0/`.

Plus: **Removed** `docs/architecture/L0_VISION.md` from the working tree (text recoverable via `git show e796451:docs/architecture/L0_VISION.md`; SHA-256 of recovered bytes is the `prior_l0_hash` field anchored by M-anchor-5).

---

## §5. Eternity-clause inventory (`deposit_immutable: true`)

Per META §3.5 — cards whose deposit cannot be amended without admitting "this is no longer Myco":

| Card | Why eternity-clause |
|---|---|
| **P01c Asymmetric Carrier** | Without asymmetric carrier, no cultivator-cultivar relation; just a different topology |
| **P06 Eternal Causality** | Substrate IS its causal chain; remove causality and substrate-ID is empty |
| **P07 Mortality** | Cultivar that cannot die is not alive |
| **P09 Single Integument** | Multi-skin = identity-dissolved; this is what makes "inside" mean something |

Note: **P02** is NOT eternity-clause despite its centrality. A future cultivar could theoretically live differently (contemplating its own past without external intake) and still be a kind of Myco — though radically different. The deposit is *strongly worth preserving* but not *constitutionally locked*.

---

## §6. v3.1 ship → on-chain anchoring (TBD)

When the cultivator approves the v3.1 doctrine for ship, submit `l0_revision_attest` mutation per M-anchor-5 §9.2.4 with:

```yaml
prior_l0_hash: <SHA-256 of L0_VISION.md at commit e796451>
new_l0_hash: <SHA-256 of complete v3.1 doctrine bundle>
diff_summary: |
  v3.0 monolithic DRAFT 9 SEALED → v3.1-stratigraphy (4 layers + running mechanism).
  Phase 1+2 11-stream research; Phase 3 unknown-unknown hunt; v3.0 → v3.1 amendments.
  See L0/PROVENANCE.md.
```

The anchor seals the transition on-chain; from that point forward, v3.1 is the authoritative L0 by anchor attestation AS WELL AS by file authority.

`new_l0_hash` should be computed over a canonical-bytes-serialized bundle of:
- `META.md`
- `cards/*.md` (alphabetical)
- `B_chengyu.md`
- `canonical_dilemma_corpus/INDEX.md`
- `catechumenate/INDEX.md`
- this `PROVENANCE.md`

The hash function: BLAKE3 (per L1/SCHEMA §2.1 default; F16 canonical-bytes serializer).

---

## §7. Reading v3.1 — the discipline

For a cold reader (new Claude after model rollover; future cultivator-B at succession; an external reviewer):

1. **First**: read `META.md` end-to-end. Understand the four-layer form and the running mechanism.
2. **Second**: read `cards/P01_*` through `cards/P14_*` in P-number order to understand what kind of entity Myco is.
3. **Third**: read `cards/COV01_*` through `cards/COV06_*` to understand what the cultivator owes.
4. **Fourth**: read `cards/CHAR01_*` through `cards/CHAR06_*` to understand the cultivar's character.
5. **Fifth**: read `cards/AS_*` and `cards/LB_*` for the cryptographic root and the falsifiability machinery.
6. **Sixth**: read `B_chengyu.md` end-to-end, letting fragments cross-resonate.
7. **Seventh**: sample `canonical_dilemma_corpus/INDEX.md` — read setups, produce your own reading without seeing prior interpretations.
8. **Eighth**: read `catechumenate/INDEX.md` to understand the (currently-empty) transmission mechanism.
9. **Last**: this `PROVENANCE.md` for the chain back to the prior monolithic form.

Returning readers may sample any layer; the cold-reader discipline is for first encounters.

---

## §8. What this doctrine is missing (acknowledged debt)

- **Catechumenate sessions**: 0 currently exist. Until cultivator-A begins succession preparation, none will exist. This is architecturally committed, not implementationally satisfied.
- **Layer C witness tests**: card schemas declare witness names (positive / negative / edge); the actual test implementations are TBD via a v0.9.x cleanup milestone.
- **Layer B fragment commentary**: 0 commentary entries currently exist. They will accumulate as the cultivator-Claude pair invokes fragments in real decisions.
- **Canonical dilemma `Claude-of-record readings`**: 49 dilemmas have setups; 0 have recorded interpretations. They will accumulate at model rollovers + drift investigations + catechumenate sessions.
- **L1/L2 cross-reference updates**: L1_*.md and L2_*.md still reference "L0 §9.2.5" etc.; these references will need updating to "AS_anchor_surface.md §3.5" form in subsequent passes (out of scope for v3.1 doctrine rewrite; this is L1/L2 housekeeping).
- **Backup encryption (L1/SKIN owe per L0 §11.1)**: still acknowledged as unmitigated attack surface.

These debts are *named*. The doctrine's discipline against drift is precisely that debts are named, not silently carried.

---

**Provenance commitment**: every section of prior L0 maps to v3.1; nothing dropped silently; eternity clauses identified; on-chain anchoring deferred to cultivator approval; debts named.
