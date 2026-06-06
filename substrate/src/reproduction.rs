//! Substrate reproduction handler — extracted from `server.rs` (Phase B Step 4).
//!
//! Owns the single P8 永恒繁衍 (perpetual reproduction) entry point:
//! `handle_sprout_child` synthesizes a fresh child substrate's DAG from the
//! parent's spore-schema (gradient axes + operator pinning + federation
//! hint + birth-period quarantine if parent has unresolved immune signals)
//! and emits a `spore_emission:{child_id_prefix}` DAG event in the parent.
//!
//! Doctrine traceability:
//! - L0 P8 永恒繁衍 — first-class reproduction operation; child inherits
//!   spore-schema, NOT parent's causal DAG.
//! - L0 P8 集体免疫 — inherited disease via parent's immune-summary
//!   triggering birth-period quarantine entry event in child.
//! - L1/HARD_RULES C34 birth_period_violation_during_quarantine.
//! - **8f / L1/GOVERNANCE §16 (F22) + L1/HARD_RULES C47/C48** — generation
//!   discipline (forkbomb defense, P8 cascade). Before sprouting, the parent
//!   verifies lineage depth (C47) and lifetime spawn quota (C48); a breach
//!   refuses the sprout and emits the matching immune sporocarp. See the
//!   constants + checks in `handle_sprout_child`.

use std::collections::BTreeMap;

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};

use crate::persistence::save_dag;
use crate::server::{emit_immune_sporocarp, save_dag_state, ServerState};
use crate::SubstrateError;

// ---------------------------------------------------------------------------
// F22 reproduction-discipline fixed points (L1/GOVERNANCE §16; CI-class per
// I2 dimension table row "Reproduction discipline parameters (F22 / §16)").
//
// These are the L1-tunable seeds named verbatim in §16. They are encoded as
// named constants matching the spec field names + default values so the
// enforcement site reads 1:1 against the governance doc. A future F22
// mutation path (CI-attested) would promote these to substrate state; until
// then they are the constitutional defaults.
// ---------------------------------------------------------------------------

/// **L1/GOVERNANCE §16.A `reproduction_lineage_depth_max`** (default 10).
/// A substrate may sprout a child iff `parent.generation_depth + 1 <= max`.
/// Root substrate is depth 0, so depth-`max` is the deepest substrate that
/// can still exist; a substrate AT depth `max` cannot sprout (child would be
/// `max + 1`). Breach → C47 `generation_depth_exceeded`.
///
/// `pub` so integration tests (and any operator-side introspection crate) can
/// pin the constitutional default against L1/GOVERNANCE §16.A.
pub const REPRODUCTION_LINEAGE_DEPTH_MAX: u64 = 10;

/// **L1/GOVERNANCE §16.C `reproduction_lifetime_quota`** (default 100).
/// A substrate may sprout iff `children_spawned_count + 1 <= quota`, where
/// `children_spawned_count` is the DAG event count of this substrate's
/// child-sprout nodes (I4 prevents retro-edit; CI-class ⇒ P10.b-invariant).
/// Breach → C48 `reproduction_lifetime_quota_exceeded`.
///
/// `pub` so integration tests can pin the constitutional default against
/// L1/GOVERNANCE §16.C.
pub const REPRODUCTION_LIFETIME_QUOTA: u64 = 100;

/// Resolve the effective `reproduction_lineage_depth_max`.
///
/// Production: the §16.A constitutional default
/// ([`REPRODUCTION_LINEAGE_DEPTH_MAX`]). A test-only env override
/// `MYCO_TEST_REPRODUCTION_DEPTH_MAX` lets the C47 E2E exercise the breach
/// without booting a 10-deep lineage. Mirrors the established
/// `MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53` test-seam precedent. Production must
/// not set this variable.
fn effective_lineage_depth_max() -> u64 {
    std::env::var("MYCO_TEST_REPRODUCTION_DEPTH_MAX")
        .ok()
        .and_then(|s| s.trim().parse::<u64>().ok())
        .unwrap_or(REPRODUCTION_LINEAGE_DEPTH_MAX)
}

/// Resolve the effective `reproduction_lifetime_quota`.
///
/// Production: the §16.C constitutional default
/// ([`REPRODUCTION_LIFETIME_QUOTA`]). A test-only env override
/// `MYCO_TEST_REPRODUCTION_QUOTA` lets the C48 E2E exercise the quota breach
/// with a handful of sprouts instead of 100. Production must not set this
/// variable.
fn effective_lifetime_quota() -> u64 {
    std::env::var("MYCO_TEST_REPRODUCTION_QUOTA")
        .ok()
        .and_then(|s| s.trim().parse::<u64>().ok())
        .unwrap_or(REPRODUCTION_LIFETIME_QUOTA)
}

/// **L1/GOVERNANCE §16.B `reproduction_rate_min_interval`** (default 24h in ns).
/// A substrate may sprout iff `envelope.anchor_timestamp − last_spawn_ts ≥
/// interval`, where `last_spawn_ts` is the MAX anchor wall-clock timestamp over
/// the parent's prior `genesis_attested:*` events (None if this is the first
/// attested spawn). §16.B mandates the *anchor wall-clock* (NOT the substrate
/// cycle counter — throttle-evasion per P06 + L1/CONTINUITY time semantics);
/// the anchor timestamp arrives inside the cultivator-signed spawn-cosign
/// envelope. Breach → C48 `reproduction_lifetime_quota_exceeded` (rate half).
///
/// `pub` so integration tests can pin the constitutional default against
/// L1/GOVERNANCE §16.B.
pub const REPRODUCTION_RATE_MIN_INTERVAL_NS: i64 = 86_400 * 1_000_000_000; // 24h

/// Resolve the effective `reproduction_rate_min_interval` (ns).
///
/// Production: the §16.B constitutional default
/// ([`REPRODUCTION_RATE_MIN_INTERVAL_NS`]). A test-only env override
/// `MYCO_TEST_REPRODUCTION_RATE_MIN_INTERVAL_NS` lets the rate-throttle E2E
/// exercise the breach without two real-day-apart anchor stamps. Production
/// must not set this variable.
fn effective_rate_min_interval_ns() -> i64 {
    std::env::var("MYCO_TEST_REPRODUCTION_RATE_MIN_INTERVAL_NS")
        .ok()
        .and_then(|s| s.trim().parse::<i64>().ok())
        .unwrap_or(REPRODUCTION_RATE_MIN_INTERVAL_NS)
}

/// Verified, decoded cultivator spawn co-attestation (P08 §3.5 / §5.1).
///
/// Produced by [`verify_spawn_co_attestation`] AFTER all gates pass; carries
/// exactly the values the rest of `handle_sprout_child` needs (the
/// owner-minted child-id, the anchor timestamp for the rate-throttle record,
/// the raw envelope + signature + pubkey for the `genesis_attested` event, and
/// the cultivator's `depth_override` decision).
struct VerifiedSpawnAttestation {
    /// `blake3(parent_id || spore_schema_hash || child_genesis_ts)` — §5.6
    /// deterministic, non-reissuable child identity (replaces the random
    /// `Manifest::genesis()` id).
    minted_child_id: [u8; 32],
    /// The child's genesis timestamp (from the envelope), stamped into the
    /// child's `genesis_event` + returned to the operator.
    child_genesis_timestamp_unix_ns: i64,
    /// The spawn-cosign envelope bytes (re-emitted into the genesis_attested
    /// record for offline inspection). The anchor wall-clock the §16.B
    /// rate-throttle reads on the NEXT spawn is carried INSIDE these bytes
    /// (decoded back via `decode_spawn_cosign`), so no separate field is needed.
    ///
    /// **v0.9 keyless**: the cultivator Ed25519 signature + owner-pubkey fields
    /// were removed with the anchor surface; the envelope structure (parent
    /// replay-guard, spore-schema binding, anchor timestamp, depth_override) is
    /// still verified, but no signature is checked over it.
    envelope_bytes: Vec<u8>,
    /// The co-signed spore-schema hash (== blake3 of the operator-supplied
    /// spore_schema_canonical_bytes; I7(a)).
    spore_schema_hash: [u8; 32],
    /// The depth-override decision carried in the envelope for THIS spawn (§16.A
    /// depth_override / F22).
    depth_override: bool,
}

/// **P08 §3.5 / §5.1 — verify the cultivator spawn co-attestation.**
///
/// Runs FIRST in `handle_sprout_child`, after payload parse and BEFORE the
/// C47/C48 generation guards. On ANY failure it emits **C68
/// reproduction_unattested_spawn**, persists the DAG (the dispatch arm only
/// saves on Ok), and returns `Err` — with NO child DAG / file side effect (the
/// §5.1 "daily-mode spawn = doctrine collapse" signal).
///
/// Gates, in order:
/// 1. pinned operator identity present (owner_pubkey = pinned.pubkey);
/// 2. envelope decodes as `myco-spawn-cosign-v1`;
/// 3. envelope.parent_substrate_id == this substrate's id (replay guard);
/// 4. I7(a): blake3(spore_schema_canonical_bytes) == envelope.spore_schema_hash
///    AND the canonical bytes are a well-formed 7-field spore-schema;
/// 5. Ed25519 verify(owner_pubkey, attestation_signature, envelope_bytes);
/// 6. §16.B rate throttle: anchor_ts − last_spawn_ts ≥ interval AND
///    anchor_ts > last_spawn_ts (clock-rewind block). Breach → C48 (rate).
///
/// On success returns the [`VerifiedSpawnAttestation`] with the §5.6
/// owner-minted child-id.
fn verify_spawn_co_attestation(
    state: &mut ServerState,
    request: &Message,
) -> Result<VerifiedSpawnAttestation, SubstrateError> {
    // Helper: emit C68 + persist + return Err, with a shared evidence prefix.
    fn reject_c68(
        state: &mut ServerState,
        evidence: String,
    ) -> Result<VerifiedSpawnAttestation, SubstrateError> {
        // implements L0::P8; negative-witness: substrate/tests/e2e_reproduction.rs::c68_unattested_spawn_refused_and_immune_no_child_dag
        let _ = emit_immune_sporocarp(
            state,
            "C68_reproduction_unattested_spawn",
            "reproduction_unattested_spawn",
            &evidence,
        );
        let _ = save_dag_state(state);
        Err(SubstrateError::Protocol(evidence))
    }

    // --- Parse the required payload fields. ---
    let envelope_bytes = match request.payload.get("spawn_cosign_envelope") {
        Some(Value::Bytes(b)) if !b.is_empty() => b.clone(),
        _ => {
            return reject_c68(
                state,
                "sprout_child refused (C68): missing/empty spawn_cosign_envelope — \
                 a child spawn requires a myco-spawn-cosign-v1 envelope (P08 §5.1: \
                 daily-mode spawn = doctrine collapse)"
                    .to_string(),
            );
        }
    };
    let spore_schema_canonical_bytes = match request.payload.get("spore_schema_canonical_bytes") {
        Some(Value::Bytes(b)) if !b.is_empty() => b.clone(),
        _ => {
            return reject_c68(
                state,
                "sprout_child refused (C68): missing/empty spore_schema_canonical_bytes \
                 (required for I7(a) static-schema validation)"
                    .to_string(),
            );
        }
    };

    // --- Gate 2: envelope decodes as myco-spawn-cosign-v1. ---
    //
    // `_env_anchor_nonce` is signed and part of the byte-parity contract (it is
    // re-encoded verbatim into the genesis_attested event), but it is NOT
    // freshness-checked here: it is RESERVED for future M-anchor nonce-ledger
    // wiring (an issued/consumed anchor-nonce ledger, like the heartbeat nonce
    // path). Until that lands, the CURRENT spawn-replay defense is the §16.B
    // clock-rewind guard in gate 6 below (`env_anchor_ts` must be STRICTLY later
    // than the max anchor stamp over prior genesis_attested:* events), so a
    // replayed envelope cannot mint a second child.
    let (
        env_parent_id,
        env_spore_schema_hash,
        env_child_genesis_ts,
        env_anchor_ts,
        _env_anchor_nonce,
        env_depth_override,
    ) = match crate::events::decode_spawn_cosign(&envelope_bytes) {
        Some(t) => t,
        None => {
            return reject_c68(
                state,
                "sprout_child refused (C68): spawn_cosign_envelope failed to decode \
                 as myco-spawn-cosign-v1 (wrong domain or malformed shape)"
                    .to_string(),
            );
        }
    };

    // --- Gate 3: parent_substrate_id replay guard. ---
    let my_id = state.substrate_id();
    if env_parent_id != my_id {
        return reject_c68(
            state,
            format!(
                "sprout_child refused (C68): spawn_cosign envelope.parent_substrate_id={} \
                 ≠ this substrate's id={} (replay guard — an envelope minted for \
                 another parent cannot authorize a spawn here)",
                crate::server::hex_first_8_bytes(&env_parent_id),
                crate::server::hex_first_8_bytes(&my_id),
            ),
        );
    }

    // --- Gate 4: I7(a) static-schema validation. ---
    let computed_spore_hash: [u8; 32] =
        blake3::hash(&spore_schema_canonical_bytes).into();
    if computed_spore_hash != env_spore_schema_hash {
        return reject_c68(
            state,
            format!(
                "sprout_child refused (C68): blake3(spore_schema_canonical_bytes)={} \
                 ≠ co-signed envelope.spore_schema_hash={} (I7(a) static-schema \
                 mismatch — the supplied spore-schema is not what the cultivator signed)",
                crate::server::hex_first_8_bytes(&computed_spore_hash),
                crate::server::hex_first_8_bytes(&env_spore_schema_hash),
            ),
        );
    }
    if let Err(e) = myco_kernel_schema::spore::SporeSchema::validate_canonical_bytes_shape(
        &spore_schema_canonical_bytes,
    ) {
        return reject_c68(
            state,
            format!(
                "sprout_child refused (C68): co-signed spore-schema fails I7(a) \
                 shape validation: {e}"
            ),
        );
    }

    // --- Gate 5 (REMOVED, v0.9 keyless): the cultivator Ed25519 signature
    // verification over the spawn-cosign envelope was dropped with the anchor
    // surface. Gates 2/3/4 (envelope decode + parent replay-guard + I7(a)
    // static-schema) and gate 6 (§16.B rate throttle) remain the structural
    // spawn-discipline; C68 still fruits on any of those failing. ---

    // --- Gate 6: §16.B anchor-wall-clock rate throttle. ---
    // last_spawn_ts = MAX anchor_timestamp over prior genesis_attested:* events.
    let last_spawn_ts: Option<i64> = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| {
            n.node_type
                .starts_with(crate::events::NODE_TYPE_GENESIS_ATTESTED_PREFIX)
        })
        .filter_map(|n| {
            crate::events::decode_genesis_attested_event(n.content_canonical_bytes.as_ref())
                .and_then(|d| crate::events::decode_spawn_cosign(&d.0))
                .map(|env| env.3) // anchor_timestamp_unix_ns
        })
        .max();
    if let Some(prev_ts) = last_spawn_ts {
        let interval = effective_rate_min_interval_ns();
        // Block clock-rewind: a new spawn must carry a STRICTLY later anchor
        // stamp than the prior spawn, AND respect the min interval.
        if env_anchor_ts <= prev_ts {
            return reject_c68(
                state,
                format!(
                    "sprout_child refused (C68 via §16.B): spawn-cosign \
                     anchor_timestamp {env_anchor_ts} ≤ prior spawn anchor_timestamp \
                     {prev_ts} — anchor clock-rewind is a throttle-evasion signal \
                     (P06 + L1/CONTINUITY time semantics)"
                ),
            );
        }
        if env_anchor_ts.saturating_sub(prev_ts) < interval {
            // §16.B rate breach → C48 (rate half), distinct from C68.
            let evidence = format!(
                "sprout_child refused: spawn-cosign anchor_timestamp delta \
                 {} ns < reproduction_rate_min_interval {} ns (L1/GOVERNANCE §16.B \
                 anchor-wall-clock throttle; prior spawn at {}, this at {})",
                env_anchor_ts - prev_ts,
                interval,
                prev_ts,
                env_anchor_ts
            );
            let _ = emit_immune_sporocarp(
                state,
                "C48_reproduction_lifetime_quota_exceeded",
                "reproduction_rate_min_interval_exceeded",
                &evidence,
            );
            let _ = save_dag_state(state);
            return Err(SubstrateError::Protocol(evidence));
        }
    }

    // --- Success: owner-mint the §5.6 deterministic child-id. ---
    // blake3(parent_id || spore_schema_hash || child_genesis_ts_le).
    let minted_child_id: [u8; 32] = {
        let mut hasher = blake3::Hasher::new();
        hasher.update(&my_id);
        hasher.update(&env_spore_schema_hash);
        hasher.update(&env_child_genesis_ts.to_le_bytes());
        hasher.finalize().into()
    };

    // `env_anchor_ts` was consumed by the §16.B rate gate above; the value the
    // NEXT spawn re-reads lives inside `envelope_bytes` (see struct doc).
    Ok(VerifiedSpawnAttestation {
        minted_child_id,
        child_genesis_timestamp_unix_ns: env_child_genesis_ts,
        envelope_bytes,
        spore_schema_hash: env_spore_schema_hash,
        depth_override: env_depth_override,
    })
}

/// M20 P8 永恒繁衍 — Sprout a child substrate from the parent's spore-schema.
///
/// Per L0/cards/P01-P14 (principles).2 P8: "The substrate can spawn child substrates. Reproduction is
/// a first-class operation. The new substrate inherits the parent's
/// spore-schema (minimum structural form for the child to begin its own
/// symbiosis)."
///
/// M20-MV spore-schema = (gradient axes + schemas + current values) +
/// (operator identity pubkey for continuity) + (fresh substrate_id +
/// fresh genesis_time + cycle_counter=0 + last_absorbed_cycle=None).
///
/// The parent's causal DAG is NOT transferred — the child starts its own
/// causal history (L1 decision per L0 P8). The parent emits a
/// `spore_emission:{child_id_hex_prefix}` DAG node recording the reproduction.
///
/// Payload schema:
/// ```text
/// Map({
///   "child_state_dir": String,  // target directory (must not exist or must be empty)
///   "spore_metadata": Map       // optional; arbitrary K-V hints recorded in the spore_emission node
/// })
/// ```
///
/// Returns:
/// ```text
/// Map({
///   "child_substrate_id": Bytes(32),
///   "child_state_dir": String,
///   "spore_emission_hash": Bytes(32),   // in parent's DAG
/// })
/// ```
pub(crate) fn handle_sprout_child(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let child_state_dir = match request.payload.get("child_state_dir") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "sprout_child: child_state_dir must be a non-empty String".to_string(),
            ));
        }
    };
    let spore_metadata = request.payload.get("spore_metadata").cloned();

    // -----------------------------------------------------------------------
    // **P08 §3.5 / §5.1 — cultivator spawn co-attestation (runs FIRST).**
    //
    // A child spawn is a CI-class doctrine event, NOT a daily-mode mutation:
    // it requires the cultivator's myco-spawn-cosign-v1 co-signature. This
    // gate verifies the signed envelope (pinned-identity → decode → parent
    // replay-guard → I7(a) static-schema → Ed25519 verify → §16.B rate
    // throttle) BEFORE any side effect; on failure it emits C68 (or C48 for a
    // rate breach), persists, and returns Err with no child DAG/file created.
    // On success it yields the §5.6 owner-minted deterministic child-id, which
    // REPLACES the random `Manifest::genesis()` id below.
    let attestation = verify_spawn_co_attestation(state, request)?;
    let minted_child_id = attestation.minted_child_id;

    // -----------------------------------------------------------------------
    // 8f / L1/GOVERNANCE §16 (F22) generation discipline — forkbomb defense.
    //
    // These two checks run BEFORE any side effect (no directory is created, no
    // Python query is issued, no child DAG is built). A breach emits the
    // matching immune sporocarp into the PARENT's DAG, persists it (the
    // SPROUT_CHILD dispatch arm only saves on Ok, so we save here explicitly —
    // same precedent as `dag_query::handle_enumerate_dag_since`'s C6 path),
    // and refuses the sprout with the existing rejection shape
    // (`SubstrateError::Protocol`, surfaced to the operator as an error
    // envelope by the main loop).
    //
    // The RATE half of §16.B (`reproduction_rate_min_interval`) is now
    // enforced in `verify_spawn_co_attestation` (gate 6) above: the anchor
    // wall-clock arrives inside the cultivator-signed spawn-cosign envelope
    // (`anchor_timestamp − last_spawn_ts ≥ interval`, with last_spawn_ts =
    // MAX over prior genesis_attested:* events; a clock-rewind is itself a
    // refusal). The QUOTA half (§16.C) is the pure DAG event-count below
    // (I4-tamper-evident; needs no wall-clock).

    // --- C47 generation_depth_exceeded (§16.A) ---
    // Root = depth 0; the child this sprout would create is `parent + 1`. A
    // substrate at depth == REPRODUCTION_LINEAGE_DEPTH_MAX cannot sprout
    // (child would exceed the max) UNLESS the cultivator's already-verified
    // spawn-cosign envelope carries `depth_override` (F22) — which is wired
    // below: an override records an audit event and proceeds, its absence
    // hard-caps depth (the safe default for forkbomb defense).
    let parent_generation_depth = state.generation_depth();
    let child_generation_depth = parent_generation_depth.saturating_add(1);
    let lineage_depth_max = effective_lineage_depth_max();
    if child_generation_depth > lineage_depth_max {
        // **§16.A depth_override (F22)**: the cultivator's spawn-cosign envelope
        // carries a signed `depth_override` flag. Because the envelope's
        // signature was already verified by `verify_spawn_co_attestation`, an
        // override here is a genuine cultivator decision to exceed the lineage
        // cap for THIS spawn. We record that it was exercised (audit trail) and
        // proceed; otherwise the forkbomb depth guard fires C47.
        if attestation.depth_override {
            let evidence = format!(
                "depth_override exercised: child generation_depth {child_generation_depth} \
                 exceeds reproduction_lineage_depth_max {lineage_depth_max} \
                 (parent.generation_depth={parent_generation_depth}); permitted by \
                 cultivator-signed depth_override in the myco-spawn-cosign-v1 envelope \
                 (L1/GOVERNANCE §16.A / F22)."
            );
            let _ = crate::server::emit_substrate_event(
                state,
                "depth_override_exercised".to_string(),
                {
                    let mut m = BTreeMap::new();
                    m.insert(
                        "child_generation_depth".to_string(),
                        Value::Uint(child_generation_depth),
                    );
                    m.insert(
                        "reproduction_lineage_depth_max".to_string(),
                        Value::Uint(lineage_depth_max),
                    );
                    m.insert("evidence".to_string(), Value::String(evidence));
                    m.insert(
                        "child_substrate_id".to_string(),
                        Value::Bytes(minted_child_id.to_vec()),
                    );
                    cb_encode(&Value::Map(m))
                        .map_err(|e| SubstrateError::Protocol(format!("depth_override encode: {e}")))?
                },
            );
            // Note: persisted by the dispatch arm on Ok (the spawn proceeds).
        } else {
            let evidence = format!(
                "sprout_child refused: child generation_depth {child_generation_depth} \
                 would exceed reproduction_lineage_depth_max {lineage_depth_max} \
                 (parent.generation_depth={parent_generation_depth}); forkbomb depth guard \
                 per L1/GOVERNANCE §16.A. No depth_override attested in the spawn-cosign envelope."
            );
            let _ = emit_immune_sporocarp(
                state,
                "C47_generation_depth_exceeded",
                "generation_depth_exceeded",
                &evidence,
            );
            // Persist the breach so it survives restart (dispatch won't save on Err).
            let _ = save_dag_state(state);
            return Err(SubstrateError::Protocol(evidence));
        }
    }

    // --- C48 reproduction_lifetime_quota_exceeded (§16.C, QUOTA half) ---
    // children_spawned_count = DAG event count of this substrate's child-sprout
    // nodes. The governance doc names the counter node-type
    // `spawn_completed:{child_substrate_id}`; the live reproduction path emits
    // `spore_emission:{child_id_prefix}` for each successful sprout, so that is
    // the authoritative child-sprout event we count here (I4 prevents
    // retro-edit; CI-class ⇒ P10.b-invariant). Quota is a LIFETIME cap: it
    // counts every prior sprout regardless of whether the child still lives.
    let children_spawned_count = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| n.node_type.starts_with("spore_emission:"))
        .count() as u64;
    let lifetime_quota = effective_lifetime_quota();
    if children_spawned_count.saturating_add(1) > lifetime_quota {
        let evidence = format!(
            "sprout_child refused: children_spawned_count {children_spawned_count} + 1 \
             would exceed reproduction_lifetime_quota {lifetime_quota} \
             per L1/GOVERNANCE §16.C. Each over-quota spawn requires its own \
             §2 attestation (no bulk); not attested."
        );
        let _ = emit_immune_sporocarp(
            state,
            "C48_reproduction_lifetime_quota_exceeded",
            "reproduction_lifetime_quota_exceeded",
            &evidence,
        );
        let _ = save_dag_state(state);
        return Err(SubstrateError::Protocol(evidence));
    }

    let child_path = std::path::PathBuf::from(&child_state_dir);

    // Guard: child_state_dir must not contain an existing dag.cb (don't
    // overwrite an existing substrate's identity). Post-M21.4, dag.cb is
    // the sole persistent artifact; its presence indicates a live child.
    if child_path.join("dag.cb").exists() {
        return Err(SubstrateError::Protocol(format!(
            "sprout_child: refusing to overwrite existing dag.cb at {child_state_dir}"
        )));
    }
    // Also reject if legacy manifest.cb is present (pre-M21.4 child).
    if child_path.join("manifest.cb").exists() {
        return Err(SubstrateError::Protocol(format!(
            "sprout_child: refusing to overwrite existing manifest.cb at {child_state_dir}"
        )));
    }

    // Create the child state_dir.
    std::fs::create_dir_all(&child_path).map_err(SubstrateError::Io)?;

    // M21.4 P5 万物互联: build the child's DAG directly — no legacy state
    // files. The child's first DAG node is its genesis_event; operator_pinned
    // event records parent's identity for operator continuity; axis_registered
    // + axis_perturbed events seed the child's gradient.
    //
    // **P08 §5.6**: the child's substrate_id is the OWNER-MINTED deterministic
    // id `blake3(parent_id, spore_schema_hash, child_genesis_ts)` produced by
    // `verify_spawn_co_attestation` (NOT a random `Manifest::genesis()` id).
    // This gives non-reissuance: re-running the same co-signed spawn re-derives
    // the same child identity. The genesis_event below stamps it + the signed
    // genesis timestamp, which the child reads back at boot via
    // `DerivedState::apply_genesis`.
    let child_genesis_time_unix_ns = attestation.child_genesis_timestamp_unix_ns;
    let child_cycle: u64 = 0;

    // Query parent's axis schemas to seed the child's gradient as events.
    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;
    let parent_schemas = client
        .query_gradient_schemas()
        .map_err(SubstrateError::Bridge)?;
    let child_axis_count = parent_schemas.len() as u64;

    // Build child's DAG: genesis_event → operator_pinned (if parent had one)
    // → per-axis (axis_registered + optional axis_perturbed for non-initial value).
    let mut child_dag = myco_kernel_schema::dag::Dag::new();

    // 1. genesis_event — 8f / §16.A: record the child's lineage depth as
    // `parent.generation_depth + 1`. This is the authoritative carrier: when
    // the child boots from this dag.cb, `DerivedState::apply_genesis` reads it
    // back into the child's `Manifest.generation_depth`, so the child in turn
    // enforces C47 against its own (deeper) depth. `child_generation_depth`
    // was computed + bounded by the §16.A guard above.
    let child_genesis_nt = crate::events::genesis_event_node_type(&minted_child_id);
    let child_genesis_content = crate::events::encode_genesis_event(
        &minted_child_id,
        child_genesis_time_unix_ns,
        child_generation_depth,
    );
    child_dag
        .insert_node(vec![], child_genesis_nt, child_cycle, child_genesis_content)
        .map_err(|e| SubstrateError::Protocol(format!("child genesis_event insert: {e}")))?;

    // 1b. **P08 §3.5 I7(b) — birth_closure_pending** marker, written into the
    // CHILD's DAG right after genesis_event. When the child first boots it will
    // see this (without a later birth_closure_complete), run its OWN I3 boot
    // self-check (I7 step c), and emit birth_closure_complete with the verdict.
    {
        let nt = crate::events::birth_closure_pending_node_type(&state.substrate_id());
        let content = crate::events::encode_birth_closure_pending(
            &state.substrate_id(),
            &minted_child_id,
            &attestation.spore_schema_hash,
        );
        let parents = vec![child_dag.tip().unwrap()];
        child_dag
            .insert_node(parents, nt, child_cycle, content)
            .map_err(|e| {
                SubstrateError::Protocol(format!("child birth_closure_pending insert: {e}"))
            })?;
    }

    // 2. operator_pinned child-inheritance REMOVED (v0.9 keyless): the parent no
    // longer carries a pinned operator identity, so there is nothing to seed into
    // the child's DAG for operator continuity. (The owner-key TOFU layer is gone.)

    // 2b. M22.4 P5 万物互联: if the parent has an open federation listener,
    // record its address in the child's DAG so the child can dial back. The
    // child substrate, after boot, can call `federation_link_to_parent_from_hint`
    // to consume this hint, connect to the parent, and emit
    // `federation_parent_linked`.
    if let Some(parent_listener_addr) = state.federation.listener_addr() {
        use std::time::{SystemTime, UNIX_EPOCH};
        let hinted_at_unix_ns = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .ok()
            .and_then(|d| i64::try_from(d.as_nanos()).ok())
            .unwrap_or(0);
        let nt = crate::events::NODE_TYPE_PARENT_FEDERATION_HINT.to_string();
        let content = crate::events::encode_parent_federation_hint(
            &state.substrate_id(),
            &parent_listener_addr.to_string(),
            hinted_at_unix_ns,
        );
        let parents = vec![child_dag.tip().unwrap()];
        child_dag
            .insert_node(parents, nt, child_cycle, content)
            .map_err(|e| SubstrateError::Protocol(format!("parent_federation_hint insert: {e}")))?;
    }

    // 2c. M22.5 P8 永恒繁衍: compute parent's immune-summary (list of
    // immune sporocarp hashes) and, if non-empty, write a
    // birth_period_quarantine_entered event into child's DAG. The child
    // enters quarantine on boot. This implements L0/cards/P01-P14 (principles).2 P8 + pass-1
    // mycoparasite-13: "child enters birth-period quarantine if parent had
    // unresolved immune signals".
    let immune_summary: Vec<[u8; 32]> = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| n.node_type.starts_with("immune:"))
        .map(|n| n.hash.0)
        .collect();
    let quarantine_duration_cycles: u64 = 10; // M22.5 default; future: configurable
    if !immune_summary.is_empty() {
        use std::time::{SystemTime, UNIX_EPOCH};
        let entered_at_unix_ns = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .ok()
            .and_then(|d| i64::try_from(d.as_nanos()).ok())
            .unwrap_or(0);
        let nt = crate::events::NODE_TYPE_BIRTH_PERIOD_QUARANTINE_ENTERED.to_string();
        let content = crate::events::encode_birth_period_quarantine_entered(
            &state.substrate_id(),
            &immune_summary,
            quarantine_duration_cycles,
            entered_at_unix_ns,
        );
        let parents = vec![child_dag.tip().unwrap()];
        child_dag.insert_node(parents, nt, child_cycle, content).map_err(|e| {
            SubstrateError::Protocol(format!("birth_period_quarantine_entered insert: {e}"))
        })?;
    }

    // 3. Per-axis events: axis_registered, then axis_perturbed for any delta.
    for schema in &parent_schemas {
        let reg_nt = crate::events::axis_registered_node_type(&schema.name);
        let reg_event = crate::events::AxisRegisteredEvent {
            name: schema.name.clone(),
            axis_class: schema.axis_class.clone(),
            fruiting_threshold: schema.fruiting_threshold,
            initial_value: schema.initial_value,
            decay_rate_per_cycle: schema.decay_rate_per_cycle,
            is_mortality_signal: schema.is_mortality_signal,
            update_rule_kind: schema.update_rule_kind.clone(),
        };
        let reg_content = crate::events::encode_axis_registered(&reg_event);
        let parents = vec![child_dag.tip().unwrap()];
        child_dag
            .insert_node(parents, reg_nt, child_cycle, reg_content)
            .map_err(|e| SubstrateError::Protocol(format!("child axis_registered insert: {e}")))?;
        let delta = schema.current_value - schema.initial_value;
        if delta != 0.0 {
            let pert_nt = crate::events::axis_perturbed_node_type(&schema.name);
            let pert_content = crate::events::encode_axis_perturbed(&schema.name, delta);
            let parents = vec![child_dag.tip().unwrap()];
            child_dag
                .insert_node(parents, pert_nt, child_cycle, pert_content)
                .map_err(|e| {
                    SubstrateError::Protocol(format!("child axis_perturbed insert: {e}"))
                })?;
        }
    }

    // Persist child's DAG (the SOLE child state file post-M21.4).
    save_dag(&child_dag, &child_path)?;

    // Emit spore_emission:{child_id_prefix} DAG node in PARENT's DAG.
    let child_id_hex_prefix: String = minted_child_id
        .iter()
        .take(8)
        .map(|b| format!("{b:02x}"))
        .collect();
    let mut spore_content = BTreeMap::new();
    spore_content.insert(
        "child_substrate_id".to_string(),
        Value::Bytes(minted_child_id.to_vec()),
    );
    spore_content.insert(
        "child_state_dir".to_string(),
        Value::String(child_state_dir.clone()),
    );
    spore_content.insert(
        "child_axis_count".to_string(),
        Value::Uint(child_axis_count),
    );
    spore_content.insert(
        "parent_substrate_id".to_string(),
        Value::Bytes(state.substrate_id().to_vec()),
    );
    spore_content.insert(
        "parent_cycle_at_emission".to_string(),
        Value::Uint(state.cycle_counter()),
    );
    // 8f / §16.A: record the child's lineage depth in the parent's spore
    // node so the parent's DAG carries the depth lineage for observability.
    spore_content.insert(
        "child_generation_depth".to_string(),
        Value::Uint(child_generation_depth),
    );
    if let Some(m) = spore_metadata {
        spore_content.insert("spore_metadata".to_string(), m);
    }
    let spore_canonical = cb_encode(&Value::Map(spore_content))
        .map_err(|e| SubstrateError::Protocol(format!("spore_emission encode: {e}")))?;
    let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let spore_node_type = format!("spore_emission:{child_id_hex_prefix}");
    let cycle = state.cycle_counter();
    let spore_hash = state
        .dag
        .insert_node(parents, spore_node_type, cycle, spore_canonical)
        .map_err(|e| SubstrateError::Protocol(format!("spore_emission DAG insert: {e}")))?;

    // **P08 §3.5 I7-closure — genesis_attested:{child_prefix}** in the PARENT's
    // DAG. This is the immutable owner-attested record that this child's
    // genesis was cultivator-co-signed: it carries the signed envelope +
    // signature + pubkey (re-verifiable offline), the parent/child/spore
    // binding, and the I7(a) static-schema verdict (true — verified above).
    // The §16.B rate-throttle reads `last_spawn_ts` off THESE events.
    let genesis_attested_nt = crate::events::genesis_attested_node_type(&minted_child_id);
    let genesis_attested_content = crate::events::encode_genesis_attested_event(
        &attestation.envelope_bytes,
        &state.substrate_id(),
        &minted_child_id,
        &attestation.spore_schema_hash,
        true, // child_static_schema_valid — I7(a) passed in verify_spawn_co_attestation
        cycle,
    );
    let genesis_attested_hash =
        crate::server::emit_substrate_event(state, genesis_attested_nt, genesis_attested_content)?;

    let mut payload = BTreeMap::new();
    payload.insert(
        "child_substrate_id".to_string(),
        Value::Bytes(minted_child_id.to_vec()),
    );
    payload.insert(
        "child_state_dir".to_string(),
        Value::String(child_state_dir),
    );
    payload.insert(
        "child_axis_count".to_string(),
        Value::Uint(child_axis_count),
    );
    // 8f / §16.A: surface the child's lineage depth so the operator can
    // confirm `parent + 1` without re-reading the child's DAG.
    payload.insert(
        "child_generation_depth".to_string(),
        Value::Uint(child_generation_depth),
    );
    payload.insert(
        "spore_emission_hash".to_string(),
        Value::Bytes(spore_hash.as_ref().to_vec()),
    );
    // **P08 §3.5**: surface the I7-closure record hash + the signed child
    // genesis timestamp so the operator can confirm the attestation landed
    // and (with the minted-id derivation) re-derive the child identity.
    payload.insert(
        "genesis_attested_hash".to_string(),
        Value::Bytes(genesis_attested_hash.as_ref().to_vec()),
    );
    payload.insert(
        "child_genesis_timestamp_unix_ns".to_string(),
        Value::Timestamp(child_genesis_time_unix_ns),
    );

    Ok(Some(Message::new(
        msg_type::SPROUT_CHILD_RESPONSE,
        request.request_id,
        payload,
    )))
}
