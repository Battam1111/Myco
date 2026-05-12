"""Mechanical-category singleton dimensions cluster (v0.8.8 merge).

Holds four mechanical dimensions that lack a letter-family peer:
:class:`AD1AdapterSilentSkip`, :class:`CS1ContractVersionSync`,
:class:`FR1FreshSubstrateInvariants`, :class:`SC1SchemaParity`.

These were left as per-file singletons in the v0.8.8 pass-1 cluster
merge because they don't share a letter prefix; the v0.8.8 pass-2
"maximum aggressive merge" directive (per substrate owner) consolidates
them here on file-count grounds. Cluster-merge follows the v0.8.8
substrate-wide consolidation policy (per L1 protocol.md, §R2 "one
module per dim" is an L3 organization choice — overrideable without
a molt). Section markers ``# === <DIM_ID> — ...`` preserve per-dim
review boundaries; git history holds the original per-file state.

Original per-file LOC (sum ~ 364, well within PA2 megafile cap):

* :class:`AD1AdapterSilentSkip` — adapter silent-skip pattern (72 LOC).
* :class:`CS1ContractVersionSync` — canon contract-version drift (94 LOC).
* :class:`FR1FreshSubstrateInvariants` — post-germination invariants (120 LOC).
* :class:`SC1SchemaParity` — canon JSON-Schema vs load_canon parity (78 LOC).
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any, ClassVar

import yaml

from myco.core.identity_cluster import MycoContext, Severity
from myco.homeostasis.primitives_cluster import Category, Dimension, Finding

__all__ = [
    "AD1AdapterSilentSkip",
    "CS1ContractVersionSync",
    "FR1FreshSubstrateInvariants",
    "SC1SchemaParity",
]


# =========================================================================
# === AD1 — formerly ad1_adapter_silent_skip.py (72 LOC)
# =========================================================================

#: Match `return []` (with optional whitespace).
_SILENT_SKIP_RE: re.Pattern[str] = re.compile(r"\breturn\s*\[\s*\]")


class AD1AdapterSilentSkip(Dimension):
    """Adapter modules must not silently return [] on failure.

    Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
    (L0 P2 永恒吞噬 = "missing a signal costs more than eating one too
    many"; craft v0.6.0 §F22 / Round 2 T17).

    v0.6.0 reshaped adapters to return failed-stub IngestResults
    instead of ``[]``. AD1 watches for regressions: literal
    ``return []`` patterns inside adapter ``ingest()`` methods.

    Severity: LOW at land, ramps to HIGH after 30 sessions.
    """

    id = "AD1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        adapters_root = ctx.substrate.root / "src" / "myco" / "ingestion" / "adapters"
        if not adapters_root.is_dir():
            return
        for path in adapters_root.glob("*.py"):
            if path.name == "__init__.py" or path.name == "protocol.py":
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for ln_num, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if _SILENT_SKIP_RE.search(line):
                    rel = path.relative_to(ctx.substrate.root).as_posix()
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"adapter silent-skip pattern `return []` at "
                            f"line {ln_num}; return failed-stub "
                            f"IngestResult instead (L0 P2)"
                        ),
                        path=rel,
                    )


# =========================================================================
# === CS1 — formerly cs1_contract_version_sync.py (94 LOC)
# =========================================================================


class CS1ContractVersionSync(Dimension):
    """Canon's ``synced_contract_version`` matches ``contract_version``.

    Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
    § "Dimension enumeration" (v0.5.8 addition, fixable HIGH).

    Lint-visible form of the contract-drift check that
    :mod:`myco.ingestion.hunger` reports as a reflex signal. Promoting
    to a first-class dim means drift is gateable at CI and
    ``myco immune --fix`` auto-fixes via the shared
    ``_sync_contract_version`` helper.

    Severity: HIGH. Drift erodes trust in the whole homeostasis loop.
    Fixable: True (idempotent YAML patch).
    """

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
        from myco.digestion.cluster import _sync_contract_version

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


# =========================================================================
# === FR1 — formerly fr1_fresh_substrate_invariants.py (120 LOC)
# =========================================================================


class FR1FreshSubstrateInvariants(Dimension):
    """Fresh-substrate directory invariants are satisfied post-germination.

    Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
    § "Dimension enumeration" (v0.5.8 addition).

    A healthy substrate has, at minimum:
    * ``_canon.yaml`` at the root,
    * the file declared in ``canon.identity.entry_point`` (usually MYCO.md),
    * ``notes/raw/`` + ``notes/integrated/`` as directories,
    * ``docs/`` as a directory.

    ``myco germinate`` creates all of these; FR1 detects post-germination
    loss (user deleted it, rogue write-surface wipe, botched merge).

    Severity: HIGH per missing root-level anchor (``_canon.yaml`` and
    the entry point are contract surfaces), MEDIUM for missing
    sub-directories (notes/raw/, notes/integrated/, docs/).

    Fixable: False. Repair is operator work (``mkdir`` or ``git restore``)
    so we don't paper over a real data loss.
    """

    id = "FR1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root
        canon = ctx.substrate.canon

        # 1) _canon.yaml
        canon_path = ctx.substrate.paths.canon
        if not canon_path.is_file():
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=Severity.HIGH,
                message=f"_canon.yaml missing at {root}",
                path="_canon.yaml",
            )

        # 2) entry point
        entry_name = canon.entry_point
        entry_path = root / entry_name
        if not entry_path.is_file():
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=Severity.HIGH,
                message=(
                    f"canon.identity.entry_point {entry_name!r} does "
                    f"not exist at substrate root"
                ),
                path=entry_name,
            )

        # 3) notes/raw, notes/integrated, docs — MEDIUM each
        # v0.8.4 root-cleanup: notes_dir is canon-configurable via
        # SubstratePaths.notes (defaults to "notes/").
        notes_dir = ctx.substrate.paths.notes
        for sub in ("raw", "integrated"):
            p = notes_dir / sub
            if not p.is_dir():
                rel = p.relative_to(root).as_posix()
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=Severity.MEDIUM,
                    message=(
                        f"{rel}/ directory missing — fresh substrates "
                        f"carry this directory; a missing one means "
                        f"either pre-v0.5 substrate layout or a user "
                        f"wipe. Restore (``git restore``) or mkdir."
                    ),
                    path=rel,
                )
        # v0.8.4 root-cleanup: docs_dir is canon-configurable.
        docs_path = ctx.substrate.paths.docs
        if not docs_path.is_dir():
            rel = docs_path.relative_to(root).as_posix()
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=Severity.MEDIUM,
                message=(
                    f"{rel}/ directory missing — fresh substrates "
                    f"carry this directory; a missing one means "
                    f"either pre-v0.5 substrate layout or a user "
                    f"wipe. Restore (``git restore``) or mkdir."
                ),
                path=rel,
            )


# =========================================================================
# === SC1 — formerly sc1_schema_parity.py (78 LOC)
# =========================================================================


class SC1SchemaParity(Dimension):
    """JSON-Schema and load_canon must agree on _canon.yaml shape.

    Governing doctrine: ``docs/architecture/L1_CONTRACT/canon_schema.md``
    + craft ``v0_5_9_immune_zero_craft_2026-04-21.md`` §"deferred SC1".
    v0.6.0 finally lands the dim.

    Severity: LOW at land, ramps to HIGH after 30 sessions. SC1 verifies
    that the JSON-Schema at ``docs/schema/canon.schema.json`` admits the
    substrate's ``_canon.yaml`` and that the kernel's ``load_canon``
    parser admits the same. Drift between the two is a SSoT split
    that this dim catches.
    """

    id = "SC1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # v0.8.5 — canon-configurable layout via SubstratePaths.canon/docs.
        canon_path = ctx.substrate.paths.canon
        schema_path = ctx.substrate.paths.docs / "schema" / "canon.schema.json"
        if not canon_path.is_file() or not schema_path.is_file():
            # Substrate may not ship the JSON-Schema (downstream substrates).
            return
        try:
            schema_data: Any = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=f"canon.schema.json failed to parse: {exc}",
                path="docs/schema/canon.schema.json",
            )
            return
        try:
            canon_data: Any = yaml.safe_load(canon_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return
        # Soft validation: required top-level keys named in schema.required
        # must be present in canon. Full jsonschema validation is deferred
        # to v0.6.x when jsonschema becomes a non-optional dependency.
        if isinstance(schema_data, dict) and isinstance(canon_data, dict):
            required = schema_data.get("required") or []
            for key in required:
                if key not in canon_data:
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"canon.schema.json declares required key {key!r} "
                            f"but _canon.yaml is missing it"
                        ),
                        path="_canon.yaml",
                    )
