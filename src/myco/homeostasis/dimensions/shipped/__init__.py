"""Shipped lint dimensions — release-surface invariants.

2 dims at v0.8.6+: SH1 (package version anchor — every doctrine /
manifest reference to a version number matches the live
__version__), SH2 (kernel ahead of canon — v0.6.0 ratchet that
fires when source code has features whose canon manifest entry has
not landed yet, signaling a forgotten molt).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration". One module per dimension per craft
v0_6_0_unified_evolution Round 4 owner amendment §R2.
"""
