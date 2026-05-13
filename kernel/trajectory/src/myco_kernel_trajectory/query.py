"""Trajectory queries over the causal DAG (L1_TRAJECTORY §1).

## Doctrine

Per L1_TRAJECTORY §1:

```
intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))
```

This module provides the `neighborhood` + `causal_ancestors` +
`causal_descendants` primitives that operate on an abstract DAG model.

## Cold-start (per L1_TRAJECTORY §3)

At substrate genesis the causal DAG contains only the genesis_event
sporocarp. Queries return a `cold_start_marker`. This is correct behavior:
"the pair has no joint history yet" is a true statement at t=0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class TrajectoryError(Exception):
    """Trajectory-query error."""


@dataclass(frozen=True, slots=True)
class DagNode:
    """Abstract DAG node for trajectory queries.

    The kernel/trajectory module operates on this abstract shape; the
    concrete DAG implementation lives in kernel/schema (Rust). Cross-process
    integration in M5+ wires Python → Rust DAG access.

    Fields
    ------
    node_id:
        Hex-encoded BLAKE3 hash of the node (matches kernel/schema NodeHash).
    parent_ids:
        Tuple of parent node IDs.
    at_cycle:
        Substrate metabolic-cycle at insertion.
    node_type:
        Type tag (e.g., "delta", "sporocarp", "attestation").
    """

    node_id: str
    parent_ids: tuple[str, ...]
    at_cycle: int
    node_type: str


class DagSource(Protocol):
    """Abstract DAG read interface — implemented by cross-process bridges
    that consume kernel/schema's actual DAG."""

    def get(self, node_id: str) -> DagNode | None:
        """Look up a node by ID; None if not found."""
        ...

    def all_node_ids(self) -> list[str]:
        """All node IDs currently in the DAG (in insertion order)."""
        ...

    def is_empty(self) -> bool:
        """Whether the DAG has any nodes."""
        ...


class InMemoryDagSource:
    """Simple in-memory DAG for tests + standalone trajectory queries."""

    __slots__ = ("nodes", "insertion_order")

    nodes: dict[str, DagNode]
    insertion_order: list[str]

    def __init__(self) -> None:
        self.nodes = {}
        self.insertion_order = []

    def add(self, node: DagNode) -> None:
        """Insert a node (caller responsible for valid parents + uniqueness)."""
        if node.node_id in self.nodes:
            raise TrajectoryError(f"duplicate node_id: {node.node_id}")
        for p in node.parent_ids:
            if p not in self.nodes:
                raise TrajectoryError(f"parent {p} not in DAG")
        self.nodes[node.node_id] = node
        self.insertion_order.append(node.node_id)

    def get(self, node_id: str) -> DagNode | None:
        return self.nodes.get(node_id)

    def all_node_ids(self) -> list[str]:
        return list(self.insertion_order)

    def is_empty(self) -> bool:
        return len(self.nodes) == 0


# Sentinel marker for cold-start (per L1_TRAJECTORY §3).
COLD_START_MARKER = "cold_start_marker"


@dataclass(frozen=True, slots=True)
class TrajectoryResult:
    """Result of a trajectory query."""

    node_ids: list[str] = field(default_factory=list)
    """Node IDs in the neighborhood / ancestors / descendants."""

    cold_start: bool = False
    """True if the query returned the cold_start_marker (DAG too small)."""


def neighborhood(
    dag: DagSource,
    pivot_node_id: str,
    radius_cycles: int,
) -> TrajectoryResult:
    """Compute the causal-cycle neighborhood around the pivot node.

    Per L1_TRAJECTORY §1: returns nodes within ``radius_cycles`` of the
    pivot's at_cycle. Cold-start: if the DAG is empty or the pivot doesn't
    exist, returns the cold_start marker.

    Args:
        dag: the DAG source.
        pivot_node_id: the trajectory pivot.
        radius_cycles: cycle-window radius (e.g., 50 → include nodes within
            50 cycles either direction).
    """
    if dag.is_empty():
        return TrajectoryResult(cold_start=True)
    pivot = dag.get(pivot_node_id)
    if pivot is None:
        return TrajectoryResult(cold_start=True)

    nodes_in_window: list[str] = []
    for nid in dag.all_node_ids():
        node = dag.get(nid)
        if node is None:
            continue
        if abs(node.at_cycle - pivot.at_cycle) <= radius_cycles:
            nodes_in_window.append(nid)
    return TrajectoryResult(node_ids=nodes_in_window)


def causal_ancestors(dag: DagSource, node_id: str) -> set[str]:
    """Transitive set of causal ancestors of node_id.

    Per L1_TRAJECTORY §1 + L1_SCHEMA §2.1: ancestors are reachable via
    parent_ids walks.
    """
    ancestors: set[str] = set()
    if dag.get(node_id) is None:
        return ancestors

    visited: set[str] = set()
    stack = [node_id]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        node = dag.get(current)
        if node is None:
            continue
        for parent in node.parent_ids:
            if parent not in ancestors:
                ancestors.add(parent)
                stack.append(parent)
    return ancestors


def causal_descendants(dag: DagSource, node_id: str) -> set[str]:
    """Transitive set of causal descendants of node_id.

    Per L1_TRAJECTORY §1: descendants are nodes whose parent_ids walks
    reach node_id.
    """
    descendants: set[str] = set()
    if dag.get(node_id) is None:
        return descendants

    # Build child-index by scanning all nodes.
    children_of: dict[str, list[str]] = {}
    for nid in dag.all_node_ids():
        node = dag.get(nid)
        if node is None:
            continue
        for parent in node.parent_ids:
            children_of.setdefault(parent, []).append(nid)

    stack = [node_id]
    visited: set[str] = set()
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        for child in children_of.get(current, []):
            if child not in descendants:
                descendants.add(child)
                stack.append(child)
    return descendants


def causal_ancestors_and_descendants(
    dag: DagSource, node_ids: list[str]
) -> set[str]:
    """Union of ancestors + descendants for a list of pivot nodes.

    Per L1_TRAJECTORY §1: the input to cluster_C is the full ancestor +
    descendant set of the neighborhood.
    """
    result: set[str] = set()
    for nid in node_ids:
        result.add(nid)
        result |= causal_ancestors(dag, nid)
        result |= causal_descendants(dag, nid)
    return result
