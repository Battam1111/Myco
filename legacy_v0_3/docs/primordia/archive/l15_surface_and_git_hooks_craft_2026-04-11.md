---
type: craft
status: ARCHIVED
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.91
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# L15 Trigger Surface Expansion + Optional Git Hook Installer (Wave 18)

## 0. Problem definition

Panorama note `n_20260411T231220_3fb8` surfaced two defensive-layer
holes that the Wave 17 passive-surface patch did **not** address:

- **H-4** L15 trigger-surface whitelist is narrow. `docs/contract_changelog.md`
  — the one file that is *literally* the written record of every kernel
  contract change — is **not** listed as a `kernel_contract` surface.
  Touching it without a sibling craft is therefore invisible to L15.
  The panorama claimed `agent_protocol.md` and `craft_protocol.md`
  were also missing; inspection shows they are already present, so
  only `contract_changelog.md` is a genuine gap. But the scope problem
  is broader: `src/myco/notes.py` and `src/myco/notes_cmd.py` — the
  primary places where hunger logic and CLI plumbing live — are also
  absent from the list. Every single one of the last four contract
  bumps (Wave 14/15/16/17) modified `notes.py` and relied on the
  agent remembering to write a craft.

- **H-5** L15 only fires at `myco lint` time. If the agent
  `git commit`s without running lint (or runs `git commit --no-verify`),
  the reflex never reaches the sensory surface. There is no git hook
  integration. This is an *agent-initiated* sensory channel, same
  fundamental shape as H-1, but for the write path rather than the
  read path.

The two holes share a common defensive principle: **belt-and-suspenders
for the W3 craft obligation**. Wave 17 added a passive read surface
(boot brief sentinel block). Wave 18 adds a wider detection surface
(more trigger files) plus an optional second enforcement surface
(pre-commit hook) that the user can install once and forget.

## Round 1 — structural debate

**A1 (Proposal).** Close H-4 by extending
`canon.system.craft_protocol.reflex.trigger_surfaces.kernel_contract`
with `docs/contract_changelog.md`, `src/myco/notes.py`, and
`src/myco/notes_cmd.py`. Close H-5 by adding a single shell script
`scripts/install_git_hooks.sh` that writes `.git/hooks/pre-commit`
invoking `myco lint --project-dir .` and short-circuiting the commit
on CRITICAL/HIGH findings.

**A2 (Attack — trigger_surface bloat).** If `notes.py` is a kernel
surface then *every* lint or hunger refactor fires L15. Rounds 2/3
already showed that trivial edits are exempted via
`trivial_exempt_lines` (20 lines), but `notes.py` changes are rarely
trivial — most waves touch it with new functions. Does that mean the
agent will be forced to write a craft for every `notes.py` edit?

**A3 (Defense).** Yes — and that is **exactly the correct behavior**.
Every one of the last four contract bumps (Wave 14 session-end
reflex, Wave 15 L13 body schema, Wave 16 timestamp writer, Wave 17
boot brief injector) *already* wrote a craft even though `notes.py`
was not a declared surface. The agent complied from moral discipline
alone. L15 currently catches only `_canon.yaml` + `lint.py`; adding
`notes.py` means the discipline is no longer volitional. The
trivial-exemption remains intact: a 5-line bug fix in `notes.py`
with no new identifiers still skips. Only substantive edits trigger.

**A4 (Attack — hook fragility).** Git hooks are notoriously brittle.
Windows users with cygwin/git-bash path mismatches will fail to run
the hook. CI systems and bare checkouts will silently skip
`.git/hooks/`. If the hook fails on Windows the user may
`--no-verify` out of frustration and silently disable the whole
reflex.

**A5 (Defense — optional installer + fail-open hook).** Three
mitigations: (a) the hook is **opt-in** — `install_git_hooks.sh` must
be run explicitly once per clone; it is not part of `pip install`.
(b) The hook body uses `command -v myco >/dev/null 2>&1 || exit 0`
as the first line: if `myco` is not on PATH the hook exits 0 and the
commit proceeds (fail-open; a missing linter is never worse than no
hook at all). (c) Only CRITICAL/HIGH issues block; MEDIUM/LOW pass
through with stderr warning so the user is informed but not
bulldozed. (d) A companion `install_git_hooks.ps1` could be added
later but is out of scope for this wave — the bash version works
under git-bash on Windows which is the documented shell for Myco.

## Round 2 — implementation details

**B1 (install_git_hooks.sh skeleton).** Contract:

```bash
#!/usr/bin/env bash
# Myco — Optional pre-commit hook installer (Wave 18, contract v0.17.0)
set -eu
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOK="$ROOT/.git/hooks/pre-commit"

if [ ! -d "$ROOT/.git" ]; then
  echo "[myco] not a git checkout (no .git/); abort." >&2
  exit 1
fi

if [ -f "$HOOK" ] && [ "${1:-}" != "--force" ]; then
  if grep -q "MYCO-PRECOMMIT-MARK" "$HOOK" 2>/dev/null; then
    echo "[myco] pre-commit already installed; pass --force to overwrite."
    exit 0
  fi
  echo "[myco] $HOOK exists and is not ours; pass --force to overwrite." >&2
  exit 2
fi

cat > "$HOOK" << 'HOOK_EOF'
#!/usr/bin/env bash
# MYCO-PRECOMMIT-MARK — do not edit by hand, regenerate via scripts/install_git_hooks.sh
# Fail-open: if myco is not installed the hook exits 0 so commits still work.
command -v myco >/dev/null 2>&1 || exit 0
ROOT="$(git rev-parse --show-toplevel)"
OUT="$(myco lint --project-dir "$ROOT" 2>&1)" || true
# Block commit only on CRITICAL or HIGH issues. MEDIUM/LOW print but pass.
if echo "$OUT" | grep -E -q "(\[CRITICAL\]|\[HIGH\])"; then
  echo "$OUT" >&2
  echo "" >&2
  echo "[myco] pre-commit blocked by CRITICAL/HIGH lint issues." >&2
  echo "[myco] fix the above or commit with --no-verify (W1 violation)." >&2
  exit 1
fi
# Still surface MEDIUM/LOW so the agent sees drift between waves.
if echo "$OUT" | grep -E -q "(\[MEDIUM\]|\[LOW\])"; then
  echo "$OUT" >&2
fi
exit 0
HOOK_EOF
chmod +x "$HOOK"
echo "[myco] pre-commit installed at $HOOK"
```

**B2 (Canon surface extension).** Add three entries to
`system.craft_protocol.reflex.trigger_surfaces.kernel_contract`:

```yaml
# Wave 18 (v0.17.0): extended to close H-4. notes.py is the primary
# home of hunger/digest/detect logic; notes_cmd.py is its CLI surface.
# contract_changelog.md is the authoritative ledger — touching it
# without a craft is a direct W3 violation.
- docs/contract_changelog.md
- src/myco/notes.py
- src/myco/notes_cmd.py
```

Template canon (`src/myco/templates/_canon.yaml`) gets the same
additions so new instances ship with the widened surface.

**B3 (Bump handling).** `contract_version: v0.16.0 → v0.17.0`;
`synced_contract_version: v0.16.0 → v0.17.0`. Wave 18 is a **minor**
contract bump because it widens a detection surface rather than
changing any documented schema. `docs/contract_changelog.md` gets a
`v0.17.0` entry. Because this entry itself touches contract_changelog
— which is now a declared trigger surface — L15 will fire on the
first run after the change; the sibling craft (this document, fresh
mtime inside the lookback window) satisfies the evidence requirement
exactly as designed. The commit itself is thus self-hosting evidence
that the new surface works.

**B4 (Dogfood plan).** (1) Apply canon edits. (2) Run `myco lint` —
L15 should NOT fire because this craft is in the same window.
(3) Run `bash scripts/install_git_hooks.sh`. (4) Touch
`src/myco/notes.py` with a whitespace-only edit (<20 lines, no new
identifiers) and verify trivial exemption kicks in. (5) Attempt an
L13-violating edit (bump a craft frontmatter rounds mismatch),
`git add`, `git commit -m test` — hook should block with HIGH.
(6) Revert the bad edit. (7) Real commit passes cleanly.

## Round 3 — edge cases and doctrine

**C1 (Windows path mismatch).** Git hooks run under whatever shell
git finds — on Windows that is `sh.exe` from Git-for-Windows (MSYS
bash). The hook shebang `#!/usr/bin/env bash` works. The single
external call `myco` resolves via `command -v` to whatever is on
PATH; if the user installed myco inside a venv that is not active,
`command -v` returns empty and the hook exits 0 (fail-open). This is
safe — missing lint ≠ silent corruption.

**C2 (Hook already exists, not ours).** Installer refuses to
overwrite unless `--force`. Users with pre-existing hooks (e.g. black
formatter, flake8) get an explicit error rather than silent
destruction.

**C3 (Re-running installer after wave upgrade).** If the hook file
already carries `MYCO-PRECOMMIT-MARK`, the installer prints "already
installed" and exits 0. Running it again after a `git pull` of a
future wave that updates the hook body requires `--force`. This is
acceptable friction — hook semantics change rarely.

**C4 (Interaction with `--no-verify`).** `git commit --no-verify`
bypasses the hook entirely. Per Wave 12 doctrine, `--no-verify` is a
W1 violation unless the user has explicitly approved it. L15 itself
still catches the drift at next `myco lint` run — the hook is a
defensive *second* layer, not the only layer. H-1 (boot brief
sentinel) remains the canonical sensing mechanism.

**C5 (trivial_exempt_lines interaction).** Trivial exemption already
works and is proven by the Wave 15 rebaseline flow. No changes
required. `notes.py` edits that are strictly whitespace / import
reordering continue to pass without craft evidence.

## Decisions

1. **D1** — Extend `trigger_surfaces.kernel_contract` with
   `docs/contract_changelog.md`, `src/myco/notes.py`,
   `src/myco/notes_cmd.py`. Update both kernel canon and template
   canon. (H-4 closed.)

2. **D2** — Ship `scripts/install_git_hooks.sh` as optional, opt-in,
   fail-open pre-commit hook. Hook blocks on CRITICAL/HIGH only;
   MEDIUM/LOW surface but pass. (H-5 closed.)

3. **D3** — Installer refuses to overwrite non-myco hooks unless
   `--force`. Idempotent on re-run if the mark is present.

4. **D4** — Contract bump `v0.16.0 → v0.17.0`, minor (widens
   detection surface, no schema break). Changelog entry in
   `docs/contract_changelog.md`.

5. **D5** — Self-hosting validation: because this craft has fresh
   mtime, the initial lint after landing will not fire L15 on the
   newly-added surfaces — the evidence_pattern scan of log.md +
   primordia covers the window.

6. **D6** — `--no-verify` remains a W1 violation per Wave 12
   doctrine. The hook is a belt; L15 at lint time is the suspenders.
   Neither is sufficient alone; together they are strongly redundant.

7. **D7** — No `.ps1` Windows PowerShell installer in this wave.
   Documented minimum is git-bash; users on native PowerShell who
   want hooks can copy-paste the hook body manually or install Git
   for Windows.

8. **D8** — Hole closure mapping:
   - **H-4** full — all three missing surfaces added.
   - **H-5** full — opt-in hook available; fail-open so never worse
     than status quo; catches the write path regardless of whether
     the agent runs `myco lint` separately.
   - **H-3 / H-6** remain for Wave 19.
   - **H-2 / H-6** (architectural limits) remain for documentation.

## 5. Landing checklist

- [x] Write this craft (3 rounds, confidence ≥0.90, kernel_contract class)
- [ ] Update `_canon.yaml` trigger_surfaces.kernel_contract
- [ ] Update `src/myco/templates/_canon.yaml` trigger_surfaces.kernel_contract
- [ ] Bump `contract_version` v0.16.0 → v0.17.0 in both canons
- [ ] Create `scripts/install_git_hooks.sh`, chmod +x
- [ ] Run `myco lint --project-dir .` — expect 16/16 green (evidence_pattern covers craft mtime)
- [ ] Install hook: `bash scripts/install_git_hooks.sh`
- [ ] Self-test: trivial notes.py edit → exempt; bad commit → blocked
- [ ] Add `v0.17.0` entry to `docs/contract_changelog.md`
- [ ] `myco eat` Wave 18 conclusion note, digest to integrated
- [ ] Append milestone to `log.md`
- [ ] Commit + push via desktop-commander host-side

## 6. Known limitations

- **L-1** PowerShell-native users need Git for Windows installed.
- **L-2** Hook fail-opens if myco is not on PATH — silent but never
  worse than status quo.
- **L-3** `--no-verify` bypasses the hook. Addressed by H-1 (boot
  brief) next session; no per-commit enforcement possible without
  server-side CI.
- **L-4** Widened trigger surface means more L15 fires during
  refactoring sweeps. Expected; trivial_exempt_lines remains the
  escape valve for mechanical edits.
- **L-5** Installer is bash-only this wave. PowerShell variant is
  future work but explicit non-goal here.
