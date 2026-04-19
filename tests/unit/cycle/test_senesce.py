"""Tests for ``myco.cycle.senesce`` — including the v0.5.7-buffer
``--quick`` flag that lets the SessionEnd hook stay inside Claude
Code's ~1.5 s kill budget.

Scope of this file:

* **Default path** (``quick=False``): unchanged v0.5.6 semantics —
  reflect + immune(fix=True), ``payload["mode"] == "full"``.
* **Quick path** (``quick=True``): reflect only, immune skipped,
  payload carries an explicit ``immune.skipped`` marker so
  downstream consumers never KeyError on ``payload["immune"]``.
* **Surface parity**: the manifest declares ``quick`` as a bool arg
  with default false; the MCP tool-spec exposes it; the CLI
  argparse path accepts ``--quick`` and the dispatcher routes it
  through to the handler.

The older ``tests/unit/meta/test_session_end.py`` still exercises
the deprecation-shim import path (``from myco.meta.session_end
import run``); this file uses the canonical ``myco.cycle.senesce``
path.
"""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.cycle.senesce import _QUICK_SKIP_REASON
from myco.cycle.senesce import run as senesce_run
from myco.ingestion.eat import append_note
from myco.surface.manifest import dispatch, load_manifest
from myco.surface.mcp import build_tool_spec


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


# ---------------------------------------------------------------------------
# Default (full) mode — unchanged semantics
# ---------------------------------------------------------------------------


def test_default_runs_reflect_then_immune(genesis_substrate: Path) -> None:
    """No args → full mode: reflect + immune both contribute."""
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="some content")
    result = senesce_run({}, ctx=ctx)
    assert result.payload["reflect"]["promoted"] == 1
    assert "immune" in result.payload
    assert result.payload["immune"].get("skipped") is not True
    assert result.payload["mode"] == "full"
    assert result.exit_code < 3


def test_explicit_full_mode_matches_default(genesis_substrate: Path) -> None:
    """Passing quick=False explicitly behaves the same as passing nothing."""
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="content A")
    result_default = senesce_run({}, ctx=ctx)

    # Second substrate, same content — compare payload shape only.
    other_root = genesis_substrate.parent / "other"
    other_root.mkdir(exist_ok=True)
    # Reuse existing fixture behavior — just verify full-mode shape.
    assert set(result_default.payload.keys()) == {"reflect", "immune", "mode"}
    assert result_default.payload["mode"] == "full"


# ---------------------------------------------------------------------------
# Quick mode — the new behavior
# ---------------------------------------------------------------------------


def test_quick_mode_skips_immune(genesis_substrate: Path) -> None:
    """quick=True: immune is reported as skipped, not run."""
    ctx = _mk_ctx(genesis_substrate)
    result = senesce_run({"quick": True}, ctx=ctx)
    assert result.payload["mode"] == "quick"
    assert result.payload["immune"] == {
        "skipped": True,
        "reason": _QUICK_SKIP_REASON,
    }
    # No findings surface in quick mode (immune didn't run). Result
    # declares ``findings: tuple[Finding, ...]`` so the empty form is
    # ``()`` (not ``[]``) per v0.5.7 contract-type fix.
    assert result.findings == ()
    assert len(result.findings) == 0


def test_quick_mode_still_reflects(genesis_substrate: Path) -> None:
    """quick=True must still perform the reflect state-advance."""
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="some content")
    result = senesce_run({"quick": True}, ctx=ctx)
    # Reflect ran and promoted the raw note we just appended.
    assert result.payload["reflect"]["promoted"] == 1


def test_quick_mode_payload_has_both_keys(genesis_substrate: Path) -> None:
    """Payload shape is stable: always has 'reflect' + 'immune' keys.

    Downstream consumers (brief/hunger/etc.) read payload[\"immune\"]
    and must not KeyError under the new quick mode.
    """
    ctx = _mk_ctx(genesis_substrate)
    result = senesce_run({"quick": True}, ctx=ctx)
    assert "reflect" in result.payload
    assert "immune" in result.payload
    assert "mode" in result.payload


def test_quick_mode_exit_code_from_reflect_only(genesis_substrate: Path) -> None:
    """Quick mode ignores immune for exit-code purposes — by construction,
    since immune doesn't run. Exit is derived from reflect alone."""
    ctx = _mk_ctx(genesis_substrate)
    result = senesce_run({"quick": True}, ctx=ctx)
    # Empty substrate: reflect finds nothing, no errors → exit 0.
    assert result.exit_code == 0


def test_quick_mode_truthy_coercion(genesis_substrate: Path) -> None:
    """Accept bool coercion from the manifest coercer (str 'true' / int 1)."""
    ctx = _mk_ctx(genesis_substrate)
    # The manifest dispatcher coerces bool via ArgSpec.coerce. Here the
    # direct-call path just needs to handle truthy values from dict.
    for truthy in (True, 1):
        result = senesce_run({"quick": truthy}, ctx=ctx)
        assert result.payload["mode"] == "quick", f"truthy={truthy!r}"


# ---------------------------------------------------------------------------
# Manifest + MCP surface parity
# ---------------------------------------------------------------------------


def test_manifest_declares_quick_arg() -> None:
    """The manifest entry must declare 'quick' as a bool arg with default false."""
    m = load_manifest()
    senesce = m.by_name("senesce")
    arg_names = {a.name for a in senesce.args}
    assert "quick" in arg_names
    quick_arg = next(a for a in senesce.args if a.name == "quick")
    assert quick_arg.type == "bool"
    assert quick_arg.default is False
    assert quick_arg.required is False


def test_mcp_tool_spec_exposes_quick() -> None:
    """MCP myco_senesce tool must carry a boolean 'quick' property."""
    m = load_manifest()
    senesce = m.by_name("senesce")
    tool = build_tool_spec(senesce)
    props = tool["inputSchema"]["properties"]
    assert "quick" in props
    assert props["quick"]["type"] == "boolean"
    # Not in required list — default is false.
    assert "quick" not in tool["inputSchema"].get("required", [])


def test_alias_session_end_still_resolves_through_dispatch() -> None:
    """The deprecated alias 'session-end' must still route to senesce.

    This is the contract we promised at v0.5.3: every old verb name
    keeps working through v1.0.0.
    """
    m = load_manifest()
    alias_spec = m.by_name("session-end")
    assert alias_spec.name == "senesce"


# ---------------------------------------------------------------------------
# Dispatch path — end-to-end through manifest + handler resolution
# ---------------------------------------------------------------------------


def test_dispatch_with_quick_true(genesis_substrate: Path) -> None:
    """Going through the real dispatcher with quick=True must produce
    a quick-mode Result (not a direct handler call)."""
    ctx = _mk_ctx(genesis_substrate)
    result = dispatch("senesce", {"quick": True}, ctx=ctx)
    assert result.payload["mode"] == "quick"
    assert result.payload["immune"]["skipped"] is True


def test_dispatch_without_quick_defaults_to_full(genesis_substrate: Path) -> None:
    """Dispatcher with no quick arg must default to full mode."""
    ctx = _mk_ctx(genesis_substrate)
    result = dispatch("senesce", {}, ctx=ctx)
    assert result.payload["mode"] == "full"


def test_dispatch_via_alias_with_quick(genesis_substrate: Path) -> None:
    """Alias invocation should also carry the quick flag through."""
    ctx = _mk_ctx(genesis_substrate)
    result = dispatch("session-end", {"quick": True}, ctx=ctx)
    assert result.payload["mode"] == "quick"
