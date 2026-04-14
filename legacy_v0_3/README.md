# `legacy_v0_3/` — Pre-rewrite Myco, frozen

> **Status**: quarantined 2026-04-15. Not consumed by any code, doc, or
> test at the repository root. Will be deleted at the v0.4.0 release
> commit (Stage C of the migration).

## What this is

A snapshot of the Myco project exactly as it was after the v0.3.4
release and the L0 identity revision, with every top-level artifact
that might otherwise leak into the greenfield rewrite moved into this
directory.

Corresponding git tag: `v0.3.4-final` (on commit c51a8da — the v0.3.4
release commit, pre-revision of L0 docs).

The original pre-rewrite top-level README is preserved here as
`README_v0_3.md` in case its content is useful during rewrite triage.

## What this is NOT

- **Not a dependency.** Nothing under `docs/architecture/` or the new
  `src/myco_v4/` (when scaffolded) imports or references content here.
- **Not a reference implementation.** Per §9 E2 ("fresh re-export, no
  in-place translation") and E4 ("redefine semantics before
  re-implementing"), this directory is consulted only for:
  - Checking historical behavior when writing a new feature's craft doc.
  - The ASCC migration script (Stage C) translating old canon fields
    into the new schema.
- **Not a branch.** Per §9 E6, no long-lived `legacy/v0.3` branch
  exists. The `v0.3.4-final` tag is the sole git-history anchor; this
  directory is a disk-level convenience for inspection during the
  rewrite.

## How to use it during the rewrite

- **Read freely.** Agents may read files here to check what v0.3 did.
- **Do not import.** Nothing under `legacy_v0_3/` is on any `sys.path`
  or referenced by `pyproject.toml`. If something here seems useful, the
  agent extracts the idea and re-authors it under the new architecture.
- **Do not edit.** Changes here are meaningless — the directory is
  scheduled for deletion. If a change is needed (e.g. a bug in an old
  test breaks local `pytest`), migrate the concern into the new v4 tree
  instead of patching here.
- **Do not run tests or CI from here.** The rewritten CI (Stage B.7+)
  targets `tests/v4/`; the old CI workflows (moved into
  `legacy_v0_3/.github/`) will never run again.

## Contents map

```
legacy_v0_3/
├── README_v0_3.md                   # old top-level README
├── MYCO.md, CLAUDE.md               # pre-rewrite agent entry pages
├── README_ja.md, README_zh.md       # pre-rewrite localized READMEs
├── CHANGELOG.md, log.md             # pre-rewrite history / timeline
├── CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md
├── _canon.yaml                      # v0.3 substrate SSoT (745 lines)
├── pyproject.toml                   # v0.3 build config
├── .mcp.json                        # v0.3 MCP hookup
├── .myco_state/                     # v0.3 runtime state + boot brief
├── .pytest_cache/                   # stale test cache
├── .claude/                         # v0.3 Cowork hooks (SessionStart, PreCompact)
├── .github/                         # v0.3 CI workflows + issue templates
├── src/                             # v0.3 kernel (myco/ — ~24K LoC)
├── tests/                           # v0.3 unit + integration tests
├── docs/                            # v0.3 docs (adapters, evolution_engine, primordia archive, etc.)
├── notes/                           # v0.3 digested notes
├── wiki/                            # v0.3 wiki pages
├── plugin/                          # v0.3 Cowork plugin bundle
├── forage/                          # v0.3 forage staging
├── marketing/                       # v0.3 marketing collateral
├── skills/                          # v0.3 skill bundles
├── scripts/                         # v0.3 utility scripts
├── dist/                            # v0.3 wheel artifacts
└── assets/                          # v0.3 logos / images
```

## Deletion plan

At Stage C (v0.4.0 release):

1. ASCC migration script has run and produced a clean `_canon.yaml` at
   the repository root.
2. Nothing under `legacy_v0_3/` is referenced by any live file.
3. Single commit: `git rm -r legacy_v0_3/`.
4. `v0.3.4-final` tag remains as the sole git-history anchor.
