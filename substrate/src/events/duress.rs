//! **F23 / C50 (2026-06-02) — duress keypair coercion defense** event types.
//!
//! Doctrine: L2/TRUST_MODEL §10.A.2 (coerced Cultivator) + L1/GOVERNANCE F23
//! (`cultivator_duress_keypair_registrations`) + L0/cards/AS_anchor_surface.md
//! §5.6 / §8.4 (`duress_keypair_signature_observation`) + canonical dilemma
//! D-0047 (owner under duress signature).
//!
//! ## The mechanism
//!
//! The Cultivator pre-registers (at genesis, on a SEPARATE medium) one or more
//! `duress_keypair`s — each a distinct Ed25519 keypair, NOT the owner key. If
//! the Cultivator is ever coerced into authorizing a destructive CI mutation,
//! they sign the attestation with a duress key instead of the owner key. The
//! substrate then:
//!   1. completes the attestation **cosmetically** (the coercer sees an
//!      accepted-looking response — no rejection that would tip them off);
//!   2. does **NOT** commit the substantive mutation (no `mutation:*` effect);
//!   3. silently emits `coerced_owner_suspected` (C50) + `duress_signature_observed`
//!      (the real forensic record, hidden from the response);
//!   4. sets a freeze on destructive mutations, re-emitting C50 on each
//!      subsequent destructive CI while frozen, until an
//!      `out_of_band_safety_reattestation` (signed by the ACTIVE owner key —
//!      NEVER a duress key, the circular-trust guard) clears it.
//!
//! ## Why recognition is precise (the critical correctness property)
//!
//! Ed25519 signature verification succeeds under EXACTLY the public key whose
//! private key produced the signature. The owner key and every duress key are
//! DISJOINT keypairs (registration rejects a duress pubkey equal to the active
//! owner key — see `attestation::handle_submit_mutation`). Therefore a given
//! `attestation_signature` over `content_canonical_bytes` verifies under at
//! most one of {owner, any-single-duress-key} (collision probability is
//! cryptographically negligible). Consequences:
//!   - a **normal owner CI mutation** verifies under the owner key and under NO
//!     duress key → never mis-recognized as duress (a legit mutation is never
//!     silently dropped);
//!   - a **duress-key-signed mutation** verifies under a duress key and NOT the
//!     owner key → Python's owner-key CI gate rejects it AND the Rust duress
//!     trial-verify recognizes it → never treated as a normal owner sig.
//!
//! ## DAG-derived, byte-compat
//!
//! Like the C13 revoked-peer set, the registered-duress-pubkey set and the
//! freeze flag are in-memory projections re-derived at boot from the DAG (the
//! DAG is canonical). No new on-disk format, no snapshot bump. On a substrate
//! with zero registered duress keys every code path is inert, so non-duress
//! mutations are byte-unaffected.

use super::hex_prefix;
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

// ---------------------------------------------------------------------------
// node_type constants + prefixes.
// ---------------------------------------------------------------------------

/// Prefix for a `duress_keypair_registered:{first_8_hex_of_duress_pubkey}` DAG
/// event — the owner-attested registration record for one duress keypair. The
/// in-memory `duress_pubkeys` set is derived from these events at boot.
pub const NODE_TYPE_DURESS_KEYPAIR_REGISTERED_PREFIX: &str = "duress_keypair_registered:";

/// Prefix for a `duress_signature_observed:{first_8_hex_of_duress_pubkey}` DAG
/// event — the SILENT forensic record emitted when a submitted attestation
/// signature verified under a registered duress key. Hidden from the (cosmetic)
/// response; this is the real on-chain evidence. (AS §8.4.)
pub const NODE_TYPE_DURESS_SIGNATURE_OBSERVED_PREFIX: &str = "duress_signature_observed:";

/// node_type for the `coerced_owner_suspected` freeze-onset event (C50). Emitted
/// alongside the C50 immune sporocarp the first time a duress signature is
/// observed (and not yet cleared). Its presence-without-a-later-`duress_cleared`
/// is what `derive_duress_freeze_active_from_dag` reads as "frozen".
pub const NODE_TYPE_COERCED_OWNER_SUSPECTED: &str = "coerced_owner_suspected";

/// node_type for the `duress_cleared` event — emitted when an accepted
/// `out_of_band_safety_reattestation` (active-owner-key-signed) lifts the
/// freeze. Pairs with `coerced_owner_suspected` to form the freeze FSM.
pub const NODE_TYPE_DURESS_CLEARED: &str = "duress_cleared";

/// Domain string for the owner-signed `duress_keypair_registration` mutation
/// body (the `content_canonical_bytes` the owner signs to register a duress
/// pubkey). Disjoint from every other signing domain so a signature over a
/// different structure can never be replayed as a duress registration.
pub const DURESS_KEYPAIR_REGISTRATION_DOMAIN: &str = "myco-duress-keypair-registration-v1";

/// Domain string for the owner-signed `out_of_band_safety_reattestation`
/// mutation body (the unfreeze attestation). MUST be signed by the ACTIVE owner
/// key (verified by the Python CI gate) — a duress-key signature fails that
/// gate, which IS the circular-trust guard.
pub const OUT_OF_BAND_SAFETY_REATTESTATION_DOMAIN: &str =
    "myco-out-of-band-safety-reattestation-v1";

/// node_type for a `duress_keypair_registered` event:
/// `duress_keypair_registered:{first_8_hex_of_duress_pubkey}`.
pub fn duress_keypair_registered_node_type(duress_pubkey: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_DURESS_KEYPAIR_REGISTERED_PREFIX,
        hex_prefix(duress_pubkey, 8)
    )
}

/// node_type for a `duress_signature_observed` event:
/// `duress_signature_observed:{first_8_hex_of_duress_pubkey}`.
pub fn duress_signature_observed_node_type(duress_pubkey: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_DURESS_SIGNATURE_OBSERVED_PREFIX,
        hex_prefix(duress_pubkey, 8)
    )
}

// ---------------------------------------------------------------------------
// `duress_keypair_registration` mutation body (owner-signed) — encode + decode.
//
// Lifecycle (mirrors the C13 revoke_federation_peer staged-envelope path):
//   1. owner/genesis builds these canonical bytes for the duress pubkey;
//   2. owner signs them (the signature is the mutation's attestation_signature),
//      submitted as a `duress_keypair_registration` CI mutation;
//   3. the Python CI gate verifies the signature against the ACTIVE owner key;
//   4. on accept, Rust decodes the body, captures the owner signature + pubkey,
//      and AFTER the `mutation:duress_keypair_registration` DAG node commits
//      emits one `duress_keypair_registered:{prefix}` event + inserts the
//      pubkey into the in-memory `duress_pubkeys` set. Idempotent.
// ---------------------------------------------------------------------------

/// **F23** — build the owner-signed `duress_keypair_registration` body.
///
/// ```text
/// Map({
///   "domain": String("myco-duress-keypair-registration-v1"),
///   "duress_pubkey": Bytes(32),
///   "label": String,                          // human-readable medium label
///   "anchor_timestamp_unix_seconds": Uint,
/// })
/// ```
pub fn build_duress_keypair_registration_canonical_bytes(
    duress_pubkey: &[u8; 32],
    label: &str,
    anchor_timestamp_unix_seconds: u64,
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(DURESS_KEYPAIR_REGISTRATION_DOMAIN.to_string()),
    );
    m.insert(
        "duress_pubkey".to_string(),
        Value::Bytes(duress_pubkey.to_vec()),
    );
    m.insert("label".to_string(), Value::String(label.to_string()));
    m.insert(
        "anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(anchor_timestamp_unix_seconds),
    );
    cb_encode(&Value::Map(m))
        .expect("duress_keypair_registration body encode infallible")
        .0
}

/// **F23** — decode a `duress_keypair_registration` body. Returns
/// `(duress_pubkey, label, anchor_timestamp_unix_seconds)` or `None` if the
/// shape / domain is wrong (→ caller rejects with C5).
pub fn decode_duress_keypair_registration(bytes: &[u8]) -> Option<([u8; 32], String, u64)> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    match m.get("domain")? {
        Value::String(s) if s == DURESS_KEYPAIR_REGISTRATION_DOMAIN => {}
        _ => return None,
    }
    let duress_pubkey = bytes_to_arr32(m.get("duress_pubkey")?)?;
    let label = match m.get("label")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let anchor_timestamp_unix_seconds = match m.get("anchor_timestamp_unix_seconds")? {
        Value::Uint(u) => *u,
        _ => return None,
    };
    Some((duress_pubkey, label, anchor_timestamp_unix_seconds))
}

/// **F23** — content of a `duress_keypair_registered` DAG event (the on-chain
/// owner-attested registration record). The first three fields are the
/// owner-signed body fields; `owner_signature` + `owner_pubkey` are the
/// attestation captured at accept time so the entry is re-verifiable offline.
///
/// ```text
/// Map({
///   "duress_pubkey": Bytes(32),
///   "label": String,
///   "anchor_timestamp_unix_seconds": Uint,
///   "owner_signature": Bytes(64),
///   "owner_pubkey": Bytes(32),
/// })
/// ```
pub fn encode_duress_keypair_registered(
    duress_pubkey: &[u8; 32],
    label: &str,
    anchor_timestamp_unix_seconds: u64,
    owner_signature: &[u8; 64],
    owner_pubkey: &[u8; 32],
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "duress_pubkey".to_string(),
        Value::Bytes(duress_pubkey.to_vec()),
    );
    m.insert("label".to_string(), Value::String(label.to_string()));
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
    cb_encode(&Value::Map(m)).expect("duress_keypair_registered encode infallible")
}

/// **F23** — extract the `duress_pubkey` from a `duress_keypair_registered` DAG
/// event's content. `None` if malformed (a corrupt/hand-crafted node is simply
/// skipped during derivation rather than treated as a registration).
pub fn decode_duress_keypair_registered_pubkey(bytes: &[u8]) -> Option<[u8; 32]> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    bytes_to_arr32(m.get("duress_pubkey")?)
}

/// **F23** — re-derive the in-memory registered-duress-pubkey set from the DAG.
///
/// Called once at boot (mirrors `derive_revoked_federation_peers_from_dag`) and
/// kept current thereafter by the registration emit path. A single
/// in-insertion-order walk collecting every `duress_keypair_registered:*`
/// event's pubkey; O(N) over the DAG. Purely additive — duress registrations
/// are a genesis/owner concern that only grows (there is no
/// de-registration event by design; an owner who wishes to retire a duress key
/// rotates the owner key relationship out-of-band).
pub fn derive_duress_pubkeys_from_dag(
    dag: &myco_kernel_schema::dag::Dag,
) -> std::collections::HashSet<[u8; 32]> {
    let mut set = std::collections::HashSet::new();
    for node in dag.iter_in_insertion_order() {
        if !node
            .node_type
            .starts_with(NODE_TYPE_DURESS_KEYPAIR_REGISTERED_PREFIX)
        {
            continue;
        }
        if let Some(pubkey) =
            decode_duress_keypair_registered_pubkey(node.content_canonical_bytes.as_ref())
        {
            set.insert(pubkey);
        }
    }
    set
}

// ---------------------------------------------------------------------------
// `duress_signature_observed` event — the silent forensic record.
// ---------------------------------------------------------------------------

/// **C50 / AS §8.4** — content of a `duress_signature_observed` DAG event.
/// Records WHICH duress key was observed, the attempted (and SUPPRESSED)
/// mutation_type, and a hash of the content the coercer tried to push. Emitted
/// SILENTLY (never surfaced in the cosmetic response). `attempted_content_hash`
/// is the SHA-256 of the duress-signed `content_canonical_bytes` (the same
/// `attestation::compute_content_hash` digest used for nonce binding) — enough
/// to prove offline exactly what was attempted without storing the (suppressed)
/// body.
///
/// ```text
/// Map({
///   "duress_pubkey": Bytes(32),
///   "attempted_mutation_type": String,
///   "attempted_content_hash": Bytes(32),
///   "observed_at_unix_ns": Timestamp,
/// })
/// ```
pub fn encode_duress_signature_observed(
    duress_pubkey: &[u8; 32],
    attempted_mutation_type: &str,
    attempted_content_hash: &[u8; 32],
    observed_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "duress_pubkey".to_string(),
        Value::Bytes(duress_pubkey.to_vec()),
    );
    m.insert(
        "attempted_mutation_type".to_string(),
        Value::String(attempted_mutation_type.to_string()),
    );
    m.insert(
        "attempted_content_hash".to_string(),
        Value::Bytes(attempted_content_hash.to_vec()),
    );
    m.insert(
        "observed_at_unix_ns".to_string(),
        Value::Timestamp(observed_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("duress_signature_observed encode infallible")
}

// ---------------------------------------------------------------------------
// Freeze FSM events: coerced_owner_suspected (onset) + duress_cleared (lift).
// ---------------------------------------------------------------------------

/// **C50** — content of the `coerced_owner_suspected` freeze-onset event.
///
/// ```text
/// Map({
///   "duress_pubkey": Bytes(32),
///   "attempted_mutation_type": String,
///   "onset_at_unix_ns": Timestamp,
/// })
/// ```
pub fn encode_coerced_owner_suspected(
    duress_pubkey: &[u8; 32],
    attempted_mutation_type: &str,
    onset_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "duress_pubkey".to_string(),
        Value::Bytes(duress_pubkey.to_vec()),
    );
    m.insert(
        "attempted_mutation_type".to_string(),
        Value::String(attempted_mutation_type.to_string()),
    );
    m.insert(
        "onset_at_unix_ns".to_string(),
        Value::Timestamp(onset_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("coerced_owner_suspected encode infallible")
}

/// **F23** — build the owner-signed `out_of_band_safety_reattestation` body
/// (the unfreeze attestation). The owner asserts, out of band and with the
/// ACTIVE key, that they are safe and the coercion has ended.
///
/// ```text
/// Map({
///   "domain": String("myco-out-of-band-safety-reattestation-v1"),
///   "statement": String,                       // free-form safety statement
///   "anchor_timestamp_unix_seconds": Uint,
/// })
/// ```
pub fn build_out_of_band_safety_reattestation_canonical_bytes(
    statement: &str,
    anchor_timestamp_unix_seconds: u64,
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(OUT_OF_BAND_SAFETY_REATTESTATION_DOMAIN.to_string()),
    );
    m.insert("statement".to_string(), Value::String(statement.to_string()));
    m.insert(
        "anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(anchor_timestamp_unix_seconds),
    );
    cb_encode(&Value::Map(m))
        .expect("out_of_band_safety_reattestation body encode infallible")
        .0
}

/// **F23** — decode an `out_of_band_safety_reattestation` body. Returns
/// `(statement, anchor_timestamp_unix_seconds)` or `None` on wrong shape/domain.
pub fn decode_out_of_band_safety_reattestation(bytes: &[u8]) -> Option<(String, u64)> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    match m.get("domain")? {
        Value::String(s) if s == OUT_OF_BAND_SAFETY_REATTESTATION_DOMAIN => {}
        _ => return None,
    }
    let statement = match m.get("statement")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let anchor_timestamp_unix_seconds = match m.get("anchor_timestamp_unix_seconds")? {
        Value::Uint(u) => *u,
        _ => return None,
    };
    Some((statement, anchor_timestamp_unix_seconds))
}

/// **F23** — content of a `duress_cleared` event (freeze lifted by an accepted
/// active-key `out_of_band_safety_reattestation`). Captures the owner signature
/// + pubkey over the reattestation body so the clearance is re-verifiable.
///
/// ```text
/// Map({
///   "statement": String,
///   "anchor_timestamp_unix_seconds": Uint,
///   "owner_signature": Bytes(64),
///   "owner_pubkey": Bytes(32),
/// })
/// ```
pub fn encode_duress_cleared(
    statement: &str,
    anchor_timestamp_unix_seconds: u64,
    owner_signature: &[u8; 64],
    owner_pubkey: &[u8; 32],
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("statement".to_string(), Value::String(statement.to_string()));
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
    cb_encode(&Value::Map(m)).expect("duress_cleared encode infallible")
}

/// **C50 freeze FSM** — re-derive the duress-freeze flag from the DAG.
///
/// Walks the DAG in insertion order tracking the LATEST freeze-transition: a
/// `coerced_owner_suspected` sets the latched flag true; a later `duress_cleared`
/// resets it false. The final value is the freeze state. Called once at boot
/// (mirrors `derive_revoked_federation_peers_from_dag`); the live flag is kept
/// current by the duress recognition + unfreeze emit paths thereafter.
///
/// This is a strict last-writer FSM over the two event types, so a substrate
/// restarted while frozen resumes frozen, and one restarted after an
/// out-of-band clearance resumes unfrozen — the DAG is canonical.
pub fn derive_duress_freeze_active_from_dag(dag: &myco_kernel_schema::dag::Dag) -> bool {
    let mut frozen = false;
    for node in dag.iter_in_insertion_order() {
        if node.node_type == NODE_TYPE_COERCED_OWNER_SUSPECTED {
            frozen = true;
        } else if node.node_type == NODE_TYPE_DURESS_CLEARED {
            frozen = false;
        }
    }
    frozen
}

/// Local 32-byte extractor (mirrors `federation::bytes_to_arr32`; kept private
/// to this module so the duress codec is self-contained).
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
mod tests {
    use super::*;
    use myco_kernel_schema::dag::Dag;
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    use std::collections::BTreeMap;

    #[test]
    fn registration_body_roundtrips() {
        let pk = [0x11u8; 32];
        let bytes = build_duress_keypair_registration_canonical_bytes(&pk, "yubikey-2", 1_700_000_000);
        let (got_pk, label, ts) =
            decode_duress_keypair_registration(&bytes).expect("body decodes");
        assert_eq!(got_pk, pk);
        assert_eq!(label, "yubikey-2");
        assert_eq!(ts, 1_700_000_000);
    }

    #[test]
    fn registration_body_rejects_wrong_domain() {
        let mut m = BTreeMap::new();
        m.insert("domain".to_string(), Value::String("wrong-domain".to_string()));
        m.insert("duress_pubkey".to_string(), Value::Bytes(vec![0u8; 32]));
        m.insert("label".to_string(), Value::String("x".to_string()));
        m.insert("anchor_timestamp_unix_seconds".to_string(), Value::Uint(1));
        let bytes = cb_encode(&Value::Map(m)).unwrap().0;
        assert!(
            decode_duress_keypair_registration(&bytes).is_none(),
            "wrong-domain body must not decode as a duress registration"
        );
    }

    #[test]
    fn registration_body_rejects_garbage_and_wrong_shapes() {
        assert!(decode_duress_keypair_registration(&[0xff, 0x00, 0x23]).is_none());
        // Missing required field (label).
        let mut m = BTreeMap::new();
        m.insert(
            "domain".to_string(),
            Value::String(DURESS_KEYPAIR_REGISTRATION_DOMAIN.to_string()),
        );
        m.insert("duress_pubkey".to_string(), Value::Bytes(vec![0u8; 32]));
        m.insert("anchor_timestamp_unix_seconds".to_string(), Value::Uint(1));
        let bytes = cb_encode(&Value::Map(m)).unwrap().0;
        assert!(decode_duress_keypair_registration(&bytes).is_none());
    }

    #[test]
    fn reattestation_body_roundtrips_and_rejects_wrong_domain() {
        let bytes = build_out_of_band_safety_reattestation_canonical_bytes("I am safe", 42);
        let (statement, ts) =
            decode_out_of_band_safety_reattestation(&bytes).expect("decodes");
        assert_eq!(statement, "I am safe");
        assert_eq!(ts, 42);
        // Reuse the registration body — its domain differs, so it must NOT
        // decode as a reattestation (domain separation).
        let reg = build_duress_keypair_registration_canonical_bytes(&[0u8; 32], "x", 1);
        assert!(decode_out_of_band_safety_reattestation(&reg).is_none());
    }

    #[test]
    fn registered_event_pubkey_extracts() {
        let pk = [0xabu8; 32];
        let content =
            encode_duress_keypair_registered(&pk, "ledger", 1, &[0u8; 64], &[0u8; 32]);
        assert_eq!(
            decode_duress_keypair_registered_pubkey(content.as_ref()),
            Some(pk)
        );
    }

    #[test]
    fn node_type_prefixes_match() {
        let nt = duress_keypair_registered_node_type(&[
            0xde, 0xad, 0xbe, 0xef, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ]);
        assert!(nt.starts_with(NODE_TYPE_DURESS_KEYPAIR_REGISTERED_PREFIX));
        assert_eq!(nt, "duress_keypair_registered:deadbeef00000000");
        let nt2 = duress_signature_observed_node_type(&[0xab; 32]);
        assert!(nt2.starts_with(NODE_TYPE_DURESS_SIGNATURE_OBSERVED_PREFIX));
    }

    #[test]
    fn derive_pubkeys_collects_registrations_skips_corrupt() {
        let mut dag = Dag::new();
        let id_a = [0x01u8; 32];
        let id_b = [0x02u8; 32];
        let tip = dag
            .insert_node(
                Vec::new(),
                duress_keypair_registered_node_type(&id_a),
                0,
                encode_duress_keypair_registered(&id_a, "a", 1, &[0u8; 64], &[0u8; 32]),
            )
            .unwrap();
        let tip = dag
            .insert_node(
                vec![tip],
                duress_keypair_registered_node_type(&id_b),
                0,
                encode_duress_keypair_registered(&id_b, "b", 1, &[0u8; 64], &[0u8; 32]),
            )
            .unwrap();
        // A corrupt registered node (bad content) must be skipped, not panic.
        dag.insert_node(
            vec![tip],
            format!("{NODE_TYPE_DURESS_KEYPAIR_REGISTERED_PREFIX}cccccccc"),
            0,
            CanonicalBytes(vec![0xff, 0x00]),
        )
        .unwrap();
        let set = derive_duress_pubkeys_from_dag(&dag);
        assert_eq!(set.len(), 2);
        assert!(set.contains(&id_a));
        assert!(set.contains(&id_b));
    }

    #[test]
    fn freeze_fsm_last_writer_wins() {
        let mut dag = Dag::new();
        // No freeze events → unfrozen.
        assert!(!derive_duress_freeze_active_from_dag(&dag));
        // coerced_owner_suspected → frozen.
        let tip = dag
            .insert_node(
                Vec::new(),
                NODE_TYPE_COERCED_OWNER_SUSPECTED.to_string(),
                0,
                encode_coerced_owner_suspected(&[0u8; 32], "schema_evolution", 1),
            )
            .unwrap();
        assert!(derive_duress_freeze_active_from_dag(&dag));
        // duress_cleared → unfrozen.
        let tip = dag
            .insert_node(
                vec![tip],
                NODE_TYPE_DURESS_CLEARED.to_string(),
                0,
                encode_duress_cleared("safe", 2, &[0u8; 64], &[0u8; 32]),
            )
            .unwrap();
        assert!(!derive_duress_freeze_active_from_dag(&dag));
        // A second onset re-freezes (last-writer).
        dag.insert_node(
            vec![tip],
            NODE_TYPE_COERCED_OWNER_SUSPECTED.to_string(),
            0,
            encode_coerced_owner_suspected(&[0u8; 32], "revoke_federation_peer", 3),
        )
        .unwrap();
        assert!(derive_duress_freeze_active_from_dag(&dag));
    }
}
