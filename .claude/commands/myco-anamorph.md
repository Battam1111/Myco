---
description: "Draft a canon schema migration to a new schema_version via the anamorph subagent (named partial upgraders + tests + schema delta + migration guide). Stops before mutating _canon.yaml itself."
argument-hint: "<new-schema-version-int> [governing-craft-path]"
---

The user is drafting a schema migration. Arguments: $ARGUMENTS

Parse $ARGUMENTS as `<new-schema-version> [governing-craft-path]`. The new schema version is required (e.g. `3` for v2 → v3). The governing-craft path is required by L1; if the user did not supply one, ask for it before invoking the subagent — schema bumps are L1 contract changes and require a LANDED craft.

Once both arguments are confirmed, dispatch the **anamorph** subagent (defined at `.claude/agents/anamorph.md`). Pass:
- target schema version: $1
- governing craft path: $2

The subagent will:

1. **Phase A (governance check)**: run `myco winnow --proposal $2`. Refuse if winnow fails.
2. **Phase B (study)**: Read existing `_v<N-1>_to_v<N>_*` partials in `src/myco/core/canon.py` to learn the established style.
3. **Phase C (decompose)**: enumerate the semantic changes between current schema and target. Each becomes its own named partial. Narrowness principle: one partial = one semantic.
4. **Phase D (author partials)**: write each partial as idempotent + additive-when-possible + preserves unrelated keys.
5. **Phase E (compose)**: extend the master `_apply_upgraders` chain.
6. **Phase F (test fixtures)**: one test per partial + idempotence + smoke composing all.
7. **Phase G (schema delta)**: edit `docs/schema/canon.schema.json`.
8. **Phase H (migration guide)**: author `docs/migration/v<old-contract>_to_v<new-contract>.md`.
9. **Phase I (KNOWN_SCHEMA_VERSIONS)**: extend the frozenset.
10. **Phase J (verify)**: run pytest on the new tests; run `myco immune`.

The subagent stops BEFORE flipping `_canon.yaml::schema_version`. That is a separate user-approved step inside the contract bump (typically via `myco molt`).

When anamorph returns, relay its structured report verbatim. The report names every partial authored, every test added, the schema delta, the migration guide, and the explicit "NOT YET DONE (user step)" list.

Do NOT flip `_canon.yaml::schema_version` yourself. That requires the user to invoke `/myco-disperse <new-contract-version>` or to run `myco molt` directly, which is a contract-bump-class operation.
