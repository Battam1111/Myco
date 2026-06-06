//! Operator handshake protocol: bidirectional validation (L1/SKIN §4).
//!
//! ## Doctrine
//!
//! Per L1/SKIN §4 the handshake is **bidirectional**: the operator validates
//! the substrate (anti-impostor / wrong-substrate-ID detection) AND the
//! substrate validates the operator (single-operator gate + token derivation).
//!
//! ### v0.9 keyless
//!
//! The owner Ed25519 key + the anchor surface were removed in v0.9. The
//! handshake no longer models an owner-birth-attestation signature, an owner
//! public key, or an anchor-surface endpoint key: the substrate-ID is
//! self-derived (P01c) and the trust root at runtime is the bonded pilot-agent
//! over the operator-session channel (single-human Venom shared-fate). The
//! handshake SHAPE is unchanged: the operator pins + validates the substrate-ID,
//! the substrate mints a non-deterministic `operator_token`, and the
//! continuity claim selects the post-handshake quarantine-window length.
//!
//! ### Per-handshake operator signing keypair (L1/SKIN §4.1, pass-3)
//!
//! The operator's runtime generates a fresh signing keypair at handshake
//! initiation. The private key lives in operator-runtime memory only (never
//! on disk, never transmitted to substrate). The public key is published in
//! the [`HandshakeInitiate`] envelope. This gives the operator a real signing
//! surface distinct from the substrate-generated operator_token, closing the
//! pass-3 cryptographic-hollow finding: `operator_witness` fields (in
//! `kernel/governance` attestation envelopes) signed with the operator's
//! private key are forge-resistant by the substrate.
//!
//! ### Non-deterministic operator-token (L1/SKIN §4.2, pass-3)
//!
//! The substrate derives `operator_token` via OS-mediated sealed-key derivation
//! ([`myco_kernel_shared::sealed_derive`]). The `substrate_secret` never enters
//! substrate process address space in plaintext. The derivation:
//!
//! ```text
//! operator_token = sealed_derive(handshake_nonce, current_cycle, kernel_random)
//! ```
//!
//! where `handshake_nonce` = `operator_signing_key_public || submitted_at`
//! (chosen to bind the token to this specific handshake's operator-side
//! contribution + their wall-clock submission moment).
//!
//! ### Single-operator enforcement (L1/SKIN §4.4)
//!
//! Per L0 I8 + L1/HARD_RULES C11: skin admits at most one operator-token at a
//! time. The [`SkinState`] state machine enforces this in-process; transport-
//! level race tiebreak is OS-accept-queue FIFO order (L4-platform-specific).
//!
//! ## M1 implementation
//!
//! In-memory state machine. Persistence of [`SkinState`] across cold-resume is
//! deferred to M2 via `kernel/continuity` WAL. The continuity claim honors the
//! claim *shape* (i.e., [`ContinuityClaim::AttestedContinuity`] shortens
//! quarantine); v0.9 keyless: the attestation is a substrate/DAG-tip-derived
//! continuity proof, not an owner signature.

use myco_kernel_shared::sealed_derive::{OperatorToken, SealedDerive, SealedDeriveError};
use thiserror::Error;

/// Handshake-protocol errors.
#[derive(Debug, Error)]
#[non_exhaustive]
pub enum HandshakeError {
    /// substrate_id_proof in the initiate envelope does not match this substrate.
    #[error("substrate_id_mismatch: claimed {claimed:?}; actual {actual:?}")]
    SubstrateIdMismatch {
        /// Claim from the operator's initiate envelope.
        claimed: String,
        /// This substrate's actual identity.
        actual: String,
    },

    /// Concurrent connect attempt while an operator is already active
    /// (`concurrent_connect_attempt` immune sporocarp per L1/SKIN §6).
    #[error("concurrent_connect_attempt: skin busy with active operator")]
    SkinBusy,

    /// Operator's signing public key is invalid (empty or wrong shape).
    #[error("operator_signing_key_public invalid: {0}")]
    InvalidOperatorPubKey(String),

    /// Continuity claim is invalid (e.g., empty attestation bytes when
    /// `AttestedContinuity` is claimed).
    #[error("continuity_claim invalid: {0}")]
    InvalidContinuityClaim(String),

    /// Sealed-derive failure (propagated from kernel/shared).
    #[error("sealed_derive: {0}")]
    SealedDerive(#[from] SealedDeriveError),

    /// State-machine misuse (e.g., terminate when no operator active).
    #[error("wrong handshake state: {0}")]
    WrongState(String),
}

/// Substrate identity (immutable post-genesis; L1/HARD_RULES F2 fixed-point).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct SubstrateId(pub String);

/// Operator's per-handshake public key. Bytes are L4-platform-specific
/// (Ed25519 = 32 bytes, ECDSA-P256 = 33 bytes compressed, etc.). L1 does not
/// pre-pick a signature algorithm.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct OperatorSigningKeyPublic(pub Vec<u8>);

/// Continuity claim from the operator (L1/SKIN §4.3).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ContinuityClaim {
    /// Fresh handshake; no continuity attestation. Substrate enters full
    /// post-handshake quarantine window (default 100 cycles).
    Fresh,
    /// Attested continuity. v0.9 keyless: the envelope carries a
    /// substrate/DAG-tip-derived continuity proof naming this specific
    /// reconnection (NOT an owner signature; the owner key + anchor surface
    /// were removed). Substrate honors the shorter quarantine window
    /// (default 10 cycles) once the proof shape validates.
    AttestedContinuity {
        /// Substrate/DAG-tip-derived continuity-attestation bytes.
        continuity_attestation: Vec<u8>,
    },
}

/// Substrate identity record snapshot (read at handshake-complete construction).
///
/// In production this is read from the substrate's persisted identity record
/// (tier-1 SSoT via `kernel/schema`). M1 keeps it in-memory.
///
/// v0.9 keyless: the record carries only the self-derived substrate-ID. The
/// owner-birth-attestation signature, the active owner public key, and the
/// anchor-surface endpoint key were dropped with the owner-key + anchor surface.
#[derive(Debug, Clone)]
pub struct SubstrateIdentityRecord {
    /// Immutable substrate-ID (F2).
    pub substrate_id: SubstrateId,
}

/// Handshake-initiate envelope from operator → substrate (L1/SKIN §4.1).
#[derive(Debug, Clone)]
pub struct HandshakeInitiate {
    /// Envelope version (separate counter from delta envelope_version).
    pub envelope_version: u32,

    /// Substrate-ID the operator believes it's targeting (bootstrap-pinned).
    pub substrate_id_proof: SubstrateId,

    /// Operator's freshly-generated per-handshake signing public key.
    pub operator_signing_key_public: OperatorSigningKeyPublic,

    /// Continuity claim (`Fresh` or `AttestedContinuity`).
    pub continuity_claim: ContinuityClaim,

    /// Wall-clock timestamp from operator side (advisory; used as part of
    /// handshake_nonce for operator_token derivation).
    pub submitted_at: i64,
}

/// Handshake-complete envelope from substrate → operator (L1/SKIN §4.2).
///
/// The operator validates the substrate by pinning + comparing the returned
/// `substrate_id` against the bootstrap-pinned target. v0.9 keyless: there is
/// no owner public key to cross-check and no anchor-surface fetch: the
/// substrate-ID is self-derived (P01c) and the runtime trust root is the bonded
/// pilot-agent over the operator-session channel.
#[derive(Debug, Clone)]
pub struct HandshakeComplete {
    /// Newly-minted operator-token (non-deterministic; derived via sealed_derive).
    pub operator_token: OperatorToken,

    /// Substrate-ID (operator cross-checks against its bootstrap-pinned target).
    pub substrate_id: SubstrateId,

    /// Substrate's metabolic cycle counter at handshake-complete emission.
    pub handshake_timestamp: u64,
}

/// Handshake-terminate envelope (L1/SKIN §4.5).
#[derive(Debug, Clone)]
pub struct HandshakeTerminate {
    /// Optional dormancy preference (subject to resource pressure override
    /// per L1/SKIN §4.5).
    pub request_dormancy: Option<DormancyRequest>,
}

/// Operator's dormancy preference at termination (L1/SKIN §4.5).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DormancyRequest {
    /// Process suspended (host-dependent semantics).
    Paused,
    /// Dormant with cycle-cadence floor.
    Throttled,
}

/// Single-operator state machine (per L0 I8 + L1/SKIN §4.4).
#[derive(Debug, Clone)]
pub enum SkinState {
    /// No active operator. Substrate is dormant or fresh-genesis.
    Idle,
    /// Active operator session; single-operator lock held.
    Active(ActiveSession),
}

/// State of an active operator session.
#[derive(Debug, Clone)]
pub struct ActiveSession {
    /// Operator-token minted at this handshake.
    pub operator_token: OperatorToken,

    /// Operator's per-handshake signing pubkey (for `operator_witness`
    /// signature verification on CI attestation envelopes; that path lives in
    /// `kernel/governance`).
    pub operator_signing_key_public: OperatorSigningKeyPublic,

    /// Cycle at which the handshake completed.
    pub handshake_at_cycle: u64,

    /// Continuity claim from the handshake.
    pub continuity_claim: ContinuityClaim,

    /// Whether the post-handshake quarantine window is still active. When
    /// `true`, CI-level operations are gated regardless of governance
    /// classification (per L1/SKIN §4.3 + L1/HARD_RULES C3).
    pub in_post_handshake_quarantine: bool,
}

/// Handshake configuration (L1-tunable per L1/SKIN §7).
#[derive(Debug, Clone)]
pub struct HandshakeConfig {
    /// Post-handshake quarantine window in cycles (default 100 per L1/SKIN §7).
    pub post_handshake_quarantine_cycles: u64,

    /// Reduced quarantine window when `AttestedContinuity` is honored
    /// (default 10 per L1/SKIN §4.3).
    pub quarantine_with_continuity: u64,

    /// Idle timeout in cycles before disconnect (default 100 per L1/SKIN §7).
    pub idle_timeout_cycles: u64,
}

impl Default for HandshakeConfig {
    fn default() -> Self {
        HandshakeConfig {
            post_handshake_quarantine_cycles: 100,
            quarantine_with_continuity: 10,
            idle_timeout_cycles: 100,
        }
    }
}

/// Process a handshake-initiate envelope (L1/SKIN §4.1-§4.2).
///
/// On success:
/// - State transitions [`SkinState::Idle`] → [`SkinState::Active`].
/// - [`HandshakeComplete`] is returned for emission to the operator.
///
/// On failure:
/// - State stays [`SkinState::Idle`] (or [`SkinState::Active`] if
///   `SkinBusy`).
/// - A specific [`HandshakeError`] is returned; the caller emits the
///   corresponding immune sporocarp from the L1/SKIN §6 table.
///
/// ## Order of checks
///
/// 1. `SkinBusy`: already active.
/// 2. `SubstrateIdMismatch`: wrong substrate target.
/// 3. `InvalidOperatorPubKey`: empty / malformed.
/// 4. `InvalidContinuityClaim`: claim shape malformed.
/// 5. `SealedDerive`: kernel-mediated derivation error.
pub fn process_initiate<S: SealedDerive>(
    state: &mut SkinState,
    initiate: HandshakeInitiate,
    sealed: &S,
    identity: &SubstrateIdentityRecord,
    current_cycle: u64,
    kernel_random: &[u8],
) -> Result<HandshakeComplete, HandshakeError> {
    // §4.4: single-operator. Second handshake during active → SkinBusy.
    if matches!(state, SkinState::Active(_)) {
        return Err(HandshakeError::SkinBusy);
    }

    // §4.2 step 1: validate substrate_id_proof against own identity.
    if initiate.substrate_id_proof != identity.substrate_id {
        return Err(HandshakeError::SubstrateIdMismatch {
            claimed: initiate.substrate_id_proof.0,
            actual: identity.substrate_id.0.clone(),
        });
    }

    // §4.1: operator pubkey shape check (non-empty).
    if initiate.operator_signing_key_public.0.is_empty() {
        return Err(HandshakeError::InvalidOperatorPubKey(
            "empty key bytes".to_string(),
        ));
    }

    // §4.3: continuity-claim shape check.
    if let ContinuityClaim::AttestedContinuity {
        continuity_attestation,
    } = &initiate.continuity_claim
    {
        if continuity_attestation.is_empty() {
            return Err(HandshakeError::InvalidContinuityClaim(
                "AttestedContinuity requires non-empty continuity_attestation".to_string(),
            ));
        }
    }

    // §4.2 step 2: generate operator_token via OS-mediated sealed_derive.
    // handshake_nonce binds the token to this specific handshake's operator-side
    // contribution (their fresh pubkey) and their wall-clock submission moment.
    let mut handshake_nonce = Vec::with_capacity(initiate.operator_signing_key_public.0.len() + 8);
    handshake_nonce.extend_from_slice(&initiate.operator_signing_key_public.0);
    handshake_nonce.extend_from_slice(&initiate.submitted_at.to_be_bytes());
    let operator_token = sealed.derive(&handshake_nonce, current_cycle, kernel_random)?;

    // §4.2 step 3: construct handshake_complete for emission.
    let complete = HandshakeComplete {
        operator_token: operator_token.clone(),
        substrate_id: identity.substrate_id.clone(),
        handshake_timestamp: current_cycle,
    };

    // §4.3 quarantine: full window for Fresh, shorter for AttestedContinuity.
    // In BOTH cases the substrate enters post-handshake quarantine; the only
    // difference is window length (handled in `advance_quarantine_window` below).
    // Per L1/SKIN §4.3: even AttestedContinuity shortens to default 10
    // cycles, not zero.
    //
    // v0.9 keyless: the continuity attestation is a substrate/DAG-tip-derived
    // continuity proof; M1 honors the claim shape (chooses window length).
    // Cryptographic verification of the proof bytes is deferred to M2.
    *state = SkinState::Active(ActiveSession {
        operator_token,
        operator_signing_key_public: initiate.operator_signing_key_public,
        handshake_at_cycle: current_cycle,
        continuity_claim: initiate.continuity_claim,
        in_post_handshake_quarantine: true,
    });

    // §4.2 step 4: substrate records the handshake event as a sporocarp.
    // M1 defers sporocarp recording to M2: sporocarp construction lives in
    // `kernel/schema` + `kernel/tropism`, which is post-M1 step 2 in the
    // dependency graph. The caller of `process_initiate` is responsible for
    // emitting the sporocarp once those crates land.
    Ok(complete)
}

/// Process a handshake-terminate envelope (L1/SKIN §4.5 explicit termination).
///
/// On success: state transitions Active → Idle.
/// On Idle: returns [`HandshakeError::WrongState`].
pub fn process_terminate(
    state: &mut SkinState,
    _terminate: HandshakeTerminate,
) -> Result<(), HandshakeError> {
    match state {
        SkinState::Active(_) => {
            *state = SkinState::Idle;
            Ok(())
        }
        SkinState::Idle => Err(HandshakeError::WrongState(
            "cannot terminate: no active operator".to_string(),
        )),
    }
}

/// Advance the post-handshake quarantine window (called per cycle).
///
/// Once `post_handshake_quarantine_cycles` (or `quarantine_with_continuity`)
/// cycles have elapsed since the handshake, clears the
/// `in_post_handshake_quarantine` flag. CI-level operations subsequently flow
/// per the normal classifier path (per L1/GOVERNANCE classification rules).
pub fn advance_quarantine_window(
    state: &mut SkinState,
    current_cycle: u64,
    config: &HandshakeConfig,
) {
    if let SkinState::Active(session) = state {
        if !session.in_post_handshake_quarantine {
            return;
        }
        let cycles_elapsed = current_cycle.saturating_sub(session.handshake_at_cycle);
        let window = if matches!(
            session.continuity_claim,
            ContinuityClaim::AttestedContinuity { .. }
        ) {
            config.quarantine_with_continuity
        } else {
            config.post_handshake_quarantine_cycles
        };
        if cycles_elapsed >= window {
            session.in_post_handshake_quarantine = false;
        }
    }
}

/// Check for idle-timeout disconnect (L1/SKIN §4.5).
///
/// If the active operator session has been silent for at least
/// `idle_timeout_cycles`, transitions Active → Idle and returns `true`.
/// Returns `false` if no disconnect occurred.
pub fn check_idle_timeout(
    state: &mut SkinState,
    current_cycle: u64,
    last_envelope_cycle: u64,
    config: &HandshakeConfig,
) -> bool {
    if matches!(state, SkinState::Active(_)) {
        let cycles_since_envelope = current_cycle.saturating_sub(last_envelope_cycle);
        if cycles_since_envelope >= config.idle_timeout_cycles {
            *state = SkinState::Idle;
            return true;
        }
    }
    false
}

#[cfg(test)]
mod tests {
    use super::*;
    use myco_kernel_shared::sealed_derive::SoftwareStub;

    /// Test-only sealed-derive impl that always fails. Used to verify
    /// HandshakeError::SealedDerive propagation path.
    struct AlwaysFailingSealedDerive;

    impl SealedDerive for AlwaysFailingSealedDerive {
        fn derive(
            &self,
            _handshake_nonce: &[u8],
            _current_cycle: u64,
            _kernel_random: &[u8],
        ) -> Result<OperatorToken, SealedDeriveError> {
            Err(SealedDeriveError::BackendUnavailable(
                "test_failure".to_string(),
            ))
        }
    }

    fn make_identity() -> SubstrateIdentityRecord {
        SubstrateIdentityRecord {
            substrate_id: SubstrateId("test_substrate_001".to_string()),
        }
    }

    fn make_initiate(substrate_id: &str) -> HandshakeInitiate {
        HandshakeInitiate {
            envelope_version: 1,
            substrate_id_proof: SubstrateId(substrate_id.to_string()),
            operator_signing_key_public: OperatorSigningKeyPublic(vec![0xdd; 32]),
            continuity_claim: ContinuityClaim::Fresh,
            submitted_at: 1_700_000_000_000_000_000,
        }
    }

    #[test]
    fn test_process_initiate_ok() {
        let identity = make_identity();
        let initiate = make_initiate(&identity.substrate_id.0);
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;

        let complete =
            process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng").unwrap();

        assert_eq!(complete.substrate_id, identity.substrate_id);
        assert_eq!(complete.handshake_timestamp, 100);
        assert!(matches!(state, SkinState::Active(_)));
    }

    #[test]
    fn test_process_initiate_substrate_id_mismatch() {
        let identity = make_identity();
        let initiate = make_initiate("wrong_substrate");
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;

        let result = process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng");
        assert!(matches!(
            result,
            Err(HandshakeError::SubstrateIdMismatch { .. })
        ));
        // State should remain Idle on failure.
        assert!(matches!(state, SkinState::Idle));
    }

    #[test]
    fn test_process_initiate_empty_pubkey_rejected() {
        let identity = make_identity();
        let mut initiate = make_initiate(&identity.substrate_id.0);
        initiate.operator_signing_key_public = OperatorSigningKeyPublic(vec![]);
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;

        let result = process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng");
        assert!(matches!(
            result,
            Err(HandshakeError::InvalidOperatorPubKey(_))
        ));
        assert!(matches!(state, SkinState::Idle));
    }

    #[test]
    fn test_process_initiate_empty_continuity_attestation_rejected() {
        let identity = make_identity();
        let mut initiate = make_initiate(&identity.substrate_id.0);
        initiate.continuity_claim = ContinuityClaim::AttestedContinuity {
            continuity_attestation: vec![],
        };
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;

        let result = process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng");
        assert!(matches!(
            result,
            Err(HandshakeError::InvalidContinuityClaim(_))
        ));
    }

    #[test]
    fn test_process_initiate_skin_busy() {
        let identity = make_identity();
        let initiate1 = make_initiate(&identity.substrate_id.0);
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;

        // First handshake succeeds.
        process_initiate(&mut state, initiate1, &sealed, &identity, 100, b"rng").unwrap();
        assert!(matches!(state, SkinState::Active(_)));

        // Second handshake during active → SkinBusy.
        let initiate2 = make_initiate(&identity.substrate_id.0);
        let result = process_initiate(&mut state, initiate2, &sealed, &identity, 101, b"rng");
        assert!(matches!(result, Err(HandshakeError::SkinBusy)));
        // State should remain Active (the original session).
        assert!(matches!(state, SkinState::Active(_)));
    }

    #[test]
    fn test_process_initiate_fresh_enters_quarantine() {
        let identity = make_identity();
        let initiate = make_initiate(&identity.substrate_id.0);
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;

        process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng").unwrap();

        match state {
            SkinState::Active(s) => assert!(s.in_post_handshake_quarantine),
            _ => panic!("expected Active state"),
        }
    }

    #[test]
    fn test_process_initiate_attested_continuity_still_enters_quarantine() {
        // Per L1/SKIN §4.3: AttestedContinuity shortens window to
        // default 10 cycles, NOT skip entirely. The substrate still enters
        // quarantine; advance_quarantine_window clears it after the short
        // window.
        let identity = make_identity();
        let mut initiate = make_initiate(&identity.substrate_id.0);
        initiate.continuity_claim = ContinuityClaim::AttestedContinuity {
            continuity_attestation: vec![0xff; 64],
        };
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;

        process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng").unwrap();

        // Quarantine flag is set; advance_quarantine_window uses the short window.
        match state {
            SkinState::Active(s) => {
                assert!(s.in_post_handshake_quarantine);
                assert!(matches!(
                    s.continuity_claim,
                    ContinuityClaim::AttestedContinuity { .. }
                ));
            }
            _ => panic!("expected Active state"),
        }
    }

    #[test]
    fn test_operator_token_differs_per_handshake() {
        // Two handshakes (after termination between them) with the same operator
        // pubkey but different cycles should produce different operator tokens.
        let identity = make_identity();
        let sealed = SoftwareStub::new_for_test();

        let mut state = SkinState::Idle;
        let initiate1 = make_initiate(&identity.substrate_id.0);
        let complete1 =
            process_initiate(&mut state, initiate1, &sealed, &identity, 100, b"rng").unwrap();

        // Terminate, then second handshake.
        process_terminate(
            &mut state,
            HandshakeTerminate {
                request_dormancy: None,
            },
        )
        .unwrap();

        let initiate2 = make_initiate(&identity.substrate_id.0);
        let complete2 =
            process_initiate(&mut state, initiate2, &sealed, &identity, 200, b"rng").unwrap();

        // Same operator pubkey + same submitted_at + DIFFERENT cycle → different token
        // (sealed_derive includes current_cycle).
        assert_ne!(complete1.operator_token, complete2.operator_token);
    }

    #[test]
    fn test_process_terminate_ok() {
        let identity = make_identity();
        let initiate = make_initiate(&identity.substrate_id.0);
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;

        process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng").unwrap();

        process_terminate(
            &mut state,
            HandshakeTerminate {
                request_dormancy: Some(DormancyRequest::Paused),
            },
        )
        .unwrap();
        assert!(matches!(state, SkinState::Idle));
    }

    #[test]
    fn test_process_terminate_when_idle_fails() {
        let mut state = SkinState::Idle;
        let result = process_terminate(
            &mut state,
            HandshakeTerminate {
                request_dormancy: None,
            },
        );
        assert!(matches!(result, Err(HandshakeError::WrongState(_))));
    }

    #[test]
    fn test_advance_quarantine_window_clears_after_full_window() {
        let identity = make_identity();
        let initiate = make_initiate(&identity.substrate_id.0);
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;

        process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng").unwrap();

        let config = HandshakeConfig::default();

        // Just before window: still quarantined.
        advance_quarantine_window(
            &mut state,
            100 + config.post_handshake_quarantine_cycles - 1,
            &config,
        );
        if let SkinState::Active(s) = &state {
            assert!(s.in_post_handshake_quarantine);
        } else {
            panic!("expected Active");
        }

        // At/after window: cleared.
        advance_quarantine_window(
            &mut state,
            100 + config.post_handshake_quarantine_cycles,
            &config,
        );
        if let SkinState::Active(s) = &state {
            assert!(!s.in_post_handshake_quarantine);
        } else {
            panic!("expected Active");
        }
    }

    #[test]
    fn test_advance_quarantine_window_attested_continuity_uses_short_window() {
        let identity = make_identity();
        let mut initiate = make_initiate(&identity.substrate_id.0);
        initiate.continuity_claim = ContinuityClaim::AttestedContinuity {
            continuity_attestation: vec![0xab; 32],
        };
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;
        process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng").unwrap();

        let config = HandshakeConfig::default();
        // quarantine_with_continuity default = 10 cycles.

        // At cycle 100 + 9 (just before short window): still in quarantine.
        advance_quarantine_window(
            &mut state,
            100 + config.quarantine_with_continuity - 1,
            &config,
        );
        if let SkinState::Active(s) = &state {
            assert!(s.in_post_handshake_quarantine);
        } else {
            panic!("expected Active");
        }

        // At cycle 100 + 10 (== short window): cleared.
        advance_quarantine_window(&mut state, 100 + config.quarantine_with_continuity, &config);
        if let SkinState::Active(s) = &state {
            assert!(!s.in_post_handshake_quarantine);
        } else {
            panic!("expected Active");
        }

        // Verify that Fresh-claim handshake would NOT have cleared at this
        // same cycle (short window < full window proves they're different).
        let identity = make_identity();
        let initiate = make_initiate(&identity.substrate_id.0);
        let sealed = SoftwareStub::new_for_test();
        let mut state2 = SkinState::Idle;
        process_initiate(&mut state2, initiate, &sealed, &identity, 100, b"rng").unwrap();
        advance_quarantine_window(
            &mut state2,
            100 + config.quarantine_with_continuity,
            &config,
        );
        if let SkinState::Active(s) = &state2 {
            // Fresh quarantine uses full window (100); still in quarantine at cycle 110.
            assert!(s.in_post_handshake_quarantine);
        } else {
            panic!("expected Active");
        }
    }

    #[test]
    fn test_check_idle_timeout_triggers_disconnect() {
        let identity = make_identity();
        let initiate = make_initiate(&identity.substrate_id.0);
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;
        process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng").unwrap();

        let config = HandshakeConfig::default();

        // Recent envelope: no timeout.
        let disconnected = check_idle_timeout(&mut state, 150, 145, &config);
        assert!(!disconnected);
        assert!(matches!(state, SkinState::Active(_)));

        // Long silence: disconnect.
        let disconnected = check_idle_timeout(&mut state, 1000, 100, &config);
        assert!(disconnected);
        assert!(matches!(state, SkinState::Idle));
    }

    #[test]
    fn test_check_idle_timeout_when_idle_is_noop() {
        let mut state = SkinState::Idle;
        let config = HandshakeConfig::default();
        let disconnected = check_idle_timeout(&mut state, 1000, 0, &config);
        assert!(!disconnected);
        assert!(matches!(state, SkinState::Idle));
    }

    #[test]
    fn test_sealed_derive_failure_propagates() {
        let identity = make_identity();
        let initiate = make_initiate(&identity.substrate_id.0);
        let sealed = AlwaysFailingSealedDerive;
        let mut state = SkinState::Idle;

        let result = process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng");
        assert!(matches!(result, Err(HandshakeError::SealedDerive(_))));
        // State remains Idle on sealed-derive failure (handshake never completed).
        assert!(matches!(state, SkinState::Idle));
    }

    #[test]
    fn test_handshake_complete_carries_substrate_id() {
        let identity = make_identity();
        let initiate = make_initiate(&identity.substrate_id.0);
        let sealed = SoftwareStub::new_for_test();
        let mut state = SkinState::Idle;

        let complete =
            process_initiate(&mut state, initiate, &sealed, &identity, 100, b"rng").unwrap();

        // Per L1/SKIN §4.2 step 3 (v0.9 keyless): handshake_complete carries the
        // self-derived substrate-ID for the operator's bidirectional validation
        // (no owner pubkey / birth-attestation / anchor-endpoint fields remain).
        assert_eq!(complete.substrate_id, identity.substrate_id);
    }
}
