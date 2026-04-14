# Contract Changelog

Append-only record of contract-version bumps. A contract bump is
required whenever R1–R7 change, subsystem definitions change, the
exit-code policy grammar changes, the lint-dimension inventory changes
semantics, or the command manifest changes a verb's shape. Adding a
new lint dimension inside an existing category is a changelog line but
not a bump.

Format: one section per `contract_version`, newest first.

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
