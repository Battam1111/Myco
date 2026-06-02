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

/// **C13 (2026-06-02) — local federation peer revocation** (L1/GOVERNANCE §5.2
/// + FEDERATION §6.5.b per-peer OWNER revocation). Prefix for
/// `federation_peer_revoked:{first_8_hex_of_revoked_peer_substrate_id}` DAG
/// events. Each event is an owner-attested CRL entry: the owner co-signs a
/// revocation body (see [`build_revoke_federation_peer_canonical_bytes`]); the
/// substrate records the body + the owner signature + owner pubkey so the
/// entry is independently re-verifiable offline and re-derivable on boot
/// (see [`derive_revoked_federation_peers_from_dag`]).
///
/// SCOPE: this is the LOCAL owner-revocation half of FEDERATION §6.5.b. The
/// quorum-revocation half (≥2/3 Byzantine consensus at ≥3 peers, GOVERNANCE
/// §5.2 "P15 consensus floor") is DEFERRED — it needs the as-yet-absent PBFT
/// consensus layer + anchor-resident revocation list + outbound
/// negative-revocation proofs.
pub const NODE_TYPE_FEDERATION_PEER_REVOKED_PREFIX: &str = "federation_peer_revoked:";

/// **C13** domain string for the owner-signed federation-peer-revocation body
/// (binds the signature to this purpose so a signature over some other CI
/// envelope cannot be replayed as a revocation, and vice-versa).
pub const REVOKE_FEDERATION_PEER_DOMAIN: &str = "myco-federation-peer-revoke-v1";

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

// ---------------------------------------------------------------------------
// C13 — local federation peer revocation (owner-attested CRL).
//
// The flow (mirrors the M-anchor-5 dag_tip_cosign / l0_revision_attest staged-
// envelope pattern in `attestation.rs::handle_submit_mutation`):
//
//   1. Owner builds the revocation BODY via
//      `build_revoke_federation_peer_canonical_bytes` and signs it. That body
//      is submitted as the `revoke_federation_peer` CI mutation's
//      `content_canonical_bytes`; the signature is `attestation_signature`.
//   2. The Python classifier (rule `revoke_federation_peer_mutation`) grades it
//      CI and verifies the signature against the active owner key. An
//      unattested / bad-signature revoke is rejected `accepted=false`
//      classification=`contract_identity_level` → the substrate maps that to
//      **C5 attestation_invalid** (no new row minted).
//   3. On accept, the substrate decodes the body, captures the owner signature
//      + pinned owner pubkey, and AFTER the `mutation:revoke_federation_peer`
//      DAG node commits, emits one `federation_peer_revoked:{prefix}` event
//      carrying body-fields + signature + pubkey, and inserts the target into
//      the in-memory revoked-set. Idempotent: re-revoking an already-revoked
//      peer is a no-op (HashSet insert + content-hash-idempotent DAG insert).
// ---------------------------------------------------------------------------

/// node_type for a `federation_peer_revoked` event (C13):
/// `federation_peer_revoked:{first_8_hex_of_revoked_peer_substrate_id}`.
pub fn federation_peer_revoked_node_type(revoked_peer_substrate_id: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_FEDERATION_PEER_REVOKED_PREFIX,
        hex_prefix(revoked_peer_substrate_id, 8)
    )
}

/// **C13** — build the canonical-bytes BODY the owner signs to revoke a
/// federation peer. This is the `content_canonical_bytes` of the
/// `revoke_federation_peer` CI mutation; the owner's Ed25519 signature over
/// these exact bytes is the `attestation_signature`.
///
/// ```text
/// Map({
///   "domain": String,                                 // REVOKE_FEDERATION_PEER_DOMAIN
///   "revoked_peer_substrate_id": Bytes(32),
///   "revoked_pubkey": Bytes(32),                       // peer's pinned signing key (or zero if legacy)
///   "reason": String,
///   "anchor_timestamp_unix_seconds": Uint,             // owner anchor-clock seconds
/// })
/// ```
pub fn build_revoke_federation_peer_canonical_bytes(
    revoked_peer_substrate_id: &[u8; 32],
    revoked_pubkey: &[u8; 32],
    reason: &str,
    anchor_timestamp_unix_seconds: u64,
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(REVOKE_FEDERATION_PEER_DOMAIN.to_string()),
    );
    m.insert(
        "revoked_peer_substrate_id".to_string(),
        Value::Bytes(revoked_peer_substrate_id.to_vec()),
    );
    m.insert(
        "revoked_pubkey".to_string(),
        Value::Bytes(revoked_pubkey.to_vec()),
    );
    m.insert("reason".to_string(), Value::String(reason.to_string()));
    m.insert(
        "anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(anchor_timestamp_unix_seconds),
    );
    cb_encode(&Value::Map(m))
        .expect("revoke_federation_peer body encode infallible")
        .0
}

/// **C13** — decode a `revoke_federation_peer` body (the owner-signed
/// `content_canonical_bytes`). Returns
/// `(revoked_peer_substrate_id, revoked_pubkey, reason, anchor_timestamp_unix_seconds)`
/// or `None` if the shape / domain is wrong (→ caller rejects with C5).
#[allow(clippy::type_complexity)]
pub fn decode_revoke_federation_peer(
    bytes: &[u8],
) -> Option<([u8; 32], [u8; 32], String, u64)> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    match m.get("domain")? {
        Value::String(s) if s == REVOKE_FEDERATION_PEER_DOMAIN => {}
        _ => return None,
    }
    let revoked_peer_substrate_id = bytes_to_arr32(m.get("revoked_peer_substrate_id")?)?;
    let revoked_pubkey = bytes_to_arr32(m.get("revoked_pubkey")?)?;
    let reason = match m.get("reason")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let anchor_timestamp_unix_seconds = match m.get("anchor_timestamp_unix_seconds")? {
        Value::Uint(u) => *u,
        _ => return None,
    };
    Some((
        revoked_peer_substrate_id,
        revoked_pubkey,
        reason,
        anchor_timestamp_unix_seconds,
    ))
}

/// **C13** — content of a `federation_peer_revoked` DAG event (the on-chain
/// owner-attested CRL entry). The first four fields are the owner-signed body
/// fields; `owner_signature` + `owner_pubkey` are the attestation captured at
/// accept time so the entry is independently re-verifiable offline.
///
/// ```text
/// Map({
///   "revoked_peer_substrate_id": Bytes(32),
///   "revoked_pubkey": Bytes(32),
///   "reason": String,
///   "anchor_timestamp_unix_seconds": Uint,
///   "owner_signature": Bytes(64),
///   "owner_pubkey": Bytes(32),
/// })
/// ```
pub fn encode_federation_peer_revoked(
    revoked_peer_substrate_id: &[u8; 32],
    revoked_pubkey: &[u8; 32],
    reason: &str,
    anchor_timestamp_unix_seconds: u64,
    owner_signature: &[u8; 64],
    owner_pubkey: &[u8; 32],
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "revoked_peer_substrate_id".to_string(),
        Value::Bytes(revoked_peer_substrate_id.to_vec()),
    );
    m.insert(
        "revoked_pubkey".to_string(),
        Value::Bytes(revoked_pubkey.to_vec()),
    );
    m.insert("reason".to_string(), Value::String(reason.to_string()));
    m.insert(
        "anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(anchor_timestamp_unix_seconds),
    );
    m.insert(
        "owner_signature".to_string(),
        Value::Bytes(owner_signature.to_vec()),
    );
    m.insert(
        "owner_pubkey".to_string(),
        Value::Bytes(owner_pubkey.to_vec()),
    );
    cb_encode(&Value::Map(m)).expect("federation_peer_revoked encode infallible")
}

/// **C13** — extract the `revoked_peer_substrate_id` from a
/// `federation_peer_revoked` DAG event's content. Returns `None` if the content
/// is malformed (such an event never entered the DAG via the legitimate path,
/// so this only guards against a corrupt/hand-crafted node — it is simply
/// skipped during derivation rather than treated as a revocation).
pub fn decode_federation_peer_revoked_target(bytes: &[u8]) -> Option<[u8; 32]> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    bytes_to_arr32(m.get("revoked_peer_substrate_id")?)
}

/// **C13** — re-derive the in-memory revoked-federation-peer set from the DAG.
///
/// Called once at boot (mirrors `derive_backup_encryption_status_from_dag`)
/// and never again — `emit_federation_peer_revoked` keeps the live set current
/// thereafter. A single in-insertion-order walk collecting every
/// `federation_peer_revoked:*` event's target; O(N) over the DAG, no
/// per-event allocation beyond the set itself. There is no un-revoke event by
/// design (a CRL only grows; an owner who pinned the same peer afresh would do
/// so under a new substrate_id), so the set is purely additive.
pub fn derive_revoked_federation_peers_from_dag(
    dag: &myco_kernel_schema::dag::Dag,
) -> std::collections::HashSet<[u8; 32]> {
    let mut revoked = std::collections::HashSet::new();
    for node in dag.iter_in_insertion_order() {
        if !node
            .node_type
            .starts_with(NODE_TYPE_FEDERATION_PEER_REVOKED_PREFIX)
        {
            continue;
        }
        if let Some(target) =
            decode_federation_peer_revoked_target(node.content_canonical_bytes.as_ref())
        {
            revoked.insert(target);
        }
    }
    revoked
}

/// Local helper: coerce a canonical-bytes `Value` into a `[u8; 32]` (used by
/// the C13 decoders). Returns `None` for non-`Bytes` or wrong-length values.
fn bytes_to_arr32(v: &Value) -> Option<[u8; 32]> {
    match v {
        Value::Bytes(b) if b.len() == 32 => {
            let mut a = [0u8; 32];
            a.copy_from_slice(b);
            Some(a)
        }
        _ => None,
    }
}

#[cfg(test)]
mod c13_revocation_tests {
    //! **C13** — pure-function coverage for the federation-peer-revocation
    //! encode/decode/derive surface (the security-critical parsing path).
    use super::*;
    use myco_kernel_schema::dag::Dag;
    use myco_kernel_shared::canonical_bytes::CanonicalBytes;

    #[test]
    fn revoke_body_roundtrips_with_domain() {
        let revoked_id = [0x11u8; 32];
        let revoked_pk = [0x22u8; 32];
        let bytes = build_revoke_federation_peer_canonical_bytes(
            &revoked_id,
            &revoked_pk,
            "manual revoke",
            1_700_000_123,
        );
        let (id, pk, reason, ts) =
            decode_revoke_federation_peer(&bytes).expect("body decodes");
        assert_eq!(id, revoked_id);
        assert_eq!(pk, revoked_pk);
        assert_eq!(reason, "manual revoke");
        assert_eq!(ts, 1_700_000_123);
    }

    #[test]
    fn revoke_body_rejects_wrong_domain() {
        // A well-formed Map with the WRONG domain must not decode (prevents a
        // signature over some other CI envelope being replayed as a revoke).
        let mut m = BTreeMap::new();
        m.insert(
            "domain".to_string(),
            Value::String("not-the-revoke-domain".to_string()),
        );
        m.insert(
            "revoked_peer_substrate_id".to_string(),
            Value::Bytes(vec![0x11; 32]),
        );
        m.insert("revoked_pubkey".to_string(), Value::Bytes(vec![0x22; 32]));
        m.insert("reason".to_string(), Value::String("x".to_string()));
        m.insert(
            "anchor_timestamp_unix_seconds".to_string(),
            Value::Uint(1),
        );
        let bytes = cb_encode(&Value::Map(m)).unwrap().0;
        assert!(
            decode_revoke_federation_peer(&bytes).is_none(),
            "wrong-domain body must not decode as a revocation"
        );
    }

    #[test]
    fn revoke_body_rejects_garbage_and_wrong_shapes() {
        assert!(decode_revoke_federation_peer(&[0xff, 0x00, 0x13]).is_none());
        // Missing required field (revoked_pubkey).
        let mut m = BTreeMap::new();
        m.insert(
            "domain".to_string(),
            Value::String(REVOKE_FEDERATION_PEER_DOMAIN.to_string()),
        );
        m.insert(
            "revoked_peer_substrate_id".to_string(),
            Value::Bytes(vec![0x11; 32]),
        );
        let bytes = cb_encode(&Value::Map(m)).unwrap().0;
        assert!(decode_revoke_federation_peer(&bytes).is_none());
    }

    #[test]
    fn event_content_target_extracts() {
        let revoked_id = [0xabu8; 32];
        let content = encode_federation_peer_revoked(
            &revoked_id,
            &[0u8; 32],
            "r",
            1,
            &[0x5a; 64],
            &[0x6b; 32],
        );
        assert_eq!(
            decode_federation_peer_revoked_target(content.as_ref()),
            Some(revoked_id)
        );
    }

    #[test]
    fn node_type_prefix_matches() {
        let nt = federation_peer_revoked_node_type(&[0xde, 0xad, 0xbe, 0xef, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
        assert!(nt.starts_with(NODE_TYPE_FEDERATION_PEER_REVOKED_PREFIX));
        assert_eq!(nt, "federation_peer_revoked:deadbeef00000000");
    }

    #[test]
    fn derive_collects_all_distinct_targets_skips_malformed() {
        let mut dag = Dag::new();
        let id_a = [0x01u8; 32];
        let id_b = [0x02u8; 32];
        // Two distinct revocations.
        let tip = dag
            .insert_node(
                Vec::new(),
                federation_peer_revoked_node_type(&id_a),
                0,
                encode_federation_peer_revoked(&id_a, &[0u8; 32], "a", 1, &[0u8; 64], &[0u8; 32]),
            )
            .unwrap();
        let tip = dag
            .insert_node(
                vec![tip],
                federation_peer_revoked_node_type(&id_b),
                0,
                encode_federation_peer_revoked(&id_b, &[0u8; 32], "b", 1, &[0u8; 64], &[0u8; 32]),
            )
            .unwrap();
        // A malformed node under the same prefix → skipped, not treated as a
        // revocation.
        let _ = dag
            .insert_node(
                vec![tip],
                format!("{NODE_TYPE_FEDERATION_PEER_REVOKED_PREFIX}cccccccc"),
                0,
                CanonicalBytes(vec![0xff, 0x00]),
            )
            .unwrap();

        let revoked = derive_revoked_federation_peers_from_dag(&dag);
        assert_eq!(revoked.len(), 2, "two distinct valid targets");
        assert!(revoked.contains(&id_a));
        assert!(revoked.contains(&id_b));
    }

    #[test]
    fn derive_empty_dag_is_empty_set() {
        let dag = Dag::new();
        assert!(derive_revoked_federation_peers_from_dag(&dag).is_empty());
    }
}
