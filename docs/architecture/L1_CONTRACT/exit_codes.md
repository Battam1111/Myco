# L1 — Exit-Code Contract

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L1. Subordinate to `L0_VISION.md` and `protocol.md`.

---

## Why this is in L1

CI pipelines, agent scripts, and downstream projects (e.g. ASCC) key off
Myco's exit codes. Changing exit semantics silently breaks every consumer.
Exit codes are therefore part of the kernel contract, not an L3
implementation detail.

## The ladder

All Myco subcommands that can "find issues" return one of:

| Code | Meaning |
|------|---------|
| `0` | Clean — no issues at or above the configured threshold |
| `1` | Issues found at HIGH severity (below CRITICAL) |
| `2` | Issues found at CRITICAL severity |

Codes `≥3` are reserved for operational failures (bad flags, I/O errors,
contract violations) and are never "lint results".

## Severity taxonomy

Four severities, strictly ordered:

```
CRITICAL (4)  >  HIGH (3)  >  MEDIUM (2)  >  LOW (1)
```

Severity is a property of each individual finding. The exit code is
computed from the *worst* finding the policy considers actionable.

## Categories

Findings are classified into exactly four categories. Every lint dimension
belongs to exactly one.

| Category | Meaning | Typical dimensions |
|----------|---------|--------------------|
| **mechanical** | Structural integrity of the substrate files | write-surface, required canon fields, syntax |
| **shipped** | Integrity of distributable artifacts | package version sync, release metadata |
| **metabolic** | Health of ongoing digestion | undigested notes, stale reflections |
| **semantic** | Correctness of cross-references and claims | orphan links, canon-reality drift |

Each dimension declares its category via the
`Dimension.category: ClassVar[Category]` attribute. The `Category` enum
(`mechanical` / `shipped` / `metabolic` / `semantic`) is defined in
`src/myco/homeostasis/finding.py`. Canon mirrors this via
`lint.dimensions: <id> → <category>` to keep the mapping human-
auditable at substrate read time. A category change is still a
contract bump; the class-attribute form is the mechanical SSoT, the
canon block is the legible SSoT, and the two must agree.

## `--exit-on` grammar

The `--exit-on` flag selects which categories + severities trip exit code
`≥1`. Grammar:

```
<spec>    ::= <global> | <per-cat-list>
<global>  ::= "never" | "critical" | "high"
<per-cat-list> ::= <cat-rule> ("," <cat-rule>)*
<cat-rule> ::= <cat> ":" <threshold>
<cat>     ::= "mechanical" | "shipped" | "metabolic" | "semantic"
<threshold> ::= "never" | "critical" | "high"
```

Semantics:

- `never`: findings in this category never trip exit ≥1.
- `critical`: only CRITICAL findings trip; exit = 2.
- `high`: HIGH or CRITICAL findings trip; exit = 1 on HIGH, 2 on CRITICAL.
- Global forms apply the same threshold to all four categories.
- Per-category lists default unnamed categories to `critical`.
- Unknown categories or thresholds raise a contract error (exit code 3).

Example:

```
--exit-on=mechanical:critical,shipped:critical,metabolic:never,semantic:never
```

This is the canonical "CI gate" — block on structural or shipping breaks,
ignore ongoing metabolic/semantic noise.

## Skeleton-mode downgrade

When the substrate is a fresh auto-seeded skeleton (presence of
`.myco_state/autoseeded.txt` marker and no digested `n_*.md` notes), the
dimensions listed in `_canon.yaml::lint.skeleton_downgrade.affected_dimensions`
are auto-downgraded from CRITICAL to HIGH. Rationale: a just-born
substrate is *expected* to be incomplete, and failing a first-run hunger
call blocks legitimate adoption.

At v0.5.6 that list is empty — no dimension is currently skeleton-
downgraded. The field is retained so future dimension retirements (or
new dimensions that earn skeleton grace) can be declared there without
a schema bump. The downgrade is a property of the kernel, not the flag
set. Once the substrate metabolizes its first note, the marker is stale
and downgrade stops applying.

## Legacy behavior (pre-v0.4.0)

Before v0.4.0, `--exit-on` was absent and all dimensions returned their
own severity; the worst severity mapped directly to the exit code. That
path is retained as the fallback when no `--exit-on` is passed, but is
not preferred for CI use. New callers should always pass `--exit-on`.

## Change policy

Changing any of the following is a contract bump:

- Adding or removing a category.
- Changing the severity → exit-code map.
- Changing the skeleton-mode downgrade rule.
- Adding or removing a global keyword (`never` / `critical` / `high`).

Adding a new lint *dimension* is not a contract bump **if** it lands in an
existing category with established severity policy. New dimensions land in
L3 with an entry in the changelog.
