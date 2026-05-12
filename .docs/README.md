# docs/ — substrate documentation tree

This tree is for the **agent**. Humans speak natural language to
the agent; the agent reads everything here as first-class
substrate material (L0 principle 1). Paths are stable — substrate
canon and every craft cross-references files by their relative
path.

> **v0.8.4 root-cleanup note**: the agent entry page MYCO.md was
> moved from repo root to `.myco/MYCO.md`. Canon's
> `identity.entry_point` field is the SSoT for the path.

## Navigation

```
docs/
├── architecture/          Governing doctrine (L0–L3)
│   ├── L0_VISION.md       Five root principles (identity layer)
│   ├── L1_CONTRACT/       Hard Contract (R1–R7), exit codes, canon schema, versioning
│   ├── L2_DOCTRINE/       Per-subsystem doctrine (circulation / digestion / etc.)
│   └── L3_IMPLEMENTATION/ Manifest, symbiont protocol, verb surface maps
├── primordia/             Three-round craft archive (append-only)
├── migration/             Version-to-version upgrade guides
├── schema/                JSON-Schema for _canon.yaml (IDE validation)
├── contract_changelog.md  Append-only log of contract-version bumps
├── INSTALL.md             Installation path (editable-default)
└── release_process.md     Release playbook
```

## Read order for a new session

1. [`architecture/L0_VISION.md`](architecture/L0_VISION.md) — the
   five root principles Myco's identity is exhausted by. Read once
   per agent lifetime; revisit when doing governance-shaped work.
2. [`architecture/L1_CONTRACT/protocol.md`](architecture/L1_CONTRACT/protocol.md)
   — the seven hard rules R1–R7 every session honors.
3. [`architecture/L2_DOCTRINE/homeostasis.md`](architecture/L2_DOCTRINE/homeostasis.md)
   and the sibling `ingestion.md` / `digestion.md` / `circulation.md`
   / `genesis.md` / `extensibility.md` — read the subsystem's L2
   page before touching its code under `src/myco/`.
4. [`../.myco/MYCO.md`](../.myco/MYCO.md) — substrate entry point (this is the
   file the SessionStart hook + `myco hunger` reference).

## Read order for a release engineer

1. [`release_process.md`](release_process.md) — the playbook
2. [`contract_changelog.md`](contract_changelog.md) — previous molts
3. [`primordia/README.md`](primordia/README.md) — the craft archive index
4. [`migration/README.md`](migration/README.md) — the upgrade-path notes

## Read order for a downstream substrate maintainer

1. [`migration/README.md`](migration/README.md) — upgrade-path for your canon
2. [`architecture/L2_DOCTRINE/extensibility.md`](architecture/L2_DOCTRINE/extensibility.md)
   — the two-axis plugin model (`.myco/plugins/` + `boundary/install/clients.py`)
3. [`schema/README.md`](schema/README.md) — wire `_canon.yaml`
   validation into your editor

## The four cross-referenced SSoTs

Every number, name, and path lives in exactly one place. Other
files reference, never duplicate:

- **L0 vision** → `architecture/L0_VISION.md`
- **L1 rules** → `architecture/L1_CONTRACT/protocol.md`
- **Canon shape** → `architecture/L1_CONTRACT/canon_schema.md` +
  `schema/canon.schema.json`
- **Verb surface** → `../src/myco/boundary/surface/manifest.yaml`
  (manifest-driven; CLI + MCP both derive from it)

## What does NOT live here

- Code (`src/myco/`)
- Tests (`.tests/`)
- Live substrate state (`.myco/canon.yaml` — the substrate's SSoT;
  `.myco/state/` for derivable runtime state). Downstream substrates
  may keep the legacy `_canon.yaml` + `.myco_state/` flat layout —
  both shapes are canon-configurable per
  `system.{canon_filename, notes_dir, docs_dir}` (v0.8.4+).
- Raw agent notes (`.myco/notes/`) — those are ingestion artifacts,
  not doctrine

## Editing discipline

L0/L1/L2 changes require a craft doc under
[`primordia/README.md`](primordia/README.md) and owner approval. Changes to L3
implementation or L4 substrate don't need a craft but must conform
to the governing L0–L2. See
[`architecture/L0_VISION.md`](architecture/L0_VISION.md) §
"Changes to this page" for the full governance process.
