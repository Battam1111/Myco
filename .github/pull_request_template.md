<!-- A PR is a raw-note in Myco's metabolism. Filling this template
     well lets the maintainer assimilate it fast. Delete any section
     that doesn't apply. -->

## What this changes

<!-- One sentence, agent-readable. Name the subsystem + the specific
     file(s). Example: "circulation/graph.py: _resolve now returns None
     on files that exist-but-are-empty, so SE1 stops reporting empty
     files as dangling." -->

## Why

<!-- Which L0 principle / L1 rule / L2 doctrine section does this
     serve? If it contradicts any, flag it explicitly and argue the
     case. -->

## How you verified

- [ ] `python -m pytest` passes locally
- [ ] `python -m ruff check src tests` + `ruff format --check` clean
- [ ] `python -m mypy src/myco` clean
- [ ] `python -m myco immune` passes (specify `--exit-on` if you tuned it)
- [ ] `python -m myco hunger` shows no new drift
- [ ] If you touched any verb's write path: `check_write_allowed` still guards

<!-- CI will re-run all six. Checking them locally saves a round. -->

## Craft doc

<!-- For L0/L1/L2 changes, link the `docs/primordia/*_craft_*.md` that
     proposed this work. If you haven't written one yet but think this
     PR needs one, say so here — the maintainer will help bootstrap. -->

## Contract impact

<!-- Does this change:
     - R1–R7 text? → requires craft + molt
     - Exit codes? → note the specific code change
     - Verb manifest? → flag the specific arg shape delta
     - Dimension roster? → note added/removed IDs
     - Canon schema? → update docs/schema/canon.schema.json in this PR
     - Nothing in the list above? → just say "none" -->

## Deprecated?

<!-- If this PR deprecates something (verb, arg, dim id, canon field),
     confirm:
     - The old name/form still resolves
     - A one-shot DeprecationWarning fires
     - The removal target version is documented (typically v1.0.0 for
       v0.5.x deprecations)
     - CHANGELOG.md [Unreleased] section has an entry -->

## Checklist

- [ ] CHANGELOG.md has an `[Unreleased]` entry
- [ ] Commit message follows the house style (see recent commits)
- [ ] No unrelated reformatting in the diff
- [ ] No secrets, `.env` files, or credential-bearing content staged
