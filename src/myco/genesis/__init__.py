"""``myco.genesis`` — one-time substrate bootstrap.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/genesis.md``.
Craft: ``docs/primordia/stage_b3_genesis_craft_2026-04-15.md``.

Responsibility: create the initial substrate from scratch — write a fresh
``_canon.yaml`` from template, seed ``notes/`` and ``docs/``, drop the
skeleton marker, and render the agent-entry file. Genesis is one-shot:
re-invocation on an established substrate raises ``ContractError``.
"""

from .genesis import (
    DEFAULT_CONTRACT_VERSION,
    DEFAULT_ENTRY_POINT,
    bootstrap,
)

__all__ = [
    "bootstrap",
    "DEFAULT_CONTRACT_VERSION",
    "DEFAULT_ENTRY_POINT",
]
