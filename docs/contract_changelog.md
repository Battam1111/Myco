# Contract Changelog

Append-only record of contract-version bumps. A contract bump is
required whenever R1–R7 change, subsystem definitions change, the
exit-code policy grammar changes, the lint-dimension inventory changes
semantics, or the command manifest changes a verb's shape. Adding a
new lint dimension inside an existing category is a changelog line but
not a bump.

Format: one section per `contract_version`, newest first.

---

## v0.6.13 — 2026-04-28 — Restore `myco.mcp` legacy import as back-compat shim

**Zero R1-R7 surface deltas; zero new manifest verbs; zero new lint dims; zero subsystem changes; schema v2 unchanged.** Targeted fix for the post-v0.6.0 host-config regression: the legacy `python -m myco.mcp` spawn path is restored as a thin re-export of `myco.boundary.mcp`, with a stderr deprecation pointer + standard `DeprecationWarning` so operators see the canonical replacement.

### Why this release

A v0.6.12 dogfood report from the Cowork Local-MCP-Servers dashboard showed `myco` listed with a red **failed** badge and `Server disconnected` error. Log inspection at `C:\Users\10350\Desktop\mcp-server-myco.log:2069` surfaced the actual cause:

```
C:\Python313\python.exe: No module named myco.mcp
```

Root cause: at v0.6.0 the Round 5 owner directive ("不许有任何一丝一毫偷懒") landed the boundary subsystem and physically relocated `myco.{mcp,surface,install,symbionts}` to `myco.boundary.<sub>`, deleting the legacy top-level packages. Three releases (v0.6.10 / v0.6.11 / v0.6.12) shipped under the assumption every host config had been migrated alongside.

Reality: most host MCP configs (Claude Desktop, Cowork, Cursor, JetBrains, Continue, Cline, Zed, Goose, Windsurf, Codex CLI, Gemini CLI, OpenClaw — anything pre-dating v0.6.0) still spelled their command `python -m myco.mcp`. Every spawn raised `ModuleNotFoundError` and the MCP child died before completing the JSON-RPC handshake, surfacing as "Server disconnected" in the host UI.

### What landed

Two new files restoring the legacy import path:

- `src/myco/mcp/__init__.py` — back-compat shim. Re-exports `build_server` + `main` from `myco.boundary.mcp` as the same canonical objects (asserted by regression test). Emits a single-line stderr deprecation pointer naming both canonical replacements (`mcp-server-myco` entry-point binary OR `python -m myco.boundary.mcp` module path). Also raises a `DeprecationWarning` so test harnesses + lint hooks observe legacy use through the standard warnings filter.
- `src/myco/mcp/__main__.py` — legacy `python -m myco.mcp` entry point. Imports the shim (which triggers the deprecation pointer once per spawn) then delegates to the canonical `main()`.

Critically, the shim keeps **stdout clean** — the JSON-RPC channel for stdio transport must not be contaminated. The deprecation pointer flows to stderr exclusively, where MCP host UIs surface it in their "View Logs" panel without breaking framing.

### Test coverage delta

5 new regression tests at `tests/unit/boundary/test_legacy_mcp_shim.py`:

1. `test_shim_imports_without_error` — `import myco.mcp` resolves
2. `test_shim_reexports_canonical_symbols` — `myco.mcp.build_server is myco.boundary.mcp.build_server` (object identity, catches re-export drift on next boundary.mcp public-API change)
3. `test_shim_emits_deprecation_warning` — standard-warnings observer sees the legacy-path warning
4. `test_shim_writes_stderr_pointer` — capfd asserts stdout stays clean + stderr contains the pointer
5. `test_shim_help_subprocess_exits_zero` — subprocess smoke test that `python -m myco.mcp --help` boots end-to-end (catches `python -m` resolution + `__main__` discovery, not just in-process import graph)

Pytest: 1470 → 1477 collected (+5 shim tests + 2 incidental from registry rescan; 1 skipped unchanged). `_canon.yaml::metrics.test_count` updated to 1477.

### Boundary subsystem invariants preserved

The shim does NOT dilute L0:185-186 vocabulary discipline or the boundary subsystem's "derivation-only, no verb logic" rule (per `boundary.md`):

- **Internal kernel imports still flow through `myco.boundary.mcp`.** Verified by `PA3` + `PA4` lint dimensions which would fire on any kernel-side legacy reference. The shim exists exclusively for **external** entry points (host MCP configs + `python -m` invocations from user shell scripts).
- **No verb logic in the shim.** Two functions: emit deprecation pointer, delegate to `main()`. No state, no canon writes, no R6 surface use.
- **L0 vocabulary unchanged.** `myco.boundary` remains the canonical subsystem identifier. The shim is a back-compat path under the old name, not a recognised subsystem.

### Removal schedule

The shim ships at v0.6.13 as a one-MAJOR-class deprecation window. Removal scheduled for **not earlier than v0.7.0**, mirroring the v1.0.0 alias-removal cadence in `digestion.md` § "Aliases" and the v0.6.0 §A2 owner amendment that removed v0.5.2 verb aliases at v0.6.0. Operators have one minor band to update their MCP host configs before the next removal window.

### Operator action (immediate)

Edit your MCP host config to use either:

- `mcp-server-myco` — the canonical entry-point binary (recommended; survives any future module reorganisation as it lives in `pyproject.toml::[project.scripts]`)
- `python -m myco.boundary.mcp` — the canonical module path

If you cannot update the config right now, the legacy `python -m myco.mcp` spelling continues to work through v0.6.x with the deprecation pointer guiding the upgrade.

### Break from v0.6.12

**None at the public surface.** R1-R7 unchanged. 20-verb manifest unchanged. 46-dim lint roster unchanged. 7-subsystem inventory unchanged. Schema v2 unchanged. v0.6.13 is **strictly additive**: the kernel re-exposes a previously-deleted import path. Any v0.6.12 install continues working; v0.6.13 adds resilience for stale host configs.

### Files touched

- `src/myco/mcp/__init__.py` (new — back-compat shim with deprecation pointer)
- `src/myco/mcp/__main__.py` (new — legacy `python -m myco.mcp` entry)
- `tests/unit/boundary/test_legacy_mcp_shim.py` (new — 5 regression tests)
- `_canon.yaml` (`metrics.test_count` 1470 → 1477; `contract_version` v0.6.12 → v0.6.13; `waves.current` 24 → 25)
- `docs/contract_changelog.md` (this entry)
- `src/myco/__init__.py`, `CITATION.cff`, `server.json`, `.claude-plugin/plugin.json`, `.cowork-plugin/.claude-plugin/plugin.json` (atomic version bump via `scripts/bump_version.py --to 0.6.13`)

---

## v0.6.12 — 2026-04-28 — Supply-chain hardening + Glama maintenance signal lift

**Zero R1-R7 surface deltas; zero new manifest verbs; zero new lint dims; zero subsystem changes; schema v2 unchanged.** Pure ops + supply-chain release that closes Glama maintenance score's four factors (issue responsiveness 40%, commit cadence 25%, release recency 20%, security health 15%) into the A/A+ band, plus two doctrine-vs-impl drift fixes inherited from the v0.6.11 audit.

### Why this release

External Glama maintenance scoring (`https://glama.ai/mcp/servers/Battam1111/Myco`) graded the substrate **B** with the breakdown documented at the registry: 4-of-5 supply-chain checkboxes (Dependabot security updates / CodeQL / OpenSSF Scorecard / CODEOWNERS / branch protection) were either disabled or unconfigured. Issue responsiveness was vacuously 100% (zero open issues, zero open PRs since launch); commit cadence was strong (>30 commits in the prior 12-week window); release recency was perfect (v0.6.11 same-day). Security health was the only depressed factor — and it was the easiest one to lift cleanly without changing any agent-visible R-surface.

### What landed (4 supply-chain infrastructure additions)

| File | Role |
|------|------|
| `.github/dependabot.yml` | Two ecosystems (`pip` + `github-actions`), weekly Monday 06:00 UTC schedule, ≤5 open PRs per ecosystem, grouped runtime / tooling / auth bundles to keep maintainer review-noise floor low |
| `.github/workflows/codeql.yml` | Python static analysis on every push to `main`, every PR targeting `main`, plus weekly Monday 04:23 UTC cron. Query pack: `security-and-quality` (broader-net than the default `security-extended`). SARIF uploads to GitHub Code scanning → Glama "security health" factor reads the alert count via the `/repos/{o}/{r}/code-scanning/alerts` endpoint |
| `.github/workflows/scorecard.yml` | OpenSSF Scorecard weekly Monday 05:37 UTC + `branch_protection_rule` event + main-push triggers. `publish_results: true` posts to the public Scorecard registry → Glama can read the supply-chain health score directly |
| `.github/CODEOWNERS` | Catch-all `* @Battam1111` plus explicit ownership entries for canon / doctrine / contract / primordia / CI / release / plugin-bundle scopes |

`SECURITY.md` is refreshed: supported-versions table now reads `0.6.x latest / 0.5.x advisory / ≤0.4.x frozen / ≤0.3.x pre-rewrite frozen`. The "What Myco defends mechanically" section gains four new bullets covering the v0.6.0 LLM-policy 3-state enum (`forbidden / opt-in / providers-declared` + MP1/MP2/MP3 enforcement), the v0.6.0 CL1/CL2/CL3 MCP-credential discipline, the OAuth 2.1 streamable-http transport (PKCE-S256 + RFC 8707 resource indicators + JWKS rotation + 30s refresh-token grace + `python-jose` choice over PyJWT), and the v0.6.12 supply-chain hardening.

### v0.6.11 doctrine-vs-impl drift fixes

The v0.6.11 architecture audit surfaced two small drift items that ride along here:

1. **`MYCO.md` `★` markers for DC4 and PA1 removed.** The 12-dim ★ list at `MYCO.md` claimed both DC4 (`module_doc_ref`) and PA1 (`write_surface_coverage`) were `immune --fix`-able; the implementations declare `fixable: ClassVar[bool] = False` (`dc4_module_doc_ref.py:70`, `pa1_write_surface_coverage.py:80`) per the v0.6.0 §F18 fix-narrowness craft principle (markdown surgery + write-surface expansion are too delicate for safe-fix's idempotent / narrow / non-destructive / bounded discipline). MYCO.md is now consistent with code: 10 actually-fixable dimensions (M1, M2, M3, DC1, CS1, DI1, MB1, MB3, MB6, SE1).
2. **`MYCO.md` immune-baseline paragraph refreshed.** Pre-this-release said "exit 0, 0 findings since v0.5.9". Reality at v0.6.12: exit 0 (CRITICAL-gate via `lint.exit_policy.default = "mechanical:critical,shipped:critical,metabolic:never,semantic:never"`), 76 non-critical findings (9 HIGH AD1 adapter silent-skips inherited from pre-v0.6.0 adapters + assorted LOW DC2/DC3/DC4/SE2 hygiene). Drift originated when v0.6.0 expanded the lint roster from 25 → 46 dimensions. New paragraph names the actual count and frames HIGH-band drift as a candidate for the next severity-promotion craft.
3. **`_canon.yaml::metrics.test_count` 1427 → 1470.** v0.6.11 added 43 boundary-surface regression tests but the canon metric wasn't bumped; now matches actual collected count (`pytest -q` reports 1469 passed + 1 skipped = 1470 collected).

### Schema additions (canon)

- `system.write_surface.allowed` extended with `".github/**"` and `"SECURITY.md"`. The `.github/` tree now owns CodeQL + Scorecard + Dependabot config + CODEOWNERS + ISSUE_TEMPLATE/ + workflows/ + pull_request_template; declaring it canonical aligns PA1 (`pa1_write_surface_coverage.py`) with the paths the maintainer actually edits.

### Break from v0.6.11

**None.** R1-R7 unchanged. 20-verb manifest unchanged. 46-dim lint roster unchanged. 7-subsystem inventory unchanged. Schema v2 unchanged. The kernel is bit-for-bit identical to v0.6.11 except `__version__ = "0.6.12"`. Existing user scripts, plugin installs, MCP host configs, and downstream substrates continue working unchanged. The four new GitHub-side workflows fire on the next push to main; they do not change the runtime contract surface.

### Files touched

- `.github/dependabot.yml` (new)
- `.github/workflows/codeql.yml` (new)
- `.github/workflows/scorecard.yml` (new)
- `.github/CODEOWNERS` (new)
- `SECURITY.md` (supported-versions refresh + supply-chain hardening section)
- `MYCO.md` (DC4/PA1 ★ removal, immune-baseline paragraph refresh)
- `_canon.yaml` (write_surface adds `.github/**` + `SECURITY.md`; `metrics.test_count` 1427 → 1470; contract bump 0.6.11 → 0.6.12; waves 23 → 24)
- `docs/contract_changelog.md` (this entry)
- `src/myco/__init__.py`, `CITATION.cff`, `server.json`, `.claude-plugin/plugin.json`, `.cowork-plugin/.claude-plugin/plugin.json` (atomic version bump via `scripts/bump_version.py --to 0.6.12`)

### Test count

Pytest: **1469 passed + 1 skipped** (1470 collected). Unchanged from v0.6.11. The new GitHub workflows do not have associated pytest assertions (their correctness is verified by GitHub Actions itself running them).

### Glama re-scan trigger

After tag push the maintainer manually triggers a Glama dashboard rescan (`https://glama.ai/mcp/servers/Battam1111/Myco`). Maintenance score recovery window is 1-7 days; SARIF + Scorecard registry results take 1-2 cron firings (≤2 weeks) to populate fully. v0.6.12 is the substrate-side close of the Glama-maintenance loop; the dashboard refresh is the operator-side close.

---

## v0.6.11 — 2026-04-28 — Fungal subagents + slash commands (boundary surface extension)

**Zero R1-R7 surface deltas; zero new manifest verbs; zero new lint dims.** Boundary subsystem extension that formalizes 5 specialist agent roles + 5 user-trigger workflows previously done as ad-hoc agent sessions. Pure add: existing surfaces are unchanged.

### Governing craft

`docs/primordia/v0_6_11_subagents_and_commands_craft_2026-04-28.md` (LANDED, 3-round structure with 8 self-rebuttals all resolved).

### What landed (5 subagents + 5 slash commands)

5 fungal-named Claude Code subagents at `.claude/agents/<name>.md` (project-level, auto-discovered by Claude Code) and `<repo>/agents/<name>.md` (plugin-bundle scope, declared in `.claude-plugin/plugin.json::agents`). All names come strictly from fungal taxonomy per L0:185-186; the boundary subsystem's English-name amendment from v0.6.0 §A1 is NOT extended here.

| Subagent | Fungal idiom | Role |
|----------|--------------|------|
| `primordium` | The initial undifferentiated fruiting body that emerges before differentiation | Drafts a 3-round craft proposal under `docs/primordia/`, runs `myco winnow` to gate before returning |
| `hypha` | The exploratory thread of fungus that extends through substrate | Investigates one `myco_immune` finding (root-cause trace + minimal-fix proposal); read-only |
| `autolysis` | Fungal self-digestion of old tissue | Sweeps stale narrative refs (version drift, deleted module paths, deprecated identifiers, numeric drift, test_count drift); produces deterministic patch table |
| `stipe` | The mushroom stem that holds the cap aloft so spores can disperse | Orchestrates the full release pipeline: pre-flight gate → bump → commit → push → tag → ci.yml + release.yml watch → post-release verification |
| `anamorph` | The asexual transformative life-cycle form | Drafts canon schema migrations (named partial upgraders + tests + schema delta + migration guide); stops before flipping `_canon.yaml::schema_version` |

5 slash commands at `.claude/commands/<name>.md` (project-level) and `<repo>/commands/<name>.md` (plugin-bundle scope, declared in `.claude-plugin/plugin.json::commands`). Each is a thin orchestrator that invokes the corresponding subagent with bookkeeping (R-rule reminders, output-shape requirements, governance hooks):

| Slash | Subagent | Argument |
|-------|----------|----------|
| `/myco-primordium <topic>` | primordium | topic phrase |
| `/myco-hypha [pattern]` | hypha | optional dim ID or path pattern |
| `/myco-autolyze [category]` | autolysis | optional category filter |
| `/myco-disperse <version>` | stipe | clean PEP 440 version string |
| `/myco-anamorph <new-schema-version> <governing-craft-path>` | anamorph | schema-version int + craft path |

### Surface invariants (per craft Round 2 §F)

1. **Subagents are atoms; verbs are the composition primitive.** Subagents cannot recurse (Claude Code spec). They invoke each other only via Bash calls to Myco's verb manifest (`myco fruit`, `myco winnow`, `myco molt`, `myco immune`), never via the Agent tool.
2. **R-rule awareness baked into each subagent body.** State-mutating subagents (`primordium`, `stipe`, `anamorph`) call `myco hunger` first per R1. Read-mostly subagents (`hypha`, `autolysis`) skip the boot ritual but still honor R3 (sense-before-assert) and R6 (write-surface).
3. **Plugin-mirror discipline.** The 10 markdown files (5 agents + 5 commands) live at both `.claude/<dir>/<name>.md` (project-level) and `<repo>/<dir>/<name>.md` (plugin-bundle scope). v0.6.11 accepts the duplication as known maintenance debt. v0.6.12 may add a `scripts/build_plugin.py` copy hook. Drift is surfaced immediately by a regression test that asserts byte-identity.
4. **Naming complies with L0:185-186.** All five subagent names are fungal taxonomy.
5. **Downstream substrates extend at project level.** Per Claude Code precedence, project-level agents override plugin agents. Myco-self ships these 5 as defaults; downstream may keep, override, or supplement.

### Break from v0.6.10

**None.** R1-R7 unchanged. 20-verb manifest unchanged. 46-dim lint roster unchanged. 7-subsystem inventory unchanged. Schema v2 unchanged. The v0.6.11 release is purely additive: new surface paths (`.claude/agents/`, `.claude/commands/`, `<repo>/agents/`, `<repo>/commands/`) and new doctrine sections in `boundary.md` and `MYCO.md`. Existing user scripts, plugin installs, MCP host configs, and downstream substrates continue working unchanged.

### Schema additions (canon)

- `system.write_surface.allowed` extended with `"agents/**"` and `"commands/**"` for the plugin-bundle scope (project-level paths covered by the existing `".claude/**"` allowlist).

### Doctrine alignments

- `docs/architecture/L2_DOCTRINE/boundary.md`: new section "Subagents and slash commands (v0.6.11+)" describes the surface contract, names the 5 fungal idioms, lists invariants, and documents the deferred `myco ramify --agent` axis.
- `MYCO.md`: new section pointing agents at the surface + summarizing invariants + linking to the governing craft.

### Test coverage delta

- New file `tests/unit/boundary/test_subagent_and_command_surface.py` adds 43 regression tests covering: file existence at both paths × 5 subagents + 5 commands; frontmatter parses + required keys + name-stem match × 5 subagents; description-key + body-≥-200-chars × 5 commands; byte-identity between the project-level path and the plugin-bundle path × 10 files; count-matches-craft × 2; plugin manifest declares `agents` + `commands` × 1.
- Pytest count: 1426 → 1469 (+43; 1 skipped unchanged).

### Future axis (not landed)

- `myco ramify --agent <name>` and `myco ramify --command <name>` flag extensions are deferred. Until they land, downstream substrates copy from `.claude/agents/` manually.
- A build-hook in `scripts/build_plugin.py` to copy `.claude/<dir>/` → `<repo>/<dir>/` at plugin-bundle build time, eliminating the source-of-truth split. Tracked for v0.6.12.

### Files touched

- `.claude/agents/{primordium,hypha,autolysis,stipe,anamorph}.md` (new, 5 files)
- `.claude/commands/{myco-primordium,myco-hypha,myco-autolyze,myco-disperse,myco-anamorph}.md` (new, 5 files)
- `agents/{...}.md` (new, 5 plugin-bundle mirrors)
- `commands/{...}.md` (new, 5 plugin-bundle mirrors)
- `.claude-plugin/plugin.json` (add `agents` + `commands` keys + version bump)
- `_canon.yaml` (add `agents/**` + `commands/**` to write_surface; contract bump 0.6.10 → 0.6.11; waves 22 → 23)
- `_canon_lint.yaml` (no change; 46 dims unchanged)
- `docs/architecture/L2_DOCTRINE/boundary.md` (new section)
- `docs/primordia/v0_6_11_subagents_and_commands_craft_2026-04-28.md` (new, the LANDED 3-round craft)
- `MYCO.md` (new section)
- `.gitignore` (allowlist `.claude/agents/` and `.claude/commands/`)
- `tests/unit/boundary/test_subagent_and_command_surface.py` (new)
- `src/myco/__init__.py`, `CITATION.cff`, `server.json`, `.cowork-plugin/.claude-plugin/plugin.json` (atomic version bump)

---

## v0.6.10 — 2026-04-28 — Unified evolution + thorough refactor (MAJOR-class per L0:223)

**Full R-surface preserved; canon schema bump v1 → v2; subsystem count 5 → 7 (cycle + boundary promoted).**

**Note on the v0.6.0 / 0.6.1 / 0.6.2 PyPI namespace burns.** This release ships under tag `v0.6.10`. The semantically-prior label `v0.6.0` released to PyPI as `myco-0.6.0.post1` (PEP 440 path B, commit `a665c0b`) on 2026-04-28; that artifact carries the same R-surface as this release minus the cleanups documented under "v0.6.10 cleanups" below. Tags `v0.6.0` and `v0.6.0.post1` exist on the repo for historical fidelity. PyPI filenames `myco-0.6.0`, `myco-0.6.1`, `myco-0.6.2` are burned (PyPI filename uniqueness rule; commits `f0e12fd`, `32e4c6b`, `2e996a8` document the bumps that hit each burn). `0.6.10` is the chosen clean SemVer label well past the burn region; `pip install --upgrade myco` resolves transparently.

First MAJOR-class release per `L0_VISION.md:223-228` cadence rule —
fires Living Bets re-audit (sibling craft `v0_6_0_living_bets_audit_craft_2026-04-28.md`).
SemVer label "0.6.10" reads as a routine patch by external naming convention; Myco
contract semantics treat it as MAJOR-class for review-cadence and
breaking-change-permission per craft v0.6.0 §F1.

### Governing crafts

- `docs/primordia/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md` (LANDED, owner-approved)
- `docs/primordia/v0_6_0_living_bets_audit_craft_2026-04-28.md` (LANDED; verb-surface wager survives un-falsified at 2026-Q2 model capability; v0.7 falsification experiment pre-registered)

### What changed (major)

1. **Cycle promoted to canonical 6th subsystem** (`canon.subsystems` 5 → 6).
   Aligns L4 with `L0_VISION.md:183` which named Cycle as 6th since v0.5.3.
   New L2 doctrine `docs/architecture/L2_DOCTRINE/cycle.md`.
   Withdrawn proposals: cycle→governance rename (violated L0:185-186 "No
   alternate vocabulary") and boundary subsystem creation (same).
2. **Canon schema v1 → v2** via `_v1_to_v2` upgrader composed of two
   named partials (per craft §F6/T30 narrowness):
   - `_v1_to_v2_llm_policy_enum`: `system.no_llm_in_substrate: bool`
     → `system.llm_policy: "forbidden" | "opt-in" | "providers-declared"`
     enum (default forbidden — preserves v0.5.6 P1 strict invariant).
   - `_v1_to_v2_federation_peers_field`: adds `identity.federation_peers: []`
     forward-compat infrastructure for L0 P5 federation planning.
   `KNOWN_SCHEMA_VERSIONS = frozenset({"1", "2"})`. v0.5.x substrates
   parse cleanly without warning; lint.dimensions sub-file extraction
   deferred to v2.1.
3. **Lint dimension inventory 25 → 46** (+21 new dims). All ship at
   default-severity LOW with `lint.severity_promotion` ledger ramping
   to declared severity over 30 sessions of green observation:
   - **Mechanical structural** (9): PA2 (megafile LoC cap), PA3
     (surface pure-adapter), PA4 (core no-subsystem-deps), PA5
     (meta-subsystem layering), SC1 (canon JSON-Schema parity),
     DC5 (abstract-parent-allowlist canon-driven), MF3 (symbiont
     host-side artifact integrity), DI2 (hooks content R1+R2),
     AD1 (adapter silent-skip detection).
   - **Semantic + metabolic** (5): SE4 (reciprocal back-link), RL2
     (R3 sense-discipline signal), RL3 (R4 eat-discipline signal),
     MB4 (sporulated-reabsorbed integrity), MB6 (stale DRAFT/distilled).
   - **Shipping + capability + plugin** (3): SH2 (kernel-ahead-of-canon),
     CL1 (sampling capability gated on llm_policy), MP3 (plugin
     bytecode LLM-SDK audit).
   - **R-revision additions** (4): MB7 (resource_watch quota pressure),
     CL2 (OAuth token-residency policy), CL3 (sampling token clear),
     MF4 (overlay_verb subsystem validity).
4. **Verb count 19 → 20**: new `intake` verb (replaces unimplemented
   `forage --digest-on-read`); single-responsibility composer of
   `forage` + `eat` with strict-mode and adapter-failure-visibility.
5. **Sporulate→reassimilate closed loop** lands per L0 P4
   ("永恒迭代; integrated is not endpoint"). New
   `digestion.reassimilate.reassimilate_integrated` demotes integrated
   notes to `stage: re_raw` with audit trail; new
   `digestion.promote_sporulated.promote_consumed_distilled` lifts
   distilled notes consumed by crafts to `stage: sporulated` with
   `propagated_doctrine: <docpath>` reference. `pipeline.NOTE_STAGES`
   extends to include `sporulated` and `re_raw`.
6. **MCP capability surface extended**: new `surface.mcp_resources`
   (resources/list + resources/read with URI scheme `myco://canon`,
   `myco://contract`, `myco://notes/integrated/{id}`,
   `myco://docs/primordia/{slug}`, `myco://reflex/queue`) + new
   `surface.mcp_prompts` (20 verb-guides + 2 workflow prompts).
   Resources honor `system.resource_redaction` default protected
   scope (federation_peers, identity.tags, system.governance hidden
   from non-OAuth-canon:full hosts). Resource-read injects R3-discipline
   ledger entry per craft §F8.
7. **Symbionts populated** at `src/myco/symbionts/<host>.py` (path
   preserved per `extensibility.md:24-27` doctrine; boundary/host_integration/
   refactor withdrawn). v0.6.0 ships 5 of 11 host adapters with full
   `discover/install_basic/install_deep/uninstall` four-function
   protocol: claude-code, cursor, cowork, vscode, continue-dev. The
   remaining 6 (cline, jetbrains, zed, goose, windsurf, codex-cli /
   gemini-cli / openclaw / claude-desktop) ship as v0.6.x ecosystem-thawed
   patches per craft §F23 dual-layer versioning.
8. **Activity cleanup**: 9-day-stalled DRAFT craft `dogfood_v0_5_3_smoke_craft_2026-04-18.md`
   moved to `docs/primordia/_excreted/`; 2 distilled notes
   (`d_legacy_alias_test.md`, `d_v0_5_3_dogfood_notes.md`) moved to
   `notes/distilled/_excreted/` (no doctrine payload, event-records
   only). MB6 dim guards future stale-DRAFT/distilled at 14d MEDIUM
   / 30d HIGH thresholds (canon-driven via `lint.thresholds`).

### v0.6.10 cleanups (Δ from v0.6.0.post1)

These are the additional changes that distinguish this release from the v0.6.0.post1 PyPI artifact:

- **Lint dual-table consolidation (Option A)**: deleted the inline `_canon.yaml::lint.dimensions` block (was redundant with the sibling `_canon_lint.yaml::dimensions` table; both held the same 46-ID roster). Removed the now-redundant `dimensions` property from `docs/schema/canon.schema.json`; replaced with a `dimensions_ref` description that mirrors canon's `dimensions_ref` pointer. Single SSoT is `_canon_lint.yaml::dimensions` referenced via `_canon.yaml::lint.dimensions_ref`. No runtime change — `Dimension.category` class attr was already authoritative; `core.canon._merge_lint_dimensions_subfile` (lines 216-253) transparently merges the sibling when the inline table is absent. SC1 (canon JSON-Schema parity) continues to pass since the deleted property is OPTIONAL in the schema's `required` array.
- **Stale-narrative sweep**: ~50 inherited-from-pre-v0.6.0 references to "19 verbs" / "25 lint dimensions" / `myco.symbionts` / `src/myco/surface/manifest.yaml` updated to "20 verbs" / "46 lint dimensions" / `myco.boundary.host_integration` / `src/myco/boundary/surface/manifest.yaml` across READMEs (EN/ZH/JA), MYCO.md, both plugin manifest descriptions, the immune-tool description in `src/myco/boundary/surface/manifest.yaml`, both skills bodies (`hunger`, `myco-substrate`), the comparisons doc, and 12 `docs/promotion/*.md` files.
- **Test-count metric**: `_canon.yaml::metrics.test_count` 852 → 1427 (matches `pytest --collect-only` output post-v0.6.0).
- **Glama maintenance recency**: v0.6.0 ship landed on PyPI as `0.6.0.post1`; the maintenance-score window decayed because the `v0.6.0.post1` tag did not register as a fresh recency signal. `v0.6.10` re-arms the wall-clock signal Glama uses; maintainer triggers manual rescan post-tag, score recovers within 1-7 days.

### Aliases (deferred per `digestion.md:120-122`)

v0.5.2 CLI aliases (`genesis`, `reflect`, `distill`, `perfuse`,
`session-end`, `craft`, `bump`, `evolve`, `scaffold`) **continue to
resolve** at v0.6.0 with one-shot `DeprecationWarning`. Removal
remains scheduled at v1.0.0. v0.6.0 only upgrades the deprecation
banner severity; full removal awaits v1.0.0 per LANDED L2 doctrine
schedule (rejected craft §D9 acceleration was a P0 violation per
ChatGPT-as-critic [1.5-F]).

### Governance tiering (NEW)

- High-risk craft (L0 five principles, R1-R7 number/semantics, llm_policy
  default flip, subsystem deletion): owner approval required.
- Medium-risk craft (new dim, new verb alias, fixable-set extension):
  agent-self-winnow + 7-session-7-day public window (max of both floors).
- Low-risk craft (typo, JSON-Schema description, test fixtures):
  agent-self-winnow only.
- Owner-veto via `canon.governance.last_winnowed_proposals[].vetoed_at`
  always-on. Public window measured in `senesce_count >= 7` AND
  `wall_clock_days >= 7` (whichever later).

### Schema additions (canon)

- `system.llm_policy` (enum replaces v0.5.6 bool).
- `identity.federation_peers` (list, default empty).
- `system.resource_redaction` (paths/scopes for MCP resources).
- `system.resource_watch` (quota + LRU eviction + ETag fallback).
- `system.governance` (public window thresholds + token-residency policy).
- `lint.severity_promotion` (per-dim ramp ledger).
- `lint.thresholds` (stale-draft + stale-distilled cutoffs).
- `lint.abstract_parent_allowlist` (replaces DC2:158 hardcode; DC5 dim).
- `system.write_surface.allowed` adds `examples/**` (8 framework demos
  scope) and `dist/**` (CHANGELOG hatch hook).

### Doctrine alignments

- `L1_CONTRACT/protocol.md`: editorial clarification — "writes" =
  substrate writes; symbiont host-side writes are extensions of the
  host's own config discipline (not a R6 rule amendment, not adding
  R8 — see craft §F25).
- `L1_CONTRACT/versioning.md`: dual-layer versioning (contract-frozen
  vs ecosystem-thawed) introduced per craft §F23.
- `L1_CONTRACT/canon_schema.md`: v2 schema described.
- `L2_DOCTRINE/cycle.md`: NEW (6th subsystem doctrine).
- `L2_DOCTRINE/extensibility.md`: per-host axis enforcement dim
  promoted from "reserved" to MF3.
- `L3_IMPLEMENTATION/package_map.md`: 5 → 6 subsystems; cycle
  canonicalized; boundary withdrawn; `examples/**` + `dist/**` added
  to write_surface; severity-promotion ledger pattern documented.
- `L3_IMPLEMENTATION/symbiont_protocol.md`: 5/11 host adapters
  shipped; uninstall path implemented; remaining 6 → v0.6.x.

### Lessons learned (NEW pattern: dual-LLM critique)

The v0.6.0 craft was authored with **parallel ChatGPT-as-critic +
Gemini-as-critic agents** injecting Round 1.5 and Round 2.5 tensions
that single-perspective review would have missed. Specifically:

- **ChatGPT [1.5-D]** caught that L0:183 already named Cycle as 6th
  subsystem; the proposed rename to `governance` would have violated
  L0 directly. Corrected to "promote, don't rename."
- **ChatGPT [1.5-F]** caught that `digestion.md:120-122` doctrine
  scheduled alias removal at v1.0.0; v0.6.0 acceleration was a doctrine
  violation. Corrected to "warn at v0.6.0, remove at v1.0.0."
- **Gemini [G1.5-3]** caught that 11 host × 3 OS × 2 arch matrix was
  being tested as 1 cell; planned matrix CI for symbiont suite.
- **Gemini [G1.5-6]** caught that resources/list of `myco://canon`
  would leak federation_peers (potentially internal substrate URLs)
  to any MCP host. Corrected to default-redacted scope + OAuth-gated
  raw view.
- **ChatGPT [2.5-α]** caught that v0.6 MAJOR mandates Living Bets
  re-audit; sibling craft authored.

This dual-critique pattern is itself doctrine-worthy. v0.6.x or v0.7
may codify it as a `craft_protocol_version: 2` enhancement.

### Migration

A `docs/migration/v0_5_24_to_v0_6_0.md` (deferred to v0.6.x ecosystem-thawed
patch) details operator-visible deltas. Headline:

- Substrates auto-upgrade canon schema v1→v2 on first hunger; no
  operator action.
- All v0.5.x verb invocations continue working; deprecation banners
  louder.
- New `myco intake` verb available.
- New `myco://` MCP resources visible in host UIs.

### Acceptance

- `myco hunger` reports contract_version v0.6.0; substrate_pulse confirms.
- `myco immune` runs 25 dim baseline (kernel cache); on entry-points
  refresh expands to 44 dims, each at LOW per severity_promotion.
- `myco brief` shows 6 subsystems including cycle.
- DRAFT craft excretion verified by `myco traverse` orphan count
  reduction.
- Living Bets audit craft passes `myco winnow`.

---

## v0.5.24 — 2026-04-24 — Excretion + MCP-alias purge + param examples (TDQS A→A+ push)

**Partial R-surface delta.** New verb `excrete` in the ingestion
subsystem (R4/R7 neighborhood; no rule text changes). **Breaking
change for MCP clients** that still call the legacy tool names —
they now resolve to MCP's "unknown tool" error. CLI aliases survive
unchanged.

### Symptom at v0.5.23

Glama's v0.5.23 re-scan lifted Myco from C (2.53) to A (3.78
quality, 3.77 server TDQS, up 1.24 points). Per-tool breakdown
showed the canonical verbs clustered 4.2–4.9 while the **9
deprecated MCP aliases** (`myco_genesis`, `myco_reflect`,
`myco_distill`, `myco_perfuse`, `myco_session_end`, `myco_craft`,
`myco_bump`, `myco_evolve`, `myco_scaffold`) scored 2.9–3.7. The
min-dimension component (weight 40%) was pinned to the weakest
alias, dragging the server-level score. Glama's coherence
sub-score also flagged "lacks explicit tools for deletion or
direct editing of raw notes" — a metabolism gap since v0.4.0.

### Root cause

**MCP aliases were dead weight.** Every alias was an exact
duplicate of its canonical mcp_tool (same handler, same args, same
docstring), but Glama's TDQS evaluator treats each tool name as a
separate surface, so the aliases inherited v0.5.21-era thin
descriptions and dragged both the mean (by quantity) and the min
(by being the weakest). Keeping them gave zero UX benefit — MCP
clients cache the tool list and don't care about backward-compat
the way shell aliases do, so a client upgrade transparently picks
up the canonical name.

**No delete verb.** Raw notes captured by accident (typo paste,
wrong substrate, duplicate ingest) had no safe removal path.
Agents worked around it by editing the filesystem directly, which
bypasses the R6 write-surface guard and leaves no audit trail.

**parameterSemantics ceiling at 4.** v0.5.23's
`Annotated[T, Field(description=...)]` got every arg a description
but pydantic's `examples=[...]` was left empty. Glama's rubric
credits params with realistic example values.

### Fix

1. **Stripped `mcp_tool_aliases:`** from all 9 manifest entries
   (`src/myco/surface/manifest.yaml`). CLI `aliases:` preserved —
   `myco genesis`, `myco reflect`, etc. still work at the shell.
   Only the MCP-tool surface loses the duplicates. Regression test
   `test_v0_5_24_no_mcp_tool_aliases` guards against re-addition.

2. **Added `myco_excrete`** — new verb in the ingestion subsystem
   (`src/myco/ingestion/excrete.py`). Moves a single raw note from
   `notes/raw/` to `.myco_state/excreted/<stem>.md`, annotating
   frontmatter with `excreted_at` / `excreted_reason` /
   `excreted_from` for audit. Scope-locked to `notes/raw/` —
   targeting `notes/integrated/` or `notes/distilled/` is a
   `UsageError` (those tiers are protected by the append-only
   doctrine). Required args: `note-id` + `reason`. Optional:
   `--dry-run`. 11 regression tests cover dry-run, reason-required,
   note-id-required, write-surface violation, frontmatter
   annotation, apostrophe escaping, and stem-with-trailing-`.md`
   tolerance.

3. **Added `.myco_state/**`** to the default `write_surface.allowed`
   in `src/myco/germination/templates/canon.yaml.tmpl` (new
   substrates) and `_canon.yaml` (Myco-self). Without this, fresh
   substrates fail `myco_excrete` with a `WriteSurfaceViolation`
   for the tombstone path.

4. **Threaded `examples: [...]`** through `ArgSpec`,
   `_build_handler_signature`, `Annotated[T, Field(description=…,
   examples=[…])]`. Populated canonical examples for 36 args across
   16 verbs (every path, every required non-bool arg, every
   str-typed arg with a clear canonical value), including the new
   `excrete` verb, now ships realistic example values in the
   emitted JSON schema. Two new regression tests
   (`test_v0_5_24_examples_populated_on_high_value_args`,
   `test_v0_5_24_mcp_schema_embeds_examples`) lock this in.

### Break from v0.5.23

**MCP-client surface shrinks from 27 tools to 19.** The 9
deprecated aliases no longer appear in `tools/list` and will error
out on `tools/call`:

| Removed MCP alias | Canonical replacement |
|-----|-----|
| `myco_genesis` | `myco_germinate` |
| `myco_reflect` | `myco_assimilate` |
| `myco_distill` | `myco_sporulate` |
| `myco_perfuse` | `myco_traverse` |
| `myco_session_end` | `myco_senesce` |
| `myco_craft` | `myco_fruit` |
| `myco_bump` | `myco_molt` |
| `myco_evolve` | `myco_graft` |
| `myco_scaffold` | `myco_ramify` |

Migration is a mechanical rename in the client's tool-call site.
No argument shape changes — same handler, same schema, new name.

**CLI unchanged.** `myco genesis --project-dir ...` still works
and still emits a DeprecationWarning; no alias removal there.

### New verb contract

| Verb | MCP tool | Subsystem | Args |
|------|----------|-----------|------|
| excrete | myco_excrete | ingestion | note-id* / reason* / dry-run |

Payload shape:
```
{
  "exit_code": 0,
  "note_id": "<stem>",
  "from_path": "notes/raw/<stem>.md",
  "to_path": ".myco_state/excreted/<stem>.md",
  "reason": "<supplied>",
  "excreted_at": "<iso8601>",
  "dry_run": <bool>
}
```

### Expected Glama re-scan (v0.5.24)

- Mean TDQS: 3.77 → ~4.55 (canonical verbs only; aliases removed)
- Min TDQS: 2.90 → ~4.20 (weakest alias gone; only canonicals remain)
- Server TDQS: 3.77 → ~4.41 (0.6 × 4.55 + 0.4 × 4.20)
- Coherence completeness gap closed (excretion tool present)
- Final Quality: 3.78 A → ~4.5+ (A tier, near ceiling)

### Files touched

- `src/myco/surface/manifest.yaml` — removed 9 `mcp_tool_aliases`
  blocks, added `excrete` entry, added `examples:` to 36 args
- `src/myco/surface/manifest.py` — `ArgSpec.examples` field +
  loader wiring
- `src/myco/surface/mcp.py` — thread `examples` into
  `Annotated[..., Field(description=..., examples=...)]`
- `src/myco/ingestion/excrete.py` — new (~220 lines, full handler
  + frontmatter annotator)
- `src/myco/germination/templates/canon.yaml.tmpl` — `.myco_state/**`
  added to default write_surface
- `_canon.yaml` — `.myco_state/**` added; contract_version +
  synced_contract_version bumped
- `tests/unit/ingestion/test_excrete.py` — new, 11 tests
- `tests/unit/surface/test_manifest.py` — 4 v0.5.24 regression
  tests
- `tests/conftest.py` — seeded_substrate fixture covers
  `.myco_state/**`

Total: 207 new tests over v0.5.23 baseline (668 → 875).

---

## v0.5.23 — 2026-04-24 — Tool description richness (Glama TDQS C→A lift)

**Zero R1–R7 surface deltas.** Pure description-quality hotfix.
v0.5.22 scored C (2.53/5) on Glama's Tool Definition Quality
rubric; this release lifts every tool surface to satisfy the TDQS
six-dimension check.

### Symptom

Glama's TDQS scored Myco at C tier with server-level 2.53/5:
- `parameterSemantics: 1.22/5 avg` across all 27 tools
- `contextualCompleteness: 1.67/5 avg`
- `behavioralTransparency: 2.04/5 avg`
- Worst 4 tools at D tier (tdqs 1.7-1.9): `myco_immune`,
  `myco_winnow`, `myco_assimilate`, `myco_sense`

### Root cause

Two independent gaps:

1. **JSON schema emitted no parameter descriptions** because
   `_build_handler_signature` (added in v0.5.21 to fix the
   flat-args regression) wrapped types as bare annotations without
   Pydantic `Field(description=...)` metadata. Every tool showed
   "Schema description coverage is 0%" in Glama's per-tool
   justification.
2. **MCP tool descriptions were the one-line CLI `summary`** —
   correct for CLI `--help`, insufficient for LLM reasoning.
   Glama's rubric wants: what the tool does, when to use / NOT
   use, side effects / idempotency, return-value shape. One-liners
   score 2-3/5 on `purposeClarity` and 1-2/5 on every other
   dimension.

### Fix

- **`src/myco/surface/mcp.py`**: `_build_handler_signature` wraps
  every parameter's type in `Annotated[T, Field(description=arg.help)]`
  so Pydantic emits `description` into the JSON schema. The
  `project_dir` override parameter gets a full multi-sentence
  description covering the resolution chain.
- **`src/myco/surface/manifest.py`**: `CommandSpec` gains an
  optional `description: str = ""` field + `mcp_description`
  property that returns `description` when set, falling back to
  `summary`. Loader plumbs the new yaml key through.
- **`src/myco/surface/manifest.yaml`**: every one of the 18
  canonical verbs now has a multi-paragraph `description:` field
  covering (1) what it does, (2) when to use / when NOT to use /
  disambiguation from siblings, (3) side effects + R6 write-
  surface implications, (4) return shape. Every arg's `help:`
  field enriched to cover: what it controls, valid values /
  format, default behavior when omitted, interactions with other
  args. Manifest went from 343 → ~700 lines of structured prose.
- **`src/myco/surface/mcp.py::build_tool_spec`**: uses
  `spec.mcp_description` as the tool description (was
  `spec.summary`).

### Regression tests

- `test_every_verb_has_tool_spec` updated to check against
  `spec.mcp_description` (the new fallback-aware accessor).
- `test_every_verb_has_rich_mcp_description` — new: every canonical
  verb's description must be >= 200 chars (floor for "covers
  what/when/side-effects").
- `test_every_param_has_schema_description` — new: every parameter
  on every tool, as seen in FastMCP's emitted `inputSchema`, must
  have a non-empty `description` >= 20 chars. Guards the
  Annotated/Field wiring against future signature-builder
  regressions.

All 859 pre-existing tests still pass. Ruff + mypy + immune clean.

### Break from v0.5.22

None for MCP protocol. Tool schemas have richer metadata (extra
`description` fields per parameter, longer top-level tool
descriptions) — strictly additive from the client's perspective.
Pydantic emits these as JSON schema `description` keys which
well-behaved MCP clients either use or ignore.

CLI `--help` output for verbs is unchanged (still shows short
`summary`; the long `description` is MCP-only).

### Operator action

1. `pip install -U myco` to get 0.5.23 in your local Python env.
   (Note: close all Claude Code / Claude Desktop sessions first —
   Windows file-lock contract from v0.5.20 onboarding.)
2. Visit <https://glama.ai/mcp/servers/Battam1111/Myco> → Admin →
   click **Build & Release** to trigger a re-scan against the new
   v0.5.23 manifest.
3. Expect per-tool tdqs to rise from ~2.5 avg (C) to ~3.5+ (A) on
   re-scan. Server-level quality should flip from C to A.

### Lesson

Glama's TDQS is a well-designed LLM-as-judge rubric that rewards
pre-LLM-era-good-API-documentation hygiene: stable parameter
descriptions, explicit "when to use" notes, documented side
effects, return-shape commitments. v0.5.22's assumption that
"correct JSON schema shape" was sufficient missed that the rubric
grades *semantic* richness on top of *structural* correctness.
Future MCP server releases should budget for description writing
alongside code writing — they are different skills and the LLM
judge can tell.

---

## v0.5.22 — 2026-04-23 — Dogfood bugfixes: local_plugins scope + URL adapter error

**Zero R1–R7 surface deltas.** Pure observability / UX hotfix
surfaced by an end-to-end dogfood run of all 18 verbs.

### Fixes

- **`hunger.local_plugins` / `brief`'s "Local plugins" section** now
  count **substrate-local** plugins only. Pre-v0.5.22 they counted
  every kernel-built-in dimension + adapter + schema_upgrader as a
  "local plugin", so every fresh substrate reported misleading
  "32 local plugins" on first hunger. Root cause: ``hunger._summarize_local_plugins``
  and ``brief._local_plugins_section`` both read the global registries
  and returned a raw total. Fix: delegate to ``graft._collect_plugins``
  which now stamps each entry with a ``scope`` field (``"kernel"`` vs
  ``"substrate"``); hunger + brief filter for ``scope == "substrate"``
  so only genuine ``.myco/plugins/*`` contributions count. Fresh
  substrate now correctly reports 0; a substrate with one ramified
  dimension reports 1.

- **`eat --url` error now surfaces the real rejection reason.** When
  the URL adapter's SSRF guard refused a host (loopback / link-local
  / private / reserved IP ranges), the old error said "No adapter
  can handle 'https://...'. Install 'myco[adapters]' for PDF, HTML
  and URL support" — actively misleading, since the adapter *was*
  installed and *was* loaded. New error surfaces the specific
  UrlFetchError message (e.g. "URL adapter refused: url host
  'example.com' resolves to a non-routable address") so operators
  can distinguish a corporate-network DNS quirk from a genuine
  block. Not a new escape hatch — the SSRF guard still fires — just
  an honest error message.

### Shape changes

- `graft --list` payload entries gain a ``scope`` key (``"kernel"``
  or ``"substrate"``). Existing consumers that didn't know about
  ``scope`` continue to work — the field is additive.

### Tests

- `tests/unit/ingestion/test_hunger_count_by_kind.py` now asserts
  zero local plugins on a fresh substrate (pre-v0.5.22 this test
  asserted the bug as a feature — `dimension >= 1`).
- `tests/unit/cycle/test_graft.py` gains two tests locking the
  ``scope`` field shape + the fresh-substrate-all-kernel invariant.
- `tests/unit/ingestion/test_eat.py` gains three tests for the URL
  error path: helper function returns the SSRF reason for a
  loopback URL, returns None for non-URL targets, and the full
  ``eat`` run surfaces "URL adapter refused" rather than the
  "Install myco[adapters]" misdirection.

### Break from v0.5.21

None for anyone reading the raw `local_plugins.count`. Anyone who
was *depending* on "fresh substrate reports 32+" (no one should be)
would see a 0 there now — but that's the whole point of the fix.

### Dogfood findings NOT fixed in this release

- **CLI `--project-dir` position asymmetry**: `myco VERB --project-dir X`
  fails; must be `myco --project-dir X VERB`. MCP surface accepts it
  as a per-verb kwarg. Tracked for v0.5.23.
- **CLI `myco sense "query"` (positional)**: requires `--query`.
  Tracked for v0.5.23.

---

## v0.5.21 — 2026-04-23 — MCP handler schema hotfix (flat-args regression)

**Zero R1–R7 surface deltas.** Pure host-axis hotfix. Any verb that
takes parameters was unusable via MCP in v0.5.20 and earlier — this
release makes them work.

### Symptom

`myco_eat`, `myco_sense`, `myco_digest`, and every other
parameter-taking verb returned

```
eat: must pass one of --content '<text>' | --path <file-or-dir> | --url <url>.
```

regardless of what the agent put in the MCP tool call input.
`myco_hunger` / `myco_forage` / `myco_immune` / `myco_traverse`
kept working because they have no required args — their handlers
don't care if the kwargs dict is empty.

### Root cause

`build_server` in `myco.boundary.surface.mcp` registered every verb as:

```python
async def _handler(ctx: Context, **kwargs: Any) -> dict: ...
```

FastMCP's schema derivation (in
`mcp.server.fastmcp.utilities.func_metadata`) runs
`inspect.signature(fn)` and sees `**kwargs: Any` as **a single
required dict parameter named `"kwargs"`** — not as a varkw sink.
The emitted JSON Schema was:

```json
{"required": ["kwargs"], "properties": {"kwargs": {...}}, "type": "object"}
```

Agents following that schema sent either:

- `{"content": "..."}` (flat, because the agent has common sense) →
  pydantic ValidationError at the MCP boundary: `kwargs: Field required`.
- `{"kwargs": {"content": "..."}}` (nested, matching the schema) →
  FastMCP binds `kwargs = {"content": "..."}` which collects into
  the handler's Python varkw as `{"kwargs": {"content": "..."}}`.
  Then `build_handler_args(eat, {"kwargs": {...}})` treats the
  top-level key `kwargs` as unknown and defaults every declared
  manifest arg (`content`, `path`, `url`) to `None`. Eat's handler
  reads `args.get("content")` → `None` → UsageError.

Either way, the real args never reached the verb. And because the
tool schema lied about the shape, agents couldn't discover the
correct call shape from the tool's own advertised surface.

### Fix

`src/myco/surface/mcp.py`:

- New `_build_handler_signature(spec)` builds an
  `inspect.Signature` with one `Parameter` per manifest arg
  (typed, defaulted per manifest), plus `ctx: Context` and an
  optional `project_dir` override.
- `_make_handler` now assigns that Signature to the handler's
  `__signature__` before registration. FastMCP's introspection
  respects `__signature__`, so the emitted JSON Schema now has one
  property per verb input — no "kwargs" wrapper. Python runtime
  still gets `**kwargs` in the actual function body, so nothing
  else about binding changes.
- Handler body drops `None` values before `_invoke` so optional
  args that FastMCP default-binds to `None` don't shadow the
  manifest's own default-providing logic in `build_handler_args`
  (relevant for args like `source` whose manifest default is
  `"agent"`, not `None`).

### Tests

Seven regression tests lock the fix shape (`tests/unit/surface/test_mcp.py`):

- `test_handler_signature_has_manifest_args_not_varkw` — no verb
  handler may expose a bare `**kwargs` to introspection.
- `test_handler_signature_marks_required_args_without_default` —
  `required: true` manifest args surface as default-less Parameters.
- `test_handler_signature_exposes_project_dir_override` —
  multi-project routing override is discoverable on every verb.
- `test_fastmcp_tool_schema_exposes_individual_properties` —
  end-to-end schema shape via `build_server().list_tools()`.
- `test_fastmcp_call_eat_with_flat_args_succeeds` — closing
  regression: actual `myco_eat` flat call over FastMCP succeeds.
- `test_fastmcp_call_sense_with_flat_query_arg_succeeds` — same
  for a required-arg verb (different pydantic codepath).
- `test_fastmcp_none_values_dont_shadow_manifest_defaults` — guards
  the None-stripping in the handler body.

### Break from v0.5.20

None for well-formed agents. Agents that were working around the
bug by sending nested `{"kwargs": {...}}` will now see their
double-wrapped args split across two namespaces (top-level
`kwargs` is now an undeclared property and gets preserved by
`build_handler_args` but ignored by the verb handlers). In
practice: nobody was successfully using the nested shape (it
couldn't reach the handler either way), so there's no real break.

### Operator action

```
pip install -U myco            # or pip install --upgrade myco[mcp]
```

Then restart any open Cowork / Claude Desktop session so the MCP
server boots with the fixed code. No re-upload of the `.plugin`
bundle needed — the bundle only declares which Python module to
spawn (`python -m myco.boundary.mcp`); the module code comes from the
user's PyPI install.

### Lesson

v0.5.20 shipped a plugin bundle that routed every manifest verb
to an MCP handler that the MCP surface couldn't actually dispatch
to — and no test caught it because the tests called `_invoke`
directly (the internal dispatcher), bypassing FastMCP's schema
derivation entirely. The regression gap was "we tested the
dispatcher" without "we tested the MCP boundary the client talks
to." v0.5.21 closes that gap by exercising `FastMCP.call_tool` in
its tests, not just `_invoke`. Future MCP changes must pass
through `call_tool` in at least one test before shipping.

---

## v0.5.20 — 2026-04-23 — Cowork plugin install: retraction + drag-drop fix

**v0.5.19 shipped a broken installer.** This release retracts the
"permanent fix" framing and delivers the actual permanent fix.

### What v0.5.19 claimed vs what actually happened

v0.5.19's `myco-install cowork-plugin` wrote a plugin tree into
`<APPDATA>/Claude/local-agent-mode-sessions/<owner>/<ws>/rpm/plugin_myco/`
and upserted an entry in each `rpm/manifest.json`. The release
changelog described this as "the permanent fix for agent onboarding
in Cowork." It is not. Cowork's `[RemotePluginManager]` regenerates
`rpm/manifest.json` from an Anthropic cloud marketplace on **every
session start**, and sync runs drop any `plugins[]` row that does not
correspond to a cloud entry — the v0.5.19 writes are wiped silently
between sessions.

Symptom (as reported on 2026-04-23): after restart and a fresh Cowork
session, the `myco-substrate` skill was missing from the agent's
available-skills list even though the installer exited zero a moment
earlier. Direct inspection confirmed `rpm/manifest.json` no longer
contained the `plugin_myco` row we wrote.

### Root cause

The source of truth for Cowork plugins is an Anthropic cloud
marketplace (`marketplace_01UDYDZqTLSQBkNqpTGCfzNM` for account
uploads), not the local `rpm/` directory. Claude Desktop's drag-drop
UI POSTs the bundle to
`https://api.anthropic.com/api/organizations/{orgId}/marketplaces/{marketplaceId}/plugins/account-upload`,
and the server-side record is what every Cowork session syncs from.
`rpm/` is a cache, never a source. Reading the decompiled
`app.asar:433299-433340` confirmed this end-to-end.

### v0.5.20 fix

- **New `src/myco/install/plugin_bundle.py`**: builds a
  `myco-<version>.plugin` ZIP (single top-level dir `myco/` holding
  `.claude-plugin/plugin.json` + `.mcp.json` + `skills/myco-substrate/`
  — the layout Claude Desktop's upload handler validates against).
- **New `scripts/build_plugin.py`**: thin CLI wrapping the library;
  the GitHub Release workflow now runs it and attaches the `.plugin`
  as a release asset, so users can either `curl -L` the latest or
  `python scripts/build_plugin.py` from a repo checkout.
- **`myco-install cowork-plugin` rewritten**: drops the `rpm/` writer
  entirely. Default action now builds the bundle, prints exact
  drag-drop instructions, and exits. `--cleanup-legacy` removes
  v0.5.19-era cruft (`rpm/plugin_myco/` dirs + manifest rows).
- **`myco-install host cowork` + `--all-hosts`**: the flow that
  auto-ran the (broken) plugin install now builds the bundle and
  prints upload instructions instead. Uninstall paths are silent —
  removing the plugin is a user action in Claude Desktop's UI.
- **Legacy-function regression guard**: the old
  `install_cowork_plugin()` function now raises `RuntimeError` with a
  migration message, so any script that still imports it gets a loud
  failure rather than a silent wrong install.
- **Release workflow**: `.github/workflows/release.yml` adds a
  `.cowork-plugin/plugin.json` version check alongside the existing
  four-file parity gate, builds the `.plugin`, and uploads it via
  `gh release upload` with `--clobber` for idempotency.

### What did NOT change

- **R1–R7 rule text.** Unchanged.
- **Category enum / exit-policy / exit codes.** Unchanged.
- **18-verb manifest.** Unchanged.
- **25 lint dimensions.** Unchanged.
- **Claude Code plugin bundle** (`.claude-plugin/` at repo root).
  Unchanged — that install path works correctly and was never
  affected by the `rpm/` misunderstanding.

### Break from v0.5.19

Cosmetic. The CLI still has `myco-install cowork-plugin`, but its
flags and behavior differ: `--uninstall` is gone (no CLI uninstall —
remove through Claude Desktop UI), replaced with `--cleanup-legacy`;
new `--output` controls where the `.plugin` file is written.
Anyone whose v0.5.19 install "succeeded" should run:

```bash
myco-install cowork-plugin --cleanup-legacy
```

to scrub the residue, then follow the drag-drop upload flow below.

### Operator action

```bash
# 1. MCP config (write once)
myco-install host cowork

# 2. Build the .plugin bundle
myco-install cowork-plugin
# or:
curl -L -o myco.plugin https://github.com/Battam1111/Myco/releases/latest/download/myco.plugin

# 3. Drag dist/myco-<version>.plugin into Claude Desktop:
#    Settings → Plugins (or Extensions) → Upload → select the file
# 4. Restart any open Cowork session
```

Full rationale + screenshots: `docs/INSTALL.md § 1.1`.

### Lesson

v0.5.19 shipped a fix whose correctness I verified only by checking
the post-install filesystem state, not by checking the post-restart
filesystem state. The regression shipped because "installer wrote to
disk successfully" and "plugin persists across restarts" are
different claims and I tested only the first. Future host-axis
installers must be tested end-to-end across a session restart before
shipping a "permanent fix" label.

---

## v0.5.19 — 2026-04-23 — Cowork plugin install: the permanent onboarding fix

> **Retracted by v0.5.20.** The "permanent fix" claim below turned
> out to be wrong — the installer wrote to a local cache Cowork
> regenerates from cloud on every restart. v0.5.20 ships the actual
> fix (drag-drop `.plugin` upload). Keeping this section intact for
> archaeology; the narrative below describes the intent, not the
> shipped behavior. See v0.5.20 above for the post-mortem.

Contract-layer patch with **zero R1–R7 surface deltas**. Everything in
v0.5.19 lives at the host-axis of the extensibility model (see
`docs/architecture/L3_IMPLEMENTATION/symbiont_protocol.md`), not at
the contract itself.

### What changed

- **Nothing in R1–R7 rule text.**
- **Nothing in the category enum / exit-policy / exit codes.**
- **Nothing in the 18-verb manifest surface.**
- **Nothing in the dimension roster count** (still 25).

### The problem this release fixes

Cowork (Claude Desktop's local-agent-mode) is a first-class Myco
host, but until now the agent wouldn't *recognize* a Myco substrate
without the user explicitly asking for it. Unlike Claude Code, Cowork
does not implement the SessionStart / PreCompact hook contract the
`.claude/hooks/` entries ride on — those hooks never fire in Cowork
sessions.

Diagnostically: the user opens a Cowork workspace with `_canon.yaml`
at its root, and the agent's first turn proceeds as if Myco isn't
there. Only after the user says "run `myco hunger`" does the agent
connect the dots. R1 is effectively unenforced.

### The fix

Cowork *does* honor **Skills** — markdown files with YAML frontmatter
that the host matches against user intent + agent context. v0.5.19
ships a `.cowork-plugin/` template carrying a single skill
(`myco-substrate`) plus an installer that drops it into every Cowork
workspace registry on this machine.

New surface:

- **`.cowork-plugin/`** template tree (plugin.json + skills/myco-
  substrate/SKILL.md + .mcp.json + README.md). The SKILL.md body is
  the full onboarding brief: what Myco is (cognitive substrate, NOT
  memory tool — this framing is enforced by
  `test_cowork_skill_body_asserts_correct_framing`), 18 verbs by
  subsystem, R1-R7 contract text, how to read `substrate_pulse`,
  first-call checklist, multi-project pattern with `project_dir=`
  override, and a "what NOT to do" guardrail list.
- **`src/myco/install/cowork_plugin.py`** — library installer.
- **`scripts/install_cowork_plugin.py`** — thin shim over the library
  for users who clone the repo without running `pip install -e .`.
- **`myco-install cowork-plugin`** — first-class subcommand with
  `--dry-run` / `--uninstall` / `--cowork-root`.
- **`myco-install host cowork`** now writes the MCP config *and*
  installs the plugin tree in one step.
- **`myco-install host --all-hosts`** auto-runs the Cowork plugin
  install whenever it detects Claude Desktop — one command, every
  host on this machine primed, Cowork onboarding included.

The installer is idempotent: re-running upserts the manifest row and
refreshes the plugin tree without creating duplicates. `--uninstall`
is symmetric — removes the tree + manifest row, preserves sibling
entries (e.g. cowork-plugin-management, productivity from the Anthropic
marketplace).

### Cross-cutting infrastructure

- **`_canon.yaml::system.write_surface.allowed`** adds
  `.cowork-plugin/**`.
- **`scripts/bump_version.py`** now bumps `.cowork-plugin/plugin.json`
  in lockstep with the repo-root `.claude-plugin/plugin.json`, so
  both plugin bundles always carry the same version as the Python
  package + PyPI release + MCP Registry entry.
- **`tests/integration/test_cowork_plugin_bundle.py`** — template
  structural invariants (plugin.json + .mcp.json parse; SKILL.md
  frontmatter shape; skill body carries the correct framing + R1-R7
  + pulse contract).
- **`tests/integration/test_install_cowork_plugin.py`** — installer
  behavior on synthetic appdata: discovery walks the glob correctly,
  idempotent upsert preserves sibling plugins, dry-run never writes,
  uninstall is symmetric, OS-specific appdata resolution on Windows
  / macOS / Linux, `--all-hosts` side-effect fires when Claude
  Desktop is detected.
- **README + README_zh + README_ja + docs/INSTALL.md** — corrected
  the Cowork install instruction (was wrongly pointing at the
  Claude Code `/plugin marketplace` command; Cowork does not
  support it).

### Why a contract bump if R1–R7 didn't change?

Precedent set at v0.5.17: onboarding-surface changes that shift
which rule the agent sees first at boot time (R1 → skill-mediated
vs R1 → hook-mediated) count as contract-adjacent and earn a bump.
The skill body in `.cowork-plugin/skills/myco-substrate/SKILL.md`
is agent-facing contract material — if Myco's framing changes in
future releases (e.g. "cognitive substrate" → something else),
that *is* a contract change even though no rule number moves.

### Break from v0.5.18

None. Pure additive. Claude Code users unaffected (the old
`.claude-plugin/` bundle still ships). Cowork users who previously
got by on ad-hoc reminder prompts will now see the agent
auto-orient at session start.

### Operator action

After `pip install -U myco` (or restart of an editable install),
users who want the Cowork fix should run:

```
myco-install cowork-plugin           # installs skill + manifest entries
# or
myco-install host --all-hosts        # does everything else too
```

then restart Claude Desktop. On the next Cowork session the agent
will follow R1-R7 the moment it sees `_canon.yaml` or the user
mentions Myco.

---

## v0.5.18 — 2026-04-23 — auto-germ pulse carries transparency fields

Contract-layer patch with **zero contract-surface deltas**. v0.5.17
oversight: the auto-germ soft-fail path
(``_auto_germ_advice_response``) builds its own pulse dict inline
rather than going through ``_compute_substrate_pulse``, so it
missed the ``project_dir_source`` + ``resolved_project_dir`` fields
that v0.5.17 added to every other dispatch response.

### What changed

- **Nothing in the R1–R7 rule text.**
- **Nothing in the category enum / exit-policy / exit codes.**
- **Nothing in the 18-verb manifest surface.**
- **Nothing in the dimension roster count** (still 25).

### Fixed — auto-germ advice pulse now includes the transparency fields

Reaching ``_auto_germ_advice_response`` proves that
``_detect_workspace_root`` returned a ``file://`` root from the MCP
client, so the patched pulse can confidently report:

    "project_dir_source": "mcp.roots/list (root has no substrate)"
    "resolved_project_dir": "<workspace root path>"

Two-part diagnostic value:
- Confirms ``roots/list`` IS working on this host (previously the
  operator would wonder whether it was even reached).
- Names the exact workspace path the client exposed (for when the
  client claims workspace X but Myco expected Y).

### Break from v0.5.17

None. This patch is purely additive to the auto-germ path's pulse.

Observable delta: operators running a Myco tool in a workspace that
has no substrate will now see the ``project_dir_source`` +
``resolved_project_dir`` keys in the pulse sidecar (they were absent
in v0.5.17 for this specific branch).

---

## v0.5.17 — 2026-04-23 — Resolution transparency in pulse + multi-project hint in init instructions

Contract-layer molt with **zero contract-surface deltas**. Diagnostic
v0.5.14 left out — the one the user correctly asked for after
v0.5.16 shipped: the pulse sidecar now tells the agent WHICH level
of the substrate-resolution chain answered.

### Motivation

v0.5.14 + v0.5.16 built the auto-resolve-via-MCP-roots path. But
Claude Desktop's MCP client does not advertise the ``roots``
capability (verified in live logs — client sends
``capabilities: {extensions: ...}`` with no ``roots`` key). Every
``_resolve_project_via_roots`` call returned None, the chain fell
through to env/cwd, and operators saw "substrate_id was the same in
every workspace" with no way to tell why.

The fix: surface the chain.

### What changed

- **Nothing in the R1–R7 rule text.**
- **Nothing in the category enum / exit-policy / exit codes.**
- **Nothing in the 18-verb manifest surface.**
- **Nothing in the dimension roster count** (still 25).

### Added — ``project_dir_source`` + ``resolved_project_dir`` pulse fields

Every MCP tool response now carries, in ``substrate_pulse``:

- ``project_dir_source`` — one of ``kwargs.project_dir`` /
  ``mcp.roots/list`` / ``env.MYCO_PROJECT_DIR`` /
  ``env.CLAUDE_PROJECT_DIR`` / ``Path.cwd()``.
- ``resolved_project_dir`` — the actual filesystem path Myco used
  as the resolution's starting point.

The two fields are omitted (rather than lying) when the caller
doesn't know the source (CLI path).

### Moved — substrate-resolution chain centralised in ``_invoke``

v0.5.14 split the resolution chain between ``_invoke`` (levels 1-2)
and ``build_context`` (levels 3-4). v0.5.17 has ``_invoke`` own all
five levels end-to-end, tracking ``source`` as each answers, so the
pulse can report the exact level. ``build_context`` still has its
own chain for CLI callers; the two are kept in sync manually and
both are pinned by tests.

### Added — multi-project hint in initialization instructions

The MCP ``initialize``-time instructions block now tells agents:
"When you know which project folder the user is working on, pass
``project_dir="<absolute path>"`` in every tool call's kwargs".

This is the actionable workaround for MCP clients that don't
implement ``roots/list`` (Claude Desktop / Cowork as of writing).
Agents that read initialization instructions will see the hint and
route tool calls correctly even on non-roots-capable hosts.

### Break from v0.5.16

None at the contract layer. Operators upgrading from v0.5.16
require no code, canon, or script changes.

Observable deltas:
- Every MCP tool response gains two new pulse fields. Consumers
  that parse the pulse with ``dict.get`` see new keys; strict
  typed consumers may need a schema update.
- Agents that follow the updated initialization instructions will
  start passing ``project_dir`` in kwargs, overriding fallback
  resolution. This is the correct behaviour; it matches what the
  user wanted from v0.5.14.

---

## v0.5.16 — 2026-04-22 — Global substrate registry + auto-germ advice + graft --list-substrates

Contract-layer molt with **zero contract-surface deltas**. Third
ergonomic release in the one-劳永逸 arc (v0.5.14 + v0.5.15 + v0.5.16).
Closes the last three cross-project UX gaps: operators need to be
able to enumerate every substrate they've germinated, germinate
a new one inside a workspace the host has opened without seeing an
error, and have the registry accumulate on its own without manual
intervention.

### What changed

- **Nothing in the R1–R7 rule text.**
- **Nothing in the category enum / exit-policy / exit codes.**
- **Nothing in the 18-verb manifest surface.** (Graft grew a flag,
  not a new verb.)
- **Nothing in the dimension roster count** (still 25).

### Added — `~/.myco/substrates.yaml` global substrate registry

New module ``myco.core.registry``:

- ``register_substrate(id, path)`` — upsert a row. Idempotent.
- ``touch_substrate(id, path)`` — best-effort last-seen update.
- ``list_substrates()`` — enumerate all, sorted by recency.
- ``SubstrateEntry.exists`` — live vs stale filter.

File format: YAML map keyed by ``substrate_id``, one row per
substrate with ``path`` / ``registered_at`` / ``last_seen_at``.
Atomically written via ``atomic_utf8_write``; concurrent writes
never corrupt. Malformed files degrade to empty registry — never
raises into the calling code.

Per-user only; never shared across machines; never committed to
VCS. Mirrors shell-history / editor-recent-files semantics.

### Added — germinate → registry auto-hook

``myco.germination.germinate.bootstrap`` now calls
``register_substrate()`` on every successful (non-``--dry-run``)
germination. Failures (disk full, perms) are swallowed — a
registry-write error must never break germination. ``--dry-run``
skips the registry write entirely, matching its "write nothing"
contract.

### Added — `myco graft --list-substrates` flag

New mode on the existing ``graft`` verb. Mutually-exclusive with
``--list`` / ``--validate`` / ``--explain``. Returns the full
registry (across projects) with ``count`` / ``live_count`` /
``stale_count`` counters. Example payload entry:

    {
      "substrate_id": "c3-neurips2026",
      "path": "C:\\Users\\10350\\Desktop\\C3",
      "registered_at": "2026-04-22T13:29:11+00:00",
      "last_seen_at":  "2026-04-23T09:14:05+00:00",
      "exists": true
    }

Agent tooling integrates via the ``myco_graft`` MCP tool's new
``list_substrates`` kwarg.

### Added — auto-germ advice soft response in `_invoke`

When the MCP client exposes a workspace root (via ``roots/list``)
but that root has no ``_canon.yaml``, v0.5.15 would raise
``SubstrateNotFound`` with a message. v0.5.16 upgrades the UX:
the MCP layer catches the exception, captures the first ``file://``
root from the client via a new ``_detect_workspace_root`` helper,
and returns a SOFT response whose ``substrate_pulse.rules_hint``
tells the agent to call ``myco_germinate`` with the workspace path.

``exit_code`` stays 4 (the canonical ``SubstrateNotFound`` code per
v0.5.8's contract), the payload carries ``workspace_root`` as a
first-class field, and the agent reads the advice and offers to
germinate. Never auto-germinates silently — that would be surprising.

### Break from v0.5.15

None at the contract layer. Operators upgrading from v0.5.15
require no code, canon, or script changes.

Observable deltas:
- ``myco germinate`` writes a row to ``~/.myco/substrates.yaml``
  on every successful non-dry-run call. Users who want to opt out
  can ``rm ~/.myco/substrates.yaml`` at any time; Myco reads None
  gracefully. Future doctrine work may add a ``canon`` opt-out
  flag; today the registry is always-on.
- Fresh workspaces opened in Cowork / Claude Desktop / Cursor / …
  used to surface ``SubstrateNotFound`` errors on the first Myco
  tool call. They now surface a germinate-this-workspace hint in
  the pulse sidecar instead, which the agent can relay.
- ``myco graft`` now has a fourth mode (``--list-substrates``)
  in addition to ``--list`` / ``--validate`` / ``--explain``.
  Existing invocations unchanged.

---

## v0.5.15 — 2026-04-22 — Universal host installer (`--all-hosts`) + cowork alias

Contract-layer molt with **zero contract-surface deltas**. Closes
the ergonomic gap v0.5.14 left open: auto-discovery at runtime is
free, but first-time host configuration still required 10 separate
commands. v0.5.15 compresses that to one.

### What changed

- **Nothing in the R1–R7 rule text.**
- **Nothing in the category enum / exit-policy / exit codes.**
- **Nothing in the 18-verb manifest surface.**
- **Nothing in the dimension roster count** (still 25).

### Added — `myco-install host --all-hosts`

`myco-install` grows a new flag that auto-detects every MCP host
installed on the operator's machine and runs the per-host install
for each detection hit:

```
$ myco-install host --all-hosts
[installed] claude-code  →  wrote ~/.claude.json
[installed] claude-desktop  →  wrote %APPDATA%/Claude/claude_desktop_config.json
[installed] cursor  →  wrote ~/.cursor/mcp.json
[skipped]   windsurf  (not detected on this machine)
[skipped]   zed  (not detected on this machine)
...
3/3 host(s) installed, 8 skipped, 0 errored.
```

Detection probes each host's user-level config directory (`~/.cursor/`,
`~/.codex/`, `%APPDATA%/Claude/`, …) plus `shutil.which("openclaw")`
for the one binary-on-PATH host. Hosts absent from the probe signal
are skipped with a note; they can still be installed manually by
name.

`--all-hosts` implies `--global`: the intent is "every host on this
machine knows where Myco is, regardless of which folder I'm in", so
writing project-level configs to whatever cwd happens to be active
would be the wrong level of scope.

Public API: `myco.boundary.install.clients.detect_installed_hosts(home=None)`
returns `{client: signal-or-None}` for every entry in `CLIENTS`.
Callers use it to drive custom provisioning flows.

### Added — `cowork` as an explicit host target

Cowork is a mode inside Claude Desktop — the config file is shared
(`claude_desktop_config.json`). Previously operators searching for
"Cowork MCP setup" had to know this; now `myco-install host cowork`
just works and writes the right file. The `--all-hosts` path
dedups so we don't write the same file twice.

### Break from v0.5.14

None at the contract layer. Operators upgrading from v0.5.14
require no code, canon, or script changes.

Observable delta:
- Operators with multiple MCP hosts installed can now run one
  command instead of ten.
- The positional `client` argument on `myco-install host` is now
  optional (``nargs="?"``) — it's required when `--all-hosts` is
  absent, forbidden-in-intent when `--all-hosts` is present. The
  CLI emits a clear usage error when neither is given.

---

## v0.5.14 — 2026-04-22 — MCP roots/list auto-discovery (a.k.a. "一劳永逸")

Contract-layer molt with **zero contract-surface deltas**. The
strategic answer to "do I have to configure every project on every
host forever?" — no, you don't, because Myco now uses the MCP
protocol's own ``roots/list`` channel to discover the user's
workspace automatically on any spec-compliant client.

### What changed

- **Nothing in the R1–R7 rule text.**
- **Nothing in the category enum, the exit-policy grammar, or the
  exit-code ladder.**
- **Nothing in the 18-verb manifest surface.**
- **Nothing in the dimension roster count** (still 25).

### Added — MCP ``roots/list`` auto-discovery

The MCP protocol defines a standard server-to-client RPC
(``roots/list``) that lets the server ask the host which folder(s)
the user currently has open. Every spec-compliant client — Cowork /
Claude Desktop, Cursor, Zed, Windsurf, VS Code, Codex, Gemini,
Continue, OpenHands, OpenClaw — supports it. v0.5.13 and earlier
never used this channel; v0.5.14 does, and it fixes the
substrate-discovery problem universally.

New flow inside ``myco.boundary.surface.mcp._invoke``:

  1. Pull ``kwargs.project_dir`` if explicitly given.
  2. Otherwise, query ``session.list_roots()`` and walk each
     returned root's ancestry for a ``_canon.yaml``.
  3. Otherwise, fall through to ``MYCO_PROJECT_DIR`` (v0.5.13) or
     ``CLAUDE_PROJECT_DIR`` (new, see below).
  4. Finally, ``Path.cwd()`` as the legacy floor.

Failure modes of levels 2–4 are all graceful: the MCP call
short-circuits as soon as something answers; if nothing answers,
a new and much more useful ``SubstrateNotFound`` message explains
exactly which paths were tried and what the three fix routes are.

### Added — ``CLAUDE_PROJECT_DIR`` env fallback

``build_context``'s env-var ladder now also reads
``CLAUDE_PROJECT_DIR`` (after ``MYCO_PROJECT_DIR``). Claude Code
injects this variable in hook processes (SessionStart, PreCompact,
SessionEnd). Honouring it means shared Claude-Code + Myco setups
need zero Myco-specific env wiring.

### Fixed — latent ``kwargs.project_dir`` drop bug

The MCP layer extracted ``kwargs.project_dir`` only long enough to
label the substrate-pulse sidecar — it was dropped by
``build_handler_args`` before reaching the actual ``build_context``
call. In practice, the only way to steer a verb to a non-default
substrate was the new env-var fallback (v0.5.13) or the shell
cwd. v0.5.14 extracts ``project_dir`` BEFORE dispatch and passes it
as a first-class parameter, so the per-call override works as
documented.

### Fixed — ``SubstrateNotFound`` error message

Previously said simply ``no substrate at or above {cwd}``. Now
enumerates every detection path tried (explicit arg, MYCO_PROJECT_DIR,
CLAUDE_PROJECT_DIR, cwd) so operators can tell whether a env var
was silently dropped, whether they forgot to set one, or whether
their cwd is somewhere unexpected. Also surfaces the three fix
options (germinate, env, workspace-roots) in the error body.

### Break from v0.5.13

None at the contract layer. Operators upgrading from v0.5.13
require **no code changes, no canon edits, no script adjustments**.

Observable deltas:
- On Cowork / Claude Desktop / Cursor / Zed / Windsurf / etc., a
  freshly-germinated substrate is auto-discovered the moment you
  open its folder — no config-file edits, no env-var pinning.
  ``MYCO_PROJECT_DIR`` is still honoured when set; it just isn't
  required.
- Users who previously pinned ``env: MYCO_PROJECT_DIR`` in their
  host configs can remove that line on v0.5.14+ without breaking
  anything, as long as they open the substrate's folder as a
  workspace in the host.
- ``kwargs.project_dir`` passed by an agent now actually routes to
  the correct substrate (previous versions silently dropped it and
  used cwd/env).

---

## v0.5.13 — 2026-04-22 — MYCO_PROJECT_DIR env-var fallback + bump-script UTF-8 fix

Contract-layer molt with **zero contract-surface deltas**, same
class as v0.5.9 through v0.5.12. Ships one feature + one tooling fix.

### What changed

- **Nothing in the R1–R7 rule text.**
- **Nothing in the category enum, the exit-policy grammar, or the
  exit-code ladder.**
- **Nothing in the 18-verb manifest surface.**
- **Nothing in the dimension roster count** (still 25).

### Added — `MYCO_PROJECT_DIR` env-var fallback

`myco.boundary.surface.manifest.build_context` now reads a three-level
substrate-resolution chain:

  1. Explicit `project_dir` argument (CLI `--project-dir`, MCP
     `kwargs.project_dir`).
  2. **`MYCO_PROJECT_DIR` environment variable (new).**
  3. `Path.cwd()` — legacy behaviour, unchanged.

**Why.** Claude Desktop — and by inference several other MCP hosts —
spawns MCP server subprocesses with `cwd = C:\Windows\System32` on
Windows and silently drops the `mcpServers.<name>.cwd` field from
the host config. Without this feature, any substrate outside the
host process's own cwd was unreachable: `find_substrate_root`
walked up from System32, found no `_canon.yaml` anywhere, and
raised `SubstrateNotFound` on every tool call.

**The fix.** `env` *is* part of the standard MCP config schema and
every host honours it. Operators pin a substrate via:

    "myco": {
      "command": "...",
      "args": ["-m", "myco.boundary.mcp"],
      "env": { "MYCO_PROJECT_DIR": "/path/to/substrate" }
    }

`~` expansion runs on the env-var path so `MYCO_PROJECT_DIR=~/project`
works cross-platform without relying on shell expansion.

**Tests.** Three new unit tests in `tests/unit/surface/test_manifest.py`
cover the three precedence outcomes — env wins over cwd, explicit
arg wins over env, whitespace-only env falls through to cwd.

### Fixed — `scripts/bump_version.py` Windows console UnicodeEncodeError

The release-helper script printed `✓` and `→` glyphs in status
output, which crashed on Windows consoles running cp936 (gbk) / cp1252
with a `UnicodeEncodeError`. The version bump itself completed
before the print — no file was ever left half-written — but the
script exited non-zero, obscuring that fact.

Fix: reconfigure `sys.stdout` / `sys.stderr` to UTF-8 with
`errors='replace'` at script start. Python 3.7+ is required for
`.reconfigure()`; older Pythons fall through the `try/except` and
keep the original encoding. Glyphs now print cleanly on modern
Windows Terminal / PowerShell and degrade to replacement
characters on legacy consoles instead of crashing.

### Break from v0.5.12

None at the contract layer. Operators upgrading from v0.5.12
require **no code changes, no canon edits, no script adjustments**.

Observable deltas:
- MCP host configs that use `cwd` (previously broken on Claude
  Desktop) can keep working — but switching to `env` is recommended
  because it's universal and explicit. See
  [`docs/INSTALL.md`](INSTALL.md) / the host-specific snippet.
- Claude Code substrates that rely on shell cwd are unchanged.
  The env fallback only fires when `project_dir` is unset.

---

## v0.5.12 — 2026-04-22 — MCP Registry namespace-casing hotfix

Contract-layer molt with **zero contract-surface deltas**. v0.5.11
shipped the MCP Registry onboarding artefacts (`server.json`,
README `mcp-name` sentinel) using a lower-case `io.github.battam1111`
namespace, but the registry's GitHub auth (case-sensitive) grants
namespace permissions matching the GitHub username's actual casing
— for this account that's `io.github.Battam1111/*`. `mcp-publisher
publish` on v0.5.11 returned HTTP 403 on ownership check. v0.5.12
corrects the casing in both `server.json` and the README sentinel
so the registry's PyPI verifier accepts the claim.

### What changed

- **Nothing in the R1–R7 rule text.**
- **Nothing in the category enum, the exit-policy grammar, or the
  exit-code ladder.**
- **Nothing in the 18-verb manifest surface.**
- **Nothing in the dimension roster count** (still 25).

### Fixed

- **`server.json::name`** `io.github.battam1111/myco` →
  `io.github.Battam1111/myco` (capital B, matching the GitHub
  username exactly).
- **`README.md` sentinel** `<!-- mcp-name: io.github.battam1111/myco
  -->` → `<!-- mcp-name: io.github.Battam1111/myco -->`.
- **`server.json::version` + `packages[0].version`** bumped
  `0.5.11` → `0.5.12` so the registry verifier greps the live
  PyPI 0.5.12 release (which carries the corrected sentinel) and
  not 0.5.11 (which does not).

### Break from v0.5.11

None at the contract layer. Operators upgrading from v0.5.11
require **no code changes, no canon edits, no script adjustments**.

### Relationship to v0.5.11 on PyPI

v0.5.11 stays on PyPI as a historical artefact (PyPI disallows
version reuse). It is installable but not registry-verified. The
canonical release pinned by the MCP Registry is v0.5.12.

---

## v0.5.11 — 2026-04-22 — MCP Registry onboarding (no contract-shape change)

Contract-layer molt with **zero contract-surface deltas**, exactly
like v0.5.9 and v0.5.10. This molt pairs a version number to
onboarding Myco into the official [MCP Registry](https://registry.modelcontextprotocol.io/)
so every MCP-capable host can discover and install Myco through
the standard registry flow rather than via manual config.

### What changed

- **Nothing in the R1–R7 rule text.** No rule added, removed, or
  semantically modified.
- **Nothing in the category enum, the exit-policy grammar, or the
  exit-code ladder** (3 / 4 / 5).
- **Nothing in the 18-verb manifest surface.**
- **Nothing in the dimension roster count** (still 25).

### Added (non-contract, additive)

- **`server.json`** at the repo root. Describes Myco as an MCP
  server in the [2025-12-11 ServerJSON
  schema](https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json):
  namespace `io.github.battam1111/myco`, stdio transport, PyPI
  package `myco==0.5.11` pinned. Validated via
  `mcp-publisher validate` against the live registry.
- **`<!-- mcp-name: io.github.battam1111/myco -->` sentinel** in
  `README.md`. PyPI's long-description becomes the package page
  body, and the registry's PyPI verifier greps the body for
  `mcp-name: <namespace>` to prove the package belongs to the
  claimed GitHub namespace. HTML comment is invisible to human
  readers; string is machine-readable.
- **Write-surface additions.** `server.json` and `CITATION.cff`
  join the `_canon.yaml::system.write_surface.allowed` list so
  future agent-initiated version bumps can rewrite them in place
  without tripping PA1 or WriteSurfaceViolation.

### Break from v0.5.10

None at the contract layer. Operators upgrading from v0.5.10
require **no code changes, no canon edits, no script adjustments**.

Observable differences:
- `mcp-server-myco` is now advertised in the official MCP Registry.
  Clients that resolve namespaces via the registry (Claude Desktop,
  future auto-install flows) will find Myco without a manual config
  paste.
- PyPI 0.5.11 release includes the `mcp-name` sentinel in the
  long-description. Old releases (< 0.5.11) remain installable but
  are not registry-verified.

---

## v0.5.10 — 2026-04-21 — Audit-response hotfix (no contract-shape change)

Contract-layer molt with **zero contract-surface deltas**, exactly
like v0.5.9. This molt pairs a version number to four bug fixes
surfaced by a seven-round post-release audit of v0.5.9.

### What changed

- **Nothing in the R1–R7 rule text.** No rule added, removed, or
  semantically modified.
- **Nothing in the category enum, the exit-policy grammar, or the
  exit-code ladder** (3 / 4 / 5).
- **Nothing in the 18-verb manifest surface.**
- **Nothing in the dimension roster count** (still 25).

### Bugs fixed (audit response)

1. **``SubstrateNotFound`` exit-code preserved** — `build_context`
   no longer wraps the exception in `UsageError`, restoring the
   v0.5.8 contract-promised exit 4. Scripts that check `exit == 4`
   for "no substrate at this path" now actually work.
2. **Fresh-substrate lint noise removed** — the canon template
   trimmed of kernel-path `_ref` fields that produced 5 MEDIUM
   findings on every freshly-germinated substrate. Fresh
   substrates now report 0 immune findings out of the box.
3. **RL1 skips on missing protocol.md** — RL1 requires
   ``docs/architecture/L1_CONTRACT/protocol.md`` to exist; fresh
   substrates without it produce no RL1 findings.
4. **Canon JSON-Schema ``subsystems.*.doc`` made optional** to
   match the Python kernel validator's actual requirements.

### Added (non-contract, additive)

- ``.myco_state/unsafe_writes.log`` — best-effort audit trail that
  `guarded_write` appends to on every `MYCO_ALLOW_UNSAFE_WRITE=1`
  bypass. Resolves a v0.5.9 deferred TODO.

### Break from v0.5.9

None at the contract layer. Operators upgrading from v0.5.9
require **no code changes, no canon edits, no script adjustments**.

Observable differences for new germinations:
- The canon template is smaller: `versioning`, `commands.manifest_ref`,
  `subsystems.*.doc`, `hard_contract.rules_ref`, `waves.log_ref` are
  no longer stamped by default. Kernel-like substrates that want
  them back add them manually.
- Fresh substrates get 0 immune findings (was 10 on v0.5.9).

Existing v0.5.9 substrates with the full canon shape continue to
load and lint cleanly under v0.5.10.

---

## v0.5.9 — 2026-04-21 — Immune-zero cleanup release (no contract-shape change)

Contract-layer release with **zero contract-surface deltas**. This
molt exists solely to pair a version number to the immune-zero
baseline substrate state + the JSON-Schema / migration-guide
ecosystem additions.

Governing crafts:
[`docs/primordia/v0_5_9_immune_zero_craft_2026-04-21.md`](primordia/v0_5_9_immune_zero_craft_2026-04-21.md)
(design) and
[`docs/primordia/v0_5_9_release_craft_2026-04-21.md`](primordia/v0_5_9_release_craft_2026-04-21.md)
(release closure).

### What changed

- **Nothing in the R1–R7 rule text.** No rule added, removed, or
  semantically modified.
- **Nothing in the category enum** (`mechanical` / `shipped` /
  `metabolic` / `semantic` unchanged) or the exit-policy grammar.
- **Nothing in the 18-verb manifest surface** (no new verb, no
  arg-shape change, no alias retirement).
- **Nothing in the dimension roster count** (still 25). One dim's
  _implementation_ refined (DC2 exempts `@property` +
  abstract-protocol overrides, matching its v0.5.8 docstring
  intent); no change to its id, category, or severity.
- **Nothing in the MycoError exit-code ladder** (3 / 4 / 5
  unchanged from v0.5.8).

### Added (non-contract, additive)

- Canon JSON-Schema at `docs/schema/canon.schema.json` (Draft
  2020-12). Second mechanical check alongside
  `myco.core.canon.load_canon`.
- Migration guides at `docs/migration/v0_5_7_to_v0_5_8.md` +
  `docs/migration/v0_5_8_to_v0_5_9.md`.
- Public `check_write_allowed` + `unsafe_bypass_enabled` API in
  `myco.core.write_surface` (promoted from private naming).
- Doctrine-ref anchors in 32 pre-v0.5.8 kernel module docstrings
  (completes the code → doctrine mycelium edges).

### Break from v0.5.8

None at the contract layer. Operators upgrading from v0.5.8
require **no code changes, no canon edits, no script adjustments**.
Everything additive; every old behavior preserved.

The only observable difference at the lint layer: `myco immune` on
the self-substrate now reports 0 findings where v0.5.8 reported
121 LOW. Downstream substrates will see their own DC2/DC4/CG1/CG2
findings reduced proportionally (the DC2 refinement in particular
drops findings for every adapter / dimension subclass).

---

## v0.5.8 — 2026-04-21 — Cleanup release: 14-dim lint expansion + foundation helpers

Contract-layer release with one visible contract-surface delta
(two `MycoError` exit codes differentiated within the `≥3` band)
and a substantial lint-roster expansion (11 → 25 dims, all within
existing categories).

Governing crafts:
`docs/primordia/v0_5_8_discipline_enforcement_craft_2026-04-21.md`
(14-dim expansion + 4 foundation helpers design) and
`docs/primordia/v0_5_8_release_craft_2026-04-21.md` (release
closure craft).

### What changed

- **Lint dimension inventory: 11 → 25.** All 14 new dims land in
  existing categories (no new `Category` enum values; no
  exit-policy grammar change). Per v0.5.7 policy, adding a dim
  inside an existing category is a changelog line but not a
  hard-contract change — the bump from v0.5.7 to v0.5.8 is
  motivated by the *exit-code differentiation* below, not the
  dim count. New dims:

  | ID | Category | Severity | Summary |
  |---|---|---|---|
  | `MP2` | mechanical | MEDIUM | Plugin-tree LLM-SDK import ban |
  | `DC1` | mechanical | LOW | Module docstring present |
  | `DC2` | mechanical | LOW | Public function/method docstring |
  | `DC3` | mechanical | LOW | Public class docstring |
  | `DC4` | mechanical | LOW | Non-trivial module references doctrine |
  | `CS1` | mechanical | HIGH (fixable) | `synced_contract_version` sync |
  | `FR1` | mechanical | HIGH/MEDIUM | Fresh-substrate directory invariants |
  | `PA1` | mechanical | MEDIUM | `write_surface.allowed` coverage |
  | `CG1` | mechanical | LOW | L2 doctrine has src reference |
  | `CG2` | mechanical | LOW | src subpackage has doctrine link |
  | `DI1` | mechanical | MEDIUM | `.claude/hooks.json` present |
  | `MB3` | metabolic | HIGH (fixable) | Raw-notes high watermark |
  | `SE3` | semantic | LOW | Graph has no self-cycles |
  | `RL1` | semantic | LOW | R1-R7 rules each referenced |

- **Exit-code differentiation.**
  - `SubstrateNotFound.exit_code` was `3`; is now `4`.
  - `CanonSchemaError.exit_code` was `3`; is now `5`.
  - All other `MycoError` subclasses unchanged (`ContractError`,
    `UsageError`: `3`).
  - Both new codes stay within the `≥3` operational-failure band
    the L1 exit-code contract reserves. CI scripts that check
    `exit != 0` see no change; scripts that special-case `== 3`
    for substrate/canon failures now see `== 4` / `== 5`.

- **Fresh-substrate directory invariants pre-provisioned.**
  `myco germinate` now creates `notes/raw/` and
  `notes/integrated/` up front (was: lazy on first
  `eat`/`assimilate`). No contract-surface impact on existing
  substrates; only fresh germinations see the new layout.

- **Canon schema `lint.dimensions` block expanded.** The canonical
  roster at `_canon.yaml::lint.dimensions` now declares all 25
  dims. Substrates upgrading from v0.5.7 continue to parse
  cleanly — unknown dim ids in the canon are tolerated (MF1
  cross-checks but does not reject).

### Break from v0.5.7

- **Exit codes**: any downstream script that string-matches on
  `exit == 3` for `SubstrateNotFound` or `CanonSchemaError` sees
  different behaviour at v0.5.8. The new codes are additive
  within the contract band; scripts checking `exit != 0` are
  unaffected.
- **Lint surface**: a substrate that ran `myco immune` clean at
  v0.5.7 may see new MEDIUM/LOW findings at v0.5.8 from the 14
  new dims. The default CI gate
  (`--exit-on=mechanical:critical,shipped:critical,…`) is
  unaffected; operators who gate at MEDIUM or lower should
  review the new findings.
- **Fresh-substrate shape**: new germinations include
  `notes/raw/` + `notes/integrated/`. Substrates relying on
  "notes/ empty until first eat" as a signal of freshness should
  switch to the `.myco_state/autoseeded.txt` marker (canonical
  since v0.4.0).

Everything else — R1-R7 text, category enum, exit-policy grammar,
manifest shapes, the 18-verb surface — is unchanged from v0.5.7.

---

## v0.5.7 — 2026-04-19 — Bimodal senesce + v0.5.6 postponement closure

Contract-layer release with one user-visible contract-surface delta
(R2 now names both PreCompact-full and SessionEnd-quick paths) and
one new payload invariant (every `senesce` Result carries a `mode`
key and a shape-stable `immune` field).

Governing crafts:
`docs/primordia/v0_5_7_senesce_quick_mode_craft_2026-04-19.md` (the
bimodal-senesce design) and
`docs/primordia/v0_5_7_release_craft_2026-04-19.md` (the release-
closure audit that bundles all four v0.5.7 audit streams).

### Contract surface at v0.5.7

- **18 verbs** unchanged from v0.5.6 (17 agent + 1 human `brief`).
  No new verb. The `senesce` verb gains one bool arg (`quick`,
  default false) — manifest-level addition, not a verb addition.
- **11 lint dimensions** unchanged from v0.5.6.
- **R2 wording** expanded: *"Every session ends with `myco senesce`
  — full (assimilate + immune --fix) on PreCompact, quick
  (assimilate only) on SessionEnd. The canonical session-end is
  the full form; quick is defense-in-depth for short-budget
  hosts."* R1, R3-R7 unchanged.
- **New payload invariant (promise across v0.5.x):** every
  `senesce` Result payload has shape `{reflect: {...}, immune:
  {...}, mode: "full"|"quick"}`. In quick mode, `immune` is
  `{skipped: true, reason: <str>}`. In full mode, `immune` is the
  full `run_immune` payload dict. Downstream consumers (`brief`,
  hunger sidecar, MCP initialize echo) read `payload["immune"]`
  unconditionally; both modes produce a dict.
- **Hook layout: three hooks (was two)** — SessionStart,
  PreCompact, SessionEnd — documented in `.claude/hooks/*.md`,
  `hooks/hooks.json` description, and the L1 R2 enforcement
  table.

### What changed

1. **R2 text upgrade** in `L1_CONTRACT/protocol.md` to name both
   hook-bound execution paths and the full/quick split.
2. **MCP instructions template** (`src/myco/surface/mcp.py`) —
   the R2 echo updated to match the new L1 wording verbatim.
   Every non-Claude-Code MCP client sees the upgraded contract at
   `initialize`. Canonical verb name in the echo is now
   `myco_senesce` (was `myco_session_end`) and `assimilate` (was
   `reflect`).
3. **`senesce` payload `mode` key** — additive, backward-
   compatible. Old readers ignore it; new readers can switch on
   it. The `immune: {skipped: true, ...}` shape in quick mode is
   the invariant downstream consumers key on.
4. **Editorial drift cleanup from v0.5.6 postponements** —
   seventeen → eighteen verbs, ten → eleven dimensions, seven →
   ten hosts, stale `metrics.test_count` in canon, plugin.json
   description, R2 enforcement table across all 19+ doctrine /
   surface files.
5. **Mechanical CI baseline** — `.github/workflows/ci.yml` runs
   ruff + mypy + pytest + immune + build + twine on push/PR.
   Baseline lets the next release cycle depend on mechanical
   enforcement of what v0.5.7 had to clean up by hand.

### Break from v0.5.6

None for substrate readers. v0.5.6 canons parse under v0.5.7
unchanged. Every v0.5.6 verb invocation still resolves. The only
user-visible behavior change is that installing the Myco plugin in
Claude Code now registers a third SessionEnd hook — which simply
runs `senesce --quick` at session exit. If a downstream has
customized its Claude Code hooks config, the upgrade is additive
(drop in the third hook block).

### Doctrine files touched

- `L1_CONTRACT/protocol.md` — R2 prose + enforcement table.
- `L1_CONTRACT/versioning.md` — Current state block v0.5.6 →
  v0.5.7.
- `L1_CONTRACT/canon_schema.md` — Example YAML shape v0.5.6 →
  v0.5.7 (dimension roster + affected_dimensions annotations).
- `L1_CONTRACT/exit_codes.md` — `At v0.5.6 that list is empty` →
  `v0.5.7`.
- `L3_IMPLEMENTATION/command_manifest.md` — Verb inventory header
  + senesce row `--quick` arg annotation.
- `L3_IMPLEMENTATION/package_map.md` — Layout header + providers/
  + symbionts/ + install/ state annotations.
- `L3_IMPLEMENTATION/symbiont_protocol.md` — "Automated hosts at
  v0.5.6" → v0.5.7.
- `src/myco/surface/mcp.py` — `_INSTRUCTIONS_TEMPLATE` R2 line.
- `src/myco/cycle/senesce.py` — quick-mode implementation + full
  module docstring.
- `MYCO.md` — finish-a-session block names both hooks.
- Trilingual READMEs — verb table + daily-flow paragraph name
  the SessionEnd/senesce-quick path.

---

## v0.5.6 — 2026-04-17 — Doctrine realignment + mechanical LLM-boundary guard + bitter-lesson appendix

A contract-layer release with two user-visible contract-surface
deltas + a deep doctrine realignment across all L0-L3 pages.

Governing craft:
`docs/primordia/v0_5_6_doctrine_realignment_craft_2026-04-17.md`.

### Contract surface at v0.5.6

- **18 verbs** unchanged from v0.5.5 (17 agent + 1 human-facing
  `brief`). No new verb ships at v0.5.6.
- **11 lint dimensions** (was 10): **MP1** added (mechanical /
  HIGH / not fixable). "No LLM-provider import from `src/myco/**`
  unless `canon.system.no_llm_in_substrate: false`." Mechanically
  enforces the v0.5.5 L0-principle-1 addendum "Agent calls the
  LLM; the substrate does not".
- **New canon field** `system.no_llm_in_substrate: bool`. Default
  `true`. Opt-out requires `false` + populating
  `src/myco/providers/` + contract bump. Graceful on v0.5.5 canons
  (optional-with-default).
- **New L2 doctrine page** `L2_DOCTRINE/extensibility.md`. Single-
  source for the two orthogonal extension axes (per-substrate
  `.myco/plugins/` ⊥ per-host `src/myco/symbionts/`). Cross-linked
  from L0 principle 5 and L2 homeostasis.
- **L0 principle 1 addendum** — declared exceptions (`brief` human
  window + Agent-calls-LLM boundary) written inline.
- **L0 bitter-lesson appendix** — names the review cadence for the
  coordination-surface bet (every MAJOR re-audits) and the
  redesign trigger.

### What changed

1. **MP1 mechanical guard** — scans `src/myco/` for provider-SDK
   imports; cross-checks canon `no_llm_in_substrate`; HIGH
   finding when declared-true-but-violated. Bitter-lesson-aligned
   (keeps Myco compute-scale-invariant).
2. **`system.no_llm_in_substrate` canon field** — declared
   intent, backed by MP1 mechanical scan.
3. **`src/myco/providers/` reserved package** — declared opt-in
   escape hatch for future LLM-coupling. Empty at v0.5.6.
4. **34 doctrine alignment edits** — every S1/S2/S3 from the
   v0.5.5 panoramic audit landed as concrete corrections across
   L0/L1/L2/L3 + architecture README. Top items: 18-verb
   inventory (was 17), 11-dimension enumeration table, fixable-
   dimension + safe-fix discipline doctrine, hunger payload shape
   correction, sporulate output-shape doctrine, graph API
   doctrine, package_map refresh.
5. **Bitter-lesson appendix** at L0 — holds principles 3 and 4
   accountable to a review cadence rather than treating the
   current structure as eternal truth.

### Break from v0.5.5

None for substrate readers. v0.5.5 canons parse under v0.5.6
unchanged (new field is optional-with-default-true). Every v0.5.5
verb invocation still works. Every v0.5.x alias still resolves.

One visible contract-surface addition: **fresh substrates
authored via `myco germinate` at v0.5.6 now include
`system.no_llm_in_substrate: true` explicitly** in their canon,
declaring their posture on the Agent-LLM-boundary invariant.

### Doctrine files touched

- `L0_VISION.md` — principle 1 addendum + bitter-lesson appendix
  + principle 5 extended with src graph + two-axes; biological-
  metaphor table refreshed
- `L1_CONTRACT/canon_schema.md` — 4 example corrections + new
  field + demo-upgrader note + dangling-ref removal
- `L1_CONTRACT/versioning.md` — current-state v0.5.6 row; "clean
  reflect" → "clean assimilate"
- `L1_CONTRACT/exit_codes.md` — `DIMENSION_CATEGORY` ref removed;
  skeleton-downgrade-now-empty clarified
- `L1_CONTRACT/protocol.md` — two-axes cross-link near R1-R7
- `L2_DOCTRINE/genesis.md` — M2-fix cross-link
- `L2_DOCTRINE/ingestion.md` — eat 3-mode signature + hunger
  payload shape + brief cross-link
- `L2_DOCTRINE/digestion.md` — sporulate output-shape + MP1 guard
- `L2_DOCTRINE/circulation.md` — graph API + fingerprint + cache
  semantics
- `L2_DOCTRINE/homeostasis.md` — 11-dimension table + fixable
  protocol + safe-fix discipline + MP1 section
- `L2_DOCTRINE/extensibility.md` — **NEW** cross-cutting doctrine
- `L3_IMPLEMENTATION/command_manifest.md` — 18-verb table + brief
  sub-section + six gates + payload fixes
- `L3_IMPLEMENTATION/package_map.md` — src tree + mapping matrix
  refresh + providers/ row
- `L3_IMPLEMENTATION/migration_strategy.md` — historical-note
  banner + senesce canonical
- `L3_IMPLEMENTATION/symbiont_protocol.md` — 10-host inventory
- `docs/architecture/README.md` — full rewrite

---

## v0.5.5 — 2026-04-17 — Close every audit loose thread

Eight MAJORs merged into one release. No contract-surface shape
change: 17 verbs + 10 lint dimensions + 5 subsystems + cycle/
package unchanged. The `meta.py` → `meta/` shim, the 9 verb
aliases (`genesis`/`reflect`/`distill`/`perfuse`/`session-end`/
`craft`/`bump`/`evolve`/`scaffold`), the schema_version-permissive
canon reader, and the substrate-local `.myco/plugins/` seam all
keep working.

Governing craft:
`docs/primordia/v0_5_5_close_audit_loose_threads_craft_2026-04-17.md`.

### Contract surface at v0.5.5

- **17 verbs** (was 16, +1 for `brief`). The new `brief` is the
  one explicit human-facing verb — L0 principle 1's single carved
  exception. Does NOT replace any agent-side verb; rolls up their
  outputs for a human review moment.
- **10 dimensions** unchanged count-wise, but **M2 and MB1** are
  now **fixable** — the first real implementations of a feature
  the `immune --fix` flag has promised since v0.4.0. A safe-fix
  discipline (idempotent / narrow / non-destructive / write-
  surface-bounded) is added to L2 homeostasis as new doctrine.
- **5 subsystems + cycle/ package** unchanged. The `symbionts/`
  package is formally defined at v0.5.5 as per-host Agent-sugar
  adapters (orthogonal to substrate-local `.myco/plugins/`); no
  concrete symbiont ships at v0.5.5 but the L3
  `symbiont_protocol.md` documents the slot.
- **`schema_upgraders`** gains its first registered entry: a demo
  `v0→v1` upgrader under key `"0"` (a version never shipped in
  real canons). Substrates with `schema_version: "0"` parse
  silently through the chain-apply path. Real v1→v2 upgrader
  (when schema v2 ships) will register the same way.
- **`myco-install host`** covers 10 hosts (was 7): adds
  gemini-cli (JSON), codex-cli (TOML via block-level surgery),
  goose (YAML with `extensions:` key).
- **Circulation graph** now covers `src/**` (AST-based import +
  docstring-doc-reference edges) and persists to
  `.myco_state/graph.json` with a canon+src fingerprint.

### What changed

- `sporulate` doctrine explicitly bounded: prepares scaffolding,
  does NOT call an LLM. Agent writes the synthesis prose. L0
  principle 1 invariant ("Agent calls LLM, substrate does not")
  now has an explicit doctrine anchor.
- L3 `symbiont_protocol.md` added; `symbionts/__init__.py` rewrites
  to reflect the per-host framing; pre-v0.5.5 "downstream-substrate
  adapters" framing superseded.

### Break from v0.5.4

None. No verb renamed, no manifest shape changed, no canon field
removed. Every v0.5.4 invocation resolves unchanged.

---

## v0.5.4 — 2026-04-17 — Dogfood-session patch (seven bugs fixed)

Patch release; no contract-surface change. Yanjun asked the Agent
to dogfood Myco on the Myco repo; the end-to-end pass surfaced two
critical bugs (broken `ramify` subcommand parsing + broken
substrate-local plugin auto-registration) plus five smaller ones.
All seven are fixed and pinned with regression tests.

### Contract surface at v0.5.4

Unchanged from v0.5.3: R1-R7, 17 verbs (9 with aliases), 10 lint
dimensions, 5 subsystems plus cycle/ package. The substrate-local
plugin seam (`.myco/plugins/` + `manifest_overlay.yaml`) now
actually works end-to-end; before v0.5.4, dimensions registered via
`ramify` were silently invisible to every verb that reads the
registry.

### What changed

1. `myco --version` / `-V` added.
2. Multi-value list flags (`--tags a b c`) parse naturally.
3. Subparser dest renamed from `verb` to `_subcmd` so `ramify
   --verb <name>` no longer clobbers the subcommand selector.
4. `ramify` template fixed: `{{__name__}}` → `{__name__}`.
5. `hunger` payload gains `local_plugins.count_by_kind`.
6. `--json` output gains a top-level `findings: [...]` array.
7. `winnow` gains `G6_template_boilerplate` gate.

### Break from v0.5.3

None. Every v0.5.3 invocation keeps working. The dogfood bugs
were covered-up gaps that only surfaced when the full verb surface
was exercised end-to-end; pre-release tests happened to not cover
these specific paths.

---

## v0.5.3 — 2026-04-17 — Fungal vocabulary + Agent-First + substrate-local plugins

Three concerns merged into one MINOR release. None of them breaks
the v0.5.2 contract surface; every prior invocation keeps working.
Governing craft:
`docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md`.

### Contract surface at v0.5.3

- **R1–R7** unchanged.
- **Exit-code grammar** unchanged.
- **Five subsystems** unchanged: Germination (was Genesis),
  Ingestion, Digestion, Circulation, Homeostasis. Cross-cutting
  `cycle/` package (was `meta/`) houses the life-cycle composers.
- **Seventeen verbs** (was sixteen): the v0.5.2 set with nine
  renamed to canonical fungal-biology terms, plus one new verb
  `graft`. Canonical / alias pairs: `germinate` / `genesis`,
  `assimilate` / `reflect`, `sporulate` / `distill`, `traverse` /
  `perfuse`, `senesce` / `session-end`, `fruit` / `craft`, `molt` /
  `bump`, `winnow` / `evolve`, `ramify` / `scaffold`. `hunger`,
  `eat`, `sense`, `forage`, `digest`, `propagate`, `immune` kept
  their v0.4-era names — each is already a biologically accurate
  fungal term.
- **Ten lint dimensions** (was nine): `MF2` added
  (mechanical / HIGH — substrate-local plugin health).

### What changed

1. **Fungal vocabulary rename.** Nine verbs and two packages
   (`myco.genesis` → `myco.germination`, `myco.meta` →
   `myco.cycle`) moved to fungal-biology terms whose semantics
   match the verb's behavior. Old names register as CLI aliases
   and as MCP tool aliases; the Python shim packages at the old
   paths re-export every name from the new location. Cycle's
   `fruit.md.tmpl` replaces `craft.md.tmpl`.
2. **Agent-First framing fix.** Trilingual READMEs, `MYCO.md`,
   `INSTALL.md`, and the L1/L2/L3 doctrine pages audited for
   sentences that said "when you run `myco X`" or "the user runs
   X". L0 principle 1 (只为 Agent) says humans speak natural
   language and the Agent invokes verbs — every verb-invoking
   sentence now names the Agent as the grammatical subject.
3. **Substrate-local plugin loading.** `Substrate.load()` auto-
   imports `<root>/.myco/plugins/__init__.py` under an isolated
   module name; `load_manifest_with_overlay(substrate_root)`
   merges `<root>/.myco/manifest_overlay.yaml` into the packaged
   manifest at `build_context()` time. The new `graft` verb
   (`--list | --validate | --explain <name>`) is the Agent's
   introspection surface; the extended `ramify` verb
   (`--dimension | --adapter | --verb --substrate-local`) is the
   authoring surface. `MF2` lint dimension surfaces shape errors.
   `hunger` payload carries a `local_plugins: {loaded,
   count_by_kind, errors, module}` block so the Agent sees on
   every boot what has grafted onto the substrate.

### Break from v0.5.2

None. Every v0.5.2 `_canon.yaml` parses under v0.5.3 unchanged.
Every v0.5.2 CLI invocation resolves (one-shot `DeprecationWarning`
per alias). Every v0.5.2 MCP tool name (`myco_genesis`,
`myco_reflect`, etc.) remains registered. Every v0.5.2 Python
import path (`from myco.genesis import ...`, `from myco.meta import
session_end_run`) keeps working through its shim package. Alias
removal is scheduled for **v1.0.0** only — the entire 0.x line
stays backward-compatible.

---

## v0.5.2 — 2026-04-17 — Editable-by-default install model

The "Stable kernel, mutable substrate" framing introduced at v0.4.1
— paraphrased as "`pip install` locks the kernel at a released
version" — contradicts L0 principles 3 (永恒进化) and 4 (永恒迭代):
read-only `site-packages` prevents the agent from authoring kernel
code, but L0 principle 1 (只为 Agent) says the agent IS the author.
v0.5.2 flips the documented primary install path to editable and
adds the `myco-install fresh` subcommand to make that path one
command for new users.

### Contract surface at v0.5.2

- **R1–R7** unchanged.
- **Exit-code grammar** unchanged.
- **Subsystems** unchanged (5 + `meta/` package from v0.5.1).
- **Sixteen verbs** unchanged.
- **Nine lint dimensions** unchanged.
- **`myco-install`** — new subcommand layout (`fresh` + `host`);
  legacy `myco-install <client>` still works via auto-route.

### What changed

- Primary documented install: `pipx run --spec 'myco[mcp]'
  myco-install fresh ~/myco` (or the two-step equivalent).
- `pip install myco` demoted to a secondary, library-consumer
  path. Not deprecated — still produces a working install; just
  does not deliver on L0 principle 3/4 because the kernel at
  `<site-packages>/myco/` is read-only.
- Kernel upgrades migrate from `pip install --upgrade` to
  `git pull` inside the editable clone + `myco immune` to verify
  no drift.
- Legacy `myco-install <client>` form kept working via a
  first-arg-is-a-known-client sniff that routes to
  `host <client>`.

### Break from v0.5.1

None for substrate readers. `_canon.yaml` emitted by v0.5.1 parses
under v0.5.2 unchanged. No verb signatures changed. No manifest
edits needed in downstream substrates. Only user-facing doc and
the `myco-install` CLI's subcommand shape moved.

---

## v0.5.1 — 2026-04-17 — 永恒进化 delivered in code (MAJOR 6–10)

*(The v0.5.0 wheel filename was burned on PyPI prior to first
successful upload; v0.5.1 is the first released wheel carrying
this contract. Semantic content is identical to the v0.5.0 plan.)*


Closes all five MAJOR gaps from the v0.4.1 post-release audit
(`docs/primordia/v0_4_1_audit_craft_2026-04-15.md`). The README's
"the substrate changes shape with the work" and "you never migrate
again" claims are now backed by mechanisms, not aspirational prose.

### Contract surface at v0.5.0

- **R1–R7** unchanged from v0.4.x.
- **Exit-code grammar** unchanged.
- **Five subsystems** unchanged (genesis / ingestion / digestion /
  circulation / homeostasis), joined by a cross-cutting `meta/`
  package (not a subsystem; houses `session-end`, `craft`, `bump`,
  `evolve`, `scaffold`).
- **Sixteen verbs** (was twelve): the v0.4 set plus `craft`, `bump`,
  `evolve`, `scaffold`. `immune` gained `--list` and `--explain`.
- **Nine lint dimensions** (was eight): `MF1` added
  (mechanical / HIGH — declared subsystems exist on disk).

### Break from v0.4.x

This is **not** a backward-incompatible release for substrate
readers. Every v0.4.x `_canon.yaml` parses under v0.5 unchanged; the
forward-compat seam means a future v0.6-schema canon will also parse
(with a warning) under a v0.5 kernel. The one user-visible code
change: `session-end`'s manifest handler string moved from
`myco.meta:session_end_run` to `myco.meta.session_end:run` when the
single-file `meta.py` module was promoted to a package. The
`from myco.meta import session_end_run` re-export is preserved in
`meta/__init__.py` for any out-of-tree caller that pinned the old
import path.

### New mechanisms

- **MAJOR 6 — Dimension registration via entry-points.**
  `[project.entry-points."myco.dimensions"]` in `pyproject.toml` is
  now the source of truth for built-in dimensions; the hardcoded
  `ALL` tuple (renamed `_BUILT_IN`) is a dev-checkout fallback
  only. Third-party substrates register their own dimensions by
  declaring the same entry-points group in their own `pyproject.toml`
  — no fork of Myco required. `myco immune --list` and
  `myco immune --explain <dim>` surface the registry catalog.
- **MAJOR 7 — Subsystem/package cross-check.** The `MF1` dimension
  validates every `canon.subsystems.<name>.package` resolves to an
  existing directory under substrate root. `tests/test_scaffold.py`
  switched from a hardcoded `PACKAGES` list to
  `pkgutil.walk_packages` — adding a subsystem no longer forces a
  test edit.
- **MAJOR 8 — Forward-compatible canon reader.** An unknown
  `schema_version` in `_canon.yaml` now emits a `UserWarning`
  instead of raising `CanonSchemaError`. A new module-level
  `schema_upgraders: dict[str, Callable]` registry in
  `myco.core.canon` is the seam for future v1→v2 in-code upgraders;
  empty at v0.5, populated when schema v2 lands.
- **MAJOR 9 — Governance as verbs.** `craft / bump / evolve` became
  real agent-callable verbs:
  - `myco craft <topic>` authors a dated three-round primordia doc
    from a template.
  - `myco bump --contract <v>` is the first code path in Myco that
    mutates a post-genesis `_canon.yaml`; line-patches
    `contract_version` and `synced_contract_version`, re-validates
    via `load_canon`, appends a section to this changelog.
  - `myco evolve --proposal <path>` runs shape gates on a craft or
    proposal doc (frontmatter type, title, body size, round-marker
    count, per-round floor).
- **MAJOR 10 — Handler auto-scaffolding.**
  `myco scaffold --verb <name>` generates a stub handler file at
  the filesystem path derived from the manifest's `handler:`
  string. The stub returns a well-formed `Result` with
  `payload.stub = True` and emits a `DeprecationWarning` on every
  invocation, so unfinished verbs are neither crashes nor silent
  successes.

### Doctrine updates

- `docs/architecture/L1_CONTRACT/canon_schema.md` rule 4 — permissive
  schema-version language (warn + upgraders chain).
- `docs/architecture/L2_DOCTRINE/homeostasis.md` — entry-points-driven
  registration, `MF1` in the inventory, `--list` / `--explain`
  surface documented.
- `docs/architecture/L3_IMPLEMENTATION/command_manifest.md` —
  governance-verbs section added, inventory table updated.
- `docs/architecture/L3_IMPLEMENTATION/package_map.md` — `meta/` as a
  package (was single-file `meta.py`).

---

## v0.4.0 — 2026-04-15 — Greenfield rewrite

First entry in the post-rewrite lineage. Resets `waves.current` to
`1` per the directive recorded in
`docs/architecture/L3_IMPLEMENTATION/migration_strategy.md` §9 E5.

### Contract surface at v0.4.0

- **R1–R7** as defined in `docs/architecture/L1_CONTRACT/protocol.md`.
- **Exit-code grammar** as defined in
  `docs/architecture/L1_CONTRACT/exit_codes.md`.
- **Five subsystems** as defined in
  `docs/architecture/L2_DOCTRINE/` (genesis, ingestion, digestion,
  circulation, homeostasis).
- **Twelve verbs** as defined in `src/myco/surface/manifest.yaml`
  (genesis, hunger, eat, sense, forage, reflect, digest, distill,
  perfuse, propagate, immune, session-end).
- **Eight lint dimensions** authored fresh (not ported from the v0.3
  30-dim table):
  - Mechanical: M1 (canon identity), M2 (entry-point exists),
    M3 (write-surface declared).
  - Shipped: SH1 (package-version ref resolves).
  - Metabolic: MB1 (raw-notes backlog), MB2 (no integrated yet).
  - Semantic: SE1 (dangling refs), SE2 (orphan integrated).

### Break from v0.3.x

This is **not** an in-place upgrade from any v0.3.x contract. The
pre-rewrite codebase is preserved at tag `v0.3.4-final`; consumers
(e.g. ASCC) remain pinned there until they migrate through the fresh
re-export path (`scripts/migrate_ascc_substrate.py`, landing in Stage
C.3). No v0.3.x contract version is honored by the v0.4.0 kernel.

### Version-line monotonicity reset

Pre-rewrite tags exhibited non-monotone versioning
(`v0.46.0 → v0.6.0 → v0.45.0`, per the audit recorded in L1
`versioning.md`). The `v0.4.0` release begins a clean, strictly
increasing sequence. Future bumps follow SemVer.
