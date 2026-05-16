//! Substrate-side server loop — handles operator-facing M5 protocol.
//!
//! ## Lifecycle
//!
//! 1. Read first frame; expect `hello` keyed by [`bootstrap_key`].
//! 2. Extract session_secret, spawn the Python kernel/tropism worker (via
//!    [`BridgeClient::spawn_and_handshake`]), respond with `hello_ack`.
//! 3. Loop: read frame keyed by session_secret → dispatch → write response.
//! 4. On `shutdown`: write `shutdown_ack`, shut the Python worker down, exit.
//! 5. On EOF: shut down the Python worker and exit cleanly.
//!
//! ## Message routing
//!
//! - `register_axis` / `perturb` / `snapshot` → forwarded to Python verbatim.
//! - `advance` → runs one [`CycleEngine`] step; gradient-advance crosses to
//!   Python; other 4 steps are Rust-native stubs at M6.
//! - `shutdown` → graceful exit + Python worker shutdown.
//! - Any other type → `error` envelope.

use std::collections::BTreeMap;
use std::io::Write;
use std::path::PathBuf;
use std::time::Duration;

use myco_kernel_bridge::client::BridgeClient;
use myco_kernel_bridge::framing::{read_frame, write_frame};
use myco_kernel_bridge::protocol::{
    bootstrap_key, decode_frame_body, empty_payload, encode_frame_body, msg_type, Message,
};
use myco_kernel_bridge::BridgeError;
use myco_kernel_continuity::cycle::{CycleConfig, CycleEngine};
use myco_kernel_schema::dag::Dag;
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};

use crate::persistence::{
    default_state_dir, ensure_state_dir, load_dag, load_nonce_log, load_pinned_operator_identity,
    Manifest, PinnedOperatorIdentity,
};
use crate::SubstrateError;

// ---------------------------------------------------------------------------
// M18 P4 永恒迭代 cycle trait adapters (DagVerifyTier1, CycleAbsorber,
// DagBreachWatcher, PinnedHandshakeReader, PythonGradientAdvancer) and the
// `advance` handler now live in `crate::ingest` (Phase B Step 4). The trait
// impls are private to that module since `dispatch` only invokes
// `crate::ingest::handle_advance`.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// M23.1 P4 永恒迭代 — autonomous tick infrastructure.
// ---------------------------------------------------------------------------

/// Frame messages shipped from the stdin reader thread to the main loop.
///
/// The reader sends `Frame(bytes)` per successful frame read. On clean EOF
/// (read_frame returns `Ok(None)`), the reader exits — dropping its `Sender`
/// — and the main loop's next `recv_timeout` returns `Disconnected`. On I/O
/// error, the reader sends `ReadError(msg)` so the main loop can surface the
/// actual cause before terminating.
#[derive(Debug)]
enum FrameMsg {
    /// A complete length-prefixed frame body (HMAC + canonical-bytes).
    Frame(Vec<u8>),
    /// A read error encountered before reaching EOF — surfaced for diagnostics.
    ReadError(String),
}

/// Default autonomous tick interval (milliseconds). At 500ms the substrate
/// ticks twice per second when idle. Configurable via `MYCO_TICK_INTERVAL_MS`.
const DEFAULT_TICK_INTERVAL_MS: u64 = 500;

/// Parse the autonomous tick interval from `MYCO_TICK_INTERVAL_MS` env var
/// (defaults to [`DEFAULT_TICK_INTERVAL_MS`]).
fn parse_tick_interval() -> Duration {
    let ms: u64 = std::env::var("MYCO_TICK_INTERVAL_MS")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(DEFAULT_TICK_INTERVAL_MS);
    Duration::from_millis(ms)
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
fn do_autonomous_tick(state: &mut ServerState) -> Result<(), SubstrateError> {
    use std::time::{SystemTime, UNIX_EPOCH};

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
        }
    }
    let _ = save_dag_state(state);
    Ok(())
}

// ---------------------------------------------------------------------------
// Server state.
// ---------------------------------------------------------------------------

/// Session state for one operator connection.
pub(crate) struct ServerState {
    /// The session_secret transported by the `hello` from the operator.
    pub(crate) session_secret: [u8; 32],
    /// Whether the operator handshake has completed.
    pub(crate) handshake_complete: bool,
    /// Python kernel/tropism worker handle (None pre-handshake).
    pub(crate) python_client: Option<BridgeClient>,
    /// CycleEngine for substrate-side metabolic-cycle execution.
    pub(crate) cycle_engine: CycleEngine,
    /// Persistent substrate identity + metabolic position (M7).
    pub(crate) manifest: Manifest,
    /// Directory in which the substrate's state files live (M7).
    pub(crate) state_dir: PathBuf,
    /// Persistent causal DAG of substrate events (sporocarps etc.) (M8).
    pub(crate) dag: Dag,
    /// Pinned operator identity public key (M9). `None` until TOFU on first hello.
    pub(crate) pinned_operator_identity: Option<PinnedOperatorIdentity>,
    /// M13: Attestation nonce log (in-process; not persisted at M13 minimum).
    /// Keyed by nonce bytes for O(1) lookup on submit.
    pub(crate) nonce_log: std::collections::HashMap<[u8; 32], crate::attestation::AttestationNonce>,
    /// M22 P5 万物互联: inter-substrate federation state (listener + peers).
    /// Always present; the listener field stays `None` until the operator
    /// invokes `federation_open_listener`.
    pub(crate) federation: crate::federation::FederationState,
    /// M25.0 + M25.4: the substrate's private Ed25519 signing seed.
    ///
    /// This NEVER goes on the wire. Used to (1) sign `snapshot.cb` so a
    /// forged snapshot can't masquerade, and (2) sign FED_HELLO payloads
    /// for federation mutual auth beyond TOFU. Reconstruct an
    /// `Ed25519PrivateKey` via `Ed25519PrivateKey::from_seed(&seed)` at
    /// each signing site (the keypair is cheap to derive on demand).
    pub(crate) substrate_signing_seed: [u8; 32],
    /// M25.2 P5 万物互联: rolling observatory snapshot history. One snapshot
    /// is appended on every `cycle_advanced` emission. Used by
    /// `handle_query_substrate_observatory` to compute signal #5 time
    /// trends, `bet_weakening_quorum`, and emergent composite weights.
    ///
    /// Capped at `OBSERVATORY_HISTORY_CAP`; oldest dropped on overflow.
    /// Round-trips through `snapshot.cb` so the trend window survives
    /// reboots when a fresh snapshot is on disk; otherwise filled
    /// organically as cycles tick.
    pub(crate) observatory_history:
        std::collections::VecDeque<crate::derived_state::ObservatorySnapshot>,
    /// M25.2: cache of the most-recent operator-attested context-window size.
    /// Set whenever a `query_substrate_observatory` request carries
    /// `operator_attested_context_window_bytes`. Used at cycle-advance time
    /// to populate `signal_6_ratio_repr` on each new ObservatorySnapshot.
    /// `None` until the operator first attests a window. The substrate
    /// cannot derive this autonomously — it is an operator-environment fact.
    pub(crate) last_operator_context_window_bytes: Option<u64>,
    /// M25.1: tracks the most recent doctrine-burst sporocarp emission to
    /// prevent burst spam on every observatory query. Stores
    /// `manifest.cycle_counter` at emission time. Cooldown: 100 cycles.
    pub(crate) last_doctrine_burst_emitted_at_cycle: Option<u64>,
    /// M25.2: same as above but for the `C40_bet_weakening_quorum`
    /// detector. Cooldown: 100 cycles.
    pub(crate) last_bet_weakening_quorum_emitted_at_cycle: Option<u64>,
}

impl ServerState {
    fn new(
        state_dir: PathBuf,
        manifest: Manifest,
        dag: Dag,
        pinned_operator_identity: Option<PinnedOperatorIdentity>,
        substrate_signing_seed: [u8; 32],
    ) -> Self {
        // M7: the manifest's cycle_counter is the authoritative persisted
        // counter; the in-process CycleEngine maintains its own counter that
        // counts cycles within THIS process only. handle_advance() uses the
        // manifest counter as the cross-process source-of-truth.
        // M8: dag carries the substrate's causal history (sporocarps + future event types).
        // M9: pinned_operator_identity is the TOFU-pinned operator pubkey;
        //     None pre-first-hello.
        // M25.0: substrate_signing_seed is the substrate-private Ed25519 seed,
        //     loaded or genesis-generated by `boot_or_genesis_substrate_signing_key`.
        ServerState {
            session_secret: [0u8; 32],
            handshake_complete: false,
            python_client: None,
            cycle_engine: CycleEngine::new(CycleConfig::default()),
            manifest,
            state_dir,
            dag,
            pinned_operator_identity,
            nonce_log: std::collections::HashMap::new(),
            // M26.1 C5 SECURITY FIX: read `MYCO_ACCEPT_LEGACY_PEERS` env var at
            // construction. Default policy (env unset) rejects legacy FED_HELLOs;
            // override is for transition-period compatibility with pre-M25 peers.
            // See `FederationState::new_with_env_policy`.
            federation: crate::federation::FederationState::new_with_env_policy(),
            substrate_signing_seed,
            observatory_history: std::collections::VecDeque::new(),
            last_operator_context_window_bytes: None,
            last_doctrine_burst_emitted_at_cycle: None,
            last_bet_weakening_quorum_emitted_at_cycle: None,
        }
    }

    /// M25.0 + M25.4: return the substrate's own Ed25519 public key (32 bytes),
    /// derived from `substrate_signing_seed`. The pubkey appears on the wire
    /// (snapshot wrapper + FED_HELLO signed payload); the private seed never does.
    ///
    /// Currently only used by tests; the runtime derives the pubkey inline
    /// at each emission site (cheap; avoids cloning the seed for borrow).
    #[allow(dead_code)]
    fn substrate_signing_pubkey(&self) -> [u8; 32] {
        use myco_kernel_shared::crypto::Ed25519PrivateKey;
        Ed25519PrivateKey::from_seed(&self.substrate_signing_seed)
            .public_key()
            .0
    }

    /// M21.4 P5 万物互联: manifest persistence is now NO-OP.
    /// Manifest fields (substrate_id / genesis_time / cycle_counter /
    /// last_absorbed_cycle) are derived from DAG events on boot. The
    /// legacy `manifest.cb` file is no longer written.
    ///
    /// Kept as a function for call-site stability.
    #[allow(clippy::unnecessary_wraps)]
    pub(crate) fn save_manifest(&mut self) -> Result<(), SubstrateError> {
        // M21.4: no-op. Manifest fields are event-sourced via DAG.
        Ok(())
    }

    /// State directory as a string (for forwarding to the Python worker).
    /// M21.4: retained for sprout_child Python-side gradient snapshot path.
    #[allow(dead_code)]
    fn state_dir_str(&self) -> String {
        self.state_dir.to_string_lossy().into_owned()
    }
}

// ---------------------------------------------------------------------------
// Public server entry point.
// ---------------------------------------------------------------------------

/// Run the substrate server loop against the given stdin/stdout.
///
/// Resolves the state directory (per `MYCO_STATE_DIR` env var or default),
/// loads the manifest if one exists (cold-resume), or generates a fresh
/// genesis manifest. The Python worker is hydrated from `gradient.cb` (if
/// present) during the hello-handshake forwarding.
///
/// Returns the exit code (0 = clean shutdown, 2 = handshake failure).
///
/// M23.1 P4 永恒迭代: the loop is now **autonomous**. A dedicated stdin reader
/// thread reads operator frames in the background and ships them to the main
/// loop via an `mpsc::Sender<FrameMsg>`. The main loop uses
/// `recv_timeout(MYCO_TICK_INTERVAL_MS)` so that — when no operator frame is
/// pending — the substrate uses the idle slice to do federation work
/// (`do_autonomous_tick`) without operator intervention. This is the moment
/// the substrate stops being purely reactive: it ticks under its own clock.
pub fn run_loop() -> Result<u8, SubstrateError> {
    use crate::derived_state::DerivedState;
    use std::sync::mpsc;

    let state_dir = default_state_dir();
    ensure_state_dir(&state_dir)?;

    // M21.2 P5 万物互联: DAG-first boot.
    //
    // 1. Load DAG (authoritative substrate event log).
    // 2. Derive substrate state via DerivedState::from_dag.
    // 3. If derived has substrate_id (genesis_event present), USE DERIVED
    //    STATE for ServerState fields. State files become regenerable caches.
    // 4. If DAG is empty or pre-M21 (no genesis_event), fall back to state
    //    file loading (legacy compat). Auto-emit genesis_event for legacy
    //    substrate to migrate forward.
    //
    // This is the moment the DAG becomes Rust-side authoritative. State files
    // are still written (M21.4 will remove them); they're no longer read.

    // M11: C7 dag_retro_edit_detected — quarantine corrupted dag.cb.
    let (dag, dag_load_failure_evidence): (Dag, Option<String>) = match load_dag(&state_dir) {
        Ok(Some(d)) => (d, None),
        Ok(None) => (Dag::default(), None),
        Err(e) => {
            let dag_path = state_dir.join("dag.cb");
            let quarantine_path = state_dir.join(format!(
                "dag.cb.quarantined_{}",
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_secs())
                    .unwrap_or(0)
            ));
            let _ = std::fs::rename(&dag_path, &quarantine_path);
            (
                Dag::default(),
                Some(format!(
                    "dag.cb load failed ({e}); quarantined to {}",
                    quarantine_path.display()
                )),
            )
        }
    };

    // M25.0: load (or genesis) the substrate's private signing seed BEFORE
    // attempting to load snapshot.cb. The seed lets us verify that the
    // on-disk snapshot was signed by THIS substrate (not a forged one) — the
    // snapshot's embedded signer_pubkey must match the pubkey derived from
    // our own seed, AND the signature must verify over the payload bytes.
    //
    // M26.1 C6 SECURITY FIX: also probe the on-disk permission posture of the
    // seed file. If it was loose (Unix mode allowed group/world access), we
    // tighten in-place immediately AND queue a C4_substrate_secret_unsealed
    // immune sporocarp to emit once `state` is constructed (DAG handle lives
    // inside ServerState, so emission happens after `new()` returns).
    let (substrate_signing_seed, signing_key_was_restrictive) =
        crate::persistence::boot_or_genesis_substrate_signing_key_with_permission_status(
            &state_dir,
        )?;
    if !signing_key_was_restrictive {
        // M26.1 C6: tighten in-place so the gap doesn't widen. Best-effort —
        // a failure here is logged but does NOT abort boot (substrate remains
        // functional; the C4 sporocarp emitted below records the breach).
        let _ = crate::persistence::tighten_substrate_signing_key_permissions(&state_dir);
    }
    let substrate_signing_pubkey = {
        use myco_kernel_shared::crypto::Ed25519PrivateKey;
        Ed25519PrivateKey::from_seed(&substrate_signing_seed)
            .public_key()
            .0
    };

    // M21.5 P5 万物互联 + M25.0: try to load snapshot.cb first. If present +
    // (signature verifies against our own pubkey) + (snapshot's recorded tip
    // is in the DAG) → use it as the starting state + replay only events
    // newer than that tip. This avoids full DAG replay on large substrates.
    //
    // Fallback (snapshot missing / corrupted / signature invalid / signer
    // pubkey mismatch / stale tip): full DAG replay (correctness preserved;
    // snapshot is purely an optimization). M25.0 specifically defends against
    // cross-substrate forgery: copying substrate A's snapshot.cb into
    // substrate B's state_dir fails the signer-pubkey check at B's boot.
    let mut snapshot_rejection_evidence: Option<String> = None;
    let derived = {
        let loaded = crate::persistence::load_snapshot(&state_dir).ok().flatten();
        let from_snapshot = match loaded {
            Some(snap) => {
                // M25.0 step 1: signer pubkey must match our own — otherwise
                // some other substrate wrote this snapshot (or it was forged).
                if snap.signer_pubkey != substrate_signing_pubkey {
                    snapshot_rejection_evidence = Some(format!(
                        "snapshot.cb signer_pubkey {} != substrate signing pubkey {} \
                         (snapshot was signed by a different substrate; rejected)",
                        hex_first_8_bytes(&snap.signer_pubkey),
                        hex_first_8_bytes(&substrate_signing_pubkey),
                    ));
                    None
                } else if let Err(e) = myco_kernel_shared::crypto::verify_signature(
                    &snap.signer_pubkey,
                    &snap.signature,
                    &snap.payload,
                ) {
                    // M25.0 step 2: signature must verify over the payload.
                    snapshot_rejection_evidence = Some(format!(
                        "snapshot.cb signature failed verification: {e} (rejected)"
                    ));
                    None
                } else {
                    // Signature OK — decode payload and proceed with M21.5
                    // tip-in-DAG check.
                    match DerivedState::from_canonical_bytes(&snap.payload) {
                        Ok(Some((mut state_from_snap, snap_tip))) => {
                            let snap_tip_in_dag = match snap_tip {
                                None => dag.node_count() == 0,
                                Some(tip_arr) => {
                                    let nh = myco_kernel_shared::crypto::NodeHash::from_bytes(
                                        tip_arr,
                                    );
                                    dag.get(&nh).is_some()
                                }
                            };
                            if snap_tip_in_dag {
                                let replay_result = replay_events_after_tip(
                                    &mut state_from_snap,
                                    &dag,
                                    snap_tip.as_ref(),
                                );
                                match replay_result {
                                    Ok(()) => Some(state_from_snap),
                                    Err(_) => None,
                                }
                            } else {
                                None
                            }
                        }
                        _ => None,
                    }
                }
            }
            None => None,
        };
        from_snapshot.unwrap_or_else(|| {
            DerivedState::from_dag(&dag).unwrap_or_else(|_| DerivedState::empty())
        })
    };

    // Determine boot mode:
    //  - "dag-first" (M21.2+): derived.is_post_m21_substrate() == true
    //  - "legacy" (pre-M21.1): fall back to state file loading
    //  - "fresh genesis" (no prior state at all): create new
    let boot_from_dag = derived.is_post_m21_substrate();
    let (manifest, pinned_operator_identity, nonce_log_entries, is_fresh_genesis): (
        Manifest,
        Option<crate::persistence::PinnedOperatorIdentity>,
        Vec<crate::persistence::PersistedNonceEntry>,
        bool,
    ) = if boot_from_dag {
        // M21.2 derived-first path: state comes from DAG events.
        let mfst = derived.to_legacy_manifest();
        let pinned = derived.pinned_operator_identity.clone();
        // Convert DerivedNonce → PersistedNonceEntry for ServerState population.
        let nonces: Vec<crate::persistence::PersistedNonceEntry> = derived
            .nonce_log
            .values()
            .map(|n| crate::persistence::PersistedNonceEntry {
                nonce: n.nonce,
                bound_content_hash: n.bound_content_hash,
                bound_dag_tip: n.bound_dag_tip,
                substrate_issued_at_unix_ns: n.substrate_issued_at_unix_ns,
                expiry_unix_ns: n.expiry_unix_ns,
                anchor_clock_issued_at_unix_ns: n.anchor_clock_issued_at_unix_ns,
                anchor_clock_expiry_unix_ns: n.anchor_clock_expiry_unix_ns,
                consumed: n.consumed,
            })
            .collect();
        (mfst, pinned, nonces, false)
    } else {
        // Legacy path: load from state files.
        let (m, fresh) = match Manifest::load(&state_dir)? {
            Some(m) => (m, false),
            None => (Manifest::genesis(), true),
        };
        let pinned = load_pinned_operator_identity(&state_dir)?;
        let now_for_prune = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .ok()
            .and_then(|d| i64::try_from(d.as_nanos()).ok())
            .unwrap_or(0);
        let entries = match load_nonce_log(&state_dir) {
            Ok(Some(entries)) => entries
                .into_iter()
                .filter(|e| !(e.consumed && now_for_prune > e.expiry_unix_ns))
                .collect::<Vec<_>>(),
            _ => Vec::new(),
        };
        (m, pinned, entries, fresh)
    };

    let mut state = ServerState::new(
        state_dir,
        manifest,
        dag,
        pinned_operator_identity,
        substrate_signing_seed,
    );
    // M25.2: restore observatory history from snapshot.cb if the boot path
    // hydrated it onto `derived`. Fresh substrates / DAG-replay-only boots
    // start with an empty deque; the history then fills organically as
    // cycles tick. Cap is enforced on insert; we copy as-is here.
    state.observatory_history = derived.observatory_history.clone();
    for entry in nonce_log_entries {
        state.nonce_log.insert(
            entry.nonce,
            crate::attestation::AttestationNonce {
                nonce: entry.nonce,
                bound_content_hash: entry.bound_content_hash,
                bound_dag_tip: entry.bound_dag_tip,
                substrate_issued_at_unix_ns: entry.substrate_issued_at_unix_ns,
                expiry_unix_ns: entry.expiry_unix_ns,
                anchor_clock_issued_at_unix_ns: entry.anchor_clock_issued_at_unix_ns,
                anchor_clock_expiry_unix_ns: entry.anchor_clock_expiry_unix_ns,
                consumed: entry.consumed,
            },
        );
    }

    // M25.0: if snapshot.cb was rejected for signature mismatch or invalid
    // signature, surface as a C38 immune sporocarp so the operator can
    // investigate. The substrate continues running (snapshot is a cache;
    // DAG replay rebuilt state from authoritative source).
    if let Some(evidence) = snapshot_rejection_evidence {
        let _ = emit_immune_sporocarp(
            &mut state,
            "C38_snapshot_integrity_violation",
            "snapshot_integrity_violation",
            &evidence,
        );
        let _ = save_dag_state(&state);
    }

    // M26.1 C6 SECURITY FIX (Phase γ.2): substrate_signing_key.cb existed on
    // disk with loose Unix permissions (group/world bits set) — emit a
    // `C4_substrate_secret_unsealed` immune sporocarp on the DAG so the
    // breach is observable. We already tightened the file in-place above;
    // the sporocarp is the audit-trail record. This path is a no-op on the
    // genesis branch (fresh seed; file was written with 0600 from the start)
    // and on Windows (ACL inspection deferred to M-anchor-1).
    if !signing_key_was_restrictive {
        let evidence = format!(
            "substrate_signing_key.cb at {} had loose permissions on boot \
             (group/world bits set); tightened to 0600 in-place. M-anchor-1 \
             will replace file-permission defense with OS-sealed keystore.",
            state.state_dir.display()
        );
        let _ = emit_immune_sporocarp(
            &mut state,
            "C4_substrate_secret_unsealed",
            "substrate_secret_unsealed",
            &evidence,
        );
        let _ = save_dag_state(&state);
    }

    // If DAG load failed: emit C7 immune sporocarp into the fresh DAG.
    if let Some(evidence) = dag_load_failure_evidence {
        let _ = emit_immune_sporocarp(
            &mut state,
            "C7_dag_retro_edit_detected",
            "dag_retro_edit_detected",
            &evidence,
        );
        let _ = save_dag_state(&state);
    }

    // M21.2/M21.3: legacy-substrate auto-migration moved to handle_hello,
    // AFTER Python loads its gradient state. This way the migration can
    // back-fill BOTH genesis_event AND axis_registered events from Python's
    // already-loaded state, preserving M20 child substrate behavior (and
    // any other case where state files are authoritative + DAG is empty).
    let _ = is_fresh_genesis; // suppress unused-var warning when migration moved

    // M21.1 P5 万物互联: fresh substrate (no manifest.cb on disk) emits
    // genesis_event as the first DAG node. M21.2 generalizes this: any
    // substrate without a genesis_event in DAG gets one auto-emitted (the
    // legacy_migration branch above handles existing manifest.cb; this branch
    // handles truly fresh).
    if is_fresh_genesis && state.dag.node_count() == 0 {
        let event_node_type = crate::events::genesis_event_node_type(&state.manifest.substrate_id);
        let event_content = crate::events::encode_genesis_event(
            &state.manifest.substrate_id,
            state.manifest.genesis_time_unix_ns,
        );
        let _ = emit_substrate_event(&mut state, event_node_type, event_content);
        let _ = save_dag_state(&state);
    }

    // M12: C9 cold_resume_invariant_failure — run comprehensive integrity
    // checks at boot. For each failing check, emit a C9 immune sporocarp.
    // The substrate continues running regardless; the immune events are an
    // audit trail for the operator to inspect.
    let integrity_results = crate::integrity::run_integrity_checks(&state);
    let mut any_failed = false;
    for result in &integrity_results {
        if !result.passed {
            any_failed = true;
            let evidence = format!(
                "boot-time integrity check failed: {} — {}",
                result.check_id, result.evidence
            );
            // M19 P9 皮肤: route check_id "canonical_bytes_render_drift" to
            // its dedicated C18 detector; all others go to C9.
            let (detector_id, detector_name) = if result.check_id == "canonical_bytes_render_drift"
            {
                (
                    "C18_canonical_bytes_render_drift",
                    "canonical_bytes_render_drift".to_string(),
                )
            } else if result.check_id == "substrate_state_orphan_detected" {
                (
                    "C32_substrate_state_orphan_detected",
                    "substrate_state_orphan_detected".to_string(),
                )
            } else {
                (
                    "C9_cold_resume_invariant_failure",
                    format!("cold_resume_invariant_failure ({})", result.check_id),
                )
            };
            let _ = emit_immune_sporocarp(&mut state, detector_id, &detector_name, &evidence);
        }
    }
    if any_failed {
        let _ = save_dag_state(&state);
    }

    // M23.1: spawn stdin reader thread. The reader thread blocks on
    // `read_frame(stdin)` and ships frames to the main loop via mpsc. The
    // main loop uses `recv_timeout(tick_interval)` so that idle periods
    // become autonomous-tick opportunities.
    let (frame_tx, frame_rx) = mpsc::channel::<FrameMsg>();
    let _reader_thread = std::thread::spawn(move || {
        let stdin = std::io::stdin();
        let mut stdin_lock = stdin.lock();
        loop {
            match read_frame(&mut stdin_lock) {
                Ok(Some(frame)) => {
                    if frame_tx.send(FrameMsg::Frame(frame)).is_err() {
                        return; // main loop dropped receiver
                    }
                }
                Ok(None) => {
                    // Clean EOF — drop tx; main loop sees Disconnected.
                    return;
                }
                Err(e) => {
                    let _ = frame_tx.send(FrameMsg::ReadError(format!("{e}")));
                    return;
                }
            }
        }
    });

    // Lock stdout for the main loop's writes.
    let stdout_handle = std::io::stdout();
    let mut stdout_guard = stdout_handle.lock();
    let stdout = &mut stdout_guard;

    // M23.1: parse tick interval from env (default 500ms = 2 ticks/sec).
    let tick_interval = parse_tick_interval();

    loop {
        let expected_key = if state.handshake_complete {
            state.session_secret
        } else {
            bootstrap_key()
        };

        // M23.1: receive next frame OR fire autonomous tick on timeout.
        let frame = match frame_rx.recv_timeout(tick_interval) {
            Ok(FrameMsg::Frame(f)) => f,
            Ok(FrameMsg::ReadError(msg)) => {
                graceful_shutdown_python(&mut state);
                return Err(SubstrateError::Io(std::io::Error::other(format!(
                    "stdin reader thread error: {msg}"
                ))));
            }
            Err(mpsc::RecvTimeoutError::Timeout) => {
                // Autonomous tick — do federation work iff handshake done +
                // listener open. Other ticks are no-ops (preserves the
                // pre-handshake / no-federation idle behavior of M22 and
                // earlier).
                if state.handshake_complete {
                    if let Err(e) = do_autonomous_tick(&mut state) {
                        // Non-fatal: log + continue (tick failures should
                        // never crash the substrate; they surface via DAG
                        // events emitted by the tick).
                        let _ = writeln!(std::io::stderr(), "autonomous tick error: {e}");
                    }
                }
                continue;
            }
            Err(mpsc::RecvTimeoutError::Disconnected) => {
                // stdin reader thread exited (clean EOF or error after
                // reporting). Treat as clean shutdown.
                graceful_shutdown_python(&mut state);
                return Ok(if state.handshake_complete { 0 } else { 2 });
            }
        };

        let request = match decode_frame_body(&frame, &expected_key) {
            Ok(msg) => msg,
            Err(BridgeError::HmacMismatch(msg)) => {
                // If pre-handshake, exit. If post, write error.
                if state.handshake_complete {
                    write_error_response(stdout, &state.session_secret, 0, "hmac_mismatch", &msg)?;
                    continue;
                }
                graceful_shutdown_python(&mut state);
                return Ok(2);
            }
            Err(e) => {
                if state.handshake_complete {
                    write_error_response(
                        stdout,
                        &state.session_secret,
                        0,
                        "protocol_error",
                        &e.to_string(),
                    )?;
                    continue;
                }
                graceful_shutdown_python(&mut state);
                return Ok(2);
            }
        };

        // Dispatch.
        let result = dispatch(&mut state, &request);
        match result {
            Ok(Some(response)) => {
                let frame = encode_frame_body(&response, &state.session_secret)
                    .map_err(SubstrateError::Bridge)?;
                write_frame(stdout, &frame).map_err(SubstrateError::Bridge)?;
                if request.message_type == msg_type::SHUTDOWN {
                    graceful_shutdown_python(&mut state);
                    return Ok(0);
                }
                // M23.2 P7 必朽: after a successful accept_self_euthanasia_proposal
                // we MUST shut down — the substrate has been authorized to die.
                // The response was just delivered (so the operator sees success).
                if request.message_type == msg_type::ACCEPT_SELF_EUTHANASIA_PROPOSAL {
                    graceful_shutdown_python(&mut state);
                    return Ok(0);
                }
            }
            Ok(None) => {
                // Handshake-only path: state was mutated but no response queued (currently unused).
            }
            Err(e) => {
                // M9: when a HELLO request fails (e.g., pubkey mismatch),
                // key the error envelope with the operator-provided
                // session_secret from the hello payload so the TS operator
                // can decode our rejection. Then EXIT — a rejected hello
                // means the session is poisoned; no point continuing.
                if request.message_type == msg_type::HELLO {
                    // M11: emit immune sporocarp for the rejected hello (C2 family).
                    // The DAG is loaded at boot time and will accept this insertion
                    // even pre-handshake. Save DAG before exit so the next session
                    // can see the immune event.
                    let evidence = format!("hello rejected: {e}");
                    let _ = emit_immune_sporocarp(
                        &mut state,
                        "C30_handshake_pubkey_mismatch",
                        "handshake_pubkey_mismatch",
                        &evidence,
                    );
                    let _ = save_dag_state(&state);

                    let response_key = match request.payload.get("session_secret") {
                        Some(Value::Bytes(b)) if b.len() == 32 => {
                            let mut arr = [0u8; 32];
                            arr.copy_from_slice(b);
                            arr
                        }
                        _ => bootstrap_key(),
                    };
                    // Best-effort write of the error envelope (operator can decode).
                    let _ = write_error_response(
                        stdout,
                        &response_key,
                        request.request_id,
                        "hello_rejected",
                        &e.to_string(),
                    );
                    graceful_shutdown_python(&mut state);
                    return Ok(2);
                }
                let response_key = if state.handshake_complete {
                    state.session_secret
                } else {
                    bootstrap_key()
                };
                write_error_response(
                    stdout,
                    &response_key,
                    request.request_id,
                    "dispatcher_error",
                    &e.to_string(),
                )?;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Dispatch.
// ---------------------------------------------------------------------------

fn dispatch(state: &mut ServerState, request: &Message) -> Result<Option<Message>, SubstrateError> {
    // Pre-handshake: only HELLO is allowed.
    if !state.handshake_complete && request.message_type != msg_type::HELLO {
        return Err(SubstrateError::Handshake(format!(
            "received {} before hello",
            request.message_type
        )));
    }

    match request.message_type.as_str() {
        msg_type::HELLO => crate::handshake::handle_hello(state, request),
        msg_type::REGISTER_AXIS => {
            // M22.5: block register_axis during birth-period quarantine.
            // Inherited disease + structural mutation == bad combination.
            if crate::lifecycle::is_in_birth_period_quarantine(state) {
                return crate::lifecycle::quarantine_block(state, "register_axis");
            }
            let response = forward_to_python(state, request, msg_type::REGISTER_AXIS_ACK)?;
            // M21.1 P5 万物互联: emit axis_registered DAG event so the schema
            // addition is recorded in the causal graph (was an orphan prior).
            // The wire payload fields for register_axis are documented in
            // kernel/bridge::protocol::register_axis_payload — we extract them
            // here for the event content.
            if let Some(event) = crate::ingest::build_axis_registered_event(request) {
                let nt = crate::events::axis_registered_node_type(&event.name);
                let content = crate::events::encode_axis_registered(&event);
                let _ = emit_substrate_event(state, nt, content);
                let _ = save_dag_state(state);
            }
            // M7: persist gradient state after a mutation.
            save_python_state(state)?;
            Ok(response)
        }
        msg_type::PERTURB => {
            // M22.5: block perturb during birth-period quarantine.
            if crate::lifecycle::is_in_birth_period_quarantine(state) {
                return crate::lifecycle::quarantine_block(state, "perturb");
            }
            let response = forward_to_python(state, request, msg_type::PERTURB_ACK)?;
            // M21.1 P5 万物互联: emit axis_perturbed DAG event so the
            // perturbation is recorded in the causal graph. Plain perturb
            // (no raw_material binding) was an orphan prior to M21.1.
            if let (Some(axis_name), Some(delta)) = (
                request.payload.get("axis_name").and_then(|v| match v {
                    Value::String(s) => Some(s.clone()),
                    _ => None,
                }),
                request.payload.get("delta_repr").and_then(|v| match v {
                    Value::String(s) => s.parse::<f64>().ok(),
                    _ => None,
                }),
            ) {
                let nt = crate::events::axis_perturbed_node_type(&axis_name);
                let content = crate::events::encode_axis_perturbed(&axis_name, delta);
                let _ = emit_substrate_event(state, nt, content);
                let _ = save_dag_state(state);
            }
            save_python_state(state)?;
            Ok(response)
        }
        msg_type::SNAPSHOT => forward_to_python(state, request, msg_type::SNAPSHOT_RESPONSE),
        msg_type::ADVANCE => {
            let response = crate::ingest::handle_advance(state, request)?;
            // M7: bump the persisted cycle counter (matches the value echoed in
            // the advance_response payload). save_manifest() also bumps
            // last_save_time for observability.
            let prior_cycle = state.manifest.cycle_counter;
            let new_cycle = prior_cycle.saturating_add(1);
            state.manifest.cycle_counter = new_cycle;
            // M21.1 P5 万物互联: emit cycle_advanced DAG event so cycle counter
            // progression is recorded in the causal graph.
            let event_content = crate::events::encode_cycle_advanced(prior_cycle, new_cycle);
            let _ = emit_substrate_event(
                state,
                crate::events::NODE_TYPE_CYCLE_ADVANCED.to_string(),
                event_content,
            );
            // M25.2 P5 万物互联: append a fresh observatory snapshot to the
            // trend window. Must happen AFTER the cycle_advanced DAG event
            // is appended (so dag_node_count reflects the new state) and
            // BEFORE save_dag_state (so the snapshot is built against the
            // same state that gets persisted). The signal #5 / quorum /
            // emergent-weights logic in `handle_query_substrate_observatory`
            // walks this history.
            crate::observatory::append_observatory_snapshot_to_state(state);
            state.save_manifest()?;
            save_python_state(state)?;
            // M8: persist the DAG (sporocarps inserted during handle_advance).
            save_dag_state(state)?;
            // M21.5 P5 万物互联: opportunistic snapshot. Every K cycles, save
            // a snapshot.cb to accelerate next boot. K=10 for fast feedback in
            // tests; production may tune. If snapshot save fails, log + continue
            // (snapshot is a CACHE — substrate works without it).
            const SNAPSHOT_EVERY_K_CYCLES: u64 = 10;
            if new_cycle % SNAPSHOT_EVERY_K_CYCLES == 0 {
                let _ = save_snapshot_for_state(state);
            }
            Ok(response)
        }
        msg_type::SHUTDOWN => {
            // M7+M8: final state save before exit (best-effort; ignore errors here).
            let _ = save_python_state(state);
            let _ = state.save_manifest();
            let _ = save_dag_state(state);
            Ok(Some(Message::new(
                msg_type::SHUTDOWN_ACK,
                request.request_id,
                empty_payload(),
            )))
        }
        // M8: DAG-related operator requests handled substrate-side.
        msg_type::QUERY_RECENT_NODES => crate::dag_query::handle_query_recent_nodes(state, request),
        msg_type::COMPUTE_INTENT => crate::dag_query::handle_compute_intent(state, request),
        // M10: classified-mutation submission.
        msg_type::SUBMIT_MUTATION => {
            let response = crate::attestation::handle_submit_mutation(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // M11: immune event query (filters DAG by "immune:" prefix).
        msg_type::QUERY_IMMUNE_EVENTS => crate::dag_query::handle_query_immune_events(state, request),
        // M12: ad-hoc immune check (operator can verify integrity any time).
        msg_type::RUN_IMMUNE_CHECK => crate::integrity::handle_run_immune_check(state, request),
        // M13: anchor-surface attestation nonce (operator pre-submit step).
        msg_type::REQUEST_ATTESTATION_NONCE => {
            crate::attestation::handle_request_attestation_nonce(state, request)
        }
        // M15: DAG enumeration closure for owner-side Merkle chain reconstruction.
        msg_type::ENUMERATE_DAG_SINCE => crate::dag_query::handle_enumerate_dag_since(state, request),
        // M16: P2 永恒吞噬 — universal raw_material ingestion + causal perturbation.
        msg_type::INGEST_RAW_MATERIAL => {
            let response = crate::ingest::handle_ingest_raw_material(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::PERTURB_AXIS_FROM_RAW_MATERIAL => {
            let response = crate::ingest::handle_perturb_axis_from_raw_material(state, request)?;
            save_python_state(state)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // M20 P8 永恒繁衍 — sprout a child substrate from parent's spore-schema.
        msg_type::SPROUT_CHILD => {
            let response = crate::reproduction::handle_sprout_child(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // M22 P5 万物互联 — inter-substrate federation. Operator-driven; all
        // federation handlers mutate state.federation + emit DAG events through
        // emit_substrate_event. Listener/peer sockets are nonblocking; the
        // substrate's main loop does no I/O multiplexing of its own.
        msg_type::FEDERATION_OPEN_LISTENER => {
            let response = crate::federation::handle_federation_open_listener(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_CLOSE_LISTENER => {
            let response = crate::federation::handle_federation_close_listener(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_STATUS => {
            crate::federation::handle_federation_status(state, request)
        }
        msg_type::FEDERATION_CONNECT_PEER => {
            let response = crate::federation::handle_federation_connect_peer(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_POLL => {
            let response = crate::federation::handle_federation_poll(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_PULL_EVENTS_FROM_PEER => {
            let response =
                crate::federation::handle_federation_pull_events_from_peer(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_LINK_TO_PARENT_FROM_HINT => {
            let response =
                crate::federation::handle_federation_link_to_parent_from_hint(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::LIFT_BIRTH_PERIOD_QUARANTINE => {
            let response = crate::lifecycle::handle_lift_birth_period_quarantine(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::ACCEPT_SELF_EUTHANASIA_PROPOSAL => {
            let response = crate::lifecycle::handle_accept_self_euthanasia_proposal(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::QUERY_SUBSTRATE_OBSERVATORY => {
            crate::observatory::handle_query_substrate_observatory(state, request)
        }
        other => Err(SubstrateError::Protocol(format!(
            "substrate cannot handle message type {other:?}"
        ))),
    }
}


pub(crate) fn hex_encode(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        s.push_str(&format!("{b:02x}"));
    }
    s
}

// ---------------------------------------------------------------------------
// Persistence helpers moved to `crate::persistence_runtime` (Phase B Step 5).
// Re-exported here so existing call sites continue to compile unchanged.
// ---------------------------------------------------------------------------
pub(crate) use crate::persistence_runtime::{
    backfill_dag_from_python_state, replay_events_after_tip, replay_python_events_from_dag,
    save_dag_state, save_nonce_state, save_python_state, save_snapshot_for_state,
};

pub(crate) fn hex_first_8_bytes(bytes: &[u8; 32]) -> String {
    bytes[..8].iter().map(|b| format!("{b:02x}")).collect()
}

/// M11: Emit an immune sporocarp as a DAG node.
///
/// Wraps a detected breach event as a DAG node with `node_type = "immune:{detector_id}"`.
/// The node's content is canonical-bytes of a Map carrying the detector ID,
/// evidence, and a wall-clock timestamp.
///
/// Returns the DAG node hash (32 bytes). On failure to encode or insert,
/// returns Err — but callers typically log + continue rather than escalating,
/// because immune emission failures should not mask the original breach.
pub(crate) fn emit_immune_sporocarp(
    state: &mut ServerState,
    detector_id: &str,
    detector_name: &str,
    evidence: &str,
) -> Result<myco_kernel_shared::crypto::NodeHash, SubstrateError> {
    use std::time::{SystemTime, UNIX_EPOCH};
    let timestamp_unix_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);

    let mut content_map = BTreeMap::new();
    content_map.insert(
        "detector_id".to_string(),
        Value::String(detector_id.to_string()),
    );
    content_map.insert(
        "detector_name".to_string(),
        Value::String(detector_name.to_string()),
    );
    content_map.insert("evidence".to_string(), Value::String(evidence.to_string()));
    content_map.insert(
        "timestamp_unix_ns".to_string(),
        Value::Timestamp(timestamp_unix_ns),
    );
    let content_canonical = cb_encode(&Value::Map(content_map))
        .map_err(|e| SubstrateError::Protocol(format!("immune encode: {e}")))?;

    let parents = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let node_type = format!("immune:{detector_id}");
    let cycle = state.manifest.cycle_counter;
    state
        .dag
        .insert_node(parents, node_type, cycle, content_canonical)
        .map_err(|e| SubstrateError::Protocol(format!("immune DAG insert: {e}")))
}


/// M21.1 P5 万物互联: emit a generic substrate event as a DAG node. This is
/// the unified helper used by all state-mutation handlers to record their
/// state changes in the DAG event log, closing P5 by ensuring no state
/// mutation is an orphan from the causal graph.
///
/// The node is parented by the current DAG tip (linear chain at M21.1; M21.2+
/// may add multi-parent for events with logical predecessors). Returns the
/// inserted node hash for callers who need it.
pub(crate) fn emit_substrate_event(
    state: &mut ServerState,
    node_type: String,
    content: myco_kernel_shared::canonical_bytes::CanonicalBytes,
) -> Result<myco_kernel_shared::crypto::NodeHash, SubstrateError> {
    let parents = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let cycle = state.manifest.cycle_counter;
    state
        .dag
        .insert_node(parents, node_type, cycle, content)
        .map_err(|e| SubstrateError::Protocol(format!("substrate event DAG insert: {e}")))
}

/// Forward a request to the Python worker verbatim and surface its response.
fn forward_to_python(
    state: &mut ServerState,
    request: &Message,
    expected_response_type: &str,
) -> Result<Option<Message>, SubstrateError> {
    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;
    // Re-encode and send through the BridgeClient's low-level frame API. We
    // can't reuse BridgeClient::register_axis() etc because those allocate
    // their own request_id; we want to preserve the operator's request_id
    // for correlation in the response we send BACK to the operator.
    //
    // M6 minimum: re-issue via BridgeClient methods (which allocate fresh
    // IDs), then re-stamp the response with the operator's request_id.
    let response = forward_message(client, request)?;
    if response.message_type != expected_response_type {
        return Err(SubstrateError::Protocol(format!(
            "expected {expected_response_type} from python; got {}",
            response.message_type
        )));
    }
    // Re-stamp with operator's request_id.
    Ok(Some(Message::new(
        &response.message_type,
        request.request_id,
        response.payload,
    )))
}

/// Low-level forwarder: takes a Message, asks the BridgeClient to send a
/// fresh-id copy, returns the response. Bypasses BridgeClient's typed
/// helpers because we want the raw payload pass-through.
fn forward_message(client: &mut BridgeClient, request: &Message) -> Result<Message, BridgeError> {
    match request.message_type.as_str() {
        msg_type::REGISTER_AXIS => {
            // Extract typed args from payload and call register_axis.
            let name = expect_string_field(&request.payload, "name")?;
            let axis_class = expect_string_field(&request.payload, "axis_class")?;
            let fruiting_threshold =
                parse_float_field(&request.payload, "fruiting_threshold_repr")?;
            let initial_value = parse_float_field(&request.payload, "initial_value_repr")?;
            let decay_rate = parse_float_field(&request.payload, "decay_rate_per_cycle_repr")?;
            let is_mortality_signal = expect_bool_field(&request.payload, "is_mortality_signal")?;
            let update_rule_kind = expect_string_field(&request.payload, "update_rule_kind")?;
            client.register_axis(
                &name,
                &axis_class,
                fruiting_threshold,
                initial_value,
                decay_rate,
                is_mortality_signal,
                &update_rule_kind,
            )?;
            Ok(Message::new(
                msg_type::REGISTER_AXIS_ACK,
                0, // operator-side will be re-stamped
                empty_payload(),
            ))
        }
        msg_type::PERTURB => {
            let axis_name = expect_string_field(&request.payload, "axis_name")?;
            let delta = parse_float_field(&request.payload, "delta_repr")?;
            client.perturb(&axis_name, delta)?;
            Ok(Message::new(msg_type::PERTURB_ACK, 0, empty_payload()))
        }
        msg_type::SNAPSHOT => {
            let values = client.snapshot()?;
            let mut values_map: BTreeMap<String, Value> = BTreeMap::new();
            for (k, v) in values {
                values_map.insert(k, Value::String(float_repr(v)));
            }
            let mut payload = BTreeMap::new();
            payload.insert("values".to_string(), Value::Map(values_map));
            Ok(Message::new(msg_type::SNAPSHOT_RESPONSE, 0, payload))
        }
        other => Err(BridgeError::Protocol(format!(
            "forward_message: cannot forward {other}"
        ))),
    }
}

// ---------------------------------------------------------------------------
// Helpers.
// ---------------------------------------------------------------------------

fn write_error_response<W: Write>(
    stdout: &mut W,
    key: &[u8; 32],
    in_response_to: u64,
    code: &str,
    msg: &str,
) -> Result<(), SubstrateError> {
    let mut payload = BTreeMap::new();
    payload.insert("code".to_string(), Value::String(code.to_string()));
    payload.insert("message".to_string(), Value::String(msg.to_string()));
    payload.insert("in_response_to".to_string(), Value::Uint(in_response_to));
    let err_msg = Message::new(msg_type::ERROR, in_response_to, payload);
    let frame = encode_frame_body(&err_msg, key).map_err(SubstrateError::Bridge)?;
    write_frame(stdout, &frame).map_err(SubstrateError::Bridge)?;
    Ok(())
}

fn graceful_shutdown_python(state: &mut ServerState) {
    if let Some(client) = state.python_client.take() {
        let _ = client.shutdown();
    }
}

fn expect_string_field(map: &BTreeMap<String, Value>, key: &str) -> Result<String, BridgeError> {
    match map.get(key) {
        Some(Value::String(s)) => Ok(s.clone()),
        Some(other) => Err(BridgeError::Protocol(format!(
            "field {key:?} is not a String: {other:?}"
        ))),
        None => Err(BridgeError::Protocol(format!("missing field {key:?}"))),
    }
}

fn expect_bool_field(map: &BTreeMap<String, Value>, key: &str) -> Result<bool, BridgeError> {
    match map.get(key) {
        Some(Value::Bool(b)) => Ok(*b),
        Some(other) => Err(BridgeError::Protocol(format!(
            "field {key:?} is not a Bool: {other:?}"
        ))),
        None => Err(BridgeError::Protocol(format!("missing field {key:?}"))),
    }
}

fn parse_float_field(map: &BTreeMap<String, Value>, key: &str) -> Result<f64, BridgeError> {
    let s = expect_string_field(map, key)?;
    s.parse::<f64>()
        .map_err(|e| BridgeError::Protocol(format!("field {key:?} parse: {e}")))
}

/// Render an f64 as a Python-compatible repr string.
/// Identical to kernel/bridge::protocol::float_repr but reproduced here so
/// we don't need to expose that internal helper.
pub(crate) fn float_repr(f: f64) -> String {
    if f.is_nan() {
        "nan".to_string()
    } else if f.is_infinite() {
        if f > 0.0 {
            "inf".to_string()
        } else {
            "-inf".to_string()
        }
    } else if f == f.trunc() && f.abs() < 1e16 {
        format!("{f:.1}")
    } else {
        format!("{f}")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn float_repr_pinned_values() {
        assert_eq!(float_repr(0.0), "0.0");
        assert_eq!(float_repr(1.5), "1.5");
        assert_eq!(float_repr(-2.0), "-2.0");
    }

    #[test]
    fn float_repr_special() {
        assert_eq!(float_repr(f64::NAN), "nan");
        assert_eq!(float_repr(f64::INFINITY), "inf");
        assert_eq!(float_repr(f64::NEG_INFINITY), "-inf");
    }

    #[test]
    fn expect_string_field_success() {
        let mut m = BTreeMap::new();
        m.insert("name".to_string(), Value::String("test".to_string()));
        assert_eq!(expect_string_field(&m, "name").unwrap(), "test");
    }

    #[test]
    fn expect_string_field_missing_errors() {
        let m: BTreeMap<String, Value> = BTreeMap::new();
        assert!(expect_string_field(&m, "missing").is_err());
    }

    #[test]
    fn expect_string_field_wrong_type_errors() {
        let mut m = BTreeMap::new();
        m.insert("n".to_string(), Value::Uint(42));
        assert!(expect_string_field(&m, "n").is_err());
    }

    #[test]
    fn parse_float_field_roundtrip() {
        let mut m = BTreeMap::new();
        m.insert("x".to_string(), Value::String("2.5".to_string()));
        assert_eq!(parse_float_field(&m, "x").unwrap(), 2.5);
    }

    #[test]
    fn parse_float_field_invalid_string_errors() {
        let mut m = BTreeMap::new();
        m.insert("x".to_string(), Value::String("not_a_number".to_string()));
        assert!(parse_float_field(&m, "x").is_err());
    }
}
