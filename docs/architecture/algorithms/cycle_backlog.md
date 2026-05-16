# Cycle-Backlog Mechanism (C36)

> Extracted from L1_CONTINUITY §1.3. Normative spec lives at L1_CONTINUITY §1.3 + L1_HARD_RULES C36.

## Backlog predicate

`cycle_end_wall_clock − cycle_start_wall_clock > cycle_budget_threshold` (L1-tunable, default 5s).

## Counter and emission

- `consecutive_backlog_cycles` resets to 0 on any in-budget cycle.
- Counter ≥ L1-tunable (default 10) → `C36_cycle_backlog` immune signal.

## Witnesses (L0 §9.3.4)

`(cycle_id, observed_cycle_duration_unix_ns, cycle_budget_threshold_unix_ns, consecutive_backlog_count, gradient_axis_pressures_at_emission, anchor_nonce_derived_sample_of_recent_cycle_durations)`.

## Recovery

Continues operating; no auto-clear. Owner sees C36 at next CI co-sign; chooses re-baseline attestation or leave in flight.

## Escalation to mortality (P11.c)

- Sustained C36 past L1-tunable saturation-threshold (default 1000 cycles or 24hr continuous) → alive-but-saturated sub-state.
- Further saturation → P7 (`self_euthanasia_proposal`).

## Signal feeds

- Signal #7 per L0 §7.3 + L2_OBSERVABILITY §7.
- Feeds §7.4 falsifiability quorum.
