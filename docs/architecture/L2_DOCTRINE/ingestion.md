# L2 — Ingestion

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/*`.
> **Upward mapping**: implements L1 R1 (hunger), R3 (sense), R4 (eat).

---

## Responsibility

Ingestion owns the **intake surface** of the substrate. It implements
L0 principle 2 (永恒吞噬 — eternal ingestion, devour everything): any
input the agent can point at is ingestible raw material, without filter
on what enters.

Ingestion captures raw material and reports back what the substrate is
currently hungry for. It does **not** transform what it captures —
transformation belongs to Digestion. Ingestion is therefore cheap and
permissive; rejection at intake is reserved for write-surface (R6)
violations, never for content judgment.

## Boundary

Ingestion **does**:

- Capture raw notes via `myco eat` with minimal, loss-preserving writes.
- Inspect the substrate and produce a hunger report (what's missing,
  what's stale) via `myco hunger`.
- Answer factual queries about substrate contents via `myco sense`.
- Maintain the boot-brief injection into the project's entry-point file
  (MYCO.md / CLAUDE.md signals block).

Ingestion **does not**:

- Digest, integrate, or consolidate notes (→ Digestion).
- Check invariants or raise lint errors (→ Homeostasis).
- Traverse cross-references (→ Circulation).
- Write outside `notes/` and `.myco_state/` (R6).

## Interfaces

Four commands, each with a CLI form and an MCP-tool form. Names retain the
biological metaphor per §9 E1.

```
myco eat     <content> [--tags ...] [--source ...]
myco hunger  [--execute] [--json]
myco sense   <query>    [--scope ...] [--format ...]
myco forage  [--path DIR] [--digest-on-read]
```

- **eat**: append a raw note. Never fails on content shape; failure is
  reserved for write-surface violations.
- **hunger**: compute the hunger report. `--execute` also writes the boot
  brief and patches the entry-point signals block.
- **sense**: read-only lookup, keyed by canon, notes, and doctrine docs.
- **forage**: inspect a candidate external directory for ingestible
  material; does not auto-write unless `--digest-on-read` is passed
  (which delegates to Digestion).

## Cross-subsystem contract

- Consumes the canon schema produced by Genesis.
- Produces raw notes that Digestion transforms.
- Reads cross-references that Circulation maintains.
- Surfaces reflex signals that Homeostasis raises.

## What changed from pre-rewrite

The old `hunger` command did a lot of things (detect drift, compute
backlog, patch entry-point, cache brief). In v0.4 these are still the
same four outputs, but their implementations are split by subsystem:
drift detection and reflex severity come from Homeostasis; hunger
composes them into a single user-visible report.
