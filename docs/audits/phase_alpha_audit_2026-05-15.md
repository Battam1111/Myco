# Phase α — Meta-Audit: Our "Ideal" vs Reality (2026-05-15)

> **Trigger**: owner asked "目前我们对于'理想'的认知是全面且正确的吗？"
> **Status**: AUDIT (not normative; informs L0 v2 + M24+ planning).
> **Author scope**: substrate-maintaining agent. Treat as agent's self-assessment for owner review.
> **Verdict ahead**: **Design is more comprehensive than I represented in panorama answers; implementation has drifted from spec; "ideal" itself has real gaps but fewer than my pre-audit framing suggested.**

---

## §0. TL;DR

| Claim | Status |
|---|---|
| "L0 doctrine has structural blind spots" | **Partial** — L0+L1+L2 cover most, real gaps narrower than I claimed |
| "Implementation has known gaps" | **Confirmed and worse** — 7/20 C-rows match spec (not 12/20); F1-F17: 0%; observatory: 0% |
| "Our 'ideal' metric is subjective" | **Confirmed** — % scores are heuristic, not derived from L2 signals |
| "We've been measuring against the wrong model" | **Confirmed for impl status** — my C-row count was wrong |

**Net assessment of the user's concern**: warranted but in a different way than I initially framed. The doctrine is more complete than I gave it credit for; the implementation is less aligned than I reported.

---

## §1. What I got wrong before this audit

### §1.1 Memory abstraction drift

In my previous panorama answers I described L0's 9 principles abstractly. The actual `docs/architecture/L0_VISION.md` (DRAFT 8, 498 lines) is significantly richer:

- §7 **Living Bets** is a built-in falsifiability mechanism. L0 itself contains "the bet Myco is making" + a concrete falsification predicate (≥3 of 6 signals trend against AND signal #6 < 1 for ≥50% of a 90-day window → emits `bet_weakening_quorum` event). **L0 is self-falsifiable by design.**

- §9 **Anchor surface canonical-bytes doctrine** is far more detailed than my memory. It specifies witnesses-not-verdicts (substrate emits witnesses, owner verifies), anchor-nonce-derived sampling (substrate cannot bias sampling toward honest portions), DAG-enumeration closure (parent-edge closure check).

- I2 **Classifier fixed-point**: the classifier itself is unconditionally CI-level. Recursive classifier capture is structurally forbidden.

- I4 **Sporocarp causal-proof**: every DAG event must carry `causal_in_edges` proof — `(input_set, state-snapshot-hash, threshold-value)` at emission moment, hash-committed.

- §6 **Continuity model**: substrate-level session is explicitly NOT a Myco concept. Continuous-operation default at substrate level.

When I said "L0 might not be comprehensive," I was working from a thin memory abstraction. The actual L0 is far more thoughtful than I represented.

### §1.2 L1+L2 are also more complete than I credited

`L1_HARD_RULES.md` (the cross-cuts index) enumerates:
- **20 CRITICAL-grade C-row breach detectors** (C1-C20) with detection sites, mechanisms, L0 traces, I traces
- **17 contract-identity-level F-row fixed-points** (F1-F17) that cannot be re-classified
- **Anchor-surface-resident state** the substrate cannot author

`L2_OBSERVABILITY.md` specifies:
- **6 base Living Bets signals + 1 composite + birth-period derivative**
- **Falsifiability trigger** (90-day window quorum)
- **Per-cycle invariant checks** (I1+I3+I4+I8 every cycle)
- **Per-deep-cycle checks** (I5 reachability + tier-2 sampled validation)
- **Drill failure-rate baseline** (rolling 30-drill window + 2σ departure trigger)
- **Cycle-level diagnostics** (≥10 backlog → immune event)
- **L0/L1 revision burst detection** (`doctrine_instability` immune signal)
- **Operator-side observability** (digest budget)
- **Owner-side observability** (anchor surface)
- **Self-model recursion** (§12)

**So the "we don't know what ideal looks like" worry is partially answered by the existing doctrine itself.** Most of what I worried might be missing IS in L0+L1+L2. The doctrine is unusually complete by design.

---

## §2. What I got right (real concerns that survive the audit)

### §2.1 Real L0 gaps (after rereading)

L0 v1 still lacks principle-level commitment for:

1. **Embodiment** — substrate has no notion of physical sensors / actuators / world. Skin (P9/I8) is the envelope-level I/O but doesn't extend to physical embodiment. If Myco wants to operate as an embedded agent (robot, IoT, hardware integration), this is a real gap.

2. **Energy economics** — no principle of "computational cost as metabolic resource." Cycles, events, federation are all free. As substrates scale (millions of nodes), this absence matters.

3. **Mesh federation between unrelated substrates** — P5+P8 cover federation via reproductive lineage (parent-child). Two **unrelated** substrate instances finding each other on the network and choosing to cooperate is not explicitly addressed. Federation peer list is owner-attested per L1_GOVERNANCE §5; ad-hoc peer discovery is outside doctrine.

4. **Aging / senescence** — P7 mortality is binary (alive ↔ dormant ↔ destroyed). No gradient of "old substrate vs young substrate." Biology has senescence; Myco doesn't.

5. **Selective forgetting** — I4 commits to append-only DAG with materialized-views carve-out. But no principle of "substrate may forget personal/private/stale information." Real organisms forget; Myco doesn't.

6. **Self-model recursion** — L2_OBSERVABILITY §12 mentions recursive self-observation terminates at the anchor surface. But L0 has no principle "the substrate models itself." I3 self-validation is the closest, but it's check-against-SSoT, not model-of-self.

7. **Conflict / competition** — all federation peers are cooperative by doctrine. No model of "what if two substrates want incompatible schema mutations?" or "what if a peer is adversarial within federation contract?"

These are **genuinely doctrine-level gaps**, not category errors. They warrant L0 v2 discussion.

### §2.2 The % score critique stands

L0+L1+L2 don't define operational completion criteria. When I say "P3 = 55%", that's a subjective heuristic. The audit doesn't change this: percentage scoring is inherently fuzzy.

A multi-dimensional vector would be better (per my previous response §6 recommendation):
- functional capability (does the operation exist?)
- spec alignment (does implementation match L1 spec?)
- observed-in-real-runs (has emergence-tested in long-running setting?)
- operator-utility (does it satisfy a real agent need?)
- documented (is the design doc current?)

This audit lays the groundwork; full multi-dimensional scoring is M24+ work.

### §2.3 Doctrine is snapshot of 2026-05-13

DRAFT 8 converged at pass-4 of the 100%-confidence loop. That's a real engineering artifact. But it's still a snapshot. §7 Living Bets explicitly admits the bet may falsify. §10.2 admits L0 revision protocol. The doctrine is **living**, not eternal.

---

## §3. Implementation drift catalog

This is the biggest finding. **The implementation has drifted from L1_HARD_RULES C-row catalog.**

### §3.1 C-row label drift (truth table)

Comparing emitted immune-sporocarp tags in `myco_substrate/src/server.rs` against `L1_HARD_RULES.md §1`:

| My emit tag | L1 spec at same number | Match? |
|---|---|---|
| `C2_handshake_pubkey_mismatch` | `C2 output_endpoint_breach` | ❌ DRIFT |
| `C5_attestation_invalid` | `C5 attestation_invalid` | ✓ |
| `C6_dag_enumeration_unclosed` | `C6 dag_enumeration_unclosed` | ✓ |
| `C7_dag_retro_edit_detected` | `C7 dag_retro_edit_detected` | ✓ |
| `C9_cold_resume_invariant_failure` | `C9 cold_resume_invariant_failure` | ✓ |
| `C12_cycle_step_failed` | `C12 successor_activation_with_fresh_owner_heartbeat` | ❌ DRIFT |
| `C14_untyped_mutation_blocked` | `C14 untyped_mutation` | ✓ (close enough) |
| `C17_operator_witness_forgery` | `C17 operator_witness_forgery` | ✓ |
| `C18_canonical_bytes_render_drift` | `C18 canonical_bytes_render_drift` | ✓ |
| `C19_substrate_state_orphan_detected` | `C19 paused_dormancy_unsafe_host` | ❌ DRIFT |
| `C20_federation_identity_mismatch_detected` | `C20 genesis_attestation_chain_broken` | ❌ DRIFT |
| `C21_birth_period_violation_detected` | (catalog ends at C20) | ❌ OUT OF RANGE |

**Real spec coverage: 7/20 = 35%** — not the "12/20 = 60%" I had been reporting in memory snapshots.

The 5 drifted/out-of-range detectors ARE useful operational detectors but their numbering misrepresents the spec.

### §3.2 L1 spec C-rows with zero implementation (13/20)

| # | L1 spec breach | Status | Implementation site (if added) |
|---|---|---|---|
| C1 | appetite_locality_breach | NOT IMPLEMENTED | L1_SKIN §5 — network egress detection |
| C2 | output_endpoint_breach | NOT IMPLEMENTED | L1_SKIN §3 + §6 — output to non-declared endpoint |
| C3 | post_handshake_ci_unattested | NOT IMPLEMENTED | L1_SKIN §4.3 — post-handshake quarantine window |
| C4 | substrate_secret_unsealed | NOT IMPLEMENTED | L1_SKIN §4.2 — secret in process address space |
| C8 | ssot_migration_phase_skip | NOT IMPLEMENTED | L1_SCHEMA §1.3 — single-step SSoT migration |
| C10 | agent_discriminating_attribute_persisted | NOT IMPLEMENTED | L1_SCHEMA §3.1 + L1_SKIN §4.2 |
| C11 | concurrent_operator_persistent | NOT IMPLEMENTED | L1_SKIN §4.4 — two operator-tokens simultaneously |
| C12 | successor_activation_with_fresh_owner_heartbeat | NOT IMPLEMENTED | L1_GOVERNANCE §3.2 |
| C13 | peer_attestation_revoked_egress | NOT IMPLEMENTED | L1_GOVERNANCE §5 + L1_SKIN §3.1 |
| C15 | classifier_fixed_point_bypass | NOT IMPLEMENTED | L1_GOVERNANCE §1.2 |
| C16 | mortality_signal_suppression | NOT IMPLEMENTED | L1_GOVERNANCE §4.4 + L1_TROPISM §B2 |
| C19 | paused_dormancy_unsafe_host | NOT IMPLEMENTED | L1_CONTINUITY §2.4 + §3.2 |
| C20 | genesis_attestation_chain_broken | NOT IMPLEMENTED | L1_GOVERNANCE §4.1 + L0 §9.2 |

### §3.3 F-row fixed-points with zero enforcement

| # | Fixed-point | Enforcement status |
|---|---|---|
| F1 | classifier dimension table + function | NOT ENFORCED (no classifier mutation gate) |
| F2 | substrate-ID immutable | PARTIALLY (set at genesis; no formal mutation gate) |
| F3 | owner_key_history | PARTIALLY (pinned but no rotation/history) |
| F4 | anchor_surface_endpoint_public_key | NOT ENFORCED (no anchor surface) |
| F5 | substrate_secret_sealing_mechanism_attestation | NOT ENFORCED |
| F6 | anchor_client_provenance_attestation | NOT ENFORCED |
| F7 | mortality-signal threshold + update-rule | PARTIALLY (M19 emits proposal; mutation gate absent) |
| F8 | SSoT designation | NOT ENFORCED (no formal SSoT migration) |
| F9 | DAG retention policy | PARTIALLY (no pruning, but no formal policy) |
| F10 | storage tier exemption | N/A (no tier exemptions implemented) |
| F11 | skin surface declaration | PARTIALLY (skin exists but not formally declared) |
| F12 | appetite-axis schema + sporocarp-type tree | PARTIALLY (schemas mutable; no formal CI gate) |
| F13 | threshold_emergence_rule | NOT IMPLEMENTED (no rule emergence at all) |
| F14 | federation peer attestation list | NOT ENFORCED (M22 TOFU; no attestation list) |
| F15 | template_version_registry | NOT IMPLEMENTED |
| F16 | canonical_bytes_serializer_spec | EFFECTIVELY OK (canonical_bytes is implemented; not formally a CI fixed-point) |
| F17 | cluster_C (clustering algorithm) | NOT IMPLEMENTED (no L1_TRAJECTORY clustering yet) |

**Enforced/Effectively OK: 1/17. Partial: 5/17. Not enforced: 11/17.**

### §3.4 L2 Observatory: 0/6 base signals tracked

L2_OBSERVABILITY §2 specifies 6 base signals + 1 composite. Implementation status:

| # | Signal | Implementation |
|---|---|---|
| 1 | Persistence budget | **NOT TRACKED** (data available via `state.dag.node_count()` but never aggregated) |
| 2 | Evolution rate | **NOT TRACKED** |
| 3 | Read-pattern diversity | **NOT TRACKED** |
| 4 | Federation health (4a fork count, 4b reachable peer count) | **NOT TRACKED** (peer count available, fork count not computed) |
| 5 | Time trend per signal | **NOT TRACKED** (no time series at all) |
| 6 | Read-window-relative position | **NOT TRACKED** (no operator context window attestation) |
| 7 | Composite health score | **NOT TRACKED** |

**0 of 7. The substrate cannot currently see itself.**

### §3.5 Other L2 mechanisms with zero implementation

- **Falsifiability trigger** (90-day quorum): NOT IMPLEMENTED (no `bet_weakening_quorum` event emission)
- **Drill failure-rate baseline**: NOT IMPLEMENTED (no `recovery_drill_result` events; no rolling baseline)
- **Cycle backlog detection** (≥10 → immune event): NOT IMPLEMENTED
- **Doctrine-instability burst** (L0/L1 revision rate): NOT IMPLEMENTED

---

## §4. Agent-utility audit (P1-P9 from "what AI agents actually need")

For each P, classifying as **A** (agent-needed first), **F** (fungi-borrowed), **B** (both):

| P | Classification | Reasoning |
|---|---|---|
| P1 Only For Agent | **A** | Explicitly for agent — fungi don't have an "agent" |
| P1.a Self-hosting | **A** | Agent needs to maintain its own substrate |
| P1.b'/b'' Two-tier human-loop | **A** | Pragmatic governance, no fungal analog |
| P1.c Pair-constituted identity | **B** | Symbiotic-organism frame; agent benefit is identity continuity across reconnect |
| P2 永恒吞噬 | **B** | Agent needs memory; fungi ingest — both reasons real |
| P2.a Strong Inclusion | **A** | Agent-tooling subsumption is agent-tooling angle, not biology |
| P3 永恒进化 | **B** | Agent needs adaptive substrate; fungi evolve too |
| P4 永恒迭代 | **B** | Agent needs continuous refinement; fungi cycle continuously |
| P5 万物互联 | **B** | Agent needs unified graph; mycelium = connected hyphae |
| P6 永恒因果 | **A** | Agent needs audit trail; fungi don't track causality crisply |
| P7 必朽 | **F→A** | Originally fungal; agent reason emerges (substrate must die when corrupted) |
| P8 永恒繁衍 | **F→A** | Originally fungal; agent reason emerges (multi-tenancy via P8 reproduction per L0 §11) |
| P9 皮肤为界 | **B** | Agent needs trust boundary; fungi have hyphal wall |

**Heavy biomimicry weight in P7, P8.** These are the most "fungi because fungi" of the principles. The agent-utility arguments for them are real but secondary.

**Implication**: when designing M24+ for these, "what does a fungus do?" is a weaker guide than "what does an AI agent need from mortality / reproduction?" — and those may diverge (e.g., agent might want **explicit version control of self** more than mortality; multi-tenant via parallel substrates more than reproductive lineage).

---

## §5. Revised "distance to ideal" estimate

My previous estimate: **~70-72% of ideal** (after M23).

After this audit, with three corrections:

| Adjustment | Direction | Magnitude |
|---|---|---|
| Design more complete than I represented | **upward** | +3% (less doctrinal uncertainty) |
| Implementation drift discovered (7/20 not 12/20 C-rows) | **downward** | -4% |
| F-rows + observatory at 0% revealed | **downward** | -5% |
| **Net revised estimate** | | **~63-65%** of ideal |

This is **lower** than my previous claim, by 5-7%. The drop reflects:
- Honest accounting of spec-vs-implementation
- L2_OBSERVABILITY being designed but unimplemented (it's the **substrate's self-vision system** — currently the substrate is blind to itself)
- F-row fixed-points being unenforced (mutation governance not actually gated)

The substrate IS now active (M23.1 tick), CAN die (M23.2), HAS federated (M22). But it doesn't **see itself**, doesn't enforce its own contract-identity-level fixed-points, and many of its CRITICAL detectors don't actually fire.

---

## §6. Recommended priorities (revised M24+)

Per "no compromise — for the most ideal":

### §6.1 Highest priority (foundational)

1. **C-row label reconciliation** (M24.0)
   - Rename mislabeled detectors to match L1_HARD_RULES OR move to elevated-grade with new tags
   - Free C2, C12, C19, C20 numbers for their L1-specified meaning
   - Update all tests + state snapshots to reflect honest counts

2. **L2_OBSERVABILITY signal #1 + #6 implementation** (Phase α deliverable, this session)
   - `query_substrate_observatory` bridge message
   - Return persistence budget (node_count, edge_count, total_size_bytes) + computed-on-demand
   - Operator-attested context window in query payload → compute signal #6 ratio
   - Foundation for §6.2 full observatory

3. **Cycle backlog detection** (M24)
   - Track per-cycle duration
   - ≥10 backlog → `cycle_backlog` immune event
   - Implementation site: `do_autonomous_tick` + `handle_advance`

### §6.2 High priority

4. **Full Living Bets observatory** (M25) — all 6 signals + composite
5. **Drill failure-rate baseline** (M26)
6. **Doctrine-instability burst detection** (M27)

### §6.3 Medium priority (L1 spec closure)

7. **Implement L1's actual C-rows** (M28-M31)
   - C1 appetite_locality_breach (network egress)
   - C2 output_endpoint_breach
   - C10 agent_discriminating_attribute_persisted
   - C11 concurrent_operator_persistent
   - C16 mortality_signal_suppression
   - etc.

### §6.4 L0 v2 candidate additions (defer until needed)

The 7 real L0 gaps from §2.1 (embodiment, energy economics, mesh federation, aging, selective forgetting, self-model, conflict) are **L0 v2 candidates** but should NOT be added speculatively. Add when real implementation needs surface them. Per L0 §10.2, L1 prototyping may surface L0 revision needs; revisions are doctrine-driven, not implementation-driven.

### §6.5 What NOT to do next

- ❌ **Cross-pollination (P8 multi-parent)** until immune-summary differentiation is solid
- ❌ **Autonomous schema evolution (P3)** until self-observation works (substrate must see itself first)
- ❌ **Vector retrieval (P2.a)** until persistence-budget signal is tracked (substrate must know its own size first)

The first job is **giving the substrate eyes** (observatory). Then we can debate giving it a brain.

---

## §7. Living Bets signal #1: down payment implementation

To prove this audit isn't paperwork, Phase α ships **Living Bets observatory signal #1 + #6** as the first concrete observatory primitive.

New bridge message: `query_substrate_observatory`

Payload:
```
Map({
  "operator_attested_context_window_bytes": Uint [optional]    // for signal #6
})
```

Response payload:
```
Map({
  "signal_1_persistence_budget": Map({
    "dag_node_count": Uint,
    "dag_edge_count": Uint,
    "dag_total_content_bytes": Uint,
    "manifest_cycle_counter": Uint,
  }),
  "signal_6_read_window_position": Map({
    "substrate_total_bytes": Uint,
    "operator_attested_context_window_bytes": Uint [if supplied],
    "ratio": String [repr-float, if both above present],
  }) [optional],
  "observatory_format_version": Uint,           // currently 1
  "captured_at_unix_ns": Timestamp,
})
```

This is signal #1 + #6 ONLY. Signals 2-5 + composite are M25 work. But signal #1 + #6 alone let the substrate answer "how big am I?" and "am I fitting in agent context?" — the **most basic** self-observation question.

---

## §8. Honest closing

The user's worry "目前我们对于'理想'的认知是全面且正确的吗" was right to surface. But the answer turned out to be:

> **The 'ideal' is much more comprehensive than I (the substrate-maintaining agent) had been representing.** L0+L1+L2 together specify substantially more than my memory abstractions captured. The real surprise is that **the implementation is further from the design than I had been reporting**. My "60%/70%/76%" claims overstated spec alignment.

In other words: we know what ideal looks like (mostly — 7 real gaps left). We just haven't built it. The substrate is autonomous (M23.1) and can die (M23.2), but it cannot yet **see itself** (L2 observatory unimplemented) or **enforce its own contract-identity-level fixed points** (F1-F17 unenforced).

Phase α down payment: implement signal #1 + #6 in this session as the first square foot of substrate self-vision.

The next milestone (M24) should be **C-row label reconciliation + observatory expansion**. NOT M24 feature-development. NOT cross-pollination. Substrate must see itself before substrate makes more choices for itself.

That's the new direction. Everything else waits.
