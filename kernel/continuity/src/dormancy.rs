//! Dormancy state machine (L1_CONTINUITY §2 — canonical owner).
//!
//! ## Doctrine
//!
//! Per L0 I1: three top-level lifecycle states (alive, dormant, destroyed)
//! plus sub-states of alive (quarantined, legacy).
//!
//! ### alive → dormant triggers (§2.2)
//!
//! - Operator-connection drop (kernel/skin §4.5).
//! - Idle timeout (default 100 cycles without delta absorption).
//! - Owner-commanded dormancy via CI event.
//! - Operator-requested dormancy (handshake_terminate with request_dormancy).
//!
//! ### dormant → alive triggers (§2.3)
//!
//! - Valid operator handshake.
//! - Owner-attestation arrival at anchor-surface inbound channel.
//!
//! ### Dormant compute modes (§2.4)
//!
//! - **Throttled**: cycle rate at max-interval floor; tier-1 + gradient
//!   continue; intake closed.
//! - **Paused**: all metabolism halted; only handshake / attestation channel
//!   listening continues.
//!
//! Per pass-2 mycoparasite-23 + rhizomorph-11: attestation expiry_cycles
//! does NOT advance during paused. On wake, substrate re-validates against
//! anchor-surface wall-clock; stale-on-wake → `attestation_expired`.

use thiserror::Error;

/// Dormancy state-machine errors.
#[derive(Debug, Error, PartialEq, Eq)]
#[non_exhaustive]
pub enum DormancyError {
    /// Transition not permitted from current state.
    #[error("invalid transition from {from:?} to {to:?}: {reason}")]
    InvalidTransition {
        /// Source state.
        from: LifecycleState,
        /// Target state.
        to: LifecycleState,
        /// Why the transition was rejected.
        reason: String,
    },

    /// Attempt to operate on a destroyed substrate.
    #[error("substrate is destroyed")]
    SubstrateDestroyed,
}

/// Top-level lifecycle state (L0 I1).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum LifecycleState {
    /// Active metabolism; full cycle cadence.
    Alive,
    /// Suspended; reduced or zero cycle cadence.
    Dormant,
    /// Terminal state; substrate cannot resume.
    Destroyed,
}

/// Dormant compute mode (L1_CONTINUITY §2.4).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum DormantMode {
    /// Throttled: cycle rate at max-interval floor; tier-1 + gradient continue;
    /// intake closed; handshake + attestation channel listening continues.
    Throttled,
    /// Paused: all metabolism halted; only handshake + attestation channel
    /// listening continues.
    ///
    /// **Caveat per L1_HARD_RULES C19**: in paused mode, substrate process
    /// must remain suspended (not terminated). Termination routes through
    /// cold-resume quarantine.
    Paused,
}

/// Alive sub-state per L1_CONTINUITY §5.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum AliveSubstate {
    /// Normal alive operation.
    Normal,
    /// Quarantined: I8 / I3 / cold-resume failure observed; intake closed;
    /// federation suspended; tier-1 invariants still run; sporocarp fruiting
    /// continues for diagnostic / immune purposes.
    Quarantined,
    /// Legacy: owner unavailable; substrate runs normally except L0/L1
    /// mutations frozen. Per L1_GOVERNANCE §3.2 succession.
    Legacy,
}

/// Trigger that caused a state transition (for sporocarp emission).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DormancyTrigger {
    /// Operator-connection drop detected.
    OperatorDropped,
    /// Idle timeout (no delta absorption for ≥ idle_cycles).
    IdleTimeout,
    /// Owner CI command.
    OwnerCommanded,
    /// Operator requested dormancy via handshake_terminate.
    OperatorRequested,
    /// Valid operator handshake received.
    HandshakeAccepted,
    /// Owner attestation arrived at anchor-surface inbound channel.
    OwnerAttestationArrived,
    /// Skin breach (CRITICAL) → quarantine.
    SkinBreachCritical,
    /// Cold-resume invariant failure → quarantine.
    ColdResumeFailure,
    /// Owner-attested quarantine clearance.
    QuarantineClearance,
    /// Owner-attested destruction (final).
    OwnerDestruction,
}

/// Dormancy state machine.
#[derive(Debug, Clone)]
pub struct DormancyMachine {
    state: LifecycleState,
    alive_substate: AliveSubstate,
    dormant_mode: Option<DormantMode>,
    last_transition_cycle: u64,
    transition_history: Vec<TransitionRecord>,
}

/// A recorded state transition (for observability + audit).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TransitionRecord {
    /// State before transition.
    pub from: LifecycleState,
    /// State after transition.
    pub to: LifecycleState,
    /// Alive sub-state at transition time (only meaningful if `to == Alive`).
    pub alive_substate: AliveSubstate,
    /// Dormant mode at transition time (only meaningful if `to == Dormant`).
    pub dormant_mode: Option<DormantMode>,
    /// Trigger that caused the transition.
    pub trigger: DormancyTrigger,
    /// Substrate metabolic-cycle at transition.
    pub at_cycle: u64,
}

impl DormancyMachine {
    /// Construct a new state machine in the freshly-genesis state (alive,
    /// normal).
    pub fn new() -> Self {
        DormancyMachine {
            state: LifecycleState::Alive,
            alive_substate: AliveSubstate::Normal,
            dormant_mode: None,
            last_transition_cycle: 0,
            transition_history: Vec::new(),
        }
    }

    /// Current top-level state.
    pub fn state(&self) -> LifecycleState {
        self.state
    }

    /// Current alive sub-state (Normal / Quarantined / Legacy).
    pub fn alive_substate(&self) -> AliveSubstate {
        self.alive_substate
    }

    /// Current dormant mode (if state is Dormant).
    pub fn dormant_mode(&self) -> Option<DormantMode> {
        self.dormant_mode
    }

    /// Whether the substrate currently accepts delta intake.
    ///
    /// Intake is permitted iff: alive AND not quarantined. Dormant substrates
    /// reject intake (even though they may accept handshakes).
    pub fn accepts_intake(&self) -> bool {
        self.state == LifecycleState::Alive && self.alive_substate == AliveSubstate::Normal
    }

    /// Whether the substrate currently accepts federation egress.
    pub fn accepts_federation_egress(&self) -> bool {
        // Federation suspended in quarantine + dormant + destroyed.
        self.state == LifecycleState::Alive && self.alive_substate != AliveSubstate::Quarantined
    }

    /// Whether the substrate is destroyed (no further transitions possible).
    pub fn is_destroyed(&self) -> bool {
        self.state == LifecycleState::Destroyed
    }

    /// Transition alive → dormant.
    pub fn transition_to_dormant(
        &mut self,
        mode: DormantMode,
        trigger: DormancyTrigger,
        at_cycle: u64,
    ) -> Result<(), DormancyError> {
        if self.state == LifecycleState::Destroyed {
            return Err(DormancyError::SubstrateDestroyed);
        }
        if self.state != LifecycleState::Alive {
            return Err(DormancyError::InvalidTransition {
                from: self.state,
                to: LifecycleState::Dormant,
                reason: format!("cannot transition to dormant from {:?}", self.state),
            });
        }
        let from = self.state;
        self.state = LifecycleState::Dormant;
        self.dormant_mode = Some(mode);
        self.last_transition_cycle = at_cycle;
        self.transition_history.push(TransitionRecord {
            from,
            to: self.state,
            alive_substate: self.alive_substate,
            dormant_mode: Some(mode),
            trigger,
            at_cycle,
        });
        Ok(())
    }

    /// Transition dormant → alive.
    pub fn transition_to_alive(
        &mut self,
        trigger: DormancyTrigger,
        at_cycle: u64,
    ) -> Result<(), DormancyError> {
        if self.state == LifecycleState::Destroyed {
            return Err(DormancyError::SubstrateDestroyed);
        }
        if self.state != LifecycleState::Dormant {
            return Err(DormancyError::InvalidTransition {
                from: self.state,
                to: LifecycleState::Alive,
                reason: format!("cannot transition to alive from {:?}", self.state),
            });
        }
        let from = self.state;
        self.state = LifecycleState::Alive;
        self.dormant_mode = None;
        self.last_transition_cycle = at_cycle;
        self.transition_history.push(TransitionRecord {
            from,
            to: self.state,
            alive_substate: self.alive_substate,
            dormant_mode: None,
            trigger,
            at_cycle,
        });
        Ok(())
    }

    /// Enter quarantine sub-state (alive but quarantined).
    ///
    /// Per L1_CONTINUITY §5.1: triggered by cold-resume failure / CRITICAL
    /// skin breach / sustained I3 failure / owner-commanded quarantine.
    pub fn enter_quarantine(
        &mut self,
        trigger: DormancyTrigger,
        at_cycle: u64,
    ) -> Result<(), DormancyError> {
        if self.state != LifecycleState::Alive {
            return Err(DormancyError::InvalidTransition {
                from: self.state,
                to: self.state,
                reason: format!(
                    "cannot enter quarantine from {:?}; substrate must be alive",
                    self.state
                ),
            });
        }
        let prev_substate = self.alive_substate;
        self.alive_substate = AliveSubstate::Quarantined;
        self.last_transition_cycle = at_cycle;
        self.transition_history.push(TransitionRecord {
            from: self.state,
            to: self.state,
            alive_substate: prev_substate,
            dormant_mode: None,
            trigger,
            at_cycle,
        });
        Ok(())
    }

    /// Clear quarantine (alive-quarantined → alive-normal).
    ///
    /// Per L1_CONTINUITY §3.3 / §5.3: requires owner-attested quarantine
    /// clearance (the trigger MUST be `QuarantineClearance` for actual
    /// clearance; this module enforces the trigger value).
    pub fn clear_quarantine(
        &mut self,
        trigger: DormancyTrigger,
        at_cycle: u64,
    ) -> Result<(), DormancyError> {
        if self.alive_substate != AliveSubstate::Quarantined {
            return Err(DormancyError::InvalidTransition {
                from: self.state,
                to: self.state,
                reason: "not currently quarantined".to_string(),
            });
        }
        if trigger != DormancyTrigger::QuarantineClearance {
            return Err(DormancyError::InvalidTransition {
                from: self.state,
                to: self.state,
                reason: format!(
                    "quarantine clearance requires QuarantineClearance trigger, got {:?}",
                    trigger
                ),
            });
        }
        self.alive_substate = AliveSubstate::Normal;
        self.last_transition_cycle = at_cycle;
        self.transition_history.push(TransitionRecord {
            from: self.state,
            to: self.state,
            alive_substate: AliveSubstate::Quarantined,
            dormant_mode: None,
            trigger,
            at_cycle,
        });
        Ok(())
    }

    /// Transition to destroyed (terminal).
    ///
    /// Per L1_GOVERNANCE §4.4: three destruction modes
    /// (intentional-owner / catastrophic-environment / endogenous-pair).
    /// All require owner co-attestation upstream of this method.
    pub fn destroy(
        &mut self,
        trigger: DormancyTrigger,
        at_cycle: u64,
    ) -> Result<(), DormancyError> {
        if self.state == LifecycleState::Destroyed {
            return Err(DormancyError::SubstrateDestroyed);
        }
        let from = self.state;
        self.state = LifecycleState::Destroyed;
        self.last_transition_cycle = at_cycle;
        self.transition_history.push(TransitionRecord {
            from,
            to: self.state,
            alive_substate: self.alive_substate,
            dormant_mode: self.dormant_mode,
            trigger,
            at_cycle,
        });
        Ok(())
    }

    /// Full transition history (for audit / observability).
    pub fn history(&self) -> &[TransitionRecord] {
        &self.transition_history
    }

    /// Cycle number of the most-recent transition.
    pub fn last_transition_cycle(&self) -> u64 {
        self.last_transition_cycle
    }
}

impl Default for DormancyMachine {
    fn default() -> Self {
        DormancyMachine::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_initial_state_alive_normal() {
        let m = DormancyMachine::new();
        assert_eq!(m.state(), LifecycleState::Alive);
        assert_eq!(m.alive_substate(), AliveSubstate::Normal);
        assert!(m.accepts_intake());
        assert!(m.accepts_federation_egress());
    }

    #[test]
    fn test_alive_to_dormant_throttled() {
        let mut m = DormancyMachine::new();
        m.transition_to_dormant(DormantMode::Throttled, DormancyTrigger::IdleTimeout, 100)
            .unwrap();
        assert_eq!(m.state(), LifecycleState::Dormant);
        assert_eq!(m.dormant_mode(), Some(DormantMode::Throttled));
        assert!(!m.accepts_intake());
        assert!(!m.accepts_federation_egress());
    }

    #[test]
    fn test_alive_to_dormant_paused() {
        let mut m = DormancyMachine::new();
        m.transition_to_dormant(DormantMode::Paused, DormancyTrigger::OperatorRequested, 50)
            .unwrap();
        assert_eq!(m.dormant_mode(), Some(DormantMode::Paused));
    }

    #[test]
    fn test_dormant_to_alive() {
        let mut m = DormancyMachine::new();
        m.transition_to_dormant(DormantMode::Throttled, DormancyTrigger::IdleTimeout, 100)
            .unwrap();
        m.transition_to_alive(DormancyTrigger::HandshakeAccepted, 200)
            .unwrap();
        assert_eq!(m.state(), LifecycleState::Alive);
        assert_eq!(m.dormant_mode(), None);
        assert!(m.accepts_intake());
    }

    #[test]
    fn test_quarantine_blocks_intake_and_egress() {
        let mut m = DormancyMachine::new();
        m.enter_quarantine(DormancyTrigger::SkinBreachCritical, 50)
            .unwrap();
        assert_eq!(m.state(), LifecycleState::Alive);
        assert_eq!(m.alive_substate(), AliveSubstate::Quarantined);
        assert!(!m.accepts_intake());
        assert!(!m.accepts_federation_egress());
    }

    #[test]
    fn test_quarantine_clearance_requires_correct_trigger() {
        let mut m = DormancyMachine::new();
        m.enter_quarantine(DormancyTrigger::ColdResumeFailure, 10)
            .unwrap();
        // Wrong trigger → rejected.
        let result = m.clear_quarantine(DormancyTrigger::HandshakeAccepted, 20);
        assert!(matches!(
            result,
            Err(DormancyError::InvalidTransition { .. })
        ));
        // Correct trigger → succeeds.
        m.clear_quarantine(DormancyTrigger::QuarantineClearance, 30)
            .unwrap();
        assert_eq!(m.alive_substate(), AliveSubstate::Normal);
        assert!(m.accepts_intake());
    }

    #[test]
    fn test_clear_quarantine_when_not_quarantined_rejected() {
        let mut m = DormancyMachine::new();
        let result = m.clear_quarantine(DormancyTrigger::QuarantineClearance, 10);
        assert!(matches!(
            result,
            Err(DormancyError::InvalidTransition { .. })
        ));
    }

    #[test]
    fn test_destroy_is_terminal() {
        let mut m = DormancyMachine::new();
        m.destroy(DormancyTrigger::OwnerDestruction, 1000).unwrap();
        assert_eq!(m.state(), LifecycleState::Destroyed);
        assert!(m.is_destroyed());

        // No further transitions allowed.
        let result =
            m.transition_to_dormant(DormantMode::Throttled, DormancyTrigger::IdleTimeout, 1001);
        assert_eq!(result, Err(DormancyError::SubstrateDestroyed));
        let result = m.transition_to_alive(DormancyTrigger::HandshakeAccepted, 1001);
        assert_eq!(result, Err(DormancyError::SubstrateDestroyed));
        let result = m.destroy(DormancyTrigger::OwnerDestruction, 1001);
        assert_eq!(result, Err(DormancyError::SubstrateDestroyed));
    }

    #[test]
    fn test_transition_history_recorded() {
        let mut m = DormancyMachine::new();
        m.transition_to_dormant(DormantMode::Throttled, DormancyTrigger::IdleTimeout, 100)
            .unwrap();
        m.transition_to_alive(DormancyTrigger::HandshakeAccepted, 200)
            .unwrap();
        m.enter_quarantine(DormancyTrigger::SkinBreachCritical, 250)
            .unwrap();

        assert_eq!(m.history().len(), 3);
        assert_eq!(m.history()[0].trigger, DormancyTrigger::IdleTimeout);
        assert_eq!(m.history()[1].trigger, DormancyTrigger::HandshakeAccepted);
        assert_eq!(m.history()[2].trigger, DormancyTrigger::SkinBreachCritical);
    }

    #[test]
    fn test_cannot_dormant_when_already_dormant() {
        let mut m = DormancyMachine::new();
        m.transition_to_dormant(DormantMode::Throttled, DormancyTrigger::IdleTimeout, 100)
            .unwrap();
        let result =
            m.transition_to_dormant(DormantMode::Paused, DormancyTrigger::OperatorRequested, 110);
        assert!(matches!(
            result,
            Err(DormancyError::InvalidTransition { .. })
        ));
    }

    #[test]
    fn test_cannot_alive_when_already_alive() {
        let mut m = DormancyMachine::new();
        let result = m.transition_to_alive(DormancyTrigger::HandshakeAccepted, 10);
        assert!(matches!(
            result,
            Err(DormancyError::InvalidTransition { .. })
        ));
    }

    #[test]
    fn test_cannot_quarantine_from_dormant() {
        let mut m = DormancyMachine::new();
        m.transition_to_dormant(DormantMode::Throttled, DormancyTrigger::IdleTimeout, 100)
            .unwrap();
        let result = m.enter_quarantine(DormancyTrigger::ColdResumeFailure, 110);
        assert!(matches!(
            result,
            Err(DormancyError::InvalidTransition { .. })
        ));
    }

    #[test]
    fn test_destroy_from_dormant() {
        let mut m = DormancyMachine::new();
        m.transition_to_dormant(DormantMode::Throttled, DormancyTrigger::IdleTimeout, 100)
            .unwrap();
        m.destroy(DormancyTrigger::OwnerDestruction, 1000).unwrap();
        assert!(m.is_destroyed());
    }

    #[test]
    fn test_last_transition_cycle_tracked() {
        let mut m = DormancyMachine::new();
        assert_eq!(m.last_transition_cycle(), 0);
        m.transition_to_dormant(DormantMode::Throttled, DormancyTrigger::IdleTimeout, 42)
            .unwrap();
        assert_eq!(m.last_transition_cycle(), 42);
    }
}
