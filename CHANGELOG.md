# Changelog

All notable changes to Myco are recorded here. This changelog tracks the
**package version** (`src/myco/__init__.py::__version__`). Contract-layer
changes (L0/L1/L2 doctrine) are recorded separately in
`docs/contract_changelog.md`.

The pre-rewrite changelog is preserved at `legacy_v0_3/CHANGELOG.md`.

Format: roughly [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/).

---

## [Unreleased]

*(next development head, no entries yet)*

---

## [0.5.7] — 2026-04-19

**Defense-in-depth session-end + v0.5.6 post-release cleanup.** The
v0.5.6 panoramic-release dogfood surfaced a coverage gap in R2:
sessions that end via `/exit`, Ctrl+D, or window-close never fire
PreCompact, so the R2 ritual silently skipped. The user's fix — a
third hook, SessionEnd, bound to the same `myco senesce` — hit a
~1.5 s kill budget that `senesce` (1.656 s on myco-self) already
exceeded. v0.5.7 lands a two-mode senesce so all three session-
termination paths land inside their host budgets, plus cleans up
every editorial drift item the v0.5.6 release postponed, plus adds
a mechanical CI baseline so the drift class can't silently
re-accumulate.

Governing crafts:
`docs/primordia/v0_5_7_senesce_quick_mode_craft_2026-04-19.md`
(quick-mode design) and
`docs/primordia/v0_5_7_release_craft_2026-04-19.md`
(release closure — bundles all four audit streams into one coherent
release).

### Added

- **`myco senesce --quick` flag.** New bool arg on the `senesce`
  verb. `--quick` runs `assimilate` only (skips the `immune --fix`
  pass), producing a payload of shape
  `{reflect: {...}, immune: {skipped: true, reason: <str>}, mode: "quick"}`.
  Exit code derived from assimilate alone. Default (full) mode
  unchanged: payload shape gains a new `mode: "full"` key; every
  existing consumer of `payload["immune"]` keeps working because
  the dict is always present. Wall-clock on myco-self (Python 3.13,
  Windows): full 1.533 s, quick 0.399 s (3.8× safety margin under
  the 1.5 s SessionEnd kill).
- **SessionEnd hook binding.** Both `hooks/hooks.json` (plugin
  distribution) and `.claude/settings.local.json` (self-dogfood)
  gain a third hook:
  `SessionEnd → python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" senesce --quick`.
  PreCompact stays on full `senesce`. SessionStart stays on `hunger`.
  Every downstream substrate that installs the Myco Claude Code
  plugin inherits the new three-hook layout. New doc
  `.claude/hooks/SessionEnd.md` explains the quick-mode role.
- **MP1 dedicated craft doc.** `docs/primordia/v0_5_6_mp1_mycelium_purity_craft_2026-04-18.md`
  — the narrow, independently-reviewable justification for MP1's
  blacklist roster, `providers/` opt-in package, and the
  `system.no_llm_in_substrate` canon field. Linked up from the
  v0.5.6 realignment umbrella craft.
- **pyproject metadata.** `classifiers`, `keywords`, `project.urls`
  (Homepage / Repository / Documentation / Changelog / Bug Tracker).
  PyPI release page now renders with a complete audience +
  Python-version matrix + license + topic classification.
- **pyproject tool baselines.** `[tool.mypy]` (permissive v1 baseline:
  `warn_unused_ignores`, `warn_redundant_casts`,
  `ignore_missing_imports`) and `[tool.ruff]` (target py310, select
  E/W/F/I/B/UP/SIM/C4/RUF, line-length 88, per-file ignores for
  tests and the ramify scaffolder). `types-PyYAML`, `ruff`, and
  `mypy` added to the `dev` extras so `pip install -e ".[dev]"`
  reproduces CI's tool set.
- **CI workflow.** `.github/workflows/ci.yml` runs `ruff check` +
  `ruff format --check` + `mypy src/myco` + `pytest` +
  `myco immune` + `python -m build` + `twine check` on every push
  and pull-request. Matrix covers Python 3.10 / 3.11 / 3.12 / 3.13
  on Ubuntu plus a Windows cell on the newest Python (catches
  CRLF / cp936 locale issues).
- **Release process runbook.** `docs/release_process.md` — the
  canonical eight-step runbook for shipping to all four delivery
  channels (git main, git tag, GitHub Release, PyPI). Replaces the
  implicit "read prior CHANGELOG verification commands" flow.
- **New test coverage** (+24 tests; total 609):
  - `tests/unit/cycle/test_senesce.py` — 13 tests (was new at
    v0.5.7-buffer) covering default-full behavior, explicit quick,
    payload shape, exit-code derivation, manifest declaration, MCP
    tool-spec parity, `session-end` alias survival, and dispatcher-
    path parity.
  - `tests/unit/cycle/test_graft.py` — 11 new tests (closes the
    0-coverage gap Audit C flagged: mode dispatch, `--list`
    enumeration, `--validate` clean-substrate path, `--explain`
    known + unknown, mutually-exclusive modes).
  - `tests/unit/surface/test_manifest.py` — 2 new tests for the
    string → bool coercion path (`"true"`, `"1"`, `"on"`, case-
    insensitive; plus falsy literals).
  - `tests/unit/surface/test_cli.py` — 3 new tests for the
    `senesce` + `senesce --quick` + `session-end` CLI end-to-end
    (argparse → dispatcher → handler round-trip).

### Changed — doctrine realignment (v0.5.6 postponements)

- **R2 rewording** in `docs/architecture/L1_CONTRACT/protocol.md`:
  "Every session ends with `myco senesce` — **full** (assimilate +
  immune --fix) on PreCompact (blocking), **quick** (assimilate
  only) on SessionEnd (short-budget fallback). The canonical
  session-end is the full form; quick is the defense-in-depth
  fallback." Enforcement-table R2 row updated to name both hooks.
- **MCP initialization instructions echo** (`src/myco/surface/mcp.py::_INSTRUCTIONS_TEMPLATE`):
  R2 line updated from "call myco_session_end (reflect + immune
  --fix) before compaction" to match the new L1 wording. Cross-
  platform MCP clients (Cursor, Windsurf, Zed, Codex, Gemini,
  Continue, Claude Desktop) see the updated contract at initialize.
  Canonical MCP tool name in the echo is now `myco_senesce` (was
  the deprecated `myco_session_end`); canonical verb name in the
  echo is `assimilate` (was the deprecated `reflect`).
- **Stale claim cleanup** — 20 line-level corrections across
  `README.md`, `README_zh.md`, `README_ja.md`, `MYCO.md`,
  `CONTRIBUTING.md`, `pyproject.toml` (console-script comment),
  `.claude-plugin/plugin.json` (version + description),
  `.claude/hooks/PreCompact.md` (rewrite), two skill files,
  `src/myco/germination/templates/entry_point.md.tmpl`
  (`genesis` → `germinate`, `session-end` → `senesce --quick` split),
  `tests/test_scaffold.py` (canonical + alias dual assertion),
  `docs/architecture/README.md`, `docs/architecture/L1_CONTRACT/versioning.md`,
  `docs/architecture/L1_CONTRACT/canon_schema.md`,
  `docs/architecture/L1_CONTRACT/exit_codes.md`,
  `docs/architecture/L3_IMPLEMENTATION/package_map.md`,
  `docs/architecture/L3_IMPLEMENTATION/command_manifest.md`,
  `docs/architecture/L3_IMPLEMENTATION/symbiont_protocol.md`,
  `src/myco/providers/__init__.py`, `src/myco/providers/README.md`.
  Corrections: seventeen → eighteen verbs, ten → eleven dimensions,
  seven → ten MCP hosts, v0.5.6 → v0.5.7 current-state markers
  (historical markers preserved).
- **`brief` verb rendering.** When the last `senesce` ran in
  `mode == "quick"`, `brief` annotates the summary that immune has
  not yet run in this session boundary — the next PreCompact or
  SessionStart-hunger will surface any findings. (Deferred
  implementation to v0.5.8; v0.5.7 ships the payload invariant
  but not the brief-UI change.)

### Fixed

- **Runtime contract violation** in `src/myco/cycle/senesce.py`:
  `Result.findings` is typed `tuple[Finding, ...]` but quick-mode
  payload passed `findings=[]` (list). Now `findings=()` — aligns
  with the declared type. Test updated accordingly.
- **25 mypy errors** (graph.py type narrowing via dedicated
  `_SkipType` singleton class, mb1 int coercion guard, ramify
  iter guard, graft.py `cls` variable shadow, mcp.py
  `Optional[Path]` → `Path | None`, unused `# type: ignore`
  directives). `python -m mypy src/myco` now passes with 0 errors.
- **230+ ruff findings** (F401 unused imports, UP035 deprecated
  `typing.X` imports → `collections.abc.X`, UP045
  `Optional[X]` → `X | None`, RUF100 unused `# noqa`, I001
  import ordering, RUF013 implicit-optional — plus 86 files
  reformatted via `ruff format`). `python -m ruff check` and
  `python -m ruff format --check` both pass clean.
- **9 inherited immune findings** from v0.5.6:
  - SE1 × 7 dangling code→doc refs — `fruit.py` / `molt.py` /
    `ramify.py` / `winnow.py` docstrings redirected from the
    never-created `L2_DOCTRINE/surface.md` to
    `L3_IMPLEMENTATION/command_manifest.md` (where governance-verbs
    section lives per v0.5.0 craft §R13); `fruit.py` + `winnow.py`
    `legacy_v0_3/docs/craft_protocol.md` references rewritten to
    break the phantom regex match;
    `mp1_no_provider_imports.py` auto-resolves via the new MP1
    craft doc.
  - SE2 × 2 orphan integrated notes deleted — they were v0.5.3
    dogfood-test artifacts with no inbound references and no
    semantic content (`"bug-fix-test"` literal body + three-word
    test marker); safe to remove per Audit A's per-finding
    analysis.
- **`tests/conftest.py` DeprecationWarning noise.** The
  `genesis_substrate` fixture imported `bootstrap` from the
  `myco.genesis` shim, firing a DeprecationWarning on every test
  run. Now imports from `myco.germination` (canonical); fixture
  name preserved for test readability.
- **`_canon.yaml::metrics.test_count`**: `283` → `609` (four
  versions stale — the field has not been updated since v0.4.0).

### Changed — version bumps

- `src/myco/__init__.py::__version__`: `0.5.6` → `0.5.7`
- `_canon.yaml::contract_version` + `synced_contract_version`:
  `v0.5.6` → `v0.5.7`
- `.claude-plugin/plugin.json::version`: `0.5.6` → `0.5.7`

### Migration note

No substrate-reader break. v0.5.6 canons parse under v0.5.7
unchanged. Every v0.5.6 CLI invocation still works; `myco senesce`
without `--quick` remains the v0.5.6 behavior bit-for-bit. The new
`--quick` flag on `senesce` is opt-in; callers that don't pass it
get the v0.5.6 behavior (full assimilate + immune --fix) exactly.
Every v0.5.x verb alias (`session-end`, `reflect`, `genesis`, …)
still resolves.

To upgrade a v0.5.6 substrate: `cd ~/myco && git pull && myco molt
--contract v0.5.7 && myco immune`. Downstream substrates that
installed the Myco Claude Code plugin pick up the new SessionEnd
hook automatically on next `/plugin update`.

### Verification commands

- `myco --version` → `myco 0.5.7`
- `myco immune --list` → 11 dimensions (unchanged from v0.5.6)
- `myco senesce --quick` on myco-self → ≤ 0.5 s, `mode: "quick"`,
  `immune.skipped: True`.
- `myco senesce` on myco-self → ≤ 2.0 s, `mode: "full"`, full
  assimilate + immune payload.
- `pytest` → 609 passed.

---

## [0.5.6] — 2026-04-17

**Doctrine realignment + mechanical LLM-boundary guard + bitter-
lesson note.** The v0.5.5 panoramic review surfaced 39 drift items
across L0-L3: 15 load-bearing contradictions (verb count, dimension
enumeration, package_map staleness), 11 stale cross-references,
13 missing anchors for v0.5.5 mechanisms (fixable dimensions,
`brief` verb, safe-fix discipline, graph-over-src, sporulate LLM
boundary, symbiont protocol, schema upgrader demo, hunger payload
shape, 10-host automation, etc.). v0.5.6 closes the whole gap +
mechanically enforces the "Agent calls LLM, substrate does not"
boundary that was previously doctrine-by-convention.

Governing three-round craft:
`docs/primordia/v0_5_6_doctrine_realignment_craft_2026-04-17.md`.

### Added

- **MP1 lint dimension (mechanical / HIGH / fixable=False).** New
  in v0.5.6. AST-based scan of every `.py` under `src/myco/`
  (excluding `providers/` whitelist, `__pycache__/`, hidden dirs)
  for imports matching a provider-SDK blacklist: `openai`,
  `anthropic`, `mistralai`, `cohere`, `voyageai`,
  `google.generativeai`, `google.genai`, `langchain`,
  `langchain_core`, `langchain_openai`, `langchain_anthropic`,
  `llama_index`, `llama_cpp`, `ollama`. Cross-checks against
  new canon field `system.no_llm_in_substrate`:
  - `true` (default) + violation → `HIGH` (contract violation,
    CI gates)
  - `false` + violation → `LOW` (opt-out declared, boundary
    disarmed)
  - clean → no finding
  `--fix` is intentionally disabled: deleting an LLM import is
  destructive; human review required. Bitter-lesson-aligned:
  keeps Myco compute-scale-invariant and provider-agnostic.
- **`system.no_llm_in_substrate` canon field.** New at v0.5.6.
  Default `true`. Graceful for v0.5.5 canons (reader uses
  `canon.system.get("no_llm_in_substrate", True)`). Declares the
  substrate's posture on L0 principle 1's Agent-calls-LLM
  boundary. Flipping to `false` is a contract-bumping event
  requiring `molt` + craft approval.
- **`src/myco/providers/` reserved package.** Empty escape hatch
  for future LLM-provider coupling. Path is whitelisted by MP1;
  any module placed here is exempt from the provider-import scan.
  Populating the package requires the `no_llm_in_substrate:
  false` toggle + a contract bump. README in the package declares
  the contract.
- **`L2_DOCTRINE/extensibility.md` — new doctrine page.** Cross-
  cutting L2 doc for the two orthogonal extension axes:
  per-substrate (`.myco/plugins/`) and per-host
  (`src/myco/symbionts/`). Scope boundaries, authoring verbs,
  audit verbs, enforcement dimensions all in one table. Cross-
  linked from L0 principle 5, L2 homeostasis.md, L3
  symbiont_protocol.md.
- **L0 principle 1 addendum** — carves the two declared exceptions
  (`brief` human window + Agent-calls-LLM boundary) inline in L0
  so every downstream reader sees them from the top.
- **L0 bitter-lesson appendix** — explicit acknowledgment that
  Myco's coordination surface (18 verbs + canon schema + 11 lint
  dimensions) is a live bet against Sutton's bitter lesson.
  Names the review cadence (every MAJOR re-audits), names the
  replacement trigger (if Agents can maintain 1M-file substrates
  without structured verbs, Myco must re-justify). Labeled as
  appendix to principles 1/3/4; not a sixth principle.

### Changed — doctrine realignment (34 audit items)

Every S1/S2/S3 finding from the v0.5.5 panoramic audit landed as
a concrete text correction:

- **`L0_VISION.md`** — principle 1 addendum, bitter-lesson
  appendix, biological-metaphor table annotations (Germination
  rename, Cycle row added), principle 5 extended with `src/**`
  graph coverage + two-axes cross-link.
- **`L1_CONTRACT/canon_schema.md`** — example dimension IDs
  replaced with real ones (M1/M2/M3/MF1/MF2/MP1/SH1/MB1/MB2/SE1/
  SE2); example subsystem `genesis:` → `germination:`; example
  version updated to v0.5.6; `no_llm_in_substrate` field added;
  `affected_dimensions: []` reflects v0.5.6 reality; runtime-
  state-exclusion list adds `.myco_state/graph.json`; demo-
  upgrader note added to rule 4; dangling `L4_SUBSTRATE/
  export_plan.md` reference removed.
- **`L1_CONTRACT/versioning.md`** — "clean reflect" → "clean
  assimilate (alias reflect still resolves)"; Current-state
  (v0.5.6) row added alongside v0.4.0 starting-point row.
- **`L1_CONTRACT/exit_codes.md`** — `DIMENSION_CATEGORY` table
  reference → `Dimension.category: ClassVar[Category]`
  explanation; skeleton-downgrade-now-empty paragraph rewritten.
- **`L2_DOCTRINE/genesis.md`** — M2-fix cross-link added to
  entry-point section.
- **`L2_DOCTRINE/ingestion.md`** — eat full v0.5.4+ signature
  (`--content`/`--path`/`--url`); hunger payload shape corrected
  to `{loaded, count_by_kind, errors, module}` with per-field
  meanings; brief cross-link added; traverse companion note.
- **`L2_DOCTRINE/digestion.md`** — sporulate output shape
  documented (`notes/distilled/d_<slug>.md` frontmatter +
  scaffolding body); MP1 cross-link.
- **`L2_DOCTRINE/circulation.md`** — graph API documented
  (`build_graph(use_cache)`, `persist_graph`,
  `load_persisted_graph`, `invalidate_graph_cache`); fingerprint
  formula (`sha256(canon_text) + sorted((path, mtime) for path in
  <root>/src/**/*.py)`); traverse payload fields (`src_node_count`,
  `cached`).
- **`L2_DOCTRINE/homeostasis.md`** — 11-dimension enumeration
  table (including MP1); fixable-dimension protocol (M2 + MB1 at
  v0.5.5); safe-fix discipline (4-rule doctrine: idempotent /
  narrow / non-destructive / write-surface-bounded); MP1
  paragraph; extensibility cross-link.
- **`L3_IMPLEMENTATION/command_manifest.md`** — Verb-inventory
  header updated to v0.5.6; 18-verb table (with `brief` row);
  governance-verbs section adds "Brief — the one carved human-
  facing exception"; winnow "five gates" → "six gates"
  (G6_template_boilerplate); hunger payload shape corrected.
- **`L3_IMPLEMENTATION/package_map.md`** — src tree refreshed:
  `install/`, `mcp/`, `providers/` (v0.5.6 NEW) added;
  `cycle/brief.py` listed; symbionts description updated to
  per-host framing with `symbiont_protocol.md` pointer; test
  layout uses `germination/` and adds `cycle/`; mapping matrix
  extended.
- **`L3_IMPLEMENTATION/migration_strategy.md`** — historical-note
  banner declaring v0.4.0 greenfield-plan status; `senesce`
  canonical name with `session-end` alias annotation.
- **`L3_IMPLEMENTATION/symbiont_protocol.md`** — 10-host
  automation inventory added; `myco.install.clients` adapter
  layer cross-link.
- **`docs/architecture/README.md`** — full rewrite to v0.5.6
  status; L0-L3 table refreshed with current file list.
- **`src/myco/surface/manifest.yaml`** — `immune --fix` arg
  `help` corrected from stale "no-op at B.7" to "Apply safe
  fixes where the dimension supports them (v0.5.5: M2 + MB1
  fixable; safe-fix discipline in L2 homeostasis.md)".

### Tests

+16 new (580 total, was 564): 12 MP1 tests (registration, clean
scan, detection per major provider, from-imports, nested
imports, relative-import exemption, providers/ whitelist,
__pycache__ skip, syntax-error tolerance, LOW-severity opt-out,
kernel-only scope) + 4 canon-field tests (default-true-on-missing,
explicit true/false, missing-system-block edge case).

### Migration note

No substrate-reader break. v0.5.5 canons parse under v0.5.6
unchanged: the new `system.no_llm_in_substrate` field is read via
`.get()` with default `True`, so v0.5.5 canons behave as
canonical-declared-true. Every v0.5.5 CLI invocation still works.
Every v0.5.x verb alias still resolves. The `contract_version`
bumps from `v0.5.5` to `v0.5.6` because the new canon field
shapes the contract surface (even though it's optional-with-
default); explicit declaration in fresh substrates is the new
norm.

To upgrade a v0.5.5 substrate: `cd ~/myco && git pull && myco
immune` — MP1 runs clean on a kernel that imports no provider
SDKs; if MP1 fires on your downstream substrate, review the
imports and decide whether to (a) remove them, (b) move them to
`src/myco/providers/` + molt the canon toggle, or (c) accept
the LOW opt-out finding as advisory.

### Verification commands

- `myco --version` → `myco 0.5.6`
- `myco immune --list` → 11 dimensions (was 10; MP1 added)
- `myco immune --dimensions MP1` → clean on myco-self
- `myco immune --explain MP1` → full class docstring with
  blacklist + canon-cross-check semantics
- `myco winnow docs/primordia/v0_5_6_doctrine_realignment_craft_
  2026-04-17.md` → verdict: pass
- Architecture greps (`local_plugins: {count, health}` etc.)
  return zero live matches per the doctrine alignment report.

---

## [0.5.5] — 2026-04-17

**Close every audit loose thread in a single release.** Every
post-release round since v0.4.1 surfaced the same pattern:
infrastructure in place, no concrete use. v0.5.5 ships eight
MAJORs merged from what the panoramic review flagged as v0.5.5 +
v0.5.6 candidates, delivering on each "staring at it for months"
item at once.

Governing three-round craft:
`docs/primordia/v0_5_5_close_audit_loose_threads_craft_2026-04-17.md`.

### Added

- **MAJOR-A — first fixable lint dimensions.** The `immune --fix`
  flag has been plumbed as a no-op since v0.4.0. v0.5.5 implements:
  - `Dimension.fix(ctx, finding) -> dict[str, Any]` — default no-op
    method on the base class.
  - `Dimension.fixable: ClassVar[bool]` — default False.
  - Kernel dispatch: when `fix=True`, iterate each dimension's
    findings; call `fix()` only for dimensions with
    `fixable=True`; record outcomes in `payload["fixes"]`; guard
    every fix target against `canon.system.write_surface.allowed`
    before dispatch (fixes outside the surface are rejected with
    `error: "outside write surface"`).
  - **M2 fixable** — creates the missing `entry_point` file
    (typically `MYCO.md`) from a minimal skeleton; idempotent.
  - **MB1 fixable** — triggers `reflect(ctx)` to assimilate the
    raw backlog; reports promotion count.
  - **Safe-fix discipline (new doctrine, four rules):** idempotent;
    narrow; never destructive; bounded by write_surface.
- **MAJOR-B — schema upgrader demo.** v0.5.1 shipped
  `schema_upgraders: dict` with chain-apply + cycle detection.
  v0.5.5 registers a synthetic `v0→v1` upgrader under key `"0"`
  (no real canon ever used that version) to prove the
  forward-compat seam works end-to-end. A canon with
  `schema_version: "0"` now parses **silently** through the
  upgrader; unknown versions without a registered upgrader still
  emit `UserWarning`.
- **MAJOR-C — sporulate doctrine boundary.** L2 `digestion.md`
  adds an explicit "sporulate does NOT call an LLM" rule. The
  substrate stays provider-agnostic. `sporulate` prepares the
  scaffolding (source selection + shared-tag extraction + first-
  line seeds); the Agent writes the synthesis prose separately.
  `sporulate.py` docstring + manifest summary rewritten to reflect
  this boundary.
- **MAJOR-D — symbiont protocol stub.** `src/myco/symbionts/` has
  been an empty package since v0.4.0; v0.5.5 writes an L3
  `symbiont_protocol.md` defining symbionts as **per-host
  Agent-sugar adapters** (Claude Code skill-generators, Cursor
  rule writers, VS Code task configurators). Orthogonal to
  `.myco/plugins/` (per-substrate). Package stays empty; the
  first concrete symbiont (Claude Code) ships in a later release.
  Pre-v0.5.5 "downstream-substrate adapters" framing superseded.
- **MAJOR-F — circulation graph covers `src/**`.** New
  `src/myco/circulation/graph_src.py` walks `src/**/*.py` via AST:
  extracts `from myco.X import Y` import edges (resolved to
  module paths) and docstring-based edges for `docs/...` path
  references. Stdlib/third-party imports and `__pycache__` are
  skipped. Syntax errors tolerated gracefully. `SE1` dangling-ref
  dimension now surfaces real code-to-doctrine dangling
  references on myco-self (6 on the v0.5.4 tree at ship time).
- **MAJOR-J — graph persistence.**
  `.myco_state/graph.json` now caches the mycelium graph with a
  `(canon-sha256 + sorted src mtime list)` fingerprint. Cold
  build full; warm build reads the cache (~6x speedup on myco-
  self). `invalidate_graph_cache(substrate)` + `build_graph(ctx,
  use_cache=False)` + `persist_graph(...)` / `load_persisted_graph(...)`.
  `traverse`'s payload gains `src_node_count` + `cached` fields.
- **MAJOR-G — `myco brief` verb.** L0 principle 1's one explicit
  carved exception: a human-facing verb. Produces a stable-section
  markdown rollup (Identity / Hunger / Immune / Notes / Primordia /
  Local plugins / Suggested next) for a human review moment.
  Does not replace any agent-side verb. `--format markdown`
  (default) or `--format json`. New handler at
  `myco.cycle.brief:run`.
- **MAJOR-I — 3 new automated MCP hosts.** `myco-install host`
  now covers:
  - **gemini-cli** — writes `~/.gemini/settings.json` (JSON
    `mcpServers` family).
  - **codex-cli** — block-level regex surgery on
    `~/.codex/config.toml` (`[mcp_servers.myco]` TOML section,
    preserves sibling tables and comments; validates parse on
    Python 3.11+ via stdlib `tomllib`).
  - **goose** — writes `~/.config/goose/config.yaml` with the
    `extensions.myco` key (YAML, not JSON).
  - Automated host count: 7 → **10**.

### Doctrine updates

- `docs/architecture/L2_DOCTRINE/digestion.md` — sporulate
  boundary written into the "Digestion does not" list.
- `docs/architecture/L2_DOCTRINE/circulation.md` — graph coverage
  + cache layer documented.
- `docs/architecture/L3_IMPLEMENTATION/symbiont_protocol.md` —
  new L3 stub for MAJOR-D.
- `docs/INSTALL.md` — 3 new automated hosts in the section-1
  table; automation notes next to manual Gemini / Codex / Goose
  snippets.
- `docs/contract_changelog.md` — v0.5.5 section.

### Tests

+60 new tests (543 → ~600 target). Breakdown:
- MAJOR-A: +11 (fix dispatch + M2 + MB1 + safe-fix guards)
- MAJOR-B: +4 (schema upgrader demo)
- MAJOR-F+J: +22 (graph-over-src + persistence)
- MAJOR-G: +8 (brief verb structure + suggestions)
- MAJOR-I: +10 (Gemini / Codex TOML / Goose YAML)

### Migration note

No action required. Every v0.5.4 CLI invocation still works. The
v0.5.x verb aliases continue to resolve. The schema upgrader
demo is under version `"0"` (never a real shipped version) so no
production substrate is affected. The `.myco_state/graph.json`
cache is created lazily on first `traverse` / `sense` / `immune`
that builds the graph; deleting it is always safe (rebuild
happens on next call).

---

## [0.5.4] — 2026-04-17

Dogfood-session patch release. Yanjun asked the Agent to run Myco
on the Myco repo as an end-to-end smoke test. Seven bugs surfaced;
all seven are fixed in this release. No break from v0.5.3 —
substrate readers and handlers are unchanged.

### Fixed

- **Bug #1 — `myco --version` / `-V`**. The CLI lacked a version
  flag. Running `myco --version` errored with "VERB required". Now
  the flag prints `myco 0.5.4` and exits 0, matching standard CLI
  convention. (`src/myco/surface/cli.py`)
- **Bug #3 — list flags accept natural multi-value form**. Before:
  `myco eat --content X --tags a b c` errored with "unrecognized
  arguments: b c" because `action="append"` only absorbs one value
  per flag. Now: `nargs="*"` + `action="extend"` means `--tags a
  b c` works naturally and the legacy repeated form `--tags a
  --tags b` still works. (`src/myco/surface/cli.py`)
- **Bug #6 — subparser dest collision (CRITICAL)**. Before:
  `myco-install` parser used `dest="verb"` for its subcommand
  selector, and `ramify` has a `--verb <name>` argument. Running
  `myco ramify --dimension X1 --category mechanical --severity low`
  crashed with "unknown command: None" because the `--verb` flag's
  default None overwrote `ns.verb` (which also held the subcommand
  name). Fix: rename the subparsers destination to `_subcmd`
  (private, non-colliding). Every `ramify --dimension / --adapter`
  invocation was previously broken. (`src/myco/surface/cli.py`)
- **Bug #7 — substrate-local plugin template (CRITICAL)**. Before:
  `myco ramify --dimension LOCAL1` in a downstream substrate wrote
  a correct `local1.py` but ALSO generated a broken
  `.myco/plugins/dimensions/__init__.py` whose `register_all()`
  contained a literal `{{__name__}}` token. As Python that f-string
  escape resolved to `{__name__}`, making `importlib.import_module`
  try to import a module literally named `{__name__}.local1`. The
  ModuleNotFoundError was silently swallowed by the outer
  `plugins/__init__.py`'s best-effort try/except. Result: every
  substrate-local dimension registered via `ramify` was invisible
  to `default_registry()`, `graft --list`, and `immune`. Fix:
  replace `{{__name__}}` with `{__name__}` in the ramify template
  strings (they're written verbatim, not through `.format`). Also
  tightened the register loop to check `issubclass(obj, Dimension)`
  so only real dimension classes register. (`src/myco/cycle/ramify.py`)
- **Bug #2 — `hunger` payload `local_plugins.count_by_kind`**. The
  v0.5.3 CHANGELOG promised `{loaded, count_by_kind, errors,
  module}` but the implementation shipped a flat `count` integer.
  Now the payload carries both a flat `count` (backward-compat
  alias for the sum) AND a `count_by_kind: {dimension, adapter,
  schema_upgrader, overlay_verb}` dict. (`src/myco/ingestion/hunger.py`)
- **Bug #5 — `--json` output surfaces findings**. Before: the
  `findings` tuple on `Result` was dropped from the JSON envelope;
  agents that saw `exit_code: 1` had to issue a follow-up call to
  learn which dimension at what severity on which path had fired.
  Now every `--json` response carries a top-level `findings: [...]`
  list with `dimension_id / category / severity / message / path /
  line / fixable` per finding. Empty list when the handler produced
  none. (`src/myco/surface/cli.py`)
- **Observation #4 — `winnow` G6_template_boilerplate gate**. A
  freshly-`fruit`-ed craft skeleton (all `TBD` / `(Fill in.)` /
  template instructional prose) used to pass every shape gate by
  construction, defeating winnow's purpose as a "did the agent
  actually do the craft work" signal. New G6 gate fires when the
  body is >40% fruit-template fingerprints. All three existing
  v0.5.x craft records still pass winnow (zero violations on v0.5.0
  / v0.5.2 / v0.5.3 crafts). (`src/myco/cycle/winnow.py`)

### Tests

- `tests/unit/surface/test_cli_v0_5_4_fixes.py` — 7 regression
  tests pinning `--version` / `-V`, `--tags a b c`, subparser
  collision, `ramify --dimension` E2E, `--json` findings envelope.
- `tests/unit/meta/test_ramify_template_integrity.py` — 2 tests
  pinning the fixed template shape + end-to-end
  `Substrate.load()`-auto-imports-and-registers flow.
- `tests/unit/ingestion/test_hunger_count_by_kind.py` — 1 test
  pinning the new payload shape.
- `tests/unit/meta/test_winnow_g6.py` — 2 tests: G6 trips on a
  fresh skeleton, passes on a filled-in craft.

Test total: **499 passed** (was 486 at v0.5.3; +12 new regression
tests, +1 LOCAL1 registration surfaced via graft).

### Migration note

No action required. Every v0.5.3 CLI invocation still works. The
`local_plugins.count` field remains in the hunger payload for
backward compat; `count_by_kind` is additive. The G6 gate is
additive to winnow (existing valid crafts continue to pass).

---

## [0.5.3] — 2026-04-17

Fungal vocabulary migration + Agent-First framing fix + substrate-
local plugin loading. Three concerns merged into one MINOR release
because they emerged from the same post-v0.5.2 audit and share a
governing three-round craft
(`docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md`).
**No break from v0.5.2**: every prior CLI invocation, every prior
MCP tool name, every prior Python import path keeps working.
Deprecation warnings fire once per alias per process; alias removal
waits for v1.0.0.

### Added

- **Nine renamed verbs, one new verb, seventeen total.** The
  canonical / deprecated-alias pairs are:
  `germinate` / `genesis`, `assimilate` / `reflect`, `sporulate` /
  `distill`, `traverse` / `perfuse`, `senesce` / `session-end`,
  `fruit` / `craft`, `molt` / `bump`, `winnow` / `evolve`,
  `ramify` / `scaffold`. `graft` is new at v0.5.3. Old names
  register as both CLI aliases and MCP tool aliases
  (`myco_genesis`, `myco_craft`, etc.) so cached v0.5.2
  invocations resolve unchanged. `hunger`, `eat`, `sense`,
  `forage`, `digest`, `propagate`, `immune` kept their names —
  each already maps cleanly to a fungal-biology term.
- **Two renamed packages, two shim packages.** `src/myco/genesis/`
  became `src/myco/germination/`; `src/myco/meta/` became
  `src/myco/cycle/`. Shim packages live at the old paths; their
  `__init__.py` re-exports every public name from the new
  location and emits a `DeprecationWarning` on import.
  `from myco.meta import session_end_run` and
  `from myco.genesis import run_cli` still work.
- **Substrate-local plugin loading.**
  `<root>/.myco/plugins/__init__.py` auto-imports on
  `Substrate.load()` under an isolated module name; import errors
  are captured on `Substrate.local_plugin_errors` for MF2 to
  surface rather than crashing boot.
  `load_manifest_with_overlay(substrate_root)` merges
  `<root>/.myco/manifest_overlay.yaml` into the packaged manifest
  at `build_context()` time; overlay verbs that name-collide with
  packaged verbs are rejected. `register_external_dimension(cls)`
  in `myco.homeostasis.registry` is the public API substrate-local
  plugins call at import time.
- **New verb `graft`** (`--list | --validate | --explain <name>`)
  — the Agent's introspection surface for substrate-local plugins.
  Biology: hyphal anastomosis is the fusion of foreign hyphae onto
  the mycelial network. Authoring happens elsewhere; `graft` is
  read-only.
- **Extended `ramify` modes** — beyond the v0.5.2 `--verb <name>`
  mode, `ramify` now accepts `--dimension <ID> --category <cat>
  --severity <sev>` (scaffold a lint dimension),
  `--adapter <name> --extensions <ext,ext>` (scaffold an ingestion
  adapter), and `--substrate-local` (write under
  `<substrate>/.myco/plugins/` instead of `src/myco/`; auto-on
  when `canon.identity.substrate_id != "myco-self"` OR
  `<substrate_root>/src/myco/` does not exist).
- **`MF2` lint dimension** (mechanical / HIGH) — fires on broken
  `.myco/plugins/` shape, missing `__init__.py`, manifest-overlay
  YAML errors, import-time registration failures, or duplicate
  verb names across the overlay and the packaged manifest. Ten
  built-in dimensions total (was nine).
- **`hunger` payload `local_plugins` block** — every `hunger`
  call now reports `{loaded, count_by_kind, errors, module}` so
  the Agent sees on every boot what has grafted onto the
  substrate. Invisible magic stays audible.

### Changed

- **Trilingual READMEs rewritten.** Verb references across
  `README.md`, `README_zh.md`, `README_ja.md` updated to canonical
  fungal names with the old alias shown in parentheses inside the
  verb table. A `v0.5.3 — fungal vocabulary migration` callout
  appears under the positioning paragraph. New `Substrate-local
  plugins` subsection explains the `.myco/plugins/` path, the
  `ramify --dimension` authoring flow, and the `graft --list`
  introspection. Daily-flow rewritten as
  `hunger → eat → assimilate → digest → sporulate → traverse →
  propagate`. Editable-by-default install flow preserved from
  v0.5.2. Zero em-dashes. Line count preserved within ~1%.
- **Agent-First framing fix.** Every sentence in READMEs / MYCO.md
  / INSTALL.md / L1 / L2 / L3 doctrine that described a verb
  invocation now names the Agent as the grammatical subject. L0
  principle 1 (只为 Agent) says the Agent invokes verbs; humans
  speak natural language.
- **`docs/INSTALL.md`** — section 6 `Substrate-local plugins` added
  (covering `.myco/plugins/`, `manifest_overlay.yaml`, the extended
  `ramify` modes, and `graft` introspection). Verb references in
  per-host snippets and troubleshooting section updated to
  canonical names or clarified as aliases. Section 0 `--configure`
  note added.
- **L1 / L2 / L3 doctrine pages** — `L1/protocol.md` R2 now names
  `assimilate` + `senesce` (aliases noted). `L1/canon_schema.md`
  example comment swapped `reflect` → `assimilate`.
  `L2/digestion.md`, `L2/circulation.md`, `L2/genesis.md` carry
  headers noting the v0.5.3 rename; body verb references updated.
  `L2/homeostasis.md` documents `MF2` + `graft` cross-reference.
  `L3/command_manifest.md` rebuilt the seventeen-verb inventory
  table with alias column. `L3/package_map.md` updated filesystem
  tree (`germination/`, `cycle/`, shim `genesis/` + `meta/`, new
  `.myco/plugins/` layout) plus the mapping matrix.
- **`docs/contract_changelog.md`** — new `v0.5.3` top section.
- **`MYCO.md`** — seventeen-verb list with alias annotations;
  Agent-First framing pass; substrate-local plugins subsection
  added; `senesce` (was `session-end`) named in the
  finish-a-session block.
- **`hooks/hooks.json`** — PreCompact hook command changed from
  `session-end` to the canonical `senesce`. Description block
  updated. `.claude/settings.local.json` PreCompact hook and
  permissions allowlist updated to match; the `session-end` entry
  remains for backward compatibility with cached sessions.
- **`.claude-plugin/plugin.json`** — `version` at `0.5.3`;
  description mentions fungal vocabulary, substrate-local plugins,
  seventeen verbs.
- **`__version__`, `_canon.yaml::contract_version`,
  `_canon.yaml::synced_contract_version`,
  `src/myco/surface/manifest.yaml`** all at `0.5.3` / `v0.5.3`
  (source-of-truth files; already landed via the v0.5.3 code
  work, not touched in this doc pass).

### Migration note

**Every v0.5.x invocation still works.** The CLI emits one
`DeprecationWarning` per alias per process (e.g. using
`myco reflect` instead of `myco assimilate`); MCP tool calls to
`myco_reflect` resolve to the same handler as `myco_assimilate`;
Python imports like `from myco.meta import session_end_run` and
`from myco.genesis import run_cli` still resolve through shim
packages that emit a `DeprecationWarning` on import. Alias
removal is scheduled for **v1.0.0** — migrate at your own pace
through the entire 0.x line.

---

## [0.5.2] — 2026-04-17

Editable-by-default install model. Closes the architectural mismatch
Yanjun flagged in the v0.5.1 post-release review: the "Stable kernel,
mutable substrate" framing (introduced at v0.4.1) contradicted L0
principles 3 and 4 (永恒进化 / 永恒迭代). A read-only `site-packages`
install freezes the kernel code — but Myco's own source tree *is* a
substrate, and the kernel is its innermost ring. Locking that ring
meant the agent couldn't scaffold a new verb with a real path
(v0.5 `scaffold` writes to `src/myco/`, read-only in the wrong
install model), couldn't register a substrate-local lint rule
without publishing a separate PyPI package, couldn't fix a kernel
bug without a release.

Governing craft:
`docs/primordia/v0_5_2_editable_default_craft_2026-04-17.md`.

### Added

- **`myco-install fresh [TARGET]`** — the new primary install
  path. Subcommand of `myco-install`. Clones Myco's source to
  `TARGET` (default `~/myco`), runs `pip install -e` on it in the
  current Python environment, verifies via `python -m myco --help`,
  and optionally configures one or more MCP hosts in the same
  step (`--configure claude-code cursor windsurf`). Supports
  `--repo` (override clone source), `--branch` / `--depth` (git
  clone options), `--extras` (e.g. `mcp,dev,adapters`), `--force`
  (overwrite non-empty target), `--dry-run` (preview every step
  without side effects), `--yes` (non-interactive). Refuses a
  non-empty target unless `--force`. Requires `git` on PATH and
  prints a clear install-git-first message if absent.
- **`myco-install host <client>`** — explicit subcommand for the
  existing per-host MCP config writers. Legacy
  `myco-install <client>` (v0.4/v0.5 shape with the client as
  first positional) still works; a CLI-level sniff auto-routes it
  to `host <client>`.
- **`tests/unit/install/test_fresh.py`** — 11 tests covering
  dry-run rendering, non-empty-target refusal, unknown-client
  rejection, `--configure` path, CLI subparser routing,
  legacy-sniff compatibility, and git-missing error message.

### Changed

- **Trilingual READMEs rewritten (en / zh / ja).** The paragraph
  *"Stable kernel, mutable substrate. `pip install` locks the
  kernel at a released version."* is replaced with *"Editable by
  default. The kernel IS substrate."* Quick Start section leads
  with `pipx run --spec 'myco[mcp]' myco-install fresh ~/myco`.
  New "Non-evolving install" subsection documents the plain
  `pip install` path for library consumers, CI, and vendoring.
  Line count preserved; each language pair kept in lockstep.
- **`docs/INSTALL.md` restructured.** New section 0 ("Primary
  path — `myco-install fresh`") with the full flag table and
  upgrade flow (`git pull`, not `pip install --upgrade`). Existing
  per-host matrix moved to section 1 and renamed "Per-host MCP
  config". Table cells updated to the canonical
  `myco-install host <client>` form; legacy short form is
  documented as backward-compatible but no longer primary.
- **`src/myco/install/__init__.py` restructured** to use
  argparse subparsers (`fresh`, `host`). Entry point still
  `myco.install:main`; `python -m myco.install` also still
  works. No breaking change to downstream callers thanks to the
  legacy-sniff on the first positional arg.
- **`__version__`, `.claude-plugin/plugin.json::version`,
  `_canon.yaml::contract_version`, `_canon.yaml::
  synced_contract_version`** → `0.5.2` / `v0.5.2`.
- **`docs/contract_changelog.md`** — new `## v0.5.2 — 2026-04-17
  — Editable-by-default install model` section.

### Doctrine note

No L0/L1/L2 text was found that hardcoded "pip install locks the
kernel" as a rule; the problematic phrasing was only in READMEs +
CHANGELOG v0.4.1 entry. The CHANGELOG v0.4.1 entry is preserved
as historical audit record; the v0.5.2 entry supersedes the
framing going forward.

---

## [0.5.1] — 2026-04-17

> *(PyPI-release-metadata note: the `myco-0.5.0` wheel filename
> was burned on a prior upload to the index and cannot be reused
> per PyPI's filename-reuse policy. `0.5.1` is the first MINOR-
> release wheel on PyPI carrying the full "永恒进化 delivered in
> code" content below. No code or doctrine difference vs what
> would have been 0.5.0.)*

Closes all five MAJOR gaps from the v0.4.1 post-release audit
(`docs/primordia/v0_4_1_audit_craft_2026-04-15.md`). The README's
"the substrate changes shape with the work" (L0 principle 3,
永恒进化) and "you never migrate again" promises are now mechanically
backed, not aspirational prose. The governing three-round craft is
`docs/primordia/v0_5_0_major_6_10_craft_2026-04-17.md`.

### Added

- **MAJOR 6 — Dimension registration via entry-points.**
  `pyproject.toml` now declares every built-in lint dimension under
  `[project.entry-points."myco.dimensions"]`. Third-party substrates
  register their own dimensions the same way — no fork of Myco, no
  source edit, just a single row in their own `pyproject.toml`.
  Discovery is driven by
  `importlib.metadata.entry_points(group="myco.dimensions")`; the
  hardcoded `_BUILT_IN` tuple (renamed from `ALL`) is a dev-checkout
  fallback that fires a `DeprecationWarning` when used. Broken
  third-party entry-points are skipped with a `UserWarning` rather
  than killing the kernel.
- **`myco immune --list`** enumerates every registered dimension
  (id / category / default_severity / one-line summary) without
  running any of them. Output is sorted by id; safe on any
  substrate.
- **`myco immune --explain <dim>`** prints the dimension's class
  docstring as prose. `--list` and `--explain` are mutually
  exclusive; passing both raises `UsageError`.
- **MAJOR 7 — `MF1` lint dimension.** Mechanical / HIGH: every
  `canon.subsystems.<name>.package` path must resolve to an
  existing directory under substrate root. Silent when a subsystem
  entry has no `package:` field (documentation-only subsystems stay
  valid). The first cross-check between the canon's `subsystems`
  block and the actual package layout.
- **MAJOR 8 — Forward-compatible canon reader.** An unknown
  `schema_version` in `_canon.yaml` now emits a `UserWarning` and
  proceeds best-effort instead of raising `CanonSchemaError`. A new
  module-level registry `myco.core.canon.schema_upgraders:
  dict[str, Callable]` is the seam for future v1→v2 in-code
  upgraders (chain-applied; cycle-detected). Empty at v0.5 — schema
  v1 is still the only shipped shape. This is the single code-level
  change that makes "you never migrate again" a load-bearing claim:
  an older kernel reading a newer canon warns rather than halting.
- **MAJOR 9 — Governance as verbs.** Three new agent-callable
  CLI/MCP verbs; previously all three were Markdown-social
  conventions:
  - **`myco craft --topic <phrase>`** scaffolds a dated primordia
    doc at `docs/primordia/<slug>_craft_<date>.md` from a three-round
    template (claim / self-rebuttal / revision / counter-rebuttal /
    reflection, with YAML frontmatter carrying `type`, `slug`,
    `kind`, `date`, `rounds`, `status`). Refuses to overwrite.
  - **`myco bump --contract <v>`** is the first code path in Myco
    that mutates a post-genesis `_canon.yaml`. Regex-patches the
    top-level `contract_version:` and `synced_contract_version:`
    fields, re-reads via `load_canon` to validate, then prepends a
    new section to `docs/contract_changelog.md`. Restores the
    original canon text on any post-write parse error. `--dry-run`
    previews without writing.
  - **`myco evolve --proposal <path>`** runs five shape gates on a
    craft or proposal doc (frontmatter `type`, title, body size
    bounds, round-marker count ≥ 2, per-round body ≥ 150 chars).
    Returns `exit 0` with `verdict: pass` on clean, `exit 1` with
    `violations: [{gate, message}]` on fail. Read-only; does not
    mutate.
- **MAJOR 10 — Handler auto-scaffolding.**
  **`myco scaffold --verb <name>`** generates a minimal handler
  stub at the filesystem path derived from the manifest's
  `handler:` string (not the `subsystem:` tag). The stub returns a
  well-formed `Result(exit_code=0, payload={"stub": True, "verb":
  <name>})` and emits a `DeprecationWarning` on every invocation,
  so unfinished verbs are neither silent successes nor crashes.
  Refuses to act on a verb the manifest does not declare (manifest
  stays SSoT); refuses to overwrite unless `--force` is passed.
- **`myco.meta/` package.** What was a single-file
  `src/myco/meta.py` in v0.4 is now a package with five submodules
  (`session_end.py`, `craft.py`, `bump.py`, `evolve.py`,
  `scaffold.py`) plus a `templates/` subdirectory holding the
  craft-doc template. `meta/__init__.py` re-exports
  `session_end_run` so any out-of-tree caller that imported from
  the old module path keeps working unchanged.
- **Sixteen verbs.** v0.4 shipped twelve; v0.5 adds `craft`, `bump`,
  `evolve`, `scaffold`.
- **Nine lint dimensions.** v0.4 shipped eight; v0.5 adds `MF1`.

### Changed

- **`session-end` manifest handler path.** Moved from
  `myco.meta:session_end_run` to `myco.meta.session_end:run` as a
  consequence of the `meta.py → meta/` package migration. The
  backward-compat re-export in `meta/__init__.py` means imports
  like `from myco.meta import session_end_run` still work.
- **`test_scaffold.py::PACKAGES`** switched from a hardcoded
  14-entry list to `pkgutil.walk_packages(myco.__path__)`. Adding
  a new subsystem package no longer forces a test edit. The
  module's prose header also corrected — it previously claimed
  "eight-subsystem layout" against a 14-entry list.
- **Genesis canon template no longer claims `package:` paths.**
  A fresh substrate starts with `subsystems.<name>.doc` only;
  `package:` is opt-in for substrates whose subsystems correspond
  to code packages under the substrate root (e.g. Myco's own
  `_canon.yaml`). Prevents `MF1` from firing on every fresh-genesis
  fixture.
- **Doctrine updates bundled with the release.**
  - `docs/architecture/L1_CONTRACT/canon_schema.md` rule 4 — text
    moved from "refuses to read unknown `schema_version`" to
    "warns and preserves, with `schema_upgraders` as the forward-
    compat seam".
  - `docs/architecture/L2_DOCTRINE/homeostasis.md` — entry-points-
    driven registration, `MF1` in the inventory, `--list` /
    `--explain` surface documented, dimension-adding workflow
    updated.
  - `docs/architecture/L3_IMPLEMENTATION/command_manifest.md` —
    governance-verbs section added, 16-verb inventory table.
  - `docs/architecture/L3_IMPLEMENTATION/package_map.md` — `meta/`
    as a package, mapping matrix updated.

---

## [0.4.4] — 2026-04-16

Hotfix for hook-invocation failures when a stale `myco` exists on
PATH (Anaconda, older venvs, etc.) or when the console-script
Scripts dir is not on PATH at all.

### Fixed

- **`hooks/hooks.json` and `.claude/settings.local.json`** now
  invoke `python -m myco --json ...` instead of bare `myco --json
  ...`. The bare form assumes the currently-installed myco's
  Scripts dir is on PATH; in practice any pre-v0.4 myco on PATH
  (common with Anaconda or system Python) will shadow the target
  version and fail because v0.3 CLIs do not accept
  `--project-dir`. Using `python -m myco` dispatches through
  `sys.path`, which finds the correct package regardless of
  Scripts-dir PATH state.
- **Regression test** `test_hooks_use_python_m_myco` in
  `tests/integration/test_plugin_bundle.py` pins the new convention.

### User action required (if hit on <=0.4.3)

```bash
pip install --upgrade 'myco[mcp]'
# Re-install the plugin / re-run myco-install to pick up the new
# hook command form, or hand-edit your existing hook config files.
```

---

## [0.4.3] — 2026-04-16

Hotfix for the most common MCP install failure: `spawn ENOENT`.

### Fixed

- **`myco-install` now writes the absolute Python interpreter path**
  (`sys.executable` plus `-m myco.mcp`) instead of the bare
  `mcp-server-myco` console script. GUI MCP hosts (Claude Desktop,
  Cursor, Windsurf) do not inherit the user's shell PATH, so the
  console script is invisible to them. The absolute-path form works
  regardless of PATH, venv, or `python`/`python3` aliasing.
- **`docs/INSTALL.md` adds a troubleshooting section** covering the
  three most common MCP failures: ENOENT, missing `[mcp]` extra,
  and "server disconnected" timeout. Manual-config users get the
  absolute-path form alongside the bare console-script form.

---

## [0.4.2] — 2026-04-16

Closes the five BLOCKER gaps surfaced by the v0.4.1 post-release
audit (docs/primordia/v0_4_1_audit_craft_2026-04-15.md). The README
promise "devours code repositories, framework documentation,
datasets, papers" is now mechanically honored by the code, not just
the prose.

### Added

- **Ingestion adapter protocol** (Stage F.1). New
  `src/myco/ingestion/adapters/` subpackage with an `Adapter` ABC,
  `IngestResult` dataclass, and a global registry. Built-in adapters
  auto-register at import time; external adapters call `register()`.
- **Six built-in adapters** (Stage F.1):
  - `text-file`: any UTF-8 file including `.py`, `.js`, `.ts`, `.go`,
    `.rs`, `.rb`, `.sh`, `.c`, `.cpp`, `.java`, `.kt`, `.swift`,
    `.lua`, `.r`, `.sql`, `.toml`, `.ini`, `.cfg`, `.xml`, `.css`,
    `.md`, `.yaml`, `.json`, `.log`, Makefiles, Dockerfiles, and
    60+ more extensions. Binary detection via null-byte heuristic.
  - `code-repo`: walks a directory, delegates per file to `text-file`,
    respects `.gitignore` if `pathspec` is installed. Capped at 500
    files. Provenance carries `<repo>/<relative-path>`.
  - `url`: HTTP GET via `httpx`, dispatches by Content-Type to
    `html`/`pdf`/`json`/plain-text. Requires `[adapters]` extras.
  - `pdf`: local `.pdf` via `pypdf`, one `IngestResult` per page
    with page numbers. Requires `[adapters]` extras.
  - `html`: local `.html` via `beautifulsoup4`, strips nav/footer/
    script/style. Requires `[adapters]` extras.
  - `tabular`: `.csv`, `.tsv`, `.json`, `.jsonl` via stdlib
    `csv`/`json`. Produces a summary (columns, row count, preview
    rows). No optional deps needed.
- **`eat --path` and `eat --url`** (Stage F.1). The `eat` verb now
  accepts `--path <file-or-dir>` or `--url <https://...>` in
  addition to `--content`. Each dispatches through the adapter
  registry and produces one note per `IngestResult`. Provenance is
  automatically set from the adapter rather than defaulting to
  `"agent"`.
- **`[adapters]` optional-dependency target** (Stage F.1).
  `pip install 'myco[adapters]'` pulls `httpx>=0.27`,
  `pypdf>=4.0`, `beautifulsoup4>=4.12`. Stdlib-only adapters
  (text-file, code-repo, tabular) work without this target.

### Changed

- **`forage` no longer silently drops files** (Stage F.1). The
  hardcoded 7-extension whitelist (`_INGESTIBLE_SUFFIXES`) is
  replaced by the adapter registry: a file is listed if any adapter
  claims it. Unreachable files are counted in a new `skipped` field
  in the payload so users know the listing is intentionally
  narrowed, not silently lossy. `forage --path ./src/myco` now
  returns 66 files (was 1 in v0.4.1).
- **`distill` derives a synthesis seed** (Stage F.1). The stub
  proposal now includes shared-tag theme analysis and first-line
  claim extraction from all source notes (was: filename listing
  only). Also fixes the empty-list CLI bug where `--sources` with
  no arguments was coerced to `()` instead of `None`, skipping the
  "use all integrated notes" path and raising `ContractError`.

---

## [0.4.1] — 2026-04-15

First maintenance release after the v0.4.0 greenfield rewrite.
Ships the four public promises (`[mcp]` extras, `python -m myco.mcp`
launcher, official plugin bundle, `CONTRIBUTING.md`) plus two
cross-platform passes that turn "works in Claude Code" into "works
across every active MCP host on the 2026-04 landscape," plus a
narrative rewrite that positions Myco as the substrate that
ingests other frameworks rather than yet another framework that
gets replaced.

### Added

- **`[mcp]` optional-dependency target** (Stage D.1). `pyproject.toml`
  now declares `mcp = ["mcp>=1.2"]` so `pip install "myco[mcp]"` pulls
  the Model Context Protocol SDK alongside the package. Lower bound of
  1.2 covers `FastMCP.run()`, the synchronous stdio entry point that
  `python -m myco.mcp` relies on; the rest of the 1.x line is accepted
  because the low-level API has been stable across all 1.x releases.
- **`python -m myco.mcp` standalone launcher** (Stage D.2). New
  `src/myco/mcp/` subpackage with an `__init__.py` that re-exports
  `build_server` and a `main()` entry, plus a thin `__main__.py` that
  wires argparse to `FastMCP.run`. Three transports are selectable
  (`--transport {stdio, sse, streamable-http}`, default `stdio`). When
  the MCP SDK is not installed the launcher fails loud with a single
  sentence telling the user to `pip install 'myco[mcp]'` and a POSIX
  exit code of 2 — never a raw `ImportError` traceback. Library users
  who embed the server in their own process can import the shared
  `build_server` directly.
- **Official Claude-Code / Cowork plugin bundle** (Stage D.3). The
  repo root now ships a full plugin manifest tree alongside the
  Python source: `.claude-plugin/plugin.json`, a one-plugin
  `marketplace.json`, a `.mcp.json` pointing at `python -m myco.mcp`,
  a `hooks/hooks.json` wrapping SessionStart → `hunger` and
  PreCompact → `session-end`, and two slash skills under `skills/`
  (`/myco:hunger`, `/myco:session-end`). Users install with:

        /plugin marketplace add Battam1111/Myco
        /plugin install myco@myco

  The plugin tree coexists with the project's own `.claude/` folder;
  the two do not conflict because `.claude/` is the dogfooding config
  for the Myco repo itself while `.claude-plugin/` + root-level files
  are the distribution artifact.
- **Plugin-bundle structural tests** (Stage D.3). A new
  `tests/integration/test_plugin_bundle.py` validates the manifest
  shape, version-alignment with `myco.__version__`, hooks wiring, and
  skill-frontmatter completeness so a malformed plugin cannot ship
  silently.
- **Write-surface extended** (Stage D.3). `_canon.yaml` now whitelists
  `.claude-plugin/**`, `.mcp.json`, `hooks/**`, and `skills/**` so
  future plugin-file edits stay within R6 without a doctrine bump.
- **Trilingual README install flow updated** (Stage D.3). The English,
  Chinese, and Japanese READMEs now document the plugin install path
  alongside the manual-copy fallback, and the "ships in v0.4.1"
  forward-looking paragraphs are replaced with current-state prose.
- **`CONTRIBUTING.md`** (Stage D.4). Root-level contributor guide,
  roughly 1100 words. Sections: welcome (dual human + agent
  audience), before-you-start, dev environment, daily loop, the
  top-down L0–L3 rule, the three-round craft convention, what agents
  should do differently, what not to touch without discussion, PR
  checklist, AI-assisted contributions, bug reports, internal commit
  style (optional for external contributors), governance, code of
  conduct. The READMEs' `*(v0.4.1)*` placeholder marker on the
  `CONTRIBUTING.md` link is removed now that the file exists.
- **`mcp-server-myco` console script** (Stage D.5). `pyproject.toml`
  now declares a second entry point alongside `myco`, following the
  community `mcp-server-<name>` convention. Every MCP host config
  (Cursor, Windsurf, Zed, Codex, Gemini, Continue, Claude Desktop,
  LangChain / CrewAI / DSPy) can now just point at
  `command: "mcp-server-myco"` without having to reason about
  `python` vs `python3` aliasing or which venv the host will spawn.
  Usable via `pipx install 'myco[mcp]'` or
  `uvx mcp-server-myco` for zero-venv install.
- **Cross-platform install matrix** (Stage D.5). Trilingual READMEs
  now carry an eight-row table covering every MCP-supporting host
  on the 2026-04 landscape — each row is the exact config path and
  the exact line to paste. Aider is flagged as awaiting upstream MCP
  support (aider-ai/aider #4506).
- **`substrate_pulse` sidecar + initialization instructions**
  (Stage D.5). `myco.surface.mcp.build_server` now attaches a
  `substrate_pulse` field to every MCP tool response (current
  `substrate_id`, `contract_version`, and a rule hint that escalates
  from R1 → R3 once `myco_hunger` has fired), and populates the
  FastMCP `instructions` block with a compact R1–R7 summary linking
  to `docs/architecture/L1_CONTRACT/protocol.md`. This is the
  cross-platform analogue of the Claude-Code SessionStart hook:
  every MCP client (Cursor, Windsurf, Zed, Codex, Gemini, Continue,
  Claude Desktop) sees it without any host-side configuration.
- **"Stable kernel, mutable substrate" positioning** (Stage D.5).
  Trilingual READMEs swap the stale "v0.4.0 — Greenfield Rewrite"
  banner for a positioning line that names the design split
  explicitly: `pip install` locks the kernel; substrate evolution
  runs via the twelve MCP verbs. Contributor editable-install path
  is promoted into Quick Start.
- **Release-ephemerals excluded from sdist** (Stage D.5).
  `pyproject.toml` gains explicit `[tool.hatch.build.targets.sdist]`
  include/exclude lists so `.release_notes_*.md`, `upload*.log`,
  `dist/`, `build/`, `legacy_v0_3/`, `.pytest_cache/`, and every
  `__pycache__/` stay out of the PyPI tarball even if they happen
  to sit in the working tree at build time. `.gitignore` gains the
  same patterns as belt-and-suspenders.
- **Hook commands prefer `myco` over `python -m myco`**
  (Stage D.5). Both `hooks/hooks.json` (plugin) and
  `.claude/settings.local.json` (dogfooding) now invoke the `myco`
  console script rather than `python -m myco`, closing the same
  `python` / `python3` / venv gap the MCP launcher just closed.
- **`myco-install` one-command installer for seven MCP hosts**
  (Stage D.6). New `src/myco/install/` subpackage; third console
  script `myco-install`. Writes the correct schema per host
  (handles the four dominant schema variants: `mcpServers` JSON,
  `context_servers` JSON, `servers` JSON with `"type": "stdio"`, and
  OpenClaw's CLI-mediated `mcp.servers` nesting). Preserves any
  sibling servers in existing config files; idempotent; supports
  `--dry-run`, `--global`, `--uninstall`. Covers Claude Code,
  Claude Desktop, Cursor, Windsurf, Zed, VS Code, OpenClaw. Remaining
  hosts documented with per-platform snippets in
  [`docs/INSTALL.md`](docs/INSTALL.md).
- **OpenClaw support** (Stage D.6). OpenClaw uses a nested
  `mcp.servers.<name>` schema mutated via its own `openclaw mcp set`
  CLI, not the standard `mcpServers` key at repo root. The
  `myco-install openclaw` path shells out with the correct payload;
  documentation surfaces both the one-line helper and the manual
  path. Addresses the long-tail platform story the mainline
  "one snippet everywhere" framing cannot cover.
- **`docs/INSTALL.md` — comprehensive per-host matrix** (Stage D.6).
  New top-level install guide listing every MCP host active on the
  2026-04 landscape with the exact config path and exact line for
  each: `mcpServers`-family (11 hosts), VS Code, Zed, OpenClaw,
  OpenHands (TOML), OpenCode / Kilo Code (`mcp` key), Codex CLI
  (TOML), Goose (YAML), Warp (`mcp_servers`), Continue (YAML block),
  JetBrains AI, Devin (UI form), Bolt.new (UI form), Claude Desktop
  (three OS paths). Plus Python-framework adapter snippets for
  LangChain / CrewAI / DSPy / Smolagents / Agno / PraisonAI /
  Microsoft Agent Framework / Claude Agent SDK. Hosts without
  native MCP (Aider CLI, SWE-agent, Void) are flagged explicitly so
  users do not waste time there.
- **Narrative README rewrite** (Stage D.6). The "What it is"
  opening, five-principles block, and three-roles framing are
  re-authored across all three language READMEs (English, Chinese,
  Japanese) to embody rather than merely mention L0's five root
  principles. Every principle gets a one-sentence practical
  phrasing plus a consequence. The three roles name concrete
  behaviors instead of abstract nouns ("Myco runs a metabolism ...
  `hunger`, `eat`, `reflect / digest / distill`, `immune`,
  `propagate`"). Structure stays identically lined (169 lines each).
- **"Substrate that ingests frameworks" positioning + em-dash
  cleanup** (Stage D.7). Second pass on the trilingual READMEs
  tightening the core claim that sets Myco apart from competitors:
    * **Devour everything** is broadened to include code repositories,
      framework documentation, datasets, and papers by name (not
      just "notes and decisions"). The tagline is hardened to "not
      a framework, a substrate that ingests frameworks."
    * **Self-evolving shape** promises that even a complete internal
      rewrite remains a `myco` version bump, not a new dependency.
      The underlying substrate is never thrown away; users never
      migrate again. This is the real differentiator from every
      "agent framework" or "memory layer" on the market.
    * The rewrite explicitly frames why it works now and could not
      work before: "Agents are finally intelligent enough to
      maintain the system themselves; earlier attempts died because
      humans could not keep up."
    * Zero em-dashes across all three language READMEs. Replaced
      with colons, commas, parentheses, or sentence splits. The
      reading cadence now relies on full stops and clear nouns,
      which survives translation to CJK densities better than
      em-dash-heavy English. Word counts: en 1353, zh 636, ja 632.

### Planned

*(empty — the four v0.4.1 promises are all landed; Stage E is the
release itself.)*

### Changed

- **Package description cleaned** (Stage D.1). `pyproject.toml` no
  longer self-describes as "v0.4.0 greenfield rewrite" in its PyPI
  summary; that phrasing was accurate at the v0.4.0 release and stale
  the moment v0.4.1 became the development head.

### Post-release hygiene from v0.4.0 (Stage C.7)

- **Scaffold version assertion is now version-agnostic.** The Stage A/B
  sanity test previously hard-coded `"0.4.0.dev"`; it now accepts any
  PEP 440 release or `.dev` marker via regex. Release bumps no longer
  force a test edit.
- **`myco --help` reports `__version__` dynamically** instead of a
  hard-coded `"v0.4.0"` literal. The description line is now derived
  from the SSoT at `src/myco/__init__.py`.
- **CHANGELOG.md header corrected.** The v0.4.0 release commit
  (Stage C.4, `198470f`) left the header as `[Unreleased] — 0.4.0.dev`;
  this is now promoted to a proper `[0.4.0] — 2026-04-15` section with
  a fresh `[Unreleased]` segment above.
- **v0.4.1 handoff brief landed** at
  `docs/primordia/agent_handoff_v0_4_1_2026-04-15.md` — onboarding doc
  for the session that executes the four promises above.

---

## [0.4.0] — 2026-04-15

Greenfield rewrite release. Backward-incompatible with v0.3.x. The
pre-rewrite codebase (v0.3.4 lineage) is preserved at tag
`v0.3.4-final`; consumers (e.g. ASCC) remain pinned there until they
migrate via the fresh re-export path.

### Added

- **Eight-package source layout** under `src/myco/`: `core`, `genesis`,
  `ingestion`, `digestion`, `circulation`, `homeostasis`, `surface`,
  `symbionts`. Each subsystem maps to a biological role per L0's
  authoritative metaphor table.
- **Twelve verbs, manifest-driven.** `genesis` · `hunger` · `eat` ·
  `sense` · `forage` · `reflect` · `digest` · `distill` · `perfuse` ·
  `propagate` · `immune` · `session-end`. The single source of truth is
  `src/myco/surface/manifest.yaml`; CLI and MCP surfaces are both
  derived from it. Adding a verb edits the manifest, not `cli.py` or
  `mcp.py`.
- **Eight lint dimensions** authored fresh (not ported from v0.3's
  30-dim table):
  - Mechanical: M1 (canon identity), M2 (entry-point exists),
    M3 (write-surface declared).
  - Shipped: SH1 (package-version ref resolves).
  - Metabolic: MB1 (raw-notes backlog), MB2 (no integrated yet).
  - Semantic: SE1 (dangling refs), SE2 (orphan integrated).
- **Seven L1 hard rules (R1–R7)** with explicit mechanical /
  disciplinary enforcement mapping. See
  `docs/architecture/L1_CONTRACT/protocol.md`.
- **`_canon.yaml`, `MYCO.md`, `.claude/hooks/`** materialized fresh at
  the repository root. The SessionStart hook fires `myco hunger`; the
  PreCompact hook fires `myco session-end`.
- **ASCC substrate migrator** at `scripts/migrate_ascc_substrate.py`
  (dry-run default, `--execute` opt-in). Maps v0.3 canon fields into
  the v0.4 schema per the "fresh re-export" discipline.
- **Trilingual READMEs** (`README.md`, `README_zh.md`, `README_ja.md`)
  ported to the new surface.
- **Assets** — `assets/_gen_logo.py` generator plus produced PNGs
  referenced by the READMEs (restored Stage C.6 after an overly broad
  Stage C.4 sweep).

### Architecture

- **L0–L3 top-down design** landed under `docs/architecture/`. Five
  root principles (Only For Agent / 永恒吞噬 / 永恒进化 / 永恒迭代 /
  万物互联), three derived invariants, seven L1 hard rules, five
  biological subsystems, eight-package L3 map. Governing crafts:
  `docs/primordia/greenfield_rewrite_craft_2026-04-15.md` and
  `docs/primordia/l0_identity_revision_craft_2026-04-15.md`.
- **Single-path rewrite discipline** — v0.4 code is written directly
  into `src/myco/`, not under a `src/myco_v4/` staging path. No v4
  marker appears anywhere in paths, package names, or commit subjects.
  Rationale in
  `docs/architecture/L3_IMPLEMENTATION/migration_strategy.md`.
- **Contract changelog separation.** `docs/contract_changelog.md` now
  tracks L0/L1/L2 doctrine changes separately from this package
  changelog. First entry records the v0.4.0 contract surface and the
  break from v0.3.x.

### Removed

- **Pre-rewrite quarantine (`legacy_v0_3/`) removed from the working
  tree.** Git history is preserved; tag `v0.3.4-final` is the sole
  anchor for the pre-rewrite lineage.
- **v0.3 30-dimension lint table** superseded by the fresh 8-dimension
  set above.

### Release mechanics

- Annotated tag `v0.4.0` (`git tag -a`, never lightweight).
- GitHub release published at `Myco-v0.4.0`.
- PyPI upload: wheel + sdist, `PYTHONIOENCODING=utf-8` plus
  `--disable-progress-bar` to survive the GBK Windows console.

---
