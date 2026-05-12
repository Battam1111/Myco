"""Controlled regression coverage for the ``myco.mcp`` legacy shim.

Background: at v0.6.0 the boundary subsystem landed and the kernel
relocated ``myco.{mcp,surface,install,symbionts}`` to
``myco.boundary.<sub>``. The legacy top-level ``myco.mcp`` was
deleted (Round 5 owner directive). v0.6.10 / 0.6.11 / 0.6.12 shipped
without a shim. A v0.6.12 dogfood report showed Cowork's
Local-MCP-Server config still spelling its command
``python -m myco.mcp``; every spawn died with
``ModuleNotFoundError: No module named 'myco.mcp'``. v0.6.13 restored
the path as a thin re-export of ``myco.boundary.mcp`` plus a stderr
deprecation pointer + a ``DeprecationWarning`` for test harnesses.

**Why this single, controlled test exists.** Per
``docs/architecture/L2_DOCTRINE/boundary.md`` § "Public-API deletion
discipline (v0.7.1-named, v0.7.3-canonized)", the shim is gated for
sunset on **gate (b) telemetry verification**: ≥
``governance.shim_sunset_min_zero_cycles`` (7) senesce cycles AND
≥ ``governance.shim_sunset_min_zero_days`` (7) wall-clock days with
**zero hits** to ``.myco/state/shim_hits.json``. Every accidental
``import myco.mcp`` from a test resets that gate.

The pre-v0.7.5 layout had **five** tests in
``tests/unit/boundary/test_legacy_mcp_shim.py``, one of which spawned
``python -m myco.mcp --help`` as a subprocess; that subprocess hit
the substrate's ``__main__._record_shim_hit()`` against the real
``.myco/state/shim_hits.json`` once **per pytest run**, accumulating
28 spurious hits over the v0.7.2 → v0.7.4 release window. The
sunset gate could not naturally close because the substrate's own
test suite was the loudest non-operator consumer of the shim.

This file replaces those five tests with **one** controlled test that
pins the shim's full external contract — DeprecationWarning text,
stderr pointer, public-symbol re-export identity, and the
``_record_shim_hit()`` JSONL append shape — while routing **every**
side effect (the ``shim_hits.json`` write) to a ``tmp_path``
substrate. The real ``.myco/state/shim_hits.json`` is never touched.

Doctrine refs:
- ``docs/architecture/L2_DOCTRINE/boundary.md`` § Legacy import shims
- ``docs/architecture/L2_DOCTRINE/boundary.md`` § Public-API deletion
  discipline (gates a + b)

The contract checks below MUST stay in lockstep with
``src/myco/mcp/__init__.py`` and ``src/myco/mcp/__main__.py``. If a
future revision re-words the deprecation message or moves the
telemetry hook, update the asserts here in the same change — the
v0.7.4-noted v0.7.0 incident exists precisely because nothing in the
test suite pinned the user-visible contract before deletion.
"""

from __future__ import annotations

import importlib
import json
import sys
import warnings
from pathlib import Path

import pytest


def test_shim_contract_warning_stderr_reexport_and_telemetry(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Single controlled pin of the entire ``myco.mcp`` shim contract.

    Five sub-assertions, all on one fresh import + one
    ``_record_shim_hit()`` invocation against a ``tmp_path`` substrate:

    1. ``import myco.mcp`` succeeds and exposes ``build_server`` /
       ``main`` (the only documented public symbols of the shim).
    2. The exported symbols are byte-identical (``is``-equal, not
       merely value-equal) to ``myco.boundary.mcp.{build_server,main}``
       — the shim is a thin re-export, not a duplicate code path.
    3. The import emits a ``DeprecationWarning`` whose message
       contains the marker phrase ``"v0.6.13 back-compat shim"`` (so
       lint hooks + downstream substrates can trip on the canonical
       text via the standard warnings filter).
    4. The import writes the operator-readable pointer
       ``"myco.mcp: deprecated"`` to **stderr** (not stdout — stdout
       is the JSON-RPC frame channel; corrupting it disconnects the
       MCP host).
    5. ``_record_shim_hit()`` against a substrate whose
       ``MYCO_PROJECT_DIR`` points at ``tmp_path`` appends exactly
       one JSONL record to ``<tmp_path>/.myco/state/shim_hits.json``,
       with ``module == "myco.mcp"`` and a populated ``ts`` /
       ``session_id``. The real ``.myco/state/shim_hits.json`` is
       never written to.
    """
    # --- (a) Stage a tmp substrate so _record_shim_hit() finds canon.
    (tmp_path / "_canon.yaml").write_text(
        'schema_version: "2"\ncontract_version: "v0.7.4"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCO_PROJECT_DIR", str(tmp_path))

    # --- (b) Reload the shim under a recording warnings filter. The
    #         capfd fixture captures the stderr pointer in parallel.
    sys.modules.pop("myco.mcp", None)
    sys.modules.pop("myco.mcp.__main__", None)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", DeprecationWarning)
        shim = importlib.import_module("myco.mcp")
    stderr_after_import = capfd.readouterr()

    # --- 1. Module loads + public surface present.
    assert shim is not None
    assert hasattr(shim, "build_server")
    assert hasattr(shim, "main")

    # --- 2. Re-export identity vs canonical (catches drift if a future
    #        commit copy-pastes a divergent ``main`` into the shim).
    from myco.boundary import mcp as canonical

    assert shim.build_server is canonical.build_server
    assert shim.main is canonical.main

    # --- 3. DeprecationWarning fired + carries the canonical marker.
    deprecations = [w for w in captured if issubclass(w.category, DeprecationWarning)]
    assert deprecations, "shim must emit a DeprecationWarning on import"
    msg = str(deprecations[0].message)
    assert "v0.6.13 back-compat shim" in msg, (
        f"deprecation marker phrase missing from message: {msg!r}"
    )

    # --- 4. Stderr pointer present, stdout uncontaminated.
    assert stderr_after_import.out == "", (
        "stdout must stay clean — it is the MCP JSON-RPC frame channel; "
        f"got: {stderr_after_import.out!r}"
    )
    assert "myco.mcp: deprecated" in stderr_after_import.err, (
        f"stderr pointer missing; got: {stderr_after_import.err!r}"
    )

    # --- 5. Telemetry append: one JSONL record under tmp_path.
    #        Direct call to the shim's ``__main__`` hook — the
    #        function lives only there, so this is the only legitimate
    #        from-myco.mcp.__main__ import in the suite.
    from myco.mcp.__main__ import _record_shim_hit

    _record_shim_hit()
    hits_path = tmp_path / ".myco/state" / "shim_hits.json"
    assert hits_path.is_file(), "shim hit telemetry file not created"
    lines = [
        line for line in hits_path.read_text(encoding="utf-8").splitlines() if line
    ]
    assert len(lines) == 1, (
        f"expected exactly one telemetry record under tmp substrate, got {len(lines)}"
    )
    record = json.loads(lines[0])
    assert record["module"] == "myco.mcp"
    assert record.get("ts"), "telemetry record missing ts"
    assert record.get("session_id"), "telemetry record missing session_id"


def test_shim_telemetry_silent_when_substrate_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_record_shim_hit`` must never raise when canon is missing.

    Co-located with the contract pin above to keep all shim coverage
    in one file (so the v0.7.4 sunset audit is one-grep-able). Re-uses
    the already-imported ``_record_shim_hit`` symbol from the previous
    test's import chain, so this test does NOT re-trigger the
    one-shot deprecation warning.

    v0.7.0 incident lesson (boundary.md § "Public-API deletion
    discipline"): the shim's telemetry path MUST silent-fail on
    read-only / non-substrate cwd, otherwise a missing canon would
    crash the MCP server boot.

    Test isolation: ``_record_shim_hit`` resolves a substrate via
    ``MYCO_PROJECT_DIR`` first, then falls through to ``Path.cwd()``.
    Without ``monkeypatch.chdir`` the cwd would be the real Myco
    substrate root and the silent-no-op assertion would actually
    *append* to the real ``.myco/state/shim_hits.json``, which is
    exactly the leak this entire migration is closing. Both env and
    cwd must point at non-substrates for the assertion to be sound.
    """
    bare = tmp_path / "not_a_substrate"
    bare.mkdir()
    monkeypatch.setenv("MYCO_PROJECT_DIR", str(bare))
    monkeypatch.chdir(bare)

    from myco.mcp.__main__ import _record_shim_hit

    _record_shim_hit()  # must not raise
    assert not (bare / ".myco/state").exists(), (
        "telemetry path must silent-fail when canon is absent — "
        "creating .myco/state on a non-substrate dir would be a leak"
    )
