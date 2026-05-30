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
        Value::Uint(state.manifest.cycle_counter),
    );
    let request = Message::new(msg_type::ADVANCE, 0, payload);

    let _response = crate::ingest::handle_advance(state, &request)?;

    // Bookkeeping — same sequence as the dispatch-arm path at
    // `msg_type::ADVANCE =>` in run_loop's dispatch().
    let prior_cycle = state.manifest.cycle_counter;
    let new_cycle = prior_cycle.saturating_add(1);
    state.manifest.cycle_counter = new_cycle;
    let event_content = crate::events::encode_cycle_advanced(prior_cycle, new_cycle);
    let _ = emit_substrate_event(
        state,
        crate::events::NODE_TYPE_CYCLE_ADVANCED.to_string(),
        event_content,
    );
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
    if self_driven_cycle_advance_enabled() && state.handshake_complete {
        // Best-effort: failures here propagate as immune events via the
        // C31 cycle_step_failed path inside handle_advance, but don't
        // crash the substrate. The next tick retries.
        if let Err(e) = execute_self_driven_cycle_advance(state) {
            let _ = writeln!(
                std::io::stderr(),
                "self-driven cycle advance error: {e}"
            );
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

    let our_substrate_id = state.manifest.substrate_id;
    let our_dag_tip = state.dag.tip().map(|t| t.0);
    let our_signing_seed = state.substrate_signing_seed;
    let _accepted = state.federation.accept_pending()?;
    let events = state.federation.progress_peers(
        &our_substrate_id,
        our_dag_tip.as_ref(),
        Some(&our_signing_seed),
        &state.dag,
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
        }
    }
    let _ = save_dag_state(state);
    Ok(())
}
