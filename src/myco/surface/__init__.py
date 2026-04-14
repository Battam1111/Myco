"""``myco.surface`` — CLI + MCP adapters driven by a single manifest.

Governing doc: ``docs/architecture/L3_IMPLEMENTATION/command_manifest.md``.
Lands in Stage B.7.

Responsibility: load ``manifest.yaml``, dispatch verbs to their handlers
with the shared ``(args, ctx) -> Result`` signature, and project the
same manifest as an MCP tool surface.
"""
