"""Myco v0.9 — kernel/trajectory (intent derivation).

Per L1/TRAJECTORY §1: ``intent(t) := cluster_C(
causal_ancestors_and_descendants(neighborhood(t)))``.

Public surface (re-exported from the submodules for ergonomic imports):

- ``query`` — the abstract DAG model + neighborhood / ancestor / descendant
  primitives.
- ``cluster`` — the M4 ``cluster_C`` connected-components clusterer.
"""

from __future__ import annotations

from myco_kernel_trajectory.cluster import (
    Cluster,
    ClusteringResult,
    cluster_connected_components,
)
from myco_kernel_trajectory.query import (
    COLD_START_MARKER,
    DagNode,
    DagSource,
    InMemoryDagSource,
    TrajectoryError,
    TrajectoryResult,
    causal_ancestors,
    causal_ancestors_and_descendants,
    causal_descendants,
    neighborhood,
)

__version__ = "0.9.0a1"

__all__ = [
    "__version__",
    # query
    "DagNode",
    "DagSource",
    "InMemoryDagSource",
    "TrajectoryResult",
    "TrajectoryError",
    "COLD_START_MARKER",
    "neighborhood",
    "causal_ancestors",
    "causal_descendants",
    "causal_ancestors_and_descendants",
    # cluster
    "Cluster",
    "ClusteringResult",
    "cluster_connected_components",
]
