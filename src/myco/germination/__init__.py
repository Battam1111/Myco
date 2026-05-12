"""``myco.germination`` — one-time substrate bootstrap.

v0.5.3 rename: was ``myco.genesis`` pre-rename. The planned
``myco.genesis`` shim never shipped (the pre-rename package was
fully excreted at v0.6.0); the L2 doctrine page keeps the
``genesis.md`` filename for governance archeology purposes only.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/genesis.md``.
History: see ``docs/contract_changelog.md`` § v0.4.0 + § v0.5.3.

Responsibility: create the initial substrate from scratch — write a
fresh canon (default ``_canon.yaml`` at root; v0.8.4+ substrates may
relocate to ``.myco/canon.yaml`` via the canon-configurable
``system.canon_filename`` field after germination), seed ``notes/``
and ``docs/``, drop the skeleton marker, and render the agent-entry
file. Germinate is one-shot: re-invocation on an established
substrate raises ``ContractError``.
"""

from .germinate import (
    DEFAULT_CONTRACT_VERSION,
    DEFAULT_ENTRY_POINT,
    bootstrap,
    run_cli,
)

__all__ = [
    "bootstrap",
    "run_cli",
    "DEFAULT_CONTRACT_VERSION",
    "DEFAULT_ENTRY_POINT",
]
