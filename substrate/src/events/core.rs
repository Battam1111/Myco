//! Core M21 substrate event vocabulary: genesis / cycle / axis / operator /
//! owner_key / nonce — plus the shared float-repr + hex-prefix utilities used
//! by every domain.

use myco_kernel_shared::canonical_bytes::{
    encode as cb_encode, float_repr as shared_float_repr, CanonicalBytes, Value,
};
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

/// **C70** — owner key-rotation REQUEST event (L1/GOVERNANCE §3.1). Emitted
/// when the current owner publishes a new candidate (current-key-signed); opens
/// the 30-day cooldown veto window. The DAG-derived `pending_owner_key_rotation`
/// reads the latest such event not followed by an activation/veto.
pub const NODE_TYPE_OWNER_KEY_ROTATION_REQUESTED: &str = "owner_key_rotation_requested";

/// **C70** — owner key-rotation VETO event (L1/GOVERNANCE §3.1). Emitted when a
/// pre-registered key vetoes a pending rotation within the cooldown window; the
/// candidate is discarded and the pending rotation cleared.
pub const NODE_TYPE_OWNER_KEY_ROTATION_VETOED: &str = "owner_key_rotation_vetoed";

/// Prefix for nonce_issued events.
pub const NODE_TYPE_NONCE_ISSUED_PREFIX: &str = "nonce_issued:";

/// Prefix for nonce_consumed events.
pub const NODE_TYPE_NONCE_CONSUMED_PREFIX: &str = "nonce_consumed:";

/// Prefix for nonce_expired events (TTL-based pruning).
pub const NODE_TYPE_NONCE_EXPIRED_PREFIX: &str = "nonce_expired:";

// ---------------------------------------------------------------------------
// Float repr utility — matches kernel/bridge protocol's `float_repr` convention.
// ---------------------------------------------------------------------------

/// Format an f64 as a Python-compatible repr string for cross-platform
/// deterministic event encoding.
///
/// **Single source of truth**: delegates to
/// [`myco_kernel_shared::canonical_bytes::float_repr`], which reproduces CPython
/// `repr(float)` exactly (the canonical oracle). Re-exported here so the many
/// substrate event/observatory/ingest call sites keep importing
/// `crate::events::float_repr` unchanged. See the shared implementation for the
/// algorithm and the L1/HARD_RULES C18 (`canonical_bytes_render_drift`)
/// rationale.
pub fn float_repr(f: f64) -> String {
    shared_float_repr(f)
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

/// Content of a genesis_event:
/// ```text
/// Map({
///   "substrate_id": Bytes(32),
///   "genesis_time_unix_ns": Timestamp,
///   "generation_depth": Uint,   // 8f / §16.A; OMITTED when 0 (root)
/// })
/// ```
///
/// **8f / L1/GOVERNANCE §16.A (F22)**: `generation_depth` records this
/// substrate's lineage depth (root = 0; a sprouted child = parent + 1). It
/// is the authoritative carrier the child reads at boot via
/// `DerivedState::apply_genesis` → `Manifest.generation_depth`, which the C47
/// reproduction detector then enforces against `reproduction_lineage_depth_max`.
///
/// **Back-compat / determinism**: the field is emitted ONLY when non-zero so a
/// root substrate's genesis_event canonical-bytes (and therefore its DAG hash
/// chain + the v3.1.1.1 seal) are byte-identical to the pre-8f encoding. A
/// decoder that has never seen the field treats its absence as 0 (root).
pub fn encode_genesis_event(
    substrate_id: &[u8; 32],
    genesis_time_unix_ns: i64,
    generation_depth: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "substrate_id".to_string(),
        Value::Bytes(substrate_id.to_vec()),
    );
    m.insert(
        "genesis_time_unix_ns".to_string(),
        Value::Timestamp(genesis_time_unix_ns),
    );
    if generation_depth != 0 {
        m.insert(
            "generation_depth".to_string(),
            Value::Uint(generation_depth),
        );
    }
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

// ---- C70 phased rotate_owner_key envelopes (L1/GOVERNANCE §3.1) ----
//
// The legacy `build_rotate_owner_key_canonical_bytes` above is the single-shot
// MVP envelope and stays BYTE-IDENTICAL (its roundtrip test pins it). C70 adds
// the 3-phase FSM. The phased envelopes reuse the `rotate_owner_key_v1` domain
// but carry a `phase` discriminator ("request" | "veto" | "activate"); the
// presence of `phase` is what distinguishes a phased envelope from the legacy
// one. Each phase decodes via a dedicated function returning its own tuple.
//
// Phase byte-layouts (canonical-bytes Maps; keys sorted by the cb encoder):
//   request:  { domain, phase:"request", prior_active_pubkey, new_pubkey,
//               request_anchor_timestamp_unix_seconds, cooldown_expires_at_unix_seconds,
//               anchor_nonce }
//   veto:     { domain, phase:"veto", new_pubkey,
//               veto_anchor_timestamp_unix_seconds, anchor_nonce }
//   activate: <activate-core> + { new_key_cosignature: Bytes(64) }
//     activate-core: { domain, phase:"activate", prior_active_pubkey, new_pubkey,
//               request_anchor_timestamp_unix_seconds, cooldown_expires_at_unix_seconds,
//               activate_anchor_timestamp_unix_seconds, anchor_nonce }
//
// Dual-cosign discipline (activate): the NEW key signs the activate-CORE (which
// excludes its own signature); the OLD key signs the FULL activate envelope
// (core + new_key_cosignature) via the operator `attestation_signature` that
// Python's CI gate already verifies against the active owner key. The substrate
// reconstructs the core deterministically + verifies the new-key cosignature.

/// Phase discriminator value for a rotation request envelope.
pub const ROTATE_PHASE_REQUEST: &str = "request";
/// Phase discriminator value for a rotation veto envelope.
pub const ROTATE_PHASE_VETO: &str = "veto";
/// Phase discriminator value for a rotation activate envelope.
pub const ROTATE_PHASE_ACTIVATE: &str = "activate";

/// Extract the `phase` discriminator from a (possibly phased) rotate envelope.
/// Returns `None` for the legacy single-shot envelope (no `phase` field) or a
/// non-rotate / malformed envelope.
pub fn rotate_owner_key_phase(bytes: &[u8]) -> Option<String> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    match m.get("domain")? {
        Value::String(s) if s == ROTATE_OWNER_KEY_DOMAIN => {}
        _ => return None,
    }
    match m.get("phase")? {
        Value::String(s) => Some(s.clone()),
        _ => None,
    }
}

/// Build the canonical-bytes a current owner signs to REQUEST a rotation (C70).
/// The current owner's `attestation_signature` over these bytes is verified by
/// Python's CI gate against the active owner key.
pub fn build_rotate_owner_key_request(
    prior_active_pubkey: &[u8; 32],
    new_pubkey: &[u8; 32],
    request_anchor_timestamp_unix_seconds: u64,
    cooldown_expires_at_unix_seconds: u64,
    anchor_nonce: &[u8; 32],
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert("domain".to_string(), Value::String(ROTATE_OWNER_KEY_DOMAIN.to_string()));
    m.insert("phase".to_string(), Value::String(ROTATE_PHASE_REQUEST.to_string()));
    m.insert("prior_active_pubkey".to_string(), Value::Bytes(prior_active_pubkey.to_vec()));
    m.insert("new_pubkey".to_string(), Value::Bytes(new_pubkey.to_vec()));
    m.insert(
        "request_anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(request_anchor_timestamp_unix_seconds),
    );
    m.insert(
        "cooldown_expires_at_unix_seconds".to_string(),
        Value::Uint(cooldown_expires_at_unix_seconds),
    );
    m.insert("anchor_nonce".to_string(), Value::Bytes(anchor_nonce.to_vec()));
    cb_encode(&Value::Map(m))
        .expect("rotate_owner_key request canonical-bytes encode infallible")
        .0
}

/// Decoded rotation REQUEST envelope:
/// `(prior_active_pubkey, new_pubkey, request_anchor_ts, cooldown_expires_at, anchor_nonce)`.
pub fn decode_rotate_owner_key_request(
    bytes: &[u8],
) -> Option<([u8; 32], [u8; 32], u64, u64, [u8; 32])> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    expect_domain_phase(&m, ROTATE_PHASE_REQUEST)?;
    let prior = map_bytes32(&m, "prior_active_pubkey")?;
    let new_pk = map_bytes32(&m, "new_pubkey")?;
    let request_ts = map_uint(&m, "request_anchor_timestamp_unix_seconds")?;
    let cooldown = map_uint(&m, "cooldown_expires_at_unix_seconds")?;
    let nonce = map_bytes32(&m, "anchor_nonce")?;
    Some((prior, new_pk, request_ts, cooldown, nonce))
}

/// Build the canonical-bytes a pre-registered owner signs to VETO a pending
/// rotation (C70). Binds to the pending rotation's `new_pubkey`. Python's CI
/// gate verifies the `attestation_signature` over these bytes against the
/// currently-active owner key (during cooldown, the old key is the only
/// currently-valid key — exactly the legitimate vetoer).
pub fn build_rotate_owner_key_veto(
    new_pubkey: &[u8; 32],
    veto_anchor_timestamp_unix_seconds: u64,
    anchor_nonce: &[u8; 32],
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert("domain".to_string(), Value::String(ROTATE_OWNER_KEY_DOMAIN.to_string()));
    m.insert("phase".to_string(), Value::String(ROTATE_PHASE_VETO.to_string()));
    m.insert("new_pubkey".to_string(), Value::Bytes(new_pubkey.to_vec()));
    m.insert(
        "veto_anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(veto_anchor_timestamp_unix_seconds),
    );
    m.insert("anchor_nonce".to_string(), Value::Bytes(anchor_nonce.to_vec()));
    cb_encode(&Value::Map(m))
        .expect("rotate_owner_key veto canonical-bytes encode infallible")
        .0
}

/// Decoded rotation VETO envelope: `(new_pubkey, veto_anchor_ts, anchor_nonce)`.
pub fn decode_rotate_owner_key_veto(bytes: &[u8]) -> Option<([u8; 32], u64, [u8; 32])> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    expect_domain_phase(&m, ROTATE_PHASE_VETO)?;
    let new_pk = map_bytes32(&m, "new_pubkey")?;
    let veto_ts = map_uint(&m, "veto_anchor_timestamp_unix_seconds")?;
    let nonce = map_bytes32(&m, "anchor_nonce")?;
    Some((new_pk, veto_ts, nonce))
}

/// Build the activate-CORE canonical-bytes — the bytes the NEW key co-signs.
/// Excludes `new_key_cosignature` so the new key can sign before the cosignature
/// exists. Both keys ultimately attest to this same core (the old key signs the
/// full envelope that wraps it).
pub fn build_rotate_owner_key_activate_core(
    prior_active_pubkey: &[u8; 32],
    new_pubkey: &[u8; 32],
    request_anchor_timestamp_unix_seconds: u64,
    cooldown_expires_at_unix_seconds: u64,
    activate_anchor_timestamp_unix_seconds: u64,
    anchor_nonce: &[u8; 32],
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert("domain".to_string(), Value::String(ROTATE_OWNER_KEY_DOMAIN.to_string()));
    m.insert("phase".to_string(), Value::String(ROTATE_PHASE_ACTIVATE.to_string()));
    m.insert("prior_active_pubkey".to_string(), Value::Bytes(prior_active_pubkey.to_vec()));
    m.insert("new_pubkey".to_string(), Value::Bytes(new_pubkey.to_vec()));
    m.insert(
        "request_anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(request_anchor_timestamp_unix_seconds),
    );
    m.insert(
        "cooldown_expires_at_unix_seconds".to_string(),
        Value::Uint(cooldown_expires_at_unix_seconds),
    );
    m.insert(
        "activate_anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(activate_anchor_timestamp_unix_seconds),
    );
    m.insert("anchor_nonce".to_string(), Value::Bytes(anchor_nonce.to_vec()));
    cb_encode(&Value::Map(m))
        .expect("rotate_owner_key activate-core canonical-bytes encode infallible")
        .0
}

/// Build the FULL activate envelope = activate-core + `new_key_cosignature`.
/// The OLD key signs THIS (via the operator `attestation_signature`).
pub fn build_rotate_owner_key_activate(
    prior_active_pubkey: &[u8; 32],
    new_pubkey: &[u8; 32],
    request_anchor_timestamp_unix_seconds: u64,
    cooldown_expires_at_unix_seconds: u64,
    activate_anchor_timestamp_unix_seconds: u64,
    anchor_nonce: &[u8; 32],
    new_key_cosignature: &[u8; 64],
) -> Vec<u8> {
    // Decode the core back into a Map, append the cosignature, re-encode. This
    // guarantees the embedded core is byte-identical to what the new key signed.
    use myco_kernel_shared::canonical_bytes::decode;
    let core = build_rotate_owner_key_activate_core(
        prior_active_pubkey,
        new_pubkey,
        request_anchor_timestamp_unix_seconds,
        cooldown_expires_at_unix_seconds,
        activate_anchor_timestamp_unix_seconds,
        anchor_nonce,
    );
    let mut m = match decode(&core).expect("activate-core decodes") {
        Value::Map(m) => m,
        _ => unreachable!("activate-core is a Map"),
    };
    m.insert(
        "new_key_cosignature".to_string(),
        Value::Bytes(new_key_cosignature.to_vec()),
    );
    cb_encode(&Value::Map(m))
        .expect("rotate_owner_key activate canonical-bytes encode infallible")
        .0
}

/// Decoded rotation ACTIVATE envelope:
/// `(prior_active_pubkey, new_pubkey, request_anchor_ts, cooldown_expires_at,
///   activate_anchor_ts, anchor_nonce, new_key_cosignature, activate_core_bytes)`.
/// `activate_core_bytes` is the reconstructed core the new key must have signed,
/// returned so the caller can verify `new_key_cosignature` against `new_pubkey`.
#[allow(clippy::type_complexity)]
pub fn decode_rotate_owner_key_activate(
    bytes: &[u8],
) -> Option<([u8; 32], [u8; 32], u64, u64, u64, [u8; 32], [u8; 64], Vec<u8>)> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    expect_domain_phase(&m, ROTATE_PHASE_ACTIVATE)?;
    let prior = map_bytes32(&m, "prior_active_pubkey")?;
    let new_pk = map_bytes32(&m, "new_pubkey")?;
    let request_ts = map_uint(&m, "request_anchor_timestamp_unix_seconds")?;
    let cooldown = map_uint(&m, "cooldown_expires_at_unix_seconds")?;
    let activate_ts = map_uint(&m, "activate_anchor_timestamp_unix_seconds")?;
    let nonce = map_bytes32(&m, "anchor_nonce")?;
    let cosig = match m.get("new_key_cosignature")? {
        Value::Bytes(b) if b.len() == 64 => {
            let mut a = [0u8; 64];
            a.copy_from_slice(b);
            a
        }
        _ => return None,
    };
    // Reconstruct the core (without the cosignature) so the caller can verify
    // the new-key cosignature over the EXACT bytes the new key signed.
    let core = build_rotate_owner_key_activate_core(
        &prior,
        &new_pk,
        request_ts,
        cooldown,
        activate_ts,
        &nonce,
    );
    Some((prior, new_pk, request_ts, cooldown, activate_ts, nonce, cosig, core))
}

// ---- shared phased-envelope field extractors ----

fn expect_domain_phase(m: &BTreeMap<String, Value>, phase: &str) -> Option<()> {
    match m.get("domain")? {
        Value::String(s) if s == ROTATE_OWNER_KEY_DOMAIN => {}
        _ => return None,
    }
    match m.get("phase")? {
        Value::String(s) if s == phase => Some(()),
        _ => None,
    }
}

fn map_bytes32(m: &BTreeMap<String, Value>, key: &str) -> Option<[u8; 32]> {
    match m.get(key)? {
        Value::Bytes(b) if b.len() == 32 => {
            let mut a = [0u8; 32];
            a.copy_from_slice(b);
            Some(a)
        }
        _ => None,
    }
}

fn map_uint(m: &BTreeMap<String, Value>, key: &str) -> Option<u64> {
    match m.get(key)? {
        Value::Uint(u) => Some(*u),
        _ => None,
    }
}

// ---- C70 rotation event encoders (owner_key_rotation_requested / _vetoed) ----

/// Content of an `owner_key_rotation_requested` event (C70):
/// ```text
/// Map({ "new_pubkey": Bytes(32), "prior_active_pubkey": Bytes(32),
///       "request_anchor_timestamp_unix_seconds": Uint,
///       "cooldown_expires_at_unix_seconds": Uint })
/// ```
pub fn encode_owner_key_rotation_requested(
    new_pubkey: &[u8; 32],
    prior_active_pubkey: &[u8; 32],
    request_anchor_timestamp_unix_seconds: u64,
    cooldown_expires_at_unix_seconds: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("new_pubkey".to_string(), Value::Bytes(new_pubkey.to_vec()));
    m.insert(
        "prior_active_pubkey".to_string(),
        Value::Bytes(prior_active_pubkey.to_vec()),
    );
    m.insert(
        "request_anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(request_anchor_timestamp_unix_seconds),
    );
    m.insert(
        "cooldown_expires_at_unix_seconds".to_string(),
        Value::Uint(cooldown_expires_at_unix_seconds),
    );
    cb_encode(&Value::Map(m)).expect("owner_key_rotation_requested encode infallible")
}

/// Decode the `(new_pubkey, prior_active_pubkey, request_anchor_ts, cooldown_expires_at)`
/// tuple from an `owner_key_rotation_requested` event body. Used by the
/// DAG-derivation of `pending_owner_key_rotation` at boot.
pub fn decode_owner_key_rotation_requested(
    bytes: &[u8],
) -> Option<([u8; 32], [u8; 32], u64, u64)> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    let new_pk = map_bytes32(&m, "new_pubkey")?;
    let prior = map_bytes32(&m, "prior_active_pubkey")?;
    let request_ts = map_uint(&m, "request_anchor_timestamp_unix_seconds")?;
    let cooldown = map_uint(&m, "cooldown_expires_at_unix_seconds")?;
    Some((new_pk, prior, request_ts, cooldown))
}

/// Content of an `owner_key_rotation_vetoed` event (C70):
/// ```text
/// Map({ "new_pubkey": Bytes(32), "veto_anchor_timestamp_unix_seconds": Uint })
/// ```
pub fn encode_owner_key_rotation_vetoed(
    new_pubkey: &[u8; 32],
    veto_anchor_timestamp_unix_seconds: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("new_pubkey".to_string(), Value::Bytes(new_pubkey.to_vec()));
    m.insert(
        "veto_anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(veto_anchor_timestamp_unix_seconds),
    );
    cb_encode(&Value::Map(m)).expect("owner_key_rotation_vetoed encode infallible")
}

// ---- C70 pending-rotation DAG projection ----

/// **C70** — an owner key-rotation in flight (PENDING_COOLDOWN). DAG-derived at
/// boot + kept current by the rotate handler. Mirrors `revoked_federation_peers`
/// / `duress_freeze_active`: the DAG is canonical; this is a pure projection.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PendingOwnerKeyRotation {
    /// The candidate key awaiting activation.
    pub new_pubkey: [u8; 32],
    /// The active owner key at request time (the key being retired).
    pub prior_active_pubkey: [u8; 32],
    /// Anchor-surface timestamp of the request.
    pub request_anchor_ts: u64,
    /// Anchor-surface timestamp at which the 30-day cooldown veto window elapses
    /// (== `request_anchor_ts + OWNER_KEY_ROTATION_COOLDOWN_SECS`). Activation
    /// before this instant is the C70 violation.
    pub cooldown_expires_at: u64,
    /// Substrate cycle counter at which the request was recorded.
    pub requested_at_cycle: u64,
}

/// **C70** — the cooldown veto window, in anchor-surface seconds (30 anchor-days).
/// The authoritative copy (the Python `COOLDOWN_ANCHOR_SECONDS` mirrors it for
/// pure-FSM unit tests). Per L1/GOVERNANCE §3.1 a freshly-requested rotation may
/// not activate until this window elapses.
pub const OWNER_KEY_ROTATION_COOLDOWN_SECS: u64 = 30 * 24 * 60 * 60; // 2_592_000

/// **C70** — derive the single in-flight pending rotation from the DAG, or
/// `None` if no rotation is pending. The rule: the LATEST
/// `owner_key_rotation_requested` event that is NOT followed (in insertion
/// order) by a terminal event — an `owner_key_added` (activation) OR an
/// `owner_key_rotation_vetoed`. A terminal event after a request clears it.
///
/// Strict last-writer FSM over the three event types, so a substrate restarted
/// mid-cooldown re-derives the pending rotation, and one restarted after
/// activation/veto re-derives `None` — the DAG is canonical. Single-in-flight is
/// guaranteed by the request handler (it refuses a second request while one is
/// pending), so at most one rotation is ever open at a time.
pub fn derive_pending_owner_key_rotation_from_dag(
    dag: &myco_kernel_schema::dag::Dag,
) -> Option<PendingOwnerKeyRotation> {
    let mut pending: Option<PendingOwnerKeyRotation> = None;
    for node in dag.iter_in_insertion_order() {
        if node.node_type == NODE_TYPE_OWNER_KEY_ROTATION_REQUESTED {
            if let Some((new_pk, prior, request_ts, cooldown)) =
                decode_owner_key_rotation_requested(node.content_canonical_bytes.as_ref())
            {
                pending = Some(PendingOwnerKeyRotation {
                    new_pubkey: new_pk,
                    prior_active_pubkey: prior,
                    request_anchor_ts: request_ts,
                    cooldown_expires_at: cooldown,
                    requested_at_cycle: node.created_at_cycle,
                });
            }
        } else if node.node_type == NODE_TYPE_OWNER_KEY_ROTATION_VETOED
            || node.node_type == NODE_TYPE_OWNER_KEY_ADDED
        {
            // Either terminal clears the in-flight rotation.
            pending = None;
        }
    }
    pending
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
        let bytes = encode_genesis_event(&id, 1234567890, 0);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert_eq!(map_get_bytes(&map, "substrate_id").unwrap(), &[0x42; 32]);
    }

    #[test]
    fn encode_genesis_event_root_omits_generation_depth() {
        // 8f back-compat: a root substrate (depth 0) must produce byte-identical
        // canonical-bytes to the pre-8f two-field encoding so the DAG hash
        // chain + v3.1.1.1 seal are unchanged. We assert the field is absent.
        use myco_kernel_shared::canonical_bytes::decode;
        let id = [0x42; 32];
        let bytes = encode_genesis_event(&id, 1234567890, 0);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert!(
            !map.contains_key("generation_depth"),
            "root genesis_event must omit generation_depth for byte-compat"
        );
    }

    #[test]
    fn encode_genesis_event_child_records_generation_depth() {
        // 8f / §16.A: a sprouted child (depth > 0) records the field so the
        // child can read its own lineage depth at boot.
        use myco_kernel_shared::canonical_bytes::{decode, Value};
        let id = [0x42; 32];
        let bytes = encode_genesis_event(&id, 1234567890, 7);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert!(matches!(
            map.get("generation_depth"),
            Some(Value::Uint(7))
        ));
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
