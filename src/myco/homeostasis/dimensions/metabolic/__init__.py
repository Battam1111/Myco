"""Metabolic lint dimensions — substrate-flow + backlog signals.

6 dims at v0.8.6+: MB1 (raw-notes backlog ≥ N), MB2 (no integrated
yet — fresh substrate signal), MB3 (raw-notes high watermark, fix
via bulk-assimilate), MB4 (sporulated-reabsorbed integrity), MB6
(stale draft / distilled cleanup), MB8 (shim hit-counter — v0.7.1
sunset-gate enforcement). v0.8.5 retired MB7 (mcp_resources
excretion) and v0.6.0 reserved MB5 (never used; gap preserved
intentionally).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration". One module per dimension per craft
v0_6_0_unified_evolution Round 4 owner amendment §R2.
"""
