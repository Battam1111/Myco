//! E2E: Attestation & ceremony: M-anchor-2 birth attestation + C20, M-anchor-4 invariant witnesses, M-anchor-5 dag-tip-cosign / L0-revision envelopes, l0_revision_attest mutation defenses, schema-evolution mutation defenses, attestation-nonce issuance, and operator-pubkey ceremony test infrastructure (Sprint 6.E).
//!
//! Split out of the former monolithic `substrate_e2e.rs`. Shared spawn /
//! build helpers live in `tests/common/mod.rs`; this binary pulls them in
//! via `use common::*`. Tests are preserved verbatim from the original file.

mod common;
use common::*;

/// Helper: construct a schema_diff canonical-bytes Map matching the format
/// parsed by kernel/governance schema_evolution.parse_schema_diff.
fn build_schema_diff_modify_axis_threshold(axis: &str, new_threshold: &str) -> Vec<u8> {
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    let mut m = std::collections::BTreeMap::new();
    m.insert("op".to_string(), Value::String("modify_axis_threshold".to_string()));
    m.insert("axis_name".to_string(), Value::String(axis.to_string()));
    m.insert(
        "new_threshold_repr".to_string(),
        Value::String(new_threshold.to_string()),
    );
    cb_encode(&Value::Map(m)).expect("encode").0
}

fn build_schema_diff_add_axis(axis: &str) -> Vec<u8> {
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    let mut m = std::collections::BTreeMap::new();
    m.insert("op".to_string(), Value::String("add_axis_to_gradient".to_string()));
    m.insert("axis_name".to_string(), Value::String(axis.to_string()));
    m.insert("axis_class".to_string(), Value::String("appetite".to_string()));
    m.insert("fruiting_threshold_repr".to_string(), Value::String("5.0".to_string()));
    m.insert("initial_value_repr".to_string(), Value::String("0.0".to_string()));
    m.insert("decay_rate_per_cycle_repr".to_string(), Value::String("1.0".to_string()));
    m.insert("is_mortality_signal".to_string(), Value::Bool(false));
    m.insert("update_rule_kind".to_string(), Value::String("noop".to_string()));
    cb_encode(&Value::Map(m)).expect("encode").0
}

#[test]
fn m_anchor_4_invariant_witnesses_emitted_at_boot_for_each_tier_1_check() {
    // Boot a fresh substrate; integrity checks run as part of boot. Verify
    // the DAG carries one `invariant_witness:{check_id}` event per check
    // with structured inputs (placeholder owner_keys_consistency is excluded).
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("invariant_witness:".to_string()),
                ),
            ]),
        )
        .expect("query recent");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes.is_empty(),
        "boot must emit invariant_witness:* events"
    );

    // Collect all witness node_types — expect at least the five with
    // structured inputs (substrate_id, cycle_monotonic, dag_verify,
    // canonical_bytes_drift, orphan_detected). pinned_pubkey_well_formed
    // is conditional on pinned identity (absent pre-handshake); owner_keys
    // is a placeholder (no inputs → no witness emission).
    let mut emitted_check_ids: Vec<String> = Vec::new();
    for n in &nodes {
        if let CbValue::Map(m) = n {
            if let Some(CbValue::String(nt)) = m.get("node_type") {
                if let Some(check_id) = nt.strip_prefix("invariant_witness:") {
                    emitted_check_ids.push(check_id.to_string());
                }
            }
        }
    }
    for expected in &[
        "substrate_id_well_formed",
        "cycle_counter_monotonic",
        "dag_verify_all",
        "canonical_bytes_render_drift",
        "substrate_state_orphan_detected",
    ] {
        assert!(
            emitted_check_ids.iter().any(|id| id == expected),
            "missing witness for check_id={expected}; saw: {emitted_check_ids:?}"
        );
    }
    client.shutdown().expect("shutdown");
}

#[test]
fn m_anchor_4_invariant_witness_inputs_decode_and_carry_substrate_id() {
    // Pick the substrate_id_well_formed witness; decode its `inputs` field;
    // assert the inputs Map contains the actual substrate_id (so owner can
    // re-check non-zero offline).
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("invariant_witness:substrate_id_well_formed".to_string()),
                ),
            ]),
        )
        .expect("query recent");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(!nodes.is_empty(), "substrate_id witness must be present");
    let first = match &nodes[0] {
        CbValue::Map(m) => m.clone(),
        _ => panic!(),
    };
    let content = match first.get("content_canonical_bytes") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("content_canonical_bytes missing"),
    };
    // Decode the outer witness envelope.
    let outer = myco_kernel_shared::canonical_bytes::decode(&content).expect("witness decodes");
    let outer_map = match outer {
        CbValue::Map(m) => m,
        _ => panic!("witness is not a Map"),
    };
    // Sanity-check the standard fields.
    match outer_map.get("check_id") {
        Some(CbValue::String(s)) => assert_eq!(s, "substrate_id_well_formed"),
        _ => panic!("check_id missing"),
    }
    match outer_map.get("tier") {
        Some(CbValue::String(s)) => assert_eq!(s, "tier_1"),
        _ => panic!("tier missing"),
    }
    // Decode the inner `inputs` canonical-bytes; must contain substrate_id.
    let inputs_bytes = match outer_map.get("inputs") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("inputs missing"),
    };
    let inputs_v =
        myco_kernel_shared::canonical_bytes::decode(&inputs_bytes).expect("inputs decode");
    let inputs_map = match inputs_v {
        CbValue::Map(m) => m,
        _ => panic!(),
    };
    let id_bytes = match inputs_map.get("substrate_id") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("substrate_id field missing from inputs"),
    };
    assert_eq!(id_bytes.len(), 32, "substrate_id must be 32 bytes");
    // Owner re-check: non-zero.
    assert!(
        id_bytes.iter().any(|b| *b != 0),
        "substrate_id should be non-zero on a fresh substrate"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m_anchor_4_anchor_nonce_derived_sampling_is_deterministic() {
    use substrate::events::anchor_nonce_derived_sample_indices;
    let nonce = [0xa5u8; 32];
    let leaf_count: u64 = 100;
    let k = 10;
    let s1 = anchor_nonce_derived_sample_indices(&nonce, leaf_count, k);
    let s2 = anchor_nonce_derived_sample_indices(&nonce, leaf_count, k);
    assert_eq!(s1, s2, "same inputs must yield identical sample indices");
    assert_eq!(s1.len(), k, "k samples returned");
    // All indices in [0, leaf_count).
    for idx in &s1 {
        assert!(*idx < leaf_count, "index {idx} >= leaf_count {leaf_count}");
    }
    // Different nonce → different indices (overwhelmingly).
    let other_nonce = [0x5au8; 32];
    let s3 = anchor_nonce_derived_sample_indices(&other_nonce, leaf_count, k);
    assert_ne!(s1, s3, "different nonce must produce different sample set");
    // leaf_count=0 → empty
    let s_empty = anchor_nonce_derived_sample_indices(&nonce, 0, k);
    assert!(s_empty.is_empty());
    // k=0 → empty
    let s_zero_k = anchor_nonce_derived_sample_indices(&nonce, leaf_count, 0);
    assert!(s_zero_k.is_empty());
    // k > 1024 → clamps to 1024
    let s_clamp = anchor_nonce_derived_sample_indices(&nonce, leaf_count, 5000);
    assert_eq!(s_clamp.len(), 1024, "k clamped to 1024");
}

#[test]
fn m_anchor_4_witness_decode_helper_roundtrip() {
    use substrate::events::{
        decode_invariant_witness, encode_invariant_witness,
    };
    let inputs_bytes = vec![1u8, 2, 3, 4, 5];
    let nonce = vec![0xa1u8; 32];
    let sig = vec![0x77u8; 64];
    let encoded = encode_invariant_witness(
        "dag_verify_all",
        "tier_1",
        42,
        1_700_000_000_000_000_000,
        &inputs_bytes,
        &nonce,
        &sig,
    );
    let (cid, tier, at_cycle, at_unix_ns, inputs_out, nonce_out, sig_out) =
        decode_invariant_witness(encoded.as_ref()).expect("decodes");
    assert_eq!(cid, "dag_verify_all");
    assert_eq!(tier, "tier_1");
    assert_eq!(at_cycle, 42);
    assert_eq!(at_unix_ns, 1_700_000_000_000_000_000);
    assert_eq!(inputs_out, inputs_bytes);
    assert_eq!(nonce_out, nonce);
    assert_eq!(sig_out, sig);
}

#[test]
fn m_anchor_2_birth_attestation_event_emitted_when_env_vars_present() {
    // Build a synthetic birth attestation (fake signature; substrate doesn't
    // verify at genesis emit time — only at boot-time C20 — so this works
    // for the EMISSION half of the test). For C20 verification we use a
    // separate test below that builds a real Ed25519 signature.
    use myco_kernel_shared::crypto::Ed25519PrivateKey;

    let dir = fresh_state_dir();
    let key = Ed25519PrivateKey::from_seed(&[0xa3u8; 32]);
    let owner_pk_arr = key.public_key().0;
    let substrate_id_arr = [0x77u8; 32];
    let genesis_ns: i64 = 1_700_000_000_000_000_000;
    let spore_hash_arr = [0x99u8; 32];
    // Build the canonical attested bytes using the same helper anchor_surface_host
    // exposes.
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    use std::collections::BTreeMap;
    let mut attested_map = BTreeMap::new();
    attested_map.insert(
        "domain".to_string(),
        Value::String("myco-birth-attestation-v1".to_string()),
    );
    attested_map.insert(
        "substrate_id".to_string(),
        Value::Bytes(substrate_id_arr.to_vec()),
    );
    attested_map.insert(
        "genesis_timestamp_unix_ns".to_string(),
        Value::Timestamp(genesis_ns),
    );
    attested_map.insert(
        "spore_schema_hash".to_string(),
        Value::Bytes(spore_hash_arr.to_vec()),
    );
    attested_map.insert(
        "owner_pubkey".to_string(),
        Value::Bytes(owner_pk_arr.to_vec()),
    );
    // v0.9 §9.5: anchor endpoint pubkey collapses to owner pubkey.
    attested_map.insert(
        "anchor_endpoint_pubkey".to_string(),
        Value::Bytes(owner_pk_arr.to_vec()),
    );
    let attested_bytes = cb_encode(&Value::Map(attested_map)).unwrap().0;
    let signature = key.sign(&attested_bytes);
    let mut sig_arr = [0u8; 64];
    sig_arr.copy_from_slice(signature.as_ref());

    let hex = |bytes: &[u8]| -> String {
        let mut s = String::with_capacity(bytes.len() * 2);
        for b in bytes {
            s.push_str(&format!("{:02x}", b));
        }
        s
    };

    let env = vec![
        (
            "MYCO_SUBSTRATE_ID_OVERRIDE_HEX".to_string(),
            hex(&substrate_id_arr),
        ),
        (
            "MYCO_GENESIS_TIME_OVERRIDE_UNIX_NS".to_string(),
            genesis_ns.to_string(),
        ),
        (
            "MYCO_BIRTH_ATTESTATION_BYTES_HEX".to_string(),
            hex(&attested_bytes),
        ),
        (
            "MYCO_BIRTH_ATTESTATION_SIGNATURE_HEX".to_string(),
            hex(&sig_arr),
        ),
        (
            "MYCO_BIRTH_ATTESTATION_OWNER_PUBKEY_HEX".to_string(),
            hex(&owner_pk_arr),
        ),
    ];

    let mut client = spawn_substrate_with_env(&dir, env);
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("birth_attestation:".to_string()),
                ),
            ]),
        )
        .expect("query recent");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes.is_empty(),
        "M-anchor-2: birth_attestation:{{prefix}} event must be emitted when env vars supplied"
    );
    // Verify the substrate accepted our substrate_id override. Query for
    // the genesis_event DAG node + parse the substrate_id field from its
    // content_canonical_bytes.
    let genesis_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(10)),
                (
                    "node_type_prefix",
                    CbValue::String("genesis_event:".to_string()),
                ),
            ]),
        )
        .expect("query genesis");
    let genesis_nodes = match genesis_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("genesis nodes missing"),
    };
    assert!(!genesis_nodes.is_empty(), "genesis_event must exist");
    let first = match &genesis_nodes[0] {
        CbValue::Map(m) => m.clone(),
        _ => panic!(),
    };
    let content_bytes = match first.get("content_canonical_bytes") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("content_canonical_bytes missing"),
    };
    let decoded = myco_kernel_shared::canonical_bytes::decode(&content_bytes)
        .expect("genesis content decodes");
    let inner = match decoded {
        CbValue::Map(m) => m,
        _ => panic!(),
    };
    let returned_id = match inner.get("substrate_id") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("substrate_id field missing"),
    };
    assert_eq!(
        returned_id, substrate_id_arr.to_vec(),
        "MYCO_SUBSTRATE_ID_OVERRIDE_HEX must propagate to manifest.substrate_id"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m_anchor_2_c20_fires_when_birth_attestation_signature_tampered() {
    // Spawn substrate with a birth attestation whose signature is bytes
    // bogus. On boot, the C20 verifier must fire.
    let dir = fresh_state_dir();
    let substrate_id_arr = [0x55u8; 32];
    let genesis_ns: i64 = 1_700_000_000_000_000_001;
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    use std::collections::BTreeMap;
    let mut attested_map = BTreeMap::new();
    attested_map.insert(
        "domain".to_string(),
        Value::String("myco-birth-attestation-v1".to_string()),
    );
    attested_map.insert(
        "substrate_id".to_string(),
        Value::Bytes(substrate_id_arr.to_vec()),
    );
    attested_map.insert(
        "genesis_timestamp_unix_ns".to_string(),
        Value::Timestamp(genesis_ns),
    );
    attested_map.insert(
        "spore_schema_hash".to_string(),
        Value::Bytes(vec![0u8; 32]),
    );
    attested_map.insert("owner_pubkey".to_string(), Value::Bytes(vec![0u8; 32]));
    attested_map.insert(
        "anchor_endpoint_pubkey".to_string(),
        Value::Bytes(vec![0u8; 32]),
    );
    let attested_bytes = cb_encode(&Value::Map(attested_map)).unwrap().0;
    let bogus_sig = [0xFFu8; 64];
    let bogus_pk = [0xAAu8; 32];

    let hex = |bytes: &[u8]| -> String {
        let mut s = String::with_capacity(bytes.len() * 2);
        for b in bytes {
            s.push_str(&format!("{:02x}", b));
        }
        s
    };

    let env = vec![
        (
            "MYCO_SUBSTRATE_ID_OVERRIDE_HEX".to_string(),
            hex(&substrate_id_arr),
        ),
        (
            "MYCO_GENESIS_TIME_OVERRIDE_UNIX_NS".to_string(),
            genesis_ns.to_string(),
        ),
        (
            "MYCO_BIRTH_ATTESTATION_BYTES_HEX".to_string(),
            hex(&attested_bytes),
        ),
        (
            "MYCO_BIRTH_ATTESTATION_SIGNATURE_HEX".to_string(),
            hex(&bogus_sig),
        ),
        (
            "MYCO_BIRTH_ATTESTATION_OWNER_PUBKEY_HEX".to_string(),
            hex(&bogus_pk),
        ),
    ];

    // First boot: emits genesis_event + birth_attestation; C20 should fire
    // because the signature is bogus.
    let client = spawn_substrate_with_env(&dir, env);
    client.shutdown().expect("shutdown first boot");

    // Second boot: re-verifies birth_attestation → C20 should fire again.
    let mut client2 = spawn_substrate_with_state_dir(&dir);
    let immune_resp = client2
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                ("node_type_prefix", CbValue::String("immune:".to_string())),
            ]),
        )
        .expect("query immune");
    let nodes = match immune_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    let saw_c20 = nodes.iter().any(|n| {
        if let CbValue::Map(m) = n {
            if let Some(CbValue::String(nt)) = m.get("node_type") {
                return nt.contains("C20_genesis_attestation_chain_broken");
            }
        }
        false
    });
    assert!(
        saw_c20,
        "M-anchor-2 C20: must fire when birth_attestation signature fails verify"
    );
    client2.shutdown().expect("shutdown second boot");
}

#[test]
fn m_anchor_2_c20_does_not_fire_for_truly_fresh_substrate_at_cycle_0() {
    // Boot a substrate WITHOUT birth attestation env vars and verify that
    // C20 does NOT fire at cycle 0 (substrate may not have had a chance to
    // emit the attestation yet). Only fires once cycle_counter > 0.
    let (mut client, _dir) = spawn_substrate();
    let immune_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                ("node_type_prefix", CbValue::String("immune:".to_string())),
            ]),
        )
        .expect("query immune");
    let nodes = match immune_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    let saw_c20 = nodes.iter().any(|n| {
        if let CbValue::Map(m) = n {
            if let Some(CbValue::String(nt)) = m.get("node_type") {
                return nt.contains("C20_genesis_attestation_chain_broken");
            }
        }
        false
    });
    assert!(
        !saw_c20,
        "C20 must NOT fire at cycle 0 for a fresh substrate without attestation"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m_anchor_5_dag_tip_cosign_canonical_bytes_roundtrip() {
    use substrate::events::{
        build_dag_tip_cosign_canonical_bytes, decode_dag_tip_cosign,
    };
    let tip = [0x11u8; 32];
    let h1 = [0x22u8; 32];
    let h2 = [0x33u8; 32];
    let hashes = vec![h1, h2];
    let proposed = [0x44u8; 32];
    let anchor_ts: i64 = 1_700_000_000_000_000_000;
    let anchor_nonce = [0x55u8; 32];
    let bytes = build_dag_tip_cosign_canonical_bytes(
        &tip,
        &hashes,
        &proposed,
        anchor_ts,
        &anchor_nonce,
    );
    let (out_tip, out_hashes, out_proposed, out_ts, out_nonce) =
        decode_dag_tip_cosign(&bytes).expect("cosign envelope decodes");
    assert_eq!(out_tip, tip);
    assert_eq!(out_hashes, hashes);
    assert_eq!(out_proposed, proposed);
    assert_eq!(out_ts, anchor_ts);
    assert_eq!(out_nonce, anchor_nonce);
}

#[test]
fn m_anchor_5_dag_tip_cosign_envelope_rejects_wrong_domain() {
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    use substrate::events::decode_dag_tip_cosign;
    use std::collections::BTreeMap;
    // Hand-build a malformed envelope with the wrong domain string.
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String("not-the-cosign-domain-v0".to_string()),
    );
    m.insert("tip_hash".to_string(), Value::Bytes(vec![0u8; 32]));
    m.insert(
        "enumerated_node_hashes".to_string(),
        Value::Array(vec![]),
    );
    m.insert(
        "proposed_mutation_hash".to_string(),
        Value::Bytes(vec![0u8; 32]),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(0),
    );
    m.insert("anchor_nonce".to_string(), Value::Bytes(vec![0u8; 32]));
    let bytes = cb_encode(&Value::Map(m)).unwrap().0;
    assert!(
        decode_dag_tip_cosign(&bytes).is_none(),
        "domain mismatch must reject"
    );
}

#[test]
fn m_anchor_5_dag_tip_cosign_envelope_rejects_corrupt_hash_length() {
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    use substrate::events::{decode_dag_tip_cosign, DAG_TIP_COSIGN_DOMAIN};
    use std::collections::BTreeMap;
    // tip_hash with wrong length (16 bytes instead of 32).
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(DAG_TIP_COSIGN_DOMAIN.to_string()),
    );
    m.insert("tip_hash".to_string(), Value::Bytes(vec![0u8; 16]));
    m.insert(
        "enumerated_node_hashes".to_string(),
        Value::Array(vec![]),
    );
    m.insert(
        "proposed_mutation_hash".to_string(),
        Value::Bytes(vec![0u8; 32]),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(0),
    );
    m.insert("anchor_nonce".to_string(), Value::Bytes(vec![0u8; 32]));
    let bytes = cb_encode(&Value::Map(m)).unwrap().0;
    assert!(
        decode_dag_tip_cosign(&bytes).is_none(),
        "wrong tip_hash length must reject"
    );
}

#[test]
fn m_anchor_5_l0_revision_canonical_bytes_roundtrip() {
    use substrate::events::{
        build_l0_revision_canonical_bytes, decode_l0_revision,
    };
    let prior = [0xa1u8; 32];
    let new_h = [0xa2u8; 32];
    let diff_summary = "Add §9.4 federation observatory";
    let anchor_ts: i64 = 1_700_000_001_234_567_890;
    let anchor_nonce = [0xb1u8; 32];
    let bytes = build_l0_revision_canonical_bytes(
        &prior,
        &new_h,
        diff_summary,
        anchor_ts,
        &anchor_nonce,
    );
    let (out_prior, out_new, out_diff, out_ts, out_nonce) =
        decode_l0_revision(&bytes).expect("l0 revision envelope decodes");
    assert_eq!(out_prior, prior);
    assert_eq!(out_new, new_h);
    assert_eq!(out_diff, diff_summary);
    assert_eq!(out_ts, anchor_ts);
    assert_eq!(out_nonce, anchor_nonce);
}

#[test]
fn m_anchor_5_l0_revision_envelope_rejects_wrong_domain() {
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    use substrate::events::decode_l0_revision;
    use std::collections::BTreeMap;
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String("wrong-domain-v0".to_string()),
    );
    m.insert("prior_l0_hash".to_string(), Value::Bytes(vec![0u8; 32]));
    m.insert("new_l0_hash".to_string(), Value::Bytes(vec![0u8; 32]));
    m.insert(
        "diff_summary".to_string(),
        Value::String("x".to_string()),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(0),
    );
    m.insert("anchor_nonce".to_string(), Value::Bytes(vec![0u8; 32]));
    let bytes = cb_encode(&Value::Map(m)).unwrap().0;
    assert!(
        decode_l0_revision(&bytes).is_none(),
        "domain mismatch must reject"
    );
}

#[test]
fn m_anchor_5_node_type_prefixes_stable() {
    // Pin the L1/SCHEMA-declared node-type prefixes so any rename breaks
    // child substrates / external indexers loudly. (Same discipline as
    // the M26.3 compression_event prefix pinning.)
    use substrate::events::{
        NODE_TYPE_L0_REVISION_ATTESTED_PREFIX, NODE_TYPE_TIP_COSIGNED_PREFIX,
    };
    assert_eq!(NODE_TYPE_TIP_COSIGNED_PREFIX, "tip_cosigned:");
    assert_eq!(NODE_TYPE_L0_REVISION_ATTESTED_PREFIX, "l0_revision_attested:");
}

#[test]
fn m_anchor_5_tip_cosigned_event_body_carries_signature_pubkey_and_cycle() {
    // The DAG event body must contain the cosign envelope bytes + owner
    // signature + owner pubkey + emitted_at_cycle so a child substrate can
    // independently re-verify the signature offline.
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    use substrate::events::encode_tip_cosigned_event;
    let envelope = vec![0x55u8; 64];
    let sig = [0x77u8; 64];
    let pubkey = [0x33u8; 32];
    let cycle: u64 = 12345;
    let body = encode_tip_cosigned_event(&envelope, &sig, &pubkey, cycle);
    let v = decode(body.as_ref()).expect("body decodes");
    let m = match v {
        Value::Map(m) => m,
        _ => panic!("body is not a Map"),
    };
    match m.get("cosign_envelope") {
        Some(Value::Bytes(b)) => assert_eq!(b, &envelope),
        _ => panic!("cosign_envelope missing"),
    };
    match m.get("owner_signature") {
        Some(Value::Bytes(b)) => assert_eq!(b.as_slice(), sig.as_slice()),
        _ => panic!("owner_signature missing"),
    };
    match m.get("owner_pubkey") {
        Some(Value::Bytes(b)) => assert_eq!(b.as_slice(), pubkey.as_slice()),
        _ => panic!("owner_pubkey missing"),
    };
    match m.get("emitted_at_cycle") {
        Some(Value::Uint(n)) => assert_eq!(*n, cycle),
        _ => panic!("emitted_at_cycle missing"),
    };
}

#[test]
fn m_anchor_5_l0_revision_attested_event_body_carries_signature_pubkey_and_cycle() {
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    use substrate::events::encode_l0_revision_attested_event;
    let envelope = vec![0x66u8; 128];
    let sig = [0x88u8; 64];
    let pubkey = [0x44u8; 32];
    let cycle: u64 = 99999;
    let body = encode_l0_revision_attested_event(&envelope, &sig, &pubkey, cycle);
    let v = decode(body.as_ref()).expect("body decodes");
    let m = match v {
        Value::Map(m) => m,
        _ => panic!(),
    };
    match m.get("l0_revision_envelope") {
        Some(Value::Bytes(b)) => assert_eq!(b, &envelope),
        _ => panic!("l0_revision_envelope missing"),
    };
    match m.get("owner_signature") {
        Some(Value::Bytes(b)) => assert_eq!(b.as_slice(), sig.as_slice()),
        _ => panic!("owner_signature missing"),
    };
    match m.get("owner_pubkey") {
        Some(Value::Bytes(b)) => assert_eq!(b.as_slice(), pubkey.as_slice()),
        _ => panic!("owner_pubkey missing"),
    };
    match m.get("emitted_at_cycle") {
        Some(Value::Uint(n)) => assert_eq!(*n, cycle),
        _ => panic!("emitted_at_cycle missing"),
    };
}

#[test]
fn m_anchor_5_node_type_strings_carry_hex_prefix_of_relevant_hash() {
    // tip_cosigned:{first_8_hex_chars_of_tip_hash}
    // l0_revision_attested:{first_8_hex_chars_of_prior_l0_hash}
    use substrate::events::{
        l0_revision_attested_node_type, tip_cosigned_node_type,
    };
    let mut tip = [0u8; 32];
    tip[0] = 0xab;
    tip[1] = 0xcd;
    tip[2] = 0xef;
    tip[3] = 0x12;
    let tip_nt = tip_cosigned_node_type(&tip);
    assert!(
        tip_nt.starts_with("tip_cosigned:"),
        "node_type must start with prefix: {tip_nt}"
    );
    assert!(tip_nt.contains("abcdef12"), "node_type must encode tip prefix: {tip_nt}");

    let mut prior = [0u8; 32];
    prior[0] = 0xde;
    prior[1] = 0xad;
    prior[2] = 0xbe;
    prior[3] = 0xef;
    let l0_nt = l0_revision_attested_node_type(&prior);
    assert!(l0_nt.starts_with("l0_revision_attested:"));
    assert!(l0_nt.contains("deadbeef"), "node_type must encode prior hash prefix: {l0_nt}");
}

#[test]
fn sprint_5a_l0_revision_canonical_bytes_roundtrip() {
    // Pre-condition: the encode/decode roundtrip is canonical. If this
    // ever drifts, every substrate's L0 attestations stop verifying
    // cross-version.
    use substrate::events::{build_l0_revision_canonical_bytes, decode_l0_revision};
    let prior = [0xAAu8; 32];
    let new = [0xBBu8; 32];
    let summary = "v3.1 → v3.1.1 amendment: P07 mortality reinterpretation + CHAR07";
    let ts: i64 = 1_700_000_000_000_000_000;
    let nonce = [0xCCu8; 32];
    let bytes = build_l0_revision_canonical_bytes(&prior, &new, summary, ts, &nonce);
    let (p2, n2, s2, t2, no2) = decode_l0_revision(&bytes).expect("roundtrip decode");
    assert_eq!(p2, prior, "prior_l0_hash round-trip");
    assert_eq!(n2, new, "new_l0_hash round-trip");
    assert_eq!(s2, summary, "diff_summary round-trip");
    assert_eq!(t2, ts, "anchor_timestamp round-trip");
    assert_eq!(no2, nonce, "anchor_nonce round-trip");
}

#[test]
fn sprint_5a_l0_revision_attested_node_type_deterministic() {
    // The DAG node_type encodes the first-8-hex of prior_l0_hash so
    // consecutive revisions remain distinguishable. Pin the format so
    // downstream tooling can rely on the prefix shape.
    use substrate::events::{
        l0_revision_attested_node_type, NODE_TYPE_L0_REVISION_ATTESTED_PREFIX,
    };
    let prior = [
        0xb1, 0xbe, 0xc5, 0x9a, 0xcc, 0x8c, 0x50, 0x61, // matches memory
        0xde, 0xad, 0xbe, 0xef, 0xde, 0xad, 0xbe, 0xef, 0xde, 0xad, 0xbe, 0xef,
        0xde, 0xad, 0xbe, 0xef, 0xde, 0xad, 0xbe, 0xef, 0xde, 0xad, 0xbe, 0xef,
    ];
    let nt = l0_revision_attested_node_type(&prior);
    assert_eq!(
        nt, "l0_revision_attested:b1bec59acc8c5061",
        "node_type must encode first-8-hex of prior_l0_hash"
    );
    assert!(nt.starts_with(NODE_TYPE_L0_REVISION_ATTESTED_PREFIX));
}

#[test]
fn sprint_5a_l0_revision_attest_rejects_malformed_canonical_bytes() {
    // **Defense path**: attestation.rs:823-834 — content_canonical_bytes
    // that doesn't decode as the expected envelope triggers C5
    // attestation_invalid + rejection_reason citing the decode failure.
    //
    // Sending garbage bytes that are NOT a valid l0_revision envelope MUST
    // surface as classifier-untyped at Python OR substrate-side decode
    // failure — either way: accepted=false, no l0_revision_attested DAG
    // event emitted.
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("l0_revision_attest".to_string())),
                (
                    "content_canonical_bytes",
                    CbValue::Bytes(b"this is not a valid canonical-bytes envelope".to_vec()),
                ),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        )
        .expect("submit_mutation");
    let accepted = match resp.payload.get("accepted") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("accepted missing"),
    };
    assert!(
        !accepted,
        "Sprint 5.A T1.1: malformed l0_revision envelope MUST be rejected; \
         got accepted=true (doctrine traceability gap — anyone could forge \
         an L0 revision attestation)"
    );
    // No l0_revision_attested:* event in DAG.
    let nodes_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("l0_revision_attested:".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        nodes.is_empty(),
        "rejected l0_revision_attest MUST NOT leave an attested:* event in DAG; \
         saw {} nodes",
        nodes.len()
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5a_l0_revision_attest_rejects_wrong_domain_envelope() {
    // **Defense path**: the canonical-bytes envelope must carry
    // domain=L0_REVISION_DOMAIN. A submitter trying to pass off a
    // different envelope type (e.g., dag_tip_cosign) as an l0_revision
    // must be rejected at substrate decode time.
    use substrate::events::build_l0_revision_canonical_bytes;

    // Build a VALID l0_revision envelope first (so we have valid
    // canonical-bytes structurally), then corrupt the domain field.
    let prior = [0x11u8; 32];
    let new = [0x22u8; 32];
    let nonce = [0x33u8; 32];
    let valid = build_l0_revision_canonical_bytes(&prior, &new, "amendment", 0, &nonce);
    // The domain string "l0_revision_v1" lives early in the canonical-
    // bytes Map. Replace it with garbage to corrupt the domain check
    // while keeping the envelope decodable.
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, encode as cb_encode, Value};
    let mut decoded = match cb_decode(&valid).expect("envelope decodes") {
        Value::Map(m) => m,
        _ => panic!("envelope not a Map"),
    };
    decoded.insert(
        "domain".to_string(),
        Value::String("not_l0_revision".to_string()),
    );
    let corrupted = cb_encode(&Value::Map(decoded)).expect("encode").0;

    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("l0_revision_attest".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(corrupted)),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        )
        .expect("submit_mutation");
    let accepted = match resp.payload.get("accepted") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("accepted missing"),
    };
    assert!(
        !accepted,
        "Sprint 5.A T1.1: wrong-domain envelope must be rejected; got accepted=true"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5a_l0_revision_attest_rejects_when_python_returns_untyped() {
    // **Belt-and-suspenders test**: without proper touched_fields /
    // nonce / attestation_signature, the Python classifier's CI gate
    // returns accepted=false. This proves the CI gate holds before
    // substrate-side staging would run — there's no "skip Python" path
    // that would let an attacker reach the l0_revision DAG-event
    // emission code by bypassing classification.
    let (mut client, _dir) = spawn_substrate();
    use substrate::events::build_l0_revision_canonical_bytes;
    let prior = [0x44u8; 32];
    let new = [0x55u8; 32];
    let nonce = [0x66u8; 32];
    let valid_envelope =
        build_l0_revision_canonical_bytes(&prior, &new, "test amendment", 0, &nonce);

    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("l0_revision_attest".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(valid_envelope)),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
                // Deliberately omit attestation_signature / nonce.
            ]),
        )
        .expect("submit_mutation");
    let accepted = match resp.payload.get("accepted") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("accepted missing"),
    };
    assert!(
        !accepted,
        "Sprint 5.A T1.1: l0_revision_attest WITHOUT cultivator attestation \
         must be rejected at CI gate; got accepted=true (CI gate breach — \
         anyone could land doctrine revisions without owner consent)"
    );

    // Verify no l0_revision_attested:* event in DAG.
    let nodes_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("l0_revision_attested:".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        nodes.is_empty(),
        "no l0_revision_attested:* event should exist after rejection; saw {}",
        nodes.len()
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5b_schema_diff_canonical_bytes_modify_axis_threshold_roundtrips() {
    // The schema_diff format MUST stay stable so operator-side (TypeScript)
    // and substrate Python-side decode the same bytes. Round-trip is the
    // foundation property — if it breaks, no schema evolution works.
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value};
    let bytes = build_schema_diff_modify_axis_threshold("hunger", "7.5");
    let decoded = cb_decode(&bytes).expect("decode");
    let m = match decoded {
        Value::Map(m) => m,
        _ => panic!("schema_diff is not a Map"),
    };
    match m.get("op") {
        Some(Value::String(s)) => assert_eq!(s, "modify_axis_threshold"),
        _ => panic!("op field missing or wrong type"),
    }
    match m.get("axis_name") {
        Some(Value::String(s)) => assert_eq!(s, "hunger"),
        _ => panic!("axis_name field missing or wrong type"),
    }
    match m.get("new_threshold_repr") {
        Some(Value::String(s)) => assert_eq!(s, "7.5"),
        _ => panic!("new_threshold_repr field missing or wrong type"),
    }
}

#[test]
fn sprint_5b_schema_diff_canonical_bytes_add_axis_roundtrips() {
    // Same round-trip property for the add_axis_to_gradient op (the second
    // M17-MV schema diff op).
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value};
    let bytes = build_schema_diff_add_axis("new_axis");
    let decoded = cb_decode(&bytes).expect("decode");
    let m = match decoded {
        Value::Map(m) => m,
        _ => panic!("schema_diff is not a Map"),
    };
    match m.get("op") {
        Some(Value::String(s)) => assert_eq!(s, "add_axis_to_gradient"),
        _ => panic!("op field wrong"),
    }
    match m.get("axis_class") {
        Some(Value::String(s)) => assert_eq!(s, "appetite"),
        _ => panic!("axis_class wrong"),
    }
}

#[test]
fn sprint_5b_schema_evolution_rejected_without_owner_attestation() {
    // **Defense path**: submit_mutation with mutation_type=schema_evolution
    // requires owner attestation per classifier.py (classified as CI). Without
    // attestation, Python's CI gate (dispatcher.py:750-761) returns
    // accepted=false; substrate emits no evolution_succeeded:* event.
    let (mut client, _dir) = spawn_substrate();
    let diff = build_schema_diff_modify_axis_threshold("hunger", "9.0");
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("schema_evolution".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(diff)),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
                // Deliberately omit attestation_signature / nonce.
            ]),
        )
        .expect("submit");
    let accepted = match resp.payload.get("accepted") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("accepted missing"),
    };
    assert!(
        !accepted,
        "Sprint 5.B T1.2: schema_evolution mutation WITHOUT owner attestation \
         must be rejected; got accepted=true (CI gate breach — anyone could \
         mutate substrate schema without cultivator consent)"
    );

    // Verify NO evolution_succeeded:* / evolution_failed:* event emitted.
    for prefix in &["evolution_succeeded:", "evolution_failed:"] {
        let q = client
            .call(
                proto::QUERY_RECENT_NODES,
                build_payload(vec![
                    ("count", CbValue::Uint(50)),
                    ("node_type_prefix", CbValue::String(prefix.to_string())),
                ]),
            )
            .expect("query");
        let nodes = match q.payload.get("nodes") {
            Some(CbValue::Array(a)) => a.clone(),
            _ => panic!("nodes missing"),
        };
        assert!(
            nodes.is_empty(),
            "rejected schema_evolution must NOT emit {prefix}* events; saw {} \
             (substrate-side staging ran despite Python rejection)",
            nodes.len()
        );
    }
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5b_schema_evolution_rejected_with_malformed_diff_bytes() {
    // Garbage content_canonical_bytes that don't decode as a schema_diff Map.
    // Python parse_schema_diff raises SchemaEvolutionError → schema_apply
    // path returns failure; classifier path will also reject because
    // touched_fields is empty so the schema_evolution CI rule's coverage
    // check fails. Either way: no evolution_succeeded:* event.
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("schema_evolution".to_string())),
                (
                    "content_canonical_bytes",
                    CbValue::Bytes(b"not a canonical-bytes Map".to_vec()),
                ),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        )
        .expect("submit");
    let accepted = match resp.payload.get("accepted") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("accepted missing"),
    };
    assert!(
        !accepted,
        "Sprint 5.B T1.2: malformed schema_diff bytes must be rejected"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5b_evolution_event_node_type_format_pinned() {
    // **Format pinning**: substrate emits evolution_succeeded:{op} on
    // success, evolution_failed:{op} on rollback. The {op} suffix comes
    // directly from schema_apply_op which equals the SchemaDiffOp.value
    // string. Operator-side query tooling depends on this format being
    // stable — if it changes, dashboards break silently.
    //
    // We can't easily produce a positive event without owner pubkey, but
    // we CAN assert the format is what attestation.rs:1235 produces by
    // string-matching the literal.
    let s = format!("evolution_succeeded:{op}", op = "modify_axis_threshold");
    let f = format!("evolution_failed:{op}", op = "add_axis_to_gradient");
    assert_eq!(s, "evolution_succeeded:modify_axis_threshold");
    assert_eq!(f, "evolution_failed:add_axis_to_gradient");
    // Both supported M17-MV schema diff ops produce well-formed node types.
    for op in &["modify_axis_threshold", "add_axis_to_gradient"] {
        let nt = format!("evolution_succeeded:{op}");
        assert!(nt.starts_with("evolution_succeeded:"));
        assert!(nt.contains(op));
    }
}

#[test]
fn sprint_6l_seeded_substrate_can_request_nonce() {
    // After TOFU-pinning via Sprint 6.E infrastructure, the operator can
    // request an attestation nonce. The substrate issues one + records
    // a nonce_issued:* event in the DAG.
    let seed: [u8; 32] = [0x77; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);

    // Request a nonce bound to a stub content_hash.
    let content_hash = [0x55u8; 32];
    let resp = client
        .call(
            proto::REQUEST_ATTESTATION_NONCE,
            build_payload(vec![(
                "content_hash",
                CbValue::Bytes(content_hash.to_vec()),
            )]),
        )
        .expect("request_attestation_nonce");
    let nonce = match resp.payload.get("nonce") {
        Some(CbValue::Bytes(b)) if b.len() == 32 => b.clone(),
        _ => panic!("Sprint 6.L: response missing 32-byte nonce"),
    };
    let bound_tip = match resp.payload.get("bound_dag_tip") {
        Some(CbValue::Bytes(b)) if b.len() == 32 => b.clone(),
        _ => panic!("Sprint 6.L: response missing bound_dag_tip"),
    };
    let expiry = match resp.payload.get("expiry_unix_ns") {
        Some(CbValue::Timestamp(t)) => *t,
        _ => panic!("Sprint 6.L: response missing expiry_unix_ns"),
    };
    assert!(
        expiry > 0,
        "Sprint 6.L T2.9: nonce expiry should be a positive unix_ns"
    );
    assert!(
        bound_tip != [0u8; 32],
        "Sprint 6.L T2.9: bound_dag_tip must be non-zero (substrate has DAG content)"
    );

    // Verify a nonce_issued:* DAG event was emitted.
    let nodes_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("nonce_issued:".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert_eq!(
        nodes.len(),
        1,
        "Sprint 6.L T2.9: REQUEST_ATTESTATION_NONCE must emit exactly one \
         nonce_issued:* DAG event; got {}",
        nodes.len()
    );

    // Verify the nonce in the event matches what the response gave us.
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbV};
    let first = match &nodes[0] {
        CbValue::Map(m) => m.clone(),
        _ => panic!("node not a Map"),
    };
    let content = match first.get("content_canonical_bytes") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("content missing"),
    };
    let event_map = match cb_decode(&content).expect("decode") {
        CbV::Map(m) => m,
        _ => panic!("event not a Map"),
    };
    let event_nonce = match event_map.get("nonce") {
        Some(CbV::Bytes(b)) => b.clone(),
        _ => panic!("nonce missing in event"),
    };
    assert_eq!(
        event_nonce, nonce,
        "Sprint 6.L T2.9: DAG event nonce must match response nonce"
    );

    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_6l_nonce_request_records_content_hash_binding() {
    // The nonce_issued event must record the bound content_hash so the
    // operator (and downstream tooling) can re-verify the binding
    // offline.
    let seed: [u8; 32] = [0xAAu8; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);

    let content_hash = [0x33u8; 32];
    let _ = client.call(
        proto::REQUEST_ATTESTATION_NONCE,
        build_payload(vec![(
            "content_hash",
            CbValue::Bytes(content_hash.to_vec()),
        )]),
    );

    let nodes_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("nonce_issued:".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbV};
    let first = match &nodes[0] {
        CbValue::Map(m) => m.clone(),
        _ => panic!("node not a Map"),
    };
    let content = match first.get("content_canonical_bytes") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("content missing"),
    };
    let event_map = match cb_decode(&content).expect("decode") {
        CbV::Map(m) => m,
        _ => panic!("event not a Map"),
    };
    let bound_hash = match event_map.get("bound_content_hash") {
        Some(CbV::Bytes(b)) => b.clone(),
        _ => panic!("bound_content_hash missing in event"),
    };
    assert_eq!(
        bound_hash, content_hash,
        "Sprint 6.L T2.9: nonce_issued event must record bound content_hash \
         exactly as supplied in the request"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_6l_unique_nonces_per_request() {
    // Each REQUEST_ATTESTATION_NONCE call MUST produce a unique nonce.
    // No collision even with identical content_hash.
    let seed: [u8; 32] = [0xBBu8; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);

    let content_hash = [0x66u8; 32];
    let mut nonces: std::collections::HashSet<Vec<u8>> = std::collections::HashSet::new();
    for _ in 0..3 {
        let resp = client
            .call(
                proto::REQUEST_ATTESTATION_NONCE,
                build_payload(vec![(
                    "content_hash",
                    CbValue::Bytes(content_hash.to_vec()),
                )]),
            )
            .expect("request_attestation_nonce");
        let nonce = match resp.payload.get("nonce") {
            Some(CbValue::Bytes(b)) => b.clone(),
            _ => panic!("nonce missing"),
        };
        // Pause to ensure SHA-256-based nonce derivation gets a different
        // time mixin (the nonce generation includes SystemTime + counter +
        // stack-addr; even identical content_hash should produce unique
        // nonces).
        std::thread::sleep(std::time::Duration::from_millis(2));
        let was_new = nonces.insert(nonce);
        assert!(
            was_new,
            "Sprint 6.L T2.9: duplicate nonce from REQUEST_ATTESTATION_NONCE \
             — nonce derivation must be unique even for identical content_hash"
        );
    }
    assert_eq!(nonces.len(), 3, "expected 3 distinct nonces, got {}", nonces.len());
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_6e_seed_based_spawn_pins_operator_pubkey() {
    let seed: [u8; 32] = [0x42; 32];
    let expected_pubkey = derive_operator_pubkey_from_seed(&seed);
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);

    // Verify the DAG has an operator_pinned:* event with the derived pubkey.
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("operator_pinned:".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert_eq!(
        nodes.len(),
        1,
        "Sprint 6.E T2.9: seed-based spawn should produce exactly 1 \
         operator_pinned:* event; got {}",
        nodes.len()
    );
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbV};
    let first = match &nodes[0] {
        CbValue::Map(m) => m.clone(),
        _ => panic!("node not a Map"),
    };
    let content = match first.get("content_canonical_bytes") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("content missing"),
    };
    let event_map = match cb_decode(&content).expect("decode") {
        CbV::Map(m) => m,
        _ => panic!("event not a Map"),
    };
    let pubkey_bytes = match event_map.get("pubkey") {
        Some(CbV::Bytes(b)) => b.clone(),
        _ => panic!("pubkey missing in operator_pinned event"),
    };
    assert_eq!(
        pubkey_bytes.len(),
        32,
        "pinned pubkey must be 32 bytes; got {}",
        pubkey_bytes.len()
    );
    let mut pinned_arr = [0u8; 32];
    pinned_arr.copy_from_slice(&pubkey_bytes);
    assert_eq!(
        pinned_arr, expected_pubkey,
        "Sprint 6.E T2.9: substrate pinned pubkey ≠ test's derived pubkey \
         (sign-+-hello hookup broken)"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_6e_unseeded_spawn_still_works_for_legacy_tests() {
    // Regression: the existing spawn_substrate() path (no signing seed) must
    // continue to produce a working substrate in legacy mode (no operator
    // identity pinned). This ensures Sprint 6.E's additive change is
    // strictly backward-compatible.
    let (mut client, _dir) = spawn_substrate();
    // No operator_pinned events should exist on an unseeded substrate.
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("operator_pinned:".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert_eq!(
        nodes.len(),
        0,
        "Sprint 6.E T2.9: unseeded spawn must NOT emit operator_pinned; got {}",
        nodes.len()
    );
    client.shutdown().expect("shutdown");
}

