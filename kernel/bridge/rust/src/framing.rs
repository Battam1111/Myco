//! Bridge stdio framing — read/write length-prefixed frames.
//!
//! Frame format:
//!
//! ```text
//!  [u32 BE length, 4 bytes][frame body, length bytes]
//! ```
//!
//! Where the frame body is HMAC (32 bytes) + canonical-bytes body
//! (see [`crate::protocol`]).
//!
//! ## I/O contract
//!
//! - Reads block until a complete frame is received or EOF.
//! - Writes flush after each frame.
//! - Both sides use raw byte streams (no line buffering).
//! - Length is strict u32 big-endian (0 to 4_294_967_295).
//! - Frames larger than [`MAX_FRAME_BODY_SIZE`](crate::protocol::MAX_FRAME_BODY_SIZE)
//!   are rejected as DoS protection.

use std::io::{ErrorKind, Read, Write};

use crate::protocol::MAX_FRAME_BODY_SIZE;
use crate::BridgeError;

/// Read exactly `n` bytes from `stream`. Returns `Ok(None)` on clean EOF
/// (no bytes available), `Err` on mid-read EOF.
fn read_exact_or_eof<R: Read>(stream: &mut R, n: usize) -> Result<Option<Vec<u8>>, BridgeError> {
    if n == 0 {
        return Ok(Some(Vec::new()));
    }
    let mut buf = vec![0u8; n];
    let mut read = 0;
    while read < n {
        match stream.read(&mut buf[read..]) {
            Ok(0) => {
                if read == 0 {
                    return Ok(None); // Clean EOF before any byte.
                }
                return Err(BridgeError::Subprocess(format!(
                    "truncated read: got {} of {} bytes before EOF",
                    read, n
                )));
            }
            Ok(got) => {
                read += got;
            }
            Err(e) if e.kind() == ErrorKind::Interrupted => continue,
            Err(e) => return Err(BridgeError::Io(e)),
        }
    }
    Ok(Some(buf))
}

/// Read one length-prefixed frame from `stream`. Returns:
///
/// - `Ok(Some(body))` — frame body (HMAC + canonical-bytes) without length prefix.
/// - `Ok(None)` — clean EOF between frames.
/// - `Err` — mid-frame EOF, oversized frame, or I/O error.
pub fn read_frame<R: Read>(stream: &mut R) -> Result<Option<Vec<u8>>, BridgeError> {
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
        return Err(BridgeError::FrameTooLarge(format!(
            "incoming frame size {} exceeds cap {}",
            length, MAX_FRAME_BODY_SIZE
        )));
    }
    match read_exact_or_eof(stream, length)? {
        Some(b) => Ok(Some(b)),
        None => Err(BridgeError::Subprocess(
            "EOF after length prefix; no body bytes".to_string(),
        )),
    }
}

/// Write one length-prefixed frame to `stream` and flush.
pub fn write_frame<W: Write>(stream: &mut W, frame_body: &[u8]) -> Result<(), BridgeError> {
    if frame_body.len() > MAX_FRAME_BODY_SIZE {
        return Err(BridgeError::FrameTooLarge(format!(
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
    use std::io::Cursor;

    #[test]
    fn write_then_read_roundtrip() {
        let mut buf: Vec<u8> = Vec::new();
        write_frame(&mut buf, &[1, 2, 3, 4, 5]).unwrap();
        let mut cursor = Cursor::new(buf);
        let body = read_frame(&mut cursor).unwrap().unwrap();
        assert_eq!(body, vec![1, 2, 3, 4, 5]);
    }

    #[test]
    fn read_frame_clean_eof() {
        let mut cursor = Cursor::new(Vec::<u8>::new());
        let result = read_frame(&mut cursor).unwrap();
        assert!(result.is_none());
    }

    #[test]
    fn read_frame_partial_length_prefix_errors() {
        let mut cursor = Cursor::new(vec![0x00, 0x00]); // only 2 of 4 length bytes
        let err = read_frame(&mut cursor).unwrap_err();
        assert!(matches!(err, BridgeError::Subprocess(_)));
    }

    #[test]
    fn read_frame_partial_body_errors() {
        let mut input: Vec<u8> = Vec::new();
        input.extend_from_slice(&10u32.to_be_bytes());
        input.extend_from_slice(b"abc"); // only 3 of 10 body bytes
        let mut cursor = Cursor::new(input);
        let err = read_frame(&mut cursor).unwrap_err();
        assert!(matches!(err, BridgeError::Subprocess(_)));
    }

    #[test]
    fn write_frame_too_large_rejected() {
        let mut buf: Vec<u8> = Vec::new();
        let huge = vec![0u8; MAX_FRAME_BODY_SIZE + 1];
        let err = write_frame(&mut buf, &huge).unwrap_err();
        assert!(matches!(err, BridgeError::FrameTooLarge(_)));
    }

    #[test]
    fn read_frame_too_large_rejected() {
        let mut input: Vec<u8> = Vec::new();
        let huge = (MAX_FRAME_BODY_SIZE as u32) + 1;
        input.extend_from_slice(&huge.to_be_bytes());
        let mut cursor = Cursor::new(input);
        let err = read_frame(&mut cursor).unwrap_err();
        assert!(matches!(err, BridgeError::FrameTooLarge(_)));
    }

    #[test]
    fn write_two_frames_in_sequence() {
        let mut buf: Vec<u8> = Vec::new();
        write_frame(&mut buf, b"alpha").unwrap();
        write_frame(&mut buf, b"beta-frame").unwrap();
        let mut cursor = Cursor::new(buf);
        assert_eq!(read_frame(&mut cursor).unwrap().unwrap(), b"alpha");
        assert_eq!(read_frame(&mut cursor).unwrap().unwrap(), b"beta-frame");
        assert!(read_frame(&mut cursor).unwrap().is_none());
    }
}
