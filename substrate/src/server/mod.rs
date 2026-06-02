//! Substrate-side server loop — handles operator-facing M5 protocol.
//!
//! ## Lifecycle
//!
//! 1. Read first frame; expect `hello` keyed by [`bootstrap_key`].
//! 2. Extract session_secret, spawn the Python kernel/tropism worker (via
//!    [`BridgeClient::spawn_and_handshake`]), respond with `hello_ack`.
//! 3. Loop: read frame keyed by session_secret → dispatch → write response.
//! 4. On `shutdown`: write `shutdown_ack`, shut the Python worker down, exit.
//! 5. On EOF: shut down the Python worker and exit cleanly.
//!
//! ## Message routing
//!
//! - `register_axis` / `perturb` / `snapshot` → forwarded to Python verbatim.
//! - `advance` → runs one [`CycleEngine`] step; gradient-advance crosses to
//!   Python; other 4 steps are Rust-native stubs at M6.
//! - `shutdown` → graceful exit + Python worker shutdown.
//! - Any other type → `error` envelope.

use std::collections::BTreeMap;
use std::io::Write;
use std::path::PathBuf;
use std::time::Duration;

use myco_kernel_bridge::client::BridgeClient;
use myco_kernel_bridge::framing::{read_frame, write_frame};
use myco_kernel_bridge::protocol::{
    bootstrap_key, decode_frame_body, encode_frame_body, msg_type, Message,
};
use myco_kernel_bridge::BridgeError;
use myco_kernel_continuity::cycle::{CycleConfig, CycleEngine};
use myco_kernel_schema::dag::Dag;
use myco_kernel_shared::canonical_bytes::{
    encode as cb_encode, float_repr as shared_float_repr, Value,
};

use crate::persistence::{
    default_state_dir, ensure_state_dir, load_dag, load_nonce_log, load_pinned_operator_identity,
    Manifest, PinnedOperatorIdentity,
};
use crate::SubstrateError;

// Server loop is split across submodules; `run_loop` (in this file) calls
// `dispatch` + `do_autonomous_tick` by bare name via these re-imports, so the
// call sites are byte-identical to the pre-split monolithic `server.rs`.
mod autonomous;
mod dispatch;
use autonomous::do_autonomous_tick;
use dispatch::dispatch;

/// **M-anchor-2 §9.2.1**: read the birth attestation env vars set by the
/// operator process at substrate spawn time. Returns
/// `(attested_canonical_bytes, signature, owner_pubkey)` if all three env
/// vars are present + valid hex; `None` otherwise (partial or malformed
/// triggers fallback — C20 fires on subsequent boots).
///
/// Env var contract:
/// - `MYCO_BIRTH_ATTESTATION_BYTES_HEX`: hex of the canonical-bytes Map the
///   owner signed (returned by anchor_surface_host's BirthAttest RPC).
/// - `MYCO_BIRTH_ATTESTATION_SIGNATURE_HEX`: 128 hex chars = 64 bytes.
/// - `MYCO_BIRTH_ATTESTATION_OWNER_PUBKEY_HEX`: 64 hex chars = 32 bytes.
fn read_birth_attestation_env_vars() -> Option<(Vec<u8>, [u8; 64], [u8; 32])> {
    let bytes_hex = std::env::var("MYCO_BIRTH_ATTESTATION_BYTES_HEX").ok()?;
    let sig_hex = std::env::var("MYCO_BIRTH_ATTESTATION_SIGNATURE_HEX").ok()?;
    let pk_hex = std::env::var("MYCO_BIRTH_ATTESTATION_OWNER_PUBKEY_HEX").ok()?;
    let attested_bytes = hex_decode_vec(&bytes_hex)?;
    let sig_vec = hex_decode_vec(&sig_hex)?;
    if sig_vec.len() != 64 {
        return None;
    }
    let mut signature = [0u8; 64];
    signature.copy_from_slice(&sig_vec);
    let pk_vec = hex_decode_vec(&pk_hex)?;
    if pk_vec.len() != 32 {
        return None;
    }
    let mut owner_pubkey = [0u8; 32];
    owner_pubkey.copy_from_slice(&pk_vec);
    Some((attested_bytes, signature, owner_pubkey))
}

/// **F23 / C50** — read the duress-keypair registration env vars set by the
/// operator process at genesis (mirrors [`read_birth_attestation_env_vars`]).
/// Each registration is an owner-pre-attested duress pubkey: the owner signed a
/// `duress_keypair_registration` body off-line (anchor-surface) and the operator
/// passes the (body, signature, pubkey, label) tuple through env vars so the
/// substrate emits the `duress_keypair_registered:{prefix}` event at genesis —
/// EXACTLY as if the owner had submitted it as a CI mutation, including the
/// owner-signature capture for offline re-verification.
///
/// Env var contract (N = `MYCO_DURESS_REGISTRATION_COUNT`, capped to avoid a
/// malformed-env DoS; absent / 0 → no duress registrations):
/// - `MYCO_DURESS_REGISTRATION_COUNT`: decimal count of registrations.
/// - For i in `0..N`:
///   - `MYCO_DURESS_REGISTRATION_{i}_BYTES_HEX`: hex of the owner-signed
///     `duress_keypair_registration` body (see
///     [`crate::events::build_duress_keypair_registration_canonical_bytes`]).
///   - `MYCO_DURESS_REGISTRATION_{i}_SIGNATURE_HEX`: 128 hex chars = 64 bytes.
///   - `MYCO_DURESS_REGISTRATION_{i}_OWNER_PUBKEY_HEX`: 64 hex chars = 32 bytes.
///
/// A malformed / partial entry is SKIPPED (the others still register) — a
/// genesis with a bad duress env var still boots; the missing registration just
/// isn't present (the owner can register it later via a CI mutation). Returns
/// `(owner_signed_body, signature, owner_pubkey)` tuples; the body is decoded
/// downstream so the substrate can extract the duress pubkey + label.
fn read_duress_registrations_env_vars() -> Vec<(Vec<u8>, [u8; 64], [u8; 32])> {
    /// Cap on parsed registrations so a hostile/garbled env can't drive an
    /// unbounded genesis loop. A real cultivator registers a small handful.
    const MAX_DURESS_REGISTRATIONS: u32 = 16;

    let count: u32 = match std::env::var("MYCO_DURESS_REGISTRATION_COUNT") {
        Ok(s) => s.trim().parse().unwrap_or(0),
        Err(_) => 0,
    };
    let count = count.min(MAX_DURESS_REGISTRATIONS);
    let mut out = Vec::new();
    for i in 0..count {
        let bytes_hex = match std::env::var(format!("MYCO_DURESS_REGISTRATION_{i}_BYTES_HEX")) {
            Ok(s) => s,
            Err(_) => continue,
        };
        let sig_hex = match std::env::var(format!("MYCO_DURESS_REGISTRATION_{i}_SIGNATURE_HEX")) {
            Ok(s) => s,
            Err(_) => continue,
        };
        let pk_hex = match std::env::var(format!("MYCO_DURESS_REGISTRATION_{i}_OWNER_PUBKEY_HEX")) {
            Ok(s) => s,
            Err(_) => continue,
        };
        let Some(body) = hex_decode_vec(&bytes_hex) else {
            continue;
        };
        let Some(sig_vec) = hex_decode_vec(&sig_hex) else {
            continue;
        };
        if sig_vec.len() != 64 {
            continue;
        }
        let mut signature = [0u8; 64];
        signature.copy_from_slice(&sig_vec);
        let Some(pk_vec) = hex_decode_vec(&pk_hex) else {
            continue;
        };
        if pk_vec.len() != 32 {
            continue;
        }
        let mut owner_pubkey = [0u8; 32];
        owner_pubkey.copy_from_slice(&pk_vec);
        out.push((body, signature, owner_pubkey));
    }
    out
}

fn hex_decode_vec(s: &str) -> Option<Vec<u8>> {
    if s.len() % 2 != 0 {
        return None;
    }
    let mut out = Vec::with_capacity(s.len() / 2);
    let bytes = s.as_bytes();
    for i in (0..bytes.len()).step_by(2) {
        let hi = hex_nibble(bytes[i])?;
        let lo = hex_nibble(bytes[i + 1])?;
        out.push((hi << 4) | lo);
    }
    Some(out)
}

fn hex_nibble(b: u8) -> Option<u8> {
    match b {
        b'0'..=b'9' => Some(b - b'0'),
        b'a'..=b'f' => Some(10 + (b - b'a')),
        b'A'..=b'F' => Some(10 + (b - b'A')),
        _ => None,
    }
}

/// **M26.3 C42 fix**: thread-local side channel for surfacing
/// `manifest.cb` load-failure evidence from the boot-time legacy-path branch
/// (which doesn't yet hold `state`) up to the post-construction emit site.
///
/// Why a thread-local instead of a return-value thread-through:
/// - The boot path is a complex chain of nested matches over Result/Option;
///   threading another Option<String> through each arm would balloon the
///   patch surface and risk subtle merge mistakes with the dag.cb evidence
///   pattern (which IS thread-through). Thread-local keeps the M26.3 patch
///   surgical and isolates the side channel to ONE boot per thread, which
///   is the runtime invariant (server::run is called once per process).
pub(crate) mod manifest_failure_evidence {
    use std::cell::RefCell;
    thread_local! {
        static EV: RefCell<Option<String>> = const { RefCell::new(None) };
    }
    pub(crate) fn set(v: Option<String>) {
        EV.with(|e| *e.borrow_mut() = v);
    }
    pub(crate) fn take() -> Option<String> {
        EV.with(|e| e.borrow_mut().take())
    }
}

// ---------------------------------------------------------------------------
// M18 P4 永恒迭代 cycle trait adapters (DagVerifyTier1, CycleAbsorber,
// DagBreachWatcher, PinnedHandshakeReader, PythonGradientAdvancer) and the
// `advance` handler now live in `crate::ingest` (Phase B Step 4). The trait
// impls are private to that module since `dispatch` only invokes
// `crate::ingest::handle_advance`.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// M23.1 P4 永恒迭代 — autonomous tick infrastructure.
// ---------------------------------------------------------------------------

/// Frame messages shipped from the stdin reader thread to the main loop.
///
/// The reader sends `Frame(bytes)` per successful frame read. On clean EOF
/// (read_frame returns `Ok(None)`), the reader exits — dropping its `Sender`
/// — and the main loop's next `recv_timeout` returns `Disconnected`. On I/O
/// error, the reader sends `ReadError(msg)` so the main loop can surface the
/// actual cause before terminating.
#[derive(Debug)]
enum FrameMsg {
    /// A complete length-prefixed frame body (HMAC + canonical-bytes).
    Frame(Vec<u8>),
    /// A read error encountered before reaching EOF — surfaced for diagnostics.
    ReadError(String),
}

/// Default autonomous tick interval (milliseconds). At 500ms the substrate
/// ticks twice per second when idle. Configurable via `MYCO_TICK_INTERVAL_MS`.
const DEFAULT_TICK_INTERVAL_MS: u64 = 500;

/// Parse the autonomous tick interval from `MYCO_TICK_INTERVAL_MS` env var
/// (defaults to [`DEFAULT_TICK_INTERVAL_MS`]).
fn parse_tick_interval() -> Duration {
    let ms: u64 = std::env::var("MYCO_TICK_INTERVAL_MS")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(DEFAULT_TICK_INTERVAL_MS);
    Duration::from_millis(ms)
}

// ---------------------------------------------------------------------------
// M23.1 P4 永恒迭代 — autonomous tick implementation moved to
// `crate::server::autonomous` (`do_autonomous_tick` + the self-driven cycle
// helpers). `run_loop` invokes `do_autonomous_tick` (re-imported below) from
// its `recv_timeout` Timeout branch; behavior is unchanged.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Server state.
// ---------------------------------------------------------------------------

/// Session state for one operator connection.
pub(crate) struct ServerState {
    /// The session_secret transported by the `hello` from the operator.
    pub(crate) session_secret: [u8; 32],
    /// Whether the operator handshake has completed.
    pub(crate) handshake_complete: bool,
    /// Python kernel/tropism worker handle (None pre-handshake).
    pub(crate) python_client: Option<BridgeClient>,
    /// CycleEngine for substrate-side metabolic-cycle execution.
    pub(crate) cycle_engine: CycleEngine,
    // ----- Task #8i: discrete substrate-identity / metabolic-position fields.
    // These five fields are the single in-memory source of truth for what was
    // formerly mirrored in `manifest: Manifest`. They are seeded at boot from
    // the DAG-derived `DerivedState` (DAG-first arm) or from a loaded/genesis
    // `Manifest` via the inverse sentinel mapping (legacy arm). Read through
    // the `substrate_id()` / `genesis_time_unix_ns()` / `cycle_counter()` /
    // `last_absorbed_cycle()` / `generation_depth()` accessors, which reproduce
    // the former `to_legacy_manifest` sentinel mapping so emitted bytes are
    // byte-identical. The legacy `manifest.cb` WRITE path is dead (M21.4
    // `save_manifest` no-op); the `Manifest` struct survives only as a
    // back-compat `manifest.cb` reader + sprout-child id factory.
    /// 32-byte substrate identifier. `None` until genesis (sentinel `[0u8;32]`).
    pub(crate) substrate_id: Option<[u8; 32]>,
    /// Genesis wall-clock time (ns). `None` until genesis (sentinel `0`).
    pub(crate) genesis_time_unix_ns: Option<i64>,
    /// Authoritative metabolic-cycle counter (M7).
    pub(crate) cycle_counter: u64,
    /// Highest absorbed cycle (M18); `None` = no absorption yet.
    pub(crate) last_absorbed_cycle: Option<u64>,
    /// **8f / L1/GOVERNANCE §16.A (F22)**: this substrate's lineage depth
    /// (root = 0). Bounds C47 reproduction depth.
    pub(crate) generation_depth: u64,
    /// Directory in which the substrate's state files live (M7).
    pub(crate) state_dir: PathBuf,
    /// Persistent causal DAG of substrate events (sporocarps etc.) (M8).
    pub(crate) dag: Dag,
    /// Pinned operator identity public key (M9). `None` until TOFU on first hello.
    pub(crate) pinned_operator_identity: Option<PinnedOperatorIdentity>,
    /// M13: Attestation nonce log (in-process; not persisted at M13 minimum).
    /// Keyed by nonce bytes for O(1) lookup on submit.
    pub(crate) nonce_log: std::collections::HashMap<[u8; 32], crate::attestation::AttestationNonce>,
    /// M22 P5 万物互联: inter-substrate federation state (listener + peers).
    /// Always present; the listener field stays `None` until the operator
    /// invokes `federation_open_listener`.
    pub(crate) federation: crate::federation::FederationState,
    /// **C13 — local federation peer revocation** (L1/GOVERNANCE §5.2 +
    /// L2/FEDERATION §6.5.b per-peer OWNER revocation). Set of
    /// `substrate_id`s the owner has revoked via an attested
    /// `revoke_federation_peer` CI mutation. The DAG is canonical — each
    /// revocation is a `federation_peer_revoked:{prefix}` event; this in-memory
    /// set is a projection re-derived at boot via
    /// [`crate::events::derive_revoked_federation_peers_from_dag`] and kept
    /// current by `emit_federation_peer_revoked`. Consulted at the federation
    /// egress site (block + emit C13) and the ingest site (drop revoked-peer
    /// events). Purely additive (a CRL only grows; no un-revoke event exists).
    pub(crate) revoked_federation_peers: std::collections::HashSet<[u8; 32]>,
    /// **F23 / C50 — duress keypair coercion defense** (L2/TRUST_MODEL §10.A.2 +
    /// L1/GOVERNANCE F23 + AS §5.6). The set of pre-registered duress Ed25519
    /// pubkeys. An `attestation_signature` that verifies under ANY member (and
    /// thus NOT under the owner key — the keys are disjoint, see
    /// [`crate::events::derive_duress_pubkeys_from_dag`]) is a duress signal:
    /// the substrate cosmetically accepts the mutation but suppresses its
    /// substantive effect, emits C50 + `duress_signature_observed` silently, and
    /// freezes. DAG-derived at boot (each `duress_keypair_registered:{prefix}`
    /// event) + kept current by the registration accept path; never persisted
    /// separately. Empty on a substrate that never registered a duress key, so
    /// every duress code path is inert there (byte-compat).
    pub(crate) duress_pubkeys: std::collections::HashSet<[u8; 32]>,
    /// **F23 / C50** — whether destructive (CI-class) mutations are currently
    /// frozen because a duress signature was observed and not yet cleared. While
    /// true, an early gate in `attestation::handle_submit_mutation` cosmetically
    /// suppresses destructive CI mutations + re-emits C50 (the unfreeze
    /// mutations `out_of_band_safety_reattestation` /
    /// `anchor_heartbeat_with_safety_confirmation` are exempt). DAG-derived at
    /// boot via [`crate::events::derive_duress_freeze_active_from_dag`]
    /// (last-writer FSM over `coerced_owner_suspected` / `duress_cleared`), so a
    /// substrate restarted while frozen resumes frozen. Kept current by the
    /// duress recognition + unfreeze emit paths thereafter.
    pub(crate) duress_freeze_active: bool,
    /// M25.0 + M25.4: the substrate's private Ed25519 signing seed.
    ///
    /// This NEVER goes on the wire. Used to (1) sign `snapshot.cb` so a
    /// forged snapshot can't masquerade, and (2) sign FED_HELLO payloads
    /// for federation mutual auth beyond TOFU. Reconstruct an
    /// `Ed25519PrivateKey` via `Ed25519PrivateKey::from_seed(&seed)` at
    /// each signing site (the keypair is cheap to derive on demand).
    pub(crate) substrate_signing_seed: [u8; 32],
    /// M25.2 P5 万物互联: rolling observatory snapshot history. One snapshot
    /// is appended on every `cycle_advanced` emission. Used by
    /// `handle_query_substrate_observatory` to compute signal #5 time
    /// trends, `bet_weakening_quorum`, and emergent composite weights.
    ///
    /// Capped at `OBSERVATORY_HISTORY_CAP`; oldest dropped on overflow.
    /// Round-trips through `snapshot.cb` so the trend window survives
    /// reboots when a fresh snapshot is on disk; otherwise filled
    /// organically as cycles tick.
    pub(crate) observatory_history:
        std::collections::VecDeque<crate::derived_state::ObservatorySnapshot>,
    /// M25.2: cache of the most-recent operator-attested context-window size.
    /// Set whenever a `query_substrate_observatory` request carries
    /// `operator_attested_context_window_bytes`. Used at cycle-advance time
    /// to populate `signal_6_ratio_repr` on each new ObservatorySnapshot.
    /// `None` until the operator first attests a window. The substrate
    /// cannot derive this autonomously — it is an operator-environment fact.
    pub(crate) last_operator_context_window_bytes: Option<u64>,
    /// M25.1: tracks the most recent doctrine-burst sporocarp emission to
    /// prevent burst spam on every observatory query. Stores
    /// `manifest.cycle_counter` at emission time. Cooldown: 100 cycles.
    pub(crate) last_doctrine_burst_emitted_at_cycle: Option<u64>,
    /// M25.2: same as above but for the `C40_bet_weakening_quorum`
    /// detector. Cooldown: 100 cycles.
    pub(crate) last_bet_weakening_quorum_emitted_at_cycle: Option<u64>,
    /// **M26.2 P11.b**: per-cycle cost accumulator. Snapshot-and-reset is
    /// called at every `cycle_advanced` by `append_observatory_snapshot_to_state`,
    /// producing signals #7 (compute), #8 (network), #9 (storage) for the
    /// rolling observatory history.
    pub(crate) cost_accumulator: crate::observatory::CostAccumulator,
    /// **M26.4 F19**: per-axis cost budget thresholds. Tier-1 SSoT seed; CI-
    /// mutable via `mutation_type="cost_budget_set"` (rule registered in
    /// Python classifier). When a cost signal exceeds its budget, P11.c
    /// ordered fallback kicks in (see `saturation_stage`).
    pub(crate) cost_budgets: crate::events::CostBudgets,
    /// **M26.4 P11.c**: current saturation stage. Transitions on each
    /// `cycle_advanced` based on cost signals vs `cost_budgets`. Persists
    /// in-process only (re-derived at boot from DAG via the most recent
    /// `substrate_saturated` / `substrate_normal_restored` event pair).
    pub(crate) saturation_stage: crate::events::SaturationStage,
    /// **M26.4 P11.c**: consecutive cycles spent in `PostEligibility`. When
    /// this reaches `cost_budgets.sustained_saturation_cycle_threshold`, the
    /// substrate transitions to `Saturated` (alive::saturated). Resets when
    /// the stage drops back to Normal/PreEligibility.
    pub(crate) post_eligibility_consecutive_cycles: u64,
    /// **P11.c sustained-saturation → P7 escalation**: consecutive cycles spent
    /// in `Saturated`. When this crosses `cost_budgets
    /// .sustained_saturation_mortality_cycle_threshold`, the substrate
    /// escalates to a `self_euthanasia_proposal:metabolic_saturation` (a
    /// PROPOSAL the existing accept_self_euthanasia path executes — NOT
    /// auto-death). In-memory only; re-derived/reset to 0 at boot (the boot
    /// path restarts saturation tracking at Normal), so zero byte-format risk.
    pub(crate) saturated_consecutive_cycles: u64,
    /// **P11.c P02-refusal debounce** — consecutive cycles in which ANY cost
    /// axis exceeded its budget (incremented every exhausted cycle regardless of
    /// saturation stage; reset to 0 on the first within-budget cycle). The
    /// pre-eligibility P02 refusal gates on this being ≥
    /// `P02_REFUSAL_SUSTAINED_CYCLES` so a single transient compute SPIKE (one
    /// slow Python cycle can exceed the 100ms seed compute budget) does NOT
    /// refuse intake — only genuinely SUSTAINED exhaustion does (L2/OBSERVABILITY
    /// §3 "spikes DAG-recorded but do not fire"). In-memory only (zero byte risk).
    pub(crate) consecutive_budget_exhausted_cycles: u64,
    /// **P11.c**: cooldown for the metabolic-saturation self-euthanasia
    /// proposal — `Some(cycle)` of the last emission, reset to `None` on
    /// return to `Normal` so a fresh saturation episode can re-propose.
    /// In-memory only (zero byte-format risk).
    pub(crate) last_saturation_mortality_proposal_at_cycle: Option<u64>,
    /// **M26.4 F20**: owner-declared objective for P14.c telos_alignment.
    /// `None` → substrate falls back to L1/TROPISM §F.1 branch-2 (centroid
    /// over recent trajectory deltas). CI-mutable via
    /// `mutation_type="owner_objective_declaration"`.
    pub(crate) owner_objective: Option<crate::events::OwnerObjective>,
    /// **M26.4 P14.c**: cooldown tracking for telos drift emission. Same
    /// 100-cycle cooldown as M25.1/M25.2 detectors to prevent spam on every
    /// observatory query.
    pub(crate) last_telos_drift_emitted_at_cycle: Option<u64>,
    /// **CHAR07 §8.3 C71**: cooldown for the `sycophancy_indicator_elevated`
    /// daily signal. Same 100-cycle cooldown as the other detectors so a
    /// sustained-zero-disagreement stretch emits at most once per window
    /// rather than every cycle. In-memory only (re-derived at boot).
    pub(crate) last_char07_sycophancy_emitted_at_cycle: Option<u64>,
    /// **M26.4 P11.c**: track recent `budget_exhausted:{axis}` emissions per
    /// axis to drive C53 (budget_exhausted_silent) detection. Key = axis
    /// name; value = cycle of most recent emission.
    pub(crate) last_budget_exhausted_per_axis: std::collections::HashMap<String, u64>,
    /// **v3.1.1 P07 §3.1 + F26**: registry of 应朽 detection
    /// rules. Open-ended per P07 §3.1.c (L1 may register additional family
    /// members without L0 amendment). The prune-scan deep-cycle step in
    /// `handle_advance` iterates this registry every
    /// `PRUNE_SCAN_DEEP_CYCLE_INTERVAL` cycles and emits one
    /// `internal_mortality_event:{category}` tombstone per detected
    /// candidate (P07 §3.3).
    pub(crate) prune_registry: crate::prune::PruneRuleRegistry,
    /// **v3.1.1 C54 hoarding_indicator cooldown**: track the cycle at
    /// which the substrate last emitted C54 to prevent per-cycle spam on
    /// the same hoarding episode. Same 100-cycle cooldown discipline as
    /// other M25 / M26 detectors. `None` = never emitted.
    pub(crate) last_hoarding_indicator_emitted_at_cycle: Option<u64>,
    /// **v3.1.1 Sprint 2.C — L1/SKIN §8**: cached projection of the latest
    /// `backup_encryption_status_declared:{status}` DAG event's status
    /// field. `None` = "unspecified" per L1/SKIN §8 → triggers
    /// `backup_encryption_undeclared` Daily sporocarp on boot. Valid
    /// non-None values: "encrypted_externally" / "cultivator_declined_explicit"
    /// (per `events::BACKUP_ENCRYPTION_STATUS_VALID_VALUES`). Re-derived
    /// from DAG on every boot — DAG is canonical, this field is cache.
    pub(crate) backup_encryption_status: Option<String>,
    /// **v3.1.1 Sprint 5.E (T2.3)**: at-most-once-per-boot flag for the
    /// `C60_python_worker_unexpected_exit` immune sporocarp. Set to true
    /// after the autonomous-tick liveness check detects child death; gates
    /// further emissions until the substrate restarts. Without this gate,
    /// every tick after Python death would re-emit C60, spamming the DAG.
    pub(crate) python_worker_death_logged: bool,
    /// **v3.1.1 Sprint 5.F (T2.4)**: per-detector immune-emission rate limit
    /// state. Maps `detector_id` to `(last_emission_unix_ns,
    /// last_emitted_hash, suppression_count)`. The
    /// `emit_immune_sporocarp` helper checks this map on every call:
    /// if a same-detector emission occurred within
    /// `IMMUNE_EMISSION_RATE_LIMIT_MS` ago, the new call is suppressed
    /// (DAG not mutated) and the cached hash is returned. The
    /// suppression count is exposed in the observatory digest so the
    /// operator can detect attempted DoS without the DAG getting
    /// pathologically large.
    pub(crate) immune_emission_state:
        std::collections::HashMap<String, (i64, myco_kernel_shared::crypto::NodeHash, u64)>,
    /// **v3.1.1 Sprint 8.G (P03 §10.4)**: the single in-flight schema
    /// migration candidate, if any. `Some` between a `schema_migration_started`
    /// emission and the terminal commit/rollback. The MVP allows exactly ONE
    /// in flight at a time — `attestation::handle_submit_mutation` rejects a
    /// second migration while this is `Some`. Hydrated at boot from
    /// `DerivedState::migration_candidate` (which round-trips via snapshot.cb +
    /// is re-derivable from the schema_migration_started/terminal DAG events),
    /// so a substrate restarted mid-window resumes the migration.
    pub(crate) migration_candidate: Option<myco_kernel_schema::migration::CandidateState>,
    /// **v3.1.1 Sprint 8.G**: cooldown tracking for the C66
    /// `schema_migration_window_exceeded` immune emission. Stores
    /// `manifest.cycle_counter` at the most recent C66 emission; the
    /// autonomous tick suppresses re-emission within
    /// `C66_WINDOW_EXCEEDED_COOLDOWN_CYCLES`. Same per-detector cooldown
    /// discipline as the C54/C63/C64/C65 detectors. `None` = never emitted.
    pub(crate) last_migration_window_exceeded_emitted_at_cycle: Option<u64>,
    /// **COV06 §3.2.A (F21)** — the cultivation_successor_chain, mirrored from
    /// `DerivedState::successor_chain`. Hydrated at boot from a full DAG
    /// re-derivation (NOT snapshot.cb — byte-compat additive). The succession
    /// FSM derivation (`crate::cultivation::current_cultivation_state`) reads the
    /// DAG directly; this mirror lets handlers validate non-overlap / monotone
    /// `valid_from` without re-walking the DAG on every append.
    pub(crate) successor_chain: Vec<crate::derived_state::DerivedSuccessorEntry>,
    /// **COV06 §3.2.C** — active succession config (cadence + windows + terminal
    /// choice), mirrored from `DerivedState::succession_config`. `None` → the
    /// built-in defaults (cadence 30d, legacy 365d, terminal 730d, choice
    /// `indefinite_orphan`) overlaid with `MYCO_TEST_*` env overrides.
    pub(crate) succession_config: Option<crate::derived_state::DerivedSuccessionConfig>,
    /// **COV06** — latest recorded cultivator heartbeat, mirrored from
    /// `DerivedState::latest_heartbeat`. The autonomous-tick staleness watchdog
    /// measures `now_anchor - anchor_timestamp_unix_ns` against the cadence.
    pub(crate) latest_heartbeat: Option<crate::derived_state::DerivedLatestHeartbeat>,
    /// **COV06 (efficiency)** — memoized cultivation-succession FSM state. The
    /// derivation (`crate::cultivation::current_cultivation_state`) is an
    /// unbounded full-DAG walk; reads happen on every ADVANCE (the `is_archived`
    /// metabolism guard) and every autonomous tick, while the underlying state
    /// only changes when a cultivation-FAMILY event is emitted (heartbeats are
    /// unprunable, so the walk grows monotonically). This cache mirrors the
    /// `latest_heartbeat`/`successor_chain` pattern: it is recomputed (one walk)
    /// at the centralized emit point [`emit_substrate_event`] whenever a
    /// cultivation-family node is appended, and hydrated once at boot. Hot reads
    /// go through [`ServerState::cultivation_state`] (O(1)).
    pub(crate) cultivation_state: crate::cultivation::CultivationState,
    /// **COV06 T1** — cooldown tracking for the `cultivator_heartbeat_stale`
    /// emission. Stores `cycle_counter` at the most recent T1 emission; the
    /// autonomous tick suppresses re-emission within `COV06_STALE_COOLDOWN_CYCLES`
    /// (100, same discipline as C54/C66). `None` = never emitted.
    pub(crate) last_cultivator_heartbeat_stale_emitted_at_cycle: Option<u64>,
    /// **COV06 T4** — cooldown tracking for the `cultivation_orphaned` emission.
    /// `None` = never emitted. (cultivation_orphaned is itself un-suppressible —
    /// the cooldown only prevents per-cycle DAG spam of the SAME orphan episode,
    /// not the orphan transition itself.)
    pub(crate) last_cultivation_orphaned_emitted_at_cycle: Option<u64>,
    /// **COV06 T6/T7** — cooldown tracking for the terminal-window emission
    /// (`self_euthanasia_proposal:cultivation_orphaned_terminal` OR the
    /// `bet_retired_proposal` archive seal). `None` = never emitted.
    pub(crate) last_cultivation_terminal_emitted_at_cycle: Option<u64>,
}

impl ServerState {
    // `pub(crate)` (was private): lets same-crate unit tests — e.g.
    // `prune::tests` exercising `count_prune_resurrections` — construct an
    // in-memory `ServerState` from discrete identity fields + a `Dag`.
    //
    // **Task #8i**: takes the five discrete substrate-identity / metabolic-
    // position values directly (no `Manifest`). `substrate_id` / `genesis_time`
    // are `Option` — `None` is the pre-genesis sentinel that the accessors map
    // back to `[0u8;32]` / `0`. The DAG-first boot arm passes `derived`'s
    // already-`Option` fields verbatim; the legacy arm passes the inverse
    // sentinel mapping of a loaded/genesis `Manifest`.
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn new(
        state_dir: PathBuf,
        substrate_id: Option<[u8; 32]>,
        genesis_time_unix_ns: Option<i64>,
        cycle_counter: u64,
        last_absorbed_cycle: Option<u64>,
        generation_depth: u64,
        dag: Dag,
        pinned_operator_identity: Option<PinnedOperatorIdentity>,
        substrate_signing_seed: [u8; 32],
    ) -> Self {
        // M7: `cycle_counter` is the authoritative persisted counter; the
        // in-process CycleEngine maintains its own counter that counts cycles
        // within THIS process only. handle_advance() uses this field as the
        // cross-process source-of-truth.
        // M8: dag carries the substrate's causal history (sporocarps + future event types).
        // M9: pinned_operator_identity is the TOFU-pinned operator pubkey;
        //     None pre-first-hello.
        // M25.0: substrate_signing_seed is the substrate-private Ed25519 seed,
        //     loaded or genesis-generated by `boot_or_genesis_substrate_signing_key`.
        // M26.2 P11.b: seed CostAccumulator with current on-disk file sizes
        // so the FIRST cycle's signal_9 is the delta from boot-time, not a
        // misleading "all bytes are new". MUST capture state_dir BEFORE the
        // struct literal because state_dir is moved into the struct.
        let cost_accumulator = crate::observatory::CostAccumulator::new(&state_dir);
        ServerState {
            session_secret: [0u8; 32],
            handshake_complete: false,
            python_client: None,
            cycle_engine: CycleEngine::new(CycleConfig::default()),
            // Task #8i discrete identity / metabolic-position fields (params
            // shadow the fields → struct-shorthand binds each by name).
            substrate_id,
            genesis_time_unix_ns,
            cycle_counter,
            last_absorbed_cycle,
            generation_depth,
            state_dir,
            dag,
            pinned_operator_identity,
            nonce_log: std::collections::HashMap::new(),
            // M26.1 C5 SECURITY FIX: read `MYCO_ACCEPT_LEGACY_PEERS` env var at
            // construction. Default policy (env unset) rejects legacy FED_HELLOs;
            // override is for transition-period compatibility with pre-M25 peers.
            // See `FederationState::new_with_env_policy`.
            federation: crate::federation::FederationState::new_with_env_policy(),
            // C13: empty at construction; the boot path re-derives it from the
            // full DAG AFTER `new()` (mirrors backup_encryption_status +
            // cultivation mirrors). NOT persisted separately — DAG is canonical.
            revoked_federation_peers: std::collections::HashSet::new(),
            // F23/C50: empty + unfrozen at construction; the boot path
            // re-derives both from the full DAG AFTER `new()` (mirrors
            // revoked_federation_peers). NOT persisted separately — DAG is
            // canonical. A genesis substrate with no duress registration leaves
            // these inert, so non-duress mutations are byte-unaffected.
            duress_pubkeys: std::collections::HashSet::new(),
            duress_freeze_active: false,
            substrate_signing_seed,
            observatory_history: std::collections::VecDeque::new(),
            last_operator_context_window_bytes: None,
            last_doctrine_burst_emitted_at_cycle: None,
            last_bet_weakening_quorum_emitted_at_cycle: None,
            cost_accumulator,
            // M26.4 seed defaults — F19 budgets + F20 objective + P11.c
            // state machine. Boot path will later replay
            // `substrate_saturated`/`substrate_normal_restored` events to
            // restore the runtime saturation_stage (M26.4 minimum: start at
            // Normal on every boot; sustained-saturation tracking restarts).
            //
            // **v3.1.1 Sprint 5.D**: `MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53`
            // env var (test-only) tightens budgets to 1 unit each so every
            // cycle exhausts them. Used to exercise the P11.c emission +
            // SaturationStage transition pipeline + C53 silent-breach
            // detector under deterministic conditions. Production must not
            // set this variable.
            cost_budgets: if std::env::var("MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53")
                .map(|v| matches!(v.trim().to_ascii_lowercase().as_str(), "1" | "true"))
                .unwrap_or(false)
            {
                crate::events::CostBudgets {
                    compute_ns_per_cycle: 1,
                    network_bytes_per_cycle: 1,
                    storage_bytes_per_cycle: 1,
                    // Also tighten cycle-floor + saturation-threshold so the
                    // P11.c stage machine reaches `substrate_saturated`
                    // within a handful of cycles (vs. 1000+ at seed values).
                    // This lets tests exercise the full stage-transition
                    // pipeline without long-running cycle loops.
                    pre_eligibility_cycle_floor: 1,
                    sustained_saturation_cycle_threshold: 2,
                    // Tight stage-3 escalation: a few cycles past Saturated and
                    // the substrate proposes metabolic-saturation euthanasia, so
                    // tests can witness the escalation without 1000+ cycles.
                    sustained_saturation_mortality_cycle_threshold: 3,
                }
            } else {
                crate::events::seed_cost_budgets()
            },
            saturation_stage: crate::events::SaturationStage::Normal,
            post_eligibility_consecutive_cycles: 0,
            saturated_consecutive_cycles: 0,
            consecutive_budget_exhausted_cycles: 0,
            last_saturation_mortality_proposal_at_cycle: None,
            owner_objective: crate::events::seed_owner_objective(),
            last_telos_drift_emitted_at_cycle: None,
            last_char07_sycophancy_emitted_at_cycle: None,
            last_budget_exhausted_per_axis: std::collections::HashMap::new(),
            // v3.1.1 P07: seed the prune registry with the L0 proof-of-
            // mechanism rule. L1 may register additional rules at runtime.
            prune_registry: crate::prune::PruneRuleRegistry::seed(),
            last_hoarding_indicator_emitted_at_cycle: None,
            // v3.1.1 Sprint 2.C: backup-encryption status starts None
            // ("unspecified"). Cultivator MAY set via CI mutation; on every
            // boot we re-derive from DAG (see `derive_backup_encryption_status`
            // in attestation.rs) and override this seed if any DAG event
            // is present.
            backup_encryption_status: None,
            // v3.1.1 Sprint 5.E: Python-worker death flag starts cleared.
            // Set to true the first time autonomous_tick detects child exit.
            python_worker_death_logged: false,
            // v3.1.1 Sprint 5.F: per-detector immune-emission rate-limit
            // tracking starts empty. Populated lazily on first emission per
            // detector_id; reset on substrate restart (rate-limit window is
            // wall-clock, not cycle-counter, so this is safe).
            immune_emission_state: std::collections::HashMap::new(),
            // v3.1.1 Sprint 8.G: no migration in flight at construction. The
            // boot path hydrates this from DerivedState::migration_candidate
            // AFTER `new()` (mirrors observatory_history), so a substrate
            // restarted mid-window resumes its migration.
            migration_candidate: None,
            last_migration_window_exceeded_emitted_at_cycle: None,
            // COV06: cultivation FSM mirrors start empty; the boot path
            // re-derives them from the full DAG AFTER `new()` (mirrors
            // observatory_history + migration_candidate). NOT persisted in
            // snapshot.cb (byte-compat additive — no format bump).
            successor_chain: Vec::new(),
            succession_config: None,
            latest_heartbeat: None,
            // Genesis default; boot hydrates this from the full-DAG re-derivation
            // and `emit_substrate_event` keeps it current thereafter.
            cultivation_state: crate::cultivation::CultivationState::Normal,
            last_cultivator_heartbeat_stale_emitted_at_cycle: None,
            last_cultivation_orphaned_emitted_at_cycle: None,
            last_cultivation_terminal_emitted_at_cycle: None,
        }
    }

    // ----------------------------------------------------------------------
    // Task #8i — discrete substrate-identity / metabolic-position accessors.
    //
    // These replace the former live `manifest: Manifest` in-memory mirror.
    // The five CONSUMED manifest fields now live as discrete fields directly
    // on `ServerState` (single source of truth; no redundant Manifest copy).
    // The two Option-returning identity accessors reproduce the sentinel
    // mapping of the now-removed `DerivedState::to_legacy_manifest` VERBATIM
    // (substrate_id None → [0u8;32]; genesis_time None → 0) so every hashed /
    // wire byte that previously read `state.manifest.<field>` stays
    // byte-identical. The mapping byte-exactness is the one correctness-
    // critical invariant: a skew would change genesis_event / snapshot /
    // witness bytes and break the v3.1.1.1 seal.

    /// 32-byte substrate identifier, sentinel-mapped (`None` → `[0u8;32]`).
    /// Byte-exact replacement for the former `state.manifest.substrate_id`.
    /// Mirrors the now-removed `DerivedState::to_legacy_manifest` mapping.
    pub(crate) fn substrate_id(&self) -> [u8; 32] {
        self.substrate_id.unwrap_or([0u8; 32])
    }

    /// **COV06 (efficiency)** — O(1) read of the memoized cultivation-succession
    /// FSM state. Equivalent to `crate::cultivation::current_cultivation_state(self)`
    /// but without the full-DAG walk; the value is maintained at the centralized
    /// `emit_substrate_event` point + hydrated at boot. Use this on hot paths
    /// (the ADVANCE/tick metabolism guard); the pure walk remains available for
    /// unit tests that build a DAG directly.
    pub(crate) fn cultivation_state(&self) -> crate::cultivation::CultivationState {
        self.cultivation_state
    }

    /// Genesis wall-clock time (ns), sentinel-mapped (`None` → `0`).
    /// Byte-exact replacement for the former `state.manifest.genesis_time_unix_ns`.
    pub(crate) fn genesis_time_unix_ns(&self) -> i64 {
        self.genesis_time_unix_ns.unwrap_or(0)
    }

    /// Authoritative metabolic-cycle counter.
    pub(crate) fn cycle_counter(&self) -> u64 {
        self.cycle_counter
    }

    /// Highest absorbed cycle (M18); `None` = no absorption yet.
    pub(crate) fn last_absorbed_cycle(&self) -> Option<u64> {
        self.last_absorbed_cycle
    }

    /// Lineage depth (8f / §16.A); root = 0.
    pub(crate) fn generation_depth(&self) -> u64 {
        self.generation_depth
    }

    /// Advance the authoritative metabolic-cycle counter (dispatch / autonomous
    /// tick bookkeeping). Replaces the former `state.manifest.cycle_counter = …`.
    pub(crate) fn set_cycle_counter(&mut self, cycle: u64) {
        self.cycle_counter = cycle;
    }

    /// Record the highest absorbed cycle after an absorption_event.
    /// Replaces the former `state.manifest.last_absorbed_cycle = …`.
    pub(crate) fn set_last_absorbed_cycle(&mut self, cycle: Option<u64>) {
        self.last_absorbed_cycle = cycle;
    }

    /// M25.0 + M25.4: return the substrate's own Ed25519 public key (32 bytes),
    /// derived from `substrate_signing_seed`. The pubkey appears on the wire
    /// (snapshot wrapper + FED_HELLO signed payload); the private seed never does.
    ///
    /// Currently only used by tests; the runtime derives the pubkey inline
    /// at each emission site (cheap; avoids cloning the seed for borrow).
    #[allow(dead_code)]
    fn substrate_signing_pubkey(&self) -> [u8; 32] {
        use myco_kernel_shared::crypto::Ed25519PrivateKey;
        Ed25519PrivateKey::from_seed(&self.substrate_signing_seed)
            .public_key()
            .0
    }

    /// M21.4 P5 万物互联: manifest persistence is now NO-OP.
    /// Manifest fields (substrate_id / genesis_time / cycle_counter /
    /// last_absorbed_cycle) are derived from DAG events on boot. The
    /// legacy `manifest.cb` file is no longer written.
    ///
    /// Kept as a function for call-site stability.
    #[allow(clippy::unnecessary_wraps)]
    pub(crate) fn save_manifest(&mut self) -> Result<(), SubstrateError> {
        // M21.4: no-op. Manifest fields are event-sourced via DAG.
        Ok(())
    }

    /// State directory as a string (for forwarding to the Python worker).
    /// M21.4: retained for sprout_child Python-side gradient snapshot path.
    #[allow(dead_code)]
    fn state_dir_str(&self) -> String {
        self.state_dir.to_string_lossy().into_owned()
    }
}

// ---------------------------------------------------------------------------
// Public server entry point.
// ---------------------------------------------------------------------------

/// Run the substrate server loop against the given stdin/stdout.
///
/// Resolves the state directory (per `MYCO_STATE_DIR` env var or default),
/// loads the manifest if one exists (cold-resume), or generates a fresh
/// genesis manifest. The Python worker is hydrated from `gradient.cb` (if
/// present) during the hello-handshake forwarding.
///
/// Returns the exit code (0 = clean shutdown, 2 = handshake failure).
///
/// M23.1 P4 永恒迭代: the loop is now **autonomous**. A dedicated stdin reader
/// thread reads operator frames in the background and ships them to the main
/// loop via an `mpsc::Sender<FrameMsg>`. The main loop uses
/// `recv_timeout(MYCO_TICK_INTERVAL_MS)` so that — when no operator frame is
/// pending — the substrate uses the idle slice to do federation work
/// (`do_autonomous_tick`) without operator intervention. This is the moment
/// the substrate stops being purely reactive: it ticks under its own clock.
pub fn run_loop() -> Result<u8, SubstrateError> {
    use crate::derived_state::DerivedState;
    use std::sync::mpsc;

    let state_dir = default_state_dir();
    ensure_state_dir(&state_dir)?;

    // M21.2 P5 万物互联: DAG-first boot.
    //
    // 1. Load DAG (authoritative substrate event log).
    // 2. Derive substrate state via DerivedState::from_dag.
    // 3. If derived has substrate_id (genesis_event present), USE DERIVED
    //    STATE for ServerState fields. State files become regenerable caches.
    // 4. If DAG is empty or pre-M21 (no genesis_event), fall back to state
    //    file loading (legacy compat). Auto-emit genesis_event for legacy
    //    substrate to migrate forward.
    //
    // This is the moment the DAG becomes Rust-side authoritative. State files
    // are still written (M21.4 will remove them); they're no longer read.

    // M11: C7 dag_retro_edit_detected — quarantine corrupted dag.cb.
    let (dag, dag_load_failure_evidence): (Dag, Option<String>) = match load_dag(&state_dir) {
        Ok(Some(d)) => (d, None),
        Ok(None) => (Dag::default(), None),
        Err(e) => {
            let dag_path = state_dir.join("dag.cb");
            let quarantine_path = state_dir.join(format!(
                "dag.cb.quarantined_{}",
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_secs())
                    .unwrap_or(0)
            ));
            let _ = std::fs::rename(&dag_path, &quarantine_path);
            (
                Dag::default(),
                Some(format!(
                    "dag.cb load failed ({e}); quarantined to {}",
                    quarantine_path.display()
                )),
            )
        }
    };

    // M25.0: load (or genesis) the substrate's private signing seed BEFORE
    // attempting to load snapshot.cb. The seed lets us verify that the
    // on-disk snapshot was signed by THIS substrate (not a forged one) — the
    // snapshot's embedded signer_pubkey must match the pubkey derived from
    // our own seed, AND the signature must verify over the payload bytes.
    //
    // M26.1 C6 SECURITY FIX: also probe the on-disk permission posture of the
    // seed file. If it was loose (Unix mode allowed group/world access), we
    // tighten in-place immediately AND queue a C4_substrate_secret_unsealed
    // immune sporocarp to emit once `state` is constructed (DAG handle lives
    // inside ServerState, so emission happens after `new()` returns).
    let (substrate_signing_seed, signing_key_was_restrictive) =
        crate::persistence::boot_or_genesis_substrate_signing_key_with_permission_status(
            &state_dir,
        )?;
    if !signing_key_was_restrictive {
        // M26.1 C6: tighten in-place so the gap doesn't widen. Best-effort —
        // a failure here is logged but does NOT abort boot (substrate remains
        // functional; the C4 sporocarp emitted below records the breach).
        let _ = crate::persistence::tighten_substrate_signing_key_permissions(&state_dir);
    }
    let substrate_signing_pubkey = {
        use myco_kernel_shared::crypto::Ed25519PrivateKey;
        Ed25519PrivateKey::from_seed(&substrate_signing_seed)
            .public_key()
            .0
    };

    // M21.5 P5 万物互联 + M25.0: try to load snapshot.cb first. If present +
    // (signature verifies against our own pubkey) + (snapshot's recorded tip
    // is in the DAG) → use it as the starting state + replay only events
    // newer than that tip. This avoids full DAG replay on large substrates.
    //
    // Fallback (snapshot missing / corrupted / signature invalid / signer
    // pubkey mismatch / stale tip): full DAG replay (correctness preserved;
    // snapshot is purely an optimization). M25.0 specifically defends against
    // cross-substrate forgery: copying substrate A's snapshot.cb into
    // substrate B's state_dir fails the signer-pubkey check at B's boot.
    let mut snapshot_rejection_evidence: Option<String> = None;
    // `mut`: COV06 re-derives cultivation FSM state onto `derived` after boot
    // (rederive_cultivation_from_dag) before mirroring onto ServerState.
    let mut derived = {
        let loaded = crate::persistence::load_snapshot(&state_dir).ok().flatten();
        let from_snapshot = match loaded {
            Some(snap) => {
                // M25.0 step 1: signer pubkey must match our own — otherwise
                // some other substrate wrote this snapshot (or it was forged).
                if snap.signer_pubkey != substrate_signing_pubkey {
                    snapshot_rejection_evidence = Some(format!(
                        "snapshot.cb signer_pubkey {} != substrate signing pubkey {} \
                         (snapshot was signed by a different substrate; rejected)",
                        hex_first_8_bytes(&snap.signer_pubkey),
                        hex_first_8_bytes(&substrate_signing_pubkey),
                    ));
                    None
                } else if let Err(e) = myco_kernel_shared::crypto::verify_signature(
                    &snap.signer_pubkey,
                    &snap.signature,
                    &snap.payload,
                ) {
                    // M25.0 step 2: signature must verify over the payload.
                    snapshot_rejection_evidence = Some(format!(
                        "snapshot.cb signature failed verification: {e} (rejected)"
                    ));
                    None
                } else {
                    // Signature OK — decode payload and proceed with M21.5
                    // tip-in-DAG check.
                    match DerivedState::from_canonical_bytes(&snap.payload) {
                        Ok(Some((mut state_from_snap, snap_tip))) => {
                            let snap_tip_in_dag = match snap_tip {
                                None => dag.node_count() == 0,
                                Some(tip_arr) => {
                                    let nh = myco_kernel_shared::crypto::NodeHash::from_bytes(
                                        tip_arr,
                                    );
                                    dag.get(&nh).is_some()
                                }
                            };
                            if snap_tip_in_dag {
                                let replay_result = replay_events_after_tip(
                                    &mut state_from_snap,
                                    &dag,
                                    snap_tip.as_ref(),
                                );
                                match replay_result {
                                    Ok(()) => Some(state_from_snap),
                                    Err(_) => None,
                                }
                            } else {
                                None
                            }
                        }
                        _ => None,
                    }
                }
            }
            None => None,
        };
        from_snapshot.unwrap_or_else(|| {
            DerivedState::from_dag(&dag).unwrap_or_else(|_| DerivedState::empty())
        })
    };

    // Determine boot mode:
    //  - "dag-first" (M21.2+): derived.is_post_m21_substrate() == true
    //  - "legacy" (pre-M21.1): fall back to state file loading
    //  - "fresh genesis" (no prior state at all): create new
    let boot_from_dag = derived.is_post_m21_substrate();
    // **Task #8i**: boot now yields the five DISCRETE identity / metabolic-
    // position values (not a `Manifest`). The DAG-first arm copies `derived`'s
    // already-`Option` identity fields verbatim (no sentinel round-trip); the
    // legacy arm derives them from a loaded/genesis `Manifest` via the inverse
    // sentinel mapping (`[0u8;32]` → `None`, `0` → `None`) so the auto-emitted
    // genesis_event stays byte-identical to the pre-#8i path.
    #[allow(clippy::type_complexity)]
    let (
        boot_substrate_id,
        boot_genesis_time_unix_ns,
        boot_cycle_counter,
        boot_last_absorbed_cycle,
        boot_generation_depth,
        pinned_operator_identity,
        nonce_log_entries,
        is_fresh_genesis,
    ): (
        Option<[u8; 32]>,
        Option<i64>,
        u64,
        Option<u64>,
        u64,
        Option<crate::persistence::PinnedOperatorIdentity>,
        Vec<crate::persistence::PersistedNonceEntry>,
        bool,
    ) = if boot_from_dag {
        // M21.2 derived-first path: state comes from DAG events. Copy the
        // identity / metabolic fields straight off `derived` (already `Option`
        // for substrate_id / genesis_time — no `to_legacy_manifest` needed).
        let pinned = derived.pinned_operator_identity.clone();
        // Convert DerivedNonce → PersistedNonceEntry for ServerState population.
        let nonces: Vec<crate::persistence::PersistedNonceEntry> = derived
            .nonce_log
            .values()
            .map(|n| crate::persistence::PersistedNonceEntry {
                nonce: n.nonce,
                bound_content_hash: n.bound_content_hash,
                bound_dag_tip: n.bound_dag_tip,
                substrate_issued_at_unix_ns: n.substrate_issued_at_unix_ns,
                expiry_unix_ns: n.expiry_unix_ns,
                anchor_clock_issued_at_unix_ns: n.anchor_clock_issued_at_unix_ns,
                anchor_clock_expiry_unix_ns: n.anchor_clock_expiry_unix_ns,
                consumed: n.consumed,
            })
            .collect();
        (
            // substrate_id / genesis_time are already Option on DerivedState —
            // copy verbatim (None iff no genesis_event seen yet).
            derived.substrate_id,
            derived.genesis_time_unix_ns,
            derived.cycle_counter,
            derived.last_absorbed_cycle,
            derived.generation_depth,
            pinned,
            nonces,
            false,
        )
    } else {
        // Legacy path: load from state files. **M26.3 C42 fix**: capture
        // manifest load failure instead of propagating, so we can emit
        // C42_manifest_cb_integrity_violation alongside boot continuation
        // (fresh genesis manifest). This way a corrupt manifest.cb is
        // observable in the substrate's immune DAG rather than silently
        // crashing the daemon at boot.
        let mut manifest_load_failure_evidence: Option<String> = None;
        let (m, fresh) = match Manifest::load(&state_dir) {
            Ok(Some(m)) => (m, false),
            Ok(None) => (Manifest::genesis(), true),
            Err(e) => {
                let manifest_path = state_dir.join("manifest.cb");
                let quarantine_path = state_dir.join(format!(
                    "manifest.cb.quarantined_{}",
                    std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .map(|d| d.as_secs())
                        .unwrap_or(0)
                ));
                let _ = std::fs::rename(&manifest_path, &quarantine_path);
                manifest_load_failure_evidence = Some(format!(
                    "manifest.cb load failed ({e}); quarantined to {}",
                    quarantine_path.display()
                ));
                (Manifest::genesis(), true)
            }
        };
        // Stash the failure evidence on a thread-local-ish side channel so we
        // can emit C42 once `state` is built (mirrors the dag.cb pattern).
        if let Some(ev) = manifest_load_failure_evidence.as_ref() {
            eprintln!("[boot] C42 manifest.cb integrity violation: {ev}");
        }
        // Push the evidence into a static path via a side-effect free way:
        // we re-derive on the way out by reading back the existence of the
        // quarantine file. Simpler: thread the Option<String> via a closure
        // — but in this branch we don't have access to `state` yet, so we
        // emit the immune sporocarp AFTER state construction below by
        // re-reading the quarantine evidence from disk-listing.
        // To avoid threading complexity through the existing match arms,
        // we use a thread-local Cell to carry the evidence forward.
        crate::server::manifest_failure_evidence::set(manifest_load_failure_evidence);
        let pinned = load_pinned_operator_identity(&state_dir)?;
        let now_for_prune = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .ok()
            .and_then(|d| i64::try_from(d.as_nanos()).ok())
            .unwrap_or(0);
        let entries = match load_nonce_log(&state_dir) {
            Ok(Some(entries)) => entries
                .into_iter()
                .filter(|e| !(e.consumed && now_for_prune > e.expiry_unix_ns))
                .collect::<Vec<_>>(),
            _ => Vec::new(),
        };
        // **Task #8i**: decompose the loaded/genesis `Manifest` into the five
        // discrete identity / metabolic-position values via the INVERSE sentinel
        // mapping (exact inverse of the removed `to_legacy_manifest`):
        //   substrate_id == [0u8;32]  ⇒ None
        //   genesis_time == 0         ⇒ None
        // so the genesis_event auto-emitted below (which reads
        // `state.substrate_id()` etc. = `field.unwrap_or(sentinel)`) is
        // byte-identical to the pre-#8i Manifest-mirror path. A fresh genesis
        // Manifest has a non-zero random id + non-zero genesis_time → both Some.
        let id_opt = if m.substrate_id == [0u8; 32] {
            None
        } else {
            Some(m.substrate_id)
        };
        let gtime_opt = if m.genesis_time_unix_ns == 0 {
            None
        } else {
            Some(m.genesis_time_unix_ns)
        };
        (
            id_opt,
            gtime_opt,
            m.cycle_counter,
            m.last_absorbed_cycle,
            m.generation_depth,
            pinned,
            entries,
            fresh,
        )
    };

    let mut state = ServerState::new(
        state_dir,
        boot_substrate_id,
        boot_genesis_time_unix_ns,
        boot_cycle_counter,
        boot_last_absorbed_cycle,
        boot_generation_depth,
        dag,
        pinned_operator_identity,
        substrate_signing_seed,
    );
    // M25.2: restore observatory history from snapshot.cb if the boot path
    // hydrated it onto `derived`. Fresh substrates / DAG-replay-only boots
    // start with an empty deque; the history then fills organically as
    // cycles tick. Cap is enforced on insert; we copy as-is here.
    state.observatory_history = derived.observatory_history.clone();
    // **v3.1.1 Sprint 8.G (P03 §10.4)**: resume an in-flight schema migration.
    // `derived.migration_candidate` is `Some` iff the DAG / snapshot carried a
    // `schema_migration_started:*` event without a matching terminal event.
    // We rebuild the `CandidateState` (always in the `Validating` phase while
    // outstanding) so the per-cycle dual-validation hook + the C66 window-
    // exceeded detector pick up exactly where they left off across a restart.
    if let Some(mc) = &derived.migration_candidate {
        let mut candidate = myco_kernel_schema::migration::CandidateState::new(
            mc.schema_diff_canonical_bytes.clone(),
            mc.op_name.clone(),
            mc.started_at_cycle,
            mc.dual_validation_window_cycles,
        );
        // Restore the original validation-window start cycle (and move into
        // Validating). `enter_validating` overwrites started_at_cycle with the
        // persisted value so window_complete / window_exceeded measure from the
        // true origin, not from the restart cycle.
        candidate.enter_validating(mc.started_at_cycle);
        state.migration_candidate = Some(candidate);
    }
    // **COV06** — re-derive the cultivation FSM state from the FULL DAG and
    // mirror it onto ServerState. These three fields are deliberately NOT in
    // snapshot.cb (byte-compat additive: no format_version bump), so a
    // snapshot-accelerated boot would otherwise miss cultivation events older
    // than the snapshot tip. The full-DAG re-derivation here is authoritative +
    // cheap (the cultivation event family is tiny). This makes cold-resume
    // reconstruct successor_chain / config / latest_heartbeat byte-identically.
    if let Err(e) = derived.rederive_cultivation_from_dag(&state.dag) {
        let _ = writeln!(
            std::io::stderr(),
            "COV06 cultivation re-derivation at boot failed: {e}"
        );
    }
    state.successor_chain = derived.successor_chain.clone();
    state.succession_config = derived.succession_config.clone();
    state.latest_heartbeat = derived.latest_heartbeat.clone();
    // Hydrate the memoized FSM cache once (one full-DAG walk at boot); thereafter
    // `emit_substrate_event` keeps it current on each cultivation-family emission.
    state.cultivation_state = crate::cultivation::current_cultivation_state(&state);
    for entry in nonce_log_entries {
        state.nonce_log.insert(
            entry.nonce,
            crate::attestation::AttestationNonce {
                nonce: entry.nonce,
                bound_content_hash: entry.bound_content_hash,
                bound_dag_tip: entry.bound_dag_tip,
                substrate_issued_at_unix_ns: entry.substrate_issued_at_unix_ns,
                expiry_unix_ns: entry.expiry_unix_ns,
                anchor_clock_issued_at_unix_ns: entry.anchor_clock_issued_at_unix_ns,
                anchor_clock_expiry_unix_ns: entry.anchor_clock_expiry_unix_ns,
                consumed: entry.consumed,
            },
        );
    }

    // M25.0: if snapshot.cb was rejected for signature mismatch or invalid
    // signature, surface as a C38 immune sporocarp so the operator can
    // investigate. The substrate continues running (snapshot is a cache;
    // DAG replay rebuilt state from authoritative source).
    if let Some(evidence) = snapshot_rejection_evidence {
        let _ = emit_immune_sporocarp(
            &mut state,
            "C38_snapshot_integrity_violation",
            "snapshot_integrity_violation",
            &evidence,
        );
        let _ = save_dag_state(&state);
    }

    // **v3.1.1 Sprint 2.C** — derive backup_encryption_status from DAG.
    //
    // L1/SKIN §8 puts backup-encryption-key custody outside the substrate
    // (cultivator generates locally; operator-runtime encrypts; substrate
    // only holds a public status pointer). The status SSoT lives in the DAG
    // as `backup_encryption_status_declared:{status}` events; we cache the
    // latest value on ServerState for fast access. Re-derived on every
    // boot — DAG is canonical, the cached field is just a projection.
    //
    // Daily-grade `backup_encryption_undeclared` signal emission is
    // DEFERRED to a later position in the boot sequence (after the M-anchor-2
    // genesis_event + birth_attestation block) so we don't accidentally
    // inflate `state.dag.node_count()` past the fresh-genesis guard at
    // line ~1006: `if is_fresh_genesis && state.dag.node_count() == 0`.
    state.backup_encryption_status =
        crate::events::derive_backup_encryption_status_from_dag(&state.dag);

    // **C13** — re-derive the revoked-federation-peer set from the DAG. Each
    // owner-attested `revoke_federation_peer` CI mutation emitted a
    // `federation_peer_revoked:{prefix}` event; the in-memory set is a pure
    // projection of those events (DAG is canonical). A substrate restarted
    // after revoking a peer thus continues to block egress to / ingest from
    // that peer. Mirrors `backup_encryption_status` above (DAG-derived, no new
    // on-disk format).
    state.revoked_federation_peers =
        crate::events::derive_revoked_federation_peers_from_dag(&state.dag);

    // **F23 / C50** — re-derive the registered-duress-pubkey set + the freeze
    // flag from the DAG. Each owner-attested `duress_keypair_registration` CI
    // mutation emitted a `duress_keypair_registered:{prefix}` event; the freeze
    // FSM is the last-writer over `coerced_owner_suspected` / `duress_cleared`.
    // Both are pure projections of the DAG (canonical), so a substrate
    // restarted after registering a duress key — or while frozen — resumes
    // exactly. Mirrors `revoked_federation_peers` above (DAG-derived, no new
    // on-disk format).
    state.duress_pubkeys = crate::events::derive_duress_pubkeys_from_dag(&state.dag);
    state.duress_freeze_active =
        crate::events::derive_duress_freeze_active_from_dag(&state.dag);

    // M26.1 C6 SECURITY FIX (Phase γ.2): substrate_signing_key.cb existed on
    // disk with loose Unix permissions (group/world bits set) — emit a
    // `C4_substrate_secret_unsealed` immune sporocarp on the DAG so the
    // breach is observable. We already tightened the file in-place above;
    // the sporocarp is the audit-trail record. This path is a no-op on the
    // genesis branch (fresh seed; file was written with 0600 from the start)
    // and on Windows (ACL inspection deferred to M-anchor-1).
    if !signing_key_was_restrictive {
        let evidence = format!(
            "substrate_signing_key.cb at {} had loose permissions on boot \
             (group/world bits set); tightened to 0600 in-place. M-anchor-1 \
             will replace file-permission defense with OS-sealed keystore.",
            state.state_dir.display()
        );
        let _ = emit_immune_sporocarp(
            &mut state,
            "C4_substrate_secret_unsealed",
            "substrate_secret_unsealed",
            &evidence,
        );
        let _ = save_dag_state(&state);
    }

    // If DAG load failed: emit BOTH C7 + **C41 (M26.3)** immune sporocarps
    // into the fresh DAG.
    //
    // - C7 dag_retro_edit_detected (L1/HARD_RULES §1.1) — Merkle DAG node
    //   hash mismatch on re-computation; covers the case where bytes parse
    //   but hashes don't reconstruct.
    // - **C41 dag_cb_integrity_violation (M26.3 L1/HARD_RULES §1.2)** —
    //   broader `dag.cb` file-level integrity check per L1/SCHEMA §2.1 + L0
    //   §9.4. Covers raw bytes corruption / decode failure / canonical-bytes
    //   format invalidity. Strict-superset of C7 for boot-time integrity.
    //
    // Pre-M26.3 emitted only C7 (semantically loose). M26.3 emits both so
    // the C41 doctrine row goes from `U` → `L` while preserving the existing
    // C7 emit contract that downstream tests assert.
    if let Some(evidence) = dag_load_failure_evidence {
        let _ = emit_immune_sporocarp(
            &mut state,
            "C7_dag_retro_edit_detected",
            "dag_retro_edit_detected",
            &evidence,
        );
        let _ = emit_immune_sporocarp(
            &mut state,
            "C41_dag_cb_integrity_violation",
            "dag_cb_integrity_violation",
            &evidence,
        );
        let _ = save_dag_state(&state);
    }

    // **M26.3 C42**: drain manifest.cb load failure evidence (if any was
    // recorded above in the legacy boot path) and emit
    // `C42_manifest_cb_integrity_violation`. Boot continues on a fresh genesis
    // manifest, so cycle_counter resets and substrate-ID will be regenerated
    // (the operator should treat this as substrate destruction + rebirth and
    // investigate the corrupted file in `.quarantined_*`).
    if let Some(evidence) = manifest_failure_evidence::take() {
        let _ = emit_immune_sporocarp(
            &mut state,
            "C42_manifest_cb_integrity_violation",
            "manifest_cb_integrity_violation",
            &evidence,
        );
        let _ = save_dag_state(&state);
    }

    // **M26.3 C52**: scan the DAG for `compression_event:*` nodes lacking a
    // `mutation:compression` parent. Every legitimate compression_event is
    // inserted DIRECTLY AFTER a mutation:compression DAG node (whose
    // canonical-bytes payload is the CompressionWitness). If a compression_event
    // exists without that immediate ancestry, the DAG has been tampered with
    // (or some other code path emitted compression_event without going through
    // submit_mutation CI gate) — emit C52 per L1/HARD_RULES §1.2.
    //
    // Implementation: walk the DAG; for each compression_event, look at its
    // parent_hashes; pull the parent node; check its node_type. If not
    // "mutation:compression" → C52.
    let c52_findings: Vec<String> = {
        let mut findings: Vec<String> = Vec::new();
        let nodes: Vec<_> = state.dag.iter_in_insertion_order().cloned().collect();
        for node in &nodes {
            if !node
                .node_type
                .starts_with(crate::events::NODE_TYPE_COMPRESSION_EVENT_PREFIX)
            {
                continue;
            }
            let parent_hashes = &node.parent_hashes;
            if parent_hashes.is_empty() {
                findings.push(format!(
                    "compression_event node_type={} has no parents — orphan compression",
                    node.node_type
                ));
                continue;
            }
            // A legitimate compression_event has exactly one parent: the
            // mutation:compression node. Check the FIRST parent (sufficient
            // because emitter always uses [tip] as parents).
            let parent_hash = &parent_hashes[0];
            let parent_opt = nodes
                .iter()
                .find(|n| n.hash.as_ref() == parent_hash.as_ref());
            let parent = match parent_opt {
                Some(p) => p,
                None => {
                    findings.push(format!(
                        "compression_event node_type={} parent hash not present in DAG",
                        node.node_type
                    ));
                    continue;
                }
            };
            if parent.node_type != "mutation:compression" {
                findings.push(format!(
                    "compression_event node_type={} parent is {} (expected mutation:compression)",
                    node.node_type, parent.node_type
                ));
            }
        }
        findings
    };
    for finding in c52_findings {
        let _ = emit_immune_sporocarp(
            &mut state,
            "C52_compression_uncattested",
            "compression_uncattested",
            &finding,
        );
        let _ = save_dag_state(&state);
    }

    // M21.2/M21.3: legacy-substrate auto-migration moved to handle_hello,
    // AFTER Python loads its gradient state. This way the migration can
    // back-fill BOTH genesis_event AND axis_registered events from Python's
    // already-loaded state, preserving M20 child substrate behavior (and
    // any other case where state files are authoritative + DAG is empty).
    let _ = is_fresh_genesis; // suppress unused-var warning when migration moved

    // M21.1 P5 万物互联: fresh substrate (no manifest.cb on disk) emits
    // genesis_event as the first DAG node. M21.2 generalizes this: any
    // substrate without a genesis_event in DAG gets one auto-emitted (the
    // legacy_migration branch above handles existing manifest.cb; this branch
    // handles truly fresh).
    if is_fresh_genesis && state.dag.node_count() == 0 {
        let event_node_type = crate::events::genesis_event_node_type(&state.substrate_id());
        // 8f / §16.A: a truly-fresh substrate stamps its lineage depth into
        // the genesis_event. Root substrate → 0 (field omitted, byte-compat);
        // a child birthed via the `MYCO_GENERATION_DEPTH_OVERRIDE` hook → that
        // depth. The canonical sprout path (`handle_sprout_child`) builds the
        // child's genesis_event directly with parent_depth + 1.
        let event_content = crate::events::encode_genesis_event(
            &state.substrate_id(),
            state.genesis_time_unix_ns(),
            state.generation_depth(),
        );
        let _ = emit_substrate_event(&mut state, event_node_type, event_content);
        let _ = save_dag_state(&state);

        // **M-anchor-2 §9.2.1 birth attestation emission**.
        //
        // If the operator process supplied a birth attestation via env vars,
        // emit it as a `birth_attestation:{substrate_id_prefix}` DAG node
        // RIGHT AFTER `genesis_event`. The three env vars must all be
        // present + valid hex; partial / malformed env vars are TOLERATED
        // (substrate boots without birth attestation, C20 will fire on
        // subsequent boots flagging the chain as broken).
        if let Some((attested_bytes, signature, owner_pubkey)) = read_birth_attestation_env_vars()
        {
            let now_unix_ns = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .ok()
                .and_then(|d| i64::try_from(d.as_nanos()).ok())
                .unwrap_or(0);
            let ba_node_type =
                crate::events::birth_attestation_node_type(&state.substrate_id());
            let ba_content = crate::events::encode_birth_attestation(
                &attested_bytes,
                &signature,
                &owner_pubkey,
                now_unix_ns,
            );
            let _ = emit_substrate_event(&mut state, ba_node_type, ba_content);
            let _ = save_dag_state(&state);
        }

        // **F23 / C50 — genesis duress-keypair registration emission.**
        //
        // If the operator process supplied owner-pre-attested duress
        // registrations via env vars, emit each as a
        // `duress_keypair_registered:{prefix}` DAG node right after the birth
        // attestation. Each body was signed off-line by the owner; we decode
        // it (extract pubkey + label), capture the owner signature + pubkey,
        // and emit the on-chain registration record — byte-identical to what
        // the CI-mutation accept path emits. A malformed/undecodable body is
        // skipped (the env parser already filters partial entries; a body that
        // does not decode under the registration domain is dropped here).
        //
        // We do NOT register a duress pubkey equal to the OWNER key: that would
        // make owner signatures verify under a "duress" key and silently
        // suppress legit mutations (the catastrophic mis-recognition). The same
        // guard is enforced on the CI-mutation registration path.
        //
        // At a TRULY-fresh genesis the operator identity is not yet TOFU-pinned
        // (`pinned_operator_identity` is None until the first hello), so we
        // compare against the env-supplied `owner_pubkey` — the key that signed
        // THIS registration — AND, when available (restart re-emit can't reach
        // here, but be defensive), the pinned identity.
        let pinned_owner_pubkey = state.pinned_operator_identity.as_ref().map(|p| p.pubkey);
        for (body, signature, owner_pubkey) in read_duress_registrations_env_vars() {
            let Some((duress_pubkey, label, anchor_ts)) =
                crate::events::decode_duress_keypair_registration(&body)
            else {
                continue;
            };
            if duress_pubkey == owner_pubkey || pinned_owner_pubkey == Some(duress_pubkey) {
                // Circular: a duress pubkey identical to the owner key is
                // refused (would silently suppress real owner mutations). This
                // is a genesis MISCONFIGURATION, not coercion — emit C5
                // attestation_invalid (matching the CI-mutation registration
                // guard in attestation.rs), NOT C50 (which would falsely signal
                // coercion at birth).
                let _ = emit_immune_sporocarp(
                    &mut state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "genesis duress registration refused: duress_pubkey equals the owner key (circular self-duress)",
                );
                continue;
            }
            // Verify the owner actually signed THIS registration body (the
            // CI-mutation path delegates this to Python; here we verify directly
            // since there is no Python round-trip at genesis). A typo'd / forged
            // env-var signature is refused rather than registering a bogus duress
            // key. The owner_pubkey is the operator's own genesis configuration
            // (same trust level as the birth attestation).
            if myco_kernel_shared::crypto::verify_signature(&owner_pubkey, &signature, &body)
                .is_err()
            {
                let _ = emit_immune_sporocarp(
                    &mut state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "genesis duress registration refused: owner signature over registration body failed to verify",
                );
                continue;
            }
            let nt = crate::events::duress_keypair_registered_node_type(&duress_pubkey);
            let content = crate::events::encode_duress_keypair_registered(
                &duress_pubkey,
                &label,
                anchor_ts,
                &signature,
                &owner_pubkey,
            );
            let _ = emit_substrate_event(&mut state, nt, content);
            let _ = save_dag_state(&state);
            state.duress_pubkeys.insert(duress_pubkey);
        }
    }

    // **v3.1.1 Sprint 2.C** — emit `backup_encryption_undeclared` Daily
    // signal NOW (post genesis_event + post birth_attestation) so the
    // fresh-genesis node-count guard above is not perturbed.
    //
    // Per L1/SKIN §9 detection table this is a **Daily-grade** signal —
    // visible but not breach-quarantine. Emit on a `daily_signal:*` prefix
    // so reproduction's quarantine scan (which keys on `immune:*`) does
    // NOT pull child substrates into birth-period quarantine for an
    // unresolved-by-cultivator soft signal on parent.
    if state.backup_encryption_status.is_none() {
        // **v3.1.1 Sprint 7.A fix**: emit at-most-once-per-substrate-lifetime.
        // The prior implementation re-emitted on every boot, which:
        //   1. Spammed the DAG with duplicate daily-grade signals per
        //      restart, and
        //   2. Broke the M8 "DAG persists across respawn" test in
        //      operators/claude/tests (one extra non-witness event per
        //      restart cycle).
        // Daily signals are meant to surface ONCE until cultivator declares
        // status; the operator dashboard can re-surface from DAG history
        // without the substrate re-emitting.
        let already_emitted = state.dag.iter_in_insertion_order().any(|n| {
            n.node_type == "daily_signal:backup_encryption_undeclared"
        });
        if !already_emitted {
            let evidence_str = "L1/SKIN §8: cultivator has not declared \
                 backup_encryption_status. Set via CI mutation \
                 `set_backup_encryption_status` with status one of \
                 {\"encrypted_externally\", \"cultivator_declined_explicit\"} \
                 so the absence of declaration becomes a positive choice rather \
                 than an unspecified default.";
            use std::time::{SystemTime, UNIX_EPOCH};
            let timestamp_unix_ns = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .ok()
                .and_then(|d| i64::try_from(d.as_nanos()).ok())
                .unwrap_or(0);
            let mut content_map = BTreeMap::new();
            content_map.insert(
                "detector_id".to_string(),
                Value::String("backup_encryption_undeclared".to_string()),
            );
            content_map.insert(
                "detector_name".to_string(),
                Value::String("backup_encryption_undeclared".to_string()),
            );
            content_map.insert(
                "evidence".to_string(),
                Value::String(evidence_str.to_string()),
            );
            content_map.insert("grade".to_string(), Value::String("daily".to_string()));
            content_map.insert(
                "timestamp_unix_ns".to_string(),
                Value::Timestamp(timestamp_unix_ns),
            );
            if let Ok(content) = cb_encode(&Value::Map(content_map)) {
                let _ = emit_substrate_event(
                    &mut state,
                    "daily_signal:backup_encryption_undeclared".to_string(),
                    content,
                );
                let _ = save_dag_state(&state);
            }
        }
    }

    // **M-anchor-2 §9.2.1 C20 boot-time verification**.
    //
    // On EVERY boot (not just fresh genesis), scan the DAG for the
    // birth_attestation event matching this substrate_id; verify its
    // signature against the embedded owner pubkey. Failure → C20
    // `genesis_attestation_chain_broken` immune sporocarp.
    //
    // Absence is observed too: if the substrate has run for ≥1 cycle and
    // no birth_attestation event is present, fire C20 with evidence
    // "birth_attestation missing" — this catches the case where the
    // genesis env vars were absent at first boot.
    {
        let expected_node_type =
            crate::events::birth_attestation_node_type(&state.substrate_id());
        let ba_node = state
            .dag
            .iter_in_insertion_order()
            .find(|n| n.node_type == expected_node_type)
            .cloned();
        let c20_evidence: Option<String> = match ba_node {
            None => {
                // Tolerate absence on truly-fresh substrates (cycle 0); only
                // fire if the substrate has lived past genesis without an
                // attestation having been emitted at any point.
                if state.cycle_counter() > 0 {
                    Some(format!(
                        "birth_attestation event missing for substrate_id={} (M-anchor-2 §9.2.1)",
                        hex_first_8_bytes(&state.substrate_id())
                    ))
                } else {
                    None
                }
            }
            Some(node) => {
                match crate::events::decode_birth_attestation(node.content_canonical_bytes.as_ref())
                {
                    None => Some(format!(
                        "birth_attestation decode failed for substrate_id={}",
                        hex_first_8_bytes(&state.substrate_id())
                    )),
                    Some((attested_bytes, signature, owner_pubkey)) => {
                        use myco_kernel_shared::crypto::verify_signature;
                        match verify_signature(&owner_pubkey, &signature, &attested_bytes) {
                            Ok(()) => None,
                            Err(e) => Some(format!(
                                "birth_attestation signature failed verify for \
                                 substrate_id={}: {e}",
                                hex_first_8_bytes(&state.substrate_id())
                            )),
                        }
                    }
                }
            }
        };
        if let Some(evidence) = c20_evidence {
            let _ = emit_immune_sporocarp(
                &mut state,
                "C20_genesis_attestation_chain_broken",
                "genesis_attestation_chain_broken",
                &evidence,
            );
            let _ = save_dag_state(&state);
        }
    }

    // M12: C9 cold_resume_invariant_failure — run comprehensive integrity
    // checks at boot. For each failing check, emit a C9 immune sporocarp.
    // The substrate continues running regardless; the immune events are an
    // audit trail for the operator to inspect.
    let integrity_results = crate::integrity::run_integrity_checks(&state);
    let mut any_failed = false;
    for result in &integrity_results {
        if !result.passed {
            any_failed = true;
            let evidence = format!(
                "boot-time integrity check failed: {} — {}",
                result.check_id, result.evidence
            );
            // M19 P9 皮肤: route check_id "canonical_bytes_render_drift" to
            // its dedicated C18 detector; all others go to C9.
            let (detector_id, detector_name) = if result.check_id == "canonical_bytes_render_drift"
            {
                (
                    "C18_canonical_bytes_render_drift",
                    "canonical_bytes_render_drift".to_string(),
                )
            } else if result.check_id == "substrate_state_orphan_detected" {
                (
                    "C32_substrate_state_orphan_detected",
                    "substrate_state_orphan_detected".to_string(),
                )
            } else {
                (
                    "C9_cold_resume_invariant_failure",
                    format!("cold_resume_invariant_failure ({})", result.check_id),
                )
            };
            let _ = emit_immune_sporocarp(&mut state, detector_id, &detector_name, &evidence);
        }
    }
    if any_failed {
        let _ = save_dag_state(&state);
    }

    // **P08 §3.5 I7(c) — child-boot birth closure (I3-first).**
    //
    // A child sprouted via `handle_sprout_child` carries a
    // `birth_closure_pending:*` marker in its DAG (written right after its
    // genesis_event by the parent). On the child's FIRST boot — i.e. when a
    // pending marker exists WITHOUT a later `birth_closure_complete:*` — the
    // child must run its OWN I3 self-validation as its first metabolic cycle
    // (L1/SCHEMA §3.3 step 2) BEFORE any operator cycle. We reuse the boot
    // integrity self-check just computed above (`integrity_results`); its
    // verdict (`i3_passed = !any_failed`) is the child's first-cycle I3 result.
    // The child then emits `birth_closure_complete:{child_prefix}` recording the
    // verdict. An I3 failure is ALSO a C34 birth-period violation (the C9
    // immune signals already fired in the loop above), surfacing that the child
    // failed its own birth self-validation.
    {
        let has_pending = state.dag.iter_in_insertion_order().any(|n| {
            n.node_type
                .starts_with(crate::events::NODE_TYPE_BIRTH_CLOSURE_PENDING_PREFIX)
        });
        let has_complete = state.dag.iter_in_insertion_order().any(|n| {
            n.node_type
                .starts_with(crate::events::NODE_TYPE_BIRTH_CLOSURE_COMPLETE_PREFIX)
        });
        if has_pending && !has_complete {
            let i3_passed = !any_failed;
            let child_id = state.substrate_id();
            let completed_at_unix_ns = crate::wall_clock::monotonic_unix_ns();
            let nt = crate::events::birth_closure_complete_node_type(&child_id);
            let content = crate::events::encode_birth_closure_complete(
                &child_id,
                i3_passed,
                completed_at_unix_ns,
            );
            let _ = emit_substrate_event(&mut state, nt, content);
            if !i3_passed {
                // I7(c) failure → C34 birth-period violation (the child's own
                // first-cycle I3 self-validation did not pass).
                let _ = emit_immune_sporocarp(
                    &mut state,
                    "C34_birth_period_violation_during_quarantine",
                    "birth_period_violation_detected",
                    &format!(
                        "child-boot I3 self-check FAILED at birth closure for \
                         substrate_id={} (P08 §3.5 step 2 / L1/SCHEMA §3.3): one or \
                         more boot integrity checks did not pass; see the C9/C18/C32 \
                         immune signals emitted this boot",
                        hex_first_8_bytes(&child_id)
                    ),
                );
            }
            let _ = save_dag_state(&state);
        }
    }

    // **M-anchor-4 §9.3.4**: emit invariant_witness:{check_id} DAG events
    // for each integrity check (regardless of pass/fail). The witnesses
    // give the owner raw inputs to re-derive each check's verdict
    // independently — substrate "does NOT emit pass/fail" per doctrine.
    let witnesses_emitted =
        crate::integrity::emit_invariant_witnesses(&mut state, &integrity_results);
    if witnesses_emitted > 0 {
        let _ = save_dag_state(&state);
    }

    // M23.1: spawn stdin reader thread. The reader thread blocks on
    // `read_frame(stdin)` and ships frames to the main loop via mpsc. The
    // main loop uses `recv_timeout(tick_interval)` so that idle periods
    // become autonomous-tick opportunities.
    let (frame_tx, frame_rx) = mpsc::channel::<FrameMsg>();
    let _reader_thread = std::thread::spawn(move || {
        let stdin = std::io::stdin();
        let mut stdin_lock = stdin.lock();
        loop {
            match read_frame(&mut stdin_lock) {
                Ok(Some(frame)) => {
                    if frame_tx.send(FrameMsg::Frame(frame)).is_err() {
                        return; // main loop dropped receiver
                    }
                }
                Ok(None) => {
                    // Clean EOF — drop tx; main loop sees Disconnected.
                    return;
                }
                Err(e) => {
                    let _ = frame_tx.send(FrameMsg::ReadError(format!("{e}")));
                    return;
                }
            }
        }
    });

    // Lock stdout for the main loop's writes.
    let stdout_handle = std::io::stdout();
    let mut stdout_guard = stdout_handle.lock();
    let stdout = &mut stdout_guard;

    // M23.1: parse tick interval from env (default 500ms = 2 ticks/sec).
    let tick_interval = parse_tick_interval();

    loop {
        let expected_key = if state.handshake_complete {
            state.session_secret
        } else {
            bootstrap_key()
        };

        // M23.1: receive next frame OR fire autonomous tick on timeout.
        let frame = match frame_rx.recv_timeout(tick_interval) {
            Ok(FrameMsg::Frame(f)) => f,
            Ok(FrameMsg::ReadError(msg)) => {
                graceful_shutdown_python(&mut state);
                return Err(SubstrateError::Io(std::io::Error::other(format!(
                    "stdin reader thread error: {msg}"
                ))));
            }
            Err(mpsc::RecvTimeoutError::Timeout) => {
                // Autonomous tick — do federation work iff handshake done +
                // listener open. Other ticks are no-ops (preserves the
                // pre-handshake / no-federation idle behavior of M22 and
                // earlier).
                if state.handshake_complete {
                    if let Err(e) = do_autonomous_tick(&mut state) {
                        // Non-fatal: log + continue (tick failures should
                        // never crash the substrate; they surface via DAG
                        // events emitted by the tick).
                        let _ = writeln!(std::io::stderr(), "autonomous tick error: {e}");
                    }
                }
                continue;
            }
            Err(mpsc::RecvTimeoutError::Disconnected) => {
                // stdin reader thread exited (clean EOF or error after
                // reporting). Treat as clean shutdown.
                graceful_shutdown_python(&mut state);
                return Ok(if state.handshake_complete { 0 } else { 2 });
            }
        };

        let request = match decode_frame_body(&frame, &expected_key) {
            Ok(msg) => msg,
            Err(BridgeError::HmacMismatch(msg)) => {
                // If pre-handshake, exit. If post, write error.
                if state.handshake_complete {
                    write_error_response(stdout, &state.session_secret, 0, "hmac_mismatch", &msg)?;
                    continue;
                }
                graceful_shutdown_python(&mut state);
                return Ok(2);
            }
            Err(e) => {
                if state.handshake_complete {
                    write_error_response(
                        stdout,
                        &state.session_secret,
                        0,
                        "protocol_error",
                        &e.to_string(),
                    )?;
                    continue;
                }
                graceful_shutdown_python(&mut state);
                return Ok(2);
            }
        };

        // Dispatch.
        let result = dispatch(&mut state, &request);
        match result {
            Ok(Some(response)) => {
                let frame = encode_frame_body(&response, &state.session_secret)
                    .map_err(SubstrateError::Bridge)?;
                write_frame(stdout, &frame).map_err(SubstrateError::Bridge)?;
                if request.message_type == msg_type::SHUTDOWN {
                    graceful_shutdown_python(&mut state);
                    return Ok(0);
                }
                // M23.2 P7 必朽: after a successful accept_self_euthanasia_proposal
                // we MUST shut down — the substrate has been authorized to die.
                // The response was just delivered (so the operator sees success).
                if request.message_type == msg_type::ACCEPT_SELF_EUTHANASIA_PROPOSAL {
                    graceful_shutdown_python(&mut state);
                    return Ok(0);
                }
                // **COV06 T7 / LB §4**: after a successful accept_bet_retired_proposal
                // the substrate is alive::archived — metabolism halts. The seal +
                // state_dir are preserved (cold-readable forensic); we exit cleanly.
                // A re-spawn re-derives Archived and the metabolism guard refuses
                // any cycle advance, so the archived substrate stays dormant.
                if request.message_type == msg_type::ACCEPT_BET_RETIRED_PROPOSAL {
                    graceful_shutdown_python(&mut state);
                    return Ok(0);
                }
            }
            Ok(None) => {
                // Handshake-only path: state was mutated but no response queued (currently unused).
            }
            Err(e) => {
                // M9: when a HELLO request fails (e.g., pubkey mismatch),
                // key the error envelope with the operator-provided
                // session_secret from the hello payload so the TS operator
                // can decode our rejection. Then EXIT — a rejected hello
                // means the session is poisoned; no point continuing.
                if request.message_type == msg_type::HELLO {
                    // M11: emit immune sporocarp for the rejected hello (C2 family).
                    // The DAG is loaded at boot time and will accept this insertion
                    // even pre-handshake. Save DAG before exit so the next session
                    // can see the immune event.
                    let evidence = format!("hello rejected: {e}");
                    let _ = emit_immune_sporocarp(
                        &mut state,
                        "C30_handshake_pubkey_mismatch",
                        "handshake_pubkey_mismatch",
                        &evidence,
                    );
                    let _ = save_dag_state(&state);

                    let response_key = match request.payload.get("session_secret") {
                        Some(Value::Bytes(b)) if b.len() == 32 => {
                            let mut arr = [0u8; 32];
                            arr.copy_from_slice(b);
                            arr
                        }
                        _ => bootstrap_key(),
                    };
                    // Best-effort write of the error envelope (operator can decode).
                    let _ = write_error_response(
                        stdout,
                        &response_key,
                        request.request_id,
                        "hello_rejected",
                        &e.to_string(),
                    );
                    graceful_shutdown_python(&mut state);
                    return Ok(2);
                }
                let response_key = if state.handshake_complete {
                    state.session_secret
                } else {
                    bootstrap_key()
                };
                write_error_response(
                    stdout,
                    &response_key,
                    request.request_id,
                    "dispatcher_error",
                    &e.to_string(),
                )?;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Dispatch implementation moved to `crate::server::dispatch` (`dispatch` fn).
// `run_loop` calls `dispatch` (re-imported below); routing is unchanged.
// ---------------------------------------------------------------------------


pub(crate) fn hex_encode(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        s.push_str(&format!("{b:02x}"));
    }
    s
}

// ---------------------------------------------------------------------------
// Persistence helpers moved to `crate::persistence_runtime` (Phase B Step 5).
// Re-exported here so existing call sites continue to compile unchanged.
// ---------------------------------------------------------------------------
pub(crate) use crate::persistence_runtime::{
    backfill_dag_from_python_state, replay_events_after_tip, replay_python_events_from_dag,
    save_dag_state, save_nonce_state, save_python_state, save_snapshot_for_state,
};

pub(crate) fn hex_first_8_bytes(bytes: &[u8; 32]) -> String {
    bytes[..8].iter().map(|b| format!("{b:02x}")).collect()
}

/// M11: Emit an immune sporocarp as a DAG node.
///
/// Wraps a detected breach event as a DAG node with `node_type = "immune:{detector_id}"`.
/// The node's content is canonical-bytes of a Map carrying the detector ID,
/// evidence, and a wall-clock timestamp.
///
/// Returns the DAG node hash (32 bytes). On failure to encode or insert,
/// returns Err — but callers typically log + continue rather than escalating,
/// because immune emission failures should not mask the original breach.
pub(crate) fn emit_immune_sporocarp(
    state: &mut ServerState,
    detector_id: &str,
    detector_name: &str,
    evidence: &str,
) -> Result<myco_kernel_shared::crypto::NodeHash, SubstrateError> {
    // **v3.1.1 Sprint 6.C (T1.7)** — use the monotonic wall-clock helper
    // so Sprint 5.F immune rate-limit logic cannot be defeated by a
    // backward clock jump. If the OS clock jumps from year 2030 to 2026,
    // emit_immune_sporocarp continues to produce strictly-increasing
    // timestamps, keeping the rate-limit window stable.
    let timestamp_unix_ns = crate::wall_clock::monotonic_unix_ns();

    // **v3.1.1 Sprint 5.F (T2.4)** — per-detector rate limit. Wall-clock
    // window prevents DoS attacks where an attacker rapidly triggers a
    // detector (e.g., C56 cultivator_preserve_all, C5 attestation_invalid,
    // C2 handshake_mismatch) and fills the DAG with duplicate immune
    // events. The substrate still reports the breach via the cached node
    // hash + a suppression counter; subsequent unique detector_ids are
    // unaffected. Window = `IMMUNE_EMISSION_RATE_LIMIT_NS` (1 second).
    //
    // Note: cycle_advanced + canonical-flow events bypass this rate limit
    // because they go through `emit_substrate_event`, not this function.
    // The rate limit applies strictly to immune-class detector emissions.
    const IMMUNE_EMISSION_RATE_LIMIT_NS: i64 = 1_000_000_000; // 1 second
    if let Some((prior_ts, prior_hash, prior_supp)) =
        state.immune_emission_state.get(detector_id).cloned()
    {
        if timestamp_unix_ns.saturating_sub(prior_ts) < IMMUNE_EMISSION_RATE_LIMIT_NS {
            // Suppress: increment suppression count, return cached hash.
            state.immune_emission_state.insert(
                detector_id.to_string(),
                (prior_ts, prior_hash, prior_supp.saturating_add(1)),
            );
            return Ok(prior_hash);
        }
    }

    let mut content_map = BTreeMap::new();
    content_map.insert(
        "detector_id".to_string(),
        Value::String(detector_id.to_string()),
    );
    content_map.insert(
        "detector_name".to_string(),
        Value::String(detector_name.to_string()),
    );
    content_map.insert("evidence".to_string(), Value::String(evidence.to_string()));
    content_map.insert(
        "timestamp_unix_ns".to_string(),
        Value::Timestamp(timestamp_unix_ns),
    );
    // **v3.1.1 Sprint 5.F**: when this emission is the first after a
    // rate-limited burst, include `suppressed_since_last_emission` so the
    // operator can re-derive the actual breach count from DAG.
    let suppressed_since = state
        .immune_emission_state
        .get(detector_id)
        .map(|(_, _, count)| *count)
        .unwrap_or(0);
    if suppressed_since > 0 {
        content_map.insert(
            "suppressed_since_last_emission".to_string(),
            Value::Uint(suppressed_since),
        );
    }
    let content_canonical = cb_encode(&Value::Map(content_map))
        .map_err(|e| SubstrateError::Protocol(format!("immune encode: {e}")))?;

    let parents = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let node_type = format!("immune:{detector_id}");
    let cycle = state.cycle_counter();
    let hash = state
        .dag
        .insert_node(parents, node_type, cycle, content_canonical)
        .map_err(|e| SubstrateError::Protocol(format!("immune DAG insert: {e}")))?;
    // Update rate-limit state with this fresh emission.
    state.immune_emission_state.insert(
        detector_id.to_string(),
        (timestamp_unix_ns, hash, 0),
    );
    Ok(hash)
}


/// M21.1 P5 万物互联: emit a generic substrate event as a DAG node. This is
/// the unified helper used by all state-mutation handlers to record their
/// state changes in the DAG event log, closing P5 by ensuring no state
/// mutation is an orphan from the causal graph.
///
/// The node is parented by the current DAG tip (linear chain at M21.1; M21.2+
/// may add multi-parent for events with logical predecessors). Returns the
/// inserted node hash for callers who need it.
pub(crate) fn emit_substrate_event(
    state: &mut ServerState,
    node_type: String,
    content: myco_kernel_shared::canonical_bytes::CanonicalBytes,
) -> Result<myco_kernel_shared::crypto::NodeHash, SubstrateError> {
    let parents = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let cycle = state.cycle_counter();
    // Capture before `node_type` is moved into the insert.
    let is_cultivation_family =
        crate::cultivation::is_cultivation_family_node_type(&node_type);
    let h = state
        .dag
        .insert_node(parents, node_type, cycle, content)
        .map_err(|e| SubstrateError::Protocol(format!("substrate event DAG insert: {e}")))?;
    // **COV06 (efficiency)** — keep the memoized FSM cache in sync. Every
    // cultivation-family event (heartbeats, stale, orphaned, recovered,
    // succession, bet_retired) flows through this single emit point, so one
    // recompute here covers all handlers AND the autonomous tick. The pure walk
    // runs only on these (rare) emissions; hot reads stay O(1).
    if is_cultivation_family {
        state.cultivation_state = crate::cultivation::current_cultivation_state(state);
    }
    Ok(h)
}

/// Forward a request to the Python worker verbatim and surface its response.
pub(super) fn forward_to_python(
    state: &mut ServerState,
    request: &Message,
    expected_response_type: &str,
) -> Result<Option<Message>, SubstrateError> {
    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;
    // Re-encode and send through the BridgeClient's low-level frame API. We
    // can't reuse BridgeClient::register_axis() etc because those allocate
    // their own request_id; we want to preserve the operator's request_id
    // for correlation in the response we send BACK to the operator.
    //
    // M6 minimum: re-issue via BridgeClient methods (which allocate fresh
    // IDs), then re-stamp the response with the operator's request_id.
    //
    // **v3.1.1 Sprint 6.J (T2.8)** — track call duration so the autonomous
    // tick can emit C65 on slow Python calls (defense-in-depth observability
    // for Python worker deadlock-precursor states).
    let call_start = std::time::Instant::now();
    let response_result = forward_message(client, request);
    crate::python_call_health::record_call_duration(call_start.elapsed());
    let response = response_result?;
    if response.message_type != expected_response_type {
        return Err(SubstrateError::Protocol(format!(
            "expected {expected_response_type} from python; got {}",
            response.message_type
        )));
    }
    // Re-stamp with operator's request_id.
    Ok(Some(Message::new(
        &response.message_type,
        request.request_id,
        response.payload,
    )))
}

/// Low-level forwarder: forwards an operator request to the Python worker
/// verbatim (its payload passed through unchanged) under a per-op hard
/// timeout, and returns the worker's response.
///
/// **v3.1.1 Sprint 7.E.2** — this used to re-extract typed fields and call
/// `BridgeClient::register_axis()` / `perturb()` / `snapshot()` (the blocking
/// API). It now uses [`BridgeClient::call_with_timeout`] so a hung Python
/// worker surfaces [`BridgeError::Timeout`] instead of wedging the substrate
/// forever. Behavior on the happy path is identical: the worker's
/// `register_axis_ack` / `perturb_ack` carry empty payloads and its
/// `snapshot_response` carries the same `{"values": {...}}` map the old code
/// synthesized, so forwarding `request.payload` verbatim is wire-equivalent.
///
/// The allow-list is preserved: only the three forwardable operator message
/// types reach Python here; anything else is a programming error and returns
/// a protocol error exactly as before.
fn forward_message(client: &mut BridgeClient, request: &Message) -> Result<Message, BridgeError> {
    let expected_response = match request.message_type.as_str() {
        msg_type::REGISTER_AXIS => msg_type::REGISTER_AXIS_ACK,
        msg_type::PERTURB => msg_type::PERTURB_ACK,
        msg_type::SNAPSHOT => msg_type::SNAPSHOT_RESPONSE,
        other => {
            return Err(BridgeError::Protocol(format!(
                "forward_message: cannot forward {other}"
            )))
        }
    };
    let timeout = crate::python_call_health::python_op_timeout(&request.message_type);
    let response =
        client.call_with_timeout(&request.message_type, request.payload.clone(), timeout)?;
    if response.message_type != expected_response {
        return Err(BridgeError::Protocol(format!(
            "expected {expected_response} from python; got {}",
            response.message_type
        )));
    }
    Ok(response)
}

// ---------------------------------------------------------------------------
// Helpers.
// ---------------------------------------------------------------------------

fn write_error_response<W: Write>(
    stdout: &mut W,
    key: &[u8; 32],
    in_response_to: u64,
    code: &str,
    msg: &str,
) -> Result<(), SubstrateError> {
    let mut payload = BTreeMap::new();
    payload.insert("code".to_string(), Value::String(code.to_string()));
    payload.insert("message".to_string(), Value::String(msg.to_string()));
    payload.insert("in_response_to".to_string(), Value::Uint(in_response_to));
    let err_msg = Message::new(msg_type::ERROR, in_response_to, payload);
    let frame = encode_frame_body(&err_msg, key).map_err(SubstrateError::Bridge)?;
    write_frame(stdout, &frame).map_err(SubstrateError::Bridge)?;
    Ok(())
}

fn graceful_shutdown_python(state: &mut ServerState) {
    if let Some(client) = state.python_client.take() {
        let _ = client.shutdown();
    }
}

// **v3.1.1 Sprint 7.E.2** — the per-field extraction helpers
// (`expect_string_field` / `expect_bool_field` / `parse_float_field`) that
// the old `forward_message` used to re-derive typed args were removed when
// forwarding became a verbatim, timeout-bounded payload pass-through. Python
// now validates these fields itself, so re-extracting them substrate-side was
// dead weight. `float_repr` survives because the rest of the crate
// (events / observatory / ingest) imports it for canonical float rendering.

/// Render an f64 as a Python-compatible repr string.
///
/// **Single source of truth**: delegates to
/// [`myco_kernel_shared::canonical_bytes::float_repr`] (CPython `repr(float)`
/// reproduced exactly — the canonical oracle). Re-exported here because
/// `ingest` / `observatory` import `crate::server::float_repr`. See the shared
/// implementation for the algorithm and the L1/HARD_RULES C18 rationale.
pub(crate) fn float_repr(f: f64) -> String {
    shared_float_repr(f)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn float_repr_pinned_values() {
        assert_eq!(float_repr(0.0), "0.0");
        assert_eq!(float_repr(1.5), "1.5");
        assert_eq!(float_repr(-2.0), "-2.0");
    }

    #[test]
    fn float_repr_special() {
        assert_eq!(float_repr(f64::NAN), "nan");
        assert_eq!(float_repr(f64::INFINITY), "inf");
        assert_eq!(float_repr(f64::NEG_INFINITY), "-inf");
    }
}
