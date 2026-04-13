---
type: craft
status: ACTIVE
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.92
rounds: 2
craft_protocol_version: 1
decision_class: kernel_contract
---

# Forage Substrate Craft — External reference intake as a first-class organ

> **Decision class**: `kernel_contract` (floor 0.90)
> **Terminal confidence**: 0.92
> **Rounds**: 2
> **Debate of record for**: Wave 7 — introduction of `forage/` directory,
> L14 Forage Hygiene lint, `forage_backlog` hunger signal, and
> `myco forage add / digest` CLI verbs.

## §0 Why a craft — and why kernel_contract class

the creator's Q2 in the 2026-04-11 panorama follow-up: *"我想要在 Myco 中有
一个专门下载、存放各种资料的地方，比如说能够帮助它进化的各种 GitHub
项目、博客、论文等等，目前 Myco 中有吗？是否与它原有的结构相契合？"*
Answer to the factual part: **no**, Myco currently has no such place.
`notes/` is internal capture, `docs/` is contract, `wiki/` is
hermes_skill internal library, `src/` is code. None of these fit
external material in a transient pre-digestion state.

This is a kernel_contract decision because it touches **five contract
surfaces simultaneously**:

1. **L1 structure** — new top-level directory `forage/`
2. **L11 write-surface** — agent must be allowed to write to forage/
   without per-case review
3. **canon schema** — new `system.forage_schema` block
4. **lint dimensions** — new L14 Forage Hygiene
5. **hunger model** — new `forage_backlog` signal + new CLI verb family

Any one of these alone would be `instance_contract`; five together is
unambiguously `kernel_contract`. Floor 0.90.

## §1 Three-part Claim

### C1 — Naming and biological identity

**Directory name**: `forage/` (not `refs/`, `library/`, `corpus/`, or
`substrate/`).

**Biological mapping**: in mycology, **foraging** is the active phase
where hyphae extend outward to explore the substrate for nutrients,
typically before secreting **exoenzymes** to externally digest complex
molecules (lignin, cellulose) into simple ones (sugars, amino acids) for
absorption. This is **literally** the same shape as what the user is
asking for:

- agent → hyphal extension → 主动去 GitHub / arXiv / blogs 觅食
- download → substrate encounter → 资料拉回 forage/
- summary / extract → exoenzyme phase → digest 到 notes/
- note → absorption → 进入常规 7 步代谢 pipeline
- archive/delete → nutrient depletion / discard → forage 原件淘汰

**Marginal returns test** (from biomimetic_map.md §3): `forage/` passes
because the verb form conveys **pre-digestion transient state** — a
semantic that `refs/` / `library/` actively obscure. Foraged material
is **not a permanent reference**; it is a **temporary deposit** that
must be compressed, digested, and eventually discarded. The name itself
is a discipline enforcer — whoever uses `refs/` thinks "permanent", which
contradicts the compression doctrine. `forage/` makes the transience
immediate.

**Update to `biomimetic_map.md`**: add `forage/` to §2 mapping table as
the **first** directory whose biomimetic name is justified by
information gain from day one (rather than retrofitted onto an existing
software-engineering term).

### C2 — Structure and lifecycle

**Directory layout** (minimal, not over-designed):

```
forage/
  _index.yaml                 # manifest: all foraged items, their metadata
  papers/                     # PDF, arxiv, markdown papers
  repos/                      # git clones (shallow preferred)
  articles/                   # blog posts, HN discussions, threads → .md
```

**Manifest schema** (per item in `_index.yaml`):

```yaml
items:
  - id: f_20260411T120000_a1b2       # f_ prefix, matches notes id convention
    source_url: https://arxiv.org/abs/...
    source_type: paper                # paper | repo | article | other
    local_path: papers/attention_is_all_you_need.pdf
    acquired_at: 2026-04-11T12:00:00
    status: raw                       # raw → digested → absorbed | discarded
    license: CC-BY-4.0                # REQUIRED; "unknown" allowed but flagged
    license_restrictions: []          # e.g. ["no-redistribute", "no-modify"]
    size_bytes: 1523000
    digest_target: null               # once digested: note id(s) produced
    notes: "..."                      # human annotation, optional
```

**Lifecycle (6 states, maps onto 7-step metabolism)**:

| state        | meaning                                    | step         |
|--------------|--------------------------------------------|--------------|
| `raw`        | freshly acquired, not yet processed        | 1. 发现 / 获取 |
| `digesting`  | agent is actively extracting content       | 2. 评估 / 萃取 |
| `digested`   | summary note(s) produced, original kept    | 3. 整合       |
| `absorbed`   | digest note(s) further processed + archived| 4. 压缩 / 验证 |
| `discarded`  | explicitly removed (license, noise, error) | 5. 淘汰       |
| `quarantined`| failed license check / lint, needs review  | — (dead-end) |

### C3 — Channel classification and contract integration

**Forage is an inbound channel** — material flows from external world
into substrate. It is **orthogonal to Upstream Protocol §8**, which is
the `instance → kernel` outbound channel for change proposals. The
agent_protocol.md §8 adds a new §8.9 subsection declaring three
channels explicitly:

- **inbound/forage** — external world → substrate (Wave 7, v1.7.0)
- **internal/notes** — substrate self-observation → notes/ (v1.0-v1.1)
- **outbound/upstream** — instance → kernel (v1.2.0 Upstream Protocol)

These three channels **must not be mixed**. In particular, a foraged
item **cannot** become an upstream bundle directly — it must first pass
through notes/ (internal absorption), then the resulting note can
become an upstream candidate if it meets §8.3 criteria.

**L11 write-surface** extension: `forage/**` is added to the agent
writable whitelist. This is a minor extension, symmetric to how
`notes/**` was added in v1.0.

**Canon block**:

```yaml
system:
  forage_schema:
    dir: forage
    index_file: forage/_index.yaml
    valid_statuses: [raw, digesting, digested, absorbed, discarded, quarantined]
    required_item_fields:
      - id
      - source_url
      - source_type
      - local_path
      - acquired_at
      - status
      - license
      - size_bytes
    filename_pattern: '^f_\d{8}T\d{6}_[0-9a-f]{4}$'
    max_item_size_bytes: 10485760        # 10 MB soft limit
    forage_backlog_threshold: 5          # ≥5 raw items triggers hunger
    stale_raw_days: 14                   # raw → hunger signal after 14 days
    total_budget_bytes: 209715200        # 200 MB soft total budget
    hard_budget_bytes: 1073741824        # 1 GB hard limit (enters L14)
```

### Outputs of C1+C2+C3

1. `forage/` directory + `_index.yaml` with empty `items: []` + `.gitignore`
   protecting large binary materials from being committed by default
2. `docs/biomimetic_map.md` §2 table extended with the `forage/` row
3. `_canon.yaml::system.forage_schema` block
4. `src/myco/templates/_canon.yaml::system.forage_schema` block mirror
5. `_canon.yaml::upstream_channels.class_z` adds `forage/_index.yaml`
6. **L14 Forage Hygiene** lint (new, in `src/myco/immune.py` only — single
   SSoT per Wave 6)
7. `detect_forage_backlog()` read-only signal wired into
   `compute_hunger_report`
8. `src/myco/forage.py` module (CLI backend, pure functions)
9. `src/myco/forage_cmd.py` CLI handler (`myco forage add / list / digest`)
10. `src/myco/cli.py` dispatch entry
11. `docs/agent_protocol.md` §8.9 new subsection (three-channel
    classification)
12. `docs/contract_changelog.md` v1.7.0 entry
13. `MYCO.md` banner + stage + doc index update
14. `log.md` Wave 7 milestone
15. The craft status starts ACTIVE, transitions to COMPILED when L14 is
    exercised in anger on a real foraged item

## §2 Round 1 — nine attacks

### A1 — License hazard

*"Downloaded content is copyrighted. Checking licenses into git can
cause real legal liability. Myco becomes a pirate library."*

**Defense**: the `license` field is **required** in manifest schema
(Round 1 enforces, L14 verifies). Items with `license: unknown` are
flagged as `quarantined` automatically on import; the `.gitignore`
default **excludes all `forage/papers/**/*.pdf` and
`forage/repos/**/*` from git** unless the item's license explicitly
permits redistribution (CC-BY, MIT, Apache-2.0, public domain).
Manifest `_index.yaml` is committed; actual binary content is local-only.
This mirrors how `.env` files are standard: schema committed, secrets
local.

### A2 — Repo bloat from large files

*"Even with gitignore, forage/ will become a 5 GB elephant that slows
every `git status`."*

**Defense**: `total_budget_bytes: 200 MB` soft limit triggers hunger
signal; `hard_budget_bytes: 1 GB` triggers L14 HIGH lint. Additionally,
`max_item_size_bytes: 10 MB` per-item soft cap — items larger than
10 MB trigger MEDIUM lint asking the agent to explain why they are
kept rather than digested+discarded. Git LFS is **not** the solution
because it still consumes local disk and shifts the problem; the real
answer is the compression doctrine: **if it can't be compressed into a
note, it shouldn't be in forage long-term**.

### A3 — Naming: why not `refs/` or `library/`?

*"`forage/` is cute but opaque. New readers will not know what it means."*

**Defense**: covered in C1. Summary: `refs/` implies permanence, which
contradicts the compression doctrine; `library/` implies curated
catalog, which is not the state; `corpus/` is a research term with
different connotations (NLP training data). `forage/` uniquely conveys
*transient active acquisition before digestion*. The verb form is load-bearing.
Onboarding cost is mitigated by in-directory `forage/README.md`
explaining the metaphor and lifecycle in 3 paragraphs.

### A4 — Overlap with notes/

*"`myco eat` already captures external material. Why not just `myco eat
<url>` with a source=web tag? Forage/ duplicates notes/."*

**Defense**: size and state. `myco eat` is designed for
**summary/thought/observation** capture — atomic notes of < 1 KB
typical. A 50-page PDF does not belong in notes/n\_\*.md frontmatter.
Forage/ holds the **pre-digested original**; notes/ holds the
**post-digestion extract**. They are different points in the pipeline,
not duplicates. Analogy: stomach vs bloodstream — you don't store raw
food in bloodstream.

Additionally, `notes/` entries have no `source_url` / `license` /
`size_bytes` fields. Conflating the two would force notes/ schema to
absorb fields it does not need and make L10 lint heavier.

### A5 — Agent hoarding

*"Make it too easy to forage and agent will hoard. Every search becomes
a permanent download. Myco becomes a download junkyard."*

**Defense**: the `forage_backlog` hunger signal triggers at **5 raw
items** (configurable). This is **intentionally low** — it says "you
have 5 undigested items, digest before foraging more". The 14-day
`stale_raw_days` threshold adds a second layer: raw items older than
14 days become hunger signals regardless of count. Two-layer pressure
prevents hoarding.

Additionally, `myco forage add` requires an explicit `--why` flag
(intent statement stored in manifest). No silent downloads. The
friction is **intentional**.

### A6 — Upstream Protocol channel confusion

*"Is forage an inbound or outbound channel? What if a foraged item is
relevant to kernel contract and should propagate upstream?"*

**Defense**: C3 answers this explicitly. Forage is **inbound only**.
Path `forage → notes → upstream-candidate → upstream` — the digested
note can become an upstream candidate if it meets §8.3 criteria, but
the foraged original cannot bypass notes/. The agent_protocol.md
§8.9 subsection makes this a contract.

### A7 — L11 write-surface expansion is a quiet contract escalation

*"Adding `forage/**` to write-surface looks harmless but it's a new
agent writability domain. The red line exists precisely because every
new writable path is a new attack surface."*

**Defense**: symmetric to the v1.0 addition of `notes/**`. L11 exists
to prevent agent from writing to `src/` / `docs/` / `_canon.yaml`
without review; `forage/` is by construction ephemeral and sandboxed.
However, the contract makes the restriction explicit:
**`forage/_index.yaml` is a class_z contract file** (listed in
`upstream_channels.class_z`), meaning agent can write to forage/ items
but the manifest itself is review-required. This prevents agent from
silently marking items as `absorbed` without justification.

### A8 — Compression gate ambiguity

*"When is a foraged item 'digested'? The compression doctrine only
works if the criterion is objective."*

**Defense**: objective criterion — a foraged item transitions from
`raw → digested` iff `digest_target` in manifest is non-null AND
points to ≥1 valid note id. The agent must produce at least one note
summarizing the foraged item before flipping status. L14 enforces this
transition (status=digested requires digest_target non-empty).
`digested → absorbed` requires the digest note(s) to reach status
`extracted` or `integrated` in notes/ pipeline. Both are mechanical
checks, not judgment calls.

### A9 — Binary/repo handling complexity

*"PDFs, git repos, HTML blobs — each is a different extraction problem.
Building parsers for all formats is out of scope for a substrate."*

**Defense**: Wave 7 ships **metadata + manual digest only**. The
`myco forage digest <id>` command **does not** auto-extract PDF text —
it opens the item (or prints the local_path), then prompts the agent
to produce a note via `myco eat` and update `digest_target`. Auto-extraction
is registered as Wave 8+ work. The Wave 7 deliverable is:
acquire + manifest + lifecycle + hunger signal + lint — **NOT** a
universal extractor. Keep the Claim small.

### Round 1 summary

All 9 attacks deflected without Claim revision. Intermediate confidence
rises from initial 0.78 to **0.88** (still below kernel_contract floor
0.90).

## §3 Round 2 — three residual attacks

### R2.1 — License manifest staleness

*"The `license` field is self-reported by the agent at acquisition time.
Two months later, upstream repo changes license — the manifest is now
stale AND we have no way to detect it."*

**Defense**: mark the staleness as **known limitation** in v1.7.0 (not
a blocker). L14 adds a LOW-severity check: items older than 90 days with
`status != absorbed` trigger a license-recheck reminder. Ground truth
license is whatever was at acquisition time — this is consistent with
citation norms ("accessed YYYY-MM-DD"). Recording both `acquired_at`
and `license_checked_at` (optional field, equals `acquired_at` by default)
gives the audit trail.

### R2.2 — Thresholds are arbitrary

*"Why 5 items? Why 14 days? Why 10 MB? These numbers are pulled out of
a hat."*

**Defense**: they are **seeded**, not adaptive — same pattern as v1.4.0
dead_knowledge thresholds and v1.5.0 structural_limits. Adaptive
thresholds are registered as future work in `docs/open_problems.md §4`.
The seed values come from a simple model: *"an agent can hold ~5 pending
reading items in working memory before thrashing; 14 days is roughly a
human sprint; 10 MB is the rough size above which manual triage becomes
worthwhile rather than digest-and-forget"*. They will be tuned with
field data.

### R2.3 — gitignore should protect by default, not by discipline

*"Attack A1's defense relies on agent remembering to gitignore large
files. Agents forget. Make it automatic."*

**Defense**: Wave 7 ships a default `forage/.gitignore` that excludes
`papers/**`, `repos/**`, and `articles/**/*.html`, but **does NOT**
exclude articles/\*\*/\*.md (small markdown extracts are fine). The
`_index.yaml` is always committed. This makes the common case safe by
default; the agent can override per-item by explicitly `git add -f`
for items with clearly permissive licenses. Moves the safety from
discipline to mechanism. Accepted.

### Round 2 summary

All 3 residual attacks deflected; R2.1 and R2.3 produced small Claim
refinements (license_checked_at optional field, default gitignore
shipped). Terminal confidence: **0.92** — above kernel_contract floor
0.90 by 0.02. Execute.

## §4 Execution plan (15 landing faces)

Strict ordering to minimize churn and maximize early-fail feedback:

1. Create `forage/` + `forage/_index.yaml` + `forage/README.md` +
   `forage/.gitignore` + subdirectories
2. Extend `_canon.yaml::system.forage_schema`
3. Mirror in `src/myco/templates/_canon.yaml`
4. Bump `contract_version` v1.6.0 → v1.7.0 + `synced_contract_version`
   mirror
5. Add `forage/_index.yaml` to `upstream_channels.class_z`
6. Add `forage/**` to `write_surface.allowed_paths`
7. Create `src/myco/forage.py` (pure functions: parse/serialize manifest,
   detect_forage_backlog, add/list/digest helpers)
8. Create `src/myco/forage_cmd.py` (CLI dispatch)
9. Wire `myco forage` into `src/myco/cli.py`
10. Add L14 `lint_forage_hygiene` in `src/myco/immune.py` (single SSoT,
    per Wave 6)
11. Update `main()` checks list in `src/myco/immune.py` to 15 dimensions
12. Wire `detect_forage_backlog` into `compute_hunger_report` after
    `structural_bloat`
13. Update `docs/agent_protocol.md` §8.9 (three-channel classification)
14. Update `docs/biomimetic_map.md` §2 table + §1 glossary (add
    "foraging" / "exoenzyme" explicit rows)
15. Update `docs/contract_changelog.md` v1.7.0, `MYCO.md` banner,
    `log.md` Wave 7 milestone, 15/15 lint dual-path verify, commit

## §5 Success criteria

- `forage/` exists with correct structure
- `_canon.yaml::system.contract_version == "v1.7.0"`
- `python scripts/lint_knowledge.py --project-dir .` → **15/15 PASS**
- `python -c "from myco.lint import main; main(Path('.'))"` → **15/15 PASS**
- `python -c "from myco.notes import compute_hunger_report; print(compute_hunger_report(Path('.')).signals)"` → no forage_backlog signal (empty manifest = no backlog)
- `myco forage add --source-url https://example.com/test.md --why "craft test"`
  runs without error, manifest has 1 item in status=raw
- `myco forage list` shows the test item
- L14 detects malformed manifest item (test: remove required field, lint
  flags HIGH)
- biomimetic_map.md §2 has `forage/` row
- agent_protocol.md §8.9 exists
- Single `[contract:minor]` commit with full wave summary

## §6 Known non-goals

- **No auto-extraction of PDFs / repos**. Wave 7 is acquisition +
  manifest + manual digest. Automated content extraction is Wave 8+.
- **No git LFS integration**. Binary content stays local via gitignore.
- **No universal source adapter**. `myco forage add` takes `--source-url`
  and downloads if accessible, otherwise assumes local path.
- **No license verification against upstream truth**. Self-reported at
  acquisition, staleness flagged by L14 at 90 days.
- **No notes/ auto-creation**. Digest is manual — agent uses `myco eat`
  for the note, then updates manifest `digest_target`.
- **No Wave 7 change to notes/ schema**. notes/ and forage/ remain
  schema-orthogonal.

## §7 Reverse sunset criteria

L14 Forage Hygiene will be deprecated (removed) if any of:

1. forage/ remains empty for 90 days → Lint is dead code, users rejected
   the paradigm. Remove L14, remove forage/, record as failed experiment.
2. Adaptive thresholds replace static ones AND the replacement moves
   forage_backlog into notes/ schema → L14 collapses into L10.
3. Better mechanism emerges (e.g. MCP server connectors that fetch
   on-demand without local storage) that makes forage/ redundant.

This is the L13 §8 reverse sunset discipline — every new lint born
with its exit plan.

## §8 Philosophical note

Forage/ is the **first time** Myco explicitly acknowledges that it has
an **outside**. Previous waves:

- v1.0-v1.1: substrate holds the agent's internal memory
- v1.2.0: Upstream Protocol — substrate acknowledges *other instances* of
  itself
- v1.3.0: Craft Protocol — substrate acknowledges its own *reasoning
  process* as a first-class object
- v1.4.0: Self-Model D — substrate acknowledges its own *forgetting*
- v1.5.0: biomimetic overlay — substrate acknowledges its own *identity*
- **v1.7.0: Forage — substrate acknowledges the *external world* as a
  source of nutrients**

This is a fundamentally different type of extension. All previous waves
were introspective; Wave 7 is **extrospective**. It requires a new
discipline: when the substrate reaches outside itself, it must bring
back only what it can digest. The compression doctrine now has teeth:
every foraged item must either become a note (digested) or be discarded
(excreted). No permanent storage, no hoarding, no becoming a library.

This is the mycorrhizal symbiosis made literal: the fungus extends
hyphae outward, secretes exoenzymes, absorbs what it can use, and
releases the rest. Myco now does the same to the web.
