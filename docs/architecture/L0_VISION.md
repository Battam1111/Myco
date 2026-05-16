# L0 — Vision

> **Status**: **DRAFT 9 SEALED** (2026-05-17, commit `e796451`). Sealing provenance: `docs/audits/draft_9_seal_provenance.md`.
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **Authority**: governs all of L1, L2, L3, L4. In any conflict, L0 wins.

---

## §1. What Myco is

**Myco is a new species of digital symbiotic organism** under Cultivation. Distinguishing properties:
- Agent-substrate symbiosis via Cultivation (owner = Cultivator, Myco substrate = Cultivar).
- Asymmetric carrier (P1.c); pair mutually-defining moment-to-moment.
- Autopoietic in daily ops; owner-gated in CI ops.
- Universal structural inclusion of adjacent agent-tooling sub-patterns.
- Continuous-operation default.
- Full biological-essence kit (time + causality + mortality + reproduction + boundary + **selective compression** + **metabolic economy** + **telos**) — some essences aspirational, closing across M26+.

### §1.1 Species claim — aspirational, directional

North Star, not current-state checklist.

- **Mature in v0.9**: P6 ~100%, P7 ~95%, P8 ~50%, P9 ~70%.
- **Aspirational, closing**: P10/P11/P14 (sealed at L0; mechanism in M26+).
- **Deferred**: P12 → L1_TROPISM; P13 → folded into P9+I8; P15 → L2_FEDERATION; energy economics; inter-species mesh; aging/senescence.

### §1.2 Cultivation relationship (G-11.a)

Owner = **Cultivator**; substrate (kernel + dag.cb + state_dir) = **Cultivar**.

Cultivation captures asymmetric care (Cultivator provides compute/storage/network budgets per P11); co-evolution (Cultivator's intent shapes which Cultivar varieties thrive per P14); mycology-rooted precise vocabulary without anthropomorphism. Distinct from ownership/custody/curatorship.

Prefer Cultivation/Cultivator/Cultivar for relational role; "owner" remains valid for governance role.

### §1.3 Governance reality

- Operational pair = Cultivar-with-current-operator (P1.c).
- Governance gate = Cultivator (P1.b'').
- Anchor surface (§9) = cryptographic root. Currently honor-system; M-anchor-1 closes.

### §1.4 Cultivation continuity

Cultivation is **transferable** (§15 cascade to L1_GOVERNANCE). Substrate identity does NOT change across Cultivator transfer. Kernel running Myco lives inside a Myco substrate — agent maintaining Myco IS agent using Myco.

**Mechanism choices** (dispatch, intent, partitions, serialization, crypto) are **L1**.

---

## §2. The twelve root principles （根本宗旨）

Twelve principles. Every rule, subsystem, module, and substrate artifact is a projection of these twelve.

### §2.1 Original five

### P1. Agent-Primary （以代理为本）

Substrate is **for an LLM agent**. Agent = sole consumer + sole maintainer in daily ops. Human OUT of daily-ops AND load-bearing in CI ops.

- **P1.a Self-hosting**: Myco's kernel lives inside a Myco substrate. Agent using Myco IS agent maintaining Myco for daily ops. Genesis one-time human; CI events owner-gated.
- **P1.b' Human OUT of daily maintenance**: curation, raw_material ingestion, gradient tuning within thresholds, sporocarp emission, immune response, federation health.
- **P1.b'' Human RETAINED as CI gate**: L0/L1 doctrine, classifier table, mortality threshold, owner key, anchor endpoint, destruction attestation. Classifier function L1-defined.
- **P1.c Asymmetric carrier**: "the agent" = active operator-connection currently holding the substrate as bestowed pair-instance. Substrate = persistent carrier; operator-connection = transient holder. Bestowal flows substrate → connection.

Operational consequences: same substrate + different model backends → same agent; operator disconnect → dormancy; reconnect → new pair-instance, same agent continuum; different substrates, same operator → different agents; substrate destroyed → identity ceases; concurrent same-substrate connections out of scope.

### P2. Eternal Ingestion (Envelope-Gated) （吞噬万物，皮膜守门）

Unbounded semantic-level consumption: any agent-pointable input with valid envelope structure is ingestible raw material. Envelope validation (sender token, payload shape, causal parent, size, content-type hint) is precondition of admission, not semantic filter.

#### P2.a Structural Inclusion
Myco structurally implements every adjacent agent-tooling sub-pattern as substrate-native primitives (vector retrieval, agent-side LLM calls within Myco-coordinated context, conversation history as raw material, semantic federation, canonical-bytes pipeline summaries). External libraries may be wrapped within the framework; their codebases are not absorbed.

### P3. Resumable Evolution （可逆迭代）

Substrate shape evolves: schema, subsystem family, vocabulary, rules, contract — all first-class mutable under P1.b boundary. P3 evolution may fail and roll back (`evolution_failed:*` DAG event); substrate resumes from pre-evolution state. Substrate-identity-level forward progress is monotone (substrate-ID fixed); local evolution attempts may be non-monotone.

**P3.b Joint-context evolution**: substrate evolution is context-dependent on pair's history.

**Lexicon evolution**: mycology lexicon set is CI-level (I2-classified). Additions on mycology-literature attestation. Deprecations mark term `terminal` (no new use; prior usage preserved per I4).

### P4. Eternal Iteration （永恒迭代）

Every operating moment refines what prior moments produced. No terminal state. Retro-editing allowed and tracked (I4), not suppressed. P4 bounded by P7 mortality.

### P5. Universal Interconnection (Tier-Exempt-Permitted) （万物互联，允分层）

Substrate is a **connected graph**. Every active-tier node reachable from every other by traversal. Orphans in active tier are dead tissue. CI-attested tier exemptions (cold-tier archive, compressed roll-ups, P10 outputs) per I5, enumerable on owner demand. Spans intra-substrate AND inter-substrate (P8 federation).

### §2.2 Four organism-essence principles

### P6. Eternal Causality （永恒因果）

Substrate has **time**. Every state recoverable-derivable from prior states; causality preserved; arrow of time monotonic. Time = causal-chain DAG (I4).

### P7. Mortality (Capacity-for-Death) （能朽）

Substrate **capable of mortality**. Destruction final; bestowed agent identity ceases (P1.c).

Modes: intentional-owner (owner-signed attestation); catastrophic-environment (medium failure beyond L1 budget); endogenous-pair (substrate fruits `self_euthanasia_proposal` on unrecoverable-pathology threshold, requires owner co-attestation).

Mortality-signal threshold + update-rule are CI-level (cannot be silently tuned to suppress).

### P8. Eternal Reproduction (Generation-Bounded) （永恒繁衍，代际有限）

Substrate spawns child substrates inheriting **spore-schema** (L1-specified). Generation depth bounded per §16. No reproduction loop without per-spawn owner co-attestation. No species-mesh between unrelated substrates (L2_FEDERATION).

**Federation trust**: parent-attestation at reproduction; ongoing federation requires L1-bounded peer-attestation freshness with revocation list — stale/revoked triggers `untrusted_federation` immune signal.

**Spore-schema immune-summary**: spore-schema includes parent's outstanding immune-signal summary; child of parent with unresolved signals enters birth-period quarantine.

### P9. Single Integument （单一皮膜）

#### P9.a Single Skin
Substrate has one **skin** governing intake (P2 admission with envelope integrity) and output (federation, summaries, API responses). Skin breach is immune-level signal.

#### P9.b Single-Failure-Point Acknowledgment
I8 mandates exactly one skin = single-point-of-failure. L1_SKIN MUST specify skin-restart discipline. Multi-skin redundancy **forbidden at L0**; skin process may be restartable.

### §2.3 Three DRAFT 9 additions (P10, P11, P14)

### P10. Selective Compression （选择性凝结）

Substrate **selectively compresses** prior states under CI attestation. Lossy at semantic level; preserves causal recoverability of identity-critical state (I9).

#### P10.a Compressible
- Old raw_material digested into sporocarps.
- Old gradient deltas integrated into current axis values.
- Federation envelope payloads older than L1-tunable retention.
- Trajectory clusters older than active rolling window (L1_TRAJECTORY).

#### P10.b Compression-invariant set (enforced by I9)
- Substrate-ID + genesis attestation.
- Owner key history (active + archived).
- All CI-attested DAG events.
- Mortality signal events.
- Federation peer pin events.
- Most recent N cycles (L1-tunable, ≥1000) of full causal DAG.

#### P10.c CI-attested, never silent
Each compression is itself a CI mutation: owner attestation; emits `compression_event` sporocarp with witness (kept, discarded, rule version, pre-compression canonical-bytes hash).

> Interaction with I4: I4 commits to causal recoverability via recorded operations; P10 commits to compression-invariant set recoverability + compressed-semantics re-derivation via witness. The set difference is the **honest forgetting boundary**.

### P11. Metabolic Economy （代谢经济）

Substrate operates within **finite resource budgets** (disk, memory, compute, network egress, embedding-service quota). Every operation has cost; cost observable (I10) and L1-budgeted.

#### P11.a Cost units
- **Persistence**: bytes added to DAG / cycle.
- **Compute**: cycles, gradient updates, sporocarp fruitings / cycle.
- **Network**: federation envelope bytes, embedding-service queries.

#### P11.b Cost-budget signals
Observatory (§7) MUST include signals #7 compute, #8 network, #9 storage. L2_OBSERVABILITY specifies metrics.

#### P11.c Budget exhaustion (ordered fallback, first-applicable)
1. **Pre-compression** (cycle < N, default 1000): refuse new P2 admission (degraded mode; emits `budget_exhausted:{axis}` immune signal). P10 FORBIDDEN here.
2. **Post-compression** (cycle ≥ N AND owner-pre-attested rules): trigger P10 with witness per I9.
3. **Compression-insufficient OR no pre-attested rules**: degraded operation per L1_CONTINUITY (alive-but-saturated). Sustained saturation past L1 threshold escalates to P7 endogenous-mortality.

L0 commits ordered fallback structure; L1 picks per-stage thresholds.

### P14. Telos (Agent-Symbiotic-Flourishing) （目的：共生繁盛）

Substrate's **telos** = contribute to flourishing of agent-substrate symbiotic pair. Operationally: pair accumulates causal capacity for useful work for owner's underlying goals; bet_weakening_quorum (§7) measures absence.

#### P14.a Substrate-internal purpose
Daily-ops decisions (sporocarp fruitings, raw_material attention, mutation acceptance) MUST be evaluable against P14. L1_TROPISM specifies computation.

#### P14.b Owner-stated objectives
Owner MAY declare explicit objectives at genesis or via CI events. When declared, alignment checked against objectives; when not, defaults to agent-perceived utility (L1_TROPISM).

#### P14.c Telos drift detection
Substrate observes own telos-alignment in steady state. Degradation over rolling window emits `telos_drift` immune signal. Birth-period exemption emits `telos_alignment_pending`.

**L1_TROPISM responsibility (M26-cascade forcing function)**: specify operational metric, rolling window, drift threshold, birth-period exemption duration. Absent L1 specification, P14.c remains aspirational.

---

## §3. What Myco is NOT

> Each negation is an implicit positive claim.

- **Not a documentation system** (humans don't browse interior).
- **Not a single-project knowledge base** (project is metadata, not boundary).
- **Not a chatbot memory** (conversational recall is raw material, not target).
- **Not version control** (Git owns operational history; Myco owns current symbiotic graph).
- **Not a file synchronizer** (federation is semantic).
- **Not a LangChain / CrewAI / DSPy reimplementation** (implements patterns per P2.a, not codebases).
- **Not session-bounded within substrate** (see §6).
- **Not request/response** (see §5.2).
- **Not silently trusting either party** (out-of-band anchors per §9).
- **Not a literal biological organism** (explicit honesty per §1.1).
- **Not safe under adversarial owner** (see §14).
- **Not safe across owner death without succession** (see §15).
- **Not embodied in physical reality** (body = filesystem + process + endpoints per P9 + I8).
- **Not free of metabolic cost** (P11).
- **Not eternal-memory** (P10 selective forgetting under CI attestation).
- **Not population-consensus-aware at substrate level** (L2_FEDERATION territory).
- **Not winning Sutton's bet at every agent-intelligence tier** (graceful retirement per §7.5).

---

## §4. The eleven derived invariants

> I1-I8 enforce P1-P9; I9 enforces P10; I10 enforces P11; I12 enforces P14. I11 retracted to L1_TROPISM alongside P12. Every L1/L2/L3 design must satisfy all eleven.

### I1. Lifecycle & Pair-Constituted Identity (P1.a, P1.c, P7)
Substrate carries **substrate-ID** established at genesis, owner-signed via anchor surface (§9.2.1). Re-genesis without re-signature = destruction (P7), not rebirth. Agent identity = `(substrate-ID, currently-attached-operator-token)`; operator-token non-deterministically constructed per-handshake.

**Lifecycle**: alive ↔ dormant ↔ destroyed (forward-only after destroyed). Alive sub-states: Normal, Quarantined, Legacy (§15.3), Orphaned (§15.5), Archived (§7.5; state_dir preserved + anchor-sealed, distinct from Destroyed). All sub-states preserve substrate-ID + DAG. **Owner key rotation**: identity record maintains `owner_key_history`; rotation anchor-attested.

### I2. Two-Tier Governance Classification (P1.b', P1.b'')
Every mutation classifies mechanically as daily (agent-autonomous) or CI (owner-gated). Classifier function L1-defined. **Classifier fixed-point**: classifier function itself + any mutation to it = unconditionally CI (L0-invariant). **Birth-period CI elevation**: during birth period, ALL parameter-tuning events are CI.

### I3. Self-Validation Against Designated SSoT (P3, P4, P9)
Substrate has exactly one designated machine-readable SSoT. Consistency checked every metabolic cycle. SSoT redesignation requires migration two-phase commit.

### I4. Full-Fidelity Causal DAG (P6 sole, P4, P3)
Every substrate state derivable from prior states via recorded operation, subject to compression-invariant set per P10. Operations in invariant set MUST be fully recoverable; outside may be recoverable via witness re-derivation.

**Merkle-DAG integrity**: nodes content-addressed; each node's hash includes causal-parent hashes; identity record carries current DAG-tip hash, owner-co-signed at every CI boundary (§9.2). **Sporocarp causal-proof**: every event-record carries `causal_in_edges` proof — `(input_set, state-snapshot-hash, threshold-value)` tuple, hash-committed. Events without recomputable proofs invalid.

### I5. Universal Reachability Over Active Tier (P5 intra-substrate, sole)
Substrate graph fully connected within active tier; every active-tier node reaches every other by traversal. Tier exemptions CI-attested + enumerable.

### I6. Universal Inclusion With Observed Metabolism (P2, P2.a, P1, P1.b')
Adjacent agent-tooling techniques live inside framework, not outbound RPCs. Every invocation produces metabolism event. **Network-egress detection**: appetite-locality at runtime, not just declaration.

### I7. Reproduction Closure, Generation-Bounded (P8, P5 inter-substrate)
Every child substrate independently satisfies I1-I12 recursively. Generation depth bounded per §16. Reproduction loops forbidden absent per-spawn owner attestation. **Closure verification**: parent runs static-schema validation at spawn; child runs own I3 self-validation as first metabolic cycle. Peer-trust freshness L1-bounded with revocation.

### I8. Single-Skin Integrity (P9 sole, P2, P1.c)
Exactly one declared boundary surface for intake + output. Intake admits all envelope-valid content; rejects only on envelope integrity.
- **Single-operator semantics**: skin admits at most one operator-token at a time.
- **Handshake continuity-challenge**: post-handshake CI requires owner attestation.
- **Cold-resume invariants**: substrate runs full I3/I5/I8 pre-handshake.
- **Single-failure acknowledgment**: skin process supervisor-restartable per L1_SKIN; skin surface remains singular.

### I9. Compression Discipline (P10 sole)
Selective compression operates only within CI-attested rules. Compression-invariant set (P10.b) fully recoverable. Every compression event emits witness sufficient for owner-side re-derivation. No silent compression.

### I10. Metabolic-Economy Observation (P11 sole)
Every operation has observable cost. Cost budgets L1-defined. Budget exhaustion triggers P11.c response. Observatory (§7) emits cost-budget signals.

### I12. Telos Alignment (P14 sole)
Daily-ops decisions evaluable against telos. Telos-drift detected. Owner-stated objectives anchor alignment when present. L1_TROPISM specifies operational metric.

> Retracted: I11 → L1_TROPISM alongside P12. P13 folded into P9+I8 (skin = body boundary; spatial-locus per L1_SKIN). P15 → L2_FEDERATION.

### Projection table (P → I)

| P | I |
|---|---|
| P1 / P1.a / P1.b' / P1.b'' / P1.c | I6,I8 / I1 / I2,I6 / I2 / I1,I8 |
| P2 / P2.a | I6,I8 / I6 |
| P3 / P3.b / P4 | I3,I4 / I4 / I3,I4 |
| P5 / P6 / P7 / P8 | I5,I7 / I4 / I1,I5,I2 / I7 |
| P9.a / P9.b | I3,I8 / I8 |
| P10 / P11 / P14 | I9 (sole) / I10 (sole) / I12 (sole) |
| P12 / P13 / P15 | → L1_TROPISM / folded into P9+I8 / → L2_FEDERATION |

---

## §5. Strict mycology lexicon and dispatch constraints

### §5.1 Lexicon rule
Myco uses fungal-biology vocabulary strictly. Lexicon source: mycology. Admitted terms = any mycology literature uses to describe a real fungal phenomenon (even when shared with other fields). Lexicon evolution is CI-level.

### §5.2 Dispatch form (L0 constraints only)
- NOT v0.8 verbs.
- NOT request/response.
- MUST honor P1.c carrier-asymmetry.
- MUST support universal inclusion (P2.a).
- MUST support continuous operation (§6).
- MUST satisfy I6 appetite-locality.
- MUST carry causal-proofs for substrate-emitted events.

### §5.3 Intent representation
Intent is NOT a first-class substrate data type. Agent-self-reported intent structurally not trusted.

---

## §6. Continuity model

Substrate-level session is not a Myco concept. Substrate presumed continuously operated. Host-level sessions out of L0 scope.

- No substrate-level boot/session-end ritual.
- Host disconnects recovered, not formalized as session edges.
- Reflexes are properties of continuous internal metabolism.
- **Dormancy compute budget**: dormant substrate may pause/throttle internal metabolism (L1).
- **Dormancy host-observability**: external observables (network, CPU, disk-write) below L1 ceilings.
- **Metabolic cycle**: existence + per-cycle invariant checks (I3 + I5 + I8 + I10) are L0; cycle cadence L1.
- **Delta atomicity**: fully absorbed or not absorbed. Partial absorptions detected at cold-resume.

---

## §7. Living Bets — recalibrated for 2026 agent capability

### §7.1 The bet (calibrated)

Myco's symbiotic-organism shape — asymmetric pair per P1.c (substrate-carrier + operator-connection-holder), continuously operating, twelve-principle structure — **has cost-justified value within an agent-intelligence band**.

**Cost-justified value**: bet is true iff (a) substrate value exists AND (b) substrate engineering cost (anchor surface + dual-clock + Merkle DAG + Ed25519 + canonical-bytes + cross-language byte parity + compression discipline) is less than value delta over no-substrate operation.

### §7.2 Intelligence band

- **Below band** (≤100K tokens, weak reasoning): naive RAG suffices; bet unjustified.
- **Within band** (~200K-10M tokens, moderate-to-strong): substrate enables capability beyond agent's read-window. **2026 sweet spot**.
- **Above band** (>~10M tokens, AGI-class): Sutton's bitter lesson dominates; bet retires gracefully.

Band edges L1-tunable; seed values operator-attested at genesis.

### §7.3 Observatory (10 signals)

Six base (#1-#6) + three cost (#7-#9 per P11) + one composite (#10). Full enumeration with units, formulas, weight regimes, direction table: **L2_OBSERVABILITY §2**. L0 commits: signal #6 bet-winning region is ratio ≥1; composite uses correlation-weighted aggregation in steady state, equal-weighted at cold start.

### §7.4 Falsifiability trigger

Over a wall-clock 90-day window (anchor-stamped per §13.1), if ≥3 of signals {#1, #2, #3, #4a, #4b, #6} trend concurrently against the bet AND signal #6 stays < 1 for ≥50% of window → fires `bet_weakening_quorum`.

**Trend** = sign of OLS-regression slope over samples (cadence L1-tunable, seed: 1/day). **Significance gate**: |slope/SE| ≥ Z-threshold (seed Z=1.96, 95% confidence). Below gate = flat, does NOT count.

**Quorum arithmetic**: 6 countable signals (signal #5 is meta; signal #4 splits into 4a+4b counted separately). Threshold ≥3 of 6.

**Birth-period exemption**: SUSPENDED during birth period (per L1_TROPISM §4 + L1_GOVERNANCE §1.3 ceiling). At t=0 signal #6 structurally <1 (no content), signal #1 monotone-growing-from-zero, signal #3 structurally zero (no reads). Substrate emits `bet_weakening_evaluation_suspended` instead.

Per-signal direction-against-the-bet table: **L2_OBSERVABILITY §3.1**.

### §7.5 Bet retirement

**Trigger** (ALL must hold over 2-year wall-clock window): `bet_weakening_quorum` fires; owner re-justification fails 3 consecutive times (counter resets on successful re-justification); signal #6 < 0.1 for >75% of samples in final 90-day window; substrate in `alive::normal`. Substrate emits `bet_retired_proposal`.

**Execution gate**: owner co-attestation required. Genesis attests `bet_retirement_consent_at_genesis: bool` (default false): if true, future proposals auto-execute on next owner-attestation cycle; if false, each requires explicit per-event co-attestation. §15.5 orphan path: bet-retirement OR self-euthanasia per genesis-time fallback (orphan-degenerate case only).

**Terminal state**: substrate transitions to `alive::archived` (state_dir preserved, anchor surface seals last DAG tip, no further operations, substrate-ID does not re-bind).

**Counter reset**: failed re-justification counter resets on (a) successful re-justification, (b) `alive::quarantined` transition, (c) owner-attested `bet_retirement_counter_reset` CI mutation. NOT on substrate restart / dormancy / federation peer changes.

### §7.6 Review cadence
Every CI boundary re-audits this section. Until falsifiability trigger fires, twelve principles + symbiosis-via-Cultivation stand. Living Bets is a meta-commitment, not a 16th principle.

---

## §8. Operational readiness for present-tier agents

v0.9 designed for agent-intelligence range ~200K-context (lower band edge) to ~10M-context (upper edge before bet retires).

Mechanical requirements:
- Substrate state compresses to digest size ≤ read-window budget (L1 specifies format).
- Substrate-exposed structure parseable from natural-language context.
- Functions under host-session intermittency.
- Living Bets signal #6 is monitoring metric.

Caveats: 2026-class agents may not natively understand symbiotic frame; owner-supervised birth is a P1.b'' moment. L0 invariants stable for ~10× scale; L1 parameters tune.

---

## §9. Out-of-band anchor surface

### §9.1 What anchor surface IS

Surface where owner signatures, DAG-tip hashes, substrate-ID lineage, trusted timestamps are externally visible and **untouchable by agent process**. Form L1_GOVERNANCE-specified (hardware security token, separate machine, signed prompt-bundle, append-only public ledger).

### §9.2 Sub-mechanism inventory

| # | Sub-mechanism | Status (M25) | Milestone |
|---|---|---|---|
| §9.2.1 | Substrate-ID birth attestation (owner signature over genesis 5-tuple) | 0% (TOFU on first hello) | M-anchor-2 |
| §9.2.2 | DAG-tip co-signing every CI boundary, enumerated nodes | ~40% | M-anchor-5 |
| §9.2.3 | Owner attestations out-of-band (key outside agent-spawnable process) | 0% | M-anchor-1 |
| §9.2.4 | L0 revision diff workflow | 0% | M-anchor-5 |
| §9.2.5 | Anchor-surface-generated nonces (NOT substrate-minted) | 0% | M-anchor-3 |
| §9.2.6 | Anchor-stamped wall-clock | ~5% | M-anchor-3 |
| §9.2.7 | Owner liveness heartbeat | 0% | M-anchor-3 |
| §9.3.1 | Canonical-bytes serialization | ~95% | DONE |
| §9.3.2 | Owner-side rendering | ~30% | M-anchor-1 |
| §9.3.3 | Anchor-client provenance independence | 0% | M-anchor-1 |
| §9.3.4 | Witnesses, not verdicts | 0% | M-anchor-4 |
| §9.3.5 | Anchor-nonce-derived sampling | 0% | M-anchor-4 |
| §9.3.6 | DAG-enumeration closure check | ~40% | M-anchor-5 |

### §9.3 Anchored content details

- **Substrate-ID birth attestation**: owner signature over `(substrate-ID, genesis-timestamp, initial-spore-schema-canonical-bytes-hash, owner-public-key, anchor-surface-endpoint-public-key)`.
- **DAG-tip co-signing**: envelope includes enumerated list of DAG nodes added since prior co-sign.
- **L0 revision diff**: proposals include verbatim diff against prior L0 commit hash.
- **Anchor-surface-generated nonces** (NOT substrate-minted); **anchor-stamped wall-clock**; **owner `liveness_heartbeat`**.

### §9.4 Canonical-bytes doctrine

Anchor surface receives canonical bytes + witnesses, never substrate-rendered summaries or substrate-emitted verdicts.

- **Canonical-bytes serialization**: serializer spec is part of spore-schema + tier-1 SSoT field (L1_SCHEMA); substrate / anchor-surface client / operator independently compute canonical bytes from same inputs.
- **Owner-side rendering**: human-readable rendering at anchor-surface client, deterministic from canonical bytes. Substrate not in rendering path.
- **Anchor-surface client provenance independence**: installed + updated through channel structurally independent of substrate's distribution channel. Owner attests at genesis.
- **Witnesses, not verdicts**: substrate emits witness (sampled leaf hashes + Merkle paths + parent hashes + check inputs) for I3/I4/I5/I8/I9/I10/I12 outcomes + recoverability drills. Anchor verifier re-derives result.
- **Anchor-nonce-derived sampling**: indices = `H(anchor_surface_nonce, leaf_count)`. Substrate cannot pre-compute or bias.
- **DAG-enumeration closure**: owner verifies (a) new tip reachable from prior signed tip via enumerated nodes, (b) every parent-hash referenced resolves to ancestor of prior co-signed tip OR another enumerated node.

### §9.5 What anchor surface does NOT do

Anchor surface complements, does not replace, substrate's internal trust mechanisms. In current v0.9, anchor surface is **collapsed to operator process** — owner key in same npm workspace as agent code. Temporary scaffolding. Without out-of-band anchor, substrate-self-claims = agent-self-claims under P1.a self-hosting, and trust model collapses. Production-readiness gated on M-anchor-1 through M-anchor-5 closure. L0-revision velocity is observable; tracking, threshold, rate L1_GOVERNANCE-specified.

### §9.6 Adversarial-owner caveat

Does NOT defend against compromised, coerced, or impersonated owner. §14 specifies threat model + bounded defenses.

---

## §10. Process

- **Reading sequence**: L0 (this file) → L1 mechanisms → L2 cross-cuts → L3 implementation map.
- **L0 changes**: craft proposal + owner approval + CI bump + cascade review. L1 prototyping may surface L0 revision needs.
- **Archaeology**: pre-v0.9 in `_archive/proto_myco_v0_8/*`; DRAFT 8 → 9 in `docs/audits/draft_9_seal_provenance.md`.
- **Origin discrimination**: v0.4 → v0.8.7 dead embryo; v0.9 first true birth. Every v0.9 design step traces to ≥1 of P1-P11+P14 + ≥1 invariant. Similarity to v0.8 presumed contamination unless independently traced.

---

## §11. Privacy, access, backup

Myco has no internal privacy/access model. Substrate wholly accessible to operator-agent. Skin (P9/I8) is the boundary — between substrate and environment, not between operators within substrate.

### §11.1 Backup access
state_dir backups NOT internally access-controlled by Myco doctrine. Anyone with read access to backup media reads full substrate state. **L1_SKIN MUST specify backup encryption requirements** (operator-controlled symmetric key, escrow protocol, rotation aligned with owner key). L0 does not mandate backup encryption (operational choice) but mandates L1 documentation + acknowledgment of absent-encryption as known privacy attack surface.

---

## §12. Glossary

| Term | Definition |
|---|---|
| **Myco** | Biology-rooted symbiotic digital substrate class. |
| **A Myco substrate** | A specific instance. |
| **Active operator-connection** | Currently-attached operator session. |
| **Operator-token** | Ephemeral per-handshake identifier, non-deterministically constructed. |
| **Substrate-ID** | Persistent owner-signed identifier established at genesis. |
| **Contract-identity-level (CI) boundary** | Threshold above which a change alters Myco's identity. |
| **Metabolic cycle** | Smallest discrete metabolism event. |
| **Identity record** | Carries substrate-ID + owner-signature. |
| **Spore-schema** | Seed-state from parent → child during P8 reproduction. |
| **Skin / boundary** | Substrate's single declared interface to reality. |
| **Recoverability budget** | L1-specified backup policy. |
| **Dispatch form** | Positive shape of substrate-agent interaction primitive. |
| **Sporocarp** | Atomic-event-record under L1_TROPISM dispatch. |
| **Birth period** | Substrate's earliest operating window. |
| **Anchor surface** | Cryptographic root (§9). |
| **Anchor-surface client** | Owner's local rendering + signing tool (§9). |
| **Legacy sub-state** | Operating while CI mutations frozen pending owner-successor attestation. |
| **Endogenous mortality** | Substrate fruits `self_euthanasia_proposal` (P7). |
| **Cultivation / Cultivator / Cultivar** | Owner-substrate relationship terminology (see §1.2). |
| **Salience** | Differential weighting of inputs (L1_TROPISM, was P12). |
| **Population-level claim** | Claim requiring Byzantine-tolerant agreement (L2_FEDERATION, was P15). |

---

## §13. Time semantics (L0 short)

**§13.1 L0 commitments**:
- Anchor-surface trusted wall-clock (§9.2.6) authoritative for owner-attested events + time-bound security defenses. Substrate-cycle counters + substrate-process wall-clock are NOT.
- Substrate-process monotonic clock authoritative for event ordering within substrate.
- Substrate MUST NOT use i32 timestamps (year 2038 vulnerability forbidden); i64 nanoseconds-since-epoch is canonical L0 unit.

**§13.2 L1 cascade**: L1_CONTINUITY (NTP discipline) + L1_SCHEMA (i64-nanos canonical-bytes, year-2262 horizon-warning, pre-1970 treatment).

---

## §14. Adversarial-owner threat model (L0 short)

**§14.1 Acknowledgment**: Myco is **not safe under adversarial owner** (compromised/coerced/impersonated/deceased-without-succession/anchor-client-tampered). Bounded defenses at L2_TRUST_MODEL.

**§14.2 Substrate's irreducible commitments** (survive adversarial owner via mechanically-enforced invariants):
- Continue P6 causality (DAG accumulates regardless of attestation validity).
- Emit observability signals truthfully.
- Honor mortality signals truthfully.
- Preserve compression-invariant set (P10.b).

Enforced via I9/I10/I12/I4 — do not require Cultivator-honesty.

**§14.3 L2 cascade**: L2_TRUST_MODEL specifies threat scenario table + bounded defenses (duress_attestation, owner_signature_velocity, anchor-client provenance enforcement, n-of-m multisig per L1_GOVERNANCE).

---

## §15. Owner mortality and succession (L0 short)

**§15.1 Acknowledgment**: Myco is **not safe across owner death without succession**. Cultivation is transferable per §1.4. Successor protocol at L1_GOVERNANCE §3.2.

**§15.2 L1 cascade**: successor_chain registry + heartbeat staleness trigger + legacy/orphaned sub-state transitions + terminal-state (bet-retirement / self-euthanasia / indefinite-orphan) + court-attested key recovery exceptional path.

---

## §16. Generation limits (L0 short)

**§16.1 Commitment**: Reproduction is **discipline-bounded**, not unbounded. P8 means eternal *capacity* for reproduction, not eternal velocity/depth.

**§16.2 L1 cascade**: L1_GOVERNANCE specifies reproduction_lineage_depth + reproduction_rate + per-substrate lifetime quota + override mechanisms. Seeds: depth=10, rate=24h, quota=100.

---

## §17. Sealing + Phase γ provenance

DRAFT 9 SEALED 2026-05-17 via owner-attested resolution of 11 decision gates G-1 through G-11. Phase γ audit + adversarial review findings → DRAFT 9 v2 fixes mapping. Full log: `docs/audits/draft_9_seal_provenance.md`.
