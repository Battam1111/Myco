//! Quarantine sub-state metabolism (L1_CONTINUITY §5).
//!
//! ## Doctrine
//!
//! Per L1_CONTINUITY §5.2: quarantine-state metabolism keeps substrate
//! observing itself but suspends external interaction:
//!
//! - Cycle continues at alive cadence.
//! - Tier-1 invariants run.
//! - **Intake closed** except owner-attested administration.
//! - Sporocarp fruiting continues for diagnostic / immune.
//! - **Federation outputs suspended**.
//!
//! Per L1_CONTINUITY §5.4: distinction from legacy —
//!
//! - **Legacy**: owner unavailable; substrate runs normally except L0/L1
//!   mutations frozen.
//! - **Quarantined**: substrate observing internal pathology; intake closed;
//!   federation suspended; L0/L1 mutations also gated.
//!
//! A substrate may be both legacy AND quarantined; recovery requires
//! owner-equivalent attestation (L1_GOVERNANCE §3.2) + quarantine clearance.
//!
//! ## M3 scope
//!
//! Policy + queryable rules. The dormancy state machine (in `crate::dormancy`)
//! holds the alive-substate flag; this module provides the policy decisions
//! that read from that state.

use crate::dormancy::{AliveSubstate, DormancyMachine, LifecycleState};
use thiserror::Error;

/// Quarantine policy errors.
#[derive(Debug, Error, PartialEq, Eq)]
#[non_exhaustive]
pub enum QuarantineError {
    /// Operation requires substrate not to be quarantined.
    #[error("operation blocked by quarantine sub-state: {0}")]
    Blocked(String),
}

/// Whether an operation type is allowed in the current sub-state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum OperationKind {
    /// Delta intake from operator (closed during quarantine).
    DeltaIntake,
    /// Federation egress to peers (suspended during quarantine).
    FederationEgress,
    /// Anchor-surface output (continues — owner can still observe substrate).
    AnchorSurfaceOutput,
    /// Sporocarp fruiting (continues for diagnostic / immune).
    SporocarpFruiting,
    /// Tier-1 invariant check (continues — substrate observes itself).
    Tier1Invariant,
    /// Owner-attested administration delta (allowed even during quarantine).
    OwnerAttestedAdministration,
}

/// Decide whether an operation is permitted given the current dormancy
/// + alive-substate state.
///
/// Per L1_CONTINUITY §5.2 + dormancy state machine in `crate::dormancy`.
pub fn is_operation_permitted(machine: &DormancyMachine, op: OperationKind) -> bool {
    // Destroyed: nothing permitted.
    if machine.state() == LifecycleState::Destroyed {
        return false;
    }

    // Dormant: only handshake / attestation listening (modeled separately).
    // No metabolism operations.
    if machine.state() == LifecycleState::Dormant {
        return matches!(op, OperationKind::OwnerAttestedAdministration);
    }

    // Alive: per-sub-state rules.
    match machine.alive_substate() {
        AliveSubstate::Normal => true,
        AliveSubstate::Quarantined => match op {
            // Closed in quarantine.
            OperationKind::DeltaIntake => false,
            OperationKind::FederationEgress => false,
            // Continues in quarantine.
            OperationKind::AnchorSurfaceOutput => true,
            OperationKind::SporocarpFruiting => true,
            OperationKind::Tier1Invariant => true,
            OperationKind::OwnerAttestedAdministration => true,
        },
        AliveSubstate::Legacy => match op {
            // Legacy: L0/L1 mutations frozen but normal ops continue.
            // (Granular CI-mutation gating handled at classifier level.)
            OperationKind::DeltaIntake => true,
            OperationKind::FederationEgress => true,
            OperationKind::AnchorSurfaceOutput => true,
            OperationKind::SporocarpFruiting => true,
            OperationKind::Tier1Invariant => true,
            OperationKind::OwnerAttestedAdministration => true,
        },
    }
}

/// Assert that an operation is permitted; return error if not.
pub fn assert_permitted(
    machine: &DormancyMachine,
    op: OperationKind,
) -> Result<(), QuarantineError> {
    if is_operation_permitted(machine, op) {
        Ok(())
    } else {
        Err(QuarantineError::Blocked(format!(
            "operation {:?} blocked: state={:?}, substrate_substate={:?}",
            op,
            machine.state(),
            machine.alive_substate()
        )))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dormancy::{DormancyMachine, DormancyTrigger, DormantMode};

    #[test]
    fn test_alive_normal_permits_all_ops() {
        let m = DormancyMachine::new();
        for op in [
            OperationKind::DeltaIntake,
            OperationKind::FederationEgress,
            OperationKind::AnchorSurfaceOutput,
            OperationKind::SporocarpFruiting,
            OperationKind::Tier1Invariant,
            OperationKind::OwnerAttestedAdministration,
        ] {
            assert!(
                is_operation_permitted(&m, op),
                "alive-normal should permit {op:?}"
            );
        }
    }

    #[test]
    fn test_quarantined_blocks_intake_and_federation() {
        let mut m = DormancyMachine::new();
        m.enter_quarantine(DormancyTrigger::ColdResumeFailure, 10)
            .unwrap();

        assert!(!is_operation_permitted(&m, OperationKind::DeltaIntake));
        assert!(!is_operation_permitted(&m, OperationKind::FederationEgress));
        // Continues:
        assert!(is_operation_permitted(&m, OperationKind::SporocarpFruiting));
        assert!(is_operation_permitted(&m, OperationKind::Tier1Invariant));
        assert!(is_operation_permitted(
            &m,
            OperationKind::AnchorSurfaceOutput
        ));
        assert!(is_operation_permitted(
            &m,
            OperationKind::OwnerAttestedAdministration
        ));
    }

    #[test]
    fn test_dormant_blocks_metabolism() {
        let mut m = DormancyMachine::new();
        m.transition_to_dormant(DormantMode::Throttled, DormancyTrigger::IdleTimeout, 100)
            .unwrap();
        assert!(!is_operation_permitted(&m, OperationKind::DeltaIntake));
        assert!(!is_operation_permitted(&m, OperationKind::FederationEgress));
        assert!(!is_operation_permitted(
            &m,
            OperationKind::SporocarpFruiting
        ));
        // Only owner-attested-administration listening continues.
        assert!(is_operation_permitted(
            &m,
            OperationKind::OwnerAttestedAdministration
        ));
    }

    #[test]
    fn test_destroyed_blocks_everything() {
        let mut m = DormancyMachine::new();
        m.destroy(DormancyTrigger::OwnerDestruction, 1000).unwrap();
        for op in [
            OperationKind::DeltaIntake,
            OperationKind::FederationEgress,
            OperationKind::AnchorSurfaceOutput,
            OperationKind::SporocarpFruiting,
            OperationKind::Tier1Invariant,
            OperationKind::OwnerAttestedAdministration,
        ] {
            assert!(
                !is_operation_permitted(&m, op),
                "destroyed should block {op:?}"
            );
        }
    }

    #[test]
    fn test_assert_permitted_succeeds_when_allowed() {
        let m = DormancyMachine::new();
        assert_permitted(&m, OperationKind::DeltaIntake).unwrap();
    }

    #[test]
    fn test_assert_permitted_errors_when_blocked() {
        let mut m = DormancyMachine::new();
        m.enter_quarantine(DormancyTrigger::ColdResumeFailure, 10)
            .unwrap();
        let result = assert_permitted(&m, OperationKind::DeltaIntake);
        assert!(matches!(result, Err(QuarantineError::Blocked(_))));
    }
}
