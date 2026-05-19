# Myco Doctrine — Top-Level Outline

> Navigation document. The **canonical L0 doctrine** is in [`L0/`](L0/) (v3.1-stratigraphy, 2026-05-18). L1/L2 documents are authoritative for their respective layers but **defer to L0** on conflicts.

---

## §1. Document set (v3.1)

### L0 — Canonical doctrine (4-layer stratigraphy + running mechanism)

Lives in [`L0/`](L0/). Entry point: [`L0/README.md`](L0/README.md).

**Form documents**:
- [`L0/META.md`](L0/META.md) — how the doctrine is structured (form specification, 14-field card schema)
- [`L0/PROVENANCE.md`](L0/PROVENANCE.md) — supersession chain + complete prior-L0 mapping table
- [`L0/README.md`](L0/README.md) — directory entry point + 4 reading paths

**Layer A — Principle cards** (26 cards in [`L0/cards/`](L0/cards/)):

| Card type | Cards |
|---|---|
| Postulates (12) | P01 / P01c (eternity) / P02 / P03 / P04 / P05 / P06 (eternity) / P07 (eternity) / P08 / P09 (eternity) / P10 / P11 / P14 |
| Cultivator's Covenant (6) | COV01-COV06 |
| Cultivar Character (6) | CHAR01-CHAR06 |
| Specialized (2) | AS_anchor_surface (§9 with 12 sub-mechanisms) / LB_living_bets (§7 with falsifiability + retirement) |

**Layer B** — Generative-image fragments in [`L0/B_chengyu.md`](L0/B_chengyu.md) (50 chengyu, read end-to-end).

**Layer C** — Witness-anchored doctrine: each card's `witnesses` field declares positive + negative + edge test triplet. Substrate code carries reverse comments citing witness IDs (META §5.4 lint rule).

**Layer D** — Catechumenate transmission: [`L0/catechumenate/`](L0/catechumenate/) (empty until succession preparation begins).

**Canonical dilemma corpus**: [`L0/canonical_dilemma_corpus/`](L0/canonical_dilemma_corpus/) (49 setups for model-diversity cross-check).

### L1 — Mechanism enforcement (7 docs)

| File | Topic |
|---|---|
| [`L1/TROPISM.md`](L1/TROPISM.md) | Positive dispatch form (atomic-record); salience (P12 landed); telos metric (P14 / F20) |
| [`L1/TRAJECTORY.md`](L1/TRAJECTORY.md) | Positive intent-derivation; cluster_C; injection defense; intent cross-cut |
| [`L1/SCHEMA.md`](L1/SCHEMA.md) | SSoT, Merkle DAG, recoverability, spore-schema, validation tiers, canonical-bytes |
| [`L1/GOVERNANCE.md`](L1/GOVERNANCE.md) | I2 classifier, lifecycle, attestation, Cultivation succession, federation discovery, evolution cross-cut, generation limits, F18-F25 |
| [`L1/SKIN.md`](L1/SKIN.md) | I8 envelope, handshake, single-operator, network-egress, spatial-locus (P13 fold), backup, restart, breach detection |
| [`L1/CONTINUITY.md`](L1/CONTINUITY.md) | Metabolic cycle, dormancy, recovery, delta atomicity, lifecycle regime cross-cut |
| [`L1/HARD_RULES.md`](L1/HARD_RULES.md) | C-row catalog (CRITICAL breaches), F-row catalog (CI fixed-points), anchor-resident state |

### L2 — Cross-cut themes (3 docs)

| File | Theme |
|---|---|
| [`L2/TRUST_MODEL.md`](L2/TRUST_MODEL.md) | Trust triad + adversarial Cultivator + honor-system collapse window |
| [`L2/FEDERATION.md`](L2/FEDERATION.md) | P15 consensus floor + wrapped-events + Ed25519 mutual auth + recursive injection defense |
| [`L2/OBSERVABILITY.md`](L2/OBSERVABILITY.md) | Living Bets canonical + immune catalog cross-cut + drill baseline + falsifiability summary |

### Implementation map

Out-of-doctrine, in [`docs/architecture/L3/`](L3/): `L3/OUTLINE.md`, `L3/PACKAGE_MAP.md`.

---

## §2. Reading paths

### Path 1 — Newcomer (2-3 hours)

1. [`L0/README.md`](L0/README.md) — get the shape
2. [`L0/META.md`](L0/META.md) — understand the form
3. [`L0/cards/P01_agent_primary.md`](L0/cards/P01_agent_primary.md) → P02 → P14 — substantive doctrine sample
4. [`L0/cards/COV01_*.md`](L0/cards/COV01_fiduciary_duty.md) + [`CHAR01_*.md`](L0/cards/CHAR01_hungry.md) — covenant + character
5. [`L0/B_chengyu.md`](L0/B_chengyu.md) — read end-to-end
6. Skim L1 / L2 for mechanisms

### Path 2 — Implementing something

1. Find the relevant L0 card (or query L0/cards/ by id)
2. Read its `witnesses` field + `structural_anchors` field
3. Locate L1 mechanism doc (via PROVENANCE §2 table if reference uses old `L0 §x.y` notation)
4. Write code with reverse-comments per META §5.4 lint rule

### Path 3 — Reviewing a doctrine change

1. [`L0/META.md`](L0/META.md) §3.5 (deposit / formulation) + §7 (amendment mechanism)
2. Relevant card's Provenance section
3. [`L0/PROVENANCE.md`](L0/PROVENANCE.md) cross-reference

### Path 4 — Cold-reader audit (model rollover / drift investigation)

1. [`L0/canonical_dilemma_corpus/INDEX.md`](L0/canonical_dilemma_corpus/INDEX.md) — produce your own readings without seeing prior interpretations
2. Compare against recorded `Claude-of-record` readings (when they exist)
3. Divergence beyond threshold → `doctrine_reading_drift` immune signal

---

## §3. L0 reference resolution (for L1/L2 cross-refs in old notation)

L1/L2/L3 documents may still contain references in the old `L0 §x.y` notation (e.g., "L0/cards/AS_anchor_surface.md §3.5"). These resolve to v3.1 cards per [`L0/PROVENANCE.md`](L0/PROVENANCE.md) §2 mapping table. **Surgical update of these references is deferred to a subsequent housekeeping pass** (coupled with v0.9.x witness corpus implementation per META §5.4 lint rule — both involve updating same files).

Until then, readers consult PROVENANCE §2 for two-hop resolution.

---

## §4. Cross-document discipline

- L1/L2 mutations classify CI per I2 (now [`P01 §3.4`](L0/cards/P01_agent_primary.md)); same proposal-and-approval as L0; burst threshold L1-tunable.
- When L1 work reveals an L0 constraint unworkable, L1 doc records finding + proposes L0 revision per [`L0/META.md`](L0/META.md) §7.
- L1/GOVERNANCE §1.2 classifier dimension table = canonical for classification.
- Cross-cut content lives at mechanism host (e.g., lifecycle regime in L1/CONTINUITY §6; evolution in L1/GOVERNANCE §6); L2 reserved for genuine multi-host themes (trust + federation + observability).
- Extracted content: JSON schemas in `schemas/`; algorithms + pseudocode in `algorithms/`; ASCII diagrams + FSM + dependency graphs in `diagrams/`.
- Audit + provenance: `docs/audits/` (Phase α/β/γ/δ + DRAFT 9 sealing + v3.1-stratigraphy genesis).

---

## §5. Eternity-clause cards

Cards whose deposit cannot be amended without admitting "this is no longer Myco" (per [`META.md`](L0/META.md) §7.6):

- [`P01c`](L0/cards/P01c_asymmetric_carrier.md) — asymmetric carrier
- [`P06`](L0/cards/P06_eternal_causality.md) — eternal causality
- [`P07`](L0/cards/P07_mortality.md) — mortality
- [`P09`](L0/cards/P09_single_integument.md) — single integument

Amendment requires `species_redefinition_proposal` ritual (META §7.6).

---

**This outline is itself L0 in the form-only sense (navigation, not substantive doctrine).** Conflicts with substantive cards → cards win.
