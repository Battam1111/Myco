//! ## C-row detector namespace (M24.1 Phase β follow-up)
//!
//! Immune sporocarp `detector_id` values use two disjoint namespaces:
//!
//! - **C1-C20 (L1/HARD_RULES §1 catalog)** — formal CRITICAL breach catalog.
//!   Substrate emit sites for these MUST match the L1 spec label exactly.
//!   Currently 7 of 20 are emitted with matching labels: C5 attestation_invalid,
//!   C6 dag_enumeration_unclosed, C7 dag_retro_edit_detected, C9
//!   cold_resume_invariant_failure, C14 untyped_mutation_blocked, C17
//!   operator_witness_forgery, C18 canonical_bytes_render_drift.
//!
//! - **C30+ (substrate-private)** — detectors needed for live-substrate
//!   correctness but not in the L1 catalog. Reserved range so a future L1
//!   revision can extend the formal catalog without renumber thrash.
//!   Current C30+ detectors:
//!     C30_handshake_pubkey_mismatch         (was C2; freed L1's C2 = output_endpoint_breach)
//!     C31_cycle_step_failed                 (was C12; freed L1's C12 = successor_activation_with_fresh_owner_heartbeat)
//!     C32_substrate_state_orphan_detected   (was C19; freed L1's C19 = paused_dormancy_unsafe_host)
//!     C33_federation_peer_identity_mismatch (was C20; freed L1's C20 = genesis_attestation_chain_broken)
//!     C34_birth_period_violation_during_quarantine (was C21; catalog ends at C20)
//!     C35_federation_substrate_private_event_injection (new Phase β)
//!     C36_cycle_backlog                     (M24: cycle taking >5s, backlog ≥10)
//!     C37_doctrine_instability_burst        (M25.1: >10 CI events / 100 cycles per L2/OBSERVABILITY §8)
//!     C38_snapshot_integrity_violation      (M25.0: snapshot.cb signer_pubkey mismatch or signature invalid)
//!     C39_federation_hello_signature_invalid (M25.4: peer presented signature that fails Ed25519 verify)
//!     C40_bet_weakening_quorum              (M25.2: L0/cards/LB_living_bets falsifiability trigger — ≥3 of signals 1-6 against the bet)
//!
//! The Phase α/β audit found my prior emit sites occupied C2/C12/C19/C20/C21
//! with substrate-private detector semantics — labeling drift from L1 spec.
//! M24.1 renames to C30+ namespace; C1-C20 emit sites NOW reserved for L1
//! spec labels (some still unimplemented, will land in M25+).
//!
//! M21 P5 万物互联 — DAG event type definitions.
//!
//! This module defines the **substrate event vocabulary**: every state
//! mutation in the substrate emits a DAG node whose `node_type` is one of
//! the constants here, with a content-canonical-bytes Map matching the
//! documented schema.
//!
//! ## Doctrine alignment
//!
//! Per L0/cards/P01-P14 (principles).1 P5: "The substrate is a connected graph, not a collection.
//! Every node is reachable from every other by traversal. Orphans are dead
//! tissue."
//!
//! M21 closes a P5 violation that accumulated across M5-M20: numerous state
//! mutations (cycle_counter advance, axis registration, plain perturb_axis,
//! TOFU pinning, owner_key changes, nonce issue/consume) modified substrate
//! behavior but did NOT emit DAG nodes — making them ORPHANS from the
//! causal graph. M21 emits these as DAG events alongside the existing state
//! file writes (dual-write phase), enabling `DerivedState::from_dag` to
//! produce a complete derived view of substrate state from the DAG alone.
//!
//! ## Event types (12 new in M21.1; coexisting with existing M8-M20 types)
//!
//! | node_type                       | Records                                    |
//! |---------------------------------|--------------------------------------------|
//! | `genesis_event:{id_prefix}`     | First DAG node; substrate_id + genesis_time|
//! | `cycle_advanced`                | cycle_counter increment                    |
//! | `axis_registered:{name}`        | New axis schema + initial value            |
//! | `axis_perturbed:{name}`         | Plain perturb (not raw-material-linked)    |
//! | `axis_reset_after_fruiting:{n}` | APPETITE axis reset to initial_value       |
//! | `operator_pinned:{pk_prefix}`   | TOFU first-pinning of operator pubkey      |
//! | `owner_key_initialized`         | Genesis owner key write                    |
//! | `owner_key_added`               | New owner key added to history             |
//! | `owner_key_archived`            | Owner key marked archived (rotation)       |
//! | `nonce_issued:{nonce_prefix}`   | M13 nonce issuance                         |
//! | `nonce_consumed:{nonce_prefix}` | M13 nonce consume on submit                |
//! | `nonce_expired:{nonce_prefix}`  | M14 nonce TTL expiration during prune      |
//!
//! ## Determinism contract
//!
//! Each event encoder produces canonical-bytes that, when decoded, yield the
//! same logical content. `DerivedState::apply_event` is a pure function of
//! (current_state, event) — replaying any DAG segment in insertion order
//! produces identical state.
//!
//! Float values are stored as repr-strings (matching the wire protocol's
//! `repr(f64)` convention used since M5) so cross-platform replay is
//! byte-deterministic.
//!
//! ## Module organization
//!
//! The codec functions are grouped by domain into submodules. Every item is
//! re-exported here at `crate::events::*` so existing call paths resolve
//! unchanged — these submodules are an internal organization detail, not a
//! public API surface change.

mod attestation;
mod backup_encryption;
mod char07;
mod compression;
mod consensus;
mod core;
mod cultivation;
mod federation;
mod internal_mortality;
mod schema_migration;
mod telos;

pub use attestation::*;
pub use backup_encryption::*;
pub use char07::*;
pub use compression::*;
pub use consensus::*;
pub use core::*;
pub use cultivation::*;
pub use federation::*;
pub use internal_mortality::*;
pub use schema_migration::*;
pub use telos::*;
