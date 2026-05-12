# MYCO.md: agent entry page for the `myco-self` substrate

> You are an LLM agent reading this file at session start. Everything
> in this substrate is **for you**. Humans do not browse here (L0
> principle 1, 只为 Agent). They speak natural language; you invoke
> the verbs. Read this page top to bottom; it is short by design.

## What this substrate is

This repository is Myco, the cognitive substrate, and also
**Myco's own substrate**: the codebase uses Myco on itself, eating its
own dogfood through `_canon.yaml`, `notes/`, and `docs/`. Treat every
surface you encounter here as agent-readable primary material, not as
documentation for a human reader.

The substrate is governed by the five root principles in
[`docs/architecture/L0_VISION.md`](../docs/architecture/L0_VISION.md).
Read that page before you begin real work in this substrate. You do
not have to re-read it every session; but any action that feels
governance-shaped (canon edit, doctrine revision, new subsystem) is
only legitimate when you can point at the L0 principle that justifies
it.

## What to do first

1. Call `python -m myco hunger` yourself (or rely on the
   SessionStart hook, which already fired it). This is R1 of the hard
   contract; it computes and writes the session boot brief to
   `.myco_state/boot_brief.md`, then prints the summary. Every non-
   trivial session starts with this. The human never calls `hunger`.
   You do.
2. Check `log.md` (if present) for the last five entries. The tail
   of the timeline tells you what the previous session touched.
3. If you are about to write code: consult the relevant subsystem
   doctrine page under `docs/architecture/L2_DOCTRINE/` before
   reaching into `src/myco/<subsystem>/`. L2 is the contract between
   what a subsystem *should* do and what the code in it *does* do.

## The command surface

All verbs are defined by a single manifest:
[`src/myco/boundary/surface/manifest.yaml`](../src/myco/boundary/surface/manifest.yaml).
Both the CLI (`python -m myco <verb>`) and the MCP tool server
(`myco.boundary.surface.mcp.build_server`) are generated from it. If you need
to know what verbs exist, read that file, not this page.

Twenty verbs (19 agent + 1 human-facing `brief`), grouped by
subsystem. v0.5.2 aliases were removed at v0.6.0 (per Round 4
§A2 owner amendment); the canonical names are the only forms
that resolve:

- **germination**: `germinate`
- **ingestion**: `hunger`, `eat`, `sense`, `forage`, `excrete` (new at v0.5.24, safely delete a raw note with an audit tombstone), `intake` (new at v0.6.0, bulk forage + eat with strict-mode failure visibility)
- **digestion**: `assimilate`, `digest`, `sporulate`
- **circulation**: `traverse`, `propagate`
- **homeostasis**: `immune`
- **cycle**: `senesce` (`--quick` flag at v0.5.7 for SessionEnd hook), `fruit`, `molt`, `winnow`, `ramify`, `graft` (new at v0.5.3), `brief` (new at v0.5.5, the one human-facing exception to L0 principle 1)

Every verb accepts `--project-dir`, `--exit-on`, and `--json`.

## Ingestion adapters (v0.8.0)

`myco eat --path <target>` and `myco forage --path <root>` route the
target through the registered adapter list. v0.8.0 ships **13
built-in adapters** (was 10 at v0.7.10): `url`, `pdf`, `html`,
`tabular`, `chat-log`, `sqlite`, `email-mbox`, `git-history`,
`audio` (new), `image-ocr` (new), `video-frames` (new), `code-repo`,
`text-file`. The three multimedia adapters are gated behind the
opt-in `pip install 'myco[multimedia]'` extras (~500 MB transitive
closure of PyTorch + Whisper + OpenCV + Pillow + pytesseract). The
default install stays lean: when the extras are absent, the three
adapters emit install-extras failed-stubs (per the v0.7.3 AD1
closure protocol) so the agent gets clear `pip install` guidance
instead of silently dropping audio / image / video files. Image and
video OCR additionally require the system `tesseract` binary on
PATH; install via your platform's package manager.

## The immune surface

`myco immune` runs every registered dimension against the substrate
and reports findings. At v0.6.15 the roster is **46 dimensions**
across four categories:

- **Mechanical (31)**: `M1★`, `M2★`, `M3★`, `MF1`, `MF2`, `MF3`, `MF4`, `MP1`, `MP2`, `MP3`, `DC1★`, `DC2`, `DC3`, `DC4`, `DC5`, `CS1★`, `FR1`, `PA1`, `PA2`, `PA3`, `PA4`, `PA5`, `CG1`, `CG2`, `DI1★`, `DI2`, `AD1`, `SC1`, `CL1`, `CL2`, `CL3`
- **Shipped (2)**: `SH1`, `SH2`
- **Metabolic (6)**: `MB1★`, `MB2`, `MB3★`, `MB4`, `MB6★`, `MB7`
- **Semantic (7)**: `SE1★`, `SE2`, `SE3`, `SE4`, `RL1`, `RL2`, `RL3`

★ = fixable via `immune --fix` (10 dimensions: M1, M2, M3, DC1, CS1,
DI1, MB1, MB3, MB6, SE1). DC4 + PA1 stay advisory at v0.6.15 per the
v0.6.0 §F18 fix-narrowness craft (markdown surgery + write-surface
expansion are too delicate for safe-fix's idempotent / narrow /
non-destructive / bounded discipline). The full enumeration +
severities + fixability are in
[`docs/architecture/L2_DOCTRINE/homeostasis.md`](../docs/architecture/L2_DOCTRINE/homeostasis.md)
§ "Dimension enumeration". `immune --list` prints the live list;
`immune --explain <ID>` prints the prose description.

Baseline: `myco-self` exits 0 (CRITICAL-gate via canon
`lint.exit_policy.default = "mechanical:critical,shipped:critical,
metabolic:never,semantic:never"`) since v0.5.9. Non-critical findings
ride up each time the lint roster expands (25→46 at v0.6.0); the
v0.6.15 self-substrate carries 76 non-critical findings (9 HIGH AD1
adapter silent-skips inherited from pre-v0.6.0 adapters + 67 LOW
DC2/DC3/DC4/SE2 hygiene). These are tracked, not gated. **Every
new CRITICAL finding on the self-substrate is real signal**, and
HIGH-band drift is a candidate for the next severity-promotion
craft (`myco fruit`).

## Canon validation (v0.5.9+)

`_canon.yaml` is validated twice:

1. **At kernel import.** `myco.core.canon.load_canon` raises
   `CanonSchemaError` (exit 5) on shape violations.
2. **At edit time** (optional). IDEs that understand JSON-Schema
   validate against
   [`docs/schema/canon.schema.json`](../docs/schema/canon.schema.json).
   Wiring snippets for VS Code / JetBrains / Neovim are in the
   schema folder's [README](../docs/schema/README.md).

## Upgrading between versions

Boundary-specific migration notes live under
[`docs/migration/`](../docs/migration/README.md). Start there when
upgrading a downstream substrate across a MINOR bump; each file
translates contract-layer deltas into operator-visible steps.

## How to read the substrate

The substrate is a **graph**, not a tree (L0 principle 5). Every node
(canon field, note, doctrine page, code module, external artifact)
is reachable from every other by traversal. If you find an orphan,
that is circulation work.

Layers top-down:

```
L0  docs/architecture/L0_VISION.md             identity
L1  docs/architecture/L1_CONTRACT/*.md         contract
L2  docs/architecture/L2_DOCTRINE/*.md         doctrine (five subsystems)
L3  docs/architecture/L3_IMPLEMENTATION/*.md   implementation map
L4  _canon.yaml + code + notes/                the live substrate
```

Each lower layer is strictly subordinate to every higher layer. If L4
disagrees with L3, L3 wins, but the disagreement is a finding to
record, not to silence.

## Substrate-local plugins (v0.5.3)

A downstream substrate (any substrate whose `canon.identity.substrate_id`
is not `myco-self`) can carry its own lint dimensions, ingestion
adapters, schema upgraders, and even brand-new verbs without forking
Myco. Scaffold them with `myco ramify --dimension <ID>`,
`--adapter <name>`, or `--verb <name>` (pass `--substrate-local`
explicitly to override autodetection). They land under
`<substrate>/.myco/plugins/` and are auto-imported on
`Substrate.load()`; any verb the overlay at
`<substrate>/.myco/manifest_overlay.yaml` declares appears alongside
the built-ins. You inspect what has grafted on with
`myco graft --list | --validate | --explain <name>`. The `MF2` lint
dimension (mechanical / HIGH) keeps the auto-import audible: it
fires on shape errors, overlay-YAML errors, or verb-name collisions.

**Note for `myco-self`**: this repository IS the kernel. There is no
`.myco/plugins/` tree here, and `ramify` defaults `--substrate-local`
OFF so new kernel verbs / dimensions land inside `src/myco/`. Pass
`--substrate-local` only if you need to dogfood the overlay path.

## What NOT to do

- **Do not edit L0, L1, or L2 files as a consequence of implementation
  work.** If implementation reveals a gap in doctrine, stop, fruit a
  craft doc under `docs/primordia/` (via `myco fruit`), get owner
  approval, then resume.
- **Do not resurrect `legacy_v0_3/`.** The pre-rewrite code was
  excreted in v0.7.0. Git history preserves it; `v0.3.4-final` is
  the anchor tag. `core/skip_dirs.py` retains a defensive filter for
  the dirname in case it ever reappears.
- **Do not treat `integrated` as final.** Per L0 principle 4, every
  note is a work in progress until it is sporulated out of existence.

## When you finish a session

Run `python -m myco senesce` yourself (or rely on the PreCompact hook,
which already fires it at `/compact`). That composes `assimilate`
(promote raw notes) with `immune --fix` (auto-correctable lint
findings) and returns a structured payload. For non-compact session
exits (`/exit`, Ctrl+D, window-close), the SessionEnd hook fires
`python -m myco senesce --quick` (assimilate only) to stay inside
Claude Code's ~1.5 s SessionEnd kill budget; `immune` runs on the
next boot. A clean senesce (either mode) is the acceptable end state;
a dirty one is the starting point of the next session. The legacy
`session-end` alias still resolves if you find it in an older script.

## Subagents and slash commands (v0.6.11+)

If you (the agent reading this page) are running inside Claude Code, you
have access to 5 fungal-named subagents and 5 `myco-` slash commands that
formalize specialist roles for governance, investigation, and release work.

Each subagent's full role definition lives at `.claude/agents/<name>.md`
(project-level, auto-discovered when developing Myco-self) with a
byte-identical mirror at `<repo>/agents/<name>.md` (plugin-bundle scope,
declared in `.claude-plugin/plugin.json::agents` so plugin marketplace
installs deliver them to user installations). Slash commands follow the
same pattern at `.claude/commands/<name>.md` and `<repo>/commands/<name>.md`.

**Subagent roster** (invoke via Agent tool or `@agent-<name>`):

- **`primordium`**: drafts a 3-round craft proposal under `docs/primordia/`. Use when the user asks for an RFC / craft / contract-bump justification.
- **`hypha`**: investigates one `myco_immune` finding (root-cause trace + minimal-fix proposal). Read-only.
- **`autolysis`**: sweeps the substrate for stale narrative refs and produces a deterministic patch table. Read-only output.
- **`stipe`**: orchestrates the full release pipeline (gate → bump → commit → push → tag → ci.yml + release.yml watch → verify). Mutates state.
- **`anamorph`**: drafts a canon schema migration (named partials + tests + schema delta + migration guide). Stops before flipping `_canon.yaml::schema_version`.

**Slash command roster** (user invokes via `/<name>`):

- `/myco-primordium <topic>`: invokes `primordium`.
- `/myco-hypha [pattern]`: invokes `hypha` per finding.
- `/myco-autolyze [category]`: invokes `autolysis`.
- `/myco-disperse <version>`: invokes `stipe`.
- `/myco-anamorph <new-schema-version> <governing-craft-path>`: invokes `anamorph`.

**Surface invariants you must respect** (per L2 boundary doctrine):

1. Subagents cannot recurse (Claude Code spec). Compose them through Bash
   calls to Myco verbs, not through the Agent tool.
2. State-mutating subagents (`primordium`, `stipe`, `anamorph`) start with
   `myco hunger` per R1. Read-mostly ones (`hypha`, `autolysis`) skip
   the boot ritual but still honor R3 + R6.
3. Naming stays strictly fungal-bionic per L0:185-186. The boundary
   subsystem's English-name amendment (v0.6.0 §A1) does NOT extend to
   subagent names.

The full design rationale is in the v0.6.11 craft doc at
`docs/primordia/v0_6_11_subagents_and_commands_craft_2026-04-28.md`.
The boundary doctrine page (`docs/architecture/L2_DOCTRINE/boundary.md`,
section "Subagents and slash commands") is the authoritative L2 reference.

## When you are stuck

Re-read L0. Then re-read the relevant L2 page. Then re-read this file.
If you are still stuck, ingest a note describing the stuck-ness (call
`myco eat`) and let the next assimilation decide.
