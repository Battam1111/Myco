//! Cross-language crypto parity test (Rust side).
//!
//! Loads `test_vectors/crypto_v1.json` and verifies that
//! `myco_kernel_shared::crypto::merkle_hash` and `hmac_sign` produce
//! byte-identical output to every vector in the JSON.
//!
//! Same JSON is consumed by Python (kernel/governance) and TypeScript
//! (anchor_client) implementations.

use std::fs;
use std::path::PathBuf;

use myco_kernel_shared::crypto::{hmac_sign, merkle_hash, CryptoError, NodeHash};

use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct CryptoVectors {
    merkle_hash: MerkleSection,
    hmac_sha256: HmacSection,
    empty_key_must_error: EmptyKeySection,
}

#[derive(Debug, Deserialize)]
struct MerkleSection {
    vectors: Vec<MerkleCase>,
}

#[derive(Debug, Deserialize)]
struct MerkleCase {
    name: String,
    parents_hex: Vec<String>,
    content_hex: String,
    output_hex: String,
}

#[derive(Debug, Deserialize)]
struct HmacSection {
    vectors: Vec<HmacCase>,
}

#[derive(Debug, Deserialize)]
struct HmacCase {
    name: String,
    key_hex: String,
    msg_hex: String,
    output_hex: String,
}

#[derive(Debug, Deserialize)]
struct EmptyKeySection {
    test_cases: Vec<EmptyKeyCase>,
}

#[derive(Debug, Deserialize)]
struct EmptyKeyCase {
    key_hex: String,
    msg_hex: String,
}

fn vectors_path() -> PathBuf {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    manifest_dir
        .parent()
        .expect("test_vectors_rs has a parent dir")
        .join("test_vectors")
        .join("crypto_v1.json")
}

fn load_vectors() -> CryptoVectors {
    let path = vectors_path();
    let raw = fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("failed to read {}: {e}", path.display()));
    serde_json::from_str(&raw).expect("failed to parse crypto JSON test vectors")
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

#[test]
fn all_merkle_hash_vectors() {
    let vectors = load_vectors();
    let mut failures: Vec<String> = Vec::new();
    for v in vectors.merkle_hash.vectors {
        let parents: Vec<NodeHash> = v
            .parents_hex
            .iter()
            .map(|h| {
                let bytes = parse_hex(h);
                let mut arr = [0u8; 32];
                arr.copy_from_slice(&bytes);
                NodeHash::from_bytes(arr)
            })
            .collect();
        let content = parse_hex(&v.content_hex);
        let got = merkle_hash(&parents, &content);
        let got_hex = to_hex(got.as_ref());
        if got_hex != v.output_hex {
            failures.push(format!(
                "merkle vector \"{}\" mismatch:\n  expected: {}\n  got:      {}",
                v.name, v.output_hex, got_hex
            ));
        }
    }
    assert!(
        failures.is_empty(),
        "{} merkle failure(s):\n{}",
        failures.len(),
        failures.join("\n\n")
    );
}

#[test]
fn all_hmac_sha256_vectors() {
    let vectors = load_vectors();
    let mut failures: Vec<String> = Vec::new();
    for v in vectors.hmac_sha256.vectors {
        let key = parse_hex(&v.key_hex);
        let msg = parse_hex(&v.msg_hex);
        let got = hmac_sign(&key, &msg).expect("hmac succeeds with non-empty key");
        let got_hex = to_hex(got.as_ref());
        if got_hex != v.output_hex {
            failures.push(format!(
                "hmac vector \"{}\" mismatch:\n  expected: {}\n  got:      {}",
                v.name, v.output_hex, got_hex
            ));
        }
    }
    assert!(
        failures.is_empty(),
        "{} hmac failure(s):\n{}",
        failures.len(),
        failures.join("\n\n")
    );
}

#[test]
fn empty_key_rejected() {
    let vectors = load_vectors();
    for c in vectors.empty_key_must_error.test_cases {
        let key = parse_hex(&c.key_hex);
        let msg = parse_hex(&c.msg_hex);
        let result = hmac_sign(&key, &msg);
        assert!(
            matches!(result, Err(CryptoError::HmacEmptyKey)),
            "expected HmacEmptyKey for empty key + msg_hex={:?}; got {:?}",
            c.msg_hex,
            result
        );
    }
}
