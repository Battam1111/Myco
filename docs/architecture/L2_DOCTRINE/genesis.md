# L2 — Genesis

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/*`.
> **Upward mapping**: implements L1 R1 (ritualized boot requires a
> substrate to boot from) and L0 invariant 3 (stepwise refinement starts
> with Genesis as the root).

---

## Responsibility

Genesis owns the birth of a substrate. Given a project directory with no
Myco state, Genesis produces a **minimal, self-identifying, lint-clean
skeleton** that subsequent sessions can grow into a mature substrate.

Genesis is invoked **exactly once** per project lifetime. Re-running
Genesis on an established substrate is an error, not a convenience.

## Boundary

Genesis **does**:

- Create `_canon.yaml` from the canonical schema, filling identity fields
  from project-directory inspection or interactive prompt.
- Create `.myco_state/` with the `autoseeded.txt` marker (enables
  skeleton-mode severity downgrade per L1 exit-codes doc).
- Create the minimal `notes/`, `docs/`, and entry-point file (`MYCO.md`
  for Myco itself; `CLAUDE.md` for downstream projects) from a template
  that references the approved architecture docs.
- Register the write-surface allowlist in the new canon.

Genesis **does not**:

- Seed craft docs, debates, or narrative content.
- Write code or scaffold a package.
- Attempt to infer project facts beyond what's trivially readable
  (directory name, git remote, top-level README).
- Connect to external services.

## Interface

A single command:

```
myco genesis [--project-dir DIR] [--identity-steward NAME] [--dry-run]
```

- `--project-dir`: target directory (default: current).
- `--identity-steward`: human owner of the substrate; required.
- `--dry-run`: print the files that would be created and their contents;
  change nothing.

Exit codes follow the L1 exit-code ladder. A `genesis` call on an already
bootstrapped substrate returns code 3 (contract error).

## Cross-subsystem contract

- Produces the marker that Homeostasis's skeleton-downgrade logic depends
  on.
- Produces a canon that Ingestion's `myco hunger` reads on first call.
- Produces an entry-point file whose signals block is later maintained by
  Ingestion's boot-brief injector.

## What changed from the pre-rewrite `autoseed`

The v0.3 `autoseed` was entangled with hunger, with lint self-exemption,
and with substrate upgrade paths. Genesis is narrower: birth only.
Substrate upgrades from v0.3 → v0.4 are an L4 migration script, not a
Genesis rerun.
