# Myco Architecture — Start Here

> Single entry point for the Myco repository. If you don't yet know which of
> `OUTLINE.md` / `L0` / `L1` / `L2` / `L3` to open first, **read this page, then
> follow the reading-path table at the bottom.**

Myco is a **cultivated digital organism**: a substrate (the living body) that an
AI agent inhabits and grows under a sealed doctrine, custodied by an owner key
that lives *outside* the body. The repo is two halves: **doctrine** (`docs/architecture/`,
what Myco *is* and *must* be) and **runtime** (`substrate/`, `kernel/`,
`operators/`, `anchor/`, the code that makes it live).

---

## The 4 runtime pieces (one screen)

```
                         ┌──────────────────────────────────────────┐
                         │  anchor/        OWNER-KEY CUSTODY          │
                         │    host/   (Rust signing daemon)          │
                         │    client/ (TypeScript owner UI)          │
                         │  Holds the owner key OUTSIDE the body.    │
                         │  Renders + signs attestations / nonces.   │
                         └──────────────────────────────────────────┘
                                  ▲  attest / sign  (out-of-band)
                                  │
   operators/claude              │              substrate/                      kernel/
   ┌───────────────┐   M5 wire   │   ┌───────────────────────────┐   M5 wire   ┌──────────────────────┐
   │  TypeScript   │  protocol   ▼   │  myco-substrate (Rust)    │  protocol   │  Python worker       │
   │  MCP interface│ ──────────────► │  the living body / daemon │ ──────────► │  governance/tropism/ │
   │  the agent    │  length-prefix  │  M6 runtime: orchestrates │  same bytes │  trajectory/         │
   │  drives this  │  canon-bytes    │  operators <-> kernel     │  diff socket│  hard_rules          │
   └───────────────┘  + HMAC/stdio   └───────────────────────────┘             └──────────────────────┘
                                            │ depends on (Rust crates, compile-time)
                                            ▼
                                     kernel/{shared, skin, schema, continuity, bridge/rust}
```

**Data flow:** `operators` (TS) → `substrate` (Rust) → Python `kernel` worker, all
over the **M5 bridge** (length-prefixed canonical-bytes + HMAC over stdio). Owner-key
custody happens in `anchor`, a separate process the substrate never holds keys for.

| Piece | Language | Role |
|---|---|---|
| [`substrate/`](../../substrate/) | Rust (daemon) | The **living body**. M6 runtime that hosts the organism, runs the metabolic cycle, and orchestrates `operators` ↔ `kernel`. See [`substrate/README.md`](../../substrate/README.md). |
| [`kernel/`](../../kernel/) | Rust crates **+** Python workers | The **doctrine-mechanism layer**. Rust: `shared` / `skin` / `schema` / `continuity` / `bridge`. Python: `governance` / `tropism` / `trajectory` / `hard_rules`. |
| [`operators/claude`](../../operators/) | TypeScript | The **MCP interface** the agent drives. Per-handshake keypair; HMAC-signs request envelopes. |
| [`anchor/`](../../anchor/) | Rust (`host`) + TypeScript (`client`) | **Owner-key custody**, outside the substrate process. Signs attestations, issues nonces, renders doctrine-change diffs. |

---

## The 4 doctrine layers

All under `docs/architecture/`. Stratified L0 → L3: lower layers are more abstract
and more binding (**L4 < L3 < L2 < L1 < L0**). Navigate doctrine via
[`OUTLINE.md`](OUTLINE.md); navigate code via [`L3/PACKAGE_MAP.md`](L3/PACKAGE_MAP.md).

| Layer | Purpose | Entry point |
|---|---|---|
| **L0** — canonical doctrine *(SEALED, v3.1-stratigraphy)* | What Myco **is** and **must** be. 28 principle/covenant/character cards + 60 chengyu (Layer B) + witness tests (Layer C) + catechumenate (Layer D). 4 eternity-clause cards. **Do not edit `L0/` casually** — amendments go through META §7. | [`L0/README.md`](L0/README.md) |
| **L1** — mechanism enforcement (7 docs) | How each doctrine becomes a runtime mechanism: TROPISM, TRAJECTORY, SCHEMA, GOVERNANCE, SKIN, CONTINUITY, HARD_RULES. | [`L1/`](L1/) |
| **L2** — cross-cut themes (3 docs) | Concerns that span mechanisms: TRUST_MODEL, FEDERATION, OBSERVABILITY. | [`L2/`](L2/) |
| **L3** — implementation charter | The code map. Binds module boundaries, dependency direction, build order, test discipline (language-agnostic). | [`L3/PACKAGE_MAP.md`](L3/PACKAGE_MAP.md) + [`L3/OUTLINE.md`](L3/OUTLINE.md) |

Supporting material: [`algorithms/`](algorithms/) (pseudocode), [`diagrams/`](diagrams/)
(ASCII FSMs + dependency graphs), [`schemas/`](schemas/) (JSON schemas).

---

## "I want to…" — reading paths

| I want to… | Open |
|---|---|
| **Understand the philosophy** (what Myco is, why it's a species) | [`L0/README.md`](L0/README.md) → `META.md` → cards `P01`/`P02`/`P14` → [`L0/B_chengyu.md`](L0/B_chengyu.md) |
| **Implement or extend code** | [`L3/PACKAGE_MAP.md`](L3/PACKAGE_MAP.md) (module map) + [`../../substrate/README.md`](../../substrate/README.md) (runtime layout) |
| **Find the mechanism behind a doctrine** | [`OUTLINE.md`](OUTLINE.md) §1 → the matching [`L1/`](L1/) doc |
| **Review a doctrine change** | [`L0/META.md`](L0/META.md) §7 (amendment mechanism) + [`L0/PROVENANCE.md`](L0/PROVENANCE.md) (supersession chain) |
| **Audit for drift / model rollover** | [`L0/canonical_dilemma_corpus/INDEX.md`](L0/canonical_dilemma_corpus/INDEX.md) — read cold, compare to recorded readings |
| **Run it** | [`../guides/GETTING_STARTED.md`](../guides/GETTING_STARTED.md) |

---

> **Navigation note:** this README and [`OUTLINE.md`](OUTLINE.md) are L0 only in the
> *form* (navigation) sense — on any conflict with substantive doctrine, the
> **cards in [`L0/cards/`](L0/cards/) win**.
