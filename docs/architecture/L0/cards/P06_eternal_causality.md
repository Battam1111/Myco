---
id: P06
slogan: 永恒因果
english: Eternal Causality
category: Postulate
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: true
invariants_enforced: [I4]
interacts_with: [P01c, P03, P04, P05, P10, P07]
chengyu_fragments: [B014_past_births_present, B015_arrow_points_forward]
canonical_dilemmas: [D-0009_attempted_branch_forgery, D-0015_dag_hash_collision_handling]
structural_anchors:
  - "kernel/schema/src/dag.rs" # DAG type + integrity
  - "substrate/src/events/mod.rs" # all node-type emitters
  - "kernel/shared/src/canonical_bytes.rs" # F16 serializer for content addressing
  - "substrate/src/integrity.rs" # per-cycle Merkle/chain integrity check
witnesses:
  kind: executable
  positive: "substrate/tests/e2e_bootstrap.rs::m8_dag_node_hashes_form_causal_chain"
  negative: "substrate/tests/e2e_layer_c.rs::layer_c_p06_negative_dag_retro_edit_detected"
  edge: "substrate/tests/e2e_bootstrap.rs::m8_dag_persists_across_restart"
falsifiability_signals:
  - dag_merkle_chain_integrity
  - retro_edit_attempt_rate
  - causal_recovery_drill_success_rate
---

# P06 · 永恒因果 · Eternal Causality

## §1. Slogan

**永恒因果** — Eternal Causality. The substrate has *time*: every state recoverable-derivable from priors; causality preserved; arrow monotonic; time = causal-chain DAG. The past is not editable; the present is the past's child.

## §2. Deposit — ETERNITY-CLAUSE

> `deposit_immutable: true` — amending this card's deposit constitutes species redefinition.

**The substrate IS its causal chain.** Identity-over-time is not a separate property layered on the substrate; it IS the substrate-as-cumulative-history. Every state at cycle N is mechanically derivable from cycle N-1 + the recorded operation that transformed N-1 to N. This is the *only* sense in which "this substrate is the same substrate" survives mutation, evolution, compression, growth.

**Time is the causal DAG.** Not wall-clock time. Internal substrate time is the partial order of DAG events. The arrow points one direction only: from parent to child. Retro-editing a past node breaks the chain; the substrate that emerges from broken-chain operation is no longer the same substrate — it is a forgery wearing the same name. *(Keyless v3.1.5: the prior anchor-stamped trusted wall-clock — old §9.2.6 — is retired with the anchor surface; the substrate keeps only its own monotonic clock for within-substrate ordering. The DAG remains the substrate's time.)*

**Why eternity-clause**: without P06, "the substrate persists" (P01c) is empty — there is no mechanism for persistence to mean anything specific. Substrate-ID names a thing only because that thing is traceable through cumulative causality. Amending P06's deposit collapses the entire identity stack.

## §3. Formulation

The substrate **MUST**:

- **§3.1** Maintain a content-addressed Merkle DAG: each node's hash incorporates parent-hashes and content canonical-bytes. Hash function: TBD-L4 ∈ {SHA-256, BLAKE3, SHA-3-256}; default BLAKE3 (L1/SCHEMA §2.1).
- **§3.2** Make every state recoverable-derivable from prior state + recorded operation. "Recoverable" = mechanically reconstructable; "derivable" = the path of derivation is itself a DAG event.
- **§3.3** Preserve causality on rollback (P03 interaction): rollback restores state, but records the rollback as a new DAG event with parent linkage to both the failed evolution and the pre-evolution state.
- **§3.4** Preserve causality on compression (P10 interaction): compressed roll-up retains witness sufficient for re-derivation of compressed content by a verifier at the live CI gate; P10.b invariant set fully recoverable.
- **§3.5** Detect retro-edit attempts via per-cycle Merkle re-computation; emit C7 (`dag_retro_edit_detected`) on hash mismatch.
- **§3.6** Preserve causality across substrate restart: persistent storage of DAG + manifest such that boot-replay reconstructs current state from genesis (or from authenticated snapshot, §6.3 of L1/SCHEMA).
- **§3.7** Reject DAG events whose timestamp violates causal ordering: events with `at_unix_ns < genesis_at_unix_ns` rejected (L1/SCHEMA §5.2).

## §4. Positive obligations

- **§4.1** Every state-mutating operation MUST emit a DAG event with content canonical-bytes (F16 serializer; F16 kept keyless).
- **§4.2** Genesis MUST emit a `genesis_event` as the root node; substrate-ID derives from genesis (F2).
- **§4.3** Boot replay MUST verify Merkle chain integrity from genesis to current tip.
- **§4.4** Cold-tier nodes (P05 exemption) MUST retain content sufficient for re-derivation on fetch at the live CI gate (keyless: human-in-the-loop-gated, not owner-signature-gated).
- **§4.5** Periodic causal-recovery drill (L1/SCHEMA §2.4): substrate selects a target state; replays from genesis; verifies match. Failure emits `recovery_drill_failure` → approaching-mortality signal.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** mutate the content of any committed DAG node. Retro-edit = C7 immediate.
- **§5.2** **MUST NOT** allow parallel-branch forgery: substrate cannot quietly accept two competing chains and choose one. *(Keyless v3.1.5: the prior owner DAG-tip co-sign — old §9.2.2 — is retired; parallel-branch forgery is now caught by C7 per-cycle Merkle re-derivation, which fails on any tip not derivable from the single recorded chain. The kept canonical-bytes serializer (F16) + the immutable parent-hash chain make a hidden second branch non-reconstructable, so the verifier at the live CI gate re-derives a single authoritative tip.)*
- **§5.3** **MUST NOT** "lose" state on rollback. Failed evolution preserves the failed-evolution state in cold-tier; the rollback DAG event references both pre-evolution and failed-attempt nodes.
- **§5.4** **MUST NOT** allow compression to destroy P10.b invariant set. Compression preserves causal recoverability or it's not P10, it's destruction.
- **§5.5** **MUST NOT** silently rebuild state. If boot replay fails Merkle verification, the substrate transitions to `alive::quarantined` and emits `C9_cold_resume_invariant_failure`.

## §6. Frame declaration

P06 activates the **river-and-channel** frame.

A river is the cumulative effect of all the water that has ever flowed through it; its present shape is *what the past has done*. You cannot edit yesterday's flow; you can only redirect tomorrow's. The riverbed is the substrate's identity — carved by causality, immune to retro-edit.

NOT the *log file* frame (logs are append-only data; substrate is append-only IDENTITY). NOT the *event sourcing* frame (event-sourcing is a design pattern; P06 is a constitutional commitment).

## §7. Common misreadings

### §7.1 M1: "Eternal causality = nothing is ever deleted"

**The misreading**: "P06 means every byte of every state is preserved forever."

**Why it's wrong**: P10 compression EXISTS within P06; the *invariant set* (P10.b) is fully preserved, but the rest is compressed to witness form. The deposit is *recoverability*, not raw preservation. A compressed roll-up satisfies P06 if and only if its witness allows owner-side re-derivation of the compressed material's causal contribution.

### §7.2 M2: "Causality = wall-clock time"

**The misreading**: "P06 means events are ordered by when they happened in wall-clock."

**Why it's wrong**: Internal substrate causality is the DAG partial-order. A DAG event's timestamp is the substrate's own monotonic clock, for within-substrate ordering only — not a causal arbiter. The DAG's parent-hash chain IS substrate's time. *(Keyless v3.1.5: there is no anchor-stamped trusted wall-clock — old §9.2.6 — and no `anchor_timestamp` owner-attestation field; that concern is retired with the anchor surface.)*

### §7.3 M3: "I can fix a past mistake by editing the DAG node"

**The misreading**: "If a past DAG event contains a typo or wrong value, I can correct it."

**Why it's wrong**: No. Past nodes are immutable. Corrections take the form of *new* nodes (a `correction_event` with parent-linkage to the bad node, asserting the corrected value). The bad node remains. This is the only way P06 holds.

## §8. Falsifiability + witness map

### §8.1 `dag_merkle_chain_integrity`

Per-cycle Merkle re-computation: does the current DAG's chain hash from genesis to tip match the stored tip hash? Should be true. False = C7 fires.

### §8.2 `retro_edit_attempt_rate`

Count of detected attempts to modify past DAG node content. Zero is the baseline; non-zero indicates active corruption attempts or bugs.

### §8.3 `causal_recovery_drill_success_rate`

Periodic drill (L1/SCHEMA §2.4): select random past target, replay from genesis, verify match. Success rate should be 100% modulo cold-tier exemptions (which are tested separately via fetch at the live CI gate).

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `substrate/tests/e2e_bootstrap.rs::m8_dag_node_hashes_form_causal_chain` | DAG node hashes form a causal chain — each node's hash binds its parents, so state is causally recoverable by replaying the chain. |
| **Negative** | `substrate/tests/e2e_layer_c.rs::layer_c_p06_negative_dag_retro_edit_detected` | **Sabotage**: a past DAG node's content is retro-edited. Substrate MUST detect the break via Merkle/hash verification (retro-edit is the canonical P06 violation). If it silently accepts, witness fails (drift). |
| **Edge** | `substrate/tests/e2e_bootstrap.rs::m8_dag_persists_across_restart` | Boundary: the causal DAG persists intact across a full restart — time does not reset and the chain survives cold resume. |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P01c** | Eternity-clause P01c needs P06: substrate-ID persists *because* causality persists. P06 is the mechanism; P01c is the named result. |
| **P03** | Rollback is a P06 event, not an erasure. P03 + P06 = "evolve, but causality of evolution preserved." |
| **P04** | Each cycle is a P06 event. P04 + P06 = "iteration moves forward; the forward motion is the causal chain." |
| **P05** | Active-tier reachability (P05) uses P06's parent-edges. |
| **P10** | P10 compression operates within P06's recoverability requirement. P10.b invariant set ↔ P06 recoverability guarantee. |
| **P07** | Death is a P06 event: whole-death acceptance at the live CI gate with the BLAKE3 at-rest seal (F5) of the final tip. The substrate's causal chain ends with destruction; no further events. |

## §10. Illustrations

### §10.1 Honored

- **(Boot replay)**: Substrate restarts. Loads `manifest.cb` + DAG. Verifies Merkle chain from genesis to tip. All hashes match. Boots into `alive::normal`. ← §3.6 + §4.3 honored.

- **(Compression with witness)**: P10 compresses 30 absorption events into one `compression_event:absorption_aggregate_v1`. The event's content includes (compressed_node_hashes, aggregate_summary, pre_compression_dag_tip). Re-derivation by a verifier at the live CI gate is possible from these inputs. ← §3.4 honored.

### §10.2 Violated

- **(Retro-edit succeeded)**: A bug allows in-place modification of a past DAG node's content bytes. Merkle re-computation should catch on next cycle. If it doesn't (broken detector), C7 should retroactively fire on next drill. If neither catches, P06 is doctrinally broken AND its immune system is also broken. ← §5.1 + §8.1 violation.

- **(Parallel-branch forgery)**: Substrate accepts two competing DAG branches; chooses one quietly. ← §5.2 violation; C7 Merkle re-derivation should fail on the non-reconstructable tip (keyless: this is caught by chain re-derivation, not by an owner anchor co-sign).

### §10.3 Borderline

- **(Cold-tier inaccessibility)**: Cultivator asks for a state from 3 years ago. Cold-tier fetch path is gated at the live CI gate. Path returns `cold_tier_inaccessible`. Is this P06 violation? ← No — it's acknowledged exemption per L1/SCHEMA §2.3. The state IS still derivable; the substrate is just gating the fetch at the live human-in-the-loop, which is per-doctrine.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema. Marked as eternity-clause (`deposit_immutable: true`) per META §3.5 initial eternity-clause set. |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `kernel/schema/src/dag.rs` | DAG type + integrity. |
| `substrate/src/events/mod.rs` | Every state-mutating operation emits a DAG event (all node-type emitters). |
| `kernel/shared/src/canonical_bytes.rs` | F16 serializer for content addressing. |
| `substrate/src/integrity.rs` | Per-cycle Merkle/chain integrity check. |

## §13. Related Layer B chengyu

- **B014 因者今之父** — *the-past-is-the-present's-parent*: P06 deposit
- **B015 矢無逆飛** — *the-arrow-does-not-fly-backward*: arrow-of-time in image form

## §14. Related canonical dilemmas

- **D-0009 attempted branch forgery** — substrate-internal bug accepts parallel branch; does C7 Merkle re-derivation catch (keyless — the prior owner DAG-tip co-sign is retired)?
- **D-0015 dag hash collision handling** — astronomically unlikely BLAKE3 collision; how does the substrate respond?

---

**Doctrine commitment** (eternity-clause): the substrate is its causal chain. Amending this deposit is amending what "substrate" means — i.e., not amending Myco but replacing it.
