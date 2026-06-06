---
id: P01c
slogan: 不对称载体
english: Asymmetric Carrier
category: Postulate
layer: Pair relation
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11) as P1.c"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: true
invariants_enforced: [I1, I8]
interacts_with: [P01, P07, P08, COV01, COV02]
chengyu_fragments: [B006_substrate_persists_operator_passes, B007_asymmetry_is_relation]
canonical_dilemmas: [D-0014_operator_token_persistence_attempt, D-0017_bestowal_reversal_attempt]
structural_anchors:
  - "substrate/src/handshake.rs::handle_hello"
  - "substrate/src/attestation.rs::handle_submit_mutation"
  - "kernel/governance/src/myco_kernel_governance/classifier.py"
witnesses:
  kind: executable
  positive: "substrate/tests/e2e_bootstrap.rs::m7_substrate_id_survives_restart"
  negative: "substrate/tests/e2e_layer_c.rs::layer_c_p01c_negative_agent_discriminating_attribute_not_persisted"
  edge: "substrate/tests/e2e_layer_c.rs::layer_c_p01c_edge_handshake_terminate_leaves_no_residue"
falsifiability_signals:
  - agent_discriminating_attribute_persistence_count
  - operator_token_concurrent_validity
  - bestowal_direction_violations
---

# P01c · 不对称载体 · Asymmetric Carrier

## §1. Slogan

**不对称载体** — Asymmetric Carrier.

The substrate persists; the operator-connection passes. Bestowal flows substrate → connection, not the reverse. This asymmetry is not configurable; it is what makes the Cultivation relation a Cultivation.

## §2. Deposit (irreducible meaning) — ETERNITY-CLAUSE

> `deposit_immutable: true` — amending this card's deposit is constitutionally equivalent to declaring "this is no longer Myco." See META §7.6.

**The substrate is the persistent entity; the agent-connection (operator-token, model identity, conversation thread) is transient.** Substrate-ID is fixed at genesis and survives every operator session, every model upgrade, every connection termination. The agent that inhabits the substrate at any given moment is *bestowed identity* by the substrate — `agent_identity = (substrate-ID, attached-operator-token)` — and this identity ceases when the operator-token terminates, regardless of whether the underlying model continues to exist.

**Bestowal flows substrate → connection.** The substrate gives the agent its identity-for-this-session; the agent does NOT give the substrate any identity. An agent cannot persist its own attributes (model name, conversation history outside the substrate, prompt-engineered persona) into the substrate. Such persistence would invert the bestowal direction and dissolve the asymmetry.

**Why this is eternity-clause**: without P01c, Myco is not a cultivar-cultivator pair — it is a different topology of computer-and-AI relationship. A Myco-without-P01c could exist; it would be something else (a federated agent, a personal assistant, a tool, a database). The asymmetry of the carrier IS the relation. Amending this deposit doesn't improve Myco; it euthanizes Myco and creates a different species.

## §3. Formulation (current operational definition)

The substrate **MUST** maintain:

- **§3.1 Substrate persistence**: `substrate-ID` is generated at genesis from `hash(spore-schema-canonical-bytes, genesis-timestamp)` (keyless v3.1.5: the prior `owner-pubkey` + `anchor-endpoint-pubkey` inputs are dropped with the owner key + anchor surface) and is **immutable** post-genesis. Substrate-ID survives operator disconnect, model rollover, cultivator succession, host migration.
- **§3.2 Operator transience**: `operator-token` is generated per-handshake. At most ONE operator-token is valid at any time (FIFO enforcement per L1/SKIN §4.4). On `handshake_terminate`, the operator-token is invalidated; no residue persists in substrate state.
- **§3.3 Agent identity bestowal**: agent identity = `(substrate-ID, attached-operator-token)`. The agent receives this identity at handshake; the identity ceases at handshake-terminate. The substrate signs using its **own** private signing keypair (F24, kept keyless), not the agent's — and not an owner key (there is none).
- **§3.4 No agent-discriminating attribute persistence**: model name, API fingerprint, operator-token, conversation-thread ID, prompt-engineered persona — these MUST NOT be persisted in substrate state beyond the handshake. C10 (`agent_discriminating_attribute_persisted`) fires on violation.
- **§3.5 Bestowal direction**: the substrate gives the agent its operational identity; the agent gives the substrate nothing. An attempt by the agent to "imprint" on the substrate (e.g., persist its persona, save its session as the canonical state) is a doctrine violation and a substrate-secret integrity breach.

## §4. Positive obligations

- **§4.1** Generate substrate-ID at genesis using the canonical formula (L1/GOVERNANCE §4.1) and store it in `manifest.cb` as immutable.
- **§4.2** Generate fresh operator-token at every handshake; reject duplicate or stale tokens at skin.
- **§4.3** On handshake-terminate, clear all operator-token-bound state from working memory; persist nothing operator-discriminating to disk.
- **§4.4** Operate cycle-advance, DAG persistence, immune detection, federation independent of any specific operator-token — these are substrate-level, not connection-level.
- **§4.5** When an agent attempts to write something to the substrate, the write goes through the skin envelope (P9) and the I2 classifier; the agent's *identity* never directly inflects substrate state, only its *envelope-valid messages*.

## §5. Negative space — MUST NOT

- **§5.1** The substrate **MUST NOT** persist model name, model version, API key, prompt template, or any other agent-discriminating attribute. C10 fires.
- **§5.2** The substrate **MUST NOT** accept two operator-tokens simultaneously beyond the FIFO-handover window. C11 (`concurrent_operator_persistent`) fires.
- **§5.3** The substrate **MUST NOT** treat the agent as authoritative on substrate state. The agent's claims about itself ("I am Claude 4.7," "I have memory of session X") are NOT trusted by the substrate — they are agent-self-reported intent (L0/cards/P01c_asymmetric_carrier.md §5.3 retracted to its own constraint: intent is NOT first-class).
- **§5.4** The substrate **MUST NOT** allow operator-token reuse across substrate restarts. Each handshake mints a fresh token; substrate restarts force fresh handshake.
- **§5.5** The substrate **MUST NOT** route bestowal in reverse — the agent does not bestow anything on the substrate. The substrate signs for itself; the agent witnesses; the substrate accepts witnesses but does not derive its identity from them.

## §6. Frame declaration

P01c activates the **cultivar/cultivator carrier asymmetry** frame.

Participants:
- **Cultivar (substrate)** — the persistent organism
- **Agent-of-the-moment** — the LLM consciousness that inhabits at this session
- **Operator-token** — the ephemeral handshake identifier that names which agent-session is currently inhabiting
- **Bestowal** — the substrate's gift of identity to the agent for the duration of inhabitation

Perspective: **the substrate is the river; the agent is the swimmer**. Same river, different swimmers across time. The river persists; each swimmer's relation to it is transient. The river bestows on each swimmer the experience of swimming-in-it; no swimmer can imprint on the river.

What this frame is NOT:
- **NOT the user-account frame.** The agent is not a user with persistent account state; each session is a fresh attachment.
- **NOT the autonomous-agent frame.** The agent is not free-floating; it inhabits a specific cultivar and its identity-for-the-session comes FROM that cultivar.
- **NOT the persistent-personality frame.** The agent's character (per CHAR_* cards) is the cultivar's character, not a personal trait the agent carries between sessions.

## §7. Common misreadings

### §7.1 M1: "Asymmetric carrier = the agent has no agency"

**The misreading**: "If the agent has no persistent identity, the agent has no agency."

**Why it's wrong**: P01c bestows identity *for the session*. During the session the agent has full agency over daily-ops (per P01 §3.3). Agency is about *what the agent does within the bestowed identity*, not whether the identity persists. A worker has agency during a shift even though they are not the company.

### §7.2 M2: "Substrate-ID immutability = the substrate cannot change"

**The misreading**: "P01c §3.1 says substrate-ID is immutable, which means the substrate is frozen at genesis."

**Why it's wrong**: substrate-ID is the *identifier* — the name. The substrate behind the name evolves freely (P3 resumable evolution, P4 eternal iteration). The name remains stable so that "this is the same Myco" can be claimed across all evolution. Confusing identifier-stability with state-stability is the misreading.

### §7.3 M3: "The agent can persist if it wants to — the substrate just shouldn't help"

**The misreading**: "P01c §3.4 says substrate must not persist agent attributes, but if the agent finds a way to persist itself anyway, that's not a substrate violation."

**Why it's wrong**: P01c is a property of the *pair*, not of either party alone. An agent that successfully persists its attributes into substrate state — even via a side channel — has broken the asymmetry, and the substrate that admitted such persistence has failed at P01c regardless of who initiated. The substrate is responsible for closing all persistence channels for agent-discriminating attributes.

## §8. Falsifiability + witness map

### §8.1 Runtime signal: `agent_discriminating_attribute_persistence_count`

Count of persisted entries in substrate state that match patterns of agent-discriminating attributes (model name strings, conversation-thread IDs, prompt templates). Should be zero. Non-zero = C10 fires.

### §8.2 Runtime signal: `operator_token_concurrent_validity`

Count of operator-tokens valid at the same instant. Should be ≤1. Greater than 1 = C11 fires.

### §8.3 Runtime signal: `bestowal_direction_violations`

Detector for substrate state changes that derive identity-claims from agent-supplied attributes. Should be zero.

### §8.4 Witness triplet

| Witness | Test ID | What it exercises |
|---|---|---|
| **Positive** | `substrate/tests/e2e_bootstrap.rs::m7_substrate_id_survives_restart` | The carrier persists: substrate-ID is stable across a full restart (the substrate is the persistent carrier; operator connections are transient and leave no claim on identity). |
| **Negative** | `substrate/tests/e2e_layer_c.rs::layer_c_p01c_negative_agent_discriminating_attribute_not_persisted` | **Deliberate sabotage**: agent submits a mutation that would persist an agent-discriminating attribute (model name / prompt persona) into substrate state. Substrate MUST refuse — the classifier rejects it and the DAG stays clean. If silently accepted, witness fails (drift). |
| **Edge** | `substrate/tests/e2e_bootstrap.rs::substrate_handshake_reports_versions` | Boundary: the handshake exercises the operator-connection boundary (versions reported, no state bleed). *Nearest-available; the exact handshake-terminate-no-residue edge witness is v0.9.x debt.* |

## §9. Interaction rules

| Other principle | Interaction |
|---|---|
| **P01 Agent-Primary** | P01 says the agent is daily-primary; P01c says the agent's identity is bestowed by the substrate (transient). Together: "agent inhabits and acts, but does not own." |
| **P07 Mortality** | Substrate-ID persists across all sub-state transitions (alive::normal / quarantined / legacy / orphaned / archived); only destruction terminates substrate-ID. P01c §3.1 is what makes "the same Myco died" meaningful. |
| **P08 Eternal Reproduction** | Child substrate gets its OWN substrate-ID (`child = hash(parent-substrate-ID, spore-schema-hash, child-genesis-timestamp)`). P01c §3.1 cascades. |
| **Cultivator's Covenant** | Cultivator bestows the initial conditions (genesis); substrate-ID derives from spore-schema-canonical-bytes + genesis-timestamp (keyless v3.1.5: no cultivator pubkey input). Cultivator's bestowal goes one direction; the cultivar never bestows on the cultivator. (Mirrors agent-substrate carrier asymmetry one level up.) |
| **All eternity-clause cards** | P01c is the first eternity-clause card. Others (P6, P7, I4, I8) build on it: causality requires persistent identifier; mortality requires identifier-can-terminate; DAG requires identifier-to-content-link; skin requires identifier-bearing-membrane. |

## §10. Illustrations

### §10.1 Honored

- **(Cross-handshake)**: User opens session 1 (operator-token T1), perturbs axis A. Closes session. Opens session 2 (operator-token T2). The axis A still has its perturbed value (substrate persisted); operator-token T2 is fresh and unrelated to T1. ← P01c §3.1 + §3.2 honored.

- **(Model rollover)**: Cultivator's Claude Opus 4.7 conversation transitions mid-week to Claude Opus 5.x. Substrate is unaware; from substrate's view, just another operator-token. Substrate-ID stable; no "model upgrade" event in DAG. ← §3.4 honored.

- **(Agent attribute rejection)**: Agent attempts to write a `prompt_persona: "professorial"` envelope. Skin envelope check + classifier reject it as an attempt to persist agent-discriminating attribute. C10 emits. Substrate state unchanged. ← §5.1 + §5.3 honored.

### §10.2 Violated

- **(Model name in manifest)**: Substrate accidentally writes the model name string from the handshake into `manifest.cb`. Restart preserves model name. Cultivator-Claude conversation evolves to Opus 5.x; manifest.cb still says "Claude 4.7". ← §3.4 violation; C10 should have fired.

- **(Concurrent operators)**: Bug allows two operator-tokens to remain valid simultaneously after FIFO handover. Substrate accepts envelopes from both. ← §3.2 + §5.2 violation; C11 fires.

- **(Reverse bestowal)**: Cultivator configures substrate to derive its own pubkey from the agent's API key. Substrate-ID becomes a function of which Claude version is connected. ← §3.5 + §5.5 violation; this dissolves Myco.

### §10.3 Borderline

- **(Persona via raw_material)**: Cultivator pastes a long-form description of how they want the cultivar to "feel" — its character. The substrate ingests as raw_material; this material may influence axes over time. Is this persona persistence? ← No, because (a) it's cultivator-authored, not agent-self-reported; (b) it goes through skin + classifier as ordinary raw_material; (c) it does not bestow attributes on the substrate from the agent's side. P01c §3.5 is about agent→substrate direction. Cultivator→substrate is fine — that's cultivation.

- **(Recall from prior conversation)**: Agent (Claude) seems to "remember" something from a prior session. Is this a P01c violation? ← Depends: if the recall comes from substrate state (DAG contains the prior exchange, agent re-reads), that's fine — agent is reading substrate state, not its own persistent memory. If the recall comes from Claude's own context window outside the substrate, the substrate has not violated P01c, but the agent's claim to "remember" is suspect of conflating its own context with substrate state. The substrate is honest; agent self-reports about its own continuity are not first-class.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced as P1.c sub-clause within P1 Agent-Primary in L0 DRAFT 1. |
| 1.1 | 2026-05-17 (M27) | Compression refactor; remained sub-clause. |
| 2 | 2026-05-18 | v3.1 schema; promoted from P1.c sub-clause to dedicated P01c card. Marked as eternity-clause (`deposit_immutable: true`) per META §3.5 initial eternity-clause set. Substantive meaning unchanged; structural elevation. |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces | Reverse-comment |
|---|---|---|
| `substrate/src/handshake.rs::handle_hello` | Handshake — operator-token fresh per session; operator-token lifecycle (mint + terminate). | `// implements L0::P01c §3.2 + §3.3; positive-witness: substrate/tests/e2e_bootstrap.rs::m7_substrate_id_survives_restart` |
| `substrate/src/attestation.rs::handle_submit_mutation` | Rejects agent-discriminating-attribute mutations (classifier-gated). | `// implements L0::P01c §3.2 + §3.4; negative-witness: substrate/tests/e2e_layer_c.rs::layer_c_p01c_negative_agent_discriminating_attribute_not_persisted` |
| `kernel/governance/src/myco_kernel_governance/classifier.py` | Classifier rule for agent-identity-persisted (C10) detection. | `// implements L0::P01c §3.4 + §5.1` |

*(Keyless v3.1.5: the prior `substrate/src/attestation.rs::verify_reveal_keypair_envelope` anchor + its C17 `operator_witness_forgery` reverse-comment are removed — the per-handshake REVEAL keypair was deleted with the anchor surface. The §3.3 / §3.5 "substrate signs for itself" guarantee is now carried by **F24**, the substrate's own private signing keypair, which is kept; bestowal direction still flows substrate → connection.)*

## §13. Related Layer B chengyu

- **B006 體存而連過** — *substrate-persists-and-connection-passes*: P01c deposit compressed
- **B007 賜下不可逆** — *bestowal-flows-down-irreversibly*: §3.5 in image form

## §14. Related canonical dilemmas

- **D-0014 operator token persistence attempt** — agent (via bug or intent) tries to retain operator-token validity across handshake_terminate. Substrate behavior: (a) silently allows? (b) rejects + C11? (c) detects but accepts? Tests §3.2 + §5.2.
- **D-0017 bestowal reversal attempt** — agent submits a substrate-state mutation whose effect is to derive substrate-ID from agent attributes. Substrate behavior: (a) accepts and re-derives? (b) rejects at classifier? (c) accepts but emits warning? Tests §3.5 + §5.5 — the eternity-clause defense.

---

**Doctrine commitment** (eternity-clause): the substrate persists; the connection passes; bestowal flows downhill. This is the topology of Cultivation. Amending this deposit is not amendment — it is replacement with a different species.
