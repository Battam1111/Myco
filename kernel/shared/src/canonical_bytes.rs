//! Canonical-bytes serializer (per L0 §9.3 + L1_SCHEMA §3.1).
//!
//! ## Specification
//!
//! Deterministic encoding from typed values to canonical bytes. Identical
//! inputs MUST produce identical outputs across all language implementations
//! (substrate-kernel Rust, operator-bindings per LLM-host, anchor-client TS).
//!
//! ## Encoding
//!
//! TLV (Tag-Length-Value) format with explicit type tags. All multi-byte
//! integers are big-endian.
//!
//! ### Tags
//!
//! | Tag  | Type      | Encoding                                           |
//! |------|-----------|----------------------------------------------------|
//! | 0x00 | Null      | no payload                                         |
//! | 0x01 | Bool      | 1-byte value (0x00 = false, 0x01 = true)           |
//! | 0x10 | Int64     | 8-byte big-endian two's-complement                 |
//! | 0x11 | Uint64    | 8-byte big-endian                                  |
//! | 0x20 | String    | varint length + UTF-8 bytes (no BOM, no escape)    |
//! | 0x21 | Bytes     | varint length + raw bytes                          |
//! | 0x30 | Array     | varint count + N items in declared order           |
//! | 0x31 | Map       | varint count + N (key, value) pairs sorted by canonical-bytes of key |
//! | 0x40 | Timestamp | 8-byte big-endian i64 (unix nanoseconds)           |
//! | 0x41 | Hash      | 32-byte raw (BLAKE3 / SHA-256 fixed length)        |
//!
//! Varint encoding: 7 bits per byte, MSB=1 if more bytes follow, MSB=0 on the
//! last byte. Big-endian within each byte.
//!
//! ### Canonical guarantees
//!
//! - **Deterministic**: same input → identical output bytes.
//! - **Self-describing**: decoder needs no schema (tags carry types).
//! - **Sorted maps**: keys ordered lexicographically by their canonical bytes
//!   (NOT by their string content; canonical bytes are the comparison basis).
//! - **No ambiguity**: each typed value has exactly one canonical encoding.
//! - **No trailing bytes**: a valid canonical-bytes stream has no padding.
//!
//! ## Doctrine traceability
//!
//! - L0 §9.3: canonical-bytes serialization is part of the anchor-surface
//!   doctrine. Substrate emits canonical bytes; anchor-surface client renders
//!   deterministically for owner review.
//! - L1_SCHEMA §3.1: `canonical_bytes_serializer_spec` is part of the
//!   spore-schema (spore-inheritable) AND a tier-1 SSoT field.
//! - L1_HARD_RULES C18: `canonical_bytes_render_drift` (if substrate-side render
//!   differs from anchor-surface render of the same canonical bytes) is a
//!   CRITICAL skin breach.
//!
//! ## M1 implementation status
//!
//! Primitive types (Null, Bool, Int64, Uint64, String, Bytes) + container
//! types (Array, Map) implemented with full encode + tests. Timestamp + Hash
//! tags reserved; encoded as their bytes representations via the primitive types
//! until specific calling conventions land in M2.

use std::collections::BTreeMap;
use thiserror::Error;

/// Canonical-bytes serialization errors.
#[derive(Debug, Error)]
pub enum CanonicalBytesError {
    /// Invalid input: e.g., string that is not valid UTF-8.
    #[error("invalid input: {0}")]
    InvalidInput(String),

    /// Value count exceeded a reasonable limit (denial-of-service protection).
    #[error("value too large: {0}")]
    ValueTooLarge(String),
}

/// Canonical bytes — the deterministic on-the-wire representation.
/// Newtype wrapper to make it impossible to accidentally pass non-canonical bytes
/// where canonical bytes are expected.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CanonicalBytes(pub Vec<u8>);

impl AsRef<[u8]> for CanonicalBytes {
    fn as_ref(&self) -> &[u8] {
        &self.0
    }
}

/// Typed values that can be canonically encoded.
///
/// This is the substrate's typed value system at the serialization boundary.
/// Higher-level domain types (sporocarps, attestation envelopes, etc.) are
/// converted to/from `Value` at the kernel/schema layer.
#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    /// Null / None / missing.
    Null,
    /// Boolean.
    Bool(bool),
    /// Signed 64-bit integer.
    Int(i64),
    /// Unsigned 64-bit integer.
    Uint(u64),
    /// UTF-8 string.
    String(String),
    /// Raw byte sequence.
    Bytes(Vec<u8>),
    /// Ordered array. Items remain in declared order.
    Array(Vec<Value>),
    /// Map with string keys. Keys sorted by canonical-bytes of the key string
    /// (NOT alphabetical by string content; canonical-bytes ordering).
    Map(BTreeMap<String, Value>),
    /// Unix-nanoseconds timestamp.
    Timestamp(i64),
    /// 32-byte hash (e.g., BLAKE3 or SHA-256).
    Hash([u8; 32]),
}

/// Tag bytes.
const TAG_NULL: u8 = 0x00;
const TAG_BOOL: u8 = 0x01;
const TAG_INT: u8 = 0x10;
const TAG_UINT: u8 = 0x11;
const TAG_STRING: u8 = 0x20;
const TAG_BYTES: u8 = 0x21;
const TAG_ARRAY: u8 = 0x30;
const TAG_MAP: u8 = 0x31;
const TAG_TIMESTAMP: u8 = 0x40;
const TAG_HASH: u8 = 0x41;

/// Encode a [`Value`] to canonical bytes.
pub fn encode(value: &Value) -> Result<CanonicalBytes, CanonicalBytesError> {
    let mut buf = Vec::new();
    encode_into(value, &mut buf)?;
    Ok(CanonicalBytes(buf))
}

/// Encode a [`Value`] appending into the given buffer.
fn encode_into(value: &Value, buf: &mut Vec<u8>) -> Result<(), CanonicalBytesError> {
    match value {
        Value::Null => buf.push(TAG_NULL),
        Value::Bool(b) => {
            buf.push(TAG_BOOL);
            buf.push(if *b { 0x01 } else { 0x00 });
        }
        Value::Int(i) => {
            buf.push(TAG_INT);
            buf.extend_from_slice(&i.to_be_bytes());
        }
        Value::Uint(u) => {
            buf.push(TAG_UINT);
            buf.extend_from_slice(&u.to_be_bytes());
        }
        Value::String(s) => {
            buf.push(TAG_STRING);
            write_varint(s.len() as u64, buf);
            buf.extend_from_slice(s.as_bytes());
        }
        Value::Bytes(b) => {
            buf.push(TAG_BYTES);
            write_varint(b.len() as u64, buf);
            buf.extend_from_slice(b);
        }
        Value::Array(items) => {
            buf.push(TAG_ARRAY);
            write_varint(items.len() as u64, buf);
            for item in items {
                encode_into(item, buf)?;
            }
        }
        Value::Map(entries) => {
            // BTreeMap iteration is by Rust string ordering (lexicographic on UTF-8 bytes).
            // For canonical-bytes ordering, we re-sort by the canonical-bytes of each key.
            buf.push(TAG_MAP);
            write_varint(entries.len() as u64, buf);
            let mut sorted: Vec<(&String, &Value)> = entries.iter().collect();
            // Sort by canonical bytes of the key (which is canonical bytes of String(key)).
            // For strings, canonical-bytes ordering happens to match UTF-8 byte ordering
            // because the encoding is TAG_STRING + varint + UTF-8 bytes — and TAG_STRING
            // is constant. Varint encoding of length sorts numerically for equal-length-
            // prefixes; we need to be careful with mixed-length keys. Safer: compute
            // canonical bytes of each key and sort those.
            //
            // M1 implementation: sort by canonical-bytes-of-key-as-Value::String.
            let mut keyed: Vec<(Vec<u8>, &String, &Value)> = Vec::with_capacity(sorted.len());
            for (k, v) in sorted.drain(..) {
                let cb = encode(&Value::String(k.clone()))?;
                keyed.push((cb.0, k, v));
            }
            keyed.sort_by(|a, b| a.0.cmp(&b.0));
            for (key_canonical, _key, val) in keyed.iter() {
                buf.extend_from_slice(key_canonical);
                encode_into(val, buf)?;
            }
        }
        Value::Timestamp(ts) => {
            buf.push(TAG_TIMESTAMP);
            buf.extend_from_slice(&ts.to_be_bytes());
        }
        Value::Hash(h) => {
            buf.push(TAG_HASH);
            buf.extend_from_slice(h);
        }
    }
    Ok(())
}

/// Variable-length integer encoding. 7 bits per byte; MSB=1 if more bytes follow.
fn write_varint(mut n: u64, buf: &mut Vec<u8>) {
    while n >= 0x80 {
        buf.push((n as u8 & 0x7f) | 0x80);
        n >>= 7;
    }
    buf.push(n as u8);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_null() {
        let bytes = encode(&Value::Null).unwrap();
        assert_eq!(bytes.as_ref(), &[0x00]);
    }

    #[test]
    fn test_bool() {
        let bytes_true = encode(&Value::Bool(true)).unwrap();
        let bytes_false = encode(&Value::Bool(false)).unwrap();
        assert_eq!(bytes_true.as_ref(), &[0x01, 0x01]);
        assert_eq!(bytes_false.as_ref(), &[0x01, 0x00]);
    }

    #[test]
    fn test_int_zero() {
        let bytes = encode(&Value::Int(0)).unwrap();
        // tag + 8 bytes of zero
        assert_eq!(bytes.as_ref(), &[0x10, 0, 0, 0, 0, 0, 0, 0, 0]);
    }

    #[test]
    fn test_int_one() {
        let bytes = encode(&Value::Int(1)).unwrap();
        assert_eq!(bytes.as_ref(), &[0x10, 0, 0, 0, 0, 0, 0, 0, 1]);
    }

    #[test]
    fn test_int_negative_one() {
        let bytes = encode(&Value::Int(-1)).unwrap();
        // two's complement of -1 = all 0xff
        assert_eq!(bytes.as_ref(), &[0x10, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]);
    }

    #[test]
    fn test_string_empty() {
        let bytes = encode(&Value::String("".to_string())).unwrap();
        assert_eq!(bytes.as_ref(), &[0x20, 0x00]); // tag + varint(0)
    }

    #[test]
    fn test_string_hello() {
        let bytes = encode(&Value::String("hello".to_string())).unwrap();
        assert_eq!(
            bytes.as_ref(),
            &[0x20, 0x05, b'h', b'e', b'l', b'l', b'o']
        );
    }

    #[test]
    fn test_varint_small() {
        let mut buf = Vec::new();
        write_varint(0, &mut buf);
        assert_eq!(buf, vec![0x00]);

        let mut buf = Vec::new();
        write_varint(127, &mut buf);
        assert_eq!(buf, vec![0x7f]);

        let mut buf = Vec::new();
        write_varint(128, &mut buf);
        assert_eq!(buf, vec![0x80, 0x01]);

        let mut buf = Vec::new();
        write_varint(16384, &mut buf);
        assert_eq!(buf, vec![0x80, 0x80, 0x01]);
    }

    #[test]
    fn test_array_empty() {
        let bytes = encode(&Value::Array(vec![])).unwrap();
        assert_eq!(bytes.as_ref(), &[0x30, 0x00]); // tag + varint(0)
    }

    #[test]
    fn test_array_two_ints() {
        let bytes = encode(&Value::Array(vec![Value::Int(1), Value::Int(2)])).unwrap();
        let expected = vec![
            0x30, 0x02, // array tag + count=2
            0x10, 0, 0, 0, 0, 0, 0, 0, 1, // int(1)
            0x10, 0, 0, 0, 0, 0, 0, 0, 2, // int(2)
        ];
        assert_eq!(bytes.as_ref(), &expected[..]);
    }

    #[test]
    fn test_map_sorted_keys() {
        // Insert keys in non-sorted order; verify output is sorted.
        let mut m = BTreeMap::new();
        m.insert("z".to_string(), Value::Int(1));
        m.insert("a".to_string(), Value::Int(2));
        m.insert("m".to_string(), Value::Int(3));

        let bytes = encode(&Value::Map(m)).unwrap();

        // Map tag + count + (key_canonical + value_canonical) sorted by key_canonical.
        // Keys "a", "m", "z" encoded as String → all length-1 → ordering of the canonical
        // bytes is determined by the string content byte after the length prefix.
        let expected = vec![
            0x31, 0x03, // map tag + count=3
            0x20, 0x01, b'a', 0x10, 0, 0, 0, 0, 0, 0, 0, 2,  // "a" → int(2)
            0x20, 0x01, b'm', 0x10, 0, 0, 0, 0, 0, 0, 0, 3,  // "m" → int(3)
            0x20, 0x01, b'z', 0x10, 0, 0, 0, 0, 0, 0, 0, 1,  // "z" → int(1)
        ];
        assert_eq!(bytes.as_ref(), &expected[..]);
    }

    #[test]
    fn test_determinism_property() {
        // Property: encoding the same value twice gives identical bytes.
        let v = Value::Map({
            let mut m = BTreeMap::new();
            m.insert("a".to_string(), Value::Bool(true));
            m.insert("b".to_string(), Value::Int(42));
            m.insert("c".to_string(), Value::Array(vec![Value::Null, Value::String("x".to_string())]));
            m
        });
        let bytes1 = encode(&v).unwrap();
        let bytes2 = encode(&v).unwrap();
        assert_eq!(bytes1, bytes2);
    }

    #[test]
    fn test_timestamp() {
        let bytes = encode(&Value::Timestamp(1_700_000_000_000_000_000)).unwrap();
        let mut expected = vec![0x40];
        expected.extend_from_slice(&1_700_000_000_000_000_000_i64.to_be_bytes());
        assert_eq!(bytes.as_ref(), &expected[..]);
    }

    #[test]
    fn test_hash() {
        let h = [0xab; 32];
        let bytes = encode(&Value::Hash(h)).unwrap();
        let mut expected = vec![0x41];
        expected.extend_from_slice(&h);
        assert_eq!(bytes.as_ref(), &expected[..]);
    }
}
