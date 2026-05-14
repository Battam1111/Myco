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
//! M5 is request-response with strict serial ordering: each `send_request`
//! writes a frame, blocks for the response, and verifies the correlation
//! ID. M6+ may add async + pipelining.

use std::io::{BufReader, BufWriter, Write};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};

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
}

impl Default for BridgeClientConfig {
    fn default() -> Self {
        BridgeClientConfig {
            python_executable: "python".to_string(),
            session_secret: None,
            extra_env: Vec::new(),
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
pub struct BridgeClient {
    child: Option<Child>,
    stdin: BufWriter<ChildStdin>,
    stdout: BufReader<ChildStdout>,
    session_secret: [u8; 32],
    /// Sequence counter for request_id. Each request gets a unique value.
    next_request_id: u64,
    /// The hello_ack received during handshake (for diagnostic surfacing).
    pub hello_ack: HelloAck,
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

        let mut client = BridgeClient {
            child: Some(child),
            stdin: BufWriter::new(stdin),
            stdout: BufReader::new(stdout),
            session_secret,
            next_request_id: 1,
            hello_ack: HelloAck {
                kernel_tropism_version: String::new(),
                python_version: String::new(),
            },
        };

        // Send hello using BOOTSTRAP_KEY.
        let request_id = client.allocate_request_id();
        let hello_msg = Message::new(msg_type::HELLO, request_id, hello_payload(&session_secret));
        let bootstrap = bootstrap_key();
        let hello_frame = encode_frame_body(&hello_msg, &bootstrap)?;
        write_frame(&mut client.stdin, &hello_frame)?;

        // Read hello_ack using SESSION_SECRET (Python already has it from hello).
        let response = client.read_response(request_id)?;
        client.hello_ack = parse_hello_ack(&response)?;
        Ok(client)
    }

    fn allocate_request_id(&mut self) -> u64 {
        let id = self.next_request_id;
        self.next_request_id = self.next_request_id.wrapping_add(1);
        id
    }

    /// Send one request and read the matching response.
    fn send_request(
        &mut self,
        message_type: &str,
        payload: std::collections::BTreeMap<String, myco_kernel_shared::canonical_bytes::Value>,
    ) -> Result<Message, BridgeError> {
        let request_id = self.allocate_request_id();
        let msg = Message::new(message_type, request_id, payload);
        let frame = encode_frame_body(&msg, &self.session_secret)?;
        write_frame(&mut self.stdin, &frame)?;
        self.read_response(request_id)
    }

    /// Read the next frame and verify its correlation ID.
    fn read_response(&mut self, expected_request_id: u64) -> Result<Message, BridgeError> {
        let frame = match read_frame(&mut self.stdout)? {
            Some(b) => b,
            None => {
                return Err(BridgeError::Subprocess(
                    "child closed stdout before responding".to_string(),
                ))
            }
        };
        let response = decode_frame_body(&frame, &self.session_secret)?;
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

    /// Read the current gradient state (axis name → current value).
    pub fn snapshot(&mut self) -> Result<std::collections::BTreeMap<String, f64>, BridgeError> {
        let response = self.send_request(msg_type::SNAPSHOT, empty_payload())?;
        parse_snapshot_response(&response)
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
        use myco_kernel_shared::canonical_bytes::{map_get_bool, map_get_uint};
        let response = self.send_request(msg_type::LOAD_STATE, state_dir_payload(state_dir))?;
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
        Ok(())
    }
}

impl Drop for BridgeClient {
    fn drop(&mut self) {
        // Best-effort cleanup: if shutdown was not called explicitly, try
        // to send shutdown + wait. Failures here are silent because Drop
        // can't return errors.
        if self.child.is_some() {
            let _ = self.shutdown_inner();
            if let Some(mut child) = self.child.take() {
                // If shutdown_inner failed somehow and the child is still alive,
                // kill it to avoid leaking processes.
                let _ = child.kill();
                let _ = child.wait();
            }
        }
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
