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

/// Nanoseconds per anchor-day (24h). Used to convert the L1/GOVERNANCE
/// anchor-day windows (cadence 30d, legacy 365d, terminal 730d) to the
/// nanosecond timestamps the heartbeat envelopes carry.
pub(crate) const NANOS_PER_DAY: i64 = 86_400_000_000_000;

/// **COV06 §3.2.C** — minimum dual-signed Layer-D Catechumenate sessions a
/// successor must accumulate before F21 activation. Per META §6.3 + COV06 §5.3:
/// activation that lacks ≥50 sessions is `owner_succession_bypass` (C46). This
/// is the gate that makes succession **un-fabricable in production** — synthetic
/// tests pass a count directly (49 → C46, 50 → proceeds), but a real successor
/// must accumulate 50 real dual-signed sessions.
pub(crate) const CATECHUMENATE_MIN_SESSIONS: u64 = 50;

// ---------------------------------------------------------------------------
// Built-in succession-config defaults (anchor-days). L1-tunable via the
// `cultivation_succession_config_declared` CI event; test-overridable via env.
// ---------------------------------------------------------------------------

/// Default heartbeat cadence (anchor-days). L1/GOVERNANCE §3.2.B; range [1, 90].
pub(crate) const DEFAULT_CADENCE_DAYS: u64 = 30;
/// Default normal→orphaned legacy window (anchor-days). L1/GOVERNANCE §3.2.C.
pub(crate) const DEFAULT_LEGACY_WINDOW_DAYS: u64 = 365;
/// Default orphaned→terminal window (anchor-days). L1/GOVERNANCE §3.2.C.
pub(crate) const DEFAULT_ORPHANED_TERMINAL_WINDOW_DAYS: u64 = 730;
/// Default genesis terminal choice when no config is declared. L1/GOVERNANCE
/// §3.2.C: `indefinite_orphan` is the conservative default (acknowledged-debt;
/// no auto-death, no auto-archive — the cultivar persists in limbo until a
/// successor recovers it or the cultivator declares a choice).
pub(crate) const DEFAULT_TERMINAL_CHOICE: &str = "indefinite_orphan";

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
///   - `cultivation_orphaned:{pk}`         → Orphaned (legacy→orphaned). Also set
///                                            by `cultivation_orphaned_terminal`
///                                            markers (still Orphaned until a
///                                            terminal seal/death lands).
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
            // Covers both `cultivation_orphaned:{pk}` and the
            // `cultivation_orphaned_terminal` marker (same prefix).
            current = CultivationState::Orphaned;
        } else if nt.starts_with(crate::events::NODE_TYPE_SUCCESSION_COMPLETED_PREFIX)
            || nt == crate::events::NODE_TYPE_CULTIVATOR_HEARTBEAT_RESUMED
        {
            // T3 (succession activation) and T2 (heartbeat resume) both return
            // the substrate to alive::normal from alive::legacy.
            current = CultivationState::Normal;
        } else if nt.starts_with(crate::events::NODE_TYPE_CULTIVATOR_HEARTBEAT_STALE_PREFIX) {
            current = CultivationState::Legacy;
        }
    }
    current
}

/// **COV06** — PURE staleness in whole anchor-days between a last-heartbeat
/// timestamp and a "now" anchor timestamp (both nanosecond unix). Negative
/// deltas (clock skew / now-before-last) clamp to 0. Deterministic — reads no
/// clock — so the autonomous-tick staleness logic + its tests are reproducible.
pub fn compute_staleness(last_hb_unix_ns: i64, now_anchor_unix_ns: i64) -> i64 {
    let delta = now_anchor_unix_ns.saturating_sub(last_hb_unix_ns);
    if delta <= 0 {
        0
    } else {
        delta / NANOS_PER_DAY
    }
}

/// **COV06 §5.3 (C46)** — the catechumenate-floor predicate: returns `true` when
/// the successor has fewer than [`CATECHUMENATE_MIN_SESSIONS`] dual-signed Layer-D
/// sessions. A `true` result MUST reject a succession-acceptance with C46
/// (`owner_succession_bypass`). Pure + total (no clock, no DAG).
pub fn catechumenate_below_min(session_count: u64) -> bool {
    session_count < CATECHUMENATE_MIN_SESSIONS
}

/// **COV06 §3.2.C** — the resolved cultivation config used by the autonomous
/// tick + handlers. Built from (in priority order): `MYCO_TEST_*` env overrides
/// (test-only) → the latest `cultivation_succession_config_declared` DAG event
/// (mirrored onto `ServerState::succession_config`) → the built-in defaults.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SuccessionConfig {
    /// Heartbeat cadence (anchor-days).
    pub cadence_days: u64,
    /// normal→orphaned legacy window (anchor-days).
    pub legacy_window_days: u64,
    /// orphaned→terminal window (anchor-days).
    pub orphaned_terminal_window_days: u64,
    /// `self_euthanasia` | `bet_retirement` | `indefinite_orphan`.
    pub terminal_choice: String,
}

impl SuccessionConfig {
    /// Staleness threshold for T1 (normal→legacy): **3× cadence** per COV06 §3.1
    /// + L1/GOVERNANCE §3.2.B (default 90 anchor-days).
    pub fn staleness_threshold_days(&self) -> u64 {
        self.cadence_days.saturating_mul(3)
    }

    /// Resolve the effective config for a substrate. Priority:
    ///   1. `MYCO_TEST_*` env overrides (each field independent; test-only).
    ///   2. The declared config mirrored onto `ServerState::succession_config`.
    ///   3. Built-in defaults.
    ///
    /// Env vars (production must NOT set these): `MYCO_TEST_CULTIVATION_CADENCE_DAYS`,
    /// `MYCO_TEST_CULTIVATION_LEGACY_WINDOW_DAYS`,
    /// `MYCO_TEST_CULTIVATION_TERMINAL_WINDOW_DAYS`,
    /// `MYCO_TEST_CULTIVATION_TERMINAL_CHOICE`.
    pub(crate) fn resolve(state: &ServerState) -> SuccessionConfig {
        let declared = state.succession_config.as_ref();
        let cadence_days = env_u64("MYCO_TEST_CULTIVATION_CADENCE_DAYS")
            .or_else(|| declared.map(|c| c.cadence_days))
            .unwrap_or(DEFAULT_CADENCE_DAYS);
        let legacy_window_days = env_u64("MYCO_TEST_CULTIVATION_LEGACY_WINDOW_DAYS")
            .or_else(|| declared.map(|c| c.legacy_window_days))
            .unwrap_or(DEFAULT_LEGACY_WINDOW_DAYS);
        let orphaned_terminal_window_days = env_u64("MYCO_TEST_CULTIVATION_TERMINAL_WINDOW_DAYS")
            .or_else(|| declared.map(|c| c.orphaned_terminal_window_days))
            .unwrap_or(DEFAULT_ORPHANED_TERMINAL_WINDOW_DAYS);
        let terminal_choice = std::env::var("MYCO_TEST_CULTIVATION_TERMINAL_CHOICE")
            .ok()
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .or_else(|| declared.map(|c| c.terminal_choice.clone()))
            .unwrap_or_else(|| DEFAULT_TERMINAL_CHOICE.to_string());
        SuccessionConfig {
            cadence_days,
            legacy_window_days,
            orphaned_terminal_window_days,
            terminal_choice,
        }
    }
}

/// Read a `u64` from an env var, returning `None` if unset / unparseable.
fn env_u64(key: &str) -> Option<u64> {
    std::env::var(key).ok().and_then(|s| s.trim().parse::<u64>().ok())
}

/// **COV06** — resolve the "now" anchor timestamp the autonomous-tick staleness
/// watchdog measures against. Priority:
///   1. `MYCO_TEST_ANCHOR_NOW_NS` (test-only deterministic clock).
///   2. The latest threaded anchor stamp from `ServerState::latest_heartbeat`
///      PLUS the wall-clock elapsed since — but the substrate MUST NOT read its
///      own clock for liveness (AS §5.2). So in the absence of the test override
///      AND a fresh operator-threaded anchor stamp, we return `None` (no
///      staleness decision is made; the watchdog is a no-op). Production
///      staleness is driven by the operator threading periodic anchor stamps
///      (the heartbeat-query cadence), which lands `cultivator_heartbeat_recorded`
///      events carrying anchor wall-clock — the same path used in tests.
pub(crate) fn resolve_anchor_now_ns() -> Option<i64> {
    env_u64("MYCO_TEST_ANCHOR_NOW_NS").map(|v| v as i64)
}

// ===========================================================================
// Operator-facing handlers (Step 5).
// ===========================================================================

use crate::server::{emit_immune_sporocarp, emit_substrate_event};
use crate::SubstrateError;
use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
use myco_kernel_shared::crypto::verify_signature;
use std::collections::BTreeMap;

/// Domain-separation context for the anchor heartbeat envelope signature.
const HEARTBEAT_CONTEXT: &str = "myco-cultivator-liveness-heartbeat-v1";
/// Domain-separation context for the successor-chain-entry attestation.
const SUCCESSOR_CHAIN_CONTEXT: &str = "myco-successor-chain-entry-v1";
/// Domain-separation context for the succession-acceptance signature.
const SUCCESSION_ACCEPTANCE_CONTEXT: &str = "myco-succession-acceptance-v1";

/// Reconstruct the canonical signing input for a `cultivator_liveness_heartbeat`
/// envelope (AS §3.7). The anchor signs THIS; the substrate re-derives + verifies
/// against the active owner pubkey. The `substrate_id` + `heartbeat_nonce` bind
/// the signature to this substrate + block replay across pulses.
fn heartbeat_signing_input(
    substrate_id: &[u8; 32],
    cultivator_pubkey: &[u8; 32],
    anchor_timestamp_unix_ns: i64,
    valid_until_unix_ns: i64,
    heartbeat_nonce: &[u8; 32],
) -> Result<Vec<u8>, SubstrateError> {
    let mut m = BTreeMap::new();
    m.insert("context".to_string(), Value::String(HEARTBEAT_CONTEXT.to_string()));
    m.insert("substrate_id".to_string(), Value::Bytes(substrate_id.to_vec()));
    m.insert(
        "cultivator_pubkey".to_string(),
        Value::Bytes(cultivator_pubkey.to_vec()),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(anchor_timestamp_unix_ns),
    );
    m.insert(
        "valid_until_unix_ns".to_string(),
        Value::Timestamp(valid_until_unix_ns),
    );
    m.insert(
        "heartbeat_nonce".to_string(),
        Value::Bytes(heartbeat_nonce.to_vec()),
    );
    cb_encode(&Value::Map(m))
        .map(|cb| cb.0)
        .map_err(|e| SubstrateError::Protocol(format!("heartbeat signing input encode: {e}")))
}

/// Reconstruct the canonical signing input for a successor-chain-entry
/// attestation. The active cultivator (or `alive::legacy` cultivator) signs THIS.
fn successor_chain_signing_input(
    substrate_id: &[u8; 32],
    successor_pubkey: &[u8; 32],
    valid_from_unix_ns: i64,
    valid_until_unix_ns: Option<i64>,
) -> Result<Vec<u8>, SubstrateError> {
    let mut m = BTreeMap::new();
    m.insert(
        "context".to_string(),
        Value::String(SUCCESSOR_CHAIN_CONTEXT.to_string()),
    );
    m.insert("substrate_id".to_string(), Value::Bytes(substrate_id.to_vec()));
    m.insert(
        "successor_pubkey".to_string(),
        Value::Bytes(successor_pubkey.to_vec()),
    );
    m.insert(
        "valid_from_unix_ns".to_string(),
        Value::Timestamp(valid_from_unix_ns),
    );
    match valid_until_unix_ns {
        Some(t) => {
            m.insert("valid_until_unix_ns".to_string(), Value::Timestamp(t));
        }
        None => {
            m.insert("valid_until_unix_ns".to_string(), Value::Null);
        }
    }
    cb_encode(&Value::Map(m))
        .map(|cb| cb.0)
        .map_err(|e| SubstrateError::Protocol(format!("successor chain signing input encode: {e}")))
}

/// Reconstruct the canonical signing input for a `succession_acceptance`
/// (T3). The successor signs THIS with their OWN key.
fn succession_acceptance_signing_input(
    substrate_id: &[u8; 32],
    successor_pubkey: &[u8; 32],
    prior_cultivator_pubkey: &[u8; 32],
    anchor_timestamp_unix_ns: i64,
) -> Result<Vec<u8>, SubstrateError> {
    let mut m = BTreeMap::new();
    m.insert(
        "context".to_string(),
        Value::String(SUCCESSION_ACCEPTANCE_CONTEXT.to_string()),
    );
    m.insert("substrate_id".to_string(), Value::Bytes(substrate_id.to_vec()));
    m.insert(
        "successor_pubkey".to_string(),
        Value::Bytes(successor_pubkey.to_vec()),
    );
    m.insert(
        "prior_cultivator_pubkey".to_string(),
        Value::Bytes(prior_cultivator_pubkey.to_vec()),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(anchor_timestamp_unix_ns),
    );
    cb_encode(&Value::Map(m))
        .map(|cb| cb.0)
        .map_err(|e| SubstrateError::Protocol(format!("succession acceptance signing input encode: {e}")))
}

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

/// **COV06** — handle `record_cultivator_heartbeat`. Verify the anchor signature
/// over the canonical heartbeat envelope against the active owner pubkey (the
/// pinned operator IDENTITY, M9 TOFU). On success emit
/// `cultivator_heartbeat_recorded` + refresh the latest-heartbeat mirror; if the
/// substrate is currently `alive::legacy` AND the SAME cultivator pubkey signs,
/// ALSO emit `cultivator_heartbeat_resumed` (T2 legacy→normal recovery).
pub(crate) fn handle_record_cultivator_heartbeat(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let pinned = state
        .pinned_operator_identity
        .as_ref()
        .ok_or_else(|| {
            SubstrateError::Protocol(
                "record_cultivator_heartbeat: no pinned operator identity (M9 TOFU not completed)"
                    .to_string(),
            )
        })?
        .clone();

    let cultivator_pubkey: [u8; 32] = payload_bytes(request, "cultivator_pubkey")?;
    let anchor_timestamp_unix_ns = payload_timestamp(request, "anchor_timestamp_unix_ns")?;
    let valid_until_unix_ns = payload_timestamp(request, "valid_until_unix_ns")?;
    let heartbeat_nonce: [u8; 32] = payload_bytes(request, "heartbeat_nonce")?;
    let anchor_signature: [u8; 64] = payload_bytes(request, "anchor_signature")?;

    // The anchor signature is verified against the ACTIVE owner pubkey. In the
    // pinned-operator-identity model the operator IDENTITY key IS the owner key
    // (post-M-anchor-1, the operator signing path routes through the anchor
    // surface host). The heartbeat envelope's `cultivator_pubkey` field declares
    // WHO is alive; the signature must come from the pinned owner.
    let substrate_id = state.substrate_id();
    let signing_input = heartbeat_signing_input(
        &substrate_id,
        &cultivator_pubkey,
        anchor_timestamp_unix_ns,
        valid_until_unix_ns,
        &heartbeat_nonce,
    )?;
    if verify_signature(&pinned.pubkey, &anchor_signature, &signing_input).is_err() {
        let _ = emit_immune_sporocarp(
            state,
            "C5_attestation_invalid",
            "attestation_invalid",
            "record_cultivator_heartbeat: anchor signature invalid",
        );
        return Err(SubstrateError::Protocol(
            "record_cultivator_heartbeat: anchor signature invalid".to_string(),
        ));
    }

    // T2 detection: was the substrate in alive::legacy, and is the SAME prior
    // cultivator pubkey resuming? Compute BEFORE emitting the recorded event.
    let was_legacy = current_cultivation_state(state) == CultivationState::Legacy;
    let resuming = was_legacy
        && state
            .latest_heartbeat
            .as_ref()
            .map(|h| h.cultivator_pubkey == cultivator_pubkey)
            .unwrap_or(true); // empty history but legacy → still a resume by the signer

    let cycle = state.cycle_counter();
    let recorded_content = crate::events::encode_cultivator_heartbeat_recorded(
        &cultivator_pubkey,
        anchor_timestamp_unix_ns,
        valid_until_unix_ns,
        &heartbeat_nonce,
        &anchor_signature,
        cycle,
    );
    let recorded_hash = emit_substrate_event(
        state,
        crate::events::NODE_TYPE_CULTIVATOR_HEARTBEAT_RECORDED.to_string(),
        recorded_content,
    )?;

    if resuming {
        let resumed_content = crate::events::encode_cultivator_heartbeat_resumed(
            &cultivator_pubkey,
            anchor_timestamp_unix_ns,
            cycle,
        );
        let _ = emit_substrate_event(
            state,
            crate::events::NODE_TYPE_CULTIVATOR_HEARTBEAT_RESUMED.to_string(),
            resumed_content,
        )?;
    }

    // Refresh the latest-heartbeat mirror (the staleness watchdog's reference).
    state.latest_heartbeat = Some(crate::derived_state::DerivedLatestHeartbeat {
        cultivator_pubkey,
        anchor_timestamp_unix_ns,
    });

    let new_state = current_cultivation_state(state);
    let mut payload = BTreeMap::new();
    payload.insert(
        "recorded_event_hash".to_string(),
        Value::Bytes(recorded_hash.0.to_vec()),
    );
    payload.insert("resumed".to_string(), Value::Bool(resuming));
    payload.insert(
        "cultivation_state".to_string(),
        Value::String(new_state.label().to_string()),
    );
    Ok(Some(Message::new(
        msg_type::RECORD_CULTIVATOR_HEARTBEAT_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// **COV06 §3.2.A (F21)** — handle `update_successor_chain`. CI-attested append
/// of a SuccessorEntry: verify the owner attestation over the entry envelope,
/// validate monotone `valid_from` (strictly increasing vs the last entry) +
/// non-overlapping intervals, then emit `successor_chain_updated:{pk}` + mirror
/// the entry onto `ServerState::successor_chain`.
pub(crate) fn handle_update_successor_chain(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let pinned = state
        .pinned_operator_identity
        .as_ref()
        .ok_or_else(|| {
            SubstrateError::Protocol(
                "update_successor_chain: no pinned operator identity (M9 TOFU not completed)"
                    .to_string(),
            )
        })?
        .clone();

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
    let attestation_signature: [u8; 64] = payload_bytes(request, "attestation_signature")?;

    // Verify the owner attestation over the entry envelope.
    let substrate_id = state.substrate_id();
    let signing_input = successor_chain_signing_input(
        &substrate_id,
        &successor_pubkey,
        valid_from_unix_ns,
        valid_until_unix_ns,
    )?;
    if verify_signature(&pinned.pubkey, &attestation_signature, &signing_input).is_err() {
        let _ = emit_immune_sporocarp(
            state,
            "C5_attestation_invalid",
            "attestation_invalid",
            "update_successor_chain: attestation signature invalid",
        );
        return Err(SubstrateError::Protocol(
            "update_successor_chain: attestation signature invalid".to_string(),
        ));
    }

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
        &attestation_signature,
        chain_position,
        cycle,
    );
    let nt = crate::events::successor_chain_updated_node_type(&successor_pubkey);
    let updated_hash = emit_substrate_event(state, nt, content)?;

    state.successor_chain.push(crate::derived_state::DerivedSuccessorEntry {
        successor_pubkey,
        valid_from_unix_ns,
        valid_until_unix_ns,
        attestation_signature,
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

/// **COV06 T3** — handle `accept_succession`. The chain-head successor signs a
/// `succession_acceptance`. Gates (in order):
///   1. Verify the successor signature against the SUCCESSOR's own pubkey.
///   2. **C46** (`owner_succession_bypass`): reject if
///      `catechumenate_session_count < 50` (the un-fabricable gate).
///   3. **C12** (`successor_activation_with_fresh_owner_heartbeat`): reject if the
///      cultivator heartbeat is still FRESH — succession is for incapacity, not
///      takeover. Freshness = staleness < staleness_threshold (3× cadence), using
///      the operator-threaded `anchor_timestamp_unix_ns` as "now".
///   4. Else emit `succession_completed:{successor_pubkey}` + `owner_key_added`
///      (appends to owner_key_history per the FSM diagram).
pub(crate) fn handle_accept_succession(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let successor_pubkey: [u8; 32] = payload_bytes(request, "successor_pubkey")?;
    let prior_cultivator_pubkey: [u8; 32] = payload_bytes(request, "prior_cultivator_pubkey")?;
    let anchor_timestamp_unix_ns = payload_timestamp(request, "anchor_timestamp_unix_ns")?;
    let successor_signature: [u8; 64] = payload_bytes(request, "successor_signature")?;
    let catechumenate_session_count = match request.payload.get("catechumenate_session_count") {
        Some(Value::Uint(n)) => *n,
        _ => {
            return Err(SubstrateError::Protocol(
                "accept_succession: catechumenate_session_count must be Uint".to_string(),
            ))
        }
    };

    // Gate 1: verify the successor's signature with the SUCCESSOR's own key
    // (the successor presents their own pubkey + signs the acceptance envelope).
    let substrate_id = state.substrate_id();
    let signing_input = succession_acceptance_signing_input(
        &substrate_id,
        &successor_pubkey,
        &prior_cultivator_pubkey,
        anchor_timestamp_unix_ns,
    )?;
    if verify_signature(&successor_pubkey, &successor_signature, &signing_input).is_err() {
        let _ = emit_immune_sporocarp(
            state,
            "C5_attestation_invalid",
            "attestation_invalid",
            "accept_succession: successor signature invalid",
        );
        return Err(SubstrateError::Protocol(
            "accept_succession: successor signature invalid".to_string(),
        ));
    }

    // Gate 2 (C46): catechumenate floor. The un-fabricable production gate —
    // a real successor must accumulate ≥50 real dual-signed Layer-D sessions.
    if catechumenate_below_min(catechumenate_session_count) {
        let evidence = format!(
            "accept_succession: catechumenate_session_count={catechumenate_session_count} < \
             CATECHUMENATE_MIN_SESSIONS={CATECHUMENATE_MIN_SESSIONS}; F21 activation REQUIRES \
             ≥50 dual-signed Layer-D sessions (COV06 §5.3 + META §6.3). Premature succession \
             = owner_succession_bypass."
        );
        let _ = emit_immune_sporocarp(
            state,
            "C46_owner_succession_bypass",
            "owner_succession_bypass",
            &evidence,
        );
        return Err(SubstrateError::Protocol(evidence));
    }

    // Gate 3 (C12): refuse succession while the cultivator heartbeat is FRESH —
    // succession is for incapacity, not takeover (FSM: succession is a legacy→
    // normal transition; if normal/fresh, there is nothing to succeed). Freshness
    // is measured against the operator-threaded acceptance anchor timestamp.
    let cfg = SuccessionConfig::resolve(state);
    let threshold_days = cfg.staleness_threshold_days() as i64;
    if let Some(hb) = state.latest_heartbeat.as_ref() {
        // Only the PRIOR cultivator's heartbeat freshness gates succession.
        if hb.cultivator_pubkey == prior_cultivator_pubkey {
            let staleness_days =
                compute_staleness(hb.anchor_timestamp_unix_ns, anchor_timestamp_unix_ns);
            if staleness_days < threshold_days {
                let evidence = format!(
                    "accept_succession: cultivator heartbeat is still FRESH \
                     (staleness {staleness_days}d < threshold {threshold_days}d); succession is \
                     for incapacity, not takeover (C12). Wait for staleness or use \
                     cultivator-attested key rotation instead."
                );
                let _ = emit_immune_sporocarp(
                    state,
                    "C12_successor_activation_with_fresh_owner_heartbeat",
                    "successor_activation_with_fresh_owner_heartbeat",
                    &evidence,
                );
                return Err(SubstrateError::Protocol(evidence));
            }
        }
    }

    // All gates passed → emit succession_completed (T3) + owner_key_added.
    let cycle = state.cycle_counter();
    let content = crate::events::encode_succession_completed(
        &successor_pubkey,
        &prior_cultivator_pubkey,
        anchor_timestamp_unix_ns,
        &successor_signature,
        catechumenate_session_count,
        cycle,
    );
    let nt = crate::events::succession_completed_node_type(&successor_pubkey);
    let completed_hash = emit_substrate_event(state, nt, content)?;

    // Append to owner_key_history (FSM diagram T3 effect). The anchor timestamp
    // is nanoseconds; owner_key_added records seconds.
    let anchor_ts_seconds = (anchor_timestamp_unix_ns / 1_000_000_000).max(0) as u64;
    let owner_key_content = crate::events::encode_owner_key_added(
        &successor_pubkey,
        &prior_cultivator_pubkey,
        anchor_ts_seconds,
    );
    let _ = emit_substrate_event(
        state,
        crate::events::NODE_TYPE_OWNER_KEY_ADDED.to_string(),
        owner_key_content,
    )?;

    let new_state = current_cultivation_state(state);
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

/// Domain-separation context for the bet-retirement co-attestation.
const BET_RETIRED_CONTEXT: &str = "myco-bet-retired-seal-v1";

/// **COV06 T7 / LB §4** — handle `accept_bet_retired_proposal`. The cultivator
/// co-attests a `bet_retired_proposal` (emitted by the COV06-T7 orphaned-terminal
/// watchdog OR an LB §4 living-bet quorum). Steps:
///   1. Verify the cultivator signature over `canonical_bytes(Map({context,
///      substrate_id, proposal_hash}))` against the active owner pubkey.
///   2. Confirm `proposal_hash` points to a real `bet_retired_proposal` in the
///      DAG; extract its `reason`.
///   3. Emit `bet_retired:{reason}` — the archive seal. The substrate is now
///      `alive::archived` (sticky): metabolism halts, state_dir preserved
///      cold-readable. The main loop, observing this message type, exits cleanly
///      (re-spawn re-derives Archived + the metabolism guard refuses cycling).
///
/// This single seal serves BOTH COV06-T7 (orphaned→archived) AND LB_living_bets
/// §4 (living-bet retirement) — `alive::archived` is designed once for both.
pub(crate) fn handle_accept_bet_retired_proposal(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, map_get_string, Value as CbV};

    let pinned = state
        .pinned_operator_identity
        .as_ref()
        .ok_or_else(|| {
            SubstrateError::Protocol(
                "accept_bet_retired_proposal: no pinned operator identity (M9 TOFU not completed)"
                    .to_string(),
            )
        })?
        .clone();

    let proposal_hash: [u8; 32] = payload_bytes(request, "proposal_hash")?;
    let cultivator_signature: [u8; 64] = payload_bytes(request, "cultivator_signature")?;

    // Verify the cultivator co-attestation over (context, substrate_id, proposal_hash).
    let substrate_id = state.substrate_id();
    let mut signing_map = BTreeMap::new();
    signing_map.insert(
        "context".to_string(),
        Value::String(BET_RETIRED_CONTEXT.to_string()),
    );
    signing_map.insert("substrate_id".to_string(), Value::Bytes(substrate_id.to_vec()));
    signing_map.insert(
        "proposal_hash".to_string(),
        Value::Bytes(proposal_hash.to_vec()),
    );
    let signing_input = cb_encode(&Value::Map(signing_map))
        .map_err(|e| SubstrateError::Protocol(format!("bet_retired signing input encode: {e}")))?;
    if verify_signature(&pinned.pubkey, &cultivator_signature, signing_input.as_ref()).is_err() {
        let _ = emit_immune_sporocarp(
            state,
            "C5_attestation_invalid",
            "attestation_invalid",
            "accept_bet_retired_proposal: cultivator signature invalid",
        );
        return Err(SubstrateError::Protocol(
            "accept_bet_retired_proposal: cultivator signature invalid".to_string(),
        ));
    }

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
        &cultivator_signature,
        &pinned.pubkey,
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
/// stays cold-readable. Pure DAG derivation.
pub(crate) fn is_archived(state: &ServerState) -> bool {
    current_cultivation_state(state) == CultivationState::Archived
}

#[cfg(test)]
mod tests {
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
            None,
            [0u8; 32],
        )
    }

    /// Push a cultivation event onto the DAG (tip-parented).
    fn push(state: &mut ServerState, node_type: String, content: myco_kernel_shared::canonical_bytes::CanonicalBytes) {
        let parents = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let cycle = state.cycle_counter();
        state.dag.insert_node(parents, node_type, cycle, content).expect("insert");
    }

    fn pk(b: u8) -> [u8; 32] {
        [b; 32]
    }

    // ---- compute_staleness ----

    #[test]
    fn staleness_zero_when_now_equals_last() {
        assert_eq!(compute_staleness(1000, 1000), 0);
    }

    #[test]
    fn staleness_clamps_negative_to_zero() {
        // now BEFORE last (clock skew) → 0, never negative.
        assert_eq!(compute_staleness(2000, 1000), 0);
    }

    #[test]
    fn staleness_counts_whole_days() {
        let last = 0i64;
        let now = 90 * NANOS_PER_DAY + 12 * 3_600_000_000_000; // 90.5 days
        assert_eq!(compute_staleness(last, now), 90);
    }

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

    // ---- SuccessionConfig defaults ----

    #[test]
    fn config_defaults_when_none_declared() {
        let state = test_state();
        let cfg = SuccessionConfig::resolve(&state);
        assert_eq!(cfg.cadence_days, 30);
        assert_eq!(cfg.legacy_window_days, 365);
        assert_eq!(cfg.orphaned_terminal_window_days, 730);
        assert_eq!(cfg.terminal_choice, "indefinite_orphan");
        assert_eq!(cfg.staleness_threshold_days(), 90); // 3× cadence
    }

    #[test]
    fn config_uses_declared_when_present() {
        let mut state = test_state();
        state.succession_config = Some(crate::derived_state::DerivedSuccessionConfig {
            cadence_days: 7,
            legacy_window_days: 100,
            orphaned_terminal_window_days: 200,
            terminal_choice: "bet_retirement".to_string(),
        });
        let cfg = SuccessionConfig::resolve(&state);
        assert_eq!(cfg.cadence_days, 7);
        assert_eq!(cfg.legacy_window_days, 100);
        assert_eq!(cfg.terminal_choice, "bet_retirement");
        assert_eq!(cfg.staleness_threshold_days(), 21);
    }

    // ---- current_cultivation_state FSM derivation ----

    #[test]
    fn state_normal_with_no_events() {
        let state = test_state();
        assert_eq!(current_cultivation_state(&state), CultivationState::Normal);
    }

    #[test]
    fn state_legacy_after_heartbeat_stale() {
        let mut state = test_state();
        let p = pk(0xAA);
        push(
            &mut state,
            events::cultivator_heartbeat_stale_node_type(&p),
            events::encode_cultivator_heartbeat_stale(&p, 0, 90 * NANOS_PER_DAY, 90, 30, 1),
        );
        assert_eq!(current_cultivation_state(&state), CultivationState::Legacy);
    }

    #[test]
    fn state_normal_after_resume_following_stale() {
        let mut state = test_state();
        let p = pk(0xAA);
        push(
            &mut state,
            events::cultivator_heartbeat_stale_node_type(&p),
            events::encode_cultivator_heartbeat_stale(&p, 0, 90 * NANOS_PER_DAY, 90, 30, 1),
        );
        push(
            &mut state,
            events::NODE_TYPE_CULTIVATOR_HEARTBEAT_RESUMED.to_string(),
            events::encode_cultivator_heartbeat_resumed(&p, 100 * NANOS_PER_DAY, 2),
        );
        assert_eq!(current_cultivation_state(&state), CultivationState::Normal);
    }

    #[test]
    fn state_orphaned_after_orphan_following_legacy() {
        let mut state = test_state();
        let p = pk(0xAA);
        push(
            &mut state,
            events::cultivator_heartbeat_stale_node_type(&p),
            events::encode_cultivator_heartbeat_stale(&p, 0, 90 * NANOS_PER_DAY, 90, 30, 1),
        );
        push(
            &mut state,
            events::cultivation_orphaned_node_type(&p),
            events::encode_cultivation_orphaned(&p, 365 * NANOS_PER_DAY, "legacy_window_elapsed", 2),
        );
        assert_eq!(current_cultivation_state(&state), CultivationState::Orphaned);
    }

    #[test]
    fn state_normal_after_succession_following_legacy() {
        let mut state = test_state();
        let prior = pk(0xAA);
        let succ = pk(0xBB);
        push(
            &mut state,
            events::cultivator_heartbeat_stale_node_type(&prior),
            events::encode_cultivator_heartbeat_stale(&prior, 0, 90 * NANOS_PER_DAY, 90, 30, 1),
        );
        let sig = [0x11u8; 64];
        push(
            &mut state,
            events::succession_completed_node_type(&succ),
            events::encode_succession_completed(&succ, &prior, 100 * NANOS_PER_DAY, &sig, 50, 2),
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
            events::encode_cultivation_orphaned(&p, 365 * NANOS_PER_DAY, "legacy_window_elapsed", 1),
        );
        push(
            &mut state,
            events::cultivation_recovered_node_type(&p),
            events::encode_cultivation_recovered(&p, "court-ref", 400 * NANOS_PER_DAY, 2),
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
            events::encode_cultivation_orphaned(&p, 365 * NANOS_PER_DAY, "legacy_window_elapsed", 1),
        );
        let hash = [0x22u8; 32];
        let sig = [0x33u8; 64];
        push(
            &mut state,
            events::bet_retired_node_type("cultivation_orphaned_terminal"),
            events::encode_bet_retired("cultivation_orphaned_terminal", &hash, &sig, &p, 2, 730 * NANOS_PER_DAY),
        );
        assert_eq!(current_cultivation_state(&state), CultivationState::Archived);

        // A stray later heartbeat-stale event must NOT resurrect from archived.
        push(
            &mut state,
            events::cultivator_heartbeat_stale_node_type(&p),
            events::encode_cultivator_heartbeat_stale(&p, 0, 90 * NANOS_PER_DAY, 90, 30, 3),
        );
        assert_eq!(
            current_cultivation_state(&state),
            CultivationState::Archived,
            "archived is terminal — sticky against later events"
        );
    }

    // ===================================================================
    // Handler tests (Step 5) — exercise signature gates + FSM transitions.
    // ===================================================================

    use myco_kernel_shared::crypto::Ed25519PrivateKey;

    /// Build a state with a pinned operator identity whose pubkey is derived
    /// from `seed` (so signatures made with `seed` verify as the owner).
    fn pinned_state(seed: &[u8; 32]) -> ServerState {
        let mut state = test_state();
        let pubkey = Ed25519PrivateKey::from_seed(seed).public_key().0;
        state.pinned_operator_identity = Some(crate::persistence::PinnedOperatorIdentity {
            pubkey,
            first_pinned_unix_ns: 0,
        });
        state
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

    fn heartbeat_request(
        seed: &[u8; 32],
        substrate_id: &[u8; 32],
        cultivator_pubkey: &[u8; 32],
        anchor_ts: i64,
        nonce: &[u8; 32],
        valid_sig: bool,
    ) -> Message {
        let signing_input = heartbeat_signing_input(
            substrate_id,
            cultivator_pubkey,
            anchor_ts,
            anchor_ts + 30 * NANOS_PER_DAY,
            nonce,
        )
        .unwrap();
        let sig = if valid_sig {
            Ed25519PrivateKey::from_seed(seed).sign(&signing_input).as_ref().to_vec()
        } else {
            vec![0u8; 64]
        };
        let mut payload = BTreeMap::new();
        payload.insert("cultivator_pubkey".to_string(), Value::Bytes(cultivator_pubkey.to_vec()));
        payload.insert("anchor_timestamp_unix_ns".to_string(), Value::Timestamp(anchor_ts));
        payload.insert(
            "valid_until_unix_ns".to_string(),
            Value::Timestamp(anchor_ts + 30 * NANOS_PER_DAY),
        );
        payload.insert("heartbeat_nonce".to_string(), Value::Bytes(nonce.to_vec()));
        payload.insert("anchor_signature".to_string(), Value::Bytes(sig));
        Message::new(msg_type::RECORD_CULTIVATOR_HEARTBEAT, 1, payload)
    }

    #[test]
    fn heartbeat_valid_sig_emits_recorded_event() {
        let seed = [0x42u8; 32];
        let mut state = pinned_state(&seed);
        let sid = state.substrate_id();
        let cpk = Ed25519PrivateKey::from_seed(&seed).public_key().0;
        let req = heartbeat_request(&seed, &sid, &cpk, 1000, &[0x01u8; 32], true);
        let resp = handle_record_cultivator_heartbeat(&mut state, &req).expect("ok");
        assert!(resp.is_some());
        assert_eq!(count_nodes(&state, events::NODE_TYPE_CULTIVATOR_HEARTBEAT_RECORDED), 1);
        assert!(state.latest_heartbeat.is_some());
        assert_eq!(state.latest_heartbeat.as_ref().unwrap().anchor_timestamp_unix_ns, 1000);
    }

    #[test]
    fn heartbeat_bad_sig_rejected_and_emits_c5() {
        let seed = [0x42u8; 32];
        let mut state = pinned_state(&seed);
        let sid = state.substrate_id();
        let cpk = Ed25519PrivateKey::from_seed(&seed).public_key().0;
        let req = heartbeat_request(&seed, &sid, &cpk, 1000, &[0x01u8; 32], false);
        let err = handle_record_cultivator_heartbeat(&mut state, &req);
        assert!(err.is_err(), "bad anchor signature must be rejected");
        assert_eq!(count_nodes(&state, events::NODE_TYPE_CULTIVATOR_HEARTBEAT_RECORDED), 0);
        assert!(count_immune(&state, "C5_attestation_invalid") >= 1);
    }

    #[test]
    fn heartbeat_while_legacy_emits_resumed_t2() {
        let seed = [0x42u8; 32];
        let mut state = pinned_state(&seed);
        let cpk = Ed25519PrivateKey::from_seed(&seed).public_key().0;
        // Put the substrate into alive::legacy via a stale event for the same pk.
        push(
            &mut state,
            events::cultivator_heartbeat_stale_node_type(&cpk),
            events::encode_cultivator_heartbeat_stale(&cpk, 0, 90 * NANOS_PER_DAY, 90, 30, 1),
        );
        state.latest_heartbeat = Some(crate::derived_state::DerivedLatestHeartbeat {
            cultivator_pubkey: cpk,
            anchor_timestamp_unix_ns: 0,
        });
        assert_eq!(current_cultivation_state(&state), CultivationState::Legacy);
        let sid = state.substrate_id();
        let req = heartbeat_request(&seed, &sid, &cpk, 100 * NANOS_PER_DAY, &[0x02u8; 32], true);
        handle_record_cultivator_heartbeat(&mut state, &req).expect("ok");
        assert_eq!(count_nodes(&state, events::NODE_TYPE_CULTIVATOR_HEARTBEAT_RESUMED), 1);
        assert_eq!(
            current_cultivation_state(&state),
            CultivationState::Normal,
            "T2: a fresh heartbeat from the prior cultivator resumes alive::normal"
        );
    }

    fn successor_request(
        seed: &[u8; 32],
        substrate_id: &[u8; 32],
        successor_pubkey: &[u8; 32],
        valid_from: i64,
        valid_until: Option<i64>,
    ) -> Message {
        let signing_input =
            successor_chain_signing_input(substrate_id, successor_pubkey, valid_from, valid_until)
                .unwrap();
        let sig = Ed25519PrivateKey::from_seed(seed).sign(&signing_input).as_ref().to_vec();
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
        payload.insert("attestation_signature".to_string(), Value::Bytes(sig));
        Message::new(msg_type::UPDATE_SUCCESSOR_CHAIN, 1, payload)
    }

    #[test]
    fn successor_chain_append_emits_event_and_mirrors() {
        let seed = [0x42u8; 32];
        let mut state = pinned_state(&seed);
        let sid = state.substrate_id();
        let succ = pk(0xCC);
        let req = successor_request(&seed, &sid, &succ, 1000, None);
        handle_update_successor_chain(&mut state, &req).expect("ok");
        assert_eq!(count_nodes(&state, events::NODE_TYPE_SUCCESSOR_CHAIN_UPDATED_PREFIX), 1);
        assert_eq!(state.successor_chain.len(), 1);
        assert_eq!(state.successor_chain[0].successor_pubkey, succ);
    }

    #[test]
    fn successor_chain_rejects_non_monotone_valid_from() {
        let seed = [0x42u8; 32];
        let mut state = pinned_state(&seed);
        let sid = state.substrate_id();
        // First entry closed [1000, 2000).
        let req1 = successor_request(&seed, &sid, &pk(0xCC), 1000, Some(2000));
        handle_update_successor_chain(&mut state, &req1).expect("ok1");
        // Second entry with valid_from BEFORE the first → rejected.
        let req2 = successor_request(&seed, &sid, &pk(0xDD), 500, Some(3000));
        assert!(handle_update_successor_chain(&mut state, &req2).is_err());
        assert_eq!(state.successor_chain.len(), 1, "rejected entry must not be appended");
    }

    #[test]
    fn successor_chain_rejects_overlap_with_open_head() {
        let seed = [0x42u8; 32];
        let mut state = pinned_state(&seed);
        let sid = state.substrate_id();
        // Open-ended head [1000, ∞).
        let req1 = successor_request(&seed, &sid, &pk(0xCC), 1000, None);
        handle_update_successor_chain(&mut state, &req1).expect("ok1");
        // Any later append overlaps the open head → rejected.
        let req2 = successor_request(&seed, &sid, &pk(0xDD), 2000, None);
        assert!(handle_update_successor_chain(&mut state, &req2).is_err());
    }

    fn succession_request(
        successor_seed: &[u8; 32],
        substrate_id: &[u8; 32],
        prior_pk: &[u8; 32],
        anchor_ts: i64,
        session_count: u64,
    ) -> Message {
        let successor_pk = Ed25519PrivateKey::from_seed(successor_seed).public_key().0;
        let signing_input = succession_acceptance_signing_input(
            substrate_id,
            &successor_pk,
            prior_pk,
            anchor_ts,
        )
        .unwrap();
        let sig = Ed25519PrivateKey::from_seed(successor_seed).sign(&signing_input).as_ref().to_vec();
        let mut payload = BTreeMap::new();
        payload.insert("successor_pubkey".to_string(), Value::Bytes(successor_pk.to_vec()));
        payload.insert("prior_cultivator_pubkey".to_string(), Value::Bytes(prior_pk.to_vec()));
        payload.insert("anchor_timestamp_unix_ns".to_string(), Value::Timestamp(anchor_ts));
        payload.insert("successor_signature".to_string(), Value::Bytes(sig));
        payload.insert("catechumenate_session_count".to_string(), Value::Uint(session_count));
        Message::new(msg_type::ACCEPT_SUCCESSION, 1, payload)
    }

    #[test]
    fn succession_below_50_sessions_rejected_c46() {
        let owner_seed = [0x42u8; 32];
        let successor_seed = [0x77u8; 32];
        let mut state = pinned_state(&owner_seed);
        let prior_pk = Ed25519PrivateKey::from_seed(&owner_seed).public_key().0;
        // Make the substrate legacy (stale heartbeat) so C12 doesn't pre-empt C46.
        push(
            &mut state,
            events::cultivator_heartbeat_stale_node_type(&prior_pk),
            events::encode_cultivator_heartbeat_stale(&prior_pk, 0, 90 * NANOS_PER_DAY, 90, 30, 1),
        );
        let sid = state.substrate_id();
        // 12 sessions (COV06 §10.2 borderline) → C46.
        let req = succession_request(&successor_seed, &sid, &prior_pk, 100 * NANOS_PER_DAY, 12);
        assert!(handle_accept_succession(&mut state, &req).is_err());
        assert!(count_immune(&state, "C46_owner_succession_bypass") >= 1);
        assert_eq!(count_nodes(&state, events::NODE_TYPE_SUCCESSION_COMPLETED_PREFIX), 0);
    }

    #[test]
    fn succession_with_fresh_heartbeat_rejected_c12() {
        let owner_seed = [0x42u8; 32];
        let successor_seed = [0x77u8; 32];
        let mut state = pinned_state(&owner_seed);
        let prior_pk = Ed25519PrivateKey::from_seed(&owner_seed).public_key().0;
        // FRESH heartbeat: last pulse at T, acceptance at T+1day (< 90d threshold).
        state.latest_heartbeat = Some(crate::derived_state::DerivedLatestHeartbeat {
            cultivator_pubkey: prior_pk,
            anchor_timestamp_unix_ns: 1000 * NANOS_PER_DAY,
        });
        let sid = state.substrate_id();
        // 50 sessions (passes C46) but heartbeat is fresh → C12.
        let req = succession_request(
            &successor_seed,
            &sid,
            &prior_pk,
            1001 * NANOS_PER_DAY, // 1 day after last heartbeat
            50,
        );
        assert!(handle_accept_succession(&mut state, &req).is_err());
        assert!(count_immune(&state, "C12_successor_activation_with_fresh_owner_heartbeat") >= 1);
        assert_eq!(count_nodes(&state, events::NODE_TYPE_SUCCESSION_COMPLETED_PREFIX), 0);
    }

    #[test]
    fn succession_50_sessions_stale_heartbeat_completes() {
        let owner_seed = [0x42u8; 32];
        let successor_seed = [0x77u8; 32];
        let mut state = pinned_state(&owner_seed);
        let prior_pk = Ed25519PrivateKey::from_seed(&owner_seed).public_key().0;
        // STALE heartbeat: last pulse at T, acceptance 100 days later (> 90d).
        state.latest_heartbeat = Some(crate::derived_state::DerivedLatestHeartbeat {
            cultivator_pubkey: prior_pk,
            anchor_timestamp_unix_ns: 0,
        });
        // Put into legacy so the FSM transition to normal is meaningful.
        push(
            &mut state,
            events::cultivator_heartbeat_stale_node_type(&prior_pk),
            events::encode_cultivator_heartbeat_stale(&prior_pk, 0, 90 * NANOS_PER_DAY, 90, 30, 1),
        );
        let sid = state.substrate_id();
        let req = succession_request(&successor_seed, &sid, &prior_pk, 100 * NANOS_PER_DAY, 50);
        let resp = handle_accept_succession(&mut state, &req).expect("succession completes");
        assert!(resp.is_some());
        assert_eq!(count_nodes(&state, events::NODE_TYPE_SUCCESSION_COMPLETED_PREFIX), 1);
        // owner_key_added emitted (FSM T3 effect).
        assert_eq!(count_nodes(&state, events::NODE_TYPE_OWNER_KEY_ADDED), 1);
        assert_eq!(
            current_cultivation_state(&state),
            CultivationState::Normal,
            "T3: succession returns the substrate to alive::normal"
        );
    }

    #[test]
    fn succession_bad_successor_sig_rejected() {
        let owner_seed = [0x42u8; 32];
        let successor_seed = [0x77u8; 32];
        let mut state = pinned_state(&owner_seed);
        let prior_pk = Ed25519PrivateKey::from_seed(&owner_seed).public_key().0;
        let sid = state.substrate_id();
        let mut req = succession_request(&successor_seed, &sid, &prior_pk, 100 * NANOS_PER_DAY, 50);
        // Corrupt the successor signature.
        req.payload.insert("successor_signature".to_string(), Value::Bytes(vec![0u8; 64]));
        assert!(handle_accept_succession(&mut state, &req).is_err());
        assert_eq!(count_nodes(&state, events::NODE_TYPE_SUCCESSION_COMPLETED_PREFIX), 0);
    }

    #[test]
    fn bet_retired_co_attest_seals_archive_and_is_archived() {
        let owner_seed = [0x42u8; 32];
        let mut state = pinned_state(&owner_seed);
        // Emit a bet_retired_proposal first (as the T7 watchdog would).
        let proposal_content =
            events::encode_bet_retired_proposal("cultivation_orphaned_terminal", 5, 800 * NANOS_PER_DAY);
        let parents = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let proposal_hash = state
            .dag
            .insert_node(
                parents,
                events::NODE_TYPE_BET_RETIRED_PROPOSAL.to_string(),
                state.cycle_counter(),
                proposal_content,
            )
            .expect("insert proposal");

        // Cultivator co-attests over (context, substrate_id, proposal_hash).
        let sid = state.substrate_id();
        let mut m = BTreeMap::new();
        m.insert("context".to_string(), Value::String(BET_RETIRED_CONTEXT.to_string()));
        m.insert("substrate_id".to_string(), Value::Bytes(sid.to_vec()));
        m.insert("proposal_hash".to_string(), Value::Bytes(proposal_hash.0.to_vec()));
        let signing_input = cb_encode(&Value::Map(m)).unwrap().0;
        let sig = Ed25519PrivateKey::from_seed(&owner_seed).sign(&signing_input).as_ref().to_vec();

        let mut payload = BTreeMap::new();
        payload.insert("proposal_hash".to_string(), Value::Bytes(proposal_hash.0.to_vec()));
        payload.insert("cultivator_signature".to_string(), Value::Bytes(sig));
        let req = Message::new(msg_type::ACCEPT_BET_RETIRED_PROPOSAL, 1, payload);

        let resp = handle_accept_bet_retired_proposal(&mut state, &req).expect("seal");
        assert!(resp.is_some());
        assert_eq!(count_nodes(&state, events::NODE_TYPE_BET_RETIRED_PREFIX), 1);
        assert_eq!(current_cultivation_state(&state), CultivationState::Archived);
        assert!(is_archived(&state), "substrate must be alive::archived after the seal");
    }

    #[test]
    fn bet_retired_bad_sig_rejected() {
        let owner_seed = [0x42u8; 32];
        let mut state = pinned_state(&owner_seed);
        let proposal_content =
            events::encode_bet_retired_proposal("bet_falsified", 5, 0);
        let proposal_hash = state
            .dag
            .insert_node(
                Vec::new(),
                events::NODE_TYPE_BET_RETIRED_PROPOSAL.to_string(),
                0,
                proposal_content,
            )
            .expect("insert");
        let mut payload = BTreeMap::new();
        payload.insert("proposal_hash".to_string(), Value::Bytes(proposal_hash.0.to_vec()));
        payload.insert("cultivator_signature".to_string(), Value::Bytes(vec![0u8; 64]));
        let req = Message::new(msg_type::ACCEPT_BET_RETIRED_PROPOSAL, 1, payload);
        assert!(handle_accept_bet_retired_proposal(&mut state, &req).is_err());
        assert_eq!(count_nodes(&state, events::NODE_TYPE_BET_RETIRED_PREFIX), 0);
    }
}
