//! Skin surface declaration (L1_SKIN §1 + L1_HARD_RULES F11).
//!
//! ## Doctrine
//!
//! The substrate has exactly one declared skin surface in SSoT (tier-1 field).
//! The surface lists:
//!
//! - **Intake endpoints** — where deltas enter (e.g., Unix socket, named pipe,
//!   TCP port).
//! - **Output endpoints** — where outputs exit (federation peers, anchor-surface
//!   endpoint, optional summary export).
//! - **Forbidden surfaces** — implicit "everything else is breach"; enforced by
//!   the [`crate::egress_enforce`] module + the [`crate::output_gate`] routing
//!   check.
//!
//! Skin surface is a **contract-identity-level fixed point** (L1_HARD_RULES F11):
//! mutating the declared endpoint set requires owner-attested CI envelope.
//! Substrate cannot silently add an endpoint.
//!
//! ## M1 implementation
//!
//! In-memory representation. M2 lands persistence to SSoT via `kernel/schema`,
//! and CI-mutation enforcement via `kernel/governance` classifier.

use std::collections::HashSet;
use thiserror::Error;

/// Surface-declaration errors.
#[derive(Debug, Error, PartialEq, Eq)]
#[non_exhaustive]
pub enum SurfaceError {
    /// Endpoint URI is empty or malformed.
    #[error("invalid endpoint: {0}")]
    InvalidEndpoint(String),

    /// Duplicate endpoint URI in the declared set (across intake + output).
    #[error("duplicate endpoint URI: {0}")]
    DuplicateEndpoint(String),
}

/// Endpoint kind tag.
///
/// L1_SKIN §1 enumerates intake vs output; output further split into federation
/// vs anchor-surface vs optional summary-export. The kind tag drives routing
/// in [`crate::output_gate`] and enforcement in [`crate::egress_enforce`].
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum EndpointKind {
    /// Delta intake — receives [`crate::envelope::Envelope`] from an operator.
    Intake,
    /// Federation egress — outbound to a peer substrate.
    FederationOut,
    /// Anchor-surface output — canonical-bytes-discipline-mandated outputs to
    /// the owner-controlled anchor surface (per L0 §9.3 + L1_SKIN §3).
    AnchorSurfaceOut,
    /// Optional summary export — outbound to owner-readable summary log
    /// (canonical-bytes still required; renderer-readable derivative).
    SummaryExportOut,
}

/// An endpoint declaration.
///
/// The URI is L4-platform-specific (e.g., `tcp://0.0.0.0:9091`,
/// `unix:///var/run/myco.sock`, `https://anchor.example.com/v1/attest`).
/// M1 stores it as an opaque string; L4 implementations parse it for transport.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Endpoint {
    /// Endpoint URI / connection string.
    pub uri: String,

    /// Endpoint kind (intake / output kind).
    pub kind: EndpointKind,
}

/// The declared skin surface — tier-1 SSoT, F11 fixed-point.
///
/// Substrate cannot mutate this except via owner-attested CI envelope (enforced
/// at the classifier in `kernel/governance`).
#[derive(Debug, Clone, Default)]
pub struct SkinSurface {
    intake: Vec<Endpoint>,
    output: Vec<Endpoint>,
}

impl SkinSurface {
    /// Construct an empty surface.
    ///
    /// An empty surface has no intake (substrate cannot receive deltas) and
    /// no output (substrate cannot emit). Used only as a starting state in
    /// substrate genesis; the owner-attested genesis envelope populates it.
    pub fn new() -> Self {
        SkinSurface {
            intake: Vec::new(),
            output: Vec::new(),
        }
    }

    /// Construct from explicit intake + output endpoint lists.
    ///
    /// Validates:
    /// - No endpoint URI is empty.
    /// - No URI appears more than once across the combined intake+output set.
    /// - All intake endpoints have [`EndpointKind::Intake`].
    /// - All output endpoints have a non-Intake kind.
    pub fn from_endpoints(
        intake: Vec<Endpoint>,
        output: Vec<Endpoint>,
    ) -> Result<Self, SurfaceError> {
        let mut seen = HashSet::new();
        for ep in intake.iter().chain(output.iter()) {
            if ep.uri.is_empty() {
                return Err(SurfaceError::InvalidEndpoint("empty uri".to_string()));
            }
            if !seen.insert(ep.uri.clone()) {
                return Err(SurfaceError::DuplicateEndpoint(ep.uri.clone()));
            }
        }
        for ep in intake.iter() {
            if ep.kind != EndpointKind::Intake {
                return Err(SurfaceError::InvalidEndpoint(format!(
                    "intake list endpoint {} has non-intake kind {:?}",
                    ep.uri, ep.kind
                )));
            }
        }
        for ep in output.iter() {
            if ep.kind == EndpointKind::Intake {
                return Err(SurfaceError::InvalidEndpoint(format!(
                    "output list endpoint {} has Intake kind",
                    ep.uri
                )));
            }
        }
        Ok(SkinSurface { intake, output })
    }

    /// Declared intake endpoints.
    pub fn intake(&self) -> &[Endpoint] {
        &self.intake
    }

    /// Declared output endpoints.
    pub fn output(&self) -> &[Endpoint] {
        &self.output
    }

    /// Whether a URI is declared as an intake endpoint.
    pub fn is_declared_intake(&self, uri: &str) -> bool {
        self.intake.iter().any(|e| e.uri == uri)
    }

    /// Whether a URI is declared as an output endpoint of the given kind.
    pub fn is_declared_output(&self, uri: &str, kind: &EndpointKind) -> bool {
        self.output.iter().any(|e| e.uri == uri && &e.kind == kind)
    }

    /// Find an output endpoint by URI (any kind). Useful for distinguishing
    /// "URI unknown" from "URI present but wrong kind" in error messages.
    pub fn find_output_by_uri(&self, uri: &str) -> Option<&Endpoint> {
        self.output.iter().find(|e| e.uri == uri)
    }

    /// Total declared endpoint count (intake + output).
    pub fn endpoint_count(&self) -> usize {
        self.intake.len() + self.output.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_empty_surface() {
        let s = SkinSurface::new();
        assert!(s.intake().is_empty());
        assert!(s.output().is_empty());
        assert_eq!(s.endpoint_count(), 0);
    }

    #[test]
    fn test_default_is_empty() {
        let s = SkinSurface::default();
        assert_eq!(s.endpoint_count(), 0);
    }

    #[test]
    fn test_from_endpoints_ok() {
        let intake = vec![Endpoint {
            uri: "tcp://0.0.0.0:9091".into(),
            kind: EndpointKind::Intake,
        }];
        let output = vec![
            Endpoint {
                uri: "https://anchor.example".into(),
                kind: EndpointKind::AnchorSurfaceOut,
            },
            Endpoint {
                uri: "tcp://peer1:9092".into(),
                kind: EndpointKind::FederationOut,
            },
            Endpoint {
                uri: "https://summary.example".into(),
                kind: EndpointKind::SummaryExportOut,
            },
        ];
        let s = SkinSurface::from_endpoints(intake, output).unwrap();
        assert_eq!(s.intake().len(), 1);
        assert_eq!(s.output().len(), 3);
        assert_eq!(s.endpoint_count(), 4);
    }

    #[test]
    fn test_duplicate_uri_rejected() {
        let intake = vec![Endpoint {
            uri: "tcp://x".into(),
            kind: EndpointKind::Intake,
        }];
        let output = vec![Endpoint {
            uri: "tcp://x".into(), // same URI
            kind: EndpointKind::FederationOut,
        }];
        let result = SkinSurface::from_endpoints(intake, output);
        assert_eq!(
            result.unwrap_err(),
            SurfaceError::DuplicateEndpoint("tcp://x".into())
        );
    }

    #[test]
    fn test_empty_uri_rejected() {
        let intake = vec![Endpoint {
            uri: "".into(),
            kind: EndpointKind::Intake,
        }];
        let result = SkinSurface::from_endpoints(intake, vec![]);
        assert!(matches!(result, Err(SurfaceError::InvalidEndpoint(_))));
    }

    #[test]
    fn test_is_declared_intake() {
        let intake = vec![Endpoint {
            uri: "tcp://x".into(),
            kind: EndpointKind::Intake,
        }];
        let s = SkinSurface::from_endpoints(intake, vec![]).unwrap();
        assert!(s.is_declared_intake("tcp://x"));
        assert!(!s.is_declared_intake("tcp://y"));
    }

    #[test]
    fn test_is_declared_output_kind_sensitive() {
        let output = vec![Endpoint {
            uri: "https://a".into(),
            kind: EndpointKind::AnchorSurfaceOut,
        }];
        let s = SkinSurface::from_endpoints(vec![], output).unwrap();
        assert!(s.is_declared_output("https://a", &EndpointKind::AnchorSurfaceOut));
        // Wrong kind: same URI but FederationOut → not declared.
        assert!(!s.is_declared_output("https://a", &EndpointKind::FederationOut));
    }

    #[test]
    fn test_intake_kind_check_rejects_wrong_kind() {
        // Intake list with an AnchorSurfaceOut-kinded endpoint → reject.
        let intake = vec![Endpoint {
            uri: "x".into(),
            kind: EndpointKind::AnchorSurfaceOut,
        }];
        let result = SkinSurface::from_endpoints(intake, vec![]);
        assert!(matches!(result, Err(SurfaceError::InvalidEndpoint(_))));
    }

    #[test]
    fn test_output_kind_check_rejects_intake_kind() {
        // Output list with an Intake-kinded endpoint → reject.
        let output = vec![Endpoint {
            uri: "x".into(),
            kind: EndpointKind::Intake,
        }];
        let result = SkinSurface::from_endpoints(vec![], output);
        assert!(matches!(result, Err(SurfaceError::InvalidEndpoint(_))));
    }

    #[test]
    fn test_find_output_by_uri() {
        let output = vec![Endpoint {
            uri: "https://peer".into(),
            kind: EndpointKind::FederationOut,
        }];
        let s = SkinSurface::from_endpoints(vec![], output).unwrap();
        let found = s.find_output_by_uri("https://peer").unwrap();
        assert_eq!(found.kind, EndpointKind::FederationOut);
        assert!(s.find_output_by_uri("https://missing").is_none());
    }

    #[test]
    fn test_clone_preserves_endpoints() {
        let intake = vec![Endpoint {
            uri: "x".into(),
            kind: EndpointKind::Intake,
        }];
        let s = SkinSurface::from_endpoints(intake, vec![]).unwrap();
        let s2 = s.clone();
        assert_eq!(s2.intake(), s.intake());
    }
}
