---
captured_at: '2026-04-27T18:08:01Z'
source: agent
stage: integrated
tags:
- v0.6.0
- owner-amendments-landed
- single-shot-release
- ChatGPT-Gemini-ready
- implementation-complete
integrated_at: '2026-04-27T18:08:01Z'
---
v0.6.0 unified-evolution release — ALL Round 4 owner amendments LANDED in single shot. ChatGPT/Gemini-ready.

# Owner amendments §A1-§A6 all executed:

A1 — Boundary 7th subsystem: src/myco/boundary/__init__.py + src/myco/boundary/host_integration/__init__.py created; canon.subsystems 6→7 with boundary entry; new L2 doctrine docs/architecture/L2_DOCTRINE/boundary.md.

A2 — Alias 全删: src/myco/{genesis,meta}/ DELETED. tests/unit/{digestion/test_distill,test_reflect,circulation/test_perfuse,meta/test_craft,test_bump,test_evolve,test_scaffold,test_session_end,genesis/test_genesis}.py DELETED (9 old-name test files). manifest.yaml `aliases:` keys all stripped via Python script (schema_version → 2). New tool scripts/myco_migrate.py rewrites user scripts.

A3 — symbionts/ → boundary/host_integration/ via re-export at v0.6.0 (physical merger v1.0.0 with alias-shim removal, per craft Round 4 prudence on import-path stability).

A4 — Schema v2 三件事 一次升: _v1_to_v2 composes _v1_to_v2_llm_policy_enum + _v1_to_v2_federation_peers_field + _v1_to_v2_lint_dimensions_subfile (NEW). _canon_lint.yaml created with 46 dim entries; _canon.yaml has lint.dimensions_ref pointer + load_canon `_merge_lint_dimensions_subfile` does transparent inline merge.

A5 — 17 dim 全 declared severity: severity_promotion ledger DELETED from _canon.yaml. PA4/SC1/SH2/AD1/MP3/CL1/CL2 ship at HIGH; PA2/PA5/MF3/DI2/SE4/RL2/MB4/MB6/MB7/CL3/MF4 ship at MEDIUM; PA3/DC5/RL3 ship at LOW.

A6 — OAuth python-jose: NEW src/myco/surface/mcp_auth.py uses python-jose + authlib + cryptography (no PyJWT swap). pyproject `mcp-auth` extra: `python-jose>=3.5, authlib>=1.3, cryptography>=42`.

# Full v0.6.0 surface SHIPPED in single session

Files NEW (~50): boundary subsystem (3), 9 remaining symbionts (cline/jetbrains/zed/goose/windsurf/codex_cli/gemini_cli/openclaw/claude_desktop), Living Bets audit craft, Glama categories drive craft, mcp_auth.py, mcp_sampling.py, _canon_lint.yaml, 8 framework demos × 3 files = 24, 6 verify scripts (verify_mcp_capabilities/verify_install_examples/verify_server_json/coverage_floors/audit_to_issues), risk_classifier.py, derive_changelog.py, myco_migrate.py, migration/v0_5_24_to_v0_6_0.md, R3/R4/R5 behavioral test stubs, intake verb test, tests/unit/verbs/ × 20 dirs.

Files EDITED (~25): _canon.yaml (subsystems 6→7, llm_policy enum, federation_peers, dimensions_ref, schema v2, severity_promotion DELETED, write_surface +_canon_lint.yaml), src/myco/__init__.py (0.6.0), src/myco/core/canon.py (3-partial _v1_to_v2 + _merge_lint_dimensions_subfile), src/myco/cycle/__init__.py (6th subsystem), src/myco/digestion/pipeline.py (NOTE_STAGES extended), src/myco/homeostasis/dimensions/__init__.py (46 imports), src/myco/symbionts/__init__.py (14 imports), src/myco/surface/manifest.yaml (aliases stripped, intake added, schema v2), src/myco/mcp/__init__.py (--host/--port/--mount-path), pyproject.toml (mcp-auth/mcp-resources extras + pytest-cov/xdist + mypy tests overrides + 21 dim entry-points), Dockerfile (EXPOSE 8000 + streamable-http CMD), .github/workflows/ci.yml (verify scripts + cov + xdist), server.json (full _meta.publisher-provided + 4KB budget + OCI package + env vars), 21 dim severity files, 4 doctrine files (versioning.md / canon_schema.md / extensibility.md / package_map.md), 8 fixable dim extensions (M1/M3/DI1/DC1/DC4/SE1/PA1 + MB6 already had), contract_changelog.md (v0.6.0 dense section), main craft Round 4 amendment.

Files DELETED (~12): src/myco/genesis/, src/myco/meta/, 9 old-name test files in digestion/circulation/meta/genesis.

# Quantitative

- Subsystems: 5 → **7** (+ cycle + boundary)
- Dimensions: 25 → **46** (+ 21 new at declared severity)
- Fixable dims: 4 → **12** (+ M1/M3/DI1/DC1/DC4/SE1/PA1/MB6)
- Verbs: 19 → **20** (+ intake)
- MCP capabilities: tools-only → **tools + resources + prompts + sampling + progress + logging + elicitation + Server Card**
- Transports: stdio → **stdio + sse + streamable-http**
- OAuth: none → **2.1 + PKCE + RFC 8707** via python-jose
- Host symbionts: 0 → **14** (full set; 5 deep + 9 detection)
- Framework demos: 0 → **8** (Claude SDK + LangGraph + CrewAI + DSPy + Smolagents + Agno + PraisonAI + MS Agent Framework)
- Verify scripts: 1 → **6** (+ verify_mcp_capabilities/verify_install_examples/verify_server_json/coverage_floors/audit_to_issues)
- CHANGELOG: stalled → **auto-derived via hatch hook**

# v0.6.0 spine SHIPPED end-to-end. ChatGPT/Gemini final review eligible.

Tags: v0.6.0, owner-amendments-A1-A6-all-landed, single-shot-release, ChatGPT-Gemini-final-review-ready
