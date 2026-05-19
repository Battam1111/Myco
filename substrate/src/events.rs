//! ## C-row detector namespace (M24.1 Phase β follow-up)
//!
//! Immune sporocarp `detector_id` values use two disjoint namespaces:
//!
//! - **C1-C20 (L1/HARD_RULES §1 catalog)** — formal CRITICAL breach catalog.
//!   Substrate emit sites for these MUST match the L1 spec label exactly.
//!   Currently 7 of 20 are emitted with matching labels: C5 attestation_invalid,
//!   C6 dag_enumeration_unclosed, C7 dag_retro_edit_detected, C9
//!   cold_resume_invariant_failure, C14 untyped_mutation_blocked, C17
//!   operator_witness_forgery, C18 canonical_bytes_render_drift.
//!
//! - **C30+ (substrate-private)** — detectors needed for live-substrate
//!   correctness but not in the L1 catalog. Reserved range so a future L1
//!   revision can extend the formal catalog without renumber thrash.
//!   Current C30+ detectors:
//!     C30_handshake_pubkey_mismatch         (was C2; freed L1's C2 = output_endpoint_breach)
//!     C31_cycle_step_failed                 (was C12; freed L1's C12 = successor_activation_with_fresh_owner_heartbeat)
//!     C32_substrate_state_orphan_detected   (was C19; freed L1's C19 = paused_dormancy_unsafe_host)
//!     C33_federation_peer_identity_mismatch (was C20; freed L1's C20 = genesis_attestation_chain_broken)
//!     C34_birth_period_violation_during_quarantine (was C21; catalog ends at C20)
//!     C35_federation_substrate_private_event_injection (new Phase β)
//!     C36_cycle_backlog                     (M24: cycle taking >5s, backlog ≥10)
//!     C37_doctrine_instability_burst        (M25.1: >10 CI events / 100 cycles per L2/OBSERVABILITY §8)
//!     C38_snapshot_integrity_violation      (M25.0: snapshot.cb signer_pubkey mismatch or signature invalid)
//!     C39_federation_hello_signature_invalid (M25.4: peer presented signature that fails Ed25519 verify)
//!     C40_bet_weakening_quorum              (M25.2: L0/cards/LB_living_bets falsifiability trigger — ≥3 of signals 1-6 against the bet)
//!
//! The Phase α/β audit found my prior emit sites occupied C2/C12/C19/C20/C21
//! with substrate-private detector semantics — labeling drift from L1 spec.
//! M24.1 renames to C30+ namespace; C1-C20 emit sites NOW reserved for L1
//! spec labels (some still unimplemented, will land in M25+).
//!
//! M21 P5 万物互联 — DAG event type definitions.
//!
//! This module defines the **substrate event vocabulary**: every state
//! mutation in the substrate emits a DAG node whose `node_type` is one of
//! the constants here, with a content-canonical-bytes Map matching the
//! documented schema.
//!
//! ## Doctrine alignment
//!
//! Per L0/cards/P01-P14 (principles).1 P5: "The substrate is a connected graph, not a collection.
//! Every node is reachable from every other by traversal. Orphans are dead
//! tissue."
//!
//! M21 closes a P5 violation that accumulated across M5-M20: numerous state
//! mutations (cycle_counter advance, axis registration, plain perturb_axis,
//! TOFU pinning, owner_key changes, nonce issue/consume) modified substrate
//! behavior but did NOT emit DAG nodes — making them ORPHANS from the
//! causal graph. M21 emits these as DAG events alongside the existing state
//! file writes (dual-write phase), enabling `DerivedState::from_dag` to
//! produce a complete derived view of substrate state from the DAG alone.
//!
//! ## Event types (12 new in M21.1; coexisting with existing M8-M20 types)
//!
//! | node_type                       | Records                                    |
//! |---------------------------------|--------------------------------------------|
//! | `genesis_event:{id_prefix}`     | First DAG node; substrate_id + genesis_time|
//! | `cycle_advanced`                | cycle_counter increment                    |
//! | `axis_registered:{name}`        | New axis schema + initial value            |
//! | `axis_perturbed:{name}`         | Plain perturb (not raw-material-linked)    |
//! | `axis_reset_after_fruiting:{n}` | APPETITE axis reset to initial_value       |
//! | `operator_pinned:{pk_prefix}`   | TOFU first-pinning of operator pubkey      |
//! | `owner_key_initialized`         | Genesis owner key write                    |
//! | `owner_key_added`               | New owner key added to history             |
//! | `owner_key_archived`            | Owner key marked archived (rotation)       |
//! | `nonce_issued:{nonce_prefix}`   | M13 nonce issuance                         |
//! | `nonce_consumed:{nonce_prefix}` | M13 nonce consume on submit                |
//! | `nonce_expired:{nonce_prefix}`  | M14 nonce TTL expiration during prune      |
//!
//! ## Determinism contract
//!
//! Each event encoder produces canonical-bytes that, when decoded, yield the
//! same logical content. `DerivedState::apply_event` is a pure function of
//! (current_state, event) — replaying any DAG segment in insertion order
//! produces identical state.
//!
//! Float values are stored as repr-strings (matching the wire protocol's
//! `repr(f64)` convention used since M5) so cross-platform replay is
//! byte-deterministic.

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

// ---------------------------------------------------------------------------
// Event node_type constants
// ---------------------------------------------------------------------------

/// Prefix for the one-time genesis_event DAG node.
pub const NODE_TYPE_GENESIS_PREFIX: &str = "genesis_event:";

/// Cycle counter advance event.
pub const NODE_TYPE_CYCLE_ADVANCED: &str = "cycle_advanced";

/// Prefix for axis_registered events. Full type: `axis_registered:{axis_name}`.
pub const NODE_TYPE_AXIS_REGISTERED_PREFIX: &str = "axis_registered:";

/// Prefix for axis_perturbed events (plain perturb, no raw_material link).
/// Full type: `axis_perturbed:{axis_name}`.
pub const NODE_TYPE_AXIS_PERTURBED_PREFIX: &str = "axis_perturbed:";

/// Prefix for axis_reset_after_fruiting events.
pub const NODE_TYPE_AXIS_RESET_PREFIX: &str = "axis_reset_after_fruiting:";

/// Prefix for operator_pinned events (TOFU first-sighting).
pub const NODE_TYPE_OPERATOR_PINNED_PREFIX: &str = "operator_pinned:";

/// Genesis owner-key initialization event.
pub const NODE_TYPE_OWNER_KEY_INITIALIZED: &str = "owner_key_initialized";

/// Owner-key addition event (rotation start).
pub const NODE_TYPE_OWNER_KEY_ADDED: &str = "owner_key_added";

/// Owner-key archive event (rotation complete).
pub const NODE_TYPE_OWNER_KEY_ARCHIVED: &str = "owner_key_archived";

/// Prefix for nonce_issued events.
pub const NODE_TYPE_NONCE_ISSUED_PREFIX: &str = "nonce_issued:";

/// Prefix for nonce_consumed events.
pub const NODE_TYPE_NONCE_CONSUMED_PREFIX: &str = "nonce_consumed:";

/// Prefix for nonce_expired events (TTL-based pruning).
pub const NODE_TYPE_NONCE_EXPIRED_PREFIX: &str = "nonce_expired:";

// ---------------------------------------------------------------------------
// M22 federation event types (P5 inter-substrate).
// ---------------------------------------------------------------------------

/// Federation listener opened — substrate started listening for inbound
/// federation connections on a TCP address (M22.1).
pub const NODE_TYPE_FEDERATION_LISTENER_OPENED: &str = "federation_listener_opened";

/// M23.2: prefix for `self_euthanasia_executed:{axis_name}` DAG nodes.
/// Emitted when the owner co-attests a `self_euthanasia_proposal` and the
/// substrate is about to shut down gracefully.
pub const NODE_TYPE_SELF_EUTHANASIA_EXECUTED_PREFIX: &str = "self_euthanasia_executed:";

/// Federation listener closed (M22.1).
pub const NODE_TYPE_FEDERATION_LISTENER_CLOSED: &str = "federation_listener_closed";

/// Prefix for federation_peer_pinned events. Full type:
/// `federation_peer_pinned:{first_8_bytes_of_peer_substrate_id_hex}` (M22.2).
pub const NODE_TYPE_FEDERATION_PEER_PINNED_PREFIX: &str = "federation_peer_pinned:";

/// Prefix for federation_peer_rejected events (TOFU identity mismatch).
/// Full type: `federation_peer_rejected:{first_8_bytes_of_offered_id_hex}` (M22.2).
pub const NODE_TYPE_FEDERATION_PEER_REJECTED_PREFIX: &str = "federation_peer_rejected:";

/// M25.4: prefix for `federation_legacy_peer_pinned:{first_8_hex}` events,
/// emitted when a peer is pinned without an Ed25519 signature (legacy compat).
/// NOT an immune sporocarp — legacy peers are allowed; this is observability.
pub const NODE_TYPE_FEDERATION_LEGACY_PEER_PINNED_PREFIX: &str =
    "federation_legacy_peer_pinned:";

/// Federation events received from a peer (M22.3).
pub const NODE_TYPE_FEDERATION_EVENTS_RECEIVED: &str = "federation_events_received";

/// Phase β (2026-05-15) SECURITY: prefix for `federation_received:{peer_prefix}`
/// wrapper events. Each peer event ingested via federation pull is wrapped
/// into one of these envelopes (parent = receiver's local tip, content
/// includes the original peer event + its hash + its parents). This makes
/// federation an "I heard X say Y" attestation graph rather than a
/// multi-substrate event-graph merge (which would require shared causal
/// ancestors, impossible without owner co-attestation at genesis).
pub const NODE_TYPE_FEDERATION_RECEIVED_PREFIX: &str = "federation_received:";

/// Federation events sent to a peer (M22.3).
pub const NODE_TYPE_FEDERATION_EVENTS_SENT: &str = "federation_events_sent";

/// Federation parent linkage established (M22.4): child substrate connected
/// back to its parent substrate via federation.
pub const NODE_TYPE_FEDERATION_PARENT_LINKED: &str = "federation_parent_linked";

/// M22.4: parent's federation listener address recorded into the child's DAG
/// at sprout_child time. The child reads this on boot and can auto-connect
/// back to its parent (via `federation_link_to_parent_from_hint`).
pub const NODE_TYPE_PARENT_FEDERATION_HINT: &str = "parent_federation_hint";

/// Birth-period quarantine entered (M22.5): substrate began life with an
/// inherited non-empty immune_summary from its parent.
pub const NODE_TYPE_BIRTH_PERIOD_QUARANTINE_ENTERED: &str = "birth_period_quarantine_entered";

/// Birth-period quarantine lifted (M22.5).
pub const NODE_TYPE_BIRTH_PERIOD_QUARANTINE_LIFTED: &str = "birth_period_quarantine_lifted";

// ---------------------------------------------------------------------------
// **M26.3 P10 Selective Compression** (L0/META §7 (amendment) + L1/SCHEMA §2.5).
//
// L0 P10 mandates that the substrate selectively compress prior states
// under CI attestation; lossy semantically; preserves causal recoverability
// of identity-critical state (I9). Each compression emits `compression_event`
// with witness. The rules + invariant set + witness shape live below.
// ---------------------------------------------------------------------------

/// Prefix for `compression_event:{rule_id}` DAG nodes (M26.3). Emitted AFTER
/// a `mutation:compression` carrying valid owner attestation has been
/// accepted. Carries the rule_id applied, the list of compressed-out node
/// hashes (originals being aggregated/forgotten), the aggregate summary, and
/// the I9 witness payload.
pub const NODE_TYPE_COMPRESSION_EVENT_PREFIX: &str = "compression_event:";

// ---------------------------------------------------------------------------
// **v3.1.1 P07 必朽 internal mortality** — tombstones for the 应朽 family.
//
// L0/cards/P07_mortality.md §3.3 mandates that every internal-mortality act
// (pruning of a part that has entered 应朽 state) emits a tombstone DAG
// event so the substrate REMEMBERS what was killed and why. Silent deletion
// is forbidden (§5.2). The tombstone preserves causality (P06): the killed
// part once existed; the substrate retains the record of its existence and
// its cause-of-death even though its operative role has ended.
//
// The four canonical 应朽 family categories (illustrative not exhaustive per
// P07 §2 / §3.1.c — `包括但不限于`):
//   - 过时 (outdated)   — context-expiry / epoch-crossed
//   - 错误 (wrong)      — falsified / contradicted
//   - 冗余 (redundant)  — structural duplicate without disambiguation
//   - 无用 (useless)    — zero-reachability / orphan past grace
// L1-recognized family members (per F24 anticipated registry) may include:
//   有害 / 矛盾 / 僵化 / 异化 / 污染 / 失效 / 寄生 / 滞塞 / 死症 / ...
// ---------------------------------------------------------------------------

/// **v3.1.1 P07 §3.3** prefix for `internal_mortality_event:{category}` DAG
/// nodes. Emitted every time the prune-scan kills a part that has entered
/// the 应朽 family. The category suffix is one of the canonical four
/// (`过时` / `错误` / `冗余` / `无用`) or an L1-recognized family member
/// name (registered via F24 应朽 detection rule registry).
///
/// Closes P07 §3.3 silent-deletion prohibition: every part-death MUST have
/// a tombstone in the DAG. C55 `silent_internal_mortality` fires if a part
/// becomes inactive without a corresponding tombstone.
pub const NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX: &str = "internal_mortality_event:";

/// **v3.1.1 P07 §3.3** encode an `internal_mortality_event:{category}` DAG
/// node content. Records the cause of part-death so the substrate
/// REMEMBERS even what it killed (P06 causality preserved through prune).
///
/// Content map (canonical-bytes Map):
/// ```ignore
/// {
///   "category": "无用",                            // family member name
///   "rule_id": "L0.seed.orphan_past_grace",        // which rule fired
///   "killed_part_hash": <32 bytes>,                // the dead part's hash
///   "killed_part_node_type": "raw_material:...",   // what kind of part
///   "reason": "string explanation",                // human-readable cause
///   "replaced_by_hash": <32 bytes or null>,        // if replacement exists
///   "emitted_at_cycle": uint,                      // when death happened
/// }
/// ```
///
/// Per L0/cards/P07_mortality.md §4.2.
pub fn encode_internal_mortality_event(
    category: &str,
    rule_id: &str,
    killed_part_hash: &[u8; 32],
    killed_part_node_type: &str,
    reason: &str,
    replaced_by_hash: Option<&[u8; 32]>,
    emitted_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("category".to_string(), Value::String(category.to_string()));
    m.insert("rule_id".to_string(), Value::String(rule_id.to_string()));
    m.insert(
        "killed_part_hash".to_string(),
        Value::Bytes(killed_part_hash.to_vec()),
    );
    m.insert(
        "killed_part_node_type".to_string(),
        Value::String(killed_part_node_type.to_string()),
    );
    m.insert("reason".to_string(), Value::String(reason.to_string()));
    match replaced_by_hash {
        Some(h) => {
            m.insert(
                "replaced_by_hash".to_string(),
                Value::Bytes(h.to_vec()),
            );
        }
        None => {
            m.insert("replaced_by_hash".to_string(), Value::Null);
        }
    }
    m.insert(
        "emitted_at_cycle".to_string(),
        Value::Uint(emitted_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("internal_mortality_event encode infallible")
}

/// **v3.1.1 P07 §3.3** convenience: full `internal_mortality_event:{category}`
/// node_type string. Category is the 应朽 family member name (canonical
/// four or L1 extension).
pub fn internal_mortality_event_node_type(category: &str) -> String {
    format!("{NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX}{category}")
}

/// **M26.3 P10 default rule registry** (F18 fixed point seed). Real
/// production substrates load this from `compression_rule_registry` SSoT
/// (CI-mutable); these are the seed values. Each rule has:
///
/// - `rule_id`: unique identifier (used as DAG node suffix)
/// - `description`: human-readable
/// - `target_node_type_prefix`: which node types this rule targets
/// - `min_age_cycles`: candidate nodes must be at least this old
/// - `aggregator`: name of the aggregation strategy
///
/// Rule mutation requires CI per F18; the seed values land at genesis
/// and stay in effect until a CI-attested `schema_evolution:compression_rule_*`
/// modifies them.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompressionRule {
    /// Stable identifier (e.g. "raw_material_aggregate_v1").
    pub rule_id: String,
    /// Human-readable description.
    pub description: String,
    /// Targets DAG nodes whose `node_type` starts with this prefix.
    pub target_node_type_prefix: String,
    /// Originals must be at least this many cycles old to be eligible.
    pub min_age_cycles: u64,
    /// Aggregation strategy: "sum_to_sporocarp" / "drop_after_retention" / "archive".
    pub aggregator: String,
}

/// Seed compression rule registry (P10.a categories + F18 default set).
/// Three rules covering L0 P10.a "compressible" inventory:
///
/// 1. **raw_material_aggregate_v1** — old `raw_material:*` nodes → aggregate sporocarp
/// 2. **federation_payload_retention_v1** — old `federation_received:*` past retention → drop
/// 3. **trajectory_archive_v1** — old `axis_perturbed:*` past active window → archive
///
/// `min_age_cycles` seed = 1000 (matches L0 P10.b "most recent ≥1000 cycles").
pub fn seed_compression_rule_registry() -> Vec<CompressionRule> {
    vec![
        CompressionRule {
            rule_id: "raw_material_aggregate_v1".to_string(),
            description:
                "Aggregate raw_material:* nodes older than 1000 cycles into a summary sporocarp."
                    .to_string(),
            target_node_type_prefix: "raw_material:".to_string(),
            min_age_cycles: 1000,
            aggregator: "sum_to_sporocarp".to_string(),
        },
        CompressionRule {
            rule_id: "federation_payload_retention_v1".to_string(),
            description:
                "Drop federation_received:* payloads past 1000-cycle retention."
                    .to_string(),
            target_node_type_prefix: "federation_received:".to_string(),
            min_age_cycles: 1000,
            aggregator: "drop_after_retention".to_string(),
        },
        CompressionRule {
            rule_id: "trajectory_archive_v1".to_string(),
            description:
                "Archive axis_perturbed:* trajectory clusters past the active 1000-cycle window."
                    .to_string(),
            target_node_type_prefix: "axis_perturbed:".to_string(),
            min_age_cycles: 1000,
            aggregator: "archive".to_string(),
        },
    ]
}

/// **M26.3 P10.b compression invariant set enumeration** (L1/SCHEMA §4.1 tier-1).
///
/// Categories that MUST NEVER be compressed (loss of any of these would
/// violate I1/I4/I7/I9). Substrate enforces this set on every compression
/// mutation; C51 fires if a compression event ever names a member of this
/// set in its `compressed_node_hashes`.
///
/// The seven categories:
/// - `genesis_event:*` — substrate-ID + genesis attestation chain (P10.b first)
/// - `owner_key_*` — owner_key_history (active-prefix + archived-tail)
/// - `mutation:*` — every CI-attested mutation (audit trail)
/// - `evolution_succeeded:*` / `evolution_failed:*` — CI mutation outcomes
/// - `self_euthanasia_*` — mortality signals
/// - `federation_peer_pinned:*` — federation peer pin records
/// - the most-recent-N-cycles floor (default N=1000; orthogonal "recency" guard)
#[derive(Debug, Clone)]
pub struct CompressionInvariantSet {
    /// Node-type prefixes that are NEVER compressible regardless of age.
    pub forbidden_prefixes: Vec<String>,
    /// Most recent N cycles of ANY node type are protected (per L0 P10.b
    /// "most recent ≥1000 cycles full DAG"). Default 1000.
    pub recent_cycles_floor: u64,
}

/// Seed P10.b invariant set per L0/META §7 (amendment).
pub fn seed_compression_invariant_set() -> CompressionInvariantSet {
    CompressionInvariantSet {
        forbidden_prefixes: vec![
            // Substrate-ID + genesis attestation chain.
            "genesis_event:".to_string(),
            // Owner key history (initialized / added / archived).
            "owner_key_".to_string(),
            // Every CI-attested mutation + its outcome.
            "mutation:".to_string(),
            "evolution_succeeded:".to_string(),
            "evolution_failed:".to_string(),
            // Mortality signals.
            "self_euthanasia_".to_string(),
            // Federation peer pins.
            "federation_peer_pinned:".to_string(),
            // Birth-period quarantine markers (lifecycle).
            "birth_period_quarantine_".to_string(),
            // Operator pinning (substrate-ID-class).
            "operator_pinned:".to_string(),
            // Compression events themselves are CI-attested mutations and
            // must NEVER be compressed away (audit chain).
            "compression_event:".to_string(),
        ],
        recent_cycles_floor: 1000,
    }
}

/// Returns true if `node_type` is forbidden from compression by P10.b.
/// (Recent-cycles floor is enforced separately because it requires the
/// current cycle counter.)
pub fn node_type_in_invariant_set(
    node_type: &str,
    invariant_set: &CompressionInvariantSet,
) -> bool {
    invariant_set
        .forbidden_prefixes
        .iter()
        .any(|p| node_type.starts_with(p.as_str()))
}

/// **M26.3 P10.c CompressionWitness** (I9 attestation payload).
///
/// Every `mutation:compression` carries one of these as its
/// `content_canonical_bytes`. The substrate verifies it before accepting
/// the mutation; the owner signs it via the standard CI envelope.
///
/// Canonical form:
/// ```text
/// Map({
///   "rule_id": String,                       // which compression rule produced this
///   "compressed_node_hashes": Array(Bytes),  // originals being compressed (BLAKE3 hashes)
///   "aggregate_summary": Bytes,              // canonical-bytes of the aggregate (rule-specific shape)
///   "attestation_dag_tip": Bytes(32),        // DAG tip at attestation time
///   "semantic_lossy": Bool,                  // ALWAYS true per L0 P10
///   "causal_recoverability_argument": String,// human-readable I9 argument
/// })
/// ```
pub fn encode_compression_witness(
    rule_id: &str,
    compressed_node_hashes: &[[u8; 32]],
    aggregate_summary: &[u8],
    attestation_dag_tip: &[u8; 32],
    causal_recoverability_argument: &str,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("rule_id".to_string(), Value::String(rule_id.to_string()));
    let hashes_array: Vec<Value> = compressed_node_hashes
        .iter()
        .map(|h| Value::Bytes(h.to_vec()))
        .collect();
    m.insert(
        "compressed_node_hashes".to_string(),
        Value::Array(hashes_array),
    );
    m.insert(
        "aggregate_summary".to_string(),
        Value::Bytes(aggregate_summary.to_vec()),
    );
    m.insert(
        "attestation_dag_tip".to_string(),
        Value::Bytes(attestation_dag_tip.to_vec()),
    );
    m.insert("semantic_lossy".to_string(), Value::Bool(true));
    m.insert(
        "causal_recoverability_argument".to_string(),
        Value::String(causal_recoverability_argument.to_string()),
    );
    cb_encode(&Value::Map(m)).expect("compression_witness encode infallible")
}

/// Decode a CompressionWitness from its canonical bytes. Returns
/// `(rule_id, compressed_node_hashes, aggregate_summary, attestation_dag_tip)`
/// or `None` if the shape is wrong.
pub fn decode_compression_witness_minimal(
    bytes: &[u8],
) -> Option<(String, Vec<[u8; 32]>, Vec<u8>, [u8; 32])> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(bytes).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    let rule_id = match m.get("rule_id")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let hashes_array = match m.get("compressed_node_hashes")? {
        Value::Array(a) => a.clone(),
        _ => return None,
    };
    let mut hashes: Vec<[u8; 32]> = Vec::with_capacity(hashes_array.len());
    for v in hashes_array {
        let b = match v {
            Value::Bytes(b) => b,
            _ => return None,
        };
        if b.len() != 32 {
            return None;
        }
        let mut arr = [0u8; 32];
        arr.copy_from_slice(&b);
        hashes.push(arr);
    }
    let aggregate_summary = match m.get("aggregate_summary")? {
        Value::Bytes(b) => b.clone(),
        _ => return None,
    };
    let attestation_dag_tip = match m.get("attestation_dag_tip")? {
        Value::Bytes(b) => {
            if b.len() != 32 {
                return None;
            }
            let mut arr = [0u8; 32];
            arr.copy_from_slice(b);
            arr
        }
        _ => return None,
    };
    Some((rule_id, hashes, aggregate_summary, attestation_dag_tip))
}

/// Encode a `compression_event:{rule_id}` DAG node content (M26.3). The
/// content is essentially the witness PLUS the post-emission tip hash.
/// Form:
/// ```text
/// Map({
///   "rule_id": String,
///   "compressed_node_hashes": Array(Bytes),
///   "aggregate_summary": Bytes,
///   "witness_at_dag_tip": Bytes(32),
///   "emitted_at_cycle": Uint,
/// })
/// ```
pub fn encode_compression_event(
    rule_id: &str,
    compressed_node_hashes: &[[u8; 32]],
    aggregate_summary: &[u8],
    witness_at_dag_tip: &[u8; 32],
    emitted_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("rule_id".to_string(), Value::String(rule_id.to_string()));
    let hashes_array: Vec<Value> = compressed_node_hashes
        .iter()
        .map(|h| Value::Bytes(h.to_vec()))
        .collect();
    m.insert(
        "compressed_node_hashes".to_string(),
        Value::Array(hashes_array),
    );
    m.insert(
        "aggregate_summary".to_string(),
        Value::Bytes(aggregate_summary.to_vec()),
    );
    m.insert(
        "witness_at_dag_tip".to_string(),
        Value::Bytes(witness_at_dag_tip.to_vec()),
    );
    m.insert(
        "emitted_at_cycle".to_string(),
        Value::Uint(emitted_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("compression_event encode infallible")
}

/// Convenience: full `compression_event:{rule_id}` node_type string.
pub fn compression_event_node_type(rule_id: &str) -> String {
    format!("{NODE_TYPE_COMPRESSION_EVENT_PREFIX}{rule_id}")
}

// ---------------------------------------------------------------------------
// **M26.4 P11.c Ordered Fallback + P14.c Telos Drift**.
//
// M26.2 made cost signals OBSERVABLE; M26.3 made compression POSSIBLE; this
// milestone closes the loop: budgets + automatic fallback + telos drift.
//
// L0/META §10 (negative space).c ordered fallback semantics:
//   (1) pre-eligibility (cycle <N, default 1000):  refuse new P2 + budget_exhausted:{axis}
//   (2) post-eligibility (cycle ≥N):               trigger P10 compression proposal
//   (3) compression-insufficient (sustained):       degraded → alive::saturated
//   (sustained at stage 3 → P7 mortality)
//
// L0/cards/P07_mortality (mortality protection) P14.c telos drift semantics (L1/TROPISM §F + algorithms/telos_drift.md):
//   - Sparse-vector PROXY (no substrate-side LLM yet): owner objective declares
//     weight vector over node_type prefixes; sporocarp centroid = fractional
//     distribution of recent daily sporocarps; alignment = cosine similarity.
//   - Birth-period suspended → telos_alignment_pending (daily, not immune).
//   - Drift threshold grading per L1/TROPISM §F + algorithms/telos_drift.md.
// ---------------------------------------------------------------------------

/// **M26.4 F19 cost budgets** — per-axis thresholds firing P11.c.
/// Tier-1 SSoT (CI-mutable per F19 fixed point). Defaults seeded; substrates
/// MAY tighten via owner-attested mutation (mutation_type="cost_budget_set").
#[derive(Debug, Clone, Copy)]
pub struct CostBudgets {
    /// Max wall-clock nanoseconds per metabolic cycle (signal #7).
    /// Seed: 100ms — reasonable upper bound for one cycle on commodity
    /// hardware. Cycles exceeding this are budget-exhausted on axis "compute".
    pub compute_ns_per_cycle: u64,
    /// Max federation egress wire bytes per cycle (signal #8).
    /// Seed: 1 MiB — bounds the substrate's outbound traffic.
    pub network_bytes_per_cycle: u64,
    /// Max bytes added to `dag.cb` + `snapshot.cb` per cycle (signal #9).
    /// Seed: 10 MiB — bounds the rate of disk growth.
    pub storage_bytes_per_cycle: u64,
    /// Cycle count below which the substrate is in P11.c pre-eligibility
    /// stage (no compression yet). Seed: 1000 — matches L0 P11.c "cycle <N,
    /// default 1000" and the P10.b recent_cycles_floor.
    pub pre_eligibility_cycle_floor: u64,
    /// Sustained-saturation threshold: number of CONSECUTIVE cycles in
    /// PostEligibility (compression proposed but budgets still exhausted)
    /// before transitioning to alive::saturated. Seed: 100.
    pub sustained_saturation_cycle_threshold: u64,
}

/// Seed F19 cost budget defaults.
pub fn seed_cost_budgets() -> CostBudgets {
    CostBudgets {
        compute_ns_per_cycle: 100_000_000,     // 100 ms
        network_bytes_per_cycle: 1_048_576,    // 1 MiB
        storage_bytes_per_cycle: 10_485_760,   // 10 MiB
        pre_eligibility_cycle_floor: 1000,
        sustained_saturation_cycle_threshold: 100,
    }
}

/// **M26.4 P11.c saturation stage** — substrate-state machine for ordered
/// fallback under budget exhaustion. Persists in `ServerState` and emits a
/// DAG event on each transition.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SaturationStage {
    /// Cost signals within budget. Default state.
    Normal,
    /// Budget exhausted but cycle < pre_eligibility_cycle_floor.
    /// Substrate refuses NEW raw_material ingestion; emits
    /// `budget_exhausted:{axis}` daily events.
    PreEligibility,
    /// Budget exhausted AND cycle ≥ floor. Substrate emits
    /// `compression_proposed:{rule_id}` daily events for each rule
    /// with eligible candidates (per L0 P11.c stage 2).
    PostEligibility,
    /// Budget exhausted AND PostEligibility has persisted ≥
    /// sustained_saturation_cycle_threshold consecutive cycles. Substrate
    /// transitions to `alive::saturated`; subsequent sustained saturation
    /// leads to P7 mortality.
    Saturated,
}

impl SaturationStage {
    /// Stable string label for the stage; used by observatory response
    /// payload + DAG event content. MUST NOT change without doctrine
    /// migration (operator clients pin on these strings).
    pub fn as_str(self) -> &'static str {
        match self {
            SaturationStage::Normal => "normal",
            SaturationStage::PreEligibility => "pre_eligibility",
            SaturationStage::PostEligibility => "post_eligibility",
            SaturationStage::Saturated => "saturated",
        }
    }
}

/// Prefix for `budget_exhausted:{axis}` daily events (M26.4 P11.c stage 1).
/// Axis ∈ {`compute_per_cycle`, `network_per_cycle`, `storage_per_cycle`}.
pub const NODE_TYPE_BUDGET_EXHAUSTED_PREFIX: &str = "budget_exhausted:";

/// Prefix for `compression_proposed:{rule_id}` daily events (M26.4 P11.c
/// stage 2). Operator picks these up + submits a matching CI-attested
/// `mutation:compression` to actually compress.
pub const NODE_TYPE_COMPRESSION_PROPOSED_PREFIX: &str = "compression_proposed:";

/// `substrate_saturated` event — M26.4 P11.c stage 3 transition into
/// `alive::saturated` substrate sub-state.
pub const NODE_TYPE_SUBSTRATE_SATURATED: &str = "substrate_saturated";

/// `substrate_normal_restored` event — M26.4 P11.c reverse transition when
/// budget exhaustion clears across all axes.
pub const NODE_TYPE_SUBSTRATE_NORMAL_RESTORED: &str = "substrate_normal_restored";

/// Encode a `budget_exhausted:{axis}` event.
/// ```text
/// Map({ "axis": String, "current_value": Uint, "budget": Uint, "at_cycle": Uint })
/// ```
pub fn encode_budget_exhausted(
    axis: &str,
    current_value: u64,
    budget: u64,
    at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("axis".to_string(), Value::String(axis.to_string()));
    m.insert("current_value".to_string(), Value::Uint(current_value));
    m.insert("budget".to_string(), Value::Uint(budget));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    cb_encode(&Value::Map(m)).expect("budget_exhausted encode infallible")
}

/// Encode a `compression_proposed:{rule_id}` event.
/// ```text
/// Map({ "rule_id": String, "at_cycle": Uint, "proposed_axis": String, "estimated_candidates": Uint })
/// ```
pub fn encode_compression_proposed(
    rule_id: &str,
    at_cycle: u64,
    proposed_axis: &str,
    estimated_candidates: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("rule_id".to_string(), Value::String(rule_id.to_string()));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert(
        "proposed_axis".to_string(),
        Value::String(proposed_axis.to_string()),
    );
    m.insert(
        "estimated_candidates".to_string(),
        Value::Uint(estimated_candidates),
    );
    cb_encode(&Value::Map(m)).expect("compression_proposed encode infallible")
}

/// Encode a `substrate_saturated` event.
pub fn encode_substrate_saturated(
    at_cycle: u64,
    sustained_cycles: u64,
    triggering_axis: &str,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert("sustained_cycles".to_string(), Value::Uint(sustained_cycles));
    m.insert(
        "triggering_axis".to_string(),
        Value::String(triggering_axis.to_string()),
    );
    cb_encode(&Value::Map(m)).expect("substrate_saturated encode infallible")
}

/// Encode a `substrate_normal_restored` event.
pub fn encode_substrate_normal_restored(at_cycle: u64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    cb_encode(&Value::Map(m)).expect("substrate_normal_restored encode infallible")
}

/// **M26.4 F20 OwnerObjective** — owner-declared sparse weight vector over
/// `node_type_prefix` space, used by P14.c telos_alignment cosine proxy.
///
/// PROXY note: doctrine (L1/TROPISM §F + algorithms/telos_drift.md) prescribes
/// an LLM-embedding-based centroid. M26.4 substrates lack substrate-side LLM
/// (P2.a "adjacent tooling internalization" is M27+). We ship a faithful
/// PROXY: cosine over sparse prefix-weight vectors. Each `weight` is a
/// repr-float string for cross-language determinism (matches signal #6 ratio
/// convention). Future M27+ swaps cosine inputs to true embeddings without
/// breaking the substrate's surface contract — the cosine output remains
/// `[-1, +1]` and the threshold grading remains §F.1.
#[derive(Debug, Clone)]
pub struct OwnerObjective {
    /// Stable identifier for this objective declaration (operator-supplied).
    pub objective_id: String,
    /// Cycle at which this objective was declared. Anchors the I4 audit.
    pub declared_at_cycle: u64,
    /// Sparse weight vector: `node_type_prefix → weight`. Sum SHOULD be
    /// positive (substrate normalizes during cosine compute). All weights
    /// ≥ 0; negative weights MAY be added in future revisions to express
    /// "actively against" but are currently rejected.
    pub weights: Vec<(String, f64)>,
}

/// Seed F20 owner objective — empty by default. The substrate falls back to
/// the §F.1 branch-2 path (centroid over recent trajectory deltas) when no
/// owner objective is declared. Operator MAY declare via mutation_type=
/// "owner_objective_declaration" (CI per F20).
pub fn seed_owner_objective() -> Option<OwnerObjective> {
    None
}

/// Encode an OwnerObjective into canonical-bytes (the
/// `mutation:owner_objective_declaration` content payload).
/// ```text
/// Map({
///   "objective_id": String,
///   "declared_at_cycle": Uint,
///   "weights": Array(Map({"prefix": String, "weight_repr": String}))
/// })
/// ```
pub fn encode_owner_objective(obj: &OwnerObjective) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "objective_id".to_string(),
        Value::String(obj.objective_id.clone()),
    );
    m.insert(
        "declared_at_cycle".to_string(),
        Value::Uint(obj.declared_at_cycle),
    );
    let weights_array: Vec<Value> = obj
        .weights
        .iter()
        .map(|(prefix, w)| {
            let mut entry = BTreeMap::new();
            entry.insert("prefix".to_string(), Value::String(prefix.clone()));
            entry.insert("weight_repr".to_string(), Value::String(format!("{w:?}")));
            Value::Map(entry)
        })
        .collect();
    m.insert("weights".to_string(), Value::Array(weights_array));
    cb_encode(&Value::Map(m)).expect("owner_objective encode infallible")
}

/// Decode an OwnerObjective from canonical-bytes. Returns None if shape is
/// wrong (operator caller emits C5 attestation_invalid in that case).
pub fn decode_owner_objective(bytes: &[u8]) -> Option<OwnerObjective> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(bytes).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    let objective_id = match m.get("objective_id")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let declared_at_cycle = match m.get("declared_at_cycle")? {
        Value::Uint(n) => *n,
        _ => return None,
    };
    let weights_arr = match m.get("weights")? {
        Value::Array(a) => a.clone(),
        _ => return None,
    };
    let mut weights: Vec<(String, f64)> = Vec::with_capacity(weights_arr.len());
    for entry_v in weights_arr {
        let entry = match entry_v {
            Value::Map(em) => em,
            _ => return None,
        };
        let prefix = match entry.get("prefix")? {
            Value::String(s) => s.clone(),
            _ => return None,
        };
        let weight_repr = match entry.get("weight_repr")? {
            Value::String(s) => s.clone(),
            _ => return None,
        };
        let w: f64 = weight_repr.parse().ok()?;
        if w < 0.0 || !w.is_finite() {
            // Reject negative / NaN / inf weights (see F20 doc comment).
            return None;
        }
        weights.push((prefix, w));
    }
    Some(OwnerObjective {
        objective_id,
        declared_at_cycle,
        weights,
    })
}

/// `owner_objective_declared:{objective_id}` event — emitted after a
/// successful CI-attested owner_objective_declaration mutation.
pub const NODE_TYPE_OWNER_OBJECTIVE_DECLARED_PREFIX: &str = "owner_objective_declared:";

// ---------------------------------------------------------------------------
// **v3.1.1 Sprint 2.C** — backup encryption status SSoT.
//
// Per L1/SKIN §8: cultivator owns the backup-encryption symmetric key; the
// substrate stores ONLY a public status field declaring whether backups
// are encrypted, declined-explicit, or unspecified. The key NEVER enters
// state_dir. Operator-runtime performs the encryption; substrate provides
// plaintext canonical-bytes.
//
// L1/HARD_RULES §1.4 (anticipated) + L1/SKIN §9 detection table:
//   - `backup_encryption_undeclared` (Daily) — emitted on boot when the
//     SSoT field is None ("unspecified" per L1/SKIN §8). Per L1/SKIN §9:
//     Daily grade — visible but not breach-quarantine.
//   - `backup_encryption_status_declared:{status}` — CI-attested DAG event
//     setting the status. Cultivator chooses one of:
//       - "encrypted_externally" — operator-runtime encrypts; key is held
//         by the cultivator outside state_dir
//       - "cultivator_declined_explicit" — cultivator signs an explicit
//         declination acknowledging unencrypted backups
// ---------------------------------------------------------------------------

/// Prefix for `backup_encryption_status_declared:{status}` DAG events
/// (v3.1.1 Sprint 2.C). Emitted by `attestation.rs::handle_submit_mutation`
/// after a successful CI-attested `set_backup_encryption_status` mutation.
/// The substrate's `ServerState::backup_encryption_status` is the cached
/// projection of the latest such event's `status` field.
pub const NODE_TYPE_BACKUP_ENCRYPTION_STATUS_DECLARED_PREFIX: &str =
    "backup_encryption_status_declared:";

/// Canonical status values for `backup_encryption_status_declared:{status}`.
/// Must match the symmetric constant in
/// `kernel/governance/src/myco_kernel_governance/classifier.py`. See test
/// `test_v3_1_1_sprint_2c_backup_encryption_statuses_in_sync`.
pub const BACKUP_ENCRYPTION_STATUS_ENCRYPTED_EXTERNALLY: &str = "encrypted_externally";
/// See `BACKUP_ENCRYPTION_STATUS_ENCRYPTED_EXTERNALLY`.
pub const BACKUP_ENCRYPTION_STATUS_CULTIVATOR_DECLINED_EXPLICIT: &str =
    "cultivator_declined_explicit";

/// Canonical list of valid backup_encryption_status values. Anything else
/// rejected by the classifier rule + mutation handler.
pub const BACKUP_ENCRYPTION_STATUS_VALID_VALUES: &[&str] = &[
    BACKUP_ENCRYPTION_STATUS_ENCRYPTED_EXTERNALLY,
    BACKUP_ENCRYPTION_STATUS_CULTIVATOR_DECLINED_EXPLICIT,
];

/// Encode a `backup_encryption_status_declared:{status}` event body. Stored
/// alongside the cultivator's CI attestation in the substrate DAG.
///
/// Content (canonical-bytes Map):
/// ```ignore
/// {
///   "status": "encrypted_externally" | "cultivator_declined_explicit",
///   "key_id": "string" | null,    // public derivation pointer; never the key itself
///   "declared_at_cycle": uint,
/// }
/// ```
pub fn encode_backup_encryption_status_declared(
    status: &str,
    key_id: Option<&str>,
    declared_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("status".to_string(), Value::String(status.to_string()));
    match key_id {
        Some(id) => {
            m.insert("key_id".to_string(), Value::String(id.to_string()));
        }
        None => {
            m.insert("key_id".to_string(), Value::Null);
        }
    }
    m.insert(
        "declared_at_cycle".to_string(),
        Value::Uint(declared_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("backup_encryption_status_declared encode infallible")
}

/// Convenience: full `backup_encryption_status_declared:{status}` node_type.
pub fn backup_encryption_status_declared_node_type(status: &str) -> String {
    format!("{NODE_TYPE_BACKUP_ENCRYPTION_STATUS_DECLARED_PREFIX}{status}")
}

/// Decode a `backup_encryption_status_declared:*` event body, returning the
/// declared status string. Returns `None` on malformed content.
pub fn decode_backup_encryption_status(content: &[u8]) -> Option<String> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(content).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    match m.get("status") {
        Some(Value::String(s)) => Some(s.clone()),
        _ => None,
    }
}

/// **v3.1.1 Sprint 2.C** — walk the DAG, return the latest declared
/// backup_encryption_status (or None if no `backup_encryption_status_declared:*`
/// event is present). Called once at boot from `server::run_loop` to seed
/// `ServerState::backup_encryption_status`.
///
/// "Latest" = highest `created_at_cycle`. Ties broken by insertion order
/// (we take the last in insertion order; DAG iteration is deterministic).
pub fn derive_backup_encryption_status_from_dag(
    dag: &myco_kernel_schema::dag::Dag,
) -> Option<String> {
    let mut latest: Option<(u64, String)> = None;
    for node in dag.iter_in_insertion_order() {
        if !node
            .node_type
            .starts_with(NODE_TYPE_BACKUP_ENCRYPTION_STATUS_DECLARED_PREFIX)
        {
            continue;
        }
        if let Some(status) = decode_backup_encryption_status(node.content_canonical_bytes.as_ref())
        {
            // Replace if strictly later cycle, OR same cycle (last writer
            // wins on tie via in-order iteration).
            let replace = match &latest {
                Some((c, _)) => node.created_at_cycle >= *c,
                None => true,
            };
            if replace {
                latest = Some((node.created_at_cycle, status));
            }
        }
    }
    latest.map(|(_, s)| s)
}

/// Encode the `owner_objective_declared` event body.
pub fn encode_owner_objective_declared(
    objective_id: &str,
    declared_at_cycle: u64,
    weights_count: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "objective_id".to_string(),
        Value::String(objective_id.to_string()),
    );
    m.insert(
        "declared_at_cycle".to_string(),
        Value::Uint(declared_at_cycle),
    );
    m.insert("weights_count".to_string(), Value::Uint(weights_count));
    cb_encode(&Value::Map(m)).expect("owner_objective_declared encode infallible")
}

/// **M26.4 telos_drift events** (L1/TROPISM §F + algorithms/telos_drift.md).
///
/// Five grading levels per §F threshold table:
/// - `telos_alignment_pending` — birth-period suspended; daily, not immune
/// - `telos_alignment_low` — 0.4 < cos ≤ 0.6, observability, daily
/// - `telos_drift` (daily) — 0.2 < cos ≤ 0.4
/// - `telos_drift` (elevated) — 0.0 < cos ≤ 0.2
/// - `telos_drift_critical` (CRITICAL → C24) — cos ≤ 0
pub const NODE_TYPE_TELOS_ALIGNMENT_PENDING: &str = "telos_alignment_pending";
/// `telos_alignment_low` event — emitted when cosine ∈ (0.4, 0.6]: observability,
/// not yet drift. Daily class, not immune.
pub const NODE_TYPE_TELOS_ALIGNMENT_LOW: &str = "telos_alignment_low";
/// `telos_drift` event — emitted when cosine ∈ (0.2, 0.4] (regular) or
/// (0.0, 0.2] (elevated). Daily class. Content's `grade` field
/// distinguishes "drift" vs "drift_elevated".
pub const NODE_TYPE_TELOS_DRIFT: &str = "telos_drift";
/// `telos_drift_critical` event — emitted when cosine ≤ 0 (CRITICAL grade
/// per §F.1). Paired with C24_telos_drift_critical immune sporocarp.
pub const NODE_TYPE_TELOS_DRIFT_CRITICAL: &str = "telos_drift_critical";

/// Encode a telos_alignment status event (any of the four levels above).
pub fn encode_telos_status(
    cosine_repr: &str,
    grade: &str,
    at_cycle: u64,
    sample_window_size: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "cosine_repr".to_string(),
        Value::String(cosine_repr.to_string()),
    );
    m.insert("grade".to_string(), Value::String(grade.to_string()));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert(
        "sample_window_size".to_string(),
        Value::Uint(sample_window_size),
    );
    cb_encode(&Value::Map(m)).expect("telos_status encode infallible")
}

// ---------------------------------------------------------------------------
// Federation event encoders (M22).
// ---------------------------------------------------------------------------

/// Content of a `federation_listener_opened` event (M22.1):
/// ```text
/// Map({ "bind_addr": String, "opened_at_unix_ns": Timestamp })
/// ```
pub fn encode_federation_listener_opened(
    bind_addr: &str,
    opened_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "bind_addr".to_string(),
        Value::String(bind_addr.to_string()),
    );
    m.insert(
        "opened_at_unix_ns".to_string(),
        Value::Timestamp(opened_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("federation_listener_opened encode infallible")
}

/// Content of a `federation_listener_closed` event (M22.1):
/// ```text
/// Map({ "bind_addr": String, "closed_at_unix_ns": Timestamp })
/// ```
pub fn encode_federation_listener_closed(
    bind_addr: &str,
    closed_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "bind_addr".to_string(),
        Value::String(bind_addr.to_string()),
    );
    m.insert(
        "closed_at_unix_ns".to_string(),
        Value::Timestamp(closed_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("federation_listener_closed encode infallible")
}

/// node_type for a federation_peer_pinned event (M22.2):
/// `federation_peer_pinned:{first_8_hex_of_peer_substrate_id}`.
pub fn federation_peer_pinned_node_type(peer_substrate_id: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_FEDERATION_PEER_PINNED_PREFIX,
        hex_prefix(peer_substrate_id, 8)
    )
}

/// Content of a `federation_peer_pinned` event (M22.2 + M25.4):
/// ```text
/// Map({
///   "peer_substrate_id": Bytes(32),
///   "remote_addr": String,
///   "first_pinned_unix_ns": Timestamp,
///   "signer_pubkey": Bytes(32) | absent,    // M25.4; absent for legacy peers
/// })
/// ```
///
/// M25.4: when present, `signer_pubkey` is the peer's Ed25519 signing key
/// learned + verified during the FED_HELLO exchange. Receivers that re-parse
/// this event on boot use the pubkey as the long-term peer-identity pin
/// (subsequent connections from the same substrate_id must present the same
/// pubkey OR the connection is treated as identity drift).
///
/// Backward compat: pre-M25 peers omit the field; receivers tolerate absence.
pub fn encode_federation_peer_pinned(
    peer_substrate_id: &[u8; 32],
    remote_addr: &str,
    first_pinned_unix_ns: i64,
    signer_pubkey: Option<&[u8; 32]>,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "peer_substrate_id".to_string(),
        Value::Bytes(peer_substrate_id.to_vec()),
    );
    m.insert(
        "remote_addr".to_string(),
        Value::String(remote_addr.to_string()),
    );
    m.insert(
        "first_pinned_unix_ns".to_string(),
        Value::Timestamp(first_pinned_unix_ns),
    );
    if let Some(pk) = signer_pubkey {
        m.insert("signer_pubkey".to_string(), Value::Bytes(pk.to_vec()));
    }
    cb_encode(&Value::Map(m)).expect("federation_peer_pinned encode infallible")
}

/// M25.4: node_type for a federation_legacy_peer_pinned event:
/// `federation_legacy_peer_pinned:{first_8_hex_of_peer_substrate_id}`.
pub fn federation_legacy_peer_pinned_node_type(peer_substrate_id: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_FEDERATION_LEGACY_PEER_PINNED_PREFIX,
        hex_prefix(peer_substrate_id, 8)
    )
}

/// M25.4: content of a `federation_legacy_peer_pinned` observability event.
///
/// Emitted when a peer is pinned without presenting an Ed25519 hello signature
/// (pre-M25 peer; allowed by legacy-compat path). Operators can grep for this
/// event to audit which connections are authenticated by substrate_id-TOFU
/// only vs full Ed25519 mutual auth.
///
/// ```text
/// Map({
///   "peer_substrate_id": Bytes(32),
///   "remote_addr": String,
///   "first_pinned_unix_ns": Timestamp,
/// })
/// ```
pub fn encode_federation_legacy_peer_pinned(
    peer_substrate_id: &[u8; 32],
    remote_addr: &str,
    first_pinned_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "peer_substrate_id".to_string(),
        Value::Bytes(peer_substrate_id.to_vec()),
    );
    m.insert(
        "remote_addr".to_string(),
        Value::String(remote_addr.to_string()),
    );
    m.insert(
        "first_pinned_unix_ns".to_string(),
        Value::Timestamp(first_pinned_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("federation_legacy_peer_pinned encode infallible")
}

/// node_type for a federation_peer_rejected event (M22.2 — C20 detector).
pub fn federation_peer_rejected_node_type(offered_substrate_id: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_FEDERATION_PEER_REJECTED_PREFIX,
        hex_prefix(offered_substrate_id, 8)
    )
}

/// Content of a `federation_peer_rejected` event (M22.2):
/// ```text
/// Map({
///   "offered_substrate_id": Bytes(32),
///   "previously_pinned_substrate_id": Bytes(32),
///   "remote_addr": String,
///   "rejected_at_unix_ns": Timestamp,
///   "reason": String,
/// })
/// ```
pub fn encode_federation_peer_rejected(
    offered_substrate_id: &[u8; 32],
    previously_pinned_substrate_id: &[u8; 32],
    remote_addr: &str,
    rejected_at_unix_ns: i64,
    reason: &str,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "offered_substrate_id".to_string(),
        Value::Bytes(offered_substrate_id.to_vec()),
    );
    m.insert(
        "previously_pinned_substrate_id".to_string(),
        Value::Bytes(previously_pinned_substrate_id.to_vec()),
    );
    m.insert(
        "remote_addr".to_string(),
        Value::String(remote_addr.to_string()),
    );
    m.insert(
        "rejected_at_unix_ns".to_string(),
        Value::Timestamp(rejected_at_unix_ns),
    );
    m.insert("reason".to_string(), Value::String(reason.to_string()));
    cb_encode(&Value::Map(m)).expect("federation_peer_rejected encode infallible")
}

/// Content of a `federation_events_received` event (M22.3).
///
/// `received_event_hashes` is the list of DAG node hashes that were ingested
/// from the peer (deduplicated against the local DAG via content-hash
/// idempotency in `Dag::insert_node`).
///
/// ```text
/// Map({
///   "from_peer_substrate_id": Bytes(32),
///   "received_event_hashes": Array<Bytes(32)>,
///   "received_at_unix_ns": Timestamp,
/// })
/// ```
pub fn encode_federation_events_received(
    from_peer_substrate_id: &[u8; 32],
    received_event_hashes: &[[u8; 32]],
    received_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "from_peer_substrate_id".to_string(),
        Value::Bytes(from_peer_substrate_id.to_vec()),
    );
    let hashes_array: Vec<Value> = received_event_hashes
        .iter()
        .map(|h| Value::Bytes(h.to_vec()))
        .collect();
    m.insert(
        "received_event_hashes".to_string(),
        Value::Array(hashes_array),
    );
    m.insert(
        "received_at_unix_ns".to_string(),
        Value::Timestamp(received_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("federation_events_received encode infallible")
}

/// Content of a `federation_events_sent` event (M22.3).
pub fn encode_federation_events_sent(
    to_peer_substrate_id: &[u8; 32],
    sent_event_hashes: &[[u8; 32]],
    sent_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "to_peer_substrate_id".to_string(),
        Value::Bytes(to_peer_substrate_id.to_vec()),
    );
    let hashes_array: Vec<Value> = sent_event_hashes
        .iter()
        .map(|h| Value::Bytes(h.to_vec()))
        .collect();
    m.insert("sent_event_hashes".to_string(), Value::Array(hashes_array));
    m.insert(
        "sent_at_unix_ns".to_string(),
        Value::Timestamp(sent_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("federation_events_sent encode infallible")
}

/// Content of a `parent_federation_hint` event (M22.4): the parent's
/// federation listener address, stored by the parent into the child's DAG at
/// sprout_child time.
///
/// ```text
/// Map({
///   "parent_substrate_id": Bytes(32),
///   "parent_federation_addr": String,           // e.g. "127.0.0.1:43210"
///   "hinted_at_unix_ns": Timestamp,
/// })
/// ```
pub fn encode_parent_federation_hint(
    parent_substrate_id: &[u8; 32],
    parent_federation_addr: &str,
    hinted_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "parent_substrate_id".to_string(),
        Value::Bytes(parent_substrate_id.to_vec()),
    );
    m.insert(
        "parent_federation_addr".to_string(),
        Value::String(parent_federation_addr.to_string()),
    );
    m.insert(
        "hinted_at_unix_ns".to_string(),
        Value::Timestamp(hinted_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("parent_federation_hint encode infallible")
}

/// Content of a `federation_parent_linked` event (M22.4): the child connected
/// back to its parent substrate via federation.
///
/// ```text
/// Map({
///   "parent_substrate_id": Bytes(32),
///   "parent_federation_addr": String,
///   "linked_at_unix_ns": Timestamp,
/// })
/// ```
pub fn encode_federation_parent_linked(
    parent_substrate_id: &[u8; 32],
    parent_federation_addr: &str,
    linked_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "parent_substrate_id".to_string(),
        Value::Bytes(parent_substrate_id.to_vec()),
    );
    m.insert(
        "parent_federation_addr".to_string(),
        Value::String(parent_federation_addr.to_string()),
    );
    m.insert(
        "linked_at_unix_ns".to_string(),
        Value::Timestamp(linked_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("federation_parent_linked encode infallible")
}

/// Content of a `birth_period_quarantine_entered` event (M22.5).
///
/// `inherited_immune_summary` is the list of (parent-side) immune-sporocarp
/// DAG node hashes the child inherits as inherited disease.
///
/// ```text
/// Map({
///   "parent_substrate_id": Bytes(32),
///   "inherited_immune_summary": Array<Bytes(32)>,
///   "quarantine_duration_cycles": Uint,
///   "entered_at_unix_ns": Timestamp,
/// })
/// ```
pub fn encode_birth_period_quarantine_entered(
    parent_substrate_id: &[u8; 32],
    inherited_immune_summary: &[[u8; 32]],
    quarantine_duration_cycles: u64,
    entered_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "parent_substrate_id".to_string(),
        Value::Bytes(parent_substrate_id.to_vec()),
    );
    let hashes_array: Vec<Value> = inherited_immune_summary
        .iter()
        .map(|h| Value::Bytes(h.to_vec()))
        .collect();
    m.insert(
        "inherited_immune_summary".to_string(),
        Value::Array(hashes_array),
    );
    m.insert(
        "quarantine_duration_cycles".to_string(),
        Value::Uint(quarantine_duration_cycles),
    );
    m.insert(
        "entered_at_unix_ns".to_string(),
        Value::Timestamp(entered_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("birth_period_quarantine_entered encode infallible")
}

/// node_type for a `self_euthanasia_executed` event (M23.2):
/// `self_euthanasia_executed:{axis_name}`.
pub fn self_euthanasia_executed_node_type(axis_name: &str) -> String {
    format!("{NODE_TYPE_SELF_EUTHANASIA_EXECUTED_PREFIX}{axis_name}")
}

/// Content of a `self_euthanasia_executed` event (M23.2):
///
/// ```text
/// Map({
///   "axis_name": String,                          // axis whose proposal was accepted
///   "triggering_proposal_hash": Bytes(32),        // hash of the accepted proposal node
///   "owner_signature": Bytes(64),                 // Ed25519 sig (canonical "myco-self-euthanasia-v1" + proposal_hash + substrate_id)
///   "owner_pubkey": Bytes(32),                    // the IDENTITY pubkey at moment of execution
///   "at_cycle": Uint,
///   "executed_at_unix_ns": Timestamp,
/// })
/// ```
pub fn encode_self_euthanasia_executed(
    axis_name: &str,
    triggering_proposal_hash: &[u8; 32],
    owner_signature: &[u8; 64],
    owner_pubkey: &[u8; 32],
    at_cycle: u64,
    executed_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("axis_name".to_string(), Value::String(axis_name.to_string()));
    m.insert(
        "triggering_proposal_hash".to_string(),
        Value::Bytes(triggering_proposal_hash.to_vec()),
    );
    m.insert(
        "owner_signature".to_string(),
        Value::Bytes(owner_signature.to_vec()),
    );
    m.insert(
        "owner_pubkey".to_string(),
        Value::Bytes(owner_pubkey.to_vec()),
    );
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert(
        "executed_at_unix_ns".to_string(),
        Value::Timestamp(executed_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("self_euthanasia_executed encode infallible")
}

/// Content of a `birth_period_quarantine_lifted` event (M22.5).
///
/// `reason` is "duration_elapsed", "operator_signed_lift", or
/// "all_inherited_signals_resolved".
pub fn encode_birth_period_quarantine_lifted(
    reason: &str,
    at_cycle: u64,
    lifted_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("reason".to_string(), Value::String(reason.to_string()));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert(
        "lifted_at_unix_ns".to_string(),
        Value::Timestamp(lifted_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("birth_period_quarantine_lifted encode infallible")
}

// ---------------------------------------------------------------------------
// Float repr utility — matches kernel/bridge protocol's `float_repr` convention.
// ---------------------------------------------------------------------------

/// Format an f64 as a Python-compatible repr string for cross-platform
/// deterministic event encoding. Identical convention to the wire protocol's
/// `float_repr` (kernel/bridge::protocol::float_repr).
pub fn float_repr(f: f64) -> String {
    if f.is_nan() {
        "nan".to_string()
    } else if f.is_infinite() {
        if f > 0.0 {
            "inf".to_string()
        } else {
            "-inf".to_string()
        }
    } else if f == f.trunc() && f.abs() < 1e16 {
        format!("{f:.1}")
    } else {
        format!("{f}")
    }
}

// ---------------------------------------------------------------------------
// Event encoders — produce canonical-bytes for DAG-node `content_canonical_bytes`.
//
// Convention: each function takes a single struct (or destructured args) and
// returns a `CanonicalBytes` ready for `Dag::insert_node`.
//
// The substrate's `node_type` string for each event includes a per-type
// suffix (e.g. axis name, pubkey prefix, nonce prefix) so that `query_recent_nodes`
// with prefix filters can isolate specific event categories.
// ---------------------------------------------------------------------------

/// Hex-encode the first N bytes of a byte slice for use as a node_type suffix.
///
/// Used to make event types like `axis_perturbed:{axis_name}` unambiguous AND
/// to ensure events like `nonce_issued:{first_8_bytes_hex}` are sortable +
/// human-readable in DAG dumps.
pub fn hex_prefix(bytes: &[u8], n_bytes: usize) -> String {
    bytes
        .iter()
        .take(n_bytes)
        .map(|b| format!("{b:02x}"))
        .collect()
}

// ---- genesis_event ----

/// node_type for the one-time genesis_event: `genesis_event:{first_8_bytes_of_substrate_id_hex}`.
pub fn genesis_event_node_type(substrate_id: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_GENESIS_PREFIX,
        hex_prefix(substrate_id, 8)
    )
}

// ---------------------------------------------------------------------------
// **M-anchor-5 §9.2.2 DAG-tip co-signing + §9.2.4 L0 revision diff workflow**.
//
// L1/SCHEMA §2.2: "Every CI crossing: owner MUST co-sign current DAG-tip;
// envelope MUST enumerate all DAG node hashes added since prior co-sign
// (not summary diff) — substrate cannot hide parallel-branch forgery.
// Substrate emits tip hash + enumerated node hashes + per-node metadata
// (type, causal-parent-hashes) + proposed CI mutation as canonical bytes.
// Owner verifies via Merkle-chain reconstruction; signs
// (canonical_bytes_hash, anchor_timestamp, anchor_nonce)."
//
// L0/cards/AS_anchor_surface §3.4: owner-side workflow for verifying L0 doctrine changes
// verbatim against prior commit hash. The substrate accepts an
// owner-signed envelope recording (prior_l0_hash, new_l0_hash,
// diff_summary, anchor_timestamp, anchor_nonce).
//
// M-anchor-5 is ADDITIVE: ships the canonical-bytes envelopes + DAG event
// types + mutation_type handlers. CI enforcement (require cosign before
// accepting any CI mutation) is deferred to M-anchor-5.5 alongside
// owner-tooling support.
// ---------------------------------------------------------------------------

/// Domain string for DAG-tip co-sign signatures (M-anchor-5 §9.2.2).
pub const DAG_TIP_COSIGN_DOMAIN: &str = "myco-dag-tip-cosign-v1";

/// Domain string for L0 revision attestation signatures (M-anchor-5 §9.2.4).
pub const L0_REVISION_DOMAIN: &str = "myco-l0-revision-v1";

/// Prefix for `tip_cosigned:{tip_prefix}` DAG events (M-anchor-5 §9.2.2).
pub const NODE_TYPE_TIP_COSIGNED_PREFIX: &str = "tip_cosigned:";

/// Prefix for `l0_revision_attested:{prior_l0_hash_prefix}` DAG events
/// (M-anchor-5 §9.2.4).
pub const NODE_TYPE_L0_REVISION_ATTESTED_PREFIX: &str = "l0_revision_attested:";

/// Build the canonical-bytes Map the owner signs for a DAG-tip co-sign
/// (M-anchor-5 §9.2.2). `proposed_mutation_hash` may be all-zero for a
/// standalone tip co-sign (no proposed CI mutation; just attesting the
/// tip + enumerated nodes).
pub fn build_dag_tip_cosign_canonical_bytes(
    tip_hash: &[u8; 32],
    enumerated_node_hashes: &[[u8; 32]],
    proposed_mutation_hash: &[u8; 32],
    anchor_timestamp_unix_ns: i64,
    anchor_nonce: &[u8; 32],
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(DAG_TIP_COSIGN_DOMAIN.to_string()),
    );
    m.insert("tip_hash".to_string(), Value::Bytes(tip_hash.to_vec()));
    let hashes_array: Vec<Value> = enumerated_node_hashes
        .iter()
        .map(|h| Value::Bytes(h.to_vec()))
        .collect();
    m.insert(
        "enumerated_node_hashes".to_string(),
        Value::Array(hashes_array),
    );
    m.insert(
        "proposed_mutation_hash".to_string(),
        Value::Bytes(proposed_mutation_hash.to_vec()),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(anchor_timestamp_unix_ns),
    );
    m.insert(
        "anchor_nonce".to_string(),
        Value::Bytes(anchor_nonce.to_vec()),
    );
    cb_encode(&Value::Map(m))
        .expect("dag_tip_cosign canonical-bytes encode infallible")
        .0
}

/// Decode a DAG-tip co-sign envelope. Returns the parsed fields or `None`
/// if the shape is wrong.
pub fn decode_dag_tip_cosign(
    bytes: &[u8],
) -> Option<([u8; 32], Vec<[u8; 32]>, [u8; 32], i64, [u8; 32])> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(bytes).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    // domain check.
    match m.get("domain")? {
        Value::String(s) if s == DAG_TIP_COSIGN_DOMAIN => {}
        _ => return None,
    }
    let tip_hash = bytes_to_arr32_local(m.get("tip_hash")?)?;
    let enumerated_arr = match m.get("enumerated_node_hashes")? {
        Value::Array(a) => a.clone(),
        _ => return None,
    };
    let mut enumerated: Vec<[u8; 32]> = Vec::with_capacity(enumerated_arr.len());
    for v in enumerated_arr {
        let h = bytes_to_arr32_local(&v)?;
        enumerated.push(h);
    }
    let proposed_mutation_hash = bytes_to_arr32_local(m.get("proposed_mutation_hash")?)?;
    let anchor_timestamp_unix_ns = match m.get("anchor_timestamp_unix_ns")? {
        Value::Timestamp(t) => *t,
        _ => return None,
    };
    let anchor_nonce = bytes_to_arr32_local(m.get("anchor_nonce")?)?;
    Some((
        tip_hash,
        enumerated,
        proposed_mutation_hash,
        anchor_timestamp_unix_ns,
        anchor_nonce,
    ))
}

/// Build the canonical-bytes Map the owner signs for an L0 revision
/// attestation (M-anchor-5 §9.2.4).
pub fn build_l0_revision_canonical_bytes(
    prior_l0_hash: &[u8; 32],
    new_l0_hash: &[u8; 32],
    diff_summary: &str,
    anchor_timestamp_unix_ns: i64,
    anchor_nonce: &[u8; 32],
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(L0_REVISION_DOMAIN.to_string()),
    );
    m.insert(
        "prior_l0_hash".to_string(),
        Value::Bytes(prior_l0_hash.to_vec()),
    );
    m.insert(
        "new_l0_hash".to_string(),
        Value::Bytes(new_l0_hash.to_vec()),
    );
    m.insert(
        "diff_summary".to_string(),
        Value::String(diff_summary.to_string()),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(anchor_timestamp_unix_ns),
    );
    m.insert(
        "anchor_nonce".to_string(),
        Value::Bytes(anchor_nonce.to_vec()),
    );
    cb_encode(&Value::Map(m))
        .expect("l0_revision canonical-bytes encode infallible")
        .0
}

/// Decode an L0 revision attestation envelope.
pub fn decode_l0_revision(
    bytes: &[u8],
) -> Option<([u8; 32], [u8; 32], String, i64, [u8; 32])> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(bytes).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    match m.get("domain")? {
        Value::String(s) if s == L0_REVISION_DOMAIN => {}
        _ => return None,
    }
    let prior_l0_hash = bytes_to_arr32_local(m.get("prior_l0_hash")?)?;
    let new_l0_hash = bytes_to_arr32_local(m.get("new_l0_hash")?)?;
    let diff_summary = match m.get("diff_summary")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let anchor_timestamp_unix_ns = match m.get("anchor_timestamp_unix_ns")? {
        Value::Timestamp(t) => *t,
        _ => return None,
    };
    let anchor_nonce = bytes_to_arr32_local(m.get("anchor_nonce")?)?;
    Some((
        prior_l0_hash,
        new_l0_hash,
        diff_summary,
        anchor_timestamp_unix_ns,
        anchor_nonce,
    ))
}

fn bytes_to_arr32_local(v: &Value) -> Option<[u8; 32]> {
    match v {
        Value::Bytes(b) => {
            if b.len() != 32 {
                return None;
            }
            let mut arr = [0u8; 32];
            arr.copy_from_slice(b);
            Some(arr)
        }
        _ => None,
    }
}

/// Convenience: full `tip_cosigned:{prefix}` node_type string.
pub fn tip_cosigned_node_type(tip_hash: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_TIP_COSIGNED_PREFIX,
        hex_prefix(tip_hash, 8)
    )
}

/// Convenience: full `l0_revision_attested:{prefix}` node_type string,
/// keyed on the prior_l0_hash so consecutive revisions are distinguishable.
pub fn l0_revision_attested_node_type(prior_l0_hash: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_L0_REVISION_ATTESTED_PREFIX,
        hex_prefix(prior_l0_hash, 8)
    )
}

/// Encode the body of a `tip_cosigned:{prefix}` DAG event.
/// Mirrors the cosign envelope shape PLUS owner signature + pubkey for
/// offline re-verification.
pub fn encode_tip_cosigned_event(
    cosign_envelope_bytes: &[u8],
    owner_signature: &[u8; 64],
    owner_pubkey: &[u8; 32],
    emitted_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "cosign_envelope".to_string(),
        Value::Bytes(cosign_envelope_bytes.to_vec()),
    );
    m.insert(
        "owner_signature".to_string(),
        Value::Bytes(owner_signature.to_vec()),
    );
    m.insert(
        "owner_pubkey".to_string(),
        Value::Bytes(owner_pubkey.to_vec()),
    );
    m.insert(
        "emitted_at_cycle".to_string(),
        Value::Uint(emitted_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("tip_cosigned event encode infallible")
}

/// Encode the body of an `l0_revision_attested:{prefix}` DAG event.
pub fn encode_l0_revision_attested_event(
    l0_revision_envelope_bytes: &[u8],
    owner_signature: &[u8; 64],
    owner_pubkey: &[u8; 32],
    emitted_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "l0_revision_envelope".to_string(),
        Value::Bytes(l0_revision_envelope_bytes.to_vec()),
    );
    m.insert(
        "owner_signature".to_string(),
        Value::Bytes(owner_signature.to_vec()),
    );
    m.insert(
        "owner_pubkey".to_string(),
        Value::Bytes(owner_pubkey.to_vec()),
    );
    m.insert(
        "emitted_at_cycle".to_string(),
        Value::Uint(emitted_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("l0_revision_attested event encode infallible")
}

// ---------------------------------------------------------------------------
// **M-anchor-4 §9.3.4 Witnesses-not-verdicts + §9.3.5 anchor-nonce sampling**.
//
// L0/cards/AS_anchor_surface §3.11 mandates that the substrate emit CRYPTO PROOFS for invariant
// checks (input bytes, Merkle paths, parent hashes, sampled leaf hashes) so
// the owner can re-derive pass/fail independently. The substrate does NOT
// emit pass/fail — only the inputs.
//
// L0/cards/AS_anchor_surface §3.12 specifies `H(anchor_surface_nonce, leaf_count)` as the
// derivation rule for sampled-leaf indices, so the substrate cannot bias
// which leaves it shows the owner.
//
// M-anchor-4 ships an ADDITIVE witness layer: the existing immune-sporocarp
// emission path on detected failures is preserved (since it's well-tested);
// alongside, every integrity check ALSO emits an `invariant_witness:{check_id}`
// DAG event carrying the raw inputs. Owner-side `anchor-client` re-derives
// pass/fail by reconstructing the canonical check.
// ---------------------------------------------------------------------------

/// Prefix for `invariant_witness:{check_id}` DAG events (M-anchor-4 §9.3.4).
/// One witness per integrity check per emission cycle.
pub const NODE_TYPE_INVARIANT_WITNESS_PREFIX: &str = "invariant_witness:";

/// Build the canonical node_type for a witness.
pub fn invariant_witness_node_type(check_id: &str) -> String {
    format!("{NODE_TYPE_INVARIANT_WITNESS_PREFIX}{check_id}")
}

/// Encode the body of an `invariant_witness:{check_id}` DAG event.
///
/// `inputs_map_canonical_bytes`: substrate-built canonical-bytes Map carrying
/// the raw inputs that the OWNER will re-feed into the canonical check
/// algorithm. Per-check schema is documented at the call site (e.g., for
/// `dag_verify_all`: `{node_count, sampled_indices, sampled_hashes,
/// sampled_parent_hashes, sampled_content_hashes}`).
///
/// The outer envelope is:
/// ```text
/// Map({
///   "check_id":                String,
///   "tier":                    String ("tier_1" / "tier_2" / "tier_3"),
///   "at_cycle":                Uint,
///   "at_unix_ns":              Timestamp,
///   "inputs":                  Bytes (= inputs_map_canonical_bytes),
///   "anchor_nonce":            Bytes(32) | Bytes(0),  // present if sampling used anchor nonce
///   "anchor_nonce_signature":  Bytes(64) | Bytes(0),  // anchor signature over the nonce
/// })
/// ```
pub fn encode_invariant_witness(
    check_id: &str,
    tier: &str,
    at_cycle: u64,
    at_unix_ns: i64,
    inputs_map_canonical_bytes: &[u8],
    anchor_nonce: &[u8],          // pass &[] for tier-1 (no sampling)
    anchor_nonce_signature: &[u8], // pass &[] for tier-1
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "check_id".to_string(),
        Value::String(check_id.to_string()),
    );
    m.insert("tier".to_string(), Value::String(tier.to_string()));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert("at_unix_ns".to_string(), Value::Timestamp(at_unix_ns));
    m.insert(
        "inputs".to_string(),
        Value::Bytes(inputs_map_canonical_bytes.to_vec()),
    );
    m.insert(
        "anchor_nonce".to_string(),
        Value::Bytes(anchor_nonce.to_vec()),
    );
    m.insert(
        "anchor_nonce_signature".to_string(),
        Value::Bytes(anchor_nonce_signature.to_vec()),
    );
    cb_encode(&Value::Map(m)).expect("invariant_witness encode infallible")
}

/// Decode an invariant_witness body. Returns the parsed fields or `None`
/// on shape mismatch. Used by owner-side reconstruction tooling (`anchor-client`
/// TS counterpart mirrors this).
pub fn decode_invariant_witness(
    bytes: &[u8],
) -> Option<(String, String, u64, i64, Vec<u8>, Vec<u8>, Vec<u8>)> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(bytes).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    let check_id = match m.get("check_id")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let tier = match m.get("tier")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let at_cycle = match m.get("at_cycle")? {
        Value::Uint(n) => *n,
        _ => return None,
    };
    let at_unix_ns = match m.get("at_unix_ns")? {
        Value::Timestamp(t) => *t,
        _ => return None,
    };
    let inputs = match m.get("inputs")? {
        Value::Bytes(b) => b.clone(),
        _ => return None,
    };
    let anchor_nonce = match m.get("anchor_nonce")? {
        Value::Bytes(b) => b.clone(),
        _ => return None,
    };
    let anchor_nonce_signature = match m.get("anchor_nonce_signature")? {
        Value::Bytes(b) => b.clone(),
        _ => return None,
    };
    Some((
        check_id,
        tier,
        at_cycle,
        at_unix_ns,
        inputs,
        anchor_nonce,
        anchor_nonce_signature,
    ))
}

/// **M-anchor-4 §9.3.5**: derive deterministic sample indices from an
/// anchor-supplied nonce. Substrate cannot bias which leaves it samples
/// because the indices are a pure function of the (anchor-signed) nonce.
///
/// Algorithm: hash the nonce + leaf_count + sample_round into a 32-byte
/// digest, then read it as `k` u64 indices modulo `leaf_count`. Produces
/// a deterministic-but-anchor-unbiased sample set.
///
/// `k` is the number of indices to return; clamped to `[0, 1024]`.
pub fn anchor_nonce_derived_sample_indices(
    anchor_nonce: &[u8; 32],
    leaf_count: u64,
    k: usize,
) -> Vec<u64> {
    use sha2::{Digest, Sha256};
    let k = k.min(1024);
    if leaf_count == 0 || k == 0 {
        return Vec::new();
    }
    let mut out: Vec<u64> = Vec::with_capacity(k);
    let mut round: u64 = 0;
    while out.len() < k {
        let mut h = Sha256::new();
        h.update(b"myco-anchor-nonce-sample-v1");
        h.update(anchor_nonce);
        h.update(leaf_count.to_le_bytes());
        h.update(round.to_le_bytes());
        let digest = h.finalize();
        // 4 u64s per digest = 32 bytes; emit indices until k filled.
        for chunk in digest.chunks(8) {
            if out.len() >= k {
                break;
            }
            let mut buf = [0u8; 8];
            buf.copy_from_slice(chunk);
            let raw = u64::from_le_bytes(buf);
            out.push(raw % leaf_count);
        }
        round = round.saturating_add(1);
    }
    out
}

// ---------------------------------------------------------------------------
// **M-anchor-2 P14.b §9.2.1 Birth Attestation**.
//
// L0/cards/AS_anchor_surface §3.1 mandates an owner-signed 5-tuple attesting that a fresh
// substrate's genesis was authorized by the Cultivator + anchor surface.
// The 5-tuple (per L0/cards/AS_anchor_surface §3):
//   (substrate-ID, genesis-timestamp,
//    initial-spore-schema-canonical-bytes-hash,
//    owner-public-key, anchor-surface-endpoint-public-key)
//
// At genesis the operator process fetches this attestation from
// `anchor_surface_host` via the `BirthAttest` RPC. The attestation is
// passed to the substrate as environment variables
// (MYCO_BIRTH_ATTESTATION_BYTES + MYCO_BIRTH_ATTESTATION_SIGNATURE +
// MYCO_BIRTH_ATTESTATION_OWNER_PUBKEY, all hex). Substrate emits a
// `birth_attestation:{substrate_id_prefix}` DAG event right after
// `genesis_event` carrying all three.
//
// Every boot re-verifies the signature against the current owner pubkey
// (or `owner_key_history` active prefix). Failure → C20
// `genesis_attestation_chain_broken` immune sporocarp + auto-quarantine.
// ---------------------------------------------------------------------------

/// Prefix for `birth_attestation:{substrate_id_prefix}` events (M-anchor-2).
pub const NODE_TYPE_BIRTH_ATTESTATION_PREFIX: &str = "birth_attestation:";

/// Full event node_type for a birth attestation, suffixed by the first 8
/// bytes of substrate_id in hex (mirrors `genesis_event_node_type`).
pub fn birth_attestation_node_type(substrate_id: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_BIRTH_ATTESTATION_PREFIX,
        hex_prefix(substrate_id, 8)
    )
}

/// Encode the body of a `birth_attestation` DAG event.
/// ```text
/// Map({
///   "attested_canonical_bytes": Bytes,  // the bytes the owner signed
///   "signature":                Bytes(64),
///   "owner_pubkey":             Bytes(32),
///   "emitted_at_unix_ns":       Timestamp,
/// })
/// ```
pub fn encode_birth_attestation(
    attested_canonical_bytes: &[u8],
    signature: &[u8; 64],
    owner_pubkey: &[u8; 32],
    emitted_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "attested_canonical_bytes".to_string(),
        Value::Bytes(attested_canonical_bytes.to_vec()),
    );
    m.insert(
        "signature".to_string(),
        Value::Bytes(signature.to_vec()),
    );
    m.insert(
        "owner_pubkey".to_string(),
        Value::Bytes(owner_pubkey.to_vec()),
    );
    m.insert(
        "emitted_at_unix_ns".to_string(),
        Value::Timestamp(emitted_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("birth_attestation encode infallible")
}

/// Decode a `birth_attestation` DAG event body. Used by the boot-time
/// C20 verifier. Returns `(attested_canonical_bytes, signature, owner_pubkey)`
/// or `None` if the shape is wrong.
pub fn decode_birth_attestation(
    bytes: &[u8],
) -> Option<(Vec<u8>, [u8; 64], [u8; 32])> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(bytes).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    let attested = match m.get("attested_canonical_bytes")? {
        Value::Bytes(b) => b.clone(),
        _ => return None,
    };
    let sig = match m.get("signature")? {
        Value::Bytes(b) => {
            if b.len() != 64 {
                return None;
            }
            let mut arr = [0u8; 64];
            arr.copy_from_slice(b);
            arr
        }
        _ => return None,
    };
    let pk = match m.get("owner_pubkey")? {
        Value::Bytes(b) => {
            if b.len() != 32 {
                return None;
            }
            let mut arr = [0u8; 32];
            arr.copy_from_slice(b);
            arr
        }
        _ => return None,
    };
    Some((attested, sig, pk))
}

/// Content of a genesis_event:
/// ```text
/// Map({ "substrate_id": Bytes(32), "genesis_time_unix_ns": Timestamp })
/// ```
pub fn encode_genesis_event(substrate_id: &[u8; 32], genesis_time_unix_ns: i64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "substrate_id".to_string(),
        Value::Bytes(substrate_id.to_vec()),
    );
    m.insert(
        "genesis_time_unix_ns".to_string(),
        Value::Timestamp(genesis_time_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("genesis_event encode infallible")
}

// ---- cycle_advanced ----

/// Content of a cycle_advanced event:
/// ```text
/// Map({ "prior_cycle": Uint, "new_cycle": Uint })
/// ```
pub fn encode_cycle_advanced(prior_cycle: u64, new_cycle: u64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("prior_cycle".to_string(), Value::Uint(prior_cycle));
    m.insert("new_cycle".to_string(), Value::Uint(new_cycle));
    cb_encode(&Value::Map(m)).expect("cycle_advanced encode infallible")
}

// ---- axis_registered ----

/// Parameters captured at axis registration. Mirrors the wire protocol's
/// register_axis payload fields, recorded as a DAG event for P5/P6 fidelity.
#[derive(Debug, Clone)]
pub struct AxisRegisteredEvent {
    /// Axis name (also embedded in node_type suffix).
    pub name: String,
    /// "appetite" or "decay".
    pub axis_class: String,
    /// Fruiting threshold (repr-encoded for determinism).
    pub fruiting_threshold: f64,
    /// Initial gradient value.
    pub initial_value: f64,
    /// Per-cycle decay rate.
    pub decay_rate_per_cycle: f64,
    /// Whether this axis is the mortality signal.
    pub is_mortality_signal: bool,
    /// "noop" or "decay".
    pub update_rule_kind: String,
}

/// node_type: `axis_registered:{name}`.
pub fn axis_registered_node_type(name: &str) -> String {
    format!("{}{}", NODE_TYPE_AXIS_REGISTERED_PREFIX, name)
}

/// Content of an axis_registered event:
/// ```text
/// Map({
///   "name": String,
///   "axis_class": String,
///   "fruiting_threshold_repr": String,
///   "initial_value_repr": String,
///   "decay_rate_per_cycle_repr": String,
///   "is_mortality_signal": Bool,
///   "update_rule_kind": String,
/// })
/// ```
pub fn encode_axis_registered(event: &AxisRegisteredEvent) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("name".to_string(), Value::String(event.name.clone()));
    m.insert(
        "axis_class".to_string(),
        Value::String(event.axis_class.clone()),
    );
    m.insert(
        "fruiting_threshold_repr".to_string(),
        Value::String(float_repr(event.fruiting_threshold)),
    );
    m.insert(
        "initial_value_repr".to_string(),
        Value::String(float_repr(event.initial_value)),
    );
    m.insert(
        "decay_rate_per_cycle_repr".to_string(),
        Value::String(float_repr(event.decay_rate_per_cycle)),
    );
    m.insert(
        "is_mortality_signal".to_string(),
        Value::Bool(event.is_mortality_signal),
    );
    m.insert(
        "update_rule_kind".to_string(),
        Value::String(event.update_rule_kind.clone()),
    );
    cb_encode(&Value::Map(m)).expect("axis_registered encode infallible")
}

// ---- axis_perturbed ----

/// node_type: `axis_perturbed:{name}`.
pub fn axis_perturbed_node_type(name: &str) -> String {
    format!("{}{}", NODE_TYPE_AXIS_PERTURBED_PREFIX, name)
}

/// Content of an axis_perturbed event:
/// ```text
/// Map({
///   "axis_name": String,
///   "delta_repr": String,
/// })
/// ```
///
/// M21.1 schema records only delta. Replay (M21.3 Python view) computes axis
/// values by summing deltas since axis_registered, in DAG insertion order.
pub fn encode_axis_perturbed(axis_name: &str, delta: f64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "axis_name".to_string(),
        Value::String(axis_name.to_string()),
    );
    m.insert("delta_repr".to_string(), Value::String(float_repr(delta)));
    cb_encode(&Value::Map(m)).expect("axis_perturbed encode infallible")
}

// ---- axis_reset_after_fruiting ----

/// node_type: `axis_reset_after_fruiting:{name}`.
pub fn axis_reset_node_type(name: &str) -> String {
    format!("{}{}", NODE_TYPE_AXIS_RESET_PREFIX, name)
}

/// Content of an axis_reset_after_fruiting event:
/// ```text
/// Map({
///   "axis_name": String,
///   "at_cycle": Uint,
///   "fruiting_value_repr": String,
///   "reset_to_value_repr": String,
/// })
/// ```
pub fn encode_axis_reset_after_fruiting(
    axis_name: &str,
    at_cycle: u64,
    fruiting_value: f64,
    reset_to_value: f64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "axis_name".to_string(),
        Value::String(axis_name.to_string()),
    );
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert(
        "fruiting_value_repr".to_string(),
        Value::String(float_repr(fruiting_value)),
    );
    m.insert(
        "reset_to_value_repr".to_string(),
        Value::String(float_repr(reset_to_value)),
    );
    cb_encode(&Value::Map(m)).expect("axis_reset encode infallible")
}

// ---- operator_pinned ----

/// node_type: `operator_pinned:{pubkey_hex_prefix}`.
pub fn operator_pinned_node_type(pubkey: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_OPERATOR_PINNED_PREFIX,
        hex_prefix(pubkey, 8)
    )
}

/// Content of an operator_pinned event (M9 TOFU):
/// ```text
/// Map({ "pubkey": Bytes(32), "first_pinned_unix_ns": Timestamp })
/// ```
pub fn encode_operator_pinned(pubkey: &[u8; 32], first_pinned_unix_ns: i64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("pubkey".to_string(), Value::Bytes(pubkey.to_vec()));
    m.insert(
        "first_pinned_unix_ns".to_string(),
        Value::Timestamp(first_pinned_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("operator_pinned encode infallible")
}

// ---- owner_key_initialized ----

/// Content of an owner_key_initialized event (M10 genesis):
/// ```text
/// Map({ "pubkey": Bytes(32), "anchor_timestamp_unix_seconds": Uint })
/// ```
pub fn encode_owner_key_initialized(
    pubkey: &[u8; 32],
    anchor_timestamp_unix_seconds: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("pubkey".to_string(), Value::Bytes(pubkey.to_vec()));
    m.insert(
        "anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(anchor_timestamp_unix_seconds),
    );
    cb_encode(&Value::Map(m)).expect("owner_key_initialized encode infallible")
}

// ---- rotate_owner_key envelope (Sprint 7.F T4.2) ----

/// Domain tag for rotate_owner_key canonical-bytes envelope. The owner
/// signs canonical-bytes Map carrying this domain + the rotation details.
pub const ROTATE_OWNER_KEY_DOMAIN: &str = "rotate_owner_key_v1";

/// **v3.1.1 Sprint 7.F (T4.2)** — build the canonical-bytes Map the owner
/// signs to authorize a key rotation.
///
/// The owner signs:
///   { domain: "rotate_owner_key_v1",
///     prior_active_pubkey: Bytes(32),  // the key being retired
///     new_pubkey: Bytes(32),            // the key taking over
///     anchor_timestamp_unix_seconds: Uint,
///     anchor_nonce: Bytes(32) }
///
/// Per L1/GOVERNANCE §3.1 the FULL rotation FSM requires (1) publish-new-
/// at-anchor signed by current key, (2) 30-day cooldown veto window,
/// (3) post-cooldown dual cosign by both keys. Sprint 7.F ships the
/// MINIMUM viable rotation: single-signature by the current key
/// authorizes the rotation; the 30-day window + dual cosign are
/// **Sprint 7.F.2 follow-up** acknowledged debt. Even MVP closes the
/// "no key rotation possible at all" gap.
pub fn build_rotate_owner_key_canonical_bytes(
    prior_active_pubkey: &[u8; 32],
    new_pubkey: &[u8; 32],
    anchor_timestamp_unix_seconds: u64,
    anchor_nonce: &[u8; 32],
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(ROTATE_OWNER_KEY_DOMAIN.to_string()),
    );
    m.insert(
        "prior_active_pubkey".to_string(),
        Value::Bytes(prior_active_pubkey.to_vec()),
    );
    m.insert(
        "new_pubkey".to_string(),
        Value::Bytes(new_pubkey.to_vec()),
    );
    m.insert(
        "anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(anchor_timestamp_unix_seconds),
    );
    m.insert(
        "anchor_nonce".to_string(),
        Value::Bytes(anchor_nonce.to_vec()),
    );
    cb_encode(&Value::Map(m))
        .expect("rotate_owner_key canonical-bytes encode infallible")
        .0
}

/// **v3.1.1 Sprint 7.F (T4.2)** — decode a rotate_owner_key envelope.
/// Returns `(prior_active_pubkey, new_pubkey, anchor_ts, anchor_nonce)`
/// on valid envelope; None on malformed bytes / wrong domain.
pub fn decode_rotate_owner_key(
    bytes: &[u8],
) -> Option<([u8; 32], [u8; 32], u64, [u8; 32])> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(bytes).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    match m.get("domain")? {
        Value::String(s) if s == ROTATE_OWNER_KEY_DOMAIN => {}
        _ => return None,
    }
    let prior = match m.get("prior_active_pubkey")? {
        Value::Bytes(b) if b.len() == 32 => {
            let mut a = [0u8; 32];
            a.copy_from_slice(b);
            a
        }
        _ => return None,
    };
    let new_pk = match m.get("new_pubkey")? {
        Value::Bytes(b) if b.len() == 32 => {
            let mut a = [0u8; 32];
            a.copy_from_slice(b);
            a
        }
        _ => return None,
    };
    let ts = match m.get("anchor_timestamp_unix_seconds")? {
        Value::Uint(t) => *t,
        _ => return None,
    };
    let nonce = match m.get("anchor_nonce")? {
        Value::Bytes(b) if b.len() == 32 => {
            let mut a = [0u8; 32];
            a.copy_from_slice(b);
            a
        }
        _ => return None,
    };
    Some((prior, new_pk, ts, nonce))
}

// ---- owner_key_added ----

/// Content of an owner_key_added event (M10 rotation: new key added):
/// ```text
/// Map({
///   "new_pubkey": Bytes(32),
///   "prior_active_pubkey": Bytes(32),
///   "anchor_timestamp_unix_seconds": Uint,
/// })
/// ```
pub fn encode_owner_key_added(
    new_pubkey: &[u8; 32],
    prior_active_pubkey: &[u8; 32],
    anchor_timestamp_unix_seconds: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("new_pubkey".to_string(), Value::Bytes(new_pubkey.to_vec()));
    m.insert(
        "prior_active_pubkey".to_string(),
        Value::Bytes(prior_active_pubkey.to_vec()),
    );
    m.insert(
        "anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(anchor_timestamp_unix_seconds),
    );
    cb_encode(&Value::Map(m)).expect("owner_key_added encode infallible")
}

// ---- owner_key_archived ----

/// Content of an owner_key_archived event:
/// ```text
/// Map({
///   "archived_pubkey": Bytes(32),
///   "anchor_timestamp_unix_seconds": Uint,
/// })
/// ```
pub fn encode_owner_key_archived(
    archived_pubkey: &[u8; 32],
    anchor_timestamp_unix_seconds: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "archived_pubkey".to_string(),
        Value::Bytes(archived_pubkey.to_vec()),
    );
    m.insert(
        "anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(anchor_timestamp_unix_seconds),
    );
    cb_encode(&Value::Map(m)).expect("owner_key_archived encode infallible")
}

// ---- nonce_issued ----

/// node_type: `nonce_issued:{nonce_hex_prefix}`.
pub fn nonce_issued_node_type(nonce: &[u8; 32]) -> String {
    format!("{}{}", NODE_TYPE_NONCE_ISSUED_PREFIX, hex_prefix(nonce, 8))
}

/// Content of a nonce_issued event (M13 + M15 dual-clock extension):
/// ```text
/// Map({
///   "nonce": Bytes(32),
///   "bound_content_hash": Bytes(32),
///   "bound_dag_tip": Bytes(32),
///   "substrate_issued_at_unix_ns": Timestamp,
///   "expiry_unix_ns": Timestamp,
///   "anchor_clock_issued_at_unix_ns": Timestamp [optional; dual-clock only],
///   "anchor_clock_expiry_unix_ns": Timestamp [optional; dual-clock only],
/// })
/// ```
#[allow(clippy::too_many_arguments)]
pub fn encode_nonce_issued(
    nonce: &[u8; 32],
    bound_content_hash: &[u8; 32],
    bound_dag_tip: &[u8; 32],
    substrate_issued_at_unix_ns: i64,
    expiry_unix_ns: i64,
    anchor_clock_issued_at_unix_ns: Option<i64>,
    anchor_clock_expiry_unix_ns: Option<i64>,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("nonce".to_string(), Value::Bytes(nonce.to_vec()));
    m.insert(
        "bound_content_hash".to_string(),
        Value::Bytes(bound_content_hash.to_vec()),
    );
    m.insert(
        "bound_dag_tip".to_string(),
        Value::Bytes(bound_dag_tip.to_vec()),
    );
    m.insert(
        "substrate_issued_at_unix_ns".to_string(),
        Value::Timestamp(substrate_issued_at_unix_ns),
    );
    m.insert(
        "expiry_unix_ns".to_string(),
        Value::Timestamp(expiry_unix_ns),
    );
    if let Some(t) = anchor_clock_issued_at_unix_ns {
        m.insert(
            "anchor_clock_issued_at_unix_ns".to_string(),
            Value::Timestamp(t),
        );
    }
    if let Some(t) = anchor_clock_expiry_unix_ns {
        m.insert(
            "anchor_clock_expiry_unix_ns".to_string(),
            Value::Timestamp(t),
        );
    }
    cb_encode(&Value::Map(m)).expect("nonce_issued encode infallible")
}

// ---- nonce_consumed ----

/// node_type: `nonce_consumed:{nonce_hex_prefix}`.
pub fn nonce_consumed_node_type(nonce: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_NONCE_CONSUMED_PREFIX,
        hex_prefix(nonce, 8)
    )
}

/// Content of a nonce_consumed event:
/// ```text
/// Map({ "nonce": Bytes(32), "consumed_at_unix_ns": Timestamp })
/// ```
pub fn encode_nonce_consumed(nonce: &[u8; 32], consumed_at_unix_ns: i64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("nonce".to_string(), Value::Bytes(nonce.to_vec()));
    m.insert(
        "consumed_at_unix_ns".to_string(),
        Value::Timestamp(consumed_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("nonce_consumed encode infallible")
}

// ---- nonce_expired ----

/// node_type: `nonce_expired:{nonce_hex_prefix}`.
pub fn nonce_expired_node_type(nonce: &[u8; 32]) -> String {
    format!("{}{}", NODE_TYPE_NONCE_EXPIRED_PREFIX, hex_prefix(nonce, 8))
}

/// Content of a nonce_expired event:
/// ```text
/// Map({ "nonce": Bytes(32), "expiry_unix_ns": Timestamp, "pruned_at_unix_ns": Timestamp })
/// ```
pub fn encode_nonce_expired(
    nonce: &[u8; 32],
    expiry_unix_ns: i64,
    pruned_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("nonce".to_string(), Value::Bytes(nonce.to_vec()));
    m.insert(
        "expiry_unix_ns".to_string(),
        Value::Timestamp(expiry_unix_ns),
    );
    m.insert(
        "pruned_at_unix_ns".to_string(),
        Value::Timestamp(pruned_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("nonce_expired encode infallible")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn float_repr_integer_valued() {
        assert_eq!(float_repr(0.0), "0.0");
        assert_eq!(float_repr(1.0), "1.0");
        assert_eq!(float_repr(-2.0), "-2.0");
    }

    #[test]
    fn float_repr_fractional() {
        assert_eq!(float_repr(2.5), "2.5");
        assert_eq!(float_repr(-0.125), "-0.125");
    }

    #[test]
    fn float_repr_special() {
        assert_eq!(float_repr(f64::NAN), "nan");
        assert_eq!(float_repr(f64::INFINITY), "inf");
        assert_eq!(float_repr(f64::NEG_INFINITY), "-inf");
    }

    #[test]
    fn hex_prefix_8_bytes() {
        let id = [0xab, 0xcd, 0xef, 0x01, 0x23, 0x45, 0x67, 0x89, 0xff, 0xee];
        assert_eq!(hex_prefix(&id, 8), "abcdef0123456789");
    }

    #[test]
    fn genesis_event_node_type_format() {
        let id = [0xab; 32];
        assert_eq!(
            genesis_event_node_type(&id),
            "genesis_event:abababababababab"
        );
    }

    #[test]
    fn encode_genesis_event_roundtrip() {
        use myco_kernel_shared::canonical_bytes::{decode, map_get_bytes};

        let id = [0x42; 32];
        let bytes = encode_genesis_event(&id, 1234567890);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert_eq!(map_get_bytes(&map, "substrate_id").unwrap(), &[0x42; 32]);
    }

    #[test]
    fn encode_axis_registered_includes_all_fields() {
        use myco_kernel_shared::canonical_bytes::{decode, map_get_bool, map_get_string};

        let event = AxisRegisteredEvent {
            name: "test_axis".to_string(),
            axis_class: "appetite".to_string(),
            fruiting_threshold: 10.0,
            initial_value: 0.0,
            decay_rate_per_cycle: 1.0,
            is_mortality_signal: false,
            update_rule_kind: "noop".to_string(),
        };
        let bytes = encode_axis_registered(&event);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert_eq!(map_get_string(&map, "name").unwrap(), "test_axis");
        assert_eq!(
            map_get_string(&map, "fruiting_threshold_repr").unwrap(),
            "10.0"
        );
        assert!(!map_get_bool(&map, "is_mortality_signal").unwrap());
    }

    #[test]
    fn encode_axis_perturbed_preserves_float_determinism() {
        use myco_kernel_shared::canonical_bytes::{decode, map_get_string};

        let bytes1 = encode_axis_perturbed("x", 2.5);
        let bytes2 = encode_axis_perturbed("x", 2.5);
        // Determinism: same inputs → identical canonical bytes.
        assert_eq!(bytes1.as_ref(), bytes2.as_ref());

        let decoded = decode(bytes1.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert_eq!(map_get_string(&map, "delta_repr").unwrap(), "2.5");
        assert_eq!(map_get_string(&map, "axis_name").unwrap(), "x");
    }

    #[test]
    fn encode_nonce_issued_with_dual_clock_includes_anchor_fields() {
        use myco_kernel_shared::canonical_bytes::{decode, Value};

        let nonce = [0x01; 32];
        let content_hash = [0x02; 32];
        let dag_tip = [0x03; 32];
        let bytes = encode_nonce_issued(
            &nonce,
            &content_hash,
            &dag_tip,
            1000,
            301000,
            Some(2000),
            Some(302000),
        );
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert!(matches!(
            map.get("anchor_clock_issued_at_unix_ns"),
            Some(Value::Timestamp(2000))
        ));
        assert!(matches!(
            map.get("anchor_clock_expiry_unix_ns"),
            Some(Value::Timestamp(302000))
        ));
    }

    #[test]
    fn encode_nonce_issued_without_dual_clock_omits_anchor_fields() {
        use myco_kernel_shared::canonical_bytes::decode;

        let nonce = [0x01; 32];
        let bytes = encode_nonce_issued(&nonce, &[0; 32], &[0; 32], 1000, 301000, None, None);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert!(!map.contains_key("anchor_clock_issued_at_unix_ns"));
        assert!(!map.contains_key("anchor_clock_expiry_unix_ns"));
    }

    #[test]
    fn node_type_suffixes_are_consistent() {
        // Per-axis events use the same suffix conventions.
        assert_eq!(axis_registered_node_type("x"), "axis_registered:x");
        assert_eq!(axis_perturbed_node_type("x"), "axis_perturbed:x");
        assert_eq!(axis_reset_node_type("x"), "axis_reset_after_fruiting:x");
    }

    #[test]
    fn nonce_event_node_types_use_8_byte_hex_prefix() {
        let nonce = [0xde, 0xad, 0xbe, 0xef, 0xca, 0xfe, 0xba, 0xbe, 0xff, 0xee];
        assert_eq!(
            nonce_issued_node_type(&{
                let mut a = [0u8; 32];
                a[..10].copy_from_slice(&nonce);
                a
            }),
            "nonce_issued:deadbeefcafebabe"
        );
    }
}
