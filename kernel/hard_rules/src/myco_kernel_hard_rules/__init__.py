"""Myco v0.9 — kernel/hard_rules (immune system).

Per L1/HARD_RULES §1: CRITICAL breach detectors that auto-quarantine the
substrate. Per §2: F-row fixed-point watchdogs that observe CI mutation
attempts.

**v0.9 owner-key removal**: the owner-attestation breach rows (C5
attestation_invalid + C17 operator_witness_forgery, and the inert C12 + C20
enum members) were removed with the owner-key/anchor subsystem.

Public surface (re-exported from ``detectors`` for ergonomic imports):
the :class:`BreachId` taxonomy, the :class:`ImmuneEvent` emission type, the
structured detector-input events, the ``detect_c*`` detector functions, and
the :class:`DetectorRegistry` dispatch surface.
"""

from __future__ import annotations

from myco_kernel_hard_rules.detectors import (
    BreachId,
    DagNodeAttempt,
    DetectorRegistry,
    EgressAttempt,
    HandshakeAttempt,
    ImmuneEvent,
    MutationClassification,
    build_default_registry,
    detect_c1_appetite_locality_breach,
    detect_c2_output_endpoint_breach,
    detect_c7_dag_retro_edit,
    detect_c11_concurrent_operator,
    detect_c14_untyped_mutation,
    detect_c18_canonical_bytes_render_drift,
)

__version__ = "0.9.0a1"

__all__ = [
    "__version__",
    "BreachId",
    "ImmuneEvent",
    # detector-input event types
    "EgressAttempt",
    "MutationClassification",
    "DagNodeAttempt",
    "HandshakeAttempt",
    # detector functions
    "detect_c1_appetite_locality_breach",
    "detect_c2_output_endpoint_breach",
    "detect_c7_dag_retro_edit",
    "detect_c11_concurrent_operator",
    "detect_c14_untyped_mutation",
    "detect_c18_canonical_bytes_render_drift",
    # dispatch
    "DetectorRegistry",
    "build_default_registry",
]
