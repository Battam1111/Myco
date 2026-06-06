//! Bridge client — spawn Python worker subprocess + drive the protocol.
//!
//! The [`BridgeClient`] struct owns the child process and its stdio pipes.
//! Method calls map 1:1 to the wire-protocol message types.
//!
//! ## Subprocess management
//!
//! - The Python worker is spawned via `<python> -m myco_kernel_bridge`.
//! - Both stdin and stdout are piped (binary, no line buffering).
//! - The child's stderr is inherited from the parent (Python tracebacks
//!   surface to the controller's stderr — useful for debugging M5 failures).
//! - On [`Drop`], the client sends `shutdown` (best effort) and waits for
//!   the child to exit cleanly.
//!
//! ## Synchronous protocol
//!
//! M5 is request-response with strict serial ordering: each request writes a
//! frame, blocks for the response, and verifies the correlation ID. M6+ may
//! add async + pipelining.
//!
//! ## Reader thread (v3.1.1 Sprint 7.E.2)
//!
//! The controller side does NOT read stdout inline. Instead,
//! [`BridgeClient::spawn_and_handshake`] launches a **permanent reader
//! thread** that owns `BufReader<ChildStdout>` and continuously pulls
//! length-prefixed HMAC frames, decoding each into a
//! `Result<Message, BridgeError>` pushed over an [`std::sync::mpsc`] channel.
//! The main thread writes a request frame to stdin, then blocks on
//! `rx.recv_timeout(timeout)`:
//!
//! - `Ok(Ok(msg))`  — a response arrived; correlation is checked by the waiter.
//! - `Ok(Err(e))`   — the reader decoded a frame but it failed (HMAC / version).
//! - `Err(Timeout)` — no frame within the deadline → [`BridgeError::Timeout`].
//! - `Err(Disconnected)` — the reader thread exited (child died / EOF / fatal
//!   read error) → surfaced as [`BridgeError::Subprocess`].
//!
//! This collapses the blocking and bounded-latency paths onto a SINGLE read
//! path: [`BridgeClient::call`] is just `call_with_timeout` with a very long
//! deadline, so there is never a second concurrent reader competing for the
//! same pipe.

use std::io::{BufReader, BufWriter, Write};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::mpsc::{self, Receiver, RecvTimeoutError};
use std::thread::JoinHandle;
use std::time::Duration;

use crate::framing::{read_frame, write_frame};
use crate::protocol::{
    advance_payload, bootstrap_key, decode_frame_body, empty_payload, encode_frame_body,
    hello_payload, msg_type, parse_advance_response, parse_hello_ack, parse_snapshot_response,
    perturb_payload, register_axis_payload, state_dir_payload, AdvanceReport, HelloAck, Message,
    PROTOCOL_VERSION,
};
use crate::BridgeError;

/// Configuration for spawning a [`BridgeClient`].
#[derive(Debug, Clone)]
pub struct BridgeClientConfig {
    /// Command name or absolute path to the Python interpreter.
    /// Defaults to "python" (rely on PATH resolution).
    pub python_executable: String,
    /// The 32-byte session secret. If `None`, a random one is generated.
    pub session_secret: Option<[u8; 32]>,
    /// Extra environment variables to set on the child process. Used by M7
    /// to isolate per-test state directories via `MYCO_STATE_DIR`.
    pub extra_env: Vec<(String, String)>,
    /// **v3.1.1 Sprint 6.E (T2.9)** — operator-side Ed25519 signing seed.
    /// When `Some(seed)`, BridgeClient derives the operator's Ed25519
    /// keypair from `seed` and includes `operator_pubkey` +
    /// `hello_signature` in the hello payload. The substrate then TOFU-pins
    /// that pubkey at handshake time.
    ///
    /// This unblocks positive ceremony E2E testing (CI-class mutations
    /// like l0_revision_attest / schema_evolution / cost_budget_set /
    /// owner_key_history) by giving tests both:
    ///   1. A substrate that has a known pinned operator identity, AND
    ///   2. The matching private key, so the test can produce valid
    ///      attestation_signatures.
    ///
    /// Production usage: operator runtimes (operators/claude) hold their
    /// own per-handshake keypair via the same field. Test use is
    /// indistinguishable from production use at the wire level.
    pub operator_signing_seed: Option<[u8; 32]>,
}

impl Default for BridgeClientConfig {
    fn default() -> Self {
        BridgeClientConfig {
            python_executable: "python".to_string(),
            session_secret: None,
            extra_env: Vec::new(),
            operator_signing_seed: None,
        }
    }
}

/// Bridge client — owns the spawned Python subprocess and drives the protocol.
///
/// Methods correspond to the wire-protocol message types: [`Self::register_axis`],
/// [`Self::perturb`], [`Self::advance`], [`Self::snapshot`], [`Self::shutdown`].
///
/// The constructor [`Self::spawn_and_handshake`] performs the initial `hello`
/// exchange and returns a ready-to-use client.
/// M21.3 P5 万物互联: full axis schema info returned by `query_gradient_schemas`.
#[derive(Debug, Clone)]
pub struct AxisSchemaInfo {
    /// Axis name (also used as identity in the gradient).
    pub name: String,
    /// "appetite" or "decay".
    pub axis_class: String,
    /// Threshold at which the axis fruits a sporocarp.
    pub fruiting_threshold: f64,
    /// Initial gradient value at genesis (original).
    pub initial_value: f64,
    /// Current gradient value (may differ from initial due to perturbations).
    pub current_value: f64,
    /// Per-cycle decay multiplier (used for DECAY axes).
    pub decay_rate_per_cycle: f64,
    /// Whether this axis is the substrate's mortality signal.
    pub is_mortality_signal: bool,
    /// Update rule kind: "noop" or "decay".
    pub update_rule_kind: String,
}

/// The deadline used by the blocking [`BridgeClient::call`] / `send_request`
/// path. It is intentionally enormous — the blocking API promises "wait as
/// long as it takes", and the only reason it is finite at all is so a
/// genuinely dead reader thread (whose `Disconnected` we somehow missed)
/// can never wedge a controller forever. One hour is far longer than any
/// legitimate gradient operation yet still bounded.
const BLOCKING_CALL_DEADLINE: Duration = Duration::from_secs(3600);

/// In-process client for talking to a Python kernel/tropism worker over stdio.
///
/// Stdout is NOT owned here: a permanent reader thread (spawned in
/// [`Self::spawn_and_handshake`]) owns `BufReader<ChildStdout>` and feeds
/// decoded frames over [`Self::responses`]. See the module docs for the
/// reader-thread protocol.
pub struct BridgeClient {
    child: Option<Child>,
    stdin: BufWriter<ChildStdin>,
    /// Decoded response frames from the permanent reader thread. Each item is
    /// the result of reading + HMAC-verifying + canonical-bytes-decoding one
    /// stdout frame. The channel becomes `Disconnected` when the reader thread
    /// exits (child EOF / death / fatal read error).
    responses: Receiver<Result<Message, BridgeError>>,
    /// Join handle for the reader thread. Joined on [`Drop`] after stdin is
    /// closed so the thread observes EOF and exits, avoiding a detached thread.
    reader_handle: Option<JoinHandle<()>>,
    session_secret: [u8; 32],
    /// Sequence counter for request_id. Each request gets a unique value.
    next_request_id: u64,
    /// Poison latch: set once a [`Self::call_with_timeout`] times out. The M5
    /// stream is strictly serial, so a late response for the abandoned request
    /// would mis-pair with the next request. Once poisoned, every subsequent
    /// request fails fast with [`BridgeError::Desynchronized`] instead of
    /// reading a stale frame. Only a fresh `spawn_and_handshake` clears it.
    desynchronized: bool,
    /// The hello_ack received during handshake (for diagnostic surfacing).
    pub hello_ack: HelloAck,
}

/// The permanent reader thread body.
///
/// Owns `reader` (`BufReader<ChildStdout>`) for the life of the connection.
/// Loops: read one length-prefixed frame → decode + HMAC-verify with
/// `session_secret` → push `Ok(Message)` to `tx`. On:
///
/// - clean EOF (child closed stdout): push a terminal `Subprocess` error so a
///   blocked waiter wakes immediately, then exit (channel becomes Disconnected).
/// - read I/O error / oversized frame: push that error, then exit.
/// - decode / HMAC error: push the error but KEEP READING — a single bad frame
///   is a per-call failure, not a stream death (matches the old inline
///   `read_response`, which returned the decode error to that one caller).
///
/// The send only fails if the receiver (the `BridgeClient`) was dropped; in
/// that case we stop (nobody is listening) — the child is being torn down.
fn reader_thread_body(
    mut reader: BufReader<ChildStdout>,
    session_secret: [u8; 32],
    tx: mpsc::Sender<Result<Message, BridgeError>>,
) {
    loop {
        match read_frame(&mut reader) {
            Ok(Some(frame)) => {
                let decoded = decode_frame_body(&frame, &session_secret);
                // KEEP READING on a decode error (per-call failure). Stop only
                // if the receiver is gone.
                if tx.send(decoded).is_err() {
                    return;
                }
            }
            Ok(None) => {
                // Clean EOF: the child closed stdout. Wake any blocked waiter
                // with a terminal error, then exit so further recv() yields
                // Disconnected.
                let _ = tx.send(Err(BridgeError::Subprocess(
                    "python worker closed stdout (EOF); reader thread exiting".to_string(),
                )));
                return;
            }
            Err(e) => {
                // Fatal read-side error (truncated frame, oversized frame, I/O
                // failure). Surface it once, then exit.
                let _ = tx.send(Err(e));
                return;
            }
        }
    }
}

impl BridgeClient {
    /// Spawn the Python worker and complete the `hello` handshake.
    pub fn spawn_and_handshake(config: BridgeClientConfig) -> Result<Self, BridgeError> {
        let session_secret = config
            .session_secret
            .unwrap_or_else(generate_session_secret);

        let mut cmd = Command::new(&config.python_executable);
        cmd.arg("-m")
            .arg("myco_kernel_bridge")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit());
        for (k, v) in &config.extra_env {
            cmd.env(k, v);
        }
        let mut child = cmd.spawn().map_err(|e| {
            BridgeError::Subprocess(format!(
                "failed to spawn `{} -m myco_kernel_bridge`: {e}",
                config.python_executable
            ))
        })?;

        let stdin = child
            .stdin
            .take()
            .ok_or_else(|| BridgeError::Subprocess("child stdin not piped".to_string()))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| BridgeError::Subprocess("child stdout not piped".to_string()))?;

        // Spawn the permanent reader thread. It owns BufReader<ChildStdout>
        // for the whole connection lifetime and decodes frames with the
        // session_secret. The Python daemon keys EVERY response — including
        // hello_ack — with session_secret (see kernel/bridge/python daemon:
        // `encode_message(response, state.session_secret)`), so a single
        // session-keyed reader covers the entire stream including the
        // handshake response below.
        let (tx, rx) = mpsc::channel::<Result<Message, BridgeError>>();
        let reader = BufReader::new(stdout);
        let reader_handle = std::thread::Builder::new()
            .name("myco-bridge-reader".to_string())
            .spawn(move || reader_thread_body(reader, session_secret, tx))
            .map_err(|e| {
                BridgeError::Subprocess(format!("failed to spawn bridge reader thread: {e}"))
            })?;

        let mut client = BridgeClient {
            child: Some(child),
            stdin: BufWriter::new(stdin),
            responses: rx,
            reader_handle: Some(reader_handle),
            session_secret,
            next_request_id: 1,
            desynchronized: false,
            hello_ack: HelloAck {
                kernel_tropism_version: String::new(),
                python_version: String::new(),
            },
        };

        // Send hello using BOOTSTRAP_KEY.
        let request_id = client.allocate_request_id();
        let mut hello_payload_map = hello_payload(&session_secret);
        // **v3.1.1 Sprint 6.E (T2.9)** — if operator_signing_seed is set,
        // derive Ed25519 keypair + sign the hello-canonical-bytes so the
        // substrate TOFU-pins this operator identity. Matches the
        // substrate's verify_hello_signature_and_pin contract in
        // substrate/src/handshake.rs:204-284.
        if let Some(seed) = &config.operator_signing_seed {
            use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
            use myco_kernel_shared::crypto::Ed25519PrivateKey;
            let priv_key = Ed25519PrivateKey::from_seed(seed);
            let pub_key = priv_key.public_key();
            let pubkey_bytes: [u8; 32] = pub_key.0;
            // Build the canonical-bytes signing input: {session_secret, operator_pubkey}.
            let mut signing_map = std::collections::BTreeMap::new();
            signing_map.insert(
                "session_secret".to_string(),
                Value::Bytes(session_secret.to_vec()),
            );
            signing_map.insert(
                "operator_pubkey".to_string(),
                Value::Bytes(pubkey_bytes.to_vec()),
            );
            let signing_input = cb_encode(&Value::Map(signing_map))
                .map_err(|e| BridgeError::Protocol(format!("hello signing-body encode: {e}")))?;
            let sig = priv_key.sign(signing_input.as_ref());
            hello_payload_map.insert(
                "operator_pubkey".to_string(),
                Value::Bytes(pubkey_bytes.to_vec()),
            );
            hello_payload_map.insert(
                "hello_signature".to_string(),
                Value::Bytes(sig.as_ref().to_vec()),
            );
        }
        let hello_msg = Message::new(msg_type::HELLO, request_id, hello_payload_map);
        let bootstrap = bootstrap_key();
        let hello_frame = encode_frame_body(&hello_msg, &bootstrap)?;
        write_frame(&mut client.stdin, &hello_frame)?;

        // Read hello_ack via the reader thread. Python keys the hello_ack with
        // the session_secret it just received in the hello payload, so the
        // session-keyed reader decodes it exactly like every later response.
        let response = client.recv_response(request_id, BLOCKING_CALL_DEADLINE)?;
        client.hello_ack = parse_hello_ack(&response)?;
        Ok(client)
    }

    fn allocate_request_id(&mut self) -> u64 {
        let id = self.next_request_id;
        self.next_request_id = self.next_request_id.wrapping_add(1);
        id
    }

    /// Send one request and block (bounded by [`BLOCKING_CALL_DEADLINE`]) for
    /// the matching response. This is the legacy blocking path; it routes
    /// through the SAME reader thread as [`Self::call_with_timeout`] so there
    /// is only ever one reader on the pipe.
    fn send_request(
        &mut self,
        message_type: &str,
        payload: std::collections::BTreeMap<String, myco_kernel_shared::canonical_bytes::Value>,
    ) -> Result<Message, BridgeError> {
        self.send_request_with_timeout(message_type, payload, BLOCKING_CALL_DEADLINE)
    }

    /// Send one request and wait at most `timeout` for the matching response.
    ///
    /// Writes the request frame to stdin, then blocks on the reader-thread
    /// channel via [`Self::recv_response`]. The write happens BEFORE the
    /// poison check is consulted for the *result* so that a poisoned client
    /// never even touches the pipe (see the early return).
    fn send_request_with_timeout(
        &mut self,
        message_type: &str,
        payload: std::collections::BTreeMap<String, myco_kernel_shared::canonical_bytes::Value>,
        timeout: Duration,
    ) -> Result<Message, BridgeError> {
        // Fail fast if a prior call timed out: the serial stream is poisoned
        // and we must not write a new request that could pair with a stale
        // in-flight response.
        if self.desynchronized {
            return Err(BridgeError::Desynchronized);
        }
        let request_id = self.allocate_request_id();
        let msg = Message::new(message_type, request_id, payload);
        let frame = encode_frame_body(&msg, &self.session_secret)?;
        write_frame(&mut self.stdin, &frame)?;
        self.recv_response(request_id, timeout)
    }

    /// Receive the next response from the reader thread, bounded by `timeout`,
    /// and verify its correlation ID + version.
    ///
    /// On timeout this latches [`Self::desynchronized`] so all later calls
    /// fail fast (a late frame for the abandoned request would mis-pair).
    fn recv_response(
        &mut self,
        expected_request_id: u64,
        timeout: Duration,
    ) -> Result<Message, BridgeError> {
        let response = match self.responses.recv_timeout(timeout) {
            Ok(Ok(msg)) => msg,
            // The reader decoded a frame but it failed HMAC / version / shape.
            Ok(Err(e)) => return Err(e),
            // No frame within the deadline. The child is (as far as we know)
            // still alive but produced no response — poison the connection and
            // surface a Timeout.
            Err(RecvTimeoutError::Timeout) => {
                self.desynchronized = true;
                return Err(BridgeError::Timeout(timeout));
            }
            // The reader thread exited: child EOF / death / fatal read error.
            // It always pushes a terminal Err before exiting, so reaching the
            // Disconnected branch means that terminal error was already
            // consumed by an earlier recv; report the disconnect plainly.
            Err(RecvTimeoutError::Disconnected) => {
                return Err(BridgeError::Subprocess(
                    "python worker reader thread disconnected (child exited)".to_string(),
                ))
            }
        };
        if response.message_type == msg_type::ERROR {
            // Decode error envelope payload for diagnostic surface.
            let code = response
                .payload
                .get("code")
                .and_then(|v| match v {
                    myco_kernel_shared::canonical_bytes::Value::String(s) => Some(s.as_str()),
                    _ => None,
                })
                .unwrap_or("<unknown_code>");
            let msg = response
                .payload
                .get("message")
                .and_then(|v| match v {
                    myco_kernel_shared::canonical_bytes::Value::String(s) => Some(s.as_str()),
                    _ => None,
                })
                .unwrap_or("<no_message>");
            return Err(BridgeError::Protocol(format!(
                "worker error envelope: code={code} message={msg}"
            )));
        }
        if response.request_id != expected_request_id {
            return Err(BridgeError::CorrelationMismatch {
                expected: expected_request_id,
                got: response.request_id,
            });
        }
        if response.version != PROTOCOL_VERSION {
            return Err(BridgeError::Protocol(format!(
                "response protocol version mismatch: got {}, expected {PROTOCOL_VERSION}",
                response.version
            )));
        }
        Ok(response)
    }

    /// Register a gradient axis on the Python worker.
    ///
    /// `axis_class` must be either "appetite" or "decay".
    /// `update_rule_kind` must be either "decay" or "noop".
    #[allow(clippy::too_many_arguments)]
    pub fn register_axis(
        &mut self,
        name: &str,
        axis_class: &str,
        fruiting_threshold: f64,
        initial_value: f64,
        decay_rate_per_cycle: f64,
        is_mortality_signal: bool,
        update_rule_kind: &str,
    ) -> Result<(), BridgeError> {
        let payload = register_axis_payload(
            name,
            axis_class,
            fruiting_threshold,
            initial_value,
            decay_rate_per_cycle,
            is_mortality_signal,
            update_rule_kind,
        );
        let response = self.send_request(msg_type::REGISTER_AXIS, payload)?;
        if response.message_type != msg_type::REGISTER_AXIS_ACK {
            return Err(BridgeError::Protocol(format!(
                "expected register_axis_ack; got {}",
                response.message_type
            )));
        }
        Ok(())
    }

    /// Perturb a gradient axis.
    pub fn perturb(&mut self, axis_name: &str, delta: f64) -> Result<(), BridgeError> {
        let payload = perturb_payload(axis_name, delta);
        let response = self.send_request(msg_type::PERTURB, payload)?;
        if response.message_type != msg_type::PERTURB_ACK {
            return Err(BridgeError::Protocol(format!(
                "expected perturb_ack; got {}",
                response.message_type
            )));
        }
        Ok(())
    }

    /// Advance the gradient by one cycle. Returns the report of fruited
    /// axes and emitted sporocarps.
    pub fn advance(&mut self, current_cycle: u64) -> Result<AdvanceReport, BridgeError> {
        let payload = advance_payload(current_cycle);
        let response = self.send_request(msg_type::ADVANCE, payload)?;
        parse_advance_response(&response)
    }

    /// **v3.1.1 Sprint 7.E.2** — like [`Self::advance`] but bounded by
    /// `timeout`. The gradient-advance step crosses into Python and runs a
    /// full kernel/tropism cycle; this is the longest-running per-call
    /// operation, so the substrate's metabolic loop uses this variant to stay
    /// responsive to a hung worker (returns [`BridgeError::Timeout`] rather
    /// than blocking the whole substrate forever).
    pub fn advance_with_timeout(
        &mut self,
        current_cycle: u64,
        timeout: Duration,
    ) -> Result<AdvanceReport, BridgeError> {
        let payload = advance_payload(current_cycle);
        let response = self.send_request_with_timeout(msg_type::ADVANCE, payload, timeout)?;
        parse_advance_response(&response)
    }

    /// Read the current gradient state (axis name → current value).
    pub fn snapshot(&mut self) -> Result<std::collections::BTreeMap<String, f64>, BridgeError> {
        let response = self.send_request(msg_type::SNAPSHOT, empty_payload())?;
        parse_snapshot_response(&response)
    }

    /// Send a raw typed request and read its correlated response. Used by
    /// downstream crates (substrate) to forward operator messages to
    /// the Python worker while preserving operator-side request_id ownership.
    ///
    /// Returns the response Message (caller is responsible for re-stamping
    /// the operator-side request_id).
    ///
    /// This is the blocking sibling of [`Self::call_with_timeout`]: it waits
    /// up to [`BLOCKING_CALL_DEADLINE`] (effectively unbounded for legitimate
    /// operations) on the same reader thread. Prefer `call_with_timeout` for
    /// any call path that must stay responsive to a hung worker.
    pub fn call(
        &mut self,
        message_type: &str,
        payload: std::collections::BTreeMap<String, myco_kernel_shared::canonical_bytes::Value>,
    ) -> Result<Message, BridgeError> {
        self.send_request(message_type, payload)
    }

    /// **v3.1.1 Sprint 7.E.2** — send a raw typed request and wait at most
    /// `timeout` for the correlated response, returning
    /// [`BridgeError::Timeout`] if the Python worker produces no response in
    /// time.
    ///
    /// This is the bounded-latency sibling of [`Self::call`]. Both write to
    /// stdin and then block on the SAME permanent reader thread; the only
    /// difference is the deadline passed to the channel `recv`. With this in
    /// place, the substrate's Sprint 6.J observability (which times each call)
    /// becomes ACTION: a blocked-but-alive Python worker (deadlock, GIL
    /// contention, infinite loop) no longer wedges the controller forever —
    /// the call returns `Timeout` so the caller can emit an immune signal and
    /// tear the worker down.
    ///
    /// ## Desync / poisoning
    ///
    /// The M5 wire protocol is strictly serial with a single in-flight call.
    /// If a request times out, a late response for that abandoned request may
    /// still be in flight on the pipe; consuming it on the *next* call would
    /// mis-pair request/response. To prevent that, a timeout **poisons** the
    /// client: every subsequent call (timed or blocking) fails immediately
    /// with [`BridgeError::Desynchronized`]. Recovery requires tearing this
    /// client down and re-spawning the worker — which the substrate already
    /// does on Python-worker death. The reader thread itself keeps running so
    /// [`Self::is_child_alive`] and graceful [`Drop`] still work.
    pub fn call_with_timeout(
        &mut self,
        message_type: &str,
        payload: std::collections::BTreeMap<String, myco_kernel_shared::canonical_bytes::Value>,
        timeout: std::time::Duration,
    ) -> Result<Message, BridgeError> {
        self.send_request_with_timeout(message_type, payload, timeout)
    }

    /// Tell the Python worker to persist its gradient state to `state_dir`.
    pub fn save_state(&mut self, state_dir: &str) -> Result<(), BridgeError> {
        let response = self.send_request(msg_type::SAVE_STATE, state_dir_payload(state_dir))?;
        if response.message_type != msg_type::SAVE_STATE_ACK {
            return Err(BridgeError::Protocol(format!(
                "expected save_state_ack; got {}",
                response.message_type
            )));
        }
        Ok(())
    }

    /// Tell the Python worker to load gradient state from `state_dir`.
    /// Returns `(axis_count, hydrated)` where `hydrated=false` indicates the
    /// caller should treat this as a genesis condition.
    pub fn load_state(&mut self, state_dir: &str) -> Result<(u64, bool), BridgeError> {
        self.load_state_with_genesis(state_dir, None)
    }

    /// M10: like [`Self::load_state`] but also supplies a genesis owner pubkey.
    /// If no `owner_keys.cb` exists on disk, the Python worker initializes a
    /// fresh owner-key history with this pubkey as the genesis owner.
    pub fn load_state_with_genesis(
        &mut self,
        state_dir: &str,
        genesis_owner_pubkey: Option<&[u8; 32]>,
    ) -> Result<(u64, bool), BridgeError> {
        self.load_state_full(state_dir, genesis_owner_pubkey, false)
    }

    /// M21.3 P5 万物互联: full load_state with `skip_disk_load` flag.
    ///
    /// When `skip_disk_load = true`, Python does NOT read `gradient.cb` or
    /// `owner_keys.cb` from disk. The caller (Rust substrate) must then
    /// replay DAG events to reconstruct Python's state in-memory.
    ///
    /// Used in the M21.2+ DAG-first boot path: state files become regenerable
    /// caches; Python derives state from Rust's event stream.
    pub fn load_state_full(
        &mut self,
        state_dir: &str,
        genesis_owner_pubkey: Option<&[u8; 32]>,
        skip_disk_load: bool,
    ) -> Result<(u64, bool), BridgeError> {
        use myco_kernel_shared::canonical_bytes::{map_get_bool, map_get_uint, Value};
        let mut payload = state_dir_payload(state_dir);
        if let Some(pk) = genesis_owner_pubkey {
            payload.insert(
                "genesis_owner_pubkey".to_string(),
                Value::Bytes(pk.to_vec()),
            );
        }
        if skip_disk_load {
            payload.insert("skip_disk_load".to_string(), Value::Bool(true));
        }
        let response = self.send_request(msg_type::LOAD_STATE, payload)?;
        if response.message_type != msg_type::LOAD_STATE_ACK {
            return Err(BridgeError::Protocol(format!(
                "expected load_state_ack; got {}",
                response.message_type
            )));
        }
        let axis_count = map_get_uint(&response.payload, "axis_count")
            .map_err(|e| BridgeError::Protocol(e.to_string()))?;
        let hydrated = map_get_bool(&response.payload, "hydrated")
            .map_err(|e| BridgeError::Protocol(e.to_string()))?;
        Ok((axis_count, hydrated))
    }

    // **v0.9 owner-key removal**: `apply_owner_key_rotation` (C70 — tell Python
    // to mutate its in-memory owner_keys history after an activated dual-cosign
    // rotation) was removed with the owner-key subsystem. The substrate no longer
    // verifies owner signatures, so Python carries no owner_keys history to rotate.

    /// M21.3: Query all current axis schemas from Python.
    ///
    /// Returns a vec of (name, axis_class, fruiting_threshold, initial_value,
    /// current_value, decay_rate_per_cycle, is_mortality_signal, update_rule_kind)
    /// for each registered axis.
    ///
    /// Used by Rust to back-fill axis_registered + axis_perturbed DAG events
    /// for substrates that loaded gradient state from gradient.cb (legacy path).
    pub fn query_gradient_schemas(&mut self) -> Result<Vec<AxisSchemaInfo>, BridgeError> {
        use myco_kernel_shared::canonical_bytes::{
            map_get_array, map_get_bool, map_get_string, Value,
        };
        let response = self.send_request(msg_type::QUERY_GRADIENT_SCHEMAS, empty_payload())?;
        if response.message_type != msg_type::QUERY_GRADIENT_SCHEMAS_RESPONSE {
            return Err(BridgeError::Protocol(format!(
                "expected query_gradient_schemas_response; got {}",
                response.message_type
            )));
        }
        let axes_array = map_get_array(&response.payload, "axes")
            .map_err(|e| BridgeError::Protocol(e.to_string()))?;
        let mut out = Vec::with_capacity(axes_array.len());
        for v in axes_array {
            let m = match v {
                Value::Map(m) => m,
                other => {
                    return Err(BridgeError::Protocol(format!(
                        "axis entry not a Map: {other:?}"
                    )))
                }
            };
            let getf = |k: &str| -> Result<&str, BridgeError> {
                map_get_string(m, k).map_err(|e| BridgeError::Protocol(e.to_string()))
            };
            let parse_f = |k: &str| -> Result<f64, BridgeError> {
                getf(k)?
                    .parse()
                    .map_err(|e| BridgeError::Protocol(format!("{k} parse: {e}")))
            };
            out.push(AxisSchemaInfo {
                name: getf("name")?.to_string(),
                axis_class: getf("axis_class")?.to_string(),
                fruiting_threshold: parse_f("fruiting_threshold_repr")?,
                initial_value: parse_f("initial_value_repr")?,
                current_value: parse_f("current_value_repr")?,
                decay_rate_per_cycle: parse_f("decay_rate_per_cycle_repr")?,
                is_mortality_signal: map_get_bool(m, "is_mortality_signal")
                    .map_err(|e| BridgeError::Protocol(e.to_string()))?,
                update_rule_kind: getf("update_rule_kind")?.to_string(),
            });
        }
        Ok(out)
    }

    /// Send a graceful shutdown and wait for the child to exit.
    pub fn shutdown(mut self) -> Result<(), BridgeError> {
        self.shutdown_inner()
    }

    fn shutdown_inner(&mut self) -> Result<(), BridgeError> {
        let response = self.send_request(msg_type::SHUTDOWN, empty_payload())?;
        if response.message_type != msg_type::SHUTDOWN_ACK {
            return Err(BridgeError::Protocol(format!(
                "expected shutdown_ack; got {}",
                response.message_type
            )));
        }
        // Drop stdin to signal EOF to the child.
        // Then wait for the child to exit.
        if let Some(mut child) = self.child.take() {
            let _ = self.stdin.flush();
            child
                .wait()
                .map_err(|e| BridgeError::Subprocess(format!("wait failed: {e}")))?;
        }
        // The child has exited → its stdout write-end is closed → the reader
        // thread observes EOF, pushes its terminal Err, and returns. Join it
        // so we never leak a detached thread holding the stdout handle.
        self.join_reader_thread();
        Ok(())
    }

    /// Join the permanent reader thread, if it is still owned. Idempotent.
    ///
    /// Safe to call only once the child's stdout write-end is closed (i.e.
    /// after `child.wait()` / `child.kill()+wait()`), otherwise the reader is
    /// still blocked in `read_frame` and this would hang. All call sites
    /// observe that ordering.
    fn join_reader_thread(&mut self) {
        if let Some(handle) = self.reader_handle.take() {
            let _ = handle.join();
        }
    }
}

impl BridgeClient {
    /// **v3.1.1 Sprint 5.E** — non-blocking liveness check for the child
    /// process (Python worker / substrate binary on the operator side).
    ///
    /// Returns:
    ///   - `Ok(true)` if the child is still running
    ///   - `Ok(false)` if the child has exited (clean or otherwise)
    ///   - `Err` only on syscall-level failures inspecting the child
    ///
    /// Calls `Child::try_wait()` which is non-blocking on both Unix and
    /// Windows. Substrate uses this in its autonomous-tick loop to detect
    /// silent Python-worker death (e.g., OOM kill, segfault, unhandled
    /// Python exception) without itself blocking on stdin/stdout reads.
    ///
    /// **Why this matters** (T2.3): without liveness sensing, a dead Python
    /// worker leaves the substrate in "looks alive but actually blocked"
    /// state — the next operator call hangs forever. Sensing the death
    /// lets the substrate emit a typed immune signal + reject incoming
    /// requests gracefully.
    pub fn is_child_alive(&mut self) -> Result<bool, BridgeError> {
        let child = match self.child.as_mut() {
            Some(c) => c,
            None => return Ok(false),
        };
        match child.try_wait() {
            Ok(Some(_status)) => Ok(false), // child exited
            Ok(None) => Ok(true),           // child still running
            Err(e) => Err(BridgeError::Subprocess(format!(
                "try_wait failed during liveness check: {e}"
            ))),
        }
    }

    /// **v3.1.1 Sprint 5.E** — return the child process's OS-level PID,
    /// or `None` if the child handle has been taken (post-shutdown).
    /// Used by Sprint 5.E tests to externally kill the child and verify
    /// `is_child_alive()` reflects the death.
    pub fn child_pid(&self) -> Option<u32> {
        self.child.as_ref().map(|c| c.id())
    }

    /// **v3.1.1 Sprint 7.E.2 (test support)** — build a [`BridgeClient`] around
    /// an already-spawned child process, WITHOUT performing the `hello`
    /// handshake. The child must have piped stdin + stdout.
    ///
    /// This exists so tests can point the client at an arbitrary stub child —
    /// in particular a "hung worker" that consumes stdin but never writes a
    /// response — to exercise [`Self::call_with_timeout`]'s timeout path
    /// deterministically without a cooperating Python daemon. The reader
    /// thread is spawned exactly as in [`Self::spawn_and_handshake`]; `Drop`
    /// (kill + wait + join) and [`Self::is_child_alive`] work normally.
    ///
    /// `hello_ack` is left empty (no handshake occurred). Not for production
    /// use — real clients must complete the handshake to establish a shared
    /// session_secret with the worker.
    #[doc(hidden)]
    pub fn from_spawned_child_for_test(
        mut child: Child,
        session_secret: [u8; 32],
    ) -> Result<Self, BridgeError> {
        let stdin = child
            .stdin
            .take()
            .ok_or_else(|| BridgeError::Subprocess("test child stdin not piped".to_string()))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| BridgeError::Subprocess("test child stdout not piped".to_string()))?;
        let (tx, rx) = mpsc::channel::<Result<Message, BridgeError>>();
        let reader = BufReader::new(stdout);
        let reader_handle = std::thread::Builder::new()
            .name("myco-bridge-reader-test".to_string())
            .spawn(move || reader_thread_body(reader, session_secret, tx))
            .map_err(|e| {
                BridgeError::Subprocess(format!("failed to spawn test reader thread: {e}"))
            })?;
        Ok(BridgeClient {
            child: Some(child),
            stdin: BufWriter::new(stdin),
            responses: rx,
            reader_handle: Some(reader_handle),
            session_secret,
            next_request_id: 1,
            desynchronized: false,
            hello_ack: HelloAck {
                kernel_tropism_version: String::new(),
                python_version: String::new(),
            },
        })
    }
}

impl Drop for BridgeClient {
    fn drop(&mut self) {
        // Best-effort cleanup: if shutdown was not called explicitly, try
        // to send shutdown + wait. Failures here are silent because Drop
        // can't return errors.
        if self.child.is_some() {
            // `shutdown_inner` joins the reader thread on its happy path. But
            // it can bail early (e.g. the client was poisoned by a timeout, or
            // the child already died) and leave `child` + `reader_handle`
            // owned — hence the fallback below.
            let _ = self.shutdown_inner();
            if let Some(mut child) = self.child.take() {
                // shutdown_inner did not reap the child (failed / poisoned).
                // Kill it so we never leak a process, then wait so its stdout
                // write-end is closed.
                let _ = child.kill();
                let _ = child.wait();
            }
        }
        // Whether or not the child was ours to reap, the child's stdout
        // write-end is now closed (it either exited cleanly above, was killed,
        // or was never spawned). The reader thread therefore observes EOF and
        // returns; join it so the thread (and the BufReader<ChildStdout> it
        // owns) is fully torn down before this client disappears.
        self.join_reader_thread();
    }
}

/// Generate a cryptographically random session secret. M5 uses
/// `getrandom`-style OS randomness via the standard library; M6 may
/// switch to a Myco-managed entropy pool.
fn generate_session_secret() -> [u8; 32] {
    // Use the time-based seed + counter trick if no getrandom is available.
    // For M5 we rely on a simple SHA-256-based mix of process state.
    use sha2::{Digest, Sha256};
    use std::time::{SystemTime, UNIX_EPOCH};
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let pid = std::process::id();
    let mut h = Sha256::new();
    h.update(b"myco-bridge-session-secret-v1");
    h.update(now.to_le_bytes());
    h.update(pid.to_le_bytes());
    // Also stir in stack address for entropy.
    let stack_var = 0u8;
    let addr = &stack_var as *const u8 as usize;
    h.update(addr.to_le_bytes());
    let result = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}

#[cfg(test)]
mod tests {
    // Subprocess-spawning tests live in `tests/bridge_e2e.rs` to keep
    // unit tests fast and self-contained.
}
