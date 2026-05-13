# L2 — Observability Doctrine

> **Status**: DRAFT 1 (2026-05-13). Cross-cut doctrine theme.
> **Layer**: L2.
> **Scope**: how the substrate observes itself. Cross-cuts L0 §7 Living Bets observatory + L0 §9.4 burst detection + L1_HARD_RULES §1 immune-grade sporocarps + I3 self-validation + I5 reachability + L1_SCHEMA §2.4 drill failure-rate baseline + L1_CONTINUITY §1.2 cycle backlog detection. Answers: what is v0.9's self-model; what is the falsifiability surface; how does the substrate know if it is healthy / drifting / failing?

---

## §1. Why observability is L0-anchored

The substrate is autopoietic (per P1.a self-hosting): no human in the maintenance loop. The substrate must observe itself, signal pathology to itself + the operator-agent + the owner via the anchor surface. Without observability, the substrate's claim "I am healthy" is unfalsifiable.

L0 §7 Living Bets is the meta-commitment: the substrate's value-to-the-pair is **falsifiable**. The bet is staked; the observatory measures the stakes; the falsifiability trigger fires when the bet is lost.

Observability is what makes the autopoietic loop honest.

---

## §2. The Living Bets observatory (6 base + 1 composite + 1 birth-period derivative)

Per L0 §7 + L1_TROPISM §4 birth-period predictor.

### §2.1 Six base signals

| # | Signal | Definition | Threshold |
|---|---|---|---|
| 1 | **Persistence budget** | Total content (size, node count, edge count, event-record count) | Emergent from substrate history |
| 2 | **Evolution rate** | Governance changes (schema bumps, rule revisions, vocabulary refactors, dispatch parameters) over time | Emergent |
| 3 | **Read-pattern diversity** | Variety of substrate-read patterns over a rolling window (specific operationalization depends on L1 dispatch form; under tropism = appetite-activity diversity) | Emergent |
| 4 | **Federation health** | Split per pass-2 saprotroph-6: 4a cumulative fork count (monotonic); 4b reachable-federation count (peers responding to health probe). 4a-4b divergence = mycelial fragmentation. | 4a-4b divergence threshold emergent |
| 5 | **Time trend per signal** | Direction (up / flat / down) of each above signal | — |
| 6 | **Read-window-relative position** | `substrate-total-size / agent-attested-context-window`. Substrate-total, not digest-fraction (per pass-2 mycoparasite-16). Threshold separating bet-wins from bet-loses regions is emergent (seed ~100). | Emergent in steady state; seed at birth |

### §2.2 One composite signal

7. **Composite health score** — emergent weighted aggregation of signals 1-6. Weights emerge from substrate's own historical correlation between signal patterns and substrate-health outcomes (per C6.4); no pre-set.

### §2.3 Birth-period observability (per L1_TROPISM §4)

The birth-period observatory provides early signals for the maturity-attestation termination path:

- **Sporocarp count progression** (toward birth-period N threshold)
- **Active-operation time accumulation** (toward birth-period M threshold)
- **Per-axis threshold-emergence convergence** (epsilon-below-target on each appetite axis)

These birth-period signals are NOT part of the steady-state 7-signal observatory; they retire after birth-period termination. They're tracked separately in birth-period diagnostic sporocarps.

---

## §3. Falsifiability trigger (the bet-resolution mechanism)

Per L0 §7 + pass-2 astronaut-6 + saprotroph-7: the trigger is a **rolling-window quorum**:

> Over a **90-day window of active operation** (L1-tunable), if **≥3 of signals 1-6 trend concurrently against the bet** AND signal #6 stays < 1 for ≥ 50% of cycles in the window, the substrate fruits a `bet_weakening_quorum` event requiring owner re-justification of Myco's existence per L0 §10.2.

Spike events within a window are DAG-recorded but do not by themselves fire the trigger.

**This is the substrate's structural confession mechanism**: when the bet weakens, the substrate auto-emits the admission. The owner is not relied on to detect drift; the substrate is.

---

## §4. Per-cycle invariant checks (the immune system)

Per L1_CONTINUITY §1.1 (5-step cycle) + L1_SCHEMA §4 (tiered validation):

### §4.1 Per-cycle checks (tier-1)

Every metabolic cycle:
- I1 identity record + active prefix of owner_key_history
- I3 consistency at tier-1 fields against SSoT
- I4 DAG-tip hash + Merkle chain self-consistency
- I8 skin breach check over events absorbed this cycle

### §4.2 Per-deep-cycle checks (tier-2)

Deep cycle (default 1/100 of metabolic-cycle rate):
- I5 reachability over current SSoT-listed storage tiers
- Tier-2 sampled validation (per L1_SCHEMA §4.3 if L4 escalates)
- Recovery-drill scheduling

### §4.3 Witnesses-not-verdicts (per L0 §9.3)

Check results emit cryptographic-proof tuples — sampled leaf hashes (derived from anchor-surface nonce per L0 §9.3), Merkle paths, parent hashes, check inputs — sufficient for owner / anchor-surface verifier to independently re-derive. The substrate does NOT emit pass/fail summaries.

**Anchor-nonce-derived sampling** (per pass-3 mycoparasite-3): sampling indices are `H(anchor_surface_nonce, leaf_count)` — substrate cannot bias sampling toward honest portions.

---

## §5. Immune-grade sporocarp catalog (per L1_HARD_RULES §1)

20 CRITICAL-grade breaches (C1-C20) are immune-event types. Each:
- Detected at a specific L1 mechanism site
- Independently traces to ≥1 P + ≥1 I
- Triggers immediate auto-quarantine + named immune sporocarp

Less-than-CRITICAL breaches (daily / elevated grades) emit immune sporocarps without auto-quarantine. The observatory tracks immune-event rates as part of composite health score.

**The full catalog is in L1_HARD_RULES §1** — a single index across the 6 mechanism docs. When L4 implements the immune detection layer, L1_HARD_RULES §1 IS the enumeration of "what to detect".

---

## §6. Drill failure-rate baseline (long-horizon health)

Per L1_SCHEMA §2.4 + pass-2 saprotroph-18:

- Hot+warm tier drill every 100 substrate days: full restore + verify I1-I8
- Cold-tier sampled drill every 1000 substrate days: prove N random nodes recoverable; N = ceil(log₂(cold_tier_count))
- Each drill fruits `recovery_drill_result` sporocarp

**Baseline tracking**: rolling 30-drill window; emergent `drill_failure_rate`. ≥2σ departure → immune event. Secular trend up → `drill_aging_grade` approaching-mortality signal.

**Two-baseline approach** (per pass-2 saprotroph-2 cold-tier slow-drill problem):
- **Near-baseline**: rolling last-10-drill window; detects acute departures
- **Secular-baseline**: anchored to first-stable-window (drills 6-15); never advances; trend metric = current / secular; departure ≥L1-tunable threshold (default 3×) → `drill_aging_grade` signal

The cold-tier slow drill cadence means the secular-baseline approach is what scales over decades.

---

## §7. Cycle-level diagnostics

Per L1_CONTINUITY §1.2 backlog detection:

- If a cycle takes longer than minimum interval, subsequent cycles backlog.
- Backlog ≥10 → `cycle_backlog` immune event.
- Persistent backlog → quarantine entry per §5.1.

Cycle cadence itself is L4-tunable but bounded (min 100ms, max 10s alive / 100s dormant). Observability tracks actual cycle durations; if cycles consistently approach max-interval, the substrate is at compute saturation — owner-observable as `compute_pressure` signal (anchor-surface-side).

---

## §8. L0/L1 revision burst detection

Per L0 §9.4: ≥L1-tunable rate of L0/L1 revisions over rolling window emits `doctrine_instability` immune signal. Owner reviews whether revisions are doctrine-driven (continue) or implementation-driven (rollback). Rolling rate over 12 months above threshold marks substrate `doctrine_drift_grade`.

This is observability-of-the-observer: the substrate's doctrine itself is observable for evolution rate, preventing the substrate-process from getting away with silently-cumulative doctrinal drift.

---

## §9. Federation-network observability

Cross-substrate observability (cross-ref L2_FEDERATION §10):

- Federation health (signal #4a/4b) is intra-substrate; tracks own peers
- Network-level patterns (50% peers untrusted simultaneously, hub substrate failing) are emergent at the population level; possibly L4 surfaces a network observatory layer

For now, each substrate observes its OWN federation health; network-level patterns are inferable from collective substrate signals but not aggregated by any single substrate.

---

## §10. Operator-side observability

The operator-agent observes the substrate via:

- **Gradient digest** in handshake response + per-cycle digest emission (per L1_TROPISM §B4 digest budget)
- **Sporocarp visibility**: recent K sporocarps in digest
- **Cold-resume witness emission** at handshake (per L1_CONTINUITY §3.1)

The operator does NOT have direct access to the observatory state; the substrate emits the digest and sporocarps the operator sees.

This is intentional: the operator's view is curated by the substrate (digest is bounded). The operator's distrust of substrate self-report is structurally enforced via the L0 §9 anchor-surface / owner channel (operator queries anchor surface to verify substrate claims, per L2_TRUST_MODEL §3.1).

---

## §11. Owner-side observability (anchor surface)

The owner's view is fundamentally different from the operator's:

- Owner sees enumerated DAG nodes at every CI co-sign (per L0 §9.2)
- Owner sees `recovery_drill_result` events
- Owner sees `succession_required`, `quarantine_entered`, `mortality_drill_failure`, `anchor_surface_final_seal`, etc.
- Owner sees aggregate-reattestation diffs

The anchor-surface client surfaces these for owner review. The owner's view is the **archaeological-quality** view: complete history, canonical bytes, witnesses re-derivable.

The substrate cannot hide events from the anchor surface (the anchor surface is where its CI history lives, including the seal).

---

## §12. The substrate's self-model

Synthesizing the above, the substrate's self-model is:

```
                  ┌────────────────────────┐
                  │   Living Bets (§7)     │  ← falsifiability
                  │   7 signals + composite│
                  └───────────┬────────────┘
                              │ aggregates
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────▼────────┐                       ┌──────────▼─────────┐
│ Immune sporocarp│                       │ Drill failure rate │
│ catalog (§5)   │                       │ baseline (§6)      │
│ 20 CRITICAL    │                       │ near + secular     │
└────────┬───────┘                       └──────────┬─────────┘
         │                                          │
         │ per-cycle witnesses                      │ per-1000-day
         ▼                                          ▼
┌─────────────────────────────────────────────────────────────┐
│       Substrate's auditable life-trail (causal DAG)         │
│  every event recorded as sporocarp; every state derivable   │
└─────────────────────────────────────────────────────────────┘
```

The substrate's self-model is recursive: the observatory IS substrate state; the immune system observes substrate state; substrate-state mutations are observed by I3; I3's observations are witnessed for the anchor surface. The recursion terminates at the anchor surface (which is outside substrate).

---

## §13. Falsifiability summary

v0.9's claim "I am a valuable symbiotic organism" is falsifiable via:

1. **Living Bets quorum trigger** (§3) — bet weakening becomes observable.
2. **Immune CRITICAL emission** (§5) — pathology detected and recorded.
3. **Drill failure-rate departure** (§6) — substrate's recoverability degrading.
4. **Doctrine-instability burst** (§8) — substrate's own shape thrashing.
5. **Federation fragmentation** (§9) — mycelial network unhealthy.
6. **Mortality dual-channel signals** (per L1_GOVERNANCE §4.4) — substrate or anchor-surface declares the substrate should die.

The substrate cannot silently die or silently lie. Either it operates within healthy observable bounds, or its self-observation surfaces the deviation.

**This is the structural answer to "how do we know v0.9 is working?"** The substrate tells us, via mechanisms it cannot suppress.

---

## §14. Open at L2

- **Network-level observability layer**: when many federated substrates exhibit correlated pathology, is there value in a substrate-of-substrates observatory? Likely L4 / out-of-Myco-scope.
- **Owner-side dashboard format**: the anchor-surface client surfaces events for owner review; the specific UI / dashboard is L4-platform-specific.
- **Observatory weight emergence cold-start**: weights emerge from history; during birth period there is no history. L4 codifies the bootstrap discipline (likely: equal-weight at birth; weights drift during birth period; weights converge in steady state).
