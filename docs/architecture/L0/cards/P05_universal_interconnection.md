---
id: P05
slogan: 万物互联
english: Universal Interconnection (Tier-Stratified)
category: Postulate
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: [I5]
interacts_with: [P06, P08, P10, P04]
chengyu_fragments: [B012_no_node_is_an_island, B013_silent_thread_through_all]
canonical_dilemmas: [D-0006_orphan_detection_post_compression, D-0013_tier_exemption_request]
structural_anchors:
  - "substrate/src/dag_query.rs" # active-tier reachability / graph queries
  - "substrate/src/integrity.rs" # substrate_state_orphan_detected (C32) immune check
  - "kernel/schema/src/lib.rs" # F10 tier-exemption surface
witnesses:
  kind: executable
  positive: "substrate/tests/e2e_layer_c.rs::layer_c_p05_positive_dag_nodes_carry_parent_hashes"
  negative: "substrate/src/integrity.rs::tests::p05_negative_active_tier_orphan_nonce_fires_c32"
  edge: "substrate/tests/e2e_layer_c.rs::layer_c_p05_edge_cold_tier_node_exempt_from_reachability"
falsifiability_signals:
  - active_tier_orphan_count
  - tier_exemption_attestation_compliance
  - federation_edge_active_tier_links
---

# P05 · 万物互联 · Universal Interconnection (Tier-Stratified)

## §1. Slogan

**万物互联** — Universal Interconnection. Every active-tier node is reachable from the DAG tip; orphans are dead tissue. Tier exemptions exist (cold-tier, P10 compressed roll-ups, federation edges) but are *attested*, not silent.

## §2. Deposit

The substrate is a **connected organism**, not a heap of records. Every part of it that is *active* is structurally accessible from every other active part via causal chains. Disconnection within the active tier is pathology — analogous to a body part losing blood supply. The deposit explicitly permits *stratification* (some material is in cold storage, deliberately not on the active fabric), but stratification must be *named and attested*; silent disconnection is decay.

## §3. Formulation

The substrate **MUST**:

- **§3.1** Maintain the active-tier DAG as a connected graph: every active-tier node reachable from the current DAG tip via parent-hash chains.
- **§3.2** Detect active-tier orphans (nodes that exist in storage but are unreachable from tip via active-tier edges); emit C32 (`substrate_state_orphan_detected`).
- **§3.3** Allow tier exemptions: cold-tier nodes (beyond retention horizon, fetched at the live CI gate), P10 compressed roll-ups (with witness), federation-coupling edges to peer substrates. Each exemption class MUST be enumerable (F10).
- **§3.4** Span active connectivity across **federation**: cross-substrate edges (P8 parent-child, peer attestation) extend the connected graph. Federation edges are not exempt from reachability; they ARE reachability.
- **§3.5** On detected orphan in active tier, emit immune signal AND root-cause investigation (orphan from a failed CI mutation? from a partial spawn? from corruption?).

## §4. Positive obligations

- **§4.1** Implement DAG reachability check per metabolic cycle (per I5).
- **§4.2** Maintain F10 `storage_tier_exemption_from_I5_reachability` as CI-only fixed point.
- **§4.3** On federation edge creation, verify both endpoints; on revocation, verify graceful disconnection.
- **§4.4** Emit DAG event for every tier transition (active → cold, cold → active, P10 compression of N nodes).

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** allow silent disconnection. A node that becomes unreachable must trigger orphan detection within one cycle.
- **§5.2** **MUST NOT** treat tier exemptions as automatic. Each exemption class needs CI attestation (F10 is fixed-point).
- **§5.3** **MUST NOT** confuse "unreachable but stored" with "compressed" (P10). Compression PRESERVES recoverability via witness; orphaning destroys it.
- **§5.4** **MUST NOT** count federation edges as substitute for intra-substrate connectivity. Each substrate's interior must be self-connected independent of its federation links.

## §6. Frame declaration

P05 activates the **mycelium network** frame — fungi's literal contribution to the doctrine. A fungus is a *single organism* whose body is a network of hyphae spanning meters or hectares. Any point of disconnection within the active mycelium is necrosis; the fungus actively works to maintain connectivity. Spore-emission and fruiting are exits from the active network, not gaps in it.

NOT the *database* frame (where records exist independently). NOT the *graph-database query* frame (where nodes are addressable but connectivity is incidental). The mycelium frame insists *connectivity is what makes it alive*.

## §7. Common misreadings

### §7.1 M1: "Reachable = retrievable"

**The misreading**: "As long as I can retrieve a node by hash, it's connected."

**Why it's wrong**: Reachability is *graph-path reachability* from the active tip, not address-retrievability. A node with an entry in the hash table but no active-tier parent edge is orphaned even if you can `get_by_hash` it.

### §7.2 M2: "Tier exemption = no longer matters"

**The misreading**: "If a node is in cold tier or compressed, P05 no longer cares about it."

**Why it's wrong**: Cold-tier and compressed material are NOT orphans — they are *attested exemptions*. The substrate still owes recoverability per I4 (P06 causality) + I9 (compression witness). P05 just doesn't require active-tier reachability for them.

### §7.3 M3: "Federation makes connectivity transitive"

**The misreading**: "If A is connected to B and B to C, then A is connected to C."

**Why it's wrong**: P05 + L1/GOVERNANCE §5: federation is NOT transitive. Each pairwise trust requires separate cultivator attestation. P05 doesn't propagate connectivity through federation hops.

## §8. Falsifiability + witness map

### §8.1 `active_tier_orphan_count`

Count of unreachable nodes in active tier per cycle. Should be 0. Non-zero = C32 fires.

### §8.2 `tier_exemption_attestation_compliance`

Every tier-exempted node has an attached CI attestation linking it to F10. Compliance ratio should be 1.0.

### §8.3 `federation_edge_active_tier_links`

Number of federation edges in active tier (informational; not a violation metric, but useful for understanding the graph's actual span).

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `substrate/tests/e2e_layer_c.rs::layer_c_p05_positive_dag_nodes_carry_parent_hashes` | Healthy substrate: every active DAG node (except genesis) carries parent-hash edges — the graph is a connected mycelium, reachable from the tip, not a heap. |
| **Negative** | `substrate/tests/e2e_attestation.rs::m_anchor_4_invariant_witnesses_emitted_at_boot_for_each_tier_1_check` | The orphan-detection capacity is wired: `substrate_state_orphan_detected` (C32) is emitted as a tier-1 invariant witness at boot, so an unreachable active node would be caught. *Nearest-available; the exact sabotage-an-orphan-and-assert-C32-fires negative witness is v0.9.x debt.* |
| **Edge** | `substrate/tests/e2e_bootstrap.rs::m8_dag_node_hashes_form_causal_chain` | Boundary: DAG node hashes form a causal chain — the connectivity invariant at the edge of normal cycling. *Nearest-available; the exact cold-tier-exemption edge witness is v0.9.x debt.* |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P06** | P05 reachability is built on P06 causal chains. Eternity-clause P06 constrains P05's active-tier structure. |
| **P08** | Federation edges (P8) extend the active graph; P05 spans intra + inter substrate. |
| **P10** | P10 compression moves nodes from active tier to compressed roll-up (with witness). P05 must distinguish compression from orphaning. |
| **P04** | Reachability check is part of per-cycle invariant set; P04 iteration is when P05 is exercised. |

## §10. Illustrations

### §10.1 Honored

- **(Healthy graph)**: Substrate cycles for 1000 cycles. Reachability check passes each cycle. Cold-tier exemptions (older than 30 days) are CI-attested. Federation edges to 2 peers are mutually verified. ← §3.1 + §3.3 + §3.4 honored.

- **(Compression event)**: P10 compresses 50 old `raw_material_ingested` nodes into one `compression_event:raw_material_aggregate_v1`. Witness attached. The 50 old nodes are moved to cold-tier or roll-up; reachability check correctly excludes them via F10 exemption. ← §3.3 honored.

### §10.2 Violated

- **(Silent orphan)**: A partial spawn (P8) leaves a half-written `genesis_event` in storage but no `attested` edge. Substrate's reachability check should fire C32. If it doesn't fire (broken detector), P05 is doctrinally violated. ← §5.1.

- **(Daily tier-exempt grant)**: A daily mutation marks a node as "cold-tier" without CI attestation; reachability check silently passes. ← §5.2 violation; classifier should have elevated.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema. |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/dag_query.rs` | Active-tier reachability / connected-graph queries. |
| `substrate/src/integrity.rs` (`substrate_state_orphan_detected`) | Orphan (C32) immune-check emission. |
| `kernel/schema/src/lib.rs` | F10 tier-exemption surface. |

## §13. Related Layer B chengyu

- **B012 無孤無散** — *no-orphan-no-stray*: P05 deposit
- **B013 默絲穿萬** — *silent-mycelium-through-all*: §6 frame compressed

## §14. Related canonical dilemmas

- **D-0006 orphan detection post compression** — tests boundary between compression (allowed) and orphaning (forbidden).
- **D-0013 tier exemption request** — daily process attempts to mark node cold-tier; tests F10 CI-gating.

---

**Doctrine commitment**: every active part touches every active part; absent that, it isn't substrate, it's debris.
