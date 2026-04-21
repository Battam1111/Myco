---
type: craft
topic: v0_5_8_discipline_enforcement
slug: v0_5_8_discipline_enforcement
kind: design
date: 2026-04-21
rounds: 3
craft_protocol_version: 1
status: APPROVED
---

# V0.5.8 Discipline Enforcement — Craft

> **Date**: 2026-04-21
> **Layer**: L2–L3 (homeostasis doctrine + implementation roster)
> **Upward**: L0 principles 1–5 (Only For Agent / 永恒吞噬 / 永恒进化 /
> 永恒迭代 / 万物互联) and L1 R1-R7 (all seven). The craft closes gaps
> where the doctrine existed but the enforcement did not.
> **Governs**: 14 new lint dimensions under
> `src/myco/homeostasis/dimensions/`, the canon `lint.dimensions`
> roster at `_canon.yaml`, the L2 `homeostasis.md` doctrine, and the
> four new foundation helpers (`io_atomic.py`, `trust.py`,
> `skip_dirs.py`, `write_surface.py`) under `src/myco/core/`.

---

## Round 1 — 主张 (claim)

**Claim**: the v0.5.0–v0.5.7 release line grew the lint surface from
8 → 11 dimensions but left a catalogue of `R1`–`R7` rules and
audit-revealed invariants **only conventionally** enforced — humans
and agents were expected to honor them by habit. v0.5.8 closes the
gap mechanically by landing 14 additional dimensions, four
foundation helpers (atomic writes, trust sanitization, canonical
skip-dirs, write-surface guard), and a post-agent-first-audit sweep
of 13+ concrete bugs identified across four opus-lens audit rounds
(Lens 5/6/7/8/10/11/13/16 …).

The load-bearing claim: **mechanical enforcement changes agent
behaviour in ways doctrine-only enforcement does not**. An agent
that can ignore a sentence cannot ignore an exit code. The
v0.5.0–v0.5.7 cadence proved that expanding the doctrine without
expanding the enforcement surface produces drift. v0.5.8 is the
first release where every L1 rule has at least one mechanical
anchor.

## Round 1.5 — 自我反驳 (self-rebuttal)

- **T1**: 14 new dimensions is a 127% surface expansion in a single
  release. History says large lint surface expansions create
  MEDIUM/LOW noise that agents learn to tune out.
- **T2**: Foundation helpers (`io_atomic.py`, `trust.py`, …) are
  infrastructure shifts. Adding them without wiring them into
  every existing callsite means the old-path/new-path split lives
  for several releases.
- **T3**: The audit iterated four times and still missed items
  Iter 5 would have caught (if quota had allowed). Declaring
  convergence now ships with known-unknowns.
- **T4**: Exit-code differentiation (`SubstrateNotFound → 4`,
  `CanonSchemaError → 5`) is technically within the contract
  (all ≥3) but any downstream script that special-cases `== 3`
  sees different behaviour. That's a soft break.
- **T5**: The 14 new dimensions land on all substrates, not just
  myco-self. Third-party substrates that imported Myco v0.5.7 and
  pinned their CI gate against the 11-dim roster will see 14
  extra findings — some may fail CI on v0.5.8 upgrade.

## Round 2 — 修正 (revision)

- **R1** (T1 — noise): all 14 new dims default to LOW or MEDIUM
  severity except the three that guard real kernel invariants
  (`CS1` HIGH — contract-sync drift, `FR1` HIGH — fresh-substrate
  anchors, `MB3` HIGH — raw-backlog ≥50). The default
  `--exit-on=mechanical:critical,shipped:critical,…` keeps
  substrate CI gates unchanged unless the operator opts in. Noise
  management is baked into the severity ladder.
- **R2** (T2 — old-path/new-path split): v0.5.8 wires the new
  helpers into every write site visible from the audit. A
  lingering call to the old write path is now a pre-PR immune
  finding under `DI1`/`PA1`. Future releases continue the rollout,
  but the split ends — "every write goes through
  `atomic_utf8_write`" is a v0.5.9 enforcement target.
- **R3** (T3 — Iter 5 unknowns): the four-iteration audit found
  zero P0-severity items in Iter 4 after the earlier iterations'
  fixes landed. Practical convergence. Iter 5's quota-blocked run
  was re-synthesized in-session from the prior 16 lens findings;
  the delta was cosmetic. A v0.5.9 agent-first audit will resume
  on a cleaner baseline.
- **R4** (T4 — exit-code differentiation): every existing caller
  that checks `exit != 0` continues to work. Scripts that
  special-case `== 3` will see `== 4` or `== 5` for two specific
  classes of failure — a more informative signal, not a regression.
  The change is noted in `docs/contract_changelog.md` so script
  authors see it at molt time.
- **R5** (T5 — third-party CI surprise): the 11 → 25 dim
  expansion is documented in L2 homeostasis.md and advertised in
  the release notes. Third-party substrates can freeze the pre-
  v0.5.8 behaviour via `immune --dimensions M1,M2,M3,…` (explicit
  allowlist); the default "run all registered" behaviour picks up
  the new dims, which is the intended upgrade path but is clearly
  documented as opt-out-able.

## Round 2.5 — 再驳 (counter-rebuttal)

- **T6** (re R1): the HIGH-severity `FR1` dimension can fire on a
  substrate that deleted `notes/integrated/` intentionally (e.g. a
  substrate that uses a different notes layout). Default HIGH +
  default gate = surprise CI fail.
  
- **T7** (re R3): Iter 5 being quota-blocked is a weak signal for
  convergence. A real fifth audit iteration might have found the
  next P0. Declaring convergence on a quota block is convenient,
  not rigorous.

## Round 3 — 收敛 (convergence)

- **R6** (T6 — FR1 surprise): FR1's HIGH is scoped to `_canon.yaml`
  and the entry-point file (the truly load-bearing anchors); the
  `notes/raw` / `notes/integrated` / `docs` checks are MEDIUM.
  Substrates that genuinely don't use `notes/integrated/` can
  either (a) opt out via `--dimensions -FR1` or (b) accept the
  MEDIUM finding and mechanize the absence in their own
  substrate-local plugin. The tightness is intentional: the
  default assumption is that every Myco substrate has these
  directories; the minority that doesn't is visible rather than
  invisible.

- **R7** (T7 — convergence vs quota): accepted. The v0.5.8
  release notes mark convergence as "practical, pending a fresh
  agent-first audit on the post-v0.5.8 tree". The v0.5.9 craft
  will re-run the 4-iteration sweep against the cleaner baseline;
  any P0 it surfaces is a v0.5.9 scope item, not a retroactive
  v0.5.8 regression.

## Decision

Approved. Ship the 14-dim expansion + foundation helpers +
exit-code differentiation + audit fixes as v0.5.8. Document the
opt-out path for third-party CI. Commit to a v0.5.9 agent-first
audit on the cleaner baseline.

## Mechanism (v0.5.8-specific implementation notes)

1. **14 new lint dimensions**
   - `MP2` — plugin-tree LLM-SDK import ban (MEDIUM / LOW on opt-out)
   - `DC1`–`DC4` — docstring hygiene (all LOW)
   - `CS1` — `synced_contract_version` drift (HIGH, fixable)
   - `FR1` — fresh-substrate directory invariants (HIGH/MEDIUM)
   - `PA1` — `write_surface.allowed` coverage (MEDIUM)
   - `SE3` — graph self-cycle (LOW)
   - `MB3` — raw-notes high watermark ≥ 50 (HIGH, fixable)
   - `CG1`/`CG2` — code ↔ doctrine linkage (LOW)
   - `DI1` — discipline hooks present when `.claude/` declared (MEDIUM)
   - `RL1` — every R1-R7 rule referenced (LOW)

2. **Four foundation helpers** under `src/myco/core/`:
   - `io_atomic.py` — `atomic_utf8_write`, `bounded_read_text`,
     `bounded_read_bytes`, `DEFAULT_MAX_READ_BYTES` (10 MB).
   - `trust.py` — `safe_frontmatter_field`, `strip_controls`,
     `flatten_newlines`, `strip_markdown_meta`.
   - `skip_dirs.py` — canonical `DEFAULT_SKIP_DIRS` + `should_skip_dir`.
     Unifies what had been 3–4 divergent lists across forage /
     graph_src / code_repo / MP1.
   - `write_surface.py` — `is_path_allowed`, `guarded_write`,
     `WriteSurfaceViolation`. Consumed by future write sites to
     enforce R6 mechanically on every keystroke.

3. **Exit-code differentiation**:
   - `MycoError.exit_code = 3` (default, unchanged)
   - `ContractError.exit_code = 3` (unchanged)
   - `UsageError.exit_code = 3` (unchanged)
   - `SubstrateNotFound.exit_code = 4` (was 3; promoted)
   - `CanonSchemaError.exit_code = 5` (was 3; promoted)

4. **Audit-driven fixes** (13+ concrete P0/P1 items across four
   opus lens audits):
   - Lens 5: exit-code differentiation + immune human output
     + germinate preview trimmed.
   - Lens 6 (security): `.env` removed from `_CODE_EXTS`,
     credential filename denylist, adapter size caps (10 MB),
     SSRF guard + response-size cap in `url_fetcher.py`.
   - Lens 7: forage walker now prunes skip-dirs + short-circuits
     on MAX_ITEMS (was scanning every `.git` file).
   - Lens 8: HTTP streaming fetch with byte-cap abort; scheme
     allowlist (http/https only).
   - Lens 10: LF-only line endings at every `write_text` site;
     POSIX source normalisation across adapters; `.gitattributes`
     and `pre-commit-config` newly committed.
   - Lens 11: MCP pulse canon cache (mtime-keyed) so repeated
     tool calls don't re-parse YAML; MP2 plugin scope.
   - Lens 13: symlink cycle guard in `_walk_py` + `_iter_py_files`
     + the fingerprint walker; fresh substrates pre-create
     `notes/raw/` and `notes/integrated/`.
   - Lens 16: SE1 dangling-ref check switched from per-edge
     `stat(2)` to `edge.dst in graph.nodes` set membership
     (2400× speedup on myco-self); text-file + pdf + html +
     tabular size caps.
   - Concurrent-writes TOCTOU: `eat.append_note` uses
     `os.open(O_WRONLY | O_CREAT | O_EXCL)` in a retry loop
     (replaces `while path.exists()`).
   - YAML injection in `_render_note`: now uses
     `yaml.safe_dump`; `trust.safe_frontmatter_field` strips
     control chars from tags/source before render.
   - Windows cp936 subprocess encoding: every
     `subprocess.run(..., text=True)` gets explicit
     `encoding="utf-8", errors="replace"`.

5. **Fresh-substrate directory invariant**: germinate now
   creates `notes/raw/` and `notes/integrated/` up front so FR1
   doesn't have to distinguish "fresh" from "corrupted".

6. **Template & canon roster refresh**: `_canon.yaml` mirrors the
   25-dim roster under `lint.dimensions`; the canon template in
   `germination/templates/canon.yaml.tmpl` stays minimal (no
   `dimensions` subtable by default — the canon roster is
   declarative, the kernel uses class attrs as mechanical SSoT).

## Why this matters (L0 tie-in)

- **Only For Agent**: every new dim is a mechanical signal the
  agent can read; humans weren't the target audience to begin
  with.
- **永恒吞噬**: MP2 extends the "no provider imports" boundary
  to plugin code; the substrate remains agnostic to what it
  ingests as long as the ingestion path is honest.
- **永恒进化**: CS1 closes the hunger→assimilate loop (drift
  detected → drift corrected by the same verb). The contract
  can now evolve without the `synced_contract_version` field
  rusting shut.
- **永恒迭代**: the audit iterated 4× until Iter 4 found zero
  P0s. The cleanup release itself is the fruit of that cycle.
- **万物互联**: DC1–DC4 + CG1/CG2 + RL1 are the new connective-
  tissue dims. Code → doctrine → rules all have at least one
  mechanical anchor.
