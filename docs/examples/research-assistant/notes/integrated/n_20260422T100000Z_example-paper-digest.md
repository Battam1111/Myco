---
captured_at: "2026-04-22T10:00:00Z"
integrated_at: "2026-04-22T10:05:00Z"
tags: ["paper", "example", "research"]
source: "example (synthetic)"
stage: "integrated"
references:
  - "notes/integrated/n_20260422T100100Z_example-decision.md"
---

# Example paper digest: Long-context cache invalidation (2026)

**Citation**: Example et al., *On the semantics of long-context
prompt caching*, arXiv:2601.00000 (synthetic example).

**One-paragraph summary**: the paper demonstrates that major
commercial inference providers diverge in cache-invalidation
semantics — some invalidate on any prompt-prefix edit while
others invalidate only on full-prefix mismatch. Agents that rely
on cache stability across sessions need to probe for the
provider's behaviour rather than assume it.

**First-line claims**:

1. Cache-invalidation semantics are provider-specific and
   undocumented.
2. Session-start probing adds <50 ms per session and resolves
   the ambiguity.
3. Myco's MCP pulse mtime-cache validates on every read, so the
   client-side behaviour is provider-agnostic.

This digest is pre-seeded as an example in the
research-assistant substrate. Delete it (and the other
`n_example-*.md` notes) when you fork this directory for your
own research.
