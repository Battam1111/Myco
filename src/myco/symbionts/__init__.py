"""``myco.symbionts`` — per-host Agent-sugar adapters.

**Definition (v0.5.5 MAJOR-D)**: symbionts are per-host integration
adapters. Each module here wires Myco's manifest verbs into one
specific Agent-host environment's native extension surface (Claude
Code skills + hooks, Cursor rule files, Windsurf memories, VS Code
tasks, etc.) without requiring the host to know anything about
Myco internals.

**Not** per-substrate — that is `.myco/plugins/` (substrate-local).
A symbiont is shared across every Myco substrate the user creates
on a given host.

Governing doctrine:
``docs/architecture/L3_IMPLEMENTATION/symbiont_protocol.md``.

Governing craft:
``docs/primordia/v0_5_5_close_audit_loose_threads_craft_2026-04-17.md``
§MAJOR-D.

v0.5.5 ships this package as **defined-but-empty** — the protocol
is specified, the slot is claimed, but no concrete symbiont modules
are yet populated. The first concrete symbiont (Claude Code skill +
hook generation) is a separate release; the stub-protocol approach
lets future work populate without design backlog.

The symbionts package is **not a subsystem** (does not appear in
``canon.subsystems``); it is a cross-cutting adapter layer similar
to ``surface/`` or ``install/``. Pre-v0.5.5 the docstring described
symbionts as "downstream-substrate adapters"; that framing was
never specified or populated and is now superseded by the per-host
definition above.
"""

__all__: list[str] = []  # intentionally empty until first symbiont lands
