"""Semantic lint dimensions — graph + cross-reference + cadence signals.

7 dims at v0.8.6+: SE1 (dangling refs), SE2 (orphan integrated
notes), SE3 (graph self-cycle), SE5 (version-anchor freshness in
live agent-facing docs — v0.7.2 永恒删减 ratchet), RL1 (R1-R7
rules referenced somewhere), LB1 (Living Bets audit cadence
overdue — v0.7.5 amendment), LB2 (Living Bets two-regime axis
present — v0.8.0). v0.8.6 retired SE4 (permanently-empty white-
list since v0.6.0) and RL2 + RL3 (read a session-calls log that
production code never wrote — dead-letter checkers).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration". One module per dimension per craft
v0_6_0_unified_evolution Round 4 owner amendment §R2.
"""
