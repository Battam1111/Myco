//! Output endpoint routing + canonical-bytes discipline (L1/SKIN §3).
//!
//! ## Doctrine
//!
//! Outputs leave the substrate through declared output endpoints (L1/SKIN §1
//! declared via [`crate::surface::SkinSurface`]). Per L1/SKIN §3:
//!
//! - Output envelopes are **signed by the substrate** (substrate's signing key
//!   from the identity record). M1 accepts the signature bytes as an opaque
//!   parameter (caller provides). M2 wires the actual signature production via
//!   `kernel/governance` attestation pipeline.
//!
//! - **Canonical-bytes discipline** for anchor-surface output (L0/cards/AS_anchor_surface §3): outputs
//!   to the anchor-surface endpoint carry canonical bytes, NOT substrate-
//!   rendered summaries. The anchor-surface client renders deterministically
//!   for owner review.
//!
//! - **Federation egress freshness check** (L1/SKIN §3.1): every outbound
//!   federation envelope verifies its target peer's freshness + non-revocation
//!   per L1/GOVERNANCE §5.2 **BEFORE emission**. Stale or revoked target →
//!   emission suppressed; `federation_egress_blocked` immune event fruits.
//!
//! - **Forbidden output** (L1/SKIN §3.2): anything outside declared endpoints
//!   is skin breach (`output_endpoint_breach`, L1/HARD_RULES C2 CRITICAL).
//!
//! ## M1 implementation
//!
//! Logic + API-boundary check only. Real transport happens at L4. The
//! [`FederationPeerFreshness`] trait abstracts the freshness check; M1 ships a
//! [`StubPeerFreshness`] that always passes. M2 wires the real check via
//! `kernel/governance` peer-list + anchor-surface negative-revocation proof.

use crate::surface::{Endpoint, EndpointKind, SkinSurface};
use myco_kernel_shared::canonical_bytes::CanonicalBytes;
use thiserror::Error;

/// Output-gating errors.
#[derive(Debug, Error, PartialEq, Eq)]
#[non_exhaustive]
pub enum OutputError {
    /// Target URI is not in the declared output endpoint set
    /// (`output_endpoint_breach`, L1/HARD_RULES C2 CRITICAL).
    #[error("output_endpoint_breach: target {0} not in declared output endpoints")]
    UndeclaredEndpoint(String),

    /// Target URI exists but with a different endpoint kind
    /// (e.g., declared as `FederationOut` but caller routes it as
    /// `AnchorSurfaceOut`). Same CRITICAL grade as undeclared.
    #[error(
        "output_endpoint_breach: kind mismatch at {uri}: expected {expected:?}, declared as {declared:?}"
    )]
    KindMismatch {
        /// Endpoint URI.
        uri: String,
        /// Kind the caller is routing as.
        expected: EndpointKind,
        /// Kind the surface declares.
        declared: EndpointKind,
    },

    /// Federation egress to a stale or revoked peer
    /// (`federation_egress_blocked`, L1/SKIN §6 Elevated).
    #[error("federation_egress_blocked: peer {0} stale or revoked")]
    FederationEgressBlocked(String),

    /// Anchor-surface output was emitted with a substrate-side rendered summary
    /// instead of canonical bytes. Reserved for the future `OutputEnvelope`
    /// constructor that takes either canonical or rendered bytes; M1 forces
    /// canonical at the type level (the payload is [`CanonicalBytes`]) so this
    /// variant is unreachable in M1 but defined for L1/HARD_RULES C18 future
    /// hook.
    #[error(
        "canonical-bytes discipline violation: anchor-surface output must carry canonical bytes"
    )]
    NonCanonicalAnchorOutput,
}

/// A signed output envelope ready for emission.
///
/// Per L1/SKIN §3 outputs are signed by the substrate. M1 stores the signature
/// bytes opaquely. The signature covers `target.uri || canonical_bytes(payload)`
/// canonicalization; the exact signature input format is L4-platform-specific
/// per the chosen signature algorithm (Ed25519, P256, etc.).
#[derive(Debug, Clone)]
pub struct OutputEnvelope {
    /// Target endpoint (must be in declared output list at construction time).
    pub target: Endpoint,

    /// Canonical-bytes payload (per L0/cards/AS_anchor_surface §3 for anchor-surface; for federation
    /// peers also canonical-bytes per L1/GOVERNANCE §5.3 low-entropy
    /// serialization).
    pub payload: CanonicalBytes,

    /// Substrate's signature on the canonical-bytes payload.
    /// Format is L4-platform-specific.
    pub substrate_signature: Vec<u8>,
}

/// Trait for federation peer freshness check (L1/SKIN §3.1).
///
/// Real implementations consult the `kernel/governance` peer-list mirror AND
/// the anchor-surface negative-revocation proof. The substrate's canon caches
/// peer list, but the proof is required for emission, not the cache (per
/// L1/SKIN §3.1).
pub trait FederationPeerFreshness {
    /// Check if the given peer endpoint URI has a fresh, non-revoked
    /// attestation. Returns `Ok(())` if fresh; `Err(FederationEgressBlocked)`
    /// if stale or revoked.
    fn check_freshness(&self, peer_uri: &str) -> Result<(), OutputError>;
}

/// Stub peer-freshness checker — always returns fresh.
///
/// **M1 ONLY.** The real check (per L1/SKIN §3.1) requires:
///
/// - `kernel/governance` peer-attestation-list (substrate-cached mirror) AND
/// - Anchor-surface negative-revocation proof (freshness oracle).
///
/// M2 ships [`crate::output_gate::AnchorSurfaceProofChecker`] (TBD) which
/// replaces this stub. Production substrates MUST NOT ship with this stub.
pub struct StubPeerFreshness;

impl FederationPeerFreshness for StubPeerFreshness {
    fn check_freshness(&self, _peer_uri: &str) -> Result<(), OutputError> {
        Ok(())
    }
}

/// Always-blocked peer-freshness checker.
///
/// Useful for tests + the "all peers stale" scenario; production code should
/// use a real impl.
pub struct DenyAllPeerFreshness;

impl FederationPeerFreshness for DenyAllPeerFreshness {
    fn check_freshness(&self, peer_uri: &str) -> Result<(), OutputError> {
        Err(OutputError::FederationEgressBlocked(peer_uri.to_string()))
    }
}

/// **C13 — owner-revocation-aware peer-freshness checker** (L1/GOVERNANCE §5.2
/// + L1/HARD_RULES C13 `peer_attestation_revoked_egress`).
///
/// A real [`FederationPeerFreshness`] impl that blocks egress to any peer whose
/// endpoint URI is on the owner-revocation set, and passes everyone else. This
/// replaces the conceptual role of [`StubPeerFreshness`] (which always passes)
/// for the revocation dimension of the §3.1 check.
///
/// **Wiring note (skin-trait vs substrate-side).** In the live Myco substrate
/// the authoritative federation egress site is substrate-side
/// (`substrate::federation::FederationState::progress_peers`), where the
/// DAG-derived revoked-set (`ServerState::revoked_federation_peers`, keyed by
/// `substrate_id`) is reachable; that is where the production C13 block fires
/// pre-emission. The substrate does NOT route its federation egress through
/// this skin trait (the trait is an L1/SKIN §3.1 abstraction with no live
/// substrate consumer today). This impl therefore makes the skin trait itself
/// revocation-honest — so a future caller that DOES route through the skin gate
/// has a correct, non-stub checker to use — and keeps the §3.1 contract
/// faithful: the freshness oracle blocks revoked targets. The revoked identity
/// here is matched by endpoint URI (the skin layer's notion of a peer);
/// substrate-side matching is by `substrate_id`.
pub struct RevokedPeerFreshness<'a> {
    /// The set of revoked peer endpoint URIs. Egress to any URI in this set is
    /// blocked with [`OutputError::FederationEgressBlocked`].
    pub revoked_peer_uris: &'a std::collections::HashSet<String>,
}

impl FederationPeerFreshness for RevokedPeerFreshness<'_> {
    fn check_freshness(&self, peer_uri: &str) -> Result<(), OutputError> {
        if self.revoked_peer_uris.contains(peer_uri) {
            Err(OutputError::FederationEgressBlocked(peer_uri.to_string()))
        } else {
            Ok(())
        }
    }
}

/// Construct an output envelope, performing all L1/SKIN §3 checks.
///
/// Checks (in order):
///
/// 1. Target URI declared as an output endpoint of the requested kind
///    (`UndeclaredEndpoint` or `KindMismatch` on failure).
/// 2. For `FederationOut`: peer freshness via [`FederationPeerFreshness`].
///
/// On success: returns a constructed [`OutputEnvelope`] ready for transport.
pub fn route_output<F: FederationPeerFreshness>(
    surface: &SkinSurface,
    target_uri: &str,
    target_kind: EndpointKind,
    payload: CanonicalBytes,
    substrate_signature: Vec<u8>,
    peer_freshness: &F,
) -> Result<OutputEnvelope, OutputError> {
    // L1/SKIN §3.2: target must be declared as output of requested kind.
    if !surface.is_declared_output(target_uri, &target_kind) {
        if let Some(existing) = surface.find_output_by_uri(target_uri) {
            return Err(OutputError::KindMismatch {
                uri: target_uri.to_string(),
                expected: target_kind,
                declared: existing.kind.clone(),
            });
        }
        return Err(OutputError::UndeclaredEndpoint(target_uri.to_string()));
    }

    // L1/SKIN §3.1: federation egress freshness BEFORE emission.
    if target_kind == EndpointKind::FederationOut {
        peer_freshness.check_freshness(target_uri)?;
    }

    Ok(OutputEnvelope {
        target: Endpoint {
            uri: target_uri.to_string(),
            kind: target_kind,
        },
        payload,
        substrate_signature,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::surface::{Endpoint, EndpointKind, SkinSurface};

    fn make_surface() -> SkinSurface {
        SkinSurface::from_endpoints(
            vec![Endpoint {
                uri: "tcp://intake".into(),
                kind: EndpointKind::Intake,
            }],
            vec![
                Endpoint {
                    uri: "https://anchor".into(),
                    kind: EndpointKind::AnchorSurfaceOut,
                },
                Endpoint {
                    uri: "tcp://peer1".into(),
                    kind: EndpointKind::FederationOut,
                },
                Endpoint {
                    uri: "tcp://peer2".into(),
                    kind: EndpointKind::FederationOut,
                },
                Endpoint {
                    uri: "https://summary".into(),
                    kind: EndpointKind::SummaryExportOut,
                },
            ],
        )
        .unwrap()
    }

    fn dummy_payload() -> CanonicalBytes {
        CanonicalBytes(vec![0x01, 0x02, 0x03])
    }

    #[test]
    fn test_route_anchor_output_ok() {
        let s = make_surface();
        let env = route_output(
            &s,
            "https://anchor",
            EndpointKind::AnchorSurfaceOut,
            dummy_payload(),
            vec![0xff; 64],
            &StubPeerFreshness,
        )
        .unwrap();
        assert_eq!(env.target.uri, "https://anchor");
        assert_eq!(env.target.kind, EndpointKind::AnchorSurfaceOut);
        assert_eq!(env.substrate_signature.len(), 64);
    }

    #[test]
    fn test_route_federation_output_ok_with_fresh_peer() {
        let s = make_surface();
        let env = route_output(
            &s,
            "tcp://peer1",
            EndpointKind::FederationOut,
            dummy_payload(),
            vec![0xab; 64],
            &StubPeerFreshness,
        )
        .unwrap();
        assert_eq!(env.target.uri, "tcp://peer1");
        assert_eq!(env.target.kind, EndpointKind::FederationOut);
    }

    #[test]
    fn test_route_summary_export_ok() {
        let s = make_surface();
        route_output(
            &s,
            "https://summary",
            EndpointKind::SummaryExportOut,
            dummy_payload(),
            vec![0; 32],
            &StubPeerFreshness,
        )
        .unwrap();
    }

    #[test]
    fn test_route_undeclared_endpoint_rejected() {
        let s = make_surface();
        let result = route_output(
            &s,
            "https://attacker.evil",
            EndpointKind::AnchorSurfaceOut,
            dummy_payload(),
            vec![0; 32],
            &StubPeerFreshness,
        );
        assert_eq!(
            result.unwrap_err(),
            OutputError::UndeclaredEndpoint("https://attacker.evil".into())
        );
    }

    #[test]
    fn test_route_kind_mismatch_rejected() {
        let s = make_surface();
        // peer1 is declared as FederationOut; routing as AnchorSurfaceOut →
        // KindMismatch.
        let result = route_output(
            &s,
            "tcp://peer1",
            EndpointKind::AnchorSurfaceOut,
            dummy_payload(),
            vec![0; 32],
            &StubPeerFreshness,
        );
        assert!(matches!(
            result,
            Err(OutputError::KindMismatch {
                expected: EndpointKind::AnchorSurfaceOut,
                declared: EndpointKind::FederationOut,
                ..
            })
        ));
    }

    #[test]
    fn test_route_intake_uri_as_output_rejected() {
        let s = make_surface();
        // tcp://intake is an Intake endpoint; trying to route as output → not
        // in is_declared_output for any output kind. Since it's not in output
        // at all (find_output_by_uri returns None), error is UndeclaredEndpoint.
        let result = route_output(
            &s,
            "tcp://intake",
            EndpointKind::FederationOut,
            dummy_payload(),
            vec![0; 32],
            &StubPeerFreshness,
        );
        assert_eq!(
            result.unwrap_err(),
            OutputError::UndeclaredEndpoint("tcp://intake".into())
        );
    }

    #[test]
    fn test_federation_egress_blocked_on_stale_peer() {
        let s = make_surface();
        let result = route_output(
            &s,
            "tcp://peer1",
            EndpointKind::FederationOut,
            dummy_payload(),
            vec![0; 32],
            &DenyAllPeerFreshness,
        );
        assert_eq!(
            result.unwrap_err(),
            OutputError::FederationEgressBlocked("tcp://peer1".into())
        );
    }

    #[test]
    fn test_c13_revoked_peer_freshness_blocks_revoked_passes_others() {
        // **C13** — RevokedPeerFreshness blocks egress to a revoked peer URI
        // (FederationEgressBlocked) and passes a non-revoked peer.
        let s = make_surface();
        let mut revoked = std::collections::HashSet::new();
        revoked.insert("tcp://peer1".to_string());
        let checker = RevokedPeerFreshness {
            revoked_peer_uris: &revoked,
        };
        // peer1 is revoked → egress blocked.
        let blocked = route_output(
            &s,
            "tcp://peer1",
            EndpointKind::FederationOut,
            dummy_payload(),
            vec![0; 32],
            &checker,
        );
        assert_eq!(
            blocked.unwrap_err(),
            OutputError::FederationEgressBlocked("tcp://peer1".into()),
            "egress to a revoked peer must be blocked with FederationEgressBlocked"
        );
        // peer2 is NOT revoked → egress allowed.
        let ok = route_output(
            &s,
            "tcp://peer2",
            EndpointKind::FederationOut,
            dummy_payload(),
            vec![0; 32],
            &checker,
        );
        assert!(
            ok.is_ok(),
            "egress to a non-revoked peer must pass the C13 freshness check"
        );
    }

    #[test]
    fn test_c13_empty_revocation_set_passes_all() {
        // An empty revocation set blocks nobody (revocation is opt-in per peer).
        let s = make_surface();
        let revoked = std::collections::HashSet::new();
        let checker = RevokedPeerFreshness {
            revoked_peer_uris: &revoked,
        };
        for uri in ["tcp://peer1", "tcp://peer2"] {
            assert!(
                route_output(
                    &s,
                    uri,
                    EndpointKind::FederationOut,
                    dummy_payload(),
                    vec![0; 32],
                    &checker,
                )
                .is_ok(),
                "empty revocation set must not block {uri}"
            );
        }
    }

    #[test]
    fn test_non_federation_skips_freshness_check() {
        // DenyAllPeerFreshness would block ANY federation egress; but
        // anchor-surface routing should not invoke freshness at all.
        let s = make_surface();
        let result = route_output(
            &s,
            "https://anchor",
            EndpointKind::AnchorSurfaceOut,
            dummy_payload(),
            vec![0; 32],
            &DenyAllPeerFreshness,
        );
        // Should succeed because freshness is NOT consulted for non-federation.
        assert!(result.is_ok());
    }

    #[test]
    fn test_payload_preserved_in_output_envelope() {
        let s = make_surface();
        let payload = CanonicalBytes(vec![0x42; 100]);
        let env = route_output(
            &s,
            "https://anchor",
            EndpointKind::AnchorSurfaceOut,
            payload.clone(),
            vec![0; 32],
            &StubPeerFreshness,
        )
        .unwrap();
        assert_eq!(env.payload, payload);
    }

    #[test]
    fn test_empty_surface_blocks_all_outputs() {
        let s = SkinSurface::new();
        let result = route_output(
            &s,
            "anywhere",
            EndpointKind::AnchorSurfaceOut,
            dummy_payload(),
            vec![0; 32],
            &StubPeerFreshness,
        );
        assert!(matches!(result, Err(OutputError::UndeclaredEndpoint(_))));
    }
}
