# L1 — Contract Protocol (Hard Rules R1–R7)

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L1. Subordinate to `L0_VISION.md`. Authoritative over all L2/L3/L4.
> **This is the single source of truth for Myco's Hard Contract. All other
> files (MYCO.md boot page, CLAUDE.md gateway, SESSION hook prompts, test
> fixtures) must reference — never duplicate and never contradict — this page.**

---

## Purpose

L0 gives Myco its five root principles (Only For Agent, 永恒吞噬, 永恒进化,
永恒迭代, 万物互联) and three derived invariants. L1 translates those into
**seven enforceable rules** that an agent can follow mechanically and that
the immune system can lint automatically.

The rules are numbered R1–R7. They are deliberately few. Adding an eighth
rule requires a craft doc, a contract-version bump, and explicit owner
approval. The old pre-rewrite era shipped with two competing rule counts
(MYCO.md = 7, CLAUDE.md = 6) and drift between them. That class of
discrepancy is now an immune error, not a style choice.

---

## The Seven Rules

### R1 — Session boot is ritualized

**Every session begins with `myco hunger --execute`** (CLI) or the
equivalent `myco_hunger(execute=true)` MCP call. The SessionStart hook
fires it automatically; manual invocation is the backup.

Why: without a ground-truth sense of the substrate's current hunger
(missing canon fields, empty notes, stale contract version), the agent
cannot make safe decisions. Hunger is not optional.

### R2 — Session end is ritualized

**Every session ends with `myco reflect` followed by `myco immune --fix`.**
The PreCompact hook fires these automatically; `myco session-end` is the
manual wrapper.

Why: unconsolidated ingest accumulates. Unfixed drift compounds. A session
that skips reflection leaves the next session's agent starting from a
degraded substrate.

### R3 — Sense before asserting

**Before any factual claim about the substrate — a number, a name, a path,
a decision, a contract version — the agent calls `myco sense` first.**
Memory is not a source; the substrate is.

Why: the whole reason Myco exists is that agent memory across sessions is
unreliable. Asserting substrate-held facts without sensing them
contradicts L0 principle 1 (Only For Agent — the agent reads the
substrate, not its memory).

### R4 — Eat insights the moment they occur

**Every decision, insight, friction point, and user feedback is captured
via `myco eat` immediately — not at session end, not "when I remember",
immediately.** The cost of a lost insight is compound; the cost of eating a
trivial one is near-zero.

Why: memory decay is the main adversary. Defer-and-batch policies always
lose material. Eat-now is cheaper than reconstructing-later.

### R5 — Cross-reference on creation

**After creating any new file, add cross-references to related files.**
Orphaned files are dead knowledge. The mycelium graph (the network of
cross-references) is the substrate's circulatory system; an orphan is a
cell without blood supply.

Why: L2 Circulation requires a connected graph. Creating a file without
linking it is a local operation that inflicts global damage.

### R6 — Write only to the allowed surface

**All writes go to paths declared in `_canon.yaml::system.write_surface.allowed`.**
Any other path is substrate pollution and is rejected by the immune system.

Why: an agent that writes anywhere produces a substrate nobody can lint,
audit, or migrate. Write-surface discipline is what keeps the substrate
mechanically tractable.

### R7 — Top-down subordination is non-negotiable

**Lower layers must conform to upper layers. L4 implements L3, L3 implements
L2, L2 implements L1, L1 implements L0.** A conflict resolves in favor of
the upper layer; implementation convenience is never a license to edit a
contract, doctrine, or vision.

Why: without R7, top-down design degrades into mutual accommodation, and
the layering collapses into accretion. R7 is what makes the greenfield
rewrite worth doing.

---

## Enforcement

Each rule maps to concrete enforcement points. The immune system (L2
Homeostasis) provides the mechanical half; the agent provides the
disciplined half.

| Rule | Mechanical enforcement | Agent discipline |
|------|------------------------|------------------|
| R1 | `SessionStart` hook; `myco_hunger` first-call detection | Invoke manually if hook fails |
| R2 | `PreCompact` hook; `myco session-end` summary | Invoke manually before `/compact` |
| R3 | — (not mechanically enforceable) | Call `myco sense` before factual claims |
| R4 | — | Call `myco eat` on every decision/insight |
| R5 | Immune lint: orphan file detection | Add cross-refs at file creation |
| R6 | CLI/MCP refuse writes outside allowed surface | n/a (enforced) |
| R7 | Immune lint: layer-mapping integrity (L2 refers L1, L3 refers L2) | Re-read upper layer before editing lower |

Rules that are not mechanically enforceable (R3, R4, partial R5) are
elevated in the session-start context so the agent sees them on every boot.

---

## Version & changes

This page is versioned by the **contract version** in `_canon.yaml`. Any
change to R1–R7 (wording, semantics, count) is a contract change:

1. Author a craft doc in `docs/primordia/`.
2. Obtain explicit owner approval.
3. Bump `_canon.yaml::contract_version`.
4. Log in `docs/contract_changelog.md`.
5. Update every file that references the Hard Contract (see the
   `grep -r "Hard Contract"` suite in the immune tests).

Minor editorial tightening (typo fixes, clarifying footnotes) is allowed
without a contract bump, but the semantics of the seven rules are frozen
until the next craft+approval cycle.
