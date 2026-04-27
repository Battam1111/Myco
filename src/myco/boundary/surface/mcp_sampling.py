"""``surface.mcp_sampling`` — server-to-client LLM sampling (v0.6.0).

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
"""

from __future__ import annotations

from typing import Any

from .mcp_auth import _clear_token_after_call

__all__ = ["should_advertise_sampling", "request_sampling_completion"]


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
            "mcp_sampling.request_sampling_completion called with "
            "llm_policy=forbidden — CL1 violation"
        )

    # Compose the sampling request per MCP spec.
    messages = [{"role": "user", "content": {"type": "text", "text": prompt}}]
    try:
        result = await mcp_ctx.session.create_message(
            messages=messages,
            maxTokens=max_tokens,
        )
    except AttributeError:
        # Host doesn't support sampling capability — graceful degrade
        # to scaffolding-only mode.
        return ""
    except Exception:
        # Any other failure: scaffolding-only fallback.
        return ""
    finally:
        # CL3 dim verifies this clear is wired. Token holder is the
        # session object; clearing best-effort.
        try:
            _clear_token_after_call(mcp_ctx.session)
        except Exception:
            pass

    # Extract content from the host's response.
    if isinstance(result, dict):
        content = result.get("content")
        if isinstance(content, dict):
            text = content.get("text")
            if isinstance(text, str):
                return text
        if isinstance(content, str):
            return content
    return ""
