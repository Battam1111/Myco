//! M21 P5 万物互联 — DerivedState: full substrate state from DAG events.
//!
//! ## Doctrine alignment
//!
//! Per L0/cards/P01-P14 (principles).1 P5 ("Universal Interconnection"): the substrate is a connected
//! graph; orphans are dead tissue. Prior to M21, ~5 substrate state files
//! lived OUTSIDE the DAG — making the corresponding state pieces orphans.
//!
//! M21.1 introduces `DerivedState`, a Rust struct that can be **fully
//! rebuilt** from the DAG event log via `DerivedState::from_dag(&dag)`.
//! Comparing DerivedState against the existing in-memory state surfaces
//! any orphan (state mutation that wasn't accompanied by a DAG event).
//!
//! ## M21.1 scope (Rust-side state only)
//!
//! In-scope:
//! - substrate_id (from genesis_event)
//! - genesis_time_unix_ns
//! - cycle_counter (from cycle_advanced + absorption_event progressions)
//! - last_absorbed_cycle (from absorption_event events)
//! - pinned_operator_identity (from operator_pinned events)
//! - nonce_log (from nonce_issued / consumed / expired events)
//!
//! Deferred to M21.3 (Python autonomy refactor):
//! - gradient configuration (axis schemas + current values)
//! - owner_keys history
//!
//! The deferred items currently live in Python; M21.3 makes Python a
//! view-only consumer of the Rust event stream.
//!
//! ## Determinism contract
//!
//! `DerivedState` impls `PartialEq` and `Eq` so reconciliation is exact-match.
//! All float values are stored as repr-strings inside DAG nodes; replay
//! produces identical bytewise state regardless of platform.

use std::collections::{HashMap, VecDeque};

use myco_kernel_schema::dag::{Dag, DagNode};
use myco_kernel_shared::canonical_bytes::{
    decode as cb_decode, map_get_bytes, map_get_uint, Value,
};

/// M25.2 P5 万物互联 + **M26.2 P11.b**: a single point-in-time observatory
/// snapshot used to build historical signal series for signal #5 (time
/// trends), `bet_weakening_quorum`, the emergent composite weights, and the
/// per-cycle cost signals (#7 compute, #8 network, #9 storage).
///
/// Canonical form (used inside DerivedState's `observatory_history` array):
/// ```text
/// Map({
///   "at_cycle": Uint,
///   "at_unix_ns": Timestamp,
///   "signal_1_dag_node_count": Uint,
///   "signal_1_dag_total_content_bytes": Uint,
///   "signal_2_evolution_event_count": Uint,
///   "signal_3_distinct_perturbed_axes_count": Uint,
///   "signal_4b_reachable_peer_count": Uint,
///   "signal_6_ratio_repr": String,    // empty string if no operator window
///   "signal_7_compute_ns": Uint,      // M26.2 wall-clock ns for this cycle
///   "signal_8_network_bytes": Uint,   // M26.2 federation egress bytes this cycle
///   "signal_9_storage_bytes": Uint,   // M26.2 dag.cb + snapshot.cb delta this cycle
/// })
/// ```
///
/// **Backward compat**: the three M26.2 cost fields are tolerated as absent
/// when parsing pre-M26.2 snapshots (default to 0). Old snapshot.cb files
/// continue to load; only new snapshots carry the cost fields.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObservatorySnapshot {
    /// `manifest.cycle_counter` at snapshot time.
    pub at_cycle: u64,
    /// Wall-clock at snapshot time.
    pub at_unix_ns: i64,
    /// Signal #1: total DAG nodes.
    pub signal_1_dag_node_count: u64,
    /// Signal #1: total DAG content bytes (sum of node `content_canonical_bytes.len`).
    pub signal_1_dag_total_content_bytes: u64,
    /// Signal #2: cumulative count of evolution / schema-change events.
    pub signal_2_evolution_event_count: u64,
    /// Signal #3: distinct axis names that ever appeared in `axis_perturbed:*`.
    pub signal_3_distinct_perturbed_axes_count: u64,
    /// Signal #4b: count of currently-Established federation peers.
    pub signal_4b_reachable_peer_count: u64,
    /// Signal #6: `substrate_total_bytes / operator_context_window_bytes`.
    /// Empty string when no operator context-window attestation has been
    /// supplied recently (substrate cannot derive this autonomously).
    pub signal_6_ratio_repr: String,
    /// **M26.2 P11.b signal #7**: wall-clock nanoseconds spent in the cycle
    /// that produced this snapshot. Measured from previous `cycle_advanced`
    /// to current `cycle_advanced` via `Instant::elapsed`. Substrate-process
    /// wall-clock per L0/cards/P06_eternal_causality + L1/CONTINUITY (time semantics) (M-anchor-3 will promote to anchor-stamped
    /// timing for tamper-evident cost evidence).
    pub signal_7_compute_ns: u64,
    /// **M26.2 P11.b signal #8**: cumulative federation-egress wire bytes
    /// (length prefix + body) since the previous `cycle_advanced`. Drained
    /// from `FederationState::bytes_egressed_since_last_drain` at snapshot time.
    pub signal_8_network_bytes: u64,
    /// **M26.2 P11.b signal #9**: bytes added to `dag.cb` + `snapshot.cb`
    /// on disk since the previous `cycle_advanced`. Computed as
    /// (current_file_sizes - last_recorded_file_sizes) at snapshot time.
    /// Non-negative (file size is monotone within a cycle's perspective).
    pub signal_9_storage_bytes: u64,
    /// **M26.4 P14.c signal**: rolling-window telos_alignment cosine, repr-float
    /// string for cross-language determinism. Range `[-1, +1]` after L2-norm
    /// cosine computation; empty string when no telos signal is computable
    /// (e.g. birth-period, or no sporocarps in window, or no owner objective +
    /// no fallback feedback trajectory). NOT a Living Bet signal — P14.c
    /// telos is orthogonal to L0/cards/LB_living_bets Living Bets (per L1/TROPISM §F.5).
    pub signal_telos_alignment_repr: String,
    /// **v3.1.1 P07** rolling-window count of `internal_mortality_event:*`
    /// DAG events. Per `prune::HOARDING_INDICATOR_WINDOW_CYCLES` window
    /// (default 200 cycles back). Used by L2/OBSERVABILITY §2 (anticipated
    /// metric) as the primary observability surface for the substrate's
    /// internal-mortality discipline. Higher = healthier metabolism.
    /// Default 0 in pre-v3.1.1 snapshots.
    pub signal_internal_mortality_event_density: u64,
    /// **v3.1.1 P07 / L1/HARD_RULES §1.4 C54** hoarding indicator: `true`
    /// iff over the recent window the substrate ingested non-trivially but
    /// emitted < `HOARDING_INDICATOR_MORTALITY_FLOOR` tombstones — i.e.,
    /// P07 §3.1 is not firing despite live ingestion. Default `false`.
    /// Pre-v3.1.1 snapshots default `false`.
    pub signal_hoarding_indicator: bool,
}

/// L1-tunable seed cap for the in-memory observatory history. The substrate
/// trims oldest entries when this is exceeded.
pub const OBSERVATORY_HISTORY_CAP: usize = 90;

impl ObservatorySnapshot {
    /// Encode this snapshot as a canonical-bytes Map. Used by the surrounding
    /// `DerivedState::to_canonical_bytes` to serialize the history array.
    pub fn to_canonical_value(&self) -> Value {
        use std::collections::BTreeMap;
        let mut m = BTreeMap::new();
        m.insert("at_cycle".to_string(), Value::Uint(self.at_cycle));
        m.insert("at_unix_ns".to_string(), Value::Timestamp(self.at_unix_ns));
        m.insert(
            "signal_1_dag_node_count".to_string(),
            Value::Uint(self.signal_1_dag_node_count),
        );
        m.insert(
            "signal_1_dag_total_content_bytes".to_string(),
            Value::Uint(self.signal_1_dag_total_content_bytes),
        );
        m.insert(
            "signal_2_evolution_event_count".to_string(),
            Value::Uint(self.signal_2_evolution_event_count),
        );
        m.insert(
            "signal_3_distinct_perturbed_axes_count".to_string(),
            Value::Uint(self.signal_3_distinct_perturbed_axes_count),
        );
        m.insert(
            "signal_4b_reachable_peer_count".to_string(),
            Value::Uint(self.signal_4b_reachable_peer_count),
        );
        m.insert(
            "signal_6_ratio_repr".to_string(),
            Value::String(self.signal_6_ratio_repr.clone()),
        );
        // M26.2 P11.b cost signals. Always emitted from M26.2 onward (default
        // 0 means "no cost recorded for this cycle"). Pre-M26.2 readers
        // tolerate these as unknown via the backward-compat parsing below.
        m.insert(
            "signal_7_compute_ns".to_string(),
            Value::Uint(self.signal_7_compute_ns),
        );
        m.insert(
            "signal_8_network_bytes".to_string(),
            Value::Uint(self.signal_8_network_bytes),
        );
        m.insert(
            "signal_9_storage_bytes".to_string(),
            Value::Uint(self.signal_9_storage_bytes),
        );
        // M26.4 P14.c telos_alignment — empty string when not computable.
        m.insert(
            "signal_telos_alignment_repr".to_string(),
            Value::String(self.signal_telos_alignment_repr.clone()),
        );
        // v3.1.1 P07 internal-mortality observability (L2/OBSERVABILITY §2
        // anticipated metrics). Backward-compat: pre-v3.1.1 snapshots
        // tolerated as absent → default 0/false on read.
        m.insert(
            "signal_internal_mortality_event_density".to_string(),
            Value::Uint(self.signal_internal_mortality_event_density),
        );
        m.insert(
            "signal_hoarding_indicator".to_string(),
            Value::Bool(self.signal_hoarding_indicator),
        );
        Value::Map(m)
    }

    /// Decode a single snapshot Map. Returns an EventDecode error if the
    /// shape is wrong.
    pub fn from_canonical_value(v: &Value) -> Result<Self, DerivedStateError> {
        let m = match v {
            Value::Map(m) => m,
            other => {
                return Err(DerivedStateError::EventDecode {
                    node_type: "observatory_snapshot".to_string(),
                    reason: format!("not a Map: {other:?}"),
                })
            }
        };
        let read_uint = |k: &str| -> Result<u64, DerivedStateError> {
            map_get_uint(m, k).map_err(|e| DerivedStateError::EventField {
                node_type: "observatory_snapshot".to_string(),
                field: k.to_string(),
                reason: e.to_string(),
            })
        };
        let at_cycle = read_uint("at_cycle")?;
        let at_unix_ns = match m.get("at_unix_ns") {
            Some(Value::Timestamp(t)) => *t,
            _ => {
                return Err(DerivedStateError::EventField {
                    node_type: "observatory_snapshot".to_string(),
                    field: "at_unix_ns".to_string(),
                    reason: "missing or not Timestamp".to_string(),
                })
            }
        };
        let signal_1_dag_node_count = read_uint("signal_1_dag_node_count")?;
        let signal_1_dag_total_content_bytes = read_uint("signal_1_dag_total_content_bytes")?;
        let signal_2_evolution_event_count = read_uint("signal_2_evolution_event_count")?;
        let signal_3_distinct_perturbed_axes_count =
            read_uint("signal_3_distinct_perturbed_axes_count")?;
        let signal_4b_reachable_peer_count = read_uint("signal_4b_reachable_peer_count")?;
        let signal_6_ratio_repr = match m.get("signal_6_ratio_repr") {
            Some(Value::String(s)) => s.clone(),
            // tolerate absent for forward-compat
            _ => String::new(),
        };
        // M26.2 cost signals — tolerate absent for backward-compat with
        // pre-M26.2 snapshot.cb files (default to 0 = "no cost recorded").
        let signal_7_compute_ns = match m.get("signal_7_compute_ns") {
            Some(Value::Uint(n)) => *n,
            _ => 0,
        };
        let signal_8_network_bytes = match m.get("signal_8_network_bytes") {
            Some(Value::Uint(n)) => *n,
            _ => 0,
        };
        let signal_9_storage_bytes = match m.get("signal_9_storage_bytes") {
            Some(Value::Uint(n)) => *n,
            _ => 0,
        };
        // M26.4 P14.c telos_alignment — tolerate absent for backward-compat
        // with pre-M26.4 snapshot.cb files.
        let signal_telos_alignment_repr = match m.get("signal_telos_alignment_repr") {
            Some(Value::String(s)) => s.clone(),
            _ => String::new(),
        };
        // v3.1.1 P07 internal-mortality observability — tolerate absent for
        // backward-compat with pre-v3.1.1 snapshot.cb files (default 0/false).
        let signal_internal_mortality_event_density =
            match m.get("signal_internal_mortality_event_density") {
                Some(Value::Uint(n)) => *n,
                _ => 0,
            };
        let signal_hoarding_indicator = match m.get("signal_hoarding_indicator") {
            Some(Value::Bool(b)) => *b,
            _ => false,
        };
        Ok(ObservatorySnapshot {
            at_cycle,
            at_unix_ns,
            signal_1_dag_node_count,
            signal_1_dag_total_content_bytes,
            signal_2_evolution_event_count,
            signal_3_distinct_perturbed_axes_count,
            signal_4b_reachable_peer_count,
            signal_6_ratio_repr,
            signal_7_compute_ns,
            signal_8_network_bytes,
            signal_9_storage_bytes,
            signal_telos_alignment_repr,
            signal_internal_mortality_event_density,
            signal_hoarding_indicator,
        })
    }
}

use crate::events::{
    NODE_TYPE_CYCLE_ADVANCED, NODE_TYPE_GENESIS_PREFIX, NODE_TYPE_NONCE_CONSUMED_PREFIX,
    NODE_TYPE_NONCE_EXPIRED_PREFIX, NODE_TYPE_NONCE_ISSUED_PREFIX,
    NODE_TYPE_OPERATOR_PINNED_PREFIX, NODE_TYPE_SCHEMA_MIGRATION_COMMITTED_PREFIX,
    NODE_TYPE_SCHEMA_MIGRATION_ROLLED_BACK_PREFIX, NODE_TYPE_SCHEMA_MIGRATION_STARTED_PREFIX,
};
use crate::persistence::PinnedOperatorIdentity;

/// One persisted attestation nonce as derivable from DAG events. Mirrors the
/// in-memory `AttestationNonce` in `server.rs`; M21.2+ may consolidate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DerivedNonce {
    /// 32-byte nonce.
    pub nonce: [u8; 32],
    /// Hash of content the operator intends to submit.
    pub bound_content_hash: [u8; 32],
    /// DAG tip at issuance.
    pub bound_dag_tip: [u8; 32],
    /// Substrate-clock issuance time.
    pub substrate_issued_at_unix_ns: i64,
    /// Substrate-clock expiry.
    pub expiry_unix_ns: i64,
    /// Operator-supplied anchor-clock issuance time (M15 optional).
    pub anchor_clock_issued_at_unix_ns: Option<i64>,
    /// Anchor-clock expiry (M15 optional, paired with above).
    pub anchor_clock_expiry_unix_ns: Option<i64>,
    /// Whether this nonce has been consumed.
    pub consumed: bool,
}

/// **v3.1.1 Sprint 8.G** — an in-flight schema migration candidate, as
/// derivable from DAG events + persisted in snapshot.cb.
///
/// Mirrors the relevant fields of `myco_kernel_schema::migration::CandidateState`
/// (the phase is always `Validating` while one of these exists; commit /
/// rollback clear it). It carries everything the substrate needs to resume a
/// migration across a restart: which op, the diff bytes, the window, and when
/// validation began.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DerivedMigrationCandidate {
    /// Operator-visible op name (`modify_axis_threshold`, etc.).
    pub op_name: String,
    /// The schema_diff being applied, as canonical bytes.
    pub schema_diff_canonical_bytes: Vec<u8>,
    /// Cycle at which the dual-validation window opened.
    pub started_at_cycle: u64,
    /// Number of cycles the candidate must validate before commit.
    pub dual_validation_window_cycles: u64,
    /// Wall-clock at migration start (informational).
    pub started_at_unix_ns: i64,
}

/// **COV06 §3.2.A (F21)** — one entry of the cultivation_successor_chain, as
/// derived from a `successor_chain_updated:{pk}` DAG event.
///
/// Mirrors the L1/GOVERNANCE §3.2.A `SuccessorEntry` shape. The chain is
/// **re-derived from the DAG at boot** (NOT persisted in snapshot.cb), so the
/// snapshot format_version + bytes are unchanged by COV06. Non-overlapping
/// intervals with monotone `valid_from` are validated at the skin
/// (`handle_update_successor_chain`); the derivation here is append-only.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DerivedSuccessorEntry {
    /// 32-byte successor cultivator pubkey.
    pub successor_pubkey: [u8; 32],
    /// Anchor wall-clock from which this successor is valid.
    pub valid_from_unix_ns: i64,
    /// Anchor wall-clock until which this successor is valid; `None` =
    /// open-ended (chain head).
    pub valid_until_unix_ns: Option<i64>,
    /// 64-byte chain-head / cultivator attestation signature.
    pub attestation_signature: [u8; 64],
}

/// **COV06 §3.2.C** — the cultivation cadence + windows + terminal choice, as
/// derived from the latest `cultivation_succession_config_declared` DAG event.
/// All durations are in **anchor-days**. `None` for the whole struct → built-in
/// defaults are used (cadence 30d, legacy 365d, terminal 730d, choice
/// `indefinite_orphan`). Re-derived at boot from the DAG; not persisted in
/// snapshot.cb (latest declaration wins on replay).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DerivedSuccessionConfig {
    /// Heartbeat cadence in anchor-days (default 30).
    pub cadence_days: u64,
    /// normal→orphaned legacy window in anchor-days (default 365).
    pub legacy_window_days: u64,
    /// orphaned→terminal window in anchor-days (default 730).
    pub orphaned_terminal_window_days: u64,
    /// `self_euthanasia` | `bet_retirement` | `indefinite_orphan`.
    pub terminal_choice: String,
}

/// **COV06** — the latest recorded cultivator heartbeat, as derived from the
/// most recent `cultivator_heartbeat_recorded` / `cultivator_heartbeat_resumed`
/// DAG event. The autonomous-tick staleness watchdog measures
/// `now_anchor - anchor_timestamp_unix_ns` against the cadence. Re-derived at
/// boot from the DAG; not persisted in snapshot.cb.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DerivedLatestHeartbeat {
    /// 32-byte cultivator pubkey of the most recent heartbeat.
    pub cultivator_pubkey: [u8; 32],
    /// Anchor wall-clock of the most recent heartbeat pulse.
    pub anchor_timestamp_unix_ns: i64,
}

/// Error during DAG event replay.
#[derive(Debug, thiserror::Error)]
#[non_exhaustive]
pub enum DerivedStateError {
    /// A DAG node's content failed to decode as canonical bytes.
    #[error("event content decode failed for node_type={node_type}: {reason}")]
    EventDecode {
        /// The DAG node's node_type.
        node_type: String,
        /// Underlying decode error.
        reason: String,
    },
    /// A required field was missing or wrong-typed.
    #[error("event field error for node_type={node_type}: {field}: {reason}")]
    EventField {
        /// The DAG node's node_type.
        node_type: String,
        /// Which field.
        field: String,
        /// What went wrong.
        reason: String,
    },
    /// genesis_event seen more than once. The substrate has at most one.
    #[error("genesis_event seen multiple times in DAG")]
    MultipleGenesis,
    /// nonce_consumed/expired references a nonce never issued.
    #[error("nonce event references unknown nonce: prefix={prefix}")]
    NonceUnknown {
        /// First 16 hex chars of the nonce.
        prefix: String,
    },
}

/// Full substrate state derivable from DAG event log.
///
/// Boot path (post-M21.2): `DerivedState::from_dag(&dag)` produces the
/// authoritative state. The state-file-based boot path (M5-M20) is fallback.
///
/// Dual-write path (M21.1): existing ServerState fields remain authoritative;
/// DerivedState is computed for C19 reconciliation only.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DerivedState {
    /// 32-byte substrate identifier. `None` until the genesis_event is seen.
    pub substrate_id: Option<[u8; 32]>,
    /// Wall-clock time at substrate genesis.
    pub genesis_time_unix_ns: Option<i64>,
    /// **8f / L1/GOVERNANCE §16.A (F22)**: this substrate's lineage depth,
    /// read from the `generation_depth` field of its `genesis_event` (absent
    /// → 0 = root). Seeded into `ServerState.generation_depth` by the DAG-first
    /// boot arm (Task #8i) so the C47 reproduction detector can enforce
    /// `reproduction_lineage_depth_max` at sprout time.
    pub generation_depth: u64,
    /// Authoritative metabolic-cycle counter.
    pub cycle_counter: u64,
    /// Highest cycle whose raw_material has been absorbed (M18).
    pub last_absorbed_cycle: Option<u64>,
    /// Pinned operator IDENTITY pubkey (M9 TOFU). `None` until first operator_pinned event.
    pub pinned_operator_identity: Option<PinnedOperatorIdentity>,
    /// Live nonce log: derived from nonce_issued events, with nonce_consumed /
    /// nonce_expired events updating per-entry `consumed` flag or removing.
    pub nonce_log: HashMap<[u8; 32], DerivedNonce>,
    /// M25.2 P5 万物互联: rolling history of per-cycle observatory snapshots.
    /// Populated by the live server on every `cycle_advanced` emission. The
    /// snapshot.cb persistence layer round-trips this so the trend window
    /// survives reboots; pure DAG-replay boots start with an empty history
    /// (filled organically over subsequent cycles).
    ///
    /// Capped at `OBSERVATORY_HISTORY_CAP` (90); oldest dropped on overflow.
    pub observatory_history: VecDeque<ObservatorySnapshot>,
    /// **v3.1.1 Sprint 8.G (P03 §10.4)**: the single in-flight schema
    /// migration candidate, if any. `Some` between a
    /// `schema_migration_started:*` event and its terminal
    /// `schema_migration_committed:*` / `schema_migration_rolled_back:*`
    /// event. `None` otherwise (the common case — migrations are rare + the
    /// MVP allows only ONE in flight at a time). Snapshot.cb round-trips this
    /// so a substrate restarted mid-window resumes the migration; pre-Sprint-8.G
    /// snapshots that lack the field decode to `None` (back-compat).
    pub migration_candidate: Option<DerivedMigrationCandidate>,
    /// **COV06 §3.2.A (F21)** — the cultivation_successor_chain, derived from
    /// `successor_chain_updated:{pk}` DAG events in insertion order. **NOT
    /// persisted in snapshot.cb** — re-derived from the DAG at boot, so the
    /// snapshot format_version + bytes are unchanged (byte-compat additive).
    pub successor_chain: Vec<DerivedSuccessorEntry>,
    /// **COV06 §3.2.C** — the active succession config (cadence + windows +
    /// terminal choice), from the latest `cultivation_succession_config_declared`
    /// event. `None` → built-in defaults. NOT persisted in snapshot.cb.
    pub succession_config: Option<DerivedSuccessionConfig>,
    /// **COV06** — the latest recorded cultivator heartbeat (the staleness
    /// watchdog's reference point). `None` → no heartbeat ever recorded. NOT
    /// persisted in snapshot.cb (re-derived from the DAG at boot).
    pub latest_heartbeat: Option<DerivedLatestHeartbeat>,
}

impl DerivedState {
    /// Empty initial state — corresponds to pre-genesis substrate.
    pub fn empty() -> Self {
        DerivedState {
            substrate_id: None,
            genesis_time_unix_ns: None,
            generation_depth: 0,
            cycle_counter: 0,
            last_absorbed_cycle: None,
            pinned_operator_identity: None,
            nonce_log: HashMap::new(),
            observatory_history: VecDeque::new(),
            migration_candidate: None,
            successor_chain: Vec::new(),
            succession_config: None,
            latest_heartbeat: None,
        }
    }

    /// M21.2: True iff this DerivedState contains a `genesis_event` (i.e., the
    /// DAG event log was constructed on a post-M21.1 substrate that emitted
    /// the genesis_event). This is the signal that DAG is the authoritative
    /// source — boot path uses derived state instead of legacy state files.
    pub fn is_post_m21_substrate(&self) -> bool {
        self.substrate_id.is_some()
    }

    /// M21.5 P5 万物互联: encode the snapshot as canonical bytes.
    /// Stored alongside `dag.cb` as `snapshot.cb` to accelerate boot —
    /// avoids full DAG replay every restart on large substrates.
    ///
    /// Schema (canonical-bytes Map):
    /// ```text
    /// Map({
    ///   "format_version": Uint(2),         // 8.G: bumped v1→v2 for migration_candidate
    ///   "snapshot_at_dag_tip": Bytes(32),  // optional; absent for empty DAG
    ///   "substrate_id": Bytes(32),         // optional; absent until genesis_event
    ///   "genesis_time_unix_ns": Timestamp, // optional
    ///   "cycle_counter": Uint,
    ///   "last_absorbed_cycle": Uint,       // optional
    ///   "pinned_operator_identity": Map,   // optional
    ///   "nonce_log": Array<Map>,
    ///   "observatory_history": Array<Map>, // optional; absent in pre-M25.2 snapshots
    ///   "migration_candidate": Map,        // optional; absent when no migration in flight
    /// })
    /// ```
    ///
    /// **8.G back-compat**: `format_version` bumped 1→2 to carry the optional
    /// `migration_candidate` field. The decoder accepts BOTH v1 and v2 (a v1
    /// snapshot simply lacks the field → `migration_candidate = None`), so old
    /// snapshot.cb files continue to load unchanged.
    pub fn to_canonical_bytes(
        &self,
        snapshot_at_dag_tip: Option<&[u8; 32]>,
    ) -> myco_kernel_shared::canonical_bytes::CanonicalBytes {
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        use std::collections::BTreeMap;

        let mut root = BTreeMap::new();
        root.insert("format_version".to_string(), Value::Uint(2));
        if let Some(tip) = snapshot_at_dag_tip {
            root.insert(
                "snapshot_at_dag_tip".to_string(),
                Value::Bytes(tip.to_vec()),
            );
        }
        if let Some(id) = &self.substrate_id {
            root.insert("substrate_id".to_string(), Value::Bytes(id.to_vec()));
        }
        if let Some(t) = self.genesis_time_unix_ns {
            root.insert("genesis_time_unix_ns".to_string(), Value::Timestamp(t));
        }
        // 8f / §16.A: persist lineage depth in snapshot.cb so a snapshot-
        // accelerated boot (which may skip replaying the genesis_event)
        // still recovers the substrate's depth. Emitted only when non-zero
        // for back-compat with pre-8f snapshot decoders (absent → 0).
        if self.generation_depth != 0 {
            root.insert(
                "generation_depth".to_string(),
                Value::Uint(self.generation_depth),
            );
        }
        root.insert("cycle_counter".to_string(), Value::Uint(self.cycle_counter));
        if let Some(c) = self.last_absorbed_cycle {
            root.insert("last_absorbed_cycle".to_string(), Value::Uint(c));
        }
        if let Some(pinned) = &self.pinned_operator_identity {
            let mut pm = BTreeMap::new();
            pm.insert("pubkey".to_string(), Value::Bytes(pinned.pubkey.to_vec()));
            pm.insert(
                "first_pinned_unix_ns".to_string(),
                Value::Timestamp(pinned.first_pinned_unix_ns),
            );
            root.insert("pinned_operator_identity".to_string(), Value::Map(pm));
        }
        let nonces: Vec<Value> = self
            .nonce_log
            .values()
            .map(|n| {
                let mut nm = BTreeMap::new();
                nm.insert("nonce".to_string(), Value::Bytes(n.nonce.to_vec()));
                nm.insert(
                    "bound_content_hash".to_string(),
                    Value::Bytes(n.bound_content_hash.to_vec()),
                );
                nm.insert(
                    "bound_dag_tip".to_string(),
                    Value::Bytes(n.bound_dag_tip.to_vec()),
                );
                nm.insert(
                    "substrate_issued_at_unix_ns".to_string(),
                    Value::Timestamp(n.substrate_issued_at_unix_ns),
                );
                nm.insert(
                    "expiry_unix_ns".to_string(),
                    Value::Timestamp(n.expiry_unix_ns),
                );
                if let Some(t) = n.anchor_clock_issued_at_unix_ns {
                    nm.insert(
                        "anchor_clock_issued_at_unix_ns".to_string(),
                        Value::Timestamp(t),
                    );
                }
                if let Some(t) = n.anchor_clock_expiry_unix_ns {
                    nm.insert(
                        "anchor_clock_expiry_unix_ns".to_string(),
                        Value::Timestamp(t),
                    );
                }
                nm.insert("consumed".to_string(), Value::Bool(n.consumed));
                Value::Map(nm)
            })
            .collect();
        root.insert("nonce_log".to_string(), Value::Array(nonces));

        // M25.2: persist the observatory history. Omitted entirely when
        // empty (back-compat with pre-M25.2 snapshot decoders).
        if !self.observatory_history.is_empty() {
            let snapshots: Vec<Value> = self
                .observatory_history
                .iter()
                .map(|s| s.to_canonical_value())
                .collect();
            root.insert("observatory_history".to_string(), Value::Array(snapshots));
        }

        // 8.G: persist the in-flight migration candidate. Omitted entirely
        // when None (the common case) — so a substrate that never opts into
        // migration produces a snapshot byte-identical (modulo format_version)
        // to the pre-8.G encoding for this field.
        if let Some(mc) = &self.migration_candidate {
            let mut mcm = BTreeMap::new();
            mcm.insert("op_name".to_string(), Value::String(mc.op_name.clone()));
            mcm.insert(
                "schema_diff_canonical_bytes".to_string(),
                Value::Bytes(mc.schema_diff_canonical_bytes.clone()),
            );
            mcm.insert(
                "started_at_cycle".to_string(),
                Value::Uint(mc.started_at_cycle),
            );
            mcm.insert(
                "dual_validation_window_cycles".to_string(),
                Value::Uint(mc.dual_validation_window_cycles),
            );
            mcm.insert(
                "started_at_unix_ns".to_string(),
                Value::Timestamp(mc.started_at_unix_ns),
            );
            root.insert("migration_candidate".to_string(), Value::Map(mcm));
        }

        encode(&Value::Map(root)).expect("snapshot encode infallible")
    }

    /// M21.5: decode a snapshot from canonical bytes, returning (state, snapshot_at_dag_tip).
    /// Returns `None` on format version mismatch (caller falls back to full DAG replay).
    #[allow(clippy::type_complexity)]
    pub fn from_canonical_bytes(
        bytes: &[u8],
    ) -> Result<Option<(Self, Option<[u8; 32]>)>, DerivedStateError> {
        use myco_kernel_shared::canonical_bytes::{
            decode, map_get_array, map_get_bytes, map_get_string, map_get_uint, Value,
        };
        let decoded = decode(bytes).map_err(|e| DerivedStateError::EventDecode {
            node_type: "snapshot.cb".to_string(),
            reason: format!("decode: {e}"),
        })?;
        let map = match decoded {
            Value::Map(m) => m,
            other => {
                return Err(DerivedStateError::EventDecode {
                    node_type: "snapshot.cb".to_string(),
                    reason: format!("root not Map: {other:?}"),
                })
            }
        };
        let version =
            map_get_uint(&map, "format_version").map_err(|e| DerivedStateError::EventField {
                node_type: "snapshot.cb".to_string(),
                field: "format_version".to_string(),
                reason: e.to_string(),
            })?;
        // 8.G: accept v1 (pre-migration) AND v2 (carries migration_candidate).
        // A v1 snapshot simply lacks migration_candidate → None. Any other
        // version is unknown → caller falls back to full DAG replay.
        if version != 1 && version != 2 {
            return Ok(None); // unknown version → caller falls back
        }
        let snapshot_at_dag_tip = match map.get("snapshot_at_dag_tip") {
            Some(Value::Bytes(b)) if b.len() == 32 => {
                let mut arr = [0u8; 32];
                arr.copy_from_slice(b);
                Some(arr)
            }
            _ => None,
        };
        let substrate_id = match map.get("substrate_id") {
            Some(Value::Bytes(b)) if b.len() == 32 => {
                let mut arr = [0u8; 32];
                arr.copy_from_slice(b);
                Some(arr)
            }
            _ => None,
        };
        let genesis_time_unix_ns = match map.get("genesis_time_unix_ns") {
            Some(Value::Timestamp(t)) => Some(*t),
            _ => None,
        };
        // 8f / §16.A: optional in snapshot.cb — absent in pre-8f snapshots and
        // in every root substrate → 0 (root lineage depth).
        let generation_depth = match map.get("generation_depth") {
            Some(Value::Uint(n)) => *n,
            _ => 0,
        };
        let cycle_counter =
            map_get_uint(&map, "cycle_counter").map_err(|e| DerivedStateError::EventField {
                node_type: "snapshot.cb".to_string(),
                field: "cycle_counter".to_string(),
                reason: e.to_string(),
            })?;
        let last_absorbed_cycle = match map.get("last_absorbed_cycle") {
            Some(Value::Uint(u)) => Some(*u),
            _ => None,
        };
        let pinned_operator_identity = match map.get("pinned_operator_identity") {
            Some(Value::Map(pm)) => {
                let pk =
                    map_get_bytes(pm, "pubkey").map_err(|e| DerivedStateError::EventField {
                        node_type: "snapshot.cb".to_string(),
                        field: "pinned_operator_identity.pubkey".to_string(),
                        reason: e.to_string(),
                    })?;
                if pk.len() != 32 {
                    return Err(DerivedStateError::EventField {
                        node_type: "snapshot.cb".to_string(),
                        field: "pubkey".to_string(),
                        reason: format!("expected 32 bytes; got {}", pk.len()),
                    });
                }
                let mut pubkey = [0u8; 32];
                pubkey.copy_from_slice(pk);
                let first_pinned_unix_ns = match pm.get("first_pinned_unix_ns") {
                    Some(Value::Timestamp(t)) => *t,
                    _ => 0,
                };
                Some(crate::persistence::PinnedOperatorIdentity {
                    pubkey,
                    first_pinned_unix_ns,
                })
            }
            _ => None,
        };
        let nonce_log_array =
            map_get_array(&map, "nonce_log").map_err(|e| DerivedStateError::EventField {
                node_type: "snapshot.cb".to_string(),
                field: "nonce_log".to_string(),
                reason: e.to_string(),
            })?;
        let mut nonce_log = HashMap::new();
        for v in nonce_log_array {
            let nm = match v {
                Value::Map(m) => m,
                other => {
                    return Err(DerivedStateError::EventField {
                        node_type: "snapshot.cb".to_string(),
                        field: "nonce_log_entry".to_string(),
                        reason: format!("not a Map: {other:?}"),
                    })
                }
            };
            let read_32 = |field: &str| -> Result<[u8; 32], DerivedStateError> {
                let b = map_get_bytes(nm, field).map_err(|e| DerivedStateError::EventField {
                    node_type: "snapshot.cb".to_string(),
                    field: field.to_string(),
                    reason: e.to_string(),
                })?;
                if b.len() != 32 {
                    return Err(DerivedStateError::EventField {
                        node_type: "snapshot.cb".to_string(),
                        field: field.to_string(),
                        reason: format!("not 32 bytes: {}", b.len()),
                    });
                }
                let mut arr = [0u8; 32];
                arr.copy_from_slice(b);
                Ok(arr)
            };
            let nonce = read_32("nonce")?;
            let bound_content_hash = read_32("bound_content_hash")?;
            let bound_dag_tip = read_32("bound_dag_tip")?;
            let substrate_issued_at_unix_ns = match nm.get("substrate_issued_at_unix_ns") {
                Some(Value::Timestamp(t)) => *t,
                _ => 0,
            };
            let expiry_unix_ns = match nm.get("expiry_unix_ns") {
                Some(Value::Timestamp(t)) => *t,
                _ => 0,
            };
            let anchor_clock_issued_at_unix_ns = match nm.get("anchor_clock_issued_at_unix_ns") {
                Some(Value::Timestamp(t)) => Some(*t),
                _ => None,
            };
            let anchor_clock_expiry_unix_ns = match nm.get("anchor_clock_expiry_unix_ns") {
                Some(Value::Timestamp(t)) => Some(*t),
                _ => None,
            };
            let consumed = match nm.get("consumed") {
                Some(Value::Bool(b)) => *b,
                _ => false,
            };
            nonce_log.insert(
                nonce,
                DerivedNonce {
                    nonce,
                    bound_content_hash,
                    bound_dag_tip,
                    substrate_issued_at_unix_ns,
                    expiry_unix_ns,
                    anchor_clock_issued_at_unix_ns,
                    anchor_clock_expiry_unix_ns,
                    consumed,
                },
            );
        }
        // M25.2: optional observatory_history. Absent → empty.
        let observatory_history: VecDeque<ObservatorySnapshot> = match map.get("observatory_history")
        {
            Some(Value::Array(arr)) => {
                let mut hist = VecDeque::with_capacity(arr.len());
                for v in arr {
                    hist.push_back(ObservatorySnapshot::from_canonical_value(v)?);
                }
                hist
            }
            _ => VecDeque::new(),
        };

        // 8.G: optional migration_candidate (v2+). Absent (v1 or no migration
        // in flight) → None. A malformed candidate Map is a hard error so a
        // corrupt snapshot surfaces rather than silently dropping an in-flight
        // migration; the boot path treats a Err here as "fall back to DAG
        // replay" which re-derives the candidate from the started/terminal
        // events anyway.
        let migration_candidate: Option<DerivedMigrationCandidate> =
            match map.get("migration_candidate") {
                Some(Value::Map(mcm)) => {
                    let op_name = map_get_string(mcm, "op_name")
                        .map_err(|e| DerivedStateError::EventField {
                            node_type: "snapshot.cb".to_string(),
                            field: "migration_candidate.op_name".to_string(),
                            reason: e.to_string(),
                        })?
                        .to_string();
                    let schema_diff_canonical_bytes = match mcm.get("schema_diff_canonical_bytes") {
                        Some(Value::Bytes(b)) => b.clone(),
                        _ => {
                            return Err(DerivedStateError::EventField {
                                node_type: "snapshot.cb".to_string(),
                                field: "migration_candidate.schema_diff_canonical_bytes".to_string(),
                                reason: "missing or not Bytes".to_string(),
                            })
                        }
                    };
                    let started_at_cycle = map_get_uint(mcm, "started_at_cycle").map_err(|e| {
                        DerivedStateError::EventField {
                            node_type: "snapshot.cb".to_string(),
                            field: "migration_candidate.started_at_cycle".to_string(),
                            reason: e.to_string(),
                        }
                    })?;
                    let dual_validation_window_cycles =
                        map_get_uint(mcm, "dual_validation_window_cycles").map_err(|e| {
                            DerivedStateError::EventField {
                                node_type: "snapshot.cb".to_string(),
                                field: "migration_candidate.dual_validation_window_cycles"
                                    .to_string(),
                                reason: e.to_string(),
                            }
                        })?;
                    let started_at_unix_ns = match mcm.get("started_at_unix_ns") {
                        Some(Value::Timestamp(t)) => *t,
                        _ => 0,
                    };
                    Some(DerivedMigrationCandidate {
                        op_name,
                        schema_diff_canonical_bytes,
                        started_at_cycle,
                        dual_validation_window_cycles,
                        started_at_unix_ns,
                    })
                }
                _ => None,
            };

        Ok(Some((
            DerivedState {
                substrate_id,
                genesis_time_unix_ns,
                generation_depth,
                cycle_counter,
                last_absorbed_cycle,
                pinned_operator_identity,
                nonce_log,
                observatory_history,
                migration_candidate,
                // **COV06**: these three are NOT persisted in snapshot.cb (no
                // format bump). The boot path re-derives them from the full DAG
                // after snapshot load (see `rederive_cultivation_from_dag`), so
                // a snapshot-accelerated boot recovers the cultivation state
                // even for events that predate the snapshot tip.
                successor_chain: Vec::new(),
                succession_config: None,
                latest_heartbeat: None,
            },
            snapshot_at_dag_tip,
        )))
    }

    /// **COV06** — re-derive the cultivation FSM state (successor_chain +
    /// succession_config + latest_heartbeat) from a full DAG walk, overwriting
    /// whatever the tail-replay / snapshot path produced. These three fields are
    /// deliberately NOT persisted in snapshot.cb (additive byte-compat: no
    /// format_version bump), so a snapshot-accelerated boot — which replays only
    /// the tail after the snapshot tip — would otherwise miss cultivation events
    /// older than the snapshot. This pass restores them authoritatively. The
    /// cultivation event family is tiny (heartbeats + chain updates + one config),
    /// so the full walk is cheap. Called from the boot path after `derived` is
    /// materialized.
    pub fn rederive_cultivation_from_dag(
        &mut self,
        dag: &myco_kernel_schema::dag::Dag,
    ) -> Result<(), DerivedStateError> {
        self.successor_chain.clear();
        self.succession_config = None;
        self.latest_heartbeat = None;
        for node in dag.iter_in_insertion_order() {
            let nt = &node.node_type;
            if nt == crate::events::NODE_TYPE_CULTIVATOR_HEARTBEAT_RECORDED
                || nt == crate::events::NODE_TYPE_CULTIVATOR_HEARTBEAT_RESUMED
            {
                self.apply_cultivator_heartbeat(node)?;
            } else if nt.starts_with(crate::events::NODE_TYPE_SUCCESSOR_CHAIN_UPDATED_PREFIX) {
                self.apply_successor_chain_updated(node)?;
            } else if nt == crate::events::NODE_TYPE_CULTIVATION_SUCCESSION_CONFIG_DECLARED {
                self.apply_succession_config_declared(node)?;
            }
        }
        Ok(())
    }

    // **Task #8i**: `to_legacy_manifest` removed. The DAG-first boot arm now
    // seeds `ServerState`'s discrete identity / metabolic-position fields
    // straight from these `DerivedState` fields (substrate_id / genesis_time
    // are already `Option`), and the `ServerState` accessors reproduce the old
    // sentinel mapping (`None` → `[0u8;32]` / `0`). There is no longer an
    // intermediate `Manifest` materialized at boot from the DAG.

    /// Rebuild full state by replaying every DAG node in insertion order.
    ///
    /// On any malformed event, returns `Err`. Successful replay produces a
    /// state that, by determinism contract, exactly equals the substrate's
    /// in-memory state at the time the DAG snapshot was taken.
    pub fn from_dag(dag: &Dag) -> Result<Self, DerivedStateError> {
        let mut state = Self::empty();
        for node in dag.iter_in_insertion_order() {
            state.apply_event(node)?;
        }
        Ok(state)
    }

    /// Apply a single DAG node event to the state. Pure function of
    /// (current_state, event); idempotent for ignore-type events.
    pub fn apply_event(&mut self, node: &DagNode) -> Result<(), DerivedStateError> {
        let nt = &node.node_type;
        if nt.starts_with(NODE_TYPE_GENESIS_PREFIX) {
            self.apply_genesis(node)
        } else if nt == NODE_TYPE_CYCLE_ADVANCED {
            self.apply_cycle_advanced(node)
        } else if nt.starts_with(NODE_TYPE_OPERATOR_PINNED_PREFIX) {
            self.apply_operator_pinned(node)
        } else if nt.starts_with(NODE_TYPE_NONCE_ISSUED_PREFIX) {
            self.apply_nonce_issued(node)
        } else if nt.starts_with(NODE_TYPE_NONCE_CONSUMED_PREFIX) {
            self.apply_nonce_consumed(node)
        } else if nt.starts_with(NODE_TYPE_NONCE_EXPIRED_PREFIX) {
            self.apply_nonce_expired(node)
        } else if nt.starts_with("absorption_event:cycle_") {
            self.apply_absorption_event(node)
        } else if nt.starts_with(NODE_TYPE_SCHEMA_MIGRATION_STARTED_PREFIX) {
            self.apply_schema_migration_started(node)
        } else if nt.starts_with(NODE_TYPE_SCHEMA_MIGRATION_COMMITTED_PREFIX)
            || nt.starts_with(NODE_TYPE_SCHEMA_MIGRATION_ROLLED_BACK_PREFIX)
        {
            // Terminal migration events clear the in-flight candidate. Both
            // commit and rollback end the migration; the schema outcome
            // (promoted vs dropped) is the Python side's concern.
            self.migration_candidate = None;
            Ok(())
        } else if nt == crate::events::NODE_TYPE_CULTIVATOR_HEARTBEAT_RECORDED
            || nt == crate::events::NODE_TYPE_CULTIVATOR_HEARTBEAT_RESUMED
        {
            // **COV06** — track the latest cultivator heartbeat (the staleness
            // watchdog's reference). Both recorded + resumed pulses refresh it.
            self.apply_cultivator_heartbeat(node)
        } else if nt.starts_with(crate::events::NODE_TYPE_SUCCESSOR_CHAIN_UPDATED_PREFIX) {
            // **COV06 §3.2.A (F21)** — append a SuccessorEntry to the chain.
            self.apply_successor_chain_updated(node)
        } else if nt == crate::events::NODE_TYPE_CULTIVATION_SUCCESSION_CONFIG_DECLARED {
            // **COV06 §3.2.C** — latest config declaration wins.
            self.apply_succession_config_declared(node)
        } else {
            // Pure-record events (M8-M20) that don't impact Rust-side
            // DerivedState: sporocarp:*, immune:*, raw_material:*,
            // perturb_from_raw:*, mutation:*, evolution_succeeded/failed:*,
            // self_euthanasia_proposal:*, spore_emission:*,
            // schema_migration_cycle_validated:* (sampled progress only), and
            // the M21.1 axis_* + owner_key_* events (which feed Python's view).
            Ok(())
        }
    }

    /// **Sprint 8.G** — a `schema_migration_started:{op}` event opens the
    /// in-flight migration window. Per the MVP single-in-flight rule, the
    /// substrate rejects a second concurrent migration at the skin
    /// (attestation.rs), so derivation simply overwrites: the LAST started
    /// event wins, which on a well-formed DAG is the only one outstanding.
    fn apply_schema_migration_started(
        &mut self,
        node: &DagNode,
    ) -> Result<(), DerivedStateError> {
        let map = decode_event_map(node)?;
        let op_name = match map.get("op") {
            Some(Value::String(s)) => s.clone(),
            _ => {
                return Err(DerivedStateError::EventField {
                    node_type: node.node_type.clone(),
                    field: "op".to_string(),
                    reason: "missing or not String".to_string(),
                })
            }
        };
        let schema_diff_canonical_bytes = match map.get("schema_diff_canonical_bytes") {
            Some(Value::Bytes(b)) => b.clone(),
            _ => {
                return Err(DerivedStateError::EventField {
                    node_type: node.node_type.clone(),
                    field: "schema_diff_canonical_bytes".to_string(),
                    reason: "missing or not Bytes".to_string(),
                })
            }
        };
        let started_at_cycle =
            map_get_uint(&map, "started_at_cycle").map_err(|e| DerivedStateError::EventField {
                node_type: node.node_type.clone(),
                field: "started_at_cycle".to_string(),
                reason: e.to_string(),
            })?;
        let dual_validation_window_cycles = map_get_uint(&map, "dual_validation_window_cycles")
            .map_err(|e| DerivedStateError::EventField {
                node_type: node.node_type.clone(),
                field: "dual_validation_window_cycles".to_string(),
                reason: e.to_string(),
            })?;
        let started_at_unix_ns = timestamp_field(node, &map, "started_at_unix_ns")?;
        self.migration_candidate = Some(DerivedMigrationCandidate {
            op_name,
            schema_diff_canonical_bytes,
            started_at_cycle,
            dual_validation_window_cycles,
            started_at_unix_ns,
        });
        Ok(())
    }

    /// **COV06** — a `cultivator_heartbeat_recorded` / `_resumed` event refreshes
    /// the latest-heartbeat reference (the staleness watchdog's clock). Both
    /// carry `cultivator_pubkey` + `anchor_timestamp_unix_ns`.
    fn apply_cultivator_heartbeat(&mut self, node: &DagNode) -> Result<(), DerivedStateError> {
        let map = decode_event_map(node)?;
        let cultivator_pubkey = bytes_32_field(node, &map, "cultivator_pubkey")?;
        let anchor_timestamp_unix_ns = timestamp_field(node, &map, "anchor_timestamp_unix_ns")?;
        self.latest_heartbeat = Some(DerivedLatestHeartbeat {
            cultivator_pubkey,
            anchor_timestamp_unix_ns,
        });
        Ok(())
    }

    /// **COV06 §3.2.A (F21)** — a `successor_chain_updated:{pk}` event appends a
    /// SuccessorEntry. Non-overlap + monotone-`valid_from` validation happens at
    /// the skin (`handle_update_successor_chain`); derivation is append-only so a
    /// well-formed DAG reconstructs the chain in insertion order.
    fn apply_successor_chain_updated(&mut self, node: &DagNode) -> Result<(), DerivedStateError> {
        let map = decode_event_map(node)?;
        let successor_pubkey = bytes_32_field(node, &map, "successor_pubkey")?;
        let valid_from_unix_ns = timestamp_field(node, &map, "valid_from_unix_ns")?;
        let valid_until_unix_ns = match map.get("valid_until_unix_ns") {
            Some(Value::Timestamp(t)) => Some(*t),
            _ => None, // Null or absent → open-ended
        };
        let attestation_signature = bytes_64_field(node, &map, "attestation_signature")?;
        self.successor_chain.push(DerivedSuccessorEntry {
            successor_pubkey,
            valid_from_unix_ns,
            valid_until_unix_ns,
            attestation_signature,
        });
        Ok(())
    }

    /// **COV06 §3.2.C** — a `cultivation_succession_config_declared` event sets
    /// the active config; the latest declaration wins (overwrite).
    fn apply_succession_config_declared(
        &mut self,
        node: &DagNode,
    ) -> Result<(), DerivedStateError> {
        let map = decode_event_map(node)?;
        let cadence_days = map_get_uint(&map, "cadence_days").map_err(|e| {
            DerivedStateError::EventField {
                node_type: node.node_type.clone(),
                field: "cadence_days".to_string(),
                reason: e.to_string(),
            }
        })?;
        let legacy_window_days = map_get_uint(&map, "legacy_window_days").map_err(|e| {
            DerivedStateError::EventField {
                node_type: node.node_type.clone(),
                field: "legacy_window_days".to_string(),
                reason: e.to_string(),
            }
        })?;
        let orphaned_terminal_window_days = map_get_uint(&map, "orphaned_terminal_window_days")
            .map_err(|e| DerivedStateError::EventField {
                node_type: node.node_type.clone(),
                field: "orphaned_terminal_window_days".to_string(),
                reason: e.to_string(),
            })?;
        let terminal_choice = match map.get("terminal_choice") {
            Some(Value::String(s)) => s.clone(),
            _ => {
                return Err(DerivedStateError::EventField {
                    node_type: node.node_type.clone(),
                    field: "terminal_choice".to_string(),
                    reason: "missing or not String".to_string(),
                })
            }
        };
        self.succession_config = Some(DerivedSuccessionConfig {
            cadence_days,
            legacy_window_days,
            orphaned_terminal_window_days,
            terminal_choice,
        });
        Ok(())
    }

    // ---------------------------------------------------------------------
    // Per-event handlers.
    // ---------------------------------------------------------------------

    fn apply_genesis(&mut self, node: &DagNode) -> Result<(), DerivedStateError> {
        if self.substrate_id.is_some() {
            return Err(DerivedStateError::MultipleGenesis);
        }
        let map = decode_event_map(node)?;
        let id_slice =
            map_get_bytes(&map, "substrate_id").map_err(|e| DerivedStateError::EventField {
                node_type: node.node_type.clone(),
                field: "substrate_id".to_string(),
                reason: e.to_string(),
            })?;
        if id_slice.len() != 32 {
            return Err(DerivedStateError::EventField {
                node_type: node.node_type.clone(),
                field: "substrate_id".to_string(),
                reason: format!("expected 32 bytes; got {}", id_slice.len()),
            });
        }
        let mut id = [0u8; 32];
        id.copy_from_slice(id_slice);
        self.substrate_id = Some(id);
        self.genesis_time_unix_ns = Some(timestamp_field(node, &map, "genesis_time_unix_ns")?);
        // 8f / §16.A: read lineage depth from the genesis_event. Absent → 0
        // (root / pre-8f substrate). This is how a sprouted child learns its
        // own depth at boot from its DAG alone.
        self.generation_depth = match map.get("generation_depth") {
            Some(Value::Uint(n)) => *n,
            _ => 0,
        };
        Ok(())
    }

    fn apply_cycle_advanced(&mut self, node: &DagNode) -> Result<(), DerivedStateError> {
        let map = decode_event_map(node)?;
        let new_cycle =
            map_get_uint(&map, "new_cycle").map_err(|e| DerivedStateError::EventField {
                node_type: node.node_type.clone(),
                field: "new_cycle".to_string(),
                reason: e.to_string(),
            })?;
        self.cycle_counter = new_cycle;
        Ok(())
    }

    fn apply_operator_pinned(&mut self, node: &DagNode) -> Result<(), DerivedStateError> {
        let map = decode_event_map(node)?;
        let pk_slice =
            map_get_bytes(&map, "pubkey").map_err(|e| DerivedStateError::EventField {
                node_type: node.node_type.clone(),
                field: "pubkey".to_string(),
                reason: e.to_string(),
            })?;
        if pk_slice.len() != 32 {
            return Err(DerivedStateError::EventField {
                node_type: node.node_type.clone(),
                field: "pubkey".to_string(),
                reason: format!("expected 32 bytes; got {}", pk_slice.len()),
            });
        }
        let mut pubkey = [0u8; 32];
        pubkey.copy_from_slice(pk_slice);
        let first_pinned_unix_ns = timestamp_field(node, &map, "first_pinned_unix_ns")?;
        // TOFU semantics: first operator_pinned event sets identity; subsequent
        // are protocol violations BUT we accept (overwrite) defensively since
        // the wire protocol rejects duplicates upstream. M21.2+ may emit C-row
        // detector here on conflict.
        self.pinned_operator_identity = Some(PinnedOperatorIdentity {
            pubkey,
            first_pinned_unix_ns,
        });
        Ok(())
    }

    fn apply_nonce_issued(&mut self, node: &DagNode) -> Result<(), DerivedStateError> {
        let map = decode_event_map(node)?;
        let nonce = bytes_32_field(node, &map, "nonce")?;
        let bound_content_hash = bytes_32_field(node, &map, "bound_content_hash")?;
        let bound_dag_tip = bytes_32_field(node, &map, "bound_dag_tip")?;
        let substrate_issued_at_unix_ns =
            timestamp_field(node, &map, "substrate_issued_at_unix_ns")?;
        let expiry_unix_ns = timestamp_field(node, &map, "expiry_unix_ns")?;
        let anchor_clock_issued_at_unix_ns = match map.get("anchor_clock_issued_at_unix_ns") {
            Some(Value::Timestamp(t)) => Some(*t),
            _ => None,
        };
        let anchor_clock_expiry_unix_ns = match map.get("anchor_clock_expiry_unix_ns") {
            Some(Value::Timestamp(t)) => Some(*t),
            _ => None,
        };
        self.nonce_log.insert(
            nonce,
            DerivedNonce {
                nonce,
                bound_content_hash,
                bound_dag_tip,
                substrate_issued_at_unix_ns,
                expiry_unix_ns,
                anchor_clock_issued_at_unix_ns,
                anchor_clock_expiry_unix_ns,
                consumed: false,
            },
        );
        Ok(())
    }

    fn apply_nonce_consumed(&mut self, node: &DagNode) -> Result<(), DerivedStateError> {
        let map = decode_event_map(node)?;
        let nonce = bytes_32_field(node, &map, "nonce")?;
        match self.nonce_log.get_mut(&nonce) {
            Some(entry) => {
                entry.consumed = true;
                Ok(())
            }
            None => Err(DerivedStateError::NonceUnknown {
                prefix: hex_first_8(&nonce),
            }),
        }
    }

    fn apply_nonce_expired(&mut self, node: &DagNode) -> Result<(), DerivedStateError> {
        let map = decode_event_map(node)?;
        let nonce = bytes_32_field(node, &map, "nonce")?;
        // Expired nonces are removed from the live log. If we never had it
        // (unlikely with proper event emission), treat as no-op.
        self.nonce_log.remove(&nonce);
        Ok(())
    }

    fn apply_absorption_event(&mut self, node: &DagNode) -> Result<(), DerivedStateError> {
        let map = decode_event_map(node)?;
        let cycle = map_get_uint(&map, "cycle").map_err(|e| DerivedStateError::EventField {
            node_type: node.node_type.clone(),
            field: "cycle".to_string(),
            reason: e.to_string(),
        })?;
        // last_absorbed_cycle is the HIGHEST cycle whose raw_material was
        // absorbed in this event. The event content stores cycle (= post_cycle
        // at emission time). For derivation purposes we track the max.
        // (Absorbed raw_materials are themselves DAG nodes; their
        // created_at_cycle is bounded above by `cycle`, so cycle is an upper
        // bound on what's been absorbed.)
        self.last_absorbed_cycle = Some(match self.last_absorbed_cycle {
            None => cycle,
            Some(prior) => prior.max(cycle),
        });
        Ok(())
    }
}

// ---------------------------------------------------------------------------
// Helpers.
// ---------------------------------------------------------------------------

fn decode_event_map(
    node: &DagNode,
) -> Result<std::collections::BTreeMap<String, Value>, DerivedStateError> {
    let decoded = cb_decode(node.content_canonical_bytes.as_ref()).map_err(|e| {
        DerivedStateError::EventDecode {
            node_type: node.node_type.clone(),
            reason: e.to_string(),
        }
    })?;
    match decoded {
        Value::Map(m) => Ok(m),
        other => Err(DerivedStateError::EventDecode {
            node_type: node.node_type.clone(),
            reason: format!("event content is not a Map: {other:?}"),
        }),
    }
}

fn timestamp_field(
    node: &DagNode,
    map: &std::collections::BTreeMap<String, Value>,
    field: &str,
) -> Result<i64, DerivedStateError> {
    match map.get(field) {
        Some(Value::Timestamp(t)) => Ok(*t),
        Some(other) => Err(DerivedStateError::EventField {
            node_type: node.node_type.clone(),
            field: field.to_string(),
            reason: format!("expected Timestamp; got {other:?}"),
        }),
        None => Err(DerivedStateError::EventField {
            node_type: node.node_type.clone(),
            field: field.to_string(),
            reason: "missing".to_string(),
        }),
    }
}

fn bytes_32_field(
    node: &DagNode,
    map: &std::collections::BTreeMap<String, Value>,
    field: &str,
) -> Result<[u8; 32], DerivedStateError> {
    let slice = map_get_bytes(map, field).map_err(|e| DerivedStateError::EventField {
        node_type: node.node_type.clone(),
        field: field.to_string(),
        reason: e.to_string(),
    })?;
    if slice.len() != 32 {
        return Err(DerivedStateError::EventField {
            node_type: node.node_type.clone(),
            field: field.to_string(),
            reason: format!("expected 32 bytes; got {}", slice.len()),
        });
    }
    let mut arr = [0u8; 32];
    arr.copy_from_slice(slice);
    Ok(arr)
}

/// **COV06** — extract a 64-byte signature field (Ed25519 sig) from an event map.
fn bytes_64_field(
    node: &DagNode,
    map: &std::collections::BTreeMap<String, Value>,
    field: &str,
) -> Result<[u8; 64], DerivedStateError> {
    let slice = map_get_bytes(map, field).map_err(|e| DerivedStateError::EventField {
        node_type: node.node_type.clone(),
        field: field.to_string(),
        reason: e.to_string(),
    })?;
    if slice.len() != 64 {
        return Err(DerivedStateError::EventField {
            node_type: node.node_type.clone(),
            field: field.to_string(),
            reason: format!("expected 64 bytes; got {}", slice.len()),
        });
    }
    let mut arr = [0u8; 64];
    arr.copy_from_slice(slice);
    Ok(arr)
}

fn hex_first_8(bytes: &[u8; 32]) -> String {
    bytes[..8].iter().map(|b| format!("{b:02x}")).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::events::{
        axis_perturbed_node_type, encode_axis_perturbed, encode_cycle_advanced,
        encode_genesis_event, encode_nonce_consumed, encode_nonce_expired, encode_nonce_issued,
        encode_operator_pinned, genesis_event_node_type, nonce_consumed_node_type,
        nonce_expired_node_type, nonce_issued_node_type, operator_pinned_node_type,
    };
    use myco_kernel_shared::canonical_bytes::CanonicalBytes;
    use myco_kernel_shared::canonical_bytes::{encode, Value};

    fn make_node(node_type: String, cycle: u64, content: CanonicalBytes) -> DagNode {
        use myco_kernel_shared::crypto::{merkle_hash, NodeHash};
        let hash: NodeHash = merkle_hash(&[], content.as_ref());
        DagNode {
            hash,
            parent_hashes: vec![],
            node_type,
            created_at_cycle: cycle,
            content_canonical_bytes: content,
        }
    }

    #[test]
    fn empty_state_has_no_substrate_id() {
        let s = DerivedState::empty();
        assert_eq!(s.substrate_id, None);
        assert_eq!(s.cycle_counter, 0);
        assert!(s.nonce_log.is_empty());
    }

    #[test]
    fn genesis_event_sets_substrate_id_and_time() {
        let mut s = DerivedState::empty();
        let id = [0x42; 32];
        let node = make_node(
            genesis_event_node_type(&id),
            0,
            encode_genesis_event(&id, 1_234_567_890, 0),
        );
        s.apply_event(&node).unwrap();
        assert_eq!(s.substrate_id, Some(id));
        assert_eq!(s.genesis_time_unix_ns, Some(1_234_567_890));
        // 8f: a root genesis_event (depth omitted) decodes to depth 0.
        assert_eq!(s.generation_depth, 0);
    }

    #[test]
    fn genesis_event_records_child_generation_depth() {
        // 8f / §16.A: a child genesis_event carrying generation_depth=4 must
        // surface in DerivedState so the child enforces C47 at boot.
        let mut s = DerivedState::empty();
        let id = [0x77; 32];
        let node = make_node(
            genesis_event_node_type(&id),
            0,
            encode_genesis_event(&id, 1_234_567_890, 4),
        );
        s.apply_event(&node).unwrap();
        // Task #8i: the boot path now seeds ServerState.generation_depth
        // directly from this DerivedState field (no to_legacy_manifest hop),
        // so verifying the field surfaces the child depth is the full check.
        assert_eq!(s.generation_depth, 4);
    }

    #[test]
    fn duplicate_genesis_event_is_rejected() {
        let mut s = DerivedState::empty();
        let id = [0x01; 32];
        let node = make_node(
            genesis_event_node_type(&id),
            0,
            encode_genesis_event(&id, 1, 0),
        );
        s.apply_event(&node).unwrap();
        let result = s.apply_event(&node);
        assert!(matches!(result, Err(DerivedStateError::MultipleGenesis)));
    }

    #[test]
    fn cycle_advanced_updates_counter() {
        let mut s = DerivedState::empty();
        let node = make_node("cycle_advanced".to_string(), 1, encode_cycle_advanced(0, 1));
        s.apply_event(&node).unwrap();
        assert_eq!(s.cycle_counter, 1);

        let node2 = make_node("cycle_advanced".to_string(), 2, encode_cycle_advanced(1, 7));
        s.apply_event(&node2).unwrap();
        assert_eq!(s.cycle_counter, 7);
    }

    #[test]
    fn operator_pinned_event_records_identity() {
        let mut s = DerivedState::empty();
        let pubkey = [0xab; 32];
        let node = make_node(
            operator_pinned_node_type(&pubkey),
            0,
            encode_operator_pinned(&pubkey, 999_999),
        );
        s.apply_event(&node).unwrap();
        let p = s.pinned_operator_identity.unwrap();
        assert_eq!(p.pubkey, pubkey);
        assert_eq!(p.first_pinned_unix_ns, 999_999);
    }

    #[test]
    fn nonce_issued_creates_log_entry_with_consumed_false() {
        let mut s = DerivedState::empty();
        let nonce = [0x11; 32];
        let node = make_node(
            nonce_issued_node_type(&nonce),
            0,
            encode_nonce_issued(&nonce, &[0x22; 32], &[0x33; 32], 1000, 1300, None, None),
        );
        s.apply_event(&node).unwrap();
        let entry = s.nonce_log.get(&nonce).unwrap();
        assert!(!entry.consumed);
        assert_eq!(entry.substrate_issued_at_unix_ns, 1000);
        assert_eq!(entry.expiry_unix_ns, 1300);
        assert_eq!(entry.anchor_clock_issued_at_unix_ns, None);
    }

    #[test]
    fn nonce_issued_with_dual_clock_records_anchor_fields() {
        let mut s = DerivedState::empty();
        let nonce = [0x11; 32];
        let node = make_node(
            nonce_issued_node_type(&nonce),
            0,
            encode_nonce_issued(
                &nonce,
                &[0x22; 32],
                &[0x33; 32],
                1000,
                1300,
                Some(2000),
                Some(2300),
            ),
        );
        s.apply_event(&node).unwrap();
        let entry = s.nonce_log.get(&nonce).unwrap();
        assert_eq!(entry.anchor_clock_issued_at_unix_ns, Some(2000));
        assert_eq!(entry.anchor_clock_expiry_unix_ns, Some(2300));
    }

    #[test]
    fn nonce_consumed_flips_flag() {
        let mut s = DerivedState::empty();
        let nonce = [0x11; 32];
        s.apply_event(&make_node(
            nonce_issued_node_type(&nonce),
            0,
            encode_nonce_issued(&nonce, &[0; 32], &[0; 32], 1, 100, None, None),
        ))
        .unwrap();
        assert!(!s.nonce_log[&nonce].consumed);
        s.apply_event(&make_node(
            nonce_consumed_node_type(&nonce),
            0,
            encode_nonce_consumed(&nonce, 50),
        ))
        .unwrap();
        assert!(s.nonce_log[&nonce].consumed);
    }

    #[test]
    fn nonce_consumed_unknown_returns_error() {
        let mut s = DerivedState::empty();
        let nonce = [0xff; 32];
        let result = s.apply_event(&make_node(
            nonce_consumed_node_type(&nonce),
            0,
            encode_nonce_consumed(&nonce, 50),
        ));
        assert!(matches!(
            result,
            Err(DerivedStateError::NonceUnknown { .. })
        ));
    }

    #[test]
    fn nonce_expired_removes_entry() {
        let mut s = DerivedState::empty();
        let nonce = [0x11; 32];
        s.apply_event(&make_node(
            nonce_issued_node_type(&nonce),
            0,
            encode_nonce_issued(&nonce, &[0; 32], &[0; 32], 1, 100, None, None),
        ))
        .unwrap();
        assert!(s.nonce_log.contains_key(&nonce));
        s.apply_event(&make_node(
            nonce_expired_node_type(&nonce),
            0,
            encode_nonce_expired(&nonce, 100, 200),
        ))
        .unwrap();
        assert!(!s.nonce_log.contains_key(&nonce));
    }

    #[test]
    fn pure_record_events_are_ignored_for_rust_derived_state() {
        let mut s = DerivedState::empty();
        // sporocarp:* and friends should not affect Rust-side state.
        let content = encode(&Value::Map(std::collections::BTreeMap::new())).unwrap();
        for nt in &[
            "sporocarp:appetite_fruiting",
            "immune:C5_attestation_invalid",
            "raw_material:text",
            "perturb_from_raw:hunger",
            "mutation:delta_absorb",
            "evolution_succeeded:modify_axis_threshold",
            "spore_emission:abcd1234",
            "axis_registered:hunger",
            "axis_perturbed:hunger",
            "axis_reset_after_fruiting:hunger",
        ] {
            let node = make_node(nt.to_string(), 0, content.clone());
            s.apply_event(&node).expect("should not error");
        }
        // State remains empty.
        assert_eq!(s, DerivedState::empty());
    }

    #[test]
    fn axis_perturbed_does_not_panic_on_decode() {
        // We need to make sure axis_perturbed events (rich Map content) don't
        // cause apply_event to err — they are pure-record from Rust's perspective.
        let mut s = DerivedState::empty();
        let event = encode_axis_perturbed("x", 1.5);
        let node = make_node(axis_perturbed_node_type("x"), 1, event);
        s.apply_event(&node)
            .expect("axis_perturbed should be ignored cleanly");
    }

    #[test]
    fn from_dag_replays_in_insertion_order() {
        let mut dag = Dag::new();
        let id = [0xab; 32];
        // Genesis
        dag.insert_node(
            vec![],
            genesis_event_node_type(&id),
            0,
            encode_genesis_event(&id, 100, 0),
        )
        .unwrap();
        // Cycle 1
        let tip = dag.tip().unwrap();
        dag.insert_node(
            vec![tip],
            "cycle_advanced".to_string(),
            1,
            encode_cycle_advanced(0, 1),
        )
        .unwrap();
        // Cycle 2
        let tip = dag.tip().unwrap();
        dag.insert_node(
            vec![tip],
            "cycle_advanced".to_string(),
            2,
            encode_cycle_advanced(1, 2),
        )
        .unwrap();
        // Operator pin
        let pubkey = [0xcd; 32];
        let tip = dag.tip().unwrap();
        dag.insert_node(
            vec![tip],
            operator_pinned_node_type(&pubkey),
            2,
            encode_operator_pinned(&pubkey, 200),
        )
        .unwrap();

        let derived = DerivedState::from_dag(&dag).unwrap();
        assert_eq!(derived.substrate_id, Some(id));
        assert_eq!(derived.genesis_time_unix_ns, Some(100));
        assert_eq!(derived.cycle_counter, 2);
        assert!(derived.pinned_operator_identity.is_some());
        assert_eq!(derived.pinned_operator_identity.unwrap().pubkey, pubkey);
    }

    #[test]
    fn from_dag_replay_is_deterministic() {
        // Building the same DAG twice and replaying produces identical states.
        let build = || -> Dag {
            let mut dag = Dag::new();
            let id = [0x55; 32];
            dag.insert_node(
                vec![],
                genesis_event_node_type(&id),
                0,
                encode_genesis_event(&id, 1, 0),
            )
            .unwrap();
            let tip = dag.tip().unwrap();
            dag.insert_node(
                vec![tip],
                "cycle_advanced".to_string(),
                1,
                encode_cycle_advanced(0, 1),
            )
            .unwrap();
            let nonce = [0xab; 32];
            let tip = dag.tip().unwrap();
            dag.insert_node(
                vec![tip],
                nonce_issued_node_type(&nonce),
                1,
                encode_nonce_issued(&nonce, &[0; 32], &[0; 32], 100, 400, None, None),
            )
            .unwrap();
            dag
        };
        let d1 = DerivedState::from_dag(&build()).unwrap();
        let d2 = DerivedState::from_dag(&build()).unwrap();
        assert_eq!(d1, d2);
    }

    #[test]
    fn absorption_event_advances_last_absorbed_cycle() {
        let mut s = DerivedState::empty();
        let mut content_map = std::collections::BTreeMap::new();
        content_map.insert("cycle".to_string(), Value::Uint(5));
        content_map.insert("absorbed_count".to_string(), Value::Uint(2));
        content_map.insert("absorbed_hashes".to_string(), Value::Array(vec![]));
        let bytes = encode(&Value::Map(content_map)).unwrap();
        let node = make_node("absorption_event:cycle_5".to_string(), 5, bytes);
        s.apply_event(&node).unwrap();
        assert_eq!(s.last_absorbed_cycle, Some(5));
    }

    #[test]
    fn absorption_event_only_advances_high_water_mark() {
        let mut s = DerivedState::empty();
        let make_abs = |cycle: u64| {
            let mut m = std::collections::BTreeMap::new();
            m.insert("cycle".to_string(), Value::Uint(cycle));
            m.insert("absorbed_count".to_string(), Value::Uint(0));
            m.insert("absorbed_hashes".to_string(), Value::Array(vec![]));
            let bytes = encode(&Value::Map(m)).unwrap();
            make_node(format!("absorption_event:cycle_{cycle}"), cycle, bytes)
        };
        s.apply_event(&make_abs(3)).unwrap();
        s.apply_event(&make_abs(7)).unwrap();
        s.apply_event(&make_abs(5)).unwrap(); // out-of-order: should NOT regress
        assert_eq!(s.last_absorbed_cycle, Some(7));
    }

    // ---------------------------------------------------------------------
    // M25.2: ObservatorySnapshot canonical-bytes roundtrip tests.
    // ---------------------------------------------------------------------

    fn make_observatory_snapshot(at_cycle: u64) -> ObservatorySnapshot {
        ObservatorySnapshot {
            at_cycle,
            at_unix_ns: 1_700_000_000_000 + (at_cycle as i64) * 1_000_000,
            signal_1_dag_node_count: 100 + at_cycle * 7,
            signal_1_dag_total_content_bytes: 5_000 + at_cycle * 137,
            signal_2_evolution_event_count: at_cycle / 3,
            signal_3_distinct_perturbed_axes_count: (at_cycle % 5).saturating_add(1),
            signal_4b_reachable_peer_count: at_cycle % 4,
            signal_6_ratio_repr: format!("{}.{:0>2}", at_cycle / 10, at_cycle % 10),
            // M26.2 P11.b cost signals: vary the values cycle-over-cycle so
            // roundtrip tests exercise distinct nonzero u64 paths.
            signal_7_compute_ns: 1_000_000 + at_cycle * 13_579,
            signal_8_network_bytes: at_cycle * 256,
            signal_9_storage_bytes: 1_024 + at_cycle * 137,
            // M26.4 P14.c telos: vary cosine values across `[-1, +1]` to
            // exercise serializer round-trip.
            signal_telos_alignment_repr: format!("{:.6}", ((at_cycle as f64) * 0.07).sin()),
            // v3.1.1 P07 observability: vary across cycles to exercise
            // serializer + alternate the boolean each cycle.
            signal_internal_mortality_event_density: at_cycle * 2,
            signal_hoarding_indicator: at_cycle % 2 == 0,
        }
    }

    #[test]
    fn observatory_snapshot_canonical_value_roundtrip() {
        let original = make_observatory_snapshot(7);
        let v = original.to_canonical_value();
        let decoded = ObservatorySnapshot::from_canonical_value(&v)
            .expect("snapshot decodes from its own canonical Value");
        assert_eq!(decoded, original);
    }

    #[test]
    fn observatory_snapshot_empty_signal_6_repr_roundtrip() {
        let mut snap = make_observatory_snapshot(3);
        snap.signal_6_ratio_repr.clear(); // simulate "no operator window attested"
        let v = snap.to_canonical_value();
        let decoded = ObservatorySnapshot::from_canonical_value(&v).unwrap();
        assert_eq!(decoded.signal_6_ratio_repr, "");
        assert_eq!(decoded, snap);
    }

    #[test]
    fn observatory_history_canonical_bytes_roundtrip() {
        // Populate a DerivedState with a non-empty observatory_history,
        // round-trip it through canonical_bytes, and assert structural
        // equality.
        let mut state = DerivedState::empty();
        state.substrate_id = Some([0x33; 32]);
        state.genesis_time_unix_ns = Some(1_700_000_000_000);
        state.cycle_counter = 12;
        for cycle in 1..=12 {
            state.observatory_history.push_back(make_observatory_snapshot(cycle));
        }
        let snapshot_at_tip = [0x77u8; 32];
        let bytes = state.to_canonical_bytes(Some(&snapshot_at_tip));
        let (decoded_state, decoded_tip) =
            DerivedState::from_canonical_bytes(bytes.as_ref())
                .expect("snapshot decode succeeds")
                .expect("snapshot version 1 recognized");
        assert_eq!(decoded_tip, Some(snapshot_at_tip));
        assert_eq!(decoded_state.observatory_history.len(), 12);
        for (orig, dec) in state
            .observatory_history
            .iter()
            .zip(decoded_state.observatory_history.iter())
        {
            assert_eq!(orig, dec, "snapshot identity preserved across roundtrip");
        }
        assert_eq!(state, decoded_state, "full DerivedState equality");
    }

    // ---------------------------------------------------------------------
    // 8.G: schema-migration candidate derivation + snapshot round-trip.
    // ---------------------------------------------------------------------

    fn migration_started_node(op: &str, started_at_cycle: u64, window: u64) -> DagNode {
        use crate::events::{
            encode_schema_migration_started, schema_migration_started_node_type,
        };
        make_node(
            schema_migration_started_node_type(op),
            started_at_cycle,
            encode_schema_migration_started(
                op,
                &[0xaa, 0xbb, 0xcc],
                started_at_cycle,
                window,
                1_700_000_000_000_000_000,
            ),
        )
    }

    #[test]
    fn schema_migration_started_sets_candidate() {
        let mut s = DerivedState::empty();
        assert!(s.migration_candidate.is_none());
        s.apply_event(&migration_started_node("modify_axis_threshold", 5, 100))
            .unwrap();
        let mc = s.migration_candidate.expect("candidate present after started");
        assert_eq!(mc.op_name, "modify_axis_threshold");
        assert_eq!(mc.started_at_cycle, 5);
        assert_eq!(mc.dual_validation_window_cycles, 100);
        assert_eq!(mc.schema_diff_canonical_bytes, vec![0xaa, 0xbb, 0xcc]);
    }

    #[test]
    fn schema_migration_committed_clears_candidate() {
        use crate::events::{
            encode_schema_migration_committed, schema_migration_committed_node_type,
        };
        let mut s = DerivedState::empty();
        s.apply_event(&migration_started_node("modify_axis_threshold", 5, 100))
            .unwrap();
        assert!(s.migration_candidate.is_some());
        let committed = make_node(
            schema_migration_committed_node_type("modify_axis_threshold"),
            105,
            encode_schema_migration_committed("modify_axis_threshold", 105, 5, 100),
        );
        s.apply_event(&committed).unwrap();
        assert!(
            s.migration_candidate.is_none(),
            "commit must clear the in-flight candidate"
        );
    }

    #[test]
    fn schema_migration_rolled_back_clears_candidate() {
        use crate::events::{
            encode_schema_migration_rolled_back, schema_migration_rolled_back_node_type,
        };
        let mut s = DerivedState::empty();
        s.apply_event(&migration_started_node("add_axis_to_gradient", 2, 50))
            .unwrap();
        assert!(s.migration_candidate.is_some());
        let rolled_back = make_node(
            schema_migration_rolled_back_node_type("add_axis_to_gradient"),
            7,
            encode_schema_migration_rolled_back("add_axis_to_gradient", "diverged", 7),
        );
        s.apply_event(&rolled_back).unwrap();
        assert!(
            s.migration_candidate.is_none(),
            "rollback must clear the in-flight candidate"
        );
    }

    #[test]
    fn schema_migration_cycle_validated_is_pure_record() {
        // The sampled cycle_validated event must NOT touch the candidate (it
        // is observability only — decide_cycle drives the actual transition).
        use crate::events::{
            encode_schema_migration_cycle_validated,
            schema_migration_cycle_validated_node_type,
        };
        let mut s = DerivedState::empty();
        s.apply_event(&migration_started_node("modify_axis_threshold", 5, 100))
            .unwrap();
        let before = s.migration_candidate.clone();
        let validated = make_node(
            schema_migration_cycle_validated_node_type("modify_axis_threshold"),
            10,
            encode_schema_migration_cycle_validated("modify_axis_threshold", 10, true, ""),
        );
        s.apply_event(&validated).unwrap();
        assert_eq!(
            s.migration_candidate, before,
            "cycle_validated must not alter the candidate"
        );
    }

    #[test]
    fn migration_candidate_snapshot_roundtrip_v2() {
        let mut state = DerivedState::empty();
        state.substrate_id = Some([0x33; 32]);
        state.genesis_time_unix_ns = Some(1_700_000_000_000);
        state.cycle_counter = 12;
        state.migration_candidate = Some(DerivedMigrationCandidate {
            op_name: "modify_axis_threshold".to_string(),
            schema_diff_canonical_bytes: vec![0xde, 0xad, 0xbe, 0xef],
            started_at_cycle: 8,
            dual_validation_window_cycles: 100,
            started_at_unix_ns: 1_700_000_111_222,
        });
        let bytes = state.to_canonical_bytes(None);
        // v2 format_version must be present.
        let decoded_v = match myco_kernel_shared::canonical_bytes::decode(bytes.as_ref()).unwrap() {
            Value::Map(m) => m,
            _ => panic!(),
        };
        assert!(matches!(
            decoded_v.get("format_version"),
            Some(Value::Uint(2))
        ));
        let (decoded_state, _) = DerivedState::from_canonical_bytes(bytes.as_ref())
            .expect("decode ok")
            .expect("version 2 recognized");
        assert_eq!(decoded_state.migration_candidate, state.migration_candidate);
        assert_eq!(state, decoded_state, "full DerivedState equality v2 roundtrip");
    }

    #[test]
    fn snapshot_without_migration_candidate_omits_field_and_roundtrips() {
        let mut state = DerivedState::empty();
        state.substrate_id = Some([0x44; 32]);
        state.cycle_counter = 3;
        assert!(state.migration_candidate.is_none());
        let bytes = state.to_canonical_bytes(None);
        let decoded_map = match myco_kernel_shared::canonical_bytes::decode(bytes.as_ref()).unwrap()
        {
            Value::Map(m) => m,
            _ => panic!(),
        };
        assert!(
            !decoded_map.contains_key("migration_candidate"),
            "absent migration → field omitted (back-compat byte shape)"
        );
        let (decoded_state, _) = DerivedState::from_canonical_bytes(bytes.as_ref())
            .unwrap()
            .unwrap();
        assert!(decoded_state.migration_candidate.is_none());
        assert_eq!(state, decoded_state);
    }

    #[test]
    fn v1_snapshot_decodes_with_none_migration_candidate() {
        // A hand-built v1 snapshot (no migration_candidate field, format_version=1)
        // must still decode — proving pre-8.G snapshot.cb files keep loading.
        use std::collections::BTreeMap;
        let mut root = BTreeMap::new();
        root.insert("format_version".to_string(), Value::Uint(1));
        root.insert("cycle_counter".to_string(), Value::Uint(9));
        root.insert("nonce_log".to_string(), Value::Array(vec![]));
        let bytes = myco_kernel_shared::canonical_bytes::encode(&Value::Map(root)).unwrap();
        let (decoded_state, tip) = DerivedState::from_canonical_bytes(bytes.as_ref())
            .expect("v1 decode ok")
            .expect("v1 recognized");
        assert!(tip.is_none());
        assert_eq!(decoded_state.cycle_counter, 9);
        assert!(
            decoded_state.migration_candidate.is_none(),
            "v1 snapshot must decode to None migration_candidate"
        );
    }

    #[test]
    fn observatory_history_empty_compatible() {
        // A DerivedState with NO observatory_history (pre-M25.2 snapshot)
        // round-trips: the omitted field decodes back to an empty deque.
        let mut state = DerivedState::empty();
        state.substrate_id = Some([0x44; 32]);
        state.genesis_time_unix_ns = Some(1_700_000_000_000);
        state.cycle_counter = 5;
        assert!(state.observatory_history.is_empty());
        let bytes = state.to_canonical_bytes(None);
        let (decoded_state, decoded_tip) =
            DerivedState::from_canonical_bytes(bytes.as_ref())
                .expect("decode ok")
                .expect("version 1");
        assert!(decoded_tip.is_none());
        assert!(decoded_state.observatory_history.is_empty());
        assert_eq!(state, decoded_state);
    }
}
