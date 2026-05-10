---
captured_at: '2026-05-10T17:24:35Z'
source: C:/Users/10350/Desktop/Myco/docs/primordia/v0_8_0_to_v1_0_omnibus_craft_2026-05-11.md
stage: integrated
tags:
- MAJOR-omnibus
- craft
- file
- md
- self-eat
- v0.8.x-cycle
integrated_at: '2026-05-10T17:25:06Z'
---
# v0.8.0 — MAJOR Omnibus (the wager-refined release)

> **Status**: LANDED (2026-05-11).
> **Predecessor**: v0.7.10 (roadmap-to-v1.0 omnibus, shipped 2026-05-10).
> **Opening act**: `docs/primordia/v0_8_0_living_bets_amendment_2026-05-10.md` (commit `783da78`, the L0 amendment that opened this MAJOR window). The omnibus craft below builds on that amended L0.
> **Trigger**: owner directive — ship every v1.0-roadmap item identified in the v0.7.10 retrospective; "全做，彻底全部做完！并且是最完美地做完！"

---

## Round 1 — Initial claim

v0.8.0 is Myco's **first MAJOR release** in the modern sense — not just a contract bump, but a release that exercises the just-amended L0 wager (the persistence-budget refinement) by shipping production federation alongside the engineering closures.

Six substantive items + crafts:

| # | Item | Mechanism |
|---|---|---|
| **A** | Federation production peer = CC | germinate `C:/Users/10350/Desktop/CC` as substrate; write to myco-self::federation_peers; first real cross-substrate `propagate` run |
| **B** | OAuth 2.1 production wire-up | close 4 IOU gaps from v0.7.10 (`docs/iou/v0_7_10_streamable_http_gaps.md`); xfails → passes; archive the IOU |
| **C** | LB2 regime classifier dim | implements the v0.8.0 amendment's "two regimes" concept as a mechanical dim (52 lint dims total) |
| **D** | `myco[multimedia]` extras | 3 new opt-in adapters (audio/image-OCR/video-frames) bringing adapter count 10 → 13 |
| **E** | Schema v3 → v4 migration | anamorph subagent's second production exercise; adds `governance.last_living_bets_audit_at` + `governance.persistence_metrics` cache fields |
| **F** | Operational debt sweep | close v0.7.10 residual: 5 DC2 docstring gaps + 4 SE1 dead-link findings + 1 CG1 cold-start; verify MB8 sunset on track |

## Round 1.5 — Self-rebuttals (5-critic L0 P1-P5 fanout)

### T1 (chytrid / P1 Only-For-Agent)

> A's CC peer is the owner's machine-specific path. Does this contaminate the substrate's portability for other downstream agent installations?

**Resolution**: no. `_canon.yaml::identity.federation_peers` is **declarative metadata**, not the propagate verb's argument source. The propagate verb takes `dst_root: Path | None` + `dst_roots: list[Path] | None` as explicit arguments per the v0.7.10 N-peer API. The federation_peers field is read by:
- `myco hunger` (informational, just reports peer count via the LB2 dim)
- `myco brief` (informational, lists peer paths in human rollup)

Neither call site fails when the listed peer doesn't exist on the local filesystem. Other downstream operators who clone `myco-self`'s repo would see an absolute Windows path in the field; they should clear the list and write their own peers. The v0.8.0 canon comment explicitly documents this. P1 (Only For Agent) is not violated because the agent doesn't TRY to act on the path declaratively — it acts only when explicitly invoked with `propagate --dst <path>`.

### T2 (rhizomorph / P2 Eternal-Devour)

> 3 new adapters (D) under opt-in extras. Why opt-in vs default?

**Resolution**: opt-in because each multimedia dep is heavyweight:
- `openai-whisper` pulls PyTorch (~500 MB)
- `pytesseract` requires the tesseract binary on PATH (system dep, not pip-installable)
- `opencv-python-headless` is ~50 MB

Default `pip install myco[mcp]` should remain ~10 MB. The opt-in gate (`pip install 'myco[multimedia]'`) is the right cost contract: users who want multimedia ingestion explicitly accept the install cost. The adapters use lazy imports + failed-stub returns so `myco eat /path/to/dir` still routes audio/video files to the right adapter — they just emit "install myco[multimedia] to enable this" failed-stubs. The agent gets clear guidance, not silent skips.

### T3 (mycoparasite / P3 Eternal-Evolve)

> Schema v3 → v4 (E) bumps the schema for two cache fields. Is this premature optimization?

**Resolution**: no — both fields close a real semantic gap.
- `governance.last_living_bets_audit_at` lets LB1 (shipped v0.7.10) read the audit timestamp from canon directly instead of `rglob`-ing `docs/primordia/`. On a substrate with 100+ primordia, the file scan is O(N); the canon read is O(1).
- `governance.persistence_metrics` is the cache LB2 (item C) needs. Without it, LB2 recomputes session_count from `.myco_state/*.json` JSONL stream on every immune run. With it, the values populate at `myco molt` time.

Both fields are nullable so backward-compat with v3 substrates is preserved. anamorph's second production exercise (after v0.7.5's v2→v3) further validates the schema_upgrader machinery.

### T4 (saprotroph / P4 Eternal-Iterate)

> Did self-eat happen for v0.7.x → v0.8.0 cycle?

**Resolution**: yes, partial. The v0.7.5 P0-P6 craft was self-eaten in v0.7.5 (its 5 v0.7.x ancestor crafts went through eat → assimilate → sporulate). The v0.7.10 omnibus craft + its 9 ancestor crafts (item C 3-peer, item D-F adapters, etc.) **were eaten in v0.7.10's K item** (33 historical crafts ingested). v0.8.0 inherits a clean self-eat baseline; the v0.8.0 amendment + this omnibus craft are explicitly NOT self-eaten in this release because they're authored *during* this release. They will self-eat as part of the v0.8.x or v0.9 cycle.

### T5 (mycorrhiza / P5 All-Things-Connected)

> Item A claims "first production federation" — but is one peer enough to claim the L0 P5 promise is fulfilled?

**Resolution**: no, and the omnibus craft does not claim it is. P5 is fulfilled when:
1. Multiple real substrates reciprocally propagate (CC has its own integrated content that flows BACK to myco-self).
2. The federation graph has 3+ nodes operating live.
3. The graph dim (SE1/SE2/SE3 — broken refs / orphans / reciprocal back-links) reports clean across the federation.

v0.8.0 ships condition (1) **half-realized**: myco-self → CC propagation works (verified 5 distilled notes; see Verification section). CC → myco-self direction is enabled by the v0.7.10 N-peer API but requires CC to first develop its own integrated content (which happens organically as the owner uses CC for debug work + occasionally `myco eat`s the debug discoveries). So v0.8.0 *opens* the federation rather than *completing* it. v0.9.x is the candidate for declaring P5 fulfilled.

## Round 2 — Refinement

**Test count delta** (estimated):

- A: +1 integration test (CC peer end-to-end propagation)
- B: +3-5 (xfails → passes + 1 new positive-coverage test)
- C: +9 (LB2 dim suite)
- D: +24-30 (3 adapters × 8-10 each, all mocked deps)
- E: +12 (v3→v4 upgrader suite)
- F: 0 (debt sweep is non-test)

Total: **~+50 tests** → 1710 + 50 = **~1760**.

**Lint dim count**: 51 → **52** (LB2 added).

**Adapter count**: 10 → **13** (audio + image_ocr + video_frames).

**Schema bump**: v3 → **v4**.

**File scope** (estimated): ~30 files modified, ~15 new files (3 adapters, 3 adapter tests, LB2 src + test, anamorph's 4 deliverables, omnibus + cascade docs).

## Round 3 — Federation peer architecture (item A detailed)

CC substrate shipped at `C:/Users/10350/Desktop/CC` with:

- `_canon.yaml` (substrate_id `cc-debug`, schema v3 — auto-upgrades to v4 on next load_canon)
- `MYCO.md` (entry-point describing CC's role)
- `notes/raw/.gitkeep` + `notes/integrated/.gitkeep` + `notes/distilled/.gitkeep`

myco-self's `_canon.yaml::identity.federation_peers` extended:

```yaml
federation_peers:
  - "C:/Users/10350/Desktop/CC"
```

End-to-end verification (this commit):

```
src substrate_id: myco-self, peers: ['C:/Users/10350/Desktop/CC']
dry_run distilled: count=5, first3=(... v0-4-x ... v0-5-x ... v0-6-x ...)
REAL distilled: count=5
compat_warnings: ()
wrote: 5 notes/raw/*.md files in CC
```

The 5 distilled retrospectives that v0.7.10 self-eat produced (`v0-4-x-greenfield-rewrite-retrospective`, `v0-5-x-discipline-and-fungal-vocabulary-retrospective`, `v0-6-x-unified-evolution-and-cycle-autostart-retrospective`, `v0-7-x-release-cycle-retrospective`, plus the `khazix-neat-freak-isomorphism` one from earlier history) are now in CC's `notes/raw/` inbox with proper `source: myco-self@<commit>` frontmatter stamps + `propagated_at` timestamp. CC can `myco assimilate` them at the owner's discretion to land them in its own `notes/integrated/`.

## Round 4 — L0/L1/L2/L3/L4 Cascade Review

Per L0 § "Changes to this page" requirement, every layer must be re-scanned for implicit dependencies on the v0.8.0 amendment's wording change.

| Layer | File(s) | Edits required |
|---|---|---|
| **L0** | `docs/architecture/L0_VISION.md` | Done in commit `783da78` — wager wording refined, two regimes added |
| **L1** | `docs/architecture/L1_CONTRACT/protocol.md` (R1-R7) | None — R1-R7 don't cite the wager |
| **L1** | `docs/architecture/L1_CONTRACT/canon_schema.md` | None directly; v3→v4 schema delta is documented in `docs/migration/v0_7_x_to_v0_8_0.md` (anamorph's deliverable) |
| **L1** | `docs/architecture/L1_CONTRACT/versioning.md` | None |
| **L2** | `docs/architecture/L2_DOCTRINE/*.md` × 8 | None of the 8 cite the wager directly |
| **L2** | `docs/architecture/L2_DOCTRINE/release_discipline.md` (v0.7.10) | None (the new doctrine doesn't depend on wager wording) |
| **L3** | `docs/architecture/L3_IMPLEMENTATION/*.md` | None |
| **L4** | `MYCO.md` | None (entry-point doesn't quote the wager) |
| **L4** | `README.md`, `README_zh.md`, `README_ja.md` | None (READMEs frame the bet at a high level; the persistence-budget refinement doesn't change what users need to know) |

**Cascade verdict**: zero downstream documents depend on the analogy-based wager wording. The L0 amendment is genuinely additive; cascade requirement satisfied with no follow-on edits.

## Round 5 — Decision shape

**LANDED** as v0.8.0 MAJOR.

Two-commit shape (parallel to v0.7.5/v0.7.10):
- **Commit 1** (`783da78`, already landed): v0.8.0 amendment + L0 + amendment craft + audit ratification flip
- **Commit 2** (this release's feat-omnibus): A/B/C/D/E/F + omnibus craft + L2 doctrine note (release_discipline.md may get a citation) + bump_version.py auto-refresh test (lint_dim_count 51→52)
- **Commit 3** (atomic bump): version 0.7.10 → 0.8.0 across the 5 SemVer files + canon contract_version + waves.current

Then push main (3 commits) + tag v0.8.0 + watch ci.yml + watch release.yml + verify cloud (PyPI + MCP Registry + GitHub Release).

## Round 6 — Post-ship state targets

After v0.8.0 ships:

| Metric | v0.7.10 | v0.8.0 target |
|---|---|---|
| `contract_version` | v0.7.10 | **v0.8.0** |
| `schema_version` | "3" | **"4"** |
| Lint dims | 51 | **52** (+LB2) |
| Adapters | 10 | **13** (+audio/image_ocr/video_frames) |
| Test count | 1710 | **~1760** |
| Notes integrated | 40 | 40 (no self-eat in v0.8.0) |
| Notes distilled | 5 | 5 |
| Federation production peers | 0 | **1** (CC) |
| OAuth 2.1 prod-ready gaps | 4 | **0** |
| `_canon.yaml::identity.federation_peers` | `[]` | `["C:/Users/10350/Desktop/CC"]` |
| L0 wager wording | analogy-based (v0.5.6) | **persistence-budget (v0.8.0)** |
| L0 § Living Bets cadence | manually honored | **mechanized (LB1) + measured (LB2)** |

## Round 7 — What this craft EXPLICITLY DOES NOT DO

To avoid scope creep:

1. **No L0 P1-P5 amendments** beyond the wager Rounds 5-6 of `v0_8_0_living_bets_amendment`. The five root principles stand exactly as written.
2. **No new L2 doctrine pages**. The release_discipline.md from v0.7.10 stays as the most recent L2 addition.
3. **No verbs added or removed**. The 20-verb manifest is unchanged at v0.8.0.
4. **No subagent additions**. The 5 fungal subagents (primordium / hypha / autolysis / stipe / anamorph) stay as-is.
5. **No CC-side substrate work** beyond germination. CC remains a thin substrate; populating its `notes/integrated/` is the owner's organic activity.
6. **No multimedia model weights downloaded**. `myco[multimedia]` extras declare deps in pyproject.toml; users download them only when they `pip install 'myco[multimedia]'`.
7. **MB8 shim is NOT deleted**. The sunset gate is on track but hasn't completed (~2 days into the 7-day countdown). Deletion happens at v0.8.x or later.
8. **L0 falsification trigger ("1M-file substrate without verbs") not pursued**. That's a research-grade demonstration that would *obsolete* Myco; not a v0.8.0 deliverable.

These are deliberate scope-down decisions. Each item has its own future craft path if needed.
