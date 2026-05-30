//! Substrate manifest persistence (M7) — `<state_dir>/manifest.cb`.
//!
//! Substrate identity + metabolic-cycle position. The Rust side owns
//! `manifest.cb`; Python owns `gradient.cb`.

use std::collections::BTreeMap;
use std::fs;
use std::io::{Read, Write};
use std::path::Path;

use myco_kernel_shared::canonical_bytes::{
    decode as cb_decode, encode as cb_encode, map_get_bytes, map_get_uint, Value,
};

use super::{current_unix_ns, ensure_state_dir};
use crate::SubstrateError;

/// Current manifest file format version. Bumped on any breaking change to
/// the canonical-bytes schema.
pub const MANIFEST_FORMAT_VERSION: u64 = 1;

/// Filename for the Rust-managed manifest within a state directory.
pub const MANIFEST_FILENAME: &str = "manifest.cb";

/// Filename for the Python-managed gradient state within a state directory.
pub const GRADIENT_FILENAME: &str = "gradient.cb";

/// Substrate identity + metabolic-cycle position. Persisted to `manifest.cb`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Manifest {
    /// 32-byte substrate identifier, set once at genesis.
    pub substrate_id: [u8; 32],
    /// Genesis wall-clock time, in nanoseconds since UNIX epoch.
    pub genesis_time_unix_ns: i64,
    /// Current authoritative metabolic-cycle counter.
    pub cycle_counter: u64,
    /// Most recent save wall-clock time (informational; bumped on every save).
    pub last_save_time_unix_ns: i64,
    /// M18 (P4 永恒迭代): highest cycle whose raw_material has been absorbed.
    /// `None` = no absorption yet (every raw_material is pending). After each
    /// absorption_event the substrate sets this to the highest created_at_cycle
    /// of the absorbed batch — preserving the "each moment refines what prior
    /// moments produced" semantics without overloading any valid cycle value.
    pub last_absorbed_cycle: Option<u64>,
    /// **8f / L1/GOVERNANCE §16.A (F22)**: this substrate's lineage depth.
    /// Root substrate = 0; a child sprouted by `handle_sprout_child` records
    /// `parent.generation_depth + 1`. Used by the C47
    /// `generation_depth_exceeded` reproduction detector to bound lineage
    /// depth against `reproduction_lineage_depth_max` (default 10), defending
    /// the forkbomb attack class (§16 cascade of L0 P08 永恒繁衍).
    ///
    /// **Back-compat**: absent in pre-8f `manifest.cb` / `genesis_event` /
    /// `snapshot.cb` → decoded as `0` (root). This keeps the wire format
    /// additive: old substrates load unchanged and behave as roots.
    pub generation_depth: u64,
}

impl Manifest {
    /// Generate a fresh genesis manifest with a random substrate_id and
    /// current wall-clock time.
    pub fn genesis() -> Self {
        // **M-anchor-2 §9.2.1 hook**: allow the operator process to override
        // both `substrate_id` and `genesis_time_unix_ns` via env vars. This
        // is what makes birth attestation possible: operator pre-generates
        // both values, requests a birth_attestation from anchor_surface_host
        // (which signs them), then spawns the substrate with those exact
        // values + the resulting attestation env vars (per
        // `server::read_birth_attestation_env_vars`).
        //
        // Without these overrides, substrate-generated values still work —
        // it just means the substrate boots without a birth attestation
        // (C20 fires on subsequent boots flagging the chain as broken).
        //
        // Env var contract:
        // - `MYCO_SUBSTRATE_ID_OVERRIDE_HEX`: 64 hex chars = 32 bytes.
        // - `MYCO_GENESIS_TIME_OVERRIDE_UNIX_NS`: i64 decimal.
        let substrate_id = match std::env::var("MYCO_SUBSTRATE_ID_OVERRIDE_HEX") {
            Ok(s) if s.len() == 64 => {
                let mut arr = [0u8; 32];
                let mut ok = true;
                for i in 0..32 {
                    match u8::from_str_radix(&s[i * 2..i * 2 + 2], 16) {
                        Ok(b) => arr[i] = b,
                        Err(_) => {
                            ok = false;
                            break;
                        }
                    }
                }
                if ok {
                    arr
                } else {
                    generate_substrate_id()
                }
            }
            _ => generate_substrate_id(),
        };
        let genesis_time = match std::env::var("MYCO_GENESIS_TIME_OVERRIDE_UNIX_NS") {
            Ok(s) => s.parse::<i64>().unwrap_or_else(|_| current_unix_ns()),
            _ => current_unix_ns(),
        };
        // **8f / L1/GOVERNANCE §16.A**: allow the operator process to override
        // `generation_depth` at genesis. Mirrors the substrate_id /
        // genesis_time override hooks above. The authoritative depth for a
        // *sprouted* child is carried by its `genesis_event` DAG node (set by
        // the parent's `handle_sprout_child`); this env hook exists so a
        // birth ritual that pre-builds a child can also stamp the depth.
        // Absent / malformed → 0 (root).
        let generation_depth = match std::env::var("MYCO_GENERATION_DEPTH_OVERRIDE") {
            Ok(s) => s.parse::<u64>().unwrap_or(0),
            _ => 0,
        };
        Manifest {
            substrate_id,
            genesis_time_unix_ns: genesis_time,
            cycle_counter: 0,
            last_save_time_unix_ns: current_unix_ns(),
            last_absorbed_cycle: None,
            generation_depth,
        }
    }

    /// Encode the manifest as canonical bytes (the on-disk representation).
    pub fn to_canonical_bytes(&self) -> Vec<u8> {
        let mut map = BTreeMap::new();
        map.insert(
            "format_version".to_string(),
            Value::Uint(MANIFEST_FORMAT_VERSION),
        );
        map.insert(
            "substrate_id".to_string(),
            Value::Bytes(self.substrate_id.to_vec()),
        );
        map.insert(
            "genesis_time_unix_ns".to_string(),
            Value::Timestamp(self.genesis_time_unix_ns),
        );
        map.insert("cycle_counter".to_string(), Value::Uint(self.cycle_counter));
        map.insert(
            "last_save_time_unix_ns".to_string(),
            Value::Timestamp(self.last_save_time_unix_ns),
        );
        // M18: optional field — absent in v1 manifests AND when no absorption
        // has occurred yet. Only emitted when Some(cycle).
        if let Some(c) = self.last_absorbed_cycle {
            map.insert("last_absorbed_cycle".to_string(), Value::Uint(c));
        }
        // 8f / L1/GOVERNANCE §16.A: emit generation_depth only when non-zero
        // so a root substrate's manifest is byte-identical to a pre-8f one
        // (additive back-compat — root depth 0 is the absent-field default).
        if self.generation_depth != 0 {
            map.insert(
                "generation_depth".to_string(),
                Value::Uint(self.generation_depth),
            );
        }
        cb_encode(&Value::Map(map))
            .expect("manifest canonical-bytes encode is infallible")
            .0
    }

    /// Decode a manifest from canonical bytes. Returns None on version
    /// mismatch (caller falls back to genesis).
    pub fn from_canonical_bytes(bytes: &[u8]) -> Result<Option<Self>, SubstrateError> {
        let decoded = cb_decode(bytes)
            .map_err(|e| SubstrateError::Protocol(format!("manifest decode: {e}")))?;
        let map = match decoded {
            Value::Map(m) => m,
            other => {
                return Err(SubstrateError::Protocol(format!(
                    "manifest is not a Map: {other:?}"
                )))
            }
        };
        let format_version = map_get_uint(&map, "format_version")
            .map_err(|e| SubstrateError::Protocol(e.to_string()))?;
        if format_version != MANIFEST_FORMAT_VERSION {
            // Unknown future version → caller can choose genesis.
            return Ok(None);
        }
        let substrate_id_slice = map_get_bytes(&map, "substrate_id")
            .map_err(|e| SubstrateError::Protocol(e.to_string()))?;
        if substrate_id_slice.len() != 32 {
            return Err(SubstrateError::Protocol(format!(
                "substrate_id is {} bytes; expected 32",
                substrate_id_slice.len()
            )));
        }
        let mut substrate_id = [0u8; 32];
        substrate_id.copy_from_slice(substrate_id_slice);
        let genesis_time = match map.get("genesis_time_unix_ns") {
            Some(Value::Timestamp(ts)) => *ts,
            _ => {
                return Err(SubstrateError::Protocol(
                    "manifest missing genesis_time_unix_ns".to_string(),
                ))
            }
        };
        let cycle_counter = map_get_uint(&map, "cycle_counter")
            .map_err(|e| SubstrateError::Protocol(e.to_string()))?;
        let last_save_time = match map.get("last_save_time_unix_ns") {
            Some(Value::Timestamp(ts)) => *ts,
            _ => {
                return Err(SubstrateError::Protocol(
                    "manifest missing last_save_time_unix_ns".to_string(),
                ))
            }
        };
        // M18: optional field — None for pre-M18 manifests or for substrates
        // that haven't absorbed any raw_material yet.
        let last_absorbed_cycle = match map.get("last_absorbed_cycle") {
            Some(Value::Uint(n)) => Some(*n),
            _ => None,
        };
        // 8f / L1/GOVERNANCE §16.A: optional field — absent in pre-8f
        // manifests and in every root substrate → 0 (root lineage depth).
        let generation_depth = match map.get("generation_depth") {
            Some(Value::Uint(n)) => *n,
            _ => 0,
        };
        Ok(Some(Manifest {
            substrate_id,
            genesis_time_unix_ns: genesis_time,
            cycle_counter,
            last_save_time_unix_ns: last_save_time,
            last_absorbed_cycle,
            generation_depth,
        }))
    }

    /// Atomically write the manifest to `<state_dir>/manifest.cb`.
    ///
    /// Creates `state_dir` if it doesn't exist. Updates
    /// [`last_save_time_unix_ns`](Self::last_save_time_unix_ns) to the
    /// current wall-clock time before writing.
    pub fn save(&mut self, state_dir: &Path) -> Result<(), SubstrateError> {
        self.last_save_time_unix_ns = current_unix_ns();
        ensure_state_dir(state_dir)?;
        let final_path = state_dir.join(MANIFEST_FILENAME);
        let tmp_path = state_dir.join(format!("{MANIFEST_FILENAME}.tmp"));
        let bytes = self.to_canonical_bytes();
        {
            let mut f = fs::File::create(&tmp_path)?;
            f.write_all(&bytes)?;
            f.sync_all()?; // fsync — durability across crash
        }
        fs::rename(&tmp_path, &final_path)?;
        Ok(())
    }

    /// Load the manifest from `<state_dir>/manifest.cb`. Returns:
    ///
    /// - `Ok(Some(manifest))` — file exists, parses cleanly, format matches.
    /// - `Ok(None)` — file does not exist OR format is incompatible (caller
    ///   should treat as a genesis condition).
    /// - `Err(...)` — I/O or parse error.
    pub fn load(state_dir: &Path) -> Result<Option<Self>, SubstrateError> {
        let path = state_dir.join(MANIFEST_FILENAME);
        match fs::File::open(&path) {
            Ok(mut f) => {
                let mut bytes = Vec::new();
                f.read_to_end(&mut bytes)?;
                Manifest::from_canonical_bytes(&bytes)
            }
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
            Err(e) => Err(SubstrateError::Io(e)),
        }
    }
}

/// Generate a fresh random 32-byte substrate identifier.
///
/// M7 uses time + process + stack-address SHA-256 mix (same pattern as the
/// kernel/bridge session_secret generator). M8+ may switch to OS-level
/// `getrandom` once that's wired everywhere.
fn generate_substrate_id() -> [u8; 32] {
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(b"myco-substrate-id-v1");
    h.update(current_unix_ns().to_le_bytes());
    h.update(std::process::id().to_le_bytes());
    let stack_var = 0u8;
    let addr = &stack_var as *const u8 as usize;
    h.update(addr.to_le_bytes());
    let result = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}
