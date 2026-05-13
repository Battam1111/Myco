"""Tests for kernel/trajectory query + clustering."""

from __future__ import annotations

import pytest

from myco_kernel_trajectory.cluster import cluster_connected_components
from myco_kernel_trajectory.query import (
    COLD_START_MARKER,
    DagNode,
    InMemoryDagSource,
    TrajectoryError,
    TrajectoryResult,
    causal_ancestors,
    causal_ancestors_and_descendants,
    causal_descendants,
    neighborhood,
)


def _dag_node(node_id: str, parents: tuple[str, ...], cycle: int) -> DagNode:
    return DagNode(
        node_id=node_id, parent_ids=parents, at_cycle=cycle, node_type="test"
    )


# ---------------------------------------------------------------------------
# InMemoryDagSource basic behavior.
# ---------------------------------------------------------------------------


def test_empty_dag_is_empty() -> None:
    dag = InMemoryDagSource()
    assert dag.is_empty()
    assert dag.all_node_ids() == []


def test_dag_add_and_lookup() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    assert not dag.is_empty()
    assert dag.get("a") is not None
    assert dag.get("a").node_id == "a"


def test_dag_duplicate_rejected() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    with pytest.raises(TrajectoryError, match="duplicate"):
        dag.add(_dag_node("a", (), 0))


def test_dag_unknown_parent_rejected() -> None:
    dag = InMemoryDagSource()
    with pytest.raises(TrajectoryError, match="parent"):
        dag.add(_dag_node("orphan", ("nonexistent",), 0))


# ---------------------------------------------------------------------------
# neighborhood query.
# ---------------------------------------------------------------------------


def test_neighborhood_cold_start_on_empty_dag() -> None:
    dag = InMemoryDagSource()
    result = neighborhood(dag, "anything", radius_cycles=10)
    assert result.cold_start
    assert result.node_ids == []


def test_neighborhood_cold_start_on_unknown_pivot() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    result = neighborhood(dag, "missing", radius_cycles=10)
    assert result.cold_start


def test_neighborhood_includes_within_radius() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 10))
    dag.add(_dag_node("b", ("a",), 20))
    dag.add(_dag_node("c", ("b",), 30))
    dag.add(_dag_node("d", ("c",), 100))  # outside radius from "b"

    # Pivot at "b" (cycle=20); radius 15 → includes a(10), b(20), c(30).
    result = neighborhood(dag, "b", radius_cycles=15)
    assert set(result.node_ids) == {"a", "b", "c"}


# ---------------------------------------------------------------------------
# causal_ancestors / descendants.
# ---------------------------------------------------------------------------


def test_ancestors_traverses_parent_chain() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    dag.add(_dag_node("b", ("a",), 1))
    dag.add(_dag_node("c", ("b",), 2))
    dag.add(_dag_node("d", ("c",), 3))

    ancestors = causal_ancestors(dag, "d")
    assert ancestors == {"a", "b", "c"}


def test_ancestors_handles_diamond() -> None:
    """Diamond pattern: a → b → d AND a → c → d. All should be ancestors of d."""
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    dag.add(_dag_node("b", ("a",), 1))
    dag.add(_dag_node("c", ("a",), 1))
    dag.add(_dag_node("d", ("b", "c"), 2))

    ancestors = causal_ancestors(dag, "d")
    assert ancestors == {"a", "b", "c"}


def test_ancestors_of_root_is_empty() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    assert causal_ancestors(dag, "a") == set()


def test_ancestors_of_unknown_is_empty() -> None:
    dag = InMemoryDagSource()
    assert causal_ancestors(dag, "missing") == set()


def test_descendants_traverses_forward() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    dag.add(_dag_node("b", ("a",), 1))
    dag.add(_dag_node("c", ("b",), 2))

    desc = causal_descendants(dag, "a")
    assert desc == {"b", "c"}


def test_descendants_of_leaf_is_empty() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    dag.add(_dag_node("b", ("a",), 1))
    assert causal_descendants(dag, "b") == set()


def test_ancestors_and_descendants_union() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    dag.add(_dag_node("b", ("a",), 1))
    dag.add(_dag_node("c", ("b",), 2))
    dag.add(_dag_node("d", ("c",), 3))

    # From "b" alone: ancestors={a}, descendants={c,d}, self={b}.
    result = causal_ancestors_and_descendants(dag, ["b"])
    assert result == {"a", "b", "c", "d"}


# ---------------------------------------------------------------------------
# Clustering.
# ---------------------------------------------------------------------------


def test_clustering_single_chain_is_one_cluster() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    dag.add(_dag_node("b", ("a",), 1))
    dag.add(_dag_node("c", ("b",), 2))

    result = cluster_connected_components(dag, {"a", "b", "c"})
    assert result.cluster_count == 1
    assert result.clusters[0].node_ids == frozenset({"a", "b", "c"})


def test_clustering_two_disconnected_is_two_clusters() -> None:
    dag = InMemoryDagSource()
    # Two independent chains: a→b and c→d (no edge between).
    dag.add(_dag_node("a", (), 0))
    dag.add(_dag_node("b", ("a",), 1))
    dag.add(_dag_node("c", (), 0))
    dag.add(_dag_node("d", ("c",), 1))

    result = cluster_connected_components(dag, {"a", "b", "c", "d"})
    assert result.cluster_count == 2

    cluster_members = {frozenset(c.node_ids) for c in result.clusters}
    assert cluster_members == {frozenset({"a", "b"}), frozenset({"c", "d"})}


def test_cluster_of_returns_correct_cluster() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    dag.add(_dag_node("b", ("a",), 1))
    dag.add(_dag_node("c", (), 0))

    result = cluster_connected_components(dag, {"a", "b", "c"})
    cluster_of_a = result.cluster_of("a")
    cluster_of_c = result.cluster_of("c")
    assert cluster_of_a is not None
    assert cluster_of_c is not None
    assert cluster_of_a.cluster_id != cluster_of_c.cluster_id


def test_cluster_of_unknown_returns_none() -> None:
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    result = cluster_connected_components(dag, {"a"})
    assert result.cluster_of("missing") is None


def test_empty_clustering() -> None:
    dag = InMemoryDagSource()
    result = cluster_connected_components(dag, set())
    assert result.cluster_count == 0


def test_clustering_diamond_is_one_cluster() -> None:
    """Diamond: a → {b, c} → d. All connected; one cluster."""
    dag = InMemoryDagSource()
    dag.add(_dag_node("a", (), 0))
    dag.add(_dag_node("b", ("a",), 1))
    dag.add(_dag_node("c", ("a",), 1))
    dag.add(_dag_node("d", ("b", "c"), 2))

    result = cluster_connected_components(dag, {"a", "b", "c", "d"})
    assert result.cluster_count == 1


# ---------------------------------------------------------------------------
# End-to-end: trajectory query → cluster → "intent".
# ---------------------------------------------------------------------------


def test_e2e_trajectory_pipeline() -> None:
    """Full L1_TRAJECTORY §1 pipeline: neighborhood → ancestors_and_descendants
    → cluster_C → "intent"."""
    dag = InMemoryDagSource()
    # Build a 5-node chain.
    dag.add(_dag_node("a", (), 10))
    dag.add(_dag_node("b", ("a",), 20))
    dag.add(_dag_node("c", ("b",), 30))
    dag.add(_dag_node("d", ("c",), 40))
    dag.add(_dag_node("e", ("d",), 50))

    # neighborhood around "c" with radius 15 → includes b, c, d.
    nbr = neighborhood(dag, "c", radius_cycles=15)
    assert not nbr.cold_start
    assert set(nbr.node_ids) == {"b", "c", "d"}

    # ancestors+descendants of {b, c, d} → {a, b, c, d, e}.
    full_set = causal_ancestors_and_descendants(dag, nbr.node_ids)
    assert full_set == {"a", "b", "c", "d", "e"}

    # cluster_C → one cluster (all connected).
    intent = cluster_connected_components(dag, full_set)
    assert intent.cluster_count == 1
    assert intent.clusters[0].node_ids == frozenset({"a", "b", "c", "d", "e"})
