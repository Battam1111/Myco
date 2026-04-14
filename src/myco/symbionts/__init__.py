"""``myco.symbionts`` — downstream-substrate adapters.

Each module here wires Myco into a specific downstream project (e.g.
ASCC) through thin adapters. The adapters live here — not in the
downstream project — so Myco remains the single source of truth for
substrate shape while the downstream project stays ignorant of Myco's
internals. Populated opportunistically from Stage C onward.
"""
