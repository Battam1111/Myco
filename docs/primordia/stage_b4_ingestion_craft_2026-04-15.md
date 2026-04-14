# Stage B.4 — Ingestion Craft

> **Date**: 2026-04-15.
> **Governs**: `src/myco/ingestion/` + `tests/unit/ingestion/`.
> **Upward**: L2 `ingestion.md` (L1 R1 hunger, R3 sense, R4 eat).

---

## Round 1 — 主张

Five modules, per the L3 package map:

```
src/myco/ingestion/
├── __init__.py
├── eat.py          # append a raw note
├── hunger.py       # compose hunger report; --execute patches entry-point
├── sense.py        # read-only lookup over canon / notes / docs
├── forage.py       # inspect external dir, list ingestible items
└── boot_brief.py   # maintain marker-delimited signals block in entry-point
```

Each handler exposes a `run(args: dict, *, ctx: MycoContext) -> Result`
form (conforming to the manifest). Internally each also has a typed
helper (`append_note`, `compose_hunger_report`, …) for Python callers
and tests.

Note format: Markdown with a YAML frontmatter block. Filename
`notes/raw/<UTC_ISO>_<slug>.md`. Collision resolution: suffix `_2`,
`_3`, … until a free name is found.

## Round 1.5 — 自我反驳

T1. **Hunger's dependency on Homeostasis.** L2 says reflex signals come
from homeostasis. Should B.4 call `run_immune` itself, or defer? If
B.4 imports homeostasis, we've violated "each subsystem import-safe
in isolation" (L3 invariant 3). But "import-safe" ≠ "never imports";
it means importing ingestion alone shouldn't *require* homeostasis to
be present. Calling homeostasis from hunger is fine — homeostasis is
present at runtime.

T2. **Sense scope.** Unbounded substring search across the whole tree
would be slow and noisy. But scoping by subdirectory is arbitrary.

T3. **Forage under dry-run only.** L2 says forage MUST NOT auto-write
except via `--digest-on-read`. B.5 hasn't landed yet. Do we stub
forage with partial behaviour, or fully implement sans digest hook?

T4. **Boot-brief idempotency.** The entry-point file has an injected
signals block. Re-running hunger must patch in place, not append a
second block. Marker comments (`<!-- BEGIN MYCO SIGNALS -->` /
`<!-- END MYCO SIGNALS -->`) bracket the block.

T5. **Eat failure modes.** L2 says eat rejects only on write-surface
violations. But what if `notes/raw/` doesn't exist? Auto-create (per
"loss-preserving") or raise (per "substrate must be genesis'd
first")?

T6. **Note frontmatter shape.** What goes in? `captured_at`, `tags`,
`source`. Stable field set, not free-form, so lint can validate
later.

## Round 2 — 修正

R1 (T1). Hunger imports homeostasis (kernel + default_registry) at
call time, not at module import. Module-level imports limited to
`myco.core.*`; `myco.homeostasis` imported inside the function body.
This preserves the "each subsystem importable in isolation" invariant
while letting hunger compose findings.

   **But** for Stage B.4, we defer the actual `run_immune` call. The
hunger report's `reflex_signals` is wired to return `()` with a
`# TODO(B.8)` comment — homeostasis dimensions that produce the
signals are authored in B.8, and hooking them up in hunger is cheap
once they exist. We emit `contract_drift` (comparing
`canon.contract_version` vs `synced_contract_version`) and
`raw_backlog` (count of `notes/raw/*.md` files), which are the two
signals we can compute today.

R2 (T2). Sense takes `query: str` and an optional
`scope: Literal["canon", "notes", "docs", "all"]`. Default `"all"`
walks three trees in order, case-insensitive substring match.
Results capped at 50 matches to avoid context bombs. Each match has
`path`, `line`, `snippet`.

R3 (T3). Forage fully implements the read path (list files + their
sizes + detected content type). The `--digest-on-read` flag is
declared but raises `NotImplementedError("digestion not yet
available; lands at Stage B.5")` so the surface shape is stable and
B.5 fills in without changing the signature.

R4 (T4). Boot-brief uses marker comments. Algorithm:

```
if entry_text contains BEGIN_MARKER:
    replace everything between BEGIN and END markers with new block
else:
    append new block at end of entry_text
```

Both markers are HTML comments so they don't render as content. Test
both the "first injection" path and the "re-injection" path.

R5 (T5). Eat **auto-creates `notes/raw/`** if missing. Rationale: L2
says ingestion is "cheap and permissive"; making the directory on
first use is the cheapest possible policy. If the substrate root
itself is missing a canon, that's already caught by `Substrate.load`
at ctx construction time.

R6 (T6). Frontmatter shape:

```yaml
---
captured_at: "2026-04-15T12:00:00Z"
tags: ["foo", "bar"]
source: "agent"
stage: "raw"
---
```

`stage` field lets Digestion (B.5) promote notes by updating this
field, not by moving files. Path stays stable.

## Round 2.5 — 再驳

T7. R1 defers reflex_signals to B.8. Does that mean hunger is mostly
empty for Stage B.4? Will the empty report make the command feel
unfinished?

T8. R4's replace algorithm: what if there are two BEGIN markers
(corruption)? Silently replace the first, leave the second? Or
refuse?

T9. R5 auto-creates `notes/raw/`. What about `notes/` itself? Genesis
creates it; but what if a user `rm -rf notes/` between genesis and
first eat? Auto-create chain: `notes/` → `notes/raw/`.

## Round 3 — 反思

F7. Hunger is deliberately thin at B.4 — "skeleton operational" is the
win, not "feature-complete". The payload fields are:
`contract_drift: bool`, `raw_backlog: int`, `reflex_signals:
tuple[str, ...]` (empty at B.4), `advice: tuple[str, ...]`. `advice`
carries simple strings like "backlog=N; consider `myco digest`".

F8. Two BEGIN markers → `ContractError` — corruption requires human
attention; silent recovery hides a bug.

F9. Auto-create the entire `notes/raw/` chain, including `notes/` if
needed.

### What this craft revealed

- The subsystem split (homeostasis for signals, ingestion for the
  user-facing composition) means hunger's "real" logic lives in B.8's
  dimensions. B.4 establishes the scaffold and the two signals it can
  compute today.
- The manifest handler signature fits cleanly here (ctx is always
  present post-genesis). No exception needed, unlike genesis.
- No L0/L1/L2 edits emerged.

## Deliverables

```
src/myco/ingestion/
├── __init__.py             # re-exports
├── eat.py                  # append_note + run
├── hunger.py               # compose_hunger_report + run
├── sense.py                # search_substrate + run
├── forage.py               # list_candidates + run
└── boot_brief.py           # render + patch_entry_point

tests/unit/ingestion/
├── __init__.py
├── test_eat.py
├── test_hunger.py
├── test_sense.py
├── test_forage.py
└── test_boot_brief.py
```

## Acceptance

- `pytest tests/unit/ingestion/` green.
- Full suite still green (128 prior + ingestion additions).
- Eat + hunger end-to-end: after three eats, hunger reports
  `raw_backlog=3`.
- Boot-brief patch is idempotent: patching twice with the same content
  yields the same entry-point text.
