# Contract Changelog

Append-only record of contract-version bumps. A contract bump is
required whenever R1–R7 change, subsystem definitions change, the
exit-code policy grammar changes, the lint-dimension inventory changes
semantics, or the command manifest changes a verb's shape. Adding a
new lint dimension inside an existing category is a changelog line but
not a bump.

Format: one section per `contract_version`, newest first.

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
