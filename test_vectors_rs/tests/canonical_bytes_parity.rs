//! Cross-language canonical-bytes parity test (Rust side).
//!
//! Loads `test_vectors/canonical_bytes_v1.json` and verifies that the Rust
//! `myco_kernel_shared::canonical_bytes::encode` implementation produces
//! byte-identical output to every vector in the JSON.
//!
//! Same JSON is consumed by TypeScript (anchor_client) and Python
//! (kernel/governance). All three implementations must agree, or L1_HARD_RULES
//! C18 `canonical_bytes_render_drift` (CRITICAL) is triggered.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use myco_kernel_shared::canonical_bytes::{decode, encode, Value};

use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct VectorsFile {
    vectors: Vec<VectorCase>,
    varint_vectors: Vec<VarintCase>,
}

#[derive(Debug, Deserialize)]
struct VectorCase {
    name: String,
    input: InputSpec,
    output_hex: String,
}

#[derive(Debug, Deserialize)]
struct VarintCase {
    input: u64,
    output_hex: String,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "type")]
#[serde(rename_all = "lowercase")]
enum InputSpec {
    Null,
    Bool {
        value: bool,
    },
    Int {
        #[serde(default)]
        value: Option<i64>,
        #[serde(default)]
        value_decimal_str: Option<String>,
    },
    Uint {
        #[serde(default)]
        value: Option<u64>,
        #[serde(default)]
        value_decimal_str: Option<String>,
    },
    String {
        #[serde(default)]
        value: Option<String>,
        #[serde(default)]
        value_utf8_hex: Option<String>,
    },
    Bytes {
        #[serde(default)]
        value_hex: Option<String>,
        #[serde(default)]
        value_hex_repeat: Option<HexRepeat>,
    },
    Array {
        value: Vec<InputSpec>,
    },
    Map {
        value: serde_json::Map<String, serde_json::Value>,
    },
    Timestamp {
        #[serde(default)]
        value: Option<i64>,
        #[serde(default)]
        value_decimal_str: Option<String>,
    },
    Hash {
        value_hex: String,
    },
}

#[derive(Debug, Deserialize)]
struct HexRepeat {
    byte: String,
    count: usize,
}

fn vectors_path() -> PathBuf {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    manifest_dir
        .parent()
        .expect("test_vectors_rs has a parent dir")
        .join("test_vectors")
        .join("canonical_bytes_v1.json")
}

fn load_vectors() -> VectorsFile {
    let path = vectors_path();
    let raw = fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("failed to read {}: {e}", path.display()));
    serde_json::from_str(&raw).expect("failed to parse JSON test vectors")
}

fn parse_hex(hex: &str) -> Vec<u8> {
    let mut out = Vec::with_capacity(hex.len() / 2);
    let chars: Vec<char> = hex.chars().collect();
    for chunk in chars.chunks(2) {
        let s: String = chunk.iter().collect();
        out.push(u8::from_str_radix(&s, 16).expect("hex digit"));
    }
    out
}

fn to_hex(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        s.push_str(&format!("{b:02x}"));
    }
    s
}

fn spec_to_value(spec: InputSpec) -> Value {
    match spec {
        InputSpec::Null => Value::Null,
        InputSpec::Bool { value } => Value::Bool(value),
        InputSpec::Int {
            value,
            value_decimal_str,
        } => {
            let v = value_decimal_str
                .map(|s| s.parse::<i64>().expect("int decimal_str"))
                .or(value)
                .expect("int case missing value");
            Value::Int(v)
        }
        InputSpec::Uint {
            value,
            value_decimal_str,
        } => {
            let v = value_decimal_str
                .map(|s| s.parse::<u64>().expect("uint decimal_str"))
                .or(value)
                .expect("uint case missing value");
            Value::Uint(v)
        }
        InputSpec::String {
            value,
            value_utf8_hex,
        } => {
            let s = if let Some(v) = value {
                v
            } else if let Some(hex) = value_utf8_hex {
                String::from_utf8(parse_hex(&hex)).expect("invalid UTF-8")
            } else {
                panic!("string case missing value/value_utf8_hex")
            };
            Value::String(s)
        }
        InputSpec::Bytes {
            value_hex,
            value_hex_repeat,
        } => {
            let bytes = if let Some(hex) = value_hex {
                parse_hex(&hex)
            } else if let Some(rep) = value_hex_repeat {
                let b = u8::from_str_radix(&rep.byte, 16).expect("hex byte");
                vec![b; rep.count]
            } else {
                panic!("bytes case missing value_hex/value_hex_repeat")
            };
            Value::Bytes(bytes)
        }
        InputSpec::Array { value } => Value::Array(value.into_iter().map(spec_to_value).collect()),
        InputSpec::Map { value } => {
            let mut m = BTreeMap::new();
            for (k, v) in value {
                let sub_spec: InputSpec = serde_json::from_value(v).expect("map value spec");
                m.insert(k, spec_to_value(sub_spec));
            }
            Value::Map(m)
        }
        InputSpec::Timestamp {
            value,
            value_decimal_str,
        } => {
            let v = value_decimal_str
                .map(|s| s.parse::<i64>().expect("timestamp decimal_str"))
                .or(value)
                .expect("timestamp case missing value");
            Value::Timestamp(v)
        }
        InputSpec::Hash { value_hex } => {
            let bytes = parse_hex(&value_hex);
            let mut h = [0u8; 32];
            h.copy_from_slice(&bytes);
            Value::Hash(h)
        }
    }
}

#[test]
fn all_canonical_bytes_vectors() {
    let vectors = load_vectors();
    let mut failures: Vec<String> = Vec::new();
    for v in vectors.vectors {
        let name = v.name.clone();
        let value = spec_to_value(v.input);
        let got = encode(&value).expect("encode succeeds");
        let got_hex = to_hex(got.as_ref());
        if got_hex != v.output_hex {
            failures.push(format!(
                "vector \"{}\" mismatch:\n  expected: {}\n  got:      {}",
                name, v.output_hex, got_hex
            ));
        }
    }
    assert!(
        failures.is_empty(),
        "{} failure(s):\n{}",
        failures.len(),
        failures.join("\n\n")
    );
}

#[test]
fn all_canonical_bytes_vectors_decode_roundtrip() {
    // For every shared vector: decode(output_hex) then re-encode and verify
    // byte-identical output. Pins the Rust decoder against the same JSON
    // contract that Python and TypeScript decoders use (closes L1_HARD_RULES
    // C18 canonical_bytes_render_drift on the decode side).
    let vectors = load_vectors();
    let mut failures: Vec<String> = Vec::new();
    for v in vectors.vectors {
        let name = v.name.clone();
        let original = parse_hex(&v.output_hex);
        let decoded = match decode(&original) {
            Ok(value) => value,
            Err(e) => {
                failures.push(format!("vector \"{name}\" decode failed: {e}"));
                continue;
            }
        };
        let reencoded = encode(&decoded).expect("re-encode succeeds");
        let reencoded_hex = to_hex(reencoded.as_ref());
        if reencoded_hex != v.output_hex {
            failures.push(format!(
                "vector \"{name}\" decode-roundtrip mismatch:\n  original:   {}\n  reencoded:  {}",
                v.output_hex, reencoded_hex
            ));
        }
    }
    assert!(
        failures.is_empty(),
        "{} failure(s):\n{}",
        failures.len(),
        failures.join("\n\n")
    );
}

#[test]
fn all_varint_vectors() {
    use myco_kernel_shared::canonical_bytes::{encode as enc, Value as V};
    // We can't access write_varint directly (private), so we exercise it via
    // a varint-length-encoded type (String) where the bytes after the tag are
    // the varint encoding of length 0. To test varint at specific values we
    // encode a Bytes value with that many bytes and inspect the prefix.
    let vectors = load_vectors();
    let mut failures: Vec<String> = Vec::new();
    for vv in vectors.varint_vectors {
        // Encode Bytes(0x00 * vv.input) and strip the 1-byte tag.
        let n = vv.input as usize;
        // Limit to a reasonable max to avoid huge allocations during testing.
        if n > 2_097_152 {
            // 2 MB cap; tests cover up to 2097152 boundary
            continue;
        }
        let value = V::Bytes(vec![0u8; n]);
        let bytes = enc(&value).expect("encode succeeds");
        // First byte is BYTES tag (0x21); next 1-N bytes are varint(n);
        // then n zero bytes follow.
        let raw = bytes.as_ref();
        assert_eq!(raw[0], 0x21, "expected BYTES tag");
        // Extract the varint bytes by reading until MSB clear.
        let mut varint_bytes = Vec::new();
        let mut idx = 1;
        loop {
            let b = raw[idx];
            varint_bytes.push(b);
            idx += 1;
            if b & 0x80 == 0 {
                break;
            }
        }
        let got_hex = to_hex(&varint_bytes);
        if got_hex != vv.output_hex {
            failures.push(format!(
                "varint({}) mismatch:\n  expected: {}\n  got:      {}",
                vv.input, vv.output_hex, got_hex
            ));
        }
    }
    assert!(
        failures.is_empty(),
        "{} failure(s):\n{}",
        failures.len(),
        failures.join("\n\n")
    );
}
