"""Cluster module — v0.8.8 max-aggressive merge of mcp_sampling, mcp_workspace.

=== mcp_sampling ===
``surface.mcp_sampling`` — server-to-client LLM sampling (v0.6.0).

Governing doctrine: ``docs/architecture/L0_VISION.md`` P1 example #2
("agent calls the LLM, the substrate does not"); craft v0.6.0 §A.4 +
§F19 + §A6 (Round 4 owner amendments).

MCP sampling lets the substrate's MCP server reverse-call the
client's LLM session for content generation. Substrate process never
imports a provider SDK; the client (which already runs the agent's
LLM) handles the actual model call.

v0.6.0 wires sampling for two verbs:

- ``sporulate``: scaffolding + LLM-generated synthesis written to
  ``notes/distilled/d_<slug>.md`` content sections.
- ``fruit``: scaffolding + LLM-generated craft round drafts.

Behavior gated on ``canon.system.llm_policy``:

- ``"forbidden"`` (default): sampling capability NOT advertised; CL1
  dim verifies the gate.
- ``"opt-in"``: per-call elicitation required (host pops dialog);
  ``_clear_token_after_call`` invoked after each round-trip per CL3
  dim.
- ``"providers-declared"``: substrate also opts into ``providers/``
  populated path (still subject to MP1 file-existence cross-check).

=== mcp_workspace ===
``surface.mcp_workspace`` — MCP workspace + substrate discovery helpers.

Governing doctrine: ``docs/architecture/L3_IMPLEMENTATION/package_map.md``
invariant 5 ("no megafile > 800 LoC"). v0.8.x post-omnibus split:
extracted from ``surface/mcp.py`` (was 810 LoC > cap) so each module
stays under the mechanical PA2 cap. The split lands as a no-bump
commit on the v0.8.4 branch per owner directive (2026-05-11) to
preserve version-number resources for meaningful releases. The MCP server's project-dir resolution chain
(``kwargs.project_dir`` → ``mcp.roots/list`` → env vars → ``cwd``) reaches
into this module for the level-2 (``mcp.roots/list``) hop and the
level-2-fallback "no substrate at the workspace, suggest germinate"
soft-response shape.

The five extracted helpers form a cohesive sub-concern — "given an MCP
``Context``, figure out where the user's workspace IS and whether it
already has a Myco substrate":

- :func:`_resolve_project_via_roots` — ask the client for workspace
  roots; return the first one with a substrate at-or-above.
- :func:`_detect_workspace_root` — same query, but return the first
  ``file://`` root regardless of substrate presence (paired with
  :func:`_resolve_project_via_roots` to suggest germinate when the
  user opens a fresh project).
- :func:`_auto_germ_advice_response` — soft-fail tool response when the
  workspace exists but no substrate does; tells the agent to ask the
  user about ``myco_germinate``.
- :func:`_uri_to_path` — parse a ``file://`` URI to a local ``Path``
  (POSIX + Windows + percent-encoded shapes).
- :func:`_has_substrate_at_or_above` — walk-up check for ``_canon.yaml``.

These helpers are re-exported from ``surface.mcp`` for backward
compatibility — every test that imports them from the original module
still works.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from myco.core.identity_cluster import SubstrateNotFound

from .mcp_auth import _clear_token_after_call

# =========================================================================
# === mcp_sampling — formerly mcp_sampling.py
# =========================================================================

def should_advertise_sampling(canon_system: dict[str, Any]) -> bool:
    """Return True if MCP server should advertise sampling capability.

    Per CL1 dim: only when ``canon.system.llm_policy != "forbidden"``.
    """
    policy = str(canon_system.get("llm_policy", "forbidden"))
    return policy != "forbidden"


async def request_sampling_completion(
    mcp_ctx: Any,
    *,
    prompt: str,
    max_tokens: int = 2000,
    canon_system: dict[str, Any] | None = None,
) -> str:
    """Reverse-call the host's LLM session via MCP sampling.

    Args:
        mcp_ctx: MCP request context exposing ``ctx.session.create_message``.
        prompt: user-role text passed to the host LLM.
        max_tokens: maxTokens hint to the host.
        canon_system: canon.system mapping (for policy validation).

    Returns:
        Host LLM completion text. Empty string on capability absence.

    Raises:
        ``RuntimeError`` if called when llm_policy=forbidden (CL1
        violation prevented at the gate).
    """
    canon_system = canon_system or {}
    if not should_advertise_sampling(canon_system):
        raise RuntimeError(
            "mcp_sampling.request_sampling_completion called with llm_policy=forbidden — CL1 violation"
        )
    messages = [{"role": "user", "content": {"type": "text", "text": prompt}}]
    try:
        result = await mcp_ctx.session.create_message(
            messages=messages, maxTokens=max_tokens
        )
    except AttributeError:
        return ""
    except Exception:
        return ""
    finally:
        try:
            _clear_token_after_call(mcp_ctx.session)
        except Exception:
            pass
    if isinstance(result, dict):
        content = result.get("content")
        if isinstance(content, dict):
            text = content.get("text")
            if isinstance(text, str):
                return text
        if isinstance(content, str):
            return content
    return ""


# =========================================================================
# === mcp_workspace — formerly mcp_workspace.py
# =========================================================================

async def _resolve_project_via_roots(ctx: Any) -> Path | None:
    """Ask the MCP client for its workspace roots via ``roots/list``.

    Returns the first root whose path has a Myco substrate (a
    ``_canon.yaml`` at it or any ancestor). Returns ``None`` when:

    - the client doesn't support ``roots/list`` (raises / no capability)
    - the client returns an empty roots list
    - no root's URI is a ``file://`` URI
    - no root has a substrate anywhere along its ancestry

    This is the core ``一劳永逸`` fix for MCP hosts that don't set a
    useful cwd on MCP-server subprocesses (Claude Desktop, Cowork,
    Cursor, Zed, …). Every spec-compliant MCP client exposes
    workspace roots via this protocol method; Myco uses that
    standard channel rather than each host's bespoke config field.
    """
    try:
        session = getattr(ctx, "session", None)
        if session is None or not hasattr(session, "list_roots"):
            return None
        result = await session.list_roots()
    except Exception:
        return None
    roots = getattr(result, "roots", None) or []
    for root in roots:
        uri = getattr(root, "uri", None)
        if not uri:
            continue
        candidate = _uri_to_path(str(uri))
        if candidate is None:
            continue
        if _has_substrate_at_or_above(candidate):
            return candidate
    return None


async def _detect_workspace_root(ctx: Any) -> Path | None:
    """Return the first ``file://`` workspace root the client exposes,
    **regardless of whether it has a substrate**.

    Paired with :func:`_resolve_project_via_roots` as the "did the
    client at least tell us something about the workspace?" probe.
    If ``_resolve_project_via_roots`` returned ``None`` (no root had
    a substrate), we still want to know where the user's workspace
    IS so we can suggest germinating a substrate there.

    v0.5.16 addition.
    """
    try:
        session = getattr(ctx, "session", None)
        if session is None or not hasattr(session, "list_roots"):
            return None
        result = await session.list_roots()
    except Exception:
        return None
    roots = getattr(result, "roots", None) or []
    for root in roots:
        uri = getattr(root, "uri", None)
        if not uri:
            continue
        candidate = _uri_to_path(str(uri))
        if candidate is not None:
            return candidate
    return None


def _auto_germ_advice_response(
    *, verb: str, workspace_root: Path, exc: SubstrateNotFound, hunger_called: bool
) -> dict[str, Any]:
    """Return a soft-fail MCP tool response when the workspace has no
    substrate yet. The agent sees a normal-shaped response whose pulse
    tells it to call ``myco_germinate`` with the workspace root.

    Why soft-fail: raising ``SubstrateNotFound`` here would surface
    as a transport-level error on the MCP client, blocking the agent
    from relaying the suggestion to the user. A dict response with
    advice in the pulse gets the agent to say "this folder doesn't
    have a Myco substrate yet — want me to germinate one?" which is
    the UX we want.

    ``exit_code`` is set to 4 (``SubstrateNotFound``'s canonical exit
    code per the v0.5.8 contract) so anything that checks exit codes
    still differentiates "no substrate" from other error classes.
    The agent reads the pulse advice.

    v0.5.16 initial shape. v0.5.18 bugfix: also include the
    ``project_dir_source`` + ``resolved_project_dir`` transparency
    fields that v0.5.17 added to the normal dispatch path — reaching
    this function PROVES ``_detect_workspace_root`` got a workspace
    back from the client, which is itself the most useful debugging
    signal (confirms roots/list works even though _resolve_... came
    up empty because the root had no substrate).
    """
    from myco.core.trust_cluster import safe_frontmatter_field

    suggested = f"no substrate at {workspace_root}. Call myco_germinate(project_dir={str(workspace_root)!r}, substrate_id=<slug>) to bootstrap one."
    return {
        "exit_code": 4,
        "payload": {
            "error": "SubstrateNotFound",
            "detail": str(exc),
            "workspace_root": str(workspace_root),
            "advice": suggested,
        },
        "substrate_pulse": {
            "substrate_id": "(no substrate — workspace detected)",
            "contract_version": "(unknown)",
            "hard_contract_ref": "docs/architecture/L1_CONTRACT/protocol.md",
            "rules_hint": suggested,
            "project_dir_source": "mcp.roots/list (root has no substrate)",
            "resolved_project_dir": safe_frontmatter_field(
                str(workspace_root), max_len=512
            ),
        },
    }


def _uri_to_path(uri: str) -> Path | None:
    """Parse a ``file://`` URI to a local ``Path``.

    Handles POSIX (``file:///home/user/x``) and Windows
    (``file:///C:/Users/x`` or ``file://C:/Users/x``) URIs, plus
    percent-encoded spaces / non-ASCII characters. Returns ``None``
    for non-file schemes (``https://``, ``git+ssh://``, etc).
    """
    import urllib.parse
    import urllib.request

    try:
        parsed = urllib.parse.urlparse(uri)
    except Exception:
        return None
    if parsed.scheme != "file":
        return None
    try:
        return Path(urllib.request.url2pathname(parsed.path))
    except Exception:
        return None


def _has_substrate_at_or_above(path: Path) -> bool:
    """True when ``path`` or any ancestor contains a canon file.

    v0.8.4 root-cleanup (2026-05-12): walks up checking both
    ``.myco/canon.yaml`` (new layout) and ``_canon.yaml`` (legacy),
    via ``core.paths.has_substrate`` — the single SSoT for the
    dual-location canon resolution rule.
    """
    from myco.core.io_cluster import has_substrate

    try:
        p = path.resolve()
    except OSError:
        return False
    for candidate in [p, *p.parents]:
        if has_substrate(candidate):
            return True
    return False
