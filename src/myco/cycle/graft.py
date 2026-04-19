"""``myco graft`` — substrate-local plugin introspection.

Serves L2 ``homeostasis.md`` (observability of grafted code) and L2
``extensibility.md`` (substrate-local plugin seam). The verb itself is
a life-cycle observer: a graft is the hyphal anastomosis where a
downstream substrate's own code fuses with the Myco kernel at import
time. This handler lets an agent enumerate, validate, or explain
those fused plugins without leaving the CLI.

Governing craft:
``docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md``.

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
from collections.abc import Mapping
from typing import Any

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError
from myco.core.substrate import load_local_plugins
from myco.surface.manifest import load_manifest_with_overlay

__all__ = ["run"]


def _collect_plugins(ctx: MycoContext) -> list[dict[str, Any]]:
    """Introspect kernel registries + overlay for substrate-local plugins.

    Returns a list of ``{kind, name, source}`` dicts. ``kind`` is one
    of ``"dimension"``, ``"adapter"``, ``"schema_upgrader"``,
    ``"overlay_verb"``. ``source`` is the source file path (best
    effort — may be ``"<unknown>"`` for registered-in-memory items).
    """
    plugins: list[dict[str, Any]] = []

    # Dimensions (from the default registry — includes anything a
    # local plugin registered via ``register_external_dimension``).
    try:
        from myco.homeostasis import registry as _reg_mod

        reg = _reg_mod.default_registry()
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
                }
            )
    except Exception:
        pass

    # Adapters.
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
                }
            )
    except Exception:
        pass

    # Schema upgraders.
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
                }
            )
    except Exception:
        pass

    # Overlay verbs.
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

    from myco.core.substrate import _substrate_plugin_module_name

    mod_name = _substrate_plugin_module_name(ctx.substrate.root, ctx.substrate.canon)
    # Force a fresh import pass.
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
                    from myco.homeostasis import registry as _reg_mod

                    reg = _reg_mod.default_registry()
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
        f"graft --explain: unknown plugin name {name!r}. Run "
        f"`myco graft --list` to see the full set."
    )


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    list_mode = bool(args.get("list"))
    validate_mode = bool(args.get("validate"))
    explain_name = args.get("explain")

    modes_set = sum(
        [
            1 if list_mode else 0,
            1 if validate_mode else 0,
            1 if explain_name else 0,
        ]
    )
    if modes_set == 0:
        raise UsageError(
            "graft: specify exactly one of --list / --validate / --explain."
        )
    if modes_set > 1:
        raise UsageError(
            "graft: --list / --validate / --explain are mutually exclusive."
        )

    if list_mode:
        plugins = _collect_plugins(ctx)
        return Result(
            exit_code=0,
            payload={
                "mode": "list",
                "plugins": plugins,
                "count": len(plugins),
            },
        )

    if validate_mode:
        errors = _validate(ctx)
        return Result(
            exit_code=1 if errors else 0,
            payload={
                "mode": "validate",
                "errors": errors,
                "ok": not errors,
            },
        )

    # explain mode
    info = _explain(ctx, str(explain_name).strip())
    return Result(
        exit_code=0,
        payload={
            "mode": "explain",
            **info,
        },
    )
