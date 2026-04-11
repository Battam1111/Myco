---
type: craft
status: ACTIVE
created: 2026-04-12
target_confidence: 0.85
current_confidence: 0.85
rounds: 3
craft_protocol_version: 1
decision_class: exploration
closes:
  - "Wave 26 §2.3 long-tail priority: 'Metabolic Inlet — design craft once compression engineering (open_problems §4) is partially unblocked'"
  - "Wave 26 Attack C: 'Metabolic Inlet has 4 registered open problems... compression must land first'"
  - "open_problems.md §1-4: precondition assessment after Wave 30/31/33 compression chain"
---

# Wave 34 — Metabolic Inlet Primitive Design

> **Scope**: exploration class design craft. Designs (does NOT implement)
> a minimum viable Metabolic Inlet verb scaffold that respects the 4
> open problems registered in `docs/open_problems.md §1-4` while still
> producing a usable verb that can be invoked manually today. The
> implementation lands in Wave 35 (separate kernel_contract wave).
>
> **Parents**:
> - `docs/primordia/vision_recovery_craft_2026-04-10.md` §3 (Metabolic Inlet
>   as v2.0 outward-digestive primitive)
> - `docs/primordia/vision_reaudit_craft_2026-04-12.md` §2.1 + Attack C
>   (Metabolic Inlet downstream of compression, ordering held)
> - `docs/open_problems.md §1-4` (the 4 unsolved sub-problems)
> - Wave 30 `compress_mvp_craft_2026-04-12.md` (compression now exists)
> - Wave 31 `uncompress_mvp_craft_2026-04-12.md` (reversibility)
> - Wave 33 `d_layer_prune_craft_2026-04-12.md` (continuous bloat control)
>
> **Supersedes**: none. Refines `docs/open_problems.md §4` (compression
> engineering) status from "fully blocked" to "partially unblocked".

## 0. Problem definition

`MYCO.md §身份锚点 #3` declares the substrate has a seven-step pipeline
ending in excretion, and `§任务队列 row 4` declares Metabolic Inlet as
a v2.0 primitive ("outward digestive system"). Wave 10 vision_recovery
made the claim explicit: **a substrate without a metabolic inlet is just
an inward cache, not a metabolism**.

Yet 23 waves later (W10 → W33), zero kernel surface implements the inlet.
Every existing verb (`eat`, `digest`, `view`, `hunger`, `compress`, `prune`)
operates on knowledge already inside the substrate. The `forage` verb
(introduced earlier) is the closest existing primitive to inlet, but it
serves a different need (gathering raw friction signals, not consuming
external knowledge artifacts).

Why hasn't the inlet been built? Because `docs/open_problems.md §1-4`
register **4 distinct sub-problems** that block a clean design:

1. **Cold start** (§1): a fresh instance has no friction history → no
   inlet trigger → never bootstraps. The "user審批 seed source" workaround
   defers but doesn't solve.
2. **Trigger signals** (§2): even with cold-start solved, "when to trigger
   inlet" has no validated signal definition. We know what NOT to use
   (calendar / threshold / agent self-report). Three hypotheses, none
   tested.
3. **Alignment** (§3): inlet outputs carry implicit assumptions that
   human selection layers cannot reliably extract. Mutation-selection
   model becomes劣汰良 if alignment fails. Requires cross-instance
   experience to evaluate — not solvable in one wave.
4. **Compression engineering** (§4): inlet without continuous compression
   = bloat spiral. Was fully blocked until Waves 30-33.

**The shift since Wave 26**: Wave 26 §2.1 Attack C concluded "compression
must land first before Metabolic Inlet is even designable without hitting
known traps". Waves 30/31/33 have now landed `myco compress`,
`myco uncompress`, and `myco prune` — sub-problem #4 is **partially
unblocked**: continuous compression doesn't exist yet (the 3 verbs are
manual), but the substrate now has the building blocks (atomic write,
audit trail, dead-knowledge actuator). Wave 26's blocking condition
is satisfied to the level required for design, not yet to the level
required for production-grade auto-trigger.

**This craft's premise**: 1 of the 4 sub-problems is partially solved.
2 of them (cold start, alignment) cannot be solved in any single wave.
1 of them (trigger signals) needs real friction data before it's even
testable. **Therefore the design must produce a verb that DEFERS all 4
to its operator** rather than claiming to solve any of them. The verb
becomes a scaffold, not a complete system. Operator-deferred design is
honest about what we don't know; pretending to solve cold-start by
hard-coding seed manifests would violate Bitter Lesson stance and
identity anchor #2.

**The right scope for Wave 34**:

- Design a verb shape that can be invoked **manually** with explicit
  operator-supplied input (URL or file path).
- Define the inlet output shape: how does external content land in the
  substrate? What is its initial status, source, tags?
- Define the connection to the existing compression chain: inlet produces
  raw notes, normal pipeline metabolizes them.
- Define the provenance schema: alignment is deferred to operator
  (human-in-the-loop), but the substrate must record enough provenance
  for operators to do informed selection.
- Document each of the 4 open problems as **explicit limitation** of
  the v1 verb, each with an exit condition that future waves can lift.

**The wrong scope for Wave 34**:

- Implementing the verb (Wave 35).
- Solving cold start by hard-coding seed sources (violates anchors #2/#7).
- Solving trigger signals by hard-coding cron / threshold / calendar
  (violates open_problems §2 already-rejected list).
- Solving alignment by claiming the LLM can extract implicit assumptions
  (violates §3 known failure mode).
- Adding any auto-trigger / daemon / scheduler (out of CLI hosting
  paradigm scope per H-2).

## 1. Round 1 — Per-question audit

Seven design questions, each addressing one load-bearing decision.

### 1.1 Verb name

**Candidates**: `myco inlet`, `myco intake`, `myco ingest`, `myco eat --remote`,
`myco forage --remote`, `myco import-knowledge`.

**Doctrine pull**: anchor #3 names it "**metabolic inlet**". Anchor #6 says
"naming shapes thought" (Wave 28 biomimetic doctrine). The verb should
align with the doctrinal label.

**Decision**: `myco inlet`. Reasoning:

- Most-direct doctrinal alignment with `MYCO.md §身份锚点 #3` and
  `§任务队列 row 4` (which both spell it "inlet").
- Distinct from `eat` (eat is human→substrate; inlet is external→substrate).
- Distinct from `forage` (forage gathers internal friction signals; inlet
  consumes external knowledge artifacts).
- Distinct from `import` (which has a Python-language meaning that would
  confuse `myco import` with package imports).
- One word, ≤6 chars, fits CLI verb taxonomy.

**Rejected**: `intake` (slightly less doctrinally precise), `ingest` (too
biological without "metabolic" prefix), `--remote` flags on existing verbs
(hides the doctrinal step behind a parameter — Wave 32 already established
that hiding pipeline steps behind parameters obscures rather than reveals).

### 1.2 Input shape

**Question**: what does the operator pass to `myco inlet`?

**Candidates**:

- A) URL: `myco inlet https://example.com/paper.pdf`
- B) File path: `myco inlet ./external/paper.pdf`
- C) Both: `myco inlet <url-or-path>`
- D) List: `myco inlet --batch sources.txt`
- E) Stdin: `cat paper.pdf | myco inlet -`
- F) Via wrapper agent: agent-fetched content piped to a body flag
  `myco inlet --content "..." --provenance "..."`

**Doctrine pull**: anchor #2 (non-parametric evolution) says we should
NOT bake in a specific source format. Anchor #6 (transparency) says
provenance must be captured.

**Decision**: A + B + F. Reasoning:

- A (URL) is the canonical case for v2.0 — external knowledge mostly
  lives at URLs.
- B (file path) is the canonical case for v1 — operators often have
  local files they want to ingest.
- F (wrapper agent path) is the canonical case for **today's environment**
  — Myco runs inside agentic tooling that can fetch content for itself.
  The agent fetches via WebFetch / Bash / WebSearch, then hands the
  content to `myco inlet` with explicit provenance.
- D (batch) deferred — premature if we don't yet know the trigger pattern.
- E (stdin) deferred — adds shell coupling without doctrinal benefit.
- C is automatic given A + B (auto-detect URL vs path).

**Rejected**: anything that requires a built-in URL fetcher. Myco kernel
has no HTTP client by design (zero non-stdlib runtime deps per `setup.cfg`).
Ingest of URL form will be implemented by **handing the URL to the agent**
which uses its own fetch capability and pipes the result back as content.
This is the F path; the kernel never owns the network.

**Concrete signature**:

```
myco inlet <source>            # source = URL or file path (auto-detect)
myco inlet --content STR --provenance STR [--tags T1,T2,...]
                               # explicit content + provenance form
                               # used by agent wrappers and tests
```

The first form is documented as a wrapper around the second — when given
a file path, it reads the file and constructs the second-form invocation
internally. When given a URL, it errors with "URL fetch not implemented
in kernel; use agent to fetch and re-invoke with --content".

### 1.3 Output shape

**Question**: what does `myco inlet` produce?

**Candidates**:

- A) One raw note per inlet call.
- B) Multiple raw notes (one per chunk if content is long).
- C) Output is a "candidate" status, distinct from `raw`.
- D) Output is an `extracted` note immediately (skip raw → digesting flow).
- E) Output is parked in a separate `inlet/` directory until promoted.

**Doctrine pull**: anchor #3 (七步管线) says raw → digesting → extracted →
integrated → excreted. New verbs should not add new statuses without
strong justification (Wave 28 immutable axiom).

**Decision**: A. Reasoning:

- One inlet → one raw note is the simplest mapping. The note enters the
  pipeline at step 1 (`raw`) and metabolizes through the existing seven
  steps. No new status, no parallel directory, no special handling.
- Chunking (B) is a downstream concern — `myco compress` already chunks
  via cohort selection. Inlet doesn't need its own chunker.
- Skipping straight to `extracted` (D) violates the digestive pipeline
  doctrine — extraction is a cognitive act the operator/agent performs,
  not a status the verb assigns.
- Separate `inlet/` directory (E) reinvents the `notes/n_*.md` storage
  layer for no doctrinal benefit. The whole point of having one storage
  format is that the substrate sees all knowledge through one window.

**Note schema additions**:

- `source: inlet` (new value in `valid_sources`)
- `inlet_origin: <URL or file path>` (new optional frontmatter field,
  required when `source=inlet`)
- `inlet_method: <"file" | "url-fetched-by-agent" | "explicit-content">`
  (new optional field, helps Round 4 alignment audit later)
- All other fields follow existing `raw`-status note shape.

These are **schema additions**, which means Wave 35 (the implementation
wave) will need a contract bump — `kernel_contract` decision class for W35.

### 1.4 Trigger

**Question**: when does `myco inlet` get invoked?

**Candidates**:

- A) Pure manual: operator decides, runs the verb.
- B) Friction-driven: hunger surfaces an `inlet_ripe` signal when some
  condition is met; operator/agent chooses to act.
- C) Auto-trigger: cron / on-N-friction / on-empty-substrate.
- D) Hybrid: manual default, hunger advisory signal as a future addition.

**Doctrine pull**: open_problems §2 explicitly rejects calendar / fixed
threshold / explicit user request / agent self-report as trigger
signals. This is the most-constrained design question because the
no-go list is long.

**Decision**: A for v1, D as the trajectory for v2. Reasoning:

- v1 (Wave 35 implementation): pure manual. The operator OR the agent
  decides when to invoke. No hunger signal yet. The verb is a passive
  primitive.
- v2 (post-Wave 35, when real friction data accumulates): consider
  adding an `inlet_ripe` advisory signal to hunger that points at one
  of the 3 hypotheses listed in open_problems §2. Each hypothesis would
  need its own data-driven craft.
- C is fully rejected (CLI hosting paradigm + open_problems §2 + anchor #2).

**Why "manual" doesn't violate doctrine**: open_problems §2 is about
**automated** trigger signals. Manual operator invocation is not a
"trigger signal" — it's just operator agency, which is the always-allowed
fallback for any verb. `myco compress` is also manual. `myco prune --apply`
is manual. The substrate's friction-driven bias is about **automation**
discipline, not about forbidding human operators.

### 1.5 Provenance & alignment scaffolding

**Question**: how does the substrate record enough provenance for
human selection layers to do informed alignment review later?

**Doctrine pull**: open_problems §3 says inlet outputs carry implicit
assumptions; mutation-selection model fails if selection cannot extract
those assumptions. The substrate cannot solve this in code — but it can
**preserve enough provenance** so that human reviewers have the raw
material.

**Decision**: 4 mandatory provenance fields on every `source=inlet` note:

1. `inlet_origin` — the source identifier (URL or absolute file path)
2. `inlet_method` — how content arrived (`file` / `url-fetched-by-agent` /
   `explicit-content`)
3. `inlet_fetched_at` — ISO timestamp of when content was captured
4. `inlet_content_hash` — sha256 of body bytes, allowing later "did this
   change since fetch?" checks

**What's deliberately NOT captured**:

- Author / publisher / license — these are content-extraction tasks the
  alignment review should perform during digest, not capture-time tasks.
  Capturing them at inlet time would imply the kernel can parse arbitrary
  document formats, which it can't.
- Implicit assumptions / "limitations" sections — open_problems §3 says
  these cannot be reliably extracted. We're not going to claim to.
- Confidence / quality score — Goodhart problem (Craft Protocol §7). The
  reviewer assigns these during digest, not the verb.

**Alignment deferral**: the verb does NOT do any alignment evaluation
itself. The note enters as `raw` and the operator/agent runs `myco evaluate`
(Wave 32) at digest time, at which point the human selection step engages.
This is the "selection layer is human, not verb" doctrine made operational.

### 1.6 Compression integration

**Question**: how does inlet interact with the W30/W31/W33 compression chain?

**Doctrine pull**: open_problems §4 says inlet without continuous
compression = bloat spiral. We can't make compression continuous in W34
(that's a separate problem), but we can make sure inlet outputs are
**naturally compressible** by the existing manual compress chain.

**Decision**: inlet outputs follow normal note shape, get a default tag
`inlet`, and the operator can run `myco compress --tag inlet --rationale "..."`
once enough inlet notes accumulate. No new compression code in W35; the
existing compress verb works because inlet outputs are just notes.

The doctrine claim "inlet outputs are naturally compressible" is testable:
Wave 35's implementation brief includes a test that creates 5 inlet notes
with a shared tag and runs `myco compress --tag <tag> --dry-run` to
confirm the existing compress verb resolves them as a cohort. If this
test fails, the inlet design has hidden incompatibility with compress.

**Bloat hard cap**: not in W35. Documented as L4 limitation. The
mitigation is the existing `compression_ripe` advisory signal in hunger
(Wave 27) which already fires when raw-note count by tag exceeds threshold.
Inlet notes will trip this signal naturally.

### 1.7 Cold-start workaround

**Question**: how does a fresh instance bootstrap inlet without violating
anchors #2 (non-parametric evolution) and #7 (no hard-coded skill libraries)?

**Doctrine pull**: open_problems §1 says cold start is unsolved in v1.x.
The workaround "user審批 seed source" defers the problem.

**Decision**: the v1 verb requires the operator to provide each source
explicitly. There is **no seed manifest**, **no default source list**,
**no built-in URL list**. A fresh instance has zero inlet activity until
the operator says `myco inlet <thing>`. This is honest about the cold-start
problem rather than hiding it under a hard-coded list.

**For test/example purposes only**: the W35 test suite will include a
fixture that creates a fake "seed file" in the test temp directory and
exercises `myco inlet ./tmp/fake_seed.md`. This fixture exists only to
test the verb mechanics; it does not ship as a production seed.

**Cold-start exit condition** (carries forward from open_problems §1):
when an instance accumulates enough friction history that hunger surfaces
a real `inlet_ripe` signal that the operator chooses to act on, the cold
start has succeeded. Until then, every inlet call is operator-driven.
This is the same exit condition open_problems §1 already documents.

### 1.8 Summary table

| # | Question | Decision | Defers to |
|---|----------|----------|-----------|
| 1 | Verb name | `myco inlet` | — |
| 2 | Input shape | `<file path or --content STR --provenance STR>` | URL fetch deferred to agent wrapper |
| 3 | Output shape | one `raw` note, `source=inlet` | normal pipeline metabolizes |
| 4 | Trigger | manual only | open_problems §2 (auto-trigger v2) |
| 5 | Provenance | 4 mandatory fields, no quality scoring | open_problems §3 (alignment review v2+) |
| 6 | Compression integration | uses existing compress chain via tags | open_problems §4 (continuous compression v2) |
| 7 | Cold start | operator-supplied sources only | open_problems §1 (autonomous bootstrap v2) |

**Total decisions**: 7. Total defers: 4 (matching the 4 open problems
exactly — the design honestly acknowledges that the verb scaffolds, not
solves, each one).

## 2. Round 2 — Attacks

Six attacks. Each must be either defended or surrendered to (refining
the design).

### Attack A: "Why a verb at all? `myco eat --content "$EXTERNAL_TEXT" --tags inlet,external` already does this."

**Defense**: Three reasons.

1. **Doctrinal visibility**. Anchor #3 names the metabolic inlet as a
   distinct primitive. Hiding it inside `eat`'s tag-flag space violates
   the Wave 32 doctrine "naming shapes thought; pipeline steps deserve
   verb names". `myco eat --tags inlet` is a workaround, not a primitive.

2. **Provenance schema**. The 4 mandatory `inlet_*` fields (§1.5)
   require schema enforcement at write time. `myco eat` does not
   know about these fields and would not enforce their presence. A
   distinct verb gives us a place to enforce the schema.

3. **Alignment audit trail**. open_problems §3's exit condition requires
   accumulating inlet provenance for cross-instance review. If inlet
   data is mixed into the general `eat` stream with a tag, querying
   "all inlet activity in this substrate" becomes a tag-search heuristic
   instead of a `source=inlet` schema query.

**Lands as**: defense holds. A distinct verb is doctrinally and operationally
justified.

### Attack B: "URL fetch is the canonical case but you defer it to agent wrappers — that's a half-finished feature."

**Defense**: This is the right level of half-finishedness for the kernel.

- Myco kernel has zero non-stdlib runtime deps by hard contract
  (`setup.cfg::install_requires` is empty). Adding `requests` or `httpx`
  to support URL fetch breaks that contract.
- Cleartext HTTP is also a security boundary. The kernel running with
  network access is a different threat model than the kernel running
  on local files only. Operators should make that decision per-instance.
- Agent wrappers (Claude, Cursor, etc.) ALREADY have HTTP fetch
  capabilities. The agent fetches the content, hands it to
  `myco inlet --content "$BODY" --provenance "$URL"`. This is one extra
  shell pipe and zero kernel surface area.

**Honest limitation**: file `n_20260412T064100_45e3.md` (W33 decisions
note) lives at a known file path; `myco inlet ./notes/...` would work
but fetching from `https://...` would not. This will land as L1 limitation
in W34's known limitations and L1 exit condition in W35's implementation
brief.

**Lands as**: defense holds; URL fetch is correctly out of kernel scope.

### Attack C: "Manual trigger means inlet will never fire. The verb will sit in `--help` unused like Wave 18's dead_knowledge signal sat for 15 waves before W33 built the actuator."

**Defense**: This is the strongest attack. It's partially right.

**The honest part**: yes, manual triggers are friction-prone. Wave 33
demonstrated that signals without actuators decay; the same risk applies
to actuators without triggers.

**The mitigating part**: this is **not symmetric** with Wave 18's dead_knowledge
case.

- Wave 18 had a signal that ALREADY fired in hunger output, but the action
  was tedious. Operators saw the signal and chose not to act because the
  cost was high. The friction was **on the action side**, not the
  detection side.
- Wave 34's inlet has no detection-side fire-and-forget signal yet.
  The operator must explicitly **want** to ingest external content. The
  friction is **on the wanting side** — and operator wanting external
  content is the natural state of any non-trivial knowledge work.

**Empirical evidence from this very session**: in marathon mode, Claude
agents routinely WebFetch external docs to answer user questions. Each of
those fetches is currently lost (the response goes to the chat, not the
substrate). Even today's Claude has implicit "wanting" of external content;
the bottleneck is not motivation but capture. Inlet captures the fetch.

**The remaining risk** (not fully defended): operators who never use
external content will never invoke inlet. For them, the verb is dead
weight in `--help`. This is acceptable because (a) `--help` already shows
20+ verbs and 1 more is marginal, (b) Wave 28's biomimetic doctrine
explicitly accepts vocabulary expansion for doctrine surface, (c) every
unused verb is also a contract surface that documents the substrate's
intended capabilities even when unused.

**Lands as**: defense holds with honest acknowledgment. File this as
limitation L2 (verb may go unused in inlet-disinclined instances).

### Attack D: "The 4 mandatory provenance fields are a schema lock-in. If the alignment problem is genuinely unsolved, you don't know what fields will be needed. You're guessing the shape."

**Defense**: The 4 fields are the **minimum-superset** of what every
known alignment workflow needs.

- `inlet_origin`: every alignment workflow needs to know where content
  came from. URL or path is universal.
- `inlet_method`: the difference between "operator handed us a file" and
  "agent fetched a URL" is auditable evidence of human-in-the-loop. This
  is open_problems §3's transparency hook.
- `inlet_fetched_at`: temporal ordering matters for "did this knowledge
  enter before or after the assumption that depends on it". Universally
  needed.
- `inlet_content_hash`: tamper / change detection. Universal.

What's NOT in the 4: domain-specific fields like authorship, license,
peer-review status, etc. These are document-format-specific and the verb
has no business knowing about PDF metadata vs HTML meta tags vs plain text.
Those land in body content and get extracted at digest time.

**The schema is a minimum scaffold**, not a complete provenance taxonomy.
Wave 35 implementation will land them as `optional_fields` in canon (not
required) so future waves can add more fields without contract breakage.
L10 lint will warn (not error) on missing fields when `source=inlet`.

**Lands as**: defense holds; schema is minimum-not-maximum.

### Attack E: "Why an exploration craft, not kernel_contract? You're proposing canon edits — schema additions to `valid_sources` and `optional_fields` are kernel_contract surface touches per L15 trigger surface list."

**Defense**: This craft is the **design**, not the implementation. Wave 34
produces the craft document only. Wave 35 implements (cli.py + notes.py +
canon edits + tests + contract bump) under a separate kernel_contract
decision class craft.

This is the same separation Wave 27 (compression design, exploration class
0.85) → Wave 30 (compression impl, kernel_contract 0.91) used. The split
ensures the design pressure and the implementation pressure don't mix —
design crafts can attack the shape without commitment cost; implementation
crafts can pressure the realization without re-deriving semantics.

**Trigger surface check**: this craft (W34) does NOT touch `_canon.yaml`,
`src/myco/lint.py`, `src/myco/mcp_server.py`, or any other L15 trigger
surface file. It is a `docs/primordia/*.md` write only. Therefore L15
craft reflex arc does not require a kernel_contract craft for the
documentation alone. W34 is correctly exploration class.

**The contract bump itself** lands in W35, not W34. W35 will be
`kernel_contract` 0.90+ class because it touches `_canon.yaml`.

**Lands as**: defense holds; class split is correct.

### Attack F: "You claim sub-problem #4 (compression engineering) is partially unblocked, but `compress` is manual, `prune` is manual, and `uncompress` is manual. None of them is **continuous**. Continuous compression remains unsolved. Therefore Metabolic Inlet remains blocked just like Wave 26 said."

**Defense**: This attack is technically right and substantively wrong.

**Technically right**: continuous compression is not implemented. The
W30/31/33 trio are operator-invoked verbs, not daemon processes.

**Substantively wrong**: open_problems §4's exit condition is "continuous
compression daemon OR equivalent event-driven compression hook". The
**equivalent event-driven hook** clause is satisfied by Wave 33's
`hunger → prune --apply` actionable loop AND Wave 27's
`compression_ripe` hunger advisory. Operators (and agents) can run
hunger as the event source, observe ripe signals, and act on them. The
daemon is replaced by **agent-as-daemon**: any agent that runs hunger
periodically becomes the continuous trigger.

This is not as clean as a real daemon, but it satisfies the "equivalent"
clause. open_problems §4 was written before Wave 12's craft reflex arc
existed; the reflex arc (which fires on session start, on lint, on
unhealthy hunger) IS the event-driven hook the §4 exit condition asked
for, just delivered through agent rather than OS.

**Wave 26's "must land first" condition**: Wave 26 §2.1 Attack C said
"compression must land first before Metabolic Inlet is even designable
without hitting known traps". Past tense "land first" is now satisfied:
W30 landed compress, W31 landed uncompress, W33 landed prune. We are
designing AFTER the landings, not before.

**Lands as**: defense holds. The "blocked" condition was satisfied
sufficiently for **design**, even though the "fully solved" condition
for production-grade auto-trigger is not yet met. File the gap as
limitation L4: compression is operator-invoked, not continuous.

## 3. Round 3 — Wave 35 implementation brief + supersession of Wave 26 priority claim

### 3.1 Wave 35 implementation brief (prescriptive landing list)

**Wave 35 will be `kernel_contract` decision class** (0.90 target,
3 rounds). It implements the verb defined here and lands the contract
bump.

**Wave 35 landing list** (prescriptive — Wave 35 will copy this verbatim):

1. `_canon.yaml` v0.26.0 → v0.27.0 (kernel + template mirrored):
   - `notes_schema.valid_sources` adds `inlet`
   - `notes_schema.optional_fields` adds `inlet_origin`, `inlet_method`,
     `inlet_fetched_at`, `inlet_content_hash`
   - new `notes_schema.inlet` sub-section: `{default_tag: "inlet"}`
2. `src/myco/notes.py` `VALID_SOURCES` adds `inlet`; `OPTIONAL_FIELDS`
   extended with the 4 inlet_* fields.
3. `src/myco/inlet_cmd.py` (NEW, ~200 LOC):
   - `_resolve_inlet_input(args) -> (content, provenance, method)` —
     handles file path, --content/--provenance pair, and URL-error case
   - `_build_inlet_meta(content, provenance, method, tags)` — computes
     hash, timestamp, builds frontmatter
   - `run_inlet(args)` — CLI dispatch with exit codes 0/2/3/5
4. `src/myco/cli.py` `inlet_parser` subparser:
   ```
   myco inlet [<source>] [--content STR] [--provenance STR]
              [--tags T1,T2] [--project-dir DIR] [--json]
   ```
   Positional `source` and `--content/--provenance` are mutually exclusive
   (XOR check at dispatch).
5. `src/myco/lint.py` extend L10 (notes schema) to softly enforce: when
   `source==inlet`, the 4 inlet_* fields SHOULD be present (warn, not
   error, to preserve grandfather compatibility).
6. `tests/unit/test_inlet.py` (NEW, 4-5 tests):
   - `test_inlet_file_creates_raw_note` — file path → raw note with
     all 4 inlet_* fields populated
   - `test_inlet_explicit_content_creates_raw_note` — --content/--provenance
     form with hash/timestamp computed
   - `test_inlet_url_errors_with_clear_message` — URL form errors with
     instruction to use agent wrapper
   - `test_inlet_compresses_via_existing_chain` — create N inlet notes
     with shared tag, run `_resolve_cohort_by_tag` directly, assert
     all N are eligible (compression integration check from §1.6)
   - `test_inlet_lints_clean` — newly-created inlet note passes L10
7. `docs/contract_changelog.md` v0.27.0 entry.
8. Wave 35 craft `docs/primordia/inlet_mvp_craft_2026-04-12.md`
   (kernel_contract, 0.90 target).
9. Wave 35 evidence note + decisions note + log.md milestone.
10. open_problems §4 status edit: append "**2026-04-12 update**: partial
    unblocking via Wave 30/31/33 chain + Wave 35 inlet primitive landed.
    Continuous compression still unsolved (operator-invoked only).
    Sub-problem remains open until daemon-equivalent event source verified."

### 3.2 Open problems status update (post-W34 only — actual edits land in W35)

Wave 34 declares the following status updates that Wave 35 will write
into `docs/open_problems.md`:

- **§1 (cold start)**: status unchanged. The W35 verb defers to
  operator-supplied sources. Exit condition unchanged.
- **§2 (trigger signals)**: status unchanged. The W35 verb is manual-only.
  The 3 candidate hypotheses (dead-knowledge ratio / wiki-miss-rate
  derivative / repeat-craft-frequency) remain untested and unimplemented.
  Exit condition unchanged.
- **§3 (alignment)**: status updated to "scaffolded". The 4 mandatory
  inlet_* provenance fields land the audit substrate that future
  alignment review tools will consume. Sub-problem itself is unchanged
  (extraction of implicit assumptions still unsolved); only the
  preconditions for future work are now in place.
- **§4 (compression engineering)**: status updated to "partially unblocked".
  The W30/31/33 chain provides operator-invokable building blocks. The
  W35 inlet outputs are designed to be naturally compressible via the
  existing compress chain. Continuous compression remains unsolved;
  operator-as-daemon is the v1.x workaround.

### 3.3 Wave 36+ trajectory (declared but not pre-scoped)

After Wave 35 lands, the Metabolic Inlet long-tail extends to:

- **Wave 36+ candidate A**: hunger `inlet_ripe` advisory signal (one of
  the 3 §2 hypotheses, picked by which one accumulates real friction
  data first).
- **Wave 36+ candidate B**: cross-ref graph (open_problems §6 D-layer
  long-tail item) — required for "is this inlet content already
  referenced by an integrated note?" alignment checks.
- **Wave 36+ candidate C**: continuous compression hook — when
  raw-note count exceeds `inlet_compression_threshold`, hunger fires
  HIGH advisory, agent invokes compress autonomously. Closes §4 fully.

**No pre-scoping**. The next wave's selection follows the same
friction-driven-after-doctrine-derivation policy that Wave 26 §3 D3 set.

## 4. Conclusions

### 4.1 Decisions (D1-D8)

**D1**: Verb name is `myco inlet` (single word, doctrinally aligned with
anchor #3 + Wave 26 §任务队列 row 4). Reasoning §1.1.

**D2**: Input shape supports file path (positional) and explicit
content/provenance pair (--content + --provenance flags). URL fetch is
NOT in kernel; agent wrappers handle it and re-invoke with explicit
content. Rationale: zero-non-stdlib-deps contract + security boundary.
Reasoning §1.2.

**D3**: Output is one `raw` status note per inlet call with
`source=inlet`. No new status. No parallel directory. Normal pipeline
metabolizes downstream. Reasoning §1.3.

**D4**: Trigger is manual only for v1. No hunger advisory signal in
W35. v2+ may add an `inlet_ripe` signal once real friction data
accumulates. Reasoning §1.4.

**D5**: Provenance schema = 4 mandatory fields when `source=inlet`:
`inlet_origin` (URL or path), `inlet_method` (`file`/`url-fetched-by-agent`/
`explicit-content`), `inlet_fetched_at` (ISO timestamp), `inlet_content_hash`
(sha256 of body). Soft-enforced via L10 lint warning, not strict L10 error
(grandfather compatibility). Reasoning §1.5.

**D6**: Compression integration uses the existing W30 `myco compress`
chain via shared tags. Inlet notes are not specially handled. Wave 35
test `test_inlet_compresses_via_existing_chain` proves naturally
compressible. Reasoning §1.6.

**D7**: Cold start is operator-deferred. No seed manifest, no default
source list, no built-in URL list. A fresh instance has zero inlet
activity until operator says `myco inlet <thing>`. Reasoning §1.7.

**D8**: Wave 34 is exploration class (design only); Wave 35 is
kernel_contract class (implementation + contract bump v0.26.0 → v0.27.0).
Trigger surface analysis: W34 touches only `docs/primordia/*.md` (no
L15 trigger surface), so reflex arc does not fire. W35 will touch canon
+ notes.py + cli.py + lint.py, requiring kernel_contract class.
Reasoning §2 Attack E.

### 4.2 Landing list (Wave 34 only — artifacts produced by THIS craft)

1. ✅ `docs/primordia/metabolic_inlet_design_craft_2026-04-12.md` (this file)
2. ⏳ Evidence note via `myco eat` capturing audit's read list + open
   problems §1-4 cross-references + the partial-unblocking argument
3. ⏳ Decisions note via `myco eat` + `myco integrate` capturing D1-D8
4. ⏳ `log.md` Wave 34 milestone entry
5. ⏳ Boot brief regenerated via `myco hunger` (auto)
6. ⏳ Commit as `[refactor] Wave 34 — Metabolic Inlet design craft (no contract bump)`

**No code changes in Wave 34.** No `_canon.yaml` edit. No `MYCO.md` edit.
No new test. No contract bump. Pure design specification only.

### 4.3 Known limitations

**L1 — URL fetch is not in kernel**: file paths and explicit-content form
are supported; URLs error out with clear instruction to use agent wrapper.
Operators in non-agentic environments lose URL ingestion convenience.
Mitigation: documentation emphasizes the wrapper pattern; agent wrappers
already have fetch capability.

**L2 — Manual-only trigger may yield unused verb**: in instances where
operators never want external content, `myco inlet` is dead weight in
`--help`. Acceptable per Wave 28 biomimetic doctrine (vocabulary expansion
for doctrine surface is worth the cost). Mitigation: the verb is at
minimum a doctrinal placeholder declaring substrate intent.

**L3 — 4 provenance fields are minimum-superset, not complete**: domain-
specific provenance (author, license, peer-review status) is NOT captured
at inlet time. Operators must extract during `myco evaluate` / `digest`.
Mitigation: schema lands as `optional_fields` so additions are
non-breaking.

**L4 — Compression is operator-invoked, not continuous**: W30/31/33 chain
exists but no daemon. open_problems §4 remains "partially unblocked",
not "solved". Continuous compression awaits Wave 36+ craft. Mitigation:
operator-as-daemon via routine hunger calls + craft reflex arc.

**L5 — Cold start is operator-deferred**: a fresh instance with zero
operator action will never run inlet. open_problems §1 unchanged. This
is honest about the bootstrap limit; the alternative (hard-coded seed
manifest) violates anchors #2/#7.

**L6 — Alignment review is human, not verb**: the 4 provenance fields
scaffold the audit but do not perform the audit. open_problems §3 remains
fully open. This is correct per "selection layer is human" doctrine —
the verb cannot solve a problem that explicitly requires cross-instance
human-review experience.

**L7 — No MCP tool mirror**: `myco inlet` is CLI-only in W35. No MCP
tool wrapper. Consistent with Wave 32 D4 (agent tool budget consideration)
and Wave 33 L6 (same reason). Mitigation: the tool surface remains
conservative and adds MCP wrappers only when friction demands.

### 4.4 Supersession pointer

This craft does NOT supersede any prior craft. It refines the status of
`docs/open_problems.md §4` from "fully blocked" to "partially unblocked"
based on Waves 30/31/33 landing the compression chain. The actual edit
to open_problems.md lands in Wave 35 (alongside the impl).

It also makes operational a doctrine claim that has been declared since
Wave 10 vision_recovery: "a substrate without metabolic inlet is just an
inward cache". The claim has been honored doctrinally for 24 waves; W34
designs the verb that begins to honor it operationally.

### 4.5 Confidence

`current_confidence: 0.85 = target_confidence: 0.85`. Single-source
convention ceiling for agent-only craft with no external research beyond
re-reading prior crafts and `open_problems.md`. Honest edge: the design
space has 4 unsolved sub-problems and the craft openly defers each. A
higher confidence would require either (a) actual operator usage data
that doesn't yet exist, or (b) cross-instance alignment review experience
that requires multi-instance deployment. Both are out of one wave's scope.

The 0.85 floor reflects "the verb shape is defensible, the deferrals are
honest, and Wave 35 implementation can proceed without re-deriving
semantics under pressure". It does NOT claim the underlying open
problems are any closer to solved.
