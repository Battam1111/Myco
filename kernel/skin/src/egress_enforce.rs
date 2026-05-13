//! Network-egress enforcement (L1_SKIN §5).
//!
//! ## Doctrine
//!
//! The substrate process operates within a **network-egress enforcement
//! boundary** that permits exactly the L1_SKIN §1 declared output endpoints.
//! Unauthorized egress = breach (`appetite_locality_breach`, L1_HARD_RULES C1
//! CRITICAL grade).
//!
//! ### What this enforces
//!
//! - Appetite update-rules that secretly call out (mycoparasite-8 trojan).
//! - Embedding service calls outside declared endpoints.
//! - Covert exfiltration via arbitrary protocol.
//!
//! ### What this does NOT enforce
//!
//! - The agent (qua maintainer) modifying substrate code to remove enforcement
//!   — that's a CI-level mutation, enforced at `kernel/governance` classifier.
//! - Host-level adversarial action — substrate cannot enforce against its own
//!   host process. Owner's monitoring responsibility (per L0 §6).
//! - Covert channels within legitimate federation envelopes — addressed by
//!   L1_GOVERNANCE §5.3 rate-limiting + canonical low-entropy serialization,
//!   not by egress detection.
//!
//! ## L4 enforcement mechanism (not picked at L1)
//!
//! L1_SKIN §5 lists four candidate enforcement families:
//!
//! 1. **Kernel-level** — Linux network namespace, Windows Filtering Platform.
//! 2. **Container-level** — iptables/nftables filter on the container egress.
//! 3. **Syscall-level** — eBPF / ptrace / seccomp socket-syscall filter.
//! 4. **Userspace proxy** — application-layer egress proxy with allowlist.
//!
//! Each has different threat-model assumptions and operational costs. L4
//! picks per substrate deployment; this module abstracts via the
//! [`EgressEnforce`] trait.
//!
//! ## M1 implementation
//!
//! [`StubEgressEnforce`] is a **software-only stub** — it checks against the
//! declared output URI list in-memory. Production substrates plug in a real
//! mechanism from the four families above.

use crate::surface::SkinSurface;
use thiserror::Error;

/// Egress-enforcement errors.
#[derive(Debug, Error, PartialEq, Eq)]
#[non_exhaustive]
pub enum EgressError {
    /// Outbound connection target is not in the declared output endpoint set
    /// (`appetite_locality_breach`, L1_HARD_RULES C1 CRITICAL).
    #[error("appetite_locality_breach: egress to {0} not in declared output endpoints")]
    UnauthorizedEgress(String),
}

/// Network-egress enforcement trait.
///
/// Real implementations intercept actual network syscalls or maintain a kernel/
/// container-level filter. The [`check_outbound`](EgressEnforce::check_outbound)
/// method is the policy-check API, which is what application-layer code
/// queries before initiating a connection AND what the kernel-level interceptor
/// consults on each socket-syscall.
///
/// ## L1_HARD_RULES C1 mapping
///
/// A `false` return from [`check_outbound`](EgressEnforce::check_outbound) MUST
/// trigger the `appetite_locality_breach` immune sporocarp emission at the
/// caller (CRITICAL grade → auto-quarantine via `kernel/continuity` quarantine
/// state).
pub trait EgressEnforce {
    /// Check whether an outbound connection to `target_uri` is authorized.
    ///
    /// Returns:
    /// - `Ok(())` if `target_uri` is in the declared output endpoint set.
    /// - `Err(EgressError::UnauthorizedEgress)` otherwise.
    fn check_outbound(&self, target_uri: &str) -> Result<(), EgressError>;
}

/// Software-only stub egress enforcer (M1 development).
///
/// **NOT PRODUCTION-SAFE.**
///
/// This is a logic-only check against the declared output endpoint list. It
/// does NOT actually intercept network syscalls — an adversarial agent that
/// bypasses the policy-check API (e.g., by directly invoking system call APIs
/// or using transport libraries that don't consult this API) can exfiltrate.
///
/// Per L1_SKIN §5, the substrate cannot enforce against its own host process;
/// this stub is useful for M1 unit-testing the policy logic, but production
/// substrates MUST pick one of the four L1_SKIN §5 enforcement families and
/// implement [`EgressEnforce`] against it.
pub struct StubEgressEnforce {
    declared_output_uris: Vec<String>,
}

impl StubEgressEnforce {
    /// Construct from the declared skin surface — captures the output URI set.
    pub fn from_surface(surface: &SkinSurface) -> Self {
        let declared_output_uris = surface.output().iter().map(|e| e.uri.clone()).collect();
        StubEgressEnforce {
            declared_output_uris,
        }
    }

    /// Construct from an explicit URI list (useful for tests).
    pub fn from_uris(uris: Vec<String>) -> Self {
        StubEgressEnforce {
            declared_output_uris: uris,
        }
    }
}

impl EgressEnforce for StubEgressEnforce {
    fn check_outbound(&self, target_uri: &str) -> Result<(), EgressError> {
        if self.declared_output_uris.iter().any(|d| d == target_uri) {
            Ok(())
        } else {
            Err(EgressError::UnauthorizedEgress(target_uri.to_string()))
        }
    }
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
            ],
        )
        .unwrap()
    }

    #[test]
    fn test_stub_allows_declared_anchor() {
        let s = make_surface();
        let e = StubEgressEnforce::from_surface(&s);
        e.check_outbound("https://anchor").unwrap();
    }

    #[test]
    fn test_stub_allows_declared_peer() {
        let s = make_surface();
        let e = StubEgressEnforce::from_surface(&s);
        e.check_outbound("tcp://peer1").unwrap();
    }

    #[test]
    fn test_stub_blocks_undeclared() {
        let s = make_surface();
        let e = StubEgressEnforce::from_surface(&s);
        let result = e.check_outbound("https://attacker.evil");
        assert_eq!(
            result.unwrap_err(),
            EgressError::UnauthorizedEgress("https://attacker.evil".into())
        );
    }

    #[test]
    fn test_stub_blocks_intake_uri() {
        // Intake URIs are inbound — they should not be valid outbound targets.
        let s = make_surface();
        let e = StubEgressEnforce::from_surface(&s);
        let result = e.check_outbound("tcp://intake");
        assert_eq!(
            result.unwrap_err(),
            EgressError::UnauthorizedEgress("tcp://intake".into())
        );
    }

    #[test]
    fn test_stub_empty_surface_blocks_everything() {
        let s = SkinSurface::new();
        let e = StubEgressEnforce::from_surface(&s);
        let result = e.check_outbound("anywhere");
        assert!(matches!(result, Err(EgressError::UnauthorizedEgress(_))));
    }

    #[test]
    fn test_stub_from_uris() {
        let e = StubEgressEnforce::from_uris(vec!["a".into(), "b".into()]);
        e.check_outbound("a").unwrap();
        e.check_outbound("b").unwrap();
        assert!(e.check_outbound("c").is_err());
    }
}
