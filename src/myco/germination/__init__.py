"""``myco.germination`` — one-time substrate bootstrap.

v0.5.3: was ``myco.genesis`` pre-rename. The shim at
``myco.genesis`` re-exports this module so existing imports keep
working across the 0.x line.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/genesis.md``.
Craft: ``docs/primordia/stage_b3_genesis_craft_2026-04-15.md``.

Responsibility: create the initial substrate from scratch — write a
fresh ``_canon.yaml`` from template, seed ``notes/`` and ``docs/``,
drop the skeleton marker, and render the agent-entry file.
Germinate is one-shot: re-invocation on an established substrate
raises ``ContractError``.
"""

from .germinate import (
    DEFAULT_CONTRACT_VERSION,
    DEFAULT_ENTRY_POINT,
    bootstrap,
    run_cli,
)

load_autoseeded = None  # Not present in current code; shim alias only.

__all__ = [
    "bootstrap",
    "run_cli",
    "DEFAULT_CONTRACT_VERSION",
    "DEFAULT_ENTRY_POINT",
]
