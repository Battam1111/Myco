//! E2E: Attestation & ceremony, M-anchor-4 invariant witnesses + schema-evolution
//! mutation defenses.
//!
//! **v0.9 owner-key removal**: the M-anchor-2 birth-attestation + C20 boot
//! verifier, the M-anchor-5 dag-tip-cosign / L0-revision envelopes + their
//! `l0_revision_attest` mutation, the attestation-nonce issuance + C44
//! consumption path, and the seed-based operator-pubkey TOFU ceremony were all
//! removed with the anchor surface, the tests exercising them are deleted. What
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

    // Collect all witness node_types, expect at least the five with
    // structured inputs (substrate_id, cycle_monotonic, dag_verify,
    // canonical_bytes_drift, orphan_detected). (v0.9 keyless: the
    // pinned_pubkey_well_formed + owner_keys_consistency checks were removed with
    // the owner-key + anchor surface, so they are no longer expected.)
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

// (v0.9 keyless: `m_anchor_4_anchor_nonce_derived_sampling_is_deterministic`
// was removed with the `anchor_nonce_derived_sample_indices` helper, the
// anchor-nonce leaf-sampling layer is gone.)

#[test]
fn m_anchor_4_witness_decode_helper_roundtrip() {
    // **v0.9 keyless**: the witness envelope no longer carries the
    // `anchor_nonce` + `anchor_nonce_signature` fields, so `encode_invariant_witness`
    // takes 5 args and `decode_invariant_witness` returns a 5-tuple.
    use substrate::events::{
        decode_invariant_witness, encode_invariant_witness,
    };
    let inputs_bytes = vec![1u8, 2, 3, 4, 5];
    let encoded = encode_invariant_witness(
        "dag_verify_all",
        "tier_1",
        42,
        1_700_000_000_000_000_000,
        &inputs_bytes,
    );
    let (cid, tier, at_cycle, at_unix_ns, inputs_out) =
        decode_invariant_witness(encoded.as_ref()).expect("decodes");
    assert_eq!(cid, "dag_verify_all");
    assert_eq!(tier, "tier_1");
    assert_eq!(at_cycle, 42);
    assert_eq!(at_unix_ns, 1_700_000_000_000_000_000);
    assert_eq!(inputs_out, inputs_bytes);
}

#[test]
fn sprint_5b_schema_diff_canonical_bytes_modify_axis_threshold_roundtrips() {
    // The schema_diff format MUST stay stable so operator-side (TypeScript)
    // and substrate Python-side decode the same bytes. Round-trip is the
    // foundation property, if it breaks, no schema evolution works.
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
fn sprint_5b_schema_evolution_accepted_keyless_and_applies() {
    // **v0.9 owner-key removal**: schema_evolution is still CI-CLASSIFIED, but
    // the owner-attestation signature gate is gone, Python's classifier accepts
    // a CI mutation KEYLESS (no attestation_signature). With a registered target
    // axis, the apply succeeds → substrate emits evolution_succeeded:{op}.
    //
    // (This replaces the former `rejected_without_owner_attestation` defense
    // test, whose premise, "anyone could mutate schema without cultivator
    // consent", described the removed owner-key trust model. Mutation authority
    // in v0.9 is the operator-session HMAC channel, not an owner signature.)
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("hunger", "appetite", 10.0, 0.0, 1.0, false, "noop")
        .expect("register_axis");
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
                // No attestation_signature, accepted keyless in v0.9.
            ]),
        )
        .expect("submit");
    let accepted = match resp.payload.get("accepted") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("accepted missing"),
    };
    assert!(
        accepted,
        "v0.9 keyless: a CI-classified schema_evolution is accepted without an \
         owner attestation; reason={:?}",
        resp.payload.get("rejection_reason")
    );
    assert!(
        matches!(resp.payload.get("schema_apply_succeeded"), Some(CbValue::Bool(true))),
        "the schema_diff applies to the registered axis"
    );

    // evolution_succeeded:* IS emitted; evolution_failed:* is not.
    let count = |client: &mut BridgeClient, prefix: &str| -> usize {
        let q = client
            .call(
                proto::QUERY_RECENT_NODES,
                build_payload(vec![
                    ("count", CbValue::Uint(50)),
                    ("node_type_prefix", CbValue::String(prefix.to_string())),
                ]),
            )
            .expect("query");
        match q.payload.get("nodes") {
            Some(CbValue::Array(a)) => a.len(),
            _ => 0,
        }
    };
    assert_eq!(count(&mut client, "evolution_succeeded:"), 1);
    assert_eq!(count(&mut client, "evolution_failed:"), 0);
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5b_schema_evolution_malformed_diff_accepted_keyless_but_apply_fails() {
    // Garbage content_canonical_bytes that don't decode as a schema_diff Map.
    //
    // **v0.9 owner-key removal**: the CI mutation is now ACCEPTED keyless
    // (classification dominates; the owner-signature gate is gone). The malformed
    // diff is caught at the SCHEMA-APPLY stage, not the acceptance stage:
    // parse_schema_diff raises → schema_apply_succeeded=false → the substrate
    // emits evolution_failed:* (NOT evolution_succeeded:*).
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
    assert!(
        matches!(resp.payload.get("accepted"), Some(CbValue::Bool(true))),
        "v0.9 keyless: the CI mutation is accepted; the malformed diff fails at apply"
    );
    assert!(
        matches!(resp.payload.get("schema_apply_succeeded"), Some(CbValue::Bool(false))),
        "a malformed schema_diff must fail the apply stage"
    );
    // No evolution_succeeded:*, the apply failed.
    let q = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                ("node_type_prefix", CbValue::String("evolution_succeeded:".to_string())),
            ]),
        )
        .expect("query");
    let n = match q.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len(),
        _ => 0,
    };
    assert_eq!(n, 0, "a malformed schema_diff must NOT emit evolution_succeeded:*");
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
