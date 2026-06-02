//! **M-anchor-5 §9.2.2 DAG-tip co-signing + §9.2.4 L0 revision diff workflow**,
//! **M-anchor-4 §9.3.4 Witnesses-not-verdicts + §9.3.5 anchor-nonce sampling**,
//! and **M-anchor-2 P14.b §9.2.1 Birth Attestation**.
//!
//! L1/SCHEMA §2.2: "Every CI crossing: owner MUST co-sign current DAG-tip;
//! envelope MUST enumerate all DAG node hashes added since prior co-sign
//! (not summary diff) — substrate cannot hide parallel-branch forgery.
//! Substrate emits tip hash + enumerated node hashes + per-node metadata
//! (type, causal-parent-hashes) + proposed CI mutation as canonical bytes.
//! Owner verifies via Merkle-chain reconstruction; signs
//! (canonical_bytes_hash, anchor_timestamp, anchor_nonce)."
//!
//! L0/cards/AS_anchor_surface §3.4: owner-side workflow for verifying L0 doctrine changes
//! verbatim against prior commit hash. The substrate accepts an
//! owner-signed envelope recording (prior_l0_hash, new_l0_hash,
//! diff_summary, anchor_timestamp, anchor_nonce).
//!
//! M-anchor-5 is ADDITIVE: ships the canonical-bytes envelopes + DAG event
//! types + mutation_type handlers. CI enforcement (require cosign before
//! accepting any CI mutation) is deferred to M-anchor-5.5 alongside
//! owner-tooling support.

use super::hex_prefix;
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

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

// ---------------------------------------------------------------------------
// **P08 §3.2 / §3.5 / §5.1 — Reproduction cultivator co-attestation + I7
// spawn-closure**.
//
// L0/cards/P08 §5.1: spawning a child substrate is NOT a daily-mode mutation —
// it is a CI-class doctrine event that REQUIRES the cultivator's co-signature.
// An unattested spawn (any operator spawning on its own authority) is the
// "daily-mode spawn = doctrine collapse" signal → C68 reproduction_unattested_spawn.
//
// P08 §3.5 + L1/SCHEMA §3.3 spawn closure (I7) is a three-party handshake:
//   (a) parent runs STATIC-SCHEMA validation: the child's spore-schema
//       canonical bytes hash matches what the cultivator co-signed AND the
//       7-field shape is well-formed;
//   (b) the cultivator co-signs the spawn at the anchor surface, binding
//       (parent-substrate-ID, child-substrate-ID-derivation inputs,
//        spore-schema-hash, child-genesis-timestamp, anchor wall-clock + nonce);
//   (c) the child runs its OWN I3 self-validation as its first metabolic cycle
//       (substrate boot integrity self-check) before any operator cycle.
//
// This module ships the canonical-bytes envelope the cultivator signs
// (`myco-spawn-cosign-v1`), the `genesis_attested:{child_prefix}` I7-closure
// record emitted into the PARENT's DAG, and the
// `birth_closure_pending` / `birth_closure_complete` markers the child writes
// (b)→(c). Mirrors the M-anchor-5 dag_tip_cosign staged-envelope pattern.
// ---------------------------------------------------------------------------

/// Domain string for reproduction spawn co-sign signatures (P08 §3.5 / §5.1).
pub const SPAWN_COSIGN_DOMAIN: &str = "myco-spawn-cosign-v1";

/// Prefix for `genesis_attested:{child_id_prefix}` DAG events — the I7-closure
/// record written into the PARENT's DAG after a cultivator-attested spawn.
pub const NODE_TYPE_GENESIS_ATTESTED_PREFIX: &str = "genesis_attested:";

/// Prefix for `birth_closure_pending:{parent_id_prefix}` DAG events — written
/// into the CHILD's DAG at construction time, signalling the child must run its
/// own I3 boot self-check (I7 step c) before any operator cycle.
pub const NODE_TYPE_BIRTH_CLOSURE_PENDING_PREFIX: &str = "birth_closure_pending:";

/// Prefix for `birth_closure_complete:{child_id_prefix}` DAG events — written
/// into the CHILD's DAG at first boot once the I3 self-check verdict is known.
pub const NODE_TYPE_BIRTH_CLOSURE_COMPLETE_PREFIX: &str = "birth_closure_complete:";

/// Build the canonical-bytes Map the cultivator signs for a reproduction
/// spawn co-sign (P08 §3.5 / §5.1).
///
/// The envelope binds the immutable spawn parameters so that:
///   - `parent_substrate_id` is a replay guard (the substrate rejects an
///     envelope minted for a different parent);
///   - `spore_schema_hash` pins the child's static schema (I7 step a);
///   - `child_genesis_timestamp_unix_ns` feeds the deterministic
///     owner-minted child-id `blake3(parent_id, spore_schema_hash,
///     child_genesis_ts)` (§5.6 non-reissuance);
///   - `anchor_timestamp_unix_ns` + `anchor_nonce` are the anchor-surface
///     wall-clock + unbiasable nonce (§16.B rate throttle uses the timestamp);
///   - `depth_override` (Bool) is the cultivator's explicit, signed override
///     of the §16.A lineage-depth cap for THIS spawn (F22 depth_override).
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

/// Encode the body of a `genesis_attested:{child_prefix}` DAG event — the
/// I7-closure record in the PARENT's DAG (P08 §3.5).
///
/// Carries the cultivator-signed envelope bytes + signature + pubkey for
/// offline re-verification, the parent/child/spore binding, and a boolean
/// witness that the parent ran the child's static-schema validation
/// (I7 step a) and it passed.
/// ```text
/// Map({
///   "spawn_cosign_envelope":     Bytes,      // the bytes the cultivator signed
///   "owner_signature":           Bytes(64),
///   "owner_pubkey":              Bytes(32),
///   "parent_substrate_id":       Bytes(32),
///   "child_substrate_id":        Bytes(32),
///   "spore_schema_hash":         Bytes(32),
///   "child_static_schema_valid": Bool,       // I7(a) verdict
///   "emitted_at_cycle":          Uint,
/// })
/// ```
#[allow(clippy::too_many_arguments)]
pub fn encode_genesis_attested_event(
    spawn_cosign_envelope_bytes: &[u8],
    owner_signature: &[u8; 64],
    owner_pubkey: &[u8; 32],
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
        "owner_signature".to_string(),
        Value::Bytes(owner_signature.to_vec()),
    );
    m.insert(
        "owner_pubkey".to_string(),
        Value::Bytes(owner_pubkey.to_vec()),
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

/// Decode a `genesis_attested` DAG event body. Returns the parsed fields or
/// `None` on shape mismatch.
///
/// Tuple order: `(spawn_cosign_envelope, owner_signature, owner_pubkey,
/// parent_substrate_id, child_substrate_id, spore_schema_hash,
/// child_static_schema_valid, emitted_at_cycle)`.
#[allow(clippy::type_complexity)]
pub fn decode_genesis_attested_event(
    bytes: &[u8],
) -> Option<(
    Vec<u8>,
    [u8; 64],
    [u8; 32],
    [u8; 32],
    [u8; 32],
    [u8; 32],
    bool,
    u64,
)> {
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
    let sig = match m.get("owner_signature")? {
        Value::Bytes(b) if b.len() == 64 => {
            let mut arr = [0u8; 64];
            arr.copy_from_slice(b);
            arr
        }
        _ => return None,
    };
    let pubkey = bytes_to_arr32_local(m.get("owner_pubkey")?)?;
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
        sig,
        pubkey,
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
        let sig = [0x66u8; 64];
        let pubkey = [0x77u8; 32];
        let parent = [0x88u8; 32];
        let child = [0x99u8; 32];
        let spore_hash = [0xaau8; 32];
        let cycle: u64 = 4242;
        let body = encode_genesis_attested_event(
            &envelope, &sig, &pubkey, &parent, &child, &spore_hash, true, cycle,
        );
        let (env_out, sig_out, pk_out, p_out, c_out, sh_out, valid_out, cyc_out) =
            decode_genesis_attested_event(body.as_ref()).expect("decodes");
        assert_eq!(env_out, envelope);
        assert_eq!(sig_out, sig);
        assert_eq!(pk_out, pubkey);
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
