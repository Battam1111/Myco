# Contract Changelog

Append-only record of contract-version bumps. A contract bump is
required whenever R1–R7 change, subsystem definitions change, the
exit-code policy grammar changes, the lint-dimension inventory changes
semantics, or the command manifest changes a verb's shape. Adding a
new lint dimension inside an existing category is a changelog line but
not a bump.

Format: one section per `contract_version`, newest first.

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
