"""Trajectory handler — derive intent from a DAG subset (M8).

``compute_intent`` runs ``kernel/trajectory``'s intent algorithm over a DAG
subset transported from the Rust substrate: it reconstructs an in-memory
DagSource, computes the pivot neighborhood + causal ancestors/descendants,
clusters the connected components, and returns the clusters. The handler is
stateless across calls — it holds nothing in :class:`DispatcherState`.
"""

from __future__ import annotations

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bool,
    Bytes as CbBytes,
    CanonicalBytesError,
    Map as CbMap,
    Uint as CbUint,
    Value,
    expect_array,
    expect_bytes,
    expect_map,
    expect_string,
    expect_uint,
)

from myco_kernel_bridge.handlers.registry import handler
from myco_kernel_bridge.handlers.state import DispatcherState
from myco_kernel_bridge.protocol import (
    BridgeProtocolError,
    Message,
    MessageType,
)


@handler(MessageType.COMPUTE_INTENT)
def _handle_compute_intent(state: DispatcherState, request: Message) -> Message:
    """Run kernel/trajectory's intent algorithm over a DAG subset (M8).

    The Rust substrate sends its DAG nodes; we build an in-memory DagSource,
    run neighborhood + ancestors+descendants + cluster_C, and return the
    clusters.
    """
    from myco_kernel_trajectory.cluster import cluster_connected_components  # noqa: PLC0415
    from myco_kernel_trajectory.query import (  # noqa: PLC0415
        DagNode,
        InMemoryDagSource,
        causal_ancestors_and_descendants,
        neighborhood,
    )

    _ = state  # this handler is stateless across calls
    keys = dict(request.payload.value)
    try:
        pivot_hash_bytes = expect_bytes(keys["pivot_hash"])
        radius_cycles = expect_uint(keys["radius_cycles"])
        dag_nodes_array = expect_array(keys["dag_nodes"])
    except (KeyError, CanonicalBytesError) as e:
        raise BridgeProtocolError(
            f"compute_intent payload error: {e}"
        ) from e

    # Reconstruct an in-memory DagSource from the transported subset.
    dag = InMemoryDagSource()
    for node_value in dag_nodes_array:
        node_map = expect_map(node_value)
        node_fields = dict(node_map.value)
        try:
            node_hash = expect_bytes(node_fields["hash"]).hex()
            parents_arr = expect_array(node_fields["parent_hashes"])
            parent_ids = tuple(expect_bytes(p).hex() for p in parents_arr)
            at_cycle = expect_uint(node_fields["at_cycle"])
            node_type = expect_string(node_fields["node_type"])
        except (KeyError, CanonicalBytesError) as e:
            raise BridgeProtocolError(
                f"compute_intent dag_node decode error: {e}"
            ) from e
        dag.add(
            DagNode(
                node_id=node_hash,
                parent_ids=parent_ids,
                at_cycle=int(at_cycle),
                node_type=node_type,
            )
        )

    pivot_id = pivot_hash_bytes.hex()
    nbr = neighborhood(dag, pivot_id, int(radius_cycles))
    full_set = causal_ancestors_and_descendants(dag, nbr.node_ids)
    intent = cluster_connected_components(dag, full_set)

    # Build response.
    cluster_values: list[Value] = []
    for cluster in intent.clusters:
        cluster_map = CbMap.from_dict(
            {
                "cluster_id": CbUint(cluster.cluster_id),
                "node_count": CbUint(len(cluster.node_ids)),
                "node_hashes": Array(
                    tuple(CbBytes(bytes.fromhex(nid)) for nid in sorted(cluster.node_ids))
                ),
            }
        )
        cluster_values.append(cluster_map)

    response_payload = CbMap.from_dict(
        {
            "cold_start": Bool(nbr.cold_start),
            "neighborhood_node_count": CbUint(len(nbr.node_ids)),
            "full_set_node_count": CbUint(len(full_set)),
            "cluster_count": CbUint(len(intent.clusters)),
            "clusters": Array(tuple(cluster_values)),
        }
    )
    return Message(
        type=MessageType.COMPUTE_INTENT_RESPONSE,
        request_id=request.request_id,
        payload=response_payload,
    )
