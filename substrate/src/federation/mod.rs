//! M22 P5 万物互联 — Inter-substrate federation.
//!
//! Federation is the **inter-substrate** half of P5 万物互联. M21 finished
//! intra-substrate connectivity (every state mutation emits a DAG event;
//! `dag.cb` is the substrate's sole authoritative artifact). M22 begins the
//! inter-substrate half: two or more substrate processes connecting over TCP
//! and exchanging DAG event subsets.
//!
//! ## Architecture
//!
//! Federation is **operator-driven** at M22 — there is NO background thread.
//! All federation activity happens synchronously inside the substrate's
//! main run loop, triggered by new bridge messages (`federation_open_listener`,
//! `federation_close_listener`, `federation_status`, `federation_connect_peer`
//! [M22.2], `federation_pull_events_from_peer` [M22.3], `federation_poll`).
//!
//! Listener and peer sockets are `set_nonblocking(true)`; the substrate's
//! `federation_poll` handler does best-effort nonblocking accept + nonblocking
//! frame drain, so federation operates "near real-time" without sacrificing
//! the synchronous main-loop discipline that M5-M21 was built on. M23 will
//! add an autonomous tick that calls `federation_poll` automatically.
//!
//! ## Wire format
//!
//! Federation messages reuse `kernel/bridge/framing.rs`'s length-prefixed
//! frame envelope verbatim (u32-BE length + 32-byte HMAC + canonical-bytes
//! body). The body's canonical-bytes shape is also the same — `v`, `type`,
//! `request_id`, `payload` keys — but with `type` values drawn from
//! [`protocol::fed_msg_type`] instead of [`myco_kernel_bridge::protocol::msg_type`].
//!
//! ## Authentication
//!
//! Per-peer HMAC key is derived deterministically from both peers' substrate_ids
//! via [`protocol::derive_federation_session_key`]. No key exchange is
//! required at the wire level — each peer asserts its substrate_id in the
//! [`fed_hello`](protocol::fed_msg_type::FED_HELLO) message; both sides compute
//! the same key from the (now-known) id pair.
//!
//! TOFU pinning (M22.2): each peer pins the first substrate_id seen from a
//! given connection. Subsequent connections from that TCP origin must present
//! the same substrate_id, OR the federation rejects the second hello with a
//! `C33_federation_peer_identity_mismatch` (Phase β: renamed from C20 to free that L1 spec number; substrate-private C30+ namespace) immune sporocarp.
//!
//! ## Doctrine alignment
//!
//! - L0/cards/P01-P14 (principles).1 P5: "The substrate is a connected graph, not a collection."
//!   M22 makes the graph span substrates as well as state-mutations.
//! - L0/cards/P01-P14 (principles).2 P8: "The substrate can spawn child substrates." M22.4 makes
//!   parent-child reproduction a live federation link instead of a pure
//!   file-clone snapshot.
//! - L0/cards/P01-P14 (principles).1 P6 永恒因果: peer DAG events arriving via federation are
//!   ingested with the same content-hash determinism as native events
//!   (idempotent on duplicate insertion).

pub mod handlers;
pub mod protocol;
pub mod transport;

// Re-export the operator-facing federation handlers so call sites can use
// `crate::federation::handle_federation_*` without reaching into the
// `handlers` submodule. The `emit_federation_*` helpers are also re-exported
// so the autonomous-tick path in `server.rs` can call them directly.
pub(crate) use handlers::{
    emit_federation_hello_signature_invalid, emit_federation_legacy_peer_pinned,
    emit_federation_peer_pinned, emit_federation_peer_rejected, handle_federation_close_listener,
    handle_federation_connect_peer, handle_federation_link_to_parent_from_hint,
    handle_federation_open_listener, handle_federation_poll,
    handle_federation_pull_events_from_peer, handle_federation_status,
};

use std::io::ErrorKind;
use std::net::{SocketAddr, TcpListener};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use myco_kernel_bridge::protocol::Message;

use crate::SubstrateError;

/// Federation state held inside `ServerState`.
///
/// Always present (never `None`) in server state — federation is opt-in
/// via the `federation_open_listener` bridge message, so the listener stays
/// `None` until invoked.
#[derive(Debug, Default)]
pub struct FederationState {
    /// Active TCP listener if `open_listener` was called. `None` otherwise.
    pub listener: Option<FederationListener>,

    /// Active peer connections (M22.2+). At M22.1 this stays empty —
    /// connections accepted by the listener are stored here once the
    /// `federation_poll` handler is in place (M22.1 ships listener only;
    /// M22.2 wires the accept path).
    pub peers: Vec<transport::PeerConnection>,

    /// Counter of total DAG events received from peers (M22.3+). Persisted
    /// indirectly via the `federation_events_received` DAG events themselves.
    pub events_received_total: u64,

    /// Counter of total DAG events sent to peers (M22.3+).
    pub events_sent_total: u64,

    /// M26.1 C5 SECURITY FIX (Phase γ.2): policy gate for pre-M25 peers that
    /// present no Ed25519 signature in their FED_HELLO.
    ///
    /// **Default**: `false` — legacy hellos are REJECTED and trigger a
    /// `C39_federation_hello_signature_invalid` immune sporocarp (sub-grade
    /// "missing_required_signature"). Under the default policy, M25.4 mutual
    /// auth has real defensive value: an attacker's optimal strategy was
    /// "never sign" because legacy fall-through was always free — that
    /// strategy is now closed.
    ///
    /// **Override**: set the `MYCO_ACCEPT_LEGACY_PEERS=1` environment variable
    /// at substrate boot. When true, legacy hellos are pinned (TOFU only) and
    /// `federation_legacy_peer_pinned` is emitted as observability (NOT an
    /// immune sporocarp — legacy peers are explicitly allowed under this
    /// policy). This is the transition-period flag; long-term doctrine
    /// (L1/GOVERNANCE) expects CI-attested override rather than env var.
    ///
    /// Doctrine traceability: L0/META §10 (negative space) — "the substrate does not silently trust
    /// either party"; Phase γ.2 audit finding "M25.4 mutual auth = 0 because
    /// attacker omits signature".
    pub accept_legacy_peers: bool,

    /// **M26.2 P11.b signal #8 (network/cycle)**: cumulative wire bytes
    /// egressed via federation since the last drain. Each successful
    /// `write_fed_frame` increments this by `4 (length prefix) + frame_body`.
    /// Drained at every `cycle_advanced` boundary by the observatory layer
    /// (see `CostAccumulator::drain_from_federation_state`); the per-cycle
    /// delta becomes `signal_8_network_per_cycle`.
    ///
    /// Saturating-add semantics; overflow at u64::MAX is benign (substrate
    /// would have already exhausted budget/storage long before).
    pub(crate) bytes_egressed_since_last_drain: u64,
}

/// Wrapper around a `TcpListener` carrying its bind address + open timestamp
/// for status reporting and DAG event encoding.
#[derive(Debug)]
pub struct FederationListener {
    /// Underlying nonblocking TCP listener.
    pub listener: TcpListener,
    /// The bound socket address (filled in even when the operator passed
    /// `:0` — we resolve to the OS-picked port).
    pub bind_addr: SocketAddr,
    /// Unix-nanosecond timestamp the listener was opened. Used as the
    /// content of the `federation_listener_opened` DAG event.
    pub opened_at_unix_ns: i64,
}

impl FederationState {
    /// M26.1 C5: construct a `FederationState` with policy read from the
    /// `MYCO_ACCEPT_LEGACY_PEERS` environment variable.
    ///
    /// Value handling:
    /// - `"1"` / `"true"` / `"yes"` (case-insensitive) → accept_legacy_peers = true
    /// - anything else (including unset) → false (default-deny per Phase γ.2)
    ///
    /// Use this at substrate boot in `ServerState::new`. Tests that need the
    /// override-active behavior can also construct directly with
    /// `FederationState { accept_legacy_peers: true, ..Default::default() }`.
    pub fn new_with_env_policy() -> Self {
        let accept_legacy = std::env::var("MYCO_ACCEPT_LEGACY_PEERS")
            .map(|v| {
                let trimmed = v.trim().to_ascii_lowercase();
                trimmed == "1" || trimmed == "true" || trimmed == "yes"
            })
            .unwrap_or(false);
        FederationState {
            accept_legacy_peers: accept_legacy,
            ..Default::default()
        }
    }

    /// **M26.2 P11.b**: read and zero the per-cycle network-egress counter.
    /// Called at each `cycle_advanced` by the observatory layer to produce
    /// `signal_8_network_per_cycle`.
    pub fn drain_bytes_egressed(&mut self) -> u64 {
        std::mem::take(&mut self.bytes_egressed_since_last_drain)
    }

    /// Open a federation TCP listener on `addr`.
    ///
    /// Idempotent in the sense that an existing listener is dropped first.
    /// The listener is `set_nonblocking(true)` so subsequent `accept` calls
    /// during `federation_poll` never block the substrate's main loop.
    ///
    /// Returns the resolved local socket address (which differs from the
    /// requested address when `addr` ends in `:0` and the OS picks a port).
    pub fn open_listener(&mut self, addr: &str) -> Result<SocketAddr, SubstrateError> {
        // Close any pre-existing listener (idempotent re-open).
        self.listener = None;
        let l = TcpListener::bind(addr).map_err(|e| {
            SubstrateError::Protocol(format!("federation listener bind {addr} failed: {e}"))
        })?;
        l.set_nonblocking(true).map_err(SubstrateError::Io)?;
        let bind_addr = l.local_addr().map_err(SubstrateError::Io)?;
        let opened_at_unix_ns = current_unix_ns();
        self.listener = Some(FederationListener {
            listener: l,
            bind_addr,
            opened_at_unix_ns,
        });
        Ok(bind_addr)
    }

    /// Close the federation listener (if any). Returns the previously-bound
    /// address so the caller can encode a `federation_listener_closed` event.
    pub fn close_listener(&mut self) -> Option<SocketAddr> {
        self.listener.take().map(|l| l.bind_addr)
    }

    /// Get the current listener bind address, or `None` if no listener.
    pub fn listener_addr(&self) -> Option<SocketAddr> {
        self.listener.as_ref().map(|l| l.bind_addr)
    }

    /// Number of currently-tracked peer connections (M22.2+; always 0 at M22.1).
    pub fn peer_count(&self) -> usize {
        self.peers.len()
    }

    /// M22.2: outbound dial + FED_HELLO roundtrip + TOFU pin.
    ///
    /// Synchronous (blocking) — operator waits for the handshake to complete
    /// or fail. On success, the peer is added to `self.peers` in
    /// [`PeerConnectionState::Established`].
    ///
    /// Returns a [`ConnectPeerOutcome`] so the caller can emit the correct
    /// DAG event (`federation_peer_pinned` for success;
    /// `federation_peer_rejected` for identity conflicts).
    pub fn connect_peer(
        &mut self,
        remote_addr: &str,
        our_substrate_id: &[u8; 32],
        our_dag_tip: Option<&[u8; 32]>,
        our_signing_seed: Option<&[u8; 32]>,
    ) -> Result<ConnectPeerOutcome, SubstrateError> {
        let (mut stream, peer_addr) = transport::dial_blocking(remote_addr)
            .map_err(|e| SubstrateError::Protocol(format!("federation dial: {e}")))?;
        stream
            .set_read_timeout(Some(Duration::from_secs(
                transport::HELLO_ACK_READ_TIMEOUT_SECS,
            )))
            .map_err(SubstrateError::Io)?;

        // M25.4: derive our hello signature when a signing seed is provided.
        // Pre-M25 callers (or substrates that have not yet wired the seed
        // through) pass None and downgrade to substrate_id-only TOFU.
        let (our_signer_pubkey_arr, our_hello_signature_arr) =
            sign_fed_hello_if_available(
                our_signing_seed,
                our_substrate_id,
                our_dag_tip,
            );

        // Send our FED_HELLO.
        let hello_payload = protocol::build_fed_hello_payload(
            our_substrate_id,
            our_dag_tip,
            our_signer_pubkey_arr.as_ref(),
            our_hello_signature_arr.as_ref(),
        );
        let hello_msg = Message::new(protocol::fed_msg_type::FED_HELLO, 1, hello_payload);
        let bootstrap = protocol::federation_bootstrap_key();
        // M26.2 signal_8: track network bytes on successful egress.
        let hello_bytes = transport::write_fed_frame(&mut stream, &hello_msg, &bootstrap)
            .map_err(|e| SubstrateError::Protocol(format!("federation hello write: {e}")))?;
        self.bytes_egressed_since_last_drain = self
            .bytes_egressed_since_last_drain
            .saturating_add(hello_bytes as u64);

        // Await FED_HELLO_ACK.
        let ack_msg = match transport::read_fed_frame(&mut stream, &bootstrap)
            .map_err(|e| SubstrateError::Protocol(format!("federation hello ack read: {e}")))?
        {
            Some(m) => m,
            None => {
                transport::close_stream(&stream);
                return Err(SubstrateError::Protocol(
                    "federation hello ack: timeout / no response".to_string(),
                ));
            }
        };

        if ack_msg.message_type != protocol::fed_msg_type::FED_HELLO_ACK {
            transport::close_stream(&stream);
            return Err(SubstrateError::Protocol(format!(
                "federation: expected fed_hello_ack; got {}",
                ack_msg.message_type
            )));
        }

        let parsed = protocol::parse_fed_hello_payload(&ack_msg.payload)
            .map_err(SubstrateError::Protocol)?;

        // M25.4: verify the peer's hello signature if present. Three outcomes:
        // - Ok(true): signature verified — pin signer_pubkey alongside id.
        // - Ok(false): legacy peer (no signature) — M26.1 C5 SECURITY FIX:
        //   under default policy (`accept_legacy_peers=false`) this is REJECTED
        //   with sub-grade `missing_required_signature`. Pre-fix, M25.4 mutual
        //   auth had 0 defensive value because attackers could simply omit the
        //   signature; Phase γ.2 audit closed that hole. Override via
        //   `MYCO_ACCEPT_LEGACY_PEERS=1` for transition-period compatibility.
        // - Err: tampered signature — reject the connection.
        let signature_verified = match protocol::verify_fed_hello_signature(&parsed) {
            Ok(true) => true,
            Ok(false) => {
                if self.accept_legacy_peers {
                    // Legacy override active: fall through to TOFU-only pinning;
                    // caller emits federation_legacy_peer_pinned observability.
                    false
                } else {
                    // M26.1 C5: reject — peer omitted the required signature.
                    transport::close_stream(&stream);
                    return Ok(ConnectPeerOutcome::RejectedSignatureInvalid {
                        peer_substrate_id: parsed.peer_substrate_id,
                        remote_addr_str: peer_addr.to_string(),
                        reason: "missing_required_signature: legacy hellos are \
                                 rejected unless MYCO_ACCEPT_LEGACY_PEERS=1"
                            .to_string(),
                    });
                }
            }
            Err(reason) => {
                transport::close_stream(&stream);
                return Ok(ConnectPeerOutcome::RejectedSignatureInvalid {
                    peer_substrate_id: parsed.peer_substrate_id,
                    remote_addr_str: peer_addr.to_string(),
                    reason,
                });
            }
        };

        // Self-connect rejection: a substrate connecting to itself is a no-op
        // (and would cause confusing self-replication). M22.2 makes this an
        // explicit error rather than silently accepting.
        if &parsed.peer_substrate_id == our_substrate_id {
            transport::close_stream(&stream);
            return Ok(ConnectPeerOutcome::RejectedSelfConnection {
                remote_addr_str: peer_addr.to_string(),
            });
        }

        // TOFU pinning check: if we already have a peer with this substrate_id
        // but at a DIFFERENT remote address, that's identity drift — reject
        // and surface for the C33 detector (substrate-private namespace; was C20 prior to Phase β rename).
        if let Some(existing) = self
            .peers
            .iter()
            .find(|p| p.peer_substrate_id == Some(parsed.peer_substrate_id))
        {
            if existing.remote_addr != peer_addr {
                let existing_addr_str = existing.remote_addr.to_string();
                transport::close_stream(&stream);
                return Ok(ConnectPeerOutcome::RejectedIdentityDrift {
                    peer_substrate_id: parsed.peer_substrate_id,
                    new_remote_addr_str: peer_addr.to_string(),
                    previously_pinned_remote_addr_str: existing_addr_str,
                });
            }
            // M25.4: if both we and peer have pinned signer_pubkeys, they must
            // match — otherwise a peer presenting the same substrate_id with a
            // DIFFERENT signing pubkey is identity drift even on a stable IP.
            if let (Some(existing_pk), Some(new_pk)) =
                (&existing.pinned_signer_pubkey, &parsed.signer_pubkey)
            {
                if existing_pk != new_pk {
                    let existing_addr_str = existing.remote_addr.to_string();
                    transport::close_stream(&stream);
                    return Ok(ConnectPeerOutcome::RejectedIdentityDrift {
                        peer_substrate_id: parsed.peer_substrate_id,
                        new_remote_addr_str: peer_addr.to_string(),
                        previously_pinned_remote_addr_str: existing_addr_str,
                    });
                }
            }
            // Same id, same addr — peer is reconnecting after a network hiccup.
            // The existing connection may be stale; replace it.
            // For M22.2 we just refuse the reconnect — operator can call
            // close_peer (M22.3+) first.
            transport::close_stream(&stream);
            return Ok(ConnectPeerOutcome::AlreadyPinned {
                peer_substrate_id: parsed.peer_substrate_id,
                remote_addr_str: peer_addr.to_string(),
            });
        }

        // Pin the new peer. M25.4: only pin signer_pubkey when we *verified*
        // the signature — never trust an unverified key.
        let pinned_signer = if signature_verified {
            parsed.signer_pubkey
        } else {
            None
        };
        let peer = transport::PeerConnection {
            stream,
            state: transport::PeerConnectionState::Established,
            peer_substrate_id: Some(parsed.peer_substrate_id),
            pinned_signer_pubkey: pinned_signer,
            remote_addr: peer_addr,
            opened_at_unix_ns: current_unix_ns(),
        };
        self.peers.push(peer);

        Ok(ConnectPeerOutcome::Pinned {
            peer_substrate_id: parsed.peer_substrate_id,
            remote_addr_str: peer_addr.to_string(),
            peer_dag_tip: parsed.peer_dag_tip,
            signer_pubkey: pinned_signer,
            signature_verified,
        })
    }

    /// M22.2: nonblocking accept loop — accept all currently-queued inbound
    /// connections and add them to `self.peers` in
    /// [`PeerConnectionState::AwaitingHello`].
    ///
    /// Returns the count of newly-accepted connections (for status reporting).
    pub fn accept_pending(&mut self) -> Result<usize, SubstrateError> {
        let Some(listener) = self.listener.as_ref() else {
            return Ok(0);
        };
        let mut accepted = 0usize;
        loop {
            match listener.listener.accept() {
                Ok((stream, remote_addr)) => {
                    // Set a short read timeout so polls don't block.
                    let _ = stream.set_read_timeout(Some(Duration::from_millis(
                        transport::POLL_READ_TIMEOUT_MS,
                    )));
                    self.peers.push(transport::PeerConnection {
                        stream,
                        state: transport::PeerConnectionState::AwaitingHello,
                        peer_substrate_id: None,
                        pinned_signer_pubkey: None,
                        remote_addr,
                        opened_at_unix_ns: current_unix_ns(),
                    });
                    accepted += 1;
                }
                Err(e) if e.kind() == ErrorKind::WouldBlock => break,
                Err(e) => {
                    return Err(SubstrateError::Io(e));
                }
            }
        }
        Ok(accepted)
    }

    /// M22.2: for each peer in `AwaitingHello`, try to read one FED_HELLO frame
    /// (with the short poll-read timeout) and complete the handshake.
    ///
    /// On a successful HELLO, sends FED_HELLO_ACK and transitions the peer to
    /// `Established`. On a rejected HELLO (self-connect / identity drift),
    /// sends a FED_ERROR and removes the peer from the list.
    ///
    /// Returns a vector of [`PollPeerEvent`] for the caller to emit DAG events.
    /// Failed peers are removed from `self.peers` automatically.
    pub fn progress_awaiting_hello_peers(
        &mut self,
        our_substrate_id: &[u8; 32],
        our_dag_tip: Option<&[u8; 32]>,
        our_signing_seed: Option<&[u8; 32]>,
    ) -> Vec<PollPeerEvent> {
        let bootstrap = protocol::federation_bootstrap_key();
        let mut events = Vec::new();
        let mut indices_to_remove: Vec<usize> = Vec::new();

        // M25.4: pre-compute our outbound ack signature once per poll round.
        let (our_signer_pubkey_arr, our_hello_signature_arr) =
            sign_fed_hello_if_available(
                our_signing_seed,
                our_substrate_id,
                our_dag_tip,
            );

        for (idx, peer) in self.peers.iter_mut().enumerate() {
            if peer.state != transport::PeerConnectionState::AwaitingHello {
                continue;
            }
            let frame_result = transport::read_fed_frame(&mut peer.stream, &bootstrap);
            let hello_msg = match frame_result {
                Ok(Some(m)) => m,
                Ok(None) => continue, // No frame ready yet; try again next poll.
                Err(e) => {
                    // Protocol error — close the peer.
                    events.push(PollPeerEvent::FailedFrameRead {
                        remote_addr_str: peer.remote_addr.to_string(),
                        reason: e.to_string(),
                    });
                    transport::close_stream(&peer.stream);
                    peer.state = transport::PeerConnectionState::Failed;
                    indices_to_remove.push(idx);
                    continue;
                }
            };
            if hello_msg.message_type != protocol::fed_msg_type::FED_HELLO {
                events.push(PollPeerEvent::FailedFrameRead {
                    remote_addr_str: peer.remote_addr.to_string(),
                    reason: format!(
                        "expected fed_hello as first frame; got {}",
                        hello_msg.message_type
                    ),
                });
                transport::close_stream(&peer.stream);
                peer.state = transport::PeerConnectionState::Failed;
                indices_to_remove.push(idx);
                continue;
            }
            let parsed = match protocol::parse_fed_hello_payload(&hello_msg.payload) {
                Ok(p) => p,
                Err(e) => {
                    events.push(PollPeerEvent::FailedFrameRead {
                        remote_addr_str: peer.remote_addr.to_string(),
                        reason: format!("parse fed_hello: {e}"),
                    });
                    transport::close_stream(&peer.stream);
                    peer.state = transport::PeerConnectionState::Failed;
                    indices_to_remove.push(idx);
                    continue;
                }
            };
            // M25.4: verify the peer's hello signature when present. A tampered
            // signature is a hard reject (peer impersonation attempt).
            // M26.1 C5 SECURITY FIX: a peer with NO signature is also a hard
            // reject under the default policy (`accept_legacy_peers=false`).
            // Pre-fix, M25.4 mutual auth was bypassable by omitting the
            // signature — attacker's optimal strategy was "never sign".
            // Override via `MYCO_ACCEPT_LEGACY_PEERS=1` env var for
            // transition-period compatibility (legacy hellos then pin TOFU
            // only + emit `federation_legacy_peer_pinned` observability).
            let signature_verified = match protocol::verify_fed_hello_signature(&parsed) {
                Ok(true) => true,
                Ok(false) => {
                    if self.accept_legacy_peers {
                        // Override active — proceed with TOFU-only pinning.
                        false
                    } else {
                        let reason = "missing_required_signature: legacy hellos \
                                      are rejected unless MYCO_ACCEPT_LEGACY_PEERS=1"
                            .to_string();
                        let _ = send_fed_error(
                            &mut peer.stream,
                            "hello_signature_invalid",
                            &reason,
                        );
                        events.push(PollPeerEvent::RejectedSignatureInvalid {
                            peer_substrate_id: parsed.peer_substrate_id,
                            remote_addr_str: peer.remote_addr.to_string(),
                            reason,
                        });
                        transport::close_stream(&peer.stream);
                        peer.state = transport::PeerConnectionState::Failed;
                        indices_to_remove.push(idx);
                        continue;
                    }
                }
                Err(reason) => {
                    let _ = send_fed_error(
                        &mut peer.stream,
                        "hello_signature_invalid",
                        &reason,
                    );
                    events.push(PollPeerEvent::RejectedSignatureInvalid {
                        peer_substrate_id: parsed.peer_substrate_id,
                        remote_addr_str: peer.remote_addr.to_string(),
                        reason,
                    });
                    transport::close_stream(&peer.stream);
                    peer.state = transport::PeerConnectionState::Failed;
                    indices_to_remove.push(idx);
                    continue;
                }
            };
            // Self-connect rejection.
            if &parsed.peer_substrate_id == our_substrate_id {
                let _ = send_fed_error(&mut peer.stream, "self_connection", "peer id is self");
                events.push(PollPeerEvent::RejectedSelfConnection {
                    remote_addr_str: peer.remote_addr.to_string(),
                });
                transport::close_stream(&peer.stream);
                peer.state = transport::PeerConnectionState::Failed;
                indices_to_remove.push(idx);
                continue;
            }
            // Send FED_HELLO_ACK + transition to Established. Note that we
            // don't check for identity drift here against our peer list,
            // because at this point we have NOT yet pinned the peer; the
            // check we want is "does this id match THIS peer's prior HELLO?"
            // — and AwaitingHello peers don't have prior HELLOs by definition.
            // Identity drift between peers (same id from two different
            // connections) is intentionally tolerant at M22.2 inbound — the
            // outbound `connect_peer` path enforces drift detection because
            // that's where the operator has clear policy intent.
            let ack_payload = protocol::build_fed_hello_ack_payload(
                our_substrate_id,
                our_dag_tip,
                our_signer_pubkey_arr.as_ref(),
                our_hello_signature_arr.as_ref(),
            );
            let ack_msg = Message::new(
                protocol::fed_msg_type::FED_HELLO_ACK,
                hello_msg.request_id,
                ack_payload,
            );
            match transport::write_fed_frame(&mut peer.stream, &ack_msg, &bootstrap) {
                Ok(ack_bytes) => {
                    // M26.2 signal_8: track network egress.
                    self.bytes_egressed_since_last_drain = self
                        .bytes_egressed_since_last_drain
                        .saturating_add(ack_bytes as u64);
                    peer.state = transport::PeerConnectionState::Established;
                    peer.peer_substrate_id = Some(parsed.peer_substrate_id);
                    // M25.4: only pin signer_pubkey on verified signatures.
                    if signature_verified {
                        peer.pinned_signer_pubkey = parsed.signer_pubkey;
                    }
                    events.push(PollPeerEvent::Pinned {
                        peer_substrate_id: parsed.peer_substrate_id,
                        remote_addr_str: peer.remote_addr.to_string(),
                        peer_dag_tip: parsed.peer_dag_tip,
                        signer_pubkey: if signature_verified {
                            parsed.signer_pubkey
                        } else {
                            None
                        },
                        signature_verified,
                    });
                }
                Err(e) => {
                    events.push(PollPeerEvent::FailedFrameRead {
                        remote_addr_str: peer.remote_addr.to_string(),
                        reason: format!("send fed_hello_ack: {e}"),
                    });
                    transport::close_stream(&peer.stream);
                    peer.state = transport::PeerConnectionState::Failed;
                    indices_to_remove.push(idx);
                }
            }
        }

        // Sweep failed peers (in reverse so indices stay valid).
        for idx in indices_to_remove.into_iter().rev() {
            self.peers.swap_remove(idx);
        }

        events
    }

    /// M22.2: find an established peer by substrate_id. Returns the peer's
    /// index in `self.peers` (None if not found or not established).
    pub fn find_established_peer(&self, peer_substrate_id: &[u8; 32]) -> Option<usize> {
        self.peers.iter().position(|p| {
            p.peer_substrate_id == Some(*peer_substrate_id)
                && p.state == transport::PeerConnectionState::Established
        })
    }

    /// M22.3: pull DAG events from a peer.
    ///
    /// Blocking: sends FED_REQUEST_EVENTS_SINCE with session key, waits up
    /// to 10s for FED_EVENT_BATCH, returns the parsed batch. The caller is
    /// responsible for inserting each event into the local DAG (via
    /// `Dag::insert_node`).
    pub fn pull_events_from_peer(
        &mut self,
        peer_substrate_id: &[u8; 32],
        since_node_hash: Option<&[u8; 32]>,
        our_substrate_id: &[u8; 32],
        max_events: u64,
    ) -> Result<protocol::ParsedEventBatch, SubstrateError> {
        let peer_idx = self.find_established_peer(peer_substrate_id).ok_or_else(|| {
            SubstrateError::Protocol(
                "pull_events_from_peer: peer not found or not Established".to_string(),
            )
        })?;
        let session_key =
            protocol::derive_federation_session_key(our_substrate_id, peer_substrate_id);

        let peer = &mut self.peers[peer_idx];
        // Bump read timeout for event batch response (might be larger).
        peer.stream
            .set_read_timeout(Some(Duration::from_secs(10)))
            .map_err(SubstrateError::Io)?;

        let req_payload =
            protocol::build_request_events_since_payload(since_node_hash, max_events);
        let req_msg = Message::new(
            protocol::fed_msg_type::FED_REQUEST_EVENTS_SINCE,
            1,
            req_payload,
        );
        // M26.2 signal_8: track network egress for pull-request frame.
        let req_bytes = transport::write_fed_frame(&mut peer.stream, &req_msg, &session_key)
            .map_err(|e| SubstrateError::Protocol(format!("pull req write: {e}")))?;
        self.bytes_egressed_since_last_drain = self
            .bytes_egressed_since_last_drain
            .saturating_add(req_bytes as u64);

        let resp_msg = match transport::read_fed_frame(&mut peer.stream, &session_key)
            .map_err(|e| SubstrateError::Protocol(format!("pull resp read: {e}")))?
        {
            Some(m) => m,
            None => {
                return Err(SubstrateError::Protocol(
                    "pull_events_from_peer: timeout / no FED_EVENT_BATCH response".to_string(),
                ));
            }
        };
        if resp_msg.message_type != protocol::fed_msg_type::FED_EVENT_BATCH {
            return Err(SubstrateError::Protocol(format!(
                "pull_events_from_peer: expected fed_event_batch; got {}",
                resp_msg.message_type
            )));
        }
        protocol::parse_event_batch_payload(&resp_msg.payload).map_err(SubstrateError::Protocol)
    }

    /// M22.3: extended poll — handles BOTH AwaitingHello peers (HELLO/ACK
    /// roundtrip from M22.2) AND Established peers' incoming
    /// FED_REQUEST_EVENTS_SINCE frames.
    ///
    /// For inbound requests, enumerates local DAG events newer than the
    /// peer-supplied `since_node_hash`, builds FED_EVENT_BATCH, and writes
    /// it back. Yields a `PollPeerEvent::EventsSent` so the caller can emit
    /// a `federation_events_sent` DAG event.
    pub fn progress_peers(
        &mut self,
        our_substrate_id: &[u8; 32],
        our_dag_tip: Option<&[u8; 32]>,
        our_signing_seed: Option<&[u8; 32]>,
        local_dag: &myco_kernel_schema::dag::Dag,
    ) -> Vec<PollPeerEvent> {
        // M22.2 path: progress AwaitingHello peers first (existing logic).
        let mut events = self.progress_awaiting_hello_peers(
            our_substrate_id,
            our_dag_tip,
            our_signing_seed,
        );

        // M22.3 path: progress Established peers (read inbound REQUEST_EVENTS_SINCE).
        let mut indices_to_remove: Vec<usize> = Vec::new();
        for (idx, peer) in self.peers.iter_mut().enumerate() {
            if peer.state != transport::PeerConnectionState::Established {
                continue;
            }
            let peer_id = match peer.peer_substrate_id {
                Some(id) => id,
                None => continue, // shouldn't happen for Established
            };
            let session_key =
                protocol::derive_federation_session_key(our_substrate_id, &peer_id);
            // Short-timeout read (already set on the peer's stream).
            let frame_result = transport::read_fed_frame(&mut peer.stream, &session_key);
            let msg = match frame_result {
                Ok(Some(m)) => m,
                Ok(None) => continue,
                Err(e) => {
                    events.push(PollPeerEvent::FailedFrameRead {
                        remote_addr_str: peer.remote_addr.to_string(),
                        reason: format!("established read: {e}"),
                    });
                    transport::close_stream(&peer.stream);
                    peer.state = transport::PeerConnectionState::Failed;
                    indices_to_remove.push(idx);
                    continue;
                }
            };
            if msg.message_type == protocol::fed_msg_type::FED_REQUEST_EVENTS_SINCE {
                let parsed = match protocol::parse_request_events_since_payload(&msg.payload) {
                    Ok(p) => p,
                    Err(e) => {
                        events.push(PollPeerEvent::FailedFrameRead {
                            remote_addr_str: peer.remote_addr.to_string(),
                            reason: format!("parse REQ_EVENTS_SINCE: {e}"),
                        });
                        continue;
                    }
                };
                let to_send = enumerate_events_for_federation(
                    local_dag,
                    parsed.since_node_hash.as_ref(),
                    parsed.max_events as usize,
                );
                let is_last_batch = to_send.len() < (parsed.max_events as usize);
                let sent_hashes: Vec<[u8; 32]> = to_send
                    .iter()
                    .map(|e| {
                        myco_kernel_shared::crypto::merkle_hash(
                            &e.parent_hashes
                                .iter()
                                .map(|h| myco_kernel_shared::crypto::NodeHash::from_bytes(*h))
                                .collect::<Vec<_>>(),
                            &e.content_canonical_bytes,
                        )
                        .0
                    })
                    .collect();
                let resp_payload = protocol::build_event_batch_payload(&to_send, is_last_batch);
                let resp_msg = Message::new(
                    protocol::fed_msg_type::FED_EVENT_BATCH,
                    msg.request_id,
                    resp_payload,
                );
                match transport::write_fed_frame(&mut peer.stream, &resp_msg, &session_key) {
                    Ok(resp_bytes) => {
                        // M26.2 signal_8: track network egress.
                        self.bytes_egressed_since_last_drain = self
                            .bytes_egressed_since_last_drain
                            .saturating_add(resp_bytes as u64);
                        self.events_sent_total =
                            self.events_sent_total.saturating_add(to_send.len() as u64);
                        events.push(PollPeerEvent::EventsSent {
                            peer_substrate_id: peer_id,
                            sent_event_hashes: sent_hashes,
                        });
                    }
                    Err(e) => {
                        events.push(PollPeerEvent::FailedFrameRead {
                            remote_addr_str: peer.remote_addr.to_string(),
                            reason: format!("send EVENT_BATCH: {e}"),
                        });
                        transport::close_stream(&peer.stream);
                        peer.state = transport::PeerConnectionState::Failed;
                        indices_to_remove.push(idx);
                    }
                }
            } else {
                // Ignore unknown frame types (forward-compat); a future fed
                // protocol version might add new message types we should
                // tolerate as unknown rather than fail-hard.
            }
        }
        for idx in indices_to_remove.into_iter().rev() {
            self.peers.swap_remove(idx);
        }

        events
    }
}

/// M22.3: enumerate up to `max_events` DAG events newer than `since` (or all
/// if `since` is None) in DAG insertion order. Returns events ready for
/// federation transmission.
fn enumerate_events_for_federation(
    dag: &myco_kernel_schema::dag::Dag,
    since_node_hash: Option<&[u8; 32]>,
    max_events: usize,
) -> Vec<protocol::EventForFederation> {
    let since_hash =
        since_node_hash.map(|h| myco_kernel_shared::crypto::NodeHash::from_bytes(*h));
    let mut started = since_hash.is_none();
    let mut out = Vec::with_capacity(max_events.min(64));
    for node in dag.iter_in_insertion_order() {
        if !started {
            if let Some(target) = since_hash.as_ref() {
                if &node.hash == target {
                    started = true;
                }
            }
            continue;
        }
        if out.len() >= max_events {
            break;
        }
        out.push(protocol::EventForFederation {
            parent_hashes: node.parent_hashes.iter().map(|h| h.0).collect(),
            node_type: node.node_type.clone(),
            created_at_cycle: node.created_at_cycle,
            content_canonical_bytes: node.content_canonical_bytes.as_ref().to_vec(),
        });
    }
    out
}

/// Helper: send a FED_ERROR envelope on a peer's stream (best-effort; ignored).
///
/// **M26.2 note**: error-path egress is NOT tracked in signal_8 because this
/// free function lacks `&mut FederationState`. Error frames are rare, small
/// (~50-100 bytes), and untracked egress is the conservative bias — better to
/// undercount cost than to overcount. If error-path traffic ever dominates,
/// promote this to a method on `FederationState`.
fn send_fed_error(stream: &mut std::net::TcpStream, code: &str, message: &str) -> Result<(), ()> {
    let payload = protocol::build_fed_error_payload(code, message);
    let msg = Message::new(protocol::fed_msg_type::FED_ERROR, 0, payload);
    let bootstrap = protocol::federation_bootstrap_key();
    transport::write_fed_frame(stream, &msg, &bootstrap)
        .map(|_| ())
        .map_err(|_| ())
}

/// M25.4: helper — derive (pubkey, signature) pair for our outbound FED_HELLO
/// payload when a signing seed is provided. Returns (None, None) when seed is
/// absent (caller acts as a legacy peer; receiver falls through to TOFU).
///
/// Materialises the result as `[u8; 32]` and `[u8; 64]` arrays so the caller
/// can borrow `Option::as_ref()` into the payload builder without moving the
/// signing key.
fn sign_fed_hello_if_available(
    our_signing_seed: Option<&[u8; 32]>,
    our_substrate_id: &[u8; 32],
    our_dag_tip: Option<&[u8; 32]>,
) -> (Option<[u8; 32]>, Option<[u8; 64]>) {
    let seed = match our_signing_seed {
        Some(s) => s,
        None => return (None, None),
    };
    let key = myco_kernel_shared::crypto::Ed25519PrivateKey::from_seed(seed);
    let pubkey = key.public_key().0;
    let signing_message = protocol::build_fed_hello_signing_message(
        our_substrate_id,
        our_dag_tip,
        protocol::FEDERATION_PROTOCOL_VERSION,
    );
    let sig = key.sign(&signing_message).0;
    (Some(pubkey), Some(sig))
}

/// Outcome of `connect_peer`. The substrate's federation handler reads this
/// to decide which DAG event (or operator error envelope) to emit.
#[derive(Debug, Clone)]
pub enum ConnectPeerOutcome {
    /// Peer pinned successfully (TOFU first-sight). Emit
    /// `federation_peer_pinned` DAG event.
    Pinned {
        /// The peer's 32-byte substrate_id (newly-pinned).
        peer_substrate_id: [u8; 32],
        /// Remote socket address as `host:port`.
        remote_addr_str: String,
        /// Peer's DAG tip (if any).
        peer_dag_tip: Option<[u8; 32]>,
        /// M25.4: peer's signing pubkey if their hello carried a verified
        /// signature; `None` when the peer is legacy / unsigned.
        signer_pubkey: Option<[u8; 32]>,
        /// M25.4: `true` if the peer presented a signature we verified;
        /// `false` for legacy peers. Used to differentiate the
        /// `federation_peer_pinned` event payload from the observability
        /// `federation_legacy_peer_pinned` event.
        signature_verified: bool,
    },
    /// Peer's substrate_id matches our own — silly self-connect. Emit nothing;
    /// surface as operator-level error.
    RejectedSelfConnection {
        /// Remote socket address attempted.
        remote_addr_str: String,
    },
    /// Peer's substrate_id matches a previously-pinned peer at a DIFFERENT
    /// address — identity drift. Emit `federation_peer_rejected` DAG event +
    /// C33 immune sporocarp (substrate-private; was C20).
    RejectedIdentityDrift {
        /// The substrate_id that's being re-claimed.
        peer_substrate_id: [u8; 32],
        /// Address attempting to claim it now.
        new_remote_addr_str: String,
        /// Address that previously pinned the id.
        previously_pinned_remote_addr_str: String,
    },
    /// M25.4: Peer presented a `hello_signature` that failed Ed25519 verification.
    /// This is a peer impersonation attempt; emit C39 immune sporocarp.
    RejectedSignatureInvalid {
        /// The peer's claimed substrate_id (cannot be trusted; logged only).
        peer_substrate_id: [u8; 32],
        /// Remote socket address.
        remote_addr_str: String,
        /// Verifier's failure reason (for observability).
        reason: String,
    },
    /// Peer's substrate_id + address match an already-pinned peer — no-op.
    AlreadyPinned {
        /// The peer's id (already pinned).
        peer_substrate_id: [u8; 32],
        /// Remote socket address.
        remote_addr_str: String,
    },
}

/// Per-peer event yielded by `progress_awaiting_hello_peers` — the caller
/// emits DAG events / immune sporocarps based on these.
#[derive(Debug, Clone)]
pub enum PollPeerEvent {
    /// A peer was newly pinned via inbound FED_HELLO.
    Pinned {
        /// 32-byte substrate_id of the newly-pinned peer.
        peer_substrate_id: [u8; 32],
        /// Remote socket address as `host:port`.
        remote_addr_str: String,
        /// Peer's DAG tip (if any).
        peer_dag_tip: Option<[u8; 32]>,
        /// M25.4: peer's signing pubkey if signature verified; `None` for
        /// legacy peers.
        signer_pubkey: Option<[u8; 32]>,
        /// M25.4: whether the peer's hello carried a verified Ed25519 signature.
        signature_verified: bool,
    },
    /// Inbound peer claimed our own substrate_id — rejected.
    RejectedSelfConnection {
        /// Remote socket address of the offending connection.
        remote_addr_str: String,
    },
    /// M25.4: inbound peer presented a `hello_signature` that failed
    /// verification — peer impersonation attempt.
    RejectedSignatureInvalid {
        /// The peer's claimed substrate_id (untrusted).
        peer_substrate_id: [u8; 32],
        /// Remote socket address.
        remote_addr_str: String,
        /// Verifier's failure reason.
        reason: String,
    },
    /// A peer connection failed at the frame-read stage. The peer has been
    /// removed from `self.peers` by `progress_awaiting_hello_peers`.
    FailedFrameRead {
        /// Remote socket address of the failed peer.
        remote_addr_str: String,
        /// Human-readable failure reason for the immune sporocarp evidence.
        reason: String,
    },
    /// M22.3: A FED_EVENT_BATCH was sent to a peer in response to its
    /// FED_REQUEST_EVENTS_SINCE. Emit `federation_events_sent` DAG event.
    EventsSent {
        /// The peer we sent to.
        peer_substrate_id: [u8; 32],
        /// Hashes of the DAG events we sent.
        sent_event_hashes: Vec<[u8; 32]>,
    },
}

/// Wall-clock unix nanoseconds. Shared utility used by federation event encoders.
pub(crate) fn current_unix_ns() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn open_listener_with_port_zero_resolves_real_port() {
        let mut fed = FederationState::default();
        let addr = fed.open_listener("127.0.0.1:0").unwrap();
        assert_eq!(addr.ip().to_string(), "127.0.0.1");
        assert!(addr.port() > 0, "OS should pick a real port; got 0");
    }

    #[test]
    fn close_listener_returns_previous_addr() {
        let mut fed = FederationState::default();
        let addr = fed.open_listener("127.0.0.1:0").unwrap();
        let closed = fed.close_listener().expect("had a listener");
        assert_eq!(closed.port(), addr.port());
        assert!(fed.listener_addr().is_none());
    }

    #[test]
    fn close_listener_idempotent_when_none() {
        let mut fed = FederationState::default();
        assert!(fed.close_listener().is_none());
        assert!(fed.close_listener().is_none());
    }

    #[test]
    fn reopen_listener_replaces_old() {
        let mut fed = FederationState::default();
        let addr1 = fed.open_listener("127.0.0.1:0").unwrap();
        let addr2 = fed.open_listener("127.0.0.1:0").unwrap();
        // Both should be valid + ports likely differ (OS reuse possible).
        assert!(addr1.port() > 0);
        assert!(addr2.port() > 0);
        // Listener should reflect the second open.
        assert_eq!(fed.listener_addr().unwrap().port(), addr2.port());
    }

    #[test]
    fn bind_invalid_address_returns_protocol_error() {
        let mut fed = FederationState::default();
        // Port 0 is fine; address "not-an-address" is not.
        let err = fed.open_listener("not:an:address").unwrap_err();
        match err {
            SubstrateError::Protocol(msg) => assert!(msg.contains("bind")),
            other => panic!("expected Protocol; got {other:?}"),
        }
    }

    #[test]
    fn peer_count_initially_zero() {
        let fed = FederationState::default();
        assert_eq!(fed.peer_count(), 0);
        assert_eq!(fed.events_received_total, 0);
        assert_eq!(fed.events_sent_total, 0);
    }

    // ---------------------------------------------------------------------------
    // M26.1 C5 (Phase γ.2): mandatory FED_HELLO signature policy.
    //
    // FederationState::default() must have accept_legacy_peers = false; the
    // env-policy constructor reads MYCO_ACCEPT_LEGACY_PEERS. These tests are
    // serial because they mutate the process environment.
    // ---------------------------------------------------------------------------

    /// Lock to serialize env-var manipulation across the C5 unit tests below.
    /// Cargo test parallelism would otherwise race on `std::env::set_var`.
    fn env_lock() -> std::sync::MutexGuard<'static, ()> {
        use std::sync::{Mutex, OnceLock};
        static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
        LOCK.get_or_init(|| Mutex::new(()))
            .lock()
            .unwrap_or_else(|e| e.into_inner())
    }

    #[test]
    fn m26_1_c5_default_rejects_legacy_peers() {
        let _g = env_lock();
        std::env::remove_var("MYCO_ACCEPT_LEGACY_PEERS");
        let fed = FederationState::new_with_env_policy();
        assert!(
            !fed.accept_legacy_peers,
            "M26.1 C5: default policy must reject legacy peers"
        );
    }

    #[test]
    fn m26_1_c5_env_var_1_enables_override() {
        let _g = env_lock();
        std::env::set_var("MYCO_ACCEPT_LEGACY_PEERS", "1");
        let fed = FederationState::new_with_env_policy();
        std::env::remove_var("MYCO_ACCEPT_LEGACY_PEERS");
        assert!(
            fed.accept_legacy_peers,
            "MYCO_ACCEPT_LEGACY_PEERS=1 must enable override"
        );
    }

    #[test]
    fn m26_1_c5_env_var_true_enables_override() {
        let _g = env_lock();
        std::env::set_var("MYCO_ACCEPT_LEGACY_PEERS", "true");
        let fed = FederationState::new_with_env_policy();
        std::env::remove_var("MYCO_ACCEPT_LEGACY_PEERS");
        assert!(fed.accept_legacy_peers);
    }

    #[test]
    fn m26_1_c5_env_var_garbage_keeps_default_deny() {
        let _g = env_lock();
        std::env::set_var("MYCO_ACCEPT_LEGACY_PEERS", "no");
        let fed = FederationState::new_with_env_policy();
        std::env::remove_var("MYCO_ACCEPT_LEGACY_PEERS");
        assert!(
            !fed.accept_legacy_peers,
            "non-truthy value must keep default-deny"
        );
    }
}
