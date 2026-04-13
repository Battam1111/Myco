# notes/ — Digestive Substrate

Atomic notes live here as flat files with YAML frontmatter.
Filename pattern: `n_YYYYMMDDTHHMMSS_xxxx.md`

## Four-command set

- `myco eat`     — capture content as a raw note (zero-friction)
- `myco digest`  — move a note through the lifecycle
- `myco observe`    — list or read notes
- `myco hunger`  — metabolic dashboard with actionable signals

## Lifecycle

`raw → digesting → {extracted | integrated | excreted}`

Non-linear jumps are allowed (e.g. `raw → integrated` directly when a note
is already mature enough to merge into canonical structures).

## Schema

See `_canon.yaml` → `system.notes_schema` for the authoritative schema. L10
lint enforces frontmatter validity on every file matching the filename
pattern (this README is ignored by L10 because it does not match).

## Why flat, not tree?

See `docs/primordia/digestive_architecture_craft_2026-04-10.md` — the 4-round
debate record. TL;DR: Zettelkasten/A-Mem/Obsidian Dataview all validate that
flat + metadata scales better than folder hierarchies once note count passes
~100. Status lifecycle is a property, not a location.

## Dogfood status

This is **Myco kernel's own** notes/ directory. The framework eats its own
design decisions here. Every meta-lesson from building Myco should pass
through this tract before it enters wiki/ or MYCO.md.
