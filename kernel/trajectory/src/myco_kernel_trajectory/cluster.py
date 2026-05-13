"""cluster_C — clustering algorithm over trajectory subgraphs (L1_TRAJECTORY §4).

## Doctrine

Per L1_TRAJECTORY §1 + §4: ``cluster_C`` is the substrate's currently-
designated clustering algorithm; intent is a function of
``(DAG, cluster_C)`` jointly. Different cluster_C choices yield different
intent renders even on identical DAGs — this is intentional (per
L1_TRAJECTORY §4 clusterer-coupling acknowledged).

M4 minimum-viable: connected-components clustering. Two nodes belong to
the same cluster iff they share a connected-component in the
neighborhood subgraph (ignoring edge direction).

## L4 escalation

L1_TRAJECTORY §4 explicitly demoted specific clustering algorithm names
(astronaut-5 finding). L4 substrates choose their cluster_C; M5+ may add
community-detection algorithms (Louvain, Leiden) as plugin clusterers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from myco_kernel_trajectory.query import DagSource


@dataclass(frozen=True, slots=True)
class Cluster:
    """One cluster of causally-related nodes."""

    cluster_id: int
    """Sequential cluster identifier (0-indexed)."""

    node_ids: frozenset[str]
    """The node IDs in this cluster."""


@dataclass(frozen=True, slots=True)
class ClusteringResult:
    """Result of running cluster_C over a node set."""

    clusters: tuple[Cluster, ...] = field(default_factory=tuple)
    """The detected clusters (one per connected component)."""

    @property
    def cluster_count(self) -> int:
        """Number of clusters."""
        return len(self.clusters)

    def cluster_of(self, node_id: str) -> Cluster | None:
        """Find which cluster contains a given node."""
        for c in self.clusters:
            if node_id in c.node_ids:
                return c
        return None


def cluster_connected_components(
    dag: DagSource, node_ids: set[str]
) -> ClusteringResult:
    """M4 cluster_C: connected-components over the neighborhood subgraph.

    Treats DAG edges as undirected for clustering purposes (a node is in
    the same cluster as its causal parents AND its causal descendants
    within the input set).

    Args:
        dag: the DAG source (for looking up parent_ids).
        node_ids: the neighborhood to cluster.

    Returns:
        ClusteringResult with one Cluster per connected component.
    """
    # Build undirected adjacency restricted to the input set.
    adj: dict[str, set[str]] = {nid: set() for nid in node_ids}
    for nid in node_ids:
        node = dag.get(nid)
        if node is None:
            continue
        for parent in node.parent_ids:
            if parent in adj:
                adj[nid].add(parent)
                adj[parent].add(nid)

    # BFS connected components.
    visited: set[str] = set()
    clusters: list[Cluster] = []
    cluster_id = 0
    for start in sorted(node_ids):
        if start in visited:
            continue
        component: set[str] = set()
        stack = [start]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component.add(current)
            for neighbor in adj.get(current, set()):
                if neighbor not in visited:
                    stack.append(neighbor)
        clusters.append(
            Cluster(cluster_id=cluster_id, node_ids=frozenset(component))
        )
        cluster_id += 1

    return ClusteringResult(clusters=tuple(clusters))
