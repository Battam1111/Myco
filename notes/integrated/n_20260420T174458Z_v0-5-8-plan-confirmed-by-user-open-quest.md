---
captured_at: '2026-04-20T17:44:58Z'
tags:
- v0.5.8
- planning
- confirmation
- auto-resolved-opens
source: agent
stage: integrated
integrated_at: '2026-04-20T17:49:04Z'
---
v0.5.8 plan confirmed by user. Open questions auto-resolved with craft reasoning: (1) Phase 1 audit cap = 6 iterations, escalate to user if P0/P1 still exist. (2) MP2 severity = MEDIUM (plugin scope is legitimately broader than kernel; canon no_llm_in_plugins flag escalates to HIGH on opt-in). (3) PreToolUse bypass = MYCO_ALLOW_UNSAFE_WRITE=1 env var, immune tracks usage (new dim or SE-class log finding) so it is auditable not silent. (4) Pulse thresholds 0-5 gentle / 5-15 elevated / >15 HIGH — reasonable defaults; tunable via canon. (5) macOS CI + Node 24 + mypy ratchet all in v0.5.8 (small-scope, worth including). (6) brief UI scope: text annotation only; JSON schema additive later. (7) L2 extensibility.md finalized at v0.5.8 (in-progress since v0.5.6). Proceeding to Phase 1 iterative deep audit (8 orthogonal lenses, convergence on zero new P0/P1).
