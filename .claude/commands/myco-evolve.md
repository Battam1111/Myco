---
description: "Run the v0.6.14+ Cycle-自起 fruit—winnow—molt 闭环 against an existing distilled note. Orchestrates: primordium-autonomous (3-critic fanout) → winnow → hypha (feasibility) → anamorph (if schema) → stipe --branch-only → gh pr create. Owner-merge-gated; no direct main push."
argument-hint: "<distilled-slug>"
---

The user wants you to run the autopoietic kernel-evolution loop against the distilled note: $ARGUMENTS

This is the v0.6.14+ **Cycle 自起 fruit—winnow—molt 闭环** orchestrator. It mechanizes the bridge from `sporulate` (distilled note) to a candidate kernel mutation (auto-craft PR), with **owner-merge-gate as the only remaining synapse**. The substrate kernel adds zero LLM dispatch; intelligence lives in the Claude Code Agent layer (you, plus the 3 fungal critics that primordium spawns).

Governing doctrine: `docs/architecture/L2_DOCTRINE/cycle.md` § "Cycle 自起 fruit—winnow—molt 闭环 (v0.6.14+)" + `docs/architecture/L2_DOCTRINE/boundary.md` § "Sixth seam (v0.6.14+)".
Governing craft: `docs/primordia/_landed/v0_6_x/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md`.

## Pre-flight gates (refuse if any fails)

Run all checks before invoking any subagent. If any returns a refusal condition, report it to the user with a diagnosis and stop. Do NOT auto-correct.

1. **Master switch on**: `myco sense --query "auto_propose_enabled"` — if canon shows `false`, refuse with `auto-evolve disabled per canon.governance.auto_propose_enabled: false`.

2. **Tracking issue seeded**: read `_canon.yaml::system.governance.auto_evolve_tracking_issue_id` — if `null`, refuse with `tracking issue not seeded; run scripts/seed_auto_evolve_tracking_issue.py first`.

3. **Rate limit**: read `.myco_state/last_auto_evolve.txt` (if exists) — if last-run timestamp is within `canon.governance.auto_evolve_min_wall_clock_seconds_between` seconds of now, refuse with the wait time.

4. **Daily budget**: read `.myco_state/auto_evolve_spend.json` (if exists) — if today's spend exceeds `canon.governance.auto_evolve_daily_budget_usd` (when not null), refuse.

5. **Distilled-hash cooldown**: read the distilled note at `notes/distilled/d_<distilled-slug>.md`; compute `sha256(content)`; check `canon.governance.last_winnowed_proposals[]` for any entry whose `originating_distilled_hash` matches AND was added within the last `auto_evolve_distilled_hash_cooldown_senesce` senesce calls. If matched, refuse with `same-distilled cooldown active; same hash already auto-crafted recently`.

6. **Distilled severity threshold**: read distilled note's frontmatter — if `severity:` is below `canon.governance.auto_evolve_min_distilled_severity` (default `medium`), refuse with `distilled severity below threshold; LOW signals do not trigger auto-evolve`.

7. **Distilled exists + readable**: if `notes/distilled/d_<distilled-slug>.md` does not exist or cannot be read, refuse.

## Orchestration chain (run in order; stop on first failure)

If all 7 pre-flight gates pass, run this chain. Each step's failure mode is `report to user + halt`; do NOT attempt automated recovery beyond the per-step retry policy noted.

### Step 1: Quarantine the distilled note

Read `notes/distilled/d_<distilled-slug>.md`. Apply:

- Strip ASCII control sequences `0x00-0x1F` except `\n` (0x0A) and `\t` (0x09).
- Cap length at 32,768 bytes (truncate; preserve frontmatter intact).
- Prepend the marker `[UNTRUSTED-INPUT-FROM-RAW-VIA-DISTILLED]` so primordium and critics know the content originated from raw notes (which `myco eat` does not filter per L0 P2).

Pass the quarantined content to primordium in step 2. Record the original sha256 hash for canon.governance bookkeeping in step 7.

### Step 2: Invoke primordium in autonomous mode

Use the **primordium** subagent (`.claude/agents/primordium.md`) with the autonomous-mode flag.

Pass primordium:
- The quarantined distilled content.
- The substrate root path.
- Instructions to: (a) draft Round 1 from the distilled's "Future axis" section, (b) spawn 3 fungal critics (mycoparasite / saprotroph / mycorrhiza) in parallel via the Task tool with the role-prompts in primordium.md § "Critic role-prompts", (c) synthesize Round 1.5 T-numbered tensions, (d) write Round 2 responses, (e) decide Round 3 status (LANDED / DRAFT / WITHDRAWN), (f) record the 3 critic agentIds in the craft's `sub_agent_fanout_artifacts` frontmatter.

primordium returns:
- The path to the drafted craft under `docs/primordia/`.
- The Round 3 status.
- The synthesized list of T-numbered tensions with severity classifications.
- The 3 critic agentIds.

If Round 3 is `DRAFT` (any HIGH critic veto unresolved) or `WITHDRAWN`: report to user, halt, do NOT proceed to step 3. The craft remains under `docs/primordia/` for human review.

### Step 3: Run winnow

If primordium returned LANDED:

Run `myco winnow --proposal docs/primordia/<craft-filename>.md` (Bash).

Expected: exit 0, verdict `pass`. If `fail`: report to user with the violations list, halt.

### Step 4: Hypha feasibility trace

Use the **hypha** subagent (`.claude/agents/hypha.md`) with the LANDED craft path as input.

Hypha (read-only) traces the craft's "## 修订后 ... 完整 scope" section against the actual `src/`, identifies impl traction issues, and returns either `feasibility: ok` or `feasibility: blocked: <reason>`. If blocked, halt with the reason.

### Step 5: Anamorph schema migration (conditional)

If the craft proposes any change to `_canon.yaml::schema_version` OR introduces a new top-level canon field:

Use the **anamorph** subagent (`.claude/agents/anamorph.md`) to draft the schema migration partials, tests, and migration guide entry. If the craft does not touch schema, skip this step.

If anamorph returns `migration_blocked: <reason>`, halt.

### Step 6: Stipe in --branch-only mode

Use the **stipe** subagent (`.claude/agents/stipe.md`) with these arguments:

- `--target-craft docs/primordia/<craft-filename>.md`
- `--path-allowlist <comma-separated paths from craft frontmatter `path_allowlist:` field>`
- `--branch-only`

Stipe creates branch `fruiting/<distilled-slug>-<YYYY-MM-DD>`, implements the craft per scope, runs gate quintet, commits, pushes, opens PR via `gh pr create` with the craft summary + repo-relative path link as body. Returns the PR URL.

If gate quintet fails: stipe halts with the failing-gate diagnosis. Branch is **not** pushed. Report to user.

### Step 7: Bookkeeping

After stipe returns the PR URL:

1. Append a new entry to `canon.governance.last_winnowed_proposals[]` (this is a write through `myco molt` — actually no, molt is for contract bumps. Let me reconsider.) — actually, append by direct canon edit through the substrate's canon-write API (Edit tool on `_canon.yaml`), since this is canon-bookkeeping, not contract version bump:

```yaml
last_winnowed_proposals:
  - slug: <distilled-slug>
    craft_path: docs/primordia/<craft-filename>.md
    pr_url: <stipe-returned-PR-URL>
    pr_branch: fruiting/<distilled-slug>-<YYYY-MM-DD>
    originating_distilled_hash: <sha256 from step 1>
    landed_at: <ISO 8601 timestamp>
    senesce_count_at_landing: <current senesce_count from .myco_state>
    status: pending_owner_merge
    vetoed_at: null  # filled by senesce reaper if PR closed-without-merge
    merged_at: null  # filled by senesce reaper or owner manually if merged
```

2. Update `.myco_state/last_auto_evolve.txt` with the current ISO timestamp.

3. Update `.myco_state/auto_evolve_spend.json` with today's incremental spend (estimate ≈ `0.50 USD` per /myco-evolve invocation — 1 primordium + 3 critics + 1 hypha + optional anamorph + 1 stipe).

### Step 8: Report to user

Final report shape:

```
/myco-evolve <distilled-slug>: <SHIPPED-PR | HALTED-AT-<step>>

Pipeline:
  Pre-flight gates:    [pass × 7]
  Step 1 (quarantine): <hash truncated to 12 hex>
  Step 2 (primordium): <craft path> (Round 3: <LANDED|DRAFT|WITHDRAWN>; <K> critics agentIds: <id1, id2, id3>)
  Step 3 (winnow):     <pass|fail>
  Step 4 (hypha):      <ok|blocked: ...>
  Step 5 (anamorph):   <not-needed | drafted: <path>>
  Step 6 (stipe):      <PR URL>
  Step 7 (canon):      last_winnowed_proposals[+1]
  Step 8 (state):      .myco_state/last_auto_evolve.txt updated

PR awaits owner review:
  URL: <PR URL>
  Branch: fruiting/<slug>-<date>
  Owner action: merge to ship, OR close-without-merge to veto (auto_revert.yml will reap).
```

## Refusal vs halt

- **Refusal** (pre-flight gates 1-7) is silent on substrate state — nothing was written, nothing to roll back.
- **Halt at steps 2-6** may have written `docs/primordia/<craft-filename>.md` (if step 2 LANDED then step 3+ failed). The craft stays as a record for human review; subsequent `/myco-evolve` invocations will catch it via step 5's distilled-hash cooldown gate.
- **Halt at step 6 after gate quintet fails** is the deepest point of failure. stipe should have refused; if it gets to the gate-quintet failure, the implementation it tried is in a state where some files may have been Edit'd but not committed. The user must inspect manually; do NOT auto-`git restore`.

## Naming reminders

- Branch: `fruiting/<distilled-slug>-<YYYY-MM-DD>` (real fungal taxonomy; **never** `auto-craft/`).
- Critic role names in primordium spawns: `mycoparasite` / `saprotroph` / `mycorrhiza` (real fungal-ecology terms; satisfy L0:185-186).
- The orchestrator term is "Cycle 自起 fruit—winnow—molt 闭环" — **NOT** "autopoietic loop". The kernel words ("Cycle", "fruit", "winnow", "molt") are existing fungal vocabulary; "自起" (self-initiation) is descriptive.
