//! DAG read/query primitives — extracted from `server.rs` (Phase B Step 3).
//!
//! Owns the operator-facing read handlers that walk the substrate's causal
//! DAG: recent-node tail, intent computation (forwarded to Python), DAG
//! enumeration from a prev-tip, and the immune-event filter. Also hosts the
//! cold-start `empty_intent_response` helper shared between intent paths.
//!
//! Doctrine traceability:
//! - L1_SCHEMA §2.2 — DAG node type taxonomy referenced by enumeration.
//! - L1_HARD_RULES §1 — C6 dag_enumeration_unclosed emitted from enumerate.

use std::collections::BTreeMap;

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::Value;

use crate::server::{emit_immune_sporocarp, hex_encode, save_dag_state, ServerState};
use crate::SubstrateError;

/// M11: Return the substrate's most-recent DAG nodes (server-side window) so
/// the operator runtime can render the substrate's "recent activity" without
/// itself walking the entire DAG.
///
/// Payload:
///   - `count` (Uint, optional): max nodes to return. Default 50.
///   - `node_type_prefix` (String, optional, M16): substring prefix filter
///     applied to `node_type` before slicing. Useful for tailing one node
///     species (e.g. `"raw_material:"`).
///
/// Response shape (canonical-bytes):
///   - `total_dag_size`: unfiltered DAG node count.
///   - `filtered_total` (M16): count AFTER prefix filter (== total_dag_size
///     when no filter applied).
///   - `returned_count`: nodes in this response.
///   - `nodes`: Array<Map> of {hash, parent_hashes, node_type, at_cycle,
///     content_canonical_bytes}.
///   - `dag_tip`: optional 32-byte hash of the current DAG tip.
pub(crate) fn handle_query_recent_nodes(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let count = request
        .payload
        .get("count")
        .and_then(|v| match v {
            Value::Uint(n) => Some(*n),
            _ => None,
        })
        .unwrap_or(50);

    // M16: optional node_type_prefix filter.
    let prefix_filter: Option<String> =
        request
            .payload
            .get("node_type_prefix")
            .and_then(|v| match v {
                Value::String(s) => Some(s.clone()),
                _ => None,
            });

    // Total DAG size is always reported unfiltered (caller-visible context).
    let unfiltered_total = state.dag.node_count();
    let all_nodes: Vec<_> = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| {
            prefix_filter
                .as_ref()
                .map(|p| n.node_type.starts_with(p))
                .unwrap_or(true)
        })
        .collect();
    let filtered_total = all_nodes.len();
    let start = filtered_total.saturating_sub(count as usize);
    let recent: Vec<Value> = all_nodes[start..]
        .iter()
        .map(|n| {
            let mut m = BTreeMap::new();
            m.insert("hash".to_string(), Value::Bytes(n.hash.as_ref().to_vec()));
            m.insert(
                "parent_hashes".to_string(),
                Value::Array(
                    n.parent_hashes
                        .iter()
                        .map(|h| Value::Bytes(h.as_ref().to_vec()))
                        .collect(),
                ),
            );
            m.insert("node_type".to_string(), Value::String(n.node_type.clone()));
            m.insert("at_cycle".to_string(), Value::Uint(n.created_at_cycle));
            m.insert(
                "content_canonical_bytes".to_string(),
                Value::Bytes(n.content_canonical_bytes.as_ref().to_vec()),
            );
            Value::Map(m)
        })
        .collect();

    let mut payload = BTreeMap::new();
    payload.insert(
        "total_dag_size".to_string(),
        Value::Uint(unfiltered_total as u64),
    );
    // M16: when a prefix filter was applied, expose the filtered-total count
    // separately so the caller can distinguish "DAG has 100 nodes; 5 match my
    // filter" from "DAG has 5 nodes total".
    payload.insert(
        "filtered_total".to_string(),
        Value::Uint(filtered_total as u64),
    );
    payload.insert(
        "returned_count".to_string(),
        Value::Uint(recent.len() as u64),
    );
    payload.insert("nodes".to_string(), Value::Array(recent));
    if let Some(tip) = state.dag.tip() {
        payload.insert("dag_tip".to_string(), Value::Bytes(tip.as_ref().to_vec()));
    }
    Ok(Some(Message::new(
        msg_type::QUERY_RECENT_NODES_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M8: Forward intent computation to the Python worker.
///
/// The substrate serializes ITS OWN DAG (full set at M8; M9+ adds windowing)
/// and sends it to Python along with the pivot and radius. Python builds an
/// in-memory DagSource and runs trajectory's neighborhood + ancestors_and_descendants
/// + cluster_C, returning the clusters.
pub(crate) fn handle_compute_intent(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;

    // Default radius: 10 cycles. Operator can override via payload.
    let radius_cycles = request
        .payload
        .get("radius_cycles")
        .and_then(|v| match v {
            Value::Uint(n) => Some(*n),
            _ => None,
        })
        .unwrap_or(10);

    // Default pivot: DAG tip. Operator can override via payload (must be a hash present in DAG).
    let pivot_bytes: Vec<u8> = match request.payload.get("pivot_hash") {
        Some(Value::Bytes(b)) if b.len() == 32 => b.clone(),
        _ => match state.dag.tip() {
            Some(t) => t.as_ref().to_vec(),
            None => {
                // Empty DAG → cold-start intent.
                return Ok(Some(empty_intent_response(request.request_id)));
            }
        },
    };
    let mut pivot_arr = [0u8; 32];
    pivot_arr.copy_from_slice(&pivot_bytes);

    // Serialize the substrate's full DAG as Array<Map> for Python.
    let dag_nodes: Vec<Value> = state
        .dag
        .iter_in_insertion_order()
        .map(|n| {
            let mut m = BTreeMap::new();
            m.insert("hash".to_string(), Value::Bytes(n.hash.as_ref().to_vec()));
            m.insert(
                "parent_hashes".to_string(),
                Value::Array(
                    n.parent_hashes
                        .iter()
                        .map(|h| Value::Bytes(h.as_ref().to_vec()))
                        .collect(),
                ),
            );
            m.insert("at_cycle".to_string(), Value::Uint(n.created_at_cycle));
            m.insert("node_type".to_string(), Value::String(n.node_type.clone()));
            Value::Map(m)
        })
        .collect();

    let payload =
        myco_kernel_bridge::protocol::compute_intent_payload(&pivot_arr, radius_cycles, dag_nodes);
    let python_response = client.call(msg_type::COMPUTE_INTENT, payload)?;
    if python_response.message_type != msg_type::COMPUTE_INTENT_RESPONSE {
        return Err(SubstrateError::Protocol(format!(
            "expected compute_intent_response from python; got {}",
            python_response.message_type
        )));
    }
    // Re-stamp the response with the operator's request_id.
    Ok(Some(Message::new(
        msg_type::COMPUTE_INTENT_RESPONSE,
        request.request_id,
        python_response.payload,
    )))
}

/// M14: enumerate DAG nodes inserted since a caller-provided `prev_tip`.
///
/// This is the substrate-driven enumeration that operators use to recompute
/// the anchor-surface Merkle chain over a freshly-attested cycle. The
/// substrate is the authoritative source for which nodes its DAG contains,
/// so the operator submits a `prev_tip` (32-byte hash; or omits it for
/// genesis-onward enumeration) and receives the ordered list of node hashes
/// inserted since that tip.
///
/// Schema-level guarantees (mirrored from `Dag::enumerate_since`):
///   - The returned list is in DAG insertion order (causal-respecting at the
///     parent-hash level; siblings ordered by insertion).
///   - When the substrate cannot find `prev_tip`, returns a `C6
///     dag_enumeration_unclosed` immune sporocarp + a protocol error.
///   - The reply includes the current tip + total DAG size + the original
///     `prev_tip` echoed back for operator audit logs.
pub(crate) fn handle_enumerate_dag_since(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // Optional prev_tip: 32-byte hash if present, None means "from genesis".
    let prev_tip_arg: Option<myco_kernel_shared::crypto::NodeHash> =
        match request.payload.get("prev_tip") {
            Some(Value::Bytes(b)) if b.len() == 32 => {
                let mut arr = [0u8; 32];
                arr.copy_from_slice(b);
                Some(myco_kernel_shared::crypto::NodeHash::from_bytes(arr))
            }
            Some(Value::Bytes(b)) => {
                return Err(SubstrateError::Protocol(format!(
                    "enumerate_dag_since: prev_tip must be 32 bytes; got {}",
                    b.len()
                )));
            }
            // Absent → None.
            _ => None,
        };

    // Run enumeration.
    let enumeration_result = state.dag.enumerate_since(prev_tip_arg.as_ref());
    let hashes = match enumeration_result {
        Ok(h) => h,
        Err(myco_kernel_schema::dag::DagError::UnknownPrevTip(t)) => {
            // C6 dag_enumeration_unclosed: operator referenced a prev_tip not
            // in the substrate's DAG. Emit immune sporocarp and reject the
            // request (operator's view is desynchronized OR forge attempt).
            let evidence = format!(
                "enumerate_dag_since called with unknown prev_tip {} \
                 (substrate has no record of this tip; possible desync or forge attempt)",
                hex_encode(t.as_ref())
            );
            let _ = emit_immune_sporocarp(
                state,
                "C6_dag_enumeration_unclosed",
                "dag_enumeration_unclosed",
                &evidence,
            );
            let _ = save_dag_state(state);
            return Err(SubstrateError::Protocol(format!(
                "enumerate_dag_since: {evidence}"
            )));
        }
        Err(e) => {
            return Err(SubstrateError::Protocol(format!(
                "enumerate_dag_since failed: {e}"
            )));
        }
    };

    // Build the per-node enumeration array. Each entry carries everything the
    // owner needs to recompute the Merkle hash + chain it to the prev_tip:
    //   - hash (substrate-claimed; owner recomputes from parents + content)
    //   - parent_hashes (declared parents in hash-order)
    //   - node_type (for L1_SCHEMA §2.2 audit)
    //   - at_cycle (informational; the cycle when emitted)
    //   - content_canonical_bytes (the actual node payload)
    //
    // Borrow-checker shape: build nodes_array in an inner scope holding only
    // an immutable borrow of state.dag. If a node is missing from the DAG
    // (impossible barring internal corruption), record the issue in
    // `missing_hash` and emit C6 after the borrow drops.
    let mut nodes_array: Vec<Value> = Vec::with_capacity(hashes.len());
    let mut missing_hash: Option<myco_kernel_shared::crypto::NodeHash> = None;
    {
        let dag = &state.dag;
        for h in &hashes {
            let Some(node) = dag.get(h) else {
                missing_hash = Some(*h);
                break;
            };
            let mut node_map = BTreeMap::new();
            node_map.insert(
                "hash".to_string(),
                Value::Bytes(node.hash.as_ref().to_vec()),
            );
            node_map.insert(
                "parent_hashes".to_string(),
                Value::Array(
                    node.parent_hashes
                        .iter()
                        .map(|p| Value::Bytes(p.as_ref().to_vec()))
                        .collect(),
                ),
            );
            node_map.insert(
                "node_type".to_string(),
                Value::String(node.node_type.clone()),
            );
            node_map.insert("at_cycle".to_string(), Value::Uint(node.created_at_cycle));
            node_map.insert(
                "content_canonical_bytes".to_string(),
                Value::Bytes(node.content_canonical_bytes.as_ref().to_vec()),
            );
            nodes_array.push(Value::Map(node_map));
        }
    }
    if let Some(h) = missing_hash {
        let evidence = format!(
            "enumerate_dag_since: enumeration listed hash {} but state.dag.get returned None \
             (DAG internal inconsistency)",
            hex_encode(h.as_ref())
        );
        let _ = emit_immune_sporocarp(
            state,
            "C6_dag_enumeration_unclosed",
            "dag_enumeration_unclosed",
            &evidence,
        );
        let _ = save_dag_state(state);
        return Err(SubstrateError::Protocol(evidence));
    }

    let total_dag_size = state.dag.node_count() as u64;
    let mut payload = BTreeMap::new();
    if let Some(tip) = state.dag.tip() {
        payload.insert(
            "current_tip".to_string(),
            Value::Bytes(tip.as_ref().to_vec()),
        );
    }
    payload.insert("total_dag_size".to_string(), Value::Uint(total_dag_size));
    payload.insert(
        "enumerated_count".to_string(),
        Value::Uint(nodes_array.len() as u64),
    );
    if let Some(prev) = prev_tip_arg {
        payload.insert("prev_tip".to_string(), Value::Bytes(prev.as_ref().to_vec()));
    }
    payload.insert("nodes".to_string(), Value::Array(nodes_array));

    Ok(Some(Message::new(
        msg_type::ENUMERATE_DAG_SINCE_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M12: Return the substrate's most-recent immune-event nodes.
///
/// Convenience helper that filters the DAG by `node_type.starts_with("immune:")`
/// and slices off the most-recent `count` entries. Returns a structured payload
/// suitable for operator runtimes (Markdown rendering, status displays, etc.).
pub(crate) fn handle_query_immune_events(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let count = request
        .payload
        .get("count")
        .and_then(|v| match v {
            Value::Uint(n) => Some(*n),
            _ => None,
        })
        .unwrap_or(50);

    let all_nodes: Vec<_> = state.dag.iter_in_insertion_order().collect();
    let immune_nodes: Vec<_> = all_nodes
        .iter()
        .filter(|n| n.node_type.starts_with("immune:"))
        .copied()
        .collect();
    let total = immune_nodes.len();
    let start = total.saturating_sub(count as usize);
    let recent: Vec<Value> = immune_nodes[start..]
        .iter()
        .map(|n| {
            let mut m = BTreeMap::new();
            m.insert("hash".to_string(), Value::Bytes(n.hash.as_ref().to_vec()));
            m.insert("node_type".to_string(), Value::String(n.node_type.clone()));
            m.insert("at_cycle".to_string(), Value::Uint(n.created_at_cycle));
            m.insert(
                "content_canonical_bytes".to_string(),
                Value::Bytes(n.content_canonical_bytes.as_ref().to_vec()),
            );
            Value::Map(m)
        })
        .collect();

    let mut payload = BTreeMap::new();
    payload.insert("total_immune_count".to_string(), Value::Uint(total as u64));
    payload.insert(
        "returned_count".to_string(),
        Value::Uint(recent.len() as u64),
    );
    payload.insert("events".to_string(), Value::Array(recent));
    Ok(Some(Message::new(
        msg_type::QUERY_IMMUNE_EVENTS_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// Build an "empty DAG → cold-start" intent response (no clusters, cold_start=true).
pub(crate) fn empty_intent_response(request_id: u64) -> Message {
    let mut payload = BTreeMap::new();
    payload.insert("cold_start".to_string(), Value::Bool(true));
    payload.insert("neighborhood_node_count".to_string(), Value::Uint(0));
    payload.insert("full_set_node_count".to_string(), Value::Uint(0));
    payload.insert("cluster_count".to_string(), Value::Uint(0));
    payload.insert("clusters".to_string(), Value::Array(Vec::new()));
    Message::new(msg_type::COMPUTE_INTENT_RESPONSE, request_id, payload)
}
