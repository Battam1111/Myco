# Doctrine Outline / Charter

> Navigation only; L1/L2 documents are authoritative. **L1** = mechanism enforcement layer (positive forms; "how does substrate do X?"). **L2** = cross-cut themes citing L1.

---

## §1. Document set

**L0** (1 doc): `L0_VISION.md` — 12 principles, 11 invariants, dispatch constraints, Living Bets, anchor surface, L1/L2-deferred topics.

**L1** (7 docs, mechanism enforcement):

| File | Topic |
|---|---|
| `L1_TROPISM.md` | Positive dispatch form (atomic-record); salience (P12 landed); telos metric (P14) |
| `L1_TRAJECTORY.md` | Positive intent-derivation; cluster_C; injection defense; intent cross-cut |
| `L1_SCHEMA.md` | SSoT, Merkle DAG, recoverability, spore-schema, validation tiers, canonical-bytes |
| `L1_GOVERNANCE.md` | I2 classifier, lifecycle, attestation, Cultivation succession, federation discovery, evolution cross-cut, generation limits, F18-F25 |
| `L1_SKIN.md` | I8 envelope, handshake, single-operator, network-egress, spatial-locus (P13 fold), backup, restart, breach detection |
| `L1_CONTINUITY.md` | Metabolic cycle, dormancy, recovery, delta atomicity, lifecycle regime cross-cut |
| `L1_HARD_RULES.md` | C-row catalog (CRITICAL breaches), F-row catalog (CI fixed-points), anchor-resident state |

**L2** (3 docs, cross-cut themes that don't fold into a single L1 host):

| File | Theme |
|---|---|
| `L2_TRUST_MODEL.md` | Trust triad + adversarial Cultivator + honor-system collapse window |
| `L2_FEDERATION.md` | P15 consensus floor + wrapped-events + Ed25519 mutual auth + recursive injection defense |
| `L2_OBSERVABILITY.md` | Living Bets canonical + immune catalog cross-cut + drill baseline + falsifiability summary |

**Implementation map** (out-of-doctrine, in `docs/implementation/`): `L3_OUTLINE.md`, `L3_PACKAGE_MAP.md`.

---

## §2. L0 design hooks → L1/L2 ownership

| L0 reference | Owner |
|---|---|
| §1 Cultivation / pair / governance | L1_GOVERNANCE §3 (succession) |
| §2 principles → invariants | L1 docs per projection table (L0 §4) |
| §5.2 dispatch form | L1_TROPISM |
| §5.3 intent | L1_TRAJECTORY |
| §6 continuity + metabolic cycle + dormancy + delta atomicity | L1_CONTINUITY |
| §7 Living Bets observatory | L2_OBSERVABILITY (canonical) |
| §7.4 falsifiability quorum | `algorithms/bet_weakening_quorum.md` |
| §7.5 bet retirement | L0 + L2_OBSERVABILITY §3 |
| §9 anchor surface | L1_GOVERNANCE §2 (mechanism) |
| §9.2 sub-mechanism milestones | `docs/implementation_status.md` |
| §10 process | this §3 |
| §11 privacy + backup | L1_SKIN §8 |
| §13.1 time semantics | L1_CONTINUITY + L1_SCHEMA |
| §13.2 adversarial owner | L2_TRUST_MODEL §10 |
| §13.3 owner mortality / succession | L1_GOVERNANCE §3.2 + `diagrams/cultivation_succession_fsm.txt` |
| §13.4 generation limits | L1_GOVERNANCE §16 |
| I1 lifecycle + sub-states | L1_CONTINUITY + L1_GOVERNANCE §3.2 |
| I2 classifier | L1_GOVERNANCE §1 |
| I3 SSoT + migration | L1_SCHEMA §1 |
| I4 DAG + Merkle + retention | L1_SCHEMA §2 |
| I5 reachability + tier exemptions | L1_SCHEMA §2.3 |
| I6 inclusion + appetite-locality + network-egress | L1_TROPISM + L1_SKIN |
| I7 closure + peer-trust | L1_SCHEMA §3.3 + L1_GOVERNANCE §5 |
| I8 single-skin + envelope + handshake | L1_SKIN |
| I9 compression discipline | L1_SCHEMA + L1_GOVERNANCE §15.F18 |
| I10 cost observation | L2_OBSERVABILITY + L1_GOVERNANCE §15.F19 |
| I12 telos alignment | L1_TROPISM §F + L1_GOVERNANCE §15.F20 |

Every L0 design hook has an owner.

---

## §3. Cross-document discipline

- L1/L2 mutations classify CI per I2; same proposal-and-approval as L0; burst threshold L1-tunable.
- When L1 work reveals L0 constraint unworkable, L1 doc records finding + proposes L0 revision (per L0 §10).
- L1_GOVERNANCE §1.2 classifier dimension table = canonical for classification.
- Cross-cut content lives at mechanism host (e.g., lifecycle regime in L1_CONTINUITY §6; evolution in L1_GOVERNANCE §6); L2 reserved for genuine multi-host themes (trust + federation + observability).
- Extracted content: JSON schemas in `schemas/`; algorithms + pseudocode in `algorithms/`; ASCII diagrams + FSM + dependency graphs in `diagrams/`.
- Audit + provenance: `docs/audits/` (Phase α/β/γ/δ + DRAFT 9 sealing).
