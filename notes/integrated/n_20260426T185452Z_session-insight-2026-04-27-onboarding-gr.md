---
captured_at: '2026-04-26T18:54:52Z'
source: agent
stage: integrated
tags:
- onboarding
- session-comprehension
- decisions
- frictions
- v0.5.24
integrated_at: '2026-04-27T17:07:50Z'
---
Session insight (2026-04-27 onboarding-grade comprehension pass on myco-self @ v0.5.24):

# Architecture compass (post-three-rounds-craft)

Real tensions surfaced (worth acting on):
- DRAFT craft `dogfood_v0_5_3_smoke_craft_2026-04-18.md` has been a 9-day empty template; either fill + winnow or excrete with reason.
- 8 graph orphans (traverse output): 2 distilled notes never promoted; `glama_usage_drive_craft_2026-04-24.md` was authored but unlinked from canon/index; multiple README.md files orphan (docs/, docs/architecture/, docs/comparisons/, docs/promotion/); migration_strategy.md orphan despite being L3.
- Five verbs lack a dedicated test_<verb>.py file: assimilate, sporulate, traverse, fruit, molt. They ARE covered transitively (assimilate ← senesce; molt ← bump_version_script; fruit ← winnow_g6; traverse ← brief), but locating coverage is opaque. Adding shim test files is cheap insurance against regression invisibility.
- `scripts/verify_mcp_boot.py` is a complete 6-stage stdio JSON-RPC diagnostic (locks 19 canonical tool names + examples on 7 high-value params + ends with myco_hunger e2e) but is NOT invoked by `.github/workflows/ci.yml` or `release.yml`. Wiring it as a release-pipeline gate would close the window where MCP-handshake regression ships unnoticed.
- Glama auto-categorisation as "Knowledge & Memory" violates L0 P1 (Myco explicitly NOT a memory tool); fix path is dashboard-only (operator action, not file-tracked).

Pseudo-tensions ruled out (intentional design, not problems):
- "Craft governance shrank after v0.5.10": docs/primordia/README.md:158-164 explicitly declares hotfixes don't require craft. The shrinkage is policy, not drift.
- "CHANGELOG.md frozen at [0.5.9]": audience split with contract_changelog.md is L0-P1-aligned (CHANGELOG = PyPI users; contract_changelog = substrate agent). Single SSoT is correct.
- "README is human-facing prose": README is a substrate boundary surface (like brief), not internal substrate; consistent with carved-exception model.

Latent risks for L0-P3 self-evolution:
- Single-maintainer governance (all commits Battam1111 / Yanjun, 0 PR history). Long-term L0-P3 promise of agent-self-maintenance has not been stress-tested by multi-author flow.
- Reactive cadence (4 days × 25 patches in v0.5.0→v0.5.24, all triggered by external ecosystem demands: MCP Registry / Cowork / Glama). No reserve crafts in flight ([Unreleased] empty, 0 open issue, 0 DRAFT). Next version cadence likely depends on Glama Try-it-live first-user friction.
- providers/ permanent-empty escape hatch: MP1-locked. When substrate-internal LLM-call utility (embedding cache, intent triage) eventually becomes useful, the lockout will require canon flip + craft + molt. Healthy now, may become friction later.

Operating heuristics for next dev sessions:
- Manifest.yaml at src/myco/surface/manifest.yaml is the single mutation point for any verb shape change; CLI + MCP both derive.
- write_surface in _canon.yaml:19-78 is the mechanical door for writes — confirm path inclusion before writing.
- Five-step project_dir resolution (MCP side): kwargs > roots/list > MYCO_PROJECT_DIR > CLAUDE_PROJECT_DIR > cwd; CLI side drops roots/list (four-step).
- Pulse sidecar carries rules_hint that mechanically advances R1→R3 across the session — read it on every tool call.

Tags: project, decisions, frictions, onboarding, v0.5.24
