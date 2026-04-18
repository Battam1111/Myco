# L2 — Germination

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9; vocabulary
> revised at v0.5.3 per
> `docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md`).
> **Filename note**: this file keeps its original `genesis.md` name
> as an intentional historical anchor — renaming doctrine files is a
> separate contract-breaking concern handled only at major releases.
> The subsystem itself is **Germination** as of v0.5.3.
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/*`.
> **Upward mapping**: implements L1 R1 (ritualized boot requires a
> substrate to boot from) and L0 invariant 3 (stepwise refinement
> starts with Germination as the root).

---

## Responsibility

Germination owns the birth of a substrate. Given a project directory
with no Myco state, Germination produces a **minimal, self-
identifying, lint-clean skeleton** that subsequent sessions can grow
into a mature substrate. Biology: a spore germinates into the first
hyphae of a new colony.

Germination is invoked **exactly once** per project lifetime. Re-
running it on an established substrate is an error, not a
convenience.

## Boundary

Germination **does**:

- Create `_canon.yaml` from the canonical schema, filling identity
  fields from project-directory inspection or interactive prompt.
- Create `.myco_state/` with the `autoseeded.txt` marker (enables
  skeleton-mode severity downgrade per L1 exit-codes doc).
- Create the minimal `notes/`, `docs/`, and entry-point file
  (`MYCO.md` for Myco itself; `CLAUDE.md` for downstream projects)
  from a template that references the approved architecture docs.
  The entry-point file is also the target of the `M2` fixable
  dimension (see `homeostasis.md`): a substrate whose entry-point
  file is missing at immune time — regardless of germination path —
  will have `M2` auto-create the file from a minimal skeleton when
  `myco immune --fix` runs, provided safe-fix discipline holds
  (idempotent / narrow / non-destructive / bounded).
- Register the write-surface allowlist in the new canon.

Germination **does not**:

- Seed craft docs, debates, or narrative content.
- Write code or scaffold a package.
- Attempt to infer project facts beyond what's trivially readable
  (directory name, git remote, top-level README).
- Connect to external services.

## Interface

A single command:

```
myco germinate [--project-dir DIR] [--substrate-id NAME] [--dry-run]
```

- `--project-dir`: target directory (default: current).
- `--substrate-id`: stable identifier for the new substrate; required.
- `--dry-run`: print the files that would be created and their
  contents; change nothing.

The v0.5.2 alias `myco genesis` still resolves to the same handler
(with a one-shot `DeprecationWarning`) throughout the 0.x line;
alias removal is scheduled for v1.0.0.

Exit codes follow the L1 exit-code ladder. A `germinate` call on an
already bootstrapped substrate returns code 3 (contract error).

## Cross-subsystem contract

- Produces the marker that Homeostasis's skeleton-downgrade logic
  depends on.
- Produces a canon that Ingestion's `myco hunger` reads on first
  call.
- Produces an entry-point file whose signals block is later
  maintained by Ingestion's boot-brief injector.

## What changed from the pre-rewrite `autoseed`

The v0.3 `autoseed` was entangled with hunger, with lint self-
exemption, and with substrate upgrade paths. Germination is
narrower: birth only. Substrate upgrades from v0.3 → v0.4 are an
L4 migration script, not a Germination rerun.
