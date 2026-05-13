//! Envelope schema + integrity check (L1_SKIN §2).
//!
//! ## Doctrine
//!
//! Every delta arriving at an intake endpoint is wrapped in an [`Envelope`].
//! The substrate validates **only the envelope**, not payload content (L0 I8 —
//! substrate is permissive at delta absorption; appetite-axis update-rules
//! evaluate payload content, not the skin).
//!
//! ## Envelope-digest binding
//!
//! Per L1_SKIN §2.1: `envelope_digest = HMAC(operator_token,
//! canonical_envelope_fields || payload)`. HMAC keyed by operator_token gives:
//!
//! - In-flight tamper detection (any byte change → digest mismatch).
//! - Operator authentication (only the operator with the same operator_token
//!   can produce a valid digest).
//!
//! The envelope_digest is an integrity-and-binding tag, NOT a long-lived
//! signature. CI mutations (attestation envelopes) use a separate signature
//! via the operator's per-handshake signing key (per L1_SKIN §4.1 +
//! `kernel/governance` §2.2); that lands at the kernel/governance layer.
//!
//! ## Breach mapping
//!
//! | Failure                                  | Immune sporocarp        | Grade   |
//! |------------------------------------------|-------------------------|---------|
//! | Required field missing / malformed       | `envelope_malformed`    | Daily   |
//! | sender_token ≠ active operator-token     | `envelope_malformed`    | Daily   |
//! | size_bytes > max                         | `envelope_malformed`    | Daily   |
//! | submitted_at_cycle stale                 | `envelope_replay`       | Elevated|
//! | envelope_digest HMAC fails               | `envelope_malformed`    | Daily   |
//! | causal_parent_ref ancient/non-existent   | `causal_chain_violation`| Elevated|
//!
//! External callers see only `envelope_malformed` per §2.1 (no oracle
//! disclosure of which field failed); internal logging differentiates for
//! immune-event sporocarp construction.

use myco_kernel_shared::canonical_bytes::{encode, CanonicalBytes, CanonicalBytesError, Value};
use myco_kernel_shared::crypto::{hmac_sign, CryptoError, HmacTag};
use myco_kernel_shared::sealed_derive::OperatorToken;
use std::collections::BTreeMap;
use thiserror::Error;

/// Envelope-validation errors.
///
/// Per L1_SKIN §2.1: external callers see only `envelope_malformed` (no oracle
/// disclosure). The specific error variant is for internal logging + immune-event
/// emission.
#[derive(Debug, Error, PartialEq, Eq)]
#[non_exhaustive]
pub enum EnvelopeError {
    /// Required field missing or otherwise malformed (e.g., wrong version).
    #[error("envelope_malformed: {0}")]
    Malformed(String),

    /// sender_token does not match the active operator-token.
    #[error("envelope_malformed: sender_token mismatch")]
    SenderTokenMismatch,

    /// payload_shape is not in the recognized set (i.e., `PayloadShape::Other`).
    #[error("envelope_malformed: unknown payload_shape: {0}")]
    UnknownPayloadShape(String),

    /// size_bytes exceeds the configured max.
    #[error("envelope_malformed: size_bytes {got} exceeds max {max}")]
    SizeTooLarge {
        /// Reported envelope size.
        got: u64,
        /// Configured maximum.
        max: u64,
    },

    /// size_bytes does not match payload byte length (envelope is internally
    /// inconsistent).
    #[error("envelope_malformed: size_bytes {claimed} does not match payload length {actual}")]
    SizeMismatch {
        /// Size claimed in the envelope.
        claimed: u64,
        /// Actual payload byte length.
        actual: u64,
    },

    /// envelope_digest HMAC verification failed.
    #[error("envelope_malformed: envelope_digest invalid")]
    DigestInvalid,

    /// submitted_at_cycle is outside the freshness window
    /// (in the future, or too old).
    #[error("envelope_replay: submitted_at_cycle {submitted} not within window of current cycle {current}")]
    StaleSubmittedCycle {
        /// Submitted cycle from the envelope.
        submitted: u64,
        /// Substrate's current cycle.
        current: u64,
    },

    /// causal_parent_ref refers to an ancient or non-existent sporocarp
    /// (kernel/schema dependency; M1 returns this on explicit caller signal).
    #[error("causal_chain_violation: {0}")]
    CausalChainViolation(String),

    /// Canonical-bytes serialization error (propagated from kernel/shared).
    #[error("canonical bytes: {0}")]
    CanonicalBytes(#[from] CanonicalBytesError),

    /// Crypto primitive error (propagated from kernel/shared).
    #[error("crypto: {0}")]
    Crypto(#[from] CryptoError),
}

/// Payload-shape tag — what the payload bytes represent.
///
/// L1_SKIN §2 enumerates: `text`, `file_ref`, `structured_yaml`, `binary_ref`.
/// The substrate validates only that the shape is in the recognized set; it
/// does NOT introspect payload content (per L0 I8).
///
/// `Other` captures unrecognized shapes for serialization round-trip purposes
/// (so canonical-bytes derivations agree across hosts) BUT
/// [`validate_envelope`] rejects `Other` — the recognized set is closed at the
/// validation boundary. To extend, the dimension table at `kernel/governance`
/// undergoes a CI mutation (per L1_GOVERNANCE §1.2).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum PayloadShape {
    /// Plain text.
    Text,
    /// Reference to a file (canonical path).
    FileRef,
    /// Structured YAML / structured-data content.
    StructuredYaml,
    /// Reference to a binary blob.
    BinaryRef,
    /// Unrecognized shape (preserved for round-trip; rejected at validation).
    Other(String),
}

impl PayloadShape {
    /// Canonical-string representation used in envelope serialization.
    pub fn as_str(&self) -> &str {
        match self {
            PayloadShape::Text => "text",
            PayloadShape::FileRef => "file_ref",
            PayloadShape::StructuredYaml => "structured_yaml",
            PayloadShape::BinaryRef => "binary_ref",
            PayloadShape::Other(s) => s.as_str(),
        }
    }

    /// Parse a string into a [`PayloadShape`]. Unknown strings become
    /// `Other(s)` which is rejected at validation.
    pub fn parse(s: &str) -> PayloadShape {
        match s {
            "text" => PayloadShape::Text,
            "file_ref" => PayloadShape::FileRef,
            "structured_yaml" => PayloadShape::StructuredYaml,
            "binary_ref" => PayloadShape::BinaryRef,
            other => PayloadShape::Other(other.to_string()),
        }
    }

    /// Whether this shape is in the recognized (validation-accepted) set.
    pub fn is_recognized(&self) -> bool {
        !matches!(self, PayloadShape::Other(_))
    }
}

/// The delta-intake envelope schema (L1_SKIN §2).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Envelope {
    /// Envelope schema version. Substrate accepts a configured set of versions.
    pub envelope_version: u32,

    /// Operator-token from the active handshake (must match the substrate's
    /// active operator-token).
    pub sender_token: OperatorToken,

    /// Payload-shape tag.
    pub payload_shape: PayloadShape,

    /// Causal parent sporocarp ID; null at first delta after handshake.
    pub causal_parent_ref: Option<Vec<u8>>,

    /// Reported payload size in bytes; must match `payload.len()`.
    pub size_bytes: u64,

    /// MIME-style content-type hint (advisory — substrate does NOT validate
    /// payload against this).
    pub content_type_hint: Option<String>,

    /// Substrate metabolic-cycle counter at envelope submission (operator-side
    /// estimate; substrate checks freshness against its own counter).
    pub submitted_at_cycle: u64,

    /// HMAC envelope_digest. Keyed by operator_token; covers
    /// canonical_envelope_fields || payload.
    pub envelope_digest: HmacTag,

    /// Delta payload bytes (substrate does NOT introspect).
    pub payload: Vec<u8>,
}

/// Configuration for envelope validation (L1-tunable per L1_SKIN §7).
///
/// Defaults match L1_SKIN §7 stated defaults.
#[derive(Debug, Clone)]
pub struct EnvelopeValidationConfig {
    /// Accepted envelope schema versions.
    pub accepted_versions: Vec<u32>,

    /// Maximum size_bytes (default 100 MB per L1_SKIN §7).
    pub max_size_bytes: u64,

    /// Freshness window in cycles (default 60 per L1_SKIN §7).
    pub freshness_window_cycles: u64,
}

impl Default for EnvelopeValidationConfig {
    fn default() -> Self {
        EnvelopeValidationConfig {
            accepted_versions: vec![1],
            max_size_bytes: 100 * 1024 * 1024, // 100 MB
            freshness_window_cycles: 60,
        }
    }
}

/// Compute the canonical envelope-fields bytes (everything except the digest
/// itself, which the digest then signs).
///
/// Per L1_SKIN §2: the digest covers `canonical_envelope_fields || payload`.
/// This function produces the `canonical_envelope_fields` portion.
///
/// The fields are encoded as a canonical [`Value::Map`] with keys sorted by
/// canonical-bytes ordering (per the kernel/shared::canonical_bytes spec).
pub fn canonical_envelope_fields(env: &Envelope) -> Result<CanonicalBytes, EnvelopeError> {
    let mut m = BTreeMap::new();
    m.insert(
        "envelope_version".to_string(),
        Value::Uint(u64::from(env.envelope_version)),
    );
    m.insert(
        "sender_token".to_string(),
        Value::Bytes(env.sender_token.0.to_vec()),
    );
    m.insert(
        "payload_shape".to_string(),
        Value::String(env.payload_shape.as_str().to_string()),
    );
    m.insert(
        "causal_parent_ref".to_string(),
        match &env.causal_parent_ref {
            Some(b) => Value::Bytes(b.clone()),
            None => Value::Null,
        },
    );
    m.insert("size_bytes".to_string(), Value::Uint(env.size_bytes));
    m.insert(
        "content_type_hint".to_string(),
        match &env.content_type_hint {
            Some(s) => Value::String(s.clone()),
            None => Value::Null,
        },
    );
    m.insert(
        "submitted_at_cycle".to_string(),
        Value::Uint(env.submitted_at_cycle),
    );
    // `?`-with-Ok-wrap triggers clippy::needless_question_mark; map_err keeps
    // the From conversion explicit.
    encode(&Value::Map(m)).map_err(EnvelopeError::from)
}

/// Compute the envelope_digest HMAC over `canonical_envelope_fields || payload`.
///
/// Per L1_SKIN §2: keyed by operator_token.
pub fn compute_envelope_digest(
    env: &Envelope,
    operator_token: &OperatorToken,
) -> Result<HmacTag, EnvelopeError> {
    let fields = canonical_envelope_fields(env)?;
    let mut bytes = fields.0;
    bytes.extend_from_slice(&env.payload);
    Ok(hmac_sign(operator_token.as_ref(), &bytes)?)
}

/// Validate an envelope per L1_SKIN §2.1.
///
/// Checks (in order):
/// 1. envelope_version recognized.
/// 2. sender_token matches active operator-token.
/// 3. payload_shape recognized (not [`PayloadShape::Other`]).
/// 4. size_bytes ≤ max.
/// 5. size_bytes consistent with payload byte length.
/// 6. submitted_at_cycle within freshness window.
/// 7. envelope_digest recomputes to the stored digest.
///
/// On any failure → specific [`EnvelopeError`] (caller emits the immune
/// sporocarp from the table at L1_SKIN §6).
pub fn validate_envelope(
    env: &Envelope,
    active_operator_token: &OperatorToken,
    current_cycle: u64,
    config: &EnvelopeValidationConfig,
) -> Result<(), EnvelopeError> {
    // Check 1: envelope_version recognized.
    if !config.accepted_versions.contains(&env.envelope_version) {
        return Err(EnvelopeError::Malformed(format!(
            "unsupported envelope_version {}",
            env.envelope_version
        )));
    }

    // Check 2: sender_token matches active operator-token.
    if env.sender_token != *active_operator_token {
        return Err(EnvelopeError::SenderTokenMismatch);
    }

    // Check 3: payload_shape recognized.
    if !env.payload_shape.is_recognized() {
        return Err(EnvelopeError::UnknownPayloadShape(
            env.payload_shape.as_str().to_string(),
        ));
    }

    // Check 4: size_bytes ≤ configured max.
    if env.size_bytes > config.max_size_bytes {
        return Err(EnvelopeError::SizeTooLarge {
            got: env.size_bytes,
            max: config.max_size_bytes,
        });
    }

    // Check 5: size_bytes consistent with payload length.
    if env.size_bytes != env.payload.len() as u64 {
        return Err(EnvelopeError::SizeMismatch {
            claimed: env.size_bytes,
            actual: env.payload.len() as u64,
        });
    }

    // Check 6: submitted_at_cycle within freshness window.
    //   - Not in the future relative to substrate's current cycle.
    //   - Not older than `freshness_window_cycles` cycles.
    if env.submitted_at_cycle > current_cycle {
        return Err(EnvelopeError::StaleSubmittedCycle {
            submitted: env.submitted_at_cycle,
            current: current_cycle,
        });
    }
    if current_cycle.saturating_sub(env.submitted_at_cycle) > config.freshness_window_cycles {
        return Err(EnvelopeError::StaleSubmittedCycle {
            submitted: env.submitted_at_cycle,
            current: current_cycle,
        });
    }

    // Check 7: envelope_digest recomputes.
    let recomputed = compute_envelope_digest(env, active_operator_token)?;
    if recomputed != env.envelope_digest {
        return Err(EnvelopeError::DigestInvalid);
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_token(byte: u8) -> OperatorToken {
        OperatorToken([byte; 32])
    }

    /// Construct a valid envelope for tests, computing the digest correctly.
    fn make_valid_envelope(token: &OperatorToken, cycle: u64, payload: Vec<u8>) -> Envelope {
        let size = payload.len() as u64;
        let mut env = Envelope {
            envelope_version: 1,
            sender_token: token.clone(),
            payload_shape: PayloadShape::Text,
            causal_parent_ref: None,
            size_bytes: size,
            content_type_hint: Some("text/plain".to_string()),
            submitted_at_cycle: cycle,
            envelope_digest: HmacTag([0; 32]), // placeholder; recomputed below
            payload,
        };
        env.envelope_digest = compute_envelope_digest(&env, token).unwrap();
        env
    }

    #[test]
    fn test_payload_shape_round_trip_recognized() {
        for s in &["text", "file_ref", "structured_yaml", "binary_ref"] {
            let shape = PayloadShape::parse(s);
            assert_eq!(shape.as_str(), *s);
            assert!(shape.is_recognized());
        }
    }

    #[test]
    fn test_payload_shape_unknown_becomes_other() {
        let shape = PayloadShape::parse("brand_new_shape");
        assert!(matches!(shape, PayloadShape::Other(_)));
        assert!(!shape.is_recognized());
        assert_eq!(shape.as_str(), "brand_new_shape");
    }

    #[test]
    fn test_canonical_envelope_fields_deterministic() {
        let token = make_token(0xaa);
        let env = make_valid_envelope(&token, 10, b"hello".to_vec());
        let f1 = canonical_envelope_fields(&env).unwrap();
        let f2 = canonical_envelope_fields(&env).unwrap();
        assert_eq!(f1, f2);
    }

    #[test]
    fn test_canonical_envelope_fields_independent_of_digest() {
        // Two envelopes identical except for envelope_digest produce identical
        // canonical_envelope_fields (the digest is NOT part of the canonical fields).
        let token = make_token(0xab);
        let mut env1 = make_valid_envelope(&token, 10, b"hi".to_vec());
        let env2 = env1.clone();
        env1.envelope_digest = HmacTag([0xcd; 32]); // tamper digest
        let f1 = canonical_envelope_fields(&env1).unwrap();
        let f2 = canonical_envelope_fields(&env2).unwrap();
        assert_eq!(f1, f2);
    }

    #[test]
    fn test_envelope_digest_round_trip() {
        let token = make_token(0xff);
        let env = make_valid_envelope(&token, 5, b"data".to_vec());
        // make_valid_envelope already sets the correct digest; verify it.
        let recomputed = compute_envelope_digest(&env, &token).unwrap();
        assert_eq!(recomputed, env.envelope_digest);
    }

    #[test]
    fn test_validate_envelope_ok() {
        let token = make_token(0x10);
        let env = make_valid_envelope(&token, 10, b"payload".to_vec());
        let config = EnvelopeValidationConfig::default();
        validate_envelope(&env, &token, 10, &config).unwrap();
    }

    #[test]
    fn test_validate_envelope_version_rejected() {
        let token = make_token(0x10);
        let mut env = make_valid_envelope(&token, 10, b"x".to_vec());
        env.envelope_version = 99;
        // Recompute digest so digest isn't the failure path (we test version specifically).
        env.envelope_digest = compute_envelope_digest(&env, &token).unwrap();
        let config = EnvelopeValidationConfig::default();
        let result = validate_envelope(&env, &token, 10, &config);
        assert!(matches!(result, Err(EnvelopeError::Malformed(_))));
    }

    #[test]
    fn test_validate_envelope_sender_token_mismatch() {
        let token_a = make_token(0x11);
        let token_b = make_token(0x22);
        let env = make_valid_envelope(&token_a, 10, b"x".to_vec());
        let config = EnvelopeValidationConfig::default();
        // Active operator-token is token_b but envelope has token_a.
        let result = validate_envelope(&env, &token_b, 10, &config);
        assert_eq!(result, Err(EnvelopeError::SenderTokenMismatch));
    }

    #[test]
    fn test_validate_envelope_unknown_payload_shape() {
        let token = make_token(0x33);
        let mut env = make_valid_envelope(&token, 10, b"x".to_vec());
        env.payload_shape = PayloadShape::Other("xenoshape".to_string());
        env.envelope_digest = compute_envelope_digest(&env, &token).unwrap();
        let config = EnvelopeValidationConfig::default();
        let result = validate_envelope(&env, &token, 10, &config);
        assert!(matches!(result, Err(EnvelopeError::UnknownPayloadShape(s)) if s == "xenoshape"));
    }

    #[test]
    fn test_validate_envelope_size_too_large() {
        let token = make_token(0x44);
        let mut env = make_valid_envelope(&token, 10, b"x".to_vec());
        env.size_bytes = 999_999_999_999;
        // size_bytes claim doesn't match payload — but the SizeTooLarge check
        // runs BEFORE the SizeMismatch check, so we'd get SizeTooLarge with
        // a small max.
        env.envelope_digest = compute_envelope_digest(&env, &token).unwrap();
        let config = EnvelopeValidationConfig {
            max_size_bytes: 1024,
            ..EnvelopeValidationConfig::default()
        };
        let result = validate_envelope(&env, &token, 10, &config);
        assert!(matches!(
            result,
            Err(EnvelopeError::SizeTooLarge { got: 999_999_999_999, max: 1024 })
        ));
    }

    #[test]
    fn test_validate_envelope_size_mismatch_payload() {
        let token = make_token(0x55);
        let mut env = make_valid_envelope(&token, 10, b"hello".to_vec());
        env.size_bytes = 999; // claim 999 but payload is 5
        env.envelope_digest = compute_envelope_digest(&env, &token).unwrap();
        let config = EnvelopeValidationConfig::default();
        let result = validate_envelope(&env, &token, 10, &config);
        assert!(matches!(
            result,
            Err(EnvelopeError::SizeMismatch { claimed: 999, actual: 5 })
        ));
    }

    #[test]
    fn test_validate_envelope_future_submitted_cycle() {
        let token = make_token(0x66);
        let env = make_valid_envelope(&token, 100, b"x".to_vec());
        let config = EnvelopeValidationConfig::default();
        // Current cycle = 50; envelope submitted at 100 (future) → stale.
        let result = validate_envelope(&env, &token, 50, &config);
        assert!(matches!(
            result,
            Err(EnvelopeError::StaleSubmittedCycle { submitted: 100, current: 50 })
        ));
    }

    #[test]
    fn test_validate_envelope_too_old() {
        let token = make_token(0x77);
        let env = make_valid_envelope(&token, 10, b"x".to_vec());
        let config = EnvelopeValidationConfig {
            freshness_window_cycles: 60,
            ..EnvelopeValidationConfig::default()
        };
        // Current cycle = 200; submitted at 10 → 190 cycles old → too old.
        let result = validate_envelope(&env, &token, 200, &config);
        assert!(matches!(
            result,
            Err(EnvelopeError::StaleSubmittedCycle { submitted: 10, current: 200 })
        ));
    }

    #[test]
    fn test_validate_envelope_within_freshness_window() {
        let token = make_token(0x88);
        let env = make_valid_envelope(&token, 10, b"x".to_vec());
        let config = EnvelopeValidationConfig {
            freshness_window_cycles: 60,
            ..EnvelopeValidationConfig::default()
        };
        // Current cycle = 70; submitted at 10 → 60 cycles old → exactly at window
        // boundary → accepted (window check is `> window`).
        validate_envelope(&env, &token, 70, &config).unwrap();
    }

    #[test]
    fn test_validate_envelope_digest_invalid() {
        let token = make_token(0x99);
        let mut env = make_valid_envelope(&token, 10, b"x".to_vec());
        // Tamper the digest.
        env.envelope_digest = HmacTag([0xff; 32]);
        let config = EnvelopeValidationConfig::default();
        let result = validate_envelope(&env, &token, 10, &config);
        assert_eq!(result, Err(EnvelopeError::DigestInvalid));
    }

    #[test]
    fn test_validate_envelope_payload_tamper_caught_by_digest() {
        let token = make_token(0xaa);
        let mut env = make_valid_envelope(&token, 10, b"original".to_vec());
        // Tamper payload but leave digest stale (since size_bytes still matches
        // tampered length: use same-length replacement).
        env.payload = b"tampered".to_vec();
        // size_bytes was 8, "tampered" is also 8.
        let config = EnvelopeValidationConfig::default();
        let result = validate_envelope(&env, &token, 10, &config);
        // Digest fails because canonical_envelope_fields || payload changed.
        assert_eq!(result, Err(EnvelopeError::DigestInvalid));
    }

    #[test]
    fn test_validate_envelope_fields_tamper_caught_by_digest() {
        let token = make_token(0xbb);
        let mut env = make_valid_envelope(&token, 10, b"x".to_vec());
        // Tamper a field (e.g., content_type_hint) without recomputing digest.
        env.content_type_hint = Some("evil/content".to_string());
        let config = EnvelopeValidationConfig::default();
        let result = validate_envelope(&env, &token, 10, &config);
        assert_eq!(result, Err(EnvelopeError::DigestInvalid));
    }

    #[test]
    fn test_validate_envelope_empty_payload_ok() {
        let token = make_token(0xcc);
        let env = make_valid_envelope(&token, 10, vec![]);
        let config = EnvelopeValidationConfig::default();
        validate_envelope(&env, &token, 10, &config).unwrap();
    }

    #[test]
    fn test_validate_envelope_with_causal_parent_ref_ok() {
        let token = make_token(0xdd);
        let mut env = make_valid_envelope(&token, 10, b"x".to_vec());
        env.causal_parent_ref = Some(vec![0xab, 0xcd, 0xef]);
        env.envelope_digest = compute_envelope_digest(&env, &token).unwrap();
        let config = EnvelopeValidationConfig::default();
        validate_envelope(&env, &token, 10, &config).unwrap();
    }
}
