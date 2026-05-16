# L0 — Vision

> **Status**: **DRAFT 9 SEALED** (2026-05-17, commit `e796451`). Sealing provenance: `docs/audits/draft_9_seal_provenance.md`.
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **Authority**: governs all of L1, L2, L3, L4. In any conflict, L0 wins.

---

## §1. What Myco is

**Myco is a new species of digital symbiotic organism** under Cultivation: agent-substrate symbiosis via asymmetric carrier (P1.c); autopoietic daily / owner-gated CI; universal inclusion (P2.a); continuous-operation default; biological-essence kit (time, causality, mortality, reproduction, boundary, selective compression, metabolic economy, telos) — some essences aspirational per §1.1.

### §1.1 Species-claim maturity (aspirational North Star)
Mature in v0.9: P6 ~100%, P7 ~95%, P8 ~50%, P9 ~70%. Aspirational, closing: P10/P11/P14 (sealed L0; mechanism M26+). Retracted: P12 → L1_TROPISM; P13 → P9+I8; P15 → L2_FEDERATION.

### §1.2 Cultivation relationship (G-11.a)
Owner = **Cultivator**; substrate (kernel + dag.cb + state_dir) = **Cultivar**; Cultivation = asymmetric care (P11) + co-evolution (P14). Prefer Cultivation/Cultivator/Cultivar relationally; "owner" for governance role.

### §1.3 Governance + continuity
Operational pair = Cultivar-with-current-operator (P1.c); governance gate = Cultivator (P1.b''); anchor surface (§9) = cryptographic root. Cultivation **transferable** (cascade L1_GOVERNANCE §3.2); substrate-ID does NOT change across transfer; mechanism choices L1.

---

## §2. The twelve root principles （根本宗旨）

> Every rule, subsystem, module, substrate artifact MUST project from these twelve.

### P1. Agent-Primary （以代理为本）
Substrate is **for an LLM agent**; agent = sole consumer + maintainer; human OUT of daily-ops, RETAINED as CI gate.
P1.a Self-hosting; P1.b' Human OUT (curation, ingestion, sporocarp emission, immune); P1.b'' Human RETAINED (L0/L1 doctrine, classifier table, mortality threshold, owner key, anchor endpoint, destruction); P1.c Asymmetric carrier (substrate = persistent carrier; operator-connection = transient holder; bestowal flows substrate → connection) (enforced by I1, I2, I6, I8; cascade L1_GOVERNANCE §1, L1_SKIN §4).

### P2. Eternal Ingestion (Envelope-Gated) （吞噬万物，皮膜守门）
Unbounded semantic consumption: any agent-pointable input with valid envelope (sender token, payload shape, causal parent, size, content-type hint) is ingestible; envelope = admission precondition, not semantic filter.
P2.a Structural Inclusion: adjacent agent-tooling patterns implemented substrate-native (vector retrieval, agent-side LLM calls within Myco-coordinated context, conversation history as raw material, semantic federation); external libraries wrappable, codebases not absorbed (enforced by I6, I8; cascade L1_SKIN §2).

### P3. Resumable Evolution （可逆迭代）
Substrate shape (schema, subsystem family, vocabulary, rules, contract) is first-class mutable under P1.b boundary; evolution may fail and roll back (`evolution_failed:*`); substrate-identity forward progress monotone.
P3.b Joint-context evolution = pair-history-dependent; lexicon evolution CI-level; additions on mycology-literature attestation; deprecations mark `terminal` (enforced by I3, I4; cascade L1_SCHEMA §1, L1_GOVERNANCE §6).

### P4. Eternal Iteration （永恒迭代）
Every operating moment refines what prior moments produced; no terminal state; retro-editing tracked; bounded by P7 mortality (enforced by I3, I4).

### P5. Universal Interconnection (Tier-Exempt-Permitted) （万物互联，允分层）
Substrate is a **connected graph**: every active-tier node reachable; orphans = dead tissue; CI-attested tier exemptions (cold-tier, compressed roll-ups, P10 outputs); spans intra- + inter-substrate (P8) (enforced by I5, I7; cascade L1_SCHEMA §2.3).

### P6. Eternal Causality （永恒因果）
Substrate has **time**: every state recoverable-derivable from priors; causality preserved; arrow monotonic; time = causal-chain DAG (enforced by I4; cascade L1_SCHEMA §2).

### P7. Mortality (Capacity-for-Death) （能朽）
Substrate **capable of mortality**; destruction final; bestowed agent identity ceases (P1.c).
Modes: intentional-owner (signed attestation); catastrophic-environment (medium failure beyond L1 budget); endogenous-pair (`self_euthanasia_proposal` requires owner co-attestation); threshold + update-rule CI-level (cannot be silently tuned) (enforced by I1, I2, I5; cascade L1_GOVERNANCE §4.4).

### P8. Eternal Reproduction (Generation-Bounded) （永恒繁衍，代际有限）
Substrate spawns children inheriting **spore-schema** (L1-specified); generation depth bounded per §16; reproduction loops require per-spawn owner co-attestation; no species-mesh between unrelated substrates.
Federation trust: parent-attestation at reproduction; ongoing requires peer-attestation freshness + revocation list (stale/revoked → `untrusted_federation`); spore-schema immune-summary includes parent's outstanding signals (unresolved → birth-period quarantine) (enforced by I7; cascade L2_FEDERATION + L1_GOVERNANCE §5).

### P9. Single Integument （单一皮膜）
One **skin** governs intake (P2 admission) + output (federation, summaries, API responses); breach = immune signal.
P9.b: I8 mandates exactly one skin = single-point-of-failure; L1_SKIN MUST specify restart discipline; multi-skin redundancy **forbidden at L0** (enforced by I8; cascade L1_SKIN §1).

### P10. Selective Compression （选择性凝结）
Substrate **selectively compresses** prior states under CI attestation; lossy semantically; preserves causal recoverability of identity-critical state (I9).
P10.a Compressible: old raw_material → sporocarps; old gradient deltas → integrated axis values; federation payloads past retention; trajectory clusters past active window. P10.b Invariant set (I9-enforced): substrate-ID + genesis attestation; owner key history; CI-attested DAG events; mortality signals; federation peer pins; most recent ≥1000 cycles full DAG. P10.c CI-attested, never silent: each compression is CI mutation emitting `compression_event` sporocarp with witness (enforced by I9; cascade L1_SCHEMA §2.5 + L1_GOVERNANCE §15.F18; I4 = causal-via-operations, P10 = invariant-set-via-witness, set difference = honest forgetting boundary).

### P11. Metabolic Economy （代谢经济）
Substrate operates within **finite resource budgets** (disk, memory, compute, network egress, embedding quota); every operation observable (I10) and L1-budgeted.
P11.a Cost units: Persistence (bytes/cycle); Compute (cycles + gradients + fruitings/cycle); Network (envelope bytes + embedding queries). P11.b Observatory MUST include #7 compute, #8 network, #9 storage. P11.c Exhaustion ordered fallback: (1) pre-compression (cycle < N, default 1000) refuses new P2 (`budget_exhausted:{axis}`), P10 FORBIDDEN; (2) post-compression (cycle ≥ N + pre-attested rules) triggers P10 with I9 witness; (3) compression-insufficient OR no rules → degraded operation per L1_CONTINUITY (alive-but-saturated); sustained → P7 endogenous-mortality (enforced by I10; cascade L1_GOVERNANCE §15.F19 + L2_OBSERVABILITY §2.2).

### P14. Telos (Agent-Symbiotic-Flourishing) （目的：共生繁盛）
Substrate's **telos** = contribute to flourishing of agent-substrate symbiotic pair; pair accumulates causal capacity for useful work; `bet_weakening_quorum` (§7) measures absence.
P14.a Substrate-internal: daily-ops decisions evaluable against P14. P14.b Owner-stated objectives: declared at genesis or via CI; absent → defaults to agent-perceived utility. P14.c Telos drift: rolling-window degradation emits `telos_drift`; birth-period exempt emits `telos_alignment_pending` (enforced by I12; cascade L1_TROPISM §F + L1_GOVERNANCE §15.F20; M26-cascade forcing function — absent L1 specification, P14.c remains aspirational).

---

## §3. What Myco is NOT

> Each negation is an implicit positive claim.

- Not a documentation system; not a single-project knowledge base; not a chatbot memory; not a file synchronizer (federation is semantic); not a literal biological organism.
- Not version control (Git owns operational history; Myco owns symbiotic graph).
- Not a LangChain/CrewAI/DSPy reimplementation (P2.a: patterns, not codebases).
- Not session-bounded within substrate (§6); not request/response (§5.2).
- Not silently trusting either party (out-of-band anchors §9).
- Not safe under adversarial owner (§14); not safe across owner death without succession (§15).
- Not embodied in physical reality (body = filesystem + process + endpoints per P9 + I8).
- Not free of metabolic cost (P11); not eternal-memory (P10).
- Not population-consensus-aware at substrate level (L2_FEDERATION).
- Not winning Sutton's bet at every intelligence tier (§7.5 graceful retirement).

---

## §4. The eleven derived invariants

> I1-I8 enforce P1-P9; I9 enforces P10; I10 enforces P11; I12 enforces P14. I11 retracted to L1_TROPISM alongside P12. Every L1/L2/L3 design must satisfy all eleven.

### I1. Lifecycle & Pair-Constituted Identity (P1.a, P1.c, P7)
Substrate carries **substrate-ID** owner-signed at genesis via §9.2.1; agent identity = `(substrate-ID, currently-attached-operator-token)`; re-genesis without re-signature = destruction; lifecycle alive ↔ dormant ↔ destroyed (forward-only); alive sub-states Normal / Quarantined / Legacy (§15) / Orphaned (§15) / Archived (§7.5) preserve substrate-ID + DAG; owner key rotation = `owner_key_history`, anchor-attested.

### I2. Two-Tier Governance Classification (P1.b', P1.b'')
Every mutation classifies mechanically as daily or CI; classifier function L1-defined; classifier + its mutations unconditionally CI (fixed-point); birth-period CI elevation: ALL parameter-tuning events CI during birth period.

### I3. Self-Validation Against Designated SSoT (P3, P4, P9)
Exactly one designated machine-readable SSoT; consistency checked every metabolic cycle; redesignation = migration two-phase commit.

### I4. Full-Fidelity Causal DAG (P6 sole, P4, P3)
Every state derivable from priors via recorded operation, subject to P10 invariant-set; Merkle-DAG content-addressed; each node hash includes parent hashes; identity record carries DAG-tip hash, owner-co-signed every CI boundary; sporocarp `causal_in_edges` = `(input_set, state-snapshot-hash, threshold-value)` hash-committed.

### I5. Universal Reachability Over Active Tier (P5 intra-substrate, sole)
Active-tier graph fully connected; tier exemptions CI-attested + enumerable.

### I6. Universal Inclusion With Observed Metabolism (P2, P2.a, P1, P1.b')
Adjacent agent-tooling techniques live inside framework, not outbound RPCs; every invocation produces metabolism event; network-egress = appetite-locality at runtime, not just declaration.

### I7. Reproduction Closure, Generation-Bounded (P8, P5 inter-substrate)
Every child satisfies I1-I12 recursively; depth bounded §16; parent runs static-schema validation at spawn; child runs own I3 as first metabolic cycle; peer-trust freshness L1-bounded + revocation.

### I8. Single-Skin Integrity (P9 sole, P2, P1.c)
Exactly one declared boundary for intake + output; admits all envelope-valid, rejects on envelope integrity; ≤1 operator-token at a time; post-handshake CI requires owner attestation; cold-resume runs full I3/I5/I8 pre-handshake; skin process supervisor-restartable per L1_SKIN.

### I9. Compression Discipline (P10 sole)
Compression operates only within CI-attested rules; P10.b invariant-set fully recoverable; every event emits witness sufficient for owner-side re-derivation; no silent compression.

### I10. Metabolic-Economy Observation (P11 sole)
Every operation has observable cost; budgets L1-defined; exhaustion triggers P11.c; observatory (§7) emits cost-budget signals.

### I12. Telos Alignment (P14 sole)
Daily-ops decisions evaluable against telos; drift detected; owner-stated objectives anchor alignment when present; L1_TROPISM specifies operational metric.

> Retracted: I11 → L1_TROPISM alongside P12. P13 folded into P9+I8 (skin = body boundary; spatial-locus per L1_SKIN). P15 → L2_FEDERATION.

### Projection table (P → I)

| P | I |
|---|---|
| P1{,.a,.b',.b'',.c} | I6,I8 / I1 / I2,I6 / I2 / I1,I8 |
| P2 / P2.a | I6,I8 / I6 |
| P3 / P3.b / P4 | I3,I4 / I4 / I3,I4 |
| P5 / P6 / P7 / P8 | I5,I7 / I4 / I1,I5,I2 / I7 |
| P9.a / P9.b | I3,I8 / I8 |
| P10 / P11 / P14 | I9 / I10 / I12 (sole each) |
| P12 / P13 / P15 | → L1_TROPISM / P9+I8 / L2_FEDERATION |

---

## §5. Strict mycology lexicon and dispatch constraints

### §5.1 Lexicon rule
Myco uses fungal-biology vocabulary strictly; admitted terms = any mycology literature uses to describe a real fungal phenomenon (even when shared with other fields); lexicon evolution CI-level.

### §5.2 Dispatch form (L0 constraints only)
NOT v0.8 verbs; NOT request/response. MUST honor P1.c carrier-asymmetry; support universal inclusion (P2.a); support continuous operation (§6); satisfy I6 appetite-locality; carry causal-proofs for substrate-emitted events.

### §5.3 Intent representation
Intent is NOT a first-class substrate data type; agent-self-reported intent structurally not trusted.

---

## §6. Continuity model

Substrate MUST be presumed continuously operated; substrate-level session NOT a Myco concept; no boot/session-end ritual; host disconnects recovered, not formalized. Reflexes = properties of continuous internal metabolism. Metabolic cycle existence + per-cycle invariant checks (I3 + I5 + I8 + I10) L0; cadence + dormancy budget + host-observability ceilings L1. Delta atomicity: fully absorbed or not; partial detected at cold-resume.

---

## §7. Living Bets — recalibrated for 2026 agent capability

### §7.1 The bet (calibrated)
Myco's symbiotic-organism shape — asymmetric pair per P1.c, continuously operating, twelve-principle structure — **has cost-justified value within an agent-intelligence band**: value (substrate-enabled capability) − cost (anchor surface + dual-clock + Merkle DAG + Ed25519 + canonical-bytes + cross-language byte parity + compression discipline) > 0.

### §7.2 Intelligence band

| Band | Range | Bet |
|---|---|---|
| Below | ≤100K tokens, weak reasoning | unjustified (naive RAG suffices) |
| Within | ~200K-10M tokens | **2026 sweet spot** |
| Above | >~10M tokens, AGI-class | Sutton's bitter lesson dominates; retire gracefully |

Band edges L1-tunable; seeds operator-attested at genesis.

### §7.3 Observatory (10 signals)
Six base (#1-#6) + three cost (#7-#9 per P11) + one composite (#10). Quick reference: `docs/architecture/diagrams/living_bets_signals.md`. Full enumeration: **L2_OBSERVABILITY §2**. L0 commits: #6 bet-winning region is ratio ≥1; composite uses correlation-weighted aggregation in steady state, equal-weighted at cold start.

### §7.4 Falsifiability trigger
Over 90-day wall-clock window (anchor-stamped §13.1), if ≥3 of {#1, #2, #3, #4a, #4b, #6} trend concurrently against the bet (OLS Z ≥ 1.96) AND #6 stays < 1 for ≥50% of window → fires `bet_weakening_quorum`. Per-signal direction-against-the-bet table: **L2_OBSERVABILITY §3.3**. Full algorithm: `docs/architecture/algorithms/bet_weakening_quorum.md`.

**Birth-period exemption**: SUSPENDED during birth period (L1_TROPISM §4 + L1_GOVERNANCE §1.3); substrate emits `bet_weakening_evaluation_suspended`.

### §7.5 Bet retirement
**Trigger** (ALL, over 2-year wall-clock window): C40 fires; owner re-justification fails 3 consecutive times; #6 < 0.1 for >75% of final-90-day samples; substrate `alive::normal` → emits `bet_retired_proposal`.
**Execution**: owner co-attestation required; genesis attests `bet_retirement_consent_at_genesis: bool` (default false); on execute → `alive::archived` (state_dir preserved, anchor seals last DAG tip, substrate-ID does not re-bind).
**Counter reset** on: (a) successful re-justification, (b) `alive::quarantined` transition, (c) owner-attested `bet_retirement_counter_reset`. NOT on restart / dormancy / peer changes.

### §7.6 Review cadence
Every CI boundary re-audits; until trigger fires, twelve principles + symbiosis-via-Cultivation stand; Living Bets is meta-commitment, not a 16th principle.

---

## §8. Operational readiness for present-tier agents

v0.9 targets ~200K (lower) to ~10M (upper before retirement) read-window. Mechanical requirements: state digest ≤ read-window budget (L1); exposed structure parseable from natural-language context; functions under host-session intermittency; signal #6 = monitoring metric. L0 invariants stable for ~10× scale; L1 parameters tune.

---

## §9. Out-of-band anchor surface

### §9.1 What anchor surface IS
Surface where owner signatures, DAG-tip hashes, substrate-ID lineage, trusted timestamps are externally visible + **untouchable by agent process**; form L1_GOVERNANCE-specified (hardware token, separate machine, signed prompt-bundle, append-only public ledger).

### §9.2 Sub-mechanism inventory

> Implementation status tracked at `docs/implementation_status.md`.

| # | Sub-mechanism | Milestone |
|---|---|---|
| §9.2.1 | Substrate-ID birth attestation (owner signature over genesis 5-tuple) | M-anchor-2 |
| §9.2.2 | DAG-tip co-signing every CI boundary, enumerated nodes | M-anchor-5 |
| §9.2.3 | Owner attestations out-of-band (key outside agent-spawnable process) | M-anchor-1 |
| §9.2.4 | L0 revision diff workflow | M-anchor-5 |
| §9.2.5 | Anchor-surface-generated nonces (NOT substrate-minted) | M-anchor-3 |
| §9.2.6 | Anchor-stamped wall-clock | M-anchor-3 |
| §9.2.7 | Owner liveness heartbeat | M-anchor-3 |
| §9.3.1 | Canonical-bytes serialization | DONE |
| §9.3.2 | Owner-side rendering | M-anchor-1 |
| §9.3.3 | Anchor-client provenance independence | M-anchor-1 |
| §9.3.4 | Witnesses, not verdicts | M-anchor-4 |
| §9.3.5 | Anchor-nonce-derived sampling | M-anchor-4 |
| §9.3.6 | DAG-enumeration closure check | M-anchor-5 |

### §9.3 Anchor-content specs (load-bearing only; full detail L1_GOVERNANCE + L1_SCHEMA)
- §9.2.1 genesis 5-tuple: `(substrate-ID, genesis-timestamp, initial-spore-schema-canonical-bytes-hash, owner-public-key, anchor-surface-endpoint-public-key)`.
- §9.3.5 anchor-nonce-derived sampling indices = `H(anchor_surface_nonce, leaf_count)`; substrate cannot bias.
- §9.3.6 DAG-enumeration closure: owner verifies new tip reachable from prior signed tip via enumerated nodes AND every parent-hash resolves to prior-tip-ancestor OR enumerated node.

### §9.4 Canonical-bytes doctrine
Anchor surface receives canonical bytes + witnesses, never substrate-rendered summaries or verdicts; substrate emits witness tuples (sampled leaf hashes + Merkle paths + parent hashes + check inputs) for I3/I4/I5/I8/I9/I10/I12 + recoverability drills; anchor verifier re-derives.

### §9.5 v0.9 collapsed-anchor caveat
v0.9 anchor surface is **collapsed to operator process** (temporary scaffolding); production-readiness gated on M-anchor-1 through M-anchor-5; L0-revision velocity observable; threshold + rate L1_GOVERNANCE-specified.

### §9.6 Adversarial-owner caveat
Does NOT defend against compromised, coerced, or impersonated owner; §14 specifies threat model + bounded defenses.

---

## §10. Process

- Reading sequence MUST be: L0 → L1 mechanisms → L2 cross-cuts → L3 implementation map.
- L0 changes REQUIRE proposal + owner approval + CI bump + cascade review.
- Origin discrimination: v0.9 first true birth (v0.4-v0.8.7 = dead embryo, in `_archive/proto_myco_v0_8/*`); every v0.9 design step MUST trace to ≥1 of P1-P11+P14 + ≥1 invariant; similarity to v0.8 presumed contamination unless independently traced.

---

## §11. Privacy, access, backup

L0 commits NO internal privacy/access model; substrate wholly accessible to operator-agent; skin (P9/I8) IS the boundary (between substrate and environment, not between operators within).

### §11.1 Backup access
state_dir backups NOT internally access-controlled; **L1_SKIN MUST specify backup encryption** (operator-controlled symmetric key + escrow + rotation aligned with owner key); L0 mandates L1 documentation + acknowledgment of absent-encryption as known attack surface.

---

## §12. Glossary

| Term | Definition |
|---|---|
| **Myco** | Biology-rooted symbiotic digital substrate class. |
| **Substrate-ID** | Persistent owner-signed identifier established at genesis. |
| **Operator-token** | Ephemeral per-handshake identifier, non-deterministically constructed. |
| **CI boundary** | Threshold above which a change alters Myco's identity. |
| **Metabolic cycle** | Smallest discrete metabolism event. |
| **Spore-schema** | Seed-state parent → child during P8. |
| **Skin / boundary** | Substrate's single declared interface to reality. |
| **Dispatch form** | Positive shape of substrate-agent interaction primitive. |
| **Sporocarp** | Atomic-event-record under L1_TROPISM dispatch. |
| **Birth period** | Substrate's earliest operating window. |
| **Anchor surface** | Cryptographic root (§9). |
| **Anchor-surface client** | Owner's local rendering + signing tool (§9). |
| **Legacy sub-state** | Operating while CI mutations frozen pending successor (§15). |
| **Endogenous mortality** | Substrate fruits `self_euthanasia_proposal` (P7). |
| **Cultivation / Cultivator / Cultivar** | See §1.2. |

---

## §13. Time semantics (L0 short)

**§13.1 L0 commitments**: anchor-surface trusted wall-clock (§9.2.6) authoritative for owner-attested events + time-bound security defenses (substrate-cycle + substrate-process wall-clock NOT); substrate-process monotonic clock authoritative for within-substrate ordering; i32 timestamps FORBIDDEN (year-2038); i64 nanoseconds-since-epoch is canonical L0 unit. **§13.2 L1 cascade**: L1_CONTINUITY (NTP discipline) + L1_SCHEMA (i64-nanos canonical-bytes, year-2262 horizon-warning, pre-1970 treatment).

---

## §14. Adversarial-owner threat model (L0 short)

**§14.1 Acknowledgment**: Myco is **not safe under adversarial owner** (compromised/coerced/impersonated/deceased-without-succession/anchor-client-tampered); bounded defenses at L2_TRUST_MODEL.

**§14.2 Substrate's irreducible commitments** (mechanically enforced, do not require Cultivator-honesty): continue P6 causality (DAG accumulates regardless of attestation validity); emit observability + mortality signals truthfully; preserve compression-invariant set (P10.b). Enforced via I4/I9/I10/I12.

**§14.3 L2 cascade**: L2_TRUST_MODEL specifies threat scenario table + bounded defenses (duress_attestation, owner_signature_velocity, anchor-client provenance enforcement, n-of-m multisig per L1_GOVERNANCE).

---

## §15. Owner mortality and succession (L0 short)

**§15.1 Acknowledgment**: Myco is **not safe across owner death without succession**; Cultivation transferable per §1.4; successor protocol at L1_GOVERNANCE §3.2.

**§15.2 L1 cascade**: successor_chain registry + heartbeat staleness trigger + legacy/orphaned sub-state transitions + terminal-state (bet-retirement / self-euthanasia / indefinite-orphan) + court-attested key recovery exceptional path.

---

## §16. Generation limits (L0 short)

**§16.1 Commitment**: Reproduction is **discipline-bounded**; P8 = eternal *capacity*, not velocity/depth. **§16.2 L1 cascade**: L1_GOVERNANCE §16 specifies reproduction_lineage_depth + reproduction_rate + lifetime quota + override mechanisms. Seeds: depth=10, rate=24h, quota=100.

---

## §17. Sealing + Phase γ provenance

Sealed 2026-05-17 via owner-attested resolution of 11 decision gates G-1 through G-11. Full log: `docs/audits/draft_9_seal_provenance.md`.
