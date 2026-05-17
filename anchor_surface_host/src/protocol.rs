//! Anchor surface host wire protocol — canonical-bytes envelopes over local TCP.
//!
//! ## Wire format
//!
//! Each on-the-wire frame is:
//!
//! ```text
//!  [u32 BE length, 4 bytes][canonical-bytes Map envelope, length bytes]
//! ```
//!
//! No HMAC at M-anchor-1 (localhost-only binding + 0600 port-discovery file
//! is the interim defense). M-anchor-1.5 adds a per-session HMAC key written
//! into the discovery file.
//!
//! ## Envelope shape
//!
//! Every message is a canonical-bytes Map with a `type` string key
//! discriminating between request types:
//!
//! ```text
//! GetPubkeyRequest:  Map({"type": "get_pubkey"})
//! GetPubkeyResponse: Map({"pubkey": Bytes(32)})
//!
//! SignRequest:       Map({"type": "sign", "message": Bytes(N)})
//! SignResponse:      Map({"signature": Bytes(64)})
//!
//! PingRequest:       Map({"type": "ping"})
//! PingResponse:      Map({"ok": Bool(true)})
//!
//! ErrorResponse:     Map({"error": String(message)})
//! ```
//!
//! Responses carry only the response-shaped keys (no `type` discriminator) so
//! that decoding logic on the operator side maps cleanly to each request type.

use std::collections::BTreeMap;
use std::io::{ErrorKind, Read, Write};
use std::net::TcpStream;

use myco_kernel_shared::canonical_bytes::{
    decode, encode, map_get_bool, map_get_bytes, map_get_string, Value,
};

use crate::HostError;

/// Maximum frame body size on the wire (1 MiB). DoS protection consistent
/// with `myco_kernel_bridge::protocol::MAX_FRAME_BODY_SIZE`.
pub const MAX_FRAME_BODY_SIZE: usize = 1024 * 1024;

/// Request types accepted by the anchor surface host.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Request {
    /// Return the 32-byte owner public key.
    GetPubkey,
    /// Sign the supplied message bytes; return the 64-byte Ed25519 signature.
    Sign {
        /// Bytes to sign with the owner's Ed25519 private key.
        message: Vec<u8>,
    },
    /// Liveness check; expect `PingResponse { ok: true }`.
    Ping,
}

impl Request {
    /// Encode this request as canonical bytes.
    pub fn encode(&self) -> Result<Vec<u8>, HostError> {
        let mut m = BTreeMap::new();
        match self {
            Request::GetPubkey => {
                m.insert("type".to_string(), Value::String("get_pubkey".to_string()));
            }
            Request::Sign { message } => {
                m.insert("type".to_string(), Value::String("sign".to_string()));
                m.insert("message".to_string(), Value::Bytes(message.clone()));
            }
            Request::Ping => {
                m.insert("type".to_string(), Value::String("ping".to_string()));
            }
        }
        Ok(encode(&Value::Map(m))?.0)
    }

    /// Decode a request from canonical bytes.
    pub fn decode(bytes: &[u8]) -> Result<Self, HostError> {
        let decoded = decode(bytes)?;
        let map = match decoded {
            Value::Map(m) => m,
            other => {
                return Err(HostError::Protocol(format!(
                    "request root is not a Map: {other:?}"
                )))
            }
        };
        let type_str = map_get_string(&map, "type")?;
        match type_str {
            "get_pubkey" => Ok(Request::GetPubkey),
            "sign" => {
                let msg = map_get_bytes(&map, "message")?.to_vec();
                Ok(Request::Sign { message: msg })
            }
            "ping" => Ok(Request::Ping),
            other => Err(HostError::Protocol(format!(
                "unknown request type {other}"
            ))),
        }
    }
}

/// Response types emitted by the anchor surface host.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Response {
    /// 32-byte Ed25519 public key.
    Pubkey {
        /// The owner's 32-byte Ed25519 public key bytes.
        pubkey: [u8; 32],
    },
    /// 64-byte Ed25519 signature.
    Signature {
        /// The 64-byte Ed25519 signature over the requested message.
        signature: [u8; 64],
    },
    /// Ping reply.
    Pong,
    /// Error reply (substituted for any of the above when the host failed
    /// to process the request).
    Error {
        /// Human-readable error description.
        message: String,
    },
}

impl Response {
    /// Encode this response as canonical bytes.
    pub fn encode(&self) -> Result<Vec<u8>, HostError> {
        let mut m = BTreeMap::new();
        match self {
            Response::Pubkey { pubkey } => {
                m.insert("pubkey".to_string(), Value::Bytes(pubkey.to_vec()));
            }
            Response::Signature { signature } => {
                m.insert("signature".to_string(), Value::Bytes(signature.to_vec()));
            }
            Response::Pong => {
                m.insert("ok".to_string(), Value::Bool(true));
            }
            Response::Error { message } => {
                m.insert("error".to_string(), Value::String(message.clone()));
            }
        }
        Ok(encode(&Value::Map(m))?.0)
    }

    /// Decode a response from canonical bytes. The caller knows which
    /// shape it expects (Pubkey vs Signature vs Pong), so this returns the
    /// concrete variant matched by inspecting keys present in the Map.
    pub fn decode(bytes: &[u8]) -> Result<Self, HostError> {
        let decoded = decode(bytes)?;
        let map = match decoded {
            Value::Map(m) => m,
            other => {
                return Err(HostError::Protocol(format!(
                    "response root is not a Map: {other:?}"
                )))
            }
        };
        if let Ok(err) = map_get_string(&map, "error") {
            return Ok(Response::Error {
                message: err.to_string(),
            });
        }
        if let Ok(pk) = map_get_bytes(&map, "pubkey") {
            if pk.len() != 32 {
                return Err(HostError::Protocol(format!(
                    "pubkey length {} != 32",
                    pk.len()
                )));
            }
            let mut arr = [0u8; 32];
            arr.copy_from_slice(pk);
            return Ok(Response::Pubkey { pubkey: arr });
        }
        if let Ok(sig) = map_get_bytes(&map, "signature") {
            if sig.len() != 64 {
                return Err(HostError::Protocol(format!(
                    "signature length {} != 64",
                    sig.len()
                )));
            }
            let mut arr = [0u8; 64];
            arr.copy_from_slice(sig);
            return Ok(Response::Signature { signature: arr });
        }
        if let Ok(true) = map_get_bool(&map, "ok") {
            return Ok(Response::Pong);
        }
        Err(HostError::Protocol(
            "response Map missing recognized key (pubkey/signature/ok/error)".to_string(),
        ))
    }
}

// ---------------------------------------------------------------------------
// Frame I/O — length-prefixed canonical-bytes envelopes over TCP.
// ---------------------------------------------------------------------------

/// Read exactly `n` bytes from `stream`. Returns `Ok(None)` on clean EOF;
/// `Err` on mid-read EOF / I/O error.
fn read_exact_or_eof(stream: &mut TcpStream, n: usize) -> Result<Option<Vec<u8>>, HostError> {
    if n == 0 {
        return Ok(Some(Vec::new()));
    }
    let mut buf = vec![0u8; n];
    let mut read = 0;
    while read < n {
        match stream.read(&mut buf[read..]) {
            Ok(0) => {
                if read == 0 {
                    return Ok(None);
                }
                return Err(HostError::Protocol(format!(
                    "truncated read: got {} of {} bytes before EOF",
                    read, n
                )));
            }
            Ok(got) => {
                read += got;
            }
            Err(e) if e.kind() == ErrorKind::Interrupted => continue,
            Err(e) => return Err(HostError::Io(e)),
        }
    }
    Ok(Some(buf))
}

/// Read one length-prefixed frame from `stream`. Returns:
///
/// - `Ok(Some(body))` — frame body (canonical-bytes envelope) without length prefix.
/// - `Ok(None)` — clean EOF between frames.
/// - `Err` — mid-frame EOF, oversized frame, or I/O error.
pub fn read_frame(stream: &mut TcpStream) -> Result<Option<Vec<u8>>, HostError> {
    let length_bytes = match read_exact_or_eof(stream, 4)? {
        Some(b) => b,
        None => return Ok(None),
    };
    let length = u32::from_be_bytes([
        length_bytes[0],
        length_bytes[1],
        length_bytes[2],
        length_bytes[3],
    ]) as usize;
    if length > MAX_FRAME_BODY_SIZE {
        return Err(HostError::Protocol(format!(
            "incoming frame size {} exceeds cap {}",
            length, MAX_FRAME_BODY_SIZE
        )));
    }
    match read_exact_or_eof(stream, length)? {
        Some(b) => Ok(Some(b)),
        None => Err(HostError::Protocol(
            "EOF after length prefix; no body bytes".to_string(),
        )),
    }
}

/// Write one length-prefixed frame to `stream` and flush.
pub fn write_frame(stream: &mut TcpStream, frame_body: &[u8]) -> Result<(), HostError> {
    if frame_body.len() > MAX_FRAME_BODY_SIZE {
        return Err(HostError::Protocol(format!(
            "outgoing frame size {} exceeds cap {}",
            frame_body.len(),
            MAX_FRAME_BODY_SIZE
        )));
    }
    let length = frame_body.len() as u32;
    stream.write_all(&length.to_be_bytes())?;
    stream.write_all(frame_body)?;
    stream.flush()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn request_get_pubkey_roundtrip() {
        let req = Request::GetPubkey;
        let bytes = req.encode().unwrap();
        let decoded = Request::decode(&bytes).unwrap();
        assert_eq!(decoded, req);
    }

    #[test]
    fn request_sign_roundtrip() {
        let req = Request::Sign {
            message: vec![1, 2, 3, 4, 5],
        };
        let bytes = req.encode().unwrap();
        let decoded = Request::decode(&bytes).unwrap();
        assert_eq!(decoded, req);
    }

    #[test]
    fn request_ping_roundtrip() {
        let req = Request::Ping;
        let bytes = req.encode().unwrap();
        let decoded = Request::decode(&bytes).unwrap();
        assert_eq!(decoded, req);
    }

    #[test]
    fn response_pubkey_roundtrip() {
        let resp = Response::Pubkey { pubkey: [0xaa; 32] };
        let bytes = resp.encode().unwrap();
        let decoded = Response::decode(&bytes).unwrap();
        assert_eq!(decoded, resp);
    }

    #[test]
    fn response_signature_roundtrip() {
        let resp = Response::Signature {
            signature: [0xcc; 64],
        };
        let bytes = resp.encode().unwrap();
        let decoded = Response::decode(&bytes).unwrap();
        assert_eq!(decoded, resp);
    }

    #[test]
    fn response_pong_roundtrip() {
        let resp = Response::Pong;
        let bytes = resp.encode().unwrap();
        let decoded = Response::decode(&bytes).unwrap();
        assert_eq!(decoded, resp);
    }

    #[test]
    fn response_error_roundtrip() {
        let resp = Response::Error {
            message: "kaboom".to_string(),
        };
        let bytes = resp.encode().unwrap();
        let decoded = Response::decode(&bytes).unwrap();
        assert_eq!(decoded, resp);
    }

    #[test]
    fn request_decode_rejects_unknown_type() {
        let mut m = BTreeMap::new();
        m.insert("type".to_string(), Value::String("nope".to_string()));
        let bytes = encode(&Value::Map(m)).unwrap().0;
        let err = Request::decode(&bytes).unwrap_err();
        match err {
            HostError::Protocol(msg) => assert!(msg.contains("nope")),
            other => panic!("expected protocol error, got {other:?}"),
        }
    }

    #[test]
    fn response_decode_rejects_unknown_shape() {
        let mut m = BTreeMap::new();
        m.insert("random".to_string(), Value::Int(42));
        let bytes = encode(&Value::Map(m)).unwrap().0;
        let err = Response::decode(&bytes).unwrap_err();
        match err {
            HostError::Protocol(msg) => assert!(msg.contains("missing recognized key")),
            other => panic!("expected protocol error, got {other:?}"),
        }
    }

    #[test]
    fn response_decode_rejects_wrong_pubkey_length() {
        let mut m = BTreeMap::new();
        m.insert("pubkey".to_string(), Value::Bytes(vec![1, 2, 3])); // not 32
        let bytes = encode(&Value::Map(m)).unwrap().0;
        let err = Response::decode(&bytes).unwrap_err();
        match err {
            HostError::Protocol(msg) => assert!(msg.contains("32")),
            other => panic!("expected protocol error, got {other:?}"),
        }
    }
}
