# myco-kernel-trajectory

Myco v0.9 — kernel/trajectory (Python) per L3_PACKAGE_MAP §8.

Implements **intent derivation** as a substrate-resident query over the
causal DAG. Per L1/TRAJECTORY §1: intent is computed, not stored —
`intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))`.

## M4 scope

- `query`: neighborhood + ancestors/descendants traversal over a DAG.
- `cluster`: cluster_C minimum-viable (connected-components clustering).
- `cold_start`: handles t=0 empty-DAG case with cold_start_marker.

## M5+ deferred

- Epoch tracking (L1/TRAJECTORY §6).
- Thread_id orthogonal grouping (L1/TRAJECTORY §5).
- Echo-chamber detection (L1/TRAJECTORY §7).
