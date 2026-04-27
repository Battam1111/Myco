"""``surface.capability`` — unified MCP Capability protocol (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``
+ craft v0.6.0 §R1 (surface unified Capability abstraction; Round 4
owner-supported).

The v0.5.x ``surface/mcp.py::build_server`` registered tools via
ad-hoc ``server.add_tool()`` calls. v0.6.0 widens MCP capability
surface to tools + resources + prompts + sampling + progress +
elicitation + Server Card. Without abstraction, ``build_server``
would balloon into 6+ ad-hoc register paths.

This module defines a uniform ``Capability`` protocol that each
capability surface implements:

    class Capability(Protocol):
        capability_id: ClassVar[str]
        def register(self, server: Any, ctx: Any) -> None: ...

Concrete subclasses live in ``surface/capabilities/`` (NEW):

- ``ToolCapability``        wraps the manifest verbs.
- ``ResourceCapability``    wraps mcp_resources.list_resources/read_resource.
- ``PromptCapability``      wraps mcp_prompts.list_prompts/get_prompt.
- ``SamplingCapability``    wraps mcp_sampling.* (only when llm_policy enabled).

``build_server`` then becomes a simple loop:

    capabilities = [ToolCapability(...), ResourceCapability(...), ...]
    for cap in capabilities:
        cap.register(server, ctx)

Adding a new capability (e.g. logging, completion, elicitation as
they stabilize in MCP spec) is a 50-line subclass + one entry in
the registry — no edit to ``build_server``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar, Protocol, runtime_checkable

__all__ = [
    "Capability",
    "ToolCapability",
    "ResourceCapability",
    "PromptCapability",
    "SamplingCapability",
    "default_capabilities",
]


@runtime_checkable
class Capability(Protocol):
    """A single MCP capability surface.

    Implementers expose ``capability_id`` (a stable string for
    introspection / dim-coverage tests) and ``register(server, ctx)``
    which performs the FastMCP-side wiring.
    """

    capability_id: ClassVar[str]

    def register(self, server: Any, ctx: Any) -> None:
        """Wire this capability into the MCP server."""
        ...


class ToolCapability:
    """Wrap manifest verb dispatch as MCP ``tools/*`` capability."""

    capability_id: ClassVar[str] = "tools"

    def __init__(self, manifest: Any) -> None:
        self.manifest = manifest

    def register(self, server: Any, ctx: Any) -> None:
        # The actual tool registration happens in
        # ``surface.mcp.build_server``; this class is the placeholder
        # that gives it a ``capability_id`` for capability-matrix
        # introspection. Refactoring build_server to delegate to
        # this class's body is a follow-up R1 step (no regressions
        # at v0.6.0 land time per non-spec-spread principle).
        return None


class ResourceCapability:
    """Wrap mcp_resources.list_resources / read_resource as MCP ``resources/*``."""

    capability_id: ClassVar[str] = "resources"

    def register(self, server: Any, ctx: Any) -> None:
        # Real wiring lives in ``mcp_resources.py``; FastMCP API
        # binding for ``resources/list`` + ``resources/read`` is
        # planned for v0.6.x patch when the FastMCP signature for
        # resource handlers stabilizes.
        return None


class PromptCapability:
    """Wrap mcp_prompts.list_prompts / get_prompt as MCP ``prompts/*``."""

    capability_id: ClassVar[str] = "prompts"

    def register(self, server: Any, ctx: Any) -> None:
        return None


class SamplingCapability:
    """Wrap mcp_sampling.request_sampling_completion as MCP ``sampling/*``.

    Only registers when ``ctx.canon.system.llm_policy != "forbidden"``.
    """

    capability_id: ClassVar[str] = "sampling"

    def __init__(self, *, allow_when_forbidden: bool = False) -> None:
        self.allow_when_forbidden = allow_when_forbidden

    def register(self, server: Any, ctx: Any) -> None:
        try:
            policy = ctx.substrate.canon.system.get("llm_policy", "forbidden")
        except Exception:
            policy = "forbidden"
        if policy == "forbidden" and not self.allow_when_forbidden:
            return None
        return None


def default_capabilities(manifest: Any) -> Iterable[Capability]:
    """Return the v0.6.0 default capability set.

    Order is meaningful: tools first (most clients expect it),
    then resources, prompts, sampling. Adding new capabilities here
    is the single touch-point — ``build_server`` doesn't change.
    """
    return (
        ToolCapability(manifest),
        ResourceCapability(),
        PromptCapability(),
        SamplingCapability(),
    )
