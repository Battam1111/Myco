//! M23.1 P4 永恒迭代 — autonomous tick.
//!
//! Extracted from `server/mod.rs`. The main loop's `recv_timeout` Timeout
//! branch invokes [`do_autonomous_tick`], which runs federation progress,
//! health observations (Python liveness / persistence / wall-clock skew /
//! slow-call), and — when enabled — a self-driven cycle advance. None of the
//! behavior changed in the move; this is purely a code-organization split.

use std::io::Write;

use myco_kernel_bridge::protocol::msg_type;

use super::{
    emit_immune_sporocarp, emit_substrate_event, hex_encode, save_dag_state, save_python_state,
    save_snapshot_for_state, ServerState,
};
use crate::SubstrateError;

/// **v3.1.1 Sprint 3** — check whether self-driven cycle advance is enabled.
///
/// When enabled, the autonomous tick path advances the metabolic cycle in
/// addition to its federation work. Closes P04 §10.3's acknowledged debt
/// (substrate-internal scheduling vs request-driven-only advance).
///
/// Truthy values: `1`, `true`, `yes`, `on` (case-insensitive). Anything
/// else (including unset) = disabled. Default off to preserve M23.1
/// behavior; operators / cultivators opt in by setting the env var on
/// substrate launch.
fn self_driven_cycle_advance_enabled() -> bool {
    match std::env::var("MYCO_SELF_DRIVEN_CYCLE_ADVANCE") {
        Ok(v) => {
            let lowered = v.trim().to_ascii_lowercase();
            matches!(lowered.as_str(), "1" | "true" | "yes" | "on")
        }
        Err(_) => false,
    }
}

/// **P04 §3.1 batch-summarized idle advance** — maximum number of inert
/// self-driven no-op cycles to accumulate before forcing a real metabolic
/// cycle (which flushes the pending span).
///
/// Strictly LESS than the P02 hunger-request threshold (10 cycles), so a batch
/// can never straddle a hunger/starvation boundary: a real `handle_advance`
/// runs at least every `SELF_DRIVEN_BATCH_MAX` cycles, evaluating hunger within
/// `≤ SELF_DRIVEN_BATCH_MAX` of any P02 threshold (closes review hole H2). The
/// prune-scan boundary (every `PRUNE_SCAN_DEEP_CYCLE_INTERVAL` = 100) is closed
/// separately by the `prune_boundary` guard in `do_autonomous_tick` (H1).
const SELF_DRIVEN_BATCH_MAX: u64 = 9;

/// **P04 §3.1** — is this cultivar provably inert, so its idle self-driven
/// cycles can be batch-summarized rather than emitting one DAG node per cycle?
///
/// Conservative by construction: ANY axis ever registered, ANY migration in
/// flight, OR ANY federation activity disqualifies batching. This is correct,
/// not over-conservative: DAG replay applies exactly ONE Python `advance()` per
/// `cycle_advanced` node, so batching a cultivar WITH a decay axis would
/// under-decay the re-derived gradient (live ran N advances; replay would run
/// 1). An axis-free cultivar's Python `advance()` is a true no-op, so its idle
/// cycles produce no per-cycle state change and are safe to batch.
fn is_provably_inert_for_batch(state: &ServerState) -> bool {
    !crate::cultivation::is_archived(state)
        && state.migration_candidate.is_none()
        && state.axis_register_count == 0
        && state.federation.listener.is_none()
        && state.federation.peers.is_empty()
}

/// **P04 §3.1** — flush any accumulated inert idle no-op span: advance the
/// cycle counter by the pending span, emit ONE spanning
/// `cycle_advanced(prior, prior + span)` DAG node, and persist.
///
/// No-op (and resets pending to 0) when there is nothing pending OR the
/// substrate is alive::archived (metabolism halted; the pending span, if any,
/// is discarded — an archived substrate must not advance its counter).
///
/// The flush deliberately does NOT call `handle_advance` / Python `advance()`:
/// it is only ever reached with `axis_register_count == 0` accumulated spans
/// (the gate guarantees zero axes for everything counted into `pending`), and
/// an axis-free Python `advance()` is a true no-op — so re-deriving the
/// gradient via one `advance()` per the single spanning node (replay) agrees
/// with the live path trivially (closes review hole H3). The counter only moves
/// here, at a persist boundary, keeping live and replay in lockstep (no C32
/// skew). Invariant after return: `pending_self_driven_noop_cycles == 0`.
pub(super) fn flush_pending_self_driven(
    state: &mut ServerState,
) -> Result<(), SubstrateError> {
    if state.pending_self_driven_noop_cycles == 0 || crate::cultivation::is_archived(state) {
        state.pending_self_driven_noop_cycles = 0;
        return Ok(());
    }
    let prior = state.cycle_counter();
    let span = state.pending_self_driven_noop_cycles;
    let new = prior.saturating_add(span);
    state.set_cycle_counter(new);
    let event_content = crate::events::encode_cycle_advanced(prior, new);
    let _ = emit_substrate_event(
        state,
        crate::events::NODE_TYPE_CYCLE_ADVANCED.to_string(),
        event_content,
    );
    state.pending_self_driven_noop_cycles = 0;
    // Persist the exact same triple as the real cycle path's bookkeeping.
    state.save_manifest()?;
    save_python_state(state)?;
    save_dag_state(state)?;
    Ok(())
}

/// **v3.1.1 Sprint 3** — perform one cycle advance from the autonomous-
/// tick path (no operator request involved).
///
/// Mirrors the dispatch-arm bookkeeping that follows
/// `crate::ingest::handle_advance`: bump cycle counter, emit
/// cycle_advanced, append observatory snapshot, persist. The synthesized
/// ADVANCE message carries the current cycle counter for handle_advance's
/// echo-back path; otherwise it's a minimal request_id=0 message.
///
/// The response from handle_advance is discarded — the autonomous tick
/// has no operator to deliver it to. The cycle's DAG events + observatory
/// snapshot are the persistent record.
///
/// Concurrency: runs in the main loop's single thread, between operator
/// requests. No background thread, no Arc<Mutex>, no concurrent access
/// to ServerState.
fn execute_self_driven_cycle_advance(
    state: &mut ServerState,
) -> Result<(), SubstrateError> {
    use std::collections::BTreeMap;
    use myco_kernel_bridge::protocol::Message;
    use myco_kernel_shared::canonical_bytes::Value;

    let mut payload = BTreeMap::new();
    payload.insert(
        "current_cycle".to_string(),
        Value::Uint(state.cycle_counter()),
    );
    let request = Message::new(msg_type::ADVANCE, 0, payload);

    let response = crate::ingest::handle_advance(state, &request)?;

    // Bookkeeping — same sequence as the dispatch-arm path at
    // `msg_type::ADVANCE =>` in run_loop's dispatch().
    let prior_cycle = state.cycle_counter();
    let new_cycle = prior_cycle.saturating_add(1);
    state.set_cycle_counter(new_cycle);
    let event_content = crate::events::encode_cycle_advanced(prior_cycle, new_cycle);
    let _ = emit_substrate_event(
        state,
        crate::events::NODE_TYPE_CYCLE_ADVANCED.to_string(),
        event_content,
    );
    // **v3.1.1 Sprint 8.G (P03 §10.4)**: per-cycle dual-validation step for the
    // self-driven path — mirrors the operator-driven ADVANCE dispatch arm.
    // Runs AFTER cycle_advanced; zero cost when no migration is in flight.
    if let Some(resp_msg) = response.as_ref() {
        let _ = crate::ingest::run_migration_step(state, resp_msg);
    }
    crate::observatory::append_observatory_snapshot_to_state(state);
    state.save_manifest()?;
    save_python_state(state)?;
    save_dag_state(state)?;
    const SNAPSHOT_EVERY_K_CYCLES: u64 = 10;
    if new_cycle % SNAPSHOT_EVERY_K_CYCLES == 0 {
        let _ = save_snapshot_for_state(state);
    }
    Ok(())
}

/// M23.1 P4 永恒迭代: one autonomous tick.
///
/// Invoked from the main loop's `recv_timeout` Timeout branch. Runs the same
/// federation-side work as `handle_federation_poll` but without producing an
/// operator response (the tick is operator-invisible — its effects are
/// observed via the DAG events emitted).
///
/// Tick is a **no-op** when no federation listener is open (the common case
/// for substrates that don't use federation). This keeps the autonomous-tick
/// path zero-cost for non-federated substrates.
pub(super) fn do_autonomous_tick(state: &mut ServerState) -> Result<(), SubstrateError> {
    use std::time::{SystemTime, UNIX_EPOCH};

    // **v3.1.1 Sprint 3 — self-driven cycle scheduler** (P04 §10.3 debt).
    //
    // When `MYCO_SELF_DRIVEN_CYCLE_ADVANCE` is set (to "1" / "true" / "yes"
    // / "on"), advance the metabolic cycle here in addition to whatever
    // federation work the existing tick path does. This closes P04 §10.3's
    // "request-driven advance" debt: substrate keeps cycling even when the
    // operator process is disconnected or idle.
    //
    // Default: OFF (preserves M23.1 behavior — autonomous tick only does
    // federation work). The operator-driven `handle_advance` dispatch is
    // unchanged either way; this just adds a parallel self-driven path.
    //
    // Concurrency: the autonomous tick runs inside the main loop's
    // request-response thread (recv_timeout Timeout branch). No background
    // thread, no Arc<Mutex>, no concurrent access to ServerState. Operator
    // requests + self-driven cycles serialize naturally through the main
    // loop's request queue.
    //
    // Per L0/cards/P04_eternal_iteration.md §10.3 acknowledged debt +
    // L1/CONTINUITY §1.2 cycle cadence (100ms-10s range covered by the
    // default 500ms tick interval).
    if self_driven_cycle_advance_enabled()
        && state.handshake_complete
        && !crate::cultivation::is_archived(state)
    {
        // **P04 §3.1 batch-summarized idle advance.** A provably-inert idle
        // cultivar (no axes, no migration, no federation) ticks continuously
        // per P04 but every tick is a true no-op. Rather than emit one
        // `cycle_advanced` node + persist per tick (bloating the eternal DAG),
        // accumulate the no-op cycles in memory and summarize them into ONE
        // spanning node at a flush boundary. P04 is honored (it never stops
        // iterating; the advance is batch-summarized, which §3.1 explicitly
        // permits); C59 is honored (sum-of-spans == cycle_counter).
        //
        // `next_post_cycle` is the post-cycle counter the NEXT real cycle would
        // land on (current counter + already-pending span + this tick). Two
        // hard boundaries force a real cycle instead of batching:
        //  - H1 prune-scan boundary: a real `handle_advance` must run the F26
        //    应朽 prune-scan at every `PRUNE_SCAN_DEEP_CYCLE_INTERVAL` (= 100);
        //    a batch must never straddle it. `should_run_prune_scan` is the SSoT
        //    for that cadence (crate::prune).
        //  - cap: `SELF_DRIVEN_BATCH_MAX` (= 9) bounds the span; this also
        //    closes H2 (P02 hunger evaluated within ≤9 of any threshold).
        let next_post_cycle = state
            .cycle_counter()
            .saturating_add(state.pending_self_driven_noop_cycles)
            .saturating_add(1);
        let prune_boundary = crate::prune::should_run_prune_scan(next_post_cycle);
        if is_provably_inert_for_batch(state)
            && state.pending_self_driven_noop_cycles + 1 < SELF_DRIVEN_BATCH_MAX
            && !prune_boundary
        {
            // Inert no-op: accumulate ONLY. No handle_advance, no Python
            // advance, no DAG node, no persist. The span is summarized at the
            // next flush (a meaningful/boundary/cap cycle, an operator request,
            // or shutdown). Keeps the eternal DAG bounded for an idle cultivar.
            state.pending_self_driven_noop_cycles += 1;
        } else {
            // Meaningful / boundary / cap / non-inert: flush the accumulated
            // span (seals it into ONE spanning cycle_advanced before any real
            // node so C59 has no gap), then run ONE real metabolic cycle.
            if let Err(e) = flush_pending_self_driven(state) {
                let _ = writeln!(
                    std::io::stderr(),
                    "self-driven idle-batch flush error: {e}"
                );
            }
            // Best-effort: failures here propagate as immune events via the
            // C31 cycle_step_failed path inside handle_advance, but don't
            // crash the substrate. The next tick retries.
            // **COV06 T7**: an alive::archived substrate halts metabolism — the
            // self-driven scheduler skips cycle advance (state_dir cold-readable).
            if let Err(e) = execute_self_driven_cycle_advance(state) {
                let _ = writeln!(
                    std::io::stderr(),
                    "self-driven cycle advance error: {e}"
                );
            }
        }
    }

    // **v3.1.1 Sprint 6.J (T2.8)** — Python slow-call observation.
    //
    // Each substrate-→-Python call records its wall-clock duration via
    // python_call_health::record_call_duration. The autonomous tick polls
    // and emits C65 once per slow-call burst. This surfaces "Python
    // getting slow" BEFORE the eventual hang, giving ops time to
    // investigate. Real deadlock recovery (BridgeClient reader-thread
    // refactor with recv_timeout) is Sprint 6.J.2 follow-up.
    if state.handshake_complete {
        let obs = crate::python_call_health::take_python_call_health_observation();
        if obs.should_emit_c65 {
            let evidence = format!(
                "Python worker had at least one slow call in recent history: \
                 lifetime_slow_call_count={} (cumulative), \
                 largest_call_duration_ms={} (>= MYCO_PYTHON_SLOW_CALL_THRESHOLD_MS, \
                 default 30000). This is a precursor to deadlock; operators \
                 should investigate Python worker state. Substrate continues \
                 because the slow call eventually returned, but ongoing \
                 slowness suggests resource pressure.",
                obs.lifetime_slow_call_count, obs.largest_call_duration_ms,
            );
            let _ = emit_immune_sporocarp(
                state,
                "C65_python_worker_slow_call",
                "python_worker_slow_call",
                &evidence,
            );
            let _ = save_dag_state(state);
        }
    }

    // **v3.1.1 Sprint 8.G (P03 §10.4)** — C66 schema_migration_window_exceeded.
    //
    // A migration that has been Validating for longer than
    // `window + DEFAULT_MIGRATION_GRACE_CYCLES` without reaching a
    // commit/rollback decision is anomalous: the most likely cause is that the
    // substrate restarted mid-window and the per-cycle decision cadence lost
    // sync, OR the operator process went idle and stopped driving ADVANCE so
    // the window never completes. Either way the candidate must not linger
    // indefinitely — we fire C66 (per-detector cooldown, like C54/C63/C64/C65)
    // and FORCE the rollback path so the active gradient stays canonical and
    // the candidate is dropped. Mirrors the scaffold const
    // `C66_MIGRATION_WINDOW_EXCEEDED`.
    if state.handshake_complete {
        if let Some(candidate) = &state.migration_candidate {
            let cycle = state.cycle_counter();
            let grace = myco_kernel_schema::migration::DEFAULT_MIGRATION_GRACE_CYCLES;
            let exceeded = matches!(
                candidate.phase,
                myco_kernel_schema::migration::MigrationPhase::Validating
            ) && candidate.window_exceeded(cycle, grace);
            if exceeded {
                const C66_WINDOW_EXCEEDED_COOLDOWN_CYCLES: u64 = 100;
                let cooldown_active =
                    match state.last_migration_window_exceeded_emitted_at_cycle {
                        Some(last) => {
                            cycle.saturating_sub(last) < C66_WINDOW_EXCEEDED_COOLDOWN_CYCLES
                        }
                        None => false,
                    };
                if !cooldown_active {
                    let op = candidate.op_name.clone();
                    let started = candidate.started_at_cycle;
                    let window = candidate.dual_validation_window_cycles;
                    let evidence = format!(
                        "schema migration (op={op}) exceeded its dual-validation window: \
                         started_at_cycle={started}, window={window}, grace={grace}, \
                         current_cycle={cycle} (elapsed {} > window+grace {}); forcing \
                         rollback per P03 §10.4 so the candidate cannot linger. Most \
                         likely cause: substrate restarted mid-window or the operator \
                         stopped driving cycles.",
                        cycle.saturating_sub(started),
                        window.saturating_add(grace),
                    );
                    let _ = emit_immune_sporocarp(
                        state,
                        myco_kernel_schema::migration::C66_MIGRATION_WINDOW_EXCEEDED,
                        "schema_migration_window_exceeded",
                        &evidence,
                    );
                    state.last_migration_window_exceeded_emitted_at_cycle = Some(cycle);

                    // Force the rollback path: tell Python to drop the
                    // candidate, emit schema_migration_rolled_back + the legacy
                    // evolution_failed sibling, clear the candidate.
                    let reason = format!(
                        "C66 window exceeded (elapsed {} > window+grace {})",
                        cycle.saturating_sub(started),
                        window.saturating_add(grace),
                    );
                    if let Err(e) = crate::ingest::force_migration_rollback(state, &op, &reason) {
                        let _ = emit_immune_sporocarp(
                            state,
                            "C31_cycle_step_failed",
                            "cycle_step_failed",
                            &format!("C66 forced rollback (op={op}) failed: {e}"),
                        );
                    }
                    let _ = save_dag_state(state);
                }
            }
        }
    }

    // **COV06 不弃不孤** — the cultivator-mortality / succession staleness
    // watchdog was REMOVED with the owner-key/anchor layer (v0.9): it depended on
    // owner-attested `cultivator_heartbeat_*` liveness pulses, which no longer
    // exist. The cultivation-succession FSM states (Normal / Legacy / Orphaned /
    // Archived / Recovered) remain DAG-derived; the bet-retirement archive seal +
    // the C46-gated succession path still drive the reachable transitions.

    // **v3.1.1 Sprint 6.G (T2.12)** — persistence-health observation.
    //
    // Each `save_dag_state` failure increments a process-global counter.
    // Poll for "should emit C64" (one-shot per failure burst). On true:
    // emit C64_persistence_unavailable immune sporocarp (best-effort —
    // the DAG-emit itself may fail since same disk, but the rate-limit
    // logic from Sprint 5.F handles repeat suppression).
    if state.handshake_complete {
        let obs = crate::persistence_health::take_persistence_health_observation();
        if obs.should_emit_c64 {
            let evidence = format!(
                "substrate state_dir persistence is failing: consecutive_failures={} \
                 (since last success), lifetime_failures={} total. State_dir may be \
                 read-only, disk full, or permissions revoked. Substrate continues \
                 with in-memory state but mutations are not durable until recovery.",
                obs.consecutive_failures, obs.lifetime_failures,
            );
            let _ = emit_immune_sporocarp(
                state,
                "C64_persistence_unavailable",
                "persistence_unavailable",
                &evidence,
            );
            // No save_dag_state call here — it would fail again. The
            // event lives in-memory; will persist on the next successful
            // save (after recovery).
        }
    }

    // **v3.1.1 Sprint 6.C (T1.7)** — wall-clock skew observation.
    //
    // The monotonic_unix_ns helper (substrate/src/wall_clock.rs) tracks
    // backward jumps as a side effect. Poll for accumulated skew on
    // each tick; emit C63_wall_clock_skew_detected if any skew occurred
    // since the last poll. This surfaces NTP corrections, manual
    // clock changes, and VM clock drift to the operator as immune
    // signals — vs. silently mis-time-stamping every subsequent event.
    if state.handshake_complete {
        let obs = crate::wall_clock::take_skew_observation();
        if obs.detection_count_since_last_take > 0 {
            let evidence = format!(
                "wall-clock backward-jump detected: {} skew events since last \
                 observation, largest jump = {} ns ({:.3} ms). Substrate's \
                 monotonic_unix_ns helper compensated; downstream rate-limits + \
                 nonce expiries remain protected. Operator should investigate \
                 host clock-sync configuration.",
                obs.detection_count_since_last_take,
                obs.largest_backward_jump_ns,
                obs.largest_backward_jump_ns as f64 / 1_000_000.0,
            );
            let _ = emit_immune_sporocarp(
                state,
                "C63_wall_clock_skew_detected",
                "wall_clock_skew_detected",
                &evidence,
            );
            let _ = save_dag_state(state);
        }
    }

    // **v3.1.1 Sprint 5.E** — Python worker liveness check (T2.3).
    //
    // Detects silent Python death (OOM, segfault, unhandled exception) BEFORE
    // the next operator call blocks forever on stdin/stdout read. Calls
    // `is_child_alive()` which is non-blocking (try_wait under the hood).
    //
    // On detected death: emit C60_python_worker_unexpected_exit immune
    // sporocarp ONCE (cooldown via a flag in ServerState would be cleaner
    // long-term; current behavior is at-most-once per substrate boot via
    // the `python_worker_death_logged` flag).
    //
    // Without this check, the operator hangs indefinitely on the next call;
    // with it, the operator gets a typed error AND the DAG records the
    // event for post-mortem.
    if state.handshake_complete && !state.python_worker_death_logged {
        if let Some(client) = state.python_client.as_mut() {
            match client.is_child_alive() {
                Ok(false) => {
                    let _ = emit_immune_sporocarp(
                        state,
                        "C60_python_worker_unexpected_exit",
                        "python_worker_unexpected_exit",
                        "Python worker child process has exited (try_wait returned exit status); \
                         subsequent operator calls will fail with bridge errors. Substrate \
                         transitions to python_unavailable state.",
                    );
                    state.python_worker_death_logged = true;
                    let _ = save_dag_state(state);
                }
                Ok(true) => { /* worker alive, no action */ }
                Err(_) => { /* try_wait syscall failed — leave to next tick */ }
            }
        }
    }

    if state.federation.listener.is_none() && state.federation.peers.is_empty() {
        // Fast path: nothing federation-related to poll.
        return Ok(());
    }

    let our_substrate_id = state.substrate_id();
    let our_dag_tip = state.dag.tip().map(|t| t.0);
    let our_signing_seed = state.substrate_signing_seed;
    let _accepted = state.federation.accept_pending()?;
    // **C13**: pass the revoked-set so the egress site blocks (pre-emission)
    // any FED_EVENT_BATCH to a revoked peer on the autonomous tick path too.
    let events = state.federation.progress_peers(
        &our_substrate_id,
        our_dag_tip.as_ref(),
        Some(&our_signing_seed),
        &state.dag,
        &state.revoked_federation_peers,
    );

    if events.is_empty() {
        return Ok(());
    }

    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);

    for ev in events {
        match ev {
            crate::federation::PollPeerEvent::Pinned {
                peer_substrate_id,
                remote_addr_str,
                peer_dag_tip: _,
                signer_pubkey,
                signature_verified,
            } => {
                // M25.4 (autonomous tick path): include the signer_pubkey in
                // the federation_peer_pinned event if the hello signature was
                // verified. Legacy peers (no signature) also emit a separate
                // federation_legacy_peer_pinned observability event.
                let _ = crate::federation::emit_federation_peer_pinned(
                    state,
                    &peer_substrate_id,
                    &remote_addr_str,
                    now,
                    signer_pubkey.as_ref(),
                );
                if !signature_verified {
                    let _ = crate::federation::emit_federation_legacy_peer_pinned(
                        state,
                        &peer_substrate_id,
                        &remote_addr_str,
                        now,
                    );
                }
            }
            crate::federation::PollPeerEvent::RejectedSelfConnection { remote_addr_str } => {
                let _ = crate::federation::emit_federation_peer_rejected(
                    state,
                    &our_substrate_id,
                    &our_substrate_id,
                    &remote_addr_str,
                    "inbound peer claimed our own substrate_id (autonomous tick)",
                );
            }
            crate::federation::PollPeerEvent::RejectedSignatureInvalid {
                peer_substrate_id,
                remote_addr_str,
                reason,
            } => {
                let _ = crate::federation::emit_federation_hello_signature_invalid(
                    state,
                    &peer_substrate_id,
                    &remote_addr_str,
                    &reason,
                );
            }
            crate::federation::PollPeerEvent::FailedFrameRead {
                remote_addr_str,
                reason,
            } => {
                let _ = crate::federation::emit_federation_peer_rejected(
                    state,
                    &[0u8; 32],
                    &our_substrate_id,
                    &remote_addr_str,
                    &format!("autonomous tick frame read failure: {reason}"),
                );
            }
            crate::federation::PollPeerEvent::EventsSent {
                peer_substrate_id,
                sent_event_hashes,
            } => {
                let content = crate::events::encode_federation_events_sent(
                    &peer_substrate_id,
                    &sent_event_hashes,
                    now,
                );
                let _ = emit_substrate_event(
                    state,
                    crate::events::NODE_TYPE_FEDERATION_EVENTS_SENT.to_string(),
                    content,
                );
            }
            crate::federation::PollPeerEvent::RejectedProtocolVersion {
                peer_substrate_id,
                remote_addr_str,
                peer_version,
                our_version,
            } => {
                // **v3.1.1 Sprint 5.H (T2.5)** — emit C61 from the
                // autonomous tick path.
                let evidence = format!(
                    "federation protocol version mismatch at fed_hello: \
                     peer.substrate_id={} from {remote_addr_str} declared \
                     protocol_version={peer_version}, our version={our_version} \
                     (autonomous tick)",
                    hex_encode(&peer_substrate_id)
                );
                let _ = emit_immune_sporocarp(
                    state,
                    "C61_federation_protocol_version_mismatch",
                    "federation_protocol_version_mismatch",
                    &evidence,
                );
            }
            crate::federation::PollPeerEvent::EgressBlockedRevoked {
                peer_substrate_id,
                remote_addr_str,
            } => {
                // **C13** (autonomous tick path) — the egress site already
                // suppressed the FED_EVENT_BATCH to the revoked peer; fruit the
                // immune sporocarp recording the blocked outbound envelope.
                let evidence = format!(
                    "federation_egress_blocked: outbound FED_EVENT_BATCH to peer {} \
                     (remote={remote_addr_str}) suppressed pre-emission — peer is on the \
                     owner-revocation list (L1/GOVERNANCE §5.2, autonomous tick)",
                    hex_encode(&peer_substrate_id)
                );
                // implements L0::P8; negative-witness: substrate/tests/e2e_revocation.rs::c13_attested_revoke_emits_crl_event_and_blocks_egress
                let _ = emit_immune_sporocarp(
                    state,
                    "C13_peer_attestation_revoked_egress",
                    "peer_attestation_revoked_egress",
                    &evidence,
                );
            }
        }
    }
    let _ = save_dag_state(state);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::persistence::Manifest;
    use crate::server::ServerState;
    use myco_kernel_schema::dag::Dag;
    use myco_kernel_schema::migration::{
        CandidateState, DEFAULT_DUAL_VALIDATION_WINDOW_CYCLES, DEFAULT_MIGRATION_GRACE_CYCLES,
    };

    fn test_state() -> ServerState {
        // Unique, on-disk state_dir per call: the flush tests below exercise
        // flush_pending_self_driven, which persists (manifest/python/dag), so the
        // dir MUST exist on a clean runner. The previous path was never created
        // on disk and passed only when a stale temp dir happened to be present
        // (it was on the dev box, not on a fresh CI runner -> CI red).
        static SEQ: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
        let seq = SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let state_dir = std::env::temp_dir().join(format!(
            "myco-autonomous-unit-{}-{}",
            std::process::id(),
            seq
        ));
        let _ = std::fs::create_dir_all(&state_dir);
        // Task #8i: seed the discrete identity fields from a fresh genesis
        // Manifest (random non-zero id ⇒ Some). cycle_counter starts at 0;
        // tests bump it via `set_cycle_counter`.
        let g = Manifest::genesis();
        ServerState::new(
            state_dir,
            Some(g.substrate_id),
            Some(g.genesis_time_unix_ns),
            g.cycle_counter,
            g.last_absorbed_cycle,
            g.generation_depth,
            Dag::new(),
            [0u8; 32],
        )
    }

    fn validating_candidate(started_at_cycle: u64) -> CandidateState {
        let mut c = CandidateState::new(
            vec![1, 2, 3],
            "modify_axis_threshold".to_string(),
            0,
            DEFAULT_DUAL_VALIDATION_WINDOW_CYCLES,
        );
        c.enter_validating(started_at_cycle);
        c
    }

    fn count_immune(state: &ServerState, detector_substr: &str) -> usize {
        state
            .dag
            .iter_in_insertion_order()
            .filter(|n| n.node_type.starts_with("immune:") && n.node_type.contains(detector_substr))
            .count()
    }

    // ----------------------------------------------------------------------
    // **P04 §3.1 batch-summarized idle advance** — gate tests.
    //
    // The self-driven scheduler reads the process-global env var
    // `MYCO_SELF_DRIVEN_CYCLE_ADVANCE`; cargo runs unit tests in parallel, so
    // these tests serialize through TEST_LOCK and set/clear the var under it.
    // The batch path never calls Python (it only accumulates), so these tests
    // run without a Python worker — they exercise the inert-batch arm of
    // `do_autonomous_tick` and `flush_pending_self_driven` directly.
    // ----------------------------------------------------------------------
    static TEST_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

    /// Count `cycle_advanced` DAG nodes.
    fn count_cycle_advanced_nodes(state: &ServerState) -> usize {
        state
            .dag
            .iter_in_insertion_order()
            .filter(|n| n.node_type == crate::events::NODE_TYPE_CYCLE_ADVANCED)
            .count()
    }

    /// Sum the spans (`new_cycle − prior_cycle`) of every `cycle_advanced`
    /// node — the C59 invariant LHS (mirrors integrity::decode_cycle_advanced_span).
    fn sum_cycle_advanced_spans(state: &ServerState) -> u64 {
        use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value};
        state
            .dag
            .iter_in_insertion_order()
            .filter(|n| n.node_type == crate::events::NODE_TYPE_CYCLE_ADVANCED)
            .map(|n| {
                let decoded = match cb_decode(n.content_canonical_bytes.as_ref()) {
                    Ok(Value::Map(m)) => m,
                    _ => return 1u64, // legacy per-node assumption
                };
                let prior = match decoded.get("prior_cycle") {
                    Some(Value::Uint(u)) => *u,
                    _ => return 1u64,
                };
                let new = match decoded.get("new_cycle") {
                    Some(Value::Uint(u)) => *u,
                    _ => return 1u64,
                };
                new.saturating_sub(prior)
            })
            .fold(0u64, |acc, span| acc.saturating_add(span))
    }

    /// **Gate test 1** — for a provably-inert cultivar, driving N self-driven
    /// idle ticks emits FEWER cycle_advanced nodes than N (batching), yet the
    /// C59 invariant (Σ spans == cycle_counter) still holds after a flush.
    ///
    /// We drive exactly `SELF_DRIVEN_BATCH_MAX - 1` ticks: the gate batches a
    /// tick iff `pending + 1 < SELF_DRIVEN_BATCH_MAX`, so these all take the
    /// pure-accumulation arm (no `execute_self_driven_cycle_advance`, hence no
    /// Python worker needed in this unit test). The cap arm IS exercised in the
    /// full e2e harness (it runs a real metabolic cycle, which needs Python);
    /// here we isolate the batching invariant. The N-1 idle ticks collapse into
    /// ONE spanning node at the flush — the core P04 §3.1 reduction.
    #[test]
    fn inert_idle_ticks_batch_and_c59_holds() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        std::env::set_var("MYCO_SELF_DRIVEN_CYCLE_ADVANCE", "1");

        let mut state = test_state();
        state.handshake_complete = true;
        assert!(
            is_provably_inert_for_batch(&state),
            "a fresh axis-free, migration-free, non-federated, non-archived \
             genesis substrate must be eligible to batch"
        );

        // Stay strictly inside one batch window (no cap-forced real cycle) and
        // well below the first prune boundary (cycle 100): every tick batches.
        let n: u64 = SELF_DRIVEN_BATCH_MAX - 1; // = 8
        for _ in 0..n {
            do_autonomous_tick(&mut state).expect("tick");
        }
        // Mid-run, nothing is on disk yet: all n cycles are pending in memory,
        // and ZERO cycle_advanced nodes exist (the whole point — no per-cycle
        // DAG bloat for an idle cultivar).
        assert_eq!(state.pending_self_driven_noop_cycles, n);
        assert_eq!(
            count_cycle_advanced_nodes(&state),
            0,
            "an inert idle cultivar emits NO cycle_advanced node until a flush"
        );
        assert_eq!(
            state.cycle_counter(),
            0,
            "the counter does not move until a flush (live == replay)"
        );

        // Seal the in-memory span: n ticks → ONE spanning node, counter == n.
        flush_pending_self_driven(&mut state).expect("flush");

        std::env::remove_var("MYCO_SELF_DRIVEN_CYCLE_ADVANCE");

        let nodes = count_cycle_advanced_nodes(&state) as u64;
        assert!(
            nodes < n,
            "batching must emit fewer cycle_advanced nodes ({nodes}) than ticks ({n})"
        );
        assert_eq!(nodes, 1, "the whole inert batch collapses into ONE node");
        // C59: sum of spans equals the cycle counter, AND both equal n (every
        // idle tick accounted for, none lost).
        assert_eq!(
            sum_cycle_advanced_spans(&state),
            state.cycle_counter(),
            "C59 sum-of-spans must equal cycle_counter"
        );
        assert_eq!(state.cycle_counter(), n, "all n idle cycles accounted for");
        assert_eq!(
            state.pending_self_driven_noop_cycles, 0,
            "pending must be 0 at the persist boundary"
        );
        // Observed reduction factor (for the report): n ticks → `nodes` node(s).
        eprintln!(
            "[batch-test] {n} idle ticks -> {nodes} cycle_advanced node ({n}x reduction)"
        );
    }

    /// **Gate test 2** — a batch must never straddle the prune-scan boundary
    /// (every PRUNE_SCAN_DEEP_CYCLE_INTERVAL = 100). The tick whose
    /// `next_post_cycle` is a multiple of 100 must NOT take the batch arm; it
    /// flushes the prior span (sealing the pre-boundary cycles) and falls
    /// through to the real-cycle arm. We assert the gate decision directly
    /// (the real-cycle arm needs Python; the BATCH decision does not).
    #[test]
    fn prune_boundary_is_never_batched() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());

        // The boundary predicate the tick uses: next_post_cycle % 100 == 0.
        assert!(
            crate::prune::should_run_prune_scan(100),
            "cycle 100 is a prune-scan boundary"
        );
        assert!(
            !crate::prune::should_run_prune_scan(99),
            "cycle 99 is not a boundary"
        );

        // Stand a cultivar at counter=98 with one already-pending no-op (so the
        // next tick's next_post_cycle = 98 + 1 + 1 = 100, the boundary). Even
        // though it is inert and under the cap, the boundary guard must FORCE
        // the non-batch arm: assert the exact composite predicate the tick uses.
        let mut state = test_state();
        state.handshake_complete = true;
        state.set_cycle_counter(98);
        state.pending_self_driven_noop_cycles = 1;

        let next_post_cycle = state
            .cycle_counter()
            .saturating_add(state.pending_self_driven_noop_cycles)
            .saturating_add(1);
        assert_eq!(next_post_cycle, 100);
        let prune_boundary = crate::prune::should_run_prune_scan(next_post_cycle);
        let would_batch = is_provably_inert_for_batch(&state)
            && state.pending_self_driven_noop_cycles + 1 < SELF_DRIVEN_BATCH_MAX
            && !prune_boundary;
        assert!(
            !would_batch,
            "the tick landing on a %100 boundary must NOT batch (so the real \
             cycle runs the F26 应朽 prune-scan)"
        );

        // One step below the boundary (next_post_cycle = 99) WOULD batch.
        let mut state2 = test_state();
        state2.handshake_complete = true;
        state2.set_cycle_counter(97);
        state2.pending_self_driven_noop_cycles = 1;
        let npc2 = state2
            .cycle_counter()
            .saturating_add(state2.pending_self_driven_noop_cycles)
            .saturating_add(1);
        assert_eq!(npc2, 99);
        let would_batch2 = is_provably_inert_for_batch(&state2)
            && state2.pending_self_driven_noop_cycles + 1 < SELF_DRIVEN_BATCH_MAX
            && !crate::prune::should_run_prune_scan(npc2);
        assert!(would_batch2, "a non-boundary inert tick under the cap batches");
    }

    /// **Gate test 3** — `flush_pending_self_driven` is a no-op when pending==0
    /// and when archived; after a real flush, pending==0 and the counter equals
    /// the sum of cycle_advanced spans.
    #[test]
    fn flush_is_noop_when_empty_or_archived_and_seals_otherwise() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());

        // (a) pending==0 → no node emitted, counter unchanged.
        let mut state = test_state();
        state.handshake_complete = true;
        let counter_before = state.cycle_counter();
        let nodes_before = count_cycle_advanced_nodes(&state);
        flush_pending_self_driven(&mut state).expect("flush empty");
        assert_eq!(state.cycle_counter(), counter_before);
        assert_eq!(count_cycle_advanced_nodes(&state), nodes_before);
        assert_eq!(state.pending_self_driven_noop_cycles, 0);

        // (b) archived + pending>0 → no advance, pending reset to 0, no node.
        let mut state = test_state();
        state.handshake_complete = true;
        state.cultivation_state = crate::cultivation::CultivationState::Archived;
        state.pending_self_driven_noop_cycles = 5;
        let counter_before = state.cycle_counter();
        let nodes_before = count_cycle_advanced_nodes(&state);
        flush_pending_self_driven(&mut state).expect("flush archived");
        assert_eq!(
            state.cycle_counter(),
            counter_before,
            "archived substrate must not advance its counter on flush"
        );
        assert_eq!(count_cycle_advanced_nodes(&state), nodes_before);
        assert_eq!(state.pending_self_driven_noop_cycles, 0);

        // (c) pending>0, not archived → one spanning node, counter advances by
        // the span, pending reset, C59 holds.
        let mut state = test_state();
        state.handshake_complete = true;
        let prior = state.cycle_counter();
        state.pending_self_driven_noop_cycles = 7;
        flush_pending_self_driven(&mut state).expect("flush span");
        assert_eq!(state.cycle_counter(), prior + 7);
        assert_eq!(state.pending_self_driven_noop_cycles, 0);
        assert_eq!(count_cycle_advanced_nodes(&state), 1);
        assert_eq!(sum_cycle_advanced_spans(&state), state.cycle_counter());
    }

    #[test]
    fn c66_fires_and_forces_rollback_when_window_exceeded() {
        // A migration that started at cycle 0, with the cycle counter now well
        // past window+grace, must trip C66 in the autonomous tick: emit the
        // immune event AND force the rollback (clear the candidate). The Python
        // commit/abort call fails gracefully (no worker in this unit test); the
        // detector + candidate-clear still fire (best-effort rollback).
        let mut state = test_state();
        state.handshake_complete = true;
        state.migration_candidate = Some(validating_candidate(0));
        // current cycle strictly past window + grace (100 + 10 = 110).
        state.set_cycle_counter(
            DEFAULT_DUAL_VALIDATION_WINDOW_CYCLES + DEFAULT_MIGRATION_GRACE_CYCLES + 5,
        );

        do_autonomous_tick(&mut state).expect("tick");

        assert_eq!(
            count_immune(&state, "C66_schema_migration_window_exceeded"),
            1,
            "C66 must fire exactly once when the migration window is exceeded"
        );
        assert!(
            state.migration_candidate.is_none(),
            "C66 must force the rollback path (clear the in-flight candidate)"
        );
        // The forced rollback also leaves a schema_migration_rolled_back event.
        let rolled_back = state
            .dag
            .iter_in_insertion_order()
            .filter(|n| n.node_type.starts_with("schema_migration_rolled_back:"))
            .count();
        assert_eq!(rolled_back, 1, "forced rollback emits the rolled_back event");
    }

    #[test]
    fn c66_does_not_fire_within_window_plus_grace() {
        let mut state = test_state();
        state.handshake_complete = true;
        state.migration_candidate = Some(validating_candidate(0));
        // current cycle at the grace boundary → not strictly past → no fire.
        state.set_cycle_counter(DEFAULT_DUAL_VALIDATION_WINDOW_CYCLES + DEFAULT_MIGRATION_GRACE_CYCLES);

        do_autonomous_tick(&mut state).expect("tick");

        assert_eq!(
            count_immune(&state, "C66_schema_migration_window_exceeded"),
            0,
            "C66 must NOT fire within window+grace"
        );
        assert!(
            state.migration_candidate.is_some(),
            "the candidate must remain in flight within window+grace"
        );
    }

    #[test]
    fn c66_respects_cooldown() {
        let mut state = test_state();
        state.handshake_complete = true;
        state.migration_candidate = Some(validating_candidate(0));
        state.set_cycle_counter(
            DEFAULT_DUAL_VALIDATION_WINDOW_CYCLES + DEFAULT_MIGRATION_GRACE_CYCLES + 5,
        );

        // First tick fires C66 + clears candidate + records the emission cycle.
        do_autonomous_tick(&mut state).expect("tick 1");
        assert_eq!(count_immune(&state, "C66_schema_migration_window_exceeded"), 1);
        let emitted_at = state.last_migration_window_exceeded_emitted_at_cycle;
        assert_eq!(
            emitted_at,
            Some(DEFAULT_DUAL_VALIDATION_WINDOW_CYCLES + DEFAULT_MIGRATION_GRACE_CYCLES + 5)
        );

        // Re-arm a fresh candidate at the SAME cycle (simulating a new window
        // that also overshoots immediately) — within the 100-cycle cooldown the
        // detector must NOT re-emit, so the count stays at 1.
        state.migration_candidate = Some(validating_candidate(0));
        do_autonomous_tick(&mut state).expect("tick 2");
        assert_eq!(
            count_immune(&state, "C66_schema_migration_window_exceeded"),
            1,
            "C66 must be suppressed within its cooldown window"
        );
    }

}
