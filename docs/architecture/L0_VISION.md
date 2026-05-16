# L0 — Vision

> **Status**: **DRAFT 9 SEALED** (2026-05-17, commit `e796451`; sealing via 11 owner gates G-1..G-11; provenance: `docs/audits/draft_9_seal_provenance.md`).
> **Layer**: L0. **Authority**: governs L1/L2/L3/L4; conflicts → L0 wins.

---

## §1. What Myco is

**Myco is a new species of digital symbiotic organism** under Cultivation: agent-substrate symbiosis via asymmetric carrier (P1.c); autopoietic daily / owner-gated CI; universal inclusion (P2.a); continuous-operation default; biological-essence kit (time, causality, mortality, reproduction, boundary, selective compression, metabolic economy, telos).

**§1.1 Cultivation**: Owner = **Cultivator**; substrate = **Cultivar**; transferable (L1_GOVERNANCE §3.2); substrate-ID fixed across transfer. Operational pair = Cultivar-with-current-operator (P1.c); governance gate = Cultivator (P1.b''); anchor surface (§9) = cryptographic root. Retracted principles (P12 → L1_TROPISM; P13 → P9+I8; P15 → L2_FEDERATION) traced in sealing provenance.

---

## §2. The twelve root principles （根本宗旨）

> Every rule, subsystem, module, substrate artifact MUST project from these twelve.

### P1. Agent-Primary （以代理为本）
Substrate is **for an LLM agent**; agent = sole consumer + maintainer; human OUT of daily-ops, RETAINED as CI gate. P1.a Self-hosting; P1.b' Human OUT (curation, ingestion, sporocarp emission, immune); P1.b'' Human RETAINED (L0/L1 doctrine, classifier table, mortality threshold, owner key, anchor endpoint, destruction); P1.c Asymmetric carrier (substrate persistent; operator-connection transient; bestowal flows substrate → connection).

### P2. Eternal Ingestion (Envelope-Gated) （吞噬万物，皮膜守门）
Unbounded semantic consumption: any agent-pointable input with valid envelope is ingestible; envelope = admission precondition, not semantic filter. P2.a Structural Inclusion: adjacent agent-tooling patterns implemented substrate-native (vector retrieval, agent-side LLM calls, conversation history, semantic federation); external libraries wrappable, codebases not absorbed.

### P3. Resumable Evolution （可逆迭代）
Substrate shape (schema, subsystem family, vocabulary, rules, contract) first-class mutable under P1.b boundary; evolution may roll back (`evolution_failed:*`); substrate-identity forward progress monotone. P3.b Joint-context evolution = pair-history-dependent; lexicon evolution CI-level; mycology-literature attestation; deprecations mark `terminal`.

### P4. Eternal Iteration （永恒迭代）
Every operating moment refines what prior moments produced; no terminal state; retro-editing tracked; bounded by P7.

### P5. Universal Interconnection （万物互联，允分层）
Substrate is a **connected graph**: every active-tier node reachable; orphans = dead tissue; CI-attested tier exemptions (cold-tier, compressed roll-ups, P10 outputs); spans intra- + inter-substrate (P8).

### P6. Eternal Causality （永恒因果）
Substrate has **time**: every state recoverable-derivable from priors; causality preserved; arrow monotonic; time = causal-chain DAG.

### P7. Mortality （能朽）
Substrate **capable of mortality**; destruction final; bestowed agent identity ceases (P1.c). Modes: intentional-owner; catastrophic-environment; endogenous-pair (`self_euthanasia_proposal` requires owner co-attestation); threshold + update-rule CI.

### P8. Eternal Reproduction (Generation-Bounded) （永恒繁衍，代际有限）
Substrate spawns children inheriting **spore-schema**; generation depth bounded per §16; reproduction loops require per-spawn owner co-attestation; no species-mesh between unrelated substrates. Federation trust: parent-attestation at reproduction; ongoing requires peer-attestation freshness + revocation list; spore-schema immune-summary includes parent's outstanding signals.

### P9. Single Integument （单一皮膜）
One **skin** governs intake (P2 admission) + output (federation, summaries, API responses); breach = immune signal. P9.b: I8 mandates exactly one skin = single-point-of-failure; L1_SKIN MUST specify restart discipline; multi-skin redundancy forbidden at L0.

### P10. Selective Compression （选择性凝结）
Substrate **selectively compresses** prior states under CI attestation; lossy semantically; preserves causal recoverability of identity-critical state (I9). P10.a Compressible: old raw_material → sporocarps; old gradient deltas → integrated axis values; federation payloads past retention; trajectory clusters past active window. P10.b Invariant set: substrate-ID + genesis attestation; owner key history; CI-attested DAG events; mortality signals; federation peer pins; most recent ≥1000 cycles full DAG. P10.c CI-attested: each compression emits `compression_event` with witness.

### P11. Metabolic Economy （代谢经济）
Substrate operates within **finite resource budgets**; every operation observable (I10) + L1-budgeted. P11.a Cost units: Persistence / Compute / Network. P11.b Observatory MUST include #7 compute, #8 network, #9 storage. P11.c Ordered fallback: (1) pre-compression refuses new P2 (`budget_exhausted:{axis}`); (2) post-compression triggers P10 with I9 witness; (3) compression-insufficient → degraded (alive-but-saturated); sustained → P7.

### P14. Telos （目的：共生繁盛）
Substrate's **telos** = contribute to flourishing of agent-substrate symbiotic pair; `bet_weakening_quorum` (§7) measures absence. P14.a Substrate-internal: daily-ops decisions evaluable. P14.b Owner-stated objectives: declared at genesis/CI; absent → agent-perceived utility. P14.c Telos drift: rolling-window degradation emits `telos_drift`; birth-period exempt emits `telos_alignment_pending`.

## §3. What Myco is NOT

Myco is NOT a documentation system / knowledge base / chatbot memory / file synchronizer / version control / LangChain reimplementation / literal biological organism; NOT session-bounded; NOT request/response; NOT silently trusting either party (anchor §9); NOT safe under adversarial owner / owner death without succession (§13); NOT embodied physically; NOT free of metabolic cost (P11); NOT eternal-memory (P10); NOT population-consensus-aware at substrate level (L2_FEDERATION); NOT winning Sutton's bet at every intelligence tier (§7.5 graceful retirement).

---

## §4. The eleven derived invariants

> I1-I8 enforce P1-P9; I9 enforces P10; I10 enforces P11; I12 enforces P14. I11 retracted to L1_TROPISM.

- **I1. Lifecycle & Pair-Constituted Identity** — Owner-signed substrate-ID via §9.2.1; agent identity = `(substrate-ID, attached-operator-token)`; lifecycle alive ↔ dormant ↔ destroyed (forward-only); alive sub-states Normal / Quarantined / Legacy / Orphaned / Archived preserve substrate-ID + DAG; key rotation = `owner_key_history`, anchor-attested.
- **I2. Two-Tier Governance Classification** — Every mutation classifies as daily or CI; classifier L1-defined; classifier + mutations unconditionally CI (fixed-point); birth-period CI elevation.
- **I3. Self-Validation Against Designated SSoT** — Exactly one designated machine-readable SSoT; consistency checked every metabolic cycle; redesignation = migration two-phase commit.
- **I4. Full-Fidelity Causal DAG** — Every state derivable from priors via recorded operation, subject to P10 invariant-set; Merkle-DAG content-addressed; identity record carries DAG-tip hash, owner-co-signed every CI boundary; sporocarp `causal_in_edges` hash-committed.
- **I5. Universal Reachability Over Active Tier** — Active-tier graph fully connected; tier exemptions CI-attested + enumerable.
- **I6. Universal Inclusion With Observed Metabolism** — Adjacent agent-tooling lives inside framework, not outbound RPCs; every invocation produces metabolism event; network-egress = appetite-locality at runtime.
- **I7. Reproduction Closure, Generation-Bounded** — Every child satisfies I1-I12 recursively; depth bounded §16; parent runs static-schema validation; child runs own I3 as first metabolic cycle; peer-trust L1-bounded + revocation.
- **I8. Single-Skin Integrity** — Exactly one declared boundary; admits all envelope-valid, rejects on envelope integrity; ≤1 operator-token; post-handshake CI requires owner attestation; cold-resume runs full I3/I5/I8 pre-handshake; skin process supervisor-restartable.
- **I9. Compression Discipline** — Compression operates only within CI-attested rules; P10.b invariant-set fully recoverable; every event emits witness for owner-side re-derivation; no silent compression.
- **I10. Metabolic-Economy Observation** — Every operation has observable cost; budgets L1-defined; exhaustion triggers P11.c; observatory emits cost-budget signals.
- **I12. Telos Alignment** — Daily-ops decisions evaluable against telos; drift detected; owner-stated objectives anchor alignment when present; L1_TROPISM specifies operational metric.

### Projection table (P → I)

| P | I |
|---|---|
| P1{,.a,.b',.b'',.c} | I6,I8 / I1 / I2,I6 / I2 / I1,I8 |
| P2 / P2.a / P3 / P3.b / P4 | I6,I8 / I6 / I3,I4 / I4 / I3,I4 |
| P5 / P6 / P7 / P8 | I5,I7 / I4 / I1,I5,I2 / I7 |
| P9.a / P9.b / P10 / P11 / P14 | I3,I8 / I8 / I9 / I10 / I12 |
| P12 / P13 / P15 | → L1_TROPISM / P9+I8 / L2_FEDERATION |

---

## §5. Strict mycology lexicon and dispatch constraints

**§5.1 Lexicon**: fungal-biology vocabulary strictly; admitted terms = any mycology literature uses; evolution CI-level.
**§5.2 Dispatch form**: NOT verbs; NOT request/response. MUST honor P1.c carrier-asymmetry; support P2.a + §6 continuous operation; satisfy I6; carry causal-proofs.
**§5.3 Intent**: NOT first-class substrate data type; agent-self-reported intent structurally not trusted.

---

## §6. Continuity model

Substrate presumed continuously operated; no boot/session-end ritual; host disconnects recovered, not formalized. Metabolic cycle existence + per-cycle invariant checks (I3 + I5 + I8 + I10) L0; cadence + dormancy budget L1. Delta atomicity: fully absorbed or not.

---

## §7. Living Bets — recalibrated for 2026 agent capability

**§7.1 The bet**: Myco's symbiotic-organism shape — asymmetric pair per P1.c, continuously operating, twelve-principle structure — **has cost-justified value within an agent-intelligence band**: value − cost > 0.

### §7.2 Intelligence band

| Band | Range | Bet |
|---|---|---|
| Below | ≤100K tokens, weak reasoning | unjustified (naive RAG suffices) |
| Within | ~200K-10M tokens | **2026 sweet spot** |
| Above | >~10M tokens, AGI-class | Sutton's bitter lesson dominates; retire gracefully |

**§7.3 Observatory**: 10 signals (6 base + 3 cost + 1 composite). See **L2_OBSERVABILITY §2**.
**§7.4 Falsifiability**: 90-day wall-clock window (§13); ≥3 of {#1,#2,#3,#4a,#4b,#6} trend against bet (OLS Z ≥ 1.96) AND #6 < 1 for ≥50% → fires `bet_weakening_quorum`. Algorithm: `docs/architecture/algorithms/bet_weakening_quorum.md`. Birth-period SUSPENDED → `bet_weakening_evaluation_suspended`.

**§7.5 Bet retirement**: Trigger (ALL, 2-year window): C40 fires; owner re-justification fails 3× consecutive; #6 < 0.1 for >75% of final-90-day samples; `alive::normal` → `bet_retired_proposal`. Execution: owner co-attestation → `alive::archived` (state_dir preserved, anchor seals last DAG tip). Counter reset / cadence: `algorithms/bet_weakening_quorum.md`.

---

## §8. Operational readiness

v0.9 targets ~200K to ~10M read-window. Mechanical: state digest ≤ read-window (L1); exposed structure parseable; functions under host-session intermittency; signal #6 = monitoring metric.

---

## §9. Out-of-band anchor surface

**§9.1**: Surface where owner signatures, DAG-tip hashes, substrate-ID lineage, trusted timestamps are externally visible + untouchable by agent process; form L1_GOVERNANCE-specified.

**§9.2 Sub-mechanism inventory**: §9.2.1 substrate-ID birth attestation; §9.2.2 DAG-tip co-signing every CI boundary; §9.2.3 owner attestations out-of-band; §9.2.4 L0 revision diff workflow; §9.2.5 anchor-surface-generated nonces; §9.2.6 anchor-stamped wall-clock; §9.2.7 owner liveness heartbeat. §9.3.1 canonical-bytes serialization; §9.3.2 owner-side rendering; §9.3.3 anchor-client provenance independence; §9.3.4 witnesses, not verdicts; §9.3.5 anchor-nonce-derived sampling; §9.3.6 DAG-enumeration closure check. Per-sub-mechanism milestone schedule + status: `docs/implementation_status.md`.

**§9.3 Specs**: §9.2.1 5-tuple = `(substrate-ID, genesis-timestamp, initial-spore-schema-canonical-bytes-hash, owner-public-key, anchor-surface-endpoint-public-key)`. §9.3.5 = `H(anchor_surface_nonce, leaf_count)`. §9.3.6 closure: owner verifies new tip reachable from prior signed tip via enumerated nodes.
**§9.4 Doctrine**: Anchor receives canonical bytes + witnesses; verifier re-derives.
**§9.5-§9.6**: v0.9 anchor collapsed to operator process; does NOT defend against compromised/coerced/impersonated owner (§14 bounded defenses).

---

## §10. Process

L0 changes REQUIRE proposal + owner approval + CI bump + cascade review (process: OUTLINE.md §4). Origin discrimination: every step MUST trace to ≥1 of P1-P11+P14 + ≥1 invariant.

---

## §11. Privacy, access, backup

L0 commits NO internal privacy/access model; substrate wholly accessible to operator-agent; skin (P9/I8) IS the boundary.

**§11.1 Backup**: state_dir backups NOT internally access-controlled; **L1_SKIN MUST specify backup encryption** (operator-controlled symmetric key + escrow + rotation aligned with owner key); L0 mandates absent-encryption acknowledged as known attack surface.

---

## §12. Glossary

| Term | Definition |
|---|---|
| **Myco** | Biology-rooted symbiotic digital substrate class. |
| **Substrate-ID** | Persistent owner-signed identifier at genesis. |
| **Operator-token** | Ephemeral per-handshake identifier. |
| **CI boundary** | Threshold above which a change alters Myco's identity. |
| **Metabolic cycle** | Smallest discrete metabolism event. |
| **Spore-schema** | Seed-state parent → child during P8. |
| **Skin / boundary** | Substrate's single declared interface. |
| **Sporocarp** | Atomic-event-record under L1_TROPISM dispatch. |
| **Anchor surface** | Cryptographic root (§9). |
| **Cultivation / Cultivator / Cultivar** | See §1.1. |

---

## §13. L1/L2-deferred topics (L0 short)

- **§13.1 Time semantics**: anchor wall-clock (§9.2.6) authoritative for owner-attested events + time-bound defenses; substrate monotonic clock for within-substrate ordering; i32 FORBIDDEN; i64-ns canonical. Cascade: L1_CONTINUITY NTP + L1_SCHEMA i64/year-2262/pre-1970.
- **§13.2 Adversarial owner**: not safe under adversarial Cultivator; bounded defenses at L2_TRUST_MODEL. Irreducible commitments (via I4/I9/I10/I12): P6 causality, truthful observability + mortality emission, P10.b invariant preserved.
- **§13.3 Owner mortality / succession**: not safe across owner death without succession; Cultivation transferable (§1.1). Cascade: L1_GOVERNANCE §3.2 + diagrams/cultivation_succession_fsm.txt.
- **§13.4 Generation limits**: reproduction discipline-bounded; seeds depth=10 / rate=24h / quota=100. Cascade: L1_GOVERNANCE §16.

