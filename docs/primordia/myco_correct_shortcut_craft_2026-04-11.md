---
type: craft
status: ACTIVE
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.91
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# `myco correct` — On-Self-Correction Ergonomic Shortcut (Wave 19)

## 0. Problem definition

Panorama note `n_20260411T231220_3fb8` identifies H-3 as MEDIUM:

> **Hard Contract rule #3 special clause**: the agent must, in the
> same turn as a self-correction ("what I said earlier about X is
> wrong"), run `myco eat --tags friction-phase2,on-self-correction`.
> In this session alone, at least 3 self-corrections went uneaten
> (duplicate function stub, missing `List` import, `m.end()` vs
> `m.group('body')` bug). There is **no lint dimension** that covers
> this rule.

The previous waves already showed that when the agent is required
to remember **both the rule and the exact tag incantation**, the
rule silently dies under execution pressure. Wave 17 solved the
*read-path* visibility for H-1. Wave 18 added a defensive write-path
hook for H-5. Wave 19 targets the *ergonomic* dimension: reduce the
cost of compliance to a single verb so the rule survives even under
cognitive load.

**Scope boundary**: this is an ergonomic shortcut, not a detector.
L13/L15 cannot structurally detect "the agent corrected itself" —
the only workable detection surface is a chat-stream NLP classifier,
which is out of scope for kernel code and better suited to Phase 2
MCP server hooks. H-3 is therefore labeled "partial" in the closure
mapping: the ergonomic barrier drops to zero, but compliance
remains volitional. This is the best a CLI-level intervention can
achieve without hosting collaboration.

## Round 1 — structural debate

**A1 (Proposal).** Add a new subcommand `myco correct` to the CLI.
Semantics: a thin wrapper over `myco eat` that auto-injects
`--tags friction-phase2,on-self-correction,self-correction` and
defaults `--source` to `"eat"`. Body is provided via `--content`,
`--file`, or stdin (same as eat). An optional `--tags` argument
appends user-provided tags in addition to the mandatory trio.

Example invocations:

```
myco correct --content "I said TR_SPEED was normalised; it isn't — see src/foo.py:42"
myco correct --title "Lint regex uses m.end() instead of m.group('body')" --content "..."
echo "text..." | myco correct
```

**A2 (Attack — is this just an alias?).** If `correct` is literally
`eat --tags ...`, why not tell the agent to memorise one shell alias
and be done? Why put it in kernel code?

**A3 (Defense).** Three reasons.
1. **Cross-platform portability**: shell aliases live in the user's
   dotfiles (bash/zsh/pwsh all different). A kernel verb works
   identically on every host. Agents do not set up per-host aliases.
2. **Discoverability**: `myco --help` lists subcommands; aliases
   don't. A new agent sessioning into an unfamiliar Myco sees
   `correct` in the help output and can pattern-match it to the rule
   text in `MYCO.md`.
3. **Enforceable tag contract**: an alias can be edited by the user;
   a subcommand guarantees the exact tag string that downstream
   digestion and Phase 2 signal-source routing depend on. If a
   future wave wants to count `on-self-correction` notes via
   `myco hunger`, that depends on the tag being canonical.

**A4 (Attack — tag sprawl).** Adding `self-correction` as a third
tag (in addition to `friction-phase2,on-self-correction`) is
redundant. Pick one.

**A5 (Defense — trim to two).** Agreed. Final mandatory tag set is
`friction-phase2, on-self-correction`. The third `self-correction`
tag is dropped. Matches the Hard Contract literally.

**A6 (Attack — why not make `myco eat --correct` a flag?).** A
flag on `eat` would be lower code footprint. One less subcommand.

**A7 (Defense — command-name mnemonics).** Subcommand names are
what an agent under cognitive load can type fastest. `myco correct`
reads left-to-right as the rule itself. `myco eat --correct`
requires two memory operations: "eat" + "the correct flag". The
whole point of the wave is that the agent **forgets** auxiliary
arguments when correcting itself. A verb is one memory operation;
a flag is two. This is the entire justification; anything that
dilutes it kills the wave.

## Round 2 — implementation details

**B1 (Command body).** New function `run_correct(args)` in
`src/myco/notes_cmd.py`:

```python
def run_correct(args) -> int:
    """`myco correct` — self-correction shortcut (Wave 19).

    Ergonomic wrapper over `run_eat` that injects the mandatory tag
    pair `friction-phase2, on-self-correction` required by Hard
    Contract rule #3 special clause. Any additional tags supplied
    via --tags are appended. Title defaults to
    "Self-correction: <first line>" if unset.
    """
    # Force the mandatory tag set while preserving user additions.
    user_tags = [t.strip() for t in (getattr(args, "tags", "") or "").split(",") if t.strip()]
    required = ["friction-phase2", "on-self-correction"]
    merged = required + [t for t in user_tags if t not in required]
    args.tags = ",".join(merged)
    if not getattr(args, "source", None):
        args.source = "eat"
    return run_eat(args)
```

**B2 (CLI parser).** New subparser in `src/myco/cli.py` mirroring
`eat_parser` but with an explicit help line:

```python
correct_parser = subparsers.add_parser(
    "correct",
    help="Self-correction shortcut — eat a friction note with "
         "mandatory tags 'friction-phase2, on-self-correction' "
         "(Hard Contract rule #3)",
)
correct_parser.add_argument("--content", type=str, default=None)
correct_parser.add_argument("--file",    type=str, default=None)
correct_parser.add_argument("--tags",    type=str, default="",
    help="Additional tags, merged with the mandatory pair")
correct_parser.add_argument("--source",  type=str, default="eat",
    choices=["chat", "eat", "promote", "import", "bootstrap"])
correct_parser.add_argument("--title",   type=str, default=None)
correct_parser.add_argument("--json",    action="store_true")
correct_parser.add_argument("--project-dir", type=str, default=".")
```

Plus a dispatch branch in `main()`:

```python
if args.command == "correct":
    from myco.notes_cmd import run_correct
    sys.exit(run_correct(args))
```

**B3 (Canon entry).** Add to `_canon.yaml` under `system` an
authoritative declaration of the mandatory tag set so future waves
can reference it without hard-coding:

```yaml
self_correction:
  # Wave 19 (v0.18.0): Hard Contract rule #3 special clause — agent
  # must eat a note in the same turn as a self-correction. The
  # `myco correct` CLI shortcut enforces these tags; manual `myco eat`
  # should also use this exact pair when the condition applies.
  mandatory_tags:
    - friction-phase2
    - on-self-correction
```

**B4 (Documentation touchpoint).** `docs/agent_protocol.md` Hard
Contract rule #3 currently describes the rule in prose. Add a
single sentence: "The `myco correct` shortcut packages these
mandatory tags into one verb; prefer it over `myco eat --tags
...` whenever the condition applies."

## Round 3 — edge cases and doctrine

**C1 (Preserving user tags when they collide with mandatory).**
The merge logic deduplicates: `[t for t in user_tags if t not in
required]`. A user passing `--tags on-self-correction,other` ends
up with `["friction-phase2", "on-self-correction", "other"]`, not
doubled. Order-preserving.

**C2 (What if `run_eat` signature changes in a future wave?).**
`run_correct` delegates to `run_eat` with `args` unchanged except
for `.tags`. Any future eat argument is inherited automatically.
The ergonomic shortcut is a thin shim, not a fork.

**C3 (Does `myco correct` bypass project-dir resolution?).** No —
`run_eat` calls `_project_root(args)` which handles `--project-dir`
identically. `myco correct --project-dir X --content "..."` works
in subprojects.

**C4 (Should L10 enforce that any note with `on-self-correction` tag
must also have `friction-phase2`?).** Tempting but out of scope. L10
is schema validation (status/source/id), not semantic coupling.
Adding such a rule would block legitimate manual `myco eat` calls
from older wave conventions and create retroactive failures. Keep
the canon entry declarative for now; a future wave can add L10 or
L16 enforcement if the tag drift becomes a real problem.

**C5 (Dogfood symmetry).** Wave 18 was self-hosting because the new
trigger surfaces were touched by the wave itself. Wave 19 is
self-hosting in a different sense: the wave's motivating example
(the three uneaten self-corrections earlier in this session) can
be retroactively captured by running `myco correct` on each one
after landing. This craft records that intention; actual retro-eat
is optional belt-and-suspenders and can be skipped for brevity.

**C6 (Contract class selection).** This wave touches `notes_cmd.py`
and `cli.py`, both of which are declared kernel_contract trigger
surfaces after Wave 18. Therefore the craft is kernel_contract
class with 0.90 floor. Target hit at 0.91.

## Decisions

1. **D1** — Add `myco correct` subcommand. `run_correct` in
   `notes_cmd.py` is a thin wrapper over `run_eat` that force-merges
   the mandatory tag pair. (H-3 partial closure: ergonomic barrier
   drops to zero.)
2. **D2** — Mandatory tags: `friction-phase2, on-self-correction`
   (exactly two, matching Hard Contract literal text). Canon entry
   `system.self_correction.mandatory_tags` makes this declarative.
3. **D3** — Additional user tags are appended after the mandatory
   pair, order-preserving, deduplicated.
4. **D4** — `docs/agent_protocol.md` Hard Contract rule #3 gets a
   one-sentence nudge pointing at the new shortcut.
5. **D5** — No L10/L16 enforcement of the tag coupling; that is a
   future wave's problem if it becomes one.
6. **D6** — Contract bump `v0.17.0 → v0.18.0`, minor (new CLI verb,
   no schema break). Changelog entry in
   `docs/contract_changelog.md`.
7. **D7** — Hole closure: **H-3 partial** — ergonomic barrier gone,
   compliance still volitional because kernel code cannot detect
   self-correction text; full closure requires chat-stream NLP
   which is Phase 2 MCP work.
8. **D8** — Retroactive eat of this session's three uneaten
   self-corrections is *not* required for wave completion. The
   wave lands green regardless. Mentioned here for honesty about
   scope.

## 5. Landing checklist

- [x] Write craft (3 rounds, kernel_contract class, confidence ≥0.90)
- [ ] Add `run_correct` to `src/myco/notes_cmd.py`
- [ ] Add `correct` subparser + dispatch to `src/myco/cli.py`
- [ ] Add `system.self_correction.mandatory_tags` to `_canon.yaml`
      and `src/myco/templates/_canon.yaml`
- [ ] Bump `contract_version` v0.17.0 → v0.18.0 in both canons
- [ ] Add one-sentence nudge to `docs/agent_protocol.md` Hard
      Contract rule #3
- [ ] Self-test: `myco correct --content "test"` creates a note
      with correct tags; `myco view` shows them
- [ ] `myco lint` → 16/16 green
- [ ] Changelog `v0.18.0` entry
- [ ] `myco eat` Wave 19 conclusion, digest to integrated
- [ ] Append milestone to `log.md`
- [ ] Commit + push

## 6. Known limitations

- **L-1** Cannot detect self-correction text — full H-3 closure
  requires chat-stream NLP (Phase 2 MCP hook).
- **L-2** Agent must still *remember to run* `myco correct`. Wave
  17 boot brief is the read-path reminder; the Hard Contract text
  in MYCO.md is the anchor. No further enforcement is possible at
  kernel level.
- **L-3** Tag dedup is exact-string; minor spelling variants
  (`friction_phase2` vs `friction-phase2`) are treated as distinct.
  Acceptable — the canonical tag is fixed by canon.
