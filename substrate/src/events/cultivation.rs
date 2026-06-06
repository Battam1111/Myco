//! **COV06 不弃不孤** — cultivator-mortality + succession DAG event vocabulary.
//!
//! L0/cards/COV06_no_abandonment_succession.md mandates that the cultivar must
//! never wake to discover its cultivator has silently vanished. This module
//! defines the **substrate event vocabulary** for the cultivation-succession
//! FSM (L1/GOVERNANCE §3.2; `diagrams/cultivation_succession_fsm.txt`):
//!
//!   alive::normal → alive::legacy → alive::orphaned → {destroyed | archived}
//!                ↑__________________↓ (recovery)
//!
//! The five FSM states (Normal/Legacy/Orphaned/Archived/Recovered) are
//! **DAG-derived** (cf. `crate::cultivation::current_cultivation_state`), not a
//! persisted enum: each transition emits one of the events below, and the
//! derivation walks the DAG for the latest event of the family. The transition
//! labels T1-T8 match the FSM diagram.
//!
//! ## Event types (COV06)
//!
//! | node_type                              | T  | Records                       |
//! |----------------------------------------|----|-------------------------------|
//! | `cultivator_heartbeat_recorded`        | —  | anchor-signed liveness pulse  |
//! | `cultivator_heartbeat_resumed`         | T2 | legacy→normal: fresh heartbeat|
//! | `cultivator_heartbeat_stale:{pk}`      | T1 | normal→legacy: staleness >3×  |
//! | `successor_chain_updated:{pk}`         | —  | F21 SuccessorEntry appended   |
//! | `succession_completed:{pk}`            | T3 | legacy→normal: successor signs|
//! | `cultivation_orphaned:{pk}`            | T4 | legacy→orphaned               |
//! | `cultivation_recovered:{pk}`           | T5 | orphaned→normal (exceptional) |
//! | `cultivation_orphaned_terminal`        | T6 | terminal-window self-eu marker|
//! | `bet_retired:{reason}`                 | T7 | orphaned→archived (LB §4 seal)|
//! | `bet_retired_proposal`                 | —  | LB §4 retirement proposal     |
//! | `cultivation_succession_config_declared`| — | genesis/CI cadence + windows  |
//!
//! ## Determinism contract
//!
//! No floats anywhere — every field is a String / Bytes / Uint / Timestamp, so
//! the canonical-bytes encoding is byte-deterministic across platforms by
//! construction (same discipline as `events/core.rs` + `events/schema_migration.rs`).
//! Anchor wall-clock timestamps are operator-threaded (AS §5.2 forbids the
//! substrate from reading its own clock for liveness); the substrate persists
//! them verbatim from the anchor-signed heartbeat envelope.

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

use super::core::hex_prefix;

// ---------------------------------------------------------------------------
// node_type constants + prefixes.
// ---------------------------------------------------------------------------

/// **F21** prefix for `successor_chain_updated:{pk}` — a SuccessorEntry was
/// appended to the cultivation_successor_chain (§3.2.A). `{pk}` = hex prefix of
/// the appended successor pubkey. CI-attested; non-overlapping monotone intervals.
pub const NODE_TYPE_SUCCESSOR_CHAIN_UPDATED_PREFIX: &str = "successor_chain_updated:";

/// **T3** prefix for `succession_completed:{pk}` — legacy→normal via succession
/// activation: the chain-head successor signed a `succession_acceptance`. `{pk}`
/// = hex prefix of the new (successor) cultivator pubkey. CI, compression-invariant.
pub const NODE_TYPE_SUCCESSION_COMPLETED_PREFIX: &str = "succession_completed:";

/// **T4** prefix for `cultivation_orphaned:{pk}` — legacy→orphaned: legacy_window
/// elapsed (default 365 anchor-days) OR empty successor_chain at legacy entry.
/// `{pk}` = hex prefix of the prior-cultivator pubkey. CI, compression-invariant.
/// P07-PROTECTED + un-suppressible (emitted via `emit_substrate_event`, bypassing
/// the immune rate-limiter, per L0/cards/P07 §4 + L1/GOVERNANCE §3.2.C).
pub const NODE_TYPE_CULTIVATION_ORPHANED_PREFIX: &str = "cultivation_orphaned:";

/// **T5** prefix for `cultivation_recovered:{pk}` — orphaned→normal (exceptional
/// recovery; honor-system court-attested key recovery per AS §6). `{pk}` = hex
/// prefix of the recovering successor pubkey. CI, compression-invariant.
pub const NODE_TYPE_CULTIVATION_RECOVERED_PREFIX: &str = "cultivation_recovered:";

/// **T6** `cultivation_orphaned_terminal` — terminal-window marker (default 730
/// anchor-days). When genesis terminal_choice == self_euthanasia, the autonomous
/// tick emits `self_euthanasia_proposal:cultivation_orphaned_terminal` (a
/// PROPOSAL — the existing accept_self_euthanasia path executes it; NOT
/// auto-death). This bare const names the reason-suffix used in that proposal.
/// P07-protected (in the invariant set as a literal).
pub const NODE_TYPE_CULTIVATION_ORPHANED_TERMINAL: &str = "cultivation_orphaned_terminal";

/// **T7** prefix for `bet_retired:{reason}` — orphaned→archived terminal via
/// LB §4 bet-retirement: state_dir preserved with an anchor `bet_retirement_seal`,
/// cold-readable forensic, recoverable by a future cultivator. ALSO serves
/// LB_living_bets §4 (a living-bet quorum + cultivator co-attest retirement).
/// `{reason}` = the retirement reason (e.g. `cultivation_orphaned_terminal`,
/// `bet_falsified`). P07-protected.
pub const NODE_TYPE_BET_RETIRED_PREFIX: &str = "bet_retired:";

/// `bet_retired_proposal` — the LB §4 retirement PROPOSAL (quorum reached OR
/// orphaned-terminal). Cultivator co-attestation against the proposal hash
/// promotes it to the `bet_retired:{reason}` archive seal. P07-protected.
pub const NODE_TYPE_BET_RETIRED_PROPOSAL: &str = "bet_retired_proposal";

/// `cultivation_succession_config_declared` — genesis (or CI-amend) declaration
/// of the cultivation cadence + windows + terminal_choice. Re-derived at boot;
/// the latest declaration wins. Absent → built-in defaults (cadence 30d,
/// legacy 365d, terminal 730d, choice `indefinite_orphan`).
pub const NODE_TYPE_CULTIVATION_SUCCESSION_CONFIG_DECLARED: &str =
    "cultivation_succession_config_declared";

// ---------------------------------------------------------------------------
// node_type builders.
// ---------------------------------------------------------------------------

/// node_type: `successor_chain_updated:{pk_prefix}` (F21).
pub fn successor_chain_updated_node_type(successor_pubkey: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_SUCCESSOR_CHAIN_UPDATED_PREFIX,
        hex_prefix(successor_pubkey, 8)
    )
}

/// node_type: `succession_completed:{pk_prefix}` (T3).
pub fn succession_completed_node_type(successor_pubkey: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_SUCCESSION_COMPLETED_PREFIX,
        hex_prefix(successor_pubkey, 8)
    )
}

/// node_type: `cultivation_orphaned:{pk_prefix}` (T4).
pub fn cultivation_orphaned_node_type(prior_cultivator_pubkey: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_CULTIVATION_ORPHANED_PREFIX,
        hex_prefix(prior_cultivator_pubkey, 8)
    )
}

/// node_type: `cultivation_recovered:{pk_prefix}` (T5).
pub fn cultivation_recovered_node_type(successor_pubkey: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_CULTIVATION_RECOVERED_PREFIX,
        hex_prefix(successor_pubkey, 8)
    )
}

/// node_type: `bet_retired:{reason}` (T7 / LB §4).
pub fn bet_retired_node_type(reason: &str) -> String {
    format!("{NODE_TYPE_BET_RETIRED_PREFIX}{reason}")
}

// ---------------------------------------------------------------------------
// Event encoders.
// ---------------------------------------------------------------------------

/// Content of a `successor_chain_updated:{pk}` event (F21 SuccessorEntry append;
/// KEYLESS v0.9 — the owner attestation signature field was removed).
///
/// ```text
/// Map({
///   "successor_pubkey": Bytes(32),
///   "valid_from_unix_ns": Timestamp,
///   "valid_until_unix_ns": Timestamp | Null,  // open-ended when Null
///   "chain_position": Uint,                    // 0-based index in the chain
///   "updated_at_cycle": Uint,
/// })
/// ```
pub fn encode_successor_chain_updated(
    successor_pubkey: &[u8; 32],
    valid_from_unix_ns: i64,
    valid_until_unix_ns: Option<i64>,
    chain_position: u64,
    updated_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
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
    m.insert("chain_position".to_string(), Value::Uint(chain_position));
    m.insert(
        "updated_at_cycle".to_string(),
        Value::Uint(updated_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("successor_chain_updated encode infallible")
}

/// Content of a `succession_completed:{pk}` event (T3; KEYLESS v0.9 — the
/// successor acceptance signature field was removed).
///
/// ```text
/// Map({
///   "successor_pubkey": Bytes(32),
///   "prior_cultivator_pubkey": Bytes(32),
///   "anchor_timestamp_unix_ns": Timestamp,
///   "catechumenate_session_count": Uint,      // ≥50 required (C46 gate)
///   "completed_at_cycle": Uint,
/// })
/// ```
pub fn encode_succession_completed(
    successor_pubkey: &[u8; 32],
    prior_cultivator_pubkey: &[u8; 32],
    anchor_timestamp_unix_ns: i64,
    catechumenate_session_count: u64,
    completed_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
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
    m.insert(
        "catechumenate_session_count".to_string(),
        Value::Uint(catechumenate_session_count),
    );
    m.insert(
        "completed_at_cycle".to_string(),
        Value::Uint(completed_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("succession_completed encode infallible")
}

/// Content of a `cultivation_orphaned:{pk}` event (T4 legacy→orphaned).
///
/// ```text
/// Map({
///   "prior_cultivator_pubkey": Bytes(32),
///   "anchor_timestamp_unix_ns": Timestamp,
///   "reason": String,                        // "legacy_window_elapsed" | "empty_chain_at_legacy"
///   "emitted_at_cycle": Uint,
/// })
/// ```
pub fn encode_cultivation_orphaned(
    prior_cultivator_pubkey: &[u8; 32],
    anchor_timestamp_unix_ns: i64,
    reason: &str,
    emitted_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "prior_cultivator_pubkey".to_string(),
        Value::Bytes(prior_cultivator_pubkey.to_vec()),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(anchor_timestamp_unix_ns),
    );
    m.insert("reason".to_string(), Value::String(reason.to_string()));
    m.insert(
        "emitted_at_cycle".to_string(),
        Value::Uint(emitted_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("cultivation_orphaned encode infallible")
}

/// Content of a `cultivation_recovered:{pk}` event (T5 orphaned→normal).
///
/// ```text
/// Map({
///   "successor_pubkey": Bytes(32),
///   "recovery_proof_reference": String,      // honor-system court-attest ref (AS §6)
///   "anchor_timestamp_unix_ns": Timestamp,
///   "recovered_at_cycle": Uint,
/// })
/// ```
pub fn encode_cultivation_recovered(
    successor_pubkey: &[u8; 32],
    recovery_proof_reference: &str,
    anchor_timestamp_unix_ns: i64,
    recovered_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "successor_pubkey".to_string(),
        Value::Bytes(successor_pubkey.to_vec()),
    );
    m.insert(
        "recovery_proof_reference".to_string(),
        Value::String(recovery_proof_reference.to_string()),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(anchor_timestamp_unix_ns),
    );
    m.insert(
        "recovered_at_cycle".to_string(),
        Value::Uint(recovered_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("cultivation_recovered encode infallible")
}

/// Content of a `bet_retired_proposal` event (LB §4 / T7 precursor).
///
/// ```text
/// Map({
///   "reason": String,                        // "cultivation_orphaned_terminal" | "bet_falsified" | ...
///   "proposed_at_cycle": Uint,
///   "anchor_timestamp_unix_ns": Timestamp,
/// })
/// ```
pub fn encode_bet_retired_proposal(
    reason: &str,
    proposed_at_cycle: u64,
    anchor_timestamp_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("reason".to_string(), Value::String(reason.to_string()));
    m.insert(
        "proposed_at_cycle".to_string(),
        Value::Uint(proposed_at_cycle),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(anchor_timestamp_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("bet_retired_proposal encode infallible")
}

/// Content of a `bet_retired:{reason}` event (T7 orphaned→archived / LB §4 seal;
/// KEYLESS v0.9 — the cultivator co-attestation signature + pubkey were removed).
///
/// ```text
/// Map({
///   "reason": String,
///   "proposal_hash": Bytes(32),              // the bet_retired_proposal this seals
///   "sealed_at_cycle": Uint,
///   "anchor_timestamp_unix_ns": Timestamp,
/// })
/// ```
pub fn encode_bet_retired(
    reason: &str,
    proposal_hash: &[u8; 32],
    sealed_at_cycle: u64,
    anchor_timestamp_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("reason".to_string(), Value::String(reason.to_string()));
    m.insert(
        "proposal_hash".to_string(),
        Value::Bytes(proposal_hash.to_vec()),
    );
    m.insert("sealed_at_cycle".to_string(), Value::Uint(sealed_at_cycle));
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(anchor_timestamp_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("bet_retired encode infallible")
}

/// Content of a `cultivation_succession_config_declared` event.
///
/// All cadence/window values are in **anchor-days** (Uint). The terminal_choice
/// is one of `self_euthanasia` / `bet_retirement` / `indefinite_orphan`
/// (§3.2.C). Re-derived at boot; latest declaration wins.
///
/// ```text
/// Map({
///   "cadence_days": Uint,                    // heartbeat cadence (default 30)
///   "legacy_window_days": Uint,              // normal→orphaned window (default 365)
///   "orphaned_terminal_window_days": Uint,   // orphaned→terminal window (default 730)
///   "terminal_choice": String,               // self_euthanasia | bet_retirement | indefinite_orphan
///   "declared_at_cycle": Uint,
/// })
/// ```
pub fn encode_cultivation_succession_config_declared(
    cadence_days: u64,
    legacy_window_days: u64,
    orphaned_terminal_window_days: u64,
    terminal_choice: &str,
    declared_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("cadence_days".to_string(), Value::Uint(cadence_days));
    m.insert(
        "legacy_window_days".to_string(),
        Value::Uint(legacy_window_days),
    );
    m.insert(
        "orphaned_terminal_window_days".to_string(),
        Value::Uint(orphaned_terminal_window_days),
    );
    m.insert(
        "terminal_choice".to_string(),
        Value::String(terminal_choice.to_string()),
    );
    m.insert(
        "declared_at_cycle".to_string(),
        Value::Uint(declared_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("cultivation_succession_config_declared encode infallible")
}

#[cfg(test)]
mod tests {
    use super::*;
    use myco_kernel_shared::canonical_bytes::{
        decode, map_get_bytes, map_get_string, map_get_uint, Value,
    };

    fn decode_map(cb: &CanonicalBytes) -> BTreeMap<String, Value> {
        match decode(cb.as_ref()).unwrap() {
            Value::Map(m) => m,
            _ => panic!("not a Map"),
        }
    }

    #[test]
    fn node_type_builders_carry_pk_prefix() {
        let pk = [0xABu8; 32];
        assert_eq!(
            successor_chain_updated_node_type(&pk),
            "successor_chain_updated:abababababababab"
        );
        assert_eq!(
            succession_completed_node_type(&pk),
            "succession_completed:abababababababab"
        );
        assert_eq!(
            cultivation_orphaned_node_type(&pk),
            "cultivation_orphaned:abababababababab"
        );
        assert_eq!(
            cultivation_recovered_node_type(&pk),
            "cultivation_recovered:abababababababab"
        );
        assert_eq!(
            bet_retired_node_type("cultivation_orphaned_terminal"),
            "bet_retired:cultivation_orphaned_terminal"
        );
    }

    #[test]
    fn successor_chain_updated_round_trips_open_and_closed_intervals() {
        let pk = [0x66u8; 32];
        // open-ended (valid_until = None → Null)
        let cb_open = encode_successor_chain_updated(&pk, 1000, None, 0, 5);
        let m_open = decode_map(&cb_open);
        assert!(matches!(m_open.get("valid_until_unix_ns"), Some(Value::Null)));
        assert_eq!(map_get_uint(&m_open, "chain_position").unwrap(), 0);
        // closed interval
        let cb_closed = encode_successor_chain_updated(&pk, 1000, Some(2000), 1, 6);
        let m_closed = decode_map(&cb_closed);
        match m_closed.get("valid_until_unix_ns") {
            Some(Value::Timestamp(t)) => assert_eq!(*t, 2000),
            _ => panic!("expected Timestamp"),
        }
    }

    #[test]
    fn succession_completed_round_trips() {
        let succ = [0x88u8; 32];
        let prior = [0x99u8; 32];
        let cb = encode_succession_completed(&succ, &prior, 1234, 50, 9);
        let m = decode_map(&cb);
        assert_eq!(map_get_bytes(&m, "successor_pubkey").unwrap(), &succ[..]);
        assert_eq!(map_get_bytes(&m, "prior_cultivator_pubkey").unwrap(), &prior[..]);
        assert_eq!(map_get_uint(&m, "catechumenate_session_count").unwrap(), 50);
    }

    #[test]
    fn cultivation_orphaned_round_trips() {
        let pk = [0xBBu8; 32];
        let cb = encode_cultivation_orphaned(&pk, 5555, "legacy_window_elapsed", 11);
        let m = decode_map(&cb);
        assert_eq!(
            map_get_string(&m, "reason").unwrap(),
            "legacy_window_elapsed"
        );
        assert_eq!(map_get_uint(&m, "emitted_at_cycle").unwrap(), 11);
    }

    #[test]
    fn cultivation_recovered_round_trips() {
        let pk = [0xCCu8; 32];
        let cb = encode_cultivation_recovered(&pk, "court-ref-2027-001", 7777, 13);
        let m = decode_map(&cb);
        assert_eq!(
            map_get_string(&m, "recovery_proof_reference").unwrap(),
            "court-ref-2027-001"
        );
    }

    #[test]
    fn bet_retired_proposal_and_seal_round_trip() {
        let prop = encode_bet_retired_proposal("cultivation_orphaned_terminal", 100, 8888);
        let m_prop = decode_map(&prop);
        assert_eq!(
            map_get_string(&m_prop, "reason").unwrap(),
            "cultivation_orphaned_terminal"
        );
        let hash = [0xDDu8; 32];
        let seal = encode_bet_retired("cultivation_orphaned_terminal", &hash, 110, 9999);
        let m_seal = decode_map(&seal);
        assert_eq!(map_get_bytes(&m_seal, "proposal_hash").unwrap(), &hash[..]);
        assert_eq!(map_get_uint(&m_seal, "sealed_at_cycle").unwrap(), 110);
    }

    #[test]
    fn succession_config_declared_round_trips() {
        let cb = encode_cultivation_succession_config_declared(
            30, 365, 730, "indefinite_orphan", 1,
        );
        let m = decode_map(&cb);
        assert_eq!(map_get_uint(&m, "cadence_days").unwrap(), 30);
        assert_eq!(map_get_uint(&m, "legacy_window_days").unwrap(), 365);
        assert_eq!(map_get_uint(&m, "orphaned_terminal_window_days").unwrap(), 730);
        assert_eq!(
            map_get_string(&m, "terminal_choice").unwrap(),
            "indefinite_orphan"
        );
    }

    #[test]
    fn determinism_same_inputs_identical_bytes() {
        let succ = [0x01u8; 32];
        let prior = [0x02u8; 32];
        let a = encode_succession_completed(&succ, &prior, 1, 50, 3);
        let b = encode_succession_completed(&succ, &prior, 1, 50, 3);
        assert_eq!(a.as_ref(), b.as_ref());
    }
}
