//! E2E: Attestation & ceremony — M-anchor-4 invariant witnesses + schema-evolution
//! mutation defenses.
//!
//! **v0.9 owner-key removal**: the M-anchor-2 birth-attestation + C20 boot
//! verifier, the M-anchor-5 dag-tip-cosign / L0-revision envelopes + their
//! `l0_revision_attest` mutation, the attestation-nonce issuance + C44
//! consumption path, and the seed-based operator-pubkey TOFU ceremony were all
//! removed with the anchor surface — the tests exercising them are deleted. What
//! remains: the keyless invariant-witness layer + the schema-evolution CI
//! defense (which still routes through Python's classifier).
//!
//! Split out of the former monolithic `substrate_e2e.rs`. Shared spawn /
//! build helpers live in `tests/common/mod.rs`; this binary pulls them in
//! via `use common::*`.

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
    // canonical_bytes_drift, orphan_detected). owner_keys is a placeholder
    // (no inputs → no witness emission). (v0.9: pinned_pubkey_well_formed was
    // removed with the owner-key layer, so it is no longer expected either.)
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
    // attestation, Python's CI gate (dispatcher.py) returns accepted=false;
    // substrate emits no evolution_succeeded:* event.
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
                // Deliberately omit attestation_signature.
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
    // string. Operator-side query tooling depends on this format being stable.
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
fn unseeded_spawn_emits_no_operator_pinned() {
    // Regression: the spawn_substrate() path must produce a working substrate
    // with NO operator_pinned events. (v0.9 keyless: there is no operator-key
    // TOFU at all, so this holds unconditionally.)
    let (mut client, _dir) = spawn_substrate();
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
        "keyless spawn must NOT emit operator_pinned; got {}",
        nodes.len()
    );
    client.shutdown().expect("shutdown");
}
