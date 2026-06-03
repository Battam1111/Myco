//! Canonical-bytes serializer (per L0/cards/AS_anchor_surface §3 + L1/SCHEMA §3.1).
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
//! - L0/cards/AS_anchor_surface §3: canonical-bytes serialization is part of the anchor-surface
//!   doctrine. Substrate emits canonical bytes; anchor-surface client renders
//!   deterministically for owner review.
//! - L1/SCHEMA §3.1: `canonical_bytes_serializer_spec` is part of the
//!   spore-schema (spore-inheritable) AND a tier-1 SSoT field.
//! - L1/HARD_RULES C18: `canonical_bytes_render_drift` (if substrate-side render
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
#[derive(Debug, Error, PartialEq, Eq)]
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

// ---------------------------------------------------------------------------
// Decoder — reverse of encode. Added at M5 to support the cross-process
// bridge (kernel/bridge) which needs to decode canonical-bytes frames
// arriving from the Python worker over stdio.
// ---------------------------------------------------------------------------

/// Read a varint from `buf` starting at `offset`. Returns `(value, new_offset)`.
fn read_varint(buf: &[u8], offset: usize) -> Result<(u64, usize), CanonicalBytesError> {
    let mut result: u64 = 0;
    let mut shift: u32 = 0;
    let mut cur = offset;
    for _ in 0..10 {
        if cur >= buf.len() {
            return Err(CanonicalBytesError::InvalidInput(
                "varint truncated".to_string(),
            ));
        }
        let byte = buf[cur];
        cur += 1;
        result |= ((byte & 0x7f) as u64) << shift;
        if byte & 0x80 == 0 {
            return Ok((result, cur));
        }
        shift += 7;
    }
    Err(CanonicalBytesError::InvalidInput(
        "varint too long (>10 bytes)".to_string(),
    ))
}

/// Decode canonical bytes into a [`Value`] tree.
///
/// Inverse of [`encode`]: `encode(&decode(b)?).unwrap() == b` for any
/// canonical bytes produced by `encode`. Drift between any implementation's
/// `decode` and any other's `encode` = L1/HARD_RULES C18.
pub fn decode(buf: &[u8]) -> Result<Value, CanonicalBytesError> {
    let (value, cursor) = decode_into(buf, 0)?;
    if cursor != buf.len() {
        return Err(CanonicalBytesError::InvalidInput(format!(
            "trailing bytes after decode: consumed {}/{}",
            cursor,
            buf.len()
        )));
    }
    Ok(value)
}

fn decode_into(buf: &[u8], offset: usize) -> Result<(Value, usize), CanonicalBytesError> {
    if offset >= buf.len() {
        return Err(CanonicalBytesError::InvalidInput(
            "decode: input truncated".to_string(),
        ));
    }
    let tag = buf[offset];
    let mut cursor = offset + 1;

    match tag {
        TAG_NULL => Ok((Value::Null, cursor)),
        TAG_BOOL => {
            if cursor >= buf.len() {
                return Err(CanonicalBytesError::InvalidInput(
                    "decode: bool payload truncated".to_string(),
                ));
            }
            let b = buf[cursor];
            if b != 0x00 && b != 0x01 {
                return Err(CanonicalBytesError::InvalidInput(format!(
                    "decode: invalid bool byte {b:#x}"
                )));
            }
            Ok((Value::Bool(b == 0x01), cursor + 1))
        }
        TAG_INT => {
            if cursor + 8 > buf.len() {
                return Err(CanonicalBytesError::InvalidInput(
                    "decode: int payload truncated".to_string(),
                ));
            }
            let arr: [u8; 8] = buf[cursor..cursor + 8].try_into().expect("size 8");
            Ok((Value::Int(i64::from_be_bytes(arr)), cursor + 8))
        }
        TAG_UINT => {
            if cursor + 8 > buf.len() {
                return Err(CanonicalBytesError::InvalidInput(
                    "decode: uint payload truncated".to_string(),
                ));
            }
            let arr: [u8; 8] = buf[cursor..cursor + 8].try_into().expect("size 8");
            Ok((Value::Uint(u64::from_be_bytes(arr)), cursor + 8))
        }
        TAG_STRING => {
            let (length, c2) = read_varint(buf, cursor)?;
            cursor = c2;
            let length = length as usize;
            if cursor + length > buf.len() {
                return Err(CanonicalBytesError::InvalidInput(
                    "decode: string payload truncated".to_string(),
                ));
            }
            let raw = &buf[cursor..cursor + length];
            let text = std::str::from_utf8(raw)
                .map_err(|e| {
                    CanonicalBytesError::InvalidInput(format!("decode: invalid utf-8: {e}"))
                })?
                .to_string();
            Ok((Value::String(text), cursor + length))
        }
        TAG_BYTES => {
            let (length, c2) = read_varint(buf, cursor)?;
            cursor = c2;
            let length = length as usize;
            if cursor + length > buf.len() {
                return Err(CanonicalBytesError::InvalidInput(
                    "decode: bytes payload truncated".to_string(),
                ));
            }
            Ok((
                Value::Bytes(buf[cursor..cursor + length].to_vec()),
                cursor + length,
            ))
        }
        TAG_ARRAY => {
            let (count, c2) = read_varint(buf, cursor)?;
            cursor = c2;
            // DoS guard: every array item is >= 1 byte (at minimum a tag byte), so
            // an array of `count` items requires >= `count` bytes remaining. Reject
            // + bound the allocation BEFORE `with_capacity`, so a tiny hostile or
            // corrupt frame (e.g. a 12-byte body claiming count=2^48) cannot request
            // a multi-TiB allocation and abort the process. Wires the long-defined-
            // but-unused `ValueTooLarge` guard.
            let remaining = buf.len().saturating_sub(cursor) as u64;
            if count > remaining {
                return Err(CanonicalBytesError::ValueTooLarge(format!(
                    "array count {count} exceeds remaining input {remaining} bytes"
                )));
            }
            let mut items: Vec<Value> = Vec::with_capacity(count as usize);
            for _ in 0..count {
                let (item, c3) = decode_into(buf, cursor)?;
                items.push(item);
                cursor = c3;
            }
            Ok((Value::Array(items), cursor))
        }
        TAG_MAP => {
            let (count, c2) = read_varint(buf, cursor)?;
            cursor = c2;
            // DoS guard (symmetry with TAG_ARRAY): each map entry is >= 2 bytes
            // (a key value + a mapped value), so `count` cannot exceed the remaining
            // input. Bounds the per-entry loop on hostile/corrupt input.
            let remaining = buf.len().saturating_sub(cursor) as u64;
            if count > remaining {
                return Err(CanonicalBytesError::ValueTooLarge(format!(
                    "map count {count} exceeds remaining input {remaining} bytes"
                )));
            }
            let mut entries: BTreeMap<String, Value> = BTreeMap::new();
            let mut prev_key_bytes: Option<Vec<u8>> = None;
            for _ in 0..count {
                let key_start = cursor;
                let (key_value, key_end) = decode_into(buf, cursor)?;
                let key_string = match key_value {
                    Value::String(s) => s,
                    other => {
                        return Err(CanonicalBytesError::InvalidInput(format!(
                            "decode: map key is not String: {other:?}"
                        )))
                    }
                };
                let key_canonical = buf[key_start..key_end].to_vec();
                if let Some(prev) = &prev_key_bytes {
                    if &key_canonical <= prev {
                        return Err(CanonicalBytesError::InvalidInput(
                            "decode: map keys not in strict canonical order".to_string(),
                        ));
                    }
                }
                prev_key_bytes = Some(key_canonical);
                let (val, c3) = decode_into(buf, key_end)?;
                entries.insert(key_string, val);
                cursor = c3;
            }
            Ok((Value::Map(entries), cursor))
        }
        TAG_TIMESTAMP => {
            if cursor + 8 > buf.len() {
                return Err(CanonicalBytesError::InvalidInput(
                    "decode: timestamp payload truncated".to_string(),
                ));
            }
            let arr: [u8; 8] = buf[cursor..cursor + 8].try_into().expect("size 8");
            Ok((Value::Timestamp(i64::from_be_bytes(arr)), cursor + 8))
        }
        TAG_HASH => {
            if cursor + 32 > buf.len() {
                return Err(CanonicalBytesError::InvalidInput(
                    "decode: hash payload truncated".to_string(),
                ));
            }
            let arr: [u8; 32] = buf[cursor..cursor + 32].try_into().expect("size 32");
            Ok((Value::Hash(arr), cursor + 32))
        }
        _ => Err(CanonicalBytesError::InvalidInput(format!(
            "decode: unknown tag {tag:#x}"
        ))),
    }
}

/// Helper: extract a String value from a Map by key.
pub fn map_get_string<'a>(
    map: &'a BTreeMap<String, Value>,
    key: &str,
) -> Result<&'a str, CanonicalBytesError> {
    match map.get(key) {
        Some(Value::String(s)) => Ok(s.as_str()),
        Some(other) => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_string({key}): not a String: {other:?}"
        ))),
        None => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_string({key}): missing key"
        ))),
    }
}

/// Helper: extract a Uint value from a Map by key.
pub fn map_get_uint(map: &BTreeMap<String, Value>, key: &str) -> Result<u64, CanonicalBytesError> {
    match map.get(key) {
        Some(Value::Uint(n)) => Ok(*n),
        Some(other) => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_uint({key}): not a Uint: {other:?}"
        ))),
        None => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_uint({key}): missing key"
        ))),
    }
}

/// Helper: extract a Bytes value from a Map by key.
pub fn map_get_bytes<'a>(
    map: &'a BTreeMap<String, Value>,
    key: &str,
) -> Result<&'a [u8], CanonicalBytesError> {
    match map.get(key) {
        Some(Value::Bytes(b)) => Ok(b.as_slice()),
        Some(other) => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_bytes({key}): not a Bytes: {other:?}"
        ))),
        None => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_bytes({key}): missing key"
        ))),
    }
}

/// Helper: extract a Map value from a Map by key.
pub fn map_get_map<'a>(
    map: &'a BTreeMap<String, Value>,
    key: &str,
) -> Result<&'a BTreeMap<String, Value>, CanonicalBytesError> {
    match map.get(key) {
        Some(Value::Map(m)) => Ok(m),
        Some(other) => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_map({key}): not a Map: {other:?}"
        ))),
        None => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_map({key}): missing key"
        ))),
    }
}

/// Helper: extract an Array value from a Map by key.
pub fn map_get_array<'a>(
    map: &'a BTreeMap<String, Value>,
    key: &str,
) -> Result<&'a [Value], CanonicalBytesError> {
    match map.get(key) {
        Some(Value::Array(a)) => Ok(a.as_slice()),
        Some(other) => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_array({key}): not an Array: {other:?}"
        ))),
        None => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_array({key}): missing key"
        ))),
    }
}

/// Helper: extract a Bool value from a Map by key.
pub fn map_get_bool(map: &BTreeMap<String, Value>, key: &str) -> Result<bool, CanonicalBytesError> {
    match map.get(key) {
        Some(Value::Bool(b)) => Ok(*b),
        Some(other) => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_bool({key}): not a Bool: {other:?}"
        ))),
        None => Err(CanonicalBytesError::InvalidInput(format!(
            "map_get_bool({key}): missing key"
        ))),
    }
}

// ---------------------------------------------------------------------------
// Float rendering — the canonical wire form for f64.
// ---------------------------------------------------------------------------

/// Render an `f64` as its canonical-bytes wire string: the exact CPython
/// `repr(float)` of the value.
///
/// ## Why floats are strings
///
/// The canonical-bytes [`Value`] type has **no float tag**. Floats are encoded
/// upstream as `Value::String(float_repr(x))` (a tag-`0x20` String), because a
/// raw IEEE-754 byte encoding has cross-language reproducibility hazards (NaN
/// payload bits, signaling bits, endianness of the significand). Round-tripping
/// through the *shortest decimal string that recovers the same f64* sidesteps
/// all of that: every language parses the same string back to the same double.
///
/// ## The oracle
///
/// The original producer of these strings is the Python kernel, which calls the
/// bare builtin `repr()`. **CPython `repr(float)` is therefore the canonical
/// oracle**, and this function reproduces it byte-for-byte. The Rust substrate,
/// the Rust bridge controller, and the TypeScript operator all delegate to (or
/// mirror) this routine. Any divergence is the float facet of
/// L1/HARD_RULES **C18** `canonical_bytes_render_drift` (CRITICAL).
///
/// Cross-language parity is pinned by the `float_vectors` array in
/// `test_vectors/canonical_bytes_v1.json` (consumed by the Rust, Python, and
/// TypeScript parity suites).
///
/// ## The algorithm (= CPython `repr`)
///
/// CPython `repr(float)` is *"the shortest decimal string that round-trips to
/// the same f64 under round-to-nearest-**even**"*, formatted with these rules:
///
/// - **Notation**: exponential iff the decimal exponent `x` (where the value is
///   `d.ddd x 10^x`) satisfies `x < -4` **or** `x >= 16`; otherwise positional.
/// - **Positional, integer-valued** (no fractional digits) gets a trailing
///   `.0` (`1.0`, `100.0`, `1000000000000000.0`).
/// - **Exponential**: `d[.ddd]` then `e`, then the exponent sign — **always**
///   present (`e+` / `e-`) — then the exponent magnitude **zero-padded to at
///   least 2 digits** (`1e-05`, `1e+16`, `1.5e+300`).
/// - **`-0.0`** renders with its sign preserved.
/// - **Non-finite**: `nan`, `inf`, `-inf` (these are rejected as divergence
///   upstream before serialization, but the branch is defined and pinned).
///
/// ## Why fixed-precision, not `{}` / `{:e}`
///
/// Rust's *shortest* float formatters (`{}` and `{:e}`) emit the correct
/// shortest **digits** but break exact midpoint ties by rounding **half-away**,
/// whereas CPython rounds **half-to-even**. (Example: the f64 nearest
/// `1340492803849185.25` renders as `...85.2` under CPython but `...85.3` under
/// Rust's shortest.) Rust's *fixed-precision* formatter `{:.p e}` **does** round
/// half-to-even — matching CPython — so we find the smallest precision `p` whose
/// round-to-even rendering recovers the input, then reformat per the rules
/// above. This reproduces CPython on every f64 (verified by fuzzing millions of
/// values against `repr`), including the tie cases that the native shortest
/// formatter gets "wrong" for our cross-language purpose.
///
/// `p` is bounded by 17 (no f64 needs more than 17 significant digits), so this
/// performs at most 18 format-and-parse probes; `float_repr` is only invoked at
/// event-encoding time, not in any hot inner loop.
pub fn float_repr(f: f64) -> String {
    if f.is_nan() {
        return "nan".to_string();
    }
    if f.is_infinite() {
        return if f > 0.0 {
            "inf".to_string()
        } else {
            "-inf".to_string()
        };
    }
    // Sign captured via the sign bit so `-0.0` is distinguishable from `0.0`
    // (`f == 0.0` is true for both).
    let negative = f.is_sign_negative();
    let abs = f.abs();
    if abs == 0.0 {
        return if negative {
            "-0.0".to_string()
        } else {
            "0.0".to_string()
        };
    }

    let (digits, exp) = shortest_round_to_even_digits(abs);
    // Mirror CPython's documented rule verbatim ("exponential iff x < -4 or
    // x >= 16") rather than clippy's `!(-4..16).contains(&exp)` rewrite, which
    // obscures the doctrine condition this line is meant to encode.
    #[allow(clippy::manual_range_contains)]
    let body = if exp < -4 || exp >= 16 {
        render_exponential(&digits, exp)
    } else {
        render_positional(&digits, exp)
    };
    if negative {
        format!("-{body}")
    } else {
        body
    }
}

/// Return `(digits, exp)` where `digits` is the shortest run of significant
/// decimal digits (no decimal point, no leading zeros, trailing zeros stripped)
/// that round-trips to `abs`, and `exp` is the power of ten of the leading
/// digit (so `abs == digits[0].digits[1..] x 10^exp`). Uses Rust's
/// round-to-even fixed-precision formatter, matching CPython's tie-break.
///
/// `abs` must be finite and strictly positive.
fn shortest_round_to_even_digits(abs: f64) -> (String, i32) {
    for p in 0..=17usize {
        let s = format!("{abs:.*e}", p);
        // `{:.p e}` rounds half-to-even; the first precision that recovers the
        // input is the CPython-shortest representation.
        if s.parse::<f64>() == Ok(abs) {
            return parse_scientific(&s);
        }
    }
    // Unreachable for finite f64 (17 significant digits always suffice), but be
    // total rather than panic.
    parse_scientific(&format!("{abs:.17e}"))
}

/// Split a Rust `{:e}`-style scientific string (`"D"` or `"D.FFF"`, then `e`,
/// then a signed integer exponent with no leading zeros) into its significant
/// digits (decimal point removed, trailing zeros stripped) and the exponent of
/// the leading digit.
fn parse_scientific(s: &str) -> (String, i32) {
    let (mantissa, exp_str) = s.split_once('e').expect("`{:e}` always contains 'e'");
    let exp: i32 = exp_str.parse().expect("exponent is an integer");
    let mut digits: String = match mantissa.split_once('.') {
        Some((int_part, frac)) => format!("{int_part}{frac}"),
        None => mantissa.to_string(),
    };
    // Strip trailing zeros (e.g. "1.50e2" carries digits "150" -> "15") while
    // keeping at least one digit.
    while digits.len() > 1 && digits.ends_with('0') {
        digits.pop();
    }
    (digits, exp)
}

/// Positional/fixed rendering. `digits` are the significant digits (no point, no
/// leading zeros); `exp` is the power of ten of the leading digit. Caller
/// guarantees `-4 <= exp < 16`.
fn render_positional(digits: &str, exp: i32) -> String {
    let ndigits = digits.len() as i32;
    if exp >= 0 {
        let int_len = exp + 1; // digits left of the decimal point
        if ndigits <= int_len {
            // All significant digits are integer-part; pad to width, add ".0".
            let mut s = String::with_capacity(int_len as usize + 2);
            s.push_str(digits);
            for _ in 0..(int_len - ndigits) {
                s.push('0');
            }
            s.push_str(".0");
            s
        } else {
            // Integer part then fractional remainder.
            let mut s = String::with_capacity(digits.len() + 1);
            s.push_str(&digits[..int_len as usize]);
            s.push('.');
            s.push_str(&digits[int_len as usize..]);
            s
        }
    } else {
        // 0.000<digits>: (-exp - 1) leading zeros after "0.".
        let lead_zeros = (-exp - 1) as usize;
        let mut s = String::with_capacity(2 + lead_zeros + digits.len());
        s.push_str("0.");
        for _ in 0..lead_zeros {
            s.push('0');
        }
        s.push_str(digits);
        s
    }
}

/// Exponential rendering, CPython style: `first-digit[.rest]e<sign><>=2-digit
/// exponent>`.
fn render_exponential(digits: &str, exp: i32) -> String {
    let (first, rest) = digits.split_at(1);
    let mut s = String::with_capacity(digits.len() + 5);
    s.push_str(first);
    if !rest.is_empty() {
        s.push('.');
        s.push_str(rest);
    }
    s.push('e');
    s.push(if exp < 0 { '-' } else { '+' });
    let abs_exp = exp.unsigned_abs();
    if abs_exp < 10 {
        s.push('0'); // zero-pad to at least 2 digits
    }
    s.push_str(&abs_exp.to_string());
    s
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn decode_array_count_exceeding_input_is_value_too_large() {
        // DoS guard: a corrupt/hostile array header that claims more items than
        // the input can hold must be rejected as ValueTooLarge BEFORE
        // `Vec::with_capacity` allocates — never OOM-aborting the process on a
        // tiny frame that claims a 2^48 count.
        let arr = Value::Array(vec![Value::Uint(1), Value::Uint(2), Value::Uint(3)]);
        let full = encode(&arr).expect("encode");
        // Keep tag + the single-byte count varint (count=3); drop all element
        // bytes → claimed count (3) now exceeds remaining input (0).
        let truncated = &full.0[0..2];
        assert!(
            matches!(decode(truncated), Err(CanonicalBytesError::ValueTooLarge(_))),
            "array count exceeding remaining input must be ValueTooLarge, got {:?}",
            decode(truncated)
        );
    }

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
        assert_eq!(
            bytes.as_ref(),
            &[0x10, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
        );
    }

    #[test]
    fn test_string_empty() {
        let bytes = encode(&Value::String("".to_string())).unwrap();
        assert_eq!(bytes.as_ref(), &[0x20, 0x00]); // tag + varint(0)
    }

    #[test]
    fn test_string_hello() {
        let bytes = encode(&Value::String("hello".to_string())).unwrap();
        assert_eq!(bytes.as_ref(), &[0x20, 0x05, b'h', b'e', b'l', b'l', b'o']);
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
            0x20, 0x01, b'a', 0x10, 0, 0, 0, 0, 0, 0, 0, 2, // "a" → int(2)
            0x20, 0x01, b'm', 0x10, 0, 0, 0, 0, 0, 0, 0, 3, // "m" → int(3)
            0x20, 0x01, b'z', 0x10, 0, 0, 0, 0, 0, 0, 0, 1, // "z" → int(1)
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
            m.insert(
                "c".to_string(),
                Value::Array(vec![Value::Null, Value::String("x".to_string())]),
            );
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

    // -----------------------------------------------------------------------
    // float_repr — reproduces CPython repr(float). The cross-language parity
    // vectors live in test_vectors/canonical_bytes_v1.json (`float_vectors`)
    // and are exercised by the test_vectors/rs parity crate; the tests here pin
    // the branch behavior and the value-preservation invariants in-crate.
    // -----------------------------------------------------------------------

    #[test]
    fn float_repr_integer_valued_gets_trailing_dot_zero() {
        assert_eq!(float_repr(0.0), "0.0");
        assert_eq!(float_repr(1.0), "1.0");
        assert_eq!(float_repr(-2.0), "-2.0");
        assert_eq!(float_repr(100.0), "100.0");
        assert_eq!(float_repr(1_000_000.0), "1000000.0");
        assert_eq!(float_repr(1e15), "1000000000000000.0");
    }

    #[test]
    fn float_repr_fractional() {
        assert_eq!(float_repr(0.5), "0.5");
        assert_eq!(float_repr(-0.125), "-0.125");
        assert_eq!(float_repr(2.5), "2.5");
        assert_eq!(float_repr(0.1), "0.1");
        assert_eq!(float_repr(12345.67), "12345.67");
        // needs all 17 significant digits
        assert_eq!(float_repr(0.1 + 0.2), "0.30000000000000004");
    }

    #[test]
    fn float_repr_negative_zero_preserves_sign() {
        // The whole point of the sign-bit check: -0.0 must NOT collapse to 0.0.
        assert_eq!(float_repr(-0.0), "-0.0");
        assert_eq!(float_repr(0.0), "0.0");
        assert!(float_repr(-0.0).starts_with('-'));
    }

    #[test]
    fn float_repr_exponential_threshold_high() {
        // x >= 16 flips to exponential; x == 15 stays positional.
        assert_eq!(float_repr(9_999_999_999_999_998.0), "9999999999999998.0");
        assert_eq!(float_repr(1e16), "1e+16");
        assert_eq!(float_repr(1e17), "1e+17");
        assert_eq!(float_repr(1.5e300), "1.5e+300");
        assert_eq!(float_repr(f64::MAX), "1.7976931348623157e+308");
    }

    #[test]
    fn float_repr_exponential_threshold_low() {
        // x < -4 flips to exponential; x == -4 stays positional.
        assert_eq!(float_repr(1e-4), "0.0001");
        assert_eq!(float_repr(0.0001234), "0.0001234");
        assert_eq!(float_repr(1e-5), "1e-05");
        assert_eq!(float_repr(0.00001234), "1.234e-05");
        assert_eq!(float_repr(-1e-7), "-1e-07");
        assert_eq!(float_repr(1e-100), "1e-100");
    }

    #[test]
    fn float_repr_exponent_zero_padded_and_signed() {
        // Exponent always carries a sign and is padded to >= 2 digits.
        assert_eq!(float_repr(1e-5), "1e-05"); // pad 5 -> 05
        assert_eq!(float_repr(1e16), "1e+16"); // sign + on positive exponent
        assert_eq!(float_repr(1.5e-10), "1.5e-10"); // 2-digit exponent unchanged
        assert_eq!(float_repr(1e100), "1e+100"); // 3-digit exponent unchanged
    }

    #[test]
    fn float_repr_subnormals_and_extremes() {
        assert_eq!(float_repr(f64::MIN_POSITIVE), "2.2250738585072014e-308");
        assert_eq!(float_repr(5e-324), "5e-324"); // smallest positive subnormal
        assert_eq!(float_repr(1e-310), "1e-310"); // mid-range subnormal
    }

    #[test]
    fn float_repr_round_half_to_even_ties() {
        // These f64 values sit at an exact decimal midpoint where BOTH neighbors
        // round-trip. CPython picks the even last digit; Rust's *shortest*
        // formatter would pick the odd one. float_repr must match CPython.
        assert_eq!(
            float_repr(f64::from_bits(0x43130caf3596ef85)),
            "1340492803849185.2" // NOT ...85.3
        );
        assert_eq!(
            float_repr(f64::from_bits(0xc2d3c2ce0c38f748)),
            "-86909605962717.12" // NOT ...717.13
        );
        assert_eq!(
            float_repr(f64::from_bits(0x431ca6bc0c46dc51)),
            "2016156484482836.2" // NOT ...836.3
        );
    }

    #[test]
    fn float_repr_special() {
        assert_eq!(float_repr(f64::NAN), "nan");
        assert_eq!(float_repr(f64::INFINITY), "inf");
        assert_eq!(float_repr(f64::NEG_INFINITY), "-inf");
    }

    proptest::proptest! {
        /// Every finite f64 rendering must parse back to the identical f64 — the
        /// fundamental round-trip guarantee that makes string-encoded floats a
        /// safe cross-language wire form.
        #[test]
        fn float_repr_round_trips(bits in proptest::num::u64::ANY) {
            let f = f64::from_bits(bits);
            if f.is_finite() {
                let s = float_repr(f);
                let back: f64 = s.parse().expect("float_repr output parses");
                // Compare bit patterns so -0.0 vs 0.0 is also caught.
                proptest::prop_assert_eq!(back.to_bits(), f.to_bits(),
                    "rendering {} did not round-trip", s);
            }
        }
    }
}
