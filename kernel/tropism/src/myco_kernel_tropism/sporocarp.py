"""Sporocarp emission — substrate-initiated typed observables (L1_TROPISM §3).

## Doctrine

Per L1_TROPISM §3 second-layer: **sporocarp** is the substrate's
observable. When a gradient axis crosses its fruiting trigger, the substrate
fruits a sporocarp — a typed, content-addressed, causally-stamped record
(per L0 I4) that anchors the continuous gradient medium to discrete
observables for:

- L0 I2 governance classification.
- L0 I3 SSoT validation.
- L0 I7 federation / spore-schema.
- L0 I4 causal DAG.

## Sporocarp shape

Per L1_TROPISM §B6: sporocarps carry **causal proofs** — the parent
sporocarp hashes whose gradient state contributed to this sporocarp's
fruiting. M3 ships the data shape + canonical-bytes encoding; M4 wires
the DAG insertion (substrate inserts the sporocarp into kernel/schema DAG).

## Why sporocarps are not verbs

Per L1_TROPISM §3: a verb is agent-initiated (agent calls → substrate
executes). A sporocarp is substrate-initiated (gradient crosses trigger →
substrate fruits → agent observes). Arrow reversed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bytes,
    CanonicalBytes,
    Map,
    String,
    Uint,
    Value,
    encode,
)
from myco_kernel_governance.crypto import NodeHash, merkle_hash


class SporocarpError(Exception):
    """Sporocarp-emission error."""


# Canonical sporocarp type prefix used in canonical-bytes encoding.
SPOROCARP_TYPE_TAG: Final[str] = "sporocarp"


@dataclass(frozen=True, slots=True)
class Sporocarp:
    """A substrate-fruited sporocarp.

    Per L1_TROPISM + L0 I4: typed, content-addressed, causally-stamped.

    Fields
    ------
    sporocarp_type:
        Subtype tag (e.g., ``"appetite_fruiting"`` /
        ``"mortality_signal_threshold_crossed"`` / ``"birth_period_milestone"``).
        Substrate-defined per its sporocarp-type tree (L1_HARD_RULES F12
        CI-protected at the schema level).
    axis_name:
        Which appetite axis fruited this sporocarp.
    fruiting_value:
        The gradient value at fruiting moment (for diagnostic / replay).
    at_cycle:
        Substrate metabolic-cycle counter at fruiting.
    causal_parent_hashes:
        Parent sporocarp hashes that contributed to this one's fruiting
        (per L1_TROPISM §B6 causal proofs).
    payload_canonical_bytes:
        Substrate-defined payload for this sporocarp type (e.g., for an
        attestation_request sporocarp, the canonical bytes of the
        attestation request envelope).
    """

    sporocarp_type: str
    axis_name: str
    fruiting_value: float
    at_cycle: int
    causal_parent_hashes: tuple[NodeHash, ...] = field(default_factory=tuple)
    payload_canonical_bytes: CanonicalBytes = field(
        default_factory=lambda: CanonicalBytes(b"")
    )

    def to_canonical_bytes(self) -> CanonicalBytes:
        """Canonical-bytes encoding of the sporocarp.

        The hash of these bytes is the sporocarp's content-addressed
        identifier in the DAG (per L0 I4).
        """
        # Float encoded as string for determinism (avoids float-rounding
        # cross-language drift). Substrates that need exact float semantics
        # must use a fixed-point encoding upstream; M3 uses repr-style.
        m_value: Value = Map.from_dict(
            {
                "type": String(SPOROCARP_TYPE_TAG),
                "sporocarp_type": String(self.sporocarp_type),
                "axis_name": String(self.axis_name),
                "fruiting_value_repr": String(repr(self.fruiting_value)),
                "at_cycle": Uint(self.at_cycle),
                "causal_parent_hashes": Array(
                    tuple(
                        Value.__class__.__call__(  # type: ignore[misc]
                            None
                        )
                        if False
                        else _hash_to_bytes_value(h)
                        for h in self.causal_parent_hashes
                    )
                ),
                "payload_canonical_bytes": Bytes(
                    self.payload_canonical_bytes.bytes_
                ),
            }
        )
        return encode(m_value)

    def hash(self) -> NodeHash:
        """Content-addressed sporocarp hash (BLAKE3 of canonical bytes).

        Per L1_SCHEMA §2.1: this hash is the sporocarp's identifier in the
        DAG. Parents are listed in causal_parent_hashes.
        """
        cbytes = self.to_canonical_bytes()
        return merkle_hash(list(self.causal_parent_hashes), cbytes.bytes_)


def _hash_to_bytes_value(h: NodeHash) -> Value:
    """Convert a NodeHash to a canonical-bytes Bytes value."""
    return Bytes(h.bytes_)


# ---------------------------------------------------------------------------
# Sporocarp emission helper.
# ---------------------------------------------------------------------------


def emit_appetite_fruiting(
    axis_name: str,
    fruiting_value: float,
    at_cycle: int,
    causal_parents: tuple[NodeHash, ...] = (),
    payload: CanonicalBytes | None = None,
) -> Sporocarp:
    """Helper: emit a sporocarp for an APPETITE axis crossing its threshold.

    The most common sporocarp type — substrate observes its own appetite
    being satisfied by accumulated delta intake.
    """
    return Sporocarp(
        sporocarp_type="appetite_fruiting",
        axis_name=axis_name,
        fruiting_value=fruiting_value,
        at_cycle=at_cycle,
        causal_parent_hashes=causal_parents,
        payload_canonical_bytes=payload or CanonicalBytes(b""),
    )


def emit_mortality_signal(
    axis_name: str,
    fruiting_value: float,
    at_cycle: int,
    causal_parents: tuple[NodeHash, ...] = (),
) -> Sporocarp:
    """Helper: emit a sporocarp for a mortality-signal axis crossing
    threshold (per L1_HARD_RULES F7; mortality signal is CI-protected).

    Per L1_GOVERNANCE §4.4 endogenous-pair channel: this sporocarp at
    proposal time becomes a `self_euthanasia_proposal` (with operator
    witness; transmitted to anchor surface).
    """
    return Sporocarp(
        sporocarp_type="mortality_signal_threshold_crossed",
        axis_name=axis_name,
        fruiting_value=fruiting_value,
        at_cycle=at_cycle,
        causal_parent_hashes=causal_parents,
    )
