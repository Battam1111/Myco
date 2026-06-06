# Myco Architecture: Start Here

> Single entry point for the Myco repository. If you don't yet know which of
> `OUTLINE.md` / `L0` / `L1` / `L2` / `L3` to open first, **read this page, then
> follow the reading-path table at the bottom.**

Myco is a **cultivated digital organism**: a substrate (the living body) that an
AI agent inhabits and grows under a sealed doctrine. It is keyless: trust is the
live human at the CI gate, plus the substrate's own causal DAG, plus the
BLAKE3-sealed doctrine bundle. The repo is two halves: **doctrine**
(`docs/architecture/`, what Myco *is* and *must* be) and **runtime**
(`substrate/`, `kernel/`, `operators/`, the code that makes it live).

---

## The 3 runtime pieces (one screen)

```
   operators/claude              M5 wire           substrate/                  M5 wire        kernel/
   ┌───────────────┐          protocol         ┌────────────────────┐       protocol     ┌──────────────────────┐
   │  TypeScript   │  ──────────────────────►  │  myco-substrate    │  ───────────────►  │  Python worker       │
   │  MCP interface│   length-prefixed         │  (Rust daemon)     │   same canonical   │  governance/tropism/ │
   │  the agent    │   canonical-bytes         │  the living body   │   bytes over       │  trajectory/         │
   │  drives this  │   + HMAC over stdio       │  M6 runtime+cycle  │   a diff socket    │  hard_rules          │
   └───────────────┘                           └────────────────────┘                    └──────────────────────┘
                                                          │ depends on (Rust crates, compile-time)
                                                          ▼
                                          kernel/{shared, skin, schema, continuity, bridge/rust}
```

**Data flow:** `operators` (TS) → `substrate` (Rust) → Python `kernel` worker, all
over the **M5 bridge** (length-prefixed canonical-bytes + HMAC over stdio). There is
no separate key-custody process: Myco is keyless, and the substrate signs only its
own at-rest state with a key it generates for itself.

| Piece | Language | Role |
|---|---|---|
| [`substrate/`](../../substrate/) | Rust (daemon) | The **living body**. M6 runtime that hosts the organism, runs the metabolic cycle, and orchestrates `operators` ↔ `kernel`. See [`substrate/README.md`](../../substrate/README.md). |
| [`kernel/`](../../kernel/) | Rust crates **+** Python workers | The **doctrine-mechanism layer**. Rust: `shared` / `skin` / `schema` / `continuity` / `bridge`. Python: `governance` / `tropism` / `trajectory` / `hard_rules`. |
| [`operators/claude`](../../operators/) | TypeScript | The **MCP interface** the agent drives. Keyless session (session-secret handshake, HMAC over the wire). |

---

## The 4 doctrine layers

All under `docs/architecture/`. Stratified L0 → L3: lower layers are more abstract
and more binding (**L4 < L3 < L2 < L1 < L0**). Navigate doctrine via
[`OUTLINE.md`](OUTLINE.md); navigate code via [`L3/PACKAGE_MAP.md`](L3/PACKAGE_MAP.md).

| Layer | Purpose | Entry point |
|---|---|---|
| **L0**: canonical doctrine *(SEALED, v3.1.5, keyless)* | What Myco **is** and **must** be. 28 principle/covenant/character cards + 60 chengyu (Layer B) + witness tests (Layer C) + catechumenate (Layer D). 4 eternity-clause cards. **Do not edit `L0/` casually**: amendments go through META §7. | [`L0/README.md`](L0/README.md) |
| **L1**: mechanism enforcement (7 docs) | How each doctrine becomes a runtime mechanism: TROPISM, TRAJECTORY, SCHEMA, GOVERNANCE, SKIN, CONTINUITY, HARD_RULES. | [`L1/`](L1/) |
| **L2**: cross-cut themes (3 docs) | Concerns that span mechanisms: TRUST_MODEL, FEDERATION, OBSERVABILITY. | [`L2/`](L2/) |
| **L3**: implementation charter | The code map. Binds module boundaries, dependency direction, build order, test discipline (language-agnostic). | [`L3/PACKAGE_MAP.md`](L3/PACKAGE_MAP.md) + [`L3/OUTLINE.md`](L3/OUTLINE.md) |

Supporting material: [`algorithms/`](algorithms/) (pseudocode), [`diagrams/`](diagrams/)
(ASCII FSMs + dependency graphs), [`schemas/`](schemas/) (JSON schemas).

---

## "I want to…": reading paths

| I want to… | Open |
|---|---|
| **Understand the philosophy** (what Myco is, why it's a species) | [`L0/README.md`](L0/README.md) → `META.md` → cards `P01`/`P02`/`P14` → [`L0/B_chengyu.md`](L0/B_chengyu.md) |
| **Implement or extend code** | [`L3/PACKAGE_MAP.md`](L3/PACKAGE_MAP.md) (module map) + [`../../substrate/README.md`](../../substrate/README.md) (runtime layout) |
| **Find the mechanism behind a doctrine** | [`OUTLINE.md`](OUTLINE.md) §1 → the matching [`L1/`](L1/) doc |
| **Review a doctrine change** | [`L0/META.md`](L0/META.md) §7 (amendment mechanism) + [`L0/PROVENANCE.md`](L0/PROVENANCE.md) (supersession chain) |
| **Audit for drift / model rollover** | [`L0/canonical_dilemma_corpus/INDEX.md`](L0/canonical_dilemma_corpus/INDEX.md): read cold, compare to recorded readings |
| **Run it** | [`../guides/GETTING_STARTED.md`](../guides/GETTING_STARTED.md) |

---

> **Navigation note:** this README and [`OUTLINE.md`](OUTLINE.md) are L0 only in the
> *form* (navigation) sense: on any conflict with substantive doctrine, the
> **cards in [`L0/cards/`](L0/cards/) win**.
