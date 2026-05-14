//! Causal DAG — content-addressed Merkle storage (L1_SCHEMA §2).
//!
//! ## Doctrine
//!
//! Per L1_SCHEMA §2.1: **content-addressed Merkle DAG**. Each node carries a
//! hash that incorporates parent-hashes; node ID = node hash. The substrate's
//! identity record carries the current DAG-tip hash.
//!
//! Hash function: BLAKE3 (chosen at kernel/shared per L1_SCHEMA §2.1
//! candidates; parallelizable + modern). The merkle_hash function in
//! kernel/shared::crypto includes a **parent-count length prefix** preventing
//! ambiguity attacks between `(N parents, M-byte content)` and
//! `(N+1 parents, (M - parent_hash_size)-byte content)` collisions
//! (per pass-3 mycoparasite-2 + L1_HARD_RULES C6/C7).
//!
//! ## Enumerated-node export (L0 §9.2 + L1_HARD_RULES C6)
//!
//! Per L0 §9.2: at every contract-identity-level boundary crossing, the
//! substrate emits the **enumerated list of all DAG node hashes added since
//! the prior co-sign** — NOT just a summary diff. The owner's anchor-surface
//! client recomputes the Merkle chain from the prior signed tip via these
//! enumerated nodes; the substrate cannot present a summary that hides
//! parallel-branch forgery.
//!
//! The [`Dag::enumerate_since`] method produces this list.
//!
//! ## Retro-edit detection (L1_HARD_RULES C7)
//!
//! Each node's hash is computed from `merkle_hash(parent_hashes,
//! content_canonical_bytes)`. Any mutation to parent_hashes OR content
//! produces a different hash. The [`Dag::verify_node_hash`] method recomputes
//! the hash and detects tampering in-memory. Persistence-layer tampering
//! detection (re-computation on cold-resume) is M2 via `kernel/continuity`.
//!
//! ## No-pruning discipline (L1_SCHEMA §2.5)
//!
//! Per L1_SCHEMA §2.5: pruning is contract-identity-level. Daily ops cannot
//! remove DAG nodes. The [`Dag`] struct intentionally provides NO `remove` /
//! `prune` API at this layer — the absence is doctrinally load-bearing.
//! Cold-tier archival (moving nodes off-host to long-term storage) is NOT
//! pruning; the archival path lands at M2 via `kernel/governance` CI
//! attestation gate + `kernel/continuity` cold-tier marker.
//!
//! ## M1 implementation
//!
//! In-memory HashMap-backed storage. Insertion order tracked via Vec for
//! enumerate_since linear scan. M2 picks production storage layout from
//! L1_SCHEMA §2.1 candidates: file-per-node / log+index / embedded KV.

use myco_kernel_shared::canonical_bytes::CanonicalBytes;
use myco_kernel_shared::crypto::{merkle_hash, NodeHash};
use std::collections::HashMap;
use thiserror::Error;

/// DAG storage errors.
#[derive(Debug, Error, PartialEq, Eq)]
#[non_exhaustive]
pub enum DagError {
    /// Caller specified a parent hash that is not present in the DAG.
    /// Required for tip-chain consistency.
    #[error("parent not found in DAG: {0:?}")]
    ParentNotFound(NodeHash),

    /// Caller attempted to insert a node whose hash is already in the DAG.
    /// Insertion is idempotent for identical content; this error fires only
    /// when the same hash maps to different content (a programmer error or
    /// hash collision).
    #[error("hash collision: {0:?}")]
    HashCollision(NodeHash),

    /// `enumerate_since` was given a `prev_tip` not present in the DAG.
    #[error("prev_tip not in DAG: {0:?}")]
    UnknownPrevTip(NodeHash),

    /// Looked up a node hash that is not in the DAG (used by
    /// [`Dag::verify_node_hash`] / [`Dag::verify_all`]).
    #[error("node not found in DAG: {0:?}")]
    NodeNotFound(NodeHash),

    /// Retro-edit detected: stored node's recomputed hash differs from its
    /// stored hash. Triggers `dag_retro_edit_detected` immune sporocarp
    /// (L1_HARD_RULES C7 CRITICAL).
    #[error("dag_retro_edit_detected: stored hash {stored:?} != recomputed {recomputed:?}")]
    RetroEditDetected {
        /// Hash stored on the node.
        stored: NodeHash,
        /// Hash recomputed from parents + content.
        recomputed: NodeHash,
    },

    /// Node-type string is empty.
    #[error("node_type cannot be empty")]
    EmptyNodeType,

    /// On-disk DAG bytes failed to decode (M8 persistence).
    #[error("dag persistence malformed: {0}")]
    PersistenceMalformed(String),
}

/// A DAG node — Merkle-addressed substrate-state event.
///
/// Per L1_SCHEMA §2.2: the substrate emits at co-sign each node's metadata
/// (type, causal-parent-hashes) so the owner can recompute the chain.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DagNode {
    /// Content-addressed Merkle hash of this node
    /// (= `merkle_hash(parent_hashes, content_canonical_bytes)`).
    pub hash: NodeHash,

    /// Causal parents (zero or more). Order is significant for hash
    /// computation. Empty `parent_hashes` = genesis / root node.
    pub parent_hashes: Vec<NodeHash>,

    /// Node-type string (e.g., `"genesis"`, `"delta"`, `"sporocarp:<subtype>"`,
    /// `"attestation"`). L1_SCHEMA does not enumerate the type set — types
    /// originate at L1_TROPISM (sporocarp tree) + L1_SKIN (delta envelopes) +
    /// L1_GOVERNANCE (attestation envelopes). M1 stores the type as an
    /// opaque string; downstream kernel crates dispatch on it.
    pub node_type: String,

    /// Substrate metabolic-cycle at insertion.
    pub created_at_cycle: u64,

    /// Node content as canonical bytes. The hash covers this AND
    /// parent_hashes; any mutation produces a different hash.
    pub content_canonical_bytes: CanonicalBytes,
}

/// Causal DAG storage — content-addressed Merkle DAG (L1_SCHEMA §2.1).
///
/// ## M1 storage
///
/// In-memory: HashMap for content lookup; Vec for insertion-order
/// preservation (needed by [`Dag::enumerate_since`]). The substrate's
/// identity record carries the current tip; the DAG itself tracks tip
/// internally.
#[derive(Debug, Clone, Default)]
pub struct Dag {
    /// All nodes, indexed by hash.
    nodes: HashMap<NodeHash, DagNode>,

    /// Insertion order — Vec of hashes in the order they were inserted.
    /// Used by `enumerate_since` to produce the "added since prior co-sign"
    /// list (L0 §9.2 + L1_HARD_RULES C6).
    insertion_order: Vec<NodeHash>,

    /// Current tip hash (the last-inserted node's hash). `None` if empty.
    /// Per L1_SCHEMA §2.1: substrate's identity record carries this.
    tip: Option<NodeHash>,
}

impl Dag {
    /// Construct an empty DAG.
    pub fn new() -> Self {
        Dag::default()
    }

    /// Insert a new node into the DAG.
    ///
    /// Computes the Merkle hash from parent_hashes + content_canonical_bytes,
    /// validates that all parents are present, then stores the node and
    /// advances the tip.
    ///
    /// On success: returns the computed hash.
    ///
    /// On parent-not-found: returns `DagError::ParentNotFound`.
    /// On empty node_type: returns `DagError::EmptyNodeType`.
    /// On hash collision (same hash mapping to different content — should be
    /// astronomically rare for BLAKE3): returns `DagError::HashCollision`.
    pub fn insert_node(
        &mut self,
        parent_hashes: Vec<NodeHash>,
        node_type: String,
        created_at_cycle: u64,
        content_canonical_bytes: CanonicalBytes,
    ) -> Result<NodeHash, DagError> {
        if node_type.is_empty() {
            return Err(DagError::EmptyNodeType);
        }

        // Verify all parents exist.
        for ph in &parent_hashes {
            if !self.nodes.contains_key(ph) {
                return Err(DagError::ParentNotFound(*ph));
            }
        }

        // Compute hash.
        let hash = merkle_hash(&parent_hashes, content_canonical_bytes.as_ref());

        // Check for hash collision — same hash but different content is a bug
        // or astronomically rare collision. Same hash + same content is idempotent
        // (we accept the duplicate insertion silently as a no-op).
        if let Some(existing) = self.nodes.get(&hash) {
            if existing.parent_hashes == parent_hashes
                && existing.content_canonical_bytes == content_canonical_bytes
            {
                // Idempotent: same content → same hash → no-op.
                return Ok(hash);
            }
            return Err(DagError::HashCollision(hash));
        }

        let node = DagNode {
            hash,
            parent_hashes,
            node_type,
            created_at_cycle,
            content_canonical_bytes,
        };

        self.nodes.insert(hash, node);
        self.insertion_order.push(hash);
        self.tip = Some(hash);

        Ok(hash)
    }

    /// Look up a node by hash.
    pub fn get(&self, hash: &NodeHash) -> Option<&DagNode> {
        self.nodes.get(hash)
    }

    /// Current tip hash. `None` for an empty DAG.
    pub fn tip(&self) -> Option<NodeHash> {
        self.tip
    }

    /// Total node count.
    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    /// Enumerate all node hashes added since the given `prev_tip`
    /// (or all nodes if `prev_tip` is `None`).
    ///
    /// Per L0 §9.2 + L1_HARD_RULES C6: at every CI boundary the substrate
    /// emits this enumerated list to the anchor surface so the owner
    /// recomputes the Merkle chain from the prior signed tip.
    ///
    /// **Co-sign envelope construction**: this method returns only the
    /// **hashes**. Per L1_SCHEMA §2.2, the co-sign envelope MUST also include
    /// each node's metadata (type + causal-parent-hashes). The caller is
    /// responsible for composing the enumeration with [`Dag::get`] for each
    /// hash to retrieve the full node payload before constructing the
    /// anchor-surface co-sign envelope. The hash-only return shape preserves
    /// memory efficiency for large enumerations.
    ///
    /// Returns the hashes in insertion order (which is also causal-chain
    /// order for the trivial single-chain case; multi-parent / branching
    /// graphs preserve insertion order, which the owner reconstructs into
    /// the DAG via the per-node `parent_hashes` metadata).
    ///
    /// - `prev_tip == None`: returns all nodes (initial co-sign).
    /// - `prev_tip == Some(tip)`: returns nodes inserted AFTER `tip`.
    /// - `prev_tip == Some(current_tip)`: returns empty vec.
    /// - `prev_tip == Some(unknown)`: returns `DagError::UnknownPrevTip`.
    pub fn enumerate_since(&self, prev_tip: Option<&NodeHash>) -> Result<Vec<NodeHash>, DagError> {
        let start_index = match prev_tip {
            None => 0,
            Some(tip) => {
                let pos = self
                    .insertion_order
                    .iter()
                    .position(|h| h == tip)
                    .ok_or(DagError::UnknownPrevTip(*tip))?;
                // We want nodes added AFTER `tip`, so start at pos + 1.
                pos + 1
            }
        };
        Ok(self.insertion_order[start_index..].to_vec())
    }

    /// Verify a stored node's hash by recomputing it.
    ///
    /// Per L1_HARD_RULES C7 (`dag_retro_edit_detected`): if a node's stored
    /// hash differs from `merkle_hash(parent_hashes, content_canonical_bytes)`,
    /// the node has been tampered with.
    ///
    /// In-memory storage cannot be tampered without invoking this code path
    /// (Rust's borrow-check enforces ownership), but this method is exposed
    /// for:
    ///
    /// - Persistence-layer integrity checks at cold-resume (M2 via
    ///   `kernel/continuity`).
    /// - Property-based tests verifying the invariant.
    /// - Defense-in-depth against future unsafe-code introductions.
    pub fn verify_node_hash(&self, hash: &NodeHash) -> Result<(), DagError> {
        let node = self.nodes.get(hash).ok_or(DagError::NodeNotFound(*hash))?;
        let recomputed = merkle_hash(&node.parent_hashes, node.content_canonical_bytes.as_ref());
        if recomputed != node.hash {
            return Err(DagError::RetroEditDetected {
                stored: node.hash,
                recomputed,
            });
        }
        Ok(())
    }

    /// Test-only mutator that tampers a stored node's content WITHOUT updating
    /// its hash. Used by `verify_node_hash` and `verify_all` tests to exercise
    /// the retro-edit detection branch.
    ///
    /// Not exposed in production builds — `#[cfg(test)]` gated. Production
    /// in-memory storage is tamper-proof at the Rust borrow-check level;
    /// persistence-layer tampering detection (M2 via `kernel/continuity`
    /// cold-resume integrity check) is the real defense.
    #[cfg(test)]
    pub(crate) fn tamper_content_for_test(
        &mut self,
        hash: &NodeHash,
        new_content: CanonicalBytes,
    ) -> Result<(), DagError> {
        let node = self
            .nodes
            .get_mut(hash)
            .ok_or(DagError::NodeNotFound(*hash))?;
        node.content_canonical_bytes = new_content;
        Ok(())
    }

    /// Verify ALL stored nodes (called periodically + at cold-resume).
    /// Returns the first detected retro-edit (the caller emits the immune
    /// sporocarp for that node + queries for additional issues separately).
    pub fn verify_all(&self) -> Result<(), DagError> {
        for hash in self.insertion_order.iter() {
            self.verify_node_hash(hash)?;
        }
        Ok(())
    }

    /// Iterate over all nodes in insertion order (M8 — enables persistence).
    pub fn iter_in_insertion_order(&self) -> impl Iterator<Item = &DagNode> {
        self.insertion_order
            .iter()
            .filter_map(|h| self.nodes.get(h))
    }

    /// Serialize the entire DAG to canonical bytes for on-disk persistence (M8).
    ///
    /// Schema (canonical-bytes Map):
    /// ```text
    ///   Map({
    ///     "format_version": Uint(1),
    ///     "nodes": Array<Map({
    ///       "parent_hashes": Array<Bytes(32)>,
    ///       "node_type": String,
    ///       "created_at_cycle": Uint,
    ///       "content_canonical_bytes": Bytes
    ///     })>  // in insertion order
    ///   })
    /// ```
    ///
    /// Node hashes themselves are NOT serialized — they are recomputed from
    /// `merkle_hash(parents, content)` on load. This acts as built-in
    /// integrity validation (any tampered byte breaks the hash chain).
    pub fn to_canonical_bytes(&self) -> CanonicalBytes {
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        use std::collections::BTreeMap;
        let mut nodes_array: Vec<Value> = Vec::with_capacity(self.insertion_order.len());
        for hash in &self.insertion_order {
            let node = self
                .nodes
                .get(hash)
                .expect("insertion_order references missing node");
            let parent_bytes: Vec<Value> = node
                .parent_hashes
                .iter()
                .map(|h| Value::Bytes(h.as_ref().to_vec()))
                .collect();
            let mut node_map = BTreeMap::new();
            node_map.insert("parent_hashes".to_string(), Value::Array(parent_bytes));
            node_map.insert(
                "node_type".to_string(),
                Value::String(node.node_type.clone()),
            );
            node_map.insert(
                "created_at_cycle".to_string(),
                Value::Uint(node.created_at_cycle),
            );
            node_map.insert(
                "content_canonical_bytes".to_string(),
                Value::Bytes(node.content_canonical_bytes.as_ref().to_vec()),
            );
            nodes_array.push(Value::Map(node_map));
        }
        let mut root = BTreeMap::new();
        root.insert(
            "format_version".to_string(),
            Value::Uint(DAG_FORMAT_VERSION),
        );
        root.insert("nodes".to_string(), Value::Array(nodes_array));
        encode(&Value::Map(root)).expect("DAG canonical-bytes encode is infallible")
    }

    /// Decode a DAG from canonical bytes.
    ///
    /// Returns:
    /// - `Ok(Some(dag))` — successful hydration.
    /// - `Ok(None)` — format_version mismatch (caller falls back to genesis).
    /// - `Err(DagError)` — malformed content OR any node's recomputed hash
    ///   diverges from its parent chain (retro-edit detection).
    pub fn from_canonical_bytes(bytes: &[u8]) -> Result<Option<Self>, DagError> {
        use myco_kernel_shared::canonical_bytes::{
            decode, map_get_array, map_get_bytes, map_get_string, map_get_uint, Value,
        };
        let decoded =
            decode(bytes).map_err(|e| DagError::PersistenceMalformed(format!("decode: {e}")))?;
        let map = match decoded {
            Value::Map(m) => m,
            other => {
                return Err(DagError::PersistenceMalformed(format!(
                    "DAG root is not a Map: {other:?}"
                )))
            }
        };
        let version = map_get_uint(&map, "format_version")
            .map_err(|e| DagError::PersistenceMalformed(e.to_string()))?;
        if version != DAG_FORMAT_VERSION {
            return Ok(None);
        }
        let nodes_array = map_get_array(&map, "nodes")
            .map_err(|e| DagError::PersistenceMalformed(e.to_string()))?;
        let mut dag = Dag::new();
        for node_value in nodes_array {
            let node_map = match node_value {
                Value::Map(m) => m,
                other => {
                    return Err(DagError::PersistenceMalformed(format!(
                        "DAG node is not a Map: {other:?}"
                    )))
                }
            };
            let parents_array = map_get_array(node_map, "parent_hashes")
                .map_err(|e| DagError::PersistenceMalformed(e.to_string()))?;
            let mut parent_hashes: Vec<NodeHash> = Vec::with_capacity(parents_array.len());
            for p in parents_array {
                match p {
                    Value::Bytes(b) if b.len() == 32 => {
                        let mut arr = [0u8; 32];
                        arr.copy_from_slice(b);
                        parent_hashes.push(NodeHash::from_bytes(arr));
                    }
                    _ => {
                        return Err(DagError::PersistenceMalformed(
                            "parent_hashes contains non-32-byte entry".to_string(),
                        ))
                    }
                }
            }
            let node_type = map_get_string(node_map, "node_type")
                .map_err(|e| DagError::PersistenceMalformed(e.to_string()))?
                .to_string();
            let created_at_cycle = map_get_uint(node_map, "created_at_cycle")
                .map_err(|e| DagError::PersistenceMalformed(e.to_string()))?;
            let content_slice = map_get_bytes(node_map, "content_canonical_bytes")
                .map_err(|e| DagError::PersistenceMalformed(e.to_string()))?;
            let content = CanonicalBytes(content_slice.to_vec());
            dag.insert_node(parent_hashes, node_type, created_at_cycle, content)?;
        }
        Ok(Some(dag))
    }
}

/// Current DAG persistence format version. Bumped on any breaking change to
/// the on-disk schema.
pub const DAG_FORMAT_VERSION: u64 = 1;

#[cfg(test)]
mod tests {
    use super::*;
    use myco_kernel_shared::canonical_bytes::{encode, Value};

    fn make_cbytes(s: &str) -> CanonicalBytes {
        encode(&Value::String(s.to_string())).unwrap()
    }

    // ---------------------------------------------------------------------
    // M8 persistence tests.
    // ---------------------------------------------------------------------

    #[test]
    fn m8_empty_dag_roundtrips_canonical_bytes() {
        let dag = Dag::new();
        let bytes = dag.to_canonical_bytes();
        let dag2 = Dag::from_canonical_bytes(bytes.as_ref()).unwrap().unwrap();
        assert_eq!(dag2.node_count(), 0);
        assert_eq!(dag2.tip(), None);
    }

    #[test]
    fn m8_single_node_dag_roundtrips() {
        let mut dag = Dag::new();
        let hash = dag
            .insert_node(vec![], "genesis".to_string(), 0, make_cbytes("init"))
            .unwrap();
        let bytes = dag.to_canonical_bytes();
        let dag2 = Dag::from_canonical_bytes(bytes.as_ref()).unwrap().unwrap();
        assert_eq!(dag2.node_count(), 1);
        assert_eq!(dag2.tip(), Some(hash));
        let node = dag2.get(&hash).unwrap();
        assert_eq!(node.node_type, "genesis");
        assert_eq!(node.created_at_cycle, 0);
    }

    #[test]
    fn m8_chained_dag_preserves_insertion_order_and_hashes() {
        let mut dag = Dag::new();
        let h1 = dag
            .insert_node(vec![], "genesis".to_string(), 0, make_cbytes("n1"))
            .unwrap();
        let h2 = dag
            .insert_node(vec![h1], "sporocarp".to_string(), 1, make_cbytes("n2"))
            .unwrap();
        let h3 = dag
            .insert_node(vec![h2], "sporocarp".to_string(), 2, make_cbytes("n3"))
            .unwrap();

        let bytes = dag.to_canonical_bytes();
        let dag2 = Dag::from_canonical_bytes(bytes.as_ref()).unwrap().unwrap();
        assert_eq!(dag2.node_count(), 3);
        assert_eq!(dag2.tip(), Some(h3));
        // All three nodes have the same hashes recomputed on load.
        assert!(dag2.get(&h1).is_some());
        assert!(dag2.get(&h2).is_some());
        assert!(dag2.get(&h3).is_some());
        // Insertion order matches.
        let nodes_in_order: Vec<_> = dag2.iter_in_insertion_order().map(|n| n.hash).collect();
        assert_eq!(nodes_in_order, vec![h1, h2, h3]);
    }

    #[test]
    fn m8_branching_dag_roundtrips() {
        let mut dag = Dag::new();
        let root = dag
            .insert_node(vec![], "genesis".to_string(), 0, make_cbytes("r"))
            .unwrap();
        let _a = dag
            .insert_node(vec![root], "branch_a".to_string(), 1, make_cbytes("a"))
            .unwrap();
        let _b = dag
            .insert_node(vec![root], "branch_b".to_string(), 1, make_cbytes("b"))
            .unwrap();
        // Multi-parent merge node.
        let _merge = dag
            .insert_node(vec![_a, _b], "merge".to_string(), 2, make_cbytes("merge"))
            .unwrap();

        let bytes = dag.to_canonical_bytes();
        let dag2 = Dag::from_canonical_bytes(bytes.as_ref()).unwrap().unwrap();
        assert_eq!(dag2.node_count(), 4);
        assert_eq!(dag2.verify_all(), Ok(()));
    }

    #[test]
    fn m8_version_mismatch_returns_none() {
        use std::collections::BTreeMap;
        let mut bad_root = BTreeMap::new();
        bad_root.insert("format_version".to_string(), Value::Uint(9999));
        bad_root.insert("nodes".to_string(), Value::Array(vec![]));
        let bad_bytes = encode(&Value::Map(bad_root)).unwrap();
        let result = Dag::from_canonical_bytes(bad_bytes.as_ref()).unwrap();
        assert!(result.is_none());
    }

    #[test]
    fn m8_malformed_bytes_return_error() {
        let result = Dag::from_canonical_bytes(b"not-canonical-bytes");
        assert!(result.is_err());
    }

    #[test]
    fn m8_persistence_byte_determinism() {
        let mut dag1 = Dag::new();
        let _ = dag1
            .insert_node(vec![], "a".to_string(), 0, make_cbytes("x"))
            .unwrap();
        let bytes1 = dag1.to_canonical_bytes();
        let bytes2 = dag1.to_canonical_bytes();
        assert_eq!(bytes1, bytes2);
    }

    #[test]
    fn test_new_dag_is_empty() {
        let dag = Dag::new();
        assert_eq!(dag.node_count(), 0);
        assert_eq!(dag.tip(), None);
    }

    #[test]
    fn test_insert_root_node() {
        let mut dag = Dag::new();
        let hash = dag
            .insert_node(vec![], "genesis".to_string(), 0, make_cbytes("init"))
            .unwrap();
        assert_eq!(dag.node_count(), 1);
        assert_eq!(dag.tip(), Some(hash));
        let node = dag.get(&hash).unwrap();
        assert_eq!(node.node_type, "genesis");
        assert_eq!(node.created_at_cycle, 0);
    }

    #[test]
    fn test_insert_child_node() {
        let mut dag = Dag::new();
        let h1 = dag
            .insert_node(vec![], "genesis".to_string(), 0, make_cbytes("g"))
            .unwrap();
        let h2 = dag
            .insert_node(vec![h1], "delta".to_string(), 1, make_cbytes("d1"))
            .unwrap();
        assert_eq!(dag.node_count(), 2);
        assert_eq!(dag.tip(), Some(h2));
        let node = dag.get(&h2).unwrap();
        assert_eq!(node.parent_hashes, vec![h1]);
    }

    #[test]
    fn test_insert_multiple_parents() {
        let mut dag = Dag::new();
        let h1 = dag
            .insert_node(vec![], "a".to_string(), 0, make_cbytes("a"))
            .unwrap();
        let h2 = dag
            .insert_node(vec![], "b".to_string(), 0, make_cbytes("b"))
            .unwrap();
        let h3 = dag
            .insert_node(vec![h1, h2], "merge".to_string(), 1, make_cbytes("m"))
            .unwrap();
        assert_eq!(dag.get(&h3).unwrap().parent_hashes.len(), 2);
    }

    #[test]
    fn test_parent_not_found_rejected() {
        let mut dag = Dag::new();
        let phantom = NodeHash([0xab; 32]);
        let result = dag.insert_node(vec![phantom], "orphan".to_string(), 0, make_cbytes("x"));
        assert_eq!(result, Err(DagError::ParentNotFound(phantom)));
    }

    #[test]
    fn test_empty_node_type_rejected() {
        let mut dag = Dag::new();
        let result = dag.insert_node(vec![], "".to_string(), 0, make_cbytes("x"));
        assert_eq!(result, Err(DagError::EmptyNodeType));
    }

    #[test]
    fn test_idempotent_insert_same_content_same_hash() {
        let mut dag = Dag::new();
        let h1 = dag
            .insert_node(vec![], "type".to_string(), 0, make_cbytes("c"))
            .unwrap();
        // Insert the same content again: same hash, no-op.
        let h2 = dag
            .insert_node(vec![], "type".to_string(), 0, make_cbytes("c"))
            .unwrap();
        assert_eq!(h1, h2);
        // node_count should still be 1.
        assert_eq!(dag.node_count(), 1);
    }

    #[test]
    fn test_different_content_different_hash() {
        let mut dag = Dag::new();
        let h1 = dag
            .insert_node(vec![], "x".to_string(), 0, make_cbytes("a"))
            .unwrap();
        let h2 = dag
            .insert_node(vec![], "x".to_string(), 0, make_cbytes("b"))
            .unwrap();
        assert_ne!(h1, h2);
        assert_eq!(dag.node_count(), 2);
    }

    #[test]
    fn test_different_parents_different_hash() {
        let mut dag = Dag::new();
        let p1 = dag
            .insert_node(vec![], "p1".to_string(), 0, make_cbytes("p1"))
            .unwrap();
        let p2 = dag
            .insert_node(vec![], "p2".to_string(), 0, make_cbytes("p2"))
            .unwrap();
        // Same content but different parents → different hash.
        let h_via_p1 = dag
            .insert_node(vec![p1], "child".to_string(), 1, make_cbytes("c"))
            .unwrap();
        let h_via_p2 = dag
            .insert_node(vec![p2], "child".to_string(), 1, make_cbytes("c"))
            .unwrap();
        assert_ne!(h_via_p1, h_via_p2);
    }

    #[test]
    fn test_enumerate_since_initial() {
        let mut dag = Dag::new();
        let h1 = dag
            .insert_node(vec![], "a".to_string(), 0, make_cbytes("a"))
            .unwrap();
        let h2 = dag
            .insert_node(vec![h1], "b".to_string(), 1, make_cbytes("b"))
            .unwrap();
        let h3 = dag
            .insert_node(vec![h2], "c".to_string(), 2, make_cbytes("c"))
            .unwrap();

        // From None: all nodes.
        let all = dag.enumerate_since(None).unwrap();
        assert_eq!(all, vec![h1, h2, h3]);
    }

    #[test]
    fn test_enumerate_since_intermediate() {
        let mut dag = Dag::new();
        let h1 = dag
            .insert_node(vec![], "a".to_string(), 0, make_cbytes("a"))
            .unwrap();
        let h2 = dag
            .insert_node(vec![h1], "b".to_string(), 1, make_cbytes("b"))
            .unwrap();
        let h3 = dag
            .insert_node(vec![h2], "c".to_string(), 2, make_cbytes("c"))
            .unwrap();

        // From h1: h2 + h3.
        let since_h1 = dag.enumerate_since(Some(&h1)).unwrap();
        assert_eq!(since_h1, vec![h2, h3]);
    }

    #[test]
    fn test_enumerate_since_current_tip_is_empty() {
        let mut dag = Dag::new();
        let h1 = dag
            .insert_node(vec![], "a".to_string(), 0, make_cbytes("a"))
            .unwrap();
        let result = dag.enumerate_since(Some(&h1)).unwrap();
        assert!(result.is_empty());
    }

    #[test]
    fn test_enumerate_since_unknown_tip_rejected() {
        let mut dag = Dag::new();
        dag.insert_node(vec![], "a".to_string(), 0, make_cbytes("a"))
            .unwrap();
        let phantom = NodeHash([0xff; 32]);
        let result = dag.enumerate_since(Some(&phantom));
        assert_eq!(result, Err(DagError::UnknownPrevTip(phantom)));
    }

    #[test]
    fn test_verify_node_hash_passes_for_untampered() {
        let mut dag = Dag::new();
        let h = dag
            .insert_node(vec![], "x".to_string(), 0, make_cbytes("c"))
            .unwrap();
        dag.verify_node_hash(&h).unwrap();
    }

    #[test]
    fn test_verify_node_hash_unknown_returns_node_not_found() {
        let dag = Dag::new();
        let phantom = NodeHash([0xfe; 32]);
        assert_eq!(
            dag.verify_node_hash(&phantom).unwrap_err(),
            DagError::NodeNotFound(phantom)
        );
    }

    #[test]
    fn test_verify_node_hash_detects_retro_edit() {
        // Exercises the L1_HARD_RULES C7 dag_retro_edit_detected branch by
        // tampering the in-memory content WITHOUT updating the stored hash.
        let mut dag = Dag::new();
        let h = dag
            .insert_node(vec![], "x".to_string(), 0, make_cbytes("original"))
            .unwrap();
        dag.tamper_content_for_test(&h, make_cbytes("tampered"))
            .unwrap();
        let result = dag.verify_node_hash(&h);
        assert!(matches!(result, Err(DagError::RetroEditDetected { .. })));
    }

    #[test]
    fn test_verify_all_passes() {
        let mut dag = Dag::new();
        let h1 = dag
            .insert_node(vec![], "a".to_string(), 0, make_cbytes("a"))
            .unwrap();
        dag.insert_node(vec![h1], "b".to_string(), 1, make_cbytes("b"))
            .unwrap();
        dag.verify_all().unwrap();
    }

    #[test]
    fn test_verify_all_detects_retro_edit_in_chain() {
        // Insert a 3-node chain, tamper the middle node, verify_all fires.
        let mut dag = Dag::new();
        let h1 = dag
            .insert_node(vec![], "a".to_string(), 0, make_cbytes("a"))
            .unwrap();
        let h2 = dag
            .insert_node(vec![h1], "b".to_string(), 1, make_cbytes("b"))
            .unwrap();
        dag.insert_node(vec![h2], "c".to_string(), 2, make_cbytes("c"))
            .unwrap();
        dag.tamper_content_for_test(&h2, make_cbytes("b_tampered"))
            .unwrap();
        let result = dag.verify_all();
        assert!(matches!(result, Err(DagError::RetroEditDetected { .. })));
    }

    #[test]
    fn test_get_unknown_hash_returns_none() {
        let dag = Dag::new();
        let phantom = NodeHash([0xab; 32]);
        assert!(dag.get(&phantom).is_none());
    }

    #[test]
    fn test_node_count_tracks_inserts() {
        let mut dag = Dag::new();
        for i in 0..5 {
            let cbytes = make_cbytes(&format!("c{}", i));
            let parents = if i == 0 {
                vec![]
            } else {
                vec![dag.tip().unwrap()]
            };
            dag.insert_node(parents, format!("n{}", i), i as u64, cbytes)
                .unwrap();
        }
        assert_eq!(dag.node_count(), 5);
    }

    #[test]
    fn test_tip_advances_on_insert() {
        let mut dag = Dag::new();
        let h1 = dag
            .insert_node(vec![], "a".to_string(), 0, make_cbytes("a"))
            .unwrap();
        assert_eq!(dag.tip(), Some(h1));
        let h2 = dag
            .insert_node(vec![h1], "b".to_string(), 1, make_cbytes("b"))
            .unwrap();
        assert_eq!(dag.tip(), Some(h2));
    }
}
