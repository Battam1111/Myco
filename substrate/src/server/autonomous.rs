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

/// **COV06** — 100-cycle cooldown for the cultivation staleness emissions
/// (same discipline as the C54/C66 detectors).
const COV06_EMISSION_COOLDOWN_CYCLES: u64 = 100;

/// **COV06** — the cultivation-succession staleness watchdog (one tick).
///
/// Derives the current FSM state, resolves the config (cadence/windows/terminal
/// choice with `MYCO_TEST_*` overrides), and — given an operator-threaded "now"
/// anchor timestamp — emits the due FSM transition:
///
///   - T1 (normal→legacy): staleness > 3× cadence → `cultivator_heartbeat_stale`.
///   - T4 (legacy→orphaned): legacy_window elapsed OR empty successor_chain →
///     `cultivation_orphaned` (un-suppressible via `emit_substrate_event`).
///   - T6/T7 (orphaned→terminal): orphaned_terminal_window elapsed → a
///     `self_euthanasia_proposal:cultivation_orphaned_terminal` (choice=
///     self_euthanasia; the existing accept path executes it — NOT auto-death)
///     OR a `bet_retired_proposal` (choice=bet_retirement). `indefinite_orphan`
///     emits nothing terminal (the cultivar persists in limbo).
///
/// No-op when no anchor "now" is available (the substrate never reads its own
/// clock for liveness, AS §5.2) or when there is no recorded heartbeat to
/// measure staleness from.
fn do_cultivation_staleness_tick(state: &mut ServerState) {
    use crate::cultivation::{
        compute_staleness, current_cultivation_state, resolve_anchor_now_ns, CultivationState,
        SuccessionConfig,
    };

    // The substrate measures staleness only against an operator-threaded "now".
    let now_anchor = match resolve_anchor_now_ns() {
        Some(t) => t,
        None => return, // no anchor clock threaded → watchdog dormant.
    };
    // Need a recorded heartbeat to measure staleness from.
    let (last_hb_pubkey, last_hb_ts) = match state.latest_heartbeat.as_ref() {
        Some(h) => (h.cultivator_pubkey, h.anchor_timestamp_unix_ns),
        None => return,
    };

    let cfg = SuccessionConfig::resolve(state);
    let staleness_days = compute_staleness(last_hb_ts, now_anchor);
    let current = current_cultivation_state(state);
    let cycle = state.cycle_counter();

    match current {
        CultivationState::Archived => {
            // Terminal — no further FSM transitions.
        }
        CultivationState::Normal | CultivationState::Recovered => {
            // T1: normal→legacy when staleness exceeds 3× cadence.
            let threshold = cfg.staleness_threshold_days() as i64;
            if staleness_days > threshold {
                let on_cooldown = state
                    .last_cultivator_heartbeat_stale_emitted_at_cycle
                    .map(|last| cycle.saturating_sub(last) < COV06_EMISSION_COOLDOWN_CYCLES)
                    .unwrap_or(false);
                if !on_cooldown {
                    let content = crate::events::encode_cultivator_heartbeat_stale(
                        &last_hb_pubkey,
                        last_hb_ts,
                        now_anchor,
                        staleness_days as u64,
                        cfg.cadence_days,
                        cycle,
                    );
                    let nt = crate::events::cultivator_heartbeat_stale_node_type(&last_hb_pubkey);
                    let _ = emit_substrate_event(state, nt, content);
                    state.last_cultivator_heartbeat_stale_emitted_at_cycle = Some(cycle);
                    let _ = save_dag_state(state);
                }
            }
        }
        CultivationState::Legacy => {
            // T4: legacy→orphaned when legacy_window elapsed OR the successor
            // chain is empty (empty chain at legacy entry → immediate orphan).
            let legacy_window_days = cfg.legacy_window_days as i64;
            let empty_chain = state.successor_chain.is_empty();
            if staleness_days >= legacy_window_days || empty_chain {
                let on_cooldown = state
                    .last_cultivation_orphaned_emitted_at_cycle
                    .map(|last| cycle.saturating_sub(last) < COV06_EMISSION_COOLDOWN_CYCLES)
                    .unwrap_or(false);
                if !on_cooldown {
                    let reason = if empty_chain {
                        "empty_chain_at_legacy"
                    } else {
                        "legacy_window_elapsed"
                    };
                    let content = crate::events::encode_cultivation_orphaned(
                        &last_hb_pubkey,
                        now_anchor,
                        reason,
                        cycle,
                    );
                    let nt = crate::events::cultivation_orphaned_node_type(&last_hb_pubkey);
                    // **P07-protected + un-suppressible**: emit via
                    // emit_substrate_event (bypasses the immune rate-limiter).
                    let _ = emit_substrate_event(state, nt, content);
                    state.last_cultivation_orphaned_emitted_at_cycle = Some(cycle);
                    let _ = save_dag_state(state);
                }
            }
        }
        CultivationState::Orphaned => {
            // T6/T7: orphaned→terminal when orphaned_terminal_window elapsed.
            // Measured from the latest heartbeat (the cultivator's last known
            // liveness); the orphaned_terminal_window is the FULL elapsed
            // staleness budget per L1/GOVERNANCE §3.2.C.
            let terminal_window_days = cfg.orphaned_terminal_window_days as i64;
            if staleness_days >= terminal_window_days {
                let on_cooldown = state
                    .last_cultivation_terminal_emitted_at_cycle
                    .map(|last| cycle.saturating_sub(last) < COV06_EMISSION_COOLDOWN_CYCLES)
                    .unwrap_or(false);
                if !on_cooldown {
                    match cfg.terminal_choice.as_str() {
                        "self_euthanasia" => {
                            // T6: emit a self_euthanasia_proposal whose axis_name
                            // is `cultivation_orphaned_terminal` so the existing
                            // accept_self_euthanasia_proposal path can EXECUTE it
                            // (cultivator co-attestation). This is a PROPOSAL —
                            // NOT auto-death.
                            let mut proposal = std::collections::BTreeMap::new();
                            proposal.insert(
                                "axis_name".to_string(),
                                myco_kernel_shared::canonical_bytes::Value::String(
                                    crate::events::NODE_TYPE_CULTIVATION_ORPHANED_TERMINAL.to_string(),
                                ),
                            );
                            proposal.insert(
                                "reason".to_string(),
                                myco_kernel_shared::canonical_bytes::Value::String(format!(
                                    "cultivation orphaned past terminal window \
                                     (staleness {staleness_days}d >= {terminal_window_days}d); \
                                     genesis terminal_choice=self_euthanasia. Awaiting cultivator \
                                     co-attestation to execute (COV06 T6 / L1/GOVERNANCE §3.2.C)."
                                )),
                            );
                            proposal.insert(
                                "orphaned_terminal".to_string(),
                                myco_kernel_shared::canonical_bytes::Value::Bool(true),
                            );
                            if let Ok(content) = myco_kernel_shared::canonical_bytes::encode(
                                &myco_kernel_shared::canonical_bytes::Value::Map(proposal),
                            ) {
                                let nt = format!(
                                    "self_euthanasia_proposal:{}",
                                    crate::events::NODE_TYPE_CULTIVATION_ORPHANED_TERMINAL
                                );
                                let _ = emit_substrate_event(state, nt, content);
                                state.last_cultivation_terminal_emitted_at_cycle = Some(cycle);
                                let _ = save_dag_state(state);
                            }
                        }
                        "bet_retirement" => {
                            // T7: emit a bet_retired_proposal; cultivator co-attest
                            // promotes it to the bet_retired:{reason} archive seal
                            // (alive::archived; state_dir preserved, cold-readable).
                            let content = crate::events::encode_bet_retired_proposal(
                                crate::events::NODE_TYPE_CULTIVATION_ORPHANED_TERMINAL,
                                cycle,
                                now_anchor,
                            );
                            let _ = emit_substrate_event(
                                state,
                                crate::events::NODE_TYPE_BET_RETIRED_PROPOSAL.to_string(),
                                content,
                            );
                            state.last_cultivation_terminal_emitted_at_cycle = Some(cycle);
                            let _ = save_dag_state(state);
                        }
                        _ => {
                            // `indefinite_orphan` (default) — the cultivar persists
                            // in limbo; no terminal event. Acknowledged-debt per
                            // §10.3. (Cooldown not set → re-checked but no-op.)
                        }
                    }
                }
            }
        }
    }
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

    // **COV06 不弃不孤** — cultivator-mortality / succession staleness watchdog.
    //
    // The substrate has no anchor socket (AS §5.2 forbids self-clock), so the
    // "now" anchor wall-clock is operator-threaded: either `MYCO_TEST_ANCHOR_NOW_NS`
    // (tests) or — in production — driven by the operator threading periodic
    // anchor stamps (which land `cultivator_heartbeat_recorded` events). When no
    // anchor "now" is available, the watchdog is a no-op (no false-positive
    // staleness from reading the host clock).
    //
    // FSM transitions emitted here (L1/GOVERNANCE §3.2):
    //   T1 normal→legacy   — staleness > 3× cadence (default 90d) → cultivator_heartbeat_stale
    //   T4 legacy→orphaned  — legacy_window (365d) elapsed OR empty chain at legacy → cultivation_orphaned
    //   T6/T7 terminal      — orphaned_terminal_window (730d) → self_euthanasia_proposal OR bet_retired_proposal
    //                         per the declared genesis terminal_choice.
    //
    // `cultivation_orphaned` is emitted via `emit_substrate_event` (NOT the immune
    // rate-limiter) so it is un-suppressible (P07 §4 + §3.2.C). Each emission has a
    // 100-cycle cooldown (same discipline as C54/C66) to avoid per-cycle DAG spam.
    if state.handshake_complete {
        do_cultivation_staleness_tick(state);
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

    let our_substrate_id = state.substrate_id();
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
        let state_dir = std::env::temp_dir().join(format!(
            "myco-c66-unit-{}-{:x}",
            std::process::id(),
            &0u8 as *const u8 as usize as u64
        ));
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
            None,
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

    // ===================================================================
    // COV06 cultivation staleness watchdog tests.
    //
    // All env-var-dependent assertions live in ONE test so the
    // process-global `MYCO_TEST_ANCHOR_NOW_NS` / `MYCO_TEST_CULTIVATION_*`
    // overrides cannot race with parallel tests in this binary. The
    // substrate-driven e2e tests exercise the same path under per-subprocess
    // env isolation.
    // ===================================================================

    fn count_nodes(state: &ServerState, prefix: &str) -> usize {
        state
            .dag
            .iter_in_insertion_order()
            .filter(|n| n.node_type.starts_with(prefix))
            .count()
    }

    fn push_event(
        state: &mut ServerState,
        node_type: String,
        content: myco_kernel_shared::canonical_bytes::CanonicalBytes,
    ) {
        let parents = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let cycle = state.cycle_counter();
        state.dag.insert_node(parents, node_type, cycle, content).expect("insert");
    }

    const DAY_NS: i64 = 86_400_000_000_000;

    /// All COV06 watchdog scenarios in ONE test (env vars are process-global;
    /// keeping them serial within a single test prevents parallel-test races on
    /// `MYCO_TEST_ANCHOR_NOW_NS` / `MYCO_TEST_CULTIVATION_TERMINAL_CHOICE`).
    #[test]
    fn cov06_staleness_watchdog_drives_fsm_transitions() {
        use crate::cultivation::{current_cultivation_state, CultivationState};
        let cpk = [0xAAu8; 32];

        // ---- (0) No anchor now → watchdog dormant (AS §5.2) ----
        std::env::remove_var("MYCO_TEST_ANCHOR_NOW_NS");
        {
            let mut state = test_state();
            state.handshake_complete = true;
            state.latest_heartbeat = Some(crate::derived_state::DerivedLatestHeartbeat {
                cultivator_pubkey: cpk,
                anchor_timestamp_unix_ns: 0,
            });
            do_autonomous_tick(&mut state).expect("tick no-anchor");
            assert_eq!(
                count_nodes(&state, "cultivator_heartbeat_stale:"),
                0,
                "no anchor now → no staleness emission"
            );
        }

        // ---- (1) T1: normal → legacy when staleness > 90d (3× default cadence) ----
        std::env::set_var("MYCO_TEST_ANCHOR_NOW_NS", (100 * DAY_NS).to_string());
        let mut state = test_state();
        state.handshake_complete = true;
        state.latest_heartbeat = Some(crate::derived_state::DerivedLatestHeartbeat {
            cultivator_pubkey: cpk,
            anchor_timestamp_unix_ns: 0, // last heartbeat at t=0; now=100d → 100d stale
        });
        do_autonomous_tick(&mut state).expect("tick T1");
        assert_eq!(
            count_nodes(&state, "cultivator_heartbeat_stale:"),
            1,
            "T1: >90d staleness must emit cultivator_heartbeat_stale"
        );
        assert_eq!(current_cultivation_state(&state), CultivationState::Legacy);
        // Cooldown: a second tick at the same cycle must NOT re-emit.
        do_autonomous_tick(&mut state).expect("tick T1 cooldown");
        assert_eq!(
            count_nodes(&state, "cultivator_heartbeat_stale:"),
            1,
            "T1 cooldown: no re-emit within 100 cycles"
        );

        // ---- (2) T4: legacy → orphaned. EMPTY successor_chain → orphan fires
        // immediately (empty chain at legacy entry), un-suppressible. ----
        do_autonomous_tick(&mut state).expect("tick T4");
        assert_eq!(
            count_nodes(&state, "cultivation_orphaned:"),
            1,
            "T4: empty successor_chain in legacy must emit cultivation_orphaned"
        );
        assert_eq!(current_cultivation_state(&state), CultivationState::Orphaned);
        std::env::remove_var("MYCO_TEST_ANCHOR_NOW_NS");

        // ---- (3) T7: orphaned + terminal window + choice=bet_retirement ----
        std::env::set_var("MYCO_TEST_ANCHOR_NOW_NS", (800 * DAY_NS).to_string());
        std::env::set_var("MYCO_TEST_CULTIVATION_TERMINAL_CHOICE", "bet_retirement");
        let mut s3 = test_state();
        s3.handshake_complete = true;
        s3.latest_heartbeat = Some(crate::derived_state::DerivedLatestHeartbeat {
            cultivator_pubkey: cpk,
            anchor_timestamp_unix_ns: 0, // 800d stale > 730d terminal window
        });
        push_event(
            &mut s3,
            crate::events::cultivator_heartbeat_stale_node_type(&cpk),
            crate::events::encode_cultivator_heartbeat_stale(&cpk, 0, 90 * DAY_NS, 90, 30, 1),
        );
        push_event(
            &mut s3,
            crate::events::cultivation_orphaned_node_type(&cpk),
            crate::events::encode_cultivation_orphaned(&cpk, 365 * DAY_NS, "legacy_window_elapsed", 1),
        );
        do_autonomous_tick(&mut s3).expect("tick terminal");
        assert_eq!(
            count_nodes(&s3, crate::events::NODE_TYPE_BET_RETIRED_PROPOSAL),
            1,
            "T7: terminal window + bet_retirement choice emits bet_retired_proposal"
        );

        // ---- (4) T6: orphaned + terminal window + choice=self_euthanasia ----
        std::env::set_var("MYCO_TEST_CULTIVATION_TERMINAL_CHOICE", "self_euthanasia");
        let mut s4 = test_state();
        s4.handshake_complete = true;
        s4.latest_heartbeat = Some(crate::derived_state::DerivedLatestHeartbeat {
            cultivator_pubkey: cpk,
            anchor_timestamp_unix_ns: 0,
        });
        push_event(
            &mut s4,
            crate::events::cultivator_heartbeat_stale_node_type(&cpk),
            crate::events::encode_cultivator_heartbeat_stale(&cpk, 0, 90 * DAY_NS, 90, 30, 1),
        );
        push_event(
            &mut s4,
            crate::events::cultivation_orphaned_node_type(&cpk),
            crate::events::encode_cultivation_orphaned(&cpk, 365 * DAY_NS, "legacy_window_elapsed", 1),
        );
        do_autonomous_tick(&mut s4).expect("tick terminal self-eu");
        assert_eq!(
            count_nodes(
                &s4,
                "self_euthanasia_proposal:cultivation_orphaned_terminal"
            ),
            1,
            "T6: terminal window + self_euthanasia choice emits a PROPOSAL (not auto-death)"
        );

        std::env::remove_var("MYCO_TEST_ANCHOR_NOW_NS");
        std::env::remove_var("MYCO_TEST_CULTIVATION_TERMINAL_CHOICE");
    }
}
