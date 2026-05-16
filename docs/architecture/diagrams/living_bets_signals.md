# Living Bets — 10-signal observatory catalog (extracted from L0_VISION.md §7.3)

> **Status**: REFERENCE TABLE. Extracted from L0_VISION.md DRAFT 9 SEALED §7.3 to keep active doctrine lean. Authoritative full enumeration lives at **L2_OBSERVABILITY §2**; this file is a quick-reference mirror.
> **Source**: L0_VISION.md DRAFT 9 SEALED commit `e796451`; M26.0 cascade A6 + M25.2/M25.3 elaborations folded into L2_OBSERVABILITY.

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

## L0 commitments (carried in L0 §7.3 + §7.4)

- Signal #6 bet-winning region = ratio ≥ 1.
- Composite #10 = correlation-weighted aggregation in steady state, equal-weighted at cold start.
- Quorum = ≥3 of 6 countable signals {#1, #2, #3, #4a, #4b, #6}; signal #5 meta; #4 splits into 4a + 4b.
- Trend significance gate Z ≥ 1.96 (95%, L1-tunable).

## Per-signal full definition

See **L2_OBSERVABILITY §2.1 / §2.2 / §2.3** for definitions, units, threshold semantics, birth-period suspension, and composite weight switching.

## Per-signal direction-against-bet table

See **L2_OBSERVABILITY §3.3**.

## Cascade

- L1 mechanism cadence + tuning: L2_OBSERVABILITY + L1_TROPISM (#3 appetite-locality) + L1_SKIN (#8 egress) + L1_SCHEMA (#9 bytes-added).
- Quorum predicate emission: L0 §7.4 + L2_OBSERVABILITY §3 + C40 at L1_HARD_RULES §1.1.
