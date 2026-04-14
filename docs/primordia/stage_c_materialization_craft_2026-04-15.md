# Stage C Craft — Materialization

> **Date**: 2026-04-15
> **Stage**: C — bring Myco online as its own substrate.
> **Inputs**: L0 vision, L1 `canon_schema.md` / `exit_codes.md` /
> `versioning.md`, L2 five subsystem docs, L3 `migration_strategy.md`
> §"Stage C — v0.4.0 release".
> **Depth**: single round. All architectural decisions were settled in
> L0-L3; Stage C is authored execution against a fixed schema.

---

## Plan (exhaustive, per user-global rule 4)

Stage C is split into four commits so each is reviewable in isolation
and reverts don't discard unrelated work:

**C.1 — Root substrate (this commit)**
- Author `/_canon.yaml` from L1 schema; ≤ 300 non-comment lines; SSoT
  only.
- Author `/MYCO.md` as the agent entry page; strictly derives from L0's
  five principles; no legacy carry-over from `legacy_v0_3/MYCO.md`.
- Author `/docs/contract_changelog.md` with the v0.4.0 genesis entry
  (canon references it under `waves.log_ref`).
- Verify: `myco immune` runs clean on the new substrate under
  `exit_on="critical"` (all eight dimensions silent or HIGH-max).

**C.2 — `.claude/hooks/`**
- `SessionStart.json` → runs `python -m myco hunger`.
- `PreCompact.json`   → runs `python -m myco session-end`.
- Scoped to this repo only; users enabling them in their own substrate
  is a downstream migration.

**C.3 — ASCC migration script**
- `scripts/migrate_ascc_substrate.py` — dry-run by default, `--execute`
  opts in. Reads ASCC's v0.3 canon, maps fields into the v0.4.0 schema,
  writes a proposed `_canon.yaml` beside the original. Does not mutate
  ASCC in place; §9 E2 "fresh re-export" discipline.

**C.4 — Release commit**
- Bump `src/myco/__init__.py::__version__` from `"0.4.0.dev"` → `"0.4.0"`.
- Full `pytest` green; full `myco immune` clean.
- `git rm -r legacy_v0_3/` (77 MB, 6 months of pre-rewrite history
  preserved in git + `v0.3.4-final` tag).
- `git tag -a v0.4.0 -m "Greenfield rewrite release."`
- **Hold for push approval** — no `git push` until Yanjun OKs.

---

## Why split

The single-pass rule (rule 4) applies **within** a commit, not across
the release. Each of the four commits is itself one-pass and complete;
splitting is about reviewable diff size, not about deferring decisions.

## C.1 specifics — canon values

| Field | Value | Rationale |
|-------|-------|-----------|
| `schema_version` | `"1"` | First schema; `myco.core.canon.KNOWN_SCHEMA_VERSIONS`. |
| `contract_version` | `"v0.4.0"` | Matches L1 `protocol.md` at release. |
| `synced_contract_version` | `"v0.4.0"` | Same at v0.4.0 birth; drifts only after `reflect`. |
| `identity.substrate_id` | `"myco-self"` | Stable slug; never renamed. |
| `identity.tags` | `["myco", "agent-substrate", "python-package"]` | Descriptive; non-exclusive per L0 principle 2. |
| `identity.entry_point` | `"MYCO.md"` | Default agent entry page. |
| `system.write_surface.allowed` | _canon + MYCO + notes/docs/src/tests/scripts/.claude + pyproject/README/CHANGELOG/LICENSE | Derived from the repo's actual writable surface; everything else is lint target, not write target. |
| `system.hard_contract.rules_ref` | `docs/architecture/L1_CONTRACT/protocol.md` | L1 protocol page. |
| `system.hard_contract.rule_count` | `7` | R1–R7. |
| `versioning.package_version_ref` | `src/myco/__init__.py` | Per L1 `versioning.md`. |
| `versioning.pyproject_dynamic` | `true` | Hatchling dynamic = ["version"]. |
| `lint.dimensions` | M1:mechanical, M2:mechanical, M3:mechanical, SH1:shipped, MB1:metabolic, MB2:metabolic, SE1:semantic, SE2:semantic | Actual B.8 registry. |
| `lint.exit_policy.default` | `"mechanical:critical,shipped:critical,metabolic:never,semantic:never"` | L1 exit-codes doc canonical CI gate. |
| `lint.skeleton_downgrade.affected_dimensions` | `[]` | No dims opt in at v0.4.0; pre-rewrite L0/L1 targets no longer exist. Reserved for future. |
| `subsystems` | the five L2 docs + package paths | Verbatim from L2 filenames. |
| `commands.manifest_ref` | `src/myco/surface/manifest.yaml` | Actual runtime manifest (was the L3 doc path in the schema example; the L4 instance points at the runtime SSoT). |
| `metrics.test_count` | `283` | Current pytest count. |
| `waves.current` | `1` | Resets at v0.4.0 per §9 E5. |
| `waves.log_ref` | `docs/contract_changelog.md` | Must exist (M2 / SE1 would otherwise fire). |

## Rebuttal (single round)

**R1.** *"`commands.manifest_ref` deviates from the schema example
(which points at `L3_IMPLEMENTATION/command_manifest.md`)."*
Intentional. The L4 instance binds to the **runtime** SSoT; the L3
doc is derivation. The L3 doc contains the design record, but the
live schema the kernel reads is `surface/manifest.yaml`. Pointing
canon at the L3 doc would mean a broken graph edge the moment the
manifest changes but the L3 doc lags. The L3 doc and L4 instance can
disagree on this field shape without contract bump — schema allows any
`_ref`-suffixed string.

**R2.** *"Empty `skeleton_downgrade.affected_dimensions` means the
feature is dead code."*
Not dead — the kernel still runs the downgrade check; it's just a
no-op for this substrate. When a future dimension opts in (e.g. a
dimension that fires loudly on a blank canon), adding it here is a
one-line canon edit, no code change.

**R3.** *"SE2 orphan-integrated will fire on every new note we haven't
linked yet."*
Acceptable — SE2 is LOW severity; `exit_on="critical"` ignores it.
CI gates don't trip on orphans. We surface the signal and keep moving.

## Reflection

The most load-bearing decision this plan makes is picking
`commands.manifest_ref = src/myco/surface/manifest.yaml` over the L3
doc path the schema example used. The schema example was
illustrative; the principle is that L4 canon binds **the runtime
SSoT**, and for commands that is the YAML the CLI and MCP actually
read. Recording that disagreement here (not silently overriding the
example) is the self-validating-substrate invariant in action.

Escalation: none.
