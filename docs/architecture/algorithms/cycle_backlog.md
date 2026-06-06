> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4). See `docs/architecture/OUTLINE.md` §3 for details.

---

# Cycle-Backlog Mechanism (C36)

> Extracted from L1/CONTINUITY §1.3. Normative spec lives at L1/CONTINUITY §1.3 + L1/HARD_RULES C36.

## Backlog predicate

`cycle_end_wall_clock − cycle_start_wall_clock > cycle_budget_threshold` (L1-tunable, default 5s).

## Counter and emission

- `consecutive_backlog_cycles` resets to 0 on any in-budget cycle.
- Counter ≥ L1-tunable (default 10) → `C36_cycle_backlog` immune signal.

## Witnesses (provenance: prior-L0 §3.11, mapped via PROVENANCE §2 to the retired L0/cards/AS_anchor_surface.md; keyless v3.1.5)

`(cycle_id, observed_cycle_duration_unix_ns, cycle_budget_threshold_unix_ns, consecutive_backlog_count, gradient_axis_pressures_at_emission, substrate_dag_tip_derived_sample_of_recent_cycle_durations)`.

> *(Keyless v3.1.5: the witness sample field was `anchor_nonce_derived_sample_of_recent_cycle_durations`; the sample is now seeded from the DAG-tip hash, not an anchor-minted nonce, and the prior `AS_anchor_surface §3.11` anchor-nonce rule is retired.)*

## Recovery

Continues operating; no auto-clear. The cultivator sees C36 at the next CI approval (the live human-in-the-loop gate; keyless v3.1.5, was "owner ... CI co-sign"); chooses to re-baseline at that gate or leave it in flight.

## Escalation to mortality (P11.c)

- Sustained C36 past L1-tunable saturation-threshold (default 1000 cycles or 24hr continuous) → alive-but-saturated sub-state.
- Further saturation → P7 (`self_euthanasia_proposal`).

## Signal feeds

- Signal #7 per L0/cards/LB_living_bets.md §3 + L2/OBSERVABILITY §7.
- Feeds §7.4 falsifiability quorum.
