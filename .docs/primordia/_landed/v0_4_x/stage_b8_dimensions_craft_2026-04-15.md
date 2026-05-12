# Stage B.8 Craft — Fresh Dimensions

> **Date**: 2026-04-15
> **Stage**: B.8 — `homeostasis/dimensions/` authored fresh (not ported
> from v0.3's 30-dim table).
> **Inputs**: L1 `exit_codes.md` (category ladder), L2 `homeostasis.md`
> (doctrine), L3 invariants from `migration_strategy.md`.
> **Depth calibration**: single round. The category taxonomy is fixed
> by L1, the file-per-dim rule is fixed by L2, and the upstream kernel
> (B.2) already ships the loop, skeleton-downgrade, and exit policy.
> Remaining choices are scope and severity per dimension — small, local
> calls, not architectural tensions.

---

## Round 1 — Proposal

### Selection rule

A dimension earns a slot at v0.4.0 only if it satisfies **all** of:

1. Maps to exactly one L1 category with clear severity.
2. Runnable from ``MycoContext`` alone (no network, no subprocess).
3. Has a concrete failure the v0.4.0 substrate could plausibly exhibit.
4. Doesn't duplicate something already enforced upstream (e.g. the
   canon parser already rejects missing top-level keys — no dimension
   for that).

### The eight dimensions

| ID    | Category   | Default Sev | Slug                  | What it checks |
|-------|------------|-------------|-----------------------|----------------|
| M1    | mechanical | HIGH        | `canon_identity_fields` | `identity.substrate_id` + `identity.entry_point` non-empty. |
| M2    | mechanical | HIGH        | `entry_point_exists`    | The file at `canon.entry_point` exists under root. |
| M3    | mechanical | MEDIUM      | `write_surface_declared`| `system.write_surface.allowed` is a non-empty list. |
| SH1   | shipped    | MEDIUM      | `package_version_ref`   | If `versioning.package_version_ref` is declared, target file exists. |
| MB1   | metabolic  | MEDIUM/LOW  | `raw_notes_backlog`     | >10 raw notes → MEDIUM; 1-10 → LOW; 0 → silent. |
| MB2   | metabolic  | LOW         | `no_integrated_yet`     | Raw notes exist but `notes/integrated/` is empty. |
| SE1   | semantic   | MEDIUM      | `dangling_refs`         | One finding per dangling edge in `build_graph(ctx)`. |
| SE2   | semantic   | LOW         | `orphan_integrated`     | Integrated notes with no inbound edges. |

### Interfaces

- Each lives in `src/myco/homeostasis/dimensions/<slug>.py`, one class,
  one module-level docstring that becomes `--explain` output.
- `dimensions/__init__.py` exports `ALL = (M1, M2, M3, SH1, MB1, MB2,
  SE1, SE2)`.
- The old smoke dim `L0KernelAlive` is deleted per its own docstring
  (*"Removed at Stage B.8 when real mechanical dimensions arrive."*).

---

## Round 1.5 — Rebuttal

**R1.** *"M3 overlaps with M2 — both are about write surface."*
No. M2 checks the entry-point **file**; M3 checks the **declaration**.
A canon with `write_surface.allowed: []` passes M2 (entry file may
still exist) but should fail M3 (empty declaration = no governance).
Keep both.

**R2.** *"MB1's severity bands are arbitrary."*
Agreed — 10 is a heuristic. But `reflect` is the primary backpressure,
and 10 un-digested raws is the threshold where a human should eyeball
the queue. Encode it as a constant at module top, easy to tune.

**R3.** *"SE1 with one finding per dangling edge floods the report."*
Acceptable for a first cut; perfuse already surfaces the same data as
a payload list. If this becomes noisy we cap at 20 findings and emit a
summary — one-line change, no contract bump (severity stays MEDIUM).

**R4.** *"SH1 is trivially satisfied in every test substrate."*
Intentional. The genesis template (`canon.yaml.tmpl`) emits
`package_version_ref: "src/myco/__init__.py"`. The dimension fires
only when the substrate *declares* a ref that then goes missing —
which is a real failure mode during rewrites. Empty `versioning:`
silently skips.

**R5.** *"You're deleting `L0KernelAlive` and its test — that's two test
assertions in `test_registry.py` and `test_kernel.py` that break."*
Yes — both are intentional tripwires, same pattern as the B.7 scaffold
test. They get rewritten to pin the real default-registry shape:
`reg.has("M1")` / `reg.has("SE1")` etc.

---

## Round 2 — Revision

- Constants go at module top (e.g. `_BACKLOG_MEDIUM_THRESHOLD = 10`).
- Dimensions that reach into the graph import `build_graph` lazily
  inside `.run()` so the module stays cheap to import and the registry
  can be constructed before `circulation` is ready in future refactors.
- Each dimension handles a missing canon block (e.g. `lint` absent) by
  returning no findings rather than raising. Raising is reserved for
  bugs in the dimension itself.

---

## Round 2.5 — Re-rebuttal

**RR1.** *"SE2 will always fire in a fresh-seeded substrate because
genesis doesn't write any integrated notes."*
Checked: SE2 only fires on notes that *exist*. A fresh substrate has
zero integrated notes → zero findings. The dimension fires only after
digest has produced integrated notes that nobody references.

**RR2.** *"What about the `is_skeleton` downgrade — should these
dimensions opt in?"*
Only L0/L1 historically downgrade (per canon). These new dimensions
live at M1-SE2 IDs — none are in `affected_dimensions`. No opt-in.
If a future substrate config wants a new downgrade target, it adds to
that list; no dimension code change needed.

---

## Round 3 — Reflection

The most instructive tension this craft surfaced was the pull between
**v0.3's 30-dim inventory** and **the L3 invariant to author fresh**.
Eight dimensions feels sparse compared to thirty — but every one of
them maps to a failure the v0.4.0 substrate can actually exhibit today,
and each is implementable in under 40 LoC. The old inventory's sprawl
was a symptom of a megafile that didn't enforce scope discipline; with
one dim per file, adding a ninth next quarter costs ~50 lines + a
changelog line and is therefore cheap. The contract is **scope
discipline**, not dimension count. Ship eight, grow as needs emerge.

Escalation: none. This is pure L3 execution on a well-specified
surface. Reports back at commit time.
