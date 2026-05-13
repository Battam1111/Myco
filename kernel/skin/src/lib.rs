//! Myco v0.9 — kernel/skin
//!
//! The substrate's boundary surface. Implements L1_SKIN §1-§6:
//!
//! - **Surface declaration** ([`surface`]) — declared intake/output endpoints
//!   (tier-1 SSoT, L1_HARD_RULES F11 fixed-point). Adding/removing an endpoint
//!   is a CI mutation.
//! - **Envelope schema + integrity check** ([`envelope`]) — every delta arriving
//!   at an intake endpoint is wrapped; substrate validates ONLY the envelope, not
//!   payload content (L0 I8).
//! - **Operator handshake** ([`handshake`]) — bidirectional validation with the
//!   operator (the LLM agent). Substrate generates a non-deterministic
//!   operator_token via OS-mediated `sealed_derive` (per L1_SKIN §4.2 +
//!   pass-3 mycoparasite-1). Operator generates a per-handshake signing keypair
//!   (per L1_SKIN §4.1 + pass-3 mycorrhiza-17 + rhizomorph-1).
//! - **Output gating** ([`output_gate`]) — outputs leave through declared output
//!   endpoints; canonical-bytes discipline for anchor-surface output (per
//!   L0 §9.3 + L1_SKIN §3).
//! - **Network-egress enforcement** ([`egress_enforce`]) — runtime detection of
//!   unauthorized network egress; specific mechanism is L4-platform-pick.
//!   M1 ships a software-only stub that checks against the declared list;
//!   M2+ lands real OS-level enforcement.
//!
//! ## Doctrine traceability
//!
//! - **L0** I6 (universal inclusion), I8 (skin), §9.3 canonical-bytes
//! - **L1_SKIN** §1 (declaration), §2 (envelope), §3 (output gating),
//!   §4 (handshake), §5 (egress enforcement), §6 (breach detection)
//! - **L1_HARD_RULES** C1 (`appetite_locality_breach`),
//!   C2 (`output_endpoint_breach`), C3 (`post_handshake_ci_unattested`),
//!   C4 (`substrate_secret_unsealed`), C11 (`concurrent_operator_persistent`),
//!   F11 (skin-surface declaration fixed-point)
//! - **L3_PACKAGE_MAP** §3 (kernel/skin spec, 4 sub-modules)
//!
//! ## M1 implementation status
//!
//! Logic layer only. Transport layer (TCP / Unix socket / named pipe) is
//! abstracted: callers pass envelopes as parsed structs into the validation
//! functions, and emit envelopes by serializing the output structs. Tokio /
//! async runtime is NOT included in M1; L4 picks the runtime. Persistence of
//! handshake state and surface declaration to SSoT is deferred to M2 with
//! kernel/continuity + kernel/schema.
//!
//! ## What is and is not in M1
//!
//! **In M1**:
//! - Envelope canonical-bytes + HMAC digest validation logic (§2).
//! - Handshake state machine (Idle ↔ Active); single-operator enforcement (§4.4).
//! - Operator-token generation via [`myco_kernel_shared::sealed_derive`] (§4.2).
//! - Output endpoint routing + canonical-bytes discipline at the API boundary (§3).
//! - Software-only egress stub (declared-list check, no syscall-level
//!   enforcement) (§5).
//!
//! **Deferred to M2+**:
//! - Federation peer freshness proof (depends on `kernel/governance` peer-list +
//!   anchor-surface negative-revocation proof). M1 provides a [`output_gate::FederationPeerFreshness`]
//!   trait with a stub impl.
//! - Continuity-attestation cryptographic verification (depends on
//!   `kernel/governance` owner_key_history active prefix). M1 grants the requested
//!   quarantine reduction based on the claim shape; M2 enforces signature.
//! - Real OS-level network-egress enforcement (kernel namespace / eBPF / etc.).
//!   M1 provides a [`egress_enforce::StubEgressEnforce`].
//! - Transport layer (sockets, queues, pipes). L4 platform-pick.

#![warn(missing_docs)]
#![warn(clippy::all)]
#![forbid(unsafe_code)]

pub mod surface;
pub mod envelope;
pub mod handshake;
pub mod output_gate;
pub mod egress_enforce;

/// Crate-level error type, aggregating errors from each sub-module.
///
/// Specific errors per sub-module are defined in each submodule and converted to
/// [`Error`] via [`thiserror::Error::from`].
#[derive(Debug, thiserror::Error)]
#[non_exhaustive]
pub enum Error {
    /// Surface-declaration error.
    #[error("surface: {0}")]
    Surface(#[from] surface::SurfaceError),

    /// Envelope-validation error.
    #[error("envelope: {0}")]
    Envelope(#[from] envelope::EnvelopeError),

    /// Handshake-protocol error.
    #[error("handshake: {0}")]
    Handshake(#[from] handshake::HandshakeError),

    /// Output-gating error.
    #[error("output gate: {0}")]
    OutputGate(#[from] output_gate::OutputError),

    /// Egress-enforcement error.
    #[error("egress: {0}")]
    Egress(#[from] egress_enforce::EgressError),

    /// Shared-kernel error (propagated from `myco-kernel-shared`).
    #[error("shared: {0}")]
    Shared(#[from] myco_kernel_shared::Error),
}

/// Result alias for crate-level operations.
pub type Result<T> = std::result::Result<T, Error>;
