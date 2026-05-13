//! M1 milestone end-to-end verification.
//!
//! Proves: a single substrate can perform a handshake + store a single DAG
//! node end-to-end. This is the L3_OUTLINE §8 M1 milestone goal.
//!
//! ## Flow under test (matches L3_OUTLINE §8 step 6 M1 end-to-end)
//!
//! 1. Substrate bootstraps with an in-memory identity record + empty SkinState
//!    + empty Dag.
//! 2. Operator emits HandshakeInitiate.
//! 3. Substrate processes handshake → derives operator_token via sealed_derive
//!    → emits HandshakeComplete.
//! 4. Operator now has the operator_token; constructs a delta Envelope and
//!    computes envelope_digest (HMAC keyed by operator_token over
//!    canonical_envelope_fields || payload).
//! 5. Substrate validates the envelope (kernel/skin envelope §2.1 7-step
//!    check).
//! 6. Substrate commits the validated delta as a DAG node (kernel/schema
//!    Merkle DAG with parent-count prefix → content-addressed hash).
//! 7. Substrate's tip advances; enumerate_since returns the new node (CI
//!    co-sign use case).
//!
//! Plus defensive variants:
//! - envelope tamper after digest computation → validation fails
//! - handshake terminate → state returns to Idle → second handshake succeeds
//! - substrate-ID mismatch in initiate → rejected; state stays Idle
//! - canonical-bytes parity across recomputations
//!
//! (DAG retro-edit detection is covered in kernel/schema's own unit tests
//! since `tamper_content_for_test` is `#[cfg(test)] pub(crate)` — not
//! cross-crate accessible. This is by design: the tamper API is a kernel-
//! internal test helper, not a production-exposed surface.)

use myco_kernel_schema::dag::Dag;
use myco_kernel_shared::canonical_bytes::{encode, Value};
use myco_kernel_shared::sealed_derive::SoftwareStub;
use myco_kernel_skin::envelope::{
    compute_envelope_digest, validate_envelope, Envelope, EnvelopeError,
    EnvelopeValidationConfig, PayloadShape,
};
use myco_kernel_skin::handshake::{
    process_initiate, process_terminate, AnchorSurfaceEndpointPublicKey, ContinuityClaim,
    HandshakeInitiate, HandshakeTerminate, OperatorSigningKeyPublic,
    OwnerBirthAttestationSignature, OwnerPublicKey, SkinState, SubstrateId,
    SubstrateIdentityRecord,
};

/// Construct a test substrate identity record.
fn make_identity() -> SubstrateIdentityRecord {
    SubstrateIdentityRecord {
        substrate_id: SubstrateId("m1_milestone_substrate".to_string()),
        owner_birth_attestation_signature: OwnerBirthAttestationSignature(vec![0xaa; 64]),
        owner_public_key_active: OwnerPublicKey(vec![0xbb; 32]),
        anchor_surface_endpoint_public_key: AnchorSurfaceEndpointPublicKey(vec![0xcc; 32]),
    }
}

/// Construct a fresh handshake-initiate envelope for the given substrate.
fn make_initiate(substrate_id: &SubstrateId, submitted_at: i64) -> HandshakeInitiate {
    HandshakeInitiate {
        envelope_version: 1,
        substrate_id_proof: substrate_id.clone(),
        operator_signing_key_public: OperatorSigningKeyPublic(vec![0xdd; 32]),
        continuity_claim: ContinuityClaim::Fresh,
        submitted_at,
    }
}

#[test]
fn m1_e2e_happy_path() {
    // ----- Step 1: substrate bootstrap. -----
    let identity = make_identity();
    let sealed = SoftwareStub::new_for_test();
    let mut state = SkinState::Idle;
    let mut dag = Dag::new();
    let current_cycle: u64 = 100;

    // Commit a genesis DAG node first (substrate has its identity record
    // committed; this represents the birth attestation event). In M2 this
    // happens via kernel/governance genesis FSM; for M1 we directly insert.
    let genesis_content = encode(&Value::Map({
        let mut m = std::collections::BTreeMap::new();
        m.insert(
            "substrate_id".to_string(),
            Value::String(identity.substrate_id.0.clone()),
        );
        m.insert("born_at_cycle".to_string(), Value::Uint(0));
        m
    }))
    .unwrap();
    let genesis_hash = dag
        .insert_node(vec![], "genesis".to_string(), 0, genesis_content)
        .unwrap();
    assert_eq!(dag.tip(), Some(genesis_hash));
    assert_eq!(dag.node_count(), 1);

    // ----- Step 2 + 3: handshake. -----
    let initiate = make_initiate(&identity.substrate_id, 1_700_000_000_000_000_000);
    let complete = process_initiate(
        &mut state,
        initiate,
        &sealed,
        &identity,
        current_cycle,
        b"kernel_random_seed",
    )
    .expect("handshake should succeed");

    // Bidirectional validation: handshake_complete carries owner-birth-attestation
    // + active owner pubkey + anchor-surface-endpoint pubkey (matches identity).
    assert_eq!(complete.substrate_id, identity.substrate_id);
    assert_eq!(
        complete.owner_birth_attestation_signature,
        identity.owner_birth_attestation_signature
    );
    assert_eq!(
        complete.owner_public_key_active_at_handshake,
        identity.owner_public_key_active
    );
    assert_eq!(
        complete.anchor_surface_endpoint_public_key,
        identity.anchor_surface_endpoint_public_key
    );

    // SkinState transitioned to Active.
    assert!(matches!(state, SkinState::Active(_)));

    // ----- Step 4: operator constructs a delta envelope. -----
    let payload = b"hello, substrate".to_vec();
    let mut envelope = Envelope {
        envelope_version: 1,
        sender_token: complete.operator_token.clone(),
        payload_shape: PayloadShape::Text,
        causal_parent_ref: None,
        size_bytes: payload.len() as u64,
        content_type_hint: Some("text/plain".to_string()),
        submitted_at_cycle: current_cycle,
        envelope_digest: myco_kernel_shared::crypto::HmacTag([0; 32]),
        payload,
    };
    envelope.envelope_digest = compute_envelope_digest(&envelope, &complete.operator_token)
        .expect("digest computation should succeed");

    // ----- Step 5: substrate validates the envelope. -----
    let config = EnvelopeValidationConfig::default();
    validate_envelope(&envelope, &complete.operator_token, current_cycle, &config)
        .expect("envelope should pass all 7 validation checks");

    // ----- Step 6: substrate commits the validated delta to the DAG. -----
    // Canonical content for the DAG node = canonical bytes of (envelope-shape
    // + payload). The exact serialization is determined by L4 (the kernel
    // layer that consumes the validated envelope); for M1 we serialize the
    // envelope's payload + shape + cycle into a canonical Map.
    let delta_content = encode(&Value::Map({
        let mut m = std::collections::BTreeMap::new();
        m.insert(
            "payload_shape".to_string(),
            Value::String(envelope.payload_shape.as_str().to_string()),
        );
        m.insert(
            "payload".to_string(),
            Value::Bytes(envelope.payload.clone()),
        );
        m.insert(
            "submitted_at_cycle".to_string(),
            Value::Uint(envelope.submitted_at_cycle),
        );
        m
    }))
    .unwrap();
    let delta_hash = dag
        .insert_node(
            vec![genesis_hash],
            "delta".to_string(),
            current_cycle,
            delta_content,
        )
        .expect("DAG should accept the delta with genesis as parent");

    // ----- Step 7: verify substrate state. -----
    assert_eq!(dag.tip(), Some(delta_hash));
    assert_eq!(dag.node_count(), 2);

    // The delta node carries the validated envelope content.
    let stored_node = dag.get(&delta_hash).unwrap();
    assert_eq!(stored_node.node_type, "delta");
    assert_eq!(stored_node.parent_hashes, vec![genesis_hash]);
    assert_eq!(stored_node.created_at_cycle, current_cycle);

    // enumerate_since for CI co-sign envelope construction (L0 §9.2):
    // since genesis, the new node is delta.
    let since_genesis = dag.enumerate_since(Some(&genesis_hash)).unwrap();
    assert_eq!(since_genesis, vec![delta_hash]);

    // verify_all confirms no retro-edit.
    dag.verify_all().expect("DAG integrity intact");
}

#[test]
fn m1_e2e_envelope_tamper_rejected() {
    // After computing a valid digest, tamper the payload (same length).
    // The recomputed digest at validation differs → envelope_malformed (DigestInvalid).
    let identity = make_identity();
    let sealed = SoftwareStub::new_for_test();
    let mut state = SkinState::Idle;
    let initiate = make_initiate(&identity.substrate_id, 1);
    let complete = process_initiate(&mut state, initiate, &sealed, &identity, 100, b"r").unwrap();

    let mut envelope = Envelope {
        envelope_version: 1,
        sender_token: complete.operator_token.clone(),
        payload_shape: PayloadShape::Text,
        causal_parent_ref: None,
        size_bytes: 8,
        content_type_hint: None,
        submitted_at_cycle: 100,
        envelope_digest: myco_kernel_shared::crypto::HmacTag([0; 32]),
        payload: b"original".to_vec(),
    };
    envelope.envelope_digest = compute_envelope_digest(&envelope, &complete.operator_token).unwrap();

    // Tamper the payload (same length so size_bytes stays consistent).
    envelope.payload = b"tampered".to_vec();

    let config = EnvelopeValidationConfig::default();
    let result = validate_envelope(&envelope, &complete.operator_token, 100, &config);
    assert_eq!(result, Err(EnvelopeError::DigestInvalid));
}

#[test]
fn m1_e2e_dag_integrity_intact_after_chain() {
    // Build a 5-node chain via the public API + verify_all returns Ok
    // (positive case of L1_HARD_RULES C7 detection — no retro-edit means
    // the chain integrity holds). The negative case (actual retro-edit
    // detection) is covered in kernel/schema/src/dag.rs unit tests where
    // the cfg(test)-gated tamper helper is accessible.
    let mut dag = Dag::new();
    let g = encode(&Value::String("g".to_string())).unwrap();
    let mut last = dag
        .insert_node(vec![], "genesis".to_string(), 0, g)
        .unwrap();
    for i in 1..5u64 {
        let c = encode(&Value::Uint(i)).unwrap();
        last = dag
            .insert_node(vec![last], format!("d_{}", i), i, c)
            .unwrap();
    }
    dag.verify_all().expect("untampered chain verifies");
    assert_eq!(dag.node_count(), 5);
}

#[test]
fn m1_e2e_handshake_terminate_then_reconnect() {
    // After handshake_terminate, substrate returns to Idle.
    // A second handshake succeeds. Verifies single-operator state machine
    // (L1_SKIN §4.4) correctness for multi-session substrate lifetime.
    let identity = make_identity();
    let sealed = SoftwareStub::new_for_test();
    let mut state = SkinState::Idle;

    // First session.
    let initiate1 = make_initiate(&identity.substrate_id, 1);
    let complete1 =
        process_initiate(&mut state, initiate1, &sealed, &identity, 100, b"r1").unwrap();
    assert!(matches!(state, SkinState::Active(_)));

    // Terminate.
    process_terminate(
        &mut state,
        HandshakeTerminate {
            request_dormancy: None,
        },
    )
    .unwrap();
    assert!(matches!(state, SkinState::Idle));

    // Second session.
    let initiate2 = make_initiate(&identity.substrate_id, 2);
    let complete2 =
        process_initiate(&mut state, initiate2, &sealed, &identity, 200, b"r2").unwrap();
    assert!(matches!(state, SkinState::Active(_)));

    // The two sessions have different operator_tokens (sealed_derive includes
    // current_cycle + handshake_nonce; different cycle → different token).
    assert_ne!(complete1.operator_token, complete2.operator_token);
}

#[test]
fn m1_e2e_dag_enumerate_since_at_ci_boundary() {
    // Simulate the CI co-sign use case: substrate accumulates several deltas
    // between owner co-signs. enumerate_since produces the exact list the
    // anchor-surface verifier needs to recompute the Merkle chain (L0 §9.2 +
    // L1_HARD_RULES C6).
    let mut dag = Dag::new();
    let mut last_co_sign_tip: Option<myco_kernel_shared::crypto::NodeHash> = None;

    // Genesis.
    let g = encode(&Value::String("g".to_string())).unwrap();
    let h_g = dag
        .insert_node(vec![], "genesis".to_string(), 0, g)
        .unwrap();

    // Co-sign #1: includes only genesis.
    let since = dag.enumerate_since(last_co_sign_tip.as_ref()).unwrap();
    assert_eq!(since, vec![h_g]);
    last_co_sign_tip = Some(h_g);

    // Three deltas.
    let mut last = h_g;
    for i in 1..=3u64 {
        let c = encode(&Value::Uint(i)).unwrap();
        let h = dag
            .insert_node(vec![last], format!("delta_{}", i), i, c)
            .unwrap();
        last = h;
    }

    // Co-sign #2: includes the three deltas (NOT genesis again).
    let since = dag.enumerate_since(last_co_sign_tip.as_ref()).unwrap();
    assert_eq!(since.len(), 3);
    assert_eq!(dag.node_count(), 4);

    // Each enumerated hash resolves to a node with full metadata (the
    // composition pattern: owner queries get() per enumerated hash to
    // reconstruct the chain).
    for h in &since {
        let node = dag.get(h).expect("enumerated node must be queryable");
        assert!(!node.node_type.is_empty());
    }
}

#[test]
fn m1_e2e_substrate_id_mismatch_rejected() {
    // Operator sends handshake_initiate claiming the wrong substrate-ID.
    // Substrate rejects (L1_SKIN §4.2 step 1).
    let identity = make_identity();
    let sealed = SoftwareStub::new_for_test();
    let mut state = SkinState::Idle;

    let mut initiate = make_initiate(&identity.substrate_id, 1);
    initiate.substrate_id_proof = SubstrateId("wrong_substrate".to_string());

    let result = process_initiate(&mut state, initiate, &sealed, &identity, 100, b"r");
    assert!(result.is_err());
    // State remains Idle on rejection.
    assert!(matches!(state, SkinState::Idle));
}

#[test]
fn m1_e2e_canonical_bytes_determinism_across_layers() {
    // Same operator-token + same envelope fields + same payload must produce
    // the same envelope_digest across recomputations. This is the
    // canonical-bytes parity check that underpins L0 §9.3 anchor-surface
    // verification (operator + substrate + anchor-client all derive the same
    // canonical bytes from the same logical state).
    let token = myco_kernel_shared::sealed_derive::OperatorToken([0xab; 32]);
    let envelope = Envelope {
        envelope_version: 1,
        sender_token: token.clone(),
        payload_shape: PayloadShape::StructuredYaml,
        causal_parent_ref: Some(vec![0xfe; 32]),
        size_bytes: 5,
        content_type_hint: Some("application/yaml".to_string()),
        submitted_at_cycle: 42,
        envelope_digest: myco_kernel_shared::crypto::HmacTag([0; 32]),
        payload: b"hello".to_vec(),
    };

    let d1 = compute_envelope_digest(&envelope, &token).unwrap();
    let d2 = compute_envelope_digest(&envelope, &token).unwrap();
    assert_eq!(d1, d2);

    // Also: CanonicalBytes round-trip on the same Value is identical.
    let v = Value::Map({
        let mut m = std::collections::BTreeMap::new();
        m.insert("a".to_string(), Value::Uint(1));
        m.insert("b".to_string(), Value::String("two".to_string()));
        m
    });
    let cb1 = encode(&v).unwrap();
    let cb2 = encode(&v).unwrap();
    assert_eq!(cb1, cb2);

    // Different value → different bytes.
    let v2 = Value::Map({
        let mut m = std::collections::BTreeMap::new();
        m.insert("a".to_string(), Value::Uint(2)); // changed
        m.insert("b".to_string(), Value::String("two".to_string()));
        m
    });
    let cb3 = encode(&v2).unwrap();
    assert_ne!(cb1, cb3);
}

