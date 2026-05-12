"""``example_overlay`` — reference substrate-local plugin (L0 P5).

This package is what the L0 P5 promise looks like in code: a
self-contained directory under ``.myco/plugins/`` that contributes
one dimension and one overlay verb to the substrate it lives in,
without touching the kernel.

Import-time contract (the only contract — there is no plugin-loader
bytecode that scans this for hooks; we register via Myco's documented
public functions):

1. **Manifest validation**: read ``plugin.json`` from the same
   directory, confirm the required keys are present, raise on missing
   ``name`` (this surfaces in ``Substrate.local_plugin_errors`` →
   ``hunger.local_plugins.errors`` per the v0.5.3 protocol).

2. **Dimension registration**: call
   :func:`myco.homeostasis.registry.register_external_dimension` with
   :class:`XYZ1RawNoteThreshold`. The dim then participates in every
   ``default_registry()`` build (immune runs, graft --list, brief, etc.).

3. **Overlay-verb handler**: expose ``example_echo_handler`` at module
   scope. The substrate's ``.myco/manifest_overlay.yaml`` declares the
   ``example-echo`` verb whose ``handler:`` field points at
   ``plugins.example_overlay:example_echo_handler``. On dispatch the
   surface layer imports that path and calls it with ``(args, ctx=ctx)``.

If any of those steps fails the loader captures the exception and the
substrate keeps running with empty plugin state — Myco's "broken
plugins are loud, not fatal" doctrine (see
``docs/architecture/L2_DOCTRINE/homeostasis.md`` § "substrate-local
plugin health" + the MF2 dimension).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from myco.core.context import MycoContext, Result
from myco.core.errors import ContractError
from myco.homeostasis.registry import register_external_dimension

from .xyz1_raw_note_threshold import XYZ1RawNoteThreshold

__all__ = [
    "PLUGIN_MANIFEST",
    "example_echo_handler",
]


# ---------------------------------------------------------------------------
# Manifest validation — fail loudly on a malformed plugin.json so the
# error reaches Substrate.local_plugin_errors (and from there hunger /
# brief / immune via MF2).
# ---------------------------------------------------------------------------


_REQUIRED_MANIFEST_KEYS: frozenset[str] = frozenset(
    {"name", "version", "kind", "entry_point"}
)


def _load_and_validate_manifest() -> dict[str, Any]:
    """Load ``plugin.json`` from this package and validate required keys.

    Raises :class:`myco.core.errors.ContractError` (subclass of
    ``MycoError``) on:

    - missing file,
    - non-mapping top level,
    - any required key missing or non-string,
    - JSON parse error.

    The error message names the missing/offending key so the operator
    knows what to fix when it surfaces in ``hunger.local_plugins.errors``.
    """
    manifest_path = Path(__file__).resolve().parent / "plugin.json"
    if not manifest_path.is_file():
        raise ContractError(f"example_overlay: plugin.json missing at {manifest_path}")
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError(
            f"example_overlay: plugin.json is not valid JSON: {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise ContractError(
            f"example_overlay: plugin.json top level must be an object, "
            f"got {type(raw).__name__}"
        )
    for key in _REQUIRED_MANIFEST_KEYS:
        if key not in raw:
            raise ContractError(
                f"example_overlay: plugin.json missing required field {key!r}"
            )
        if not isinstance(raw[key], str) or not raw[key].strip():
            raise ContractError(
                f"example_overlay: plugin.json field {key!r} must be a "
                f"non-empty string, got {raw[key]!r}"
            )
    return raw


#: Validated manifest dict. Tests inspect this to confirm the
#: validation actually ran; production callers should not rely on it.
PLUGIN_MANIFEST: dict[str, Any] = _load_and_validate_manifest()


# ---------------------------------------------------------------------------
# Dimension registration — side effect at import time.
# ---------------------------------------------------------------------------


register_external_dimension(XYZ1RawNoteThreshold)


# ---------------------------------------------------------------------------
# Overlay-verb handler — invoked by manifest dispatch.
# ---------------------------------------------------------------------------


def example_echo_handler(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """``example-echo`` — return the ``message`` argument verbatim.

    Trivial by design — the point is to exercise the verb-overlay
    dispatch path end-to-end: manifest_overlay.yaml is parsed, the
    handler string ``plugins.example_overlay:example_echo_handler`` is
    resolved via ``importlib``, and this function is called with the
    handler contract ``(args, *, ctx) -> Result``.

    Manifest declares ``message`` as a required ``str`` arg. A missing
    arg raises ``UsageError`` at the manifest layer before we get here,
    so the empty-string branch only fires when the operator passes the
    sentinel ``message=""``.
    """
    # ``ctx`` is part of the handler contract (every non-pre-substrate
    # verb receives it) but example-echo is pure — we pin a reference
    # so linters don't flag the unused parameter, then ignore it.
    _ = ctx

    raw = args.get("message", "")
    message = "" if raw is None else str(raw)
    return Result(
        exit_code=0,
        payload={
            "verb": "example-echo",
            "message": message,
            "echoed": message,
            "plugin": PLUGIN_MANIFEST["name"],
            "plugin_version": PLUGIN_MANIFEST["version"],
        },
    )
