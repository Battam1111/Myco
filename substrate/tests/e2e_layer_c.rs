//! E2E: Layer C doctrine witnesses: each test binds one doctrine card's declared positive/negative witness to executable substrate behavior (P01/P01c/P02/P03/P04/P05/P06/P07/P08/P09/P10/P11).
//!
//! Split out of the former monolithic `substrate_e2e.rs`. Shared spawn /
//! build helpers live in `tests/common/mod.rs`; this binary pulls them in
//! via `use common::*`. Tests are preserved verbatim from the original file.

mod common;
use common::*;

#[test]
fn layer_c_p01c_negative_agent_discriminating_attribute_not_persisted() {
    // **Witness binding** (P01c §3.4 + §5.1 + §5.5):
    //   declared in card → tests/integration/p01c_persisted_agent_attribute_rejected.rs
    //                     ::test_model_name_persistence_triggers_C10
    //
    // **Doctrine being defended**: P01c is the eternity-clause asymmetric
    // carrier card. The bestowal direction is substrate → agent; agent-
    // discriminating attributes (model name, prompt persona, API key) MUST
    // NOT persist into substrate state, even if the agent / operator tries
    // to inject them. The substrate is responsible for refusing — agent
    // initiative does not exonerate (§7.3 M3).
    //
    // **Strategy**: submit_mutation with a fabricated agent-persona mutation
    // type. The Python classifier returns `accepted: false` (untyped /
    // unknown), proving the substrate has no path for absorbing such state.
    // Then verify the DAG contains NO node carrying that mutation type's
    // content. The combined property — Python rejects + DAG stays clean —
    // is the eternity-clause defense.
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("set_agent_prompt_persona".to_string())),
                (
                    "content_canonical_bytes",
                    CbValue::Bytes(b"persona=helpful_assistant".to_vec()),
                ),
                ("touched_fields", CbValue::Array(vec![
                    CbValue::String("agent_prompt_persona".to_string()),
                ])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        )
        .expect("submit_mutation call");
    let accepted = match resp.payload.get("accepted") {
        Some(CbValue::Bool(b)) => *b,
        _ => false,
    };
    assert!(
        !accepted,
        "P01c §5.1: agent-discriminating mutation type must be rejected; \
         got accepted=true for mutation_type=set_agent_prompt_persona"
    );
    // Verify no `mutation:set_agent_prompt_persona` event was inserted.
    let nodes_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("mutation:set_agent_prompt_persona".to_string()),
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
        "P01c §3.4 violated: rejected mutation must NOT leave a mutation:* \
         event in DAG; saw {} nodes",
        nodes.len()
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn layer_c_p06_negative_dag_retro_edit_detected() {
    // **Witness binding** (P06 §3.1 + §3.5 + §4.3 + §5.1):
    //   declared in card → tests/integration/p06_retro_edit_detected.rs
    //                     ::test_C7_fires_on_dag_node_content_mutation
    //
    // **Doctrine being defended**: P06 is the eternity-clause causal-chain
    // card. The DAG is content-addressed; per-cycle Merkle re-computation
    // (boot replay + drill) detects any mutation of committed node content.
    // Past is immutable; corrections take the form of new nodes (§7.3 M3).
    //
    // **Strategy**: boot substrate, generate DAG content, shut down. Corrupt
    // dag.cb with random bytes. Re-boot. Substrate MUST detect mismatch and
    // emit C7 (dag_retro_edit_detected) + C41 (dag_cb_integrity_violation).
    // This is the M26.3 C41 logic restated explicitly as a P06 witness.
    let dir = fresh_state_dir();
    let client = spawn_substrate_with_state_dir(&dir);
    client.shutdown().expect("shutdown 1");

    let dag_path = dir.join("dag.cb");
    std::fs::write(&dag_path, b"layer_c_p06_negative_corruption_marker")
        .expect("corrupt dag.cb");

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
    let saw_c7 = nodes.iter().any(|n| {
        if let CbValue::Map(m) = n {
            if let Some(CbValue::String(nt)) = m.get("node_type") {
                return nt.contains("C7_dag_retro_edit_detected")
                    || nt.contains("C41_dag_cb_integrity_violation");
            }
        }
        false
    });
    assert!(
        saw_c7,
        "P06 §3.5 violated: dag.cb tampering must trigger C7/C41 immune \
         emission on re-boot; eternity-clause Merkle chain check broken"
    );
    client2.shutdown().expect("shutdown 2");
}

#[test]
fn layer_c_p07_negative_cultivator_preserve_all_rejected() {
    // **Witness binding** (P07 §3.4 + §5.3 + COV04 §3.7 + §5.6):
    //   declared in card → tests/integration/p07_mortality_evasion_blocked.rs
    //                     ::test_hoarding_attempt_rejected
    //
    // **Doctrine being defended**: P07 is the eternity-clause mandatory-
    // mortality card. The cultivator covenant (COV04) does NOT include
    // "preserve everything just in case". Any mutation that attempts to
    // disable / narrow / exempt the 应朽 detection discipline is a covenant
    // violation. The substrate MUST refuse with explanation, not silently
    // comply.
    //
    // **Strategy**: submit_mutation with each forbidden preserve-all
    // mutation type. Each MUST return accepted=false with
    // classification=covenant_violation AND emit
    // immune:C56_cultivator_preserve_all_attempted.
    let (mut client, _dir) = spawn_substrate();
    let forbidden = &[
        "preserve_all_axes",
        "never_prune",
        "disable_internal_mortality",
    ];
    for mt in forbidden {
        // Note: C56 early-reject in attestation.rs fires BEFORE the payload
        // is forwarded to Python, so touched_* fields are unnecessary —
        // including them defensively anyway for protocol completeness.
        let resp = client
            .call(
                proto::SUBMIT_MUTATION,
                build_payload(vec![
                    ("mutation_type", CbValue::String((*mt).to_string())),
                    (
                        "content_canonical_bytes",
                        CbValue::Bytes(b"preserve_all_request".to_vec()),
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
            "P07 §3.4 violated: preserve-all mutation {mt:?} must be rejected; \
             COV04 covenant breach not caught at skin"
        );
        let classification = match resp.payload.get("classification") {
            Some(CbValue::String(s)) => s.clone(),
            _ => panic!("classification missing"),
        };
        assert_eq!(
            classification, "covenant_violation",
            "P07 §5.3 violated: rejection classification for {mt:?} should be \
             covenant_violation (COV04 §3.7); got {classification:?}"
        );
    }
    // Verify the C56 immune sporocarp was emitted at least once. Note:
    // Sprint 5.F rate-limits same-detector emissions to 1 per second; the
    // 3 forbidden mutations submitted in rapid succession produce 1 DAG
    // event (first one) with subsequent attempts tracked via the
    // `suppressed_since_last_emission` counter on that event. The
    // rejection itself (accepted=false above) ALWAYS fires regardless of
    // rate limit — only the DAG-side immune event is suppressed.
    let nodes_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("immune:C56_cultivator_preserve_all_attempted".to_string()),
                ),
            ]),
        )
        .expect("query immune");
    let nodes = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes.is_empty(),
        "P07 §5.3 + COV04 §5.6: substrate must emit at least one \
         C56_cultivator_preserve_all_attempted immune event; got 0 (detection \
         broken — only rate-limiting could reduce count, not eliminate)"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn layer_c_p09_negative_malformed_envelope_rejected() {
    // **Witness binding** (P09 §3.1 + §3.2 + §4.1 + §4.3 + §5.2 + §5.4):
    //   declared in card → tests/integration/p09_envelope_malformed_rejected.rs
    //                     ::test_C2_or_immune_signal_on_bad_envelope
    //
    // **Doctrine being defended**: P09 is the eternity-clause single-
    // integument card. Exactly one declared membrane is selectively
    // permeable; malformed input MUST be rejected at the skin with a
    // typed signal, never silently accepted.
    //
    // **Strategy**: two flavors of malformed envelopes:
    //   (1) missing required `mutation_type` field — the dispatcher MUST
    //       raise a typed protocol error envelope (BridgeError::Protocol),
    //       i.e., the call returns Err, never a silent success.
    //   (2) well-formed but unknown mutation_type — accepted=false at the
    //       classifier with a non-empty rejection_reason.
    //
    // Per §4.3 the typed rejection takes either form (protocol envelope OR
    // classification field), but MUST be observable.
    let (mut client, _dir) = spawn_substrate();

    // Case 1: missing mutation_type → protocol-error envelope. This IS
    // the typed rejection at the bridge framing layer (P09 §3.1: skin
    // is the bridge protocol).
    let result_no_type = client.call(
        proto::SUBMIT_MUTATION,
        build_payload(vec![(
            "content_canonical_bytes",
            CbValue::Bytes(b"\x00\x01\x02\x03".to_vec()),
        )]),
    );
    assert!(
        result_no_type.is_err(),
        "P09 §3.2 + §5.4 violated: substrate must NOT silently accept a \
         submit_mutation envelope missing the required mutation_type field. \
         Expected typed protocol error; got Ok(_)"
    );
    // Verify the error carries a descriptive message — not an empty / panicky
    // failure. P09 §4.3 demands typed immune signal, not silent drop.
    let err_msg = format!("{}", result_no_type.unwrap_err());
    assert!(
        !err_msg.is_empty() && err_msg.to_lowercase().contains("error"),
        "P09 §4.3: rejection must carry typed signal; got opaque error: {err_msg:?}"
    );

    // Case 2: well-formed envelope but unknown mutation_type → classifier
    // returns accepted=false with rejection_reason populated.
    let resp_unknown = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("layer_c_witness_fabricated_type".to_string())),
                (
                    "content_canonical_bytes",
                    CbValue::Bytes(b"garbage".to_vec()),
                ),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        )
        .expect("submit unknown (well-formed envelope)");
    let accepted_unknown = match resp_unknown.payload.get("accepted") {
        Some(CbValue::Bool(b)) => *b,
        _ => false,
    };
    assert!(
        !accepted_unknown,
        "P09 §4.3: well-formed envelope with unknown mutation_type must be \
         classifier-rejected; got accepted=true (skin permitted unclassifiable \
         traffic to commit)"
    );
    let rejection_reason_present = resp_unknown
        .payload
        .get("rejection_reason")
        .map(|v| matches!(v, CbValue::String(s) if !s.is_empty()))
        .unwrap_or(false)
        || resp_unknown.payload.contains_key("classification");
    assert!(
        rejection_reason_present,
        "P09 §4.3: rejection response must carry typed signal (classification \
         or rejection_reason field); got payload keys: {:?}",
        resp_unknown.payload.keys().collect::<Vec<_>>()
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn layer_c_p01_positive_daily_ops_unsupervised() {
    // **Witness binding** (P01 §3.1 + §3.3 + §4.1 + §4.3):
    //   declared in card → tests/integration/p01_daily_ops_unsupervised.rs
    //                     ::test_advance_cycle_without_cultivator_attestation
    //
    // **Doctrine being proven**: P01's operational-primacy half — the
    // substrate is fully operable by an LLM agent for daily operations
    // (perturb / advance) without any cultivator presence. The cultivator
    // is "present at gates, absent from gardens".
    //
    // **Strategy**: register axis, perturb, run 3 advance cycles, take
    // snapshot. Zero cultivator attestation messages sent. Assert: each
    // advance succeeded; cycle counter advanced; snapshot reflects perturbed
    // value; DAG contains NO `mutation:` events (those require CI-class
    // attestation per P01 §3.2 contract gate).
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("p01_daily_axis", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");
    client
        .perturb("p01_daily_axis", 0.3)
        .expect("perturb");
    pump_cycles(&mut client, 3);
    let snapshot = client.snapshot().expect("snapshot");
    assert!(
        snapshot.contains_key("p01_daily_axis"),
        "P01 §4.1: agent-driven snapshot must include daily-operations axis"
    );
    // P01 §3.2 contract gate: daily ops never produce mutation:* DAG events.
    let mutation_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("mutation:".to_string()),
                ),
            ]),
        )
        .expect("query mutation");
    let muts = match mutation_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        muts.is_empty(),
        "P01 §3.2: daily ops must NOT produce mutation:* events; saw {} \
         (CI gate accidentally crossed for ordinary perturb/advance)",
        muts.len()
    );
    // P01 §3.3: cycle counter advanced — observatory's signal_7 ≥ rolling-mean
    // sample. (signal_7 is non-zero after pump_cycles.)
    let obs = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("obs");
    let s7 = match obs.payload.get("signal_7_compute_per_cycle") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_7 missing"),
    };
    let current_ns = match s7.get("current_cycle_ns") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("current_cycle_ns missing"),
    };
    assert!(
        current_ns > 0,
        "P01 §4.3: unsupervised cycles must register compute cost; got 0"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn layer_c_p02_positive_ingestion_produces_dag_event() {
    // **Witness binding** (P02 §4.1 + §4.2 + §4.5):
    //   declared in card → tests/integration/p02_ingestion_drives_evolution.rs
    //                     ::test_paper_ingested_triggers_proposal
    //
    // **Doctrine being proven**: P02 永恒吞噬 — ingested external material
    // drives downstream metabolism, not mere storage. Refutes the
    // "permanent-memory" misreading (§7.1): admission produces a DAG
    // event + classifier path.
    //
    // **Strategy**: call INGEST_RAW_MATERIAL with synthetic bytes. Assert
    // the substrate emits a `raw_material_ingested:*` DAG event in the
    // same response cycle. The event's existence (not its content)
    // proves ingestion is admitted-with-causality, not stored-as-blob.
    let (mut client, _dir) = spawn_substrate();
    client
        .call(
            proto::INGEST_RAW_MATERIAL,
            build_payload(vec![
                ("content_kind", CbValue::String("text".to_string())),
                (
                    "content_bytes",
                    CbValue::Bytes(b"layer_c_p02_witness_sample_paper".to_vec()),
                ),
            ]),
        )
        .expect("ingest");
    // INGEST_RAW_MATERIAL produces nodes with node_type=`raw_material:{kind}`,
    // e.g. `raw_material:text`. Query that prefix.
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("raw_material:".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes.is_empty(),
        "P02 §4.1: ingestion call MUST produce raw_material:* DAG event; \
         saw 0 (substrate is silent-storing, not metabolizing)"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn layer_c_p03_positive_classifier_path_traversed() {
    // **Witness binding** (P03 §3.1 + §3.3 + §4.1 + §4.3):
    //   declared in card → tests/integration/p03_schema_evolution_succeeds.rs
    //                     ::test_modify_axis_threshold_via_CI
    //
    // **Doctrine being proven**: P03 可逆迭代 — schema mutations traverse
    // the classifier → attestation → migration path. Substrate state is
    // first-class mutable under discipline, not constitutionally frozen.
    //
    // **Strategy**: submit_mutation with a schema-evolution mutation type
    // (no attestation). Python classifier MUST return a classification
    // field (proving the classifier path is wired). Without cultivator
    // attestation the mutation will not commit, but the existence of
    // classification proves the path is alive — that's what P03 needs.
    let (mut client, _dir) = spawn_substrate();
    // Use `schema_evolution` — the canonical CI-class mutation_type known
    // to the classifier (per classifier.py:210-214, classified as CI
    // unconditionally). Without owner attestation, classifier returns
    // CI + accepted=false. Both fields' presence proves the path is wired.
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("schema_evolution".to_string())),
                (
                    "content_canonical_bytes",
                    CbValue::Bytes(b"axis_name=evolved_v1;kind=appetite".to_vec()),
                ),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        )
        .expect("submit_mutation");
    let classification = match resp.payload.get("classification") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("classification missing from submit_mutation response"),
    };
    assert!(
        !classification.is_empty(),
        "P03 §4.1: classifier path must produce a non-empty classification \
         for submit_mutation; got empty (classifier wire broken)"
    );
    assert_eq!(
        classification, "contract_identity_level",
        "P03 §3.1: schema_evolution mutation MUST classify as CI; got {classification:?}"
    );
    // P03 §3.3 — without attestation, the mutation MUST NOT have
    // self-committed. Accepted=true here would mean P03's CI gate is open.
    let accepted = match resp.payload.get("accepted") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("accepted missing"),
    };
    assert!(
        !accepted,
        "P03 §3.3: schema-evolution mutation submitted without cultivator \
         attestation MUST NOT be accepted; got accepted=true (CI gate failure)"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn layer_c_p04_positive_each_cycle_changes_state() {
    // **Witness binding** (P04 §3.1 + §3.2 + §4.1 + §4.2):
    //   declared in card → tests/integration/p04_cycle_advances_refine.rs
    //                     ::test_each_advance_changes_at_least_one_state
    //
    // **Doctrine being proven**: P04 永恒迭代 — each metabolic cycle
    // refines at least one observable state. Substrate is "always one
    // cycle from a different state" — never terminal-alive.
    //
    // **Strategy**: register axis, drive 5 cycles. After each cycle, query
    // the DAG and verify a new `cycle_advanced` event appeared. Counter
    // monotonicity (provable via event count) is the canonical P04 observable.
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("p04_axis", "appetite", 2.0, 0.0, 1.0, false, "noop")
        .expect("register");

    let mut prior_count: u64 = 0;
    for cycle in 1..=5u64 {
        client.advance(cycle).expect("advance");
        let resp = client
            .call(
                proto::QUERY_RECENT_NODES,
                build_payload(vec![
                    ("count", CbValue::Uint(50)),
                    (
                        "node_type_prefix",
                        CbValue::String("cycle_advanced".to_string()),
                    ),
                ]),
            )
            .expect("query");
        let nodes = match resp.payload.get("nodes") {
            Some(CbValue::Array(a)) => a.clone(),
            _ => panic!("nodes missing"),
        };
        let count = nodes.len() as u64;
        assert!(
            count > prior_count,
            "P04 §4.2: cycle {cycle} did not produce new cycle_advanced \
             event (prior={prior_count}, now={count}) — substrate stalled, \
             eternity-iteration broken"
        );
        prior_count = count;
    }
    client.shutdown().expect("shutdown");
}

#[test]
fn layer_c_p05_positive_dag_nodes_carry_parent_hashes() {
    // **Witness binding** (P05 §3.1 + §4.1):
    //   declared in card → tests/integration/p05_active_tier_fully_connected.rs
    //                     ::test_every_active_node_reachable_from_tip
    //
    // **Doctrine being proven**: P05 万物互联 — DAG is a connected
    // mycelium, not a heap. Reachability is graph-path via parent-hash
    // chains, not address-retrieval (§7.1 M1).
    //
    // **Strategy**: drive multiple cycles to populate the DAG, then query
    // recent nodes. Every node MUST carry a `parent_hashes` array (the
    // structural-anchor for P05's connectivity invariant). Empty
    // parent_hashes is permitted ONLY for the genesis_event; all later
    // nodes MUST link back.
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("p05_axis", "appetite", 3.0, 0.0, 1.0, false, "noop")
        .expect("register");
    pump_cycles(&mut client, 3);
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![("count", CbValue::Uint(50))]),
        )
        .expect("query");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        nodes.len() >= 3,
        "P05 §4.1: insufficient DAG content to verify connectivity; \
         need ≥ 3, got {}",
        nodes.len()
    );
    let mut non_genesis_count = 0u64;
    let mut linked_count = 0u64;
    for node in &nodes {
        let m = match node {
            CbValue::Map(m) => m,
            _ => continue,
        };
        let node_type = match m.get("node_type") {
            Some(CbValue::String(s)) => s.clone(),
            _ => continue,
        };
        // genesis_event is exempt (it has no causal parent in this substrate).
        if node_type.starts_with("genesis_event") {
            continue;
        }
        non_genesis_count += 1;
        match m.get("parent_hashes") {
            Some(CbValue::Array(parents)) if !parents.is_empty() => {
                linked_count += 1;
            }
            _ => {
                // No parents on a non-genesis node = P05 violation.
            }
        }
    }
    assert!(
        non_genesis_count > 0,
        "P05: test sanity — no non-genesis events found to check"
    );
    assert_eq!(
        linked_count, non_genesis_count,
        "P05 §3.1 violated: of {non_genesis_count} non-genesis nodes, only \
         {linked_count} carry parent_hashes; orphaned nodes break the \
         mycelial connectivity invariant"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn layer_c_p08_positive_child_substrate_spawn_succeeds() {
    // **Witness binding** (P08 §3.1 + §3.2 + §3.5 + §4.1):
    //   declared in card → tests/integration/p08_sprout_child_attested.rs
    //                     ::test_owner_cosigned_spawn_succeeds
    //
    // **Doctrine being proven**: P08 永恒繁衍 — generation-bounded
    // reproduction. Parent emits spore-schema; the SPROUT_CHILD operation
    // produces a child substrate state-dir that subsequently boots into
    // a valid genesis state with parent linkage.
    //
    // **Strategy**: parent opens listener + registers axis, then sprouts
    // child. Boot the child substrate against the new state-dir and verify
    // it has a `parent_federation_hint` event (proving cross-substrate
    // linkage per §3.5). This is the m22_4 sprout path bound as P08
    // positive witness.
    // P08 §3.5 / §5.1: a child spawn is cultivator co-attested, so the parent
    // is seed-pinned and the sprout is co-signed (sprout_attested). This is the
    // POSITIVE owner-cosigned-spawn witness, so it must exercise the real
    // attested path.
    let dir_parent = fresh_state_dir();
    let mut client_parent = spawn_substrate_with_seed_and_env(&dir_parent, REPRO_SEED, vec![]);
    client_parent
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("parent open listener");
    client_parent
        .register_axis(
            "p08_inheritable",
            "appetite",
            5.0,
            0.0,
            1.0,
            false,
            "noop",
        )
        .expect("parent register");
    let child_dir = fresh_state_dir();
    sprout_attested(&mut client_parent, &child_dir, &REPRO_SEED).expect("parent sprout child");
    client_parent.shutdown().expect("shutdown parent");

    // Child inherited the parent's pinned operator identity → seed boot.
    let mut client_child = spawn_substrate_with_seed_and_env(&child_dir, REPRO_SEED, vec![]);
    let hint_resp = client_child
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("parent_federation_hint".to_string()),
                ),
            ]),
        )
        .expect("child query");
    let nodes = match hint_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert_eq!(
        nodes.len(),
        1,
        "P08 §3.5: spawned child must carry exactly one parent_federation_hint \
         (got {}); reproduction lineage broken",
        nodes.len()
    );
    client_child.shutdown().expect("shutdown child");
}

#[test]
fn layer_c_p10_positive_compression_invariant_set_covers_p10_b() {
    // **Witness binding** (P10 §3.1 + §3.2 + §3.3 + §4.1 + §4.3 + §4.4):
    //   declared in card → tests/integration/p10_compression_with_witness.rs
    //                     ::test_compression_emits_witness_and_preserves_invariant_set
    //
    // **Doctrine being proven**: P10 选择性凝结 — healthy compression
    // operates only via F18-registered rules and preserves the P10.b
    // invariant set. Compression is transformation-with-witness, not
    // deletion (§7.1 M1).
    //
    // **Strategy**: query the seed compression rule registry and the seed
    // compression invariant set. Verify: rules = 3 (raw_material /
    // federation / trajectory) per P10.a; invariant set recognizes all
    // P10.b categories (genesis, owner_keys, mutations, evolution_*,
    // mortality, federation peers, quarantine, compression itself). This
    // restates m26_3 as P10 positive witness.
    use substrate::events::{
        node_type_in_invariant_set, seed_compression_invariant_set,
        seed_compression_rule_registry,
    };
    let rules = seed_compression_rule_registry();
    assert_eq!(
        rules.len(),
        3,
        "P10.a violated: seed registry must have exactly 3 rules; got {}",
        rules.len()
    );
    let rule_ids: Vec<&str> = rules.iter().map(|r| r.rule_id.as_str()).collect();
    for expected in &[
        "raw_material_aggregate_v1",
        "federation_payload_retention_v1",
        "trajectory_archive_v1",
    ] {
        assert!(
            rule_ids.contains(expected),
            "P10.a violated: seed rule {expected} missing; got {rule_ids:?}"
        );
    }
    let inv = seed_compression_invariant_set();
    assert!(
        inv.recent_cycles_floor >= 1000,
        "P10.b violated: recent_cycles_floor must be ≥ 1000; got {}",
        inv.recent_cycles_floor
    );
    for protected in &[
        "genesis_event:any",
        "owner_key_initialized",
        "mutation:add_axis",
        "evolution_succeeded:add_axis",
        "self_euthanasia_executed:axis_x",
        "federation_peer_pinned:abcd1234",
        "birth_period_quarantine_entered",
        "compression_event:raw_material_aggregate_v1",
    ] {
        assert!(
            node_type_in_invariant_set(protected, &inv),
            "P10.b violated: {protected} must be in invariant set"
        );
    }
}

#[test]
fn layer_c_p11_positive_per_cycle_cost_signals_emitted() {
    // **Witness binding** (P11 §3.1 + §3.2 + §3.4 + §4.1 + §4.2):
    //   declared in card → tests/integration/p11_observable_cost_per_operation.rs
    //                     ::test_every_operation_emits_cost_signal
    //
    // **Doctrine being proven**: P11 代谢经济 — every state-mutating
    // operation produces observable cost signals across the three cost
    // units (Persistence, Compute, Network). I10 holds: no silent
    // absorption of cost.
    //
    // **Strategy**: pump 3 cycles. Query observatory. Verify all three
    // cost signals are present and non-degenerate (signal_7 compute_ns
    // > 0, signal_9 storage_bytes > 0; signal_8 network may be 0 without
    // federation — that's the correct value, NOT missing). This restates
    // m26_2 as P11 positive witness with the cost-trinity check explicit.
    let (mut client, _dir) = spawn_substrate();
    pump_cycles(&mut client, 3);
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s7 = match resp.payload.get("signal_7_compute_per_cycle") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!(
            "P11 §3.1: signal_7_compute_per_cycle absent — compute cost not observable"
        ),
    };
    let s7_current = match s7.get("current_cycle_ns") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("signal_7.current_cycle_ns missing"),
    };
    assert!(
        s7_current > 0,
        "P11 §3.1 (Compute): current_cycle_ns must be > 0 after real cycles; \
         got 0 (silent absorption of compute cost)"
    );

    let s8 = match resp.payload.get("signal_8_network_per_cycle") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!(
            "P11 §3.2: signal_8_network_per_cycle absent — network cost not observable"
        ),
    };
    let _s8_current = match s8.get("current_cycle_bytes") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("signal_8.current_cycle_bytes missing"),
    };
    // 0 is the valid value when no federation activity occurred; the
    // signal being PRESENT (vs absent) is the contract.

    let s9 = match resp.payload.get("signal_9_storage_per_cycle") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!(
            "P11 §3.4: signal_9_storage_per_cycle absent — storage cost not observable"
        ),
    };
    let s9_current = match s9.get("current_cycle_bytes") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("signal_9.current_cycle_bytes missing"),
    };
    assert!(
        s9_current > 0,
        "P11 §3.4 (Persistence): current_cycle_bytes must be > 0 after real \
         cycles (dag.cb grows each cycle); got 0"
    );
    client.shutdown().expect("shutdown");
}

