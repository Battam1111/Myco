---
type: craft
status: SUPERSEDED
superseded_by: compress_mvp_craft_2026-04-12.md
created: 2026-04-12
target_confidence: 0.85
current_confidence: 0.85
rounds: 3
craft_protocol_version: 1
decision_class: exploration
---

# Forward Compression — Substrate Primitive Design

> **Scope**: design-only exploration craft. No code changes. No lint rule changes.
> No `_canon.yaml` edits (pending Wave 28 implementation). Answers the 7 design
> questions locked in Wave 26 craft §3.3 for the forward-compression primitive.
>
> **Parent**: `docs/primordia/vision_reaudit_craft_2026-04-12.md` §3.3 locked this
> scope; §2.3 placed compression at top priority (highest doctrine weight + lowest
> impl coverage 0.35).
>
> **Feeds**: Wave 28 kernel_contract implementation (not yet scoped). This craft's
> §4 Decisions are the input specification for Wave 28.
>
> **Supersedes**: none.

## 0. Problem definition

Anchor #4 in `MYCO.md §身份锚点` is the substrate's most doctrine-weighted claim:

> *"压缩即认知：存储无限，注意力有限。『不遗忘，只压缩』是 doctrine 不是工程细节
> —— 压缩决策是基质的首要认知行为. 三条判据：频率 · 时效 · 排他性. 压缩是
> Agent-adaptive 的（32K vs 200K 策略不同），压缩策略本身也进化."*

As of Wave 26 (just landed), forward compression is **not implemented**. The only
substrate-level compression that exists is **reverse compression** (the `excreted`
status + mandatory `excrete_reason`) and **structural compression workflow**
(Wave 22 W13 principle for `docs/primordia/` archive movement). Neither of these
is "take N raw notes and produce 1 extracted synthesis with audit trail".

The gap was measured at Wave 26 Round 1 as:

- Anchor #4 `implementation_coverage = 0.35` (lowest of all 8 anchors)
- `MYCO.md §指标面板 compression_discipline_maturity = 0.40`
- `src/myco/` has no `myco compress` verb. The only `compress` in the tree is
  `scripts/compress_original.py` (a batch tool, not substrate-level) and
  `forage/repos/hermes-agent/trajectory_compressor.py` (ingested reference,
  not Myco's own).
- 4 out of 8 entries in `docs/open_problems.md` (§1–§4) are Metabolic Inlet
  sub-problems, and §4 is explicitly "compression engineering (bloat失控)" —
  Metabolic Inlet is downstream of compression.

The problem Wave 27 must solve (in design, not code): **answer the 7 questions
that make forward compression a well-defined substrate primitive** such that
Wave 28 can implement it without having to re-derive the semantics under
implementation pressure.

The 7 questions (from Wave 26 §3.3):

1. What is the **unit** of forward compression?
2. What is the **trigger**?
3. What is the **output** shape?
4. What is the **audit trail**?
5. What is the **reversibility** contract?
6. How does compression interact with anchor #3 **steps 2–5**?
7. What are the **non-functional requirements**?

## 1. Round 1 — Working proposals for each design question

### 1.1 Q1 — Unit of compression

**Options**:
- **(a) Tag-scoped**: all raw notes matching a given frontmatter tag (e.g.
  `myco compress --tag wave25-seed` → operates on all raw notes tagged
  `wave25-seed`)
- **(b) Time-window cohort**: all raw notes created in a given time range
  (e.g. `myco compress --since 2026-04-10 --until 2026-04-12`)
- **(c) Semantic cluster**: all notes whose content is close in embedding
  space (requires an embedding model → non-trivial dependency)
- **(d) Manual bundle**: explicit list of note IDs passed on the command line
  (e.g. `myco compress n_20260412T... n_20260412T... n_20260412T...`)
- **(e) Status-scoped**: all notes in a specific status+tag combo (e.g. all
  `digesting` notes with tag `friction-phase2`)

**Working proposal**: Primary = **(a) tag-scoped** + **(d) manual bundle**.
Rejected: (c) semantic cluster (violates anchor #2 non-parametric evolution —
embedding model is parametric and agent-adaptive cost is high); (b) time-window
(too coarse — a time window will usually mix unrelated topics); (e) status-scoped
(a special case of tag-scoped with an extra filter — foldable into (a) via
`--status` flag).

**Rationale**: Tag-scoped is the ergonomic default because Myco's notes already
carry semantic tags (users/agents tag them at `myco eat` time). The tag IS the
pre-declared semantic cluster, and it's non-parametric (the user/agent decided
it, not an embedding model). Manual bundle is the escape hatch when tag-scope
is wrong — the user explicitly lists ids.

**Ergonomics**:
```
myco compress --tag wave25-seed                   # all raw notes tagged wave25-seed
myco compress --tag wave25-seed --status raw      # same + explicit status filter
myco compress n_20260412T... n_20260412T...       # manual bundle
myco compress --tag wave25-seed --dry-run         # show what would be compressed
```

### 1.2 Q2 — Trigger

**Options**:
- **(1) Manual only**: every compression is explicitly invoked (`myco compress ...`)
- **(2) Scheduled**: cron-like (`myco compress --auto` on a timer)
- **(3) Friction-driven**: hunger detects a "ripe" group (e.g. >N notes sharing
  a tag AND >K days old), emits signal `compression_ripe`, which an agent
  session can act on

**Working proposal**: (1) + (3). Reject (2) scheduled because it violates
Myco's identity anchor #6 (mutation-selection; selection requires human-in-the-
loop, and a cron job runs without human selection). (3) is the right kind of
automation — the **signal** is friction-driven, but the **action** is still
agent-initiated; human selection is preserved because the agent decides whether
to act on the signal in session (same shape as Wave 13 boot reflex arc).

**Specifically**:
- `myco hunger` adds a new signal class: `compression_ripe`, fired when a tag
  cohort has ≥`compression_ripe_threshold` raw notes (default 5) AND the
  oldest note in the cohort is ≥`compression_ripe_age_days` (default 7).
  Thresholds live in `_canon.yaml::system.notes_schema.compression` (new
  schema section added in Wave 28, not this craft).
- The signal appears in the boot brief + hunger output, same surface as
  existing reflex signals.
- Agent can choose to act (`myco compress --tag X`) or ignore the signal.
- `myco compress --auto` is **deliberately not added**. If the agent wants
  automation, they can run the command in a loop from their own session;
  the substrate does not host daemons (consistent with `docs/open_problems.md
  §7 Agent-Initiated Sensing / H-2`).

### 1.3 Q3 — Output shape

**Options**:
- **(A) Additive**: new extracted note with links back to N originals; all
  originals stay in whatever status they were in
- **(B) Consumptive with audit**: new extracted note; originals are marked
  `excreted` with `excrete_reason: compressed into <new_id>`, preserving
  the audit chain but removing them from the active substrate
- **(C) Wiki page synthesis**: compression produces a wiki/\*.md page, not
  a note
- **(D) In-place promotion**: pick one existing note as "representative",
  mark the others excreted, no new note created

**Working proposal**: **(B) Consumptive with audit**. Reject:
- **(A) Additive**: defeats the purpose. Compression without excretion is
  just duplication — substrate bloats instead of shrinks. Violates anchor
  #4 ("storage infinite, attention finite" — attention IS the scarce
  resource, and additive compression doesn't reduce attention load).
- **(C) Wiki page synthesis**: Myco's wiki is structured knowledge, not
  digestion output. Wiki pages should come from `myco extract`-style
  explicit knowledge elevation, not automated compression. Conflating
  compress → wiki would collapse two doctrine layers.
- **(D) In-place promotion**: loses the synthesis opportunity. Compression
  is not picking a winner; it's producing a new artifact that's more
  compressed than any single input. Also loses audit: the "representative"
  note's content is unchanged, so there's no record of what the other
  notes added.

**Specifically**:
- Output note has `status: extracted` (not `integrated`, per Wave 25 D2's
  discipline about not auto-promoting synthesis into canon — integration
  is a separate downstream decision)
- Output note has `source: eat` (to be decided — see Limitations L3) OR
  a new `source: compress` value added to `_canon.yaml::notes_schema.valid_sources`
- Input notes get `status: excreted` with `excrete_reason: "compressed into
  <output_id>"` and a new optional frontmatter field
  `compressed_into: <output_id>` (to be added in Wave 28)

### 1.4 Q4 — Audit trail

Required frontmatter fields on the **output** note:

```yaml
compressed_from:                # list of input note IDs (required)
  - n_20260412T000000_a1b2
  - n_20260412T000001_c3d4
  - n_20260412T000002_e5f6
compression_method:             # how this compression was initiated
  manual                        # "manual" | "hunger-signal" | "auto" (unused v1)
compression_rationale: |        # short prose explaining what was preserved/dropped
  3 notes about hermes-agent patterns converged on command registry
  + atomic writes + error taxonomy. Kept the 3 pattern names, dropped
  the per-hermes-file traces (recoverable from vision_reaudit_craft §4.4).
compression_confidence: 0.85    # self-reported 0.0-1.0 on "did I preserve the signal"
```

Required frontmatter fields on the **excreted input** notes:

```yaml
compressed_into: n_20260412T...  # the output note's id (required)
excrete_reason: |
  compressed into n_20260412T... as part of 3-note wave25-seed cohort
```

L10 enforcement (to be added in Wave 28):
- If a note has `compressed_from`, every id in the list must exist in `notes/`
- If a note has `compressed_into`, the target id must exist AND its
  `compressed_from` must include this note's id
- Bidirectional link integrity = compression audit trail is tamper-evident

**Hallucination prevention**: the main risk is that compression produces a
plausible-looking synthesis that omits or fabricates content. Mitigations:
1. `compressed_from` list is verifiable — the originals are still on disk
   (excreted, not deleted). A human audit can diff the output against the
   inputs.
2. `compression_rationale` is required prose — agent must explain what was
   dropped. Agents resist writing rationale for fabrication because the
   fabrication is harder to justify than a faithful compression.
3. L10 lint verifies the bidirectional link integrity so a compress can't
   orphan its inputs.
4. `compression_confidence` is self-reported and subject to the same
   Goodhart risk as craft protocol confidence (single-source convention
   applies — §4 Limitations L2).

### 1.5 Q5 — Reversibility

**Working proposal**: **reversible by design**, via the following invariant:

> Input notes are never **deleted** from disk. They are marked `status:
> excreted` with `compressed_into` pointing at the output, and their file
> content is preserved verbatim.

This means a future `myco uncompress <output_id>` verb (Wave 29+, not Wave 28)
can:
1. Read the output note's `compressed_from` list
2. Flip each input note from `excreted` back to `integrated` (or whatever
   their pre-compression status was, if that's recoverable)
3. Mark the output note itself as `excreted` with
   `excrete_reason: "uncompressed by user/agent, inputs restored"`

**Not landing in Wave 28**: the `uncompress` verb itself. Wave 28 only needs
to preserve the property ("no information loss from disk") via the file-
preservation invariant. The `uncompress` verb is low-cost to add later
because the state is recoverable. This is a **design decision** not a
feature promise — Wave 28 builds the property, Wave 29+ may or may not add
the verb depending on whether friction justifies it.

**Pre-compression status lost**: one gap in this plan. If an input note was
`integrated` before compression, the compressed version has no record of its
old status (just `excreted` + `compressed_into`). Options:
- Add optional frontmatter `pre_compression_status: integrated` on excreted
  inputs (simplest)
- Leave it missing and assume `integrated` at uncompress time (lossy)
- Preserve full pre-compression frontmatter in a sidecar file (overkill)

**Lean**: first option (optional frontmatter field). Simple, additive, and
lossless. Add to Wave 28 implementation brief.

### 1.6 Q6 — Interaction with anchor #3 steps 2–5

Wave 26 Round 1 §1.3 established that steps 2 (evaluate), 3 (extract),
4 (integrate), 5 (compress) of the seven-step pipeline are **vestigial** —
they are status labels without dedicated verbs.

**Question**: does forward compression fold steps 2-5 into one verb, or does
it call them as sub-operations?

**Working proposal**: **fold steps 2-5 into `myco compress`** at Wave 28.
Rationale:

- **Step 2 (evaluate)** is implicit in compression: the agent MUST decide
  which raw notes are worth compressing and which should be excreted
  directly. This evaluation step happens before `myco compress` is even
  called. Making it a separate verb would add ceremony without adding
  structure. (Wave 28 can add a `myco evaluate --tag X` **shortcut** verb
  that just shows the candidate cohort without acting, but it's not a new
  pipeline step.)
- **Step 3 (extract)** IS the output of compression — the compressed note
  has `status: extracted` automatically. Compression subsumes extract.
- **Step 4 (integrate)** remains a separate decision: after compression
  lands an extracted note, a human or agent decides whether to further
  promote it to `integrated`. This stays as `myco digest --to integrated`
  (existing verb, no change).
- **Step 5 (compress)** IS the verb itself.

**After Wave 28 lands**, the seven-step pipeline has:
- Step 1 (发现): `myco eat`, `myco forage add`
- Step 2 (评估): implicit in `myco compress` pre-check, optional `myco
  evaluate --tag X` shortcut (dry-run view)
- Step 3 (萃取): `myco compress` output (extracted status)
- Step 4 (整合): `myco digest --to integrated`
- Step 5 (压缩): `myco compress`
- Step 6 (验证): `myco lint`
- Step 7 (淘汰): `myco digest --excrete` (standalone) OR implicit in
  `myco compress` (inputs get excreted as side-effect)

**Coverage delta** (post-Wave 28): step 2 partial (evaluate shortcut),
step 3 via compress-output, steps 5 + 7 via compress (new double-role),
others unchanged. Anchor #3 `implementation_coverage` estimated 0.43 → 0.75.

### 1.7 Q7 — Non-functional requirements

**Idempotence**: running `myco compress --tag X` twice should NOT produce two
output notes if nothing has changed. Mechanism:
1. On second invocation, compute the set of raw notes currently matching
   `--tag X`. If this set is empty (because first invocation excreted them
   all), the verb is a no-op and exits 0 with a message.
2. If new raw notes have appeared with the tag since first invocation, the
   second invocation compresses **only the new ones** into a separate output
   note.

**Atomicity**: the multi-note mutation (mark N originals excreted + create 1
extracted) must be all-or-nothing. If the process crashes mid-write, the
substrate must not be left with "N/2 originals excreted and no extracted
note" or "extracted note exists but originals not updated".

**This is where hermes catalog C2 atomic writes becomes Wave 28's declared
dependency**. Wave 28 will need to implement or adopt:
- Temp-file + rename for each individual note write (per-file atomicity)
- Two-phase commit for the group: write the output note first (to temp),
  write all input updates (to temp), then rename all temp → final in a
  specific order that preserves invariant ("output exists → all inputs
  excreted").
- If any rename fails, back out the already-done renames. This is best-effort
  — true transactional atomicity on a filesystem requires fsync
  discipline which Myco doesn't do elsewhere.

**Concurrent safety**: a concurrent `myco eat` that adds a new raw note with
the same tag during a compress operation should not be lost. Mechanism:
- `myco compress` computes the input set BEFORE any writes. A concurrent
  `eat` that lands after this snapshot is simply not part of this compression.
- No file locking required in Wave 28 minimum viable (file-level writes
  atomic via rename; tag filtering is a read).
- The next `myco compress --tag X` run will catch the newly-added note.

**Cost bound**: O(N) file reads (one per input note) + O(1) file writes per
input note (status flip + frontmatter update) + 1 file write (output note).
For typical compression (N=5), that's ~11 file operations, well under any
reasonable budget.

**Agent-adaptive compression policy** (anchor #4 "32K vs 200K")": Wave 28
does **NOT** implement adaptive policy. The MVP uses a fixed compression
behavior regardless of Agent context window. Adaptive policy is Wave 29+
territory (or open problem — see §4 Limitations L4).

## 2. Round 2 — Attacks on the design

### 2.1 Attack F — Compression hallucination

**Claim**: the design relies on the agent being honest about what it
preserved vs dropped. `compression_rationale` is prose that an agent can
fabricate. `compression_confidence` is self-reported. The audit trail
requires a human to actually diff the output against the inputs, and that
human is a single person (the user) who cannot audit every compression at
the scale the substrate encourages.

If an agent compresses 5 notes into 1 and the 1 output hallucinates a claim
that was NOT in any of the 5 inputs, **no lint will catch it**. L10 can
check link integrity but not semantic correctness. The human audit is the
only selection pressure, and it's single-point-of-failure.

This is a direct threat to anchor #6 mutation-selection collaboration: if
compressions can fabricate without detection, "system mutates, human selects"
degenerates to "system mutates, human rubber-stamps" → cancer.

**Defense**:

1. **Reversibility is the partial answer**: because inputs are preserved on
   disk (excreted, not deleted), any future audit CAN compare output against
   inputs at leisure. The information is never lost. A hallucination that
   lands in an extracted note can be detected weeks later via audit.

2. **Bidirectional lint on `compressed_from` / `compressed_into` catches
   orphan links**: can't compress into a note that doesn't exist, can't
   claim an input that doesn't point back. This is structural, lint-enforceable,
   hallucination-resistant.

3. **The most vulnerable case is small cohorts** (N=2 or 3) where hallucination
   is cheap to cover with plausible prose. The `compression_ripe` hunger
   signal threshold is default 5, which sets the friction floor above the
   easy-hallucination zone. A user who manually compresses N=2 takes on the
   audit burden themselves — they are the single human selection pressure
   for that operation.

4. **Compression-on-compression** is rejected at schema time: any note with
   `compressed_from` field cannot itself be input to another compression.
   This prevents "cascading hallucination" where each round drifts further
   from the original evidence. (Lint rule to be added in Wave 28.)

5. **The audit burden is real**: this design does NOT claim to eliminate
   hallucination risk. It claims to **bound** it (reversible, auditable,
   non-cascading) and to **resist scale** (can't compress compressed, can't
   hide in broken links). The remaining risk — "human can't audit everything"
   — is a long-term open problem (§4 Limitations L1).

Attack F lands: hallucination is not eliminated, only bounded. Confidence
target at 0.85 instead of 0.90 reflects this — this is a design that accepts
a known residual risk in exchange for unlocking anchor #4 at all.

### 2.2 Attack G — Fold-into-compress is too aggressive

**Claim**: §1.6 proposes that `myco compress` folds steps 2 (evaluate) +
3 (extract) + 5 (compress) + 7 (excrete) into one verb. That's 4 of 7
pipeline steps in one operation. This is the opposite of the seven-step
pipeline's own spirit — the point of seven distinct steps is that each
step is **observable separately**. A single verb that does 4 steps at once
erases the observability.

Specifically:
- You can't run `myco evaluate` to see what the agent thinks is worth
  compressing without triggering compression
- You can't ask "what was extracted from this group" separately from "what
  was compressed out"
- The audit trail conflates extraction (what was kept) and excretion (what
  was dropped) into a single rationale field

**Defense**:

1. **Observability is preserved through the `--dry-run` flag**: `myco compress
   --tag X --dry-run` shows the cohort, shows a proposed rationale, shows
   what would be excreted — without writing anything. This exposes the
   evaluate step without requiring it to be a separate verb.

2. **The seven-step pipeline is a doctrine-level description, not a verb
   count**. Wave 26 §1.3 noted that the current pipeline has 3/7 steps as
   verbs and the rest as state labels. Post-Wave-28 it will have 5/7 steps
   effectively addressable (1=eat, 2=compress --dry-run, 5=compress,
   6=lint, 7=compress side-effect OR digest --excrete). That's better
   than today, not worse.

3. **Ergonomic argument**: if extract + compress were separate verbs, the
   typical workflow becomes:
   ```
   myco evaluate --tag X      → shows cohort
   myco extract --tag X       → produces extracted notes
   myco compress --tag X      → now what? the extracted notes are already produced
   ```
   This is ceremony without substance. The real operation is "take this
   cohort of raw notes and produce a compressed synthesis + excrete the
   originals". That's one operation. Splitting it across 3 verbs imposes
   ceremony on every real compression.

4. **Wave 29+ can still add** `myco extract` as a standalone if friction
   demands it. The `compress` verb doesn't block `extract` from existing —
   it just subsumes the common case. Users who want `extract` without
   `compress` can have it later.

Attack G lands partially: observability must be preserved via `--dry-run`.
The fold-into-compress decision stays, but `--dry-run` becomes mandatory in
Wave 28's implementation brief.

### 2.3 Attack H — Reversibility is theater

**Claim**: §1.5 argues compression is "reversible by design" because inputs
are preserved on disk with `excreted` status. But reversibility requires
more than "files still exist on disk":
- The `uncompress` verb does not exist and is declared "Wave 29+"
- Pre-compression status is optional-frontmatter — a lossy best-effort,
  not a guarantee
- Bulk compressions don't preserve ordering among inputs
- If the output note is itself modified later (edited, re-compressed into
  another compression), the reversibility chain breaks

So the claim "reversible by design" is really "reversible-if-someone-builds-
the-verb-and-nothing-else-has-happened". That's not reversible, that's
"preserved for possible future recovery if the stars align".

**Defense**:

1. **The distinction is precise**: the design makes reversibility a
   **property of the data**, not a **property of the operation**. The data
   is preserved; a future verb can use that preservation to reverse.
   Wave 28 does not provide the verb, but it **commits** to preserving
   the invariant that makes the verb possible. This is the substrate doctrine
   in action: data is durable, verbs are evolvable.

2. **Failure modes are enumerable**:
   - Output compressed-into-another-compression: rejected at schema time
     (§2.1 defense #4). Cascade blocked → reversibility chain stays 1-deep.
   - Output edited after the fact: Myco has no "edit" verb on extracted
     notes; manual frontmatter edits via direct file write would violate L11
     write surface. If a user manually edits, they accept the reversibility
     loss (same as every other consequence of bypassing the tool protocol).
   - Input ordering: lost in current design. Adding `compressed_from` as
     an ordered list (which the design already specifies) preserves the
     ordering. Fixed.

3. **The attack's strongest point**: `uncompress` not being built means
   reversibility is aspirational until Wave 29+. Acknowledged. But the
   cost of NOT making the data reversible (destructive compression) is
   permanent information loss, and that's a worse failure mode than
   "reversibility verb is future work". Design says: pay the disk cost now,
   keep the option open.

4. **Pre-compression status**: accepted as optional-frontmatter addition in
   Wave 28 implementation brief. Not a guarantee but a best-effort recorder.
   A future audit can recover pre-status if it's there; if not, default to
   `integrated` which is the most common case.

Attack H lands as "reversibility is a commitment to future work, not a
present capability". Language in §1.5 should be updated to say "preserved
for reversibility" rather than "reversible by design". Revision accepted.

### 2.4 Attack I — Wave 28 scope creep via "declared dependencies"

**Claim**: §1.7 casually declares "this is where hermes catalog C2 atomic
writes becomes Wave 28's declared dependency". That is the entire Wave 28
scope being attached to Wave 27's tail as if it's obvious. But C2 atomic
writes is its own Round 2 capacity problem (Wave 25 Round 2 established
1-2 subsystems per wave max). Wave 28 trying to bundle "compress MVP +
atomic writes refactor" at the same time is the exact 4-subsystem scope
creep that Wave 25 D3 rejected.

So either:
- Wave 28 is "atomic writes only" (C2 alone), Wave 29 is "compress MVP"
  using W28's atomic writes — 2 waves total
- Wave 28 is "compress MVP with minimum atomic-write support for THIS specific
  operation" (not a general atomic-write module), and a Wave 29+ can later
  generalize

Which is it?

**Defense**:

This attack identifies a real scope question for Wave 28 (not Wave 27).
Wave 27 as exploration craft can legitimately leave it open. But I should
state a recommendation so Wave 28's future scope craft has a starting
point:

**Recommendation for Wave 28**: bundle "compress MVP + atomic-write module
used by compress". The rationale:

1. A general atomic-write module (`src/myco/io_utils.py::atomic_write_yaml`)
   without a consumer is speculative — we wouldn't know if the API shape
   is right. Building it alongside its first consumer (compress) guarantees
   the API fits a real use case.
2. The module's initial surface is small: one helper (`atomic_write_text`),
   one helper (`atomic_write_yaml`). ~30 lines total.
3. Wave 28 can refactor **only** the file writes that `compress` needs (the
   output note + the input note status flips). Other file writers (`notes.py::
   write_note`, `upstream.py::ingest_bundle`, etc.) stay as-is in Wave 28 and
   get retrofitted in Wave 29+ as friction demands.
4. This is one subsystem ("the compression operation including its
   supporting atomicity"), not two. It fits within Round 2 capacity.

The alternative — "Wave 28 atomic writes alone, Wave 29 compress" — has the
drawback that Wave 28 delivers something without a doctrine anchor (it just
serves engineering hygiene), which violates the new D3 discipline from
Wave 26.

Attack I lands as "make the scope explicit in Wave 28's future craft, not
this craft". This craft leaves the scope decision to Wave 28's own Round 2
discussion, but records the recommendation.

## 3. Round 3 — Synthesis + specification for Wave 28

### 3.1 Specification

Based on §1 proposals and §2 attack resolutions, Wave 28 should implement:

**Verb**: `myco compress`

**Invocation**:
```
myco compress --tag <TAG> [--status raw|digesting]
myco compress <note_id1> <note_id2> ... <note_idN>
myco compress --tag <TAG> --dry-run
```

**Required flags**:
- `--tag <TAG>` XOR positional `<note_ids>` — mutually exclusive input sources
- `--rationale <TEXT>` — required prose (enforced at invocation, not inferred)
- `--dry-run` — optional; shows what would happen without writing

**Behavior**:
1. Resolve input cohort (tag filter OR explicit ids)
2. Reject if cohort is empty (exit 4 with clear error)
3. Reject if any input already has `compressed_from` field (cascade prevention)
4. Reject if any input is in a terminal-protected status (excreted already)
5. If `--dry-run`, print cohort + proposed rationale + proposed output path, exit 0
6. Otherwise:
   a. Write output note to notes/n\_\<ts\>\_\<suffix\>.md with `status: extracted`,
      `source: compress` (new source value, added to canon in Wave 28), and all
      the audit frontmatter fields (§1.4)
   b. For each input: flip `status` → `excreted`, set `excrete_reason`, set
      `compressed_into`, optionally set `pre_compression_status`
   c. All writes via atomic temp+rename (hermes catalog C2 pattern, minimum
      surface: one helper in `src/myco/io_utils.py`)
   d. Return success with output note id

**New frontmatter fields** (to be added to `_canon.yaml::system.notes_schema`):
- `optional_fields`: add `compressed_from`, `compressed_into`,
  `compression_method`, `compression_rationale`, `compression_confidence`,
  `pre_compression_status`
- `valid_sources`: add `compress` (to the enum — alongside eat, chat,
  promote, import, bootstrap, forage, upstream_absorbed)

**New hunger signal**: `compression_ripe`
- Fires when a tag cohort has ≥`compression_ripe_threshold` raw notes AND
  oldest cohort member is ≥`compression_ripe_age_days`
- Thresholds in `_canon.yaml::system.notes_schema.compression = {ripe_threshold: 5, ripe_age_days: 7}`
- Signal appears in `myco hunger` output AND in boot brief priority signals
- Non-blocking advisory (LOW severity — not HIGH reflex)

**New lint dimension**: L18 `lint_compression_integrity` (to be added in Wave 28)
- Verifies bidirectional link integrity: every note with `compressed_from`
  has all referenced notes in `notes/`, and every referenced note has
  `compressed_into` pointing back
- Severity HIGH (broken audit chain is a structural violation)
- Detects cascade violation: rejects any note where `compressed_from` list
  contains a note that itself has `compressed_from` (cascade not allowed)

**Contract bump**: Wave 28 will bump v0.25.0 → v0.26.0 (new verb + new
schema section + new lint dimension + new source value).

### 3.2 Not in Wave 28 scope (explicit defer list)

- `myco uncompress` verb — Wave 29+ if friction justifies
- Agent-adaptive compression policy (32K vs 200K) — open problem, possibly
  never as an explicit feature (agents choose their own cohort size via
  `--tag` scoping)
- Full atomic-write refactor of `notes.py::write_note` /
  `upstream.py::ingest_bundle` / `forage.py::add_item` — Wave 29+ as
  friction demands
- `myco evaluate` standalone verb — subsumed by `myco compress --dry-run`
- `myco extract` standalone verb — subsumed by `myco compress` output
- Metabolic Inlet integration (`compression_ripe` as Inlet trigger signal)
  — remains open problem per `docs/open_problems.md §2`; compression signal
  becomes **candidate** for Inlet trigger but not committed

### 3.3 Confidence target decision

Wave 27 reports `current_confidence: 0.85` = `target_confidence: 0.85`.
Exploration class floor is 0.75 per `_canon.yaml::system.craft_protocol.
confidence_targets_by_class`. 0.85 is above floor, reflecting:

- The 7 design questions each received a working proposal grounded in
  Myco doctrine
- 4 attacks ran against the design, producing 4 revisions (audit trail
  emphasis, dry-run mandatory, language softening on reversibility,
  Wave 28 scope recommendation)
- External evidence exists (hermes catalog C2 atomic writes; notes.py
  existing write infrastructure) — this is not pure single-source debate
- Acknowledged residual risks (hallucination, audit-at-scale,
  adaptive-policy-future) are §4 limitations

**Not 0.90 (kernel_contract floor)** because:
- This is a design craft. The design is not yet tested against real
  compression workloads. Wave 28 implementation may reveal edge cases
  that require design revision.
- Single-source convention (per `docs/craft_protocol.md §4`): agent-authored
  craft with external research counts as slightly-above-floor, not target
  floor.

### 3.4 Supersession

None. This is a new primitive design, not a supersession of prior work.

## 4. Conclusion extraction

### 4.1 Decisions (become canon via Wave 27's landing, take effect in Wave 28)

**D1 — Unit of compression**: tag-scoped (primary) + manual bundle (escape
hatch). Reject semantic cluster (parametric cost), time-window (too coarse),
status-scoped (foldable into tag + `--status` flag).

**D2 — Trigger**: manual invocation (always allowed) + friction-driven
hunger signal `compression_ripe` (agent can act or ignore). Reject scheduled
cron (violates anchor #6 selection loop).

**D3 — Output shape**: consumptive with audit — new `extracted` note
referencing N originals via `compressed_from`; originals become `excreted`
with `compressed_into` back-reference. Reject additive (doesn't reduce
attention), wiki synthesis (conflates surfaces), in-place promotion (loses
synthesis opportunity).

**D4 — Audit trail**: mandatory frontmatter fields `compressed_from`
(list), `compression_method` (manual/hunger-signal), `compression_rationale`
(required prose), `compression_confidence` (self-reported). Bidirectional
link integrity enforced via new L18 lint dimension. Cascade rejected at
schema time (compressed notes cannot themselves be compressed).

**D5 — Reversibility**: data-preserved, not operation-provided. Inputs
remain on disk with `excreted` status and back-references. `myco uncompress`
verb is Wave 29+ territory. Optional `pre_compression_status` frontmatter
field records prior state for future uncompress use.

**D6 — Pipeline integration**: `myco compress` folds anchor #3 steps 2+3+5+7
into one verb (evaluate via `--dry-run`, extract via output status, compress
as the verb itself, excrete as side-effect on inputs). Step 4 (integrate)
remains separate (`myco digest --to integrated`). This raises anchor #3
coverage from 0.43 → ~0.75 post-Wave-28.

**D7 — Non-functional contract**: idempotent (empty cohort = no-op), atomic
(all-or-nothing multi-file write via temp+rename), concurrent-safe (snapshot
input cohort before writes), cost bound O(N) file operations. Agent-adaptive
policy is NOT implemented in Wave 28 — deferred to open problems.

**D8 — Wave 28 scope recommendation**: bundle `myco compress` MVP + a
minimum atomic-write helper (`src/myco/io_utils.py::atomic_write_yaml`,
~30 lines) as a single subsystem. Do NOT try to refactor all existing file
writers to atomic in Wave 28. Other refactors are Wave 29+ as friction
demands. Wave 28's own craft will re-check this recommendation in its
Round 2 capacity attack.

**D9 — Hallucination risk is bounded, not eliminated**: the design commits
to audit-ability (reversible data), link integrity (L18), and cascade
prevention (schema-level). It does NOT eliminate the risk that individual
compressions fabricate. Bounded risk is the best this primitive can offer
without a second selection pressure (multiple humans, cross-agent review).
This limitation is registered honestly.

### 4.2 Landing list (Wave 27 scope, ≤ 10 items)

Wave 27 is a **design-only** craft. The landing is lightweight relative to
Wave 25/26 because there's no MYCO.md touching, no contract bump, no lint
dimension, no code.

1. Write `docs/primordia/compression_primitive_craft_2026-04-12.md` (this
   file) to disk with valid L13 frontmatter
2. `myco eat` this craft's evidence + design-decision summary as a raw note
   tagged `wave27-seed compression-design forage-digest`
3. `myco eat` + `myco digest --to integrated` Wave 27 decisions note
   (D1–D9) for canon
4. Append Wave 27 milestone entry to `log.md` (standard 7-point format)
5. `myco lint` 18/18 PASS + `pytest tests/ -q` 4/4 PASS before commit

**Not in Wave 27 landing**:
- No `MYCO.md` edits (no public_claim surface touches needed — compression
  is already acknowledged in anchor #4, this craft elaborates how it will
  be served in Wave 28+)
- No `_canon.yaml` edits (all the schema additions are Wave 28 territory)
- No template canon bump
- No `docs/contract_changelog.md` entry (exploration class, no contract
  bump, no changelog entry required by Wave 8 convention — exploration
  crafts can land without changelog if they don't touch kernel contract)
- No code changes
- No `src/myco/io_utils.py` creation (Wave 28)
- No L18 lint implementation (Wave 28)

### 4.3 Known limitations

**L1 — Hallucination residual is not eliminated**: Attack F defense bounds
the risk but doesn't remove it. At scale, compression will produce occasional
faithful-looking fabrications that the single human reviewer (the user)
cannot catch. Long-term mitigation requires either (a) multi-agent
cross-review of compressions (cost: agent count ≥ 2), (b) external
verification against original sources (cost: source fetch), (c) statistical
sampling audit (cost: tooling + discipline). None of these are in Wave 28
scope. Registered.

**L2 — Single-agent design ceiling**: this craft's attacks are all generated
by the kernel agent without a second agent challenging the design. Per
`docs/craft_protocol.md §4` single-source convention, confidence at 0.85
(above exploration floor 0.75, below kernel floor 0.90) is the right place
for this level of rigor.

**L3 — `source: compress` is a new enum value**: adding it to
`_canon.yaml::notes_schema.valid_sources` is a schema-level change. Wave 28
will formally add it and upgrade L10 lint to recognize it. If Wave 28's
Round 2 finds reason to reuse an existing value (e.g. `promote`), D3's
output shape still holds but the source value changes. This craft defers
the final source-value decision to Wave 28.

**L4 — Agent-adaptive compression policy (32K vs 200K)**: anchor #4
explicitly calls for "agent-adaptive" compression. Wave 28 will NOT implement
this — the MVP is a fixed-behavior verb. Adaptive policy may turn into an
open problem (how does the substrate know what Agent context window a caller
has? via canon setting? via env var? via tool invocation metadata?). If it
does, Wave 29+ will register it. Otherwise, adaptive-by-cohort-size stands
in: larger cohorts implicitly mean more aggressive compression, smaller
cohorts less — and the caller chooses cohort size via `--tag` scope.

**L5 — `uncompress` verb is vapor**: §1.5 relies on future work to realize
full reversibility. Wave 28 preserves the data (honest); the reversal
mechanism is TBD. If a user asks "can I reverse this compression?" within
Wave 28's lifetime, the answer is "not with a verb, but you can manually
flip the excreted inputs back because the data is preserved".

**L6 — Wave 28's own scope craft may revise this design**: this is an
exploration craft. Its decisions are working proposals for Wave 28's
implementation craft (which will be kernel_contract class, 0.90 floor) to
validate, refine, or override. Wave 28's Round 2 attacks may find edges
this craft missed. That's the expected workflow.

### 4.4 Provenance + next step

- **Craft authored**: 2026-04-12, kernel-agent autonomous run
- **Trigger**: Wave 26 §3.3 locked this scope for Wave 27
- **Decision class**: exploration
- **Target confidence**: 0.85 (above exploration floor 0.75, below kernel floor 0.90)
- **Current confidence**: 0.85 (target met)
- **Rounds executed**: 3 (per §1, §2, §3)
- **External evidence base**: Wave 26 reconciliation findings, Wave 10
  vision_recovery compression doctrine citations, hermes catalog C2-pattern
  reference, `src/myco/notes.py` existing write infrastructure inspection,
  `docs/open_problems.md §1-4` Metabolic Inlet dependency on compression
- **L13 schema**: compliant (frontmatter has all 7 required fields)
- **L15 reflex arc**: satisfied (exploration craft materializes within
  the session; `docs/primordia/` is the canonical craft home; no
  kernel_contract surfaces touched)
- **Next step**: eat evidence + decisions notes, log.md milestone, verify
  lint + pytest, present diff for commit approval. Wave 28 will open its
  own scope craft (kernel_contract class) to implement the specification
  in §3.1 and validate it against real compression workloads.
