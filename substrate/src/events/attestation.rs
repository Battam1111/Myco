//! Substrate attestation codecs (KEYLESS v0.9): the invariant-witness layer +
//! the reproduction spawn-cosign envelope + the I7 birth-closure markers.
//!
//! **v0.9 keyless**: the owner-key + anchor surface was removed. With it went
//! the M-anchor-5 §9.2.2 DAG-tip co-sign + §9.2.4 L0-revision-attest envelopes
//! (and their `tip_cosigned:*` / `l0_revision_attested:*` DAG events), the
//! M-anchor-2 §9.2.1 owner-signed birth-attestation 5-tuple + C20 boot verifier,
//! and the M-anchor-4 §9.3.5 anchor-nonce leaf-sampling helper. The trust root
//! for an L0/doctrine change is now (1) the live human at the CI gate, the
//! git/PR review on the doctrine repo, enforced by the BLAKE3 drift-gate in CI;
//! (2) the substrate's own tamper-evident causal DAG (P06); (3) the
//! BLAKE3-sealed doctrine bundle. No owner co-signature is checked at runtime.
//!
//! What remains here:
//! - the M-anchor-4 §9.3.4 invariant-witness layer (`invariant_witness:{check_id}`
//!   DAG events carrying raw check inputs; the CI gate re-derives pass/fail);
//! - the P08 reproduction spawn-cosign envelope + the `genesis_attested` I7-closure
//!   record + the `birth_closure_pending` / `birth_closure_complete` markers
//!   (keyless: the envelope's parent-replay-guard + spore-schema binding are
//!   verified, but no owner signature is checked over it).

use super::hex_prefix;
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

/// Local 32-byte extractor shared by the kept decoders below.
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

// ---------------------------------------------------------------------------
// **M-anchor-4 §9.3.4 Witnesses-not-verdicts** (KEYLESS v0.9).
//
// The substrate emits the raw INPUTS for each invariant check (input bytes,
// node counts, DAG-tip hash) so the verdict can be re-derived independently at
// the CI gate. The substrate does NOT emit pass/fail, only the inputs.
//
// This is an ADDITIVE witness layer: the existing immune-sporocarp emission path
// on detected failures is preserved; alongside, every integrity check ALSO emits
// an `invariant_witness:{check_id}` DAG event carrying the raw inputs.
//
// **v0.9 keyless**: the §9.3.5 anchor-nonce leaf-sampling (`anchor_nonce` +
// `anchor_nonce_signature` envelope fields + the `anchor_nonce_derived_sample_indices`
// helper) was removed with the anchor surface. Tier-1 checks carry their full
// inputs; deferred tier-2 sampled re-verification derives its sample seed from a
// substrate/DAG-tip-derived value (keyless; acknowledged-debt: no external
// anchor-minted nonce).
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
/// the raw inputs re-fed into the canonical check algorithm at the CI gate.
/// Per-check schema is documented at the call site (e.g., for `dag_verify_all`:
/// `{node_count, dag_tip_hash}`).
///
/// **v0.9 keyless**: the `anchor_nonce` + `anchor_nonce_signature` envelope
/// fields were removed with the anchor surface.
///
/// The outer envelope is:
/// ```text
/// Map({
///   "check_id":   String,
///   "tier":       String ("tier_1" / "tier_2" / "tier_3"),
///   "at_cycle":   Uint,
///   "at_unix_ns": Timestamp,
///   "inputs":     Bytes (= inputs_map_canonical_bytes),
/// })
/// ```
pub fn encode_invariant_witness(
    check_id: &str,
    tier: &str,
    at_cycle: u64,
    at_unix_ns: i64,
    inputs_map_canonical_bytes: &[u8],
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
    cb_encode(&Value::Map(m)).expect("invariant_witness encode infallible")
}

/// Decode an invariant_witness body. Returns the parsed fields or `None`
/// on shape mismatch. Used by the CI-gate reconstruction tooling (the TS
/// counterpart mirrors this). **v0.9 keyless**: the anchor_nonce +
/// anchor_nonce_signature fields were removed → 5-tuple.
pub fn decode_invariant_witness(
    bytes: &[u8],
) -> Option<(String, String, u64, i64, Vec<u8>)> {
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
    Some((check_id, tier, at_cycle, at_unix_ns, inputs))
}

// ---------------------------------------------------------------------------
// **M-anchor-2 §9.2.1 Birth Attestation, REMOVED (v0.9 keyless)**.
//
// The owner-signed genesis 5-tuple (substrate-ID, genesis-timestamp,
// spore-schema-hash, owner-public-key, anchor-endpoint-public-key), the
// `birth_attestation:{substrate_id_prefix}` DAG-event codec, the env-var
// ingestion path, and the every-boot C20 signature re-verifier were all removed
// with the owner-key + anchor surface. A fresh substrate's identity is
// self-derived (P01c) and recorded in its own `genesis_event`; there is no
// owner-signed birth attestation to fetch or re-verify.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// **P08 §3.2 / §3.5 / §5.1, Reproduction spawn closure + I7** (KEYLESS v0.9).
//
// L0/cards/P08 §5.1: spawning a child substrate is NOT a daily-mode mutation,
// it is a CI-class doctrine event. An unattested spawn (a bare operator spawning
// on its own authority with no spawn envelope) is the "daily-mode spawn =
// doctrine collapse" signal → C68 reproduction_unattested_spawn.
//
// P08 §3.5 + L1/SCHEMA §3.3 spawn closure (I7):
//   (a) parent runs STATIC-SCHEMA validation: the child's spore-schema canonical
//       bytes hash matches the envelope's `spore_schema_hash` AND the 7-field
//       shape is well-formed;
//   (b) the spawn envelope binds the immutable spawn parameters
//       (parent-substrate-ID replay guard, spore-schema-hash, child-genesis
//        timestamp, the §16.B rate-throttle timestamp + a binding nonce);
//   (c) the child runs its OWN I3 self-validation as its first metabolic cycle
//       (substrate boot integrity self-check) before any operator cycle.
//
// **v0.9 keyless**: the cultivator Ed25519 co-signature over the envelope (and
// the owner-pubkey it was checked against) was removed with the anchor surface.
// The envelope's STRUCTURE, parent replay-guard, spore-schema binding, the
// timestamp the §16.B throttle reads, is still verified; no signature is checked
// over it. (The envelope's `myco-spawn-cosign-v1` canonical-bytes shape + field
// names are pinned by a cross-language parity vector, so they are unchanged.)
//
// This module ships that canonical-bytes envelope, the
// `genesis_attested:{child_prefix}` I7-closure record emitted into the PARENT's
// DAG, and the `birth_closure_pending` / `birth_closure_complete` markers the
// child writes (b)→(c).
// ---------------------------------------------------------------------------

/// Domain string for the reproduction spawn-cosign envelope (P08 §3.5 / §5.1).
/// (KEYLESS v0.9: the envelope is no longer owner-signed; the domain string +
/// canonical-bytes shape are pinned by a cross-language parity vector.)
pub const SPAWN_COSIGN_DOMAIN: &str = "myco-spawn-cosign-v1";

/// Prefix for `genesis_attested:{child_id_prefix}` DAG events, the I7-closure
/// record written into the PARENT's DAG after a verified spawn (keyless).
pub const NODE_TYPE_GENESIS_ATTESTED_PREFIX: &str = "genesis_attested:";

/// Prefix for `birth_closure_pending:{parent_id_prefix}` DAG events, written
/// into the CHILD's DAG at construction time, signalling the child must run its
/// own I3 boot self-check (I7 step c) before any operator cycle.
pub const NODE_TYPE_BIRTH_CLOSURE_PENDING_PREFIX: &str = "birth_closure_pending:";

/// Prefix for `birth_closure_complete:{child_id_prefix}` DAG events, written
/// into the CHILD's DAG at first boot once the I3 self-check verdict is known.
pub const NODE_TYPE_BIRTH_CLOSURE_COMPLETE_PREFIX: &str = "birth_closure_complete:";

/// Build the reproduction spawn-cosign canonical-bytes envelope (P08 §3.5 / §5.1).
///
/// **v0.9 keyless**: the envelope is no longer owner-signed; its STRUCTURE is
/// what the substrate verifies. The field names + canonical-bytes shape are
/// pinned by a cross-language parity vector, so they are unchanged from the
/// pre-keyless wire contract.
///
/// The envelope binds the immutable spawn parameters so that:
///   - `parent_substrate_id` is a replay guard (the substrate rejects an
///     envelope minted for a different parent);
///   - `spore_schema_hash` pins the child's static schema (I7 step a);
///   - `child_genesis_timestamp_unix_ns` feeds the deterministic
///     child-id `blake3(parent_id, spore_schema_hash, child_genesis_ts)`
///     (§5.6 non-reissuance);
///   - `anchor_timestamp_unix_ns` + `anchor_nonce` are the §16.B rate-throttle
///     timestamp + a binding nonce (operator/substrate-threaded; keyless,
///     acknowledged-debt: no external trusted clock / anchor-minted nonce);
///   - `depth_override` (Bool) is the explicit override of the §16.A
///     lineage-depth cap for THIS spawn (F22 depth_override).
pub fn build_spawn_cosign_canonical_bytes(
    parent_substrate_id: &[u8; 32],
    spore_schema_hash: &[u8; 32],
    child_genesis_timestamp_unix_ns: i64,
    anchor_timestamp_unix_ns: i64,
    anchor_nonce: &[u8; 32],
    depth_override: bool,
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(SPAWN_COSIGN_DOMAIN.to_string()),
    );
    m.insert(
        "parent_substrate_id".to_string(),
        Value::Bytes(parent_substrate_id.to_vec()),
    );
    m.insert(
        "spore_schema_hash".to_string(),
        Value::Bytes(spore_schema_hash.to_vec()),
    );
    m.insert(
        "child_genesis_timestamp_unix_ns".to_string(),
        Value::Timestamp(child_genesis_timestamp_unix_ns),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(anchor_timestamp_unix_ns),
    );
    m.insert(
        "anchor_nonce".to_string(),
        Value::Bytes(anchor_nonce.to_vec()),
    );
    m.insert("depth_override".to_string(), Value::Bool(depth_override));
    cb_encode(&Value::Map(m))
        .expect("spawn_cosign canonical-bytes encode infallible")
        .0
}

/// Decode a spawn co-sign envelope. Returns the parsed fields or `None`
/// if the shape / domain is wrong.
///
/// Tuple order:
/// `(parent_substrate_id, spore_schema_hash, child_genesis_timestamp_unix_ns,
///   anchor_timestamp_unix_ns, anchor_nonce, depth_override)`.
#[allow(clippy::type_complexity)]
pub fn decode_spawn_cosign(
    bytes: &[u8],
) -> Option<([u8; 32], [u8; 32], i64, i64, [u8; 32], bool)> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(bytes).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    match m.get("domain")? {
        Value::String(s) if s == SPAWN_COSIGN_DOMAIN => {}
        _ => return None,
    }
    let parent_substrate_id = bytes_to_arr32_local(m.get("parent_substrate_id")?)?;
    let spore_schema_hash = bytes_to_arr32_local(m.get("spore_schema_hash")?)?;
    let child_genesis_timestamp_unix_ns = match m.get("child_genesis_timestamp_unix_ns")? {
        Value::Timestamp(t) => *t,
        _ => return None,
    };
    let anchor_timestamp_unix_ns = match m.get("anchor_timestamp_unix_ns")? {
        Value::Timestamp(t) => *t,
        _ => return None,
    };
    let anchor_nonce = bytes_to_arr32_local(m.get("anchor_nonce")?)?;
    let depth_override = match m.get("depth_override")? {
        Value::Bool(b) => *b,
        _ => return None,
    };
    Some((
        parent_substrate_id,
        spore_schema_hash,
        child_genesis_timestamp_unix_ns,
        anchor_timestamp_unix_ns,
        anchor_nonce,
        depth_override,
    ))
}

/// Full `genesis_attested:{child_id_prefix}` node_type string.
pub fn genesis_attested_node_type(child_substrate_id: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_GENESIS_ATTESTED_PREFIX,
        hex_prefix(child_substrate_id, 8)
    )
}

/// Full `birth_closure_pending:{parent_id_prefix}` node_type string.
pub fn birth_closure_pending_node_type(parent_substrate_id: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_BIRTH_CLOSURE_PENDING_PREFIX,
        hex_prefix(parent_substrate_id, 8)
    )
}

/// Full `birth_closure_complete:{child_id_prefix}` node_type string.
pub fn birth_closure_complete_node_type(child_substrate_id: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_BIRTH_CLOSURE_COMPLETE_PREFIX,
        hex_prefix(child_substrate_id, 8)
    )
}

/// Encode the body of a `genesis_attested:{child_prefix}` DAG event, the
/// I7-closure record in the PARENT's DAG (P08 §3.5; KEYLESS v0.9, the
/// cultivator owner_signature + owner_pubkey fields were removed).
///
/// Carries the spawn-cosign envelope bytes (for offline inspection), the
/// parent/child/spore binding, and a boolean witness that the parent ran the
/// child's static-schema validation (I7 step a) and it passed.
/// ```text
/// Map({
///   "spawn_cosign_envelope":     Bytes,      // the spawn parameters envelope
///   "parent_substrate_id":       Bytes(32),
///   "child_substrate_id":        Bytes(32),
///   "spore_schema_hash":         Bytes(32),
///   "child_static_schema_valid": Bool,       // I7(a) verdict
///   "emitted_at_cycle":          Uint,
/// })
/// ```
pub fn encode_genesis_attested_event(
    spawn_cosign_envelope_bytes: &[u8],
    parent_substrate_id: &[u8; 32],
    child_substrate_id: &[u8; 32],
    spore_schema_hash: &[u8; 32],
    child_static_schema_valid: bool,
    emitted_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "spawn_cosign_envelope".to_string(),
        Value::Bytes(spawn_cosign_envelope_bytes.to_vec()),
    );
    m.insert(
        "parent_substrate_id".to_string(),
        Value::Bytes(parent_substrate_id.to_vec()),
    );
    m.insert(
        "child_substrate_id".to_string(),
        Value::Bytes(child_substrate_id.to_vec()),
    );
    m.insert(
        "spore_schema_hash".to_string(),
        Value::Bytes(spore_schema_hash.to_vec()),
    );
    m.insert(
        "child_static_schema_valid".to_string(),
        Value::Bool(child_static_schema_valid),
    );
    m.insert(
        "emitted_at_cycle".to_string(),
        Value::Uint(emitted_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("genesis_attested event encode infallible")
}

/// Decode a `genesis_attested` DAG event body (KEYLESS v0.9). Returns the parsed
/// fields or `None` on shape mismatch.
///
/// Tuple order: `(spawn_cosign_envelope, parent_substrate_id,
/// child_substrate_id, spore_schema_hash, child_static_schema_valid,
/// emitted_at_cycle)`.
#[allow(clippy::type_complexity)]
pub fn decode_genesis_attested_event(
    bytes: &[u8],
) -> Option<(Vec<u8>, [u8; 32], [u8; 32], [u8; 32], bool, u64)> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(bytes).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    let envelope = match m.get("spawn_cosign_envelope")? {
        Value::Bytes(b) => b.clone(),
        _ => return None,
    };
    let parent_substrate_id = bytes_to_arr32_local(m.get("parent_substrate_id")?)?;
    let child_substrate_id = bytes_to_arr32_local(m.get("child_substrate_id")?)?;
    let spore_schema_hash = bytes_to_arr32_local(m.get("spore_schema_hash")?)?;
    let child_static_schema_valid = match m.get("child_static_schema_valid")? {
        Value::Bool(b) => *b,
        _ => return None,
    };
    let emitted_at_cycle = match m.get("emitted_at_cycle")? {
        Value::Uint(n) => *n,
        _ => return None,
    };
    Some((
        envelope,
        parent_substrate_id,
        child_substrate_id,
        spore_schema_hash,
        child_static_schema_valid,
        emitted_at_cycle,
    ))
}

/// Encode the body of a `birth_closure_pending:{parent_prefix}` DAG event
/// (I7 step b marker, written into the CHILD's DAG at construction).
/// ```text
/// Map({
///   "parent_substrate_id": Bytes(32),
///   "child_substrate_id":  Bytes(32),
///   "spore_schema_hash":   Bytes(32),
/// })
/// ```
pub fn encode_birth_closure_pending(
    parent_substrate_id: &[u8; 32],
    child_substrate_id: &[u8; 32],
    spore_schema_hash: &[u8; 32],
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "parent_substrate_id".to_string(),
        Value::Bytes(parent_substrate_id.to_vec()),
    );
    m.insert(
        "child_substrate_id".to_string(),
        Value::Bytes(child_substrate_id.to_vec()),
    );
    m.insert(
        "spore_schema_hash".to_string(),
        Value::Bytes(spore_schema_hash.to_vec()),
    );
    cb_encode(&Value::Map(m)).expect("birth_closure_pending encode infallible")
}

/// Encode the body of a `birth_closure_complete:{child_prefix}` DAG event
/// (I7 step c marker, written into the CHILD's DAG at first boot once the
/// child's own I3 boot self-check verdict is known).
/// ```text
/// Map({
///   "child_substrate_id":  Bytes(32),
///   "i3_self_check_passed": Bool,        // child's first-cycle I3 verdict
///   "completed_at_unix_ns": Timestamp,
/// })
/// ```
pub fn encode_birth_closure_complete(
    child_substrate_id: &[u8; 32],
    i3_self_check_passed: bool,
    completed_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "child_substrate_id".to_string(),
        Value::Bytes(child_substrate_id.to_vec()),
    );
    m.insert(
        "i3_self_check_passed".to_string(),
        Value::Bool(i3_self_check_passed),
    );
    m.insert(
        "completed_at_unix_ns".to_string(),
        Value::Timestamp(completed_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("birth_closure_complete encode infallible")
}

#[cfg(test)]
mod spawn_cosign_tests {
    use super::*;

    #[test]
    fn spawn_cosign_envelope_roundtrips() {
        let parent = [0x11u8; 32];
        let spore_hash = [0x22u8; 32];
        let child_genesis_ts: i64 = 1_700_000_000_000_000_000;
        let anchor_ts: i64 = 1_700_000_000_500_000_000;
        let nonce = [0x33u8; 32];
        let bytes = build_spawn_cosign_canonical_bytes(
            &parent,
            &spore_hash,
            child_genesis_ts,
            anchor_ts,
            &nonce,
            true,
        );
        let (p, sh, cgt, at, n, ov) =
            decode_spawn_cosign(&bytes).expect("spawn_cosign decodes");
        assert_eq!(p, parent);
        assert_eq!(sh, spore_hash);
        assert_eq!(cgt, child_genesis_ts);
        assert_eq!(at, anchor_ts);
        assert_eq!(n, nonce);
        assert!(ov);
    }

    /// **Cross-language parity vector** (Rust half). The TS
    /// `buildSpawnCosignCanonicalBytes` MUST produce these exact bytes for the
    /// same fixed inputs (see
    /// `operators/claude/tests/canonical_bytes_parity.test.ts`). The spawn-cosign
    /// envelope is the security + wire contract between the cultivator's signing
    /// (TS) and the substrate's verify (Rust); any drift means signatures stop
    /// verifying cross-side, so this vector is pinned on BOTH sides.
    const SPAWN_COSIGN_PARITY_HEX: &str = "31072006646f6d61696e20146d79636f2d737061776e2d636f7369676e2d7631200c616e63686f725f6e6f6e636521200303030303030303030303030303030303030303030303030303030303030303200e64657074685f6f766572726964650101201173706f72655f736368656d615f68617368212002020202020202020202020202020202020202020202020202020202020202022013706172656e745f7375627374726174655f6964212001010101010101010101010101010101010101010101010101010101010101012018616e63686f725f74696d657374616d705f756e69785f6e734017979cfe710868b1201f6368696c645f67656e657369735f74696d657374616d705f756e69785f6e734017979cfe3d85cd15";

    #[test]
    fn spawn_cosign_parity_vector_pinned() {
        let parent = [0x01u8; 32];
        let spore_hash = [0x02u8; 32];
        let child_genesis_ts: i64 = 1_700_000_000_123_456_789;
        let anchor_ts: i64 = 1_700_000_000_987_654_321;
        let nonce = [0x03u8; 32];
        let bytes = build_spawn_cosign_canonical_bytes(
            &parent,
            &spore_hash,
            child_genesis_ts,
            anchor_ts,
            &nonce,
            true,
        );
        let hex: String = bytes.iter().map(|b| format!("{b:02x}")).collect();
        assert_eq!(
            hex, SPAWN_COSIGN_PARITY_HEX,
            "spawn-cosign canonical bytes drifted from the pinned cross-language \
             parity vector — TS signing + Rust verify would diverge"
        );
    }

    #[test]
    fn spawn_cosign_depth_override_false_roundtrips() {
        let bytes = build_spawn_cosign_canonical_bytes(
            &[0u8; 32],
            &[1u8; 32],
            1,
            2,
            &[2u8; 32],
            false,
        );
        let (_, _, _, _, _, ov) = decode_spawn_cosign(&bytes).expect("decodes");
        assert!(!ov, "depth_override=false must round-trip");
    }

    #[test]
    fn spawn_cosign_rejects_wrong_domain() {
        // Build a valid envelope, then corrupt the domain field.
        let valid = build_spawn_cosign_canonical_bytes(
            &[0u8; 32],
            &[0u8; 32],
            0,
            0,
            &[0u8; 32],
            false,
        );
        use myco_kernel_shared::canonical_bytes::{decode, encode as cb_enc, Value as V};
        let mut m = match decode(&valid).unwrap() {
            V::Map(m) => m,
            _ => panic!(),
        };
        m.insert("domain".to_string(), V::String("not-spawn-cosign".to_string()));
        let corrupted = cb_enc(&V::Map(m)).unwrap().0;
        assert!(
            decode_spawn_cosign(&corrupted).is_none(),
            "wrong domain must reject"
        );
    }

    #[test]
    fn spawn_cosign_rejects_corrupt_parent_id_length() {
        use myco_kernel_shared::canonical_bytes::{decode, encode as cb_enc, Value as V};
        let valid = build_spawn_cosign_canonical_bytes(
            &[0u8; 32],
            &[0u8; 32],
            0,
            0,
            &[0u8; 32],
            false,
        );
        let mut m = match decode(&valid).unwrap() {
            V::Map(m) => m,
            _ => panic!(),
        };
        m.insert("parent_substrate_id".to_string(), V::Bytes(vec![0u8; 16]));
        let corrupted = cb_enc(&V::Map(m)).unwrap().0;
        assert!(
            decode_spawn_cosign(&corrupted).is_none(),
            "16-byte parent_substrate_id must reject"
        );
    }

    #[test]
    fn genesis_attested_event_roundtrips() {
        let envelope = vec![0x55u8; 80];
        let parent = [0x88u8; 32];
        let child = [0x99u8; 32];
        let spore_hash = [0xaau8; 32];
        let cycle: u64 = 4242;
        let body = encode_genesis_attested_event(
            &envelope, &parent, &child, &spore_hash, true, cycle,
        );
        let (env_out, p_out, c_out, sh_out, valid_out, cyc_out) =
            decode_genesis_attested_event(body.as_ref()).expect("decodes");
        assert_eq!(env_out, envelope);
        assert_eq!(p_out, parent);
        assert_eq!(c_out, child);
        assert_eq!(sh_out, spore_hash);
        assert!(valid_out);
        assert_eq!(cyc_out, cycle);
    }

    #[test]
    fn node_type_strings_carry_hex_prefix() {
        let mut child = [0u8; 32];
        child[0] = 0xab;
        child[1] = 0xcd;
        assert!(genesis_attested_node_type(&child).starts_with("genesis_attested:"));
        assert!(genesis_attested_node_type(&child).contains("abcd"));
        assert!(birth_closure_complete_node_type(&child).contains("abcd"));
        let mut parent = [0u8; 32];
        parent[0] = 0xde;
        parent[1] = 0xad;
        assert!(birth_closure_pending_node_type(&parent).contains("dead"));
    }

    #[test]
    fn birth_closure_event_bodies_decode() {
        use myco_kernel_shared::canonical_bytes::{decode, Value as V};
        let parent = [0x01u8; 32];
        let child = [0x02u8; 32];
        let spore_hash = [0x03u8; 32];
        let pending = encode_birth_closure_pending(&parent, &child, &spore_hash);
        let pm = match decode(pending.as_ref()).unwrap() {
            V::Map(m) => m,
            _ => panic!(),
        };
        assert!(matches!(pm.get("parent_substrate_id"), Some(V::Bytes(b)) if b == &parent.to_vec()));

        let complete = encode_birth_closure_complete(&child, true, 1_700_000_000_000_000_000);
        let cm = match decode(complete.as_ref()).unwrap() {
            V::Map(m) => m,
            _ => panic!(),
        };
        assert!(matches!(cm.get("i3_self_check_passed"), Some(V::Bool(true))));
    }
}
