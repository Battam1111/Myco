> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# Living Bets — 10-signal observatory catalog

> Reference table extracted from L0/cards/LB_living_bets §3 to keep active doctrine lean. Authoritative full enumeration lives at **L2/OBSERVABILITY §2**; this file is a quick-reference mirror.

---

## Observatory composition

**10 signals = 6 base (#1-#6) + 3 cost (#7-#9 per P11) + 1 composite (#10).**

| # | Signal | Class | Counts toward quorum |
|---|---|---|---|
| 1 | Persistence budget | base | DOWN |
| 2 | Evolution rate | base | DOWN |
| 3 | Read-pattern diversity | base | DOWN |
| 4a | Cumulative fork count | base | DOWN |
| 4b | Reachable federation count | base | DOWN |
| 5 | Time trend per signal (OLS slope) | meta | NOT counted (meta-detector) |
| 6 | Read-window-relative position | base | DOWN below ratio 1.0 |
| 7 | Compute cost / cycle | cost (P11) | UP |
| 8 | Network cost / cycle | cost (P11) | UP |
| 9 | Storage cost / cycle | cost (P11) | UP |
| 10 | Composite (variance- or correlation-weighted) | aggregate | n/a |

## L0 commitments (carried in L0/cards/LB_living_bets §3 + §7.4)

- Signal #6 bet-winning region = ratio ≥ 1.
- Composite #10 = correlation-weighted aggregation in steady state, equal-weighted at cold start.
- Quorum = ≥3 of 6 countable signals {#1, #2, #3, #4a, #4b, #6}; signal #5 meta; #4 splits into 4a + 4b.
- Trend significance gate Z ≥ 1.96 (95%, L1-tunable).

## Per-signal full definition

See **L2/OBSERVABILITY §2.1 / §2.2 / §2.3** for definitions, units, threshold semantics, birth-period suspension, and composite weight switching.

## Per-signal direction-against-bet table

See **L2/OBSERVABILITY §3.3**.

## Cascade

- L1 mechanism cadence + tuning: L2/OBSERVABILITY + L1/TROPISM (#3 appetite-locality) + L1/SKIN (#8 egress) + L1/SCHEMA (#9 bytes-added).
- Quorum predicate emission: L0/cards/LB_living_bets §3 (falsifiability quorum) + L2/OBSERVABILITY §3 + C40 at L1/HARD_RULES §1.1.
