# v0.7.5 — P0-to-P6 Omnibus (close every gap surfaced in the v0.7.4 retrospective)

> **Status**: LANDED (2026-05-10).
> **Predecessor**: v0.7.4 (Cowork plugin extension `.plugin` → `.zip` hotfix per Anthropic GitHub issue #40414).
> **Trigger**: owner asked for the gap analysis vs the L0 ideal; received a 7-item P0-P6 priority table; explicitly directed to ship all 7 in one breath.

---

## Round 1 — Initial claim

v0.7.5 ships seven items in one atomic release:

| P# | Surface | Mechanism |
|---|---|---|
| **P0** | Owner's `claude_desktop_config.json` `myco.mcp` → `myco.boundary.mcp` | one-line edit; lets MB8 shim sunset gate begin counting |
| **P1** | Living Bets v0.7-MAJOR re-audit (L0-mandated cadence) | new craft `docs/primordia/v0_7_5_living_bets_audit_2026-05-10.md` |
| **P2** | First real schema migration since v0.6.0 (v2 → v3) | `metrics.lint_dim_count: int` field; anamorph subagent authors the upgrader; `bump_version.py` auto-refreshes both `metrics.test_count` + `metrics.lint_dim_count` to close the README/canon drift loop forever |
| **P3** | First real federation E2E test in propagate's 7-minor-version history | `tests/integration/fixtures/peer_substrate/_canon.yaml` as a real second substrate; `tests/integration/test_propagate_to_fixture_peer.py` exercises the actual `propagate()` code path filesystem-to-filesystem |
| **P4** | Myco self-eat (close P4-stagnation gap surfaced by `notes/distilled=1` on a 7-minor-version project) | `myco_eat` × 5 craft files (v0.7.0/.1/.2/.3/.4) → `myco_assimilate` → `myco_digest` (no-LLM file-promotion path) → `myco_sporulate` distilled candidates; targets `notes/integrated≥7, distilled≥6` post-run |
| **P5** | 5th ingestion modality (chat-log) | `src/myco/ingestion/adapters/chat_log.py` supports markdown chat-log + JSONL; 10-test pytest suite |
| **P6** | Operational debt | README × 3 "46 lint dimensions" → "50 lint dimensions"; `canon.metrics.test_count: 1566` → 1568 (auto-refreshed by P2 going forward); `docs/contract_changelog.md` v0.7.3 unfilled `(Fill in: ...)` stub → retroactive 1-line entry pointing to the v0.7.3 craft |

## Round 1.5 — Self-rebuttals (P1-P5 fanout via fungal critic protocol)

### T1 (chytrid / P1 Only-For-Agent)

> Doing 7 items in one release looks like a contractor mode. Where's the agent-first focus?

**Resolution**: each of the 7 maps to an L0 principle that mechanizes agent-first guarantees.
- P0 lets the agent's host-side surface auto-cleanup (MB8 ratchet)
- P1 honors the L0-mandated re-audit cadence (P3-Eternal-Evolution governance)
- P2 closes a class of canon/README drift bugs that mislead the agent's reading of substrate identity (P1)
- P3 exercises the federation pathway the L0 promised but never delivered (P5)
- P4 dogfoods the substrate's own iteration loop on its own crafts (P4)
- P5 expands ingestion modality (P2 — Eternal Devour says "anything the agent can point at")
- P6 erases human-trust bugs in version anchors

The bundle is justified BECAUSE every item closes an agent-experience gap, not in spite of it.

### T2 (rhizomorph / P2 Eternal-Devour)

> Adding a fifth adapter when 6 already exist? Why this one?

**Resolution**: I miscounted earlier. Actual existing adapters: html_reader, pdf_reader, tabular, text_file, url_fetcher, code_repo (6). Chat-log makes 7. Chat-log is the modality the L0 explicitly names ("conversation fragment") that no existing adapter handles. Markdown `## user:` / `## assistant:` blocks + JSONL `{"role": ..., "content": ...}` lines are the two production formats (Claude / ChatGPT export). This is the highest-marginal-utility next adapter.

### T3 (mycoparasite / P3 Eternal-Evolve)

> Schema bump v2 → v3 for a single new field is overkill; it pollutes the canon for dogfood's sake.

**Resolution**: the bump isn't dogfood. The field `metrics.lint_dim_count` solves a real bug class — the README × 3 / canon "46 dims" vs actual 50 dims drift, replicated 5 times across READMEs every time someone adds a new dim. Auto-refresh in `bump_version.py` makes this drift mechanically impossible going forward. The schema bump is the right vehicle because canon's strict load behavior would otherwise require every existing canon to grow the field; the upgrader handles that. Anamorph subagent's first real-world exercise is itself a valuable test.

### T4 (saprotroph / P4 Eternal-Iterate)

> Self-eat of 5 crafts via 20+ verb calls is brittle; one verb failure halts the chain.

**Resolution**: `myco_digest` is idempotent on already-integrated notes (returns `status: "already_integrated"`). Pipeline can be retried safely. If digest fails on craft N, I retry that one without re-doing crafts 1..N-1. `myco_eat` is similarly idempotent on the same source path (creates new raw note with timestamped filename). And `myco_sporulate` reads only from `notes/integrated/`; failures there don't corrupt earlier stages.

### T5 (mycorrhiza / P5 All-Things-Connected)

> The fixture peer in `tests/integration/fixtures/peer_substrate/` is a fake federation peer. Real federation is across machines or process boundaries.

**Resolution**: `propagate()`'s contract is filesystem-based by design (per the source: "publishes notes from src_ctx into dst_root's notes/raw/ inbox"). It accepts any `Path`. Two filesystem substrates ARE real federation as the contract defines it. Future enhancement to network propagation is a separate craft (and would be v0.8+). The fixture peer exercises 100% of the current contract.

## Round 2 — Refinement

**Test count delta**: +10 (chat_log adapter) +3 (federation E2E) +N (anamorph schema migration tests) ≈ +15-20.

**Lint dim count**: unchanged at 50 (no new dim added; field added to canon is a model change, not a lint dim).

**Test count after this release**: ~1583-1588.

**Files added** (NEW):
- `docs/primordia/v0_7_5_p0_to_p6_omnibus_craft_2026-05-10.md` (this file)
- `docs/primordia/v0_7_5_living_bets_audit_2026-05-10.md` (P1)
- `src/myco/ingestion/adapters/chat_log.py` (P5)
- `tests/unit/ingestion/adapters/test_chat_log.py` (P5)
- `tests/integration/fixtures/peer_substrate/_canon.yaml` (P3)
- `tests/integration/fixtures/peer_substrate/notes/raw/.gitkeep` (P3)
- `tests/integration/test_propagate_to_fixture_peer.py` (P3)
- `tests/unit/core/test_canon_schema_upgrader_v2_to_v3.py` (P2, anamorph-authored)
- `docs/migration/v0_7_4_to_v0_7_5.md` (P2 anamorph migration guide)
- 5+ files under `notes/raw/` / `notes/integrated/` / `notes/distilled/` from P4 self-eat

**Files modified**:
- `_canon.yaml`: `schema_version` "2" → "3", `contract_version` v0.7.5, new `metrics.lint_dim_count` field
- `src/myco/core/canon.py`: new `_v2_to_v3_lint_dim_count_field` partial upgrader; `KNOWN_SCHEMA_VERSIONS` extended
- `docs/schema/canon.schema.json`: schema delta for the new optional field
- `scripts/bump_version.py`: auto-refresh `metrics.test_count` + `metrics.lint_dim_count` before molt
- `src/myco/ingestion/adapters/__init__.py`: register `chat_log` adapter
- README × 3 (en/zh/ja): "46 lint dimensions" → "50 lint dimensions"
- `docs/contract_changelog.md`: v0.7.3 stub backfilled, v0.7.5 entry added

## Round 3 — Decision shape

**LANDED.** Standard release pipeline.

**User-facing migration**: substrates at `schema_version: "2"` upgrade transparently on next canon load (anamorph's `_v2_to_v3_lint_dim_count_field` is invoked automatically). Substrates at `schema_version: "3"` from a fresh `myco germinate` already have the field. No user action required for upgrade.

**Cowork-side**: drag `C:\Users\10350\Desktop\myco-0.7.5.zip` into Cowork (replaces v0.7.4 entry by `name` key).

**MB8 sunset countdown**: P0's host-config edit + the fact that the legacy shim hasn't been hit since `2026-05-08T19:35:22Z` means the 7-day zero-hit gate begins counting. Earliest deletion of `src/myco/mcp/` (and removal of MB8 dim itself): 2026-05-15.
