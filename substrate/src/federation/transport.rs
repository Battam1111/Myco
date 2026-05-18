//! M22 P5 万物互联 — federation transport types + frame I/O.
//!
//! ## Layering
//!
//! [`PeerConnection`] wraps one peer's TCP socket + handshake state machine.
//! Frame-level I/O reuses `myco_kernel_bridge::framing::{read_frame, write_frame}`
//! on the underlying `TcpStream` — same wire format as the bridge stdio.
//!
//! ## Blocking discipline
//!
//! - **Outbound dial + initial FED_HELLO roundtrip** (`connect_peer`): blocking
//!   with a TCP connect timeout (5s) + read timeout (5s).
//! - **Polling existing peers** (`federation_poll`): short read timeout
//!   (100ms) per attempt — if no frame is ready, leave the peer for next poll.
//! - **Accept loop** (`accept_pending`): the listener is `set_nonblocking(true)`;
//!   `accept` returns `WouldBlock` immediately when no connection is queued.

use std::io::ErrorKind;
use std::net::{Shutdown, SocketAddr, TcpStream};
use std::time::Duration;

use myco_kernel_bridge::framing::{read_frame, write_frame};
use myco_kernel_bridge::protocol::{decode_frame_body, encode_frame_body, Message};
use myco_kernel_bridge::BridgeError;

/// A federation peer's TCP connection + handshake state.
#[derive(Debug)]
pub struct PeerConnection {
    /// Underlying TCP stream (nonblocking).
    pub stream: TcpStream,

    /// Where in the federation handshake protocol this connection is.
    pub state: PeerConnectionState,

    /// The peer's substrate_id, learned from its FED_HELLO message.
    /// `None` while still in [`PeerConnectionState::AwaitingHello`].
    pub peer_substrate_id: Option<[u8; 32]>,

    /// M25.4: the peer's Ed25519 signing public key, pinned at hello-handshake
    /// time when the peer presented a valid `hello_signature`. Legacy peers
    /// (no signature in their hello) leave this `None` — the peer is
    /// authenticated by TOFU substrate_id only. On reconnect, an established
    /// signer_pubkey must match this pin exactly OR the connection is
    /// rejected as identity drift (C33).
    pub pinned_signer_pubkey: Option<[u8; 32]>,

    /// The peer's remote socket address (informational).
    pub remote_addr: SocketAddr,

    /// Unix-nanosecond timestamp the connection was accepted.
    pub opened_at_unix_ns: i64,
}

/// Federation peer connection state machine.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PeerConnectionState {
    /// Connection just accepted; waiting for incoming FED_HELLO from peer.
    /// The receiver side starts here; the initiator side never enters this
    /// state (the initiator sends HELLO immediately after dial completes).
    AwaitingHello,
    /// FED_HELLO exchange complete; both sides know each other's substrate_id;
    /// HMAC session key is derived. Subsequent frames are authenticated.
    Established,
    /// Connection in error state. The next `federation_poll` will close it.
    Failed,
}

/// Default short-poll read timeout for `federation_poll` (responder side).
pub const POLL_READ_TIMEOUT_MS: u64 = 100;

/// Default TCP connect timeout for outbound `connect_peer` (initiator side).
pub const CONNECT_TIMEOUT_SECS: u64 = 5;

/// Default read timeout for the FED_HELLO_ACK on the initiator side.
pub const HELLO_ACK_READ_TIMEOUT_SECS: u64 = 5;

/// Outbound dial + blocking TCP connect with a 5-second timeout.
///
/// Returns the connected TcpStream + the resolved peer SocketAddr.
pub fn dial_blocking(remote_addr: &str) -> Result<(TcpStream, SocketAddr), BridgeError> {
    let target_addr: SocketAddr = remote_addr.parse().map_err(|e| {
        BridgeError::Protocol(format!("federation dial: invalid addr {remote_addr}: {e}"))
    })?;
    let stream = TcpStream::connect_timeout(&target_addr, Duration::from_secs(CONNECT_TIMEOUT_SECS))
        .map_err(BridgeError::Io)?;
    let peer_addr = stream.peer_addr().map_err(BridgeError::Io)?;
    Ok((stream, peer_addr))
}

/// Send one federation Message over the TCP stream with the given HMAC key.
///
/// Mirrors `kernel/bridge::framing::write_frame` on a TCP socket.
///
/// **M26.2 P11.b**: returns the number of wire bytes written (4-byte length
/// prefix + frame body). Callers that track P11 cost signal #8 (network/cycle)
/// MUST forward this count into `FederationState::record_bytes_egressed` (or
/// equivalent) so the observatory can derive `signal_8_network_per_cycle`.
/// Pre-M26.2 callers that discard the count keep working — the bytes value is
/// just an extra useful return.
pub fn write_fed_frame(
    stream: &mut TcpStream,
    message: &Message,
    hmac_key: &[u8; 32],
) -> Result<usize, BridgeError> {
    let frame = encode_frame_body(message, hmac_key)?;
    let body_len = frame.len();
    write_frame(stream, &frame)?;
    // 4-byte length prefix + frame body. Mirrors kernel/bridge::framing::write_frame.
    Ok(4 + body_len)
}

/// Read one federation Message from the TCP stream with the given HMAC key.
///
/// Caller must `set_read_timeout` before invoking. Returns:
///
/// - `Ok(Some(message))` — frame read successfully and HMAC-verified.
/// - `Ok(None)` — read timed out OR clean EOF before any byte (peer hung up
///   between frames; treat as no-data-yet).
/// - `Err(e)` — protocol error or mid-frame EOF (peer crash); caller should
///   transition peer to `Failed` and close.
pub fn read_fed_frame(
    stream: &mut TcpStream,
    hmac_key: &[u8; 32],
) -> Result<Option<Message>, BridgeError> {
    match read_frame(stream) {
        Ok(Some(frame_body)) => match decode_frame_body(&frame_body, hmac_key) {
            Ok(msg) => Ok(Some(msg)),
            Err(e) => Err(e),
        },
        Ok(None) => Ok(None),
        Err(BridgeError::Io(e))
            if matches!(
                e.kind(),
                ErrorKind::WouldBlock | ErrorKind::TimedOut | ErrorKind::Interrupted
            ) =>
        {
            Ok(None)
        }
        Err(e) => Err(e),
    }
}

/// Best-effort connection shutdown — used when transitioning a peer to
/// `Failed` or closing the federation listener.
pub fn close_stream(stream: &TcpStream) {
    let _ = stream.shutdown(Shutdown::Both);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn peer_connection_state_equality() {
        assert_eq!(
            PeerConnectionState::AwaitingHello,
            PeerConnectionState::AwaitingHello
        );
        assert_ne!(
            PeerConnectionState::AwaitingHello,
            PeerConnectionState::Established
        );
        assert_ne!(
            PeerConnectionState::Established,
            PeerConnectionState::Failed
        );
    }
}
