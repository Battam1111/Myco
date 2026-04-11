# Craft Protocol · 传统手艺协议 (W3)

> **Status**: ACTIVE · CONTRACT
> **Version**: v1 (first landed in Myco contract v0.9.0, 2026-04-11)
> **Bound principle**: W3 of the Twelve Principles (`docs/WORKFLOW.md`)
> **Debates of record**:
> - `docs/primordia/craft_formalization_craft_2026-04-11.md` (v1 schema, Wave 8)
> - `docs/primordia/craft_reflex_craft_2026-04-11.md` (discovery surface + L15, Wave 11)
> - `docs/primordia/craft_autonomy_craft_2026-04-11.md` (agent-autonomous reflex arc, Wave 12)
> **Schema of record**: `_canon.yaml: system.craft_protocol`
> **Lint of record**: L13 Craft Protocol Schema + L15 Craft Reflex (src/myco/lint.py)

## 1. What it is

**Craft Protocol** (中文正式名 **传统手艺**) is Myco's agent-autonomous
selection-pressure mechanism for raising confidence on a decision through
structured self-adversarial debate before the decision is frozen into
canon, code, or contract. It is the epistemic counterpart to Myco's
mutation/selection model: mutations are proposed, selection pressure is
applied through attack rounds + online research, and only mutations that
survive reach canonical status.

**Craft runs inside the agent loop, not outside it.** When a trigger
condition fires (see §3), the agent's immutable reflex is to create the
craft file in the same session — not to defer, not to ask the human to
authorize the decision to run one. The human collaborator stays in the
loop at audit time (commit review, async critique, human-authored or
collaborative crafts that supersede agent-only ones), but never as a
reflex trigger source. This is what "autonomous cognitive substrate"
means in practice: the selection machinery is self-firing, or it is not
a substrate.

Craft is **not** ceremony. A craft that fails to find real attacks is a
failed craft; its conclusion is untrusted regardless of how many rounds
were run or how high the self-reported confidence is. The structure exists
to prevent decision drift by compression and to keep an auditable artifact
of *why* each load-bearing choice was made the way it was. Transparency —
every conclusion is eaten into `notes/`, logged in `log.md`, and committed
to git — is the honor-system compensation for the fact that single-agent
adversarial debate has a lower ceiling than multi-party debate. Hollow
crafts leave a detectable trail for human audit.

> **Wave 8 A7 overturn (Wave 12, v0.11.0)**: the original Wave 8
> `craft_formalization_craft` Round 1 A7 rejected a `myco craft` CLI on
> the grounds that "craft 的核心是人与 agent 的持续对话，不是可自动化的
> job". That judgment was correct at the time (no L15 reflex existed, so
> any CLI was just ceremony) but wrong now. With L15 in place, the
> automation target shifted from "a CLI humans invoke" to "a reflex arc
> from trigger-surface touch → craft file materialization, entirely
> within agent loop". See `docs/primordia/craft_autonomy_craft_2026-04-11.md`
> §4.1 D1–D3 for the full reasoning.

## 2. Canonical form

A craft produces exactly one artifact: a markdown file at
`docs/primordia/<topic>_craft_<YYYY-MM-DD>.md`, following the schema in
`_canon.yaml: system.craft_protocol`. The artifact is both the workspace
of the debate and the permanent record of its conclusion.

### 2.1 File naming

Filename pattern (enforced by L13):

```
^[a-z][a-z0-9]*(_[a-z0-9]+){1,}_craft_\d{4}-\d{2}-\d{2}(_[0-9a-f]{4})?\.md$
```

Topic must be at least two underscore-separated tokens. Optional 4-hex
suffix resolves same-day collisions.

Examples:
- `upstream_protocol_craft_2026-04-11.md` ✅
- `craft_formalization_craft_2026-04-11.md` ✅
- `a_craft_2026-04-11.md` ❌ (only one topic token)
- `Upstream_Craft_2026-04-11.md` ❌ (uppercase)

### 2.2 Frontmatter schema (v1)

```yaml
---
type: craft                   # must be literal "craft"
status: ACTIVE                # DRAFT | ACTIVE | COMPILED | SUPERSEDED | LOCAL
created: 2026-04-11           # ISO date
target_confidence: 0.90       # float in [0,1]; must be >= floor for decision_class
current_confidence: 0.91      # float in [0,1]; when status is ACTIVE/COMPILED must be >= target_confidence
rounds: 3                     # int; must be >= min_rounds (default 2)
craft_protocol_version: 1     # int; presence enables strict L13 checks
decision_class: kernel_contract   # one of confidence_targets_by_class keys
---
```

Files without `craft_protocol_version` are **grandfathered**: L13 skips them
entirely (see §6 Migration).

### 2.3 Status semantics

| Status | Meaning |
|---|---|
| `DRAFT` | Writing in progress; fewer than `min_rounds` completed |
| `ACTIVE` | ≥ `min_rounds` completed; `current_confidence ≥ target_confidence`; conclusion is citable |
| `COMPILED` | Conclusion has been extracted into a permanent location (`_canon.yaml`, `docs/*.md` outside `docs/primordia/`, or code). Original is archived but no longer primary reference. Should set `compiled_into: [...]` |
| `SUPERSEDED` | Replaced by a newer craft. Preserved for history. Should set `superseded_by: <path>` |
| `LOCAL` | Local experiment, gitignored, excluded from lint |

Status transitions are monotone in canonicality but not in time: ACTIVE can
become COMPILED (work moved to permanent home) or SUPERSEDED (replaced
before it ever reached permanent home). COMPILED can still become
SUPERSEDED later.

### 2.4 Required sections in the body

L13 does **not** check body structure — only frontmatter. But authors
are strongly encouraged to follow this shape for readability and for
future machine extractors:

```
## 0. Problem definition
## 1. Round 1
    ### 1.1 Claim
    ### 1.2 Attack
    ### 1.3 Online Research
    ### 1.4 Defense + Revise
## 2. Round 2 (...)
## N. Conclusion extraction
    ### N.1 Decisions
    ### N.2 Landing list
    ### N.3 Known limitations
```

## 3. Invocation triggers

Run a Craft when any of the following is true:

1. **Kernel contract change** (Class Z in Upstream Protocol §8.2): any edit
   to `docs/agent_protocol.md`, `_canon.yaml`, `scripts/lint_knowledge.py`,
   `src/myco/lint.py`, `src/myco/mcp_server.py`, or `src/myco/templates/**`.
   Minimum `target_confidence: 0.90`, `decision_class: kernel_contract`.

2. **Instance-level architectural decision**: any decision that will shape
   how an instance stores, digests, or retrieves knowledge for more than
   one session. Minimum `target_confidence: 0.85`,
   `decision_class: instance_contract`.

3. **Confidence below 0.80** on any decision that will be referenced later:
   run an `exploration`-class craft to raise confidence before committing.
   Minimum `target_confidence: 0.75`, `decision_class: exploration`.

4. **External stakeholder-visible claim**: anything that will appear in
   README, public docs, or marketing — so that the claim has an
   auditable defense trail.

5. **Online research reveals conflict** with a current canon item: run a
   craft to resolve the conflict instead of silently updating canon.

### 3.1 Reflex arc (contract v0.11.0, Wave 12)

The five triggers above are a rule book. A rule book without a reflex
arc is advisory: it only fires if the agent remembers craft exists at
the moment of decision. Wave 10 exposed this as an empirical failure —
a full README trilogy rewrite (textbook Trigger #4) proceeded without
invoking craft because the discovery surface was pure documentation.
Wave 11 built the detection; Wave 12 closes the arc by making the
reflex immutable and agent-autonomous.

**The arc**:

1. Agent touches a file in
   `_canon.yaml: system.craft_protocol.reflex.trigger_surfaces.*`.
2. Detection (runs every `myco lint` / `myco hunger` / session boot):
   `now - path.stat().st_mtime < lookback_days * 86400`. Auxiliary
   evidence check on `log.md` + `docs/primordia/*_craft_*.md` mtimes
   for the same window — if craft evidence is present, arc is
   satisfied. If the diff is trivial (≤ `trivial_exempt_lines` lines
   changed AND no new identifiers added, checked via `git diff`),
   arc is exempted — whitespace fixes do not require crafts.
3. If uncovered and non-trivial, L15 emits a HIGH issue and
   `myco hunger` emits `craft_reflex_missing`.
4. **Agent's immutable reflex on HIGH** (W3 obligation): write the
   missing craft at `docs/primordia/<topic>_craft_<YYYY-MM-DD>.md`
   **in the same session**, before resuming the task. Bypassing via
   `--no-verify` or ignoring the signal is a W3 violation, not a
   shortcut. This is not a convention — it is the protocol.

Trigger surfaces are split into two classes:

- `kernel_contract` — `docs/agent_protocol.md`, `docs/craft_protocol.md`,
  `_canon.yaml`, `src/myco/lint.py`, `src/myco/mcp_server.py`,
  `src/myco/templates/_canon.yaml`, `src/myco/templates/MYCO.md`.
  Touching any of these maps to Trigger #1 above.
- `public_claim` — `README.md`, `README_zh.md`, `README_ja.md`,
  `MYCO.md`, `docs/vision.md`. Touching any of these maps to
  Trigger #4 above.

**Severity is HIGH, not LOW** (changed in Wave 12 from the initial
Wave 11 LOW). The reasoning: Wave 11 treated the reflex as a signal
because the design still implicitly relied on a human to decide
whether to act on it. Wave 12 overturns that: the agent acts on the
signal immutably. HIGH severity is what makes `myco lint` refuse to
return 0 until the craft exists, and the agent's protocol-bound
response is never to suppress lint — it is to write the craft.

**The agent is not the passive consumer of the reflex; the agent IS
the reflex arc.** Detection fires inside the lint/hunger pass, the
obligation fires inside the agent loop, and the craft materializes
within the same session that touched the surface. The human does not
have to type anything. This is what distinguishes a substrate from a
toolbox: the substrate self-fires.

Detection strategy is **mtime-primary**: mtime is robust against log
prose variation and survives fresh-clone cutoffs (clone time becomes
a natural mtime floor). Auxiliary regex on `log.md` catches the
"touched two surfaces in one craft landing" case without requiring
per-craft log entries.

## 4. Confidence classes

| `decision_class` | Floor target | Examples |
|---|---|---|
| `kernel_contract` | **0.90** | Agent Protocol changes, lint dimensions, canon schema, upstream protocol |
| `instance_contract` | **0.85** | Per-project knowledge architecture, wiki schema, tag taxonomy |
| `exploration` | **0.75** | Naming questions, open research, tentative designs |

These floors are **taxonomic**, not empirical — they represent the
organizational contract about when a decision is "safe enough" to act on,
not an optimal point derived from data. Floors may be raised over time
based on Phase ② friction data, but should never be lowered silently.

**Important**: `current_confidence` is self-reported by the author. L13
verifies it meets the floor but cannot verify its honesty. Quality is
defended instead through social transparency: every craft conclusion is
eaten into `notes/` (via `myco eat`) and logged in `log.md`, exposing
self-reported numbers to future audit. Inflated confidence scores leave
a traceable trail.

**Single-source convention** (Wave 12, v0.11.0): a craft whose attack
rounds are all generated by a single agent without citing external
research (`Online Research` sections empty or missing) SHOULD report
`current_confidence ≤ target_confidence` (cannot exceed target). This
is a procedural compensation for the fact that single-agent adversarial
debate has a lower ceiling than multi-party debate. The convention is
not currently lint-enforced; future L16 may add detection.

## 4.5 Collaboration model (Wave 12, v0.11.0)

Agent-autonomous craft does not mean human-excluded craft. It means the
human is not in the **invocation loop**. The human remains in the
**review loop** in three ways:

1. **Async audit**: every craft is a git-tracked artifact. Humans can
   read, critique, and respond to agent-authored crafts asynchronously.
2. **Human-authored crafts**: humans write their own crafts using the
   same schema. A human-authored craft carries the same frontmatter,
   lives in the same directory, passes the same L13 check.
3. **Collaborative + supersession**: a human-authored or human+agent
   collaborative craft can **supersede** a prior agent-only craft by
   setting `superseded_by: docs/primordia/<human_craft>.md` in the
   old frontmatter and `status: SUPERSEDED`. The agent-only craft
   becomes historical; the collaborative one becomes current.

The agent-only craft is a **floor**, not a ceiling. It guarantees that
every kernel-class or public-claim decision has at least one defense
trail before shipping. Higher-quality crafts are always welcome and
always supersede.

## 5. Integration with other Myco primitives

| Primitive | How Craft Protocol interacts |
|---|---|
| `notes/` (via `myco eat`) | Every craft conclusion MUST be eaten as a raw note with tags including `craft-conclusion` + `decision-class-<class>` |
| `log.md` | Every craft completion (DRAFT → ACTIVE) appends a milestone entry referencing the craft file and final `current_confidence` |
| `_canon.yaml` | Any canon modification in `kernel_contract` class MUST cite a supporting craft file in its commit body |
| `docs/agent_protocol.md §8` (Upstream Protocol) | Instance → kernel upstream bundles MUST include a `craft_reference` field pointing to the supporting craft. Bundle's `decision_class` determines `target_confidence` floor |
| `docs/contract_changelog.md` | Each entry MUST cite the craft(s) that justified the change |
| L9 Vision Anchor lint | Vision-related conclusions inside a craft are still subject to L9 anchor checks (craft is not a lint exception) |
| L10 Notes Schema | `craft-conclusion` notes follow normal L10 schema rules |
| L13 Craft Protocol Schema | Enforces the above schema on craft files with `craft_protocol_version: 1` |

## 6. Migration (grandfather rule)

The 20+ craft files that existed in `docs/primordia/` before this protocol
was formalized are **grandfathered**: they do not declare
`craft_protocol_version` and are fully skipped by L13. They remain
historically valid and citable.

New craft files (from 2026-04-11 onward) MUST declare
`craft_protocol_version: 1` in frontmatter and will be strictly checked.

When an existing grandfathered craft is significantly edited, L13 emits
a `LOW` reminder to consider adopting v1. This is a soft migration;
nothing forces rewrite.

## 7. Known limitations

1. **`compiled_into` hygiene depends on author discipline.** L13 cannot
   detect a craft whose conclusion *should* have been marked COMPILED but
   wasn't. A `stale_active_threshold_days` (default 30) triggers LOW
   reminders but not errors.
2. **Self-reported confidence is not verifiable.** L13 checks only that
   the number meets the floor, not that it reflects reality. Goodhart
   risk is mitigated by transparency, not enforcement.
3. **Body structure is partially linted (Wave 15, v0.14.0).** `rounds: N`
   is now cross-checked against measured body content by L13's body schema
   (see canon `craft_protocol.body_schema`). Specifically:

   | finding | severity | trigger |
   |---------|----------|---------|
   | `body_chars < rounds × min_body_chars_per_round` | HIGH | hollow craft — total non-whitespace body below floor |
   | `0 < body_rounds < rounds` | HIGH | declaration lie — fewer `## Round N` anchors than declared |
   | `body_rounds == 0 and rounds > 0` | MEDIUM | style nudge — no `Round N` anchors at all, consider adding explicit headings |
   | per-round slice chars `< min_round_body_chars` | MEDIUM | thin round — individual round body below floor |

   Defaults: `min_body_chars_per_round = 200`, `min_round_body_chars = 150`.
   Round markers accept English (`Round N`, `R(N)`), Chinese (`第N轮`),
   and Japanese (`ラウンド N`). The check deliberately measures
   non-whitespace chars (language-neutral, CJK-friendly) rather than
   tokens or lines. Goodhart residue (whitespace / filler) is still
   possible but requires visible effort; transparency countermeasure in
   §4 remains primary defense. Authoritative argument:
   `docs/primordia/l13_body_schema_craft_2026-04-11.md`.
4. **Bootstrap file exemption.** The craft that introduced this protocol
   (`docs/primordia/craft_formalization_craft_2026-04-11.md`) intentionally
   omits `craft_protocol_version` to avoid recursive self-regulation,
   symmetric with Upstream Protocol §8.7 bootstrap exemption.
5. **Honor-system ceiling for agent-autonomous crafts** (Wave 12).
   With Wave 12's severity=HIGH, an agent under time pressure can
   still write a hollow craft with handwaved attacks to pass L15. The
   only compensations are transparency (every craft is git-tracked
   and `myco_eat`'d) and human async audit. Hollow-craft detection
   (attack-depth scoring, online-research citation counting, etc.)
   is registered as future work in `docs/open_problems.md`.
6. **`trivial_exempt_lines` threshold is unvalidated.** The bootstrap
   value is 20 lines. Future Phase ② friction data will tell us
   whether mechanical fixes frequently exceed 20 lines or hostile
   actors game the exemption by splitting changes. The threshold is
   canon-configurable and revisable without code change.
7. **Git dependency for `trivial_exempt`.** The exemption check uses
   `git diff --numstat`. In non-git environments (rare) or before the
   first commit, the check fails closed (reflex fires regardless),
   which is conservatively correct but may create false positives
   for minimal CI pipelines.

## 8. Deprecation criteria (reverse sunset)

L13 SHOULD be considered for removal or merge into L10 if any of the
following hold for an extended period:

- **Dead lint**: L13 reports zero violations for 6 consecutive months
  (suggests the schema has been internalized as habit and the check no
  longer provides signal).
- **Dead mechanism**: fewer than 1 new craft file per month for 3
  consecutive months (suggests the Craft Protocol itself is no longer in
  active use and its infrastructure is overhead).
- **Better replacement**: an automated attack-defense mechanism emerges
  that makes human-authored crafts a bottleneck.

L15 Craft Reflex SHOULD be considered for removal or simplification if:

- **Dead reflex**: L15 reports zero violations for 6 consecutive months
  *AND* at least one qualifying surface touch was observed in the same
  period (distinguishes "reflex internalized as habit" from "nobody is
  editing kernel files anyway").
- **Goodhart overrun**: craft files are authored merely to suppress
  L15 without real debate (detect by `rounds: 2` + near-floor
  `current_confidence` + <24h between surface touch and craft
  creation). If observed >3 times in a quarter, strengthen rather than
  remove: require a minimum craft body length or a non-trivial
  attack section count.
- **Better replacement**: a structural-edit-time prompt replaces
  post-hoc detection entirely.

These criteria are documented here to prevent the "can't delete a lint
once added" failure mode. A lint that has outlived its purpose should be
removed with the same discipline with which it was added.

## 9. Relationship to the Twelve Principles

Craft Protocol is the formal implementation of **W3 传统手艺**. The prose
gloss of W3 in `docs/WORKFLOW.md` remains the human-readable summary;
this document is the machine-verifiable specification. In case of
conflict, `docs/WORKFLOW.md` describes the *spirit*, this document
describes the *schema*, and `_canon.yaml` is the *single source of truth*
for field definitions.

---

**Canonical references**
- Principle: `docs/WORKFLOW.md` W3
- Schema: `_canon.yaml: system.craft_protocol` (reflex subblock: v0.10.0; severity HIGH + trivial_exempt: v0.11.0)
- Lint: `src/myco/lint.py::lint_craft_protocol` (L13) + `src/myco/lint.py::lint_craft_reflex` (L15, severity HIGH)
- Hunger signal: `src/myco/notes.py::detect_craft_reflex_missing` (`craft_reflex_missing`)
- Debate records:
  - `docs/primordia/craft_formalization_craft_2026-04-11.md` (v1 schema, Wave 8)
  - `docs/primordia/craft_reflex_craft_2026-04-11.md` (discovery surface + L15, Wave 11)
  - `docs/primordia/craft_autonomy_craft_2026-04-11.md` (agent-autonomous reflex arc, Wave 12 — overturns Wave 8 A7)
- Contract versions: v0.9.0 (schema) → v0.10.0 (reflex) → v0.11.0 (autonomy + severity HIGH)
