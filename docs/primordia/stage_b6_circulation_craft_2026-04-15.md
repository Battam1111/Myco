# Stage B.6 — Circulation Craft

> **Date**: 2026-04-15.
> **Governs**: `src/myco/circulation/` + `tests/unit/circulation/`.
> **Upward**: L2 `circulation.md` (§propagate per §9 E4 redefinition).

---

## Round 1 — 主张

Three modules per the L3 package map:

```
src/myco/circulation/
├── __init__.py
├── graph.py        # build cross-reference index on demand
├── perfuse.py      # report graph health; propose fixes; no auto-edit
└── propagate.py    # cross-substrate push (fresh implementation; §9 E4)
```

Graph source material:

- `_canon.yaml::*._ref` fields (scalar path strings).
- Frontmatter `references:` in notes under `notes/`.
- Standard markdown link syntax (bracketed text followed by a
  parenthesized target) in `notes/**`, `docs/**`, and the entry-point
  file.

Graph nodes: substrate-relative path strings. Edges: (src_path →
dst_path, kind). `kind` is one of `canon_ref`, `note_ref`,
`markdown_link`.

## Round 1.5 — 自我反驳

T1. **Markdown link regex.** A naive `\[.*?\]\((.*?)\)` matches code
fences, inline `[]()` in comments, and HTML-style comments. Need to
skip fenced code blocks and external URLs.

T2. **Where does graph building live at import time?** Per the L3
invariant 3 (each subsystem import-safe in isolation), circulation
must not require ingestion/digestion at import. It may *read*
substrate files through `core.paths` — fine.

T3. **Perfuse auto-edit vs propose-only.** L2 says "propose only;
humans edit". But there's a dry-run/no-dry-run flag pair implied. If
`--dry-run` is the *only* mode, the flag is meaningless. Two
answers: (a) perfuse always runs dry-run and prints a report; (b)
perfuse can apply a subset of fixes (e.g. remove dangling refs) when
asked. L2 is explicit: no rewrite. Adopt (a).

T4. **Propagate source-trace frontmatter shape.** L2 specifies
`source: <src-project>@<commit>`, `ingest_state: raw`. Getting the
commit is `subprocess` territory. For v0.4.0 alpha we accept a
`commit` string arg (CLI passes it; tests pass it explicitly); the
surface layer in B.7 reads `git rev-parse HEAD` if available.

T5. **Propagate duplicate-by-id check.** Source notes under
`integrated/` are named `n_<stamp>_<slug>.md`. The downstream inbox
is `notes/raw/`. Collision means a note with the same filename
already exists. Behavior: raise `ContractError` — matches L2's
"duplicate-by-id is an error".

T6. **Contract-version compatibility.** Major mismatch errors; minor
mismatch warns. We don't have a warning channel yet (Stage B.8's
lint dimensions will). For B.6: major mismatch raises; any other
mismatch is reported in the payload as `compat_warnings: list[str]`.

T7. **Graph file-read cost.** Walking all markdown under a substrate
is O(N files × avg size). Acceptable at alpha; cache is out of scope.

## Round 2 — 修正

R1 (T1). Strip fenced code blocks before scanning for markdown links.
Simple state machine: outside-fence / inside-fence toggled on lines
starting with ```` ``` ````. Links in HTML comments are rare and
permitted — lint can worry about them later.

R2 (T2). Graph module reads files via `ctx.substrate` only. No
dependency on other subsystems at import time.

R3 (T3). `perfuse` is always a report. Payload carries `orphans:
list[path]`, `dangling: list[(src, ref)]`, `proposals: list[str]`
(human-readable nudges). No `--dry-run` flag needed; keep the
`scope` arg so callers can limit to `canon`, `notes`, `docs`, `all`.

R4 (T4). Propagate signature:

```python
def propagate(
    *,
    src_ctx: MycoContext,
    dst_root: Path,
    select: Literal["integrated", "distilled", "both"] = "integrated",
    commit: str | None = None,
    dry_run: bool = False,
) -> Result: ...
```

The `commit` is stamped into each propagated note's frontmatter as
`source` = `"<src_substrate_id>@<commit-or-unknown>"`.

R5 (T5). On collision, error. Entire propagate is transactional:
either all files are written (dry_run ignored) or none are — we
collect target paths first, verify none exist, then write.

R6 (T6). Major-version mismatch raises `ContractError`. Any other
mismatch produces a `compat_warnings` string in the payload.
"Major" parses the contract-version ladder's major component via
`PackageVersion`-ish parser — we have `core.version.ContractVersion`
already.

## Round 2.5 — 再驳

T8. R3 drops the `--dry-run` CLI flag entirely. L2 doctrine's listed
signature has it. Keep the flag accepted-but-ignored for CLI parity;
document that perfuse is always dry-run at B.6. Future stages may
activate a write-path subset.

T9. R5 says propagate is transactional. But once we've stamped
`now` into each rendered note, two runs produce different outputs —
that breaks the "dry-run must equal real run" invariant. Fix: accept
a `now` arg (default: real now) and use it for all notes in a single
call.

T10. What's a "distilled" note in the propagate select space? B.5
writes `notes/distilled/d_<slug>.md`. Propagating those is safe —
they're still notes. Select=`both` reads both dirs.

## Round 3 — 反思

F8. Perfuse accepts `dry_run` but documents it as informational. The
graph health is always read-only at B.6.
F9. Single `now` per propagate call.
F10. `distilled` dir participates in the select axis.

### What this craft revealed

- The "report-only" discipline keeps Circulation aligned with L2's
  no-rewrite invariant while the code stays small.
- Propagate's contract-version check is the first live consumer of
  `core.version.ContractVersion`. Good — it confirms the version
  primitive's shape.
- No L0/L1/L2 edits needed.

## Deliverables

```
src/myco/circulation/
├── __init__.py
├── graph.py
├── perfuse.py
└── propagate.py

tests/unit/circulation/
├── __init__.py
├── test_graph.py
├── test_perfuse.py
└── test_propagate.py
```

## Acceptance

- `pytest tests/unit/circulation/` green.
- Full suite still green (199 prior + additions).
- Propagate src→dst round-trip: integrate notes in src, propagate to
  dst, dst's `notes/raw/` shows the propagated files with source-trace
  frontmatter.
- Graph orphan + dangling detection works on a seeded substrate.
