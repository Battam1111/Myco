"""CS1 — ``synced_contract_version`` matches ``contract_version``.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (v0.5.8 addition, fixable HIGH).


This is the lint-visible form of the contract-drift check that
:mod:`myco.ingestion.hunger` also reports as a reflex signal.
Promoting it to a first-class dimension means:

- ``myco immune`` surfaces drift even when hunger wasn't called.
- Drift is gateable at CI via the standard severity ladder.
- ``myco immune --fix`` autofixes by delegating to the same
  ``_sync_contract_version`` helper that
  :mod:`myco.digestion.assimilate` uses.

Severity: HIGH. Drift between ``synced_contract_version`` and the
kernel's ``contract_version`` means the substrate's advice
pipeline is stale; every ``hunger`` run will keep whining about it.
Left unresolved, drift erodes trust in the whole homeostasis loop.

Fixable: True. The repair is a one-line YAML patch — same shape as
``assimilate`` uses. The fix is idempotent: if the fields already
match, ``applied=False``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["CS1ContractVersionSync"]


class CS1ContractVersionSync(Dimension):
    """Canon's ``synced_contract_version`` matches ``contract_version``."""

    id = "CS1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = True

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        canon = ctx.substrate.canon
        synced = canon.synced_contract_version
        current = canon.contract_version
        if synced == current:
            return
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=self.default_severity,
            message=(
                f"canon.synced_contract_version ({synced!r}) differs "
                f"from canon.contract_version ({current!r}); run "
                f"`myco assimilate` or `myco immune --fix` to close "
                f"the drift."
            ),
            path="_canon.yaml",
            fixable=True,
        )

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """Patch ``synced_contract_version`` in-place via the shared helper.

        Delegates to :func:`myco.digestion.assimilate._sync_contract_version`
        so drift reconciliation uses a single code path. Returns
        ``applied=True`` if a write occurred, ``applied=False`` if the
        canon was already synced (idempotent re-run).
        """
        _ = finding
        from myco.digestion.assimilate import _sync_contract_version

        try:
            changed = _sync_contract_version(ctx)
        except OSError as exc:
            return {"applied": False, "detail": f"canon write failed: {exc}"}
        if not changed:
            return {
                "applied": False,
                "detail": "canon.synced_contract_version already matches",
            }
        return {
            "applied": True,
            "detail": (
                f"updated canon.synced_contract_version to "
                f"{ctx.substrate.canon.contract_version!r}"
            ),
        }
