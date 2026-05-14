//! M21 P5 万物互联 — DerivedState: full substrate state from DAG events.
//!
//! ## Doctrine alignment
//!
//! Per L0 §2.1 P5 ("Universal Interconnection"): the substrate is a connected
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

use std::collections::HashMap;

use myco_kernel_schema::dag::{Dag, DagNode};
use myco_kernel_shared::canonical_bytes::{
    decode as cb_decode, map_get_bytes, map_get_uint, Value,
};

use crate::events::{
    NODE_TYPE_CYCLE_ADVANCED, NODE_TYPE_GENESIS_PREFIX, NODE_TYPE_NONCE_CONSUMED_PREFIX,
    NODE_TYPE_NONCE_EXPIRED_PREFIX, NODE_TYPE_NONCE_ISSUED_PREFIX,
    NODE_TYPE_OPERATOR_PINNED_PREFIX,
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
    /// Authoritative metabolic-cycle counter.
    pub cycle_counter: u64,
    /// Highest cycle whose raw_material has been absorbed (M18).
    pub last_absorbed_cycle: Option<u64>,
    /// Pinned operator IDENTITY pubkey (M9 TOFU). `None` until first operator_pinned event.
    pub pinned_operator_identity: Option<PinnedOperatorIdentity>,
    /// Live nonce log: derived from nonce_issued events, with nonce_consumed /
    /// nonce_expired events updating per-entry `consumed` flag or removing.
    pub nonce_log: HashMap<[u8; 32], DerivedNonce>,
}

impl DerivedState {
    /// Empty initial state — corresponds to pre-genesis substrate.
    pub fn empty() -> Self {
        DerivedState {
            substrate_id: None,
            genesis_time_unix_ns: None,
            cycle_counter: 0,
            last_absorbed_cycle: None,
            pinned_operator_identity: None,
            nonce_log: HashMap::new(),
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
    ///   "format_version": Uint(1),
    ///   "snapshot_at_dag_tip": Bytes(32),  // optional; absent for empty DAG
    ///   "substrate_id": Bytes(32),         // optional; absent until genesis_event
    ///   "genesis_time_unix_ns": Timestamp, // optional
    ///   "cycle_counter": Uint,
    ///   "last_absorbed_cycle": Uint,       // optional
    ///   "pinned_operator_identity": Map,   // optional
    ///   "nonce_log": Array<Map>,
    /// })
    /// ```
    pub fn to_canonical_bytes(
        &self,
        snapshot_at_dag_tip: Option<&[u8; 32]>,
    ) -> myco_kernel_shared::canonical_bytes::CanonicalBytes {
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        use std::collections::BTreeMap;

        let mut root = BTreeMap::new();
        root.insert("format_version".to_string(), Value::Uint(1));
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

        encode(&Value::Map(root)).expect("snapshot encode infallible")
    }

    /// M21.5: decode a snapshot from canonical bytes, returning (state, snapshot_at_dag_tip).
    /// Returns `None` on format version mismatch (caller falls back to full DAG replay).
    #[allow(clippy::type_complexity)]
    pub fn from_canonical_bytes(
        bytes: &[u8],
    ) -> Result<Option<(Self, Option<[u8; 32]>)>, DerivedStateError> {
        use myco_kernel_shared::canonical_bytes::{
            decode, map_get_array, map_get_bytes, map_get_uint, Value,
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
        if version != 1 {
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
        Ok(Some((
            DerivedState {
                substrate_id,
                genesis_time_unix_ns,
                cycle_counter,
                last_absorbed_cycle,
                pinned_operator_identity,
                nonce_log,
            },
            snapshot_at_dag_tip,
        )))
    }

    /// M21.2: Produce a Manifest compatible with M5-M20 boot expectations.
    /// Used in the DAG-first boot path to populate ServerState.manifest from
    /// the DAG event log.
    ///
    /// `last_save_time_unix_ns` defaults to `now` (informational only; not
    /// derivable from DAG and not security-critical).
    pub fn to_legacy_manifest(&self) -> crate::persistence::Manifest {
        use crate::persistence::Manifest;
        use std::time::{SystemTime, UNIX_EPOCH};
        let now_ns = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .ok()
            .and_then(|d| i64::try_from(d.as_nanos()).ok())
            .unwrap_or(0);
        Manifest {
            substrate_id: self.substrate_id.unwrap_or([0u8; 32]),
            genesis_time_unix_ns: self.genesis_time_unix_ns.unwrap_or(0),
            cycle_counter: self.cycle_counter,
            last_save_time_unix_ns: now_ns,
            last_absorbed_cycle: self.last_absorbed_cycle,
        }
    }

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
        } else {
            // Pure-record events (M8-M20) that don't impact Rust-side
            // DerivedState: sporocarp:*, immune:*, raw_material:*,
            // perturb_from_raw:*, mutation:*, evolution_succeeded/failed:*,
            // self_euthanasia_proposal:*, spore_emission:*, and the M21.1
            // axis_* + owner_key_* events (which feed Python's view, not Rust's).
            Ok(())
        }
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
            encode_genesis_event(&id, 1_234_567_890),
        );
        s.apply_event(&node).unwrap();
        assert_eq!(s.substrate_id, Some(id));
        assert_eq!(s.genesis_time_unix_ns, Some(1_234_567_890));
    }

    #[test]
    fn duplicate_genesis_event_is_rejected() {
        let mut s = DerivedState::empty();
        let id = [0x01; 32];
        let node = make_node(
            genesis_event_node_type(&id),
            0,
            encode_genesis_event(&id, 1),
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
            encode_genesis_event(&id, 100),
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
                encode_genesis_event(&id, 1),
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
}
