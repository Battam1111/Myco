//! Cold-resume protocol (L1_CONTINUITY §3 — canonical owner).
//!
//! ## Doctrine
//!
//! Per L1_CONTINUITY §3.1: before accepting an operator handshake on a
//! substrate in dormant or freshly-loaded state, the substrate runs:
//!
//! 1. I1 check: substrate-ID + owner-signature integrity.
//! 2. I3 check: SSoT consistency at tier-1 fields.
//! 3. I4 check: DAG-tip hash + Merkle chain self-consistency.
//! 4. I5 check: reachability over current SSoT-listed tiers (deep-cycle scope).
//! 5. I8 check: skin declaration matches expected canon.
//!
//! **Witnesses, not verdicts** (per L0 §9.3 + pass-2 mycoparasite-32):
//! check results are emitted as cryptographic-proof tuples the owner /
//! anchor-surface verifier can independently re-derive. Substrate emits
//! evidence, not verdicts.
//!
//! On any check failure: substrate enters `alive but quarantined` (per §3.2);
//! quarantine_clearance is required for resumption (per §3.3).
//!
//! ## M3 scope
//!
//! This module ships the **check orchestration + witness-tuple shape**.
//! The actual per-check logic depends on cross-crate access (kernel/schema
//! for SSoT + DAG, kernel/skin for surface declaration). M3 provides trait
//! stubs; M4 wires concrete implementations.

use myco_kernel_shared::canonical_bytes::CanonicalBytes;
use myco_kernel_shared::crypto::NodeHash;
use thiserror::Error;

/// Cold-resume errors.
#[derive(Debug, Error)]
#[non_exhaustive]
pub enum ColdResumeError {
    /// One or more pre-handshake checks failed. Substrate must enter
    /// quarantine before accepting operator handshakes.
    #[error("cold_resume_invariant_failure: {failed_checks:?}")]
    InvariantFailure {
        /// List of failed check identifiers.
        failed_checks: Vec<ColdResumeCheckId>,
    },

    /// Witness computation failed (e.g., couldn't compute Merkle path).
    #[error("witness computation failed: {0}")]
    WitnessComputationFailed(String),
}

/// Identifier for each pre-handshake check.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ColdResumeCheckId {
    /// I1 check: substrate-ID + owner-signature integrity.
    I1IdentityIntegrity,
    /// I3 check: SSoT consistency at tier-1 fields.
    I3SsotConsistency,
    /// I4 check: DAG-tip hash + Merkle chain self-consistency.
    I4DagSelfConsistency,
    /// I5 check: reachability over current SSoT-listed tiers.
    I5Reachability,
    /// I8 check: skin declaration matches expected canon.
    I8SkinDeclaration,
}

impl std::fmt::Display for ColdResumeCheckId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let name = match self {
            ColdResumeCheckId::I1IdentityIntegrity => "i1_identity_integrity",
            ColdResumeCheckId::I3SsotConsistency => "i3_ssot_consistency",
            ColdResumeCheckId::I4DagSelfConsistency => "i4_dag_self_consistency",
            ColdResumeCheckId::I5Reachability => "i5_reachability",
            ColdResumeCheckId::I8SkinDeclaration => "i8_skin_declaration",
        };
        f.write_str(name)
    }
}

/// A cryptographic witness tuple for a single cold-resume check.
///
/// Per L0 §9.3: substrate emits canonical-bytes witnesses; anchor-surface
/// verifier independently re-derives. The witness MUST be sufficient for
/// independent re-derivation (sampled hashes / Merkle paths / parent hashes
/// / check inputs).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CheckWitness {
    /// Which check this witness corresponds to.
    pub check_id: ColdResumeCheckId,
    /// Whether the check passed (the substrate's own verdict; the
    /// authoritative verdict is the verifier's re-derivation).
    pub passed: bool,
    /// Canonical-bytes payload carrying the check inputs + intermediate
    /// values the verifier needs.
    pub witness_canonical_bytes: CanonicalBytes,
    /// Hash of `witness_canonical_bytes` for indexing / observability.
    pub witness_hash: NodeHash,
}

/// Full cold-resume report — a tuple of witnesses for all 5 checks.
///
/// Per L1_CONTINUITY §3.1: these witnesses land in:
///
/// - The handshake-response envelope (per L1_SKIN §4.2 step 3
///   substrate→operator attestation).
/// - The anchor-surface inbound channel for owner-side audit.
#[derive(Debug, Clone)]
pub struct ColdResumeReport {
    /// Witnesses for each of the 5 checks.
    pub witnesses: Vec<CheckWitness>,
    /// Whether ALL checks passed (substrate's view).
    pub all_passed: bool,
    /// Substrate metabolic-cycle at which the report was generated.
    pub at_cycle: u64,
}

impl ColdResumeReport {
    /// List of failed check IDs (empty if all passed).
    pub fn failed_checks(&self) -> Vec<ColdResumeCheckId> {
        self.witnesses
            .iter()
            .filter(|w| !w.passed)
            .map(|w| w.check_id)
            .collect()
    }
}

/// Trait stubs for the 5 cold-resume checks. M3 ships the orchestration
/// logic; concrete implementations land at M4 with cross-crate integration.
pub trait I1IdentityCheck {
    /// Run the I1 identity-integrity check; return a [`CheckWitness`].
    fn check(&mut self) -> Result<CheckWitness, ColdResumeError>;
}

/// I3 SSoT consistency check.
pub trait I3SsotCheck {
    /// Run the I3 SSoT consistency check.
    fn check(&mut self) -> Result<CheckWitness, ColdResumeError>;
}

/// I4 DAG self-consistency check.
pub trait I4DagCheck {
    /// Run the I4 DAG self-consistency check.
    fn check(&mut self) -> Result<CheckWitness, ColdResumeError>;
}

/// I5 reachability check.
pub trait I5ReachabilityCheck {
    /// Run the I5 reachability check.
    fn check(&mut self) -> Result<CheckWitness, ColdResumeError>;
}

/// I8 skin declaration check.
pub trait I8SkinCheck {
    /// Run the I8 skin declaration check.
    fn check(&mut self) -> Result<CheckWitness, ColdResumeError>;
}

/// Bundle of all 5 check implementations.
pub struct ColdResumeCheckers<'a> {
    /// I1 checker.
    pub i1: &'a mut dyn I1IdentityCheck,
    /// I3 checker.
    pub i3: &'a mut dyn I3SsotCheck,
    /// I4 checker.
    pub i4: &'a mut dyn I4DagCheck,
    /// I5 checker.
    pub i5: &'a mut dyn I5ReachabilityCheck,
    /// I8 checker.
    pub i8: &'a mut dyn I8SkinCheck,
}

/// Run cold-resume protocol: invoke all 5 checks, collect witnesses,
/// return a report.
///
/// All 5 checks are run even if early ones fail (so the full witness
/// tuple lands at the anchor surface for owner audit). Per L1_CONTINUITY
/// §3.1: substrate emits evidence; owner determines the verdict.
pub fn run_cold_resume(
    checkers: &mut ColdResumeCheckers,
    at_cycle: u64,
) -> Result<ColdResumeReport, ColdResumeError> {
    let witnesses = vec![
        checkers.i1.check()?,
        checkers.i3.check()?,
        checkers.i4.check()?,
        checkers.i5.check()?,
        checkers.i8.check()?,
    ];

    let all_passed = witnesses.iter().all(|w| w.passed);
    Ok(ColdResumeReport {
        witnesses,
        all_passed,
        at_cycle,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use myco_kernel_shared::canonical_bytes::{encode, Value};
    use myco_kernel_shared::crypto::merkle_hash;

    fn make_witness(id: ColdResumeCheckId, passed: bool) -> CheckWitness {
        let cb = encode(&Value::String(format!("witness_for_{}", id))).unwrap();
        let h = merkle_hash(&[], cb.as_ref());
        CheckWitness {
            check_id: id,
            passed,
            witness_canonical_bytes: cb,
            witness_hash: h,
        }
    }

    struct MockCheck {
        witness: CheckWitness,
    }
    impl I1IdentityCheck for MockCheck {
        fn check(&mut self) -> Result<CheckWitness, ColdResumeError> {
            Ok(self.witness.clone())
        }
    }
    impl I3SsotCheck for MockCheck {
        fn check(&mut self) -> Result<CheckWitness, ColdResumeError> {
            Ok(self.witness.clone())
        }
    }
    impl I4DagCheck for MockCheck {
        fn check(&mut self) -> Result<CheckWitness, ColdResumeError> {
            Ok(self.witness.clone())
        }
    }
    impl I5ReachabilityCheck for MockCheck {
        fn check(&mut self) -> Result<CheckWitness, ColdResumeError> {
            Ok(self.witness.clone())
        }
    }
    impl I8SkinCheck for MockCheck {
        fn check(&mut self) -> Result<CheckWitness, ColdResumeError> {
            Ok(self.witness.clone())
        }
    }

    #[test]
    fn test_cold_resume_all_pass() {
        let mut i1 = MockCheck {
            witness: make_witness(ColdResumeCheckId::I1IdentityIntegrity, true),
        };
        let mut i3 = MockCheck {
            witness: make_witness(ColdResumeCheckId::I3SsotConsistency, true),
        };
        let mut i4 = MockCheck {
            witness: make_witness(ColdResumeCheckId::I4DagSelfConsistency, true),
        };
        let mut i5 = MockCheck {
            witness: make_witness(ColdResumeCheckId::I5Reachability, true),
        };
        let mut i8 = MockCheck {
            witness: make_witness(ColdResumeCheckId::I8SkinDeclaration, true),
        };
        let mut checkers = ColdResumeCheckers {
            i1: &mut i1,
            i3: &mut i3,
            i4: &mut i4,
            i5: &mut i5,
            i8: &mut i8,
        };

        let report = run_cold_resume(&mut checkers, 100).unwrap();
        assert_eq!(report.witnesses.len(), 5);
        assert!(report.all_passed);
        assert!(report.failed_checks().is_empty());
    }

    #[test]
    fn test_cold_resume_partial_failure() {
        let mut i1 = MockCheck {
            witness: make_witness(ColdResumeCheckId::I1IdentityIntegrity, true),
        };
        let mut i3 = MockCheck {
            witness: make_witness(ColdResumeCheckId::I3SsotConsistency, false),
        };
        let mut i4 = MockCheck {
            witness: make_witness(ColdResumeCheckId::I4DagSelfConsistency, true),
        };
        let mut i5 = MockCheck {
            witness: make_witness(ColdResumeCheckId::I5Reachability, false),
        };
        let mut i8 = MockCheck {
            witness: make_witness(ColdResumeCheckId::I8SkinDeclaration, true),
        };
        let mut checkers = ColdResumeCheckers {
            i1: &mut i1,
            i3: &mut i3,
            i4: &mut i4,
            i5: &mut i5,
            i8: &mut i8,
        };

        let report = run_cold_resume(&mut checkers, 100).unwrap();
        assert!(!report.all_passed);
        let failed = report.failed_checks();
        assert_eq!(failed.len(), 2);
        assert!(failed.contains(&ColdResumeCheckId::I3SsotConsistency));
        assert!(failed.contains(&ColdResumeCheckId::I5Reachability));
    }

    #[test]
    fn test_check_id_display() {
        assert_eq!(
            ColdResumeCheckId::I1IdentityIntegrity.to_string(),
            "i1_identity_integrity"
        );
        assert_eq!(
            ColdResumeCheckId::I8SkinDeclaration.to_string(),
            "i8_skin_declaration"
        );
    }
}
