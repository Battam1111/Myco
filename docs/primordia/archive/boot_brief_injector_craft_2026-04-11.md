---
type: craft
status: ACTIVE
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.92
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# Boot Brief Injector + upstream_scan_stale Reader (Wave 17)

## 0. Problem definition

The agent-panorama self-audit (note `n_20260411T231220_3fb8`) surfaced
nine structural holes in Myco's reflex architecture. Four of them
(H-1, H-7, H-8, H-9) share a single root cause:

> **Every reflex arc in Myco depends on the agent voluntarily running
> `myco hunger` or `myco lint` as the "heartbeat" that delivers sensory
> input. If the agent skips that invocation at session boot, every
> downstream reflex silently fails.**

Evidence from the same session: the agent resumed from Batch 3 without
running `myco hunger` at boot, bypassing all Wave 13/14 reflex arcs
entirely. The Wave 14 LOW-severity advisory (Gear 2/4 drift) was
strictly designed to be nudge-not-enforce, but H-1's gap makes "LOW
signal you never see" functionally equivalent to "no signal at all".

H-9 is a related but orthogonal hole: `upstream_scan_last_run` timestamp
now has a writer (Wave 16) but no reader. A declared reflex with an
implemented writer and no nervous system completing the loop.

This craft closes all four in one coherent landing because they form a
single feedback loop: **persist signals → inject into boot context →
agent reads passively → loop closes.**

## 1. Round 1 — Concept

### A1. Claim

Introduce a **boot brief file** at `.myco_state/boot_brief.md` that
caches the current hunger signal summary in a form the agent's
session-boot protocol will *automatically* encounter via
`MYCO.md` hot zone reference. Every invocation of `myco hunger` writes
the brief as a side effect. The brief's freshness timestamp is visible,
so staleness itself becomes a signal. Additionally, extend
`compute_hunger_report` with a new `upstream_scan_stale` detector that
reads the Wave 16 timestamp and fires when stale, closing H-9.

### A2. Attack — "Writing a file the agent must still read is just
moving the hunger-call problem one step."

If the agent has to `cat .myco_state/boot_brief.md` at boot, that's
exactly the same discipline gap as "agent has to run `myco hunger`".
What's the actual delta in effort?

### A3. Defense

The delta is in **which surface the signal lives on**. `MYCO.md` is
read *automatically* by the project-instructions mechanism — the
agent doesn't *choose* to read it, it is delivered as part of the
context window assembly. So if `MYCO.md` contains a visible reference
to the brief AND a short inline digest of its most urgent signals,
the agent sees the signal without any volitional act. This is the
difference between "must call getchar()" and "stdin is piped into
you". CLAUDE.md/MYCO.md is the only stdin pipe Myco can reach.

Concretely: we append a small "🫀 Boot Signals" block near the top of
the MYCO.md template that the kernel re-renders after every hunger
run. The block includes: (a) the last-hunger timestamp, (b) a single
line per active high-priority signal (contract_drift, raw_backlog
HIGH, upstream_scan_stale, craft_reflex_missing), (c) a pointer to
the full brief for detail.

### A4. Revise

Refine A1: the brief file is the **evidence artifact**, but the
**injection surface** is `MYCO.md`'s hot zone. Two files, two roles:

- `.myco_state/boot_brief.md` — full details, written by hunger,
  human-readable, timestamped.
- `MYCO.md` top block — short digest (≤8 lines) auto-rendered by
  hunger, contains the 1-line-per-signal summary + freshness stamp +
  pointer to the full brief.

Rendering into `MYCO.md` requires a **deterministic region marker**
(begin/end sentinel comments) so the hunger writer can in-place-patch
exactly that block without touching the rest of the file. This is
the same pattern README badges use.

## 2. Round 2 — Design

### B1. Claim

Implementation details:

1. New directory `.myco_state/` — **not** in L11 write surface
   (dotdirs are exempt), but **must be** added to L12's allowed
   dotdir whitelist, otherwise L12 flags it HIGH ("unknown `.myco_*`
   top-level dir"). Add as a new ALLOWED_DIR with its own permissive
   validation (any `.md` or `.json` file allowed, no bundle pattern).
2. New function `write_boot_brief(root, report) -> Path` in
   `src/myco/notes.py` — serializes a HungerReport to markdown.
3. New function `render_myco_md_signals_block(root, report)` in
   `src/myco/notes.py` — regex-patches the MYCO.md region between
   `<!-- MYCO-BOOT-SIGNALS:BEGIN -->` and `<!-- MYCO-BOOT-SIGNALS:END -->`
   sentinels. If the sentinels are absent (user has deleted them or
   hasn't migrated), emit a `[WARN]` and skip — never crash hunger.
4. Wire both into `myco hunger` CLI: after `compute_hunger_report`
   returns, call both writers. Failures of either are WARN not fatal.
5. New function `detect_upstream_scan_stale(root)` in
   `src/myco/notes.py`, called from `compute_hunger_report`. Reads
   `system.upstream_scan_last_run` + canon config
   `upstream_scan.stale_days` (default 7) + counts files in
   `.myco_upstream_inbox/`. Fires HIGH if (stale AND bundles pending),
   MEDIUM if stale AND no bundles, silent otherwise.
6. Sentinel block injected into `src/myco/templates/MYCO.md` so new
   instances ship with the marker. Existing instances (including the
   ASCC one) need migration — see B4.

### B2. Attack — "What if the agent is running in Cowork sandbox with
no CLAUDE.md visibility, only system-prompt injected project
instructions?"

The ASCC instance operates in a Cowork sandbox where the file at
`/sessions/.../mnt/OPASCC/CLAUDE.md` IS injected as the project
instructions. So renaming my target from `MYCO.md` to the ASCC
project's own CLAUDE.md would be the right move there. But the kernel
repo's own boot surface is `MYCO.md`. Does the craft handle both?

### B3. Defense

Yes. The rendering function takes the **entry point filename from
`_canon.yaml::system.entry_point`** (existing field, defaults to
`MYCO.md`; ASCC instance already uses `CLAUDE.md`). So the same code
patches whichever file the local canon declares as the entry point,
per project. No hardcoding. Existing `get_entry_point(canon)` helper
in lint.py already does this lookup.

Additional benefit: the sentinel block becomes part of the entry
point regardless of project type. ASCC's CLAUDE.md hot zone gets
the block; kernel's MYCO.md hot zone gets the block; both are read
at boot by their respective hosting agents.

### B4. Revise

Migration plan for existing instances (kernel + ASCC):

- **Kernel repo**: edit `src/myco/templates/MYCO.md` and the live
  `MYCO.md` at repo root, adding the sentinel block at the documented
  location ("hot zone", near top).
- **ASCC instance** (`/sessions/.../mnt/OPASCC/CLAUDE.md`): edit in
  this session as part of Wave 17 landing, so the Myco kernel agent
  demonstrates dogfood across its two primary test beds. The ASCC
  CLAUDE.md is user-curated content and has a documented "🔥 热区" so
  I'll insert the sentinel block inside the hot zone.
- **Instances without sentinel**: hunger logs `[WARN] MYCO.md signals
  block sentinel not found — skipping in-place render. Run `myco
  migrate` or add manually.`. Feature remains opt-in by migration,
  not forced, preserving grandfather doctrine.

The `myco migrate` command (existing v0.2.0 utility) should gain a
new step: if the entry point file lacks the sentinel block, add it.
Out of scope for Wave 17 to avoid scope creep — will be Wave 17-b if
needed, but the `[WARN]` path is safe in the interim.

## 3. Round 3 — Edges

### C1. Claim

Edge handling:

- **Sentinel corruption**: if the BEGIN marker exists but END does
  not (user deleted END), hunger falls back to WARN + skip. Does NOT
  write partial content.
- **Multiple sentinel pairs**: regex must require exactly one pair.
  Zero or >1 → WARN + skip.
- **Stale brief on disk with no current hunger run**: the brief file
  carries its own timestamp; readers (future consumers + human
  inspection) MUST treat timestamp > 24h as "stale, may be lying".
  The MYCO.md sentinel block echoes this timestamp, so staleness is
  always visible.
- **Concurrent hunger runs**: file writes are NOT locked. Last writer
  wins. Acceptable because hunger is a read-mostly diagnostic and
  conflicting writers would converge to the same content anyway.
- **`.myco_state/` doesn't exist**: hunger auto-creates it on first
  successful run. `mkdir(exist_ok=True)` with narrow error handling.

### C2. Attack — "Won't regex-patching `MYCO.md` trip the `L0-L8`
lints that check number consistency, date consistency, etc.?"

The signals block contains numbers (raw_backlog counts) and dates
(timestamps). L2 (number consistency) and L6 (date consistency)
check against `_canon.yaml` SSoT. If the signals block injects a
raw_backlog count of 5 but `_canon.yaml` says raw_backlog_threshold
is 10, does L2 flag it as inconsistency?

### C3. Defense

L2 checks quantified indicators against canon; raw_backlog is a
**runtime measurement**, not a canonical constant. L2 uses an
allowlist of indicator names to check (principles_count, etc.).
`raw_backlog_current` is not in that allowlist and will be silently
ignored. Same for L6 — dates in prose text are tolerated; only
header dates like `>最后更新：YYYY-MM-DD` are cross-checked.

Defensive move: use a distinct, machine-readable format within the
sentinel block (e.g. `last_hunger_run: "2026-04-11T23:14:00Z"`) but
wrap each line as a markdown blockquote so it looks like narrative
not data. Alternatively — and this is what I'll do — prefix every
line in the block with a zero-width marker (e.g. `> 🫀 `) so L2/L6
can be taught in a future lint iteration to treat the block as
opaque. For now, the existing L2/L6 implementations don't even look
at this region, so no immediate conflict.

### C4. Revise

Add an **explicit L2/L6 exclusion**: declare the signals block
region as "ignore for number/date consistency checks" in canon. The
simplest approach is to document it in the sentinel comment itself:

```
<!-- MYCO-BOOT-SIGNALS:BEGIN (auto-generated by myco hunger; L2/L6 ignore) -->
...
<!-- MYCO-BOOT-SIGNALS:END -->
```

This is both human-readable and greppable. If future L2/L6 iterations
want to skip the region, they match on `MYCO-BOOT-SIGNALS:BEGIN` and
seek to END. Implemented defensively now (document the intent);
lint-side skip can land in Wave 17-b if needed.

## 4. Conclusion extraction

Decisions:

- **D1**: Boot brief lives at `.myco_state/boot_brief.md`, written as
  side effect of `myco hunger`.
- **D2**: Condensed signals block rendered in-place into entry-point
  file (`MYCO.md` or `CLAUDE.md` per canon) using sentinel markers.
- **D3**: New `detect_upstream_scan_stale(root)` hunger channel reads
  `upstream_scan_last_run` + `.myco_upstream_inbox/` files. Config
  in canon: `system.upstream_scan.stale_days` (default 7).
- **D4**: `.myco_state/` is a new kernel-managed dotdir. L12 extended
  to whitelist it alongside existing upstream dotdirs.
- **D5**: All writes are best-effort: failures emit `[WARN]` but
  never fail the containing hunger call.
- **D6**: Sentinel block format: `<!-- MYCO-BOOT-SIGNALS:BEGIN ... -->`
  / `... END -->` with L2/L6 exclusion noted in the BEGIN comment.
- **D7**: Migration: hand-patch kernel `MYCO.md` and ASCC `CLAUDE.md`
  as part of landing. `myco migrate` auto-injection out of scope for
  this Wave (future work).
- **D8**: Contract bump v0.15.0 → v0.16.0 (minor, backward compatible).
- **D9**: This fix addresses H-1 (boot signal injection), H-7 (Wave
  14 LOW visibility via brief), H-8 (partial — session-end drift
  will appear in next-session brief even if current session ends
  abruptly), and H-9 (upstream_scan_stale reader). H-8 remains
  partial because the initial writer still has to write; we just
  ensure the reader sees it.

## 5. Landing checklist

- [x] Write this craft
- [ ] Extend L12 ALLOWED_DIRS with `.myco_state` + permissive
      validation
- [ ] Add `detect_upstream_scan_stale(root)` to `src/myco/notes.py`
- [ ] Wire `detect_upstream_scan_stale` into `compute_hunger_report`
- [ ] Add `write_boot_brief(root, report)` to `src/myco/notes.py`
- [ ] Add `render_entry_point_signals_block(root, report)` to
      `src/myco/notes.py`
- [ ] Wire both writers into `src/myco/cli.py::hunger_cmd` (or the
      appropriate CLI handler)
- [ ] Add `system.upstream_scan` config block to `_canon.yaml` and
      `src/myco/templates/_canon.yaml`
- [ ] Bump contract v0.15.0 → v0.16.0 in both canons
- [ ] Add sentinel block to `src/myco/templates/MYCO.md` and live
      `MYCO.md`
- [ ] Add sentinel block to `/sessions/.../mnt/OPASCC/CLAUDE.md` hot
      zone (dogfood across test beds)
- [ ] Self-test: run `myco hunger`; verify `.myco_state/boot_brief.md`
      appears; verify MYCO.md signals block is populated with current
      hunger summary
- [ ] Synthetic test: manually set `upstream_scan_last_run` to an
      8-day-old timestamp; create a dummy bundle file; run `myco
      hunger`; verify `upstream_scan_stale` signal appears HIGH
- [ ] `myco lint --project-dir .` → 16/16 green
- [ ] Add v0.16.0 entry to `docs/contract_changelog.md`
- [ ] `myco eat` Wave 17 conclusion note, digest to integrated
- [ ] Append Wave 17 milestone to `log.md`
- [ ] Commit + push via desktop-commander host-side

## 6. Known limitations

- **L-1 (Migration is manual for Wave 17)**: existing instances must
  hand-patch their entry point file once. Future Wave 17-b can
  automate via `myco migrate`.
- **L-2 (Freshness is passive)**: the brief's freshness stamp is
  visible but there's no "hunger_stale" signal that escalates
  staleness itself. If hunger hasn't run in a week, the brief says
  so, but no signal actively nags. Acceptable because the natural
  consequence — agent reads an old brief and notices the date — is
  itself a nudge.
- **L-3 (H-8 remains partial)**: session-end drift still depends on
  the initial `myco hunger` call at next boot. We're not creating a
  new sensory channel; we're just making existing sensory input
  land in passive surfaces. True H-8 closure needs host-side
  cooperation (session hook) which is outside kernel scope.
- **L-4 (L2/L6 exclusion is documented not enforced)**: the BEGIN
  comment says "L2/L6 ignore" but current L2/L6 implementations
  don't actually read this hint. If a future L2/L6 iteration begins
  checking the region, it must be updated to skip. Flagged for
  future work.
- **L-5 (Concurrency not locked)**: hunger writes are not file-locked.
  Last writer wins. Concurrent hunger runs on the same repo are
  rare (single-agent assumption) so acceptable for v0.16.0.
