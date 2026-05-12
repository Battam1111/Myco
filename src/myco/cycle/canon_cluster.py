"""Cluster module — v0.8.8 pass-4 merge of molt, graft.

=== molt ===
bump verb: mutate canon + append contract_changelog entry.

MAJOR 9 (v0.5): the first code path in Myco that *mutates* a
post-genesis ``_canon.yaml``. Operates in two shapes:

- ``myco molt --contract <new_version>`` — change
  ``_canon.yaml::contract_version`` (and ``synced_contract_version``,
  held in lockstep) to ``<new_version>``, then append a section to
  ``docs/contract_changelog.md`` describing the molt.
- ``myco molt --contract <new_version> --dry-run`` — preview only,
  writes nothing.

Write strategy: **line-level regex patch** on the known top-level
``contract_version:`` and ``synced_contract_version:`` fields. We do
NOT round-trip through ``pyyaml.safe_dump`` because pyyaml does not
preserve comments, key order, or the schema-annotation header that
``_canon.yaml`` relies on (per L1 ``canon_schema.md`` rule 1 — no
narrative comments, but the schema annotation on line 2 IS retained
structural metadata).

Post-write validation: re-invoke :func:`myco.core.canon.load_canon`
on the mutated file; abort and restore the original text on any
``CanonSchemaError``.

Governing manifest: ``docs/architecture/L3_IMPLEMENTATION/command_manifest.md``
(governance-verbs section, v0.5 — per v0.5.0 craft §R13, no new L2
surface.md was created; governance-verbs content lives at L3).

=== graft ===
``myco graft`` — substrate-local plugin introspection.

Serves L2 ``homeostasis.md`` (observability of grafted code) and L2
``extensibility.md`` (substrate-local plugin seam). The verb itself is
a life-cycle observer: a graft is the hyphal anastomosis where a
downstream substrate's own code fuses with the Myco kernel at import
time. This handler lets an agent enumerate, validate, or explain
those fused plugins without leaving the CLI.

History: ``docs/contract_changelog.md`` § v0.5.3 (fungal-vocabulary
rename + substrate-local extension seam).

Three mutually-exclusive modes:

- ``--list`` — every loaded local plugin (kind, name, source).
- ``--validate`` — re-import plugins cleanly and report any errors.
- ``--explain <name>`` — source path + docstring for one plugin.

Passing no flag is a usage error (the CLI must specify a mode). The
``--list`` and ``--validate`` exit codes are finding-driven: 0 when
clean, 1 when the validate pass surfaces any errors. ``--explain``
exit-codes 0 on a hit, raises UsageError on a miss.
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Mapping
from datetime import date as _date
from typing import Any

from myco.boundary.surface.manifest import load_manifest_with_overlay
from myco.core.canon import load_canon
from myco.core.identity_cluster import (
    CanonSchemaError,
    ContractError,
    MycoContext,
    Result,
    UsageError,
)
from myco.core.io_cluster import atomic_utf8_write, bounded_read_text
from myco.core.substrate_cluster import load_local_plugins
from myco.core.trust_cluster import check_write_allowed

# =========================================================================
# === molt — formerly molt.py
# =========================================================================

_VERSION_RE = re.compile(
    "^v?\\d+\\.\\d+\\.\\d+(?:[-.][A-Za-z0-9]+(?:\\.[A-Za-z0-9]+)*)?$"
)


def _patch_canon_field(text: str, field: str, new_value: str) -> str:
    """Regex-replace a top-level scalar field in ``_canon.yaml``.

    Matches a line of the shape ``<field>: "<value>"`` at column 0.
    Raises ``ContractError`` if the field is not found — callers
    should not invoke this for optional fields without checking first.
    """
    pattern = re.compile(
        f"""^(?P<prefix>{re.escape(field)}:\\s*)(?P<q>["\\'])[^"\\']*(?P=q)\\s*$""",
        re.MULTILINE,
    )
    if not pattern.search(text):
        raise ContractError(
            f"bump: could not locate top-level {field!r} line in _canon.yaml"
        )
    return pattern.sub(f'\\g<prefix>"{new_value}"', text, count=1)


def _insert_changelog_entry(text: str, new_section: str) -> str:
    """Insert ``new_section`` above the newest existing ``## v``
    heading in ``docs/contract_changelog.md``.

    The file structure is: intro header, ``---`` divider, entries
    newest-first. We find the first ``^## v`` line and insert the new
    section immediately before it, separated by a ``---`` fence.
    """
    match = re.search("^## v[^\\n]*$", text, re.MULTILINE)
    if not match:
        divider_match = re.search("^---\\s*$", text, re.MULTILINE)
        if divider_match:
            idx = divider_match.end()
            return text[:idx] + "\n\n" + new_section.rstrip() + "\n"
        return text.rstrip() + "\n\n" + new_section.rstrip() + "\n"
    idx = match.start()
    return text[:idx] + new_section.rstrip() + "\n\n---\n\n" + text[idx:]


def _render_changelog_section(*, new_version: str, old_version: str, today: str) -> str:
    return f"## {new_version} - {today} - Contract molt via `myco molt`\n\nReplaces `{old_version}` at `_canon.yaml::contract_version`. Issued via the `myco molt --contract {new_version}` agent-\ncallable verb. `synced_contract_version` is updated in\nlockstep.\n\n### What changed\n\n(Fill in: which R1-R7 rules, subsystem definitions, exit-code\ngrammar, lint-dimension semantics, or command manifest shapes\nchanged. `myco molt` only records the version; the authoring\nagent is responsible for this narrative.)\n\n### Break from {old_version}\n\n(Fill in: backward-compatibility note. If none, say so explicitly.)\n"


def molt_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: bump contract version + append changelog + waves.

    Line-level regex-patches ``_canon.yaml::contract_version`` (and
    ``synced_contract_version`` in lockstep), appends a section to
    ``docs/contract_changelog.md``, and increments ``waves.current``.
    Post-write validates by re-reading canon; rolls back atomically
    on ``CanonSchemaError``.
    """
    raw = args.get("contract")
    if not raw:
        raise UsageError(
            "bump: --contract <new_version> is required at v0.5 (package/schema variants will land in later releases)"
        )
    new_version = str(raw).strip()
    if not _VERSION_RE.match(new_version):
        raise UsageError(
            f"bump: contract version {new_version!r} does not match the expected shape (e.g. `v0.5.0`, `v0.5.0-alpha.1`, `v0.5.0.dev`)."
        )
    dry_run = bool(args.get("dry_run", False))
    today = str(args.get("date") or _date.today().isoformat())
    canon_path = ctx.substrate.paths.canon
    changelog_path = ctx.substrate.paths.docs / "contract_changelog.md"
    if not canon_path.is_file():
        raise ContractError(f"bump: canon not found at {canon_path}")
    original_canon = bounded_read_text(canon_path)
    old_version = str(ctx.substrate.canon.contract_version)
    if old_version == new_version:
        raise UsageError(
            f"bump: contract_version is already {new_version!r}; nothing to do"
        )
    patched_canon = _patch_canon_field(original_canon, "contract_version", new_version)
    try:
        patched_canon = _patch_canon_field(
            patched_canon, "synced_contract_version", new_version
        )
        synced_touched = True
    except ContractError:
        synced_touched = False
    if dry_run:
        return Result(
            exit_code=0,
            payload={
                "dry_run": True,
                "old_version": old_version,
                "new_version": new_version,
                "synced_touched": synced_touched,
                "canon_path": str(canon_path.relative_to(ctx.substrate.root)),
                "changelog_path": str(changelog_path.relative_to(ctx.substrate.root)),
                "canon_preview_head": "\n".join(patched_canon.splitlines()[:12]),
            },
        )
    check_write_allowed(ctx, canon_path, verb="molt:canon")
    atomic_utf8_write(canon_path, patched_canon)
    try:
        load_canon(canon_path)
    except CanonSchemaError as exc:
        atomic_utf8_write(canon_path, original_canon)
        raise ContractError(
            f"bump: post-write validation failed; canon restored. Underlying error: {exc}"
        ) from exc
    check_write_allowed(ctx, changelog_path, verb="molt:changelog")
    if changelog_path.exists():
        original_changelog = bounded_read_text(changelog_path)
    else:
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        original_changelog = "# Contract Changelog\n\nAppend-only record of contract-version bumps.\n\nFormat: one section per `contract_version`, newest first.\n\n---\n"
    new_section = _render_changelog_section(
        new_version=new_version, old_version=old_version, today=today
    )
    patched_changelog = _insert_changelog_entry(original_changelog, new_section)
    atomic_utf8_write(changelog_path, patched_changelog)
    waves_touched = False
    try:
        current_text = bounded_read_text(canon_path)
        waves_pattern = re.compile(
            "^(?P<prefix>\\s*current:\\s*)(?P<n>\\d+)\\s*$", re.MULTILINE
        )
        m = waves_pattern.search(current_text)
        if m is not None:
            new_n = int(m.group("n")) + 1
            new_text = (
                current_text[: m.start("n")] + str(new_n) + current_text[m.end("n") :]
            )
            atomic_utf8_write(canon_path, new_text)
            waves_touched = True
    except (OSError, ValueError):
        pass
    return Result(
        exit_code=0,
        payload={
            "dry_run": False,
            "old_version": old_version,
            "new_version": new_version,
            "synced_touched": synced_touched,
            "waves_touched": waves_touched,
            "canon_path": str(canon_path.relative_to(ctx.substrate.root)),
            "changelog_path": str(changelog_path.relative_to(ctx.substrate.root)),
        },
    )


# =========================================================================
# === graft — formerly graft.py
# =========================================================================

def _collect_plugins(ctx: MycoContext) -> list[dict[str, Any]]:
    """Introspect kernel registries + overlay for every loaded plugin.

    Returns a list of ``{kind, name, source, scope}`` dicts. Fields:

    - ``kind``: one of ``"dimension"``, ``"adapter"``,
      ``"schema_upgrader"``, ``"overlay_verb"``.
    - ``source``: the source file path (best effort — may be
      ``"<unknown>"`` for in-memory registrations).
    - ``scope`` (v0.5.22): one of ``"kernel"`` (shipped with the myco
      package) or ``"substrate"`` (loaded from
      ``<root>/.myco/plugins/`` or ``manifest_overlay.yaml``). This
      lets callers like ``hunger`` and ``brief`` count only genuinely
      substrate-local contributions — pre-v0.5.22 those verbs
      conflated the two and reported "32 local plugins" on every
      fresh substrate. See ``docs/contract_changelog.md::v0.5.22`` for
      the full narrative.
    """
    from pathlib import Path

    substrate_plugins_root = (ctx.substrate.root / ".myco" / "plugins").resolve()

    def _classify_scope(src: str) -> str:
        """Return ``"substrate"`` iff ``src`` is a real path under
        ``<root>/.myco/plugins/``; ``"kernel"`` otherwise. Unknown
        or unresolvable paths fall through as ``"kernel"`` — we would
        rather undercount than mislabel a built-in.
        """
        if not src or src == "<unknown>":
            return "kernel"
        try:
            src_resolved = Path(src).resolve()
        except OSError:
            return "kernel"
        try:
            src_resolved.relative_to(substrate_plugins_root)
        except ValueError:
            return "kernel"
        return "substrate"

    plugins: list[dict[str, Any]] = []
    try:
        from myco.homeostasis.primitives_cluster import default_registry

        reg = default_registry()
        for dim in reg.all():
            dim_cls = type(dim)
            try:
                src = inspect.getsourcefile(dim_cls) or "<unknown>"
            except TypeError:
                src = "<unknown>"
            plugins.append(
                {
                    "kind": "dimension",
                    "name": getattr(dim_cls, "id", dim_cls.__name__),
                    "source": src,
                    "scope": _classify_scope(src),
                }
            )
    except Exception:
        pass
    try:
        from myco.ingestion import adapters as _adapters_mod

        for ad in _adapters_mod.all_adapters():
            ad_cls = type(ad)
            try:
                src = inspect.getsourcefile(ad_cls) or "<unknown>"
            except TypeError:
                src = "<unknown>"
            plugins.append(
                {
                    "kind": "adapter",
                    "name": ad_cls.__name__,
                    "source": src,
                    "scope": _classify_scope(src),
                }
            )
    except Exception:
        pass
    try:
        from myco.core.canon import schema_upgraders

        for key, fn in schema_upgraders.items():
            try:
                src = inspect.getsourcefile(fn) or "<unknown>"
            except TypeError:
                src = "<unknown>"
            plugins.append(
                {
                    "kind": "schema_upgrader",
                    "name": str(key),
                    "source": src,
                    "scope": _classify_scope(src),
                }
            )
    except Exception:
        pass
    try:
        manifest = load_manifest_with_overlay(ctx.substrate.root)
        base_names = {c.name for c in load_manifest_with_overlay(None).commands}
        for c in manifest.commands:
            if c.name in base_names:
                continue
            plugins.append(
                {
                    "kind": "overlay_verb",
                    "name": c.name,
                    "source": str(ctx.substrate.paths.manifest_overlay),
                    "scope": "substrate",
                }
            )
    except Exception:
        pass
    return plugins


def _validate(ctx: MycoContext) -> list[str]:
    """Re-import ``.myco/plugins/`` in isolation and return errors.

    We reuse :func:`load_local_plugins` and ask it to try loading again.
    Because it's idempotent (returns the cached module when the same
    module_name is already in ``sys.modules``), we first pop any
    previous entry so the reload is clean. Errors the reload surfaces
    end up in the returned list.
    """
    import sys as _sys

    from myco.core.substrate_cluster import _substrate_plugin_module_name

    mod_name = _substrate_plugin_module_name(ctx.substrate.root, ctx.substrate.canon)
    _sys.modules.pop(mod_name, None)
    result = load_local_plugins(ctx.substrate.root, canon=ctx.substrate.canon)
    return list(result.errors)


def _explain(ctx: MycoContext, name: str) -> dict[str, Any]:
    """Return kind/source/docstring for a named plugin, or raise."""
    for entry in _collect_plugins(ctx):
        if entry["name"] == name:
            kind = entry["kind"]
            source = entry["source"]
            docstring = ""
            try:
                if kind == "dimension":
                    from myco.homeostasis.primitives_cluster import default_registry

                    reg = default_registry()
                    if reg.has(name):
                        docstring = (type(reg.get(name)).__doc__ or "").strip()
                elif kind == "adapter":
                    from myco.ingestion import adapters as _adapters_mod

                    for ad in _adapters_mod.all_adapters():
                        if type(ad).__name__ == name:
                            docstring = (type(ad).__doc__ or "").strip()
                            break
                elif kind == "schema_upgrader":
                    from myco.core.canon import schema_upgraders

                    fn = schema_upgraders.get(name)
                    if fn is not None:
                        docstring = (fn.__doc__ or "").strip()
                elif kind == "overlay_verb":
                    manifest = load_manifest_with_overlay(ctx.substrate.root)
                    docstring = manifest.by_name(name).summary
            except Exception:
                docstring = ""
            return {
                "name": name,
                "kind": kind,
                "source": source,
                "docstring": docstring,
            }
    raise UsageError(
        f"graft --explain: unknown plugin name {name!r}. Run `myco graft --list` to see the full set."
    )


def graft_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: enumerate / validate / explain local plugins.

    Dispatches on the mutually-exclusive ``list`` / ``validate`` /
    ``explain`` / ``list-substrates`` flags. Passing none is a
    ``UsageError``; validate's exit code is finding-driven, the
    others always return 0 on hit.

    v0.5.16 adds ``--list-substrates`` which returns every substrate
    registered in ``~/.myco/substrates.yaml`` (cross-project
    enumeration, not just this substrate's grafts).
    """
    list_mode = bool(args.get("list"))
    validate_mode = bool(args.get("validate"))
    explain_name = args.get("explain")
    list_substrates_mode = bool(args.get("list_substrates"))
    modes_set = sum(
        [
            1 if list_mode else 0,
            1 if validate_mode else 0,
            1 if explain_name else 0,
            1 if list_substrates_mode else 0,
        ]
    )
    if modes_set == 0:
        raise UsageError(
            "graft: specify exactly one of --list / --validate / --explain / --list-substrates."
        )
    if modes_set > 1:
        raise UsageError(
            "graft: --list / --validate / --explain / --list-substrates are mutually exclusive."
        )
    if list_mode:
        plugins = _collect_plugins(ctx)
        return Result(
            exit_code=0,
            payload={"mode": "list", "plugins": plugins, "count": len(plugins)},
        )
    if validate_mode:
        errors = _validate(ctx)
        return Result(
            exit_code=1 if errors else 0,
            payload={"mode": "validate", "errors": errors, "ok": not errors},
        )
    if list_substrates_mode:
        from myco.core.substrate_cluster import list_substrates

        entries = list_substrates()
        return Result(
            exit_code=0,
            payload={
                "mode": "list-substrates",
                "substrates": [
                    {
                        "substrate_id": e.substrate_id,
                        "path": str(e.path),
                        "registered_at": e.registered_at.isoformat(),
                        "last_seen_at": e.last_seen_at.isoformat(),
                        "exists": e.exists,
                    }
                    for e in entries
                ],
                "count": len(entries),
                "live_count": sum(1 for e in entries if e.exists),
                "stale_count": sum(1 for e in entries if not e.exists),
            },
        )
    info = _explain(ctx, str(explain_name).strip())
    return Result(exit_code=0, payload={"mode": "explain", **info})
