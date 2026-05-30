//! M22 federation event types (P5 inter-substrate) + birth-period quarantine
//! + self-euthanasia execution events.

use super::hex_prefix;
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

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
