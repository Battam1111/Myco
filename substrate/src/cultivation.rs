//! **COV06 不弃不孤** — cultivator-mortality + succession FSM.
//!
//! L0/cards/COV06_no_abandonment_succession.md + L1/GOVERNANCE §3.2 specify a
//! five-state cultivation-succession FSM whose states are **sub-states of
//! `alive`** and are **DAG-DERIVED** (not a persisted Rust enum):
//!
//! ```text
//!   Normal ──T1(stale)──> Legacy ──T4(orphan)──> Orphaned ──T7(bet_retire)──> Archived
//!     ↑                     │  ↑                     │
//!     └──T2(resume)─────────┘  └──T3(succession)─────┤ (back to Normal)
//!     └──T5(recovery)─────────────────────────────────┘
//! ```
//!
//! The current state is computed by walking the DAG for the latest event of the
//! cultivation family (cf. `crate::lifecycle::current_quarantine_state`, which
//! derives the quarantine sub-state the same way). No enum field is persisted;
//! `current_cultivation_state` is a pure derivation over DAG events.
//!
//! This module owns:
//!   - [`CultivationState`] + [`current_cultivation_state`] — the FSM derivation.
//!   - [`compute_staleness`] — a PURE staleness-in-days function (deterministic
//!     for tests; no clock reads).
//!   - [`catechumenate_below_min`] — the C46 predicate (`session_count < 50`).
//!   - [`SuccessionConfig`] — cadence/windows/terminal-choice with built-in
//!     defaults + `MYCO_TEST_*` env overrides.
//!   - the operator-facing handlers (heartbeat / successor-chain / succession).
//!
//! AS §5.2 forbids the substrate from reading its own clock for liveness; every
//! wall-clock that enters this module is **operator-threaded** (the anchor-signed
//! heartbeat envelope carries `anchor_timestamp_unix_ns`; the autonomous tick
//! reads `MYCO_TEST_ANCHOR_NOW_NS` in tests or the latest threaded anchor stamp).

use crate::server::ServerState;

/// **COV06 §3.2.C** — minimum dual-signed Layer-D Catechumenate sessions a
/// successor must accumulate before F21 activation. Per META §6.3 + COV06 §5.3:
/// activation that lacks ≥50 sessions is `owner_succession_bypass` (C46). This
/// is the gate that makes succession **un-fabricable in production** — synthetic
/// tests pass a count directly (49 → C46, 50 → proceeds), but a real successor
/// must accumulate 50 real dual-signed sessions.
pub(crate) const CATECHUMENATE_MIN_SESSIONS: u64 = 50;

// (v0.9 owner-key removal: the succession-config defaults + the `SuccessionConfig`
// resolver + `compute_staleness` were removed with the heartbeat-staleness
// watchdog they served. `DerivedSuccessionConfig` + the `cultivation_succession_config_declared`
// event remain as DAG-derivation infrastructure.)

/// **COV06** — the five cultivation-succession FSM states (sub-states of
/// `alive`; L1/GOVERNANCE §3.2). DAG-derived — never persisted as a field.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CultivationState {
    /// `alive::normal` — heartbeat fresh; full daily + CI operations.
    Normal,
    /// `alive::legacy` — heartbeat stale; daily ops continue, CI FROZEN except
    /// `successor_chain` mutation. Entered via T1.
    Legacy,
    /// `alive::orphaned` — legacy_window elapsed OR empty chain at legacy entry;
    /// operational ceiling enforced. Entered via T4.
    Orphaned,
    /// `alive::archived` — terminal-non-destroyed via LB §4 bet-retirement;
    /// state_dir preserved, cold-readable, no metabolism. Entered via T7.
    Archived,
    /// `alive::normal` reached via T5 exceptional recovery (orphaned→normal).
    /// Distinguished from `Normal` for observability — the substrate REMEMBERS
    /// it was recovered (the latest `cultivation_recovered` event dominates a
    /// preceding `cultivation_orphaned`).
    Recovered,
}

impl CultivationState {
    /// Human-readable `alive::<sub>` label.
    pub fn label(&self) -> &'static str {
        match self {
            CultivationState::Normal => "alive::normal",
            CultivationState::Legacy => "alive::legacy",
            CultivationState::Orphaned => "alive::orphaned",
            CultivationState::Archived => "alive::archived",
            CultivationState::Recovered => "alive::normal(recovered)",
        }
    }
}

/// **COV06 §3.2** — derive the current cultivation-succession FSM state by
/// walking the DAG for the LATEST event of the cultivation family (mirrors
/// `crate::lifecycle::current_quarantine_state`). The last transition wins.
///
/// Derivation rules (latest-event-wins; insertion order):
///   - `bet_retired:{reason}`              → Archived (terminal; sticky — nothing
///                                            transitions out of archived).
///   - `cultivation_recovered:{pk}`        → Recovered (orphaned→normal).
///   - `cultivation_orphaned:{pk}`         → Orphaned (legacy→orphaned). Orphaned
///                                            PERSISTS until a `bet_retired:*`
///                                            seal (archive) or death lands — the
///                                            orphaned→terminal watchdog emits a
///                                            *proposal* (`bet_retired_proposal` /
///                                            `self_euthanasia_proposal:…`), not a
///                                            cultivation-family event, so it does
///                                            not transition the FSM by itself.
///   - `succession_completed:{pk}`         → Normal (legacy→normal).
///   - `cultivator_heartbeat_resumed`      → Normal (legacy→normal recovery).
///   - `cultivator_heartbeat_stale:{pk}`   → Legacy (normal→legacy).
///   - anything else / no event            → Normal (the genesis default).
///
/// `Archived` is sticky: once a `bet_retired:*` seal lands the substrate's
/// metabolism halts, so no later cultivation event can occur. We special-case it
/// so a stray later event in a malformed DAG cannot resurrect an archived cultivar.
pub(crate) fn current_cultivation_state(state: &ServerState) -> CultivationState {
    let mut current = CultivationState::Normal;
    let mut archived = false;
    for n in state.dag.iter_in_insertion_order() {
        let nt = &n.node_type;
        if nt.starts_with(crate::events::NODE_TYPE_BET_RETIRED_PREFIX) {
            current = CultivationState::Archived;
            archived = true;
        } else if archived {
            // Archived is terminal — ignore everything after the seal.
            continue;
        } else if nt.starts_with(crate::events::NODE_TYPE_CULTIVATION_RECOVERED_PREFIX) {
            current = CultivationState::Recovered;
        } else if nt.starts_with(crate::events::NODE_TYPE_CULTIVATION_ORPHANED_PREFIX) {
            // `cultivation_orphaned:{pk}`. NOTE: the `cultivation_orphaned_terminal`
            // marker is NOT in this family — it is a *reason* string carried inside
            // terminal proposals (`bet_retired_proposal` / `self_euthanasia_proposal:…`
            // / the `bet_retired:cultivation_orphaned_terminal` seal), and it does
            // NOT match this prefix (no trailing colon). Orphaned therefore persists
            // here until a `bet_retired:*` seal or death lands.
            current = CultivationState::Orphaned;
        } else if nt.starts_with(crate::events::NODE_TYPE_SUCCESSION_COMPLETED_PREFIX) {
            // T3 (succession activation) returns the substrate to alive::normal
            // from alive::legacy.
            current = CultivationState::Normal;
        }
    }
    current
}

/// Returns `true` if `node_type` belongs to the cultivation-succession FSM
/// family — i.e., emitting it can change the value of
/// [`current_cultivation_state`]. The centralized [`crate::server::emit_substrate_event`]
/// uses this to decide when to refresh the memoized `ServerState::cultivation_state`
/// cache. This is exactly the set of branches the derivation above inspects.
pub(crate) fn is_cultivation_family_node_type(node_type: &str) -> bool {
    node_type.starts_with(crate::events::NODE_TYPE_BET_RETIRED_PREFIX)
        || node_type.starts_with(crate::events::NODE_TYPE_CULTIVATION_RECOVERED_PREFIX)
        || node_type.starts_with(crate::events::NODE_TYPE_CULTIVATION_ORPHANED_PREFIX)
        || node_type.starts_with(crate::events::NODE_TYPE_SUCCESSION_COMPLETED_PREFIX)
}

/// **COV06 §5.3 (C46)** — the catechumenate-floor predicate: returns `true` when
/// the successor has fewer than [`CATECHUMENATE_MIN_SESSIONS`] dual-signed Layer-D
/// sessions. A `true` result MUST reject a succession-acceptance with C46
/// (`owner_succession_bypass`). Pure + total (no clock, no DAG).
pub fn catechumenate_below_min(session_count: u64) -> bool {
    session_count < CATECHUMENATE_MIN_SESSIONS
}

/// Read a `u64` from an env var, returning `None` if unset / unparseable.
fn env_u64(key: &str) -> Option<u64> {
    std::env::var(key).ok().and_then(|s| s.trim().parse::<u64>().ok())
}

/// **COV06** — resolve the "now" anchor timestamp (test-only deterministic
/// clock via `MYCO_TEST_ANCHOR_NOW_NS`; `None` otherwise — the substrate never
/// reads its own clock for liveness, AS §5.2). Used as the `bet_retired` seal's
/// anchor-timestamp stamp when present.
pub(crate) fn resolve_anchor_now_ns() -> Option<i64> {
    env_u64("MYCO_TEST_ANCHOR_NOW_NS").map(|v| v as i64)
}

// ===========================================================================
// Operator-facing handlers (Step 5).
// ===========================================================================

use crate::server::{emit_immune_sporocarp, emit_substrate_event};
use crate::SubstrateError;
use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::Value;
use std::collections::BTreeMap;

/// Extract a fixed-length byte field from a payload, returning a Protocol error
/// if missing / wrong-typed / wrong-length.
fn payload_bytes<const N: usize>(
    request: &Message,
    key: &str,
) -> Result<[u8; N], SubstrateError> {
    match request.payload.get(key) {
        Some(Value::Bytes(b)) if b.len() == N => {
            let mut arr = [0u8; N];
            arr.copy_from_slice(b);
            Ok(arr)
        }
        _ => Err(SubstrateError::Protocol(format!(
            "{key} must be {N} Bytes"
        ))),
    }
}

/// Extract a Timestamp field (i64) from a payload.
fn payload_timestamp(request: &Message, key: &str) -> Result<i64, SubstrateError> {
    match request.payload.get(key) {
        Some(Value::Timestamp(t)) => Ok(*t),
        _ => Err(SubstrateError::Protocol(format!("{key} must be a Timestamp"))),
    }
}

/// **COV06 §3.2.A (F21)** — handle `update_successor_chain` (KEYLESS v0.9).
///
/// Appends a SuccessorEntry: validates monotone `valid_from` (strictly
/// increasing vs the last entry) + non-overlapping intervals, then emits
/// `successor_chain_updated:{pk}` + mirrors the entry onto
/// `ServerState::successor_chain`. The owner Ed25519 attestation gate was
/// removed with the anchor surface; the structural interval validation remains.
pub(crate) fn handle_update_successor_chain(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let successor_pubkey: [u8; 32] = payload_bytes(request, "successor_pubkey")?;
    let valid_from_unix_ns = payload_timestamp(request, "valid_from_unix_ns")?;
    let valid_until_unix_ns = match request.payload.get("valid_until_unix_ns") {
        Some(Value::Timestamp(t)) => Some(*t),
        Some(Value::Null) | None => None,
        _ => {
            return Err(SubstrateError::Protocol(
                "update_successor_chain: valid_until_unix_ns must be Timestamp or Null".to_string(),
            ))
        }
    };

    // Validate monotone valid_from + non-overlap against the existing chain
    // (§3.2.A: non-overlapping intervals; monotone valid_from).
    if let Some(last) = state.successor_chain.last() {
        if valid_from_unix_ns <= last.valid_from_unix_ns {
            return Err(SubstrateError::Protocol(format!(
                "update_successor_chain: valid_from ({valid_from_unix_ns}) must be strictly \
                 greater than the last entry's valid_from ({}) — §3.2.A monotone interval",
                last.valid_from_unix_ns
            )));
        }
        // Non-overlap: the prior entry's interval must close before this one opens.
        if let Some(prior_until) = last.valid_until_unix_ns {
            if prior_until > valid_from_unix_ns {
                return Err(SubstrateError::Protocol(format!(
                    "update_successor_chain: interval overlap — prior entry valid_until \
                     ({prior_until}) > new valid_from ({valid_from_unix_ns}); §3.2.A non-overlap"
                )));
            }
        } else {
            // Prior entry is open-ended; appending a new entry would overlap it.
            return Err(SubstrateError::Protocol(
                "update_successor_chain: prior chain head is open-ended (valid_until=Null); \
                 close it before appending a successor — §3.2.A non-overlap"
                    .to_string(),
            ));
        }
    }
    // Closed intervals must be well-formed.
    if let Some(until) = valid_until_unix_ns {
        if until <= valid_from_unix_ns {
            return Err(SubstrateError::Protocol(format!(
                "update_successor_chain: valid_until ({until}) must be > valid_from ({valid_from_unix_ns})"
            )));
        }
    }

    let chain_position = state.successor_chain.len() as u64;
    let cycle = state.cycle_counter();
    let content = crate::events::encode_successor_chain_updated(
        &successor_pubkey,
        valid_from_unix_ns,
        valid_until_unix_ns,
        chain_position,
        cycle,
    );
    let nt = crate::events::successor_chain_updated_node_type(&successor_pubkey);
    let updated_hash = emit_substrate_event(state, nt, content)?;

    state.successor_chain.push(crate::derived_state::DerivedSuccessorEntry {
        successor_pubkey,
        valid_from_unix_ns,
        valid_until_unix_ns,
    });

    let mut payload = BTreeMap::new();
    payload.insert(
        "updated_event_hash".to_string(),
        Value::Bytes(updated_hash.0.to_vec()),
    );
    payload.insert(
        "chain_length".to_string(),
        Value::Uint(state.successor_chain.len() as u64),
    );
    Ok(Some(Message::new(
        msg_type::UPDATE_SUCCESSOR_CHAIN_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// **COV06 T3** — handle `accept_succession` (KEYLESS v0.9). Gates (in order):
///   1. **C46** (`owner_succession_bypass`): reject if
///      `catechumenate_session_count < 50` (the un-fabricable gate — KEPT).
///   2. Else emit `succession_completed:{successor_pubkey}`.
///
/// The owner Ed25519 gates were removed with the anchor surface: the successor
/// signature verify (gate 1), the C12 fresh-owner-heartbeat takeover guard, and
/// the `owner_key_added` history append are gone. The C46 catechumenate floor —
/// the structurally un-fabricable production gate — remains the authorization
/// root. `prior_cultivator_pubkey` is still recorded for the lineage record.
pub(crate) fn handle_accept_succession(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let successor_pubkey: [u8; 32] = payload_bytes(request, "successor_pubkey")?;
    let prior_cultivator_pubkey: [u8; 32] = payload_bytes(request, "prior_cultivator_pubkey")?;
    let anchor_timestamp_unix_ns = payload_timestamp(request, "anchor_timestamp_unix_ns")?;
    let catechumenate_session_count = match request.payload.get("catechumenate_session_count") {
        Some(Value::Uint(n)) => *n,
        _ => {
            return Err(SubstrateError::Protocol(
                "accept_succession: catechumenate_session_count must be Uint".to_string(),
            ))
        }
    };

    // Gate (C46): catechumenate floor. The un-fabricable production gate —
    // a real successor must accumulate ≥50 real dual-signed Layer-D sessions.
    if catechumenate_below_min(catechumenate_session_count) {
        let evidence = format!(
            "accept_succession: catechumenate_session_count={catechumenate_session_count} < \
             CATECHUMENATE_MIN_SESSIONS={CATECHUMENATE_MIN_SESSIONS}; F21 activation REQUIRES \
             ≥50 dual-signed Layer-D sessions (COV06 §5.3 + META §6.3). Premature succession \
             = owner_succession_bypass."
        );
        // implements L0::P1.b''; negative-witness: substrate/tests/e2e_cultivation.rs::succession_below_50_sessions_rejected_c46
        let _ = emit_immune_sporocarp(
            state,
            "C46_owner_succession_bypass",
            "owner_succession_bypass",
            &evidence,
        );
        return Err(SubstrateError::Protocol(evidence));
    }

    // Gate passed → emit succession_completed (T3, keyless).
    let cycle = state.cycle_counter();
    let content = crate::events::encode_succession_completed(
        &successor_pubkey,
        &prior_cultivator_pubkey,
        anchor_timestamp_unix_ns,
        catechumenate_session_count,
        cycle,
    );
    let nt = crate::events::succession_completed_node_type(&successor_pubkey);
    let completed_hash = emit_substrate_event(state, nt, content)?;

    // Post-emit: emit_substrate_event already refreshed the memoized cache.
    let new_state = state.cultivation_state();
    let mut payload = BTreeMap::new();
    payload.insert(
        "completed_event_hash".to_string(),
        Value::Bytes(completed_hash.0.to_vec()),
    );
    payload.insert(
        "cultivation_state".to_string(),
        Value::String(new_state.label().to_string()),
    );
    Ok(Some(Message::new(
        msg_type::ACCEPT_SUCCESSION_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// **COV06 T7 / LB §4** — handle `accept_bet_retired_proposal` (KEYLESS v0.9).
/// The cultivator co-attests a `bet_retired_proposal` (emitted by the COV06-T7
/// orphaned-terminal watchdog OR an LB §4 living-bet quorum). Steps:
///   1. Confirm `proposal_hash` points to a real `bet_retired_proposal` in the
///      DAG; extract its `reason` (the non-arbitrary structural gate).
///   2. Emit `bet_retired:{reason}` — the archive seal. The substrate is now
///      `alive::archived` (sticky): metabolism halts, state_dir preserved
///      cold-readable. The main loop, observing this message type, exits cleanly
///      (re-spawn re-derives Archived + the metabolism guard refuses cycling).
///
/// The owner Ed25519 co-attestation gate was removed with the anchor surface;
/// the proposal-reference is the deliberate structural gate that replaces it.
/// This single seal serves BOTH COV06-T7 (orphaned→archived) AND LB_living_bets
/// §4 (living-bet retirement) — `alive::archived` is designed once for both.
pub(crate) fn handle_accept_bet_retired_proposal(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, map_get_string, Value as CbV};

    let proposal_hash: [u8; 32] = payload_bytes(request, "proposal_hash")?;

    // Look up the proposal in the DAG; extract its reason.
    let proposal_node_hash = myco_kernel_shared::crypto::NodeHash::from_bytes(proposal_hash);
    let proposal_node = state.dag.get(&proposal_node_hash).ok_or_else(|| {
        SubstrateError::Protocol(
            "accept_bet_retired_proposal: proposal_hash not found in DAG".to_string(),
        )
    })?;
    if proposal_node.node_type != crate::events::NODE_TYPE_BET_RETIRED_PROPOSAL {
        return Err(SubstrateError::Protocol(format!(
            "accept_bet_retired_proposal: proposal_hash points to {} (not a bet_retired_proposal)",
            proposal_node.node_type
        )));
    }
    let reason = match cb_decode(proposal_node.content_canonical_bytes.as_ref())
        .map_err(|e| SubstrateError::Protocol(format!("decode proposal content: {e}")))?
    {
        CbV::Map(m) => map_get_string(&m, "reason")
            .map_err(|e| SubstrateError::Protocol(e.to_string()))?
            .to_string(),
        _ => {
            return Err(SubstrateError::Protocol(
                "bet_retired_proposal content not a Map".to_string(),
            ))
        }
    };

    // Emit the bet_retired:{reason} archive seal (alive::archived).
    let cycle = state.cycle_counter();
    let now_anchor = resolve_anchor_now_ns().unwrap_or(0);
    let content = crate::events::encode_bet_retired(
        &reason,
        &proposal_hash,
        cycle,
        now_anchor,
    );
    let nt = crate::events::bet_retired_node_type(&reason);
    let sealed_hash = emit_substrate_event(state, nt, content)?;

    let mut payload = BTreeMap::new();
    payload.insert(
        "sealed_event_hash".to_string(),
        Value::Bytes(sealed_hash.0.to_vec()),
    );
    payload.insert("reason".to_string(), Value::String(reason));
    Ok(Some(Message::new(
        msg_type::ACCEPT_BET_RETIRED_PROPOSAL_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// **COV06** — is the substrate in `alive::archived` (terminal via bet-retirement)?
/// Metabolic operations (cycle advance) are refused while archived; the state_dir
/// stays cold-readable. Reads the memoized FSM cache (maintained at the emit
/// point + hydrated at boot) — this is on the per-ADVANCE / per-tick hot path.
pub(crate) fn is_archived(state: &ServerState) -> bool {
    state.cultivation_state() == CultivationState::Archived
}

#[cfg(test)]
mod tests {
    //! **v0.9 owner-key removal**: the cultivator-heartbeat handler, the
    //! heartbeat-staleness watchdog, the `SuccessionConfig` resolver +
    //! `compute_staleness`, the C12 fresh-owner-heartbeat takeover guard, and the
    //! owner Ed25519 signature gates on update_successor_chain / accept_succession
    //! / accept_bet_retired were all removed. These tests cover the KEYLESS
    //! survivors: the cultivation-FSM derivation (over the reachable transitions),
    //! the C46 catechumenate gate, and the three keyless handlers.

    use super::*;
    use crate::events;
    use crate::persistence::Manifest;
    use myco_kernel_schema::dag::Dag;

    fn test_state() -> ServerState {
        let g = Manifest::genesis();
        ServerState::new(
            std::env::temp_dir().join(format!(
                "myco-cov06-unit-{}-{:x}",
                std::process::id(),
                &0u8 as *const u8 as usize as u64
            )),
            Some(g.substrate_id),
            Some(g.genesis_time_unix_ns),
            g.cycle_counter,
            g.last_absorbed_cycle,
            g.generation_depth,
            Dag::new(),
            [0u8; 32],
        )
    }

    /// Push a cultivation event onto the DAG (tip-parented), refreshing the
    /// memoized FSM cache for cultivation-family events (mirrors the production
    /// emit path).
    fn push(state: &mut ServerState, node_type: String, content: myco_kernel_shared::canonical_bytes::CanonicalBytes) {
        let parents = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let cycle = state.cycle_counter();
        let is_cultivation_family = is_cultivation_family_node_type(&node_type);
        state.dag.insert_node(parents, node_type, cycle, content).expect("insert");
        if is_cultivation_family {
            state.cultivation_state = current_cultivation_state(state);
        }
    }

    fn pk(b: u8) -> [u8; 32] {
        [b; 32]
    }

    fn count_nodes(state: &ServerState, prefix: &str) -> usize {
        state
            .dag
            .iter_in_insertion_order()
            .filter(|n| n.node_type.starts_with(prefix))
            .count()
    }

    fn count_immune(state: &ServerState, substr: &str) -> usize {
        state
            .dag
            .iter_in_insertion_order()
            .filter(|n| n.node_type.starts_with("immune:") && n.node_type.contains(substr))
            .count()
    }

    const DAY_NS: i64 = 86_400_000_000_000;

    // ---- catechumenate_below_min (C46 predicate) ----

    #[test]
    fn c46_predicate_fires_below_floor() {
        assert!(catechumenate_below_min(0));
        assert!(catechumenate_below_min(12)); // COV06 §10.2 borderline example
        assert!(catechumenate_below_min(49));
    }

    #[test]
    fn c46_predicate_passes_at_and_above_floor() {
        assert!(!catechumenate_below_min(50));
        assert!(!catechumenate_below_min(90)); // §10.1 honored example
        assert!(!catechumenate_below_min(1000));
    }

    // ---- current_cultivation_state FSM derivation (keyless-reachable) ----

    #[test]
    fn state_normal_with_no_events() {
        let state = test_state();
        assert_eq!(current_cultivation_state(&state), CultivationState::Normal);
    }

    #[test]
    fn state_orphaned_after_orphan_event() {
        let mut state = test_state();
        let p = pk(0xAA);
        push(
            &mut state,
            events::cultivation_orphaned_node_type(&p),
            events::encode_cultivation_orphaned(&p, 365 * DAY_NS, "legacy_window_elapsed", 2),
        );
        assert_eq!(current_cultivation_state(&state), CultivationState::Orphaned);
    }

    #[test]
    fn state_normal_after_succession() {
        // T3 keyless: a `succession_completed:` event returns the FSM to Normal.
        let mut state = test_state();
        let prior = pk(0xAA);
        let succ = pk(0xBB);
        push(
            &mut state,
            events::succession_completed_node_type(&succ),
            events::encode_succession_completed(&succ, &prior, 100 * DAY_NS, 50, 2),
        );
        assert_eq!(current_cultivation_state(&state), CultivationState::Normal);
    }

    #[test]
    fn state_recovered_after_recovery_following_orphan() {
        let mut state = test_state();
        let p = pk(0xAA);
        push(
            &mut state,
            events::cultivation_orphaned_node_type(&p),
            events::encode_cultivation_orphaned(&p, 365 * DAY_NS, "legacy_window_elapsed", 1),
        );
        push(
            &mut state,
            events::cultivation_recovered_node_type(&p),
            events::encode_cultivation_recovered(&p, "court-ref", 400 * DAY_NS, 2),
        );
        assert_eq!(current_cultivation_state(&state), CultivationState::Recovered);
    }

    #[test]
    fn state_archived_after_bet_retired_and_is_sticky() {
        let mut state = test_state();
        let p = pk(0xAA);
        // orphan → then bet_retired seal → Archived.
        push(
            &mut state,
            events::cultivation_orphaned_node_type(&p),
            events::encode_cultivation_orphaned(&p, 365 * DAY_NS, "legacy_window_elapsed", 1),
        );
        let hash = [0x22u8; 32];
        push(
            &mut state,
            events::bet_retired_node_type("cultivation_orphaned_terminal"),
            events::encode_bet_retired("cultivation_orphaned_terminal", &hash, 2, 730 * DAY_NS),
        );
        assert_eq!(current_cultivation_state(&state), CultivationState::Archived);

        // A stray later orphan event must NOT resurrect from archived.
        push(
            &mut state,
            events::cultivation_orphaned_node_type(&p),
            events::encode_cultivation_orphaned(&p, 800 * DAY_NS, "legacy_window_elapsed", 3),
        );
        assert_eq!(
            current_cultivation_state(&state),
            CultivationState::Archived,
            "archived is terminal — sticky against later events"
        );
    }

    // ===================================================================
    // Keyless handler tests — no signature gate; structural validation only.
    // ===================================================================

    fn successor_request(
        successor_pubkey: &[u8; 32],
        valid_from: i64,
        valid_until: Option<i64>,
    ) -> Message {
        let mut payload = BTreeMap::new();
        payload.insert("successor_pubkey".to_string(), Value::Bytes(successor_pubkey.to_vec()));
        payload.insert("valid_from_unix_ns".to_string(), Value::Timestamp(valid_from));
        payload.insert(
            "valid_until_unix_ns".to_string(),
            match valid_until {
                Some(t) => Value::Timestamp(t),
                None => Value::Null,
            },
        );
        Message::new(msg_type::UPDATE_SUCCESSOR_CHAIN, 1, payload)
    }

    #[test]
    fn successor_chain_append_emits_event_and_mirrors() {
        let mut state = test_state();
        let succ = pk(0xCC);
        let req = successor_request(&succ, 1000, None);
        handle_update_successor_chain(&mut state, &req).expect("ok");
        assert_eq!(count_nodes(&state, events::NODE_TYPE_SUCCESSOR_CHAIN_UPDATED_PREFIX), 1);
        assert_eq!(state.successor_chain.len(), 1);
        assert_eq!(state.successor_chain[0].successor_pubkey, succ);
    }

    #[test]
    fn successor_chain_rejects_non_monotone_valid_from() {
        let mut state = test_state();
        // First entry closed [1000, 2000).
        let req1 = successor_request(&pk(0xCC), 1000, Some(2000));
        handle_update_successor_chain(&mut state, &req1).expect("ok1");
        // Second entry with valid_from BEFORE the first → rejected.
        let req2 = successor_request(&pk(0xDD), 500, Some(3000));
        assert!(handle_update_successor_chain(&mut state, &req2).is_err());
        assert_eq!(state.successor_chain.len(), 1, "rejected entry must not be appended");
    }

    #[test]
    fn successor_chain_rejects_overlap_with_open_head() {
        let mut state = test_state();
        // Open-ended head [1000, ∞).
        let req1 = successor_request(&pk(0xCC), 1000, None);
        handle_update_successor_chain(&mut state, &req1).expect("ok1");
        // Any later append overlaps the open head → rejected.
        let req2 = successor_request(&pk(0xDD), 2000, None);
        assert!(handle_update_successor_chain(&mut state, &req2).is_err());
    }

    fn succession_request(
        successor_pk: &[u8; 32],
        prior_pk: &[u8; 32],
        anchor_ts: i64,
        session_count: u64,
    ) -> Message {
        let mut payload = BTreeMap::new();
        payload.insert("successor_pubkey".to_string(), Value::Bytes(successor_pk.to_vec()));
        payload.insert("prior_cultivator_pubkey".to_string(), Value::Bytes(prior_pk.to_vec()));
        payload.insert("anchor_timestamp_unix_ns".to_string(), Value::Timestamp(anchor_ts));
        payload.insert("catechumenate_session_count".to_string(), Value::Uint(session_count));
        Message::new(msg_type::ACCEPT_SUCCESSION, 1, payload)
    }

    #[test]
    fn succession_below_50_sessions_rejected_c46() {
        let mut state = test_state();
        let prior_pk = pk(0xAA);
        let succ_pk = pk(0xBB);
        // 12 sessions (COV06 §10.2 borderline) → C46 (the kept un-fabricable gate).
        let req = succession_request(&succ_pk, &prior_pk, 100 * DAY_NS, 12);
        assert!(handle_accept_succession(&mut state, &req).is_err());
        assert!(count_immune(&state, "C46_owner_succession_bypass") >= 1);
        assert_eq!(count_nodes(&state, events::NODE_TYPE_SUCCESSION_COMPLETED_PREFIX), 0);
    }

    #[test]
    fn succession_50_sessions_completes_keyless() {
        // Keyless: ≥50 catechumenate sessions is the only gate. No owner signature,
        // no fresh-heartbeat C12 check, no owner_key_added side effect.
        let mut state = test_state();
        let prior_pk = pk(0xAA);
        let succ_pk = pk(0xBB);
        let req = succession_request(&succ_pk, &prior_pk, 100 * DAY_NS, 50);
        let resp = handle_accept_succession(&mut state, &req).expect("succession completes");
        assert!(resp.is_some());
        assert_eq!(count_nodes(&state, events::NODE_TYPE_SUCCESSION_COMPLETED_PREFIX), 1);
        assert_eq!(
            current_cultivation_state(&state),
            CultivationState::Normal,
            "T3: succession returns the substrate to alive::normal"
        );
    }

    #[test]
    fn bet_retired_seals_archive_and_is_archived_keyless() {
        let mut state = test_state();
        // Emit a bet_retired_proposal first (as the orphaned-terminal path would).
        let proposal_content =
            events::encode_bet_retired_proposal("cultivation_orphaned_terminal", 5, 800 * DAY_NS);
        let proposal_hash = state
            .dag
            .insert_node(
                Vec::new(),
                events::NODE_TYPE_BET_RETIRED_PROPOSAL.to_string(),
                state.cycle_counter(),
                proposal_content,
            )
            .expect("insert proposal");

        // Keyless: only the proposal_hash reference is required.
        let mut payload = BTreeMap::new();
        payload.insert("proposal_hash".to_string(), Value::Bytes(proposal_hash.0.to_vec()));
        let req = Message::new(msg_type::ACCEPT_BET_RETIRED_PROPOSAL, 1, payload);

        let resp = handle_accept_bet_retired_proposal(&mut state, &req).expect("seal");
        assert!(resp.is_some());
        assert_eq!(count_nodes(&state, events::NODE_TYPE_BET_RETIRED_PREFIX), 1);
        assert_eq!(current_cultivation_state(&state), CultivationState::Archived);
        assert!(is_archived(&state), "substrate must be alive::archived after the seal");
    }

    #[test]
    fn bet_retired_rejects_missing_proposal() {
        // A proposal_hash that points to no DAG node is rejected (the structural gate).
        let mut state = test_state();
        let mut payload = BTreeMap::new();
        payload.insert("proposal_hash".to_string(), Value::Bytes(vec![0xEEu8; 32]));
        let req = Message::new(msg_type::ACCEPT_BET_RETIRED_PROPOSAL, 1, payload);
        assert!(handle_accept_bet_retired_proposal(&mut state, &req).is_err());
        assert_eq!(count_nodes(&state, events::NODE_TYPE_BET_RETIRED_PREFIX), 0);
    }
}
